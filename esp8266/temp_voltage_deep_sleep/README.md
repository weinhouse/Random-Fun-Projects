### Esp8266 final project

My best luck has been with Adafruit Huzzah. Warming up to esp-01, but there are limited gpio's and I will need to scrape off the led or purchase version without LED, and also solder from main chip to ground for reset so I can use deep sleep if I'm using battery. There could be some good use cases for ESP-01 with minor adjustments. There were also issues with the particular NodeMCU which would need adjustment even with ability to deep sleep since it still consumed 9.5 Mvolts sleeping. Huzzah has no led's and deep sleeps at .14 Mv

##### Final project details:
- Main project ended up as a proto board, battery powered, using Huzzah dev board, and Arduino IDE for [code](https://github.com/weinhouse/Random-Fun-Projects/blob/master/esp8266/temp_voltage_deep_sleep/arduino_IDE_AdafruitHazzahBreakoutBoard_scan_network_temp_and_voltage.ino)
  - I also ended up with a usb powered version using esp-8266-01 without the deep sleep routine and no voltage checking.
    - both versons can be seen on the above [pdf](https://github.com/weinhouse/Random-Fun-Projects/blob/master/esp8266/temp_voltage_deep_sleep/Huzzah_battery_powered_sensor_proto_board.pdf)
- Outline of process:
  - Code uses WifiMulti library to connect to one of my 4 Access Points strongest wins.
  - Code uses Json library to package up data that I want sent to my home automation system.
  - Code uses MQTT library to transmit the data to my mqtt broker.
  - Hardware has a voltage divider and I calculate voltage of battery and send so that I can monitor when to change.

Initial testing seems to indicate > 3 months between battery changes. This will be more since I was testing with a 10 minute cycle and I'm changing that to 20 minutes in my final project.
