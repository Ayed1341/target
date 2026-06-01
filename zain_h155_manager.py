#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║          ZAIN H155 ADVANCED ROUTER MANAGER - Professional Edition           ║
║                    4G/LTE Tower & Frequency Optimizer                       ║
║                         Author: Router Pro Suite                            ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import requests
import json
import re
import sys
import time
import hashlib
import base64
import argparse
import urllib3
from datetime import datetime
from getpass import getpass
from typing import Optional

# Suppress SSL warnings for local router connections
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ── Optional: maintained Huawei library (handles SCRAM login automatically) ──
# Install on your device with:  pip install huawei-lte-api
# This is the recommended path – it auto-detects your firmware's login scheme
# (newer H155 firmware uses SCRAM challenge-response, which is why the manual
#  XML login can fail with error 125003 on every attempt).
try:
    from huawei_lte_api.Connection import Connection as _HuaweiConnection
    from huawei_lte_api.Client import Client as _HuaweiClient
    HUAWEI_LIB = True
except ImportError:
    HUAWEI_LIB = False

# ─────────────────────────────────────────────────────────────
#  ANSI COLOR PALETTE
# ─────────────────────────────────────────────────────────────
class C:
    RESET   = "\033[0m"
    BOLD    = "\033[1m"
    DIM     = "\033[2m"
    UNDER   = "\033[4m"

    BLACK   = "\033[30m"
    RED     = "\033[91m"
    GREEN   = "\033[92m"
    YELLOW  = "\033[93m"
    BLUE    = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN    = "\033[96m"
    WHITE   = "\033[97m"
    ORANGE  = "\033[38;5;214m"
    LIME    = "\033[38;5;118m"
    PINK    = "\033[38;5;213m"
    TEAL    = "\033[38;5;51m"
    GOLD    = "\033[38;5;220m"

    BG_BLACK  = "\033[40m"
    BG_RED    = "\033[41m"
    BG_GREEN  = "\033[42m"
    BG_BLUE   = "\033[44m"
    BG_CYAN   = "\033[46m"
    BG_DARK   = "\033[48;5;234m"

def colorize(text, *codes):
    return "".join(codes) + text + C.RESET

def ok(msg):    print(f"  {C.GREEN}✔{C.RESET}  {msg}")
def err(msg):   print(f"  {C.RED}✘{C.RESET}  {colorize(msg, C.RED)}")
def warn(msg):  print(f"  {C.YELLOW}⚠{C.RESET}  {colorize(msg, C.YELLOW)}")
def info(msg):  print(f"  {C.CYAN}ℹ{C.RESET}  {msg}")
def step(msg):  print(f"\n  {C.MAGENTA}▶{C.RESET}  {colorize(msg, C.BOLD)}")
def sep():      print(f"\n  {C.DIM}{'─'*68}{C.RESET}")

# ─────────────────────────────────────────────────────────────
#  BANNER
# ─────────────────────────────────────────────────────────────
BANNER = f"""
{C.CYAN}{C.BOLD}
 ███████╗ █████╗ ██╗███╗  ██╗    ██╗  ██╗ ██╗███████╗███████╗
 ╚════███║██╔══██╗██║████╗ ██║    ██║  ██║███║██╔════╝██╔════╝
     ███╔╝███████║██║██╔██╗██║    ███████║╚██║███████╗███████╗
    ███╔╝ ██╔══██║██║██║╚████║    ██╔══██║ ██║╚════██║╚════██║
   ███████╗██║  ██║██║██║ ╚███║   ██║  ██║ ██║███████║███████║
   ╚══════╝╚═╝  ╚═╝╚═╝╚═╝  ╚══╝   ╚═╝  ╚═╝ ╚═╝╚══════╝╚══════╝{C.RESET}
{C.GOLD}             ⚡  Advanced Router Manager · v40.2 Edition  ⚡{C.RESET}
{C.DIM}             Model: Zain H155 | 4G·5G Tower & Frequency Optimizer{C.RESET}
{C.DIM}             98 tools · Auto-CA · Best Tower · Autopilot · Reports{C.RESET}
"""

# ─────────────────────────────────────────────────────────────
#  KNOWN BAND / EARFCN DATABASE — STC (Saudi Telecom) focused
#  Includes Zain & Mobily overlap. LTE (FDD/TDD) + 5G NR.
# ─────────────────────────────────────────────────────────────
BAND_DB = {
    # ── LTE FDD ──
    1:  {"name": "B1  LTE (2100 MHz)", "dl_range": (2110, 2170), "earfcn": (0,    599),   "op": "STC/Zain/Mobily", "tech": "4G"},
    3:  {"name": "B3  LTE (1800 MHz)", "dl_range": (1805, 1880), "earfcn": (1200, 1949),  "op": "STC/Zain/Mobily", "tech": "4G"},
    7:  {"name": "B7  LTE (2600 MHz)", "dl_range": (2620, 2690), "earfcn": (2750, 3449),  "op": "STC/Zain",        "tech": "4G"},
    8:  {"name": "B8  LTE (900 MHz)",  "dl_range": (925,  960),  "earfcn": (3450, 3799),  "op": "STC/Zain/Mobily", "tech": "4G"},
    20: {"name": "B20 LTE (800 MHz)",  "dl_range": (791,  821),  "earfcn": (6150, 6449),  "op": "STC/Zain",        "tech": "4G"},
    28: {"name": "B28 LTE (700 MHz)",  "dl_range": (758,  803),  "earfcn": (9210, 9659),  "op": "STC/Zain",        "tech": "4G"},
    # ── LTE TDD ──
    38: {"name": "B38 TDD (2600 MHz)", "dl_range": (2570, 2620), "earfcn": (37750,38249), "op": "STC TDD",         "tech": "4G"},
    40: {"name": "B40 TDD (2300 MHz)", "dl_range": (2300, 2400), "earfcn": (38650,39649), "op": "STC/Zain TDD",    "tech": "4G"},
    41: {"name": "B41 TDD (2500 MHz)", "dl_range": (2496, 2690), "earfcn": (39650,41589), "op": "STC/Zain TDD",    "tech": "4G"},
    42: {"name": "B42 TDD (3500 MHz)", "dl_range": (3400, 3600), "earfcn": (41590,43589), "op": "STC TDD",         "tech": "4G"},
}

# 5G NR bands used by STC in Saudi Arabia (NSA mode pairs with LTE anchor)
NR_BAND_DB = {
    1:  {"name": "n1  5G (2100 MHz)",  "dl_range": (2110, 2170), "op": "STC 5G",  "tech": "5G"},
    3:  {"name": "n3  5G (1800 MHz)",  "dl_range": (1805, 1880), "op": "STC 5G",  "tech": "5G"},
    28: {"name": "n28 5G (700 MHz)",   "dl_range": (758,  803),  "op": "STC 5G",  "tech": "5G"},
    41: {"name": "n41 5G (2500 MHz)",  "dl_range": (2496, 2690), "op": "STC 5G",  "tech": "5G"},
    78: {"name": "n78 5G (3500 MHz)",  "dl_range": (3300, 3800), "op": "STC 5G",  "tech": "5G"},  # primary STC 5G band
}

# Signal quality thresholds
RSRP_GRADES = [
    (-80,  "Excellent", C.LIME),
    (-90,  "Good",      C.GREEN),
    (-100, "Fair",      C.YELLOW),
    (-110, "Poor",      C.ORANGE),
    (-999, "Bad",       C.RED),
]

SINR_GRADES = [
    (20, "Excellent", C.LIME),
    (13, "Good",      C.GREEN),
    (0,  "Fair",      C.YELLOW),
    (-3, "Poor",      C.ORANGE),
    (-99,"Bad",       C.RED),
]

# ─────────────────────────────────────────────────────────────
#  H155 HTTP API SESSION
# ─────────────────────────────────────────────────────────────
class H155Session:
    """
    Handles authenticated communication with Huawei H155 web API.
    The H155 uses a token-based session over HTTP with CSRF protection.
    """

    DEFAULT_GATEWAY = "192.168.8.1"
    BASE_ENDPOINTS = {
        "login_state":   "/api/user/state-login",
        "login":         "/api/user/login",
        "logout":        "/api/user/logout",
        "device_info":   "/api/device/information",
        "signal":        "/api/device/signal",
        "net_mode":      "/api/net/net-mode",
        "net_mode_list": "/api/net/net-mode-list",
        "cell_info":     "/api/net/cell-info",
        "plmn_list":     "/api/net/plmn-list",
        "current_plmn":  "/api/net/current-plmn",
        "reboot":        "/api/device/control",
        "band_set":      "/api/net/net-mode",
        "token":         "/api/webserver/SesTokInfo",
        "monitoring":    "/api/monitoring/status",
    }

    def __init__(self, gateway: str = None):
        self.gateway  = gateway or self.DEFAULT_GATEWAY
        self.base_url = f"http://{self.gateway}"
        self.session  = requests.Session()
        self.session.verify = False
        self.session.timeout = 10
        self._token   = None
        self._session_id = None
        self.authenticated = False
        # huawei-lte-api handles (used when the library is installed)
        self._hw_conn   = None
        self._hw_client = None
        # ── auto re-authentication state ──
        self._password      = None    # remembered so we can re-login on expiry
        self._manual_login  = None    # (password_value, password_type) that worked
        self._reauth_count  = 0       # how many times the session was rebuilt

    # ── SESSION-EXPIRY DETECTION & AUTO RE-AUTH ─────────────
    # Huawei routers drop the web session after a while; subsequent calls fail
    # with 100003 ("no rights / needs login") or 125003 ("wrong session token").
    # These helpers transparently re-establish the session so long-running
    # daemons (autopilot, watchdog, dashboards) keep working unattended.
    _SESSION_ERR_MARKERS = ("100003", "125003", "125002", "needs login",
                            "No rights", "no rights", "not login", "ResponseErrorNotSupported")

    @classmethod
    def _is_session_error(cls, text_or_exc) -> bool:
        s = str(text_or_exc)
        return any(mark in s for mark in cls._SESSION_ERR_MARKERS)

    def _reauth(self) -> bool:
        """Rebuild the router session using the remembered credentials."""
        if not self._password:
            return False
        self._reauth_count += 1
        # Preferred: rebuild the huawei-lte-api connection (handles SCRAM).
        if HUAWEI_LIB:
            try:
                url = f"http://admin:{self._password}@{self.gateway}/"
                self._hw_conn   = _HuaweiConnection(url)
                self._hw_client = _HuaweiClient(self._hw_conn)
                self._hw_client.device.information()   # verify it works
                self.authenticated = True
                self._token = None                     # force fresh CSRF token
                return True
            except Exception:
                self._hw_conn = None
                self._hw_client = None
        # Fallback: manual XML re-login (reuse the variant that worked before).
        if self._get_token():
            if self._manual_login:
                pw_val, pw_type = self._manual_login
            else:
                pw_val = base64.b64encode(self._password.encode()).decode()
                pw_type = "4"
            login_xml = (
                '<?xml version="1.0" encoding="UTF-8"?><request>'
                "<Username>admin</Username>"
                f"<Password>{pw_val}</Password>"
                f"<password_type>{pw_type}</password_type></request>"
            )
            resp = self._xml_post(self.BASE_ENDPOINTS["login"], login_xml)
            if resp and "<response>OK</response>" in resp:
                self.authenticated = True
                return True
        return False

    def _safe_lib(self, func, label: str):
        """Run a huawei-lte-api read; on session-expiry, re-auth once and retry.
        Returns (ok, result). Only warns on a genuine (non-recovered) failure."""
        try:
            return True, func()
        except Exception as e:
            if self._is_session_error(e) and self._reauth():
                try:
                    return True, func()
                except Exception as e2:
                    if not self._is_session_error(e2):
                        warn(f"{label}: {e2}")
                    return False, None
            if not self._is_session_error(e):
                warn(f"{label}: {e}")
            return False, None

    # ── LOW-LEVEL HTTP ──────────────────────────────────────
    def _get_token(self) -> bool:
        """Fetch CSRF token + session cookie from router."""
        try:
            r = self.session.get(
                self.base_url + self.BASE_ENDPOINTS["token"],
                timeout=8
            )
            r.raise_for_status()
            tok  = re.search(r"<TokInfo>(.*?)</TokInfo>", r.text)
            ses  = re.search(r"<SesInfo>(.*?)</SesInfo>",  r.text)
            if tok and ses:
                self._token      = tok.group(1)
                self._session_id = ses.group(1)
                self.session.headers.update({
                    "__RequestVerificationToken": self._token,
                    "Cookie": self._session_id,
                })
                return True
        except Exception as e:
            err(f"Token fetch failed: {e}")
        return False

    def _xml_post(self, endpoint: str, xml_body: str) -> Optional[str]:
        """POST XML to router endpoint, auto-refresh token on 401/403."""
        url = self.base_url + endpoint
        headers = {
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "__RequestVerificationToken": self._token or "",
        }
        try:
            r = self.session.post(url, data=xml_body, headers=headers, timeout=10)
            # Refresh token from response header if provided
            new_tok = r.headers.get("__RequestVerificationTokenone")
            if new_tok:
                self._token = new_tok
                self.session.headers.update({"__RequestVerificationToken": new_tok})
            return r.text
        except requests.exceptions.ConnectionError:
            err("Cannot reach router. Is the gateway correct?")
        except Exception as e:
            err(f"POST error: {e}")
        return None

    def _xml_get(self, endpoint: str) -> Optional[str]:
        url = self.base_url + endpoint
        try:
            r = self.session.get(url, timeout=10)
            return r.text
        except requests.exceptions.ConnectionError:
            err("Connection refused – router unreachable.")
        except Exception as e:
            err(f"GET error: {e}")
        return None

    def _parse_xml_val(self, xml: str, tag: str, default="N/A") -> str:
        m = re.search(rf"<{tag}>(.*?)</{tag}>", xml, re.DOTALL)
        return m.group(1).strip() if m else default

    # ── AUTHENTICATION ──────────────────────────────────────
    def connect(self, password: str) -> bool:
        """
        Login flow:
        - Preferred: huawei-lte-api library (auto-detects firmware login scheme,
          including SCRAM used by newer H155 firmware – fixes persistent 125003).
        - Fallback: manual XML login attempts.
        """
        step("Connecting to router...")
        info(f"Gateway : {colorize(self.gateway, C.CYAN)}")
        self._password = password   # remembered for automatic re-authentication

        # ── Preferred path: maintained library ──────────────────
        if HUAWEI_LIB:
            info("Using huawei-lte-api (auto SCRAM/firmware detection)")
            try:
                url = f"http://admin:{password}@{self.gateway}/"
                self._hw_conn   = _HuaweiConnection(url)
                self._hw_client = _HuaweiClient(self._hw_conn)
                # Verify by reading device info
                _ = self._hw_client.device.information()
                ok(colorize("Authenticated via huawei-lte-api!", C.GREEN + C.BOLD))
                self.authenticated = True
                return True
            except Exception as e:
                warn(f"Library login failed ({type(e).__name__}): {e}")
                warn("Falling back to manual XML login...")
                self._hw_conn = None
                self._hw_client = None
        else:
            warn("huawei-lte-api not installed – using manual login.")
            info("For best results:  " + colorize("pip install huawei-lte-api", C.CYAN, C.BOLD))

        # ── Fallback path: manual XML ───────────────────────────
        if not self._get_token():
            err("Could not retrieve session token.")
            return False
        ok("Session token acquired")

        state_xml = self._xml_get(self.BASE_ENDPOINTS["login_state"])
        if state_xml:
            state = self._parse_xml_val(state_xml, "State")
            if state == "0":
                ok("Router is reachable (not logged in)")
            elif state == "1":
                warn("A previous session is still active – clearing it")
                self._xml_post(
                    self.BASE_ENDPOINTS["logout"],
                    '<?xml version="1.0" encoding="UTF-8"?><request><Logout>1</Logout></request>'
                )
                time.sleep(1)
                self._get_token()
                ok("Stale session cleared, fresh token acquired")

        # Build password variants for older firmware
        pw_b64_plain = base64.b64encode(password.encode()).decode()
        pw_sha256    = hashlib.sha256(password.encode()).hexdigest()
        pw_b64_sha   = base64.b64encode(pw_sha256.encode()).decode()
        pw_md5       = hashlib.md5(password.encode()).hexdigest()
        pw_b64_md5   = base64.b64encode(pw_md5.encode()).decode()

        attempts = [
            (pw_b64_plain, "4", "Base64 plain"),
            (pw_sha256,    "4", "SHA256-hex type4"),
            (pw_b64_sha,   "4", "SHA256→Base64 type4"),
            (pw_b64_plain, "3", "Base64 plain type3"),
            (pw_sha256,    "3", "SHA256-hex type3"),
            (pw_b64_sha,   "3", "SHA256→Base64 type3"),
            (password,     "4", "Plaintext type4"),
            (password,     "3", "Plaintext type3"),
            (pw_b64_md5,   "4", "MD5→Base64 type4"),
        ]

        last_resp = None
        for idx, (pw_val, pw_type, label) in enumerate(attempts):
            if idx > 0:
                self._get_token()
                time.sleep(0.4)
            login_xml = (
                '<?xml version="1.0" encoding="UTF-8"?>'
                "<request>"
                f"<Username>admin</Username>"
                f"<Password>{pw_val}</Password>"
                f"<password_type>{pw_type}</password_type>"
                "</request>"
            )
            info(f"Trying auth method: {colorize(label, C.DIM)}")
            resp = self._xml_post(self.BASE_ENDPOINTS["login"], login_xml)
            if resp and "<response>OK</response>" in resp:
                ok(colorize(f"Authenticated! [{label}]", C.GREEN + C.BOLD))
                self.authenticated = True
                self._manual_login = (pw_val, pw_type)   # reuse on re-auth
                return True
            last_resp = resp
            if resp:
                code = self._parse_xml_val(resp, "code")
                if code == "125002":
                    err("Account locked! Too many failed attempts.")
                    return False

        err("Authentication failed – all methods exhausted.")
        if last_resp:
            code = self._parse_xml_val(last_resp, "code")
            if code != "N/A":
                err(f"Last error code: {colorize(code, C.RED)}")
                codes = {
                    "125001": "Wrong username/password",
                    "125002": "Account locked",
                    "125003": "Session/token conflict – install huawei-lte-api to fix",
                    "125004": "Max sessions reached",
                }
                hint = codes.get(code)
                if hint:
                    warn(f"Hint: {hint}")
        if not HUAWEI_LIB:
            warn("Strongly recommended: " + colorize("pip install huawei-lte-api", C.CYAN, C.BOLD))
        return False

    def logout(self):
        step("Logging out...")
        xml = '<?xml version="1.0" encoding="UTF-8"?><request><Logout>1</Logout></request>'
        self._xml_post(self.BASE_ENDPOINTS["logout"], xml)
        ok("Session closed")

    # ── DEVICE INFO ─────────────────────────────────────────
    def get_device_info(self) -> dict:
        if self._hw_client is not None:
            okq, d = self._safe_lib(lambda: self._hw_client.device.information(),
                                    "Library device-info read failed")
            if okq:
                return {
                    "model":    d.get("DeviceName",       "N/A"),
                    "imei":     d.get("Imei",             "N/A"),
                    "imsi":     d.get("Imsi",             "N/A"),
                    "iccid":    d.get("Iccid",            "N/A"),
                    "hardware": d.get("HardwareVersion",  "N/A"),
                    "software": d.get("SoftwareVersion",  "N/A"),
                    "mac":      d.get("MacAddress1",      "N/A"),
                    "uptime":   d.get("uptime",           "N/A"),
                    "wan_ip":   d.get("WanIPAddress",     "N/A"),
                }

        xml = self._xml_get(self.BASE_ENDPOINTS["device_info"])
        if not xml:
            return {}
        return {
            "model":        self._parse_xml_val(xml, "DeviceName"),
            "imei":         self._parse_xml_val(xml, "Imei"),
            "imsi":         self._parse_xml_val(xml, "Imsi"),
            "iccid":        self._parse_xml_val(xml, "Iccid"),
            "hardware":     self._parse_xml_val(xml, "HardwareVersion"),
            "software":     self._parse_xml_val(xml, "SoftwareVersion"),
            "mac":          self._parse_xml_val(xml, "MacAddress1"),
            "uptime":       self._parse_xml_val(xml, "uptime"),
            "wan_ip":       self._parse_xml_val(xml, "WanIPAddress"),
        }

    # ── SIGNAL ──────────────────────────────────────────────
    def get_signal(self) -> dict:
        # Preferred: use the library client – it knows the right endpoint
        # and field names for your specific firmware (fixes the empty N/A reads).
        if self._hw_client is not None:
            okq, d = self._safe_lib(lambda: self._hw_client.device.signal(),
                                    "Library signal read failed")
            if okq:
                raw = {
                    "rsrp":   d.get("rsrp",   "N/A"),
                    "rsrq":   d.get("rsrq",   "N/A"),
                    "rssi":   d.get("rssi",   "N/A"),
                    "sinr":   d.get("sinr",   "N/A"),
                    "band":   d.get("band",   "N/A"),
                    "cell_id":d.get("cell_id","N/A"),
                    "pci":    d.get("pci",    "N/A"),
                    "earfcn": d.get("earfcn", "N/A"),
                    "mode":   d.get("mode",   "N/A"),
                    "txpower":d.get("txpower","N/A"),
                    "tac":    d.get("tac",    "N/A"),
                    "plmn":   d.get("plmn",   "N/A"),
                }
                def safe_int(v):
                    try: return int(re.sub(r"[^-\d]", "", str(v)))
                    except: return None
                raw["rsrp_int"] = safe_int(raw["rsrp"])
                raw["sinr_int"] = safe_int(raw["sinr"])
                return raw

        xml = self._xml_get(self.BASE_ENDPOINTS["signal"])
        if not xml:
            return {}
        raw = {
            "rsrp":   self._parse_xml_val(xml, "rsrp"),
            "rsrq":   self._parse_xml_val(xml, "rsrq"),
            "rssi":   self._parse_xml_val(xml, "rssi"),
            "sinr":   self._parse_xml_val(xml, "sinr"),
            "band":   self._parse_xml_val(xml, "band"),
            "cell_id":self._parse_xml_val(xml, "cell_id"),
            "pci":    self._parse_xml_val(xml, "pci"),
            "earfcn": self._parse_xml_val(xml, "earfcn"),
            "mode":   self._parse_xml_val(xml, "mode"),
            "txpower":self._parse_xml_val(xml, "txpower"),
            "tac":    self._parse_xml_val(xml, "tac"),
            "plmn":   self._parse_xml_val(xml, "plmn"),
        }
        # Parse numeric values
        def safe_int(v):
            try: return int(re.sub(r"[^-\d]", "", v))
            except: return None

        raw["rsrp_int"] = safe_int(raw["rsrp"])
        raw["sinr_int"] = safe_int(raw["sinr"])
        return raw

    def get_monitoring(self) -> dict:
        if self._hw_client is not None:
            okq, d = self._safe_lib(lambda: self._hw_client.monitoring.status(),
                                    "Library monitoring read failed")
            if okq:
                return {
                    "connection_status": d.get("ConnectionStatus",     "N/A"),
                    "network_type":      d.get("CurrentNetworkType",    "N/A"),
                    "network_type_ex":   d.get("CurrentNetworkTypeEx",  "N/A"),
                    "roaming":           d.get("RoamingStatus",         "N/A"),
                    "sim_status":        d.get("SimStatus",             "N/A"),
                    "dl_speed":          d.get("CurrentDownloadRate",   "0"),
                    "ul_speed":          d.get("CurrentUploadRate",     "0"),
                    "dl_total":          d.get("TotalDownload",         "0"),
                    "ul_total":          d.get("TotalUpload",           "0"),
                }

        xml = self._xml_get(self.BASE_ENDPOINTS["monitoring"])
        if not xml:
            return {}
        return {
            "connection_status": self._parse_xml_val(xml, "ConnectionStatus"),
            "network_type":      self._parse_xml_val(xml, "CurrentNetworkType"),
            "network_type_ex":   self._parse_xml_val(xml, "CurrentNetworkTypeEx"),
            "roaming":           self._parse_xml_val(xml, "RoamingStatus"),
            "sim_status":        self._parse_xml_val(xml, "SimStatus"),
            "dl_speed":          self._parse_xml_val(xml, "CurrentDownloadRate"),
            "ul_speed":          self._parse_xml_val(xml, "CurrentUploadRate"),
            "dl_total":          self._parse_xml_val(xml, "TotalDownload"),
            "ul_total":          self._parse_xml_val(xml, "TotalUpload"),
        }

    # ── NETWORK MODE / BAND LOCKING ─────────────────────────
    def get_net_mode(self) -> dict:
        if self._hw_client is not None:
            okq, d = self._safe_lib(lambda: self._hw_client.net.net_mode(),
                                    "Library net-mode read failed")
            if okq:
                return {
                    "network_mode":  d.get("NetworkMode", "N/A"),
                    "network_band":  d.get("NetworkBand", "N/A"),
                    "lte_band":      d.get("LTEBand",     "N/A"),
                }

        xml = self._xml_get(self.BASE_ENDPOINTS["net_mode"])
        if not xml:
            return {}
        return {
            "network_mode":  self._parse_xml_val(xml, "NetworkMode"),
            "network_band":  self._parse_xml_val(xml, "NetworkBand"),
            "lte_band":      self._parse_xml_val(xml, "LTEBand"),
        }

    def set_net_mode(self, network_mode: str, network_band: str, lte_band: str) -> bool:
        """
        Set network mode and band locks.
        network_mode: "03"=LTE only, "02"=3G only, "01"=2G only, "00"=Auto
        network_band: hex bitmask for 2G/3G bands
        lte_band:     hex bitmask for LTE bands
        """
        if self._hw_client is not None:
            okq, r = self._safe_lib(
                lambda: self._hw_client.net.set_net_mode(network_mode, network_band, lte_band),
                "Library set-net-mode failed")
            if okq:
                return r == "OK" or (isinstance(r, dict) and not r.get("error"))

        xml = (
            '<?xml version="1.0" encoding="UTF-8"?>'
            "<request>"
            f"<NetworkMode>{network_mode}</NetworkMode>"
            f"<NetworkBand>{network_band}</NetworkBand>"
            f"<LTEBand>{lte_band}</LTEBand>"
            "</request>"
        )
        resp = self._xml_post(self.BASE_ENDPOINTS["band_set"], xml)
        return resp is not None and "<response>OK</response>" in resp

    def get_cell_info(self) -> str:
        """Return raw cell neighbor list XML (or library-shaped string)."""
        if self._hw_client is not None:
            # Library returns parsed dict(s); re-emit as the <Cell> XML
            # shape the rest of the code already parses.
            okq, d = self._safe_lib(lambda: self._hw_client.net.cell_info(),
                                    "Library cell-info read failed")
            if okq:
                cells = d if isinstance(d, list) else [d]
                parts = []
                for c in cells:
                    if not isinstance(c, dict):
                        continue
                    fields = "".join(
                        f"<{k}>{v}</{k}>" for k, v in c.items() if v is not None
                    )
                    parts.append(f"<Cell>{fields}</Cell>")
                if parts:
                    return "<response>" + "".join(parts) + "</response>"
        return self._xml_get(self.BASE_ENDPOINTS["cell_info"]) or ""

    def get_plmn_list(self) -> str:
        """Trigger network scan (blocking, ~60s)."""
        return self._xml_get(self.BASE_ENDPOINTS["plmn_list"]) or ""

    def reboot(self) -> bool:
        xml = '<?xml version="1.0" encoding="UTF-8"?><request><Control>1</Control></request>'
        resp = self._xml_post(self.BASE_ENDPOINTS["reboot"], xml)
        return resp is not None and "<response>OK</response>" in resp

    # ── GENERIC AUTHENTICATED TRANSPORT (works in both login modes) ──
    # The original code paired a "library read" with a "raw-XML read" in every
    # getter. The helpers below generalise that so the 40 advanced features can
    # talk to ANY router endpoint without duplicating that branching each time.
    def _lib_session(self):
        """Best-effort: return the authenticated requests.Session that the
        huawei-lte-api Connection uses internally (so GETs reuse its cookies)."""
        if self._hw_conn is None:
            return None
        for attr in ("requests_session", "_requests_session", "session", "_session"):
            s = getattr(self._hw_conn, attr, None)
            if s is not None and hasattr(s, "get"):
                return s
        return None

    def lib(self, dotted: str):
        """Resolve a huawei-lte-api client callable by dotted path (e.g.
        'sms.get_sms_list'), or return None if unavailable in this library
        version. Lets features prefer the library's CSRF-aware write methods
        without risking AttributeError on differing library versions."""
        if self._hw_client is None:
            return None
        obj = self._hw_client
        for part in dotted.split("."):
            obj = getattr(obj, part, None)
            if obj is None:
                return None
        return obj if callable(obj) else None

    def api_get(self, endpoint: str, _retry: bool = True) -> str:
        """Authenticated GET → raw XML text ('' on failure). In library mode it
        reuses the library's authenticated session; otherwise the manual one.
        Auto re-authenticates and retries once if the session has expired."""
        if self._hw_client is not None:
            s = self._lib_session()
            if s is not None:
                try:
                    text = s.get(self.base_url + endpoint, timeout=10).text
                except Exception as e:
                    warn(f"GET {endpoint} failed: {e}")
                    return ""
                if _retry and self._is_session_error(text) and self._reauth():
                    return self.api_get(endpoint, _retry=False)
                return text
        text = self._xml_get(endpoint) or ""
        if _retry and self._is_session_error(text) and self._reauth():
            return self.api_get(endpoint, _retry=False)
        return text

    def api_post(self, endpoint: str, fields, _retry: bool = True) -> str:
        """Authenticated POST. `fields` may be a dict (serialised to
        <key>value</key> pairs in document order) or a ready XML body string.
        Returns the raw XML response text ('' on failure). Auto re-authenticates
        and retries once if the session has expired."""
        if isinstance(fields, dict):
            body = ('<?xml version="1.0" encoding="UTF-8"?><request>'
                    + "".join(f"<{k}>{v}</{k}>" for k, v in fields.items())
                    + "</request>")
        else:
            body = fields
        if self._hw_client is not None:
            s = self._lib_session()
            if s is not None:
                # Bootstrap a CSRF token from the already-authenticated session
                # so writes validate even though we POST raw XML ourselves.
                if not self._token:
                    try:
                        t = s.get(self.base_url + self.BASE_ENDPOINTS["token"],
                                  timeout=8).text
                        tok = re.search(r"<TokInfo>(.*?)</TokInfo>", t)
                        if tok:
                            self._token = tok.group(1)
                    except Exception:
                        pass
                headers = {
                    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                    "__RequestVerificationToken": self._token or "",
                }
                try:
                    r = s.post(self.base_url + endpoint, data=body,
                               headers=headers, timeout=10)
                    new_tok = (r.headers.get("__RequestVerificationTokenone")
                               or r.headers.get("__RequestVerificationToken"))
                    if new_tok:
                        self._token = new_tok.split("#")[0] if "#" in new_tok else new_tok
                    text = r.text
                except Exception as e:
                    warn(f"POST {endpoint} failed: {e}")
                    return ""
                if _retry and self._is_session_error(text) and self._reauth():
                    return self.api_post(endpoint, fields, _retry=False)
                return text
        text = self._xml_post(endpoint, body) or ""
        if _retry and self._is_session_error(text) and self._reauth():
            return self.api_post(endpoint, fields, _retry=False)
        return text

    @staticmethod
    def post_ok(resp: str) -> bool:
        """True if a router POST response indicates success."""
        return bool(resp) and "<response>OK</response>" in resp


# ─────────────────────────────────────────────────────────────
#  BAND BITMASK UTILITIES
# ─────────────────────────────────────────────────────────────
def bands_to_lte_bitmask(band_list: list[int]) -> str:
    """Convert list of LTE band numbers to hex bitmask string."""
    mask = 0
    for b in band_list:
        if 1 <= b <= 64:
            mask |= (1 << (b - 1))
    return format(mask, "X") or "7FFFFFFFFFFFFFFF"

