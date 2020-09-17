#!/usr/bin/env python3

# Pushbutton script for multiple buttons.

# Script uses polling. interrupts may be better for you, I had issues when using
  # a non tactile switch, seems ok, top command indicated low cpu usage.

import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)

button1 = 21
button2 = 20
button3 = 16

button1Old = 1
button2Old = 1
button3Old = 1

GPIO.setup([button1, button2, button3], GPIO.IN, pull_up_down=GPIO.PUD_UP)


def wait_for_button_release(b, bOld):
    while True:
        bNew = GPIO.input(b)
        if bOld == 0 and bNew == 1:
            print('button pressed: {} - {}'.format(b, time.time()))
            return
        bOld = bNew
        time.sleep(0.1)


try:
    while True:
        time.sleep(0.1)
#        print('button1: {}'.format(GPIO.input(button1))) #for troubleshooting

        if GPIO.input(button1) == 0:
            wait_for_button_release(button1, button1Old)

        if GPIO.input(button2) == 0:
            wait_for_button_release(button2, button2Old)

        if GPIO.input(button3) == 0:
            wait_for_button_release(button3, button3Old)

except Exception as e:
    print(e)
    GPIO.cleanup(button1)
    GPIO.cleanup(button2)
    GPIO.cleanup(button3)
