'''
MicroPython OLED Display
This is a basic setup for simple printing of messages to display.
- oled display = x:128, y:64
- with this library(ssd1306) characters are fixed width 8-pixels X 8-pixels
- my particular oled, first two rows print as yellow and balance as blue
- more info at: https://docs.micropython.org/en/latest/esp8266/tutorial/ssd1306.html
'''

from ssd1306 import SSD1306_I2C
from machine import Pin, Timer, I2C,
import time

i2c=I2C(1,sda=Pin(2),scl=Pin(3), freq=400000)
dsp=SSD1306_I2C(128,64,i2c)

disp_line1 = "Nice display!" #limit to 16 characters X 8 = 128-bits
disp_line2 = "****************"


def disp_header():
    dsp.text(disp_line1,0,0)
    dsp.text(disp_line2,0,8)
    dsp.show()
    
   
def line3Message(msg3):
    dsp.fill_rect(0, 16, 128, 8, 0) # fill = start: x=0:y=16, right x128, down y+8
    dsp.text(str(msg3), 0, 16)
    dsp.show()
    
def line4Message(msg4):
    dsp.fill_rect(0, 24, 128, 8, 0)
    dsp.text(str(msg4), 0, 24)
    dsp.show()
    
    
def line5Message(msg5):
    dsp.fill_rect(0, 32, 128, 8, 0)
    dsp.text(str(msg5), 0, 32)
    dsp.show()
    
    
def line6Message(msg6):
    dsp.fill_rect(0, 40, 128, 8, 0)
    dsp.text(str(msg6), 0, 40)
    dsp.show()


def line7Message(msg7):
    dsp.fill_rect(0, 48, 128, 8, 0)
    dsp.text(str(msg7), 0, 48)
    dsp.show()
    
    
def line8Message(msg8):
    dsp.fill_rect(0, 56, 128, 8, 0)
    dsp.text(str(msg8), 0, 56)
    dsp.show()


# Test
dsp.fill_rect(0, 0, 128, 64, 0) # Clear entire display
disp_header()
line3Message('Line 3')
line4Message('Line 4')
line5Message('Line 5')
line6Message('Line 6')
line7Message('Line 7')
line8Message('Line 8')

# turn_on_signal(None) # Turn on once then turn_on and turn off signal each other

while True:
    time.sleep(1)