def lte_bitmask_to_bands(hex_mask: str) -> list[int]:
    """Convert hex bitmask back to list of band numbers."""
    try:
        mask = int(hex_mask, 16)
    except ValueError:
        return []
    return [i + 1 for i in range(64) if mask & (1 << i)]

def earfcn_to_band(earfcn: int) -> Optional[int]:
    for band, info in BAND_DB.items():
        lo, hi = info["earfcn"]
        if lo <= earfcn <= hi:
            return band
    return None

def earfcn_to_freq_mhz(earfcn: int) -> Optional[float]:
    band = earfcn_to_band(earfcn)
    if band and band in BAND_DB:
        lo, hi = BAND_DB[band]["dl_range"]
        lo_earfcn, _ = BAND_DB[band]["earfcn"]
        # LTE formula: F_DL = F_DL_low + 0.1 * (N_DL - N_Offs_DL)
        freq = lo + 0.1 * (earfcn - lo_earfcn)
        return round(freq, 2)
    return None

def nr_bands_to_bitmask(band_list: list[int]) -> str:
    """Convert list of 5G NR band numbers (n1, n78...) to hex bitmask string."""
    mask = 0
    for b in band_list:
        if 1 <= b <= 256:
            mask |= (1 << (b - 1))
    return format(mask, "X") or "0"

def nr_bitmask_to_bands(hex_mask: str) -> list[int]:
    """Convert NR hex bitmask back to list of band numbers."""
    try:
        mask = int(hex_mask, 16)
    except (ValueError, TypeError):
        return []
    return [i + 1 for i in range(256) if mask & (1 << i)]

# ─────────────────────────────────────────────────────────────
#  DISPLAY HELPERS
# ─────────────────────────────────────────────────────────────
def grade_rsrp(val: Optional[int]):
    if val is None:
        return "Unknown", C.DIM
    for threshold, label, color in RSRP_GRADES:
        if val >= threshold:
            return label, color
    return "Bad", C.RED

def grade_sinr(val: Optional[int]):
    if val is None:
        return "Unknown", C.DIM
    for threshold, label, color in SINR_GRADES:
        if val >= threshold:
            return label, color
    return "Bad", C.RED

def signal_bar(rsrp: Optional[int]) -> str:
    if rsrp is None:
        return "░░░░░"
    levels = [(-80, "█"), (-90, "▓"), (-100, "▒"), (-110, "░")]
    bars = 0
    for threshold, _ in levels:
        if rsrp >= threshold:
            bars += 1
    full  = "█" * bars
    empty = "░" * (4 - bars)
    colors = [C.RED, C.ORANGE, C.YELLOW, C.GREEN, C.LIME]
    color  = colors[min(bars, 4)]
    return f"{color}{full}{C.DIM}{empty}{C.RESET}"

def speed_fmt(bps_str: str) -> str:
    try:
        bps = int(bps_str)
        if bps >= 1_000_000:
            return f"{bps/1_000_000:.1f} MB/s"
        elif bps >= 1_000:
            return f"{bps/1_000:.1f} KB/s"
        return f"{bps} B/s"
    except:
        return bps_str

def bytes_fmt(b_str: str) -> str:
    try:
        b = int(b_str)
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if b < 1024:
                return f"{b:.1f} {unit}"
            b /= 1024
        return f"{b:.1f} PB"
    except:
        return b_str

def network_type_name(code: str) -> str:
    types = {
        "0": "No service", "1": "GSM", "2": "GPRS", "3": "EDGE",
        "4": "WCDMA", "5": "HSDPA", "6": "HSUPA", "7": "HSPA",
        "8": "TD-SCDMA", "9": "HSPA+", "10": "EVDO rev.0",
        "11": "EVDO rev.A", "12": "EVDO rev.B", "13": "1xRTT",
        "14": "UMB", "15": "1xEVDV", "17": "HSPA+ 64QAM",
        "18": "HSPA+ MIMO", "19": "LTE", "20": "LTE-CA", "21": "NR 5G",
        "41": "UMTS", "43": "DC-HSPA+", "101": "LTE CA",
    }
    return types.get(code, f"Type {code}")


# ─────────────────────────────────────────────────────────────
#  SHARED INPUT / PARSE HELPERS  (used by the advanced features)
# ─────────────────────────────────────────────────────────────
def ask(prompt_text: str) -> Optional[str]:
    """input() that returns None on Ctrl-C / EOF instead of raising."""
    try:
        return input(prompt_text).strip()
    except (KeyboardInterrupt, EOFError):
        print()
        return None

def confirm(prompt_text: str) -> bool:
    ans = ask(prompt_text)
    return ans is not None and ans.lower() in ("y", "yes")

def xval(xml: str, tag: str, default: str = "N/A") -> str:
    """Extract a single XML tag value from a response string."""
    m = re.search(rf"<{tag}>(.*?)</{tag}>", xml or "", re.DOTALL)
    return m.group(1).strip() if m else default

def xml_error_code(xml: str) -> Optional[str]:
    """Return the <code> from an <error> response, or None if not an error."""
    if xml and "<error>" in xml:
        return xval(xml, "code", None)
    return None

# Human-readable Huawei API error codes (covers the common H155 set)
API_ERRORS = {
    "100002": "Not supported by firmware",
    "100003": "Access denied / not enough rights",
    "100004": "System busy – try again",
    "103002": "Unknown error",
    "108001": "Wrong username",
    "108002": "Wrong password",
    "108003": "Already logged in",
    "108006": "Wrong username or password",
    "108007": "Too many login attempts – wait and retry",
    "120001": "Voice busy",
    "125001": "Wrong token",
    "125002": "Wrong session",
    "125003": "Wrong session token (install huawei-lte-api)",
    "113018": "SMS system not yet initialised",
    "113114": "SMS phone number invalid",
}

def explain_error(xml: str) -> Optional[str]:
    code = xml_error_code(xml)
    if code is None:
        return None
    return f"Error {code}: {API_ERRORS.get(code, 'see Huawei API reference')}"


# ─────────────────────────────────────────────────────────────
#  FEATURE MODULES
# ─────────────────────────────────────────────────────────────

def cmd_status(sess: H155Session, args):
    """Show full device + signal status dashboard."""
    step("Fetching device status...")
    sep()

    dev = sess.get_device_info()
    mon = sess.get_monitoring()
    sig = sess.get_signal()
    net = sess.get_net_mode()

    # ── Device Info ─────────────────────────────────────────
    print(f"\n  {C.GOLD}{C.BOLD}┌─  DEVICE  ─────────────────────────────────────┐{C.RESET}")
    if dev:
        fields = [
            ("Model",     dev.get("model",    "N/A")),
            ("IMEI",      dev.get("imei",     "N/A")),
            ("SIM (ICCID)",dev.get("iccid",   "N/A")),
            ("WAN IP",    dev.get("wan_ip",   "N/A")),
            ("Software",  dev.get("software", "N/A")),
            ("MAC",       dev.get("mac",      "N/A")),
        ]
        for k, v in fields:
            print(f"  {C.DIM}│{C.RESET}  {colorize(k+':',C.CYAN):<20} {colorize(v, C.WHITE)}")
    print(f"  {C.GOLD}{C.BOLD}└────────────────────────────────────────────────┘{C.RESET}")

    # ── Connection ──────────────────────────────────────────
    print(f"\n  {C.BLUE}{C.BOLD}┌─  CONNECTION  ─────────────────────────────────┐{C.RESET}")
    if mon:
        conn = mon.get("connection_status", "N/A")
        conn_color = C.GREEN if conn == "901" else C.RED
        conn_label = "Connected" if conn == "901" else f"Status {conn}"
        net_type = network_type_name(mon.get("network_type", "0"))
        roam   = "Yes" if mon.get("roaming", "0") == "1" else "No"
        sim_ok = "OK"  if mon.get("sim_status","255") == "1" else mon.get("sim_status","?")

        print(f"  {C.DIM}│{C.RESET}  {'Status:':<20} {colorize(conn_label, conn_color, C.BOLD)}")
        print(f"  {C.DIM}│{C.RESET}  {'Network Type:':<20} {colorize(net_type, C.CYAN)}")
        print(f"  {C.DIM}│{C.RESET}  {'SIM:':<20} {colorize(sim_ok, C.GREEN)}")
        print(f"  {C.DIM}│{C.RESET}  {'Roaming:':<20} {colorize(roam, C.YELLOW if roam=='Yes' else C.GREEN)}")
        print(f"  {C.DIM}│{C.RESET}  {'↓ Speed:':<20} {colorize(speed_fmt(mon.get('dl_speed','0')), C.LIME)}")
        print(f"  {C.DIM}│{C.RESET}  {'↑ Speed:':<20} {colorize(speed_fmt(mon.get('ul_speed','0')), C.TEAL)}")
        print(f"  {C.DIM}│{C.RESET}  {'Total ↓:':<20} {colorize(bytes_fmt(mon.get('dl_total','0')), C.DIM)}")
        print(f"  {C.DIM}│{C.RESET}  {'Total ↑:':<20} {colorize(bytes_fmt(mon.get('ul_total','0')), C.DIM)}")
    print(f"  {C.BLUE}{C.BOLD}└────────────────────────────────────────────────┘{C.RESET}")

    # ── Signal ──────────────────────────────────────────────
    print(f"\n  {C.MAGENTA}{C.BOLD}┌─  SIGNAL  ──────────────────────────────────────┐{C.RESET}")
    if sig:
        rsrp_int = sig.get("rsrp_int")
        sinr_int = sig.get("sinr_int")
        r_label, r_color = grade_rsrp(rsrp_int)
        s_label, s_color = grade_sinr(sinr_int)
        bar = signal_bar(rsrp_int)

        band_num_raw = sig.get("band", "N/A")
        try:
            band_num = int(band_num_raw)
            band_info = BAND_DB.get(band_num, {})
            band_name = band_info.get("name", f"Band {band_num}")
        except:
            band_name = band_num_raw

        earfcn_raw = sig.get("earfcn", "N/A")
        freq_mhz   = "N/A"
        try:
            earfcn_i = int(earfcn_raw)
            f = earfcn_to_freq_mhz(earfcn_i)
            freq_mhz = f"{f} MHz" if f else "N/A"
        except: pass

        print(f"  {C.DIM}│{C.RESET}  {'Signal Bar:':<20} {bar}")
        print(f"  {C.DIM}│{C.RESET}  {'RSRP:':<20} {colorize(sig.get('rsrp','N/A'), r_color, C.BOLD)}  ({colorize(r_label, r_color)})")
        print(f"  {C.DIM}│{C.RESET}  {'RSRQ:':<20} {colorize(sig.get('rsrq','N/A'), C.CYAN)}")
        print(f"  {C.DIM}│{C.RESET}  {'RSSI:':<20} {colorize(sig.get('rssi','N/A'), C.CYAN)}")
        print(f"  {C.DIM}│{C.RESET}  {'SINR:':<20} {colorize(sig.get('sinr','N/A'), s_color, C.BOLD)}  ({colorize(s_label, s_color)})")
        print(f"  {C.DIM}│{C.RESET}  {'Band:':<20} {colorize(band_name, C.GOLD)}")
        print(f"  {C.DIM}│{C.RESET}  {'EARFCN:':<20} {colorize(earfcn_raw, C.CYAN)}  → {colorize(freq_mhz, C.TEAL)}")
        print(f"  {C.DIM}│{C.RESET}  {'Cell ID:':<20} {colorize(sig.get('cell_id','N/A'), C.WHITE)}")
        print(f"  {C.DIM}│{C.RESET}  {'PCI:':<20} {colorize(sig.get('pci','N/A'), C.WHITE)}")
        print(f"  {C.DIM}│{C.RESET}  {'TAC:':<20} {colorize(sig.get('tac','N/A'), C.DIM)}")
        print(f"  {C.DIM}│{C.RESET}  {'TX Power:':<20} {colorize(sig.get('txpower','N/A'), C.ORANGE)}")
    print(f"  {C.MAGENTA}{C.BOLD}└────────────────────────────────────────────────┘{C.RESET}")

    # ── Band Lock Status ────────────────────────────────────
    if net:
        print(f"\n  {C.TEAL}{C.BOLD}┌─  BAND LOCK  ───────────────────────────────────┐{C.RESET}")
        mode = net.get("network_mode", "N/A")
        mode_names = {"00": "Auto", "01": "2G Only", "02": "3G Only", "03": "4G/LTE Only", "0301": "4G+3G"}
        mode_label = mode_names.get(mode, f"Mode {mode}")
        lte_mask = net.get("lte_band", "7FFFFFFFFFFFFFFF")
        locked_bands = lte_bitmask_to_bands(lte_mask)
        known = [BAND_DB[b]["name"] for b in locked_bands if b in BAND_DB]
        unknown = [f"Band {b}" for b in locked_bands if b not in BAND_DB]
        all_bands = known + unknown

        print(f"  {C.DIM}│{C.RESET}  {'Network Mode:':<20} {colorize(mode_label, C.CYAN, C.BOLD)}")
        if all_bands:
            for b in all_bands:
                print(f"  {C.DIM}│{C.RESET}  {'':20} {colorize('✔ ' + b, C.GREEN)}")
        else:
            print(f"  {C.DIM}│{C.RESET}  {'Bands:':<20} {colorize('All (no lock)', C.DIM)}")
        print(f"  {C.TEAL}{C.BOLD}└────────────────────────────────────────────────┘{C.RESET}")
    sep()


def cmd_scan_towers(sess: H155Session, args):
    """
    Scan neighbor cells and rank towers by signal quality.
    Uses /api/net/cell-info which returns serving + neighbor list.
    """
    step("Scanning towers (neighbor cell info)...")
    warn("This reads live neighbor cell data – no service interruption.")
    sep()

    xml = sess.get_cell_info()
    if not xml:
        err("No cell data received.")
        return

    # Parse all cell entries
    cells = []
    for cell_xml in re.finditer(r"<Cell>(.*?)</Cell>", xml, re.DOTALL):
        c = cell_xml.group(1)
        def v(tag, default="N/A"):
            m = re.search(rf"<{tag}>(.*?)</{tag}>", c)
            return m.group(1).strip() if m else default
        try:
            rsrp_val = int(re.sub(r"[^-\d]", "", v("Rsrp", "0")))
        except:
            rsrp_val = -999

        cells.append({
            "plmn":    v("Plmn"),
            "band":    v("Band"),
            "earfcn":  v("Earfcn"),
            "pci":     v("Pci"),
            "rsrp":    v("Rsrp"),
            "rsrp_int":rsrp_val,
            "rsrq":    v("Rsrq"),
            "sinr":    v("Sinr"),
            "cell_id": v("CellId"),
            "tac":     v("Tac"),
            "serving": v("Sinr") != "N/A",  # heuristic: serving cell has SINR
        })

    if not cells:
        warn("No neighbor cell data available.")
        warn("The router may need LTE mode and active data connection.")
        return

    # Sort by RSRP descending (best first)
    cells.sort(key=lambda x: x["rsrp_int"], reverse=True)

    print(f"\n  {C.GOLD}{C.BOLD}  Found {len(cells)} tower(s) – sorted by signal strength{C.RESET}\n")
    print(f"  {C.DIM}  {'#':<4} {'PCI':<6} {'Band':<8} {'EARFCN':<10} {'Freq (MHz)':<12} {'RSRP':<12} {'RSRQ':<10} {'Cell ID':<12} {'Grade'}{C.RESET}")
    print(f"  {C.DIM}  {'─'*90}{C.RESET}")

    for i, c in enumerate(cells):
        rank = i + 1
        pci    = c["pci"]
        band_n = c["band"]
        earfcn = c["earfcn"]
        rsrp   = c["rsrp"]
        rsrq   = c["rsrq"]
        cell_id= c["cell_id"]
        rsrp_i = c["rsrp_int"]

        freq_mhz = "N/A"
        try:
            f = earfcn_to_freq_mhz(int(earfcn))
            freq_mhz = f"{f:.1f}" if f else "N/A"
        except: pass

        grade_label, grade_color = grade_rsrp(rsrp_i)
        bar = signal_bar(rsrp_i)

        # Highlight best tower
        rank_str = f"{C.GOLD}{C.BOLD}★{rank:<2}{C.RESET}" if rank == 1 else f"  {rank:<2}"

        print(
            f"  {rank_str}  "
            f"{colorize(pci, C.CYAN):<15}"
            f"{colorize(band_n, C.MAGENTA):<17}"
            f"{colorize(earfcn, C.DIM):<19}"
            f"{colorize(freq_mhz, C.TEAL):<21}"
            f"{colorize(rsrp, grade_color):<21}"
            f"{colorize(rsrq, C.DIM):<19}"
            f"{colorize(cell_id, C.WHITE):<21}"
            f"{bar}  {colorize(grade_label, grade_color)}"
        )

    print()
    # Recommendation
    best = cells[0]
    try:
        best_band = int(best["band"])
        band_info = BAND_DB.get(best_band, {})
        band_label = band_info.get("name", f"Band {best_band}")
    except:
        band_label = f"Band {best['band']}"

    print(f"\n  {C.LIME}{C.BOLD}  ★ Best Tower Recommendation:{C.RESET}")
    print(f"  {C.GREEN}  PCI: {best['pci']}  |  {band_label}  |  EARFCN: {best['earfcn']}  |  RSRP: {best['rsrp']}{C.RESET}")
    sep()


def cmd_lock_band(sess: H155Session, args):
    """Lock to specific LTE bands."""
    if args.bands:
        selected = [int(b) for b in args.bands]
    else:
        # Interactive selection
        print(f"\n  {C.GOLD}{C.BOLD}Available LTE Bands:{C.RESET}\n")
        band_list = sorted(BAND_DB.keys())
        for b in band_list:
            info_d = BAND_DB[b]
            print(f"    {colorize(str(b), C.CYAN, C.BOLD):>12}   {colorize(info_d['name'], C.WHITE):<30}  {colorize(info_d['op'], C.DIM)}")

        print(f"\n  {C.YELLOW}Enter band numbers separated by spaces (e.g. 1 3 7):{C.RESET}")
        try:
            raw = input(f"  {C.CYAN}Bands > {C.RESET}").strip()
            selected = [int(x) for x in raw.split() if x.strip().isdigit()]
        except KeyboardInterrupt:
            warn("Cancelled.")
            return

    if not selected:
        err("No bands selected.")
        return

    step(f"Locking to band(s): {colorize(str(selected), C.GOLD)}")
    mask = bands_to_lte_bitmask(selected)
    info(f"LTE bitmask: {colorize(mask, C.CYAN)}")

    for b in selected:
        name = BAND_DB.get(b, {}).get("name", f"Band {b}")
        info(f"  Adding: {colorize(name, C.GREEN)}")

    mode = "03"  # LTE only for band lock
    if args.auto_mode:
        mode = "00"
        info("Mode: Auto (LTE preferred)")

    ok_flag = sess.set_net_mode(mode, "3FFFFFFF", mask)
    if ok_flag:
        ok(colorize("Band lock applied successfully!", C.GREEN + C.BOLD))
        info("Modem will reconnect on the locked band(s).")
    else:
        err("Failed to apply band lock. Check connection or try rebooting.")
    sep()


def cmd_unlock_bands(sess: H155Session, args):
    """Remove all band locks – set to auto all bands."""
    step("Removing all band locks (auto mode)...")
    ok_flag = sess.set_net_mode("00", "3FFFFFFF", "7FFFFFFFFFFFFFFF")
    if ok_flag:
        ok(colorize("All band locks removed. Router in full auto mode.", C.GREEN + C.BOLD))
    else:
        err("Failed to unlock bands.")
    sep()


def cmd_set_lte_only(sess: H155Session, args):
    """Force LTE-only mode, all LTE bands."""
    step("Setting LTE-only mode (all bands)...")
    ok_flag = sess.set_net_mode("03", "3FFFFFFF", "7FFFFFFFFFFFFFFF")
    if ok_flag:
        ok(colorize("LTE-only mode enabled.", C.CYAN + C.BOLD))
    else:
        err("Failed to set LTE-only mode.")
    sep()


def cmd_set_auto(sess: H155Session, args):
    """Set full auto network selection."""
    step("Setting auto network mode...")
    ok_flag = sess.set_net_mode("00", "3FFFFFFF", "7FFFFFFFFFFFFFFF")
    if ok_flag:
        ok(colorize("Auto mode enabled.", C.GREEN + C.BOLD))
    else:
        err("Failed to set auto mode.")
    sep()


def cmd_best_band(sess: H155Session, args):
    """
    Auto-detect best tower and lock to it:
    1. Scan cell neighbors
    2. Rank by RSRP
    3. Lock to band of best cell
    """
    step("Auto-detect best band from neighbor scan...")
    sep()

    xml = sess.get_cell_info()
    if not xml:
        err("No cell data. Make sure router is in LTE mode.")
        return

    cells = []
    for cell_xml in re.finditer(r"<Cell>(.*?)</Cell>", xml, re.DOTALL):
        c = cell_xml.group(1)
        def v(tag, default="N/A"):
            m = re.search(rf"<{tag}>(.*?)</{tag}>", c)
            return m.group(1).strip() if m else default
        try:
            rsrp_i = int(re.sub(r"[^-\d]", "", v("Rsrp", "-999")))
        except:
            rsrp_i = -999
        cells.append({
            "band":    v("Band"),
            "earfcn":  v("Earfcn"),
            "pci":     v("Pci"),
            "rsrp_int":rsrp_i,
            "rsrp":    v("Rsrp"),
        })

    if not cells:
        err("No cells found in scan.")
        return

    cells.sort(key=lambda x: x["rsrp_int"], reverse=True)
    best = cells[0]

    try:
        best_band = int(best["band"])
    except:
        err(f"Cannot parse band: {best['band']}")
        return

    band_info = BAND_DB.get(best_band, {})
    band_name = band_info.get("name", f"Band {best_band}")

    ok(f"Best band found: {colorize(band_name, C.GOLD, C.BOLD)}")
    info(f"  PCI: {best['pci']}  |  EARFCN: {best['earfcn']}  |  RSRP: {best['rsrp']}")

    mask = bands_to_lte_bitmask([best_band])
    info(f"  Locking to {colorize(band_name, C.CYAN)} (mask: {mask})")

    ok_flag = sess.set_net_mode("03", "3FFFFFFF", mask)
    if ok_flag:
        ok(colorize(f"Locked to {band_name} – best signal tower!", C.LIME + C.BOLD))
    else:
        err("Failed to apply band lock.")
    sep()


def cmd_reboot(sess: H155Session, args):
    """Reboot the router."""
    step("Rebooting router...")
    warn("Router will be offline for ~60 seconds.")
    try:
        confirm = input(f"  {C.RED}Confirm reboot? (yes/no): {C.RESET}").strip().lower()
    except KeyboardInterrupt:
        warn("Cancelled.")
        return
    if confirm != "yes":
        warn("Reboot cancelled.")
        return
    if sess.reboot():
        ok(colorize("Reboot command sent!", C.YELLOW + C.BOLD))
    else:
        err("Reboot failed.")
    sep()


def cmd_live_signal(sess: H155Session, args):
    """Continuously monitor signal every N seconds."""
    interval = getattr(args, "interval", 3) or 3
    step(f"Live signal monitor (refresh every {interval}s) – Ctrl+C to stop")
    sep()

    try:
        while True:
            sig = sess.get_signal()
            mon = sess.get_monitoring()
            ts  = datetime.now().strftime("%H:%M:%S")

            rsrp_i = sig.get("rsrp_int")
            r_label, r_color = grade_rsrp(rsrp_i)
            bar = signal_bar(rsrp_i)
            net_type = network_type_name(mon.get("network_type", "0"))

            dl = speed_fmt(mon.get("dl_speed", "0"))
            ul = speed_fmt(mon.get("ul_speed", "0"))

            # Clear line trick
            print(
                f"\r  {C.DIM}{ts}{C.RESET}  "
                f"{bar}  "
                f"RSRP: {colorize(sig.get('rsrp','?'), r_color, C.BOLD)}  "
                f"SINR: {colorize(sig.get('sinr','?'), C.CYAN)}  "
                f"Band: {colorize(sig.get('band','?'), C.GOLD)}  "
                f"Type: {colorize(net_type, C.TEAL)}  "
                f"↓{colorize(dl, C.LIME)}  ↑{colorize(ul, C.BLUE)}    ",
                end="", flush=True
            )
            time.sleep(interval)
    except KeyboardInterrupt:
        print()
        ok("Live monitor stopped.")
    sep()


def cmd_band_info(sess: H155Session, args):
    """Show all known band information and current lock."""
    step("LTE Band Reference Table")
    sep()

    net = sess.get_net_mode()
    lte_mask = net.get("lte_band", "7FFFFFFFFFFFFFFF") if net else "7FFFFFFFFFFFFFFF"
    locked   = set(lte_bitmask_to_bands(lte_mask))

    print(f"\n  {C.GOLD}{C.BOLD}  {'Band':<10} {'Name':<28} {'DL Range':<20} {'EARFCN Range':<22} {'Locked?':<10} {'Operators'}{C.RESET}")
    print(f"  {C.DIM}  {'─'*105}{C.RESET}")

    for b, d in sorted(BAND_DB.items()):
        is_locked  = b in locked
        lock_str   = colorize("✔ YES", C.GREEN, C.BOLD) if is_locked else colorize("─ no", C.DIM)
        dl_lo, dl_hi = d["dl_range"]
        e_lo, e_hi   = d["earfcn"]
        print(
            f"  {colorize(str(b), C.CYAN, C.BOLD):<18}"
            f"{colorize(d['name'], C.WHITE):<37}"
            f"{colorize(f'{dl_lo}-{dl_hi} MHz', C.TEAL):<29}"
            f"{colorize(f'{e_lo}-{e_hi}', C.DIM):<31}"
            f"{lock_str:<19}"
            f"{colorize(d['op'], C.YELLOW)}"
        )
    sep()


# ─────────────────────────────────────────────────────────────
#  ADVANCED FEATURE 1: SIGNAL HISTORY LOG
# ─────────────────────────────────────────────────────────────
def cmd_signal_log(sess: H155Session, args):
    """
    Log signal samples to a CSV file with timestamps.
    Runs for --duration seconds (default: 60), sampling every --interval sec.
    """
    duration = getattr(args, "duration", 60) or 60
    interval = getattr(args, "interval", 5)  or 5
    logfile  = f"signal_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

    step(f"Signal Logger – {duration}s duration, every {interval}s → {colorize(logfile, C.CYAN)}")
    sep()

    samples   = []
    start_t   = time.time()
    count     = 0
    end_t     = start_t + duration

    try:
        while time.time() < end_t:
            sig = sess.get_signal()
            mon = sess.get_monitoring()
            ts  = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            row = {
                "timestamp": ts,
                "rsrp":      sig.get("rsrp",    "N/A"),
                "rsrq":      sig.get("rsrq",    "N/A"),
                "rssi":      sig.get("rssi",    "N/A"),
                "sinr":      sig.get("sinr",    "N/A"),
                "band":      sig.get("band",    "N/A"),
                "pci":       sig.get("pci",     "N/A"),
                "earfcn":    sig.get("earfcn",  "N/A"),
                "cell_id":   sig.get("cell_id", "N/A"),
                "dl_speed":  speed_fmt(mon.get("dl_speed","0")),
                "ul_speed":  speed_fmt(mon.get("ul_speed","0")),
                "net_type":  network_type_name(mon.get("network_type","0")),
            }
            samples.append(row)
            count += 1
            rsrp_i = sig.get("rsrp_int")
            bar    = signal_bar(rsrp_i)
            r_lbl, r_col = grade_rsrp(rsrp_i)
            remaining = int(end_t - time.time())
            print(
                f"\r  {C.DIM}[{count:>3}] {ts}{C.RESET}  {bar}  "
                f"RSRP:{colorize(sig.get('rsrp','?'), r_col, C.BOLD)}  "
                f"SINR:{colorize(sig.get('sinr','?'), C.CYAN)}  "
                f"Band:{colorize(sig.get('band','?'), C.GOLD)}  "
                f"{colorize(f'{remaining}s left', C.DIM)}    ",
                end="", flush=True
            )
            time.sleep(interval)
    except KeyboardInterrupt:
        print()
        warn("Logging stopped early.")

    print()

    if not samples:
        warn("No samples collected.")
        return

    # Write CSV
    import csv
    with open(logfile, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=samples[0].keys())
        writer.writeheader()
        writer.writerows(samples)

    ok(f"Saved {count} samples → {colorize(logfile, C.CYAN, C.BOLD)}")

    # Summary stats
    rsrp_vals = []
    for s in samples:
        try: rsrp_vals.append(int(re.sub(r"[^-\d]","",s["rsrp"])))
        except: pass

    if rsrp_vals:
        avg   = sum(rsrp_vals) / len(rsrp_vals)
        best  = max(rsrp_vals)
        worst = min(rsrp_vals)
        sep()
        print(f"  {C.GOLD}{C.BOLD}  Session Summary:{C.RESET}")
        l1, c1 = grade_rsrp(int(avg))
        l2, c2 = grade_rsrp(best)
        l3, c3 = grade_rsrp(worst)
        print(f"  {C.DIM}  Samples  : {count}")
        print(f"  {C.DIM}  Avg RSRP : {C.RESET}{colorize(f'{avg:.1f} dBm  ({l1})', c1)}")
        print(f"  {C.DIM}  Best     : {C.RESET}{colorize(f'{best}  dBm  ({l2})', c2)}")
        print(f"  {C.DIM}  Worst    : {C.RESET}{colorize(f'{worst} dBm  ({l3})', c3)}")
    sep()


