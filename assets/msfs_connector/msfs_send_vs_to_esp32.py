from SimConnect import SimConnect, AircraftRequests
import serial, time, math

sp = serial.Serial("COM4", 115200, timeout=0)  # non-blocking write OK

sm = SimConnect()
aq = AircraftRequests(sm, _time=0)

prev_vs = None
DEAD_BAND = 10         # only send if |ΔVS| >= 10 fpm
RATE_LIMIT = 0.02      # seconds between sends (~50 Hz)

while True:
    vs = aq.get("VERTICAL_SPEED")   # fpm (float or None)
    if vs is None:
        time.sleep(RATE_LIMIT)
        continue

    vs_i = int(round(vs))           # send as int
    if prev_vs is None or abs(vs_i - prev_vs) >= DEAD_BAND:
        line = f"{vs_i}\n"
        sp.write(line.encode("ascii"))
        prev_vs = vs_i
        print(line.strip())  # optional debug

    time.sleep(RATE_LIMIT)
