#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TITAN_HUNTER  -  Authorized Recon & Analysis Framework (Termux-friendly)
========================================================================

A single-file reconnaissance / analysis toolkit for AUTHORIZED bug-bounty
programs and legal security research only.

What this tool does:
    * In-scope async crawling and asset discovery
    * JavaScript intelligence (endpoints, secret-shaped strings, sourcemaps)
    * API & GraphQL endpoint mapping
    * Factual response analysis (headers, fingerprints, similarity)
    * Evidence capture (request/response metadata)
    * Sessions: save / resume / dedup / historical comparison
    * JSON + Markdown reporting

What this tool deliberately does NOT do:
    * Send exploit payloads, brute-force auth, or attack targets
    * Touch any host outside your declared scope
    * Fabricate vulnerabilities. It reports *observations* with confidence,
      and leaves the vulnerability judgement to you, the human.

USE ONLY against systems you own or are explicitly authorized to test
(a signed engagement, or a public bug-bounty program's stated scope).
Unauthorized scanning may be illegal. You are responsible for your use.

License: MIT. No warranty.
"""

from __future__ import annotations

import argparse
import asyncio
import dataclasses
import datetime as _dt
import hashlib
import json
import logging
import os
import re
import sys
import time
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple
from urllib.parse import urljoin, urlparse, urldefrag

# --------------------------------------------------------------------------- #
#  Optional dependencies with graceful fallbacks (Termux installs are flaky)
# --------------------------------------------------------------------------- #
try:
    import aiohttp  # type: ignore

    _HAVE_AIOHTTP = True
except Exception:  # pragma: no cover - environment dependent
    aiohttp = None  # type: ignore
    _HAVE_AIOHTTP = False

try:
    import requests  # type: ignore

    _HAVE_REQUESTS = True
except Exception:  # pragma: no cover
    requests = None  # type: ignore
    _HAVE_REQUESTS = False

if not _HAVE_AIOHTTP and not _HAVE_REQUESTS:
    import urllib.request as _urlreq
    import urllib.error as _urlerr

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.prompt import Prompt, IntPrompt, Confirm
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
    from rich import box

    _HAVE_RICH = True
    _console = Console()
except Exception:  # pragma: no cover

    _HAVE_RICH = False

    class _PlainConsole:
        """Minimal stand-in so the tool still runs without Rich."""

        def print(self, *args, **kwargs):
            text = " ".join(str(a) for a in args)
            text = re.sub(r"\[/?[a-zA-Z0-9 #_]+\]", "", text)  # strip markup
            print(text)

        def rule(self, title: str = ""):
            print("-" * 8, title, "-" * 8)

    _console = _PlainConsole()  # type: ignore


VERSION = "1.0.0"

# --------------------------------------------------------------------------- #
#  Constants
# --------------------------------------------------------------------------- #
USER_AGENT_PROFILES: Dict[str, str] = {
    "default": f"TITAN_HUNTER/{VERSION} (+authorized-recon)",
    "chrome": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "android": (
        "Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Mobile Safari/537.36"
    ),
    "googlebot": (
        "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
    ),
}

SECURITY_HEADERS = {
    "content-security-policy": ("CWE-693", "A05:2021 Security Misconfiguration"),
    "strict-transport-security": ("CWE-319", "A02:2021 Cryptographic Failures"),
    "x-frame-options": ("CWE-1021", "A05:2021 Security Misconfiguration"),
    "x-content-type-options": ("CWE-693", "A05:2021 Security Misconfiguration"),
    "referrer-policy": ("CWE-200", "A01:2021 Broken Access Control"),
}

# Signatures that mark a response as an upstream interstitial (content filter,
# WAF, CDN challenge, or censorship block) rather than the real target. The tool
# uses these to AVOID mistaking a block page for the target — this improves
# accuracy; it is not an evasion mechanism.
BLOCK_SERVER_HINTS = (
    "wirefilter", "netsweeper", "forcepoint", "bluecoat", "fortiguard",
    "squid", "sucuri", "incapsula", "imperva", "barracuda", "websense",
)
BLOCK_BODY_HINTS = (
    "access denied", "this site has been blocked", "site is blocked",
    "blocked by", "content filter", "web filter", "forbidden by policy",
    "saudi authority for intellectual property",
    "الهيئة السعودية للملكية الفكرية", "محجوب", "تم حجب", "غير متاح",
)
# Status codes that, combined with a small body or known markers, strongly
# suggest an interstitial. 451 = Unavailable For Legal Reasons (censorship).
BLOCK_STATUS = {403, 451, 503}

# Public OSINT sources the engine may query (these are NOT the target; results
# are filtered back through the scope guard before anything is crawled).
OSINT_HOSTS = {"crt.sh", "web.archive.org"}

# Common published API-doc locations (probed in-scope, normal GETs).
SCHEMA_PATHS = (
    "/swagger.json", "/swagger/v1/swagger.json", "/openapi.json",
    "/v2/api-docs", "/v3/api-docs", "/api-docs", "/api/swagger.json",
    "/.well-known/openapi.json", "/swagger/v1/swagger.yaml",
)

# Non-attacking Top-10 surface annotator heuristics. These produce a MANUAL
# testing checklist from passive signals — they do NOT send any payloads.
# Maps a lowercase parameter-name hint -> (owasp, cwe, what to check by hand).
PARAM_HINTS: List[Tuple[str, str, str, str]] = [
    ("id",       "A01 Broken Access Control", "CWE-639", "test for IDOR: change the id to another user's/object's value"),
    ("user",     "A01 Broken Access Control", "CWE-639", "test horizontal/vertical access by swapping the identifier"),
    ("account",  "A01 Broken Access Control", "CWE-639", "test cross-account access manually"),
    ("uid",      "A01 Broken Access Control", "CWE-639", "test IDOR manually"),
    ("role",     "A01 Broken Access Control", "CWE-269", "test privilege escalation via role tampering"),
    ("file",     "A03 Injection / Path",      "CWE-22",  "test path traversal / LFI by hand"),
    ("path",     "A03 Injection / Path",      "CWE-22",  "test path traversal by hand"),
    ("page",     "A03 Injection / Path",      "CWE-98",  "test file/template inclusion by hand"),
    ("template", "A03 Injection",             "CWE-1336","test server-side template injection by hand"),
    ("q",        "A03 Injection",             "CWE-79",  "test reflected XSS / search injection by hand"),
    ("search",   "A03 Injection",             "CWE-79",  "test reflected XSS by hand"),
    ("query",    "A03 Injection",             "CWE-89",  "review for SQL injection by hand"),
    ("sort",     "A03 Injection",             "CWE-89",  "review for SQL injection in ORDER BY by hand"),
    ("url",      "A10 SSRF",                  "CWE-918", "test SSRF / open redirect by hand"),
    ("redirect", "A01 / Open Redirect",       "CWE-601", "test open redirect by hand"),
    ("next",     "A01 / Open Redirect",       "CWE-601", "test open redirect by hand"),
    ("dest",     "A01 / Open Redirect",       "CWE-601", "test open redirect by hand"),
    ("callback", "A10 SSRF",                  "CWE-918", "test SSRF via callback by hand"),
    ("cmd",      "A03 Injection",             "CWE-78",  "review for OS command injection by hand"),
    ("debug",    "A05 Misconfiguration",      "CWE-489", "check whether debug mode leaks data"),
]

# Endpoint-ish strings inside JS / HTML.
ENDPOINT_RE = re.compile(
    r"""(?:["'`])(
        (?:/[A-Za-z0-9_\-./]{2,}) |
        (?:https?://[A-Za-z0-9_\-./?=&%:]+) |
        (?:[A-Za-z0-9_\-]+/[A-Za-z0-9_\-./]+\.(?:json|php|aspx?|jsp|do|action|api))
    )(?:["'`])""",
    re.VERBOSE,
)

API_HINT_RE = re.compile(
    r"""["'`](/(?:api|v\d+|rest|graphql|gql|internal|admin|service|services|rpc)
        [A-Za-z0-9_\-./]*)["'`]""",
    re.VERBOSE | re.IGNORECASE,
)

SOURCEMAP_RE = re.compile(r"//[#@]\s*sourceMappingURL=([^\s'\"]+)")

GRAPHQL_PATH_HINTS = ("/graphql", "/gql", "/api/graphql", "/query", "/v1/graphql")

# Secret-shaped patterns. These are *candidates*; every hit is validated
# by entropy + context before being surfaced, to cut false positives.
SECRET_PATTERNS: List[Tuple[str, str, str]] = [
    ("AWS Access Key ID", r"\bAKIA[0-9A-Z]{16}\b", "CWE-798"),
    ("AWS Secret (context)", r"(?i)aws_secret_access_key['\"\s:=]+([A-Za-z0-9/+]{40})", "CWE-798"),
    ("Google API Key", r"\bAIza[0-9A-Za-z\-_]{35}\b", "CWE-798"),
    ("Slack Token", r"\bxox[baprs]-[0-9A-Za-z\-]{10,}\b", "CWE-798"),
    ("Stripe Live Key", r"\bsk_live_[0-9A-Za-z]{24,}\b", "CWE-798"),
    ("GitHub Token", r"\bgh[pousr]_[0-9A-Za-z]{36}\b", "CWE-798"),
    ("Generic Bearer/JWT", r"\beyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\b", "CWE-522"),
    ("Private Key Block", r"-----BEGIN (?:RSA |EC |OPENSSH |DSA |PGP )?PRIVATE KEY-----", "CWE-321"),
    ("Firebase URL", r"https://[a-z0-9\-]+\.firebaseio\.com", "CWE-200"),
    ("Generic api_key assignment", r"(?i)(?:api[_-]?key|apikey|secret|token)['\"\s:=]{1,4}([A-Za-z0-9_\-]{20,})", "CWE-798"),
]

# Strings that, when they appear in a "secret" candidate, mark it as noise.
SECRET_FALSE_POSITIVE_HINTS = (
    "example", "your_", "xxxx", "placeholder", "dummy", "test_key",
    "0000000000", "1234567890", "abcdefg", "<", ">", "{{", "}}", "process.env",
)


def now_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def shannon_entropy(s: str) -> float:
    if not s:
        return 0.0
    from math import log2

    counts: Dict[str, int] = {}
    for ch in s:
        counts[ch] = counts.get(ch, 0) + 1
    n = len(s)
    return -sum((c / n) * log2(c / n) for c in counts.values())


def sha1(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8", "replace")).hexdigest()


# --------------------------------------------------------------------------- #
#  Configuration
# --------------------------------------------------------------------------- #
def _default_base_dir() -> str:
    # Use Android shared storage when present, else a local folder.
    for cand in ("/sdcard/TITAN", os.path.expanduser("~/TITAN")):
        parent = os.path.dirname(cand)
        if os.path.isdir(parent) or parent == os.path.expanduser("~"):
            return cand
    return os.path.abspath("./TITAN")


@dataclass
class Config:
    target: str = ""
    scope_file: str = ""
    base_dir: str = field(default_factory=_default_base_dir)
    workers: int = 8
    timeout: float = 15.0
    retries: int = 2
    rate_limit: float = 5.0  # max requests per second (token bucket)
    user_agent_profile: str = "default"
    crawl_depth: int = 2
    max_pages: int = 300
    report_formats: List[str] = field(default_factory=lambda: ["json", "markdown"])
    verify_tls: bool = True
    follow_subdomains: bool = True
    graphql_introspection: bool = False  # opt-in; standard recon, still off by default
    soft404_detection: bool = True       # baseline & discard catch-all 200s
    resume: bool = True                  # auto-resume from checkpoint if present
    checkpoint_every: int = 25           # flush crawl checkpoint every N pages
    passive_discovery: bool = True       # OSINT (CT logs + Wayback), no target hits
    schema_discovery: bool = True        # probe swagger/openapi docs (in-scope)
    anthropic_api_key: str = ""          # for AI report analysis (option 14/15)
    anthropic_model: str = "claude-opus-4-7"

    # Derived paths
    @property
    def reports_dir(self) -> str:
        return os.path.join(self.base_dir, "reports")

    @property
    def logs_dir(self) -> str:
        return os.path.join(self.base_dir, "logs")

    @property
    def cache_dir(self) -> str:
        return os.path.join(self.base_dir, "cache")

    @property
    def evidence_dir(self) -> str:
        return os.path.join(self.base_dir, "evidence")

    @property
    def sessions_dir(self) -> str:
        return os.path.join(self.base_dir, "sessions")

    def ensure_dirs(self) -> None:
        for d in (self.reports_dir, self.logs_dir, self.cache_dir,
                  self.evidence_dir, self.sessions_dir):
            os.makedirs(d, exist_ok=True)

    @property
    def user_agent(self) -> str:
        return USER_AGENT_PROFILES.get(self.user_agent_profile,
                                       USER_AGENT_PROFILES["default"])

    def save(self, path: str) -> None:
        with open(path, "w") as fh:
            json.dump(asdict(self), fh, indent=2)

    @classmethod
    def load(cls, path: str) -> "Config":
        with open(path) as fh:
            data = json.load(fh)
        valid = {f.name for f in dataclasses.fields(cls)}
        return cls(**{k: v for k, v in data.items() if k in valid})


# --------------------------------------------------------------------------- #
#  Scope guard  -  the heart of "authorized only"
# --------------------------------------------------------------------------- #
class ScopeGuard:
    """
    Enforces that the engine only ever requests in-scope hosts.

    Scope file format (one rule per line, '#' comments allowed):
        example.com            -> exact host
        *.example.com          -> any subdomain (and the apex)
        api.example.com
    If no scope file is given, scope is locked to the target host only.
    """

    def __init__(self, cfg: Config):
        self.exact: Set[str] = set()
        self.wildcards: Set[str] = set()
        self._load(cfg)

    def _load(self, cfg: Config) -> None:
        if cfg.scope_file and os.path.isfile(cfg.scope_file):
            with open(cfg.scope_file) as fh:
                for raw in fh:
                    line = raw.strip().lower()
                    if not line or line.startswith("#"):
                        continue
                    if line.startswith("*."):
                        self.wildcards.add(line[2:])
                    else:
                        host = urlparse(line if "://" in line else "//" + line).hostname or line
                        self.exact.add(host)
        # Always include the target host.
        t = urlparse(cfg.target if "://" in cfg.target else "//" + cfg.target).hostname
        if t:
            self.exact.add(t.lower())
            if cfg.follow_subdomains:
                # allow subdomains of the apex by default
                parts = t.lower().split(".")
                if len(parts) >= 2:
                    self.wildcards.add(".".join(parts[-2:]))

    def in_scope(self, url: str) -> bool:
        host = (urlparse(url).hostname or "").lower()
        if not host:
            return False
        if host in self.exact:
            return True
        for wc in self.wildcards:
            if host == wc or host.endswith("." + wc):
                return True
        return False

    def describe(self) -> str:
        bits = sorted(self.exact) + [f"*.{w}" for w in sorted(self.wildcards)]
        return ", ".join(bits) if bits else "(empty - nothing allowed)"


# --------------------------------------------------------------------------- #
#  Rate limiter (async token bucket)
# --------------------------------------------------------------------------- #
class RateLimiter:
    def __init__(self, rate_per_sec: float):
        self.rate = max(0.1, rate_per_sec)
        self._tokens = self.rate
        self._last = time.monotonic()
        self._lock = asyncio.Lock()

    def slow_down(self, factor: float = 0.5, floor: float = 0.3) -> float:
        """Reduce throughput when the server signals stress (429) or the network
        resets connections. Returns the new rate. Polite-scanning behavior."""
        self.rate = max(floor, self.rate * factor)
        self._tokens = min(self._tokens, self.rate)
        return self.rate

    async def acquire(self) -> None:
        async with self._lock:
            while True:
                now = time.monotonic()
                self._tokens = min(self.rate, self._tokens + (now - self._last) * self.rate)
                self._last = now
                if self._tokens >= 1:
                    self._tokens -= 1
                    return
                await asyncio.sleep((1 - self._tokens) / self.rate)


# --------------------------------------------------------------------------- #
#  HTTP response container + engine
# --------------------------------------------------------------------------- #
@dataclass
class HttpResult:
    url: str
    status: int
    headers: Dict[str, str]
    body: str
    elapsed_ms: float
    error: Optional[str] = None
    final_url: Optional[str] = None

    @property
    def ok(self) -> bool:
        return self.error is None and self.status > 0


class HttpEngine:
    """
    Async HTTP with aiohttp when available; otherwise falls back to running
    requests/urllib in a thread pool. Rate-limited, retried, scope-checked.
    Every call records evidence.
    """

    def __init__(self, cfg: Config, scope: ScopeGuard, evidence: "EvidenceStore",
                 logger: logging.Logger):
        self.cfg = cfg
        self.scope = scope
        self.evidence = evidence
        self.log = logger
        self.limiter = RateLimiter(cfg.rate_limit)
        self.sem = asyncio.Semaphore(cfg.workers)
        self._session = None  # aiohttp session
        # When a TLS verification error is hit, we self-heal to insecure for the
        # rest of the run (recon targets often have broken/expired certs, and
        # Termux's CA bundle is frequently incomplete). A visible warning is
        # emitted and recorded so the operator knows.
        self._insecure = not cfg.verify_tls
        self._tls_warned = False

    async def __aenter__(self):
        if _HAVE_AIOHTTP:
            timeout = aiohttp.ClientTimeout(total=self.cfg.timeout,
                                            connect=min(self.cfg.timeout, 10))
            connector = aiohttp.TCPConnector(limit=self.cfg.workers, ssl=False
                                             if self._insecure else None)
            self._session = aiohttp.ClientSession(timeout=timeout, connector=connector)
        return self

    @staticmethod
    def _is_tls_error(exc: Exception) -> bool:
        s = (str(exc) + type(exc).__name__).lower()
        return any(k in s for k in ("ssl", "certificate", "cert_", "tls",
                                    "hostname mismatch", "self-signed"))

    async def __aexit__(self, *exc):
        if self._session is not None:
            await self._session.close()

    async def fetch(self, url: str, method: str = "GET",
                    headers: Optional[Dict[str, str]] = None,
                    data: Optional[str] = None,
                    record: bool = True, external: bool = False) -> HttpResult:
        url, _ = urldefrag(url)
        host = (urlparse(url).hostname or "").lower()
        # OSINT sources are not the target; only permitted via external=True and
        # only for the known public-index allowlist. Everything else must be in
        # the authorized scope. Results from OSINT are re-filtered before use.
        allowed = self.scope.in_scope(url) or (external and host in OSINT_HOSTS)
        if not allowed:
            self.log.warning("BLOCKED out-of-scope request: %s", url)
            return HttpResult(url, 0, {}, "", 0.0, error="out-of-scope")

        hdrs = {"User-Agent": self.cfg.user_agent, "Accept": "*/*"}
        if headers:
            hdrs.update(headers)

        last_err = None
        for attempt in range(self.cfg.retries + 1):
            await self.limiter.acquire()
            async with self.sem:
                try:
                    if _HAVE_AIOHTTP:
                        res = await self._fetch_aiohttp(url, method, hdrs, data)
                    else:
                        res = await asyncio.to_thread(self._fetch_sync, url, method, hdrs, data)
                    if record:
                        self.evidence.record(res, method, hdrs, data)
                    if res.status == 429:  # server asking us to ease off
                        new = self.limiter.slow_down()
                        self.log.warning("429 from %s — throttling to %.2f req/s",
                                         url, new)
                    return res
                except Exception as exc:  # network flap, timeout, dns, etc.
                    last_err = f"{type(exc).__name__}: {exc}"
                    if "reset" in str(exc).lower() or "ConnectionReset" in type(exc).__name__:
                        new = self.limiter.slow_down(0.7)
                        self.log.debug("connection reset — throttling to %.2f req/s", new)
                    if self._is_tls_error(exc) and not self._insecure:
                        # Rebuild as insecure and retry immediately (don't burn
                        # an attempt on a cert problem we can work around).
                        self._insecure = True
                        if not self._tls_warned:
                            self.log.warning("TLS verification failed for %s — "
                                             "continuing without verification.", url)
                            self._tls_warned = True
                        if _HAVE_AIOHTTP and self._session is not None:
                            await self._session.close()
                            timeout = aiohttp.ClientTimeout(total=self.cfg.timeout,
                                                            connect=min(self.cfg.timeout, 10))
                            self._session = aiohttp.ClientSession(
                                timeout=timeout,
                                connector=aiohttp.TCPConnector(limit=self.cfg.workers, ssl=False))
                        continue
                    self.log.debug("attempt %d failed for %s: %s", attempt + 1, url, exc)
                    await asyncio.sleep(min(2 ** attempt, 6))
        res = HttpResult(url, 0, {}, "", 0.0, error=last_err or "unknown error")
        if record:
            self.evidence.record(res, method, hdrs, data)
        return res

    async def _fetch_aiohttp(self, url, method, hdrs, data) -> HttpResult:
        start = time.monotonic()
        async with self._session.request(method, url, headers=hdrs, data=data,
                                          allow_redirects=True,
                                          ssl=False if self._insecure else None) as resp:
            body = await resp.text(errors="replace")
            elapsed = (time.monotonic() - start) * 1000
            return HttpResult(
                url=url, status=resp.status,
                headers={k.lower(): v for k, v in resp.headers.items()},
                body=body, elapsed_ms=elapsed, final_url=str(resp.url),
            )

    def _fetch_sync(self, url, method, hdrs, data) -> HttpResult:
        start = time.monotonic()
        if _HAVE_REQUESTS:
            r = requests.request(method, url, headers=hdrs,
                                 data=data, timeout=self.cfg.timeout,
                                 verify=not self._insecure, allow_redirects=True)
            elapsed = (time.monotonic() - start) * 1000
            return HttpResult(url, r.status_code,
                              {k.lower(): v for k, v in r.headers.items()},
                              r.text, elapsed, final_url=r.url)
        # pure-stdlib fallback
        import ssl as _ssl
        ctx = None
        if self._insecure:
            ctx = _ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = _ssl.CERT_NONE
        req = _urlreq.Request(url, data=(data.encode() if data else None),
                              headers=hdrs, method=method)
        try:
            with _urlreq.urlopen(req, timeout=self.cfg.timeout, context=ctx) as resp:  # nosec - scope-checked
                body = resp.read().decode("utf-8", "replace")
                elapsed = (time.monotonic() - start) * 1000
                return HttpResult(url, resp.status,
                                  {k.lower(): v for k, v in resp.headers.items()},
                                  body, elapsed, final_url=resp.geturl())
        except _urlerr.HTTPError as e:  # still a valid response we want to see
            body = e.read().decode("utf-8", "replace") if hasattr(e, "read") else ""
            elapsed = (time.monotonic() - start) * 1000
            return HttpResult(url, e.code, {k.lower(): v for k, v in e.headers.items()},
                              body, elapsed)


# --------------------------------------------------------------------------- #
#  Evidence store
# --------------------------------------------------------------------------- #
@dataclass
class EvidenceItem:
    id: str
    timestamp: str
    url: str
    method: str
    request_headers: Dict[str, str]
    request_body: Optional[str]
    status: int
    response_headers: Dict[str, str]
    response_snippet: str
    elapsed_ms: float
    error: Optional[str]


class EvidenceStore:
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.items: List[EvidenceItem] = []

    def record(self, res: HttpResult, method: str,
               req_headers: Dict[str, str], req_body: Optional[str]) -> EvidenceItem:
        snippet = res.body[:1500]
        item = EvidenceItem(
            id=sha1(res.url + method + now_iso())[:12],
            timestamp=now_iso(), url=res.url, method=method,
            request_headers=req_headers, request_body=req_body,
            status=res.status, response_headers=res.headers,
            response_snippet=snippet, elapsed_ms=round(res.elapsed_ms, 1),
            error=res.error,
        )
        self.items.append(item)
        return item

    def dump(self) -> List[Dict[str, Any]]:
        return [asdict(i) for i in self.items]


# --------------------------------------------------------------------------- #
#  Findings  (FACTS with confidence, not asserted vulnerabilities)
# --------------------------------------------------------------------------- #
@dataclass
class Finding:
    title: str
    severity: str            # informational|low|medium|high  (conservative)
    confidence: str          # low|medium|high
    affected_url: str
    endpoint: str
    detection_logic: str
    validation_logic: str
    request_sample: str
    response_indicators: str
    reproduction: List[str]
    evidence_id: str
    technical_explanation: str
    security_impact: str
    remediation: str
    cwe: str
    owasp: str
    group_scope: str = "url"   # "host" collapses the same issue across URLs
    affected_urls: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=now_iso)

    def dedup_key(self) -> str:
        if self.group_scope == "host":
            host = urlparse(self.affected_url).hostname or ""
            return sha1(f"{self.title}|{host}")
        return sha1(f"{self.title}|{self.affected_url}|{self.endpoint}")


class FindingsManager:
    def __init__(self):
        self._by_key: Dict[str, Finding] = {}

    def add(self, finding: Finding) -> bool:
        if not finding.affected_urls:
            finding.affected_urls = [finding.affected_url]
        key = finding.dedup_key()
        existing = self._by_key.get(key)
        if existing:
            # Same issue, another URL: merge instead of duplicating.
            for u in finding.affected_urls:
                if u not in existing.affected_urls:
                    existing.affected_urls.append(u)
            return False
        self._by_key[key] = finding
        return True

    @property
    def findings(self) -> List[Finding]:
        order = {"high": 0, "medium": 1, "low": 2, "informational": 3}
        return sorted(self._by_key.values(),
                      key=lambda f: order.get(f.severity, 9))

    def severity_summary(self) -> Dict[str, int]:
        out: Dict[str, int] = {}
        for f in self._by_key.values():
            out[f.severity] = out.get(f.severity, 0) + 1
        return out


# --------------------------------------------------------------------------- #
#  Analyzers
# --------------------------------------------------------------------------- #
class JSAnalyzer:
    """Pull endpoints, sourcemap refs, and secret-shaped strings out of JS.

    Endpoint extraction uses (a) generic string scanning and (b) call-site aware
    patterns (fetch/axios/XHR/jQuery/route tables) which catch URLs that naive
    string scanning misses and are higher-confidence. A real AST backend
    (acorn/esprima/tree-sitter) can be slotted into `analyze_ast` when available;
    we fall back to call-site regex otherwise.
    """

    # Call-site patterns: the captured group is a URL/path argument.
    CALLSITE_RES = [
        re.compile(r"""fetch\(\s*["'`]([^"'`]+)["'`]"""),
        re.compile(r"""axios\.(?:get|post|put|delete|patch|head)\(\s*["'`]([^"'`]+)["'`]""", re.I),
        re.compile(r"""axios\(\s*\{[^}]*?url\s*:\s*["'`]([^"'`]+)["'`]""", re.I | re.S),
        re.compile(r"""\.open\(\s*["'][A-Z]+["']\s*,\s*["'`]([^"'`]+)["'`]"""),
        re.compile(r"""\$\.(?:get|post|ajax|getJSON)\(\s*["'`]([^"'`]+)["'`]""", re.I),
        re.compile(r"""url\s*:\s*["'`](/[^"'`]+)["'`]"""),
        re.compile(r"""(?:path|route|endpoint)\s*:\s*["'`](/[^"'`]+)["'`]""", re.I),
        re.compile(r"""["'`](/(?:api|v\d+|graphql|rest|internal)/[^"'`\s]+)["'`]""", re.I),
    ]

    def __init__(self):
        self.endpoints: Set[str] = set()
        self.api_refs: Set[str] = set()
        self.sourcemaps: Set[str] = set()
        self.secret_hits: List[Dict[str, str]] = []
        self.callsites: Set[str] = set()      # higher-confidence, from call sites
        self.recovered_sources: List[str] = []  # original files via sourcemaps

    def analyze(self, base_url: str, body: str) -> None:
        for m in ENDPOINT_RE.finditer(body):
            cand = m.group(1)
            if 2 < len(cand) < 256:
                self.endpoints.add(self._normalize(base_url, cand))
        for m in API_HINT_RE.finditer(body):
            self.api_refs.add(self._normalize(base_url, m.group(1)))
        for m in SOURCEMAP_RE.finditer(body):
            self.sourcemaps.add(self._normalize(base_url, m.group(1)))
        # Call-site aware extraction (higher confidence than raw strings).
        for rx in self.CALLSITE_RES:
            for m in rx.finditer(body):
                u = m.group(1)
                if 1 < len(u) < 256 and not u.startswith(("data:", "blob:", "#")):
                    full = self._normalize(base_url, u)
                    self.callsites.add(full)
                    self.api_refs.add(full)
        self._scan_secrets(base_url, body)

    def _scan_secrets(self, base_url: str, body: str) -> None:
        for name, pattern, cwe in SECRET_PATTERNS:
            for m in re.finditer(pattern, body):
                raw = m.group(0)
                value = m.group(1) if m.groups() else raw
                if self._is_noise(value):
                    continue
                # Validate: candidates that are clearly low-entropy or template
                # placeholders are dropped to cut false positives.
                ent = shannon_entropy(value)
                confidence = "high" if ent >= 3.5 else "medium" if ent >= 2.8 else "low"
                if confidence == "low" and name.startswith("Generic"):
                    continue
                self.secret_hits.append({
                    "type": name, "cwe": cwe, "source": base_url,
                    "match_preview": raw[:8] + "…(redacted)",
                    "entropy": f"{ent:.2f}", "confidence": confidence,
                })

    @staticmethod
    def _is_noise(value: str) -> bool:
        low = value.lower()
        return any(h in low for h in SECRET_FALSE_POSITIVE_HINTS)

    @staticmethod
    def _normalize(base_url: str, ref: str) -> str:
        if ref.startswith("http"):
            return ref
        return urljoin(base_url, ref)


class InterstitialDetector:
    """
    Decides whether an HTTP response is an upstream interstitial (content
    filter / WAF / CDN challenge / censorship block) rather than the real
    target. Returns (is_block, reason). Conservative: needs a real signal.
    This raises accuracy (don't crawl a block page as if it were the site);
    it is NOT an evasion mechanism.
    """

    @staticmethod
    def inspect(res: "HttpResult") -> Tuple[bool, str]:
        server = res.headers.get("server", "").lower()
        for hint in BLOCK_SERVER_HINTS:
            if hint in server:
                return True, f"filter/WAF server header: '{res.headers.get('server')}'"
        body_l = res.body[:4000].lower()
        for hint in BLOCK_BODY_HINTS:
            if hint.lower() in body_l:
                return True, f"block-page marker in body: '{hint}'"
        if res.status == 451:
            return True, "HTTP 451 Unavailable For Legal Reasons (censorship)"
        if res.status in BLOCK_STATUS and res.body:
            has_links = bool(re.search(r'href\s*=\s*["\']https?://', res.body))
            if len(res.body) < 9000 and not has_links and "<html" in body_l:
                return True, f"interstitial shape: status {res.status}, small page, no links"
        return False, ""


class HtmlLinkExtractor:
    LINK_RE = re.compile(r'(?:href|src|action)\s*=\s*["\']([^"\']+)["\']', re.I)
    SCRIPT_RE = re.compile(r'<script[^>]+src\s*=\s*["\']([^"\']+)["\']', re.I)
    FORM_RE = re.compile(r'<form\b([^>]*)>(.*?)</form>', re.I | re.S)
    INPUT_RE = re.compile(r'<(input|select|textarea)\b([^>]*)>', re.I)
    ATTR_RE = re.compile(r'(\w[\w-]*)\s*=\s*["\']([^"\']*)["\']')

    @classmethod
    def links(cls, base_url: str, body: str) -> Tuple[Set[str], Set[str]]:
        links, scripts = set(), set()
        for m in cls.LINK_RE.finditer(body):
            links.add(urljoin(base_url, m.group(1)))
        for m in cls.SCRIPT_RE.finditer(body):
            scripts.add(urljoin(base_url, m.group(1)))
        return links, scripts

    @classmethod
    def forms(cls, base_url: str, body: str) -> List[Dict[str, Any]]:
        """Catalogue HTML forms: action, method, and input fields. This is
        attack-surface *mapping* — what a tester reviews by hand; the tool does
        not submit anything."""
        out: List[Dict[str, Any]] = []
        for fm in cls.FORM_RE.finditer(body):
            attrs = dict(cls.ATTR_RE.findall(fm.group(1)))
            inputs = []
            for im in cls.INPUT_RE.finditer(fm.group(2)):
                iattrs = dict(cls.ATTR_RE.findall(im.group(2)))
                name = iattrs.get("name") or iattrs.get("id")
                if name:
                    inputs.append({"name": name,
                                   "type": iattrs.get("type", im.group(1).lower())})
            out.append({
                "action": urljoin(base_url, attrs.get("action", "")) or base_url,
                "method": (attrs.get("method") or "GET").upper(),
                "source_page": base_url,
                "inputs": inputs,
            })
        return out


class SmartAnalyzer:
    """
    Factual response analysis: header hygiene, fingerprints, similarity.
    Produces conservative findings only for verifiable facts.
    """

    TECH_SIGNATURES = {
        "server": "Server header",
        "x-powered-by": "X-Powered-By header",
        "x-aspnet-version": "ASP.NET",
        "x-generator": "Generator",
    }

    def __init__(self, findings: FindingsManager):
        self.findings = findings
        self.technologies: Set[str] = set()
        self._fingerprints: Dict[str, str] = {}

    def detect_tech(self, res: HttpResult) -> None:
        for h, label in self.TECH_SIGNATURES.items():
            if h in res.headers:
                self.technologies.add(f"{label}: {res.headers[h]}")
        body = res.body.lower()
        for marker, tech in (("wp-content", "WordPress"), ("/_next/", "Next.js"),
                             ("react", "React"), ("ng-version", "Angular"),
                             ("__nuxt", "Nuxt")):
            if marker in body:
                self.technologies.add(tech)

    def check_security_headers(self, res: HttpResult, evidence_id: str) -> None:
        if not res.ok or res.status >= 400:
            return
        missing = [h for h in SECURITY_HEADERS if h not in res.headers]
        for h in missing:
            cwe, owasp = SECURITY_HEADERS[h]
            self.findings.add(Finding(
                title=f"Missing security header: {h}",
                severity="low" if h in ("content-security-policy",
                                         "strict-transport-security") else "informational",
                confidence="high",
                affected_url=res.url, endpoint=urlparse(res.url).path or "/",
                detection_logic=f"Header '{h}' absent from a 2xx/3xx response.",
                validation_logic="Direct observation of response headers; no inference.",
                request_sample=f"GET {res.url}",
                response_indicators=f"status={res.status}; '{h}' not present",
                reproduction=[f"curl -sI '{res.url}'",
                              f"Observe that '{h}' is not returned."],
                evidence_id=evidence_id,
                technical_explanation=(
                    f"The response omits the {h} header, which browsers use to "
                    "enforce a corresponding protection."),
                security_impact=(
                    "Reduces defense-in-depth. Impact depends on the app; verify "
                    "manually whether it is exploitable in context."),
                remediation=f"Set the '{h}' header at the server/edge.",
                cwe=cwe, owasp=owasp, group_scope="host",
            ))

    # Headers that disclose exact software versions (info leak, eases targeting).
    VERSION_HEADERS = ("server", "x-powered-by", "x-aspnet-version",
                       "x-aspnetmvc-version", "x-generator")
    _VER_RE = re.compile(r"\d+\.\d+")

    def check_version_disclosure(self, res: HttpResult, evidence_id: str) -> None:
        if not res.ok:
            return
        disclosed = {h: res.headers[h] for h in self.VERSION_HEADERS
                     if h in res.headers and self._VER_RE.search(res.headers[h])}
        if not disclosed:
            return
        detail = "; ".join(f"{k}: {v}" for k, v in disclosed.items())
        self.findings.add(Finding(
            title="Software version disclosure in response headers",
            severity="informational", confidence="high",
            affected_url=res.url, endpoint=urlparse(res.url).path or "/",
            detection_logic=f"Version-bearing headers present: {detail}",
            validation_logic="Direct observation of response headers; no inference.",
            request_sample=f"HEAD {res.url}",
            response_indicators=detail,
            reproduction=[f"curl -sI '{res.url}'", "Read the Server / X-Powered-By "
                          "/ X-AspNet-Version headers."],
            evidence_id=evidence_id,
            technical_explanation=(
                "The server advertises exact component versions. This does not by "
                "itself grant access, but it lets an attacker map the stack to known "
                "CVEs faster. Verify whether the disclosed versions are EOL/vulnerable."),
            security_impact="Information disclosure; accelerates targeted research.",
            remediation="Suppress or genericize version banners at the server/edge.",
            cwe="CWE-200", owasp="A05:2021 Security Misconfiguration",
            group_scope="host",
        ))

    def similarity(self, a: str, b: str) -> float:
        """Cheap token Jaccard similarity for response diffing."""
        ta = set(re.findall(r"\w+", a.lower()))
        tb = set(re.findall(r"\w+", b.lower()))
        if not ta and not tb:
            return 1.0
        inter = len(ta & tb)
        union = len(ta | tb) or 1
        return inter / union


class PassiveRecon:
    """
    OSINT asset discovery from PUBLIC indexes (Certificate Transparency via
    crt.sh, and the Wayback Machine). This never touches the target — it queries
    third-party archives, then the caller filters results back through the scope
    guard. Useful for widening the map and works even when the target is
    unreachable from the current network.
    """

    def __init__(self, cfg: Config, logger: logging.Logger):
        self.cfg = cfg
        self.log = logger

    def _apex(self) -> str:
        host = urlparse(self.cfg.target if "://" in self.cfg.target
                        else "//" + self.cfg.target).hostname or self.cfg.target
        parts = host.split(".")
        return ".".join(parts[-2:]) if len(parts) >= 2 else host

    @staticmethod
    def parse_crtsh(body: str) -> Set[str]:
        hosts: Set[str] = set()
        try:
            for row in json.loads(body):
                for name in str(row.get("name_value", "")).splitlines():
                    name = name.strip().lstrip("*.").lower()
                    if name and "@" not in name:
                        hosts.add(name)
        except (json.JSONDecodeError, TypeError, AttributeError):
            pass
        return hosts

    @staticmethod
    def parse_wayback(body: str) -> Set[str]:
        urls: Set[str] = set()
        try:
            rows = json.loads(body)
            for row in rows[1:] if rows and isinstance(rows[0], list) else rows:
                if isinstance(row, list) and row:
                    urls.add(row[0])
                elif isinstance(row, str):
                    urls.add(row)
        except (json.JSONDecodeError, TypeError, IndexError):
            pass
        return urls

    async def run(self, eng: "HttpEngine") -> Dict[str, Set[str]]:
        apex = self._apex()
        out: Dict[str, Set[str]] = {"hosts": set(), "urls": set()}
        if not self.cfg.passive_discovery:
            return out
        crt = await eng.fetch(f"https://crt.sh/?q=%25.{apex}&output=json",
                              external=True)
        if crt.ok and crt.body:
            out["hosts"] |= self.parse_crtsh(crt.body)
        wb = await eng.fetch(
            "https://web.archive.org/cdx/search/cdx?"
            f"url=*.{apex}/*&output=json&fl=original&collapse=urlkey&limit=2000",
            external=True)
        if wb.ok and wb.body:
            out["urls"] |= self.parse_wayback(wb.body)
        self.log.info("Passive OSINT: %d hosts, %d archived URLs",
                      len(out["hosts"]), len(out["urls"]))
        return out


class SchemaDiscovery:
    """Probe well-known published API-doc locations (in-scope, normal GETs) and
    extract the documented endpoint list. This reads API documentation; it does
    not call or attack the documented endpoints."""

    def __init__(self, logger: logging.Logger):
        self.log = logger
        self.schemas: List[Dict[str, Any]] = []
        self.endpoints: Set[str] = set()

    async def run(self, eng: "HttpEngine", base: str) -> None:
        p = urlparse(base)
        root = f"{p.scheme}://{p.netloc}"
        for path in SCHEMA_PATHS:
            res = await eng.fetch(root + path)
            if not res.ok or res.status != 200:
                continue
            body = res.body.lstrip()
            if not (body.startswith("{") and
                    ("swagger" in res.body[:200].lower()
                     or "openapi" in res.body[:200].lower()
                     or '"paths"' in res.body[:2000])):
                continue
            try:
                doc = json.loads(res.body)
            except json.JSONDecodeError:
                continue
            paths = list((doc.get("paths") or {}).keys())
            self.schemas.append({"url": root + path,
                                 "type": "openapi" if "openapi" in doc else "swagger",
                                 "path_count": len(paths)})
            for pth in paths:
                self.endpoints.add(urljoin(root, pth))
            self.log.info("Schema found: %s (%d paths)", path, len(paths))


class Top10Annotator:
    """
    Turns the discovered map into a MANUAL testing checklist mapped to the OWASP
    Top 10. It flags WHERE each category could apply and WHAT to verify by hand.
    It sends no payloads and makes no requests — it only annotates passive
    signals so the operator's manual testing is organized and in-scope.
    """

    @staticmethod
    def build(param_map: Dict[str, Dict[str, List[str]]],
              forms: List[Dict[str, Any]],
              findings: List["Finding"],
              param_types: Optional[Dict[str, Dict[str, str]]] = None,
              endpoint_types: Optional[Dict[str, str]] = None) -> List[Dict[str, str]]:
        checklist: List[Dict[str, str]] = []
        param_types = param_types or {}
        endpoint_types = endpoint_types or {}

        for endpoint, params in param_map.items():
            ptypes = param_types.get(endpoint, {})
            ep_type = endpoint_types.get(endpoint, "")
            for name in params:
                low = name.lower()
                ptype = ptypes.get(name, "")
                ep_note = f"endpoint={ep_type or '?'}"
                if ptype and ptype != "unknown":
                    ep_note += f", value type={ptype}"
                # 1) name-based hints
                matched = False
                for hint, owasp, cwe, action in PARAM_HINTS:
                    if hint == low or hint in low:
                        checklist.append({
                            "surface": f"{endpoint} ? {name}",
                            "owasp": owasp, "cwe": cwe,
                            "manual_check": action,
                            "note": f"flagged from param name; {ep_note}",
                        })
                        matched = True
                        break
                # 2) value-type hints when name alone didn't trigger
                if not matched:
                    if ptype == "url":
                        checklist.append({
                            "surface": f"{endpoint} ? {name}",
                            "owasp": "A10 SSRF / Open Redirect", "cwe": "CWE-918",
                            "manual_check": "value looks like a URL — test SSRF / "
                                            "open redirect by hand",
                            "note": f"flagged from value type=url; {ep_note}",
                        })
                    elif ptype == "filename":
                        checklist.append({
                            "surface": f"{endpoint} ? {name}",
                            "owasp": "A03 Path / LFI", "cwe": "CWE-22",
                            "manual_check": "value looks like a filename — test "
                                            "path traversal / LFI by hand",
                            "note": f"flagged from value type=filename; {ep_note}",
                        })
                    elif ptype == "numeric-id":
                        checklist.append({
                            "surface": f"{endpoint} ? {name}",
                            "owasp": "A01 Broken Access Control", "cwe": "CWE-639",
                            "manual_check": "numeric identifier — test IDOR by "
                                            "swapping values",
                            "note": f"flagged from value type=numeric-id; {ep_note}",
                        })

        for fm in forms:
            field_names = " ".join(i["name"].lower() for i in fm["inputs"])
            has_pw = "pass" in field_names
            has_csrf = any(t in field_names for t in
                           ("csrf", "token", "__requestverificationtoken", "authenticity"))
            if has_pw:
                checklist.append({
                    "surface": f"{fm['method']} {fm['action']} (login/credential form)",
                    "owasp": "A07 Identification & Auth Failures", "cwe": "CWE-287",
                    "manual_check": "review auth: rate limiting, lockout, password policy, "
                                    "credential handling — by hand",
                    "note": "password field present",
                })
            if fm["method"] == "POST" and not has_csrf:
                checklist.append({
                    "surface": f"{fm['method']} {fm['action']}",
                    "owasp": "A01 Broken Access Control (CSRF)", "cwe": "CWE-352",
                    "manual_check": "check for anti-CSRF token / SameSite cookies by hand",
                    "note": "POST form with no obvious CSRF field",
                })

        for f in findings:
            if "version disclosure" in f.title.lower():
                checklist.append({
                    "surface": f.affected_url,
                    "owasp": "A06 Vulnerable & Outdated Components", "cwe": "CWE-1104",
                    "manual_check": "verify disclosed versions against known CVEs",
                    "note": "from version-disclosure finding",
                })
        return checklist


class EndpointClassifier:
    """Classify a response into a coarse type so the map distinguishes pages,
    JSON APIs, static files, redirects, auth pages, uploads, etc."""

    @staticmethod
    def classify(url: str, status: int, ctype: str, body: str) -> str:
        ct = ctype.lower()
        path = urlparse(url).path.lower()
        if 300 <= status < 400:
            return "redirect"
        if "json" in ct or path.endswith(".json"):
            return "json-api"
        if "/api/" in path or re.search(r"/v\d+/", path) or "graphql" in path:
            return "api"
        if path.endswith((".js", ".css", ".png", ".jpg", ".svg", ".woff", ".ico")):
            return "static"
        if any(k in path for k in ("login", "signin", "auth", "signup", "register")):
            return "auth"
        if any(k in path for k in ("upload", "import", "file")):
            return "upload"
        if "html" in ct:
            return "page"
        return "other"

    @staticmethod
    def infer_param_type(values: List[str]) -> str:
        if not values:
            return "unknown"
        v = values[0]
        if re.fullmatch(r"\d+", v):
            return "numeric-id"
        if re.fullmatch(r"[0-9a-fA-F-]{32,36}", v):
            return "uuid/hash"
        if re.match(r"https?://", v):
            return "url"
        if "@" in v and "." in v:
            return "email"
        if v.lower() in ("true", "false", "0", "1"):
            return "boolean"
        if re.search(r"\.(html?|php|aspx?|jsp)$", v):
            return "filename"
        return "string"


class ResponseClusterer:
    """Greedy similarity clustering over collected responses. Surfaces outliers
    (singletons) — endpoints that behave differently from the templated bulk,
    which are usually the interesting ones to review by hand."""

    def __init__(self, similarity_fn):
        self._sim = similarity_fn
        self.clusters: List[Dict[str, Any]] = []  # {rep_body, members:[url], size}

    def add(self, url: str, status: int, body: str) -> None:
        snippet = body[:2000]
        for c in self.clusters:
            if c["status"] == status and self._sim(c["rep_body"], snippet) >= 0.80:
                c["members"].append(url)
                c["size"] += 1
                return
        self.clusters.append({"status": status, "rep_body": snippet,
                              "members": [url], "size": 1})

    def outliers(self) -> List[str]:
        if len(self.clusters) < 2:
            return []
        return [c["members"][0] for c in self.clusters if c["size"] == 1]

    def summary(self) -> List[Dict[str, Any]]:
        return [{"status": c["status"], "size": c["size"],
                 "example": c["members"][0]} for c in
                sorted(self.clusters, key=lambda x: -x["size"])]


class JobCheckpoint:
    """
    Crash-safe, resumable crawl state. Writes atomically so an interrupted scan
    (mobile network drop, app killed) can pick up where it left off instead of
    starting over. Stored as JSON under the sessions dir.
    """

    def __init__(self, cfg: Config):
        slug = re.sub(r"[^a-zA-Z0-9_.-]", "_",
                      urlparse(cfg.target if "://" in cfg.target
                               else "//" + cfg.target).hostname or "target")
        self.path = os.path.join(cfg.sessions_dir, f"{slug}.checkpoint.json")

    def save(self, queue, seen, assets, js_files) -> None:
        data = {"saved_at": now_iso(),
                "queue": [list(x) for x in queue],
                "seen": sorted(seen),
                "discovered_assets": sorted(assets),
                "javascript_files": sorted(js_files)}
        tmp = self.path + ".tmp"
        try:
            with open(tmp, "w") as fh:
                json.dump(data, fh)
            os.replace(tmp, self.path)  # atomic on POSIX (incl. Termux)
        except OSError:
            pass

    def load(self) -> Optional[Dict[str, Any]]:
        if not os.path.isfile(self.path):
            return None
        try:
            with open(self.path) as fh:
                return json.load(fh)
        except (OSError, json.JSONDecodeError):
            return None

    def clear(self) -> None:
        for p in (self.path, self.path + ".tmp"):
            try:
                os.remove(p)
            except OSError:
                pass


# --------------------------------------------------------------------------- #
#  Scanner orchestration
# --------------------------------------------------------------------------- #
class Scanner:
    def __init__(self, cfg: Config, logger: logging.Logger):
        self.cfg = cfg
        self.log = logger
        self.scope = ScopeGuard(cfg)
        self.evidence = EvidenceStore(cfg)
        self.findings = FindingsManager()
        self.js = JSAnalyzer()
        self.smart = SmartAnalyzer(self.findings)
        self.discovered_assets: Set[str] = set()
        self.api_endpoints: Set[str] = set()
        self.javascript_files: Set[str] = set()
        self.graphql_endpoints: Set[str] = set()
        self.diagnostics: Dict[str, Any] = {}
        self.seed_used: str = ""
        self.soft404_skipped: int = 0
        self._soft404: Optional[Dict[str, Any]] = None
        self.checkpoint = JobCheckpoint(cfg)
        # Attack-surface MAP (enumeration only; the tool never submits/attacks):
        self.param_map: Dict[str, Dict[str, List[str]]] = {}  # endpoint -> {param: [values]}
        self.forms: List[Dict[str, Any]] = []
        self.passive_hosts: Set[str] = set()
        self.passive_urls: Set[str] = set()
        self.schemas: List[Dict[str, Any]] = []
        self.top10_checklist: List[Dict[str, str]] = []
        self.endpoint_types: Dict[str, str] = {}
        self.param_types: Dict[str, Dict[str, str]] = {}
        self.clusterer = ResponseClusterer(self.smart.similarity)
        self.response_outliers: List[str] = []
        self.response_clusters: List[Dict[str, Any]] = []

    def _record_params(self, url: str) -> None:
        """Catalogue query parameters per endpoint so the operator can see the
        parameterized attack surface at a glance."""
        from urllib.parse import parse_qs
        p = urlparse(url)
        if not p.query:
            return
        endpoint = f"{p.scheme}://{p.netloc}{p.path}"
        bucket = self.param_map.setdefault(endpoint, {})
        for name, vals in parse_qs(p.query, keep_blank_values=True).items():
            store = bucket.setdefault(name, [])
            for v in vals:
                if v not in store and len(store) < 10:
                    store.append(v)

    async def _baseline_soft404(self, eng: "HttpEngine", seed: str) -> None:
        """Request a couple of guaranteed-nonexistent paths. If the host answers
        2xx for those, it has a catch-all (soft 404); we record the shape so real
        crawling can discard pages that merely echo the catch-all response."""
        if not self.cfg.soft404_detection:
            return
        p = urlparse(seed)
        base = f"{p.scheme}://{p.netloc}"
        probe = f"{base}/{sha1(str(time.time()))[:20]}-titan-404-probe"
        res = await eng.fetch(probe)
        if res.ok and InterstitialDetector.inspect(res)[0]:
            return  # a block page is not a soft-404 baseline
        if res.ok and 200 <= res.status < 300:
            self._soft404 = {"status": res.status, "len": len(res.body),
                             "body": res.body[:8000]}
            self.diagnostics["soft404_baseline"] = {"status": res.status,
                                                    "len": len(res.body)}
            self.log.info("Soft-404 baseline captured: status=%s len=%s",
                          res.status, len(res.body))

    def _is_soft404(self, res: "HttpResult") -> bool:
        b = self._soft404
        if not b or not (200 <= res.status < 300) or b["status"] != res.status:
            return False
        # Reject if body size differs a lot; otherwise compare token similarity.
        if b["len"] and abs(len(res.body) - b["len"]) / max(b["len"], 1) > 0.30:
            return False
        return self.smart.similarity(b["body"], res.body[:8000]) >= 0.85

    def _seed(self) -> str:
        t = self.cfg.target
        return t if "://" in t else "https://" + t

    def _seed_candidates(self) -> List[str]:
        """If the target has no scheme, try https/http and a www. variant so a
        single misconfiguration doesn't silently yield zero results."""
        t = self.cfg.target.strip()
        if "://" in t:
            return [t]
        host = urlparse("//" + t).hostname or t
        cands = [f"https://{host}", f"http://{host}"]
        if not host.startswith("www."):
            cands += [f"https://www.{host}", f"http://www.{host}"]
        # Keep only in-scope candidates.
        return [c for c in cands if self.scope.in_scope(c)]

    async def _probe_seed(self, eng: "HttpEngine") -> Optional[str]:
        """Return the first candidate URL that yields a *usable* response (2xx/3xx
        and not an upstream block page). Records diagnostics for every attempt so
        the operator can see exactly what happened."""
        attempts = []
        blocked_reason = None
        for cand in self._seed_candidates():
            res = await eng.fetch(cand)
            is_block, reason = InterstitialDetector.inspect(res) if res.ok else (False, "")
            attempts.append({"url": cand, "status": res.status, "error": res.error,
                             "final_url": res.final_url, "bytes": len(res.body),
                             "blocked": is_block, "block_reason": reason or None})
            self.diagnostics["seed_attempts"] = attempts
            if is_block:
                blocked_reason = blocked_reason or reason
                continue  # do NOT treat a filter/WAF page as the target
            usable = res.ok and 200 <= res.status < 400
            if usable:
                self.diagnostics["seed_ok"] = cand
                if res.final_url and not self.scope.in_scope(res.final_url):
                    self.diagnostics["seed_redirected_out_of_scope"] = res.final_url
                return cand
        self.diagnostics["seed_ok"] = None
        if blocked_reason:
            self.diagnostics["blocked"] = blocked_reason
        return None

    async def crawl(self) -> None:
        seed = self._seed()
        if not self.scope.in_scope(seed):
            raise RuntimeError(f"Seed {seed} is not in scope: {self.scope.describe()}")

        seen: Set[str] = set()
        queue: List[Tuple[str, int]] = []
        resumed = False

        # Resume from a previous checkpoint if one exists.
        if self.cfg.resume:
            ckpt = self.checkpoint.load()
            if ckpt and ckpt.get("queue"):
                seen = set(ckpt.get("seen", []))
                queue = [(u, d) for u, d in ckpt["queue"]]
                self.discovered_assets |= set(ckpt.get("discovered_assets", []))
                self.javascript_files |= set(ckpt.get("javascript_files", []))
                resumed = True
                self.diagnostics["resumed_from"] = ckpt.get("saved_at")
                self.log.info("Resumed crawl: %d queued, %d seen.",
                              len(queue), len(seen))

        async with HttpEngine(self.cfg, self.scope, self.evidence, self.log) as eng:
            if not resumed:
                working = await self._probe_seed(eng)
                if not working:
                    self.diagnostics["reason"] = (
                        "Seed unreachable. See seed_attempts for the status/error "
                        "of each tried URL (TLS, timeout, DNS, redirect, block...).")
                    self.log.error("Seed unreachable for %s", self.cfg.target)
                    return
                self.seed_used = working
                await self._baseline_soft404(eng, working)
                queue = [(working, 0)]

                # Passive OSINT (queries public indexes, NOT the target). Only
                # in-scope results are kept and queued for crawling.
                if self.cfg.passive_discovery:
                    osint = await PassiveRecon(self.cfg, self.log).run(eng)
                    sp = urlparse(working)
                    for h in osint["hosts"]:
                        cand = f"{sp.scheme}://{h}/"
                        if self.scope.in_scope(cand):
                            self.passive_hosts.add(h)
                            queue.append((cand, 0))
                    for u in osint["urls"]:
                        if self.scope.in_scope(u):
                            self.passive_urls.add(u)
                            self._record_params(u)
                            queue.append((u, self.cfg.crawl_depth))  # leaf: parse, don't expand

                # Schema discovery: read published API docs (in-scope GETs).
                if self.cfg.schema_discovery:
                    sd = SchemaDiscovery(self.log)
                    await sd.run(eng, working)
                    self.schemas = sd.schemas
                    self.api_endpoints |= {u for u in sd.endpoints if self.scope.in_scope(u)}
            else:
                self.seed_used = self._seed()

            processed = 0
            while queue and len(seen) < self.cfg.max_pages:
                batch = queue[: self.cfg.workers]
                queue = queue[self.cfg.workers:]
                tasks = []
                for url, depth in batch:
                    if url in seen or depth > self.cfg.crawl_depth:
                        continue
                    seen.add(url)
                    tasks.append(self._visit(eng, url, depth))
                results = await asyncio.gather(*tasks, return_exceptions=True)
                for r in results:
                    if isinstance(r, Exception):
                        self.log.debug("visit error: %s", r)
                        continue
                    if r:
                        for nxt in r:
                            if nxt not in seen and self.scope.in_scope(nxt):
                                queue.append((nxt, batch[0][1] + 1))
                # Crash-safe checkpoint every N pages.
                processed += len(batch)
                if processed >= self.cfg.checkpoint_every:
                    processed = 0
                    self.checkpoint.save(queue, seen, self.discovered_assets,
                                         self.javascript_files)

        # JS analysis pass
        await self._analyze_js()
        self.api_endpoints |= self.js.api_refs
        self._classify_graphql()

        # Finalize response clustering + parameter type inference (analysis only).
        self.response_outliers = self.clusterer.outliers()
        self.response_clusters = self.clusterer.summary()
        for ep, pmap in self.param_map.items():
            self.param_types[ep] = {name: EndpointClassifier.infer_param_type(vals)
                                    for name, vals in pmap.items()}

        # Build the (non-attacking) Top-10 manual-testing checklist from the map,
        # enriched with endpoint-type and param-type signals.
        self.top10_checklist = Top10Annotator.build(
            self.param_map, self.forms, self.findings.findings,
            param_types=self.param_types, endpoint_types=self.endpoint_types)

        if self.soft404_skipped:
            self.diagnostics["soft404_skipped"] = self.soft404_skipped

        if len(self.discovered_assets) <= 1 and not self.diagnostics.get("reason"):
            self.diagnostics["reason"] = (
                "Seed reachable but few/no links extracted. Likely a "
                "JavaScript-rendered SPA (links built at runtime), an empty/"
                "challenge page (Cloudflare/WAF), or a login wall. Try option 2 "
                "to inspect served JS, raise --depth, or check the seed response "
                "snippet in evidence.")
        self.diagnostics["pages_visited"] = len(seen)
        # Completed cleanly -> drop the checkpoint.
        self.checkpoint.clear()

    async def _visit(self, eng: HttpEngine, url: str, depth: int) -> List[str]:
        res = await eng.fetch(url)
        if not res.ok:
            return []
        is_block, reason = InterstitialDetector.inspect(res)
        if is_block:
            # A filter/WAF/CDN/censorship page is not the target. Record the fact
            # once, then ignore it for asset/tech/link extraction.
            self.diagnostics.setdefault("blocked", reason)
            self.log.warning("Interstitial detected at %s (%s) — skipping.", url, reason)
            return []
        if self._is_soft404(res):
            # Catch-all "page exists" response — not a real asset.
            self.soft404_skipped += 1
            self.log.debug("Soft-404 discarded: %s", url)
            return []
        ev = self.evidence.items[-1].id if self.evidence.items else ""
        self.discovered_assets.add(res.final_url or res.url)
        self._record_params(res.final_url or res.url)
        self.smart.detect_tech(res)
        self.smart.check_security_headers(res, ev)
        self.smart.check_version_disclosure(res, ev)

        ctype = res.headers.get("content-type", "")
        # Classify the endpoint and feed the response clusterer (analysis only).
        self.endpoint_types[res.final_url or res.url] = EndpointClassifier.classify(
            res.final_url or res.url, res.status, ctype, res.body)
        self.clusterer.add(res.final_url or res.url, res.status, res.body)
        next_urls: List[str] = []
        if "html" in ctype or "<html" in res.body[:500].lower():
            links, scripts = HtmlLinkExtractor.links(res.final_url or url, res.body)
            for f in HtmlLinkExtractor.forms(res.final_url or url, res.body):
                if f not in self.forms:
                    self.forms.append(f)
            for s in scripts:
                if s.endswith(".js") or ".js?" in s:
                    self.javascript_files.add(s)
            for l in links:
                self._record_params(l)   # catalogue params even if not crawled
            next_urls = [l for l in links
                         if not l.lower().endswith((".png", ".jpg", ".jpeg",
                                                    ".gif", ".css", ".svg", ".ico",
                                                    ".woff", ".woff2"))]
        elif "javascript" in ctype or url.endswith(".js"):
            self.javascript_files.add(res.final_url or url)
            self.js.analyze(res.final_url or url, res.body)
        return next_urls

    async def _analyze_js(self) -> None:
        if not self.javascript_files:
            return
        async with HttpEngine(self.cfg, self.scope, self.evidence, self.log) as eng:
            tasks = [eng.fetch(u) for u in list(self.javascript_files)[: self.cfg.max_pages]]
            for res in await asyncio.gather(*tasks, return_exceptions=True):
                if isinstance(res, Exception) or not getattr(res, "ok", False):
                    continue
                self.js.analyze(res.final_url or res.url, res.body)
            # Sourcemap recovery: fetch any referenced .map files (in-scope),
            # parse out the original sources, and re-analyze the real source.
            maps = [m for m in self.js.sourcemaps if self.scope.in_scope(m)]
            if maps:
                for res in await asyncio.gather(*[eng.fetch(m) for m in maps],
                                                return_exceptions=True):
                    if isinstance(res, Exception) or not getattr(res, "ok", False):
                        continue
                    srcs, content = self._parse_sourcemap(res.body)
                    if content:
                        self.js.recovered_sources.extend(srcs)
                        self.js.analyze(res.final_url or res.url, content)
        self.discovered_assets |= self.js.endpoints
        self._emit_secret_findings()

    @staticmethod
    def _parse_sourcemap(body: str) -> Tuple[List[str], str]:
        """Extract original file list and concatenated original source from a
        sourcemap (.map) JSON. Sourcemaps are publicly served build artifacts."""
        try:
            doc = json.loads(body)
        except json.JSONDecodeError:
            return [], ""
        sources = [str(s) for s in (doc.get("sources") or [])]
        content = "\n".join(c for c in (doc.get("sourcesContent") or []) if c)
        return sources, content

    def _emit_secret_findings(self) -> None:
        for hit in self.js.secret_hits:
            ev = next((i.id for i in self.evidence.items
                       if i.url == hit["source"]), "")
            self.findings.add(Finding(
                title=f"Exposed secret-shaped string in JS: {hit['type']}",
                severity="medium" if hit["confidence"] == "high" else "low",
                confidence=hit["confidence"],
                affected_url=hit["source"],
                endpoint=urlparse(hit["source"]).path,
                detection_logic=f"Regex match for {hit['type']} in served JavaScript.",
                validation_logic=(
                    f"Candidate validated by Shannon entropy={hit['entropy']} and "
                    "placeholder/template filtering. Confirm the value is live "
                    "and in-scope before reporting."),
                request_sample=f"GET {hit['source']}",
                response_indicators=f"match preview: {hit['match_preview']}",
                reproduction=[f"curl -s '{hit['source']}'",
                              f"Search the body for a {hit['type']} pattern.",
                              "Manually confirm the credential is valid and authorized."],
                evidence_id=ev,
                technical_explanation=(
                    "Client-served JavaScript appears to contain a credential-shaped "
                    "string. Front-end code is fully readable by anyone."),
                security_impact=(
                    "If the value is a live secret, it may grant unauthorized access. "
                    "Many such strings are public/publishable keys — verify first."),
                remediation=("Move secrets server-side; rotate any confirmed-live key; "
                             "scope front-end keys to least privilege."),
                cwe=hit["cwe"], owasp="A07:2021 Identification & Auth Failures",
            ))

    def _classify_graphql(self) -> None:
        for asset in list(self.discovered_assets) + list(self.api_endpoints):
            path = urlparse(asset).path.lower()
            if any(h in path for h in GRAPHQL_PATH_HINTS):
                self.graphql_endpoints.add(asset)

    async def graphql_probe(self) -> None:
        """
        Map GraphQL endpoints. Introspection is a *standard, documented* query,
        but it is gated behind config and scope, and only ever sent in-scope.
        """
        if not self.graphql_endpoints:
            self.log.info("No GraphQL endpoints discovered to probe.")
            return
        if not self.cfg.graphql_introspection:
            self.log.info("GraphQL endpoints found; introspection disabled in config.")
            return
        q = '{"query":"query{__schema{queryType{name}}}"}'
        async with HttpEngine(self.cfg, self.scope, self.evidence, self.log) as eng:
            for ep in self.graphql_endpoints:
                res = await eng.fetch(ep, method="POST",
                                      headers={"Content-Type": "application/json"},
                                      data=q)
                if res.ok and "__schema" in res.body:
                    ev = self.evidence.items[-1].id if self.evidence.items else ""
                    self.findings.add(Finding(
                        title="GraphQL introspection enabled",
                        severity="low", confidence="high",
                        affected_url=ep, endpoint=urlparse(ep).path,
                        detection_logic="Introspection query returned __schema data.",
                        validation_logic="Response body contains a valid __schema object.",
                        request_sample=f"POST {ep}  body={q}",
                        response_indicators="'__schema' present in JSON response",
                        reproduction=[f"curl -s -X POST '{ep}' "
                                      f"-H 'Content-Type: application/json' -d '{q}'"],
                        evidence_id=ev,
                        technical_explanation=(
                            "The endpoint answers introspection, revealing the full "
                            "schema. Often intended in dev, sometimes left on in prod."),
                        security_impact=("Eases API mapping for an attacker. Low on its "
                                         "own; combine with authz testing."),
                        remediation="Disable introspection in production if not required.",
                        cwe="CWE-200", owasp="A05:2021 Security Misconfiguration",
                    ))


# --------------------------------------------------------------------------- #
#  Sessions
# --------------------------------------------------------------------------- #
class SessionManager:
    def __init__(self, cfg: Config):
        self.cfg = cfg

    def _slug(self) -> str:
        host = urlparse(self.cfg.target if "://" in self.cfg.target
                        else "//" + self.cfg.target).hostname or "target"
        return re.sub(r"[^a-zA-Z0-9_.-]", "_", host)

    def save(self, scanner: Scanner) -> str:
        self.cfg.ensure_dirs()
        path = os.path.join(self.cfg.sessions_dir, f"{self._slug()}.session.json")
        state = {
            "saved_at": now_iso(),
            "config": asdict(self.cfg),
            "discovered_assets": sorted(scanner.discovered_assets),
            "api_endpoints": sorted(scanner.api_endpoints),
            "javascript_files": sorted(scanner.javascript_files),
            "graphql_endpoints": sorted(scanner.graphql_endpoints),
            "technologies": sorted(scanner.smart.technologies),
            "parameters": sorted(scanner.param_map.keys()),
            "forms": sorted(f"{f['method']} {f['action']}" for f in scanner.forms),
            "findings": [asdict(f) for f in scanner.findings.findings],
        }
        with open(path, "w") as fh:
            json.dump(state, fh, indent=2)
        return path

    def load(self) -> Optional[Dict[str, Any]]:
        path = os.path.join(self.cfg.sessions_dir, f"{self._slug()}.session.json")
        if not os.path.isfile(path):
            return None
        with open(path) as fh:
            return json.load(fh)

    def compare(self, current: Scanner) -> Dict[str, List[str]]:
        prev = self.load()
        if not prev:
            return {"note": ["No previous session to compare."]}
        cur_forms = {f"{f['method']} {f['action']}" for f in current.forms}
        dims = {
            "assets": (set(prev.get("discovered_assets", [])), set(current.discovered_assets)),
            "api_endpoints": (set(prev.get("api_endpoints", [])), set(current.api_endpoints)),
            "javascript_files": (set(prev.get("javascript_files", [])), set(current.javascript_files)),
            "parameters": (set(prev.get("parameters", [])), set(current.param_map.keys())),
            "forms": (set(prev.get("forms", [])), cur_forms),
        }
        diff: Dict[str, List[str]] = {}
        for name, (old, new) in dims.items():
            diff[f"new_{name}"] = sorted(new - old)
            diff[f"removed_{name}"] = sorted(old - new)
        return diff


# --------------------------------------------------------------------------- #
#  Reporting
# --------------------------------------------------------------------------- #
# --------------------------------------------------------------------------- #
#  AI report analyzer (option 14)  -  reads a report, asks Claude for
#  structured analysis. Strictly review/triage; the model is NOT given the
#  ability to execute anything against the target.
# --------------------------------------------------------------------------- #
class AIReportAnalyzer:
    """
    Sends the JSON report (plus optional Markdown excerpt) to the Anthropic API
    and asks for an explicit analysis: surface shape, prioritized manual-testing
    plan, methodology issues, and warnings.

    Network policy: this is the ONLY component allowed to talk to
    api.anthropic.com. It never sends requests to the recon target.
    """

    API_URL = "https://api.anthropic.com/v1/messages"
    API_VERSION = "2023-06-01"
    MAX_TOKENS = 2000

    SYSTEM_PROMPT = (
        "You are reviewing a passive reconnaissance report from a Termux-based "
        "tool used for AUTHORIZED bug-bounty / security research. Your job is "
        "review and triage ONLY:\n"
        "1. Summarize what kind of target this is and what the surface looks like.\n"
        "2. Identify methodology problems in the run (block pages mistaken for "
        "the target, empty results, scope misconfig, soft-404 noise, etc.) and "
        "explain how the operator should fix them.\n"
        "3. Prioritize the existing manual-testing checklist items: which to "
        "investigate first, which look low-value, which look noisy.\n"
        "4. Point out gaps the recon missed (passive sources to query, schema "
        "endpoints not yet probed, JS files worth re-reading).\n"
        "5. Flag anything that looks out-of-scope or unsafe to test.\n\n"
        "DO NOT output exploit payloads, attack strings, or step-by-step "
        "exploitation instructions. Output guidance the operator follows by "
        "hand with their own tools (Burp, ZAP, sqlmap, nuclei) under their "
        "signed scope. Be concrete and specific to the report you are given."
    )

    def __init__(self, cfg: Config, logger: logging.Logger):
        self.cfg = cfg
        self.log = logger

    @staticmethod
    def _slim(report: Dict[str, Any]) -> Dict[str, Any]:
        """Strip oversized fields and trim long lists so the prompt fits."""
        r = dict(report)
        # Drop full response bodies; keep evidence metadata only.
        ev = []
        for e in (r.get("evidence") or [])[:30]:
            e = dict(e)
            e["response_snippet"] = (e.get("response_snippet") or "")[:300]
            e.pop("request_headers", None)
            ev.append(e)
        r["evidence"] = ev
        # Cap big lists.
        for k in ("discovered_assets", "api_endpoints", "javascript_files",
                  "passive_urls", "passive_hosts", "js_callsites",
                  "recovered_sources"):
            if isinstance(r.get(k), list) and len(r[k]) > 80:
                r[k] = r[k][:80] + [f"... (+{len(r[k]) - 80} more, truncated)"]
        return r

    def _payload(self, report: Dict[str, Any]) -> Dict[str, Any]:
        slim = self._slim(report)
        user_msg = (
            "Analyze this recon report. Use the structure: "
            "(A) Target summary, "
            "(B) Methodology issues (what went wrong / how to fix), "
            "(C) Prioritized manual testing plan (ranked, with reasoning), "
            "(D) Gaps to fill before submitting, "
            "(E) Safety / scope warnings.\n\n"
            "Report JSON:\n```json\n" + json.dumps(slim, indent=2)[:120000] + "\n```"
        )
        return {
            "model": self.cfg.anthropic_model,
            "max_tokens": self.MAX_TOKENS,
            "system": self.SYSTEM_PROMPT,
            "messages": [{"role": "user", "content": user_msg}],
        }

    def _post(self, body: Dict[str, Any], *, key_override: Optional[str] = None,
              max_tokens_override: Optional[int] = None) -> Tuple[int, Dict[str, Any], str]:
        key = key_override or self.cfg.anthropic_api_key
        if not key:
            return 0, {}, "no API key configured (option 8 -> set key)"
        if max_tokens_override is not None:
            body = dict(body, max_tokens=max_tokens_override)
        data = json.dumps(body).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "x-api-key": key,
            "anthropic-version": self.API_VERSION,
        }
        # Use plain stdlib urllib so this works on Termux without aiohttp.
        import urllib.request as _u, urllib.error as _e
        req = _u.Request(self.API_URL, data=data, headers=headers, method="POST")
        try:
            with _u.urlopen(req, timeout=60) as resp:
                raw = resp.read().decode("utf-8", "replace")
                try:
                    return resp.status, json.loads(raw), ""
                except json.JSONDecodeError:
                    return resp.status, {}, f"non-JSON response: {raw[:200]}"
        except _e.HTTPError as exc:
            raw = exc.read().decode("utf-8", "replace") if hasattr(exc, "read") else ""
            return exc.code, {}, raw[:500]
        except Exception as exc:
            return 0, {}, f"{type(exc).__name__}: {exc}"

    @staticmethod
    def _extract_text(resp: Dict[str, Any]) -> str:
        chunks = []
        for block in resp.get("content") or []:
            if isinstance(block, dict) and block.get("type") == "text":
                chunks.append(block.get("text", ""))
        return "\n".join(chunks).strip()

    def analyze_report(self, report_path: str) -> Tuple[bool, str]:
        try:
            with open(report_path) as fh:
                report = json.load(fh)
        except (OSError, json.JSONDecodeError) as exc:
            return False, f"cannot read report: {exc}"
        status, resp, err = self._post(self._payload(report))
        if status == 200 and resp:
            return True, self._extract_text(resp) or "(empty response)"
        return False, f"API error (status={status}): {err}"

    def test_key(self, key: Optional[str] = None) -> Tuple[bool, str]:
        """Cheap round-trip to verify the key is valid and the model responds."""
        test_body = {
            "model": self.cfg.anthropic_model,
            "max_tokens": 16,
            "messages": [{"role": "user", "content": "Reply with exactly: OK"}],
        }
        status, resp, err = self._post(test_body, key_override=key,
                                       max_tokens_override=16)
        if status == 200 and resp:
            txt = self._extract_text(resp)
            return True, f"key valid; model={resp.get('model','?')}; reply={txt!r}"
        if status == 401:
            return False, "key rejected (401 unauthorized) — double-check the value"
        if status == 429:
            return False, "rate-limited (429) — key is recognized but throttled"
        if status == 0 and "no API key" in err:
            return False, err
        return False, f"status={status}; {err}"


class AIAssistant:
    """
    Interactive chat assistant (option 16). Reads files/folders the operator
    points it at, sends the contents plus the operator's question to Claude,
    and — for explicit edit requests — proposes a replacement that is shown as
    a diff and only written after a y/N confirmation, with an automatic backup.

    HARD LIMITS (enforced in code, not just prompts):
      * No shell execution, ever. No subprocess, no os.system, no package
        install. If a user asks to "run X" or "install Y", the handler refuses.
      * Reads only files explicitly named by the operator in the chat turn.
      * Writes only to text-shaped files (allowed extensions) and only after
        an interactive y/N confirmation, with .bak preserved.
      * Refuses to touch typical executable / system locations.
    """

    # Lightweight allowlist for what is treated as a "text/code" file to edit.
    EDITABLE_EXT = {
        ".py", ".js", ".ts", ".jsx", ".tsx", ".json", ".yaml", ".yml",
        ".toml", ".ini", ".cfg", ".md", ".txt", ".html", ".htm", ".css",
        ".csv", ".tsv", ".xml", ".sql", ".rst", ".env.sample", ".log",
    }
    # Directories we refuse to write into, no matter what.
    FORBIDDEN_WRITE_PREFIXES = (
        "/system", "/vendor", "/etc", "/bin", "/sbin", "/usr/bin", "/usr/sbin",
        "/data/data", "/proc", "/sys", "/dev",
    )
    # Extensions we refuse to write to (executables, archives, binaries).
    FORBIDDEN_WRITE_EXT = {
        ".sh", ".bash", ".zsh", ".ksh", ".fish", ".exe", ".bin", ".so", ".dll",
        ".dylib", ".apk", ".dex", ".elf", ".o", ".a", ".jar", ".class",
        ".pyc", ".pyo",
    }
    MAX_READ_BYTES = 200_000        # per file; bigger files are truncated
    MAX_FOLDER_FILES = 25           # cap files included when a folder is named
    MAX_CONTEXT_CHARS = 140_000     # rough cap on the prompt content

    SYSTEM_PROMPT = (
        "You are the in-app assistant for TITAN_HUNTER, a recon tool used for "
        "authorized security research. The user will paste questions and may "
        "attach files (reports, code, logs) for you to analyze.\n\n"
        "Capabilities you have in this app:\n"
        "  - Read files/folders the user attaches.\n"
        "  - Explain code, reports, errors, and tracebacks.\n"
        "  - Propose edits to text/code files (the app will diff them and ask "
        "    the user before saving).\n\n"
        "Things you DO NOT have and must not pretend to have:\n"
        "  - No shell execution. You cannot install packages, run commands, "
        "    start services, or invoke any binary. If the user asks for this, "
        "    explain that the app refuses shell execution and tell them the "
        "    exact command to run themselves in their terminal.\n"
        "  - No network requests beyond this very API call.\n"
        "  - No writing to executable files or system locations.\n\n"
        "For EDIT requests: respond in two parts.\n"
        "  1. A short explanation of the change.\n"
        "  2. The COMPLETE updated file, wrapped exactly as:\n"
        "     <<<FILE: /absolute/path/to/file>>>\n"
        "     ... full file contents ...\n"
        "     <<<END FILE>>>\n"
        "Only emit one <<<FILE>>> block per turn. Do not abbreviate. The app "
        "will diff and confirm with the user before writing.\n\n"
        "For analysis-only requests, just answer in prose. Do not include a "
        "<<<FILE>>> block unless the user explicitly asked you to modify a file."
    )

    FILE_BLOCK_RE = re.compile(
        r"<<<FILE:\s*(?P<path>[^\n>]+?)\s*>>>\s*\n(?P<body>.*?)\n<<<END FILE>>>",
        re.S,
    )

    def __init__(self, cfg: Config, logger: logging.Logger):
        self.cfg = cfg
        self.log = logger
        self.history: List[Dict[str, str]] = []   # {role, content}

    # ---- file IO with hard limits ------------------------------------------
    @classmethod
    def _is_editable(cls, path: str) -> bool:
        low = path.lower()
        if any(low.startswith(p) for p in cls.FORBIDDEN_WRITE_PREFIXES):
            return False
        ext = os.path.splitext(low)[1]
        if ext in cls.FORBIDDEN_WRITE_EXT:
            return False
        return ext in cls.EDITABLE_EXT or ext == ""

    @classmethod
    def read_path(cls, p: str) -> Tuple[List[Dict[str, str]], List[str]]:
        """Return ([{path, content}], notes). Folders are expanded shallowly."""
        notes: List[str] = []
        out: List[Dict[str, str]] = []
        if not os.path.exists(p):
            notes.append(f"not found: {p}")
            return out, notes
        if os.path.isdir(p):
            picked = 0
            for root, dirs, files in os.walk(p):
                # don't descend into hidden / vendor dirs
                dirs[:] = [d for d in dirs if not d.startswith(".") and
                           d not in {"node_modules", "__pycache__", ".git"}]
                for fn in sorted(files):
                    full = os.path.join(root, fn)
                    ext = os.path.splitext(fn)[1].lower()
                    if ext not in cls.EDITABLE_EXT:
                        continue
                    if picked >= cls.MAX_FOLDER_FILES:
                        notes.append(f"folder cap hit at {cls.MAX_FOLDER_FILES} files; "
                                     "name a specific file for more detail.")
                        return out, notes
                    rec = cls._read_one(full, notes)
                    if rec:
                        out.append(rec)
                        picked += 1
            return out, notes
        # single file
        rec = cls._read_one(p, notes)
        if rec:
            out.append(rec)
        return out, notes

    @classmethod
    def _read_one(cls, path: str, notes: List[str]) -> Optional[Dict[str, str]]:
        try:
            sz = os.path.getsize(path)
        except OSError as exc:
            notes.append(f"stat error {path}: {exc}")
            return None
        try:
            with open(path, "rb") as fh:
                raw = fh.read(cls.MAX_READ_BYTES + 1)
        except OSError as exc:
            notes.append(f"read error {path}: {exc}")
            return None
        truncated = len(raw) > cls.MAX_READ_BYTES
        if truncated:
            raw = raw[:cls.MAX_READ_BYTES]
            notes.append(f"truncated {path} at {cls.MAX_READ_BYTES} bytes "
                         f"(file is {sz} bytes)")
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            notes.append(f"skipped non-UTF-8 binary file: {path}")
            return None
        return {"path": path, "content": text}

    # ---- prompt + API call -------------------------------------------------
    def _build_user_message(self, question: str,
                            files: List[Dict[str, str]],
                            read_notes: List[str]) -> str:
        parts: List[str] = []
        if files:
            parts.append("Attached files:")
            budget = self.MAX_CONTEXT_CHARS
            for f in files:
                header = f"\n--- FILE: {f['path']} ---\n"
                room = max(2000, budget - len(header))
                body = f["content"][:room]
                if len(f["content"]) > room:
                    body += f"\n... (file truncated at {room} chars in prompt)"
                parts.append(header + body)
                budget -= len(header) + len(body)
                if budget <= 0:
                    parts.append("\n(prompt context budget reached; "
                                 "remaining files omitted)")
                    break
        if read_notes:
            parts.append("\nFile read notes: " + "; ".join(read_notes))
        parts.append("\nUser question:\n" + question)
        return "\n".join(parts)

    def ask(self, question: str, files: List[Dict[str, str]],
            read_notes: List[str]) -> Tuple[bool, str]:
        # Reuse the analyzer's transport so we have one code path.
        az = AIReportAnalyzer(self.cfg, self.log)
        user_msg = self._build_user_message(question, files, read_notes)
        self.history.append({"role": "user", "content": user_msg})
        body = {
            "model": self.cfg.anthropic_model,
            "max_tokens": 4000,
            "system": self.SYSTEM_PROMPT,
            "messages": self.history,
        }
        status, resp, err = az._post(body)
        if status == 200 and resp:
            text = az._extract_text(resp) or "(empty response)"
            self.history.append({"role": "assistant", "content": text})
            # Keep history bounded so the prompt doesn't grow unbounded.
            if len(self.history) > 20:
                self.history = self.history[-20:]
            return True, text
        return False, f"API error (status={status}): {err}"

    # ---- edit proposal handling -------------------------------------------
    @classmethod
    def extract_edits(cls, reply: str) -> List[Dict[str, str]]:
        out = []
        for m in cls.FILE_BLOCK_RE.finditer(reply):
            out.append({"path": m.group("path").strip(),
                        "new_content": m.group("body")})
        return out

    @classmethod
    def make_diff(cls, path: str, new_content: str) -> str:
        import difflib
        try:
            with open(path) as fh:
                old = fh.read().splitlines(keepends=True)
        except OSError:
            old = []
        new = new_content.splitlines(keepends=True)
        diff = difflib.unified_diff(old, new,
                                    fromfile=path + " (current)",
                                    tofile=path + " (proposed)",
                                    n=3)
        return "".join(diff) or "(no textual change)"

    @classmethod
    def apply_edit(cls, path: str, new_content: str) -> Tuple[bool, str]:
        if not cls._is_editable(path):
            return False, (f"refused: {path} is not in the editable allowlist "
                           f"(extension or protected location).")
        # Backup if file exists.
        if os.path.exists(path):
            bak = path + ".bak"
            try:
                with open(path, "rb") as src, open(bak, "wb") as dst:
                    dst.write(src.read())
            except OSError as exc:
                return False, f"backup failed: {exc}"
        # Atomic-ish write.
        tmp = path + ".tmp"
        try:
            os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
            with open(tmp, "w") as fh:
                fh.write(new_content)
            os.replace(tmp, path)
        except OSError as exc:
            return False, f"write failed: {exc}"
        return True, f"wrote {path} (backup at {path}.bak)"


class Reporter:
    def __init__(self, cfg: Config, scanner: Scanner):
        self.cfg = cfg
        self.s = scanner

    def _base(self) -> Dict[str, Any]:
        return {
            "tool": f"TITAN_HUNTER {VERSION}",
            "target": self.cfg.target,
            "scope": ScopeGuard(self.cfg).describe(),
            "scan_time": now_iso(),
            "findings": [asdict(f) for f in self.s.findings.findings],
            "evidence": self.s.evidence.dump(),
            "severity_summary": self.s.findings.severity_summary(),
            "technologies": sorted(self.s.smart.technologies),
            "discovered_assets": sorted(self.s.discovered_assets),
            "api_endpoints": sorted(self.s.api_endpoints),
            "javascript_files": sorted(self.s.javascript_files),
            "graphql_endpoints": sorted(self.s.graphql_endpoints),
            "parameters": self.s.param_map,
            "forms": self.s.forms,
            "api_schemas": self.s.schemas,
            "passive_hosts": sorted(self.s.passive_hosts),
            "passive_urls": sorted(self.s.passive_urls)[:500],
            "owasp_top10_checklist": self.s.top10_checklist,
            "endpoint_types": self.s.endpoint_types,
            "parameter_types": self.s.param_types,
            "js_callsites": sorted(self.s.js.callsites),
            "recovered_sources": sorted(set(self.s.js.recovered_sources))[:500],
            "response_clusters": self.s.response_clusters,
            "response_outliers": self.s.response_outliers,
        }

    def json_report(self) -> str:
        self.cfg.ensure_dirs()
        path = os.path.join(self.cfg.reports_dir,
                            f"report_{int(time.time())}.json")
        with open(path, "w") as fh:
            json.dump(self._base(), fh, indent=2)
        return path

    # Severity ordering for the OWASP categories that appear in PARAM_HINTS.
    _OWASP_ORDER = {"A01": 1, "A02": 2, "A03": 3, "A04": 4, "A05": 5,
                    "A06": 6, "A07": 7, "A08": 8, "A09": 9, "A10": 10}

    @classmethod
    def _owasp_key(cls, item: Dict[str, str]) -> Tuple[int, str]:
        owasp = item.get("owasp", "")
        prefix = owasp.split()[0] if owasp else "Z"
        return (cls._OWASP_ORDER.get(prefix, 99), owasp)

    def checklist_report(self) -> str:
        """
        Export a standalone manual-testing checklist (checklist_<ts>.md) the
        operator can carry through the engagement: one box per surface item,
        OWASP category, CWE, what to verify by hand, a Tester Notes line, and a
        Status field. This is a worksheet — it does not send anything.
        """
        self.cfg.ensure_dirs()
        d = self._base()
        target = d["target"] or "(unset)"
        scope = d["scope"]
        ts = int(time.time())
        path = os.path.join(self.cfg.reports_dir, f"checklist_{ts}.md")

        checklist = list(d.get("owasp_top10_checklist", []))
        checklist.sort(key=self._owasp_key)
        by_cat: Dict[str, List[Dict[str, str]]] = {}
        for item in checklist:
            by_cat.setdefault(item.get("owasp", "Other"), []).append(item)

        # Auxiliary worksheet items pulled straight from the map.
        params = d.get("parameters", {}) or {}
        ptypes = d.get("parameter_types", {}) or {}
        etypes = d.get("endpoint_types", {}) or {}
        forms = d.get("forms", []) or []
        schemas = d.get("api_schemas", []) or []
        outliers = d.get("response_outliers", []) or []
        passive_hosts = d.get("passive_hosts", []) or []

        L: List[str] = []
        L.append(f"# Manual Testing Checklist — {target}")
        L.append(f"**Scope:** {scope}  ")
        L.append(f"**Generated:** {d['scan_time']}  ")
        L.append(f"**Tool:** {d['tool']}\n")
        L.append("> Worksheet for authorized testing only. Items below are leads "
                 "from passive recon; the tool sent no payloads. Tick each box as "
                 "you verify or rule out the item by hand, in scope, with your "
                 "own tools (Burp / ZAP / sqlmap / nuclei).\n")

        # --- Pre-flight ---
        L.append("## 0. Pre-flight")
        L.append("- [ ] I have written authorization to test this target.")
        L.append("- [ ] I have read the program's scope and rules (rate limits, "
                "excluded paths, reporting policy).")
        L.append("- [ ] My test traffic is identifiable (custom UA / header) where required.")
        L.append("- [ ] I will stop and report immediately on signs of real PII, "
                "production data exposure, or service impact.\n")

        # --- Surface snapshot ---
        L.append("## 1. Surface snapshot")
        L.append(f"- Assets discovered: **{len(d['discovered_assets'])}**")
        L.append(f"- API endpoints: **{len(d['api_endpoints'])}**")
        L.append(f"- JS files: **{len(d['javascript_files'])}**  |  "
                 f"Call-site endpoints: **{len(d.get('js_callsites', []))}**  |  "
                 f"Recovered sources: **{len(d.get('recovered_sources', []))}**")
        L.append(f"- HTML forms: **{len(forms)}**  |  "
                 f"Parameterized endpoints: **{len(params)}**")
        L.append(f"- Published API schemas: **{len(schemas)}**  |  "
                 f"Response outliers: **{len(outliers)}**  |  "
                 f"Passive OSINT hosts: **{len(passive_hosts)}**\n")

        # --- Top-10 checklist (sorted by OWASP category) ---
        L.append(f"## 2. OWASP Top-10 manual checks ({len(checklist)})")
        if not checklist:
            L.append("_No candidates flagged from the current map._\n")
        idx = 0
        for cat in sorted(by_cat, key=lambda c: self._owasp_key({"owasp": c})):
            L.append(f"### {cat}")
            for it in by_cat[cat]:
                idx += 1
                cid = f"T10-{idx:03d}"
                L.append(f"- [ ] **[{cid}] {it['surface']}**")
                L.append(f"      - Check: {it['manual_check']}")
                L.append(f"      - CWE: {it['cwe']}  |  Note: {it.get('note','')}")
                L.append(f"      - Tester notes: _______________________")
                L.append(f"      - Status: ☐ not started  ☐ in progress  "
                         f"☐ confirmed  ☐ not vulnerable  ☐ out of scope\n")

        # --- Response outliers worth a manual look ---
        if outliers:
            L.append(f"## 3. Response outliers ({len(outliers)})")
            L.append("_Endpoints that didn't match the templated bulk. Review "
                     "these first — they're usually the interesting ones._\n")
            for i, u in enumerate(outliers[:50], 1):
                L.append(f"- [ ] **[OUT-{i:03d}]** {u}")
                L.append(f"      - Why it differs: _______________________")
                L.append(f"      - Tester notes: _______________________\n")

        # --- Forms worksheet ---
        if forms:
            L.append(f"## 4. Forms worksheet ({len(forms)})")
            for i, fm in enumerate(forms[:50], 1):
                fields = ", ".join(f"`{inp['name']}`({inp['type']})"
                                   for inp in fm["inputs"]) or "—"
                L.append(f"- [ ] **[FRM-{i:03d}]** {fm['method']} {fm['action']}")
                L.append(f"      - Fields: {fields}")
                L.append(f"      - Manual checks: auth strength, CSRF token, "
                         f"input validation, rate limiting (by hand)")
                L.append(f"      - Tester notes: _______________________\n")

        # --- Parameter inventory worksheet ---
        if params:
            L.append(f"## 5. Parameter inventory ({len(params)})")
            for i, (ep, pmap) in enumerate(list(params.items())[:80], 1):
                ep_type = etypes.get(ep, "?")
                ptype_map = ptypes.get(ep, {})
                p_summary = ", ".join(f"`{n}`({ptype_map.get(n,'?')})" for n in pmap)
                L.append(f"- [ ] **[PRM-{i:03d}]** `{ep}` _(endpoint type: {ep_type})_")
                L.append(f"      - Params: {p_summary}")
                L.append(f"      - Tester notes: _______________________\n")

        # --- API schemas + passive surface ---
        if schemas:
            L.append(f"## 6. Published API schemas ({len(schemas)})")
            for i, s in enumerate(schemas, 1):
                L.append(f"- [ ] **[API-{i:03d}]** {s['type']}: {s['url']} "
                         f"({s['path_count']} documented paths)")
                L.append(f"      - Review the schema; cross-check authn/authz on "
                         f"each documented path by hand")
                L.append(f"      - Tester notes: _______________________\n")

        if passive_hosts:
            L.append(f"## 7. Passive OSINT hosts ({len(passive_hosts)})")
            L.append("_Verify which are in scope and live before testing._\n")
            for i, h in enumerate(passive_hosts[:80], 1):
                L.append(f"- [ ] **[OSI-{i:03d}]** {h}  — in scope? ☐  live? ☐  "
                         f"notes: _______________________")

        L.append("\n---")
        L.append("_TITAN_HUNTER produced this worksheet from passive recon only. "
                 "All verification is manual, in scope, and at the tester's discretion._")

        with open(path, "w") as fh:
            fh.write("\n".join(L))
        return path

    def markdown_report(self) -> str:
        self.cfg.ensure_dirs()
        d = self._base()
        path = os.path.join(self.cfg.reports_dir,
                            f"report_{int(time.time())}.md")
        L: List[str] = []
        L.append(f"# TITAN_HUNTER Recon Report\n")
        L.append(f"**Target:** {d['target']}  ")
        L.append(f"**Scope:** {d['scope']}  ")
        L.append(f"**Generated:** {d['scan_time']}  ")
        L.append(f"**Tool:** {d['tool']}\n")
        L.append("> Authorized testing only. Findings below are *observations* "
                 "requiring human verification before submission.\n")

        L.append("## Summary")
        ss = d["severity_summary"] or {"(none)": 0}
        L.append(", ".join(f"{k}: {v}" for k, v in ss.items()) + "\n")

        L.append("## Scope")
        L.append(f"`{d['scope']}`\n")

        L.append("## Findings")
        if not d["findings"]:
            L.append("_No findings met the validation threshold._\n")
        for i, f in enumerate(d["findings"], 1):
            L.append(f"### {i}. {f['title']}")
            L.append(f"- **Severity:** {f['severity']}  |  **Confidence:** {f['confidence']}")
            urls = f.get("affected_urls") or [f["affected_url"]]
            if len(urls) > 1:
                L.append(f"- **Affected URLs ({len(urls)}):** {urls[0]} "
                         f"(+{len(urls)-1} more — see JSON)")
            else:
                L.append(f"- **Affected URL:** {urls[0]}")
            L.append(f"- **Endpoint:** `{f['endpoint']}`")
            L.append(f"- **CWE:** {f['cwe']}  |  **OWASP:** {f['owasp']}")
            L.append(f"- **Detection:** {f['detection_logic']}")
            L.append(f"- **Validation:** {f['validation_logic']}")
            L.append(f"- **Request sample:** `{f['request_sample']}`")
            L.append(f"- **Response indicators:** {f['response_indicators']}")
            L.append(f"- **Technical detail:** {f['technical_explanation']}")
            L.append(f"- **Impact:** {f['security_impact']}")
            L.append("- **Reproduction:**")
            for step in f["reproduction"]:
                L.append(f"  1. {step}")
            L.append(f"- **Remediation:** {f['remediation']}")
            L.append(f"- **Evidence ID:** `{f['evidence_id']}`  |  **Found:** {f['timestamp']}\n")

        L.append("## Evidence")
        L.append(f"Captured {len(d['evidence'])} request/response records "
                 f"(full data in JSON report).\n")

        L.append("## Technical Details")
        L.append("**Technologies observed:** " +
                 (", ".join(d["technologies"]) or "none") + "\n")
        L.append(f"**Assets discovered:** {len(d['discovered_assets'])}  ")
        L.append(f"**API endpoints:** {len(d['api_endpoints'])}  ")
        L.append(f"**JavaScript files:** {len(d['javascript_files'])}  ")
        L.append(f"**GraphQL endpoints:** {len(d['graphql_endpoints'])}\n")

        L.append("## Attack Surface Map")
        params = d.get("parameters", {})
        L.append(f"### Parameterized endpoints ({len(params)})")
        if not params:
            L.append("_None observed._")
        for ep, pmap in list(params.items())[:50]:
            names = ", ".join(f"`{n}`" for n in pmap)
            L.append(f"- {ep} — params: {names}")
        forms = d.get("forms", [])
        L.append(f"\n### HTML forms ({len(forms)})")
        if not forms:
            L.append("_None observed._")
        for fm in forms[:50]:
            fields = ", ".join(f"`{i['name']}`({i['type']})" for i in fm["inputs"]) or "—"
            L.append(f"- {fm['method']} {fm['action']} — fields: {fields}")
        L.append("")

        schemas = d.get("api_schemas", [])
        if schemas:
            L.append(f"### API schemas ({len(schemas)})")
            for s in schemas:
                L.append(f"- {s['type']}: {s['url']} ({s['path_count']} documented paths)")
            L.append("")
        ph = d.get("passive_hosts", [])
        if ph:
            L.append(f"### Passive OSINT hosts ({len(ph)})")
            for h in ph[:60]:
                L.append(f"- {h}")
            L.append("")

        # Endpoint type breakdown
        etypes = d.get("endpoint_types", {})
        if etypes:
            counts: Dict[str, int] = {}
            for t in etypes.values():
                counts[t] = counts.get(t, 0) + 1
            L.append("### Endpoint types")
            L.append(", ".join(f"{k}: {v}" for k, v in sorted(counts.items())) + "\n")
        outliers = d.get("response_outliers", [])
        if outliers:
            L.append(f"### Response outliers ({len(outliers)})")
            L.append("_Endpoints that behaved differently from the templated bulk — "
                     "review these first._")
            for u in outliers[:40]:
                L.append(f"- {u}")
            L.append("")
        rec = d.get("recovered_sources", [])
        if rec:
            L.append(f"### Recovered source files via sourcemaps ({len(rec)})")
            for s in rec[:60]:
                L.append(f"- {s}")
            L.append("")
        cs = d.get("js_callsites", [])
        if cs:
            L.append(f"### JS call-site endpoints ({len(cs)})")
            for u in cs[:60]:
                L.append(f"- {u}")
            L.append("")

        checklist = d.get("owasp_top10_checklist", [])
        L.append(f"## OWASP Top-10 Manual Testing Checklist ({len(checklist)})")
        L.append("> Generated from passive signals. These are **leads to verify by "
                 "hand**, in scope — the tool sends no payloads and confirms nothing.\n")
        if not checklist:
            L.append("_No candidates flagged from the current map._")
        # group by OWASP category for readability
        by_cat: Dict[str, List[Dict[str, str]]] = {}
        for item in checklist:
            by_cat.setdefault(item["owasp"], []).append(item)
        for cat, items in by_cat.items():
            L.append(f"### {cat}")
            for it in items:
                L.append(f"- [ ] **{it['surface']}** — {it['manual_check']} "
                         f"({it['cwe']}; {it['note']})")
            L.append("")

        L.append("## References")
        L.append("- OWASP Top 10: https://owasp.org/Top10/")
        L.append("- CWE: https://cwe.mitre.org/")
        L.append("- OWASP Web Security Testing Guide\n")

        with open(path, "w") as fh:
            fh.write("\n".join(L))
        return path


# --------------------------------------------------------------------------- #
#  Logging
# --------------------------------------------------------------------------- #
def make_logger(cfg: Config) -> logging.Logger:
    cfg.ensure_dirs()
    logger = logging.getLogger("titan")
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()
    fh = logging.FileHandler(os.path.join(cfg.logs_dir, "titan.log"))
    fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    fh.setLevel(logging.DEBUG)
    logger.addHandler(fh)
    sh = logging.StreamHandler()
    sh.setLevel(logging.WARNING)
    logger.addHandler(sh)
    return logger


# --------------------------------------------------------------------------- #
#  Interactive UI
# --------------------------------------------------------------------------- #
BANNER = r"""
╔════════════════════════════════════════════════╗
║   TITAN_HUNTER  ·  Authorized Recon Framework   ║
║       legal bug bounty / security research       ║
╚════════════════════════════════════════════════╝
"""


def _ask(prompt: str, default: str = "") -> str:
    if _HAVE_RICH:
        return Prompt.ask(prompt, default=default)
    raw = input(f"{prompt} [{default}]: ").strip()
    return raw or default


def _ask_int(prompt: str, default: int) -> int:
    try:
        return int(_ask(prompt, str(default)))
    except ValueError:
        return default


def print_menu():
    if _HAVE_RICH:
        _console.print(Panel.fit(BANNER, border_style="cyan"))
        t = Table(box=box.SIMPLE, show_header=False)
        t.add_column("k", style="bold cyan")
        t.add_column("v")
        rows = [
            ("1", "Smart Recon Scan"), ("2", "Deep JavaScript Intelligence"),
            ("3", "API Discovery"), ("4", "GraphQL Mapping"),
            ("5", "Secret Discovery"), ("6", "Smart Analysis Engine"),
            ("7", "Generate Professional Report"), ("8", "Configure Target"),
            ("9", "Configure Output Paths"), ("10", "Resume Previous Session"),
            ("11", "Historical Comparison"), ("12", "Export Results"),
            ("13", "[bold]FULL AUTO  (scan → JS/API/GraphQL/secrets → report)[/bold]"),
            ("14", "AI Report Analyzer (Claude reviews your latest report)"),
            ("15", "Test Anthropic API key"),
            ("16", "AI Assistant chat (read files, propose edits, no shell)"),
            ("0", "Exit"),
        ]
        for k, v in rows:
            t.add_row(f"[{k}]", v)
        _console.print(t)
    else:
        print(BANNER)
        for line in ("[1] Smart Recon Scan", "[2] Deep JavaScript Intelligence",
                     "[3] API Discovery", "[4] GraphQL Mapping",
                     "[5] Secret Discovery", "[6] Smart Analysis Engine",
                     "[7] Generate Professional Report", "[8] Configure Target",
                     "[9] Configure Output Paths", "[10] Resume Previous Session",
                     "[11] Historical Comparison", "[12] Export Results",
                     "[13] FULL AUTO  (scan -> JS/API/GraphQL/secrets -> report)",
                     "[14] AI Report Analyzer (Claude reviews your latest report)",
                     "[15] Test Anthropic API key",
                     "[16] AI Assistant chat (read files, propose edits, no shell)",
                     "[0] Exit"):
            print(line)


def show_config(cfg: Config):
    k = cfg.anthropic_api_key
    key_disp = (k[:7] + "…" + k[-4:]) if k and len(k) > 12 else ("(set)" if k else "(none)")
    info = (f"target={cfg.target or '(unset)'}  scope={cfg.scope_file or 'target-only'}\n"
            f"base_dir={cfg.base_dir}  workers={cfg.workers}  rate={cfg.rate_limit}/s\n"
            f"timeout={cfg.timeout}s  retries={cfg.retries}  depth={cfg.crawl_depth}  "
            f"max_pages={cfg.max_pages}\nUA={cfg.user_agent_profile}  "
            f"graphql_introspection={cfg.graphql_introspection}\n"
            f"anthropic_key={key_disp}  model={cfg.anthropic_model}")
    if _HAVE_RICH:
        _console.print(Panel(info, title="Current Config", border_style="green"))
    else:
        print("--- Config ---\n" + info)


def configure_target(cfg: Config):
    cfg.target = _ask("Target domain or URL", cfg.target)
    sf = _ask("Scope file path (blank = target-only)", cfg.scope_file)
    cfg.scope_file = sf
    cfg.workers = _ask_int("Workers", cfg.workers)
    cfg.timeout = float(_ask("Timeout (s)", str(cfg.timeout)))
    cfg.retries = _ask_int("Retries", cfg.retries)
    cfg.rate_limit = float(_ask("Rate limit (req/s)", str(cfg.rate_limit)))
    cfg.crawl_depth = _ask_int("Crawl depth", cfg.crawl_depth)
    cfg.max_pages = _ask_int("Max pages", cfg.max_pages)
    ua = _ask(f"User-Agent profile {list(USER_AGENT_PROFILES)}", cfg.user_agent_profile)
    if ua in USER_AGENT_PROFILES:
        cfg.user_agent_profile = ua
    gi = _ask("Enable GraphQL introspection probe? (y/n)",
              "y" if cfg.graphql_introspection else "n")
    cfg.graphql_introspection = gi.lower().startswith("y")
    # AI analyzer (option 14) — used only to send the report to api.anthropic.com.
    cur = cfg.anthropic_api_key
    masked = (cur[:7] + "…" + cur[-4:]) if cur and len(cur) > 12 else ("(set)" if cur else "(none)")
    new_key = _ask(f"Anthropic API key for AI analysis [current: {masked}] "
                   "(blank to keep, '-' to clear)", "")
    if new_key == "-":
        cfg.anthropic_api_key = ""
    elif new_key.strip():
        cfg.anthropic_api_key = new_key.strip()
    cfg.anthropic_model = _ask("Anthropic model", cfg.anthropic_model)
    _console.print("[green]Target configured.[/green]" if _HAVE_RICH else "Target configured.")


def configure_output(cfg: Config):
    cfg.base_dir = _ask("Base output directory", cfg.base_dir)
    cfg.ensure_dirs()
    _console.print(f"Output dirs ready under {cfg.base_dir}")


def _require_target(cfg: Config) -> bool:
    if not cfg.target:
        msg = "Set a target first (option 8)."
        _console.print(f"[red]{msg}[/red]" if _HAVE_RICH else msg)
        return False
    return True


async def run_full_scan(cfg: Config, logger: logging.Logger) -> Scanner:
    scanner = Scanner(cfg, logger)
    _console.print(f"Scope: {scanner.scope.describe()}")
    if _HAVE_RICH:
        with Progress(SpinnerColumn(), TextColumn("[cyan]{task.description}"),
                      transient=True) as p:
            p.add_task("Crawling in-scope assets…", total=None)
            await scanner.crawl()
            await scanner.graphql_probe()
    else:
        print("Crawling… (this can take a while on mobile networks)")
        await scanner.crawl()
        await scanner.graphql_probe()
    _console.print(
        f"Done. assets={len(scanner.discovered_assets)} "
        f"js={len(scanner.javascript_files)} api={len(scanner.api_endpoints)} "
        f"graphql={len(scanner.graphql_endpoints)} "
        f"findings={len(scanner.findings.findings)}")
    # When nothing came back, tell the operator *why* instead of a silent zero.
    if len(scanner.discovered_assets) == 0:
        _print_diagnostics(scanner)
    return scanner


def _print_diagnostics(scanner: Scanner) -> None:
    d = scanner.diagnostics
    lines = ["[!] No assets discovered — diagnostics:"]
    if d.get("blocked"):
        lines.append(f"    >>> UPSTREAM BLOCK DETECTED: {d['blocked']}")
        lines.append("    The responses came from a content filter / WAF / CDN / "
                     "censorship page, NOT from the target. Recon results are "
                     "inconclusive. Confirm the target is in an authorized program "
                     "and reachable from an authorized network before retrying.")
    if d.get("reason"):
        lines.append(f"    reason: {d['reason']}")
    for att in d.get("seed_attempts", []):
        st = att["status"]
        err = att["error"] or "-"
        lines.append(f"    tried {att['url']}  status={st}  err={err}  "
                     f"bytes={att['bytes']}  final={att.get('final_url')}")
    if d.get("seed_redirected_out_of_scope"):
        lines.append(f"    NOTE: seed redirected OUT OF SCOPE -> "
                     f"{d['seed_redirected_out_of_scope']} (add it to your scope "
                     f"file if authorized).")
    if not d.get("seed_attempts"):
        lines.append("    (no seed attempts recorded — check the target value)")
    lines.append("    tips: verify the target is reachable from this device "
                 "(try `curl -I https://<target>`), raise --timeout, lower --rate, "
                 "or widen scope with a *.domain rule.")
    text = "\n".join(lines)
    if _HAVE_RICH:
        _console.print(Panel(text, title="Diagnostics", border_style="red"))
    else:
        print(text)


def _print_map(scanner: Scanner) -> None:
    """Compact end-to-end 'map' of what was discovered."""
    s = scanner
    blocks = [
        ("Seed", [s.seed_used or "(none)"]),
        ("Technologies", sorted(s.smart.technologies) or ["(none)"]),
        ("Assets", sorted(s.discovered_assets)[:30] or ["(none)"]),
        ("API endpoints", sorted(s.api_endpoints)[:30] or ["(none)"]),
        ("JavaScript files", sorted(s.javascript_files)[:30] or ["(none)"]),
        ("GraphQL endpoints", sorted(s.graphql_endpoints) or ["(none)"]),
        ("Parameterized endpoints", [f"{ep}  [{', '.join(pm)}]"
                                     for ep, pm in s.param_map.items()] or ["(none)"]),
        ("HTML forms", [f"{fm['method']} {fm['action']} "
                        f"({len(fm['inputs'])} fields)" for fm in s.forms] or ["(none)"]),
        ("API schemas", [f"{x['type']} {x['url']} ({x['path_count']} paths)"
                         for x in s.schemas] or ["(none)"]),
        ("Passive OSINT hosts", sorted(s.passive_hosts)[:30] or ["(none)"]),
        ("Top-10 manual checklist", [f"{c['owasp']}: {c['surface']}"
                                     for c in s.top10_checklist] or ["(none)"]),
        ("JS call-site endpoints", sorted(s.js.callsites)[:30] or ["(none)"]),
        ("Recovered sources (sourcemaps)", sorted(set(s.js.recovered_sources))[:30] or ["(none)"]),
        ("Response outliers", s.response_outliers[:30] or ["(none)"]),
        ("Secret candidates", [f"{h['confidence']} - {h['type']} ({h['source']})"
                               for h in s.js.secret_hits] or ["(none)"]),
        ("Findings", [f"{f.severity}/{f.confidence} - {f.title}"
                      + (f" (x{len(f.affected_urls)})" if len(f.affected_urls) > 1 else "")
                      for f in s.findings.findings] or ["(none)"]),
    ]
    for title, items in blocks:
        if _HAVE_RICH:
            _console.print(f"[bold cyan]{title}[/bold cyan] ({len(items)})")
        else:
            print(f"== {title} ({len(items)}) ==")
        for it in items[:30]:
            _console.print(f"   - {it}")


def run_full_pipeline(cfg: Config, logger: logging.Logger,
                      sessions: "SessionManager") -> Optional[Scanner]:
    """
    One-shot: recon crawl -> JS intel -> API mapping -> GraphQL -> secrets ->
    smart analysis -> evidence -> JSON+Markdown report -> session save +
    historical diff. This is the 'do everything' option.
    """
    if not _require_target(cfg):
        return None
    scanner = asyncio.run(run_full_scan(cfg, logger))  # crawl + graphql probe

    rep = Reporter(cfg, scanner)
    json_path = rep.json_report()
    md_path = rep.markdown_report()
    checklist_path = rep.checklist_report()

    diff = sessions.compare(scanner)   # compare BEFORE overwriting saved session
    session_path = sessions.save(scanner)

    _print_map(scanner)
    _console.print("")
    _console.print(f"JSON report     -> {json_path}")
    _console.print(f"Markdown report -> {md_path}")
    _console.print(f"Manual checklist -> {checklist_path}")
    _console.print(f"Session         -> {session_path}")
    if "new_assets" in diff:
        _console.print(f"Delta vs last   -> +{len(diff.get('new_assets', []))} new, "
                       f"-{len(diff.get('removed_assets', []))} removed assets")
    return scanner


def _latest_json_report(cfg: Config) -> Optional[str]:
    """Find the most recent JSON report file in the reports dir."""
    cfg.ensure_dirs()
    cands = []
    try:
        for name in os.listdir(cfg.reports_dir):
            if name.startswith("report_") and name.endswith(".json"):
                p = os.path.join(cfg.reports_dir, name)
                cands.append((os.path.getmtime(p), p))
    except OSError:
        return None
    if not cands:
        return None
    cands.sort(reverse=True)
    return cands[0][1]


def run_test_api_key(cfg: Config, logger: logging.Logger) -> None:
    """Option 15: round-trip the configured key against api.anthropic.com."""
    if not cfg.anthropic_api_key:
        prompted = _ask("No key on file. Paste one to test (blank to cancel)", "")
        if not prompted.strip():
            _console.print("Cancelled.")
            return
        key_to_test = prompted.strip()
    else:
        key_to_test = None  # use stored
    az = AIReportAnalyzer(cfg, logger)
    ok, msg = az.test_key(key_to_test)
    if ok:
        _console.print(f"[green]OK[/green]  {msg}" if _HAVE_RICH else f"OK  {msg}")
    else:
        _console.print(f"[red]FAIL[/red]  {msg}" if _HAVE_RICH else f"FAIL  {msg}")


def run_ai_analysis(cfg: Config, logger: logging.Logger) -> None:
    """Option 14: send the latest JSON report to Claude for review/triage and
    write the response next to it as an .ai.md companion file."""
    if not cfg.anthropic_api_key:
        _console.print("No Anthropic API key configured. Use option 8 to set it, "
                       "or option 15 to test a key first.")
        return
    report_path = _latest_json_report(cfg)
    if not report_path:
        _console.print("No JSON report found. Run option 13 first.")
        return
    pick = _ask(f"Analyze latest report?\n  {report_path}\n(or paste another path)",
                report_path)
    report_path = pick.strip() or report_path
    if not os.path.isfile(report_path):
        _console.print(f"File not found: {report_path}")
        return
    _console.print(f"Sending report to Claude for analysis: {report_path}")
    az = AIReportAnalyzer(cfg, logger)
    ok, text = az.analyze_report(report_path)
    if not ok:
        _console.print(f"[red]Analysis failed:[/red] {text}" if _HAVE_RICH
                       else f"Analysis failed: {text}")
        return
    out = report_path.rsplit(".", 1)[0] + ".ai.md"
    header = (f"# AI Report Analysis\n\n"
              f"_Source report:_ `{os.path.basename(report_path)}`  \n"
              f"_Model:_ `{cfg.anthropic_model}`  \n"
              f"_Generated:_ {now_iso()}\n\n"
              f"> Review/triage by an LLM based on the report contents. The "
              f"model did not contact the target and produced no payloads. "
              f"All verification remains manual, in scope.\n\n---\n\n")
    try:
        with open(out, "w") as fh:
            fh.write(header + text + "\n")
    except OSError as exc:
        _console.print(f"Could not write {out}: {exc}")
        return
    _console.print(f"AI analysis → {out}")
    if _HAVE_RICH:
        _console.print(Panel(text[:1500] + ("…" if len(text) > 1500 else ""),
                             title="AI Analysis (preview)", border_style="cyan"))
    else:
        print("--- AI Analysis (preview) ---")
        print(text[:1500])


SHELL_REQUEST_HINTS = (
    "install ", "apt ", "apt-get ", "pkg ", "pip install", "npm install",
    "run ", "execute ", "exec ", "spawn ", "subprocess",
    "ثبت", "ثبّت", "ثبّتلي", "نزّل", "نفّذ", "شغّل", "شغل ",
)


def _looks_like_shell_request(text: str) -> bool:
    low = text.lower()
    return any(h in low for h in SHELL_REQUEST_HINTS)


def run_ai_chat(cfg: Config, logger: logging.Logger) -> None:
    """
    Option 16: a chat assistant for reports / code / logs. Reads paths the
    operator types. Proposes edits as diffs and waits for y/N. Never executes
    shell commands or installs anything.
    """
    if not cfg.anthropic_api_key:
        _console.print("No Anthropic API key configured. Use option 8 to set it, "
                       "or option 15 to test a key first.")
        return

    assistant = AIAssistant(cfg, logger)
    _console.print("AI Assistant ready. Commands:")
    _console.print("  /file <path>     attach a file or folder to the next message")
    _console.print("  /clear           clear conversation history")
    _console.print("  /exit            return to menu")
    _console.print("Notes: the assistant cannot execute shell or install anything. "
                   "Edits are proposed as diffs and require y/N to save.\n")

    pending_files: List[Dict[str, str]] = []
    pending_notes: List[str] = []

    while True:
        try:
            user = _ask("you", "").strip()
        except (EOFError, KeyboardInterrupt):
            _console.print("\n(returning to menu)")
            return
        if not user:
            continue
        if user in ("/exit", "/quit", "exit", "quit"):
            return
        if user == "/clear":
            assistant.history.clear()
            pending_files.clear()
            pending_notes.clear()
            _console.print("(history cleared)")
            continue
        if user.startswith("/file "):
            path = user[len("/file "):].strip()
            files, notes = AIAssistant.read_path(path)
            pending_files.extend(files)
            pending_notes.extend(notes)
            _console.print(f"(attached {len(files)} file(s) from {path})")
            for n in notes:
                _console.print(f"   note: {n}")
            continue

        # Up-front guard on shell-style requests. The system prompt already
        # instructs Claude to refuse, but we add a local nudge so the operator
        # sees the policy immediately and doesn't burn an API call.
        if _looks_like_shell_request(user) and not pending_files:
            _console.print("[yellow]This assistant doesn't run shell commands or "
                           "install packages. I can explain how to do it, but "
                           "you'll need to run it yourself in your terminal.[/yellow]"
                           if _HAVE_RICH else
                           "This assistant doesn't run shell or install packages. "
                           "I can explain the command; you run it in your terminal.")

        ok, reply = assistant.ask(user, pending_files, pending_notes)
        pending_files = []   # files are consumed per turn
        pending_notes = []
        if not ok:
            _console.print(f"[red]error:[/red] {reply}" if _HAVE_RICH else f"error: {reply}")
            continue

        # Print the textual reply (minus the edit block; that's handled below).
        edits = AIAssistant.extract_edits(reply)
        textual = AIAssistant.FILE_BLOCK_RE.sub("", reply).strip()
        if _HAVE_RICH:
            _console.print(Panel(textual or "(no prose)", title="claude",
                                 border_style="cyan"))
        else:
            print("claude:")
            print(textual)

        # If Claude proposed a file edit, diff and ask.
        for ed in edits:
            path = ed["path"]
            new_content = ed["new_content"]
            if not AIAssistant._is_editable(path):
                _console.print(f"[yellow]refused: {path} is outside the editable "
                               "allowlist (extension or protected location).[/yellow]"
                               if _HAVE_RICH else
                               f"refused: {path} not editable.")
                continue
            diff = AIAssistant.make_diff(path, new_content)
            if _HAVE_RICH:
                _console.print(Panel(diff[:6000] + ("\n... (diff truncated)"
                                                    if len(diff) > 6000 else ""),
                                     title=f"proposed diff: {path}",
                                     border_style="magenta"))
            else:
                print(f"--- proposed diff: {path} ---")
                print(diff[:6000])
            confirm = _ask(f"apply edit to {path}? (y/N)", "N").strip().lower()
            if confirm == "y":
                ok2, msg = AIAssistant.apply_edit(path, new_content)
                _console.print(("[green]" if ok2 else "[red]") +
                               f"{msg}[/]" if _HAVE_RICH else msg)
            else:
                _console.print("(skipped)")


def interactive(cfg: Config):
    logger = make_logger(cfg)
    sessions = SessionManager(cfg)
    scanner: Optional[Scanner] = None

    while True:
        print_menu()
        choice = _ask("Select", "0").strip()

        if choice == "0":
            _console.print("Bye. Stay in scope. ✌" if _HAVE_RICH else "Bye.")
            return
        elif choice == "13":
            result = run_full_pipeline(cfg, logger, sessions)
            if result is not None:
                scanner = result
        elif choice == "14":
            run_ai_analysis(cfg, logger)
        elif choice == "15":
            run_test_api_key(cfg, logger)
        elif choice == "16":
            run_ai_chat(cfg, logger)
        elif choice == "8":
            configure_target(cfg)
            show_config(cfg)
        elif choice == "9":
            configure_output(cfg)
        elif choice in {"1", "2", "3", "4", "5", "6"}:
            if not _require_target(cfg):
                continue
            scanner = asyncio.run(run_full_scan(cfg, logger))
            path = sessions.save(scanner)
            _console.print(f"Session saved → {path}")
            # Topic-specific summaries
            if choice == "2":
                _console.print(f"JS files: {len(scanner.javascript_files)}, "
                               f"secret candidates: {len(scanner.js.secret_hits)}")
            elif choice == "3":
                for a in sorted(scanner.api_endpoints)[:40]:
                    _console.print(f"  API  {a}")
            elif choice == "4":
                for g in sorted(scanner.graphql_endpoints):
                    _console.print(f"  GraphQL  {g}")
            elif choice == "5":
                for h in scanner.js.secret_hits:
                    _console.print(f"  {h['confidence']:>6}  {h['type']}  ({h['source']})")
        elif choice == "7":
            if scanner is None:
                _console.print("Run a scan first.")
                continue
            rep = Reporter(cfg, scanner)
            out = []
            if "json" in cfg.report_formats:
                out.append(rep.json_report())
            if "markdown" in cfg.report_formats:
                out.append(rep.markdown_report())
            out.append(rep.checklist_report())
            for o in out:
                _console.print(f"Report → {o}")
        elif choice == "10":
            state = sessions.load()
            if not state:
                _console.print("No saved session for this target.")
            else:
                _console.print(f"Loaded session from {state.get('saved_at')}: "
                               f"{len(state.get('discovered_assets', []))} assets, "
                               f"{len(state.get('findings', []))} findings.")
        elif choice == "11":
            if scanner is None:
                _console.print("Run a scan first, then compare.")
                continue
            diff = sessions.compare(scanner)
            for k, v in diff.items():
                _console.print(f"[bold]{k}[/bold]: {len(v)}" if _HAVE_RICH else f"{k}: {len(v)}")
                for item in v[:20]:
                    _console.print(f"   {item}")
        elif choice == "12":
            if scanner is None:
                _console.print("Nothing to export yet.")
                continue
            rep = Reporter(cfg, scanner)
            _console.print(f"JSON → {rep.json_report()}")
            _console.print(f"Markdown → {rep.markdown_report()}")
            _console.print(f"Checklist → {rep.checklist_report()}")
        else:
            _console.print("Unknown option.")


# --------------------------------------------------------------------------- #
#  CLI entry
# --------------------------------------------------------------------------- #
def build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="TITAN_HUNTER — authorized recon & analysis (Termux-friendly)")
    p.add_argument("-t", "--target", help="target domain or URL")
    p.add_argument("-s", "--scope", help="scope file (one host or *.host per line)")
    p.add_argument("-o", "--output", help="base output dir (default /sdcard/TITAN or ~/TITAN)")
    p.add_argument("--workers", type=int, default=8)
    p.add_argument("--rate", type=float, default=5.0, help="requests/sec")
    p.add_argument("--depth", type=int, default=2)
    p.add_argument("--timeout", type=float, default=15.0)
    p.add_argument("--ua", choices=list(USER_AGENT_PROFILES), default="default")
    p.add_argument("--graphql-introspection", action="store_true")
    p.add_argument("--no-tls-verify", action="store_true")
    p.add_argument("--scan", action="store_true", help="run a full scan non-interactively")
    p.add_argument("--report", action="store_true", help="write reports after --scan")
    p.add_argument("--config", help="load config JSON")
    return p


def cfg_from_args(a: argparse.Namespace) -> Config:
    if a.config and os.path.isfile(a.config):
        cfg = Config.load(a.config)
    else:
        cfg = Config()
    if a.target:
        cfg.target = a.target
    if a.scope:
        cfg.scope_file = a.scope
    if a.output:
        cfg.base_dir = a.output
    cfg.workers = a.workers
    cfg.rate_limit = a.rate
    cfg.crawl_depth = a.depth
    cfg.timeout = a.timeout
    cfg.user_agent_profile = a.ua
    cfg.graphql_introspection = a.graphql_introspection
    cfg.verify_tls = not a.no_tls_verify
    return cfg


def main(argv: Optional[List[str]] = None) -> int:
    args = build_argparser().parse_args(argv)
    cfg = cfg_from_args(args)
    cfg.ensure_dirs()

    if not _HAVE_AIOHTTP:
        _console.print("[yellow]aiohttp not found — using requests/urllib fallback. "
                       "For best concurrency: pip install aiohttp[/yellow]"
                       if _HAVE_RICH else
                       "Note: aiohttp not found; using fallback. pip install aiohttp")

    if args.scan:
        if not cfg.target:
            print("error: --scan requires --target", file=sys.stderr)
            return 2
        logger = make_logger(cfg)
        scanner = asyncio.run(run_full_scan(cfg, logger))
        SessionManager(cfg).save(scanner)
        if args.report:
            rep = Reporter(cfg, scanner)
            print("JSON:", rep.json_report())
            print("Markdown:", rep.markdown_report())
            print("Checklist:", rep.checklist_report())
        return 0

    interactive(cfg)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\ninterrupted")
        sys.exit(130)