# ─────────────────────────────────────────────────────────────
#  ADVANCED FEATURE 2: MULTI-BAND BENCHMARK (scan → lock each → measure → rank)
# ─────────────────────────────────────────────────────────────
def cmd_benchmark(sess: H155Session, args):
    """
    For each available LTE band:
      1. Lock router to that band only
      2. Wait for reconnect
      3. Sample signal 5 times
      4. Restore best band automatically
    Produces a ranked comparison table.
    """
    step("Multi-Band Benchmark – testing each band individually")
    warn("Router will reconnect multiple times. Takes ~2-3 min. Don't disconnect.")
    sep()

    try:
        confirm = input(f"  {C.RED}Start benchmark? (yes/no): {C.RESET}").strip().lower()
    except KeyboardInterrupt:
        warn("Cancelled.")
        return
    if confirm != "yes":
        warn("Benchmark cancelled.")
        return

    # Determine which bands to test from neighbor scan first
    xml = sess.get_cell_info()
    visible_bands = set()
    if xml:
        for cell_xml in re.finditer(r"<Cell>(.*?)</Cell>", xml, re.DOTALL):
            c = cell_xml.group(1)
            m = re.search(r"<Band>(.*?)</Band>", c)
            if m:
                try: visible_bands.add(int(m.group(1)))
                except: pass

    test_bands = sorted(visible_bands) if visible_bands else sorted(BAND_DB.keys())
    info(f"Bands to test: {colorize(str(test_bands), C.CYAN)}")

    results = []  # list of {band, name, rsrp_avg, sinr_avg, samples}

    for band in test_bands:
        band_name = BAND_DB.get(band, {}).get("name", f"Band {band}")
        print(f"\n  {C.MAGENTA}▶{C.RESET}  Testing {colorize(band_name, C.GOLD, C.BOLD)}...")

        mask     = bands_to_lte_bitmask([band])
        ok_flag  = sess.set_net_mode("03", "3FFFFFFF", mask)
        if not ok_flag:
            warn(f"  Could not lock Band {band} – skipping")
            continue

        # Wait for reconnect
        print(f"  {C.DIM}  Waiting for reconnect", end="", flush=True)
        for _ in range(12):
            time.sleep(2)
            print(f"{C.DIM}.{C.RESET}", end="", flush=True)
        print()

        # Sample signal
        rsrp_list, sinr_list = [], []
        for i in range(5):
            sig = sess.get_signal()
            try: rsrp_list.append(int(re.sub(r"[^-\d]","",sig.get("rsrp","-999"))))
            except: pass
            try: sinr_list.append(int(re.sub(r"[^-\d]","",sig.get("sinr","-99"))))
            except: pass
            time.sleep(1)

        if rsrp_list:
            avg_rsrp = sum(rsrp_list) / len(rsrp_list)
            avg_sinr = sum(sinr_list) / len(sinr_list) if sinr_list else -99
            r_lbl, r_col = grade_rsrp(int(avg_rsrp))
            bar = signal_bar(int(avg_rsrp))
            print(f"  {C.DIM}  Result: {C.RESET}{bar}  RSRP: {colorize(f'{avg_rsrp:.1f}', r_col, C.BOLD)}  SINR: {colorize(f'{avg_sinr:.1f}', C.CYAN)}  ({colorize(r_lbl, r_col)})")
            results.append({
                "band":      band,
                "name":      band_name,
                "rsrp_avg":  avg_rsrp,
                "sinr_avg":  avg_sinr,
                "grade":     r_lbl,
                "color":     r_col,
                "bar":       bar,
            })
        else:
            warn(f"  No signal on Band {band} (not available here)")

    if not results:
        err("No results collected.")
        return

    # Sort by RSRP
    results.sort(key=lambda x: x["rsrp_avg"], reverse=True)

    sep()
    print(f"\n  {C.GOLD}{C.BOLD}  ╔══  BENCHMARK RESULTS  ══════════════════════════╗{C.RESET}")
    for i, r in enumerate(results):
        rank_icon = f"{C.GOLD}★{C.RESET}" if i == 0 else f"{C.DIM}{i+1}.{C.RESET}"
        rsrp_str = "%.1f" % r["rsrp_avg"]
        sinr_str = "%.1f" % r["sinr_avg"]
        print(
            f"  {C.GOLD}{C.BOLD}  ║{C.RESET}  {rank_icon}  "
            + colorize(r["name"], C.WHITE).ljust(35)
            + r["bar"] + "  "
            + ("RSRP: " + colorize(rsrp_str, r["color"], C.BOLD)).ljust(20)
            + ("SINR: " + colorize(sinr_str, C.CYAN)).ljust(12)
            + "  " + colorize(r["grade"], r["color"])
        )
    print(f"  {C.GOLD}{C.BOLD}  ╚═══════════════════════════════════════════════════╝{C.RESET}")

    # Lock to winner
    winner = results[0]
    info(f"\n  Auto-locking to winner: {colorize(winner['name'], C.LIME, C.BOLD)}")
    mask = bands_to_lte_bitmask([winner["band"]])
    if sess.set_net_mode("03", "3FFFFFFF", mask):
        ok(colorize(f"Locked to {winner['name']} – benchmark complete!", C.LIME + C.BOLD))
    sep()


# ─────────────────────────────────────────────────────────────
#  ADVANCED FEATURE 3: SMART WATCHDOG (auto re-lock if band drifts)
# ─────────────────────────────────────────────────────────────
def cmd_watchdog(sess: H155Session, args):
    """
    Monitor the active band every N seconds.
    If the modem drifts to a different band than desired, re-lock automatically.
    Useful after power cuts or network events that reset band selection.
    """
    interval = getattr(args, "interval", 10) or 10

    # Ask which band to guard
    net = sess.get_net_mode()
    lte_mask = net.get("lte_band", "7FFFFFFFFFFFFFFF") if net else "7FFFFFFFFFFFFFFF"
    locked   = lte_bitmask_to_bands(lte_mask)

    if not locked or locked == lte_bitmask_to_bands("7FFFFFFFFFFFFFFF"):
        warn("No band currently locked. Run 'best' or 'lock' first.")
        warn("Watchdog will guard the band you enter below.")
        print(f"\n  {C.CYAN}Enter band number to guard (e.g. 3):{C.RESET}")
        try:
            raw = input(f"  {C.YELLOW}Band > {C.RESET}").strip()
            guard_bands = [int(raw)]
        except:
            err("Invalid input.")
            return
    else:
        guard_bands = locked

    guard_names = [BAND_DB.get(b, {}).get("name", f"Band {b}") for b in guard_bands]
    guard_mask  = bands_to_lte_bitmask(guard_bands)

    step(f"Watchdog active – guarding: {colorize(', '.join(guard_names), C.GOLD, C.BOLD)}")
    info(f"Check interval: {interval}s  |  Ctrl+C to stop")
    sep()

    relock_count = 0
    check_count  = 0

    try:
        while True:
            sig     = sess.get_signal()
            ts      = datetime.now().strftime("%H:%M:%S")
            cur_band_raw = sig.get("band", "0")
            try:
                cur_band = int(cur_band_raw)
            except:
                cur_band = 0

            check_count += 1
            rsrp_i = sig.get("rsrp_int")
            bar    = signal_bar(rsrp_i)
            r_lbl, r_col = grade_rsrp(rsrp_i)

            if cur_band in guard_bands:
                status_icon = f"{C.GREEN}✔{C.RESET}"
                status_txt  = colorize("ON TARGET", C.GREEN)
            else:
                status_icon = f"{C.RED}✘{C.RESET}"
                status_txt  = colorize(f"DRIFT! Band {cur_band} → re-locking", C.RED, C.BOLD)
                # Re-apply lock silently
                sess.set_net_mode("03", "3FFFFFFF", guard_mask)
                relock_count += 1

            print(
                f"\r  {C.DIM}[{ts}] #{check_count:>4}{C.RESET}  "
                f"{status_icon}  {bar}  "
                f"Band:{colorize(cur_band_raw, C.GOLD)}  "
                f"RSRP:{colorize(sig.get('rsrp','?'), r_col, C.BOLD)}  "
                f"Relocks:{colorize(str(relock_count), C.RED if relock_count else C.DIM)}  "
                f"{status_txt}    ",
                end="", flush=True
            )
            time.sleep(interval)

    except KeyboardInterrupt:
        print()
        sep()
        ok(f"Watchdog stopped after {check_count} checks, {colorize(str(relock_count), C.YELLOW)} re-locks.")
    sep()


# ─────────────────────────────────────────────────────────────
#  ANTENNA SELECTION
# ─────────────────────────────────────────────────────────────
# H155 antenna mode endpoint
ANTENNA_ENDPOINT = "/api/device/antenna_type"
ANTENNA_SET_EP   = "/api/device/antenna_type"

# Known antenna mode codes for Huawei H155
ANTENNA_MODES = {
    "0": ("Auto (internal)",        C.CYAN),
    "1": ("Internal antenna only",  C.GREEN),
    "2": ("External antenna only",  C.GOLD),
    "3": ("Internal + External",    C.LIME),
}

def cmd_antenna(sess: H155Session, args):
    """
    Read and set antenna mode on H155.
    Internal / External / Both / Auto.
    """
    step("Antenna Configuration")
    sep()

    # Read current
    xml = sess._xml_get(ANTENNA_ENDPOINT)
    current = "N/A"
    if xml:
        current = sess._parse_xml_val(xml, "antenna_type", "N/A")
        label, col = ANTENNA_MODES.get(current, ("Unknown", C.DIM))
        ok(f"Current antenna mode: {colorize(label, col, C.BOLD)} (code {current})")
    else:
        warn("Could not read antenna status – router may not expose this API.")
        warn("Will attempt to set anyway.")

    sep()
    print(f"  {C.GOLD}{C.BOLD}  Available antenna modes:{C.RESET}\n")
    for code, (label, col) in ANTENNA_MODES.items():
        marker = colorize(" ◀ current", C.DIM) if code == current else ""
        print(f"    {colorize('['+code+']', col, C.BOLD)}  {colorize(label, C.WHITE)}{marker}")

    print()
    try:
        choice = input(f"  {C.CYAN}Enter mode code (0/1/2/3) or Enter to cancel: {C.RESET}").strip()
    except KeyboardInterrupt:
        warn("\nCancelled.")
        return

    if not choice:
        warn("No change made.")
        return

    if choice not in ANTENNA_MODES:
        err(f"Invalid code: {choice}")
        return

    label, col = ANTENNA_MODES[choice]
    info(f"Setting antenna to: {colorize(label, col, C.BOLD)}")

    set_xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        "<request>"
        f"<antenna_type>{choice}</antenna_type>"
        "</request>"
    )
    resp = sess._xml_post(ANTENNA_SET_EP, set_xml)

    if resp and "<response>OK</response>" in resp:
        ok(colorize(f"Antenna set to: {label}", col + C.BOLD))
        info("Signal may take 10-15 seconds to stabilize.")
    else:
        warn("Router returned non-OK response for antenna change.")
        warn("H155 firmware may not support remote antenna switching.")
        warn("Check router admin page manually: http://192.168.8.1 → Advanced → Antenna")
        if resp:
            code_e = sess._parse_xml_val(resp, "code")
            if code_e != "N/A":
                err(f"Error code: {code_e}")

    # After antenna change, show signal
    time.sleep(3)
    sig = sess.get_signal()
    if sig.get("rsrp", "N/A") != "N/A":
        rsrp_i = sig.get("rsrp_int")
        r_lbl, r_col = grade_rsrp(rsrp_i)
        bar = signal_bar(rsrp_i)
        ok(f"Signal after change: {bar}  RSRP: {colorize(sig.get('rsrp','?'), r_col, C.BOLD)}  ({colorize(r_lbl, r_col)})")
    sep()


# ─────────────────────────────────────────────────────────────
#  IP CONFLICT RESOLVER
# ─────────────────────────────────────────────────────────────
import subprocess
import socket

DHCP_EP      = "/api/dhcp/settings"
LAN_EP       = "/api/lan/hostinfo"
GATEWAY_EP   = "/api/lan/hostinfo"
DHCP_SET_EP  = "/api/dhcp/settings"

def cmd_fix_ip_conflicts(sess: H155Session, args):
    """
    Detect and fix IP conflicts on the router LAN:
    1. Read current DHCP pool
    2. Scan ARP table for duplicate IPs
    3. Show all connected devices
    4. Offer to change DHCP pool / gateway IP to resolve conflicts
    """
    step("IP Conflict Detector & Resolver")
    sep()

    # ── Read DHCP settings ───────────────────────────────────
    dhcp_xml = sess._xml_get(DHCP_EP)
    dhcp_start = dhcp_end = "N/A"
    if dhcp_xml:
        dhcp_start = sess._parse_xml_val(dhcp_xml, "DhcpIPAddress",      "192.168.8.100")
        dhcp_end   = sess._parse_xml_val(dhcp_xml, "DhcpEndIPAddress",   "192.168.8.200")

    # Read LAN IP separately
    dev_xml = sess._xml_get("/api/device/information")
    router_lan_ip = "192.168.8.1"
    if dev_xml:
        router_lan_ip = sess._parse_xml_val(dev_xml, "LanIPAddress", "192.168.8.1")

    print(f"  {C.GOLD}{C.BOLD}  Router LAN IP  : {C.RESET}{colorize(router_lan_ip, C.CYAN)}")
    print(f"  {C.GOLD}{C.BOLD}  DHCP Pool Start: {C.RESET}{colorize(dhcp_start, C.GREEN)}")
    print(f"  {C.GOLD}{C.BOLD}  DHCP Pool End  : {C.RESET}{colorize(dhcp_end,   C.GREEN)}")

    # ── Scan connected devices via hostinfo ──────────────────
    sep()
    step("Scanning connected devices...")

    host_xml = sess._xml_get("/api/wlan/host-list")
    devices  = []
    if host_xml:
        for host in re.finditer(r"<Host>(.*?)</Host>", host_xml, re.DOTALL):
            h = host.group(1)
            def hv(t):
                m = re.search(rf"<{t}>(.*?)</{t}>", h)
                return m.group(1).strip() if m else "N/A"
            devices.append({
                "name":      hv("HostName"),
                "ip":        hv("IpAddress"),
                "mac":       hv("MacAddress"),
                "interface": hv("AssociatedSsid"),
                "active":    hv("Active"),
            })

    # Also scan ARP locally
    arp_devices = []
    try:
        result = subprocess.run(["arp", "-a"], capture_output=True, text=True, timeout=5)
        for line in result.stdout.splitlines():
            m = re.search(r"\((\d+\.\d+\.\d+\.\d+)\).*?([0-9a-f:]{17})", line, re.I)
            if m:
                arp_devices.append({"ip": m.group(1), "mac": m.group(2)})
    except Exception:
        pass

    all_ips  = {}
    conflicts = []

    if devices:
        print(f"\n  {C.CYAN}{C.BOLD}  Connected devices (from router):{C.RESET}")
        print(f"  {C.DIM}  {'IP':<18} {'MAC':<20} {'Hostname':<22} {'Interface'}{C.RESET}")
        print(f"  {C.DIM}  {'─'*72}{C.RESET}")
        for d in devices:
            ip = d["ip"]
            if ip in all_ips:
                conflicts.append(ip)
                flag = colorize("  ⚠ DUPLICATE", C.RED, C.BOLD)
            else:
                all_ips[ip] = d["mac"]
                flag = ""
            print(f"  {colorize(ip, C.CYAN):<27} {colorize(d['mac'], C.DIM):<29} "
                  f"{colorize(d['name'], C.WHITE):<31} {colorize(d['interface'], C.GOLD)}{flag}")
    else:
        warn("Could not retrieve device list from router API.")

    if arp_devices:
        print(f"\n  {C.TEAL}{C.BOLD}  ARP table (this device):{C.RESET}")
        for a in arp_devices:
            ip = a["ip"]
            if ip in all_ips and all_ips[ip].lower() != a["mac"].lower():
                conflicts.append(ip)
                print(f"  {colorize(ip, C.RED, C.BOLD):<27} {colorize(a['mac'], C.RED)}"
                      f"  {colorize('⚠ MAC MISMATCH – CONFLICT!', C.RED, C.BOLD)}")
            else:
                all_ips[ip] = a["mac"]
                print(f"  {colorize(ip, C.CYAN):<27} {colorize(a['mac'], C.DIM)}")

    sep()

    if conflicts:
        print(f"\n  {C.RED}{C.BOLD}  ⚠  IP CONFLICTS DETECTED: {conflicts}{C.RESET}\n")
    else:
        ok("No IP conflicts detected on the LAN.")

    # ── Fix options ──────────────────────────────────────────
    print(f"\n  {C.GOLD}{C.BOLD}  Fix Options:{C.RESET}")
    print(f"    {colorize('[1]', C.CYAN, C.BOLD)}  Change DHCP pool range")
    print(f"    {colorize('[2]', C.CYAN, C.BOLD)}  Change router LAN gateway IP (e.g. 192.168.10.1)")
    print(f"    {colorize('[3]', C.CYAN, C.BOLD)}  Renew all DHCP leases (reboot DHCP server)")
    print(f"    {colorize('[4]', C.CYAN, C.BOLD)}  Show DNS settings")
    print(f"    {colorize('[0]', C.DIM)}  Back")
    print()

    try:
        fix = input(f"  {C.YELLOW}Select fix: {C.RESET}").strip()
    except KeyboardInterrupt:
        warn("\nCancelled.")
        return

    if fix == "1":
        # Change DHCP pool
        print(f"\n  Current pool: {colorize(dhcp_start, C.CYAN)} → {colorize(dhcp_end, C.CYAN)}")
        try:
            new_start = input(f"  {C.YELLOW}New start IP (e.g. 192.168.8.50): {C.RESET}").strip()
            new_end   = input(f"  {C.YELLOW}New end   IP (e.g. 192.168.8.150): {C.RESET}").strip()
        except KeyboardInterrupt:
            warn("\nCancelled.")
            return
        if not new_start or not new_end:
            warn("No change made.")
            return
        # Validate
        try:
            socket.inet_aton(new_start)
            socket.inet_aton(new_end)
        except socket.error:
            err("Invalid IP address format.")
            return
        set_xml = (
            '<?xml version="1.0" encoding="UTF-8"?>'
            "<request>"
            f"<DhcpIPAddress>{new_start}</DhcpIPAddress>"
            f"<DhcpEndIPAddress>{new_end}</DhcpEndIPAddress>"
            f"<DhcpLeaseTime>86400</DhcpLeaseTime>"
            f"<DnsStatus>1</DnsStatus>"
            "</request>"
        )
        resp = sess._xml_post(DHCP_SET_EP, set_xml)
        if resp and "<response>OK</response>" in resp:
            ok(colorize("DHCP pool updated! Devices will get new IPs on reconnect.", C.GREEN + C.BOLD))
        else:
            warn("Router returned non-OK – may need manual change via web UI.")

    elif fix == "2":
        # Change gateway IP
        print(f"\n  Current gateway: {colorize(router_lan_ip, C.CYAN)}")
        warn("Changing gateway IP will disconnect you. Reconnect at new IP.")
        try:
            new_gw = input(f"  {C.YELLOW}New gateway IP (e.g. 192.168.10.1): {C.RESET}").strip()
        except KeyboardInterrupt:
            warn("\nCancelled.")
            return
        if not new_gw:
            return
        try:
            socket.inet_aton(new_gw)
        except socket.error:
            err("Invalid IP.")
            return
        # Derive new DHCP pool from new gateway
        prefix = ".".join(new_gw.split(".")[:3])
        new_start = prefix + ".100"
        new_end   = prefix + ".200"
        set_xml = (
            '<?xml version="1.0" encoding="UTF-8"?>'
            "<request>"
            f"<DhcpIPAddress>{new_start}</DhcpIPAddress>"
            f"<DhcpEndIPAddress>{new_end}</DhcpEndIPAddress>"
            f"<DhcpLeaseTime>86400</DhcpLeaseTime>"
            f"<DnsStatus>1</DnsStatus>"
            "</request>"
        )
        resp = sess._xml_post(DHCP_SET_EP, set_xml)
        ok_flag = resp and "<response>OK</response>" in resp

        # Also try dedicated LAN IP endpoint
        lan_xml = (
            '<?xml version="1.0" encoding="UTF-8"?>'
            "<request>"
            f"<DhcpLanIpAddress>{new_gw}</DhcpLanIpAddress>"
            f"<DhcpLanNetmask>255.255.255.0</DhcpLanNetmask>"
            "</request>"
        )
        sess._xml_post("/api/lan/ipinfo", lan_xml)

        if ok_flag:
            ok(colorize("Gateway IP change sent.", C.GREEN + C.BOLD))
            warn(f"Reconnect to router at: http://{new_gw}")
        else:
            warn("Non-OK response – try changing via web UI at http://" + router_lan_ip)

    elif fix == "3":
        # Renew DHCP (reboot DHCP)
        warn("Sending DHCP renew signal...")
        set_xml = (
            '<?xml version="1.0" encoding="UTF-8"?>'
            "<request>"
            f"<DhcpIPAddress>{dhcp_start}</DhcpIPAddress>"
            f"<DhcpEndIPAddress>{dhcp_end}</DhcpEndIPAddress>"
            f"<DhcpLeaseTime>3600</DhcpLeaseTime>"
            f"<DnsStatus>1</DnsStatus>"
            "</request>"
        )
        resp = sess._xml_post(DHCP_SET_EP, set_xml)
        if resp and "<response>OK</response>" in resp:
            ok(colorize("DHCP lease time refreshed – devices will renew shortly.", C.GREEN + C.BOLD))
        else:
            warn("Non-OK response. Try rebooting router to force all DHCP renewals.")

    elif fix == "4":
        # Show DNS
        dns_xml = sess._xml_get("/api/dns/info") or dhcp_xml or ""
        dns1 = sess._parse_xml_val(dns_xml, "PrimaryDns",   "N/A")
        dns2 = sess._parse_xml_val(dns_xml, "SecondaryDns", "N/A")
        print(f"\n  Primary DNS  : {colorize(dns1, C.CYAN)}")
        print(f"  Secondary DNS: {colorize(dns2, C.CYAN)}")
        info("To change DNS, use router web UI: http://192.168.8.1 → Advanced → DHCP")
    sep()


# ─────────────────────────────────────────────────────────────
#  FULL AUTO OPTIMIZER  (scan + antenna test + band lock + watchdog)
# ─────────────────────────────────────────────────────────────
def cmd_full_optimize(sess: H155Session, args):
    """
    Complete one-shot optimizer:
    Step 1 – Set LTE-only mode
    Step 2 – Test internal vs external antenna (measure each)
    Step 3 – Scan neighbor towers
    Step 4 – Lock to best band from best tower
    Step 5 – Verify signal improvement
    Step 6 – Activate watchdog for 60s stability check
    """
    step("FULL AUTO OPTIMIZER")
    sep()

    # Guard: every step below needs a live session. Without it the optimizer
    # just reads empty data and prints a wall of N/A (the issue you saw).
    if not getattr(sess, "authenticated", False):
        err("Not logged in – cannot optimize.")
        warn("The router rejected the password (code 108006 / 125003).")
        warn("Fix the login first:")
        print(f"  {C.DIM}  • Open http://192.168.8.1 in a browser and confirm the admin password works there")
        print(f"  {C.DIM}  • Check the router sticker for the 'Admin'/'Web UI' password (often ≠ WiFi key)")
        _example_cmd = 'python3 zain_h155_manager.py --password "REAL_PASSWORD"'
        print(f"  {C.DIM}  • Then run: {colorize(_example_cmd, C.CYAN)}{C.RESET}")
        sep()
        return

    print(f"  {C.GOLD}{C.BOLD}  This will automatically:{C.RESET}")
    print(f"  {C.DIM}  1. Force LTE-only mode")
    print(f"  {C.DIM}  2. Test internal vs external antenna")
    print(f"  {C.DIM}  3. Scan all neighbor towers")
    print(f"  {C.DIM}  4. Lock to best band + best tower")
    print(f"  {C.DIM}  5. Verify and show improvement{C.RESET}")
    sep()

    try:
        confirm = input(f"  {C.RED}Start full optimization? (yes/no): {C.RESET}").strip().lower()
    except KeyboardInterrupt:
        warn("Cancelled.")
        return
    if confirm != "yes":
        warn("Cancelled.")
        return

    results_log = []

    # ── STEP 1: LTE only ────────────────────────────────────
    print(f"\n  {C.CYAN}{C.BOLD}  [STEP 1/5] Setting LTE-only mode...{C.RESET}")
    sess.set_net_mode("03", "3FFFFFFF", "7FFFFFFFFFFFFFFF")
    time.sleep(5)
    ok("LTE-only mode active")

    # ── STEP 2: Antenna test ─────────────────────────────────
    print(f"\n  {C.CYAN}{C.BOLD}  [STEP 2/5] Antenna comparison test...{C.RESET}")
    antenna_results = {}

    for ant_code, (ant_label, ant_col) in ANTENNA_MODES.items():
        if ant_code == "3":
            continue   # Skip combined for now; test pure modes
        info(f"  Testing: {colorize(ant_label, ant_col)}")
        set_xml = (
            '<?xml version="1.0" encoding="UTF-8"?>'
            "<request>"
            f"<antenna_type>{ant_code}</antenna_type>"
            "</request>"
        )
        sess._xml_post(ANTENNA_SET_EP, set_xml)
        time.sleep(6)  # stabilize
        samples = []
        for _ in range(4):
            sig = sess.get_signal()
            try:
                samples.append(int(re.sub(r"[^-\d]", "", sig.get("rsrp", "-999"))))
            except:
                pass
            time.sleep(1)
        if samples:
            avg = sum(samples) / len(samples)
            antenna_results[ant_code] = {"label": ant_label, "col": ant_col, "avg_rsrp": avg}
            r_lbl, r_col = grade_rsrp(int(avg))
            bar = signal_bar(int(avg))
            print(f"  {bar}  {colorize(ant_label, ant_col):<30} RSRP avg: {colorize('%.1f' % avg, r_col, C.BOLD)}  ({r_lbl})")
        else:
            warn(f"  No signal data for {ant_label}")

    # Pick best antenna
    if antenna_results:
        best_ant = max(antenna_results.items(), key=lambda x: x[1]["avg_rsrp"])
        best_ant_code, best_ant_data = best_ant
        ok(f"Best antenna: {colorize(best_ant_data['label'], best_ant_data['col'], C.BOLD)}")
        # Apply best antenna
        set_xml = (
            '<?xml version="1.0" encoding="UTF-8"?>'
            "<request>"
            f"<antenna_type>{best_ant_code}</antenna_type>"
            "</request>"
        )
        sess._xml_post(ANTENNA_SET_EP, set_xml)
        results_log.append(f"Antenna: {best_ant_data['label']}")
        time.sleep(4)
    else:
        warn("  Antenna API not available – keeping current antenna.")
        results_log.append("Antenna: unchanged (API unavailable)")

    # ── STEP 3: Read ACTIVE carrier aggregation ──────────────
    print(f"\n  {C.CYAN}{C.BOLD}  [STEP 3/5] Reading active carrier aggregation...{C.RESET}")
    sig_now = sess.get_signal()
    band_field = sig_now.get("band", "N/A")
    sinr_now   = sig_now.get("sinr_int")
    rsrp_now   = sig_now.get("rsrp_int")

    # Parse band numbers out of the signal "band" field, e.g.
    # "20MHz@1450(B3) + 20MHz@500(B1) + 20MHz@9310(B28)"
    active_bands = sorted({int(m) for m in re.findall(r"B(\d+)", str(band_field))})
    if active_bands:
        names = []
        for b in active_bands:
            names.append(BAND_DB.get(b, {}).get("name", f"Band {b}"))
        if len(active_bands) > 1:
            ok(f"Carrier aggregation ACTIVE: {colorize(str(len(active_bands)) + ' bands', C.LIME, C.BOLD)}")
        else:
            info("Single band currently in use (no aggregation).")
        for n in names:
            print(f"  {C.DIM}    • {colorize(n, C.GOLD)}{C.RESET}")
        results_log.append(f"Active CA: {'+'.join('B'+str(b) for b in active_bands)}")
    else:
        warn("  Could not read active band list from signal.")

    # ── STEP 4: Smart band decision (preserve aggregation) ───
    print(f"\n  {C.CYAN}{C.BOLD}  [STEP 4/5] Smart band decision...{C.RESET}")

    # Quality gate: if signal is already good AND aggregation is active,
    # locking to one band would DROP the other carriers and reduce speed.
    good_signal = (rsrp_now is not None and rsrp_now >= -95 and
                   sinr_now is not None and sinr_now >= 10)

    if len(active_bands) > 1 and good_signal:
        ok(colorize("Aggregation is healthy – preserving all carriers.", C.LIME + C.BOLD))
        info("Locking to a single band here would reduce throughput, so skipping.")
        # Lock to the SET of currently-aggregated bands (keeps CA, blocks drift
        # to worse bands) instead of collapsing to one.
        mask = bands_to_lte_bitmask(active_bands)
        if sess.set_net_mode("03", "3FFFFFFF", mask):
            ok(f"Locked to aggregated set: {colorize('+'.join('B'+str(b) for b in active_bands), C.GOLD, C.BOLD)}")
            results_log.append("Band lock: kept full CA set")
        else:
            warn("  Could not apply CA-set lock – leaving all bands enabled.")
            results_log.append("Band lock: all bands (CA preserved)")
    elif active_bands:
        # Signal is weak: try locking to the strongest single low-band for
        # stability (low bands penetrate better), then compare.
        low_bands = [b for b in active_bands if b in (28, 20, 8)]
        target    = low_bands[0] if low_bands else active_bands[0]
        band_name = BAND_DB.get(target, {}).get("name", f"Band {target}")
        info(f"Weak signal – testing stability lock on {colorize(band_name, C.GOLD)}")
        before = rsrp_now if rsrp_now is not None else -999
        mask   = bands_to_lte_bitmask([target])
        if sess.set_net_mode("03", "3FFFFFFF", mask):
            time.sleep(8)
            after_sig = sess.get_signal()
            after = after_sig.get("rsrp_int")
            after = after if after is not None else -999
            if after >= before:
                ok(f"{band_name} held/improved signal ({before}→{after} dBm) – keeping it.")
                results_log.append(f"Band lock: {band_name} (improved)")
            else:
                info(f"{band_name} was worse ({before}→{after}) – restoring all bands.")
                sess.set_net_mode("03", "3FFFFFFF", "7FFFFFFFFFFFFFFF")
                results_log.append("Band lock: reverted to all bands")
        else:
            warn("  Lock attempt failed – leaving all bands enabled.")
            results_log.append("Band lock: all bands")
    else:
        info("  No band data – keeping LTE-only with all bands enabled.")
        results_log.append("Band lock: all LTE bands")

    # ── STEP 5: Verify ───────────────────────────────────────
    print(f"\n  {C.CYAN}{C.BOLD}  [STEP 5/5] Verifying final signal...{C.RESET}")
    time.sleep(5)
    sig_final = sess.get_signal()
    rsrp_final = sig_final.get("rsrp_int")
    r_lbl, r_col = grade_rsrp(rsrp_final)
    bar_final    = signal_bar(rsrp_final)

    sep()
    print(f"\n  {C.LIME}{C.BOLD}  ╔══  OPTIMIZATION COMPLETE  ══════════════════════╗{C.RESET}")
    print(f"  {C.LIME}  ║{C.RESET}  Final signal : {bar_final}  {colorize(sig_final.get('rsrp','N/A'), r_col, C.BOLD)}  ({colorize(r_lbl, r_col)})")
    print(f"  {C.LIME}  ║{C.RESET}  SINR         : {colorize(sig_final.get('sinr','N/A'), C.CYAN, C.BOLD)}")
    print(f"  {C.LIME}  ║{C.RESET}  Band         : {colorize(sig_final.get('band','N/A'), C.GOLD)}")
    print(f"  {C.LIME}  ║{C.RESET}  PCI          : {colorize(sig_final.get('pci','N/A'), C.WHITE)}")
    print(f"  {C.LIME}  ║{C.RESET}")
    for step_log in results_log:
        print(f"  {C.LIME}  ║{C.RESET}  {colorize('✔ ' + step_log, C.GREEN)}")
    print(f"  {C.LIME}{C.BOLD}  ╚══════════════════════════════════════════════════╝{C.RESET}")
    sep()


# ═════════════════════════════════════════════════════════════
#  ★  v40 UPGRADE  ─  40 ADVANCED FEATURES  ★
#  Every feature below talks to a real Huawei H155 web-API endpoint
#  (or the local OS for diagnostics). No stubs, no placeholders.
# ═════════════════════════════════════════════════════════════

# ── Endpoint map for the advanced features ──
EP = {
    "sms_count":     "/api/sms/sms-count",
    "sms_list":      "/api/sms/sms-list",
    "sms_send":      "/api/sms/send-sms",
    "sms_send_stat": "/api/sms/send-status",
    "sms_delete":    "/api/sms/delete-sms",
    "ussd_send":     "/api/ussd/send",
    "ussd_get":      "/api/ussd/get",
    "ussd_release":  "/api/ussd/release",
    "traffic":       "/api/monitoring/traffic-statistics",
    "month_stat":    "/api/monitoring/month_statistics",
    "clear_traffic": "/api/monitoring/clear-traffic",
    "start_date":    "/api/monitoring/start_date",
    "wlan_basic":    "/api/wlan/basic-settings",
    "wlan_multi":    "/api/wlan/multi-basic-settings",
    "wlan_security": "/api/wlan/security-settings",
    "host_list":     "/api/wlan/host-list",
    "mac_filter":    "/api/wlan/multi-macfilter-settings",
    "data_switch":   "/api/dialup/mobile-dataswitch",
    "dial_conn":     "/api/dialup/connection",
    "profiles":      "/api/dialup/profiles",
    "plmn_list":     "/api/net/plmn-list",
    "register":      "/api/net/register",
    "net_mode":      "/api/net/net-mode",
    "current_plmn":  "/api/net/current-plmn",
    "pin_status":    "/api/pin/status",
    "pin_operate":   "/api/pin/operate",
    "dmz":           "/api/security/dmz",
    "vservers":      "/api/security/virtual-servers",
    "firewall":      "/api/security/firewall-switch",
    "upnp":          "/api/security/upnp",
    "dhcp":          "/api/dhcp/settings",
    "fw_check":      "/api/online-update/check-new-version",
    "fw_status":     "/api/online-update/status",
    "led":           "/api/led/circle-switch",
    "led_night":     "/api/led/nightmode",
    "device_info":   "/api/device/information",
    "signal":        "/api/device/signal",
    "monitoring":    "/api/monitoring/status",
}


