#include <Arduino.h>
#include <Arduino_RouterBridge.h>

// ============================================================
// SKYGUARDIAN MCU
// LED + BUZZER CONTROL
// ============================================================

const int BUZZER_PIN = 8;


// ============================================================
// LED 3 RGB CONTROL
// ============================================================

void set_led3_color(int r, int g, int b)
{
    analogWrite(LED3_R, r);
    analogWrite(LED3_G, g);
    analogWrite(LED3_B, b);
}


// ============================================================
// BUZZER STATE
// ============================================================

enum BuzzerMode
{
    BUZZER_OFF = 0,
    BUZZER_NEW = 1,
    BUZZER_MONITOR = 2,
    BUZZER_ANOMALY = 3
};

volatile BuzzerMode buzzerMode = BUZZER_OFF;

unsigned long buzzerTimer = 0;
unsigned long newBeepStarted = 0;

bool buzzerState = false;
int patternStep = 0;


// ============================================================
// BUZZER LOW-LEVEL CONTROL
// ============================================================

void buzzer_on()
{
    digitalWrite(BUZZER_PIN, HIGH);
    buzzerState = true;
}


void buzzer_off()
{
    digitalWrite(BUZZER_PIN, LOW);
    buzzerState = false;
}


// ============================================================
// SET BUZZER MODE
// Called from Linux/Python through Bridge
// ============================================================

void set_buzzer_mode(int mode)
{
    if (mode < 0 || mode > 3)
    {
        mode = BUZZER_OFF;
    }

    buzzerMode = (BuzzerMode)mode;

    buzzerTimer = millis();
    patternStep = 0;

    buzzer_off();

    // --------------------------------------------------------
    // NEW AIRCRAFT
    // --------------------------------------------------------

    if (buzzerMode == BUZZER_NEW)
    {
        buzzer_on();

        newBeepStarted = millis();
    }

    // --------------------------------------------------------
    // MONITOR
    // --------------------------------------------------------

    else if (buzzerMode == BUZZER_MONITOR)
    {
        buzzer_on();
    }

    // --------------------------------------------------------
    // ANOMALY
    // --------------------------------------------------------

    else if (buzzerMode == BUZZER_ANOMALY)
    {
        buzzer_on();
    }
}


// ============================================================
// UPDATE BUZZER
// Non-blocking — MCU remains responsive
// ============================================================

void update_buzzer()
{
    unsigned long now = millis();


    // ========================================================
    // OFF
    // ========================================================

    if (buzzerMode == BUZZER_OFF)
    {
        buzzer_off();
        return;
    }


    // ========================================================
    // NEW AIRCRAFT
    //
    // One short beep
    // ========================================================

    if (buzzerMode == BUZZER_NEW)
    {
        if (now - newBeepStarted >= 200)
        {
            buzzer_off();

            buzzerMode = BUZZER_OFF;
        }

        return;
    }


    // ========================================================
    // MONITOR
    //
    // beep ... beep ... beep ...
    // ========================================================

    if (buzzerMode == BUZZER_MONITOR)
    {
        switch (patternStep)
        {
            case 0:

                buzzer_on();

                if (now - buzzerTimer >= 180)
                {
                    buzzerTimer = now;
                    patternStep = 1;
                }

                break;


            case 1:

                buzzer_off();

                if (now - buzzerTimer >= 150)
                {
                    buzzerTimer = now;
                    patternStep = 2;
                }

                break;


            case 2:

                buzzer_on();

                if (now - buzzerTimer >= 180)
                {
                    buzzerTimer = now;
                    patternStep = 3;
                }

                break;


            case 3:

                buzzer_off();

                if (now - buzzerTimer >= 1200)
                {
                    buzzerTimer = now;
                    patternStep = 0;
                }

                break;
        }

        return;
    }


    // ========================================================
    // ANOMALY
    //
    // Fast repeating beep
    // ========================================================

    if (buzzerMode == BUZZER_ANOMALY)
    {
        if (now - buzzerTimer >= 120)
        {
            buzzerTimer = now;

            if (buzzerState)
            {
                buzzer_off();
            }
            else
            {
                buzzer_on();
            }
        }

        return;
    }
}


// ============================================================
// SETUP
// ============================================================

void setup()
{
    // --------------------------------------------------------
    // Buzzer
    // --------------------------------------------------------

    pinMode(BUZZER_PIN, OUTPUT);

    buzzer_off();


    // --------------------------------------------------------
    // LED
    // --------------------------------------------------------

    pinMode(LED3_R, OUTPUT);
    pinMode(LED3_G, OUTPUT);
    pinMode(LED3_B, OUTPUT);


    // --------------------------------------------------------
    // RouterBridge
    // --------------------------------------------------------

    Bridge.begin();


    // --------------------------------------------------------
    // Python → MCU functions
    // --------------------------------------------------------

    Bridge.provide(
        "set_led3_color",
        set_led3_color
    );


    Bridge.provide(
        "set_buzzer_mode",
        set_buzzer_mode
    );


    // --------------------------------------------------------
    // Initial state
    // --------------------------------------------------------

    set_led3_color(0, 255, 0);

    buzzer_off();
}


// ============================================================
// LOOP
// ============================================================

void loop()
{
    update_buzzer();
}
