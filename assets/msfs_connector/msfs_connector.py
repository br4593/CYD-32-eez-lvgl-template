from SimConnect import SimConnect, AircraftRequests
import serial, json, time

# --- serial to ESP32/Arduino ---
sp = serial.Serial("COM4", 115200, timeout=0)

# --- MSFS connection ---
sm = SimConnect()
aq = AircraftRequests(sm, _time=0)

prev = {"ias": 0.0, "vs": 0, "alt": 0, "hdg": 0}

while True:
    # Use the exact same SimVar tokens as your working script
    ias = aq.get("AIRSPEED_INDICATED")          # knots (float)
    vs  = aq.get("VERTICAL_SPEED")              # ft/min (float)
    alt = aq.get("PLANE_ALTITUDE")              # feet MSL (float)
    # Prefer a heading that doesn’t depend on the gyro being powered:
    # hdg = aq.get("PLANE_HEADING_DEGREES_MAGNETIC")
    hdg = aq.get("PLANE_HEADING_DEGREES_TRUE")

    # Warn if a SimVar name failed (returns None)
    if None in (ias, vs, alt, hdg):
        missing = [k for k, v in zip(
            ("ias","vs","alt","hdg"), (ias,vs,alt,hdg)
        ) if v is None]
        print(f"⚠️  Missing SimVars: {', '.join(missing)} — check names/power state.")

    # Build JSON (fallback to previous value if None)
    data = {
        "ias": round(ias if ias is not None else prev["ias"], 1),
        "vs":  int(vs if vs is not None else prev["vs"]),
        "alt": int(round(alt if alt is not None else prev["alt"])),
        "hdg": int(round((hdg if hdg is not None else prev["hdg"]))) % 360
    }
    prev = data.copy()

    line = json.dumps(data) + "\n"
    sp.write(line.encode("utf-8"))
    print(line.strip())

    time.sleep(0.01)  # ~100 Hz
