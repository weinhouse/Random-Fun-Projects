## Hardware Debounce


### Testing:
Tested using raspberry pi 4 with Adafruit FeatherWing relay switch.

- Lots of bouncing in a 145 uS time frame
- Virtually no bounce in a 14.4 uS time frame

#### Switch signal sent using the following code:
```
import RPi.GPIO as GPIO # Import the RPi.GPIO library
from time import sleep # Import the sleep function
import random

# Set the GPIO pin numbering mode to BCM (Broadcom SOC channel)
GPIO.setmode(GPIO.BCM)
num = 1

# Define the GPIO pin you want to use (e.g., GPIO 17)
output_pin = 4

# Set the defined GPIO pin as an output pin
GPIO.setup(output_pin, GPIO.OUT)

try:
    while True:
        # Set the pin to HIGH (3.3V), turning on an LED
        random_delay = random.uniform(0.1, 3.0)
        sleep(random_delay)
        GPIO.output(output_pin, GPIO.HIGH)
        print("GPIO HIGH")
        print(num)
        num += 1
        # Set the pin to LOW (0V), turning off an LED
        random_delay = random.uniform(0.2, 0.5)
        sleep(random_delay) # Wait for 1 second
        GPIO.output(output_pin, GPIO.LOW)
        # print("GPIO LOW")
except KeyboardInterrupt:
    # Trap a KeyboardInterrupt (e.g., CTRL+C) to clean up
    print("Exiting program")
    GPIO.cleanup() # Reset all GPIO ports used by this program to their default state
```
```
GPIO HIGH
185921
GPIO HIGH
185922
GPIO HIGH
185923
^CExiting program
larryw@raspberrypi:~ $ 
```

#### Capture after using external switch and output from debounce circuit (two bounce events out of 185,923 random switch events):
```
Rising edge detected on GPIO 27 185922!
Rising edge detected on GPIO 27 185923!
Rising edge detected on GPIO 27 185924!
Rising edge detected on GPIO 27 185925!
^C
```
#### Code:
```
import RPi.GPIO as GPIO
import time
num = 1

# Function to execute when the interrupt is triggered
def my_callback(channel):
    global num
    print(f"Rising edge detected on GPIO {channel} {num}!")
    num += 1 
  

try:
    # Set up GPIO 27 as an input with a pull-down resistor
    # The pull-down resistor ensures the pin is held at 0V by default.
    # The rising edge is triggered when the voltage is pulled up to 3.3V.
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(27, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

    # Add a rising edge detection event on GPIO 27
    # `bouncetime` is used to debounce the pin, ignoring further edges for 200ms
    # This prevents multiple triggers from a single physical event, like a button press
    # GPIO.add_event_detect(27, GPIO.RISING, callback=my_callback, bouncetime=20)
    GPIO.add_event_detect(27, GPIO.RISING, callback=my_callback)

    # Keep the script running
    print("Waiting for rising edge on GPIO 27...")
    while True:
        time.sleep(1)

except KeyboardInterrupt:
    print("\nProgram terminated by user")
finally:
    GPIO.cleanup() # Clean up all GPIO resources
```




