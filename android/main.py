#!/usr/bin/env python3
"""
Zain H155 Manager — Android (Kivy) front-end.

This is a touch GUI wrapper around the SAME optimization engine used by the
command-line tool (`zain_h155_manager.py`, copied to `engine.py` at build
time). It reuses the real H155Session, the smart-autopilot tactic engine and
all helper functions — only the presentation layer is new.

Android note: stock Android blocks raw `ping`/`traceroute` from the app
sandbox, so we monkey-patch the engine's latency probe with a socket
(TCP-connect) measurement that works without root. MTU/traceroute tactics
that rely on the `ping` binary simply no-op (the engine already handles that
gracefully).
"""

import threading
import socket
import time
from functools import partial

from kivy.app import App
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.core.window import Window
from kivy.metrics import dp

# ── Import the shared engine (copied next to this file at build time) ──
try:
    import engine
    ENGINE_OK = True
    ENGINE_ERR = ""
except Exception as e:          # pragma: no cover - only on broken builds
    ENGINE_OK = False
    ENGINE_ERR = repr(e)


# ── Android-safe latency: TCP connect time (no ping binary needed) ──
def android_latency_ms(host="1.1.1.1", count=3, port=443):
    samples = []
    for _ in range(max(1, count)):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2.0)
        try:
            t0 = time.time()
            s.connect((host, port))
            samples.append((time.time() - t0) * 1000.0)
        except OSError:
            pass
        finally:
            s.close()
    return sum(samples) / len(samples) if samples else None


if ENGINE_OK:
    # Route every latency probe in the engine through the socket method so the
    # latency / jitter / dead-link / DNS tactics work on Android.
    engine.measure_latency_ms = android_latency_ms


Window.softinput_mode = "below_target"


