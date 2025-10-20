
#include "sim_utils.h"


SimData simData;

void readJsonFromSerial()
{
    if (Serial.available()) {
        String line = Serial.readStringUntil('\n');
        StaticJsonDocument<128> doc;
        if (deserializeJson(doc, line) == DeserializationError::Ok) {
            simData.ias = doc["ias"];
            simData.vs  = doc["vs"];
            simData.alt = doc["alt"];
            simData.hdg = doc["hdg"];
            // Now use these values to update your LVGL indicators
        }
    }
}
