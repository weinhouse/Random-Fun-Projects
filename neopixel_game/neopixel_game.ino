#include <FastLED.h>
#define NUM_LEDS 60
CRGBArray<NUM_LEDS> leds;

#define touchPin A0

int touchPinVal = 0;
float LEDS_ON = 1.1;

int butPin = 2;
int butPinVal = 1;


void setup() {
  FastLED.addLeds< WS2812B, 16, GRB>(leds, NUM_LEDS);
  FastLED.setBrightness(30);
  Serial.begin(9600);
  pinMode(butPin, INPUT_PULLUP);
  }


void loop() {
  butPinVal = digitalRead(butPin);
  touchPinVal = analogRead(touchPin);
  LEDS_ON = floor(50.0 / 903.0 * ( touchPinVal - ( (50.0 * 15.0) / 903.0 ) ));
  int intLEDS_ON = int(LEDS_ON);
  Serial.print(touchPinVal);
  Serial.print(" ");
  Serial.print(intLEDS_ON);
  Serial.print(" ");
  Serial.println(butPinVal);
  if (intLEDS_ON == 0) {
    FastLED.clear(true);
  }
  if (butPinVal == 0) {
    winner();
  }
  static uint8_t hue;
  for(int i = 0; i < intLEDS_ON; i++) {   
    leds.fadeToBlackBy(15);

    leds[i] = CHSV(hue++, 255,255);

    FastLED.delay(2);
  }
  for(int i = intLEDS_ON; i > 0; i--) {   

    leds.fadeToBlackBy(15);

    leds[i] = CHSV(hue++, 255,255);

    FastLED.delay(2);
  }
}

void winner() {
  for (int j = 0; j < 15; j++) {
    static uint8_t hue;
    for(int i = 0; i < 60; i++) {   
      leds.fadeToBlackBy(15);
  
      leds[i] = CHSV(hue++, 255,255);

      FastLED.delay(2);
    }
    for(int i = 60; i > 0; i--) {   

      leds.fadeToBlackBy(15);

      leds[i] = CHSV(hue++, 255,255);

      FastLED.delay(4);
    }
  }
}