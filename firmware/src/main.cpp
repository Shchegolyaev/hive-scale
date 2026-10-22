// =====================================================================
//  Контрольный улей: HX711 + 4 тензодатчика, SHT31 ×2, DS18B20, ESP32.
//  Цикл: проснулся -> замерил -> в очередь -> отправил по MQTT -> уснул.
// =====================================================================
#include <Arduino.h>
#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <Wire.h>
#include <Adafruit_SHT31.h>
#include <OneWire.h>
#include <DallasTemperature.h>
#include <HX711.h>
#include <Preferences.h>
#include <esp_sleep.h>
#include <esp_timer.h>
#include <esp_sntp.h>
#include <driver/gpio.h>
#include <time.h>
#include <algorithm>
#include "config.h"

// ---------------------------------------------------------------------
//  Данные, которые переживают deep sleep
// ---------------------------------------------------------------------
struct Sample {
  uint32_t ts;            // unix-время (до первой синхронизации — «сырое»)
  int32_t  raw;           // сырой отсчёт HX711, INT32_MIN если нет
  float    w;             // кг
  float    tIn, hIn, tOut, hOut;
  float    tDs[DS_MAX];
  float    vbat;
};

struct HistItem { uint32_t ts; float w; };

RTC_DATA_ATTR uint32_t bootCount;
RTC_DATA_ATTR Sample   queueBuf[QUEUE_LEN];
RTC_DATA_ATTR uint8_t  qHead, qCount;          // кольцевой буфер: qHead — самый старый
RTC_DATA_ATTR HistItem hist[HIST_LEN];
RTC_DATA_ATTR uint8_t  hHead, hCount;
RTC_DATA_ATTR uint8_t  fastLeft;
RTC_DATA_ATTR uint32_t lastAlertTs;
RTC_DATA_ATTR uint32_t lastNtpTs;
RTC_DATA_ATTR bool     wifiCached;
RTC_DATA_ATTR uint8_t  wifiBssid[6];
RTC_DATA_ATTR int32_t  wifiChannel;
RTC_DATA_ATTR int8_t   lastRssi;
RTC_DATA_ATTR uint16_t failStreak;             // подряд неудачных отправок
RTC_DATA_ATTR char     pendingAlert[192];

// Калибровка — во flash (NVS), переживает отключение питания
struct Cal { int32_t offset; float scale; float tc; float tRef; } cal;
Preferences prefs;

HX711 hx;
Adafruit_SHT31 shtIn, shtOut;
OneWire oneWire(PIN_ONEWIRE);
DallasTemperature ds(&oneWire);
WiFiClientSecure net;
PubSubClient mqtt(net);
uint8_t dsCount;

// ---------------------------------------------------------------------
//  Утилиты
// ---------------------------------------------------------------------
static inline bool timeValid() { return (uint32_t)time(nullptr) >= EPOCH_VALID; }

void loadCal() {
  prefs.begin("scale", true);
  cal.offset = prefs.getInt("offset", 0);
  cal.scale  = prefs.getFloat("scale", 0.0f);   // отсчётов на 1 кг; 0 = не откалибровано
  cal.tc     = prefs.getFloat("tc", 0.0f);      // кг на °C
  cal.tRef   = prefs.getFloat("tref", 20.0f);
  prefs.end();
}

void saveCal() {
  prefs.begin("scale", false);
  prefs.putInt("offset", cal.offset);
  prefs.putFloat("scale", cal.scale);
  prefs.putFloat("tc", cal.tc);
  prefs.putFloat("tref", cal.tRef);
  prefs.end();
}

[[noreturn]] void goToSleep(uint32_t seconds) {
  if (seconds < 20) seconds = 20;
  Serial.printf("sleep %us\n", (unsigned)seconds);
  Serial.flush();
  WiFi.disconnect(true);
  WiFi.mode(WIFI_OFF);
  // Держим SCK в 1 во сне -> HX711 и мост тензодатчиков обесточены.
  pinMode(PIN_HX_SCK, OUTPUT);
  digitalWrite(PIN_HX_SCK, HIGH);
  gpio_hold_en((gpio_num_t)PIN_HX_SCK);
  gpio_deep_sleep_hold_en();
  esp_sleep_enable_timer_wakeup((uint64_t)seconds * 1000000ULL);
  esp_deep_sleep_start();
}

// Сторож: если что-то повисло (TLS, датчик) — всё равно уходим спать.
void watchdogCb(void*) { goToSleep(INTERVAL_DAY_S); }