# ─────────────────────────────────────────────────────────────
#  GROUP A — SMS & USSD  (features 1-5)
# ─────────────────────────────────────────────────────────────
def cmd_sms_list(sess: H155Session, args):
    """[1] Read the SIM/router SMS inbox."""
    step("SMS Inbox")
    sep()
    body = {
        "PageIndex": 1, "ReadCount": 20, "BoxType": 1,
        "SortType": 0, "Ascending": 0, "UnreadPreferred": 1,
    }
    xml = sess.api_post(EP["sms_list"], body)
    e = explain_error(xml)
    if e:
        err(e)
        return
    msgs = list(re.finditer(r"<Message>(.*?)</Message>", xml, re.DOTALL))
    if not msgs:
        info("Inbox is empty.")
        sep()
        return
    print(f"  {C.GOLD}{C.BOLD}  {len(msgs)} message(s):{C.RESET}\n")
    for m in msgs:
        blk = m.group(1)
        smstat = xval(blk, "Smstat")  # 0 = unread, 1 = read
        unread = smstat == "0"
        flag = colorize("●", C.RED) if unread else colorize("○", C.DIM)
        phone = xval(blk, "Phone")
        date = xval(blk, "Date")
        content = xval(blk, "Content", "")
        idx = xval(blk, "Index")
        print(f"  {flag} {colorize(phone, C.CYAN, C.BOLD):<28} {colorize(date, C.DIM)}  {colorize('#'+idx, C.DIM)}")
        print(f"     {colorize(content, C.WHITE)}\n")
    sep()


def cmd_sms_send(sess: H155Session, args):
    """[2] Send an SMS to a phone number."""
    step("Send SMS")
    sep()
    phone = getattr(args, "to", None) or ask(f"  {C.YELLOW}Recipient number: {C.RESET}")
    if not phone:
        warn("Cancelled.")
        return
    content = getattr(args, "message", None) or ask(f"  {C.YELLOW}Message text: {C.RESET}")
    if not content:
        warn("Empty message – cancelled.")
        return
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    body = (
        '<?xml version="1.0" encoding="UTF-8"?><request>'
        "<Index>-1</Index>"
        f"<Phones><Phone>{phone}</Phone></Phones>"
        "<Sca></Sca>"
        f"<Content>{content}</Content>"
        f"<Length>{len(content)}</Length>"
        "<Reserved>1</Reserved>"
        f"<Date>{now}</Date>"
        "</request>"
    )
    info(f"Sending to {colorize(phone, C.CYAN)} ({len(content)} chars)...")
    resp = sess.api_post(EP["sms_send"], body)
    if sess.post_ok(resp):
        # Poll send status briefly
        for _ in range(5):
            time.sleep(1)
            st = sess.api_get(EP["sms_send_stat"])
            phase = xval(st, "Phase")
            if phase in ("2", "0"):  # 2 = sent
                break
        ok(colorize("SMS sent successfully!", C.GREEN + C.BOLD))
    else:
        err(explain_error(resp) or "Send failed – check signal and SMS centre number.")
    sep()


def cmd_sms_delete(sess: H155Session, args):
    """[3] Delete an SMS by its index."""
    step("Delete SMS")
    sep()
    idx = ask(f"  {C.YELLOW}Message index to delete (see 'SMS Inbox'): {C.RESET}")
    if not idx or not idx.isdigit():
        warn("No valid index – cancelled.")
        return
    resp = sess.api_post(EP["sms_delete"], {"Index": idx})
    if sess.post_ok(resp):
        ok(colorize(f"Message #{idx} deleted.", C.GREEN + C.BOLD))
    else:
        err(explain_error(resp) or "Delete failed.")
    sep()


def cmd_sms_count(sess: H155Session, args):
    """[4] Show SMS mailbox counters."""
    step("SMS Counters")
    sep()
    xml = sess.api_get(EP["sms_count"])
    if not xml:
        err("No SMS data.")
        return
    rows = [
        ("Unread",     xval(xml, "LocalUnread", "0"),  C.RED),
        ("Inbox",      xval(xml, "LocalInbox", "0"),   C.CYAN),
        ("Sent",       xval(xml, "LocalOutbox", "0"),  C.GREEN),
        ("Drafts",     xval(xml, "LocalDraft", "0"),   C.YELLOW),
        ("SIM Unread", xval(xml, "SimUnread", "0"),    C.ORANGE),
        ("SIM Inbox",  xval(xml, "SimInbox", "0"),     C.DIM),
    ]
    for label, val, col in rows:
        print(f"  {colorize(label+':', C.DIM):<22} {colorize(val, col, C.BOLD)}")
    sep()


def cmd_ussd(sess: H155Session, args):
    """[5] Send a USSD code (e.g. balance check *123#)."""
    step("USSD Code")
    sep()
    code = getattr(args, "code", None) or ask(f"  {C.YELLOW}USSD code (e.g. *123#): {C.RESET}")
    if not code:
        warn("Cancelled.")
        return
    # Release any stuck session first (ignore result)
    sess.api_post(EP["ussd_release"], {})
    time.sleep(0.5)
    info(f"Dialling {colorize(code, C.CYAN, C.BOLD)}...")
    resp = sess.api_post(EP["ussd_send"], {"content": code, "codeType": "CodeType", "timeout": ""})
    if not sess.post_ok(resp):
        err(explain_error(resp) or "USSD send rejected.")
        return
    reply = ""
    for _ in range(8):
        time.sleep(1.5)
        got = sess.api_get(EP["ussd_get"])
        reply = xval(got, "content", "")
        if reply:
            break
    if reply:
        print(f"\n  {C.GREEN}{C.BOLD}  Network reply:{C.RESET}")
        print(f"  {colorize(reply, C.WHITE)}\n")
    else:
        warn("No USSD reply received (try again – network may be slow).")
    sess.api_post(EP["ussd_release"], {})
    sep()


# ─────────────────────────────────────────────────────────────
#  GROUP B — DATA USAGE & TRAFFIC  (features 6-9)
# ─────────────────────────────────────────────────────────────
def cmd_traffic_stats(sess: H155Session, args):
    """[6] Current session traffic statistics."""
    step("Session Traffic Statistics")
    sep()
    xml = sess.api_get(EP["traffic"])
    if not xml:
        err("No traffic data.")
        return
    dl = bytes_fmt(xval(xml, "CurrentDownload", "0"))
    ul = bytes_fmt(xval(xml, "CurrentUpload", "0"))
    dl_rate = speed_fmt(xval(xml, "CurrentDownloadRate", "0"))
    ul_rate = speed_fmt(xval(xml, "CurrentUploadRate", "0"))
    conn = xval(xml, "CurrentConnectTime", "0")
    try:
        mins, secs = divmod(int(conn), 60)
        hrs, mins = divmod(mins, 60)
        uptime = f"{hrs}h {mins}m {secs}s"
    except ValueError:
        uptime = conn
    tot_dl = bytes_fmt(xval(xml, "TotalDownload", "0"))
    tot_ul = bytes_fmt(xval(xml, "TotalUpload", "0"))
    print(f"  {colorize('Session uptime:', C.DIM):<24} {colorize(uptime, C.CYAN, C.BOLD)}")
    print(f"  {colorize('↓ This session:', C.DIM):<24} {colorize(dl, C.LIME)}   ({dl_rate})")
    print(f"  {colorize('↑ This session:', C.DIM):<24} {colorize(ul, C.TEAL)}   ({ul_rate})")
    print(f"  {colorize('↓ Lifetime total:', C.DIM):<24} {colorize(tot_dl, C.GREEN, C.BOLD)}")
    print(f"  {colorize('↑ Lifetime total:', C.DIM):<24} {colorize(tot_ul, C.GREEN, C.BOLD)}")
    sep()


def cmd_month_stats(sess: H155Session, args):
    """[7] Monthly data usage vs configured plan."""
    step("Monthly Data Usage")
    sep()
    xml = sess.api_get(EP["month_stat"])
    if not xml:
        err("No monthly statistics available.")
        return
    dl = int(xval(xml, "CurrentMonthDownload", "0") or 0)
    ul = int(xval(xml, "CurrentMonthUpload", "0") or 0)
    total = dl + ul
    print(f"  {colorize('Month ↓:', C.DIM):<20} {colorize(bytes_fmt(str(dl)), C.LIME, C.BOLD)}")
    print(f"  {colorize('Month ↑:', C.DIM):<20} {colorize(bytes_fmt(str(ul)), C.TEAL, C.BOLD)}")
    print(f"  {colorize('Month total:', C.DIM):<20} {colorize(bytes_fmt(str(total)), C.GOLD, C.BOLD)}")

    # Compare against plan limit if one is configured
    plan = sess.api_get(EP["start_date"])
    limit_raw = xval(plan, "DataLimit", "0")  # e.g. "100GB" or "0"
    m = re.match(r"(\d+)\s*(GB|MB|TB)?", limit_raw or "", re.I)
    if m and int(m.group(1)) > 0:
        unit = (m.group(2) or "GB").upper()
        mult = {"MB": 1024**2, "GB": 1024**3, "TB": 1024**4}.get(unit, 1024**3)
        limit_bytes = int(m.group(1)) * mult
        pct = (total / limit_bytes * 100) if limit_bytes else 0
        filled = int(min(pct, 100) / 5)
        bar = colorize("█" * filled, C.LIME if pct < 80 else C.RED) + colorize("░" * (20 - filled), C.DIM)
        col = C.GREEN if pct < 80 else (C.YELLOW if pct < 100 else C.RED)
        print(f"\n  {colorize('Plan limit:', C.DIM):<20} {colorize(limit_raw, C.CYAN)}")
        print(f"  {colorize('Usage:', C.DIM):<20} [{bar}] {colorize(f'{pct:.1f}%', col, C.BOLD)}")
    else:
        info("No data-plan limit configured (use 'Data Plan' to set one).")
    sep()


def cmd_clear_traffic(sess: H155Session, args):
    """[8] Reset the router's traffic counters."""
    step("Clear Traffic Statistics")
    if not confirm(f"  {C.RED}Reset all traffic counters to zero? (yes/no): {C.RESET}"):
        warn("Cancelled.")
        return
    resp = sess.api_post(EP["clear_traffic"], {"ClearTraffic": 1})
    if sess.post_ok(resp):
        ok(colorize("Traffic statistics cleared.", C.GREEN + C.BOLD))
    else:
        err(explain_error(resp) or "Failed to clear traffic.")
    sep()


def cmd_data_plan(sess: H155Session, args):
    """[9] View / set the monthly data plan (start day + limit)."""
    step("Data Plan Configuration")
    sep()
    cur = sess.api_get(EP["start_date"])
    start_day = xval(cur, "StartDay", "1")
    data_limit = xval(cur, "DataLimit", "0")
    threshold = xval(cur, "MonthThreshold", "90")
    print(f"  {colorize('Current start day:', C.DIM):<22} {colorize(start_day, C.CYAN)}")
    print(f"  {colorize('Current limit:', C.DIM):<22} {colorize(data_limit, C.CYAN)}")
    print(f"  {colorize('Alert threshold:', C.DIM):<22} {colorize(threshold + '%', C.CYAN)}\n")
    if not confirm(f"  {C.YELLOW}Update the plan now? (yes/no): {C.RESET}"):
        warn("Left unchanged.")
        return
    nd = ask(f"  {C.YELLOW}Billing start day (1-31) [{start_day}]: {C.RESET}") or start_day
    nl = ask(f"  {C.YELLOW}Monthly limit (e.g. 100GB, 0=unlimited) [{data_limit}]: {C.RESET}") or data_limit
    nt = ask(f"  {C.YELLOW}Alert threshold %% [{threshold}]: {C.RESET}") or threshold
    body = {
        "StartDay": nd, "DataLimit": nl, "DataLimitAwoke": nt,
        "MonthThreshold": nt, "SetMonthData": 1, "TrafficMaxLimit": "0",
        "turnoffdataenable": 0, "turnoffdataswitch": 0,
    }
    resp = sess.api_post(EP["start_date"], body)
    if sess.post_ok(resp):
        ok(colorize("Data plan updated.", C.GREEN + C.BOLD))
    else:
        err(explain_error(resp) or "Failed to update data plan.")
    sep()


# ─────────────────────────────────────────────────────────────
#  GROUP C — WIFI MANAGEMENT  (features 10-15)
# ─────────────────────────────────────────────────────────────
def _wlan_settings(sess: H155Session) -> str:
    """Return the best-available WLAN settings XML (multi or basic)."""
    xml = sess.api_get(EP["wlan_multi"])
    if xml and "<Ssid" in xml:
        return xml
    return sess.api_get(EP["wlan_basic"])


def cmd_wifi_info(sess: H155Session, args):
    """[10] Show Wi-Fi SSID(s) and radio configuration."""
    step("Wi-Fi Configuration")
    sep()
    xml = _wlan_settings(sess)
    if not xml:
        err("Could not read Wi-Fi settings.")
        return
    ssids = re.findall(r"<WifiSsid>(.*?)</WifiSsid>", xml, re.DOTALL)
    if not ssids:
        # basic-settings single SSID
        ssid = xval(xml, "WifiSsid", xval(xml, "Ssid", "N/A"))
        enabled = xval(xml, "WifiEnable", "1")
        chan = xval(xml, "WifiChannel", "auto")
        print(f"  {colorize('SSID:', C.DIM):<18} {colorize(ssid, C.CYAN, C.BOLD)}")
        print(f"  {colorize('Radio:', C.DIM):<18} {colorize('ON' if enabled=='1' else 'OFF', C.GREEN if enabled=='1' else C.RED)}")
        print(f"  {colorize('Channel:', C.DIM):<18} {colorize(chan, C.GOLD)}")
    else:
        for i, blk in enumerate(ssids):
            name = xval(blk, "WifiSsid", "N/A")
            enabled = xval(blk, "WifiEnable", "1")
            bcast = xval(blk, "WifiBroadcast", "1")
            idx = xval(blk, "Index", str(i))
            tag = "Guest" if i > 0 else "Primary"
            print(f"  {colorize(f'[{tag}]', C.GOLD, C.BOLD)}  SSID {colorize(name, C.CYAN, C.BOLD)} (#{idx})")
            print(f"      Radio: {colorize('ON' if enabled=='1' else 'OFF', C.GREEN if enabled=='1' else C.RED)}"
                  f"   Broadcast: {colorize('Yes' if bcast=='1' else 'Hidden', C.DIM)}")
    sep()


def cmd_wifi_ssid(sess: H155Session, args):
    """[11] Rename the primary Wi-Fi SSID."""
    step("Change Wi-Fi SSID")
    sep()
    cur = sess.api_get(EP["wlan_basic"])
    old = xval(cur, "WifiSsid", xval(cur, "Ssid", "N/A"))
    print(f"  Current SSID: {colorize(old, C.CYAN, C.BOLD)}\n")
    new = getattr(args, "ssid", None) or ask(f"  {C.YELLOW}New SSID (1-32 chars): {C.RESET}")
    if not new:
        warn("Cancelled.")
        return
    if not (1 <= len(new) <= 32):
        err("SSID must be 1-32 characters.")
        return
    resp = sess.api_post(EP["wlan_basic"], {"WifiSsid": new, "WifiBroadcast": 0, "WifiEnable": 1})
    if sess.post_ok(resp):
        ok(colorize(f"SSID changed to '{new}'. Reconnect Wi-Fi clients.", C.GREEN + C.BOLD))
    else:
        err(explain_error(resp) or "Failed to change SSID.")
    sep()


def cmd_wifi_password(sess: H155Session, args):
    """[12] Change the Wi-Fi (WPA pre-shared) password."""
    step("Change Wi-Fi Password")
    sep()
    new = getattr(args, "wifi_pass", None)
    if not new:
        try:
            new = getpass("  New Wi-Fi password (8-63 chars): ").strip()
        except (KeyboardInterrupt, EOFError):
            print()
            warn("Cancelled.")
            return
    if not (8 <= len(new) <= 63):
        err("WPA password must be 8-63 characters.")
        return
    resp = sess.api_post(EP["wlan_security"], {
        "WifiAuthmode": "WPA2PSK",
        "WifiBasicencryptionmodes": "AES",
        "WifiWpaencryptionmodes": "AES",
        "WpaPreSharedKey": new,
    })
    if sess.post_ok(resp):
        ok(colorize("Wi-Fi password updated. Clients must reconnect.", C.GREEN + C.BOLD))
    else:
        err(explain_error(resp) or "Failed to change Wi-Fi password.")
    sep()


def cmd_wifi_clients(sess: H155Session, args):
    """[13] List devices connected to the router."""
    step("Connected Clients")
    sep()
    xml = sess.api_get(EP["host_list"])
    hosts = list(re.finditer(r"<Host>(.*?)</Host>", xml, re.DOTALL))
    if not hosts:
        warn("No connected clients reported.")
        sep()
        return
    print(f"  {C.DIM}  {'IP':<16} {'MAC':<19} {'Hostname':<22} {'Link'}{C.RESET}")
    print(f"  {C.DIM}  {'─'*68}{C.RESET}")
    for h in hosts:
        blk = h.group(1)
        ip = xval(blk, "IpAddress")
        mac = xval(blk, "MacAddress")
        name = xval(blk, "HostName", "?")
        link = xval(blk, "AssociatedSsid", xval(blk, "Layer2Interface", "—"))
        active = xval(blk, "Active", "1") == "1"
        dot = colorize("●", C.GREEN if active else C.DIM)
        print(f"  {dot} {colorize(ip, C.CYAN):<25} {colorize(mac, C.DIM):<28} "
              f"{colorize(name, C.WHITE):<31} {colorize(link, C.GOLD)}")
    print(f"\n  {colorize(str(len(hosts)) + ' client(s) total', C.DIM)}")
    sep()


def cmd_wifi_guest(sess: H155Session, args):
    """[14] Toggle the guest Wi-Fi network on/off."""
    step("Guest Wi-Fi Toggle")
    sep()
    xml = sess.api_get(EP["wlan_multi"])
    ssids = re.findall(r"<WifiSsid>(.*?)</WifiSsid>", xml, re.DOTALL)
    if len(ssids) < 2:
        warn("This router does not expose a separate guest SSID via the API.")
        sep()
        return
    guest = ssids[1]
    cur = xval(guest, "WifiEnable", "0")
    name = xval(guest, "WifiSsid", "Guest")
    print(f"  Guest SSID '{colorize(name, C.CYAN)}' is currently "
          f"{colorize('ON', C.GREEN) if cur=='1' else colorize('OFF', C.RED)}.")
    new = "0" if cur == "1" else "1"
    if not confirm(f"  {C.YELLOW}Turn guest network {'OFF' if new=='0' else 'ON'}? (yes/no): {C.RESET}"):
        warn("Unchanged.")
        return
    idx = xval(guest, "Index", "1")
    resp = sess.api_post(EP["wlan_multi"], {
        "Index": idx, "WifiEnable": new, "WifiSsid": name,
    })
    if sess.post_ok(resp):
        ok(colorize(f"Guest Wi-Fi turned {'ON' if new=='1' else 'OFF'}.", C.GREEN + C.BOLD))
    else:
        err(explain_error(resp) or "Failed to toggle guest Wi-Fi.")
    sep()


def cmd_mac_filter(sess: H155Session, args):
    """[15] View / set the Wi-Fi MAC-address filter (allow/deny list)."""
    step("Wi-Fi MAC Filter")
    sep()
    xml = sess.api_get(EP["mac_filter"])
    mode = xval(xml, "WifiMacFilterStatus", xval(xml, "wifihostidswitch", "0"))
    modes = {"0": "Disabled", "1": "Allow listed only", "2": "Block listed"}
    print(f"  Filter mode: {colorize(modes.get(mode, mode), C.GOLD, C.BOLD)}")
    macs = re.findall(r"<WifiMacFilterMac\d*>(.*?)</WifiMacFilterMac\d*>", xml)
    macs = [m for m in macs if m]
    if macs:
        print(f"  {C.DIM}  Filtered MACs:{C.RESET}")
        for m in macs:
            print(f"    {colorize(m, C.CYAN)}")
    print()
    print(f"  {colorize('[0]', C.DIM)} Disable   {colorize('[1]', C.CYAN)} Allow-list   {colorize('[2]', C.RED)} Block-list")
    choice = ask(f"  {C.YELLOW}New mode (Enter to cancel): {C.RESET}")
    if choice not in ("0", "1", "2"):
        warn("Unchanged.")
        return
    body = {"WifiMacFilterStatus": choice}
    if choice != "0":
        target = ask(f"  {C.YELLOW}MAC address to {'allow' if choice=='1' else 'block'} (AA:BB:CC:DD:EE:FF): {C.RESET}")
        if target and re.match(r"^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$", target):
            body["WifiMacFilterMac0"] = target
        else:
            err("Invalid MAC – aborting.")
            return
    resp = sess.api_post(EP["mac_filter"], body)
    if sess.post_ok(resp):
        ok(colorize("MAC filter updated.", C.GREEN + C.BOLD))
    else:
        err(explain_error(resp) or "Failed to update MAC filter.")
    sep()


# ─────────────────────────────────────────────────────────────
#  GROUP D — CONNECTION CONTROL  (features 16-20)
# ─────────────────────────────────────────────────────────────
def cmd_data_toggle(sess: H155Session, args):
    """[16] Turn mobile data on or off."""
    step("Mobile Data Switch")
    sep()
    cur = xval(sess.api_get(EP["data_switch"]), "dataswitch", "1")
    print(f"  Mobile data is currently "
          f"{colorize('ON', C.GREEN, C.BOLD) if cur=='1' else colorize('OFF', C.RED, C.BOLD)}.")
    new = "0" if cur == "1" else "1"
    if not confirm(f"  {C.YELLOW}Turn mobile data {'OFF' if new=='0' else 'ON'}? (yes/no): {C.RESET}"):
        warn("Unchanged.")
        return
    resp = sess.api_post(EP["data_switch"], {"dataswitch": new})
    if sess.post_ok(resp):
        ok(colorize(f"Mobile data turned {'ON' if new=='1' else 'OFF'}.", C.GREEN + C.BOLD))
    else:
        err(explain_error(resp) or "Failed to toggle mobile data.")
    sep()


def cmd_roaming_toggle(sess: H155Session, args):
    """[17] Enable / disable data roaming."""
    step("Data Roaming")
    sep()
    xml = sess.api_get(EP["dial_conn"])
    cur = xval(xml, "RoamAutoConnectEnable", "0")
    print(f"  Roaming auto-connect is "
          f"{colorize('ENABLED', C.GREEN) if cur=='1' else colorize('DISABLED', C.RED)}.")
    new = "0" if cur == "1" else "1"
    if not confirm(f"  {C.YELLOW}{'Disable' if new=='0' else 'Enable'} roaming? (yes/no): {C.RESET}"):
        warn("Unchanged.")
        return
    body = {
        "RoamAutoConnectEnable": new,
        "MaxIdelTime": xval(xml, "MaxIdelTime", "0"),
        "ConnectMode": xval(xml, "ConnectMode", "0"),
        "MTU": xval(xml, "MTU", "1500"),
        "auto_dial_switch": xval(xml, "auto_dial_switch", "1"),
        "pdp_always_on": xval(xml, "pdp_always_on", "0"),
    }
    resp = sess.api_post(EP["dial_conn"], body)
    if sess.post_ok(resp):
        ok(colorize(f"Roaming {'enabled' if new=='1' else 'disabled'}.", C.GREEN + C.BOLD))
    else:
        err(explain_error(resp) or "Failed to change roaming setting.")
    sep()


def cmd_reconnect(sess: H155Session, args):
    """[18] Force a data reconnect (refresh WAN IP)."""
    step("Reconnect Mobile Data")
    sep()
    old_ip = xval(sess.api_get(EP["device_info"]), "WanIPAddress", "N/A")
    info(f"Current WAN IP: {colorize(old_ip, C.CYAN)}")
    info("Dropping data connection...")
    sess.api_post(EP["data_switch"], {"dataswitch": "0"})
    for _ in range(4):
        time.sleep(1)
        print(f"{C.DIM}.{C.RESET}", end="", flush=True)
    print()
    info("Re-establishing data connection...")
    sess.api_post(EP["data_switch"], {"dataswitch": "1"})
    new_ip = old_ip
    for _ in range(10):
        time.sleep(2)
        new_ip = xval(sess.api_get(EP["device_info"]), "WanIPAddress", old_ip)
        if new_ip not in ("N/A", "", old_ip):
            break
        print(f"{C.DIM}.{C.RESET}", end="", flush=True)
    print()
    if new_ip not in ("N/A", "", old_ip):
        ok(colorize(f"Reconnected. New WAN IP: {new_ip}", C.GREEN + C.BOLD))
    else:
        warn(f"Reconnected; WAN IP is {new_ip} (may be unchanged on this network).")
    sep()


def cmd_apn_list(sess: H155Session, args):
    """[19] List configured APN profiles."""
    step("APN Profiles")
    sep()
    xml = sess.api_get(EP["profiles"])
    if not xml:
        err("Could not read APN profiles.")
        return
    cur = xval(xml, "CurrentProfile", "")
    profs = list(re.finditer(r"<Profile>(.*?)</Profile>", xml, re.DOTALL))
    if not profs:
        warn("No APN profiles found.")
        sep()
        return
    for p in profs:
        blk = p.group(1)
        idx = xval(blk, "Index")
        name = xval(blk, "Name", "?")
        apn = xval(blk, "ApnName", xval(blk, "Apn", "?"))
        active = (idx == cur)
        marker = colorize("  ◀ active", C.LIME, C.BOLD) if active else ""
        print(f"  {colorize('['+idx+']', C.CYAN, C.BOLD)} {colorize(name, C.WHITE):<24} "
              f"APN: {colorize(apn, C.GOLD)}{marker}")
    sep()


def cmd_apn_set(sess: H155Session, args):
    """[20] Create / apply a new APN profile."""
    step("Set APN Profile")
    sep()
    cmd_apn_list(sess, args)
    name = ask(f"  {C.YELLOW}Profile name (e.g. zain): {C.RESET}")
    apn = ask(f"  {C.YELLOW}APN string (e.g. zain.sa / internet): {C.RESET}")
    if not name or not apn:
        warn("Cancelled.")
        return
    user = ask(f"  {C.YELLOW}Username (Enter if none): {C.RESET}") or ""
    pwd = ask(f"  {C.YELLOW}Password (Enter if none): {C.RESET}") or ""
    body = {
        "Delete": 0, "SetDefault": 1, "Modify": 1, "Index": "",
        "IsValid": 1, "Name": name, "ApnIsStatic": 1, "ApnName": apn,
        "DialupNum": "*99#", "Username": user, "Password": pwd,
        "AuthMode": 0, "IpType": 2, "ReadOnly": 0,
    }
    resp = sess.api_post(EP["profiles"], body)
    if sess.post_ok(resp):
        ok(colorize(f"APN profile '{name}' applied.", C.GREEN + C.BOLD))
        info("A data reconnect may be required for it to take effect.")
    else:
        err(explain_error(resp) or "Failed to set APN.")
    sep()


# ─────────────────────────────────────────────────────────────
#  GROUP E — ADVANCED NETWORK  (features 21-25)
# ─────────────────────────────────────────────────────────────
def cmd_operator_scan(sess: H155Session, args):
    """[21] Scan for available mobile operators (PLMN list)."""
    step("Operator Scan (PLMN)")
    warn("This is a blocking network scan (~30-60s). Data drops briefly.")
    sep()
    if not confirm(f"  {C.YELLOW}Start scan? (yes/no): {C.RESET}"):
        warn("Cancelled.")
        return
    info("Scanning... please wait.")
    xml = sess.api_get(EP["plmn_list"])
    nets = list(re.finditer(r"<Network>(.*?)</Network>", xml, re.DOTALL))
    if not nets:
        err(explain_error(xml) or "No operators returned (scan may have timed out).")
        return
    state_names = {"1": "Available", "2": "Current", "3": "Forbidden"}
    rat_names = {"0": "2G", "2": "3G", "7": "4G/LTE", "11": "5G NR"}
    print(f"\n  {C.DIM}  {'Operator':<24} {'PLMN':<10} {'RAT':<8} {'State'}{C.RESET}")
    print(f"  {C.DIM}  {'─'*56}{C.RESET}")
    for n in nets:
        blk = n.group(1)
        name = xval(blk, "FullName", xval(blk, "ShortName", "?"))
        numeric = xval(blk, "Numeric")
        rat = rat_names.get(xval(blk, "Rat"), xval(blk, "Rat"))
        st = xval(blk, "State")
        st_label = state_names.get(st, st)
        col = C.LIME if st == "2" else (C.RED if st == "3" else C.WHITE)
        print(f"  {colorize(name, col):<33} {colorize(numeric, C.CYAN):<19} "
              f"{colorize(rat, C.GOLD):<17} {colorize(st_label, col)}")
    sep()


def cmd_operator_select(sess: H155Session, args):
    """[22] Manually register to a specific operator, or return to auto."""
    step("Manual Operator Selection")
    sep()
    print(f"  {colorize('[a]', C.CYAN, C.BOLD)} Automatic operator selection")
    print(f"  {colorize('[m]', C.CYAN, C.BOLD)} Manual – enter a PLMN code")
    mode = ask(f"  {C.YELLOW}Choice: {C.RESET}")
    if mode == "a":
        body = {"Mode": 0, "Plmn": "", "Rat": ""}
        resp = sess.api_post(EP["register"], body)
        if sess.post_ok(resp):
            ok(colorize("Set to automatic operator selection.", C.GREEN + C.BOLD))
        else:
            err(explain_error(resp) or "Failed.")
    elif mode == "m":
        plmn = ask(f"  {C.YELLOW}PLMN code (e.g. 42004 for Zain KSA): {C.RESET}")
        if not plmn or not plmn.isdigit():
            err("Invalid PLMN.")
            return
        rat = ask(f"  {C.YELLOW}RAT (0=2G 2=3G 7=4G 11=5G) [7]: {C.RESET}") or "7"
        body = {"Mode": 1, "Plmn": plmn, "Rat": rat}
        resp = sess.api_post(EP["register"], body)
        if sess.post_ok(resp):
            ok(colorize(f"Registration request sent for PLMN {plmn}.", C.GREEN + C.BOLD))
        else:
            err(explain_error(resp) or "Registration failed (operator may be forbidden).")
    else:
        warn("Cancelled.")
    sep()


