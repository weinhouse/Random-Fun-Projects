#include <Adafruit_NeoPixel.h>
#include "Adafruit_MAX1704X.h"
#include <WiFi.h>
#include <WiFiMulti.h>
#include <PubSubClient.h>

WiFiMulti wifiMulti;

WiFiClient espClient;
PubSubClient client(espClient);

float cellVoltage;
int PotPin = 8;
float PotVal;
boolean ErrorIndicatorState = 0;

#define PIN 6 //Neopixel pin
int Intensity = 0; // 0 - 12 (lights on neopixel) to be sent forward for further processing.
int IntensityOld = 0;
Adafruit_NeoPixel strip = Adafruit_NeoPixel(12, PIN, NEO_GRB + NEO_KHZ800);
byte pixelVals[][3] = {
  {0, 0, 255},
  {0, 50, 255},
  {0,255,255},
  {0,255,100},
  {0, 255, 0},
  {50, 255, 0},
  {255, 255, 0},
  {255, 100, 0},
  {255, 0, 0},
  {255, 0, 50},
  {255, 0, 255},
  {100, 0, 255}
};

Adafruit_MAX17048 maxlipo;

#define WAKEUP_GPIO  GPIO_NUM_12 //no need to declair pinmode, 10K pulldown resister.
#define BUTTON_PIN_BITMASK 0x200000000 // 2^33 in hex

unsigned long currentTime; //use for all timed events.

unsigned long last_updated_voltage = 0;
int voltage_read_interval = 10000;

unsigned long last_mqtt_time = 0;
int mqtt_publish_interval = 5000;

unsigned long last_sleep = 0;
int sleep_interval = 90000;

unsigned long error_indicator_time = 0;
int error_indicator_interval = 3000;


void ToSleep() {
  if (currentTime - last_sleep > sleep_interval) {
    Serial.println("Going to sleep now");
    delay(1000);
    strip.clear();
    strip.show();
    esp_deep_sleep_start(); //upon wake up, all variables re-set and setup() is run.
  }
}


float IRAM_ATTR checkLipo() {
  if (currentTime - last_updated_voltage > voltage_read_interval || last_updated_voltage > currentTime) {
     float cellVoltage = maxlipo.cellVoltage();
     if (isnan(cellVoltage)) {
       return 999.999;
     }
     last_updated_voltage = currentTime;
     return cellVoltage;
  }
}


void IRAM_ATTR mqttPublishBat() {
  if(currentTime - last_mqtt_time > mqtt_publish_interval || last_mqtt_time > currentTime) {
    char result[8];
    dtostrf(cellVoltage, 6, 2, result);
    client.publish("jumilla/neopixel/battery", result);
    last_mqtt_time = currentTime;
  }
}


void IRAM_ATTR mqttPublishIntensity() {
  char inten[16]; itoa(Intensity, inten, 10 );
  client.publish("jumilla/neopixel/intensity", inten);
}


void IRAM_ATTR PixelIntensity() {
  if ( IntensityOld != Intensity ) {
    strip.clear();
    for ( uint16_t i = 0; i < Intensity; i++) {
      byte red = pixelVals[i][0];
      byte green = pixelVals[i][1];
      byte blue = pixelVals[i][2];
      strip.setPixelColor(i, strip.Color(red, green, blue));
    }
    strip.show();
    if (client.connected()) {
      mqttPublishIntensity();
    }
    IntensityOld = Intensity;
    last_sleep = currentTime; // reset deep sleep timer
  }
}

float IRAM_ATTR averagePotval() {
  float sumPotVals = 0.0;
  float average;
  for (int i = 0; i < 20; i++) {
    int readVal = analogRead(PotPin);
    sumPotVals = readVal + sumPotVals;
    delay(1);
  }
  average = sumPotVals / 20;
  return average;
}

void runWhipe() {
  Serial.println("running whipe");
  for ( int i = 0; i < strip.numPixels(); i++ ) {
    int row = i;
    byte red = pixelVals[row][0];
    byte green = pixelVals[row][1];
    byte blue = pixelVals[row][2];
    for(uint16_t i=0; i<strip.numPixels(); i++) {
       strip.setPixelColor(i, strip.Color(red, green, blue));
       strip.show();
       delay(25);
    }
  }
  strip.clear();
  strip.show();
}

void pixelDisplay(uint32_t color, int pos) {
  strip.setPixelColor(pos, color);
  strip.show();
}

void reconnectMQTT() {
  // Loop three times
  for ( int i = 0; i < 3; i++ ) {
    pixelDisplay(strip.Color(0,   180,   0), 10);
  //while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    // Attempt to connect
    if (client.connect("arduinoClient","mqtt","mqtt")) {
    Serial.println("connected");
    break;
    } else {
      delay(2000);
      pixelDisplay(strip.Color(180,   0,   0), 10);
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      // Wait 5 seconds before retrying
      delay(2000);
    }
  }
}


void initMulti() {
  wifiMulti.addAP("AlexRoom-2.4", "");
  wifiMulti.addAP("OurNetwork2.4", "");
  wifiMulti.addAP("Backyard", "");
  Serial.print("Starting wiFi. ");
  for ( int i = 0; i < 3; i++ ) {
    pixelDisplay(strip.Color(0,   180,   0), 10);
    if (wifiMulti.run() == WL_CONNECTED) {
      Serial.println("");
      Serial.println("WiFi connected");
      Serial.print("IP: ");
      Serial.println(WiFi.localIP());
      reconnectMQTT();
      strip.clear();
      strip.show();
      break;
    }
    Serial.print(". ");
    strip.clear();
    strip.show();
    delay(500);
  }
  if (WiFi.status() != WL_CONNECTED) {
    pixelDisplay(strip.Color(180,   0,   0), 10);
    delay(1000);
    strip.clear();
    strip.show();
  }
}


void errorIndicator() {
  if (currentTime - error_indicator_time > error_indicator_interval) {
    if (ErrorIndicatorState == 1) {
      pixelDisplay(strip.Color(20,0,0),10);
    }
    else {
      if (Intensity >= 11) {
        pixelDisplay(strip.Color(255, 0, 255),10);
      }
      else {
        pixelDisplay(strip.Color(0,0,0),10);
      }
    }
    ErrorIndicatorState = !ErrorIndicatorState;
    error_indicator_time = currentTime;
    Serial.println(ErrorIndicatorState);
  }
}
 

void doWiFiStuff() {
    if (WiFi.status() == WL_CONNECTED && client.connected()) {
      client.loop();
      mqttPublishBat();
    }
    else {
      errorIndicator();
    }
}


void setup() {
  Serial.begin(9600);
  pinMode(PotPin, INPUT);
  strip.begin(); //NeoPixel strip
  strip.setBrightness(20);
  strip.show(); // Initialize all pixels to 'off'
  runWhipe();
  esp_sleep_enable_ext0_wakeup(WAKEUP_GPIO, 1);  //1 = High, 0 = Low
  while (!maxlipo.begin()) {
    Serial.println(F("Couldnt find Adafruit MAX17048?\nMake sure a battery is plugged in!"));
    delay(2000);
  }
  client.setServer("192.168.1.6",1883); //MQTT Server.
  initMulti(); //Start Wifi
}


void loop() {
  currentTime = millis();
  cellVoltage = checkLipo();
  PotVal = averagePotval();
  Intensity = floor(PotVal / 330);
  PixelIntensity();
  doWiFiStuff();
  ToSleep();
  delay(5);
}
