#pragma once
// Скопируй в secrets.h и заполни. secrets.h в .gitignore.

#define WIFI_SSID            "dacha"
#define WIFI_PASS            "change-me"
#define MQTT_HOST    "mqtt.example.com"
#define MQTT_USER    "hive1"
#define MQTT_PASS    "change-me"

// Корневой сертификат CA брокера. Для Let's Encrypt — ISRG Root X1:
// https://letsencrypt.org/certs/isrgrootx1.pem (действует до 2035 г.)
static const char MQTT_CA_CERT[] = R"EOF(
-----BEGIN CERTIFICATE-----
...вставь сюда содержимое isrgrootx1.pem...
-----END CERTIFICATE-----
)EOF";
