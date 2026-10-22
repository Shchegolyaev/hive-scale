// notifier — слушает MQTT и шлёт уведомления в Telegram и/или ntfy:
//   - тревоги от ульев (apiary/<id>/alert): рой, резкий сброс веса;
//   - улей пропал со связи / вернулся;
//   - низкий заряд батареи.
package main

import (
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"net/url"
	"os"
	"os/signal"
	"strconv"
	"strings"
	"sync"
	"syscall"
	"time"

	mqtt "github.com/eclipse/paho.mqtt.golang"
)

type cfg struct {
	mqttURL, mqttUser, mqttPass string
	tgToken, tgChat, ntfyURL    string
	offlineAfter                time.Duration
	lowBat                      float64
}

type hiveState struct {
	lastSeen   time.Time
	offline    bool
	lowBatSent time.Time
	lastWeight float64
}

type notifier struct {
	cfg  cfg
	http *http.Client
	mu   sync.Mutex
	hive map[string]*hiveState
}

func env(k, def string) string {
	if v := os.Getenv(k); v != "" {
		return v
	}
	return def
}

func main() {
	offline, err := time.ParseDuration(env("OFFLINE_AFTER", "3h"))
	if err != nil {
		log.Fatalf("OFFLINE_AFTER: %v", err)
	}
	lowBat, err := strconv.ParseFloat(env("LOWBAT_V", "3.5"), 64)
	if err != nil {
		log.Fatalf("LOWBAT_V: %v", err)
	}
	n := &notifier{
		cfg: cfg{
			mqttURL: env("MQTT_URL", "tcp://mosquitto:1883"), mqttUser: os.Getenv("MQTT_USER"), mqttPass: os.Getenv("MQTT_PASS"),
			tgToken: os.Getenv("TG_TOKEN"), tgChat: os.Getenv("TG_CHAT_ID"), ntfyURL: os.Getenv("NTFY_URL"),
			offlineAfter: offline, lowBat: lowBat,
		},
		http: &http.Client{Timeout: 15 * time.Second},
		hive: map[string]*hiveState{},
	}
	if n.cfg.tgToken == "" && n.cfg.ntfyURL == "" {
		log.Println("WARN: не задан ни TG_TOKEN, ни NTFY_URL — уведомления будут только в логе")
	}

	opts := mqtt.NewClientOptions().
		AddBroker(n.cfg.mqttURL).
		SetClientID("notifier").
		SetUsername(n.cfg.mqttUser).
		SetPassword(n.cfg.mqttPass).
		SetCleanSession(false).
		SetAutoReconnect(true).
		SetConnectRetry(true).
		SetConnectRetryInterval(5 * time.Second).
		SetOnConnectHandler(func(c mqtt.Client) {
			c.Subscribe("apiary/+/alert", 1, n.onAlert)
			c.Subscribe("apiary/+/state", 1, n.onState)
			log.Println("mqtt connected")
		})
	c := mqtt.NewClient(opts)
	c.Connect()

	go n.watchOffline()

	sig := make(chan os.Signal, 1)
	signal.Notify(sig, syscall.SIGINT, syscall.SIGTERM)
	<-sig
	c.Disconnect(500)
}

func hiveID(topic string) string {
	p := strings.Split(topic, "/")
	if len(p) >= 2 {
		return p[1]
	}
	return topic
}

func (n *notifier) state(id string) *hiveState {
	s, ok := n.hive[id]
	if !ok {
		s = &hiveState{lastSeen: time.Now()}
		n.hive[id] = s
	}
	return s
}

func (n *notifier) onAlert(_ mqtt.Client, m mqtt.Message) {
	var a struct {
		Type string  `json:"type"`
		Drop float64 `json:"drop"`
		W    float64 `json:"w"`
		Ts   int64   `json:"ts"`
	}
	if err := json.Unmarshal(m.Payload(), &a); err != nil {
		log.Printf("bad alert %q: %v", m.Payload(), err)
		return
	}
	id := hiveID(m.Topic())
	at := time.Unix(a.Ts, 0).Local().Format("15:04")
	var text string
	switch a.Type {
	case "swarm":
		text = fmt.Sprintf("🐝 %s: похоже на РОЙ — вес упал на %.1f кг (сейчас %.1f кг) в %s", id, a.Drop, a.W, at)
	case "big_drop":
		text = fmt.Sprintf("⚠️ %s: резкий сброс веса на %.1f кг (сейчас %.1f кг) в %s — осмотр, снятие магазина или кто-то трогает улей", id, a.Drop, a.W, at)
	default:
		text = fmt.Sprintf("%s: %s", id, m.Payload())
	}
	n.send(text, a.Type == "swarm")
}

func (n *notifier) onState(_ mqtt.Client, m mqtt.Message) {
	var st struct {
		Vbat *float64 `json:"vbat"`
		W    *float64 `json:"w"`
	}
	if err := json.Unmarshal(m.Payload(), &st); err != nil {
		return
	}
	id := hiveID(m.Topic())

	n.mu.Lock()
	s := n.state(id)
	wasOffline := s.offline
	s.lastSeen, s.offline = time.Now(), false
	if st.W != nil {
		s.lastWeight = *st.W
	}
	lowBat := st.Vbat != nil && *st.Vbat < n.cfg.lowBat && time.Since(s.lowBatSent) > 24*time.Hour
	if lowBat {
		s.lowBatSent = time.Now()
	}
	n.mu.Unlock()

	if wasOffline {
		n.send(fmt.Sprintf("✅ %s снова на связи", id), false)
	}
	if lowBat {
		n.send(fmt.Sprintf("🔋 %s: батарея %.2f В", id, *st.Vbat), false)
	}
}

func (n *notifier) watchOffline() {
	for range time.Tick(time.Minute) {
		var lost []string
		n.mu.Lock()
		for id, s := range n.hive {
			if !s.offline && time.Since(s.lastSeen) > n.cfg.offlineAfter {
				s.offline = true
				lost = append(lost, fmt.Sprintf("📵 %s: нет данных с %s (последний вес %.1f кг)",
					id, s.lastSeen.Format("02.01 15:04"), s.lastWeight))
			}
		}
		n.mu.Unlock()
		for _, t := range lost {
			n.send(t, false)
		}
	}
}

func (n *notifier) send(text string, urgent bool) {
	log.Println(text)
	if n.cfg.tgToken != "" && n.cfg.tgChat != "" {
		u := "https://api.telegram.org/bot" + n.cfg.tgToken + "/sendMessage"
		resp, err := n.http.PostForm(u, url.Values{"chat_id": {n.cfg.tgChat}, "text": {text}})
		if err != nil {
			log.Printf("telegram: %v", err)
		} else {
			resp.Body.Close()
			if resp.StatusCode != http.StatusOK {
				log.Printf("telegram: HTTP %d", resp.StatusCode)
			}
		}
	}
	if n.cfg.ntfyURL != "" {
		req, _ := http.NewRequest(http.MethodPost, n.cfg.ntfyURL, strings.NewReader(text))
		req.Header.Set("Title", "Пасека")
		if urgent {
			req.Header.Set("Priority", "urgent")
		}
		resp, err := n.http.Do(req)
		if err != nil {
			log.Printf("ntfy: %v", err)
		} else {
			resp.Body.Close()
		}
	}
}