void startWatchdog() {
  esp_timer_handle_t t;
  esp_timer_create_args_t args = {};
  args.callback = &watchdogCb;
  args.name = "awake_wdt";
  esp_timer_create(&args, &t);
  esp_timer_start_once(t, (uint64_t)MAX_AWAKE_MS * 1000ULL);
}

// ---------------------------------------------------------------------
//  Датчики
// ---------------------------------------------------------------------
float readVbat() {
#if PIN_VBAT >= 0
  uint32_t mv = 0;
  for (int i = 0; i < 8; i++) mv += analogReadMilliVolts(PIN_VBAT);
  return mv / 8.0f / 1000.0f * VBAT_DIVIDER;
#else
  return NAN;
#endif
}

// Медиана + усреднение средней половины: отсекает выбросы от ветра и пчёл на прилётной доске.
bool readHxRaw(int32_t& out, int samples = HX_SAMPLES) {
  gpio_hold_dis((gpio_num_t)PIN_HX_SCK);
  hx.begin(PIN_HX_DT, PIN_HX_SCK, 128);
  hx.power_up();
  for (int i = 0; i < HX_DISCARD; i++) {
    if (!hx.wait_ready_timeout(400)) { hx.power_down(); return false; }
    hx.read();
  }
  static int32_t buf[128];
  if (samples > 128) samples = 128;
  for (int i = 0; i < samples; i++) {
    if (!hx.wait_ready_timeout(400)) { hx.power_down(); return false; }
    buf[i] = hx.read();
  }
  hx.power_down();
  std::sort(buf, buf + samples);
  int from = samples / 4, to = samples - samples / 4;
  int64_t sum = 0;
  for (int i = from; i < to; i++) sum += buf[i];
  out = (int32_t)(sum / (to - from));
  return true;
}

float platformTemp(const Sample& s) {
#if TC_SOURCE < 0
  return s.tOut;
#else
  return s.tDs[TC_SOURCE];
#endif
}

float rawToKg(int32_t raw, float tPlat) {
  if (cal.scale == 0.0f || raw == INT32_MIN) return NAN;
  float kg = (raw - cal.offset) / cal.scale;
  if (cal.tc != 0.0f && !isnan(tPlat)) kg -= cal.tc * (tPlat - cal.tRef);
  return kg;
}

void initBuses() {
  Wire.begin(PIN_I2C_SDA, PIN_I2C_SCL);
  Wire.setClock(I2C_HZ);
  ds.begin();
  dsCount = min<uint8_t>(ds.getDeviceCount(), DS_MAX);
  ds.setResolution(11);              // 0,125 °C, 375 мс
  ds.setWaitForConversion(false);
}

Sample measure() {
  Sample s;
  s.ts = (uint32_t)time(nullptr);
  s.vbat = readVbat();                         // до Wi-Fi: под нагрузкой АЦП врёт
  s.tIn = s.hIn = s.tOut = s.hOut = NAN;
  for (int i = 0; i < DS_MAX; i++) s.tDs[i] = NAN;

  if (dsCount) ds.requestTemperatures();       // конвертация идёт параллельно с HX711

  int32_t raw;
  s.raw = readHxRaw(raw) ? raw : INT32_MIN;

  if (shtIn.begin(SHT_IN_ADDR))   shtIn.readBoth(&s.tIn, &s.hIn);
  if (shtOut.begin(SHT_OUT_ADDR)) shtOut.readBoth(&s.tOut, &s.hOut);

  for (uint8_t i = 0; i < dsCount; i++) {
    float t = ds.getTempCByIndex(i);
    if (t > -55 && t < 125 && t != 85.0f) s.tDs[i] = t;   // 85 — «не успел», -127 — обрыв
  }

  s.w = rawToKg(s.raw, platformTemp(s));
  Serial.printf("raw=%ld w=%.3f in=%.1f/%.0f%% out=%.1f/%.0f%% vbat=%.2f\n",
                (long)s.raw, s.w, s.tIn, s.hIn, s.tOut, s.hOut, s.vbat);
  return s;
}

// ---------------------------------------------------------------------
//  Очередь неотправленных замеров
// ---------------------------------------------------------------------
void enqueue(const Sample& s) {
  if (qCount == QUEUE_LEN) {                   // переполнение — теряем самый старый
    qHead = (qHead + 1) % QUEUE_LEN;
    qCount--;
  }
  queueBuf[(qHead + qCount) % QUEUE_LEN] = s;
  qCount++;
}

