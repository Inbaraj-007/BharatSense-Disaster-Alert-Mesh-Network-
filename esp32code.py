#include <SPI.h>
#include <LoRa.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <MPU6050.h>
#include <WiFi.h>
#include <HTTPClient.h>

// ── Pin Config ──
#define LORA_SCK  18
#define LORA_MISO 19
#define LORA_MOSI 23
#define LORA_CS   5
#define LORA_RST  14
#define LORA_DIO0 2
#define SOIL_PIN  34
#define TRIG_PIN  26
#define ECHO_PIN  27
#define BUZZER    25
#define NODE_ID   "NODE_A"

// ── WiFi + Server ──
const char* ssid      = "YourWiFiName";
const char* password  = "YourWiFiPassword";
const char* serverURL = "http://YOUR_LAPTOP_IP:5000/data";

// ── Danger Limits ──
#define SOIL_ALERT  70
#define WATER_ALERT 15
#define VIBR_ALERT  2.5

Adafruit_SSD1306 oled(128, 64, &Wire, -1);
MPU6050 mpu;

void setup() {
  Serial.begin(115200);
  pinMode(BUZZER, OUTPUT);
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);

  // OLED start
  Wire.begin(21, 22);
  oled.begin(SSD1306_SWITCHCAPVCC, 0x3C);
  oled.clearDisplay();
  oled.setTextSize(1);
  oled.setTextColor(WHITE);
  oled.setCursor(0, 0);
  oled.println("BharatSense");
  oled.println("NODE_A starting...");
  oled.display();

  // LoRa start
  SPI.begin(LORA_SCK, LORA_MISO, LORA_MOSI, LORA_CS);
  LoRa.setPins(LORA_CS, LORA_RST, LORA_DIO0);
  if (!LoRa.begin(433E6)) {
    oled.println("LoRa FAILED!");
    oled.display();
    while (1);
  }
  oled.println("LoRa OK");
  oled.display();

  // MPU start
  mpu.initialize();
  oled.println("MPU OK");
  oled.display();

  // WiFi connect
  WiFi.begin(ssid, password);
  oled.println("WiFi connecting...");
  oled.display();
  int tries = 0;
  while (WiFi.status() != WL_CONNECTED && tries < 20) {
    delay(500);
    tries++;
  }
  if (WiFi.status() == WL_CONNECTED) {
    oled.println("WiFi OK!");
  } else {
    oled.println("WiFi failed - OK");
  }
  oled.display();
  delay(1500);
}

void loop() {
  // Read all sensors
  int   soil  = readSoil();
  int   water = readWater();
  float vibr  = readVibration();

  // Check danger
  bool alert = (soil  > SOIL_ALERT)  ||
               (water < WATER_ALERT) ||
               (vibr  > VIBR_ALERT);

  // Show on OLED
  oled.clearDisplay();
  oled.setCursor(0, 0);
  oled.println("NODE_A [REAL HW]");
  oled.print("Soil:  "); oled.print(soil);  oled.println("%");
  oled.print("Water: "); oled.print(water); oled.println(" cm");
  oled.print("Vibr:  "); oled.println(vibr);
  if (alert) {
    oled.println("!! DANGER ALERT !!");
    digitalWrite(BUZZER, HIGH);
  } else {
    oled.println("Status: All OK");
    digitalWrite(BUZZER, LOW);
  }
  oled.display();

  // Send via LoRa
  String msg = String(NODE_ID) + "," +
               String(soil)    + "," +
               String(water)   + "," +
               String(vibr, 2) + "," +
               String(alert ? "ALERT" : "OK");

  LoRa.beginPacket();
  LoRa.print(msg);
  LoRa.endPacket();
  Serial.println("Sent: " + msg);

  // Send via WiFi to laptop
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin(serverURL);
    http.addHeader("Content-Type", "application/json");
    String json =
      "{\"node\":\"NODE_A\","
      "\"soil\":"  + String(soil)  + ","
      "\"water\":" + String(water) + ","
      "\"vibr\":"  + String(vibr)  + ","
      "\"alert\":" + String(alert ? "true" : "false") + ","
      "\"lat\":11.0168,"
      "\"lng\":76.9558}";
    http.POST(json);
    http.end();
  }

  delay(2000);
}

// ── Sensor Functions ──
int readSoil() {
  int raw = analogRead(SOIL_PIN);
  return map(raw, 0, 4095, 0, 100);
}

int readWater() {
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);
  long dur = pulseIn(ECHO_PIN, HIGH);
  return dur * 0.034 / 2;
}

float readVibration() {
  int16_t ax, ay, az, gx, gy, gz;
  mpu.getMotion6(&ax, &ay, &az, &gx, &gy, &gz);
  return sqrt(
    pow(ax / 16384.0, 2) +
    pow(ay / 16384.0, 2) +
    pow(az / 16384.0, 2)
  );
}