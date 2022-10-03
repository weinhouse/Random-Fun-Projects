from time import sleep
import RPi.GPIO as GPIO

inPin = 40
oldState = 0
currentState = 0

GPIO.setmode(GPIO.BOARD)
GPIO.setup(inPin,GPIO.IN,pull_up_down=GPIO.PUD_DOWN)
sleep(1)
try:
    while True:
        buttonState = GPIO.input(inPin)
        if currentState != buttonState:
           print('State changed to {}'.format(buttonState))
           oldState = currentState
           currentState = buttonState
        sleep(.25)
except KeyboardInterrupt:
    GPIO.cleanup()
    print('GPIO Good to go')
