#line 1 "/home/arduino/ArduinoApps/skyguardian2/sketch/sketch.ino"
#include <Arduino.h>
#include <Arduino_RouterBridge.h>

// ==========================================
// LED 3 RGB CONTROL
// ==========================================

#line 8 "/home/arduino/ArduinoApps/skyguardian2/sketch/sketch.ino"
void set_led3_color(int r, int g, int b);
#line 20 "/home/arduino/ArduinoApps/skyguardian2/sketch/sketch.ino"
void setup();
#line 44 "/home/arduino/ArduinoApps/skyguardian2/sketch/sketch.ino"
void loop();
#line 8 "/home/arduino/ArduinoApps/skyguardian2/sketch/sketch.ino"
void set_led3_color(int r, int g, int b)
{
    analogWrite(LED3_R, r);
    analogWrite(LED3_G, g);
    analogWrite(LED3_B, b);
}


// ==========================================
// SETUP
// ==========================================

void setup()
{
    pinMode(LED3_R, OUTPUT);
    pinMode(LED3_G, OUTPUT);
    pinMode(LED3_B, OUTPUT);

    // IMPORTANT
    Bridge.begin();

    // Make the function available to Python
    Bridge.provide(
        "set_led3_color",
        set_led3_color
    );

    // Start SkyGuardian in GREEN
    set_led3_color(0, 255, 0);
}


// ==========================================
// LOOP
// ==========================================

void loop()
{
    // Nothing required here
}
