Goal of this project is to figure out hardware and software for remote sensors which will send data to home atomation infrastructure using rest or more likely MQTT. I was interested in deep sleep mode to sleep for say 10 minutes consuming < 1 Milliamp and then read and send (~20 seconds of higher consuption processing). I've explored the following interfaces:

- Raw AT commands (To hard to create anything very useful)
- MicroPython (Cool, but seemes pretty unstable on the boards tested)
- LUA NodeMCU (Seems good, did some basic testing not sure I want to work with another Language)
- Arduino IDE (Seems best so far, I've been learning with Arduino, so I can piggy back on that and continue)

### esp8266 research:
#### boards:
  - [esp-01](https://www.amazon.com/gp/product/B07WTBX6QK)
  - [Adafruit HUZZAH Breakout](https://www.adafruit.com/product/2471?gclid=Cj0KCQjw0caCBhCIARIsAGAfuMwYJhK4BSxBEPRQ4VUXTi3n2HCp3yLLs-bW9CtIB9SMHkCAoDBkC3caAquLEALw_wcB)
  - [HiLetgo NodeMCU ESP-12E](https://www.amazon.com/gp/product/B081CSJV2V)
 
#### Serial Interface:

(Terminal software needs to send \n\r miniterm.py works ok, also Arduino IDE serial interface.)
  - Adafruit [USB to TTL](https://www.adafruit.com/product/954?gclid=Cj0KCQjw0caCBhCIARIsAGAfuMzYtA6iFOP_1GGoUyxvZxqZRbhfdzQe0sQp620ku4pbGZ-kngWaLz0aAkZJEALw_wcB)
  - Adafruit [Friend](https://www.adafruit.com/product/3309)

#### flashing:
Using [esptool.py](https://github.com/espressif/esptool) for flashing installed with pip install esptool

Flashing esp-01 with [Espressif AT firmware](https://www.espressif.com/en/support/download/at) (V1.7.4	2020.06.03). [Example](https://github.com/weinhouse/Random-Fun-Projects/blob/master/esp8266/AT_firmware.md)