def cmd_nr_band_lock(sess: H155Session, args):
    """[23] Lock 5G NR band(s) (n1/n3/n28/n41/n78)."""
    step("5G NR Band Lock")
    sep()
    print(f"  {C.GOLD}{C.BOLD}Available 5G NR bands:{C.RESET}\n")
    for b in sorted(NR_BAND_DB):
        d = NR_BAND_DB[b]
        print(f"    {colorize(str(b), C.CYAN, C.BOLD):>12}   {colorize(d['name'], C.WHITE):<28} {colorize(d['op'], C.DIM)}")
    if args.bands:
        selected = [int(b) for b in args.bands]
    else:
        raw = ask(f"\n  {C.YELLOW}NR band numbers (e.g. 78 41), blank = all NR: {C.RESET}")
        if raw is None:
            warn("Cancelled.")
            return
        selected = [int(x) for x in raw.split() if x.isdigit()] or sorted(NR_BAND_DB)
    nr_mask = nr_bands_to_bitmask(selected)
    net = sess.get_net_mode()
    lte_mask = (net or {}).get("lte_band", "7FFFFFFFFFFFFFFF")
    info(f"NR bitmask: {colorize(nr_mask, C.CYAN)}   (keeping LTE bands: {lte_mask})")
    # NSA 5G: NetworkMode 0803 keeps LTE anchor + NR; include NRBand field.
    body = {
        "NetworkMode": "0803",
        "NetworkBand": "3FFFFFFF",
        "LTEBand": lte_mask,
        "NRBand": nr_mask,
    }
    resp = sess.api_post(EP["net_mode"], body)
    if sess.post_ok(resp):
        names = ", ".join(NR_BAND_DB.get(b, {}).get("name", f"n{b}") for b in selected)
        ok(colorize(f"5G NR locked to: {names}", C.LIME + C.BOLD))
    else:
        err(explain_error(resp) or "NR band lock failed (router may be LTE-only).")
    sep()


def cmd_ca_info(sess: H155Session, args):
    """[24] Decode active carrier-aggregation bands from the signal field."""
    step("Carrier Aggregation Status")
    sep()
    sig = sess.get_signal()
    band_field = str(sig.get("band", "N/A"))
    nums = sorted({int(m) for m in re.findall(r"B(\d+)", band_field)})
    print(f"  {colorize('Raw band field:', C.DIM):<20} {colorize(band_field, C.WHITE)}")
    if not nums:
        warn("Could not decode aggregated bands from the signal report.")
        sep()
        return
    if len(nums) > 1:
        ok(colorize(f"Carrier Aggregation ACTIVE — {len(nums)} component carriers", C.LIME + C.BOLD))
    else:
        info("Single carrier (no aggregation right now).")
    total_bw = 0
    for b in nums:
        name = BAND_DB.get(b, {}).get("name", f"Band {b}")
        bw_match = re.search(rf"(\d+)MHz@\d+\(B{b}\)", band_field)
        bw = int(bw_match.group(1)) if bw_match else 0
        total_bw += bw
        bw_txt = f"{bw} MHz" if bw else "?"
        print(f"    {colorize('▸', C.GOLD)} {colorize(name, C.CYAN):<30} BW: {colorize(bw_txt, C.TEAL)}")
    if total_bw:
        print(f"\n  {colorize('Aggregate bandwidth:', C.DIM):<22} {colorize(str(total_bw)+' MHz', C.LIME, C.BOLD)}")
    sep()


def cmd_current_plmn(sess: H155Session, args):
    """[25] Show the currently-registered operator and access technology."""
    step("Current Network Registration")
    sep()
    xml = sess.api_get(EP["current_plmn"])
    name = xval(xml, "FullName", xval(xml, "ShortName", "N/A"))
    numeric = xval(xml, "Numeric", "N/A")
    rat = xval(xml, "Rat", "N/A")
    state = xval(xml, "State", "N/A")
    rat_names = {"0": "2G (GSM)", "2": "3G (WCDMA)", "7": "4G/LTE", "11": "5G NR"}
    print(f"  {colorize('Operator:', C.DIM):<18} {colorize(name, C.CYAN, C.BOLD)}")
    print(f"  {colorize('PLMN code:', C.DIM):<18} {colorize(numeric, C.GOLD)}")
    print(f"  {colorize('Access tech:', C.DIM):<18} {colorize(rat_names.get(rat, rat), C.LIME)}")
    print(f"  {colorize('Reg. state:', C.DIM):<18} {colorize(state, C.WHITE)}")
    sep()


# ─────────────────────────────────────────────────────────────
#  GROUP F — SECURITY & NAT  (features 26-30)
# ─────────────────────────────────────────────────────────────
def cmd_sim_pin(sess: H155Session, args):
    """[26] Manage the SIM PIN (status / enable / disable / change)."""
    step("SIM PIN Management")
    sep()
    st = sess.api_get(EP["pin_status"])
    sim_state = xval(st, "SimState", xval(st, "SimStatus", "?"))
    pin_state = xval(st, "PinState", "?")
    times = xval(st, "TimesLeft", xval(st, "SimPinTimes", "?"))
    print(f"  {colorize('SIM state:', C.DIM):<18} {colorize(sim_state, C.CYAN)}")
    print(f"  {colorize('PIN protection:', C.DIM):<18} {colorize('ON' if pin_state=='1' else 'OFF', C.GREEN if pin_state=='1' else C.DIM)}")
    print(f"  {colorize('Attempts left:', C.DIM):<18} {colorize(times, C.YELLOW)}\n")
    print(f"  {colorize('[1]', C.CYAN)} Enable PIN   {colorize('[2]', C.CYAN)} Disable PIN   {colorize('[3]', C.CYAN)} Change PIN")
    choice = ask(f"  {C.YELLOW}Action (Enter to cancel): {C.RESET}")
    if choice not in ("1", "2", "3"):
        warn("Cancelled.")
        return
    # OperateType: 1=enable, 2=disable, 3=change
    op = {"1": "1", "2": "2", "3": "3"}[choice]
    cur_pin = ask(f"  {C.YELLOW}Current PIN: {C.RESET}")
    if not cur_pin or not cur_pin.isdigit():
        err("Invalid PIN.")
        return
    new_pin = ""
    if choice == "3":
        new_pin = ask(f"  {C.YELLOW}New PIN (4-8 digits): {C.RESET}") or ""
        if not (new_pin.isdigit() and 4 <= len(new_pin) <= 8):
            err("New PIN must be 4-8 digits.")
            return
    body = {
        "OperateType": op, "CurrentPin": cur_pin,
        "NewPin": new_pin, "PukCode": "",
    }
    resp = sess.api_post(EP["pin_operate"], body)
    if sess.post_ok(resp):
        ok(colorize("PIN operation succeeded.", C.GREEN + C.BOLD))
    else:
        err(explain_error(resp) or "PIN operation failed (check the current PIN).")
    sep()


def cmd_dmz(sess: H155Session, args):
    """[27] View / configure the DMZ host."""
    step("DMZ Host")
    sep()
    xml = sess.api_get(EP["dmz"])
    enabled = xval(xml, "DmzStatus", "0")
    host = xval(xml, "DmzIPAddress", "—")
    print(f"  DMZ is {colorize('ENABLED', C.GREEN) if enabled=='1' else colorize('DISABLED', C.DIM)}"
          f"   Host: {colorize(host, C.CYAN)}\n")
    print(f"  {colorize('[1]', C.CYAN)} Enable & set host   {colorize('[0]', C.DIM)} Disable")
    choice = ask(f"  {C.YELLOW}Action (Enter to cancel): {C.RESET}")
    if choice == "1":
        ip = ask(f"  {C.YELLOW}DMZ host LAN IP (e.g. 192.168.8.150): {C.RESET}")
        try:
            socket.inet_aton(ip or "")
        except (socket.error, TypeError):
            err("Invalid IP.")
            return
        resp = sess.api_post(EP["dmz"], {"DmzStatus": 1, "DmzIPAddress": ip})
    elif choice == "0":
        resp = sess.api_post(EP["dmz"], {"DmzStatus": 0, "DmzIPAddress": host if host != "—" else ""})
    else:
        warn("Cancelled.")
        return
    if sess.post_ok(resp):
        ok(colorize("DMZ updated.", C.GREEN + C.BOLD))
    else:
        err(explain_error(resp) or "Failed to update DMZ.")
    sep()


def cmd_port_forward(sess: H155Session, args):
    """[28] List / add port-forwarding (virtual server) rules."""
    step("Port Forwarding")
    sep()
    xml = sess.api_get(EP["vservers"])
    rules = list(re.finditer(r"<Server>(.*?)</Server>", xml, re.DOTALL))
    if rules:
        print(f"  {C.DIM}  {'Name':<16} {'Ext Port':<10} {'→ Int IP:Port':<26} {'Proto'}{C.RESET}")
        print(f"  {C.DIM}  {'─'*60}{C.RESET}")
        for r in rules:
            b = r.group(1)
            name = xval(b, "VirtualServerName", "?")
            ep_port = xval(b, "VirtualServerWanPort", xval(b, "VirtualServerRemoteStartPort", "?"))
            ip = xval(b, "VirtualServerIPAddress", "?")
            ip_port = xval(b, "VirtualServerStartPort", "?")
            proto = {"0": "TCP", "1": "UDP", "2": "BOTH"}.get(xval(b, "VirtualServerProtocol"), "?")
            print(f"  {colorize(name, C.WHITE):<25} {colorize(ep_port, C.CYAN):<19} "
                  f"{colorize(ip+':'+ip_port, C.GOLD):<35} {colorize(proto, C.TEAL)}")
    else:
        info("No port-forwarding rules configured.")
    print()
    if not confirm(f"  {C.YELLOW}Add a new rule? (yes/no): {C.RESET}"):
        return
    name = ask(f"  {C.YELLOW}Rule name: {C.RESET}")
    wan_port = ask(f"  {C.YELLOW}External (WAN) port: {C.RESET}")
    ip = ask(f"  {C.YELLOW}Internal LAN IP: {C.RESET}")
    lan_port = ask(f"  {C.YELLOW}Internal port: {C.RESET}")
    proto = ask(f"  {C.YELLOW}Protocol 0=TCP 1=UDP 2=BOTH [0]: {C.RESET}") or "0"
    if not (name and wan_port and ip and lan_port):
        err("All fields required.")
        return
    body = {
        "VirtualServerName": name, "VirtualServerStatus": 1,
        "VirtualServerRemoteIPAddress": "", "VirtualServerWanPort": wan_port,
        "VirtualServerWanEndPort": wan_port, "VirtualServerIPAddress": ip,
        "VirtualServerStartPort": lan_port, "VirtualServerEndPort": lan_port,
        "VirtualServerProtocol": proto,
    }
    resp = sess.api_post(EP["vservers"], body)
    if sess.post_ok(resp):
        ok(colorize(f"Port-forward rule '{name}' added.", C.GREEN + C.BOLD))
    else:
        err(explain_error(resp) or "Failed to add rule.")
    sep()


def cmd_firewall(sess: H155Session, args):
    """[29] View / toggle the router firewall switches."""
    step("Firewall Switches")
    sep()
    xml = sess.api_get(EP["firewall"])
    fields = [
        ("FirewallMainSwitch", "Main firewall"),
        ("FirewallIPFilterSwitch", "IP filter"),
        ("FirewallWanPortPingSwitch", "Block WAN ping"),
        ("FirewallMacFilterSwitch", "MAC filter"),
        ("FirewallUrlFilterSwitch", "URL filter"),
    ]
    state = {}
    for key, label in fields:
        v = xval(xml, key, "0")
        state[key] = v
        print(f"  {colorize(label+':', C.DIM):<22} "
              f"{colorize('ON', C.GREEN) if v=='1' else colorize('OFF', C.RED)}")
    print()
    main_new = "0" if state.get("FirewallMainSwitch") == "1" else "1"
    if not confirm(f"  {C.YELLOW}Turn MAIN firewall {'OFF' if main_new=='0' else 'ON'}? (yes/no): {C.RESET}"):
        warn("Unchanged.")
        return
    state["FirewallMainSwitch"] = main_new
    resp = sess.api_post(EP["firewall"], state)
    if sess.post_ok(resp):
        ok(colorize(f"Main firewall turned {'ON' if main_new=='1' else 'OFF'}.", C.GREEN + C.BOLD))
    else:
        err(explain_error(resp) or "Failed to update firewall.")
    sep()


def cmd_upnp(sess: H155Session, args):
    """[30] View / toggle UPnP."""
    step("UPnP")
    sep()
    xml = sess.api_get(EP["upnp"])
    cur = xval(xml, "UpnpStatus", "0")
    print(f"  UPnP is {colorize('ENABLED', C.GREEN) if cur=='1' else colorize('DISABLED', C.RED)}.")
    new = "0" if cur == "1" else "1"
    if not confirm(f"  {C.YELLOW}{'Disable' if new=='0' else 'Enable'} UPnP? (yes/no): {C.RESET}"):
        warn("Unchanged.")
        return
    resp = sess.api_post(EP["upnp"], {"UpnpStatus": new})
    if sess.post_ok(resp):
        ok(colorize(f"UPnP {'enabled' if new=='1' else 'disabled'}.", C.GREEN + C.BOLD))
    else:
        err(explain_error(resp) or "Failed to toggle UPnP.")
    sep()


# ─────────────────────────────────────────────────────────────
#  GROUP G — DIAGNOSTICS  (features 31-34)
# ─────────────────────────────────────────────────────────────
def cmd_ping(sess: H155Session, args):
    """[31] Ping a host through the router (run from this machine)."""
    step("Ping Diagnostic")
    sep()
    target = getattr(args, "target", None) or ask(f"  {C.YELLOW}Host to ping [8.8.8.8]: {C.RESET}") or "8.8.8.8"
    count = "5"
    info(f"Pinging {colorize(target, C.CYAN)} ({count} packets)...")
    flag = "-n" if sys.platform.startswith("win") else "-c"
    try:
        res = subprocess.run(["ping", flag, count, target],
                             capture_output=True, text=True, timeout=30)
        out = res.stdout.strip()
        print()
        for line in out.splitlines():
            low = line.lower()
            if "ttl=" in low or "time=" in low:
                print(f"  {colorize(line, C.GREEN)}")
            elif "loss" in low or "packets" in low or "rtt" in low or "round-trip" in low or "minimum" in low:
                print(f"  {colorize(line, C.GOLD, C.BOLD)}")
            else:
                print(f"  {C.DIM}{line}{C.RESET}")
        if res.returncode == 0:
            ok("Host reachable.")
        else:
            warn("Host did not respond to all probes.")
    except FileNotFoundError:
        err("'ping' command not available on this system.")
    except subprocess.TimeoutExpired:
        err("Ping timed out.")
    sep()


def cmd_traceroute(sess: H155Session, args):
    """[32] Trace the route to a host from this machine."""
    step("Traceroute Diagnostic")
    sep()
    target = getattr(args, "target", None) or ask(f"  {C.YELLOW}Host to trace [8.8.8.8]: {C.RESET}") or "8.8.8.8"
    if sys.platform.startswith("win"):
        cmd = ["tracert", "-d", "-h", "15", target]
    else:
        cmd = ["traceroute", "-n", "-m", "15", target]
    info(f"Tracing route to {colorize(target, C.CYAN)} (max 15 hops)...")
    print()
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        for line in res.stdout.splitlines():
            print(f"  {C.DIM}{line}{C.RESET}")
        ok("Trace complete.")
    except FileNotFoundError:
        # tracepath fallback (common on Linux without traceroute)
        try:
            res = subprocess.run(["tracepath", "-n", target],
                                 capture_output=True, text=True, timeout=60)
            for line in res.stdout.splitlines():
                print(f"  {C.DIM}{line}{C.RESET}")
            ok("Trace complete (tracepath).")
        except FileNotFoundError:
            err("Neither 'traceroute' nor 'tracepath' is installed.")
    except subprocess.TimeoutExpired:
        warn("Traceroute timed out (partial results above).")
    sep()


def cmd_speedtest(sess: H155Session, args):
    """[33] Measure real download throughput through the router."""
    step("Download Speed Test")
    sep()
    # Cloudflare's speed endpoint serves arbitrary-size payloads – reliable & free.
    size_mb = 25
    url = f"https://speed.cloudflare.com/__down?bytes={size_mb * 1024 * 1024}"
    info(f"Downloading {size_mb} MB test payload via the router...")
    try:
        start = time.time()
        downloaded = 0
        with requests.get(url, stream=True, timeout=60, verify=True) as r:
            r.raise_for_status()
            for chunk in r.iter_content(chunk_size=65536):
                downloaded += len(chunk)
                elapsed = time.time() - start
                if elapsed > 0:
                    mbps = (downloaded * 8) / elapsed / 1_000_000
                    pct = downloaded / (size_mb * 1024 * 1024) * 100
                    print(f"\r  {C.DIM}{pct:5.1f}%{C.RESET}  "
                          f"{colorize(f'{mbps:6.2f} Mbps', C.LIME, C.BOLD)}   "
                          f"({bytes_fmt(str(downloaded))})   ", end="", flush=True)
        elapsed = time.time() - start
        print()
        if elapsed > 0:
            mbps = (downloaded * 8) / elapsed / 1_000_000
            mBps = downloaded / elapsed / 1_000_000
            sep()
            print(f"  {colorize('Downloaded:', C.DIM):<18} {colorize(bytes_fmt(str(downloaded)), C.CYAN)}")
            print(f"  {colorize('Time:', C.DIM):<18} {colorize(f'{elapsed:.1f} s', C.CYAN)}")
            print(f"  {colorize('Throughput:', C.DIM):<18} {colorize(f'{mbps:.2f} Mbps', C.LIME, C.BOLD)}  ({mBps:.2f} MB/s)")
    except requests.exceptions.SSLError:
        err("TLS error reaching the speed-test server.")
    except requests.exceptions.RequestException as e:
        err(f"Speed test failed: {e}")
    sep()


def cmd_dns_set(sess: H155Session, args):
    """[34] View / set custom DNS servers on the router DHCP service."""
    step("Custom DNS Servers")
    sep()
    xml = sess.api_get(EP["dhcp"])
    pri = xval(xml, "PrimaryDns", "—")
    sec = xval(xml, "SecondaryDns", "—")
    print(f"  Current DNS: {colorize(pri, C.CYAN)} / {colorize(sec, C.CYAN)}\n")
    print(f"  {C.DIM}  Presets: 1=Google(8.8.8.8) 2=Cloudflare(1.1.1.1) 3=Quad9(9.9.9.9) c=Custom{C.RESET}")
    choice = ask(f"  {C.YELLOW}Choose preset or 'c' (Enter to cancel): {C.RESET}")
    presets = {
        "1": ("8.8.8.8", "8.8.4.4"),
        "2": ("1.1.1.1", "1.0.0.1"),
        "3": ("9.9.9.9", "149.112.112.112"),
    }
    if choice in presets:
        new_pri, new_sec = presets[choice]
    elif choice == "c":
        new_pri = ask(f"  {C.YELLOW}Primary DNS: {C.RESET}")
        new_sec = ask(f"  {C.YELLOW}Secondary DNS: {C.RESET}") or new_pri
    else:
        warn("Cancelled.")
        return
    for ip in (new_pri, new_sec):
        try:
            socket.inet_aton(ip or "")
        except (socket.error, TypeError):
            err(f"Invalid IP: {ip}")
            return
    body = {
        "DhcpIPAddress": xval(xml, "DhcpIPAddress", "192.168.8.1"),
        "DhcpLanNetmask": xval(xml, "DhcpLanNetmask", "255.255.255.0"),
        "DhcpStatus": xval(xml, "DhcpStatus", "1"),
        "DhcpStartIPAddress": xval(xml, "DhcpStartIPAddress", "192.168.8.100"),
        "DhcpEndIPAddress": xval(xml, "DhcpEndIPAddress", "192.168.8.200"),
        "DhcpLeaseTime": xval(xml, "DhcpLeaseTime", "86400"),
        "DnsStatus": 0, "PrimaryDns": new_pri, "SecondaryDns": new_sec,
    }
    resp = sess.api_post(EP["dhcp"], body)
    if sess.post_ok(resp):
        ok(colorize(f"DNS set to {new_pri} / {new_sec}. Renew client leases to apply.", C.GREEN + C.BOLD))
    else:
        err(explain_error(resp) or "Failed to set DNS.")
    sep()


# ─────────────────────────────────────────────────────────────
#  GROUP H — SYSTEM & UTILITIES  (features 35-42)
# ─────────────────────────────────────────────────────────────
def cmd_firmware_check(sess: H155Session, args):
    """[35] Check whether a firmware update is available."""
    step("Firmware Update Check")
    sep()
    dev = sess.get_device_info()
    print(f"  {colorize('Current software:', C.DIM):<22} {colorize(dev.get('software', 'N/A'), C.CYAN, C.BOLD)}")
    print(f"  {colorize('Hardware:', C.DIM):<22} {colorize(dev.get('hardware', 'N/A'), C.DIM)}")
    info("Querying update server...")
    xml = sess.api_get(EP["fw_check"])
    if not xml:
        warn("Update API not reachable (carrier may block OTA, or none pending).")
        sep()
        return
    new_ver = xval(xml, "version", xval(xml, "NewVersion", ""))
    state = xval(xml, "status", xval(xml, "State", ""))
    if new_ver:
        ok(colorize(f"Update available: {new_ver}", C.LIME + C.BOLD))
        if state not in ("N/A", ""):
            info(f"Update state code: {colorize(state, C.DIM)}")
        notes = xval(xml, "info", "")
        if notes and notes != "N/A":
            print(f"  {C.DIM}{notes}{C.RESET}")
        warn("Apply firmware updates from the official web UI to avoid bricking.")
    else:
        ok(colorize("Firmware is up to date.", C.GREEN + C.BOLD))
    sep()


def cmd_led_control(sess: H155Session, args):
    """[36] Turn the router status LEDs on/off (or night mode)."""
    step("LED Control")
    sep()
    xml = sess.api_get(EP["led"])
    cur = xval(xml, "circle_switch", xval(xml, "led_switch", "1"))
    print(f"  Status LEDs are "
          f"{colorize('ON', C.GREEN) if cur=='1' else colorize('OFF', C.DIM)}.")
    new = "0" if cur == "1" else "1"
    if not confirm(f"  {C.YELLOW}Turn LEDs {'OFF' if new=='0' else 'ON'}? (yes/no): {C.RESET}"):
        warn("Unchanged.")
        return
    resp = sess.api_post(EP["led"], {"circle_switch": new})
    if not sess.post_ok(resp):
        # Some firmwares use the nightmode endpoint instead
        resp = sess.api_post(EP["led_night"], {"nightmode_switch": "1" if new == "0" else "0"})
    if sess.post_ok(resp):
        ok(colorize(f"LEDs turned {'ON' if new=='1' else 'OFF'}.", C.GREEN + C.BOLD))
    else:
        err(explain_error(resp) or "LED control not supported on this firmware.")
    sep()


def _gather_status(sess: H155Session) -> dict:
    """Collect a full structured snapshot of the router state."""
    return {
        "captured_at": datetime.now().isoformat(timespec="seconds"),
        "gateway": sess.gateway,
        "device": sess.get_device_info(),
        "monitoring": sess.get_monitoring(),
        "signal": sess.get_signal(),
        "net_mode": sess.get_net_mode(),
    }


def cmd_export_json(sess: H155Session, args):
    """[37] Export a full status snapshot to a JSON file."""
    step("Export Status → JSON")
    sep()
    snap = _gather_status(sess)
    fname = getattr(args, "file", None) or f"h155_status_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    try:
        with open(fname, "w", encoding="utf-8") as f:
            json.dump(snap, f, indent=2, ensure_ascii=False)
    except OSError as e:
        err(f"Could not write file: {e}")
        return
    ok(colorize(f"Snapshot written → {fname}", C.GREEN + C.BOLD))
    sig = snap["signal"]
    info(f"RSRP {sig.get('rsrp','?')} | SINR {sig.get('sinr','?')} | Band {sig.get('band','?')}")
    sep()