// После первой синхронизации NTP «сырые» метки (от 1970 г.) сдвигаем на поправку.
void fixTimestamps(int64_t delta) {
  for (uint8_t i = 0; i < qCount; i++) {
    Sample& s = queueBuf[(qHead + i) % QUEUE_LEN];
    if (s.ts < EPOCH_VALID) s.ts += delta;
  }
  for (uint8_t i = 0; i < hCount; i++) {
    HistItem& h = hist[(hHead + i) % HIST_LEN];
    if (h.ts < EPOCH_VALID) h.ts += delta;
  }
  if (lastAlertTs && lastAlertTs < EPOCH_VALID) lastAlertTs += delta;
}

// ---------------------------------------------------------------------
//  Детектор роя: вес упал на 1,2–6 кг относительно максимума за ~25 мин,
//  в сезон, днём, в тёплую погоду.
// ---------------------------------------------------------------------
void checkSwarm(const Sample& s) {
  if (isnan(s.w)) return;

  float maxW = -1e9f;
  for (uint8_t i = 0; i < hCount; i++) {
    const HistItem& h = hist[(hHead + i) % HIST_LEN];
    if (s.ts >= h.ts && s.ts - h.ts <= SWARM_WINDOW_S && h.w > maxW) maxW = h.w;
  }
  // запоминаем текущий замер
  if (hCount == HIST_LEN) { hHead = (hHead + 1) % HIST_LEN; hCount--; }
  hist[(hHead + hCount) % HIST_LEN] = {s.ts, s.w};
  hCount++;

  if (maxW < -1e8f) return;
  float drop = maxW - s.w;
  if (drop < SWARM_DROP_KG) return;
  if (lastAlertTs && s.ts - lastAlertTs < SWARM_COOLDOWN_S) return;

  const char* type;
  if (drop > SWARM_BIG_DROP_KG) {
    type = "big_drop";                      // осмотр, снятие магазина... или кража
  } else {
    if (timeValid()) {
      time_t now = s.ts; struct tm lt; localtime_r(&now, &lt);
      int month = lt.tm_mon + 1;
      if (month < SWARM_MONTH_FROM || month > SWARM_MONTH_TO) return;
      if (lt.tm_hour < SWARM_HOUR_FROM || lt.tm_hour >= SWARM_HOUR_TO) return;
    }
    if (!isnan(s.tOut) && s.tOut < SWARM_MIN_TEMP_C) return;
    type = "swarm";
  }

  snprintf(pendingAlert, sizeof(pendingAlert),
           "{\"type\":\"%s\",\"drop\":%.2f,\"w\":%.2f,\"ts\":%u}", type, drop, s.w, (unsigned)s.ts);
  lastAlertTs = s.ts;
  fastLeft = FAST_CYCLES;
  Serial.printf("ALERT %s\n", pendingAlert);
}

// ---------------------------------------------------------------------
//  Сеть
// ---------------------------------------------------------------------
bool waitWifi(uint32_t timeoutMs) {
  uint32_t t0 = millis();
  while (WiFi.status() != WL_CONNECTED) {
    if (millis() - t0 > timeoutMs) return false;
    delay(50);
  }
  return true;
}

bool connectWifi() {
  WiFi.persistent(false);
  WiFi.mode(WIFI_STA);
#ifdef USE_STATIC_IP
  WiFi.config(IPAddress(STATIC_IP), IPAddress(STATIC_GW), IPAddress(STATIC_MASK), IPAddress(STATIC_DNS));
#endif
  bool ok = false;
  if (wifiCached) {
    WiFi.begin(WIFI_SSID, WIFI_PASS, wifiChannel, wifiBssid, true);
    ok = waitWifi(WIFI_FAST_TIMEOUT_MS);
    if (!ok) { WiFi.disconnect(); delay(50); }
  }
  if (!ok) {
    WiFi.begin(WIFI_SSID, WIFI_PASS);
    ok = waitWifi(WIFI_TIMEOUT_MS);
  }
  if (ok) {
    memcpy(wifiBssid, WiFi.BSSID(), 6);
    wifiChannel = WiFi.channel();
    wifiCached = true;
    lastRssi = WiFi.RSSI();
  } else {
    wifiCached = false;                       // в следующий раз — полное сканирование
  }
  Serial.printf("wifi %s rssi=%d\n", ok ? "ok" : "FAIL", lastRssi);
  return ok;
}

