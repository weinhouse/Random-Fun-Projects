### Draw a circle
```
from ssd1306 import SSD1306_I2C
from machine import Pin, I2C
import time
import math

i2c=I2C(1,sda=Pin(2),scl=Pin(3), freq=400000)
dsp=SSD1306_I2C(128,64,i2c)

r=15
xCenter=45
yCenter=48

for deg in range(0,360,1):
    rads=deg*2*3.14/360
    x=r*math.cos(rads)+xCenter
    y=r*math.sin(rads)+yCenter
    dsp.pixel(int(x),int(y),1)
    
dsp.show()

while 1:
   time.sleep(30)
   dsp.poweroff()
   time.sleep(2)
   dsp.poweron()
```


