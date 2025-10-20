#include <Arduino.h>
#include <ArduinoJson.h>

struct SimData {
    float hdg;   // heading (degrees)
    float vs;      // vertical speed (ft/min)
    float alt;     // altitude (feet)
    float ias;   // indicated airspeed (knots)
    int hdg_bug; // heading bug (degrees)

};

extern SimData simData;

void readJsonFromSerial();

