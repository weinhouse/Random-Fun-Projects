So far, my best luck has been with Adafruit Huzzah. Warming up to esp-01, but there are limited gpio's and I will need to scrape off the led or purchase version without LED, and also solder from main chip to ground for reset so I can use deep sleep if I'm using battery. There could be some good use cases for ESP-01 with minor adjustments. There weere also issues with the particular NodeMCU which would need adjustment even with ability to deep sleep since it still consumed 9.5 Mvolts sleeping. Huzzah has no led's and deep sleeps at .14 Mv

Here is [example](https://github.com/weinhouse/Random-Fun-Projects/blob/master/esp8266/code/arduino_IDE_AdafruitHazzahBreakoutBoard_scan_network_temp_and_voltage.ino) of Scanning network for strongest Access Point, changing access point if necessary, reading voltage of battery, reading temperature. I'm testing now and then move forward sending to Web server and ultimately to MQTT server on home network.

Currently the output is just going to a file via a WebHook server. here is the output from huzzah :-)
```
2021-04-14 09:34:17.825044	{"mp_name":"huzzah-1", "ssid":"Shed2.4", "ip_address":"192.168.1.177", "adc_value":"375", "voltage":"4.05", "temperature_F":"59.56"}
```

Here's the hardware setup so far, once tested I'll want to solder up a better pcb prototype
![image](https://github.com/weinhouse/Random-Fun-Projects/blob/master/esp8266/code/esp8266_huzzah.png)
