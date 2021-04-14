//This is my current testing Arduino IDE sketch setup for temperature sensor with a voltage check and sending to a WebHook server, ultimately would like this to send via MQTT to a home automation sofware such as Home Assistant.

#include <DHTesp.h> //DHT Temp Sensor

#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>

#include <OneWire.h>
#include <DallasTemperature.h>

// For reading temperature
#define ONE_WIRE_BUS 12
OneWire oneWire(ONE_WIRE_BUS);
DallasTemperature sensors(&oneWire);

int best_signal = -1000;
String best_ssid;
String original_ssid;

// For reading voltage.
const int analogInPin = A0;
int analogValue;
float voltage;
float LSB = 4.11 / 381;  //Least Significant Bit Vmax / Test ADC Measurement

// Two variables needed to include the micro processors name.
String mp_name = "\"mp_name\":\"huzzah-1\"";
const char* serverName = "http://192.168.1.2/cgi-bin/huzzah-1.py";
String log_info;


void setup() {
  Serial.begin(115200);
  WiFi.mode(WIFI_STA);
  Serial.println("\nStarting. . .");
  Serial.print("Retained IP: ");
  delay(5000);
  Serial.println(WiFi.localIP().toString());
  if (WiFi.status() != WL_CONNECTED) {
    scanNetwork();
    connect_to_network(best_ssid);
  }
  original_ssid = WiFi.SSID();
}


void loop() {
  // put your main code here, to run repeatedly:
  log_info = mp_name;
  Serial.print("\nssid: " + WiFi.SSID());
  Serial.println(", ip_address: " + WiFi.localIP().toString());
  logging("ssid", WiFi.SSID());
  logging("ip_address", WiFi.localIP().toString());
  delay(2000);
  scanNetwork();
  Serial.println("");
  Serial.print("original ");
  Serial.println(original_ssid);
  Serial.print("bestSSid ");
  Serial.println(best_ssid);
  if (original_ssid == best_ssid) {
    Serial.println("same ssid");
    Serial.println("");
  } else {
    connect_to_network(best_ssid);
  }

  analogValue = analogRead(analogInPin);
  voltage = analogValue * LSB;
  Serial.print("ADC value: ");
  Serial.print(analogValue);
  Serial.print(" Voltage: ");
  Serial.println(voltage);
  logging("adc_value", String(analogValue));
  logging("voltage", String(voltage));

  String temp_f = readDSTemperatureF();
  if (temp_f == "--") {
    Serial.println("Failed to read from DS18B20 sensor");
    logging("err_temp_read", "Faild to read sensor");
  } else {
    Serial.println("Temp in F: " + temp_f);
    logging("temperature_F", temp_f);
  }

  String logging_info = "{" + log_info + "}";
  Serial.println(logging_info);
  sendToServer(logging_info);

  Serial.println("deep sleep");
  ESP.deepSleep(600e6);

}

String connect_to_network(String ssid) {
  if (WiFi.status() == WL_CONNECTED) //disconnect if connected
  {
    Serial.print("Disconnecting ");
    WiFi.disconnect();
    while (WiFi.status() != WL_IDLE_STATUS)
    {
      delay(600);
      Serial.print(".");
    }
    Serial.println("");
    Serial.println(WiFi.localIP());
    Serial.println(WiFi.status());
  }

  Serial.print("Connecting to ");
  Serial.print(ssid);
  WiFi.begin(ssid, "<SSID Password>");
  int counter = 0;
  while (WiFi.status() != WL_CONNECTED)
  {
    delay(1000);
    Serial.print(".");
    if (counter >= 15) {
      Serial.println("");
      Serial.println("Not able to connect");
      break;
    }
    counter += 1;
  }
  Serial.println("");
  delay(100);
  Serial.println("Connected");
}

void scanNetwork() {
  Serial.println("Starting a scan");
  int n = WiFi.scanNetworks(); //returns the number of networks found.
  Serial.println("scan done");
  if (n == 0) {
    Serial.println("no networks found");
  } else {
    Serial.print(n);
    Serial.println(" networks found");
    Serial.println("Only our Access Points");
    for (int i = 0; i < n; ++i) {
      // Print SSID and RSSI for each network found
      String essid_name = WiFi.SSID(i);
      if (essid_name == "AlexRoom-2.4" ||
          essid_name == "OurNetwork2.4" ||
          essid_name == "Shed2.4" ||
          essid_name == "Backyard"){
        Serial.print(i + 1);
        Serial.print(": ");
        Serial.print(WiFi.SSID(i));
        Serial.print(" (");
        Serial.print(WiFi.RSSI(i));
        Serial.print(")");
        Serial.println((WiFi.encryptionType(i) == ENC_TYPE_NONE) ? " " : "*");
        int signal = WiFi.RSSI(i);
        if (signal >= best_signal) {
            best_signal = signal;
            best_ssid = WiFi.SSID(i);
        }
      }
    }
  }
}


String logging(String key, String value){
  log_info = log_info + ", " + "\"" + key + "\"" + ":" + "\"" + value + "\"";
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

void sendToServer( String d){
  HTTPClient http;
  http.begin(serverName);
  int httpResponseCode = http.POST(d);
  Serial.print("HTTP Response code: ");
  Serial.println(httpResponseCode);
  http.end();
