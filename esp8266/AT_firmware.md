Flashing esp-01 with [Espressif AT firmware](https://www.espressif.com/en/support/download/at) (V1.7.4	2020.06.03)

Download and unzip the file, there is a README.md that will help with flashing located in the unzipped folder: `ESP8266_NonOS_AT_Bin_V1.7.4/bin/at/README.md`, and following are the esptool commands that I used to place image at the correct locations:
```
NOTE! - change --port depending on what is in use.
      - it's recommended to erase flash first.
 
esptool.py --port /dev/ttyUSB0 erase_flash

esptool.py --chip auto --port /dev/ttyUSB0 --baud 115200 --before default_reset --after hard_reset write_flash -z --flash_mode dio --flash_freq 40m --flash_size 1MB 0x00000 /home/larryw/Desktop/flash/ESP8266_NonOS_AT_Bin_V1.7.4/bin/boot_v1.7.bin
esptool.py --chip auto --port /dev/ttyUSB0 --baud 115200 --before default_reset --after hard_reset write_flash -z --flash_mode dio --flash_freq 40m --flash_size 1MB 0x01000 /home/larryw/Desktop/flash/ESP8266_NonOS_AT_Bin_V1.7.4/bin/at/512+512/user1.1024.new.2.bin
esptool.py --chip auto --port /dev/ttyUSB0 --baud 115200 --before default_reset --after hard_reset write_flash -z --flash_mode dio --flash_freq 40m --flash_size 1MB 0xfc000 /home/larryw/Desktop/flash/ESP8266_NonOS_AT_Bin_V1.7.4/bin/esp_init_data_default_v08.bin
esptool.py --chip auto --port /dev/ttyUSB0 --baud 115200 --before default_reset --after hard_reset write_flash -z --flash_mode dio --flash_freq 40m --flash_size 1MB 0x7e000 /home/larryw/Desktop/flash/ESP8266_NonOS_AT_Bin_V1.7.4/bin/blank.bin
esptool.py --chip auto --port /dev/ttyUSB0 --baud 115200 --before default_reset --after hard_reset write_flash -z --flash_mode dio --flash_freq 40m --flash_size 1MB 0xfe000 /home/larryw/Desktop/flash/ESP8266_NonOS_AT_Bin_V1.7.4/bin/blank.bin
```
Check version with AT+GMR and other AT [Instruction Sethttps://gist.github.com/bewest/4632563](https://www.espressif.com/sites/default/files/documentation/4a-esp8266_at_instruction_set_en.pdf)
  - ##### NOTE! Can't use Screen does not have \r\n use [miniterm.py](https://gist.github.com/bewest/4632563) or Arduino IDE's serial interface
    - `miniterm.py -p /dev/ttyUSB0 -b 115200`
Here are some example AT commands including a POST to a webserver:
```
AT+GMR
AT version:1.7.4.0(May 11 2020 19:13:04)
SDK version:3.0.4(9532ceb)
compile time:May 27 2020 10:12:17
Bin version(Wroom 02):1.7.4
OK

AT+RESTORE #Restore to Factory default

AT+CWMODE?
AT+CWMODE=1 # 1 = STA, 2 = AP, 3 = Both

AT+CWLAP #List networks

AT+CWJAP="AlexRoom-2.4","8188872432"

Show connection
AT+CIFSR

** the following will post to a webserver (I used miniterm.py:
AT+CIPSTART="TCP","192.168.1.2",80

AT+CIPSEND=260

**Using miniterm.py copy and paste the following <<EOF
POST /cgi-bin/first.py HTTP/1.0
From: larry@weinhouse.com
User-Agent: HTTPTool/1.0
Content-Type: application/x-www-form-urlencoded
Content-Length:10

notBadhehe
EOF
```
```
