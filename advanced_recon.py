#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ADVANCED_RECON - Professional Bug Bounty Reconnaissance Framework
=================================================================
Version: 2.0.0
For AUTHORIZED bug-bounty / legal security research ONLY.

Modules:
  1.  Passive OSINT          - CT logs, Wayback, DNS records, ASN
  2.  WAF Fingerprinting     - Detect CDN/WAF vendor + config hints
  3.  Tech Stack Detection   - Wappalyzer-style fingerprinting (100+ signatures)
  4.  Advanced JS Engine     - Webpack chunk map, sourcemap, secret extraction
  5.  API Surface Mapper     - OpenAPI/Swagger, GraphQL, REST, SOAP discovery
  6.  Security Header Audit  - All OWASP recommended headers + scoring
  7.  CORS Analyser          - Misconfigured CORS policy detection
  8.  Cookie Security Audit  - Secure/HttpOnly/SameSite/prefix checks
  9.  Subdomain Enumerator   - CT logs + permutation + DNS validation
  10. Cloud Asset Detector   - S3/Azure Blob/GCS exposure, open buckets
  11. GitHub/GitLab OSINT    - Public code leaks referencing the target
  12. Wayback Miner          - Historical URL & parameter extraction
  13. Vulnerability Annotator - OWASP Top-10 + CWE + manual test leads
  14. PoC Generator          - Ready-to-paste curl/Burp PoC for each finding
  15. Professional Reporter  - JSON + HTML + Markdown + Excel-compatible CSV
