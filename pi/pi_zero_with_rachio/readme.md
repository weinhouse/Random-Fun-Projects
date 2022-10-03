### Remote sprinkler control using Rachio, Raspberry Pi, and Shelly

Using a sprinkler controller (I'm using a [Rachio](https://rachio.com/)) to send a start signal to wireless signal device (I'm using [Raspberry Pi zero-w](https://www.raspberrypi.com/products/raspberry-pi-zero-w/)), which then sends a signal to a wireless relay to start a sprinkler (I'm using a [Shelly1](https://shopusa.shelly.cloud/shelly-1-wifi-smart-home-automation-1#163)). Need an Optocoupler (I'm using [SFH620A-2](https://www.digikey.com/en/products/detail/vishay-semiconductor-opto-division/SFH620A-2/1731591?utm_medium=email&utm_source=oce&utm_campaign=4251_OCE22RT&utm_content=productdetail_US&utm_cid=3127460&so=77457002&mkt_tok=MDI4LVNYSy01MDcAAAGGbRmd_kJ0XreCpOpFP1nH02K7By-9nil4TQubpnW5AxNZf_YGMN3IoHuVOIzBOp7uCn9jmENH0GFDrcg8C5zHVmM8B710Uo-bifJVCry7)) to move signal from 24 volt sprinkler to 5v wireless signal device. **ToDo: might be better to use microcontroller like esp 8266/32 or Pi pico-w**

We need to set up a [pi zero](https://github.com/weinhouse/Random-Fun-Projects/blob/master/pi/pi_zero_with_rachio/PiSetup.md)

Next a circuit so Rachio can signal the pi. The circuit consists of two resistors reducing the 24 voltage to ~5.6v because the resistor into the Optocoupler would get very hot otherwise. When Optocoupler is triggered, it connects the 3.3v of the Pi to a GPIO signaling that Shelly should be notified to turn on.

![alt text](https://github.com/weinhouse/Random-Fun-Projects/blob/master/pi/pi_zero_with_rachio/RachioToPi.png "Rachio to GPIO schematic")



#### Here is how I calculate what resistors to use to work with Optocoupler ([Data Sheet](https://www.vishay.com/docs/83675/sfh620a.pdf)).
```
R-1 10k ohm for voltage split
R-2  3k ohm for voltage split
R-3 100 ohm to Optocoupler
R-4  1k ohm to GPIO for protection

Calculate voltage split:
R-1 = 10k ohm
R-2 = (6 x 10k) / (24 - 6) = 3333 ohm
R-2 = (5 x 10k) / (24 - 5 = 2631 ohm
R-2 = 3k ohm = ~5.6 volts going to Optocoupler

Caclulate resistor to Optocoupler
R=(Vs-Vf)/if  Vs = Voltage Source, Vf = LED forward voltage, if = LED forward current
R=(5.6v-1.25)/.060 = 65.8 ohm
R = 100 ohm (close enough to the 65.8 ohm) to pin 1 of Optocoupler
```


