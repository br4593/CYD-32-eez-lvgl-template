# file: vs_serial_streamer_json.py
import threading, queue, time, json, math
import tkinter as tk
from tkinter import ttk, messagebox

import serial
from serial.tools import list_ports

# ---- SimConnect --------------------------------------------------------------
USE_SIMCONNECT = True
try:
    from SimConnect import SimConnect, AircraftRequests
except Exception:
    USE_SIMCONNECT = False
    SimConnect = None
    AircraftRequests = None


class DebugConfig:
    """Thread-safe debug flags shared across threads."""
    def __init__(self, rx=False, tx=False, msfs=False):
        self._lock = threading.Lock()
        self._rx = rx
        self._tx = tx
        self._msfs = msfs

    def update(self, rx=None, tx=None, msfs=None):
        with self._lock:
            if rx is not None: self._rx = bool(rx)
            if tx is not None: self._tx = bool(tx)
            if msfs is not None: self._msfs = bool(msfs)

    def get(self):
        with self._lock:
            return {"rx": self._rx, "tx": self._tx, "msfs": self._msfs}


class DataStreamer:
    """
    Background worker: reads selected vars from AircraftRequests and writes JSON to serial.
    Sends only when selected values change beyond per-key dead-bands.
    """
    VAR_MAP = {
        "hdg": "PLANE_HEADING_DEGREES_TRUE",  # library may return radians; we auto-detect
        "vs":  "VERTICAL_SPEED",
        "spd": "AIRSPEED_INDICATED",
        "alt": "PLANE_ALTITUDE",
    }

    def __init__(
        self,
        ser: serial.Serial,
        aq: 'AircraftRequests',
        rate_limit: float,
        dead_bands: dict[str, int],
        selected_keys: set[str],
        debug: DebugConfig,
        log_q: queue.Queue,
    ):
        self.ser = ser
        self.aq = aq
        self.rate_limit = rate_limit
        self.dead_bands = {k: int(dead_bands.get(k, 0)) for k in self.VAR_MAP}
        self.selected = set(selected_keys)
        self.debug = debug
        self.log_q = log_q
        self.stop_event = threading.Event()
        self.prev: dict[str, int] = {}

    def _log(self, kind: str, msg: str):
        flags = self.debug.get()
        if kind in ("info", "error"):
            self.log_q.put(msg)
        elif kind == "rx" and flags["rx"]:
            self.log_q.put(msg)
        elif kind == "tx" and flags["tx"]:
            self.log_q.put(msg)
        elif kind == "msfs" and flags["msfs"]:
            self.log_q.put(msg)

    def _get_raw(self, key: str):
        if self.aq is None: return None
        var = self.VAR_MAP[key]
        try:
            val = self.aq.get(var)
            return None if val is None else float(val)
        except Exception as e:
            self._log("msfs", f"MSFS read error [{key}/{var}]: {e}")
            return None

    @staticmethod
    def _round_value(key: str, raw: float) -> int:
        if key == "hdg":
            # Auto-detect radians vs degrees; some bindings expose radians for *_DEGREES_* vars.
            # Treat as radians when within ~[0, 2π+ε].
            if -0.1 <= raw <= (2 * math.pi + 0.1):
                raw_deg = math.degrees(raw)
            else:
                raw_deg = raw
            return int(round(raw_deg)) % 360  # normalize
        return int(round(raw))

    def run(self):
        self.prev = {}
        while not self.stop_event.is_set():
            curr: dict[str, int] = {}
            for key in self.selected:
                raw = self._get_raw(key)
                if raw is None:
                    continue
                val = self._round_value(key, raw)
                curr[key] = val
                self._log("msfs", f"MSFS {key}={val}")

            if curr:
                changed = False
                for k, v in curr.items():
                    if k not in self.prev:
                        changed = True
                        break
                    if abs(v - self.prev[k]) >= abs(int(self.dead_bands.get(k, 0))):
                        changed = True
                        break

                if changed:
                    line = json.dumps(curr, separators=(",", ":")) + "\n"
                    try:
                        self.ser.write(line.encode("ascii"))
                        self._log("tx", f"TX: {line.strip()}")
                        self.prev = curr
                    except Exception as e:
                        self.log_q.put(f"Write error: {e}")
                        break
            else:
                self._log("msfs", "MSFS: No data (SIM?).")

            time.sleep(self.rate_limit)


