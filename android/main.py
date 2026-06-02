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
        self._cards_busy = False
        self._cards_ev = None

    # ── UI ──────────────────────────────────────────────────
    def build(self):
        Window.clearcolor = (0.04, 0.05, 0.07, 1)  # dark premium telecom theme
        root = BoxLayout(orientation="vertical", padding=dp(8), spacing=dp(6))

        title = Label(text="[b][color=33ccff]AYED NETWORK MASTER PRO[/color][/b]\n"
                           "[size=11][color=8899aa]by Ayed Oraybi · H155/H115 Control Center[/color][/size]",
                      markup=True, halign="center", size_hint_y=None, height=dp(46), font_size="18sp")
        root.add_widget(title)

        # Live mini-cards (updated every 2s once connected) — real router data
        self.cards = Label(
            text="[b]DL[/b] -   [b]UL[/b] -   [b]Ping[/b] -   [b]RSRP[/b] -   [b]Band[/b] -",
            markup=True, size_hint_y=None, height=dp(30), font_size="13sp",
            color=(0.6, 0.95, 0.8, 1))
        root.add_widget(self.cards)

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
        grid = GridLayout(cols=2, size_hint_y=None, height=dp(244), spacing=dp(4))
        for label, cb in (
            ("Diagnose Login", self.on_diagnostics),
            ("Status", self.on_status),
            ("Auto-Tune", self.on_autotune),
            ("Best CA (4G+4G)", self.on_best_ca),
            ("Enable 5G (EN-DC)", self.on_enable_5g),
            ("Best Tower", self.on_best_tower),
            ("Speed Test", self.on_speedtest),
            ("Devices", self.on_devices),
            ("Reconnect", self.on_reconnect),
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

        # Log tools row
        tools = GridLayout(cols=3, size_hint_y=None, height=dp(44), spacing=dp(4))
        for label, cb in (("Copy Log", self.on_copy_log),
                          ("Save Log", self.on_save_log),
                          ("Clear Log", self.on_clear_log)):
            b = Button(text=label, background_color=(0.18, 0.22, 0.30, 1))
            b.bind(on_release=cb)
            tools.add_widget(b)
        root.add_widget(tools)

        if not ENGINE_OK:
            self.put("ENGINE IMPORT FAILED:\n" + ENGINE_ERR +
                     "\nThe build did not include engine.py correctly.")
        else:
            # Tee the engine's log helpers into the on-screen log so read
            # failures (e.g. "Library signal read failed: ...") are visible.
            import re as _re
            _ansi = _re.compile(r"\x1b\[[0-9;]*m")

            def _mklog(tag):
                def _fn(msg=""):
                    self.put("[%s] %s" % (tag, _ansi.sub("", str(msg))))
                return _fn
            engine.warn = _mklog("warn")
            engine.err = _mklog("err")
            engine.info = _mklog("info")
            lib_state = "available" if getattr(engine, "HUAWEI_LIB", False) else "NOT installed (manual login)"
            self.put("Ready. huawei-lte-api: " + lib_state)
            self.put("Enter the router admin password and tap Connect.\n"
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
                Clock.schedule_once(lambda dt: self._start_cards(), 0)
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
            # 5G NR line only when the modem actually reports NR
            if sig.get("nrrsrp_int") is not None or str(sig.get("nrband", "N/A")) not in ("N/A", ""):
                lines.append("5G NR     : band %s  RSRP %s  SINR %s" % (
                    sig.get("nrband", "?"), sig.get("nrrsrp", "?"), sig.get("nrsinr", "?")))
            self.put("\n".join(lines))
        self.run_bg(work)

    def on_enable_5g(self, *_):
        if not self.require_session():
            return

        def work():
            self.put("Enabling 5G (auto NSA mode — also clears any LTE-only lock that blocks 5G)...")
            okk = engine.enable_endc(self.sess, nr_bands=[40, 41, 78])
            self.put("Mode set ✔" if okk else "Router rejected the mode change.")
            engine.time.sleep(6)
            # NSA attaches the NR carrier only under load — push a quick download.
            self.put("Triggering NR leg with a short download...")
            engine.measure_download_mbps(15)
            engine.time.sleep(2)
            sig = self.sess.get_signal()
            nrp = sig.get("nrrsrp_int")
            band = str(sig.get("nrband", "N/A"))
            attached = band not in ("N/A", "", "0") or "NR" in str(sig.get("band", "")).upper()
            if attached:
                self.put("✔ 5G NR AGGREGATED — band %s, RSRP %s" % (band, sig.get("nrrsrp", "?")))
            elif nrp is not None:
                self.put("5G cell IN RANGE (NR RSRP %s) but not aggregated yet — "
                         "NSA adds it under heavy load. Try a big download/Speed Test." % sig.get("nrrsrp", "?"))
            else:
                self.put("No NR signal right now (no 5G coverage on n40/n41/n78 here, or SIM not 5G).")
            self.on_status()
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

    def on_diagnostics(self, *_):
        # Dumps raw firmware responses so we can see the exact login/encryption
        # scheme. Works WITHOUT a successful login (uses a fresh token only).
        gw = self.gw.text.strip() or "192.168.8.1"

        def work():
            s = engine.H155Session(gateway=gw)
            try:
                s._get_token()
            except Exception:
                pass
            self.put("══════ LOGIN DIAGNOSTICS ══════")
            self.put("(copy this whole block and send it)")
            endpoints = [
                ("SesTokInfo", "/api/webserver/SesTokInfo"),
                ("state-login", "/api/user/state-login"),
                ("publickey", "/api/webserver/publickey"),
                ("device-info", "/api/device/information"),
                ("signal", "/api/device/signal"),
            ]
            for label, ep in endpoints:
                try:
                    r = s.session.get(s.base_url + ep, timeout=8)
                    body = " ".join(r.text.split())
                    self.put("[%s] (%d) %s" % (label, r.status_code, body[:500]))
                except Exception as e:
                    self.put("[%s] ERROR %r" % (label, e))
            self.put("══════ END DIAGNOSTICS ══════")
        self.run_bg(work)

    def on_devices(self, *_):
        if not self.require_session():
            return

        def work():
            hosts = engine.parse_hosts(self.sess)
            if not hosts:
                self.put("No connected devices reported by the router.")
                return
            eth = sum(1 for h in hosts if h.get("via") == "Ethernet")
            wifi = len(hosts) - eth
            self.put("── CONNECTED DEVICES (%d: %d Ethernet, %d Wi-Fi) ──" % (len(hosts), eth, wifi))
            for h in hosts:
                tag = "" if h.get("active") else " (idle)"
                self.put("[%s] %-15s %s  %s%s" % (h.get("via", "?")[:4], h.get("ip", "?"),
                                                  h.get("mac", "?"), h.get("name", "?"), tag))
        self.run_bg(work)

    def on_reconnect(self, *_):
        if not self.require_session():
            return

        def work():
            self.put("Reconnecting mobile data...")
            ep = engine.EP["data_switch"]
            self.sess.api_post(ep, {"dataswitch": "0"})
            engine.time.sleep(2)
            self.sess.api_post(ep, {"dataswitch": "1"})
            self.put("Reconnect signal sent.")
        self.run_bg(work)

    # ── log tools ───────────────────────────────────────────
    def on_copy_log(self, *_):
        try:
            from kivy.core.clipboard import Clipboard
            Clipboard.copy(self.log.text)
            self.put("Log copied to clipboard.")
        except Exception as e:
            self.put("Copy failed: %r" % e)

    def on_save_log(self, *_):
        import os
        try:
            from android.storage import primary_external_storage_path
            base = primary_external_storage_path() + "/Download"
        except Exception:
            base = "/sdcard/Download"
        try:
            os.makedirs(base, exist_ok=True)
            path = "%s/ayed_netmaster_%s.txt" % (base, time.strftime("%Y%m%d_%H%M%S"))
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.log.text)
            self.put("Saved log → " + path)
        except Exception as e:
            self.put("Save failed: %r" % e)

    def on_clear_log(self, *_):
        self.log.text = ""

    # ── live mini-cards (real router data, every 2.5s) ──────
    def _start_cards(self):
        if self._cards_ev is None:
            self._cards_ev = Clock.schedule_interval(lambda dt: self._refresh_cards(), 2.5)

    def _refresh_cards(self):
        if self.sess is None or self._cards_busy:
            return
        self._cards_busy = True

        def work():
            txt = self.cards.text
            try:
                sig = self.sess.get_signal()
                mon = self.sess.get_monitoring()
                dl = engine.speed_fmt(mon.get("dl_speed", "0"))
                ul = engine.speed_fmt(mon.get("ul_speed", "0"))
                rsrp = sig.get("rsrp", "-")
                band = sig.get("band", "-")
                txt = ("[b]DL[/b] %s   [b]UL[/b] %s   [b]RSRP[/b] %s   [b]Band[/b] %s"
                       % (dl, ul, rsrp, band))
            except Exception:
                pass
            finally:
                self._cards_busy = False
            Clock.schedule_once(lambda dt: setattr(self.cards, "text", txt), 0)
        threading.Thread(target=work, daemon=True).start()

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
        unreach = 0
        while self.ap_running:
            cycles += 1
            try:
                ctx.snap = engine._snapshot(sess)
            except Exception:
                ctx.snap = {}
            snap = ctx.snap or {}
            # ── Reachability gate: if the router can't be read (usually a phone
            #    Wi-Fi blip on a stationary router), DON'T run tactics — that would
            #    needlessly toggle data / storm logins. Back off and re-check.
            reachable = bool(snap) and (snap.get("rsrp") is not None or snap.get("connected"))
            if not reachable:
                unreach += 1
                self.set_status_line("AP#%d  router unreachable — backing off (x%d)" % (cycles, unreach))
                wait = min(self.interval * (1 + unreach), 120)
                for _ in range(int(wait)):
                    if not self.ap_running:
                        break
                    engine.time.sleep(1)
                continue
            unreach = 0
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