class H155App(App):
    title = "Zain H155 Manager"

    def __init__(self, **kw):
        super().__init__(**kw)
        self.sess = None
        self.ap_running = False
        self.ap_thread = None
        self.interval = 20

    # ── UI ──────────────────────────────────────────────────
    def build(self):
        root = BoxLayout(orientation="vertical", padding=dp(8), spacing=dp(6))

        title = Label(text="[b]Zain H155 Manager[/b]  v40.4", markup=True,
                      size_hint_y=None, height=dp(30), font_size="18sp")
        root.add_widget(title)

        # Connection row
        conn = GridLayout(cols=2, size_hint_y=None, height=dp(96), spacing=dp(4))
        conn.add_widget(Label(text="Gateway", size_hint_x=0.35))
        self.gw = TextInput(text="192.168.8.1", multiline=False)
        conn.add_widget(self.gw)
        conn.add_widget(Label(text="Password", size_hint_x=0.35))
        self.pw = TextInput(text="", password=True, multiline=False)
        conn.add_widget(self.pw)
        root.add_widget(conn)

        self.connect_btn = Button(text="Connect", size_hint_y=None, height=dp(46),
                                  background_color=(0.16, 0.55, 0.30, 1))
        self.connect_btn.bind(on_release=self.on_connect)
        root.add_widget(self.connect_btn)

        # Action buttons
        grid = GridLayout(cols=2, size_hint_y=None, height=dp(150), spacing=dp(4))
        for label, cb in (
            ("Status", self.on_status),
            ("Auto-Tune", self.on_autotune),
            ("Best CA (4G+4G)", self.on_best_ca),
            ("Best Tower", self.on_best_tower),
            ("Speed Test", self.on_speedtest),
            ("Reboot", self.on_reboot),
        ):
            b = Button(text=label)
            b.bind(on_release=cb)
            grid.add_widget(b)
        root.add_widget(grid)

        # Autopilot toggle
        self.ap_btn = Button(text="▶ START SMART AUTOPILOT", size_hint_y=None,
                             height=dp(52), background_color=(0.10, 0.40, 0.75, 1))
        self.ap_btn.bind(on_release=self.on_toggle_autopilot)
        root.add_widget(self.ap_btn)

        # Log area
        self.log = TextInput(text="", readonly=True, font_size="12sp",
                             background_color=(0.07, 0.08, 0.10, 1),
                             foreground_color=(0.85, 0.9, 0.85, 1))
        sv = ScrollView()
        sv.add_widget(self.log)
        # let the TextInput grow so ScrollView can scroll
        self.log.size_hint_y = None
        self.log.bind(minimum_height=self.log.setter("height"))
        root.add_widget(sv)

        if not ENGINE_OK:
            self.put("ENGINE IMPORT FAILED:\n" + ENGINE_ERR +
                     "\nThe build did not include engine.py correctly.")
        else:
            self.put("Ready. Enter the router admin password and tap Connect.\n"
                     "Tip: connect this phone to the router's Wi-Fi first.")
        return root

    # ── logging (thread-safe) ───────────────────────────────
    def put(self, text):
        Clock.schedule_once(partial(self._append, text), 0)

    def _append(self, text, *_):
        stamp = time.strftime("%H:%M:%S")
        self.log.text += f"[{stamp}] {text}\n"

    def set_status_line(self, text):
        # one-line live status for autopilot (replaces previous line)
        Clock.schedule_once(partial(self._status, text), 0)

    def _status(self, text, *_):
        self.log.text += text + "\n"

    # ── background helper ───────────────────────────────────
    def run_bg(self, fn):
        threading.Thread(target=self._guard, args=(fn,), daemon=True).start()

    def _guard(self, fn):
        try:
            fn()
        except Exception as e:
            self.put("Error: %r" % e)

    def require_session(self):
        if self.sess is None:
            self.put("Not connected — tap Connect first.")
            return False
        return True

    # ── actions ─────────────────────────────────────────────
    def on_connect(self, *_):
        if not ENGINE_OK:
            return
        gw = self.gw.text.strip() or "192.168.8.1"
        pw = self.pw.text
        self.put("Connecting to %s ..." % gw)

        def work():
            sess = engine.H155Session(gateway=gw)
            ok = sess.connect(pw)
            if ok:
                self.sess = sess
                self.put("Authenticated ✔")
                self.on_status()
            else:
                self.put("Login failed — check the admin password.")
        self.run_bg(work)

    def on_status(self, *_):
        if not self.require_session():
            return

        def work():
            s = self.sess
            dev = s.get_device_info()
            mon = s.get_monitoring()
            sig = s.get_signal()
            agg = engine.active_ca_bands(s)
            wan = dev.get("wan_ip", "N/A")
            wk = engine.classify_wan_ip(wan)[0]
            conn = mon.get("connection_status", "0") == "901"
            lines = [
                "── STATUS ──",
                "Model     : %s  (SW %s)" % (dev.get("model", "?"), dev.get("software", "?")),
                "Connected : %s   Type: %s" % ("UP" if conn else "DOWN",
                                               engine.network_type_name(mon.get("network_type", "0"))),
                "RSRP/SINR : %s / %s" % (sig.get("rsrp", "?"), sig.get("sinr", "?")),
                "Band/CA   : %s  (%dCC)" % ("+".join("B" + str(b) for b in agg) or sig.get("band", "?"), len(agg)),
                "PCI/EARFCN: %s / %s" % (sig.get("pci", "?"), sig.get("earfcn", "?")),
                "WAN IP    : %s  (%s)" % (wan, wk),
            ]
            self.put("\n".join(lines))
        self.run_bg(work)

    def on_autotune(self, *_):
        if not self.require_session():
            return

        def work():
            self.put("Auto-tuning (best CA/5G)...")
            acts = engine._optimize_now(self.sess, "auto", True)
            self.put("Auto-tune: " + (", ".join(acts) if acts else "already optimal"))
            self.on_status()
        self.run_bg(work)

    def on_best_ca(self, *_):
        if not self.require_session():
            return

        def work():
            strong, _ = engine._strong_bands(self.sess)
            if len(strong) >= 2:
                engine.lock_bands(self.sess, strong[:4])
                self.put("Locked CA: " + "+".join("B" + str(b) for b in strong[:4]))
            elif strong:
                engine.lock_bands(self.sess, strong[:1])
                self.put("Single strong band: B%d" % strong[0])
            else:
                self.put("No strong bands visible (scan needs LTE + data).")
            self.on_status()
        self.run_bg(work)

    def on_best_tower(self, *_):
        if not self.require_session():
            return

        def work():
            towers = engine.visible_towers(self.sess)
            if not towers:
                self.put("No towers visible.")
                return
            best = max(towers, key=lambda t: t["rsrp_int"])
            import re
            d = re.sub(r"[^\d]", "", best["band"])
            if d:
                engine.lock_bands(self.sess, [int(d)])
                self.put("Locked toward best tower PCI %s on B%s (RSRP %s)"
                         % (best["pci"], d, best["rsrp"]))
            self.on_status()
        self.run_bg(work)

    def on_speedtest(self, *_):
        def work():
            self.put("Download test...")
            dl = engine.measure_download_mbps(10)
            self.put("Upload test...")
            ul = engine.measure_upload_mbps(5)
            lat = android_latency_ms()
            self.put("Speed: ↓ %s Mbps   ↑ %s Mbps   ping %s ms" % (
                ("%.1f" % dl) if dl else "?",
                ("%.1f" % ul) if ul else "?",
                ("%.0f" % lat) if lat else "?"))
        self.run_bg(work)

    def on_reboot(self, *_):
        if not self.require_session():
            return

        def work():
            if self.sess.reboot():
                self.put("Reboot command sent — router offline ~60s.")
            else:
                self.put("Reboot failed.")
        self.run_bg(work)

    # ── autopilot ───────────────────────────────────────────
    def on_toggle_autopilot(self, *_):
        if not self.require_session():
            return
        if self.ap_running:
            self.ap_running = False
            self.ap_btn.text = "▶ START SMART AUTOPILOT"
            self.ap_btn.background_color = (0.10, 0.40, 0.75, 1)
            self.put("Autopilot stopping...")
        else:
            self.ap_running = True
            self.ap_btn.text = "■ STOP AUTOPILOT"
            self.ap_btn.background_color = (0.70, 0.20, 0.20, 1)
            self.ap_thread = threading.Thread(target=self._autopilot_loop, daemon=True)
            self.ap_thread.start()

    def _autopilot_loop(self):
        from types import SimpleNamespace
        sess = self.sess
        args = SimpleNamespace(mode="auto", threshold=-108, no_5g=False, no_wan=False)
        ctx = engine.SmartCtx(sess, args)
        now = engine.time.monotonic()
        for key, _fn, _cad in engine.SMART_TACTICS:
            if key in engine._HEAVY_TACTICS:
                ctx.last[key] = now
        try:
            acts = engine._optimize_now(sess, ctx.mode, ctx.want_5g)
            self.put("AUTOPILOT init: " + (", ".join(acts) if acts else "already optimal"))
        except Exception as e:
            self.put("init err: %r" % e)
        ctx.mark_relock()

        cycles = 0
        while self.ap_running:
            cycles += 1
            try:
                ctx.snap = engine._snapshot(sess)
            except Exception:
                ctx.snap = {}
            acts = []
            for key, fn, cad in engine.SMART_TACTICS:
                if not ctx.due(key, cad):
                    continue
                try:
                    r = fn(sess, ctx)
                except Exception:
                    r = None
                if r:
                    acts.append(r)
            if acts:
                ctx.actions += len(acts)
            snap = ctx.snap or {}
            agg = snap.get("agg", []) or []
            line = ("AP#%d  %s  %dCC  RSRP %s  WAN %s  DL %s UL %s LAT %s  fix:%d%s"
                    % (cycles,
                       "UP" if snap.get("connected") else "DOWN",
                       len(agg),
                       snap.get("rsrp", "?"),
                       engine.classify_wan_ip(snap.get("wan", "N/A"))[0],
                       ("%.0f" % ctx.dl_last) if ctx.dl_last else "-",
                       ("%.0f" % ctx.ul_last) if ctx.ul_last else "-",
                       ("%.0f" % ctx.lat_last) if ctx.lat_last else "-",
                       ctx.actions,
                       ("  ←" + "; ".join(acts)) if acts else ""))
            self.set_status_line(line)
            for _ in range(int(self.interval)):
                if not self.ap_running:
                    break
                engine.time.sleep(1)
        self.put("Autopilot stopped after %d cycles, %d actions." % (cycles, ctx.actions))


if __name__ == "__main__":
    H155App().run()
