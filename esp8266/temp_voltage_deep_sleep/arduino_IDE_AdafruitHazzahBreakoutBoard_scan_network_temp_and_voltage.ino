// Networking esp8266
#include <ESP8266WiFi.h>
#include <ESP8266WiFiMulti.h>

// Temperature Sensor ds18b20
#include <OneWire.h>
#include <DallasTemperature.h>

// MQTT
#include <PubSubClient.h>

// Reading temperature
#define ONE_WIRE_BUS 12
OneWire oneWire(ONE_WIRE_BUS);
DallasTemperature sensors(&oneWire);

// JSON
#include <ArduinoJson.h>

// Multiple Wifi access points
ESP8266WiFiMulti wifiMulti;

// MQTT stuff:
const char* mqttServer = "<IP address of mqtt server>";
const int mqttPort = 1883;
const char* topic = "jumilla/temp_sensor/huzzah-1";
const char* mp_name = "huzzah-1";
const char* mqttUser = "<mqtt user>";
const char* mqttPassword = "<mqtt password>";
WiFiClient espClient;
PubSubClient client(espClient);

// Voltage variables
const int analogInPin = A0;
int analogValue;
float voltage;
float LSB = 4.11 / 381;  //Least Significant Bit Vmax / Test ADC Measurement

// Json variables size is number of elements
const size_t CAPACITY = JSON_ARRAY_SIZE(9);
char output[200];


void setup()
{
  Serial.begin(115200);
  Serial.setDebugOutput(true);
  Serial.println();
  WiFi.mode(WIFI_STA);
  wifiMulti.addAP("<NetworkSSID>", "<Password>");
  wifiMulti.addAP("<NetworkSSID>", "<Password>");
  wifiMulti.addAP("<NetworkSSID>", "<Password>");
  wifiMulti.addAP("<NetworkSSID>", "<Password>");
}


void loop()
{
  wifiMulti.run();
  delay(10000);
  if (WiFi.status() == WL_CONNECTED) {  
    // allocate the memory for json doc
    StaticJsonDocument<CAPACITY> doc;
    // create an empty array
    JsonObject line = doc.to<JsonObject>();;
    
    analogValue = analogRead(analogInPin);
    voltage = analogValue * LSB;

    line["name"] = mp_name;
    line["ssid"] = WiFi.SSID();
    line["ip4"] = WiFi.localIP().toString();
    line["adc"] = String(analogValue);
    line["voltage"] = String(String(voltage));

    String temp_f = readDSTemperatureF();
    if (temp_f == "--") {
      Serial.println("Failed to read from DS18B20 sensor");
      line["tempf"] = "error_temperature_read";
      // logging("err_temp_read", "Faild to read sensor");
    } else {
      Serial.println("Temp in F: " + temp_f);
      line["tempf"] = temp_f;
    }
    
    serializeJson(line, output, sizeof(output));
    Serial.println(output);
    
    connectMQTT();
    Serial.println("deep sleep");
    delay(3000); // Delay so that we can publish
    ESP.deepSleep(1200e6);
  }
}


void connectMQTT()
{
  client.setServer(mqttServer, mqttPort);
  while (!client.connected()) {
    Serial.println("Connecting to MQTT...");
 
    if ( client.connect(mp_name, mqttUser, mqttPassword )) {
      Serial.println("connected");
      delay(2000);
      client.publish(topic, output, 1);
    } else {
      Serial.print("failed with state ");
      Serial.println(client.state());
      //delay(2000);
    }
  }
}


String readDSTemperatureF() {
  // Call sensors.requestTemperatures() to issue a global temperature and Requests to all devices on the bus
  sensors.requestTemperatures();
  float tempF = sensors.getTempFByIndex(0); //sensors.getTempCByIndex(0) for Celsius
  if(int(tempF) == -196){
    return "--";
  } else {
    return String(tempF);
  }
}