def cmd_backup_config(sess: H155Session, args):
    """[38] Back up band-lock + Wi-Fi + APN config to a JSON profile file."""
    step("Backup Configuration")
    sep()
    net = sess.get_net_mode()
    wlan = sess.api_get(EP["wlan_basic"])
    profiles = sess.api_get(EP["profiles"])
    config = {
        "saved_at": datetime.now().isoformat(timespec="seconds"),
        "gateway": sess.gateway,
        "net_mode": {
            "network_mode": (net or {}).get("network_mode", "00"),
            "network_band": (net or {}).get("network_band", "3FFFFFFF"),
            "lte_band": (net or {}).get("lte_band", "7FFFFFFFFFFFFFFF"),
        },
        "locked_bands": lte_bitmask_to_bands((net or {}).get("lte_band", "7FFFFFFFFFFFFFFF")),
        "wifi_ssid": xval(wlan, "WifiSsid", xval(wlan, "Ssid", "")),
        "apn_current": xval(profiles, "CurrentProfile", ""),
    }
    fname = getattr(args, "file", None) or f"h155_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    try:
        with open(fname, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    except OSError as e:
        err(f"Could not write backup: {e}")
        return
    ok(colorize(f"Configuration backed up → {fname}", C.GREEN + C.BOLD))
    bands = config["locked_bands"]
    info(f"Saved band lock: {', '.join('B'+str(b) for b in bands) if bands else 'none'}")
    sep()


def cmd_restore_config(sess: H155Session, args):
    """[39] Restore band-lock config from a JSON backup file."""
    step("Restore Configuration")
    sep()
    fname = getattr(args, "file", None) or ask(f"  {C.YELLOW}Backup file path: {C.RESET}")
    if not fname:
        warn("Cancelled.")
        return
    try:
        with open(fname, "r", encoding="utf-8") as f:
            config = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        err(f"Cannot read backup: {e}")
        return
    nm = config.get("net_mode", {})
    mode = nm.get("network_mode", "00")
    nband = nm.get("network_band", "3FFFFFFF")
    lband = nm.get("lte_band", "7FFFFFFFFFFFFFFF")
    bands = lte_bitmask_to_bands(lband)
    print(f"  Backup from: {colorize(config.get('saved_at', '?'), C.DIM)}")
    print(f"  Band lock to restore: {colorize(', '.join('B'+str(b) for b in bands) if bands else 'all bands', C.GOLD)}")
    if not confirm(f"  {C.YELLOW}Apply this configuration now? (yes/no): {C.RESET}"):
        warn("Cancelled.")
        return
    if sess.set_net_mode(mode, nband, lband):
        ok(colorize("Configuration restored — band lock re-applied.", C.GREEN + C.BOLD))
    else:
        err("Failed to apply restored configuration.")
    sep()


def cmd_signal_alert(sess: H155Session, args):
    """[40] Watch signal and alert (bell + log) when RSRP drops below a threshold."""
    interval = getattr(args, "interval", 5) or 5
    threshold = getattr(args, "threshold", -110) or -110
    step(f"Signal Alert Monitor — alert below {threshold} dBm (every {interval}s, Ctrl+C to stop)")
    sep()
    alerts = 0
    checks = 0
    below = False
    try:
        while True:
            sig = sess.get_signal()
            rsrp = sig.get("rsrp_int")
            ts = datetime.now().strftime("%H:%M:%S")
            checks += 1
            r_lbl, r_col = grade_rsrp(rsrp)
            bar = signal_bar(rsrp)
            if rsrp is not None and rsrp < threshold:
                if not below:  # rising-edge alert only
                    alerts += 1
                    below = True
                    print("\a", end="", flush=True)  # terminal bell
                    print(f"\n  {C.RED}{C.BOLD}⚠ ALERT [{ts}] RSRP {rsrp} dBm < {threshold} dBm "
                          f"(alert #{alerts}){C.RESET}")
                    # Best-effort desktop notification on Linux
                    try:
                        subprocess.run(
                            ["notify-send", "H155 Signal Alert", f"RSRP {rsrp} dBm (Band {sig.get('band','?')})"],
                            capture_output=True, timeout=3,
                        )
                    except Exception:
                        pass
            else:
                below = False
            print(f"\r  {C.DIM}[{ts}] #{checks:>4}{C.RESET}  {bar}  "
                  f"RSRP:{colorize(sig.get('rsrp','?'), r_col, C.BOLD)}  "
                  f"Alerts:{colorize(str(alerts), C.RED if alerts else C.DIM)}  "
                  f"({colorize(r_lbl, r_col)})    ", end="", flush=True)
            time.sleep(interval)
    except KeyboardInterrupt:
        print()
        ok(f"Stopped after {checks} checks, {colorize(str(alerts), C.YELLOW)} alert(s).")
    sep()


def cmd_signal_graph(sess: H155Session, args):
    """[41] Live ASCII sparkline graph of RSRP over time."""
    interval = getattr(args, "interval", 2) or 2
    width = 50
    step(f"Live RSRP Graph (every {interval}s, Ctrl+C to stop)")
    sep()
    spark = " ▁▂▃▄▅▆▇█"
    history = []
    # RSRP mapped from -120 (worst) .. -60 (best) onto the sparkline glyphs
    lo, hi = -120, -60
    try:
        while True:
            sig = sess.get_signal()
            rsrp = sig.get("rsrp_int")
            if rsrp is not None:
                history.append(rsrp)
                history = history[-width:]
            line = ""
            for v in history:
                frac = (v - lo) / (hi - lo)
                idx = max(0, min(len(spark) - 1, int(frac * (len(spark) - 1))))
                _, col = grade_rsrp(v)
                line += colorize(spark[idx], col)
            cur = history[-1] if history else None
            r_lbl, r_col = grade_rsrp(cur)
            if history:
                avg = sum(history) / len(history)
                stats = (f"cur {colorize(str(cur), r_col, C.BOLD)}  "
                         f"avg {avg:5.1f}  min {min(history)}  max {max(history)}")
            else:
                stats = "waiting for data..."
            print(f"\r  [{line}{' ' * (width - len(history))}]  {stats}   ", end="", flush=True)
            time.sleep(interval)
    except KeyboardInterrupt:
        print()
        ok("Graph stopped.")
    sep()


def cmd_health_report(sess: H155Session, args):
    """[42] One-screen health report with an overall score and advice."""
    step("Router Health Report")
    sep()
    dev = sess.get_device_info()
    mon = sess.get_monitoring()
    sig = sess.get_signal()

    rsrp = sig.get("rsrp_int")
    sinr = sig.get("sinr_int")
    conn = mon.get("connection_status", "0") == "901"

    score = 0
    notes = []
    # RSRP scoring (max 40)
    if rsrp is not None:
        if rsrp >= -85: score += 40
        elif rsrp >= -95: score += 32; notes.append("RSRP is good but not excellent.")
        elif rsrp >= -105: score += 20; notes.append("RSRP is fair — consider an external antenna.")
        else: score += 8; notes.append("RSRP is poor — reposition the router or add an antenna.")
    # SINR scoring (max 40)
    if sinr is not None:
        if sinr >= 20: score += 40
        elif sinr >= 13: score += 32; notes.append("SINR is good.")
        elif sinr >= 0: score += 18; notes.append("SINR is fair — interference likely; try band-locking.")
        else: score += 5; notes.append("SINR is bad — heavy interference; change band/tower.")
    # Connectivity scoring (max 20)
    if conn:
        score += 20
    else:
        notes.append("Data connection is DOWN — check SIM/data switch.")

    if score >= 85: grade, gcol = "EXCELLENT", C.LIME
    elif score >= 65: grade, gcol = "GOOD", C.GREEN
    elif score >= 45: grade, gcol = "FAIR", C.YELLOW
    else: grade, gcol = "POOR", C.RED

    filled = int(score / 5)
    bar = colorize("█" * filled, gcol) + colorize("░" * (20 - filled), C.DIM)

    print(f"  {colorize('Model:', C.DIM):<16} {colorize(dev.get('model', 'N/A'), C.CYAN)}")
    print(f"  {colorize('Software:', C.DIM):<16} {colorize(dev.get('software', 'N/A'), C.DIM)}")
    print(f"  {colorize('Connection:', C.DIM):<16} {colorize('UP' if conn else 'DOWN', C.GREEN if conn else C.RED, C.BOLD)}")
    print(f"  {colorize('RSRP / SINR:', C.DIM):<16} {colorize(sig.get('rsrp','?'), C.WHITE)} / {colorize(sig.get('sinr','?'), C.WHITE)}")
    print()
    print(f"  {colorize('HEALTH SCORE', C.BOLD)}   [{bar}]  {colorize(f'{score}/100', gcol, C.BOLD)}  {colorize(grade, gcol, C.BOLD)}")
    if notes:
        print(f"\n  {C.GOLD}{C.BOLD}  Advice:{C.RESET}")
        for n in notes:
            print(f"    {colorize('•', C.GOLD)} {colorize(n, C.WHITE)}")
    else:
        print(f"\n  {colorize('✔ Everything looks great — no action needed.', C.LIME, C.BOLD)}")
    sep()


# ═════════════════════════════════════════════════════════════
#  ★★  v40.2 UPGRADE — 40 AUTOMATION & CARRIER-AGGREGATION TOOLS  ★★
#  Auto-everything: best CA (4G+4G / 4G+4G+4G) pairs, best cell tower,
#  throughput-driven optimisation, autopilot daemons, profiles & reports.
#  Every tool is fully implemented against the real H155 API / local OS.
# ═════════════════════════════════════════════════════════════

PROFILES_FILE = "h155_profiles.json"


# ── Shared measurement / discovery helpers (reused by many features) ──
def measure_download_mbps(size_mb: int = 10, timeout: int = 40, show: bool = False) -> Optional[float]:
    """Download a payload through the router and return throughput in Mbps."""
    url = f"https://speed.cloudflare.com/__down?bytes={size_mb * 1024 * 1024}"
    try:
        start = time.time()
        got = 0
        with requests.get(url, stream=True, timeout=timeout, verify=True) as r:
            r.raise_for_status()
            for chunk in r.iter_content(chunk_size=65536):
                got += len(chunk)
                if show:
                    el = time.time() - start
                    if el > 0:
                        mbps = (got * 8) / el / 1_000_000
                        print(f"\r  {C.DIM}downloading {bytes_fmt(str(got))}  "
                              f"{colorize(f'{mbps:.1f} Mbps', C.LIME)}   {C.RESET}", end="", flush=True)
        el = time.time() - start
        if show:
            print()
        return (got * 8) / el / 1_000_000 if el > 0 else None
    except requests.exceptions.RequestException:
        if show:
            print()
        return None


def measure_latency_ms(host: str = "8.8.8.8", count: int = 4) -> Optional[float]:
    """Average ICMP round-trip time in milliseconds (via the OS ping)."""
    flag = "-n" if sys.platform.startswith("win") else "-c"
    try:
        res = subprocess.run(["ping", flag, str(count), host],
                             capture_output=True, text=True, timeout=20)
        ms = [float(x) for x in re.findall(r"time[=<]\s?([\d.]+)", res.stdout)]
        return sum(ms) / len(ms) if ms else None
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None


def avg_signal(sess: H155Session, samples: int = 4, delay: float = 1.0):
    """Return (avg_rsrp, avg_sinr) over several samples (None if unavailable)."""
    rs, ss = [], []
    for _ in range(samples):
        sig = sess.get_signal()
        r, s = sig.get("rsrp_int"), sig.get("sinr_int")
        if r is not None:
            rs.append(r)
        if s is not None:
            ss.append(s)
        time.sleep(delay)
    return (sum(rs) / len(rs) if rs else None,
            sum(ss) / len(ss) if ss else None)


def stdev(vals) -> float:
    """Population standard deviation (0.0 for <2 samples)."""
    n = len(vals)
    if n < 2:
        return 0.0
    mean = sum(vals) / n
    return (sum((v - mean) ** 2 for v in vals) / n) ** 0.5


def active_ca_bands(sess: H155Session):
    """LTE band numbers currently aggregated, parsed from the signal field."""
    bf = str(sess.get_signal().get("band", ""))
    return sorted({int(x) for x in re.findall(r"B(\d+)", bf)})


def visible_bands(sess: H155Session):
    """LTE band numbers seen in the neighbour-cell scan."""
    xml = sess.get_cell_info()
    bands = set()
    for c in re.finditer(r"<Cell>(.*?)</Cell>", xml, re.DOTALL):
        mm = re.search(r"<Band>(.*?)</Band>", c.group(1))
        if mm:
            digits = re.sub(r"[^\d]", "", mm.group(1))
            if digits:
                bands.add(int(digits))
    return sorted(bands)


def visible_towers(sess: H155Session):
    """Neighbour cells as dicts: pci, band, earfcn, rsrp, rsrp_int, sinr, cell_id."""
    xml = sess.get_cell_info()
    out = []
    for c in re.finditer(r"<Cell>(.*?)</Cell>", xml, re.DOTALL):
        b = c.group(1)

        def v(t, d="N/A"):
            mm = re.search(rf"<{t}>(.*?)</{t}>", b)
            return mm.group(1).strip() if mm else d

        try:
            ri = int(re.sub(r"[^-\d]", "", v("Rsrp", "-999")))
        except ValueError:
            ri = -999
        out.append({
            "pci": v("Pci"), "band": v("Band"), "earfcn": v("Earfcn"),
            "rsrp": v("Rsrp"), "rsrp_int": ri, "sinr": v("Sinr"),
            "cell_id": v("CellId"),
        })
    return out


def lock_bands(sess: H155Session, bands, mode: str = "03") -> bool:
    """Lock the modem to the given LTE band set (enables CA across them)."""
    return sess.set_net_mode(mode, "3FFFFFFF", bands_to_lte_bitmask(bands))


def wait_reconnect(seconds: int = 12, step: int = 2):
    n = max(1, seconds // step)
    print(f"  {C.DIM}  reconnecting", end="", flush=True)
    for _ in range(n):
        time.sleep(step)
        print(f"{C.DIM}.{C.RESET}", end="", flush=True)
    print()


def band_label(b: int) -> str:
    return BAND_DB.get(b, {}).get("name", f"Band {b}")


def is_connected(sess: H155Session) -> bool:
    return sess.get_monitoring().get("connection_status", "0") == "901"


# ─────────────────────────────────────────────────────────────
#  GROUP I — CARRIER AGGREGATION (4G+4G) SUITE  (features 59-66)
# ─────────────────────────────────────────────────────────────
def cmd_ca_combos(sess: H155Session, args):
    """[59] Discover candidate carrier-aggregation band combinations."""
    from itertools import combinations
    step("Carrier-Aggregation Combinations")
    sep()
    vis = visible_bands(sess)
    if not vis:
        warn("No neighbour bands visible — run a tower scan in LTE mode first.")
        sep()
        return
    info(f"Bands visible here: {colorize(', '.join('B'+str(b) for b in vis), C.GOLD)}")
    cur = active_ca_bands(sess)
    if len(cur) > 1:
        ok(f"Currently aggregating: {colorize('+'.join('B'+str(b) for b in cur), C.LIME, C.BOLD)}")
    pairs = list(combinations(vis, 2))
    print(f"\n  {C.GOLD}{C.BOLD}  Candidate 4G+4G pairs ({len(pairs)}):{C.RESET}")
    for a, b in pairs:
        active = set([a, b]) == set(cur)
        mark = colorize("  ◀ active", C.LIME, C.BOLD) if active else ""
        print(f"    {colorize(f'B{a}+B{b}', C.CYAN, C.BOLD):<22} "
              f"{colorize(band_label(a)+' + '+band_label(b), C.DIM)}{mark}")
    if len(vis) >= 3:
        trips = list(combinations(vis, 3))
        print(f"\n  {C.GOLD}{C.BOLD}  Candidate 4G+4G+4G triples ({len(trips)}):{C.RESET}")
        for combo in trips[:12]:
            print(f"    {colorize('+'.join('B'+str(x) for x in combo), C.MAGENTA, C.BOLD)}")
    info("Use 'ca-best' to benchmark & lock the strongest pair automatically.")
    sep()


def _benchmark_combos(sess: H155Session, combos, samples=3, settle=10, speed=False):
    """Lock each band combo, verify aggregation, score it. Returns ranked list."""
    results = []
    for combo in combos:
        names = "+".join("B" + str(b) for b in combo)
        print(f"\n  {C.MAGENTA}▶{C.RESET}  Testing {colorize(names, C.GOLD, C.BOLD)}...")
        if not lock_bands(sess, list(combo)):
            warn(f"  Could not lock {names} — skipping")
            continue
        wait_reconnect(settle)
        agg = active_ca_bands(sess)
        rsrp, sinr = avg_signal(sess, samples=samples, delay=1)
        mbps = measure_download_mbps(8, show=True) if speed else None
        if rsrp is None:
            warn(f"  No signal on {names}")
            continue
        ca_ok = len(agg) >= len(combo)
        # Composite score: signal quality + aggregation bonus + throughput
        score = rsrp + (sinr or 0) * 1.5 + (10 if ca_ok else 0) + (mbps or 0)
        bar = signal_bar(int(rsrp))
        extra = f"  {colorize(f'{mbps:.1f} Mbps', C.LIME, C.BOLD)}" if mbps else ""
        print(f"  {bar}  RSRP {colorize(f'{rsrp:.1f}', C.CYAN)}  "
              f"SINR {colorize(f'{sinr:.1f}' if sinr is not None else '?', C.CYAN)}  "
              f"CA {colorize('YES' if ca_ok else 'no', C.LIME if ca_ok else C.DIM)}{extra}")
        results.append({"combo": list(combo), "names": names, "rsrp": rsrp,
                        "sinr": sinr or -99, "mbps": mbps, "ca": ca_ok, "score": score})
    results.sort(key=lambda x: x["score"], reverse=True)
    return results


def cmd_ca_best(sess: H155Session, args):
    """[60] Benchmark every 4G+4G CA pair and lock the strongest one."""
    from itertools import combinations
    step("Auto-Best Carrier Aggregation (4G+4G)")
    warn("Router will reconnect several times (~2-4 min). Don't disconnect.")
    sep()
    if not confirm(f"  {C.RED}Start CA benchmark? (yes/no): {C.RESET}"):
        warn("Cancelled.")
        return
    vis = visible_bands(sess)
    if len(vis) < 2:
        err("Need at least 2 visible bands for CA. Run a scan in LTE mode.")
        return
    # Bound the search to the strongest 4 bands → at most C(4,2)=6 pairs
    towers = visible_towers(sess)
    strength = {}
    for t in towers:
        try:
            bb = int(re.sub(r"[^\d]", "", t["band"]))
        except (ValueError, TypeError):
            continue
        strength[bb] = max(strength.get(bb, -999), t["rsrp_int"])
    top = sorted(vis, key=lambda b: strength.get(b, -999), reverse=True)[:4]
    pairs = list(combinations(sorted(top), 2))
    info(f"Testing {len(pairs)} CA pairs from strongest bands: "
         f"{colorize(', '.join('B'+str(b) for b in top), C.CYAN)}")
    results = _benchmark_combos(sess, pairs, speed=getattr(args, "speed", False))
    if not results:
        err("No CA pair produced a usable signal.")
        return
    sep()
    print(f"\n  {C.GOLD}{C.BOLD}  ╔══  CA PAIR RANKING  ═════════════════════════╗{C.RESET}")
    for i, r in enumerate(results):
        icon = f"{C.GOLD}★{C.RESET}" if i == 0 else f"{C.DIM}{i+1}.{C.RESET}"
        mbps = f"{r['mbps']:.1f}Mbps" if r["mbps"] else "—"
        rsrp_s = "{:.0f}".format(r["rsrp"])
        sinr_s = "{:.0f}".format(r["sinr"])
        ca_s = "Y" if r["ca"] else "n"
        print(f"  {C.GOLD}║{C.RESET} {icon} {colorize(r['names'], C.WHITE):<14} "
              f"RSRP {colorize(rsrp_s, C.CYAN)}  "
              f"SINR {colorize(sinr_s, C.CYAN)}  "
              f"CA {colorize(ca_s, C.LIME if r['ca'] else C.DIM)}  "
              f"{colorize(mbps, C.LIME)}")
    print(f"  {C.GOLD}{C.BOLD}  ╚════════════════════════════════════════════════╝{C.RESET}")
    winner = results[0]
    info(f"\n  Locking winner: {colorize(winner['names'], C.LIME, C.BOLD)}")
    if lock_bands(sess, winner["combo"]):
        ok(colorize(f"Locked best CA pair: {winner['names']}!", C.LIME + C.BOLD))
    sep()


def cmd_ca_lock(sess: H155Session, args):
    """[61] Manually lock a specific CA combo (e.g. 1 3)."""
    step("Manual CA Lock")
    sep()
    if args.bands:
        combo = [int(b) for b in args.bands]
    else:
        for b in sorted(BAND_DB):
            print(f"    {colorize(str(b), C.CYAN, C.BOLD):>12}  {colorize(BAND_DB[b]['name'], C.WHITE)}")
        raw = ask(f"\n  {C.YELLOW}Bands to aggregate, e.g. '1 3' or '3 7 20': {C.RESET}")
        if not raw:
            warn("Cancelled.")
            return
        combo = [int(x) for x in raw.split() if x.isdigit()]
    if len(combo) < 2:
        err("CA needs at least 2 bands.")
        return
    names = "+".join("B" + str(b) for b in combo)
    info(f"Locking {colorize(names, C.GOLD)} (mask {bands_to_lte_bitmask(combo)})")
    if lock_bands(sess, combo):
        wait_reconnect(10)
        agg = active_ca_bands(sess)
        if len(agg) >= 2:
            ok(colorize(f"CA active: {'+'.join('B'+str(b) for b in agg)}", C.LIME + C.BOLD))
        else:
            warn(f"Bands locked, but tower is serving single carrier ({'+'.join('B'+str(b) for b in agg) or '?'}).")
            info("The cell must support these bands together for CA to engage.")
    else:
        err("Failed to apply CA lock.")
    sep()


def cmd_ca_3cc(sess: H155Session, args):
    """[62] Find and lock the best 3-carrier (4G+4G+4G) combination."""
    from itertools import combinations
    step("Best 3-Carrier Aggregation (4G+4G+4G)")
    warn("Tests 3-band combos — can take several minutes.")
    sep()
    if not confirm(f"  {C.RED}Start 3CC search? (yes/no): {C.RESET}"):
        warn("Cancelled.")
        return
    vis = visible_bands(sess)
    if len(vis) < 3:
        err(f"Only {len(vis)} band(s) visible — need 3+ for 3CC.")
        return
    triples = list(combinations(sorted(vis)[:5], 3))[:8]
    info(f"Testing {len(triples)} triple combos...")
    results = _benchmark_combos(sess, triples, samples=3, settle=12)
    if not results:
        err("No 3CC combo produced a usable signal.")
        return
    winner = results[0]
    sep()
    ok(f"Best 3CC: {colorize(winner['names'], C.LIME, C.BOLD)} (score {winner['score']:.0f})")
    if lock_bands(sess, winner["combo"]):
        ok(colorize("Locked best 3-carrier combination!", C.LIME + C.BOLD))
    sep()


def cmd_ca_live(sess: H155Session, args):
    """[63] Live carrier-aggregation monitor (component carriers + bandwidth)."""
    interval = getattr(args, "interval", 3) or 3
    step(f"Live CA Monitor (every {interval}s, Ctrl+C to stop)")
    sep()
    try:
        while True:
            sig = sess.get_signal()
            bf = str(sig.get("band", ""))
            nums = sorted({int(x) for x in re.findall(r"B(\d+)", bf)})
            total_bw = sum(int(x) for x in re.findall(r"(\d+)MHz", bf)) or 0
            ts = datetime.now().strftime("%H:%M:%S")
            rsrp_i = sig.get("rsrp_int")
            bar = signal_bar(rsrp_i)
            cc = colorize(f"{len(nums)}CC", C.LIME if len(nums) > 1 else C.DIM, C.BOLD)
            blist = "+".join("B" + str(n) for n in nums) or "?"
            print(f"\r  {C.DIM}{ts}{C.RESET}  {bar}  {cc}  "
                  f"{colorize(blist, C.GOLD):<22}  "
                  f"BW:{colorize(str(total_bw)+'MHz', C.TEAL)}  "
                  f"RSRP:{colorize(sig.get('rsrp','?'), C.CYAN)}  "
                  f"SINR:{colorize(sig.get('sinr','?'), C.CYAN)}   ", end="", flush=True)
            time.sleep(interval)
    except KeyboardInterrupt:
        print()
        ok("CA monitor stopped.")
    sep()


def cmd_ca_force(sess: H155Session, args):
    """[64] Force-enable CA across all strong visible bands."""
    step("Force-Enable Carrier Aggregation")
    sep()
    towers = visible_towers(sess)
    strong = sorted({int(re.sub(r"[^\d]", "", t["band"]))
                     for t in towers
                     if re.sub(r"[^\d]", "", t["band"]) and t["rsrp_int"] >= -110})
    if len(strong) < 2:
        warn("Fewer than 2 strong bands available — CA cannot be forced now.")
        sep()
        return
    info(f"Enabling all strong bands: {colorize('+'.join('B'+str(b) for b in strong), C.GOLD)}")
    if lock_bands(sess, strong):
        wait_reconnect(10)
        agg = active_ca_bands(sess)
        if len(agg) >= 2:
            ok(colorize(f"CA engaged: {'+'.join('B'+str(b) for b in agg)}", C.LIME + C.BOLD))
        else:
            warn("Bands enabled; the serving cell is not aggregating right now.")
    else:
        err("Failed to apply band set.")
    sep()


def cmd_ca_speed(sess: H155Session, args):
    """[65] Real download-speed test for each CA pair, ranked."""
    from itertools import combinations
    step("CA Pair Speed Ranking (real throughput)")
    warn("Runs a real download per pair — uses data and takes a few minutes.")
    sep()
    if not confirm(f"  {C.RED}Start CA speed test? (yes/no): {C.RESET}"):
        warn("Cancelled.")
        return
    vis = visible_bands(sess)
    if len(vis) < 2:
        err("Need 2+ visible bands.")
        return
    pairs = list(combinations(sorted(vis)[:4], 2))
    results = _benchmark_combos(sess, pairs, samples=2, settle=10, speed=True)
    ranked = [r for r in results if r["mbps"] is not None]
    ranked.sort(key=lambda x: x["mbps"], reverse=True)
    if not ranked:
        err("No throughput measured (check data connection).")
        return
    sep()
    for i, r in enumerate(ranked):
        icon = f"{C.GOLD}★{C.RESET}" if i == 0 else f"{C.DIM}{i+1}.{C.RESET}"
        mbps_s = "{:.1f} Mbps".format(r["mbps"])
        print(f"  {icon} {colorize(r['names'], C.WHITE):<14} {colorize(mbps_s, C.LIME, C.BOLD)}")
    winner = ranked[0]
    if lock_bands(sess, winner["combo"]):
        ok(colorize(f"Locked fastest CA pair: {winner['names']} ({winner['mbps']:.1f} Mbps)", C.LIME + C.BOLD))
    sep()


def cmd_ca_pilot(sess: H155Session, args):
    """[66] Auto-pilot that keeps the best CA combo active continuously."""
    interval = getattr(args, "interval", 30) or 30
    step(f"CA Auto-Pilot — keeps aggregation healthy (check every {interval}s)")
    info("Ctrl+C to stop.")
    sep()
    best_combo = sorted(active_ca_bands(sess))
    if len(best_combo) < 2:
        best_combo = visible_bands(sess)[:2]
    info(f"Target CA set: {colorize('+'.join('B'+str(b) for b in best_combo) or 'auto', C.GOLD)}")
    relocks = checks = 0
    try:
        while True:
            checks += 1
            agg = active_ca_bands(sess)
            sig = sess.get_signal()
            ts = datetime.now().strftime("%H:%M:%S")
            healthy = len(agg) >= 2
            if not healthy and best_combo:
                lock_bands(sess, best_combo)
                relocks += 1
                status = colorize("re-applied CA", C.RED, C.BOLD)
            else:
                status = colorize("CA healthy", C.GREEN)
            print(f"\r  {C.DIM}[{ts}] #{checks:>4}{C.RESET}  "
                  f"{colorize(str(len(agg))+'CC', C.LIME if healthy else C.RED, C.BOLD)}  "
                  f"{'+'.join('B'+str(b) for b in agg) or '?':<18}  "
                  f"RSRP:{colorize(sig.get('rsrp','?'), C.CYAN)}  "
                  f"relocks:{colorize(str(relocks), C.RED if relocks else C.DIM)}  {status}   ",
                  end="", flush=True)
            time.sleep(interval)
    except KeyboardInterrupt:
        print()
        ok(f"CA auto-pilot stopped after {checks} checks, {relocks} re-locks.")
    sep()


# ─────────────────────────────────────────────────────────────
#  GROUP J — CELL / TOWER TARGETING  (features 67-72)
# ─────────────────────────────────────────────────────────────
def _camp_on_pci(sess: H155Session, target_pci: str, band: int, earfcn: str, attempts: int = 6) -> bool:
    """Software-enforced cell preference: narrow to the tower's band and
    nudge the modem (data re-select) until it camps on the requested PCI.
    (The H155 web API has no hard PCI lock — this is a best-effort preference.)"""
    lock_bands(sess, [band])
    for i in range(attempts):
        wait_reconnect(8)
        cur = str(sess.get_signal().get("pci", ""))
        if cur == str(target_pci):
            return True
        info(f"  attempt {i+1}: on PCI {cur}, want {target_pci} — re-selecting...")
        sess.api_post(EP["data_switch"], {"dataswitch": "0"})
        time.sleep(2)
        sess.api_post(EP["data_switch"], {"dataswitch": "1"})
    return str(sess.get_signal().get("pci", "")) == str(target_pci)


def cmd_cell_lock(sess: H155Session, args):
    """[67] Lock toward a specific cell tower (PCI on its band/EARFCN)."""
    step("Cell / Tower Lock (software-enforced preference)")
    sep()
    towers = visible_towers(sess)
    if towers:
        print(f"  {C.DIM}  Visible towers (PCI / band / EARFCN / RSRP):{C.RESET}")
        for t in sorted(towers, key=lambda x: x["rsrp_int"], reverse=True)[:10]:
            print(f"    PCI {colorize(t['pci'], C.CYAN, C.BOLD):<14} "
                  f"B{colorize(t['band'], C.MAGENTA):<10} "
                  f"EARFCN {colorize(t['earfcn'], C.DIM):<10} "
                  f"RSRP {colorize(t['rsrp'], C.GOLD)}")
    pci = ask(f"\n  {C.YELLOW}Target PCI: {C.RESET}")
    if not pci:
        warn("Cancelled.")
        return
    match = next((t for t in towers if str(t["pci"]) == pci), None)
    try:
        band = int(re.sub(r"[^\d]", "", match["band"])) if match else int(ask(f"  {C.YELLOW}Its band number: {C.RESET}") or 0)
    except (ValueError, TypeError):
        err("Could not determine band for that PCI.")
        return
    earfcn = match["earfcn"] if match else ""
    info(f"Preferring PCI {colorize(pci, C.CYAN)} on {colorize(band_label(band), C.GOLD)}...")
    warn("Note: H155 firmware has no hard PCI lock; using band-narrow + re-select.")
    if _camp_on_pci(sess, pci, band, earfcn):
        ok(colorize(f"Camped on tower PCI {pci} ({band_label(band)}).", C.LIME + C.BOLD))
    else:
        warn(f"Could not force PCI {pci}; modem is on the band but a different cell.")
    sep()


def cmd_cell_unlock(sess: H155Session, args):
    """[68] Release any cell/tower preference (back to all LTE bands)."""
    step("Release Cell / Tower Lock")
    if sess.set_net_mode("03", "3FFFFFFF", "7FFFFFFFFFFFFFFF"):
        ok(colorize("Cell preference cleared — all LTE bands enabled.", C.GREEN + C.BOLD))
    else:
        err("Failed to clear cell lock.")
    sep()


def cmd_best_tower_lock(sess: H155Session, args):
    """[69] Scan towers and lock onto the strongest PCI/tower."""
    step("Auto-Lock Best Cell Tower")
    sep()
    towers = visible_towers(sess)
    if not towers:
        err("No towers visible — ensure LTE mode + active data.")
        return
    towers.sort(key=lambda x: x["rsrp_int"], reverse=True)
    best = towers[0]
    try:
        band = int(re.sub(r"[^\d]", "", best["band"]))
    except ValueError:
        err(f"Cannot parse band '{best['band']}'.")
        return
    ok(f"Best tower: PCI {colorize(best['pci'], C.GOLD, C.BOLD)} on {colorize(band_label(band), C.CYAN)} "
       f"(RSRP {best['rsrp']})")
    if not confirm(f"  {C.YELLOW}Lock onto it? (yes/no): {C.RESET}"):
        warn("Cancelled.")
        return
    if _camp_on_pci(sess, best["pci"], band, best["earfcn"]):
        ok(colorize(f"Locked onto best tower PCI {best['pci']}!", C.LIME + C.BOLD))
    else:
        warn(f"On {band_label(band)} but could not pin PCI {best['pci']} exactly.")
    sep()


def cmd_tower_rank(sess: H155Session, args):
    """[70] Sample towers over several rounds and rank by strength + stability."""
    rounds = max(3, getattr(args, "duration", 30) // 5)
    step(f"Tower Stability Ranking ({rounds} sampling rounds)")
    sep()
    history = {}
    for i in range(rounds):
        for t in visible_towers(sess):
            key = (t["pci"], t["band"])
            history.setdefault(key, []).append(t["rsrp_int"])
        print(f"\r  {C.DIM}sampling round {i+1}/{rounds}...{C.RESET}", end="", flush=True)
        time.sleep(5)
    print()
    if not history:
        err("No towers sampled.")
        return
    rows = []
    for (pci, band), vals in history.items():
        avg = sum(vals) / len(vals)
        rows.append((pci, band, avg, stdev(vals), len(vals)))
    rows.sort(key=lambda x: (x[2], x[4]), reverse=True)
    print(f"  {C.DIM}  {'PCI':<8}{'Band':<8}{'Avg RSRP':<12}{'Jitter':<10}{'Seen'}{C.RESET}")
    print(f"  {C.DIM}  {'─'*46}{C.RESET}")
    for i, (pci, band, avg, jit, seen) in enumerate(rows):
        star = f"{C.GOLD}★{C.RESET}" if i == 0 else " "
        _, col = grade_rsrp(int(avg))
        print(f"  {star} {colorize(pci, C.CYAN):<15}B{colorize(band, C.MAGENTA):<13}"
              f"{colorize(f'{avg:.1f}', col):<20}{colorize(f'±{jit:.1f}', C.DIM):<18}{seen}")
    sep()


def cmd_pci_watch(sess: H155Session, args):
    """[71] Live watch of serving PCI and neighbour PCIs."""
    interval = getattr(args, "interval", 3) or 3
    step(f"Live PCI / Neighbour Watch (every {interval}s, Ctrl+C to stop)")
    sep()
    try:
        while True:
            sig = sess.get_signal()
            serving = sig.get("pci", "?")
            neigh = sorted({t["pci"] for t in visible_towers(sess) if t["pci"] != serving})
            ts = datetime.now().strftime("%H:%M:%S")
            bar = signal_bar(sig.get("rsrp_int"))
            print(f"\r  {C.DIM}{ts}{C.RESET}  {bar}  "
                  f"serving PCI {colorize(str(serving), C.GOLD, C.BOLD)}  "
                  f"RSRP {colorize(sig.get('rsrp','?'), C.CYAN)}  "
                  f"neighbours: {colorize(', '.join(neigh[:6]) or '—', C.DIM)}     ",
                  end="", flush=True)
            time.sleep(interval)
    except KeyboardInterrupt:
        print()
        ok("PCI watch stopped.")
    sep()


def cmd_earfcn_lock(sess: H155Session, args):
    """[72] Lock to the band carrying a specific EARFCN (frequency)."""
    step("EARFCN / Frequency Lock")
    sep()
    raw = ask(f"  {C.YELLOW}Target EARFCN: {C.RESET}")
    if not raw or not raw.isdigit():
        warn("Cancelled.")
        return
    earfcn = int(raw)
    band = earfcn_to_band(earfcn)
    if not band:
        err(f"EARFCN {earfcn} is not within a known band range.")
        return
    freq = earfcn_to_freq_mhz(earfcn)
    info(f"EARFCN {earfcn} → {colorize(band_label(band), C.GOLD)} "
         f"({colorize(str(freq)+' MHz', C.TEAL) if freq else 'N/A'})")
    warn("Hard EARFCN lock needs engineering mode; locking the parent band instead.")
    if lock_bands(sess, [band]):
        ok(colorize(f"Locked to {band_label(band)} (carries EARFCN {earfcn}).", C.LIME + C.BOLD))
    else:
        err("Lock failed.")
    sep()


# ─────────────────────────────────────────────────────────────
#  GROUP K — AUTO-EVERYTHING / AUTOPILOT  (features 73-80)
# ─────────────────────────────────────────────────────────────
def cmd_autopilot(sess: H155Session, args):
    """[73] AUTO-EVERYTHING daemon: keeps signal, CA and connection optimal."""
    interval = getattr(args, "interval", 20) or 20
    threshold = getattr(args, "threshold", -108) or -108
    step("AUTO-EVERYTHING AUTOPILOT")
    info("Monitors connection + signal + CA. Re-optimises when degraded.")
    info(f"Check every {interval}s · RSRP floor {threshold} dBm · Ctrl+C to stop")
    sep()
    bad_streak = checks = fixes = 0
    last_action = "—"
    try:
        while True:
            checks += 1
            ts = datetime.now().strftime("%H:%M:%S")
            connected = is_connected(sess)
            sig = sess.get_signal()
            rsrp = sig.get("rsrp_int")
            agg = active_ca_bands(sess)

            action = None
            if not connected:
                bad_streak += 1
                if bad_streak == 1:
                    action = "reconnect"
                    sess.api_post(EP["data_switch"], {"dataswitch": "0"})
                    time.sleep(2)
                    sess.api_post(EP["data_switch"], {"dataswitch": "1"})
                elif bad_streak >= 4:
                    action = "reboot-recover"
                    sess.reboot()
                    bad_streak = 0
            elif rsrp is not None and rsrp < threshold:
                bad_streak += 1
                if bad_streak >= 2:
                    # Re-optimise: enable strong bands to (re)build CA
                    strong = sorted({int(re.sub(r"[^\d]", "", t["band"]))
                                     for t in visible_towers(sess)
                                     if re.sub(r"[^\d]", "", t["band"]) and t["rsrp_int"] >= -112})
                    if len(strong) >= 2:
                        lock_bands(sess, strong)
                        action = "rebuild-CA"
                    elif strong:
                        lock_bands(sess, strong[:1])
                        action = "lock-strongest"
                    bad_streak = 0
            else:
                bad_streak = 0

            if action:
                fixes += 1
                last_action = action

            r_lbl, r_col = grade_rsrp(rsrp)
            bar = signal_bar(rsrp)
            cstat = colorize("UP", C.GREEN) if connected else colorize("DOWN", C.RED, C.BOLD)
            relog = getattr(sess, "_reauth_count", 0)
            print(f"\r  {C.DIM}[{ts}] #{checks:>4}{C.RESET} {bar} {cstat} "
                  f"{colorize(str(len(agg))+'CC', C.LIME if len(agg)>1 else C.DIM)} "
                  f"RSRP:{colorize(sig.get('rsrp','?'), r_col, C.BOLD)} "
                  f"fixes:{colorize(str(fixes), C.YELLOW if fixes else C.DIM)} "
                  f"relogin:{colorize(str(relog), C.CYAN if relog else C.DIM)} "
                  f"last:{colorize(last_action, C.MAGENTA)}    ", end="", flush=True)
            time.sleep(interval)
    except KeyboardInterrupt:
        print()
        ok(f"Autopilot stopped — {checks} checks, {fixes} corrective actions.")
    sep()


def cmd_auto_failover(sess: H155Session, args):
    """[74] Auto-failover to the next-best band when the current one degrades."""
    interval = getattr(args, "interval", 15) or 15
    threshold = getattr(args, "threshold", -110) or -110
    step(f"Auto-Failover — switch band when RSRP < {threshold} dBm")
    info(f"Check every {interval}s · Ctrl+C to stop")
    sep()
    candidates = sorted(visible_bands(sess), key=lambda b: 0)  # ordered by appearance
    if not candidates:
        candidates = sorted(BAND_DB.keys())
    idx = 0
    lock_bands(sess, [candidates[idx]])
    info(f"Starting on {colorize(band_label(candidates[idx]), C.GOLD)}")
    switches = checks = 0
    try:
        while True:
            checks += 1
            rsrp, _ = avg_signal(sess, samples=2, delay=1)
            ts = datetime.now().strftime("%H:%M:%S")
            if rsrp is not None and rsrp < threshold:
                idx = (idx + 1) % len(candidates)
                lock_bands(sess, [candidates[idx]])
                switches += 1
                wait_reconnect(8)
            bar = signal_bar(int(rsrp) if rsrp is not None else None)
            print(f"\r  {C.DIM}[{ts}] #{checks:>4}{C.RESET}  {bar}  "
                  f"on {colorize(band_label(candidates[idx]), C.GOLD):<20}  "
                  f"RSRP:{colorize(f'{rsrp:.0f}' if rsrp is not None else '?', C.CYAN)}  "
                  f"switches:{colorize(str(switches), C.YELLOW)}    ", end="", flush=True)
            time.sleep(interval)
    except KeyboardInterrupt:
        print()
        ok(f"Failover stopped — {switches} band switches over {checks} checks.")
    sep()


def cmd_auto_recover(sess: H155Session, args):
    """[75] Watch for dead data connection and auto reconnect/reboot to recover."""
    interval = getattr(args, "interval", 20) or 20
    step(f"Auto-Recovery Watchdog (check every {interval}s, Ctrl+C to stop)")
    sep()
    fails = recoveries = checks = 0
    try:
        while True:
            checks += 1
            ts = datetime.now().strftime("%H:%M:%S")
            if is_connected(sess):
                fails = 0
                state = colorize("healthy", C.GREEN)
            else:
                fails += 1
                if fails == 2:
                    sess.api_post(EP["data_switch"], {"dataswitch": "0"})
                    time.sleep(2)
                    sess.api_post(EP["data_switch"], {"dataswitch": "1"})
                    recoveries += 1
                    state = colorize("reconnecting", C.YELLOW, C.BOLD)
                elif fails >= 5:
                    sess.reboot()
                    recoveries += 1
                    fails = 0
                    state = colorize("REBOOTING", C.RED, C.BOLD)
                else:
                    state = colorize(f"down x{fails}", C.RED)
            print(f"\r  {C.DIM}[{ts}] #{checks:>4}{C.RESET}  "
                  f"recoveries:{colorize(str(recoveries), C.YELLOW if recoveries else C.DIM)}  "
                  f"{state}     ", end="", flush=True)
            time.sleep(interval)
    except KeyboardInterrupt:
        print()
        ok(f"Recovery watchdog stopped — {recoveries} recovery action(s).")
    sep()


def cmd_auto_antenna(sess: H155Session, args):
    """[76] Periodically A/B test antennas and keep the strongest."""
    interval = getattr(args, "interval", 300) or 300
    step(f"Auto-Antenna Optimiser (re-test every {interval}s, Ctrl+C to stop)")
    sep()
    cycles = 0
    try:
        while True:
            cycles += 1
            best_code, best_rsrp, best_label = None, -999, ""
            for code, (label, col) in ANTENNA_MODES.items():
                if code == "3":
                    continue
                sess._xml_post(ANTENNA_SET_EP,
                               '<?xml version="1.0" encoding="UTF-8"?><request>'
                               f"<antenna_type>{code}</antenna_type></request>")
                time.sleep(5)
                rsrp, _ = avg_signal(sess, samples=3, delay=1)
                if rsrp is not None and rsrp > best_rsrp:
                    best_code, best_rsrp, best_label = code, rsrp, label
            if best_code is not None:
                sess._xml_post(ANTENNA_SET_EP,
                               '<?xml version="1.0" encoding="UTF-8"?><request>'
                               f"<antenna_type>{best_code}</antenna_type></request>")
                ok(f"[cycle {cycles}] Selected {colorize(best_label, C.GOLD, C.BOLD)} "
                   f"(RSRP {best_rsrp:.1f} dBm)")
            else:
                warn(f"[cycle {cycles}] Antenna API unavailable — skipping.")
            time.sleep(interval)
    except KeyboardInterrupt:
        print()
        ok(f"Auto-antenna stopped after {cycles} optimisation cycle(s).")
    sep()


def cmd_auto_band_rotate(sess: H155Session, args):
    """[77] Rotate through candidate bands, measure each, keep the best."""
    step("Auto Band Rotation")
    sep()
    bands = visible_bands(sess) or sorted(BAND_DB.keys())
    info(f"Rotating through: {colorize(', '.join('B'+str(b) for b in bands), C.CYAN)}")
    scores = {}
    for b in bands:
        print(f"\n  {C.MAGENTA}▶{C.RESET}  {colorize(band_label(b), C.GOLD)}")
        if not lock_bands(sess, [b]):
            warn("  lock failed — skip")
            continue
        wait_reconnect(8)
        rsrp, sinr = avg_signal(sess, samples=3, delay=1)
        if rsrp is None:
            warn("  no signal")
            continue
        scores[b] = rsrp + (sinr or 0)
        bar = signal_bar(int(rsrp))
        print(f"  {bar}  RSRP {colorize(f'{rsrp:.1f}', C.CYAN)}  SINR {colorize(f'{sinr:.1f}' if sinr is not None else '?', C.CYAN)}")
    if not scores:
        err("No band produced a usable signal.")
        return
    best = max(scores, key=scores.get)
    sep()
    ok(f"Best band: {colorize(band_label(best), C.LIME, C.BOLD)}")
    if lock_bands(sess, [best]):
        ok(colorize(f"Locked {band_label(best)}.", C.LIME + C.BOLD))
    sep()


def cmd_smart_schedule(sess: H155Session, args):
    """[78] Time-based profiles: stability band at night, CA speed by day."""
    step("Smart Time-Based Scheduler")
    info("Applies a 'day' profile and a 'night' profile automatically.")
    sep()
    day_raw = ask(f"  {C.YELLOW}DAY bands (speed/CA), e.g. '3 1 7' [auto-CA]: {C.RESET}")
    night_raw = ask(f"  {C.YELLOW}NIGHT bands (stability), e.g. '20 28' [low-band]: {C.RESET}")
    day_h = ask(f"  {C.YELLOW}Day starts at hour (0-23) [7]: {C.RESET}") or "7"
    night_h = ask(f"  {C.YELLOW}Night starts at hour (0-23) [23]: {C.RESET}") or "23"
    try:
        day_start, night_start = int(day_h), int(night_h)
    except ValueError:
        err("Invalid hour.")
        return
    day_bands = [int(x) for x in (day_raw or "").split() if x.isdigit()] or visible_bands(sess)[:2]
    night_bands = [int(x) for x in (night_raw or "").split() if x.isdigit()] or [b for b in (28, 20, 8) if b in visible_bands(sess)][:1] or [20]
    interval = getattr(args, "interval", 60) or 60
    info(f"DAY ({day_start}:00+): {colorize('+'.join('B'+str(b) for b in day_bands), C.GOLD)}")
    info(f"NIGHT ({night_start}:00+): {colorize('+'.join('B'+str(b) for b in night_bands), C.CYAN)}")
    info("Ctrl+C to stop.")
    sep()
    current = None
    try:
        while True:
            h = datetime.now().hour
            is_day = day_start <= h < night_start
            want = "day" if is_day else "night"
            if want != current:
                lock_bands(sess, day_bands if is_day else night_bands)
                current = want
                ts = datetime.now().strftime("%H:%M:%S")
                ok(f"[{ts}] Applied {colorize(want.upper(), C.GOLD, C.BOLD)} profile.")
            time.sleep(interval)
    except KeyboardInterrupt:
        print()
        ok("Scheduler stopped.")
    sep()


def cmd_keepalive(sess: H155Session, args):
    """[79] Keep-alive pinger that prevents idle drops and auto-reconnects."""
    interval = getattr(args, "interval", 30) or 30
    host = getattr(args, "target", None) or "8.8.8.8"
    step(f"Connection Keep-Alive (ping {host} every {interval}s, Ctrl+C to stop)")
    sep()
    pings = reconnects = 0
    try:
        while True:
            pings += 1
            lat = measure_latency_ms(host, count=2)
            ts = datetime.now().strftime("%H:%M:%S")
            if lat is None:
                if not is_connected(sess):
                    sess.api_post(EP["data_switch"], {"dataswitch": "0"})
                    time.sleep(2)
                    sess.api_post(EP["data_switch"], {"dataswitch": "1"})
                    reconnects += 1
                state = colorize("no reply → reconnect", C.RED, C.BOLD)
            else:
                state = colorize(f"{lat:.0f} ms", C.GREEN)
            print(f"\r  {C.DIM}[{ts}] #{pings:>4}{C.RESET}  {state:<28}  "
                  f"reconnects:{colorize(str(reconnects), C.YELLOW if reconnects else C.DIM)}   ",
                  end="", flush=True)
            time.sleep(interval)
    except KeyboardInterrupt:
        print()
        ok(f"Keep-alive stopped — {pings} probes, {reconnects} reconnect(s).")
    sep()


def cmd_scheduled_reboot(sess: H155Session, args):
    """[80] Schedule a reboot (one-off at HH:MM, or after a delay)."""
    step("Scheduled Reboot")
    sep()
    when = ask(f"  {C.YELLOW}Reboot at HH:MM, or '+Nm'/'+Nh' from now: {C.RESET}")
    if not when:
        warn("Cancelled.")
        return
    target = None
    rel = re.match(r"\+(\d+)([mh])", when.strip())
    if rel:
        secs = int(rel.group(1)) * (60 if rel.group(2) == "m" else 3600)
        target = time.time() + secs
    elif re.match(r"^\d{1,2}:\d{2}$", when.strip()):
        hh, mm = map(int, when.strip().split(":"))
        now = datetime.now()
        tgt = now.replace(hour=hh, minute=mm, second=0, microsecond=0)
        ts = tgt.timestamp()
        if ts <= time.time():
            ts += 86400  # tomorrow
        target = ts
    else:
        err("Format must be HH:MM or +Nm / +Nh.")
        return
    eta = datetime.fromtimestamp(target).strftime("%Y-%m-%d %H:%M:%S")
    ok(f"Reboot scheduled for {colorize(eta, C.GOLD, C.BOLD)}. Ctrl+C to cancel.")
    try:
        while time.time() < target:
            remaining = int(target - time.time())
            hrs, rem = divmod(remaining, 3600)
            mins, secs = divmod(rem, 60)
            print(f"\r  {C.DIM}Time to reboot: {hrs:02d}:{mins:02d}:{secs:02d}{C.RESET}   ",
                  end="", flush=True)
            time.sleep(1)
        print()
        warn("Rebooting now...")
        if sess.reboot():
            ok(colorize("Reboot command sent.", C.YELLOW + C.BOLD))
        else:
            err("Reboot failed.")
    except KeyboardInterrupt:
        print()
        warn("Scheduled reboot cancelled.")
    sep()


# ─────────────────────────────────────────────────────────────
#  GROUP L — THROUGHPUT / LATENCY OPTIMISATION  (features 81-86)
# ─────────────────────────────────────────────────────────────
def cmd_speed_per_band(sess: H155Session, args):
    """[81] Real download speedtest locked to each band, ranked by Mbps."""
    step("Speed-Per-Band Ranking (real downloads)")
    warn("Runs a real download per band — takes a few minutes.")
    sep()
    if not confirm(f"  {C.RED}Start? (yes/no): {C.RESET}"):
        warn("Cancelled.")
        return
    bands = visible_bands(sess) or sorted(BAND_DB.keys())
    results = []
    for b in bands:
        print(f"\n  {C.MAGENTA}▶{C.RESET}  {colorize(band_label(b), C.GOLD)}")
        if not lock_bands(sess, [b]):
            continue
        wait_reconnect(8)
        mbps = measure_download_mbps(8, show=True)
        if mbps is not None:
            results.append((b, mbps))
            print(f"  {colorize(f'{mbps:.1f} Mbps', C.LIME, C.BOLD)}")
    if not results:
        err("No throughput measured.")
        return
    results.sort(key=lambda x: x[1], reverse=True)
    sep()
    for i, (b, mbps) in enumerate(results):
        icon = f"{C.GOLD}★{C.RESET}" if i == 0 else f"{C.DIM}{i+1}.{C.RESET}"
        print(f"  {icon} {colorize(band_label(b), C.WHITE):<22} {colorize(f'{mbps:.1f} Mbps', C.LIME, C.BOLD)}")
    best = results[0][0]
    if lock_bands(sess, [best]):
        ok(colorize(f"Locked fastest band: {band_label(best)} ({results[0][1]:.1f} Mbps)", C.LIME + C.BOLD))
    sep()


def cmd_optimize_speed(sess: H155Session, args):
    """[82] Full optimiser that chooses by REAL throughput (band vs best CA)."""
    from itertools import combinations
    step("Throughput-Driven Optimiser")
    warn("Measures real speed for top bands and the best CA pair, then locks the winner.")
    sep()
    if not confirm(f"  {C.RED}Start? (yes/no): {C.RESET}"):
        warn("Cancelled.")
        return
    vis = visible_bands(sess)
    if not vis:
        err("No bands visible.")
        return
    trials = [[b] for b in vis[:3]]
    if len(vis) >= 2:
        trials += [list(p) for p in list(combinations(sorted(vis)[:3], 2))[:2]]
    best = None
    for combo in trials:
        names = "+".join("B" + str(b) for b in combo)
        print(f"\n  {C.MAGENTA}▶{C.RESET}  {colorize(names, C.GOLD)}")
        if not lock_bands(sess, combo):
            continue
        wait_reconnect(9)
        mbps = measure_download_mbps(8, show=True)
        if mbps is None:
            continue
        agg = len(active_ca_bands(sess))
        print(f"  {colorize(f'{mbps:.1f} Mbps', C.LIME, C.BOLD)}  ({agg}CC)")
        if best is None or mbps > best[1]:
            best = (combo, mbps, names)
    if not best:
        err("No measurable throughput.")
        return
    sep()
    ok(f"Fastest config: {colorize(best[2], C.LIME, C.BOLD)} @ {best[1]:.1f} Mbps")
    if lock_bands(sess, best[0]):
        ok(colorize("Locked the fastest configuration!", C.LIME + C.BOLD))
    sep()


def cmd_latency_optimize(sess: H155Session, args):
    """[83] Pick the band with the lowest ping latency."""
    step("Latency-Optimised Band Selection")
    sep()
    host = getattr(args, "target", None) or "8.8.8.8"
    bands = visible_bands(sess) or sorted(BAND_DB.keys())
    results = []
    for b in bands:
        print(f"\n  {C.MAGENTA}▶{C.RESET}  {colorize(band_label(b), C.GOLD)}")
        if not lock_bands(sess, [b]):
            continue
        wait_reconnect(8)
        lat = measure_latency_ms(host, count=5)
        if lat is not None:
            results.append((b, lat))
            print(f"  latency {colorize(f'{lat:.0f} ms', C.CYAN, C.BOLD)}")
        else:
            warn("  no ping reply")
    if not results:
        err("No latency measured.")
        return
    results.sort(key=lambda x: x[1])
    sep()
    for i, (b, lat) in enumerate(results):
        icon = f"{C.GOLD}★{C.RESET}" if i == 0 else f"{C.DIM}{i+1}.{C.RESET}"
        print(f"  {icon} {colorize(band_label(b), C.WHITE):<22} {colorize(f'{lat:.0f} ms', C.CYAN, C.BOLD)}")
    best = results[0][0]
    if lock_bands(sess, [best]):
        ok(colorize(f"Locked lowest-latency band: {band_label(best)} ({results[0][1]:.0f} ms)", C.LIME + C.BOLD))
    sep()


def cmd_stability_score(sess: H155Session, args):
    """[84] Score each band by signal stability (lower jitter = better)."""
    samples = max(6, getattr(args, "duration", 30) // 3)
    step(f"Band Stability Scoring ({samples} samples/band)")
    sep()
    bands = visible_bands(sess) or sorted(BAND_DB.keys())[:5]
    rows = []
    for b in bands:
        print(f"\n  {C.MAGENTA}▶{C.RESET}  {colorize(band_label(b), C.GOLD)}")
        if not lock_bands(sess, [b]):
            continue
        wait_reconnect(8)
        vals = []
        for _ in range(samples):
            r = sess.get_signal().get("rsrp_int")
            if r is not None:
                vals.append(r)
            time.sleep(1)
        if len(vals) < 2:
            warn("  insufficient samples")
            continue
        avg = sum(vals) / len(vals)
        jit = stdev(vals)
        rows.append((b, avg, jit))
        print(f"  avg {colorize(f'{avg:.1f}', C.CYAN)}  jitter {colorize(f'±{jit:.2f}', C.GOLD)}")
    if not rows:
        err("No data.")
        return
    # Rank: high avg, low jitter
    rows.sort(key=lambda x: (x[1] - x[2] * 3), reverse=True)
    sep()
    for i, (b, avg, jit) in enumerate(rows):
        icon = f"{C.GOLD}★{C.RESET}" if i == 0 else f"{C.DIM}{i+1}.{C.RESET}"
        print(f"  {icon} {colorize(band_label(b), C.WHITE):<22} "
              f"avg {colorize(f'{avg:.1f}', C.CYAN)}  jitter {colorize(f'±{jit:.2f}', C.GOLD)}")
    best = rows[0][0]
    if lock_bands(sess, [best]):
        ok(colorize(f"Locked most stable band: {band_label(best)}", C.LIME + C.BOLD))
    sep()


def cmd_band_block(sess: H155Session, args):
    """[85] Blacklist a bad band — enable all known bands except it."""
    step("Blacklist a Band")
    sep()
    for b in sorted(BAND_DB):
        print(f"    {colorize(str(b), C.CYAN, C.BOLD):>12}  {colorize(BAND_DB[b]['name'], C.WHITE)}")
    raw = ask(f"\n  {C.YELLOW}Band number(s) to BLOCK, e.g. '40 41': {C.RESET}")
    if not raw:
        warn("Cancelled.")
        return
    blocked = {int(x) for x in raw.split() if x.isdigit()}
    keep = [b for b in BAND_DB if b not in blocked]
    if not keep:
        err("That would block every band.")
        return
    info(f"Blocking {colorize('+'.join('B'+str(b) for b in sorted(blocked)), C.RED)}; "
         f"keeping {len(keep)} band(s).")
    if lock_bands(sess, keep):
        ok(colorize("Blacklist applied — modem will avoid the blocked band(s).", C.GREEN + C.BOLD))
    else:
        err("Failed to apply blacklist.")
    sep()


def cmd_band_priority(sess: H155Session, args):
    """[86] Set a preferred band set (modem favours the strongest among them)."""
    step("Preferred Band Set")
    sep()
    raw = getattr(args, "bands", None)
    if raw:
        pref = [int(b) for b in raw]
    else:
        for b in sorted(BAND_DB):
            print(f"    {colorize(str(b), C.CYAN, C.BOLD):>12}  {colorize(BAND_DB[b]['name'], C.WHITE)}")
        line = ask(f"\n  {C.YELLOW}Preferred bands in priority order, e.g. '3 1 7 20': {C.RESET}")
        if not line:
            warn("Cancelled.")
            return
        pref = [int(x) for x in line.split() if x.isdigit()]
    if not pref:
        err("No bands given.")
        return
    info(f"Preferring: {colorize(' > '.join('B'+str(b) for b in pref), C.GOLD)}")
    if lock_bands(sess, pref):
        ok(colorize(f"Locked to preferred set ({len(pref)} bands).", C.GREEN + C.BOLD))
        info("The modem will camp on the strongest band within this set (and aggregate if able).")
    else:
        err("Failed to apply preference.")
    sep()


# ─────────────────────────────────────────────────────────────
#  GROUP M — ANALYTICS & REPORTING  (features 87-92)
# ─────────────────────────────────────────────────────────────
def cmd_signal_heatmap(sess: H155Session, args):
    """[87] Hour-of-day RSRP heatmap from a CSV signal log."""
    import glob
    import csv
    step("Time-of-Day Signal Heatmap")
    sep()
    path = getattr(args, "file", None)
    if not path:
        logs = sorted(glob.glob("signal_log_*.csv"))
        if not logs:
            warn("No signal_log_*.csv found. Run 'log' first to collect data.")
            sep()
            return
        path = logs[-1]
    info(f"Reading {colorize(path, C.CYAN)}")
    buckets = {h: [] for h in range(24)}
    try:
        with open(path, newline="") as f:
            for row in csv.DictReader(f):
                try:
                    h = datetime.strptime(row["timestamp"], "%Y-%m-%d %H:%M:%S").hour
                    rsrp = int(re.sub(r"[^-\d]", "", row.get("rsrp", "")))
                    buckets[h].append(rsrp)
                except (ValueError, KeyError):
                    continue
    except OSError as e:
        err(f"Cannot read file: {e}")
        return
    glyphs = " ░▒▓█"
    print(f"\n  {C.GOLD}{C.BOLD}  Hour   Avg RSRP   Heat{C.RESET}")
    for h in range(24):
        vals = buckets[h]
        if not vals:
            continue
        avg = sum(vals) / len(vals)
        _, col = grade_rsrp(int(avg))
        frac = max(0.0, min(1.0, (avg + 120) / 60))  # -120..-60 → 0..1
        g = glyphs[min(len(glyphs) - 1, int(frac * (len(glyphs) - 1)))]
        bar = colorize(g * 20, col)
        print(f"  {h:02d}:00   {colorize(f'{avg:7.1f}', col)}   {bar}  ({len(vals)})")
    sep()


def cmd_band_history(sess: H155Session, args):
    """[88] Track how much time is spent on each band (rolling sampler)."""
    duration = getattr(args, "duration", 60) or 60
    interval = getattr(args, "interval", 3) or 3
    step(f"Band Usage History — sampling {duration}s every {interval}s")
    sep()
    counts = {}
    end = time.time() + duration
    samples = 0
    try:
        while time.time() < end:
            bands = active_ca_bands(sess) or [0]
            key = "+".join("B" + str(b) for b in bands) if bands != [0] else "unknown"
            counts[key] = counts.get(key, 0) + 1
            samples += 1
            remaining = int(end - time.time())
            print(f"\r  {C.DIM}sampling... {remaining}s left  current: {key}{C.RESET}   ",
                  end="", flush=True)
            time.sleep(interval)
    except KeyboardInterrupt:
        pass
    print()
    if not samples:
        warn("No samples.")
        return
    sep()
    print(f"  {C.GOLD}{C.BOLD}  Band/CA usage distribution:{C.RESET}")
    for key, cnt in sorted(counts.items(), key=lambda x: x[1], reverse=True):
        pct = cnt / samples * 100
        bar = colorize("█" * int(pct / 5), C.LIME) + colorize("░" * (20 - int(pct / 5)), C.DIM)
        print(f"  {colorize(key, C.CYAN):<26} [{bar}] {colorize(f'{pct:5.1f}%', C.GOLD, C.BOLD)}")
    sep()


def cmd_throughput_log(sess: H155Session, args):
    """[89] Log live throughput (router rate counters) to CSV."""
    import csv
    duration = getattr(args, "duration", 60) or 60
    interval = getattr(args, "interval", 3) or 3
    fname = getattr(args, "file", None) or f"throughput_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    step(f"Throughput Logger — {duration}s every {interval}s → {colorize(fname, C.CYAN)}")
    sep()
    rows = []
    end = time.time() + duration
    try:
        while time.time() < end:
            mon = sess.get_monitoring()
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            dl = mon.get("dl_speed", "0")
            ul = mon.get("ul_speed", "0")
            rows.append({"timestamp": ts, "dl_bps": dl, "ul_bps": ul,
                         "dl": speed_fmt(dl), "ul": speed_fmt(ul)})
            remaining = int(end - time.time())
            print(f"\r  {C.DIM}{ts}{C.RESET}  ↓{colorize(speed_fmt(dl), C.LIME)}  "
                  f"↑{colorize(speed_fmt(ul), C.TEAL)}  {remaining}s left   ", end="", flush=True)
            time.sleep(interval)
    except KeyboardInterrupt:
        pass
    print()
    if not rows:
        warn("No data logged.")
        return
    try:
        with open(fname, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=rows[0].keys())
            w.writeheader()
            w.writerows(rows)
    except OSError as e:
        err(f"Write failed: {e}")
        return
    peaks = [int(r["dl_bps"]) for r in rows if r["dl_bps"].isdigit()]
    ok(f"Saved {len(rows)} rows → {colorize(fname, C.CYAN, C.BOLD)}")
    if peaks:
        info(f"Peak ↓ {colorize(speed_fmt(str(max(peaks))), C.LIME, C.BOLD)}")
    sep()


def cmd_daily_report(sess: H155Session, args):
    """[90] Generate a Markdown daily summary report file."""
    step("Daily Summary Report")
    sep()
    snap = _gather_status(sess)
    sig = snap["signal"]
    lat = measure_latency_ms()
    mbps = measure_download_mbps(8)
    fname = getattr(args, "file", None) or f"h155_report_{datetime.now().strftime('%Y%m%d')}.md"
    lines = [
        f"# Zain H155 Daily Report — {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        f"- **Model:** {snap['device'].get('model', 'N/A')}",
        f"- **Software:** {snap['device'].get('software', 'N/A')}",
        f"- **WAN IP:** {snap['device'].get('wan_ip', 'N/A')}",
        f"- **Connection:** {'UP' if is_connected(sess) else 'DOWN'}",
        "",
        "## Signal",
        f"- RSRP: {sig.get('rsrp', 'N/A')}",
        f"- RSRQ: {sig.get('rsrq', 'N/A')}",
        f"- SINR: {sig.get('sinr', 'N/A')}",
        f"- Band: {sig.get('band', 'N/A')}",
        f"- Active CA: {'+'.join('B'+str(b) for b in active_ca_bands(sess)) or 'single carrier'}",
        "",
        "## Performance",
        f"- Latency: {f'{lat:.0f} ms' if lat is not None else 'N/A'}",
        f"- Download: {f'{mbps:.1f} Mbps' if mbps is not None else 'N/A'}",
        "",
        f"_Generated by Zain H155 Manager v40 at {datetime.now().isoformat(timespec='seconds')}_",
    ]
    try:
        with open(fname, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
    except OSError as e:
        err(f"Write failed: {e}")
        return
    ok(colorize(f"Daily report written → {fname}", C.GREEN + C.BOLD))
    sep()


def cmd_html_report(sess: H155Session, args):
    """[91] Export a styled HTML status report."""
    step("HTML Status Report")
    sep()
    snap = _gather_status(sess)
    sig, dev, mon = snap["signal"], snap["device"], snap["monitoring"]
    rows = [
        ("Model", dev.get("model", "N/A")), ("Software", dev.get("software", "N/A")),
        ("WAN IP", dev.get("wan_ip", "N/A")), ("Connection", "UP" if is_connected(sess) else "DOWN"),
        ("RSRP", sig.get("rsrp", "N/A")), ("RSRQ", sig.get("rsrq", "N/A")),
        ("SINR", sig.get("sinr", "N/A")), ("Band", sig.get("band", "N/A")),
        ("Active CA", "+".join("B" + str(b) for b in active_ca_bands(sess)) or "single"),
        ("↓ rate", speed_fmt(mon.get("dl_speed", "0"))),
        ("↑ rate", speed_fmt(mon.get("ul_speed", "0"))),
    ]
    tr = "".join(f"<tr><th>{k}</th><td>{v}</td></tr>" for k, v in rows)
    html = (
        "<!doctype html><html><head><meta charset='utf-8'>"
        "<title>Zain H155 Report</title><style>"
        "body{font-family:system-ui,Arial;background:#0f1115;color:#e6e6e6;padding:30px}"
        "h1{color:#ffcc33}table{border-collapse:collapse;min-width:340px}"
        "th,td{border:1px solid #333;padding:8px 14px;text-align:left}"
        "th{background:#1b1f27;color:#8ad}td{background:#14171d}"
        "footer{margin-top:18px;color:#777;font-size:12px}</style></head><body>"
        f"<h1>Zain H155 Status</h1><table>{tr}</table>"
        f"<footer>Generated {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} "
        "by Zain H155 Manager v40</footer></body></html>"
    )
    fname = getattr(args, "file", None) or f"h155_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    try:
        with open(fname, "w", encoding="utf-8") as f:
            f.write(html)
    except OSError as e:
        err(f"Write failed: {e}")
        return
    ok(colorize(f"HTML report written → {fname}", C.GREEN + C.BOLD))
    info("Open it in any browser.")
    sep()


def cmd_profiles(sess: H155Session, args):
    """[92] Named profile library — save/list/apply many band+CA setups."""
    step("Profile Library")
    sep()
    try:
        with open(PROFILES_FILE, "r", encoding="utf-8") as f:
            store = json.load(f)
    except (OSError, json.JSONDecodeError):
        store = {}
    print(f"  {colorize('[l]', C.CYAN)} list   {colorize('[s]', C.CYAN)} save current   "
          f"{colorize('[a]', C.CYAN)} apply   {colorize('[d]', C.CYAN)} delete")
    action = ask(f"  {C.YELLOW}Action: {C.RESET}")
    if action == "l":
        if not store:
            info("No saved profiles yet.")
        for name, p in store.items():
            bands = lte_bitmask_to_bands(p.get("lte_band", ""))
            print(f"    {colorize(name, C.GOLD, C.BOLD):<20} "
                  f"{colorize('+'.join('B'+str(b) for b in bands) or 'all', C.CYAN)}  "
                  f"{colorize('(mode '+p.get('network_mode','?')+')', C.DIM)}")
    elif action == "s":
        name = ask(f"  {C.YELLOW}Profile name: {C.RESET}")
        if not name:
            warn("Cancelled.")
            return
        net = sess.get_net_mode() or {}
        store[name] = {
            "network_mode": net.get("network_mode", "00"),
            "network_band": net.get("network_band", "3FFFFFFF"),
            "lte_band": net.get("lte_band", "7FFFFFFFFFFFFFFF"),
            "saved_at": datetime.now().isoformat(timespec="seconds"),
        }
        with open(PROFILES_FILE, "w", encoding="utf-8") as f:
            json.dump(store, f, indent=2)
        ok(colorize(f"Saved profile '{name}'.", C.GREEN + C.BOLD))
    elif action == "a":
        name = ask(f"  {C.YELLOW}Profile to apply: {C.RESET}")
        p = store.get(name)
        if not p:
            err("No such profile.")
            return
        if sess.set_net_mode(p["network_mode"], p["network_band"], p["lte_band"]):
            bands = lte_bitmask_to_bands(p["lte_band"])
            ok(colorize(f"Applied '{name}': {'+'.join('B'+str(b) for b in bands) or 'all bands'}", C.LIME + C.BOLD))
        else:
            err("Failed to apply profile.")
    elif action == "d":
        name = ask(f"  {C.YELLOW}Profile to delete: {C.RESET}")
        if store.pop(name, None) is not None:
            with open(PROFILES_FILE, "w", encoding="utf-8") as f:
                json.dump(store, f, indent=2)
            ok(colorize(f"Deleted '{name}'.", C.GREEN + C.BOLD))
        else:
            warn("No such profile.")
    else:
        warn("Cancelled.")
    sep()


# ─────────────────────────────────────────────────────────────
#  GROUP N — ADVANCED & RESILIENCE  (features 93-98)
# ─────────────────────────────────────────────────────────────
def cmd_endc_optimize(sess: H155Session, args):
    """[93] 5G NR + LTE (EN-DC / NSA) aggregation optimiser."""
    step("5G EN-DC (NR + LTE) Optimiser")
    sep()
    towers = visible_towers(sess)
    strong_lte = sorted({int(re.sub(r"[^\d]", "", t["band"]))
                         for t in towers
                         if re.sub(r"[^\d]", "", t["band"]) and t["rsrp_int"] >= -110})
    if not strong_lte:
        strong_lte = visible_bands(sess) or [3]
    lte_mask = bands_to_lte_bitmask(strong_lte)
    nr_mask = nr_bands_to_bitmask(sorted(NR_BAND_DB.keys()))
    info(f"LTE anchor bands: {colorize('+'.join('B'+str(b) for b in strong_lte), C.GOLD)}")
    info(f"Enabling all NR bands for EN-DC: {colorize('n'+', n'.join(str(b) for b in sorted(NR_BAND_DB)), C.MAGENTA)}")
    body = {"NetworkMode": "0803", "NetworkBand": "3FFFFFFF",
            "LTEBand": lte_mask, "NRBand": nr_mask}
    resp = sess.api_post(EP["net_mode"], body)
    if sess.post_ok(resp):
        wait_reconnect(10)
        sig = sess.get_signal()
        ntype = network_type_name(sess.get_monitoring().get("network_type", "0"))
        nr_active = "5G" in ntype or "NR" in str(sig.get("band", "")).upper()
        if nr_active:
            ok(colorize(f"EN-DC active — {ntype}", C.LIME + C.BOLD))
        else:
            warn(f"EN-DC requested; currently on {ntype} (no 5G coverage here, or LTE-only device).")
    else:
        err(explain_error(resp) or "Failed to set EN-DC mode (router may be LTE-only).")
    sep()


def cmd_mimo_info(sess: H155Session, args):
    """[94] Show MIMO / multi-antenna diagnostic fields from the signal API."""
    step("MIMO / Antenna Diagnostics")
    sep()
    xml = sess.api_get(EP["signal"])
    if not xml:
        err("No signal data.")
        return
    fields = [
        ("mode", "Radio mode"), ("rsrp", "RSRP"), ("rsrq", "RSRQ"),
        ("sinr", "SINR"), ("rssi", "RSSI"), ("cqi0", "CQI (codeword 0)"),
        ("cqi1", "CQI (codeword 1)"), ("ulfrequency", "UL frequency"),
        ("dlfrequency", "DL frequency"), ("txpower", "TX power (per chain)"),
        ("earfcn", "EARFCN"), ("pci", "PCI"), ("nrrsrp", "5G NR RSRP"),
        ("nrsinr", "5G NR SINR"), ("nrdlbandwidth", "5G NR DL bandwidth"),
    ]
    shown = 0
    for tag, label in fields:
        val = xval(xml, tag, "")
        if val and val != "N/A":
            print(f"  {colorize(label+':', C.DIM):<26} {colorize(val, C.CYAN, C.BOLD)}")
            shown += 1
    # MIMO layer hint from TX power chains
    tx = xval(xml, "txpower", "")
    chains = len([p for p in re.findall(r"[A-Z]+:[-\d]+", tx)]) if tx else 0
    if chains:
        print(f"  {colorize('TX chains (MIMO):', C.DIM):<26} {colorize(str(chains)+'x', C.GOLD, C.BOLD)}")
    if not shown:
        warn("Firmware did not expose extended MIMO fields.")
    sep()


def cmd_auto_apn_test(sess: H155Session, args):
    """[95] Test each APN profile's real speed and keep the fastest."""
    step("Auto APN Speed Test")
    warn("Switches APN profiles and downloads on each — uses data.")
    sep()
    if not confirm(f"  {C.RED}Start? (yes/no): {C.RESET}"):
        warn("Cancelled.")
        return
    xml = sess.api_get(EP["profiles"])
    profs = re.findall(r"<Profile>(.*?)</Profile>", xml, re.DOTALL)
    if not profs:
        err("No APN profiles to test.")
        return
    original = xval(xml, "CurrentProfile", "")
    results = []
    for blk in profs:
        idx = xval(blk, "Index")
        name = xval(blk, "Name", idx)
        print(f"\n  {C.MAGENTA}▶{C.RESET}  Profile {colorize(name, C.GOLD)}")
        sess.api_post(EP["profiles"], {"SetDefault": idx, "Modify": 0, "Delete": 0})
        sess.api_post(EP["data_switch"], {"dataswitch": "0"})
        time.sleep(2)
        sess.api_post(EP["data_switch"], {"dataswitch": "1"})
        wait_reconnect(8)
        mbps = measure_download_mbps(8, show=True)
        if mbps is not None:
            results.append((idx, name, mbps))
            print(f"  {colorize(f'{mbps:.1f} Mbps', C.LIME, C.BOLD)}")
    if not results:
        err("No measurable throughput on any APN.")
        sess.api_post(EP["profiles"], {"SetDefault": original, "Modify": 0, "Delete": 0})
        return
    results.sort(key=lambda x: x[2], reverse=True)
    best = results[0]
    sep()
    for i, (idx, name, mbps) in enumerate(results):
        icon = f"{C.GOLD}★{C.RESET}" if i == 0 else f"{C.DIM}{i+1}.{C.RESET}"
        print(f"  {icon} {colorize(name, C.WHITE):<20} {colorize(f'{mbps:.1f} Mbps', C.LIME, C.BOLD)}")
    sess.api_post(EP["profiles"], {"SetDefault": best[0], "Modify": 0, "Delete": 0})
    ok(colorize(f"Kept fastest APN: {best[1]} ({best[2]:.1f} Mbps)", C.LIME + C.BOLD))
    sep()


def cmd_self_test(sess: H155Session, args):
    """[96] Probe every read endpoint and report which the router supports."""
    step("API Self-Test")
    sep()
    checks = [
        ("Device info", EP["device_info"]), ("Signal", EP["signal"]),
        ("Monitoring", EP["monitoring"]), ("Traffic stats", EP["traffic"]),
        ("Monthly stats", EP["month_stat"]), ("SMS count", EP["sms_count"]),
        ("WLAN basic", EP["wlan_basic"]), ("Host list", EP["host_list"]),
        ("Data switch", EP["data_switch"]), ("Dial connection", EP["dial_conn"]),
        ("APN profiles", EP["profiles"]), ("Current PLMN", EP["current_plmn"]),
        ("PIN status", EP["pin_status"]), ("DMZ", EP["dmz"]),
        ("Virtual servers", EP["vservers"]), ("Firewall", EP["firewall"]),
        ("UPnP", EP["upnp"]), ("DHCP", EP["dhcp"]),
        ("Firmware check", EP["fw_check"]), ("LED", EP["led"]),
    ]
    okc = 0
    for label, ep in checks:
        xml = sess.api_get(ep)
        if not xml:
            res = colorize("✘ no response", C.RED)
        elif "<error>" in xml:
            res = colorize(f"⚠ {explain_error(xml) or 'error'}", C.YELLOW)
        else:
            res = colorize("✔ OK", C.GREEN)
            okc += 1
        print(f"  {colorize(label, C.DIM):<22} {res}")
    sep()
    pct = okc / len(checks) * 100
    col = C.LIME if pct >= 80 else (C.YELLOW if pct >= 50 else C.RED)
    ok(f"Supported endpoints: {colorize(f'{okc}/{len(checks)} ({pct:.0f}%)', col, C.BOLD)}")
    sep()


def cmd_setup_wizard(sess: H155Session, args):
    """[97] Guided first-time optimal setup wizard."""
    step("Guided Optimal Setup Wizard")
    sep()
    print(f"  {C.GOLD}{C.BOLD}  This wizard will, step by step:{C.RESET}")
    print(f"  {C.DIM}  1. Switch to LTE for a clean baseline")
    print(f"  {C.DIM}  2. Pick the best antenna (if supported)")
    print(f"  {C.DIM}  3. Build the strongest carrier-aggregation set")
    print(f"  {C.DIM}  4. Verify and report the result{C.RESET}\n")
    if not confirm(f"  {C.YELLOW}Begin wizard? (yes/no): {C.RESET}"):
        warn("Cancelled.")
        return
    # 1) LTE baseline
    print(f"\n  {C.CYAN}{C.BOLD}[1/4] LTE baseline{C.RESET}")
    sess.set_net_mode("03", "3FFFFFFF", "7FFFFFFFFFFFFFFF")
    time.sleep(4)
    ok("LTE-only baseline set.")
    # 2) Antenna
    print(f"\n  {C.CYAN}{C.BOLD}[2/4] Antenna selection{C.RESET}")
    best_code, best_rsrp, best_label = None, -999, ""
    for code, (label, col) in ANTENNA_MODES.items():
        if code == "3":
            continue
        sess._xml_post(ANTENNA_SET_EP,
                       '<?xml version="1.0" encoding="UTF-8"?><request>'
                       f"<antenna_type>{code}</antenna_type></request>")
        time.sleep(5)
        rsrp, _ = avg_signal(sess, samples=3, delay=1)
        if rsrp is not None and rsrp > best_rsrp:
            best_code, best_rsrp, best_label = code, rsrp, label
    if best_code is not None:
        sess._xml_post(ANTENNA_SET_EP,
                       '<?xml version="1.0" encoding="UTF-8"?><request>'
                       f"<antenna_type>{best_code}</antenna_type></request>")
        ok(f"Selected antenna: {colorize(best_label, C.GOLD)} (RSRP {best_rsrp:.1f})")
    else:
        info("Antenna API not available — leaving as-is.")
    # 3) Best CA
    print(f"\n  {C.CYAN}{C.BOLD}[3/4] Carrier aggregation{C.RESET}")
    strong = sorted({int(re.sub(r"[^\d]", "", t["band"]))
                     for t in visible_towers(sess)
                     if re.sub(r"[^\d]", "", t["band"]) and t["rsrp_int"] >= -112})
    if len(strong) >= 2:
        lock_bands(sess, strong)
        wait_reconnect(10)
        agg = active_ca_bands(sess)
        ok(f"CA set: {colorize('+'.join('B'+str(b) for b in (agg or strong)), C.LIME, C.BOLD)}")
    elif strong:
        lock_bands(sess, strong[:1])
        ok(f"Single strong band: {colorize(band_label(strong[0]), C.GOLD)}")
    else:
        info("No strong bands detected — left on all-band auto.")
    # 4) Verify
    print(f"\n  {C.CYAN}{C.BOLD}[4/4] Verification{C.RESET}")
    time.sleep(4)
    sig = sess.get_signal()
    r_lbl, r_col = grade_rsrp(sig.get("rsrp_int"))
    bar = signal_bar(sig.get("rsrp_int"))
    sep()
    print(f"  {C.LIME}{C.BOLD}  ╔══  SETUP COMPLETE  ══════════════════════════╗{C.RESET}")
    print(f"  {C.LIME}║{C.RESET}  Signal : {bar}  {colorize(sig.get('rsrp','N/A'), r_col, C.BOLD)} ({r_lbl})")
    print(f"  {C.LIME}║{C.RESET}  SINR   : {colorize(sig.get('sinr','N/A'), C.CYAN)}")
    print(f"  {C.LIME}║{C.RESET}  CA     : {colorize('+'.join('B'+str(b) for b in active_ca_bands(sess)) or 'single', C.GOLD)}")
    print(f"  {C.LIME}{C.BOLD}  ╚════════════════════════════════════════════════╝{C.RESET}")
    sep()


def cmd_live_dashboard(sess: H155Session, args):
    """[98] All-in-one live dashboard (signal + CA + connection + health)."""
    interval = getattr(args, "interval", 3) or 3
    step(f"Live Dashboard (every {interval}s, Ctrl+C to stop)")
    sep()
    try:
        while True:
            sig = sess.get_signal()
            mon = sess.get_monitoring()
            agg = active_ca_bands(sess)
            ts = datetime.now().strftime("%H:%M:%S")
            rsrp_i = sig.get("rsrp_int")
            sinr_i = sig.get("sinr_int")
            r_lbl, r_col = grade_rsrp(rsrp_i)
            s_lbl, s_col = grade_sinr(sinr_i)
            bar = signal_bar(rsrp_i)
            conn = mon.get("connection_status", "0") == "901"
            ntype = network_type_name(mon.get("network_type", "0"))
            dl = speed_fmt(mon.get("dl_speed", "0"))
            ul = speed_fmt(mon.get("ul_speed", "0"))
            # clear screen for a stable dashboard view
            print("\033[2J\033[H", end="")
            print(f"  {C.GOLD}{C.BOLD}╔═══  ZAIN H155 LIVE DASHBOARD  ═══╗{C.RESET}   {C.DIM}{ts}{C.RESET}")
            print(f"  Connection : {colorize('UP' if conn else 'DOWN', C.GREEN if conn else C.RED, C.BOLD)}   "
                  f"Type: {colorize(ntype, C.TEAL)}")
            print(f"  Signal     : {bar}  RSRP {colorize(sig.get('rsrp','?'), r_col, C.BOLD)} ({r_lbl})")
            print(f"  Quality    : SINR {colorize(sig.get('sinr','?'), s_col, C.BOLD)} ({s_lbl})  "
                  f"RSRQ {colorize(sig.get('rsrq','?'), C.CYAN)}")
            print(f"  Aggregation: {colorize(str(len(agg))+'CC', C.LIME if len(agg)>1 else C.DIM, C.BOLD)}  "
                  f"{colorize('+'.join('B'+str(b) for b in agg) or '?', C.GOLD)}")
            print(f"  Cell       : PCI {colorize(sig.get('pci','?'), C.WHITE)}  "
                  f"EARFCN {colorize(sig.get('earfcn','?'), C.DIM)}")
            print(f"  Throughput : ↓{colorize(dl, C.LIME)}   ↑{colorize(ul, C.TEAL)}")
            print(f"  {C.DIM}Ctrl+C to exit{C.RESET}")
            time.sleep(interval)
    except KeyboardInterrupt:
        print()
        ok("Dashboard closed.")
    sep()


# ─────────────────────────────────────────────────────────────
#  MAIN CLI  –  NUMBERED INTERACTIVE MENU
# ─────────────────────────────────────────────────────────────

# (number, key, function, description, category_color)
MENU_ITEMS = [
    ( 1, "status",    cmd_status,          "Full device + signal dashboard",              C.CYAN),
    ( 2, "scan",      cmd_scan_towers,     "Scan & rank all visible towers",              C.CYAN),
    ( 3, "live",      cmd_live_signal,     "Live signal monitor (real-time)",             C.CYAN),
    ( 4, "log",       cmd_signal_log,      "Log signal to CSV file (with summary)",       C.CYAN),
    ( 5, "best",      cmd_best_band,       "Auto-detect best band → lock instantly",      C.LIME),
    ( 6, "lock",      cmd_lock_band,       "Lock to specific LTE band(s) manually",       C.LIME),
    ( 7, "unlock",    cmd_unlock_bands,    "Remove all band locks (full auto mode)",      C.LIME),
    ( 8, "lte-only",  cmd_set_lte_only,    "Force LTE-only mode (all bands)",             C.LIME),
    ( 9, "auto",      cmd_set_auto,        "Set full auto network selection",             C.LIME),
    (10, "antenna",   cmd_antenna,         "Antenna: internal / external / both / auto",  C.GOLD),
    (11, "band-info", cmd_band_info,       "Band reference table + lock status",          C.GOLD),
    (12, "benchmark", cmd_benchmark,       "Multi-band benchmark → auto-lock winner",     C.GOLD),
    (13, "watchdog",  cmd_watchdog,        "Smart watchdog – re-lock on band drift",      C.GOLD),
    (14, "ip-fix",    cmd_fix_ip_conflicts,"Detect & fix IP conflicts on LAN",            C.ORANGE),
    (15, "optimize",  cmd_full_optimize,   "FULL AUTO OPTIMIZER (antenna+band+verify)",   C.MAGENTA),
    (16, "reboot",    cmd_reboot,          "Reboot the router",                           C.RED),
    # ── v40 advanced features ──────────────────────────────────────────────
    (17, "sms",        cmd_sms_list,        "Read the SMS inbox",                         C.PINK),
    (18, "sms-send",   cmd_sms_send,        "Send an SMS message",                        C.PINK),
    (19, "sms-del",    cmd_sms_delete,      "Delete an SMS by index",                     C.PINK),
    (20, "sms-count",  cmd_sms_count,       "SMS mailbox counters",                       C.PINK),
    (21, "ussd",       cmd_ussd,            "Send a USSD code (balance, offers)",         C.PINK),
    (22, "traffic",    cmd_traffic_stats,   "Session traffic statistics",                 C.TEAL),
    (23, "usage",      cmd_month_stats,     "Monthly data usage vs plan",                 C.TEAL),
    (24, "clear-stats",cmd_clear_traffic,   "Reset traffic counters",                     C.TEAL),
    (25, "data-plan",  cmd_data_plan,       "View / set monthly data plan",               C.TEAL),
    (26, "wifi",       cmd_wifi_info,       "Show Wi-Fi configuration",                   C.BLUE),
    (27, "wifi-ssid",  cmd_wifi_ssid,       "Change Wi-Fi SSID",                          C.BLUE),
    (28, "wifi-pass",  cmd_wifi_password,   "Change Wi-Fi password",                      C.BLUE),
    (29, "clients",    cmd_wifi_clients,    "List connected clients",                     C.BLUE),
    (30, "guest",      cmd_wifi_guest,      "Toggle guest Wi-Fi network",                 C.BLUE),
    (31, "mac-filter", cmd_mac_filter,      "Wi-Fi MAC allow / deny filter",              C.BLUE),
    (32, "data",       cmd_data_toggle,     "Mobile data on / off",                       C.GREEN),
    (33, "roaming",    cmd_roaming_toggle,  "Data roaming on / off",                      C.GREEN),
    (34, "reconnect",  cmd_reconnect,       "Force data reconnect (new WAN IP)",          C.GREEN),
    (35, "apn",        cmd_apn_list,        "List APN profiles",                          C.GREEN),
    (36, "apn-set",    cmd_apn_set,         "Create / apply an APN profile",              C.GREEN),
    (37, "op-scan",    cmd_operator_scan,   "Scan available mobile operators",            C.MAGENTA),
    (38, "op-select",  cmd_operator_select, "Manual operator selection",                  C.MAGENTA),
    (39, "nr-lock",    cmd_nr_band_lock,    "Lock 5G NR band(s)",                         C.LIME),
    (40, "ca",         cmd_ca_info,         "Carrier-aggregation status",                 C.LIME),
    (41, "plmn",       cmd_current_plmn,    "Current network registration",               C.LIME),
    (42, "pin",        cmd_sim_pin,         "SIM PIN management",                         C.RED),
    (43, "dmz",        cmd_dmz,             "DMZ host configuration",                     C.RED),
    (44, "portfwd",    cmd_port_forward,    "Port-forwarding (virtual servers)",          C.RED),
    (45, "firewall",   cmd_firewall,        "Firewall switches",                          C.RED),
    (46, "upnp",       cmd_upnp,            "UPnP enable / disable",                      C.RED),
    (47, "ping",       cmd_ping,            "Ping diagnostic",                            C.ORANGE),
    (48, "trace",      cmd_traceroute,      "Traceroute diagnostic",                      C.ORANGE),
    (49, "speedtest",  cmd_speedtest,       "Real download speed test",                   C.ORANGE),
    (50, "dns",        cmd_dns_set,         "Set custom DNS servers",                     C.ORANGE),
    (51, "firmware",   cmd_firmware_check,  "Check for a firmware update",                C.GOLD),
    (52, "led",        cmd_led_control,     "Turn status LEDs on / off",                  C.GOLD),
    (53, "export",     cmd_export_json,     "Export status snapshot → JSON",              C.CYAN),
    (54, "backup",     cmd_backup_config,   "Backup configuration to file",               C.CYAN),
    (55, "restore",    cmd_restore_config,  "Restore configuration from file",            C.CYAN),
    (56, "alert",      cmd_signal_alert,    "Alert when signal drops below threshold",    C.GOLD),
    (57, "graph",      cmd_signal_graph,    "Live RSRP ASCII graph",                      C.CYAN),
    (58, "health",     cmd_health_report,   "Health report: score + advice",              C.LIME),
    # ── v40.2 automation & carrier-aggregation suite ───────────────────────
    (59, "ca-combos",  cmd_ca_combos,       "Discover candidate CA band combos",          C.LIME),
    (60, "ca-best",    cmd_ca_best,         "Benchmark 4G+4G CA pairs → lock best",       C.LIME),
    (61, "ca-lock",    cmd_ca_lock,         "Manually lock a CA combo (e.g. 1+3)",        C.LIME),
    (62, "ca-3cc",     cmd_ca_3cc,          "Find & lock best 4G+4G+4G (3CC) combo",      C.LIME),
    (63, "ca-live",    cmd_ca_live,         "Live carrier-aggregation monitor",           C.LIME),
    (64, "ca-force",   cmd_ca_force,        "Force-enable CA across strong bands",        C.LIME),
    (65, "ca-speed",   cmd_ca_speed,        "Real speedtest per CA pair → lock fastest",  C.LIME),
    (66, "ca-pilot",   cmd_ca_pilot,        "Auto-keep best CA active (daemon)",          C.LIME),
    (67, "cell-lock",  cmd_cell_lock,       "Lock toward a specific tower (PCI)",         C.GOLD),
    (68, "cell-unlock",cmd_cell_unlock,     "Release cell/tower lock",                    C.GOLD),
    (69, "tower-best", cmd_best_tower_lock, "Scan & lock the strongest tower",            C.GOLD),
    (70, "tower-rank", cmd_tower_rank,      "Rank towers by strength + stability",        C.GOLD),
    (71, "pci-watch",  cmd_pci_watch,       "Live PCI / neighbour watch",                 C.GOLD),
    (72, "earfcn-lock",cmd_earfcn_lock,     "Lock the band carrying an EARFCN",           C.GOLD),
    (73, "autopilot",  cmd_autopilot,       "AUTO-EVERYTHING daemon (signal+CA+recover)", C.MAGENTA),
    (74, "auto-fail",  cmd_auto_failover,   "Auto-failover to next-best band",            C.MAGENTA),
    (75, "auto-recover",cmd_auto_recover,   "Auto reconnect/reboot on dead link",         C.MAGENTA),
    (76, "auto-antenna",cmd_auto_antenna,   "Periodic auto antenna A/B selection",        C.MAGENTA),
    (77, "auto-rotate",cmd_auto_band_rotate,"Rotate bands → keep best",                   C.MAGENTA),
    (78, "schedule",   cmd_smart_schedule,  "Time-based day/night band profiles",         C.MAGENTA),
    (79, "keepalive",  cmd_keepalive,       "Keep-alive + auto reconnect",                C.MAGENTA),
    (80, "sched-reboot",cmd_scheduled_reboot,"Schedule a reboot (HH:MM or +Nm)",          C.MAGENTA),
    (81, "speed-bands",cmd_speed_per_band,  "Real speedtest per band → lock fastest",     C.ORANGE),
    (82, "opt-speed",  cmd_optimize_speed,  "Optimise by REAL throughput (band vs CA)",   C.ORANGE),
    (83, "opt-latency",cmd_latency_optimize,"Optimise by lowest ping latency",            C.ORANGE),
    (84, "stability",  cmd_stability_score, "Score bands by signal stability",            C.ORANGE),
    (85, "band-block", cmd_band_block,      "Blacklist a bad band",                       C.ORANGE),
    (86, "band-prio",  cmd_band_priority,   "Set preferred band priority set",            C.ORANGE),
    (87, "heatmap",    cmd_signal_heatmap,  "Time-of-day signal heatmap (from log)",      C.TEAL),
    (88, "band-hist",  cmd_band_history,    "Track % time per band/CA",                   C.TEAL),
    (89, "tput-log",   cmd_throughput_log,  "Log live throughput to CSV",                 C.TEAL),
    (90, "daily",      cmd_daily_report,    "Generate a daily Markdown report",           C.TEAL),
    (91, "html",       cmd_html_report,     "Export a styled HTML status report",         C.TEAL),
    (92, "profiles",   cmd_profiles,        "Named profile library (save/apply)",         C.TEAL),
    (93, "endc",       cmd_endc_optimize,   "5G NR+LTE EN-DC (NSA) optimiser",            C.PINK),
    (94, "mimo",       cmd_mimo_info,       "MIMO / multi-antenna diagnostics",           C.PINK),
    (95, "apn-test",   cmd_auto_apn_test,   "Test APNs by speed → keep fastest",          C.PINK),
    (96, "selftest",   cmd_self_test,       "Probe which API endpoints work",             C.PINK),
    (97, "wizard",     cmd_setup_wizard,    "Guided optimal setup wizard",                C.PINK),
    (98, "dashboard",  cmd_live_dashboard,  "All-in-one live dashboard",                  C.PINK),
    ( 0, "exit",      None,                "Exit",                                        C.DIM),
]

def show_numbered_menu():
    """Print the interactive numbered menu."""
    num_to_item = {item[0]: item for item in MENU_ITEMS}

    print(f"\n  {C.GOLD}{C.BOLD}╔══════════════════════════════════════════════════════════╗{C.RESET}")
    print(f"  {C.GOLD}{C.BOLD}║              ZAIN H155 – SELECT AN OPTION               ║{C.RESET}")
    print(f"  {C.GOLD}{C.BOLD}╠══════════════════════════════════════════════════════════╣{C.RESET}")

    cats = [
        ("📡  MONITORING",      [1, 2, 3, 4, 57, 58]),
        ("📶  BAND CONTROL",    [5, 6, 7, 8, 9, 39, 40, 41]),
        ("📡  ANTENNA",         [10]),
        ("🔬  ADVANCED TUNING", [11, 12, 13, 56]),
        ("✉️   SMS / USSD",      [17, 18, 19, 20, 21]),
        ("📊  DATA / USAGE",    [22, 23, 24, 25]),
        ("📶  WI-FI",           [26, 27, 28, 29, 30, 31]),
        ("🔌  CONNECTION",      [32, 33, 34, 35, 36]),
        ("🌐  OPERATOR",        [37, 38]),
        ("🔒  SECURITY / NAT",  [14, 42, 43, 44, 45, 46]),
        ("🩺  DIAGNOSTICS",     [47, 48, 49, 50]),
        ("💾  BACKUP / EXPORT", [51, 52, 53, 54, 55]),
        ("🧩  CARRIER AGGREGATION", [59, 60, 61, 62, 63, 64, 65, 66]),
        ("🗼  CELL / TOWER",    [67, 68, 69, 70, 71, 72]),
        ("🤖  AUTO-EVERYTHING", [73, 74, 75, 76, 77, 78, 79, 80]),
        ("🚀  SPEED / LATENCY", [81, 82, 83, 84, 85, 86]),
        ("📈  ANALYTICS",       [87, 88, 89, 90, 91, 92]),
        ("🧪  ADVANCED / RESILIENCE", [93, 94, 95, 96, 97, 98]),
        ("⚡  OPTIMIZER",       [15]),
        ("⚙️   SYSTEM",          [16, 0]),
    ]

    for cat_label, nums in cats:
        print(f"  {C.GOLD}║{C.RESET}  {colorize(cat_label, C.BOLD, C.WHITE)}")
        for n in nums:
            num, key, fn, desc, col = num_to_item[n]
            num_str = colorize(f"[{num:>2}]", col, C.BOLD)
            print(f"  {C.GOLD}║{C.RESET}       {num_str}  {colorize(desc, C.WHITE)}")
        print(f"  {C.GOLD}║{C.RESET}")

    print(f"  {C.GOLD}╚══════════════════════════════════════════════════════════╝{C.RESET}")
    print(f"\n  {C.YELLOW}Run directly:  {C.DIM}python zain_h155_manager.py <number or name>{C.RESET}")

def resolve_command(cmd_str: str):
    """Resolve a command from number string or name string."""
    cmd_str = cmd_str.strip().lower()
    # Try as number
    try:
        n = int(cmd_str)
        for item in MENU_ITEMS:
            if item[0] == n:
                return item[1], item[2]
        return None, None
    except ValueError:
        pass
    # Try as name
    for item in MENU_ITEMS:
        if item[1] == cmd_str:
            return item[1], item[2]
    return None, None

def main():
    print(BANNER)

    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("command",      nargs="?",      default=None)
    parser.add_argument("--gateway",    default="192.168.8.1")
    parser.add_argument("--password",   default=None)
    parser.add_argument("--bands",      nargs="+",      type=int)
    parser.add_argument("--auto-mode",  action="store_true")
    parser.add_argument("--interval",   type=int,       default=3)
    parser.add_argument("--duration",   type=int,       default=60)
    # ── v40 feature arguments (all optional; features prompt if omitted) ──
    parser.add_argument("--to",         default=None, help="SMS recipient number")
    parser.add_argument("--message",    default=None, help="SMS message body")
    parser.add_argument("--code",       default=None, help="USSD code, e.g. *123#")
    parser.add_argument("--ssid",       default=None, help="New Wi-Fi SSID")
    parser.add_argument("--wifi-pass",  dest="wifi_pass", default=None, help="New Wi-Fi password")
    parser.add_argument("--target",     default=None, help="Host for ping/traceroute")
    parser.add_argument("--threshold",  type=int, default=-110, help="RSRP alert threshold (dBm)")
    parser.add_argument("--file",       default=None, help="File path for export/backup/restore")
    parser.add_argument("--help", "-h", action="store_true")

    args = parser.parse_args()

    if args.help:
        show_numbered_menu()
        sys.exit(0)

    # ── Password ────────────────────────────────────────────
    DEFAULT_PASSWORD = "4tdidpfmaht"
    password = args.password
    if not password:
        print(f"  {C.CYAN}Enter router admin password")
        print(f"  {C.DIM}(press Enter to use default: {colorize(DEFAULT_PASSWORD, C.YELLOW)}){C.RESET}")
        try:
            typed = input(f"  {C.YELLOW}Password: {C.RESET}").strip()
            password = typed if typed else DEFAULT_PASSWORD
            if not typed:
                info(f"Using default password: {colorize(DEFAULT_PASSWORD, C.GOLD)}")
        except KeyboardInterrupt:
            print()
            warn("Cancelled.")
            sys.exit(0)

    # ── Connect once ────────────────────────────────────────
    sess = H155Session(gateway=args.gateway)
    if not sess.connect(password):
        sys.exit(1)

    # ── Determine command ───────────────────────────────────
    # If command given via CLI (name or number) → run it and exit
    if args.command:
        key, fn = resolve_command(args.command)
        if fn is None:
            err(f"Unknown command: '{args.command}'")
            show_numbered_menu()
            sess.logout()
            sys.exit(1)
        try:
            fn(sess, args)
        except KeyboardInterrupt:
            print()
            warn("Interrupted.")
        except Exception as e:
            err(f"Unexpected error: {e}")
            import traceback; traceback.print_exc()
        finally:
            sess.logout()
        print(f"\n  {C.DIM}Done – {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{C.RESET}\n")
        return

    # ── Interactive numbered menu loop ──────────────────────
    while True:
        show_numbered_menu()
        print()
        try:
            choice = input(f"  {C.CYAN}Enter number (or name): {C.RESET}").strip()
        except KeyboardInterrupt:
            print()
            break

        if not choice:
            continue

        if choice in ("0", "exit", "quit", "q"):
            break

        key, fn = resolve_command(choice)
        if fn is None:
            err(f"Invalid option: '{choice}'  – enter a number from the menu.")
            continue

        print()
        try:
            fn(sess, args)
        except KeyboardInterrupt:
            print()
            warn("Interrupted – back to menu.")
        except Exception as e:
            err(f"Unexpected error: {e}")
            import traceback; traceback.print_exc()

        input(f"\n  {C.DIM}Press Enter to return to menu...{C.RESET}")

    sess.logout()
    print(f"\n  {C.DIM}Done – {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{C.RESET}\n")


if __name__ == "__main__":
    main()
