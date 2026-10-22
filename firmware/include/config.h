#pragma once
// =====================================================================
//  Контрольный улей — настройки. Всё, что нужно поменять под себя, здесь.
// =====================================================================

#define HIVE_ID "hive1"

// ---------- Wi-Fi ----------
#define WIFI_FAST_TIMEOUT_MS 5000    // попытка по запомненному BSSID/каналу
#define WIFI_TIMEOUT_MS      12000   // полное сканирование
// Статический IP экономит 1–2 с на DHCP. Включай вместе с резервом адреса на роутере.
// #define USE_STATIC_IP
#define STATIC_IP   192, 168, 1, 60
#define STATIC_GW   192, 168, 1, 1
#define STATIC_MASK 255, 255, 255, 0
#define STATIC_DNS  192, 168, 1, 1

// ---------- MQTT ----------
#define MQTT_PORT    8883
#define TOPIC_STATE  "apiary/" HIVE_ID "/state"
#define TOPIC_ALERT  "apiary/" HIVE_ID "/alert"

// Пароли, адрес брокера и CA-сертификат — в secrets.h (не коммитится).
// Скопируй secrets.example.h -> secrets.h и заполни.
#include "secrets.h"

// ---------- Время ----------
#define TZ_INFO      "MSK-3"
#define NTP1         "ru.pool.ntp.org"
#define NTP2         "pool.ntp.org"
#define NTP_EVERY_S  3600          // RC-генератор ESP32 в deep sleep заметно уплывает
#define EPOCH_VALID  1700000000UL  // время меньше этого = ещё не синхронизировано

// ---------- Пины (ESP32 WROOM-32; сверь с распиновкой своей платы) ----------
#define PIN_HX_DT    25
#define PIN_HX_SCK   26   // + подтяжка 10 кОм к 3V3: HX711 спит, пока спит ESP32
#define PIN_I2C_SDA  21
#define PIN_I2C_SCL  22
#define PIN_ONEWIRE  4    // + 4,7 кОм к 3V3
#define PIN_VBAT     35   // делитель 470k/470k + 100 нФ на землю; -1 если питание от сети
#define VBAT_DIVIDER 2.0f
#define PIN_CAL      13   // замкнуть на GND при включении -> режим калибровки

// ---------- Датчики ----------
#define SHT_IN_ADDR  0x44  // SHT31 в улье (ADDR -> GND)
#define SHT_OUT_ADDR 0x45  // SHT31 снаружи (ADDR -> VCC)
#define I2C_HZ       50000 // медленнее = надёжнее на проводах 1–3 м
#define DS_MAX       3     // до 3 шт. DS18B20 (гнездо, края, платформа)
#define HX_DISCARD   4     // первые отсчёты после пробуждения HX711 выбрасываем
#define HX_SAMPLES   16    // при 10 SPS ≈ 1,6 с
// Термокомпенсация тензодатчиков: какой датчик считать температурой платформы.
// -1 = наружный SHT31, 0..DS_MAX-1 = индекс DS18B20.
#define TC_SOURCE    -1

// ---------- Интервалы, с ----------
#define INTERVAL_DAY_S     600
#define INTERVAL_NIGHT_S   1800
#define INTERVAL_COLD_S    1800   // снаружи ниже COLD_TEMP_C (зимовка)
#define INTERVAL_LOWBAT_S  3600
#define INTERVAL_FAST_S    120    // после подозрения на рой
#define FAST_CYCLES        8
#define COLD_TEMP_C        5.0f
#define DAY_START_H        6
#define DAY_END_H          22
#define LOWBAT_V           3.45f
#define MAX_AWAKE_MS       45000  // аварийный уход в сон

// ---------- Буферы в RTC-памяти (переживают deep sleep) ----------
#define QUEUE_LEN 64   // замеров без связи: 64 × 10 мин ≈ 10 ч
#define HIST_LEN  16   // история веса для детектора роя

// ---------- Детектор роя ----------
#define SWARM_DROP_KG     1.2f   // падение от максимума за окно
#define SWARM_BIG_DROP_KG 6.0f   // больше — скорее снят магазин / осмотр / кража
#define SWARM_WINDOW_S    1500   // окно ~25 мин
#define SWARM_MIN_TEMP_C  14.0f
#define SWARM_HOUR_FROM   9
#define SWARM_HOUR_TO     19
#define SWARM_MONTH_FROM  5
#define SWARM_MONTH_TO    8
#define SWARM_COOLDOWN_S  3600