void syncTimeIfNeeded() {
  uint32_t now = (uint32_t)time(nullptr);
  bool valid = now >= EPOCH_VALID;
  if (valid && now - lastNtpTs < NTP_EVERY_S) return;

  uint32_t m0 = millis();
  configTzTime(TZ_INFO, NTP1, NTP2);
  while (sntp_get_sync_status() != SNTP_SYNC_STATUS_COMPLETED && millis() - m0 < 5000) delay(50);
  uint32_t after = (uint32_t)time(nullptr);
  if (after < EPOCH_VALID) { Serial.println("ntp FAIL"); return; }

  if (!valid) {
    int64_t delta = (int64_t)after - now - (millis() - m0) / 1000;
    fixTimestamps(delta);
    Serial.printf("ntp first sync, delta=%lld\n", (long long)delta);
  }
  lastNtpTs = after;
}

void put(JsonDocument& d, const char* key, float v, int decimals) {
  if (!isnan(v)) d[key] = serialized(String(v, decimals));   // всегда «54.000», не «54»
}

size_t buildJson(const Sample& s, char* out, size_t len) {
  JsonDocument d;
  d["ts"] = s.ts;
  if (s.raw != INT32_MIN) d["raw"] = s.raw;
  put(d, "w", s.w, 3);
  put(d, "t_in", s.tIn, 2);   put(d, "h_in", s.hIn, 1);
  put(d, "t_out", s.tOut, 2); put(d, "h_out", s.hOut, 1);
  static const char* const dsKeys[] = {"t1", "t2", "t3", "t4", "t5", "t6", "t7", "t8"};
  static_assert(DS_MAX <= 8, "DS_MAX <= 8");
  for (int i = 0; i < DS_MAX; i++) put(d, dsKeys[i], s.tDs[i], 2);
  put(d, "vbat", s.vbat, 3);
  d["rssi"] = lastRssi;
  d["boot"] = bootCount;
  d["queue"] = qCount;
  return serializeJson(d, out, len);
}

bool publishAll() {
  net.setCACert(MQTT_CA_CERT);
  net.setHandshakeTimeout(15);
  mqtt.setServer(MQTT_HOST, MQTT_PORT);
  mqtt.setBufferSize(512);
  mqtt.setSocketTimeout(10);
  if (!mqtt.connect(HIVE_ID, MQTT_USER, MQTT_PASS)) {
    Serial.printf("mqtt FAIL state=%d\n", mqtt.state());
    return false;
  }

  if (pendingAlert[0] && mqtt.publish(TOPIC_ALERT, pendingAlert)) pendingAlert[0] = 0;

  char buf[512];
  while (qCount) {
    const Sample& s = queueBuf[qHead];
    if (s.ts < EPOCH_VALID) break;            // время ещё неизвестно — подождём NTP
    size_t n = buildJson(s, buf, sizeof(buf));
    if (!mqtt.publish(TOPIC_STATE, (const uint8_t*)buf, n, false)) break;
    qHead = (qHead + 1) % QUEUE_LEN;
    qCount--;
    mqtt.loop();
  }
  mqtt.loop();
  delay(100);
  mqtt.disconnect();
  net.stop();
  return qCount == 0 && pendingAlert[0] == 0;
}

// ---------------------------------------------------------------------
//  Интервал сна, с выравниванием по часам (замеры в :00, :10, :20…)
// ---------------------------------------------------------------------
uint32_t chooseInterval(const Sample& s) {
  if (fastLeft) { fastLeft--; return INTERVAL_FAST_S; }
  if (!isnan(s.vbat) && s.vbat < LOWBAT_V) return INTERVAL_LOWBAT_S;
  if (!isnan(s.tOut) && s.tOut < COLD_TEMP_C) return INTERVAL_COLD_S;
  if (timeValid()) {
    time_t now = time(nullptr); struct tm lt; localtime_r(&now, &lt);
    if (lt.tm_hour < DAY_START_H || lt.tm_hour >= DAY_END_H) return INTERVAL_NIGHT_S;
  }
  return INTERVAL_DAY_S;
}

uint32_t alignedSleep(uint32_t interval) {
  if (!timeValid() || interval < 300) return interval;
  uint32_t now = (uint32_t)time(nullptr);
  uint32_t s = interval - (now % interval);
  return s < 30 ? s + interval : s;
}

