### esp8266 research:
#### boards:
  - [esp-01](https://www.amazon.com/gp/product/B07WTBX6QK)
  - [Adafruit HUZZAH Breakout](https://www.adafruit.com/product/2471?gclid=Cj0KCQjw0caCBhCIARIsAGAfuMwYJhK4BSxBEPRQ4VUXTi3n2HCp3yLLs-bW9CtIB9SMHkCAoDBkC3caAquLEALw_wcB)
  - [HiLetgo NodeMCU ESP-12E](https://www.amazon.com/gp/product/B081CSJV2V)

#### flashing:
Using [esptool.py](https://github.com/espressif/esptool) for flashing installed with pip install esptool

Flashing esp-01 with [Espressif AT firmware](https://www.espressif.com/en/support/download/at) (V1.7.4	2020.06.03). After unzipping the download there is a README.md that will help with flashing located in the unzipped folder path: ESP8266_NonOS_AT_Bin_V1.7.4/bin/at/README.md, and here are the esptool commands that I used to place image at the correct locations:
```
NOTE! - change --port depending on what is in use.
      - it's recommended to erase flash first.
      - 
esptool.py --port /dev/ttyUSB0 erase_flash

esptool.py --chip auto --port /dev/ttyUSB0 --baud 115200 --before default_reset --after hard_reset write_flash -z --flash_mode dio --flash_freq 40m --flash_size 1MB 0x00000 /home/larryw/Desktop/flash/ESP8266_NonOS_AT_Bin_V1.7.4/bin/boot_v1.7.bin
esptool.py --chip auto --port /dev/ttyUSB0 --baud 115200 --before default_reset --after hard_reset write_flash -z --flash_mode dio --flash_freq 40m --flash_size 1MB 0x01000 /home/larryw/Desktop/flash/ESP8266_NonOS_AT_Bin_V1.7.4/bin/at/512+512/user1.1024.new.2.bin
esptool.py --chip auto --port /dev/ttyUSB0 --baud 115200 --before default_reset --after hard_reset write_flash -z --flash_mode dio --flash_freq 40m --flash_size 1MB 0xfc000 /home/larryw/Desktop/flash/ESP8266_NonOS_AT_Bin_V1.7.4/bin/esp_init_data_default_v08.bin
esptool.py --chip auto --port /dev/ttyUSB0 --baud 115200 --before default_reset --after hard_reset write_flash -z --flash_mode dio --flash_freq 40m --flash_size 1MB 0x7e000 /home/larryw/Desktop/flash/ESP8266_NonOS_AT_Bin_V1.7.4/bin/blank.bin
esptool.py --chip auto --port /dev/ttyUSB0 --baud 115200 --before default_reset --after hard_reset write_flash -z --flash_mode dio --flash_freq 40m --flash_size 1MB 0xfe000 /home/larryw/Desktop/flash/ESP8266_NonOS_AT_Bin_V1.7.4/bin/blank.bin
```