class SerialReader:
    """Background serial RX thread: reads lines from Serial and pushes them to the GUI."""
    def __init__(self, ser: serial.Serial, debug: DebugConfig):
        self.ser = ser
        self.debug = debug
        self.stop_event = threading.Event()
        self._buf = bytearray()

    def _log(self, kind: str, msg: str, log_q: queue.Queue):
        flags = self.debug.get()
        if kind == "rx" and flags["rx"]:
            log_q.put(msg)

    def run(self, log_q: queue.Queue, latest_rx_q: queue.Queue):
        while not self.stop_event.is_set():
            try:
                chunk = self.ser.read(256)
            except Exception as e:
                log_q.put(f"Read error: {e}")
                break

            if chunk:
                self._buf.extend(chunk)
                while True:
                    nl = self._buf.find(b'\n')
                    if nl == -1:
                        break
                    line = self._buf[:nl].rstrip(b'\r')
                    del self._buf[:nl+1]
                    try:
                        text = line.decode('utf-8', errors='replace')
                    except Exception:
                        text = repr(line)
                    self._log("rx", f"RX: {text}", log_q)
                    latest_rx_q.put(text)
            time.sleep(0.005)


class SerialGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("MSFS Serial JSON Streamer")
        self.geometry("880x560")

        # Serial state
        self.ser = None

        # Debug flags (shared across threads)
        self.debug = DebugConfig(rx=False, tx=True, msfs=False)

        # Serial RX thread
        self.rx_worker = None
        self.rx_thread = None

        # SimConnect state
        self.sm = None
        self.aq = None

        # Stream worker
        self.worker = None
        self.worker_thread = None

        # Queues
        self.log_q = queue.Queue()
        self.latest_rx_q = queue.Queue()

        # UI state
        self.sim_var = tk.StringVar(value="DISCONNECTED")
        self.ser_var = tk.StringVar(value="DISCONNECTED")
        self.latest_rx_var = tk.StringVar(value="—")

        # Field selection + dead-bands
        self.sel_hdg = tk.BooleanVar(value=False)
        self.sel_vs  = tk.BooleanVar(value=True)
        self.sel_spd = tk.BooleanVar(value=False)
        self.sel_alt = tk.BooleanVar(value=False)

        self.db_hdg = tk.StringVar(value="1")
        self.db_vs  = tk.StringVar(value="10")
        self.db_spd = tk.StringVar(value="1")
        self.db_alt = tk.StringVar(value="10")

        # Debug checkboxes UI state
        self.dbg_rx   = tk.BooleanVar(value=False)
        self.dbg_tx   = tk.BooleanVar(value=True)
        self.dbg_msfs = tk.BooleanVar(value=False)

        # Rate limit
        self.rate_var = tk.StringVar(value="0.02")

        self._build_ui()
        self._pump_logs()
        self._pump_latest_rx()

    def _build_ui(self):
        frm = ttk.Frame(self, padding=10)
        frm.pack(fill="both", expand=True)

        # Row 0: Serial Port selector + Refresh
        ttk.Label(frm, text="Serial Port:").grid(row=0, column=0, sticky="w")
        self.port_cmb = ttk.Combobox(frm, width=24, state="readonly", values=self._list_ports())
        self.port_cmb.grid(row=0, column=1, sticky="w")
        ttk.Button(frm, text="Refresh", command=self._refresh_ports).grid(row=0, column=2, padx=6)

        # Row 1: Baud + Timeout + Connect/Disconnect Serial + Serial status
        ttk.Label(frm, text="Baud:").grid(row=1, column=0, sticky="w")
        self.baud_var = tk.StringVar(value="115200")
        ttk.Entry(frm, textvariable=self.baud_var, width=12).grid(row=1, column=1, sticky="w")

        ttk.Label(frm, text="Read timeout (s):").grid(row=1, column=2, sticky="e")
        self.to_var = tk.StringVar(value="0")
        ttk.Entry(frm, textvariable=self.to_var, width=8).grid(row=1, column=3, sticky="w")

        self.conn_btn = ttk.Button(frm, text="Connect Serial", command=self._connect_serial)
        self.conn_btn.grid(row=1, column=4, padx=8)
        self.disc_btn = ttk.Button(frm, text="Disconnect Serial", command=self._disconnect_serial, state="disabled")
        self.disc_btn.grid(row=1, column=5)

        self.ser_lbl = tk.Label(frm, textvariable=self.ser_var, width=14, anchor="w")
        self.ser_lbl.grid(row=1, column=6, padx=(8,0), sticky="w")
        self._update_ser_label_color()

        # Row 2: SimConnect controls + status
        ttk.Separator(frm).grid(row=2, column=0, columnspan=7, sticky="ew", pady=8)

        self.sim_btn = ttk.Button(frm, text="Connect Sim", command=self._connect_sim, state=("normal" if USE_SIMCONNECT else "disabled"))
        self.sim_btn.grid(row=3, column=0, sticky="w")

        self.sim_disc_btn = ttk.Button(frm, text="Disconnect Sim", command=self._disconnect_sim, state="disabled")
        self.sim_disc_btn.grid(row=3, column=1, sticky="w", padx=(6,0))

        self.sim_lbl = tk.Label(frm, textvariable=self.sim_var, width=14, anchor="w")
        self.sim_lbl.grid(row=3, column=2, sticky="w", padx=(12,0))
        self._update_sim_label_color()

        if not USE_SIMCONNECT:
            ttk.Label(frm, text="SimConnect module not found: install 'SimConnect' for Python.", foreground="red").grid(row=3, column=3, columnspan=4, sticky="w")

        # Row 3: Stream settings + Latest RX
        ttk.Label(frm, text="Rate limit (s):").grid(row=4, column=0, sticky="w", pady=(8,0))
        ttk.Entry(frm, textvariable=self.rate_var, width=10).grid(row=4, column=1, sticky="w", pady=(8,0))

        ttk.Label(frm, text="Latest RX:").grid(row=4, column=4, sticky="e", pady=(8,0))
        tk.Label(frm, textvariable=self.latest_rx_var, width=34, anchor="w").grid(row=4, column=5, columnspan=2, sticky="w", pady=(8,0))

        # Row 4: Field selection + dead-bands
        fld = ttk.LabelFrame(frm, text="Fields to send (JSON) & Dead-bands")
        fld.grid(row=5, column=0, columnspan=7, sticky="ew", pady=(8,0))
        # hdg
        ttk.Checkbutton(fld, text="hdg (°)", variable=self.sel_hdg, command=self._sync_debug_flags).grid(row=0, column=0, sticky="w", padx=6)
        ttk.Label(fld, text="db:").grid(row=0, column=1, sticky="e")
        ttk.Entry(fld, textvariable=self.db_hdg, width=6).grid(row=0, column=2, sticky="w")
        # vs
        ttk.Checkbutton(fld, text="vs (fpm)", variable=self.sel_vs, command=self._sync_debug_flags).grid(row=0, column=3, sticky="w", padx=(18,6))
        ttk.Label(fld, text="db:").grid(row=0, column=4, sticky="e")
        ttk.Entry(fld, textvariable=self.db_vs, width=6).grid(row=0, column=5, sticky="w")
        # spd
        ttk.Checkbutton(fld, text="spd (kt)", variable=self.sel_spd, command=self._sync_debug_flags).grid(row=0, column=6, sticky="w", padx=(18,6))
        ttk.Label(fld, text="db:").grid(row=0, column=7, sticky="e")
        ttk.Entry(fld, textvariable=self.db_spd, width=6).grid(row=0, column=8, sticky="w")
        # alt
        ttk.Checkbutton(fld, text="alt (ft)", variable=self.sel_alt, command=self._sync_debug_flags).grid(row=0, column=9, sticky="w", padx=(18,6))
        ttk.Label(fld, text="db:").grid(row=0, column=10, sticky="e")
        ttk.Entry(fld, textvariable=self.db_alt, width=6).grid(row=0, column=11, sticky="w")

        # Row 5: Debug options
        dbg = ttk.LabelFrame(frm, text="Debug")
        dbg.grid(row=6, column=0, columnspan=7, sticky="ew", pady=(8,0))
        ttk.Checkbutton(dbg, text="RX from serial", variable=self.dbg_rx, command=self._sync_debug_flags).grid(row=0, column=0, sticky="w", padx=6)
        ttk.Checkbutton(dbg, text="TX to serial", variable=self.dbg_tx, command=self._sync_debug_flags).grid(row=0, column=1, sticky="w", padx=6)
        ttk.Checkbutton(dbg, text="MSFS data", variable=self.dbg_msfs, command=self._sync_debug_flags).grid(row=0, column=2, sticky="w", padx=6)

        # Row 6: Start/Stop streaming
        self.start_btn = ttk.Button(frm, text="Start Streaming", command=self._start_stream, state="disabled")
        self.start_btn.grid(row=7, column=0, pady=10, sticky="w")
        self.stop_btn = ttk.Button(frm, text="Stop Streaming", command=self._stop_stream, state="disabled")
        self.stop_btn.grid(row=7, column=1, pady=10, sticky="w")

        # Row 7+: Log box
        self.log = tk.Text(frm, height=14, width=110, state="disabled")
        self.log.grid(row=8, column=0, columnspan=7, pady=(4, 0), sticky="nsew")

        for c in range(7):
            frm.grid_columnconfigure(c, weight=1)
        frm.grid_rowconfigure(8, weight=1)

        self._sync_debug_flags()

    # ---- Helpers -------------------------------------------------------------
    def _update_sim_label_color(self):
        self.sim_lbl.configure(fg=("green" if self.sim_var.get() == "CONNECTED" else "red"))

    def _update_ser_label_color(self):
        self.ser_lbl.configure(fg=("green" if self.ser_var.get() == "CONNECTED" else "red"))

    def _list_ports(self):
        return [p.device for p in list_ports.comports()]

    def _refresh_ports(self):
        self.port_cmb["values"] = self._list_ports()
        if not self.port_cmb.get() and self.port_cmb["values"]:
            self.port_cmb.current(0)

    def _append_log(self, line):
        self.log.configure(state="normal")
        self.log.insert("end", line + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def _pump_logs(self):
        while True:
            try:
                line = self.log_q.get_nowait()
            except queue.Empty:
                break
            else:
                self._append_log(line)
        self.after(50, self._pump_logs)

    def _pump_latest_rx(self):
        while True:
            try:
                text = self.latest_rx_q.get_nowait()
            except queue.Empty:
                break
            else:
                self.latest_rx_var.set(text)
        self.after(60, self._pump_latest_rx)

    def _update_start_enabled(self):
        enable = (self.ser and self.ser.is_open and self.aq is not None)
        self.start_btn.configure(state=("normal" if enable else "disabled"))

    def _sync_debug_flags(self):
        self.debug.update(rx=self.dbg_rx.get(), tx=self.dbg_tx.get(), msfs=self.dbg_msfs.get())

    # ---- Serial connect/disconnect ------------------------------------------
    def _connect_serial(self):
        port = self.port_cmb.get()
        if not port:
            messagebox.showwarning("Select a port", "Please select a serial port.")
            return
        try:
            baud = int(self.baud_var.get())
            to = float(self.to_var.get())
        except ValueError:
            messagebox.showerror("Invalid settings", "Baud and timeout must be numbers.")
            return

        try:
            self.ser = serial.Serial(port, baudrate=baud, timeout=to, write_timeout=None)
            self._append_log(f"Serial: Connected to {port} @ {baud} baud (timeout={to})")
            self.ser_var.set("CONNECTED")
            self._update_ser_label_color()
        except Exception as e:
            messagebox.showerror("Serial connection failed", str(e))
            return

        self.rx_worker = SerialReader(self.ser, self.debug)
        self.rx_thread = threading.Thread(target=self.rx_worker.run, args=(self.log_q, self.latest_rx_q), daemon=True)
        self.rx_thread.start()
        self._append_log("Serial RX: Started.")

        self.conn_btn.configure(state="disabled")
        self.disc_btn.configure(state="normal")
        self._update_start_enabled()

    def _disconnect_serial(self):
        self._stop_stream()

        if self.rx_worker:
            self.rx_worker.stop_event.set()
            self.rx_worker = None
        if self.rx_thread:
            self.rx_thread.join(timeout=1.0)
            self.rx_thread = None
        self._append_log("Serial RX: Stopped.")

        if self.ser:
            try:
                self.ser.close()
            except Exception:
                pass
            self._append_log("Serial: Disconnected.")
            self.ser = None
        self.ser_var.set("DISCONNECTED")
        self._update_ser_label_color()

        self.conn_btn.configure(state="normal")
        self.disc_btn.configure(state="disabled")
        self._update_start_enabled()

    # ---- SimConnect connect/disconnect --------------------------------------
    def _connect_sim(self):
        if not USE_SIMCONNECT:
            messagebox.showerror("SimConnect not available", "Install the 'SimConnect' Python package.")
            return
        try:
            if self.aq is not None:
                return
            self.sm = SimConnect()
            self.aq = AircraftRequests(self.sm, _time=0)
            try:
                _ = self.aq.get("SIM_ON_GROUND")
            except Exception:
                pass
            self._append_log("Sim: Connected to MSFS via SimConnect.")
            self.sim_var.set("CONNECTED")
            self._update_sim_label_color()
            self.sim_btn.configure(state="disabled")
            self.sim_disc_btn.configure(state="normal")
            self._update_start_enabled()
        except Exception as e:
            self._append_log(f"Sim: Connect failed: {e}")
            messagebox.showerror("SimConnect connection failed", str(e))
            self.sim_var.set("DISCONNECTED")
            self._update_sim_label_color()
            self._update_start_enabled()

    def _disconnect_sim(self):
        self._stop_stream()
        if self.sm is not None:
            try:
                self.sm.exit()
            except Exception:
                pass
        self.sm = None
        self.aq = None
        self._append_log("Sim: Disconnected.")
        self.sim_var.set("DISCONNECTED")
        self._update_sim_label_color()
        self.sim_btn.configure(state=("normal" if USE_SIMCONNECT else "disabled"))
        self.sim_disc_btn.configure(state="disabled")
        self._update_start_enabled()

    # ---- Streaming control ---------------------------------------------------
    def _start_stream(self):
        if not (self.ser and self.ser.is_open):
            messagebox.showwarning("Not connected", "Open a serial connection first.")
            return
        if self.aq is None:
            messagebox.showwarning("Sim not connected", "Connect SimConnect first.")
            return

        selected = {k for k, v in {
            "hdg": self.sel_hdg.get(),
            "vs":  self.sel_vs.get(),
            "spd": self.sel_spd.get(),
            "alt": self.sel_alt.get(),
        }.items() if v}
        if not selected:
            messagebox.showwarning("Nothing selected", "Select at least one field to send (hdg/vs/spd/alt).")
            return

        try:
            rate = float(self.rate_var.get())
            dead_bands = {
                "hdg": int(self.db_hdg.get()),
                "vs":  int(self.db_vs.get()),
                "spd": int(self.db_spd.get()),
                "alt": int(self.db_alt.get()),
            }
        except ValueError:
            messagebox.showerror("Invalid settings", "Rate must be float; dead-bands must be integers.")
            return

        self.worker = DataStreamer(
            ser=self.ser,
            aq=self.aq,
            rate_limit=rate,
            dead_bands=dead_bands,
            selected_keys=selected,
            debug=self.debug,
            log_q=self.log_q,
        )
        self.worker_thread = threading.Thread(target=self.worker.run, daemon=True)
        self.worker_thread.start()
        self._append_log(f"Streaming: Started. Fields={sorted(selected)}, DB={dead_bands}, rate={rate}s")
        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")

    def _stop_stream(self):
        if self.worker:
            self.worker.stop_event.set()
            self.worker = None
        if self.worker_thread:
            self.worker_thread.join(timeout=1.0)
            self.worker_thread = None
        self._append_log("Streaming: Stopped.")
        self.stop_btn.configure(state="disabled")
        self._update_start_enabled()


if __name__ == "__main__":
    app = SerialGUI()
    app.mainloop()