// ---------------------------------------------------------------------
//  Режим калибровки (PIN_CAL замкнут на GND при включении, Serial 115200)
// ---------------------------------------------------------------------
void printCal() {
  Serial.printf("offset=%ld scale=%.3f counts/kg tc=%.4f kg/°C tRef=%.2f\n",
                (long)cal.offset, cal.scale, cal.tc, cal.tRef);
}

void calibrationMode() {
  Serial.println(F("\n=== КАЛИБРОВКА ===\n"
                   "r       — 5 замеров (raw, кг, температуры)\n"
                   "t       — тарировка: пустая платформа -> ноль\n"
                   "c <кг>  — поставить известный груз и ввести его вес, напр. c 20.5\n"
                   "k <коэф> — термокомпенсация, кг/°C (tRef = текущая температура)\n"
                   "s       — найти датчики (I2C, DS18B20)\n"
                   "p       — показать калибровку\n"
                   "x       — выход и перезагрузка"));
  printCal();
  String line;
  for (;;) {
    if (!Serial.available()) { delay(20); continue; }
    line = Serial.readStringUntil('\n');
    line.trim();
    if (!line.length()) continue;
    char cmd = line[0];
    float arg = line.length() > 2 ? line.substring(2).toFloat() : 0;
    int32_t raw;

    switch (cmd) {
      case 'r':
        for (int i = 0; i < 5; i++) measure();
        break;
      case 't':
        if (readHxRaw(raw, 64)) { cal.offset = raw; saveCal(); Serial.println("ноль сохранён"); }
        else Serial.println("HX711 не отвечает");
        printCal();
        break;
      case 'c':
        if (arg <= 0) { Serial.println("укажи вес: c 20.5"); break; }
        if (readHxRaw(raw, 64)) {
          cal.scale = (raw - cal.offset) / arg;
          saveCal();
          Serial.printf("raw=%ld -> scale=%.3f\n", (long)raw, cal.scale);
          if (cal.scale < 0) Serial.println("Масштаб отрицательный — поменяй местами A+ и A- (или живи так, это не ошибка).");
        } else Serial.println("HX711 не отвечает");
        printCal();
        break;
      case 'k': {
        Sample s = measure();
        cal.tc = arg;
        cal.tRef = isnan(platformTemp(s)) ? 20.0f : platformTemp(s);
        saveCal(); printCal();
        break;
      }
      case 's': {
        Serial.print("I2C:");
        for (uint8_t a = 1; a < 127; a++) { Wire.beginTransmission(a); if (Wire.endTransmission() == 0) Serial.printf(" 0x%02X", a); }
        Serial.printf("\nDS18B20: %u шт.\n", (unsigned)ds.getDeviceCount());
        DeviceAddress addr;
        ds.setWaitForConversion(true); ds.requestTemperatures(); ds.setWaitForConversion(false);
        for (uint8_t i = 0; ds.getAddress(addr, i); i++) {
          Serial.printf("  t%u: ", (unsigned)(i + 1));
          for (int j = 0; j < 8; j++) Serial.printf("%02X", addr[j]);
          Serial.printf("  %.2f °C\n", ds.getTempC(addr));
        }
        break;
      }
      case 'p': printCal(); break;
      case 'x': ESP.restart(); break;
      default: Serial.println("?");
    }
  }
}

// ---------------------------------------------------------------------
void setup() {
  Serial.begin(115200);
  bootCount++;
  setenv("TZ", TZ_INFO, 1);
  tzset();

  gpio_deep_sleep_hold_dis();
  gpio_hold_dis((gpio_num_t)PIN_HX_SCK);
  pinMode(PIN_CAL, INPUT_PULLUP);
  delay(5);
  loadCal();
  initBuses();

  if (digitalRead(PIN_CAL) == LOW) calibrationMode();

  startWatchdog();
  Serial.printf("\nboot #%lu, queue=%u\n", (unsigned long)bootCount, (unsigned)qCount);

  Sample s = measure();
  enqueue(s);
  checkSwarm(s);

  bool sent = false;
  if (connectWifi()) {
    syncTimeIfNeeded();
    sent = publishAll();
  }
  failStreak = sent ? 0 : failStreak + 1;

  uint32_t interval = chooseInterval(s);
  // Нет связи несколько раз подряд — реже пытаемся, бережём батарею (замеры копятся в очереди).
  if (failStreak >= 3 && interval < INTERVAL_NIGHT_S) interval = INTERVAL_NIGHT_S;
  goToSleep(alignedSleep(interval));
}

void loop() {}
