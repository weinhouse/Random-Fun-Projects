Installed esp8266-01 (Very unstable resets:)

```
esptool.py --port /dev/ttyUSB0 erase_flash
esptool.py --port /dev/ttyUSB0 --baud 460800 write_flash --flash_size=detect -fm dio 0 /home/larryw/Desktop/flash/esp8266-1m-20210202-v1.14.bin
```

Installed on Adafruit Hazah
```
esptool.py --port /dev/ttyUSB0 erase_flash
esptool.py  --port /dev/ttyUSB0 --baud 460800 write_flash --flash_size=detect -fm dio 0 /home/larryw/Desktop/flash/esp8266-20210202-v1.14.bin
```
boot.py is the file that runs first and then main.py, these files live on the esp, files system that micropython creates. This filesystem can be read and written to via python on repl, in your script, or via tools that can use serial to manage.
  - Adafruit has a tool [adafruit-ampy](https://learn.adafruit.com/micropython-basics-load-files-and-run-code/install-ampy?gclid=Cj0KCQjw0caCBhCIARIsAGAfuMxI42mR9D5vCgR_MoLn2ln7aC0qGG-dMGxoMWt9SmYBjVuPZ0xIZN0aAohNEALw_wcB) that can read, copy, rm,etc on the esp8266 filesystem.

I wrote and tested a script that reads voltage of the battery, reads temperature, sends that data to web server, then deep sleeps:
```
# cat main.py 
from time import sleep
import machine
import onewire
import ds18x20
import urequests
import network
import do_connect # This is also uploaded to esp

url = 'http://192.168.1.2/cgi-bin/first.py'

LSB = 5.21 / 481 # Least Significant Bit Vmax / Test ADC Measurement


def read_temp():
    ow = onewire.OneWire(machine.Pin(12))
    ds = ds18x20.DS18X20(ow)
    roms = ds.scan()
    ds.convert_temp()
    sleep(1) 
    c = ds.read_temp(roms[0])
    f = (c * 1.8)+32
    return f


def deep_sleep(msecs):
    rtc = machine.RTC()
    rtc.irq(trigger=rtc.ALARM0, wake=machine.DEEPSLEEP)
    rtc.alarm(rtc.ALARM0, msecs)
    machine.deepsleep()


def read_voltage(lsb):
    adc = machine.ADC(0)
    a = adc.read()
    voltage = a * lsb
    adc_voltage = str(a) + " " + str(voltage)
    return adc_voltage


print('\nreading voltage and temperature')
sleep(3)


try:
    theVoltage = read_voltage(LSB)
    print('{}v'.format(theVoltage))
except Exception as e:
    print('error reading voltage: {}'.format(theVoltage))

try:
    temp = read_temp()
    print('{}f'.format(temp))
except Exception as e:
    print('error reading temperature: {}'.format(e))

do_connect.do_connect()

print('Sending data to server')
try:
    d = str(temp) + ", " + str(theVoltage)
    r = urequests.post(url, data=d)
    print(r.text)
except Exception as e:
    print('unable to post data: {}'.format(e))

print('\nTime to deep sleep')

deep_sleep(600000)
```
connection lib: (Started working on functionality to read signal strength of my networks will determine best essid to connect to)
```
# cat do_connect.py 
from time import sleep

def sortme(scan_list):
    return(sorted(scan_list, key = lambda x: x[3], reverse = True))


def do_connect():
    import network
    ourssids = ['OurNetwork2.4', 'AlexRoom-2.4', 'Backyard', 'Shed2.4']
    my_wifi_hotspots = []

    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    stations = wlan.scan()
    sorted_stations = sortme(stations)
    best_wifi_choice = sorted_stations[0][0].decode("utf-8")

    print('\nhotspot using:{}, best hotspot:{}'.format(wlan.config('essid'),best_wifi_choice))

    print('\nhotspots by signal strength:')
    for i in sorted_stations:
        if i[0].decode("utf-8") in ourssids:
            my_wifi_hotspots.append('{},({})'.format(i[0].decode("utf-8"),i[3]))
            print('dBm: {}, HotSpot: {}'.format(i[3],i[0].decode("utf-8"))) 
    print('\nnetwork config{}\n'.format(wlan.ifconfig()))
    print(', '.join(my_wifi_hotspots))

    if not wlan.isconnected():
        print('connecting to network...')
        wlan.connect('AlexRoom-2.4', '<your password>')
        while not wlan.isconnected():
            pass
    sleep(1)
```