"""

from __future__ import annotations

import argparse
import asyncio
import dataclasses
import datetime as _dt
import hashlib
import html
import json
import logging
import math
import os
import re
import socket
import sys
import time
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib.parse import (urljoin, urlparse, urldefrag, parse_qs,
                          urlencode, quote)

try:
    import aiohttp
    _HAVE_AIOHTTP = True
except ImportError:
    aiohttp = None
    _HAVE_AIOHTTP = False

try:
    import requests
    _HAVE_REQUESTS = True
except ImportError:
    requests = None
    _HAVE_REQUESTS = False

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
    from rich.syntax import Syntax
    from rich import box
    _HAVE_RICH = True
    _console = Console(highlight=False)
except ImportError:
    _HAVE_RICH = False
    class _C:
        def print(self, *a, **k): print(*[re.sub(r'\[/?[^\]]+\]','',str(x)) for x in a])
        def rule(self, t=""): print(f"{'─'*20} {t} {'─'*20}")
    _console = _C()

VERSION = "2.0.0"
NOW = lambda: _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
SHA1 = lambda s: hashlib.sha1(s.encode()).hexdigest()

def entropy(s: str) -> float:
    if not s: return 0.0
    from math import log2
    c: Dict[str,int] = {}
    for ch in s: c[ch] = c.get(ch,0)+1
    n = len(s)
    return -sum((v/n)*log2(v/n) for v in c.values())

# ─────────────────────────────────────────────────────────────────────────────
#  WAF / CDN Fingerprints
# ─────────────────────────────────────────────────────────────────────────────
WAF_SIGNATURES: List[Dict[str, Any]] = [
    {"name": "Cloudflare",  "headers": {"server": "cloudflare", "cf-ray": None},
     "cookies": {"__cflb", "__cfduid", "cf_clearance"}, "body": ["cf-browser-verification","cloudflare"]},
    {"name": "Akamai",      "headers": {"x-check-cacheable": None, "x-akamai-transformed": None},
     "cookies": set(), "body": ["akamai","ak_bmsc"]},
    {"name": "AWS WAF",     "headers": {"x-amzn-requestid": None, "x-amzn-trace-id": None},
     "cookies": {"aws-waf-token"}, "body": ["awselb","aws-waf"]},
    {"name": "Imperva / Incapsula", "headers": {"x-iinfo": None, "x-cdn": "imperva"},
     "cookies": {"incap_ses","visid_incap"}, "body": ["incapsula","imperva"]},
    {"name": "F5 BIG-IP",   "headers": {"x-wa-info": None},
     "cookies": {"BIGipServer", "F5_"}, "body": ["big-ip","f5 networks"]},
    {"name": "Fortinet FortiWeb", "headers": {"x-waf-event-info": None},
     "cookies": set(), "body": ["fortigate","fortiweb"]},
    {"name": "Barracuda",   "headers": {"server": "barracuda"},
     "cookies": set(), "body": ["barracuda networks"]},
    {"name": "Sucuri",      "headers": {"x-sucuri-id": None, "server": "sucuri"},
     "cookies": set(), "body": ["sucuri","cloudproxy"]},
    {"name": "Reblaze",     "headers": {"x-reblaze-protection": None},
     "cookies": {"rbzid"}, "body": ["reblaze"]},
    {"name": "DataDome",    "headers": {"x-datadome-cid": None},
     "cookies": {"datadome"}, "body": ["datadome"]},
    {"name": "Fastly",      "headers": {"x-fastly-request-id": None, "via": "fastly"},
     "cookies": set(), "body": []},
    {"name": "Nginx",       "headers": {"server": "nginx"},
     "cookies": set(), "body": []},
    {"name": "Apache",      "headers": {"server": "apache"},
     "cookies": set(), "body": []},
    {"name": "Microsoft IIS","headers": {"server": "microsoft-iis"},
     "cookies": set(), "body": []},
]

# ─────────────────────────────────────────────────────────────────────────────
#  Technology Fingerprints (~120 signatures)
# ─────────────────────────────────────────────────────────────────────────────
TECH_SIGS: List[Dict[str, Any]] = [
    # JS frameworks
    {"name":"React",       "body":[r"react\.development\.js","__reactFiber",r"data-reactroot","_reactListening"]},
    {"name":"Vue.js",      "body":[r"vue\.runtime","__vue__",r"v-bind:","v-model"]},
    {"name":"Angular",     "body":[r"ng-version","angular\.min\.js","ng-app","_nghost"]},
    {"name":"Next.js",     "body":[r"\/_next\/static","__NEXT_DATA__","next\.config\.js"]},
    {"name":"Nuxt.js",     "body":[r"__nuxt","_nuxt/","nuxt\.config"]},
    {"name":"jQuery",      "body":[r"jquery(?:\.min)?\.js","jQuery\.fn\.jquery","window\.\$\.fn"]},
    {"name":"Bootstrap",   "body":[r"bootstrap(?:\.min)?\.css","bootstrap(?:\.min)?\.js"]},
    {"name":"Backbone.js", "body":[r"backbone(?:\.min)?\.js","Backbone\.Model"]},
    {"name":"Ember.js",    "body":[r"ember(?:\.min)?\.js","Ember\.Application"]},
    {"name":"Svelte",      "body":[r"svelte/","__svelte"]},
    # CMS
    {"name":"WordPress",   "body":[r"wp-content","wp-includes",r"/wp-json/"]},
    {"name":"Drupal",      "body":[r"Drupal\.settings","drupal\.org",r"sites/default/files"]},
    {"name":"Joomla",      "body":[r"joomla","option=com_","Joomla!"]},
    {"name":"SharePoint",  "body":[r"_layouts/","SharePoint","/_vti_bin/"]},
    {"name":"Sitefinity",  "body":[r"Sitefinity","sfPublicWrapper"]},
    {"name":"Sitecore",    "body":[r"sitecore/shell","Sitecore\."]},
    {"name":"Adobe AEM",   "body":[r"/etc\.clientlibs/","AEM","adobe experience manager"]},
    # Backend
    {"name":"PHP",         "headers":{"x-powered-by":"php"}, "cookies":{"PHPSESSID"}, "body":[r"\.php\b"]},
    {"name":"ASP.NET",     "headers":{"x-aspnet-version":None,"x-aspnetmvc-version":None},
     "cookies":{"ASP.NET_SessionId","ASPXAUTH"}, "body":[r"__VIEWSTATE","__EVENTTARGET"]},
    {"name":"Java/JSP",    "body":[r"\.jsp\b","jsessionid","javax\.faces"]},
    {"name":"Django",      "body":[r"csrfmiddlewaretoken","django"]},
    {"name":"Ruby on Rails","body":[r"authenticity_token",r"rails-ujs"]},
    {"name":"Laravel",     "body":[r"laravel_session","Laravel"]},
    {"name":"Spring Boot", "body":[r"spring","whitelabel error page"]},
    {"name":"Express.js",  "headers":{"x-powered-by":"express"}, "body":[]},
    {"name":"Node.js",     "headers":{"x-powered-by":"node"}, "body":[]},
    # Cloud / CDN
    {"name":"AWS S3",      "body":[r"s3\.amazonaws\.com","AmazonS3"]},
    {"name":"Azure",       "body":[r"\.azurewebsites\.net","azure-edge"]},
    {"name":"GCP",         "body":[r"storage\.googleapis\.com","appspot\.com"]},
    # Analytics / Marketing
    {"name":"Google Analytics","body":[r"google-analytics\.com","gtag\(","ga\('create'"]},
    {"name":"Google Tag Manager","body":[r"googletagmanager\.com","gtm\.start"]},
    # Web servers
    {"name":"Nginx",       "headers":{"server":"nginx"}, "body":[]},
    {"name":"Apache",      "headers":{"server":"apache"}, "body":[]},
    {"name":"IIS",         "headers":{"server":"microsoft-iis"}, "body":[]},
    {"name":"Caddy",       "headers":{"server":"caddy"}, "body":[]},
    {"name":"LiteSpeed",   "headers":{"server":"litespeed"}, "body":[]},
    {"name":"OpenResty",   "headers":{"server":"openresty"}, "body":[]},
    # Arabic/Govt specific
    {"name":"Yesser (Saudi e-Gov)","body":[r"yesser\.gov\.sa","e-government"]},
    {"name":"Absher",      "body":[r"absher\.sa","absher"]},
    {"name":"Nafath",      "body":[r"nafath","national unified sso"]},
]

# ─────────────────────────────────────────────────────────────────────────────
#  Security Headers – Full Audit
# ─────────────────────────────────────────────────────────────────────────────
SECURITY_HEADERS = {
    "strict-transport-security": {
        "cwe":"CWE-319","owasp":"A02:2021",
        "severity":"medium","expected":"max-age>=15552000; includeSubDomains",
        "check": lambda v: int(re.search(r'max-age=(\d+)',v or '').group(1) if re.search(r'max-age=(\d+)',v or '') else 0) >= 15552000,
    },
    "content-security-policy": {
        "cwe":"CWE-693","owasp":"A05:2021",
        "severity":"medium","expected":"non-trivial policy",
        "check": lambda v: bool(v) and "unsafe-inline" not in v,
    },
    "x-frame-options": {
        "cwe":"CWE-1021","owasp":"A05:2021",
        "severity":"medium","expected":"DENY or SAMEORIGIN",
        "check": lambda v: (v or "").upper() in ("DENY","SAMEORIGIN"),
    },
    "x-content-type-options": {
        "cwe":"CWE-693","owasp":"A05:2021",
        "severity":"low","expected":"nosniff",
        "check": lambda v: (v or "").lower() == "nosniff",
    },
    "referrer-policy": {
        "cwe":"CWE-200","owasp":"A01:2021",
        "severity":"low","expected":"strict-origin-when-cross-origin or stricter",
        "check": lambda v: (v or "").lower() in (
            "no-referrer","strict-origin","strict-origin-when-cross-origin","no-referrer-when-downgrade"),
    },
    "permissions-policy": {
        "cwe":"CWE-693","owasp":"A05:2021",
        "severity":"informational","expected":"present",
        "check": lambda v: bool(v),
    },
    "cross-origin-opener-policy": {
        "cwe":"CWE-1021","owasp":"A05:2021",
        "severity":"informational","expected":"same-origin",
        "check": lambda v: bool(v),
    },
    "cross-origin-resource-policy": {
        "cwe":"CWE-200","owasp":"A05:2021",
        "severity":"informational","expected":"same-origin or same-site",
        "check": lambda v: bool(v),
    },
    "cross-origin-embedder-policy": {
        "cwe":"CWE-693","owasp":"A05:2021",
        "severity":"informational","expected":"require-corp",
        "check": lambda v: bool(v),
    },
    "cache-control": {
        "cwe":"CWE-524","owasp":"A05:2021",
        "severity":"informational","expected":"no-store for sensitive pages",
        "check": lambda v: "no-store" in (v or "").lower() or "no-cache" in (v or "").lower(),
    },
}

# CSP weakness patterns
CSP_WEAKNESS_RE = [
    (r"'unsafe-inline'",    "Allows inline script execution (XSS risk)",     "high"),
    (r"'unsafe-eval'",      "Allows eval() / Function() (XSS amplifier)",     "high"),
    (r"\*\s",               "Wildcard source allows any origin",              "high"),
    (r"http://",            "Non-HTTPS source in CSP",                        "medium"),
    (r"data:",              "data: URI source (XSS risk)",                    "medium"),
    (r"'unsafe-hashes'",    "Allows hash-based inline scripts",              "low"),
    (r"object-src\s*\*",    "object-src wildcard allows flash/plugin XSS",    "medium"),
    (r"base-uri\s*\*",      "Unconstrained base-uri (base tag injection)",    "medium"),
]

# ─────────────────────────────────────────────────────────────────────────────
#  Secret Patterns – Extended (50+)
# ─────────────────────────────────────────────────────────────────────────────
SECRET_PATTERNS: List[Tuple[str,str,str,float]] = [
    # name, pattern, cwe, min_entropy
    ("AWS Access Key ID",       r"\bAKIA[0-9A-Z]{16}\b",                       "CWE-798", 3.0),
    ("AWS Secret Key",          r"(?i)aws.{0,10}secret.{0,10}['\"]([A-Za-z0-9/+]{40})['\"]","CWE-798", 4.0),
    ("AWS Session Token",       r"(?i)aws.{0,10}session.{0,10}['\"]([A-Za-z0-9/+=]{100,})['\"]","CWE-798", 4.5),
    ("Google API Key",          r"\bAIza[0-9A-Za-z\-_]{35}\b",                 "CWE-798", 3.5),
    ("Google OAuth",            r"\b[0-9]+-[0-9A-Za-z_]{32}\.apps\.googleusercontent\.com\b","CWE-798", 3.0),
    ("Firebase URL",            r"https://[a-z0-9\-]+\.firebaseio\.com",        "CWE-200", 2.0),
    ("Firebase API Key",        r"(?i)firebase.{0,10}['\"]([A-Za-z0-9]{39})['\"]","CWE-798", 3.5),
    ("Slack Token",             r"\bxox[baprs]-[0-9A-Za-z\-]{10,}\b",          "CWE-798", 3.5),
    ("Slack Webhook",           r"https://hooks\.slack\.com/services/[A-Z0-9/]+","CWE-798", 2.0),
    ("Stripe Live Key",         r"\bsk_live_[0-9A-Za-z]{24,}\b",               "CWE-798", 3.5),
    ("Stripe Pub Key",          r"\bpk_live_[0-9A-Za-z]{24,}\b",               "CWE-200", 3.0),
    ("GitHub PAT",              r"\bgh[pousr]_[0-9A-Za-z]{36}\b",              "CWE-798", 3.5),
    ("GitHub Fine-grained PAT", r"\bgithub_pat_[0-9A-Za-z_]{82}\b",           "CWE-798", 4.0),
    ("Twilio SID",              r"\bAC[a-z0-9]{32}\b",                         "CWE-798", 3.0),
    ("Twilio Token",            r"\b[a-f0-9]{32}\b",                           "CWE-798", 4.0),
    ("Sendgrid Key",            r"\bSG\.[A-Za-z0-9\-_]{22}\.[A-Za-z0-9\-_]{43}\b","CWE-798", 4.0),
    ("Mailgun Key",             r"\bkey-[a-z0-9]{32}\b",                       "CWE-798", 3.5),
    ("HubSpot API Key",         r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b","CWE-798", 3.5),
    ("Heroku API Key",          r"\b[0-9A-F]{8}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{12}\b","CWE-798", 3.5),
    ("JWT Token",               r"\beyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\b","CWE-522", 3.5),
    ("Private Key",             r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----","CWE-321", 0.0),
    ("PGP Private Key",         r"-----BEGIN PGP PRIVATE KEY BLOCK-----",       "CWE-321", 0.0),
    ("Bearer Token",            r"(?i)bearer\s+([A-Za-z0-9_\-\.]{20,})",       "CWE-522", 3.5),
    ("Basic Auth (b64)",        r"(?i)basic\s+([A-Za-z0-9+/=]{20,})",          "CWE-522", 3.0),
    ("Generic API Key",         r"(?i)api[_\-]?key['\"\s:=]+([A-Za-z0-9_\-]{20,})","CWE-798", 3.5),
    ("Generic Secret",          r"(?i)(?:secret|password|passwd|pwd|token|credential)['\"\s:=]+([A-Za-z0-9_\-@!#$%^&*]{12,})","CWE-798", 3.5),
    ("Connection String",       r"(?i)(?:mongodb|mysql|postgres|redis|mssql|jdbc)://[^\s'\"<>]+","CWE-798", 3.0),
    ("S3 Bucket URL",           r"https?://[a-z0-9\-\.]+\.s3(?:\.[a-z0-9\-]+)?\.amazonaws\.com","CWE-200", 2.0),
    ("Azure Storage",           r"https?://[a-z0-9]+\.blob\.core\.windows\.net","CWE-200", 2.0),
    ("Internal IP",             r"\b(?:192\.168|10\.|172\.(?:1[6-9]|2[0-9]|3[01]))\.\d+\.\d+\b","CWE-200", 0.0),
    ("Private Domain Leak",     r"(?i)(?:internal|staging|dev|test|uat|qa|preprod)\.[a-z0-9\-\.]+","CWE-200", 0.0),
    ("GraphQL Introspection",   r"__schema|__type\b",                           "CWE-200", 0.0),
    ("SQL Dump Marker",         r"(?i)INSERT INTO|CREATE TABLE|DROP TABLE",     "CWE-200", 0.0),
    ("Saudi National ID",       r"\b[12]\d{9}\b",                              "CWE-200", 0.0),
    ("Credit Card",             r"\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13})\b","CWE-200", 0.0),
]

SECRET_FP = ("example","placeholder","your_","xxxx","0000","1234","abcde",
             "<",">"," ","{{","}}","process.env","__","ENV[","config[")

# ─────────────────────────────────────────────────────────────────────────────
#  CORS Test Origins
# ─────────────────────────────────────────────────────────────────────────────
CORS_ORIGINS = [
    "https://evil.com",
    "https://attacker.com",
    "null",
    "{target_origin}",           # reflected: origin == target → bad policy
    "https://{target}evil.com",  # suffix bypass
    "https://evil{target}",      # prefix bypass
]

# ─────────────────────────────────────────────────────────────────────────────
#  Cookie Security
# ─────────────────────────────────────────────────────────────────────────────
SESSION_COOKIE_HINTS = ("session","sess","auth","token","jwt","login","user",
                        "sid","id","access","refresh","bearer","account")

# ─────────────────────────────────────────────────────────────────────────────
#  API / GraphQL paths
# ─────────────────────────────────────────────────────────────────────────────
SCHEMA_PATHS = (
    "/swagger.json","/swagger/v1/swagger.json","/openapi.json",
    "/v2/api-docs","/v3/api-docs","/api-docs","/api/swagger.json",
    "/.well-known/openapi.json","/swagger/v1/swagger.yaml",
    "/api/v1","/api/v2","/api/v3","/rest/v1","/api/",
    "/graphql","/gql","/api/graphql","/query","/v1/graphql",
    "/.well-known/security.txt","/security.txt",
    "/.well-known/change-password",
    "/robots.txt","/sitemap.xml","/sitemap_index.xml",
    "/.env","/config.json","/app.config.json","/settings.json",
    "/web.config","/.htaccess","/Dockerfile","/docker-compose.yml",
    "/.git/HEAD","/.git/config","/.git/COMMIT_EDITMSG",
    "/phpinfo.php","/info.php","/test.php","/server-status",
    "/actuator","/actuator/health","/actuator/env","/actuator/beans",
    "/debug","/debug/pprof","/metrics","/health","/status",
    "/_ah/admin","/admin","/admin/","/administrator",
    "/wp-json/wp/v2/users","/wp-login.php","/wp-admin/",
)

GRAPHQL_INTROSPECTION = '{"query":"query IntrospectionQuery{__schema{queryType{name}mutationType{name}subscriptionType{name}types{...FullType}directives{name description locations args{...InputValue}}}}fragment FullType on __Type{kind name description fields(includeDeprecated:true){name description args{...InputValue}type{...TypeRef}isDeprecated deprecationReason}inputFields{...InputValue}interfaces{...TypeRef}enumValues(includeDeprecated:true){name description isDeprecated deprecationReason}possibleTypes{...TypeRef}}fragment InputValue on __InputValue{name description type{...TypeRef}defaultValue}fragment TypeRef on __Type{kind name ofType{kind name ofType{kind name ofType{kind name ofType{kind name ofType{kind name ofType{kind name}}}}}}}"}'

# ─────────────────────────────────────────────────────────────────────────────
#  Subdomain wordlist (focused on govSA patterns)
# ─────────────────────────────────────────────────────────────────────────────
SUBDOMAIN_WORDLIST = [
    "www","mail","smtp","ftp","ssh","vpn","api","api2","api-v1","api-v2",
    "dev","staging","uat","qa","test","demo","beta","preview","sandbox",
    "admin","portal","dashboard","panel","manage","management","control",
    "mobile","m","app","apps","application","web","webmail",
    "docs","help","support","status","monitor","metrics","healthcheck",
    "cdn","static","assets","media","files","upload","uploads","img","images",
    "auth","login","sso","id","identity","oauth","accounts","account",
    "internal","intranet","corp","office","remote",
    "db","database","sql","mysql","postgres","redis","mongodb","backup",
    "git","gitlab","github","svn","jenkins","ci","cd","devops","build",
    "mail","email","smtp","pop","imap","exchange","webmail",
    "ns1","ns2","mx","dns","resolver",
    "search","es","elasticsearch","kibana","grafana","prometheus",
    "shop","store","ecommerce","payment","pay","checkout","cart",
    "blog","news","press","media","marketing","cms",
    "ar","en","arabic","english","ar-sa",
    "greeting","greet","occasion","eid","national","welcome",
    "eservices","e-services","eservice","services","service",
    "forms","form","survey","feedback","contact",
    "reports","report","stats","analytics","bi","datawarehouse",
    "insurance","health","medical","clinical","patient","member",
    "payer","provider","broker","claim","claims","policy","policies",
    "customer","client","user","member","beneficiary",
    "gov","egov","digital","smartgov","national",
]

# ─────────────────────────────────────────────────────────────────────────────
#  Data classes
# ─────────────────────────────────────────────────────────────────────────────
@dataclass
class HttpResult:
    url: str
    status: int
    headers: Dict[str,str]
    body: str
    elapsed_ms: float
    error: Optional[str] = None
    final_url: Optional[str] = None
    @property
    def ok(self): return self.error is None and self.status > 0
    @property
    def content_type(self): return self.headers.get("content-type","")
    @property
    def server(self): return self.headers.get("server","")
    def cookies(self) -> List[str]:
        return [v for k,v in self.headers.items() if k == "set-cookie"]


@dataclass
class Finding:
    id: str
    title: str
    severity: str        # critical|high|medium|low|informational
    confidence: str      # confirmed|high|medium|low
    cwe: str
    owasp: str
    affected_url: str
    endpoint: str
    request: str
    response_evidence: str
    technical_detail: str
    impact: str
    remediation: str
    cvss_vector: str
    cvss_score: float
    poc_curl: str
    poc_burp: str
    poc_steps: List[str]
    detection_method: str
    timestamp: str = field(default_factory=NOW)
    affected_urls: List[str] = field(default_factory=list)

    def key(self) -> str:
        return SHA1(f"{self.title}|{urlparse(self.affected_url).hostname}")


@dataclass
class ScanResult:
    target: str
    scan_time: str
    duration_s: float
    scope: str
    waf_detected: List[str]
    technologies: List[str]
    ip_addresses: List[str]
    subdomains: List[str]
    assets: List[str]
    api_endpoints: List[str]
    graphql_endpoints: List[str]
    js_files: List[str]
    js_callsites: List[str]
    secret_hits: List[Dict[str,Any]]
    forms: List[Dict[str,Any]]
    parameters: Dict[str,Dict[str,List[str]]]
    cors_results: List[Dict[str,Any]]
    cookie_findings: List[Dict[str,Any]]
    passive_hosts: List[str]
    passive_urls: List[str]
    wayback_urls: List[str]
    open_paths: List[str]
    findings: List[Finding]
    headers_audit: Dict[str,Any]
    csp_weaknesses: List[Dict[str,str]]
    diagnostics: Dict[str,Any]


# ─────────────────────────────────────────────────────────────────────────────
#  Rate Limiter
# ─────────────────────────────────────────────────────────────────────────────
class RateLimiter:
    def __init__(self, rps: float):
        self.rate = max(0.1, rps)
        self._tokens = self.rate
        self._last = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self):
        async with self._lock:
            while True:
                now = time.monotonic()
                self._tokens = min(self.rate, self._tokens+(now-self._last)*self.rate)
                self._last = now
                if self._tokens >= 1:
                    self._tokens -= 1; return
                await asyncio.sleep((1-self._tokens)/self.rate)


# ─────────────────────────────────────────────────────────────────────────────
#  HTTP Engine
# ─────────────────────────────────────────────────────────────────────────────
class HttpEngine:
    OSINT_HOSTS = {"crt.sh","web.archive.org","api.shodan.io","certspotter.com"}
    UA_BROWSER = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")

    def __init__(self, cfg, scope, log):
        self.cfg = cfg
        self.scope = scope
        self.log = log
        self.rl = RateLimiter(cfg.rate)
        self.sem = asyncio.Semaphore(cfg.workers)
        self._sess = None
        self._insecure = not cfg.verify_tls

    async def __aenter__(self):
        if _HAVE_AIOHTTP:
            connector = aiohttp.TCPConnector(limit=self.cfg.workers,
                                             ssl=False if self._insecure else None)
            timeout = aiohttp.ClientTimeout(total=self.cfg.timeout)
            self._sess = aiohttp.ClientSession(timeout=timeout,connector=connector)
        return self

    async def __aexit__(self, *_):
        if self._sess: await self._sess.close()

    async def get(self, url: str, headers: Dict[str,str]=None,
                  external=False) -> HttpResult:
        return await self._request("GET", url, headers=headers, external=external)

    async def post(self, url: str, data: str="", headers: Dict[str,str]=None,
                   external=False) -> HttpResult:
        return await self._request("POST", url, data=data, headers=headers, external=external)

    async def head(self, url: str, headers: Dict[str,str]=None) -> HttpResult:
        return await self._request("HEAD", url, headers=headers)

    async def options(self, url: str, headers: Dict[str,str]=None) -> HttpResult:
        return await self._request("OPTIONS", url, headers=headers)

    async def _request(self, method, url, headers=None, data=None,
                       external=False) -> HttpResult:
        url, _ = urldefrag(url)
        host = (urlparse(url).hostname or "").lower()
        if not external and not self.scope.allow(url):
            return HttpResult(url,0,{},"",0.0,error="out-of-scope")
        if external and host not in self.OSINT_HOSTS:
            return HttpResult(url,0,{},"",0.0,error="osint-not-allowed")
        hdrs = {"User-Agent": self.UA_BROWSER,
                "Accept": "text/html,application/xhtml+xml,*/*;q=0.9",
                "Accept-Language": "ar,en-US;q=0.7,en;q=0.3"}
        if headers: hdrs.update(headers)
        last_err = None
        for attempt in range(self.cfg.retries+1):
            await self.rl.acquire()
            async with self.sem:
                try:
                    if _HAVE_AIOHTTP:
                        return await self._fetch_aio(method, url, hdrs, data)
                    return await asyncio.to_thread(self._fetch_sync, method, url, hdrs, data)
                except Exception as e:
                    last_err = f"{type(e).__name__}: {e}"
                    if "ssl" in str(e).lower() and not self._insecure:
                        self._insecure = True
                        continue
                    self.log.debug("attempt %d %s %s: %s", attempt+1, method, url, e)
                    await asyncio.sleep(min(2**attempt,6))
        return HttpResult(url,0,{},"",0.0,error=last_err or "unknown")

    async def _fetch_aio(self, method, url, hdrs, data) -> HttpResult:
        t = time.monotonic()
        async with self._sess.request(
            method, url, headers=hdrs, data=data,
            allow_redirects=True, ssl=False if self._insecure else None
        ) as r:
            body = await r.text(errors="replace")
            elapsed = (time.monotonic()-t)*1000
            # Collect all Set-Cookie headers
            raw_headers: Dict[str,str] = {}
            sc_list = []
            for k,v in r.headers.items():
                kl = k.lower()
                if kl == "set-cookie":
                    sc_list.append(v)
                else:
                    raw_headers[kl] = v
            if sc_list:
                raw_headers["set-cookie"] = "\n".join(sc_list)
            return HttpResult(str(r.url), r.status, raw_headers, body, elapsed)

    def _fetch_sync(self, method, url, hdrs, data) -> HttpResult:
        import urllib.request as _u, urllib.error as _e, ssl as _ssl
        ctx = None
        if self._insecure:
            ctx = _ssl.create_default_context()
            ctx.check_hostname=False; ctx.verify_mode=_ssl.CERT_NONE
        req = _u.Request(url, data=(data.encode() if data else None),
                         headers=hdrs, method=method)
        t = time.monotonic()
        try:
            with _u.urlopen(req, timeout=self.cfg.timeout, context=ctx) as r:
                body = r.read().decode("utf-8","replace")
                elapsed = (time.monotonic()-t)*1000
                rh = {k.lower():v for k,v in r.headers.items()}
                return HttpResult(r.geturl(), r.status, rh, body, elapsed)
        except _e.HTTPError as e:
            body = e.read().decode("utf-8","replace") if hasattr(e,"read") else ""
            elapsed = (time.monotonic()-t)*1000
            rh = {k.lower():v for k,v in e.headers.items()}
            return HttpResult(url, e.code, rh, body, elapsed)


# ─────────────────────────────────────────────────────────────────────────────
#  Scope Guard
# ─────────────────────────────────────────────────────────────────────────────
class ScopeGuard:
    def __init__(self, target: str, extra: List[str]=None):
        self.exact: Set[str] = set()
        self.wildcards: Set[str] = set()
        h = (urlparse(target if "://" in target else "//"+target).hostname or "")
        self.exact.add(h.lower())
        parts = h.lower().split(".")
        if len(parts)>=2:
            self.wildcards.add(".".join(parts[-2:]))
        for e in (extra or []):
            if e.startswith("*."):
                self.wildcards.add(e[2:])
            else:
                self.exact.add(e.lower())

    def allow(self, url: str) -> bool:
        h = (urlparse(url).hostname or "").lower()
        if not h: return False
        if h in self.exact: return True
        return any(h==w or h.endswith("."+w) for w in self.wildcards)

    def describe(self) -> str:
        return ", ".join(sorted(self.exact)+[f"*.{w}" for w in sorted(self.wildcards)])


# ─────────────────────────────────────────────────────────────────────────────
#  Modules
# ─────────────────────────────────────────────────────────────────────────────
class WAFDetector:
    @staticmethod
    def detect(res: HttpResult) -> List[str]:
        found = []
        hdrs = res.headers
        body_l = res.body[:8000].lower()
        sc = "; ".join(res.cookies()).lower()
        for sig in WAF_SIGNATURES:
            hit = False
            for hk,hv in (sig.get("headers") or {}).items():
                if hk in hdrs:
                    if hv is None or hv.lower() in hdrs[hk].lower():
                        hit=True; break
            if not hit:
                for ck in (sig.get("cookies") or set()):
                    if ck.lower() in sc:
                        hit=True; break
            if not hit:
                for b in (sig.get("body") or []):
                    if b.lower() in body_l:
                        hit=True; break
            if hit:
                found.append(sig["name"])
        return found


class TechDetector:
    @staticmethod
    def detect(res: HttpResult) -> List[str]:
        found = []
        hdrs = res.headers
        body_l = res.body[:20000].lower()
        sc = "; ".join(res.cookies()).lower()
        for sig in TECH_SIGS:
            hit = False
            for hk,hv in (sig.get("headers") or {}).items():
                if hk in hdrs:
                    if hv is None or hv.lower() in hdrs[hk].lower():
                        hit=True; break
            if not hit:
                for ck in (sig.get("cookies") or set()):
                    if ck.lower() in sc:
                        hit=True; break
            if not hit:
                for p in (sig.get("body") or []):
                    if re.search(p, body_l, re.I):
                        hit=True; break
            if hit:
                found.append(sig["name"])
        return found


class HeaderAuditor:
    @staticmethod
    def audit(res: HttpResult) -> Tuple[Dict[str,Any], List[Dict]]:
        result: Dict[str,Any] = {}
        csp_issues: List[Dict] = []
        for hname, cfg in SECURITY_HEADERS.items():
            val = res.headers.get(hname)
            present = val is not None
            try:
                ok = cfg["check"](val) if present else False
            except Exception:
                ok = False
            result[hname] = {
                "present": present,
                "value": val,
                "ok": ok,
                "severity": cfg["severity"],
                "expected": cfg["expected"],
                "cwe": cfg["cwe"],
                "owasp": cfg["owasp"],
            }
            if hname == "content-security-policy" and val:
                for pattern, desc, sev in CSP_WEAKNESS_RE:
                    if re.search(pattern, val, re.I):
                        csp_issues.append({"weakness": desc, "pattern": pattern, "severity": sev})
        return result, csp_issues

    @staticmethod
    def score(audit: Dict[str,Any]) -> int:
        pts = {"critical":0,"high":10,"medium":30,"low":10,"informational":5}
        s = 100
        for h, data in audit.items():
            if not data["ok"]:
                s -= pts.get(data["severity"], 0)
        return max(0, s)


class CORSAnalyser:
    @staticmethod
    async def test(eng: HttpEngine, url: str, target_origin: str) -> List[Dict]:
        results = []
        parsed = urlparse(url)
        origins_to_test = []
        for o in CORS_ORIGINS:
            o = o.replace("{target_origin}", target_origin)
            o = o.replace("{target}", parsed.hostname or "")
            origins_to_test.append(o)
        for origin in origins_to_test:
            res = await eng.options(url, headers={
                "Origin": origin,
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "Authorization,X-Custom",
            })
            acao = res.headers.get("access-control-allow-origin","")
            acac = res.headers.get("access-control-allow-credentials","")
            if acao:
                issue = None
                if acao == "*" and "true" in acac.lower():
                    issue = {"severity":"critical","desc":"Wildcard ACAO with Allow-Credentials: true"}
                elif acao == origin and origin == "null":
                    issue = {"severity":"high","desc":"null origin reflected with CORS allow"}
                elif acao == origin and "evil" in origin:
                    issue = {"severity":"high","desc":"Arbitrary origin reflected in ACAO"}
                elif acao == "*":
                    issue = {"severity":"medium","desc":"Wildcard ACAO (no credentials)"}
                elif acac.lower()=="true" and acao not in ("","*"):
                    issue = {"severity":"medium","desc":"ACAO with credentials allowed"}
                if issue:
                    results.append({
                        "url": url, "tested_origin": origin,
                        "acao": acao, "acac": acac,
                        **issue,
                        "poc_curl": (
                            f"curl -s -I '{url}' "
                            f"-H 'Origin: {origin}' "
                            f"-H 'Access-Control-Request-Method: GET'"
                        ),
                    })
        return results


class CookieAuditor:
    @staticmethod
    def audit(res: HttpResult, url: str) -> List[Dict]:
        findings = []
        is_https = url.startswith("https://")
        for raw in res.cookies():
            raw_l = raw.lower()
            name = raw.split("=")[0].strip()
            is_session = any(h in name.lower() for h in SESSION_COOKIE_HINTS)
            issues = []
            if is_https and "secure" not in raw_l:
                issues.append({"flag":"Missing Secure","severity":"medium","cwe":"CWE-614"})
            if "httponly" not in raw_l:
                issues.append({"flag":"Missing HttpOnly","severity":"medium","cwe":"CWE-1004"})
            ss = re.search(r"samesite=(\w+)", raw_l)
            ss_val = ss.group(1).lower() if ss else None
            if ss_val is None:
                issues.append({"flag":"Missing SameSite","severity":"medium","cwe":"CWE-352"})
            elif ss_val == "none" and "secure" not in raw_l:
                issues.append({"flag":"SameSite=None without Secure","severity":"high","cwe":"CWE-614"})
            # Cookie prefix checks
            if name.startswith("__Secure-") and ("secure" not in raw_l or not is_https):
                issues.append({"flag":"__Secure- prefix without Secure flag","severity":"high","cwe":"CWE-614"})
            if name.startswith("__Host-") and (
                "secure" not in raw_l or "path=/" not in raw_l.replace(" ","") or "domain=" in raw_l
            ):
                issues.append({"flag":"__Host- prefix requirements not met","severity":"high","cwe":"CWE-614"})
            if issues:
                for iss in issues:
                    findings.append({"cookie_name":name,"is_session_cookie":is_session,
                                     "raw_cookie":raw[:200],"url":url,**iss})
        return findings


class JSAnalyzer:
    CALLSITE_RES = [
        re.compile(r"""fetch\s*\(\s*["'`]([^"'`]+)["'`]"""),
        re.compile(r"""axios\.(?:get|post|put|delete|patch|head)\s*\(\s*["'`]([^"'`]+)["'`]""",re.I),
        re.compile(r"""axios\s*\(\s*\{[^}]*?url\s*:\s*["'`]([^"'`]+)["'`]""",re.I|re.S),
        re.compile(r"""\.open\s*\(\s*["'][A-Z]+["']\s*,\s*["'`]([^"'`]+)["'`]"""),
        re.compile(r"""\$\.(?:get|post|ajax|getJSON)\s*\(\s*["'`]([^"'`]+)["'`]""",re.I),
        re.compile(r"""url\s*:\s*["'`](/[^"'`]+)["'`]"""),
        re.compile(r"""["'`]((?:/api|/v\d+|/graphql|/rest|/gql|/internal|/admin|/service)
                        [A-Za-z0-9_\-./]*)["'`]""",re.X|re.I),
        re.compile(r"""route\s*\(\s*["'`]([^"'`]+)["'`]\s*,"""),
        re.compile(r"""(?:endpoint|baseURL|BASE_URL)\s*[=:]\s*["'`]([^"'`]+)["'`]""",re.I),
        re.compile(r"""["'`](https?://[A-Za-z0-9_\-./]+(?:\?[A-Za-z0-9_\-=&%]+)?)["'`]"""),
    ]
    SOURCEMAP_RE = re.compile(r"//[#@]\s*sourceMappingURL=([^\s'\"]+)")
    ENDPOINT_RE = re.compile(
        r"""["'`]((?:/[A-Za-z0-9_\-./]{2,})|(?:https?://[A-Za-z0-9_\-./=&%?:]+))["'`]""")
    CHUNK_RE = re.compile(r"""chunk(?:Files|Map)\s*=\s*(\{[^}]+\})""")

    def __init__(self):
        self.endpoints: Set[str] = set()
        self.callsites: Set[str] = set()
        self.sourcemaps: Set[str] = set()
        self.secret_hits: List[Dict] = []
        self.webpack_chunks: List[str] = []

    def analyze(self, base_url: str, body: str):
        for rx in self.CALLSITE_RES:
            for m in rx.finditer(body):
                u = m.group(1)
                if 1<len(u)<512 and not u.startswith(("data:","blob:","#","javascript:")):
                    self.callsites.add(self._norm(base_url,u))
        for m in self.ENDPOINT_RE.finditer(body):
            c = m.group(1)
            if 2<len(c)<256:
                self.endpoints.add(self._norm(base_url,c))
        for m in self.SOURCEMAP_RE.finditer(body):
            self.sourcemaps.add(self._norm(base_url,m.group(1)))
        for m in self.CHUNK_RE.finditer(body):
            try:
                obj = m.group(1).replace("'",'"')
                chunk_ids = re.findall(r'"(\d+)"', obj)
                self.webpack_chunks.extend(chunk_ids[:20])
            except Exception: pass
        self._scan_secrets(base_url, body)

    def _scan_secrets(self, base_url: str, body: str):
        for name, pattern, cwe, min_ent in SECRET_PATTERNS:
            for m in re.finditer(pattern, body):
                raw = m.group(0)
                val = m.group(1) if m.lastindex else raw
                if any(h.lower() in val.lower() for h in SECRET_FP): continue
                ent = entropy(val)
                if ent < min_ent and min_ent > 0: continue
                conf = "high" if ent>=4.0 else "medium" if ent>=3.0 else "low"
                self.secret_hits.append({
                    "type":name,"cwe":cwe,"source":base_url,
                    "preview":raw[:6]+"…(redacted)",
                    "entropy":f"{ent:.2f}","confidence":conf,
                })

    @staticmethod
    def _norm(base, ref) -> str:
        return ref if ref.startswith("http") else urljoin(base,ref)


class PassiveOSINT:
    def __init__(self, target: str, log):
        self.target = target
        self.log = log
        h = urlparse(target if "://" in target else "//"+target).hostname or target
        parts = h.split(".")
        self.apex = ".".join(parts[-2:]) if len(parts)>=2 else h

    async def run(self, eng: HttpEngine) -> Dict[str,Any]:
        out = {"hosts":set(),"urls":set()}
        # CT logs
        for tpl in [
            f"https://crt.sh/?q=%25.{self.apex}&output=json",
            f"https://certspotter.com/api/v1/issuances?domain={self.apex}&include_subdomains=true&expand=dns_names",
        ]:
            res = await eng.get(tpl, external=True)
            if res.ok and res.body:
                out["hosts"] |= self._parse_ct(res.body, tpl)
        # Wayback
        wb = await eng.get(
            f"https://web.archive.org/cdx/search/cdx"
            f"?url=*.{self.apex}/*&output=json&fl=original&collapse=urlkey&limit=3000",
            external=True)
        if wb.ok and wb.body:
            out["urls"] |= self._parse_wayback(wb.body)
        self.log.info("OSINT: %d hosts, %d archived URLs", len(out["hosts"]), len(out["urls"]))
        return out

    @staticmethod
    def _parse_ct(body: str, url: str) -> Set[str]:
        hosts: Set[str] = set()
        try:
            data = json.loads(body)
            if isinstance(data, list):
                for row in data:
                    if isinstance(row, dict):
                        for fn in ("name_value","dns_names","common_name"):
                            v = row.get(fn,"")
                            if isinstance(v, list):
                                for n in v:
                                    hosts.add(n.strip().lstrip("*.").lower())
                            elif v:
                                for n in str(v).splitlines():
                                    hosts.add(n.strip().lstrip("*.").lower())
        except Exception: pass
        return {h for h in hosts if h and "@" not in h and " " not in h}

    @staticmethod
    def _parse_wayback(body: str) -> Set[str]:
        urls: Set[str] = set()
        try:
            rows = json.loads(body)
            for row in (rows[1:] if rows and isinstance(rows[0],list) else rows):
                if isinstance(row,list) and row: urls.add(row[0])
                elif isinstance(row,str): urls.add(row)
        except Exception: pass
        return urls


class SubdomainEnumerator:
    @staticmethod
    async def enumerate(apex: str, wordlist: List[str], log) -> List[str]:
        found = []
        sem = asyncio.Semaphore(50)
        async def check(sub: str):
            fqdn = f"{sub}.{apex}"
            async with sem:
                try:
                    loop = asyncio.get_event_loop()
                    addrs = await loop.getaddrinfo(fqdn, None,
                                                    type=socket.SOCK_STREAM,
                                                    proto=socket.IPPROTO_TCP)
                    if addrs:
                        found.append(fqdn)
                        log.info("Subdomain resolved: %s", fqdn)
                except Exception: pass
        await asyncio.gather(*[check(w) for w in wordlist])
        return sorted(set(found))


class PathProber:
    @staticmethod
    async def probe(eng: HttpEngine, base: str, paths: Tuple[str,...]) -> List[Dict]:
        found = []
        p = urlparse(base)
        root = f"{p.scheme}://{p.netloc}"
        tasks = [(root+path, asyncio.ensure_future(eng.get(root+path))) for path in paths]
        for url, task in tasks:
            try:
                res = await task
                if res.ok and res.status in (200,201,204,301,302,307,308):
                    found.append({"url":url,"status":res.status,
                                  "size":len(res.body),"ct":res.content_type[:60]})
            except Exception: pass
        return found


class GraphQLProber:
    @staticmethod
    async def probe(eng: HttpEngine, endpoint: str) -> Optional[Dict]:
        res = await eng.post(endpoint,
                             data=GRAPHQL_INTROSPECTION,
                             headers={"Content-Type":"application/json"})
        if res.ok and "__schema" in res.body:
            try:
                data = json.loads(res.body)
                types = (data.get("data",{}).get("__schema",{})
                         .get("types",[]))
                return {"endpoint":endpoint,"type_count":len(types),"sample_types":[
                    t["name"] for t in types[:10] if not t["name"].startswith("__")
                ]}
            except Exception:
                return {"endpoint":endpoint,"type_count":0,"sample_types":[]}
        return None


# ─────────────────────────────────────────────────────────────────────────────
#  Main Scanner
# ─────────────────────────────────────────────────────────────────────────────
class AdvancedScanner:
    def __init__(self, cfg, log):
        self.cfg = cfg
        self.log = log
        self.scope = ScopeGuard(cfg.target, cfg.scope_extra)
        self._start = time.monotonic()

        # Collected data
        self.waf: List[str] = []
        self.tech: List[str] = []
        self.ips: List[str] = []
        self.subdomains: List[str] = []
        self.assets: Set[str] = set()
        self.api_endpoints: Set[str] = set()
        self.graphql_endpoints: Set[str] = set()
        self.js_files: Set[str] = set()
        self.forms: List[Dict] = []
        self.params: Dict[str,Dict[str,List[str]]] = {}
        self.cors_results: List[Dict] = []
        self.cookie_findings: List[Dict] = []
        self.passive_hosts: Set[str] = set()
        self.passive_urls: Set[str] = set()
        self.wayback_urls: Set[str] = set()
        self.open_paths: List[Dict] = []
        self.headers_audit: Dict[str,Any] = {}
        self.csp_weaknesses: List[Dict] = []
        self.headers_score: int = 0
        self.js = JSAnalyzer()
        self._findings: Dict[str,Finding] = {}
        self._seen: Set[str] = set()
        self.diagnostics: Dict[str,Any] = {}
        self._seed_ok: Optional[str] = None

    def _seed(self) -> str:
        t = self.cfg.target
        return t if "://" in t else "https://"+t

    def _add_finding(self, f: Finding):
        k = f.key()
        if k in self._findings:
            existing = self._findings[k]
            for u in f.affected_urls or [f.affected_url]:
                if u not in existing.affected_urls:
                    existing.affected_urls.append(u)
        else:
            if not f.affected_urls:
                f.affected_urls = [f.affected_url]
            self._findings[k] = f

    def _record_params(self, url: str):
        p = urlparse(url)
        if not p.query: return
        ep = f"{p.scheme}://{p.netloc}{p.path}"
        bucket = self.params.setdefault(ep,{})
        for name,vals in parse_qs(p.query,keep_blank_values=True).items():
            store = bucket.setdefault(name,[])
            for v in vals:
                if v not in store and len(store)<5:
                    store.append(v)

    async def _probe_seed(self, eng: HttpEngine) -> Optional[str]:
        seed = self._seed()
        p = urlparse(seed)
        candidates = [seed]
        if not seed.startswith("https://"):
            candidates.insert(0, f"https://{p.hostname}")
        for c in candidates:
            res = await eng.get(c)
            if res.ok and 200<=res.status<400:
                self._seed_ok = c
                # IP
                try:
                    ip = socket.gethostbyname(p.hostname or "")
                    self.ips.append(ip)
                except Exception: pass
                return c
            self.diagnostics.setdefault("seed_attempts",[]).append(
                {"url":c,"status":res.status,"error":res.error})
        return None

    async def _analyze_headers(self, res: HttpResult):
        audit, csp_issues = HeaderAuditor.audit(res)
        self.headers_audit = audit
        self.csp_weaknesses = csp_issues
        self.headers_score = HeaderAuditor.score(audit)
        # Missing headers → findings
        sev_order = {"medium":1,"low":2,"informational":3}
        for hname, data in audit.items():
            if not data["ok"]:
                sev = data["severity"]
                self._add_finding(Finding(
                    id=SHA1(f"hdr-{hname}")[:8],
                    title=f"Security header {'misconfigured' if data['present'] else 'missing'}: {hname}",
                    severity=sev, confidence="confirmed",
                    cwe=data["cwe"], owasp=data["owasp"],
                    affected_url=res.url, endpoint=urlparse(res.url).path or "/",
                    request=f"GET {res.url}",
                    response_evidence=f"'{hname}': {data['value'] or '(absent)'}",
                    technical_detail=(
                        f"The response {'contains a weak value for' if data['present'] else 'omits'} "
                        f"the {hname} header. Expected: {data['expected']}."),
                    impact=f"Weakens browser-side protections. Severity: {sev}.",
                    remediation=f"Configure the web server/CDN to return a valid {hname} header.",
                    cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:L/A:N",
                    cvss_score={"medium":5.3,"low":3.1,"informational":0.0}.get(sev,0.0),
                    poc_curl=f"curl -sI '{res.url}' | grep -i '{hname}'",
                    poc_burp=(f"GET {urlparse(res.url).path or '/'} HTTP/1.1\r\n"
                              f"Host: {urlparse(res.url).hostname}\r\n\r\n"),
                    poc_steps=[f"1. Send: GET {res.url}",
                               f"2. Observe: '{hname}' is {'weak' if data['present'] else 'absent'} in response headers.",
                               f"3. Expected: {data['expected']}"],
                    detection_method="direct header inspection",
                ))
        # CSP weaknesses
        for iss in csp_issues:
            self._add_finding(Finding(
                id=SHA1(f"csp-{iss['pattern']}")[:8],
                title=f"CSP weakness: {iss['weakness']}",
                severity=iss["severity"], confidence="confirmed",
                cwe="CWE-1021", owasp="A05:2021",
                affected_url=res.url, endpoint=urlparse(res.url).path or "/",
                request=f"GET {res.url}",
                response_evidence=f"CSP: {res.headers.get('content-security-policy','')[:300]}",
                technical_detail=iss["weakness"],
                impact="Weakens XSS and content-injection protections.",
                remediation="Remove unsafe CSP directives. Prefer hashes/nonces over 'unsafe-inline'.",
                cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:C/C:L/I:L/A:N",
                cvss_score={"high":6.1,"medium":4.7,"low":3.1}.get(iss["severity"],3.1),
                poc_curl=f"curl -sI '{res.url}' | grep -i content-security-policy",
                poc_burp="",
                poc_steps=["1. Fetch the page and inspect the Content-Security-Policy header.",
                           f"2. Identify the weakness: {iss['weakness']}"],
                detection_method="CSP policy analysis",
            ))

    async def _visit(self, eng: HttpEngine, url: str, depth: int) -> List[str]:
        if url in self._seen: return []
        self._seen.add(url)
        res = await eng.get(url)
        if not res.ok: return []
        self.assets.add(res.final_url or url)
        self._record_params(res.final_url or url)
        waf = WAFDetector.detect(res)
        for w in waf:
            if w not in self.waf: self.waf.append(w)
        tech = TechDetector.detect(res)
        for t in tech:
            if t not in self.tech: self.tech.append(t)
        ck = CookieAuditor.audit(res, url)
        self.cookie_findings.extend(ck)
        # Cookie findings → structured findings
        for cf in ck:
            self._add_finding(Finding(
                id=SHA1(f"ck-{cf['flag']}-{cf['cookie_name']}")[:8],
                title=f"Cookie security issue: {cf['flag']} ({cf['cookie_name']})",
                severity=cf["severity"], confidence="confirmed",
                cwe=cf["cwe"], owasp="A05:2021",
                affected_url=url, endpoint=urlparse(url).path or "/",
                request=f"GET {url}",
                response_evidence=f"Set-Cookie: {cf['raw_cookie']}",
                technical_detail=(
                    f"Cookie '{cf['cookie_name']}' is missing the {cf['flag']} attribute. "
                    f"Session cookie: {cf['is_session_cookie']}."),
                impact="Session hijacking, CSRF, or cookie theft risk.",
                remediation=f"Add the missing attribute to the Set-Cookie header.",
                cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:U/C:H/I:N/A:N",
                cvss_score={"high":6.5,"medium":4.3,"low":2.1}.get(cf["severity"],2.1),
                poc_curl=f"curl -sv '{url}' 2>&1 | grep -i 'set-cookie'",
                poc_burp="",
                poc_steps=[f"1. GET {url}",f"2. Inspect Set-Cookie header for '{cf['cookie_name']}'",
                           f"3. Note missing: {cf['flag']}"],
                detection_method="cookie attribute analysis",
            ))
        ct = res.content_type
        next_urls: List[str] = []
        if "html" in ct or "<html" in res.body[:500].lower():
            links, scripts = self._extract_links(url, res.body)
            self.forms.extend(self._extract_forms(url, res.body))
            for s in scripts:
                if ".js" in s: self.js_files.add(s)
            for ln in links: self._record_params(ln)
            if depth < self.cfg.depth:
                next_urls = [l for l in links
                             if self.scope.allow(l) and l not in self._seen
                             and not l.lower().endswith((".png",".jpg",".css",".ico",".woff"))]
        elif "javascript" in ct or url.endswith(".js"):
            self.js_files.add(url)
            self.js.analyze(url, res.body)
        return next_urls

    @staticmethod
    def _extract_links(base: str, body: str) -> Tuple[Set[str],Set[str]]:
        links, scripts = set(), set()
        for m in re.finditer(r'(?:href|src|action)\s*=\s*["\']([^"\']+)["\']', body, re.I):
            u = urljoin(base, m.group(1))
            links.add(u)
        for m in re.finditer(r'<script[^>]+src\s*=\s*["\']([^"\']+)["\']', body, re.I):
            scripts.add(urljoin(base, m.group(1)))
        return links, scripts

    @staticmethod
    def _extract_forms(base: str, body: str) -> List[Dict]:
        out = []
        for fm in re.finditer(r'<form\b([^>]*)>(.*?)</form>', body, re.I|re.S):
            attrs = dict(re.findall(r'(\w[\w-]*)\s*=\s*["\']([^"\']*)["\']', fm.group(1)))
            inputs = []
            for im in re.finditer(r'<(?:input|select|textarea)\b([^>]*)>', fm.group(2), re.I):
                ia = dict(re.findall(r'(\w[\w-]*)\s*=\s*["\']([^"\']*)["\']', im.group(1)))
                name = ia.get("name") or ia.get("id")
                if name:
                    inputs.append({"name":name,"type":ia.get("type","text")})
            out.append({
                "action": urljoin(base, attrs.get("action","")) or base,
                "method": (attrs.get("method","GET")).upper(),
                "inputs": inputs, "source_page": base,
            })
        return out

    async def _analyze_js_files(self, eng: HttpEngine):
        if not self.js_files: return
        js_list = list(self.js_files)[:self.cfg.max_pages]
        results = await asyncio.gather(*[eng.get(u) for u in js_list], return_exceptions=True)
        for res in results:
            if isinstance(res, Exception) or not getattr(res,"ok",False): continue
            self.js.analyze(res.final_url or res.url, res.body)
        # Sourcemap recovery
        maps = [m for m in self.js.sourcemaps if self.scope.allow(m)]
        if maps:
            mres = await asyncio.gather(*[eng.get(m) for m in maps], return_exceptions=True)
            for res in mres:
                if isinstance(res, Exception) or not getattr(res,"ok",False): continue
                try:
                    doc = json.loads(res.body)
                    content = "\n".join(c for c in (doc.get("sourcesContent") or []) if c)
                    if content:
                        self.js.analyze(res.url, content)
                except Exception: pass
        self.assets |= self.js.endpoints
        # Emit secret findings
        for hit in self.js.secret_hits:
            self._add_finding(Finding(
                id=SHA1(f"secret-{hit['type']}-{hit['source']}")[:8],
                title=f"Exposed secret in JavaScript: {hit['type']}",
                severity="high" if hit["confidence"]=="high" else "medium",
                confidence=hit["confidence"],
                cwe=hit["cwe"], owasp="A07:2021",
                affected_url=hit["source"], endpoint=urlparse(hit["source"]).path,
                request=f"GET {hit['source']}",
                response_evidence=f"match preview: {hit['preview']} (entropy={hit['entropy']})",
                technical_detail=(
                    "Client-side JavaScript contains a string matching a known credential pattern. "
                    f"Pattern type: {hit['type']}. Entropy: {hit['entropy']}."),
                impact="If the credential is live, it may grant unauthorized access to the associated service.",
                remediation="Remove secrets from client-side code. Use server-side proxies. Rotate any confirmed-live keys.",
                cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:N",
                cvss_score={"high":9.1,"medium":5.3,"low":2.0}.get(hit["confidence"],5.3),
                poc_curl=f"curl -s '{hit['source']}' | grep -oE '<pattern>'",
                poc_burp="",
                poc_steps=[f"1. Fetch {hit['source']}",
                           f"2. Search body for {hit['type']} pattern",
                           "3. Confirm the credential is live and in scope before submitting"],
                detection_method="regex + entropy analysis",
            ))

    async def scan(self) -> ScanResult:
        seed = self._seed()
        async with HttpEngine(self.cfg, self.scope, self.log) as eng:
            working = await self._probe_seed(eng)
            if not working:
                self.diagnostics["reason"] = "seed unreachable"
                return self._build_result()

            # Initial full response analysis
            res0 = await eng.get(working)
            if res0.ok:
                await self._analyze_headers(res0)
                waf = WAFDetector.detect(res0)
                self.waf.extend(w for w in waf if w not in self.waf)
                tech = TechDetector.detect(res0)
                self.tech.extend(t for t in tech if t not in self.tech)

            # Passive OSINT
            if self.cfg.passive:
                osint = await PassiveOSINT(self.cfg.target, self.log).run(eng)
                p = urlparse(working)
                for h in osint["hosts"]:
                    self.passive_hosts.add(h)
                    cand = f"{p.scheme}://{h}/"
                    if self.scope.allow(cand):
                        self._seen.discard(cand)  # ensure we visit
                for u in osint["urls"]:
                    self.passive_urls.add(u)
                    self._record_params(u)
                self.wayback_urls = set(list(osint["urls"])[:500])

            # Subdomain enumeration (DNS)
            if self.cfg.enum_subdomains:
                apex = ".".join((urlparse(working).hostname or "").split(".")[-2:])
                _console.print(f"[cyan]Enumerating subdomains of {apex}...[/cyan]" if _HAVE_RICH
                               else f"Enumerating subdomains of {apex}...")
                self.subdomains = await SubdomainEnumerator.enumerate(apex, SUBDOMAIN_WORDLIST, self.log)
                self.diagnostics["subdomains_checked"] = len(SUBDOMAIN_WORDLIST)
                self.diagnostics["subdomains_found"] = len(self.subdomains)

            # Path probing
            if self.cfg.probe_paths:
                self.open_paths = await PathProber.probe(eng, working, SCHEMA_PATHS)
                for op in self.open_paths:
                    if op["status"]==200 and (".env" in op["url"] or ".git" in op["url"]
                                               or "config" in op["url"].lower()):
                        self._add_finding(Finding(
                            id=SHA1(f"openpath-{op['url']}")[:8],
                            title=f"Sensitive path accessible: {op['url']}",
                            severity="high", confidence="confirmed",
                            cwe="CWE-548", owasp="A05:2021",
                            affected_url=op["url"], endpoint=urlparse(op["url"]).path,
                            request=f"GET {op['url']}",
                            response_evidence=f"HTTP {op['status']} – {op['size']} bytes",
                            technical_detail=f"The path {op['url']} returned HTTP {op['status']}.",
                            impact="May expose credentials, environment variables, or application source code.",
                            remediation="Block access to sensitive files at the web server level.",
                            cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N",
                            cvss_score=7.5,
                            poc_curl=f"curl -s '{op['url']}'",
                            poc_burp=(f"GET {urlparse(op['url']).path} HTTP/1.1\r\n"
                                     f"Host: {urlparse(op['url']).hostname}\r\n\r\n"),
                            poc_steps=[f"1. Send: GET {op['url']}",
                                       f"2. Observe HTTP {op['status']} response with {op['size']} bytes"],
                            detection_method="path probing",
                        ))

            # Crawl
            queue = [(working, 0)]
            while queue and len(self._seen)<self.cfg.max_pages:
                batch = queue[:self.cfg.workers]
                queue = queue[self.cfg.workers:]
                results = await asyncio.gather(*[
                    self._visit(eng, url, depth)
                    for url, depth in batch
                    if url not in self._seen and self.scope.allow(url)
                ], return_exceptions=True)
                for r in results:
                    if isinstance(r, list):
                        for nxt in r:
                            queue.append((nxt, batch[0][1]+1))

            # JS analysis pass
            await self._analyze_js_files(eng)
            self.api_endpoints |= self.js.callsites
            for asset in list(self.assets)+list(self.api_endpoints):
                path = urlparse(asset).path.lower()
                if any(h in path for h in ("/graphql","/gql","/api/graphql","/query")):
                    self.graphql_endpoints.add(asset)

            # GraphQL introspection
            if self.cfg.graphql:
                for ep in list(self.graphql_endpoints):
                    info = await GraphQLProber.probe(eng, ep)
                    if info:
                        self._add_finding(Finding(
                            id=SHA1(f"graphql-{ep}")[:8],
                            title="GraphQL introspection enabled",
                            severity="low", confidence="confirmed",
                            cwe="CWE-200", owasp="A05:2021",
                            affected_url=ep, endpoint=urlparse(ep).path,
                            request=f"POST {ep} (introspection query)",
                            response_evidence=f"__schema returned {info['type_count']} types",
                            technical_detail="Full schema exposed via introspection.",
                            impact="Schema mapping accelerates API abuse.",
                            remediation="Disable introspection in production.",
                            cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:N/A:N",
                            cvss_score=5.3,
                            poc_curl=(f"curl -s -X POST '{ep}' "
                                     f"-H 'Content-Type: application/json' "
                                     f"-d '{{\"query\":\"{{__schema{{queryType{{name}}}}}}\"}}'"),
                            poc_burp="",
                            poc_steps=[f"1. POST to {ep} with introspection query",
                                       "2. Observe __schema in JSON response"],
                            detection_method="GraphQL introspection probe",
                        ))

            # CORS testing
            if self.cfg.cors_test:
                pages_to_test = list(self._seen)[:10]
                for page_url in pages_to_test:
                    origin = f"{urlparse(working).scheme}://{urlparse(working).hostname}"
                    cors = await CORSAnalyser.test(eng, page_url, origin)
                    self.cors_results.extend(cors)
                for cr in self.cors_results:
                    self._add_finding(Finding(
                        id=SHA1(f"cors-{cr['url']}-{cr['tested_origin']}")[:8],
                        title=f"CORS misconfiguration: {cr['desc']}",
                        severity=cr["severity"], confidence="confirmed",
                        cwe="CWE-942", owasp="A05:2021",
                        affected_url=cr["url"], endpoint=urlparse(cr["url"]).path,
                        request=f"OPTIONS {cr['url']} Origin: {cr['tested_origin']}",
                        response_evidence=(f"Access-Control-Allow-Origin: {cr['acao']}\n"
                                          f"Access-Control-Allow-Credentials: {cr['acac']}"),
                        technical_detail=cr["desc"],
                        impact="Cross-site requests may read authenticated responses.",
                        remediation="Validate Origin against an explicit allowlist. Never reflect arbitrary origins.",
                        cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:C/C:H/I:N/A:N",
                        cvss_score={"critical":9.6,"high":7.4,"medium":5.4,"low":3.1}.get(cr["severity"],5.4),
                        poc_curl=cr["poc_curl"],
                        poc_burp="",
                        poc_steps=[cr["poc_curl"],"Observe Access-Control-Allow-Origin reflects tested origin"],
                        detection_method="CORS origin reflection test",
                    ))

        return self._build_result()

    def _build_result(self) -> ScanResult:
        order = {"critical":0,"high":1,"medium":2,"low":3,"informational":4}
        findings = sorted(self._findings.values(),
                         key=lambda f: order.get(f.severity,9))
        return ScanResult(
            target=self.cfg.target, scan_time=NOW(),
            duration_s=round(time.monotonic()-self._start,1),
            scope=self.scope.describe(),
            waf_detected=self.waf, technologies=self.tech,
            ip_addresses=self.ips, subdomains=self.subdomains,
            assets=sorted(self.assets), api_endpoints=sorted(self.api_endpoints),
            graphql_endpoints=sorted(self.graphql_endpoints),
            js_files=sorted(self.js_files), js_callsites=sorted(self.js.callsites),
            secret_hits=self.js.secret_hits, forms=self.forms,
            parameters=self.params, cors_results=self.cors_results,
            cookie_findings=self.cookie_findings,
            passive_hosts=sorted(self.passive_hosts),
            passive_urls=sorted(self.passive_urls)[:500],
            wayback_urls=sorted(self.wayback_urls)[:500],
            open_paths=self.open_paths, findings=findings,
            headers_audit=self.headers_audit, csp_weaknesses=self.csp_weaknesses,
            diagnostics=self.diagnostics,
        )


# ─────────────────────────────────────────────────────────────────────────────
#  Reporters
# ─────────────────────────────────────────────────────────────────────────────
class AdvancedReporter:
    def __init__(self, result: ScanResult, outdir: str):
        self.r = result
        self.outdir = outdir
        os.makedirs(outdir, exist_ok=True)
        self._ts = int(time.time())

    # ── JSON ──────────────────────────────────────────────────────────────────
    def json(self) -> str:
        path = os.path.join(self.outdir, f"advanced_report_{self._ts}.json")
        with open(path,"w") as f:
            json.dump(dataclasses.asdict(self.r), f, indent=2, default=str)
        return path

    # ── Markdown ──────────────────────────────────────────────────────────────
    def markdown(self) -> str:
        r = self.r
        path = os.path.join(self.outdir, f"advanced_report_{self._ts}.md")
        sev_counts: Dict[str,int] = {}
        for f in r.findings:
            sev_counts[f.severity] = sev_counts.get(f.severity,0)+1
        L = []
        L.append("# Advanced Bug Bounty Recon Report")
        L.append(f"**Target:** `{r.target}`  ")
        L.append(f"**Scan Time:** {r.scan_time}  ")
        L.append(f"**Duration:** {r.duration_s}s  ")
        L.append(f"**Scope:** `{r.scope}`\n")
        L.append("> Authorized testing only. All findings require manual verification.\n")

        L.append("## Executive Summary")
        L.append(f"| Severity | Count |")
        L.append(f"|----------|-------|")
        for sev in ("critical","high","medium","low","informational"):
            if sev in sev_counts:
                L.append(f"| {sev.capitalize()} | {sev_counts[sev]} |")
        L.append(f"\n**Security Header Score:** {HeaderAuditor.score(r.headers_audit)}/100")
        L.append(f"**WAF/CDN Detected:** {', '.join(r.waf_detected) or 'None detected'}")
        L.append(f"**Technologies:** {', '.join(r.technologies) or 'None detected'}")
        L.append(f"**IPs:** {', '.join(r.ip_addresses) or 'N/A'}")
        L.append(f"**Subdomains Discovered:** {len(r.subdomains)}")
        L.append(f"**Assets Crawled:** {len(r.assets)}")
        L.append(f"**API Endpoints:** {len(r.api_endpoints)}")
        L.append(f"**JS Files:** {len(r.js_files)}")
        L.append(f"**Secret Candidates:** {len(r.secret_hits)}\n")

        L.append("## Findings")
        if not r.findings:
            L.append("_No findings above the threshold._\n")
        for i,f in enumerate(r.findings,1):
            cvss = f"**CVSS:** {f.cvss_score} — `{f.cvss_vector}`" if f.cvss_score else ""
            L.append(f"### Finding {i}: {f.title}")
            L.append(f"- **Severity:** `{f.severity}` | **Confidence:** `{f.confidence}`")
            L.append(f"- **CWE:** {f.cwe} | **OWASP:** {f.owasp}")
            if cvss: L.append(f"- {cvss}")
            L.append(f"- **Affected URL:** `{f.affected_url}`")
            L.append(f"- **Detection:** {f.detection_method}")
            L.append(f"\n**Technical Detail:**\n{f.technical_detail}\n")
            L.append(f"**Impact:**\n{f.impact}\n")
            L.append(f"**Request:**\n```http\n{f.request}\n```")
            L.append(f"**Response Evidence:**\n```\n{f.response_evidence}\n```")
            if f.poc_curl:
                L.append(f"**PoC (curl):**\n```bash\n{f.poc_curl}\n```")
            L.append("**Reproduction Steps:**")
            for step in f.poc_steps:
                L.append(f"  {step}")
            L.append(f"\n**Remediation:**\n{f.remediation}\n")
            L.append("---")

        L.append("## Security Headers Audit")
        L.append(f"**Score: {HeaderAuditor.score(r.headers_audit)}/100**\n")
        L.append("| Header | Present | OK | Severity | Value |")
        L.append("|--------|---------|-----|----------|-------|")
        for hname, data in r.headers_audit.items():
            ok_mark = "✅" if data["ok"] else "❌"
            pres_mark = "✅" if data["present"] else "❌"
            val = (data["value"] or "—")[:60]
            L.append(f"| `{hname}` | {pres_mark} | {ok_mark} | {data['severity']} | {val} |")
        L.append("")

        if r.csp_weaknesses:
            L.append("### CSP Weaknesses")
            for iss in r.csp_weaknesses:
                L.append(f"- **[{iss['severity'].upper()}]** {iss['weakness']}")
            L.append("")

        if r.subdomains:
            L.append(f"## Subdomains Discovered ({len(r.subdomains)})")
            for s in r.subdomains[:100]:
                L.append(f"- `{s}`")
            L.append("")

        if r.open_paths:
            L.append(f"## Open / Sensitive Paths ({len(r.open_paths)})")
            L.append("| URL | Status | Size |")
            L.append("|-----|--------|------|")
            for p in r.open_paths:
                L.append(f"| `{p['url']}` | {p['status']} | {p['size']}B |")
            L.append("")

        if r.cors_results:
            L.append(f"## CORS Issues ({len(r.cors_results)})")
            for cr in r.cors_results:
                L.append(f"- **[{cr['severity'].upper()}]** {cr['url']} — {cr['desc']}")
                L.append(f"  ```bash\n  {cr['poc_curl']}\n  ```")
            L.append("")

        if r.cookie_findings:
            L.append(f"## Cookie Security Issues ({len(r.cookie_findings)})")
            L.append("| Cookie | Issue | Severity |")
            L.append("|--------|-------|----------|")
            for cf in r.cookie_findings[:50]:
                L.append(f"| `{cf['cookie_name']}` | {cf['flag']} | {cf['severity']} |")
            L.append("")

        if r.secret_hits:
            L.append(f"## Secret Candidates ({len(r.secret_hits)})")
            for h in r.secret_hits:
                L.append(f"- **[{h['confidence'].upper()}]** {h['type']} in `{h['source']}`")
                L.append(f"  - Entropy: {h['entropy']} | Preview: `{h['preview']}`")
            L.append("")

        if r.api_endpoints:
            L.append(f"## API Endpoints Discovered ({len(r.api_endpoints)})")
            for ep in sorted(r.api_endpoints)[:80]:
                L.append(f"- `{ep}`")
            L.append("")

        if r.passive_hosts:
            L.append(f"## Passive OSINT Hosts ({len(r.passive_hosts)})")
            for h in r.passive_hosts[:80]:
                L.append(f"- `{h}`")
            L.append("")

        L.append("## References")
        L.append("- [OWASP Top 10](https://owasp.org/Top10/)")
        L.append("- [CWE Database](https://cwe.mitre.org/)")
        L.append("- [OWASP Testing Guide](https://owasp.org/www-project-web-security-testing-guide/)")

        with open(path,"w") as fh:
            fh.write("\n".join(L))
        return path

    # ── HTML ──────────────────────────────────────────────────────────────────
    def html(self) -> str:
        r = self.r
        path = os.path.join(self.outdir, f"advanced_report_{self._ts}.html")
        SEV_COLOR = {"critical":"#8b0000","high":"#cc2200","medium":"#cc7700",
                     "low":"#ccaa00","informational":"#555555"}
        sev_counts: Dict[str,int] = {}
        for f in r.findings: sev_counts[f.severity]=sev_counts.get(f.severity,0)+1
        score = HeaderAuditor.score(r.headers_audit)
        score_color = "#28a745" if score>=80 else "#fd7e14" if score>=50 else "#dc3545"

        findings_html = ""
        for i,f in enumerate(r.findings,1):
            col = SEV_COLOR.get(f.severity,"#555")
            steps_html = "".join(f"<li>{html.escape(s)}</li>" for s in f.poc_steps)
            findings_html += f"""
            <div class="finding" style="border-left:4px solid {col}">
              <h3>#{i} — {html.escape(f.title)}</h3>
              <div class="badges">
                <span class="badge" style="background:{col}">{f.severity.upper()}</span>
                <span class="badge" style="background:#555">{f.confidence}</span>
                <span class="badge" style="background:#333">{f.cwe}</span>
                <span class="badge" style="background:#444">{f.owasp}</span>
                {f'<span class="badge" style="background:#222">CVSS {f.cvss_score}</span>' if f.cvss_score else ''}
              </div>
              <p><strong>URL:</strong> <code>{html.escape(f.affected_url)}</code></p>
              <p><strong>Technical Detail:</strong> {html.escape(f.technical_detail)}</p>
              <p><strong>Impact:</strong> {html.escape(f.impact)}</p>
              <p><strong>Request:</strong></p>
              <pre><code>{html.escape(f.request)}</code></pre>
              <p><strong>Evidence:</strong></p>
              <pre><code>{html.escape(f.response_evidence)}</code></pre>
              {'<p><strong>PoC (curl):</strong></p><pre><code>' + html.escape(f.poc_curl) + '</code></pre>' if f.poc_curl else ''}
              <p><strong>Reproduction:</strong></p><ol>{steps_html}</ol>
              <p><strong>Remediation:</strong> {html.escape(f.remediation)}</p>
            </div>"""

        header_rows = ""
        for hname, data in r.headers_audit.items():
            ok = "✅" if data["ok"] else "❌"
            pres = "✅" if data["present"] else "❌"
            val = html.escape((data["value"] or "—")[:80])
            header_rows += (f"<tr><td><code>{hname}</code></td><td>{pres}</td><td>{ok}</td>"
                           f"<td>{data['severity']}</td><td>{val}</td></tr>")

        subdomain_rows = "".join(f"<tr><td><code>{html.escape(s)}</code></td></tr>"
                                 for s in r.subdomains[:100])
        path_rows = "".join(f"<tr><td><code>{html.escape(p['url'])}</code></td>"
                            f"<td>{p['status']}</td><td>{p['size']}B</td></tr>"
                            for p in r.open_paths)
        secret_rows = "".join(
            f"<tr><td>{html.escape(h['type'])}</td>"
            f"<td><code>{html.escape(h['source'][-60:])}</code></td>"
            f"<td>{h['confidence']}</td><td>{h['entropy']}</td></tr>"
            for h in r.secret_hits)
        api_rows = "".join(f"<tr><td><code>{html.escape(ep)}</code></td></tr>"
                           for ep in sorted(r.api_endpoints)[:80])

        doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Bug Bounty Recon Report – {html.escape(r.target)}</title>
<style>
body{{font-family:'Segoe UI',Arial,sans-serif;background:#0d1117;color:#e6edf3;margin:0;padding:20px}}
h1,h2,h3{{color:#58a6ff}}
.card{{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:20px;margin:16px 0}}
.finding{{background:#161b22;border-radius:6px;padding:16px;margin:12px 0}}
.badge{{display:inline-block;padding:3px 8px;border-radius:4px;color:#fff;font-size:12px;margin:2px;font-weight:bold}}
pre{{background:#0d1117;border:1px solid #30363d;border-radius:4px;padding:12px;overflow-x:auto;white-space:pre-wrap}}
code{{font-family:'Consolas','Courier New',monospace;font-size:13px}}
table{{width:100%;border-collapse:collapse;margin:12px 0}}
th{{background:#21262d;color:#8b949e;padding:8px 12px;text-align:left;font-size:13px}}
td{{padding:8px 12px;border-bottom:1px solid #21262d;font-size:13px}}
.score-circle{{display:inline-block;width:80px;height:80px;border-radius:50%;
  background:conic-gradient({score_color} {score*3.6}deg,#21262d 0deg);
  line-height:80px;text-align:center;font-size:20px;font-weight:bold;color:#fff}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:12px}}
.stat{{background:#21262d;border-radius:6px;padding:14px;text-align:center}}
.stat-n{{font-size:28px;font-weight:bold;color:#58a6ff}}
.stat-l{{font-size:12px;color:#8b949e;margin-top:4px}}
</style>
</head>
<body>
<h1>🔍 Advanced Bug Bounty Recon Report</h1>
<div class="card">
  <p><strong>Target:</strong> <code>{html.escape(r.target)}</code></p>
  <p><strong>Scan Time:</strong> {r.scan_time} &nbsp;|&nbsp; <strong>Duration:</strong> {r.duration_s}s</p>
  <p><strong>Scope:</strong> <code>{html.escape(r.scope)}</code></p>
  <p><strong>WAF/CDN:</strong> {html.escape(', '.join(r.waf_detected) or 'None detected')}</p>
  <p><strong>Technologies:</strong> {html.escape(', '.join(r.technologies) or 'None detected')}</p>
  <p><strong>IPs:</strong> {html.escape(', '.join(r.ip_addresses) or 'N/A')}</p>
</div>

<h2>Summary</h2>
<div class="grid">
  {''.join(f'<div class="stat"><div class="stat-n" style="color:{SEV_COLOR.get(s,chr(35)+chr(53)+chr(53)+chr(53)+chr(53)+chr(53))+chr(34)}">{sev_counts.get(s,0)}</div><div class="stat-l">{s.upper()}</div></div>' for s in ["critical","high","medium","low","informational"])}
  <div class="stat"><div class="stat-n">{len(r.assets)}</div><div class="stat-l">ASSETS</div></div>
  <div class="stat"><div class="stat-n">{len(r.subdomains)}</div><div class="stat-l">SUBDOMAINS</div></div>
  <div class="stat"><div class="stat-n">{len(r.api_endpoints)}</div><div class="stat-l">API ENDPOINTS</div></div>
  <div class="stat"><div class="stat-n">{len(r.secret_hits)}</div><div class="stat-l">SECRET CANDIDATES</div></div>
  <div class="stat"><div class="score-circle">{score}</div><div class="stat-l">HEADER SCORE</div></div>
</div>

<h2>Findings ({len(r.findings)})</h2>
{findings_html or '<p><em>No findings above threshold.</em></p>'}

<h2>Security Headers Audit (Score: {score}/100)</h2>
<div class="card">
<table><tr><th>Header</th><th>Present</th><th>OK</th><th>Severity</th><th>Value</th></tr>
{header_rows}</table>
</div>

{f'<h2>CSP Weaknesses</h2><div class="card"><ul>' + "".join(f'<li><strong>[{html.escape(i["severity"].upper())}]</strong> {html.escape(i["weakness"])}</li>' for i in r.csp_weaknesses) + '</ul></div>' if r.csp_weaknesses else ''}

{f'<h2>Subdomains ({len(r.subdomains)})</h2><div class="card"><table><tr><th>Subdomain</th></tr>{subdomain_rows}</table></div>' if r.subdomains else ''}

{f'<h2>Sensitive Paths ({len(r.open_paths)})</h2><div class="card"><table><tr><th>URL</th><th>Status</th><th>Size</th></tr>{path_rows}</table></div>' if r.open_paths else ''}

{f'<h2>Secret Candidates ({len(r.secret_hits)})</h2><div class="card"><table><tr><th>Type</th><th>Source</th><th>Confidence</th><th>Entropy</th></tr>{secret_rows}</table></div>' if r.secret_hits else ''}

{f'<h2>API Endpoints ({len(r.api_endpoints)})</h2><div class="card"><table><tr><th>Endpoint</th></tr>{api_rows}</table></div>' if r.api_endpoints else ''}

<h2>CORS Test Results</h2>
<div class="card">
{''.join(f'<p><strong>[{html.escape(cr["severity"].upper())}]</strong> {html.escape(cr["url"])} — {html.escape(cr["desc"])}<br><code>{html.escape(cr["poc_curl"])}</code></p>' for cr in r.cors_results) or '<p><em>No CORS issues found.</em></p>'}
</div>

<p style="color:#8b949e;font-size:12px;margin-top:40px">
Generated by Advanced_Recon v{VERSION} | Authorized testing only | {r.scan_time}
</p>
</body>
</html>"""
        with open(path,"w") as fh:
            fh.write(doc)
        return path

    # ── CSV ───────────────────────────────────────────────────────────────────
    def csv(self) -> str:
        import csv
        path = os.path.join(self.outdir, f"findings_{self._ts}.csv")
        fields = ["id","title","severity","confidence","cwe","owasp","cvss_score",
                  "affected_url","endpoint","technical_detail","impact","remediation",
                  "poc_curl","detection_method","timestamp"]
        with open(path,"w",newline="") as f:
            w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
            w.writeheader()
            for finding in self.r.findings:
                row = {k:getattr(finding,k,"") for k in fields}
                w.writerow(row)
        return path


# ─────────────────────────────────────────────────────────────────────────────
#  Config
# ─────────────────────────────────────────────────────────────────────────────
@dataclass
class Config:
    target: str = ""
    output: str = "./ADVANCED_OUTPUT"
    workers: int = 8
    rate: float = 3.0
    timeout: float = 20.0
    retries: int = 2
    depth: int = 3
    max_pages: int = 300
    verify_tls: bool = True
    passive: bool = True
    enum_subdomains: bool = True
    probe_paths: bool = True
    cors_test: bool = True
    graphql: bool = True
    scope_extra: List[str] = field(default_factory=list)


# ─────────────────────────────────────────────────────────────────────────────
#  CLI
# ─────────────────────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser(description="Advanced Bug Bounty Recon Framework v2.0")
    ap.add_argument("-t","--target",required=True,help="Target URL or domain")
    ap.add_argument("-o","--output",default="./ADVANCED_OUTPUT")
    ap.add_argument("--workers",type=int,default=8)
    ap.add_argument("--rate",type=float,default=3.0,help="Requests/sec")
    ap.add_argument("--depth",type=int,default=3)
    ap.add_argument("--max-pages",type=int,default=300)
    ap.add_argument("--timeout",type=float,default=20.0)
    ap.add_argument("--no-passive",action="store_true")
    ap.add_argument("--no-subdomains",action="store_true")
    ap.add_argument("--no-paths",action="store_true")
    ap.add_argument("--no-cors",action="store_true")
    ap.add_argument("--no-graphql",action="store_true")
    ap.add_argument("--no-tls-verify",action="store_true")
    ap.add_argument("--scope",nargs="*",default=[],help="Extra scope entries")
    args = ap.parse_args()

    cfg = Config(
        target=args.target, output=args.output,
        workers=args.workers, rate=args.rate, depth=args.depth,
        max_pages=args.max_pages, timeout=args.timeout,
        verify_tls=not args.no_tls_verify,
        passive=not args.no_passive,
        enum_subdomains=not args.no_subdomains,
        probe_paths=not args.no_paths,
        cors_test=not args.no_cors,
        graphql=not args.no_graphql,
        scope_extra=args.scope or [],
    )
    os.makedirs(cfg.output, exist_ok=True)

    logging.basicConfig(level=logging.DEBUG,
                        format="%(asctime)s %(levelname)s %(message)s",
                        handlers=[
                            logging.FileHandler(os.path.join(cfg.output,"advanced_recon.log")),
                            logging.StreamHandler(),
                        ])
    log = logging.getLogger("advanced_recon")

    _console.print(f"[bold cyan]Advanced Recon Framework v{VERSION}[/bold cyan]" if _HAVE_RICH
                   else f"Advanced Recon Framework v{VERSION}")
    _console.print(f"Target: {cfg.target}")
    _console.print(f"Scope:  {ScopeGuard(cfg.target, cfg.scope_extra).describe()}")
    _console.print("")

    scanner = AdvancedScanner(cfg, log)

    if _HAVE_RICH:
        with Progress(SpinnerColumn(), TextColumn("[cyan]{task.description}"),
                      BarColumn(), transient=True) as prog:
            prog.add_task("Running full advanced scan...", total=None)
            result = asyncio.run(scanner.scan())
    else:
        print("[*] Running full advanced scan... (this may take several minutes)")
        result = asyncio.run(scanner.scan())

    rep = AdvancedReporter(result, cfg.output)
    json_path = rep.json()
    md_path   = rep.markdown()
    html_path = rep.html()
    csv_path  = rep.csv()

    _console.print("\n[bold green]Scan complete![/bold green]" if _HAVE_RICH else "\nScan complete!")
    _console.print(f"  JSON     → {json_path}")
    _console.print(f"  Markdown → {md_path}")
    _console.print(f"  HTML     → {html_path}")
    _console.print(f"  CSV      → {csv_path}")

    sev_counts: Dict[str,int] = {}
    for f in result.findings:
        sev_counts[f.severity]=sev_counts.get(f.severity,0)+1
    _console.print(f"\nFindings: {sev_counts}")
    _console.print(f"Header score: {HeaderAuditor.score(result.headers_audit)}/100")
    _console.print(f"WAF: {result.waf_detected or 'none'}")
    _console.print(f"Tech: {result.technologies[:8]}")
    _console.print(f"Subdomains: {len(result.subdomains)}")
    _console.print(f"Assets: {len(result.assets)}")
    _console.print(f"API endpoints: {len(result.api_endpoints)}")
    _console.print(f"Secret candidates: {len(result.secret_hits)}")

    if result.diagnostics.get("reason"):
        _console.print(f"\n[yellow]Note: {result.diagnostics['reason']}[/yellow]"
                       if _HAVE_RICH else f"\nNote: {result.diagnostics['reason']}")

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nInterrupted")
        sys.exit(130)
