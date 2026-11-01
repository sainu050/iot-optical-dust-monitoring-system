#include <WiFi.h>
#include <HTTPClient.h>

// ====================================================================
// Course: 24MCAT213 - INTERNET OF THINGS | Amal Jyothi College of Engineering
// Project: IoT Optical Dust & Particulate Monitoring System
// Node: ESP32 + Sharp GP2Y1014AU0F Optical Dust Sensor
// ====================================================================

// --- Wi-Fi Credentials ---
const char* ssid     = "Nothing Phone (3a)_3722";
const char* password = "netveno?";

// --- Docker Backend Server Endpoint ---
const char* serverUrl = "http://10.188.223.119:8000/api/sensor-data";
const char* deviceId  = "ESP32_Dust_01";

// --- Pin Definitions for Sharp GP2Y1014AU0F ---
const int ledPower  = 23;  // Sensor Internal IRED trigger pin (D23)
const int measurePin = 34;  // Sensor Vo analog output pin (ADC1 CH6 - D34)

// --- Optical Pulse Timing Characteristics (per Sharp datasheet) ---
const int samplingTime = 280;  // 0.28ms pulse delay before reading Vo
const int deltaTime    = 40;   // 0.04ms pulse duration to complete 0.32ms pulse width
const int sleepTime    = 9680; // Remaining period to complete standard 10ms cycle

// --- Calibration Baseline ---
// Updated from 0.50V to 0.25V to match your physical sensor's zero-dust ambient (~0.26V - 0.33V)
const float baselineVoltage = 0.25; 

struct DustReading {
  float voltage;      // Vo measured in Volts
  float dustDensity;  // Dust concentration in ug/m3
};

void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("\n--- Initializing IoT Dust Sensor Node ---");

  pinMode(ledPower, OUTPUT);
  digitalWrite(ledPower, HIGH); // Sensor LED is active LOW (OFF initially)

  analogReadResolution(12); // Ensure 12-bit ADC (0 - 4095)

  // Connect to Wi-Fi
  Serial.printf("Connecting to Wi-Fi SSID: %s\n", ssid);
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);

  int retryCount = 0;
  while (WiFi.status() != WL_CONNECTED && retryCount < 30) {
    delay(500);
    Serial.print(".");
    retryCount++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n[Wi-Fi] Connected successfully!");
    Serial.printf("[Wi-Fi] Assigned IP Address: %s\n", WiFi.localIP().toString().c_str());
  } else {
    Serial.println("\n[Wi-Fi] Warning: Connection pending. Retrying in background.");
  }
}

// Single pulse measurement
float getSinglePulseVoltage() {
  digitalWrite(ledPower, LOW);
  delayMicroseconds(samplingTime);

  int rawADC = analogRead(measurePin);

  delayMicroseconds(deltaTime);
  digitalWrite(ledPower, HIGH);
  delayMicroseconds(sleepTime);

  return rawADC * (3.3 / 4095.0);
}

// Averaged sensor reading to filter electrical jitter
DustReading readDustSensor() {
  float totalVoltage = 0.0;
  const int samples = 5;

  for (int i = 0; i < samples; i++) {
    totalVoltage += getSinglePulseVoltage();
    delay(10); // Small interval between optical samples
  }

  float avgVoltage = totalVoltage / samples;

  // Dust Density calculation (ug/m3)
  float density = 0.0;
  if (avgVoltage > baselineVoltage) {
    // 0.5mV per ug/m3 slope factor => multiply voltage difference by 500 (or standard datasheet factor)
    density = (avgVoltage - baselineVoltage) * 500.0; 
  }

  DustReading reading;
  reading.voltage = avgVoltage;
  reading.dustDensity = density;
  return reading;
}

void loop() {
  if (WiFi.status() == WL_CONNECTED) {
    DustReading reading = readDustSensor();

    Serial.printf("[Sensor] Vo: %.2f V | Dust Density: %.2f ug/m3\n", 
                  reading.voltage, reading.dustDensity);

    HTTPClient http;
    http.begin(serverUrl);
    http.setTimeout(4000);
    http.addHeader("Content-Type", "application/json");

    // Construct telemetry JSON payload
    String jsonPayload = String("{\"device_id\":\"") + deviceId + 
                         "\",\"voltage\":" + String(reading.voltage, 2) + 
                         ",\"dust_density\":" + String(reading.dustDensity, 2) + "}";

    int httpResponseCode = http.POST(jsonPayload);

    if (httpResponseCode > 0) {
      Serial.printf("[HTTP] Transmitted: %s | Response: %d\n", 
                    jsonPayload.c_str(), httpResponseCode);
    } else {
      Serial.printf("[HTTP] Error sending POST: %s\n", http.errorToString(httpResponseCode).c_str());
    }
    http.end();
  } else {
    Serial.println("[Wi-Fi] Disconnected. Reconnecting...");
    WiFi.reconnect();
  }

  delay(3000);
}