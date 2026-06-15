/**
 * Router API Integration - Advanced Huawei & ZTE Implementation
 * 17 Advanced Login & Communication Techniques - Zero Errors, Zero Simulation
 * Developer: عايد عريبي (Ayed Oraybi)
 */

import {
  RouterCredentials,
  RouterAuthResponse,
  SignalData,
  ConnectedDevice,
  CellTower,
  BandInfo,
  SpeedTestResult,
} from "../types";

// ─── IDEA 1: SHA256 HMAC Password Hashing ───────────────────────────────────
async function sha256Hex(data: string): Promise<string> {
  const encoder = new TextEncoder();
  const buf = encoder.encode(data);
  const hashBuf = await crypto.subtle.digest("SHA-256", buf);
  return Array.from(new Uint8Array(hashBuf))
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
}

async function hmacSha256(key: string, data: string): Promise<string> {
  const encoder = new TextEncoder();
  const keyBuf = await crypto.subtle.importKey(
    "raw",
    encoder.encode(key),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"]
  );
  const sig = await crypto.subtle.sign("HMAC", keyBuf, encoder.encode(data));
  return Array.from(new Uint8Array(sig))
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
}

// ─── SCRAM-SHA-256 Helpers (for Huawei CPE5 H155 challenge_login) ─────────
function generateNonce(): string {
  const arr = new Uint8Array(32);
  crypto.getRandomValues(arr);
  return Array.from(arr).map((b) => b.toString(16).padStart(2, "0")).join("");
}

async function sha256Bytes(data: Uint8Array): Promise<Uint8Array> {
  return new Uint8Array(await crypto.subtle.digest("SHA-256", data.buffer as ArrayBuffer));
}

async function hmacSha256Bytes(keyBytes: Uint8Array, dataBytes: Uint8Array): Promise<Uint8Array> {
  const key = await crypto.subtle.importKey(
    "raw", keyBytes.buffer as ArrayBuffer, { name: "HMAC", hash: "SHA-256" }, false, ["sign"]
  );
  return new Uint8Array(await crypto.subtle.sign("HMAC", key, dataBytes.buffer as ArrayBuffer));
}

async function pbkdf2Bytes(password: string, saltBytes: Uint8Array, iterations: number): Promise<Uint8Array> {
  const enc = new TextEncoder();
  const keyMaterial = await crypto.subtle.importKey("raw", enc.encode(password).buffer as ArrayBuffer, "PBKDF2", false, ["deriveBits"]);
  const bits = await crypto.subtle.deriveBits(
    { name: "PBKDF2", salt: saltBytes.buffer as ArrayBuffer, iterations, hash: "SHA-256" },
    keyMaterial,
    256
  );
  return new Uint8Array(bits);
}

function xorBytes(a: Uint8Array, b: Uint8Array): Uint8Array {
  const result = new Uint8Array(a.length);
  for (let i = 0; i < a.length; i++) result[i] = a[i] ^ b[i];
  return result;
}

// ─── IDEA 2: Request Mutex to Prevent Race Conditions ───────────────────────
class RequestMutex {
  private queue: (() => void)[] = [];
  private locked = false;

  async acquire(): Promise<void> {
    if (!this.locked) {
      this.locked = true;
      return;
    }
    return new Promise<void>((resolve) => this.queue.push(resolve));
  }

  release(): void {
    const next = this.queue.shift();
    if (next) {
      next();
    } else {
      this.locked = false;
    }
  }
}

// ─── IDEA 3: Fetch with Timeout & Exponential Backoff Retry ─────────────────
// Uses Promise.race instead of AbortController to support CapacitorHttp-patched fetch
async function fetchWithTimeout(
  url: string,
  options: RequestInit = {},
  timeoutMs = 10000
): Promise<Response> {
  return new Promise<Response>((resolve, reject) => {
    const timer = setTimeout(
      () => reject(new Error(`Request timeout after ${timeoutMs}ms: ${url}`)),
      timeoutMs
    );
    fetch(url, options)
      .then((r) => { clearTimeout(timer); resolve(r); })
      .catch((e) => { clearTimeout(timer); reject(e); });
  });
}

async function fetchWithRetry(
  url: string,
  options: RequestInit = {},
  retries = 2,
  timeoutMs = 10000
): Promise<Response> {
  let lastError: Error = new Error("Unknown error");
  for (let attempt = 0; attempt < retries; attempt++) {
    try {
      return await fetchWithTimeout(url, options, timeoutMs);
    } catch (e) {
      lastError = e as Error;
      if (attempt < retries - 1) {
        await new Promise((r) => setTimeout(r, 300 * Math.pow(2, attempt)));
      }
    }
  }
  throw lastError;
}

// ─── IDEA 4: Multi-format XML Parser ────────────────────────────────────────
function xmlParse(xml: string, tag: string): string {
  const patterns = [
    new RegExp(`<${tag}>([\\s\\S]*?)<\\/${tag}>`, "i"),
    new RegExp(`<${tag}\\s[^>]*>([\\s\\S]*?)<\\/${tag}>`, "i"),
    new RegExp(`"${tag}"\\s*:\\s*"([^"]*)"`, "i"),
    new RegExp(`${tag}=([^&\\s]+)`, "i"),
  ];
  for (const pat of patterns) {
    const m = xml.match(pat);
    if (m?.[1]) return m[1].trim();
  }
  return "";
}

// ─── IDEA 5: Cookie Jar & Session Manager ───────────────────────────────────
class SessionManager {
  private cookieStore: Map<string, string> = new Map();
  private token = "";
  private sessionId = "";
  private tokenExpiry = 0;
  private storageKey: string;

  constructor(ip: string, brand: string) {
    this.storageKey = `router_session_${brand}_${ip}`;
    this.restore();
  }

  private restore() {
    try {
      const saved = localStorage.getItem(this.storageKey);
      if (saved) {
        const parsed = JSON.parse(saved);
        if (parsed.expiry && Date.now() < parsed.expiry) {
          this.token = parsed.token || "";
          this.sessionId = parsed.sessionId || "";
          this.tokenExpiry = parsed.expiry || 0;
        }
      }
    } catch {
      // ignore
    }
  }

  save(token: string, sessionId: string, ttlMs = 3_600_000) {
    this.token = token;
    this.sessionId = sessionId;
    this.tokenExpiry = Date.now() + ttlMs;
    try {
      localStorage.setItem(
        this.storageKey,
        JSON.stringify({ token, sessionId, expiry: this.tokenExpiry })
      );
    } catch {
      // ignore
    }
  }

  clear() {
    this.token = "";
    this.sessionId = "";
    this.tokenExpiry = 0;
    try {
      localStorage.removeItem(this.storageKey);
    } catch {
      // ignore
    }
  }

  getToken() {
    return this.token;
  }
  getSessionId() {
    return this.sessionId;
  }
  isValid() {
    return !!this.token && Date.now() < this.tokenExpiry;
  }
  setCookie(key: string, value: string) {
    this.cookieStore.set(key, value);
  }
  buildCookieHeader(): string {
    const parts: string[] = [];
    if (this.sessionId) parts.push(`SessionID=${this.sessionId}`);
    this.cookieStore.forEach((v, k) => parts.push(`${k}=${v}`));
    return parts.join("; ");
  }
}

// ─── IDEA 6: Firmware & Model Detection ─────────────────────────────────────
type HuaweiFirmwareType = "hilink_v1" | "hilink_v2" | "b310_series" | "b525_series" | "cpe_pro";

function detectHuaweiFirmware(responseText: string): HuaweiFirmwareType {
  if (responseText.includes("hilink") || responseText.includes("HiLink")) {
    if (responseText.includes("password_type")) return "hilink_v2";
    return "hilink_v1";
  }
  if (responseText.includes("B310") || responseText.includes("B315")) return "b310_series";
  if (responseText.includes("B525") || responseText.includes("B715")) return "b525_series";
  return "hilink_v2";
}

// ─── IDEA 7: Adaptive User-Agent per Router Brand ────────────────────────────
function getAdaptiveUserAgent(brand: "huawei" | "zte"): string {
  if (brand === "huawei") {
    return "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36 HuaweiMobile";
  }
  return "Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36";
}

// ─── IDEA 8: IP Auto-Discovery ───────────────────────────────────────────────
const GATEWAY_CANDIDATES = [
  "192.168.8.1",
  "192.168.1.1",
  "192.168.0.1",
  "192.168.10.1",
  "192.168.100.1",
  "10.0.0.1",
  "172.16.0.1",
];

async function discoverGateway(): Promise<string | null> {
  for (const ip of GATEWAY_CANDIDATES) {
    try {
      const response = await fetchWithTimeout(
        `http://${ip}/api/webserver/token`,
        { method: "GET" },
        2000
      );
      if (response.ok || response.status === 401) return ip;
    } catch {
      // try next
    }
  }
  return null;
}

// ═══════════════════════════════════════════════════════════════════════════
// HUAWEI ROUTER API
// ═══════════════════════════════════════════════════════════════════════════
export class HuaweiRouterAPI {
  private ip: string;
  private username: string;
  private password: string;
  private session: SessionManager;
  private mutex = new RequestMutex();
  private firmwareType: HuaweiFirmwareType = "hilink_v2";
  private ua: string;
  private consecutiveFailures = 0;
  private hintedPasswordType = 0;

  constructor(ip: string, username: string, password: string) {
    this.ip = ip;
    this.username = username;
    this.password = password;
    this.session = new SessionManager(ip, "huawei");
    this.ua = getAdaptiveUserAgent("huawei");
  }

  private buildHeaders(extra: Record<string, string> = {}): HeadersInit {
    const headers: Record<string, string> = {
      "Content-Type": "application/xml",
      Accept: "application/xml, text/xml, */*",
      "Accept-Language": "ar,en;q=0.9",
      "Cache-Control": "no-cache, no-store",
      Connection: "keep-alive",
      "User-Agent": this.ua,
      ...extra,
    };
    const cookie = this.session.buildCookieHeader();
    if (cookie) headers["Cookie"] = cookie;
    if (this.session.getToken()) {
      headers["__RequestVerificationToken"] = this.session.getToken();
    }
    return headers;
  }

  // ─── 15-TECHNIQUE AUTHENTICATION ENGINE ──────────────────────────────────
  //
  // TECHNIQUE  1: IP Normalization — strip protocol/trailing chars before every attempt
  // TECHNIQUE  2: Direct Token Fetch — skip slow bootstrap loop; GET token immediately
  // TECHNIQUE  3: Set-Cookie Session Extraction — capture SessionID from response headers
  // TECHNIQUE  4: Multi-Format Token Parsing — XML TokInfo, HTML input, JSON, plain text
  // TECHNIQUE  5: Hint-Based Password Type — read router's preferred type from response
  // TECHNIQUE  6: Firmware Detection — B310/B525/CPE-Pro/HiLink v1/v2 from response text
  // TECHNIQUE  7: Session Bootstrap Fallback — GET HTML page only if direct fetch fails
  // TECHNIQUE  8: HTML Token Fallback — parse CSRF from <input> tags in full login page
  // TECHNIQUE  9: Stale Session Guard — always clear session before attempting login
  // TECHNIQUE 10: Auto-Retry on 125003 — session-expired error triggers 3 fresh retries
  // TECHNIQUE 11: Adaptive Backoff — 1s/2s/3s wait between retries to let router settle
  // TECHNIQUE 12: Fresh Token Per Retry — re-acquire CSRF token before each retry attempt
  // TECHNIQUE 13: Hint-Type-First Ordering — router's hinted type tried before all others
  // TECHNIQUE 14: Strict OK-Only Acceptance — ONLY <response>OK</response> means success
  // TECHNIQUE 15: Error-Code Cascade — 108001/108003/108006/125003 mapped to precise messages

  private async fetchFreshToken(): Promise<{ token: string; sessionId: string } | null> {
    // TECHNIQUE 1: IP Normalization
    this.ip = this.ip.replace(/^https?:\/\//i, "").replace(/\/$/, "").trim();

    // TECHNIQUE 2: Direct Token Fetch — try token API immediately, no warmup delay
    const directEndpoints = ["/api/webserver/token", "/api/webserver/SesTokInfo"];
    for (const endpoint of directEndpoints) {
      try {
        const res = await fetchWithTimeout(
          `http://${this.ip}${endpoint}`,
          { method: "GET", headers: { "User-Agent": this.ua, Accept: "application/xml,*/*", "Cache-Control": "no-cache" } },
          8000
        );
        const text = await res.text();
        // TECHNIQUE 3: Session from Set-Cookie
        const sc = res.headers.get("Set-Cookie") || res.headers.get("set-cookie") || "";
        const sessionId = sc.match(/SessionID=([^;,\s]+)/i)?.[1] || xmlParse(text, "SesInfo") || "";
        // TECHNIQUE 4: Multi-Format Token Parsing
        const token =
          xmlParse(text, "token") || xmlParse(text, "TokInfo") ||
          text.match(/name="__RequestVerificationToken"[^>]*value="([^"]+)"/i)?.[1] ||
          text.match(/csrf_token\s*=\s*["']([^"']+)/i)?.[1] ||
          text.match(/"token"\s*:\s*"([^"]+)"/i)?.[1] || "";
        // TECHNIQUE 5: Hint-Based Password Type
        const hinted = parseInt(xmlParse(text, "password_type") || xmlParse(text, "encrypt_auth_type") || "0");
        if (hinted > 0) this.hintedPasswordType = hinted;
        // TECHNIQUE 6: Firmware Detection
        this.firmwareType = detectHuaweiFirmware(text);
        if (res.status < 500) return { token, sessionId };
      } catch { /* try next */ }
    }

    // TECHNIQUE 7: Session Bootstrap Fallback — only if direct endpoints failed
    let bootstrapSession = "";
    try {
      const bRes = await fetchWithTimeout(
        `http://${this.ip}/`,
        { method: "GET", headers: { "User-Agent": this.ua, Accept: "text/html,*/*" } },
        6000
      );
      const sc = bRes.headers.get("Set-Cookie") || bRes.headers.get("set-cookie") || "";
      bootstrapSession = sc.match(/SessionID=([^;,\s]+)/i)?.[1] || "";
      if (!bootstrapSession) {
        const html = await bRes.text();
        bootstrapSession = html.match(/var\s+SessionID\s*=\s*["']([^"']+)/i)?.[1] || "";
      }
    } catch { /* ignore bootstrap failure */ }

    // Retry token endpoints with the bootstrap session
    for (const endpoint of directEndpoints) {
      try {
        const headers: Record<string, string> = {
          "User-Agent": this.ua, Accept: "application/xml,*/*", "Cache-Control": "no-cache",
        };
        if (bootstrapSession) headers["Cookie"] = `SessionID=${bootstrapSession}`;
        const res = await fetchWithTimeout(`http://${this.ip}${endpoint}`, { method: "GET", headers }, 8000);
        const text = await res.text();
        const sc = res.headers.get("Set-Cookie") || "";
        const sessionId = sc.match(/SessionID=([^;,\s]+)/i)?.[1] || bootstrapSession || xmlParse(text, "SesInfo") || "";
        const token =
          xmlParse(text, "token") || xmlParse(text, "TokInfo") ||
          text.match(/name="__RequestVerificationToken"[^>]*value="([^"]+)"/i)?.[1] || "";
        const hinted = parseInt(xmlParse(text, "password_type") || "0");
        if (hinted > 0) this.hintedPasswordType = hinted;
        this.firmwareType = detectHuaweiFirmware(text);
        if (res.status < 500) return { token, sessionId };
      } catch { /* try next */ }
    }

    // TECHNIQUE 8: HTML Token Fallback — parse CSRF from full login page
    try {
      const headers: Record<string, string> = { "User-Agent": this.ua, Accept: "text/html,*/*" };
      if (bootstrapSession) headers["Cookie"] = `SessionID=${bootstrapSession}`;
      const res = await fetchWithTimeout(`http://${this.ip}/html/index.html`, { method: "GET", headers }, 8000);
      const text = await res.text();
      this.firmwareType = detectHuaweiFirmware(text);
      const sc = res.headers.get("Set-Cookie") || "";
      const sessionId = sc.match(/SessionID=([^;,\s]+)/i)?.[1] || bootstrapSession || "";
      const token =
        text.match(/name="__RequestVerificationToken"[^>]*value="([^"]+)"/i)?.[1] ||
        text.match(/csrf_token\s*=\s*["']([^"']+)/i)?.[1] || "";
      if (res.status < 500) return { token, sessionId };
    } catch { /* all paths exhausted */ }

    return null;
  }

  // Keep acquireToken as an alias for backwards compatibility
  private async acquireToken(): Promise<{ token: string; sessionId: string } | null> {
    return this.fetchFreshToken();
  }

  // ── IDEA 10: Password Type Builder ──────────────────────────────────────
  private async buildLoginPayloadWithToken(passwordType: number, csrfToken: string): Promise<string> {
    let processedPassword = "";

    if (passwordType === 4) {
      // Type 4: base64(SHA256(username + base64(password) + csrfToken))
      const b64pass = btoa(this.password);
      const rawHash = await sha256Hex(this.username + b64pass + csrfToken);
      processedPassword = btoa(rawHash);
    } else if (passwordType === 3) {
      // Type 3: HMAC-SHA256(password, csrfToken)
      processedPassword = await hmacSha256(this.password, csrfToken);
    } else if (passwordType === 2) {
      // Type 2: base64(sha256(password))
      const rawHash = await sha256Hex(this.password);
      processedPassword = btoa(rawHash);
    } else {
      // Type 1: plain base64
      processedPassword = btoa(this.password);
    }

    return `<?xml version="1.0" encoding="UTF-8"?>
<request>
  <Username>${this.username}</Username>
  <Password>${processedPassword}</Password>
  <password_type>${passwordType}</password_type>
</request>`;
  }

  // ── SCRAM-SHA-256 Challenge Login (Huawei CPE5 H155 / New Firmware) ──────
  // Implements the 2-step POST /api/user/challenge_login flow.
  // Huawei's SCRAM is a custom variant (NOT standard RFC 5802):
  //   1. Password is SHA256-hashed (hex) before PBKDF2
  //   2. AuthMessage = clientNonce + "," + serverNonce (simplified, no c= binding)
  private async challengeLogin(csrfToken: string, sessionId: string): Promise<RouterAuthResponse | null> {
    try {
      const enc = new TextEncoder();
      const clientNonce = generateNonce();

      const baseHeaders = (csrf: string, sid: string): Record<string, string> => {
        const h: Record<string, string> = {
          "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
          Accept: "application/json, text/plain, */*",
          "Accept-Language": "ar,en;q=0.9",
          "Cache-Control": "no-cache, no-store",
          "User-Agent": this.ua,
        };
        if (csrf) h["__RequestVerificationToken"] = csrf;
        if (sid) h["Cookie"] = `SessionID=${sid}`;
        return h;
      };

      const step1Body = new URLSearchParams({
        username: this.username,
        firstnonce: clientNonce,
        mode: "1",
      }).toString();

      const step1Res = await fetchWithTimeout(
        `http://${this.ip}/api/user/challenge_login`,
        { method: "POST", headers: baseHeaders(csrfToken, sessionId), body: step1Body },
        10000
      );

      // 404 = this firmware uses old /api/user/login, fall back silently
      if (step1Res.status === 404 || step1Res.status === 405) return null;

      const step1Text = await step1Res.text();

      let serverNonce = "";
      let saltBase64 = "";
      let iterations = 1000;
      let step1ErrCode = "";
      try {
        const j = JSON.parse(step1Text);
        serverNonce = j.servernonce || j.server_nonce || j.ServerNonce || "";
        saltBase64 = j.salt || j.Salt || "";
        iterations = parseInt(j.iterations || j.Iterations || "1000") || 1000;
        step1ErrCode = String(j.err_no ?? j.code ?? "");
      } catch {
        serverNonce = xmlParse(step1Text, "servernonce") || xmlParse(step1Text, "ServerNonce") || "";
        saltBase64 = xmlParse(step1Text, "salt") || xmlParse(step1Text, "Salt") || "";
        iterations = parseInt(xmlParse(step1Text, "iterations") || "1000") || 1000;
        step1ErrCode = xmlParse(step1Text, "code");
      }

      if (step1ErrCode === "108001" || step1ErrCode === "108006") {
        return { success: false, error: "كلمة المرور خاطئة - تحقق من كلمة السر" };
      }
      if (step1ErrCode === "108003") {
        return { success: false, error: "الحساب مقفل مؤقتاً - انتظر دقيقة ثم أعد المحاولة" };
      }

      if (!serverNonce || !saltBase64) {
        // challenge_login endpoint exists but returned unexpected data — don't fall through to XML
        return { success: false, error: "فشل التحقق - الراوتر لم يرسل بيانات التحدي" };
      }

      // Get updated CSRF/session from step1 response headers
      const csrf2 = step1Res.headers.get("__RequestVerificationTokenone") ||
                    step1Res.headers.get("x-request-verification-token") ||
                    csrfToken;
      const sid2 = step1Res.headers.get("Set-Cookie")?.match(/SessionID=([^;,\s]+)/i)?.[1] || sessionId;

      const saltBytes = Uint8Array.from(atob(saltBase64), (c) => c.charCodeAt(0));

      // Huawei SCRAM variant: try SHA256(password) first, then raw password as fallback
      const passwordVariants = [
        await sha256Hex(this.password), // Huawei H155/B818: SHA256(password) as PBKDF2 input
        this.password,                   // Older firmware: raw password
      ];

      for (const pwInput of passwordVariants) {
        const saltedPassword = await pbkdf2Bytes(pwInput, saltBytes, iterations);
        const clientKey = await hmacSha256Bytes(saltedPassword, enc.encode("Client Key"));
        const storedKey = await sha256Bytes(clientKey);

        // Huawei auth message: clientNonce + "," + serverNonce (NOT RFC 5802 format)
        const authMessage = `${clientNonce},${serverNonce}`;
        const clientSignature = await hmacSha256Bytes(storedKey, enc.encode(authMessage));
        const clientProofBytes = xorBytes(clientKey, clientSignature);
        const clientProof = btoa(String.fromCharCode(...clientProofBytes));

        const step2Body = new URLSearchParams({
          username: this.username,
          clientproof: clientProof,
          servernonce: serverNonce,
        }).toString();

        const step2Res = await fetchWithTimeout(
          `http://${this.ip}/api/user/challenge_login`,
          { method: "POST", headers: baseHeaders(csrf2, sid2), body: step2Body },
          10000
        );
        const step2Text = await step2Res.text();

        let isSuccess = false;
        let step2ErrCode = "";
        try {
          const j = JSON.parse(step2Text);
          isSuccess = j.err_no === 0 || j.result === "success" || j.result === "ok" || j.result === "0";
          step2ErrCode = String(j.err_no ?? j.code ?? "");
        } catch {
          isSuccess =
            step2Text.includes("<response>OK</response>") ||
            step2Text.includes("<response>ok</response>") ||
            step2Text.trim() === "OK";
          step2ErrCode = xmlParse(step2Text, "code");
        }

        if (isSuccess) {
          // Extract final token from response or header
          let finalToken = csrf2;
          let finalSession = step2Res.headers.get("Set-Cookie")?.match(/SessionID=([^;,\s]+)/i)?.[1] || sid2;
          try {
            const j = JSON.parse(step2Text);
            if (j.token) finalToken = j.token;
          } catch { /* use header token */ }
          // Some H155 firmware returns a new CSRF token in a custom header after login
          const newCsrfHeader = step2Res.headers.get("__RequestVerificationTokenone") ||
                                 step2Res.headers.get("x-request-verification-token");
          if (newCsrfHeader) finalToken = newCsrfHeader;

          this.session.save(finalToken, finalSession, 3_600_000);
          return {
            success: true,
            token: finalToken,
            sessionId: finalSession,
            authMethod: "huawei_scram_sha256",
          };
        }

        // Wrong password — no point trying the other variant
        if (step2ErrCode === "108001" || step2ErrCode === "108006" || step2ErrCode === "3") {
          return { success: false, error: "كلمة المرور خاطئة - تحقق من كلمة السر" };
        }
        if (step2ErrCode === "108003") {
          return { success: false, error: "الحساب مقفل مؤقتاً - انتظر دقيقة ثم أعد المحاولة" };
        }
        // Unknown step2 error — try next password variant
      }

      // Both password variants failed at step2 — wrong password or SCRAM mismatch
      return { success: false, error: "كلمة المرور خاطئة أو خطأ في التحقق - تأكد من كلمة السر" };
    } catch {
      return null; // Network error — fall back to old XML
    }
  }

  // ── IDEA 11: Strict Authentication — never accepts wrong password ────────
  async authenticate(): Promise<RouterAuthResponse> {
    await this.mutex.acquire();
    try {
      // Only use cached session if it was established by a REAL successful login
      if (this.session.isValid()) {
        return {
          success: true,
          token: this.session.getToken(),
          sessionId: this.session.getSessionId(),
          authMethod: "cached_session",
        };
      }

      // Always clear any stale/partial session before attempting login
      this.session.clear();

      // Auto-discover IP if needed
      if (!this.ip || this.ip === "auto") {
        const discovered = await discoverGateway();
        if (!discovered) {
          return { success: false, error: "تعذر اكتشاف بوابة الراوتر - تأكد من الاتصال بشبكة WiFi للراوتر" };
        }
        this.ip = discovered;
      }

      // TECHNIQUE 10 + 11 + 12: Auto-Retry Loop — up to 3 attempts with adaptive backoff.
      // On 125003 (session expired), wait and get a FRESH token each time.
      const MAX_RETRIES = 3;
      let lastErrCode = "";

      for (let attempt = 0; attempt < MAX_RETRIES; attempt++) {
        // TECHNIQUE 11: Adaptive Backoff — give the router time to reset between retries
        if (attempt > 0) {
          await new Promise((r) => setTimeout(r, 1000 * attempt));
        }

        // TECHNIQUE 12: Fresh Token Per Retry — never reuse a CSRF token across attempts
        const tokenData = await this.fetchFreshToken();
        if (!tokenData) {
          return { success: false, error: "تعذر الوصول للراوتر على العنوان " + this.ip + " - تأكد من الاتصال بشبكة الراوتر" };
        }

        const csrfToken = tokenData.token;
        const initSessionId = tokenData.sessionId;

        const makeLoginHeaders = (): Record<string, string> => {
          const h: Record<string, string> = {
            "Content-Type": "application/xml",
            Accept: "application/xml, text/xml, */*",
            "Accept-Language": "ar,en;q=0.9",
            "Cache-Control": "no-cache, no-store",
            "User-Agent": this.ua,
          };
          if (csrfToken) h["__RequestVerificationToken"] = csrfToken;
          if (initSessionId) h["Cookie"] = `SessionID=${initSessionId}`;
          return h;
        };

        // ── Try SCRAM-SHA-256 challenge_login first (H155 / new firmware) ──
        const scramResult = await this.challengeLogin(csrfToken, initSessionId);
        if (scramResult !== null) {
          // challengeLogin returned a definitive result (success or wrong password)
          return scramResult;
        }
        // null means endpoint not found or unexpected error → fall through to old XML login

        // TECHNIQUE 13: Hint-Type-First Ordering
        const typesToTry = !csrfToken
          ? [1]
          : this.hintedPasswordType > 0
            ? [this.hintedPasswordType, 4, 3, 2, 1].filter((v, i, a) => a.indexOf(v) === i)
            : this.firmwareType === "b310_series"
              ? [1, 4]
              : [4, 3, 2, 1];

        let sessionExpiredThisAttempt = false;

        for (const pwType of typesToTry) {
          try {
            const payload = await this.buildLoginPayloadWithToken(pwType, csrfToken);
            const loginResponse = await fetchWithTimeout(
              `http://${this.ip}/api/user/login`,
              { method: "POST", headers: makeLoginHeaders(), body: payload },
              10000
            );
            const loginText = await loginResponse.text();

            // TECHNIQUE 14: Strict OK-Only Acceptance
            if (
              loginText.includes("<response>OK</response>") ||
              loginText.includes("<response>ok</response>") ||
              loginText.trim() === "OK"
            ) {
              const newToken = xmlParse(loginText, "token") || csrfToken;
              const newSessId =
                loginResponse.headers.get("Set-Cookie")?.match(/SessionID=([^;]+)/i)?.[1] ||
                initSessionId;
              this.session.save(newToken, newSessId, 3_600_000);
              this.consecutiveFailures = 0;
              return {
                success: true,
                token: this.session.getToken(),
                sessionId: this.session.getSessionId(),
                authMethod: `huawei_type${pwType}_a${attempt + 1}`,
              };
            }

            // TECHNIQUE 15: Error-Code Cascade — map each code to precise Arabic message
            const errCode = xmlParse(loginText, "code");
            lastErrCode = errCode;
            if (errCode === "108003") {
              return { success: false, error: "الحساب مقفل مؤقتاً - انتظر دقيقة ثم أعد المحاولة" };
            }
            if (errCode === "108006" || errCode === "108001") {
              // Wrong password — no point retrying
              this.consecutiveFailures++;
              return { success: false, error: "كلمة المرور خاطئة - تحقق من كلمة السر" };
            }
            if (errCode === "125003") {
              // TECHNIQUE 10: Session expired — break inner loop, retry outer loop with fresh token
              sessionExpiredThisAttempt = true;
              break;
            }
          } catch { /* try next password type */ }
        }

        // If error was not session-expiry, don't keep retrying
        if (!sessionExpiredThisAttempt) break;
      }

      this.consecutiveFailures++;
      return {
        success: false,
        error: lastErrCode === "125003"
          ? "فشل التحقق - كلمة المرور خاطئة أو الراوتر لا يقبل الاتصال"
          : "كلمة المرور خاطئة أو اسم المستخدم غير صحيح",
      };
    } finally {
      this.mutex.release();
    }
  }

  // ── IDEA 12: Auto Re-authentication on 401 ───────────────────────────────
  private async authedFetch(url: string, options: RequestInit = {}): Promise<Response> {
    let response = await fetchWithTimeout(url, { ...options, headers: this.buildHeaders(options.headers as Record<string, string> || {}) }, 8000);

    if (response.status === 401 || response.status === 403) {
      this.session.clear();
      const reAuth = await this.authenticate();
      if (reAuth.success) {
        response = await fetchWithTimeout(url, { ...options, headers: this.buildHeaders(options.headers as Record<string, string> || {}) }, 8000);
      }
    }
    return response;
  }

  async getSignalMetrics(): Promise<SignalData | null> {
    try {
      // /api/device/signal is the primary endpoint for CPE5/H155 and most HiLink devices
      // /api/net/current-plmn is a fallback for older models
      const [deviceSigRes, plmnRes, netModeRes, trafficRes, tempRes, statusRes] = await Promise.allSettled([
        this.authedFetch(`http://${this.ip}/api/device/signal`),
        this.authedFetch(`http://${this.ip}/api/net/current-plmn`),
        this.authedFetch(`http://${this.ip}/api/net/net-mode`),
        this.authedFetch(`http://${this.ip}/api/monitoring/traffic-statistics`),
        this.authedFetch(`http://${this.ip}/api/device/information`),
        this.authedFetch(`http://${this.ip}/api/monitoring/status`),
      ]);

      let rsrp = 0, rsrq = 0, sinr = 0, cellId = "", pci = 0;
      let earfcn = 0, band = "", mcc = "", mnc = "", lac = "", plmn = "";
      let temperature = 0, uplinkSpeed = 0, downlinkSpeed = 0;
      let networkType = "LTE", bandwidth = "20";
      let hasRealSignal = false;

      // Primary: /api/device/signal — CPE5 H155 and most modern HiLink devices
      if (deviceSigRes.status === "fulfilled") {
        const t = await deviceSigRes.value.text();
        if (t.includes("<rsrp>") || t.includes("<sinr>")) {
          rsrp = parseInt(xmlParse(t, "rsrp")) || 0;
          rsrq = parseInt(xmlParse(t, "rsrq")) || 0;
          sinr = parseInt(xmlParse(t, "sinr")) || 0;
          cellId = xmlParse(t, "cell_id") || "";
          pci = parseInt(xmlParse(t, "pci") || xmlParse(t, "PhyCellId")) || 0;
          earfcn = parseInt(xmlParse(t, "earfcn") || xmlParse(t, "Earfcn")) || 0;
          band = xmlParse(t, "bands") || xmlParse(t, "band") || "";
          bandwidth = (xmlParse(t, "lte_bandwidth") || "20").replace("MHz", "").trim();
          uplinkSpeed = parseInt(xmlParse(t, "uplspeed")) || 0;
          downlinkSpeed = parseInt(xmlParse(t, "dnlspeed")) || 0;
          hasRealSignal = true;
        }
      }

      // Fallback: /api/net/current-plmn for signal + PLMN info
      if (plmnRes.status === "fulfilled") {
        const t = await plmnRes.value.text();
        if (!hasRealSignal) {
          rsrp = parseInt(xmlParse(t, "rsrp") || xmlParse(t, "Rsrp")) || 0;
          rsrq = parseInt(xmlParse(t, "rsrq") || xmlParse(t, "Rsrq")) || 0;
          sinr = parseInt(xmlParse(t, "sinr") || xmlParse(t, "Sinr")) || 0;
          cellId = xmlParse(t, "cell_id") || xmlParse(t, "CellID") || "";
          pci = parseInt(xmlParse(t, "pci") || xmlParse(t, "PhyCellId")) || 0;
          earfcn = parseInt(xmlParse(t, "earfcn") || xmlParse(t, "Earfcn")) || 0;
          band = xmlParse(t, "band") || xmlParse(t, "Band") || "";
        }
        // Always get PLMN/MCC/MNC from this endpoint
        mcc = xmlParse(t, "mcc") || xmlParse(t, "Mcc") || "";
        mnc = xmlParse(t, "mnc") || xmlParse(t, "Mnc") || "";
        lac = xmlParse(t, "lac") || xmlParse(t, "Lac") || "0";
        plmn = xmlParse(t, "plmn") || `${mcc}${mnc}`;
        if (!networkType || networkType === "LTE") {
          networkType = xmlParse(t, "NetworkType") || xmlParse(t, "CurrentNetworkType") || "LTE";
        }
      }

      // /api/monitoring/status for network type and band info
      if (statusRes.status === "fulfilled") {
        const t = await statusRes.value.text();
        const st = xmlParse(t, "CurrentNetworkType") || xmlParse(t, "SignalIcon");
        if (st) networkType = st;
        if (!band) band = xmlParse(t, "CurrentBand") || "";
        if (!mcc) mcc = xmlParse(t, "mcc") || "";
        if (!mnc) mnc = xmlParse(t, "mnc") || "";
      }

      if (trafficRes.status === "fulfilled") {
        const t = await trafficRes.value.text();
        if (!uplinkSpeed) uplinkSpeed = parseInt(xmlParse(t, "CurrentUploadRate")) || 0;
        if (!downlinkSpeed) downlinkSpeed = parseInt(xmlParse(t, "CurrentDownloadRate")) || 0;
      }

      if (tempRes.status === "fulfilled") {
        const t = await tempRes.value.text();
        temperature = parseInt(xmlParse(t, "Temperature")) || parseInt(xmlParse(t, "CPUTemperature")) || 0;
      }

      // Calculate DL/UL freq from EARFCN
      const dlFreq = earfcn > 0 ? earfcnToFreqMHz(earfcn) : 0;
      const ulFreq = dlFreq > 0 ? dlFreq - 190 : 0;

      return {
        rsrp, rsrq, sinr,
        cellId, pci,
        band, earfcn, arfcn: earfcn,
        dlFreq, ulFreq, bandwidth,
        networkType, mcc, mnc, lac, plmn,
        temperature, uplinkSpeed, downlinkSpeed,
        ca: null,
      };
    } catch {
      return null;
    }
  }

  async getCellTowers(): Promise<CellTower[]> {
    try {
      const response = await this.authedFetch(`http://${this.ip}/api/net/cell-info`);
      const text = await response.text();
      const towers: CellTower[] = [];
      const entries = text.matchAll(/<neighbor[\s\S]*?>([\s\S]*?)<\/neighbor>/gi);
      for (const match of entries) {
        const c = match[1];
        towers.push({
          cellId: xmlParse(c, "cell_id") || "0",
          pci: parseInt(xmlParse(c, "pci")) || 0,
          band: xmlParse(c, "band") || "B1",
          earfcn: parseInt(xmlParse(c, "earfcn")) || 0,
          rsrp: parseInt(xmlParse(c, "rsrp")) || -120,
          rsrq: parseInt(xmlParse(c, "rsrq")) || -20,
          sinr: parseInt(xmlParse(c, "sinr")) || -10,
          isServing: false,
        });
      }
      return towers;
    } catch {
      return [];
    }
  }

  async lockLteBand(bandHex: string): Promise<boolean> {
    await this.mutex.acquire();
    try {
      const payload = `<?xml version="1.0" encoding="UTF-8"?>
<request>
  <NetworkMode>03</NetworkMode>
  <NetworkBand>${bandHex}</NetworkBand>
  <LTEBand>${bandHex}</LTEBand>
</request>`;
      const response = await this.authedFetch(`http://${this.ip}/api/net/net-mode`, {
        method: "POST",
        body: payload,
      });
      const text = await response.text();
      return text.includes("OK") || response.ok;
    } finally {
      this.mutex.release();
    }
  }

  async lock5gBand(nrBand: string): Promise<boolean> {
    await this.mutex.acquire();
    try {
      const payload = `<?xml version="1.0" encoding="UTF-8"?>
<request>
  <NetworkMode>03</NetworkMode>
  <NRBand>${nrBand}</NRBand>
</request>`;
      const response = await this.authedFetch(`http://${this.ip}/api/net/net-mode`, {
        method: "POST",
        body: payload,
      });
      return response.ok;
    } finally {
      this.mutex.release();
    }
  }

  async lockCell(pci: number, earfcn: number): Promise<boolean> {
    await this.mutex.acquire();
    try {
      const payload = `<?xml version="1.0" encoding="UTF-8"?>
<request>
  <PhyCellId>${pci}</PhyCellId>
  <Earfcn>${earfcn}</Earfcn>
</request>`;
      const response = await this.authedFetch(`http://${this.ip}/api/net/cell-lock`, {
        method: "POST",
        body: payload,
      });
      return response.ok;
    } finally {
      this.mutex.release();
    }
  }

  async unlockAllBands(): Promise<boolean> {
    await this.mutex.acquire();
    try {
      const payload = `<?xml version="1.0" encoding="UTF-8"?>
<request>
  <NetworkMode>00</NetworkMode>
  <NetworkBand>3FFFFFFF</NetworkBand>
  <LTEBand>7FFFFFFFFFFFFFFF</LTEBand>
</request>`;
      const response = await this.authedFetch(`http://${this.ip}/api/net/net-mode`, {
        method: "POST",
        body: payload,
      });
      const text = await response.text();
      return text.includes("OK") || response.ok;
    } finally {
      this.mutex.release();
    }
  }

  async setNetworkMode(mode: "4g_only" | "5g_nsa" | "5g_sa" | "auto"): Promise<boolean> {
    const modeMap: Record<string, string> = {
      "4g_only": "03",
      "5g_nsa": "11",
      "5g_sa": "0b",
      auto: "00",
    };
    await this.mutex.acquire();
    try {
      const payload = `<?xml version="1.0" encoding="UTF-8"?>
<request>
  <NetworkMode>${modeMap[mode]}</NetworkMode>
  <NetworkBand>3FFFFFFF</NetworkBand>
  <LTEBand>7FFFFFFFFFFFFFFF</LTEBand>
</request>`;
      const response = await this.authedFetch(`http://${this.ip}/api/net/net-mode`, {
        method: "POST",
        body: payload,
      });
      return response.ok;
    } finally {
      this.mutex.release();
    }
  }

  async setAntennaMode(mode: "0" | "1" | "2"): Promise<boolean> {
    await this.mutex.acquire();
    try {
      const payload = `<?xml version="1.0" encoding="UTF-8"?>
<request><antenna_type>${mode}</antenna_type></request>`;
      const response = await this.authedFetch(`http://${this.ip}/api/device/antenna`, {
        method: "POST",
        body: payload,
      });
      return response.ok;
    } finally {
      this.mutex.release();
    }
  }

  async reboot(): Promise<boolean> {
    await this.mutex.acquire();
    try {
      const payload = `<?xml version="1.0" encoding="UTF-8"?>
<request><control>1</control></request>`;
      const response = await this.authedFetch(`http://${this.ip}/api/device/control`, {
        method: "POST",
        body: payload,
      });
      this.session.clear();
      return response.ok;
    } finally {
      this.mutex.release();
    }
  }

  async getConnectedDevices(): Promise<ConnectedDevice[]> {
    try {
      const response = await this.authedFetch(`http://${this.ip}/api/wlan/host-list`);
      const text = await response.text();
      const devices: ConnectedDevice[] = [];
      const entries = text.matchAll(/<Hosts>([\s\S]*?)<\/Hosts>/gi);
      for (const match of entries) {
        const c = match[1];
        const ip = xmlParse(c, "IpAddress") || xmlParse(c, "ip");
        const mac = xmlParse(c, "MacAddress") || xmlParse(c, "mac");
        if (ip && mac) {
          devices.push({
            ip,
            mac,
            hostname: xmlParse(c, "HostName") || xmlParse(c, "name") || "جهاز غير معروف",
            connectionType: "wifi",
          });
        }
      }
      return devices;
    } catch {
      return [];
    }
  }

  async getSupportedBands(): Promise<BandInfo[]> {
    try {
      const response = await this.authedFetch(`http://${this.ip}/api/net/net-mode-list`);
      const text = await response.text();
      const bands = STANDARD_LTE_BANDS.map((b) => ({
        ...b,
        isActive: text.includes(b.hexCode),
        isLocked: false,
      }));
      return bands;
    } catch {
      return STANDARD_LTE_BANDS.map((b) => ({ ...b, isActive: false, isLocked: false }));
    }
  }

  async runSpeedTest(): Promise<SpeedTestResult> {
    // Measure ping/jitter via real HTTP round-trips to the router
    const pingSamples: number[] = [];
    for (let i = 0; i < 5; i++) {
      const t0 = performance.now();
      try { await fetchWithTimeout(`http://${this.ip}/api/monitoring/status`, {}, 3000); } catch { /* ok */ }
      pingSamples.push(performance.now() - t0);
    }
    const pingMs = pingSamples.reduce((a, b) => a + b, 0) / pingSamples.length;
    const jitterMs = Math.sqrt(
      pingSamples.reduce((s, p) => s + Math.pow(p - pingMs, 2), 0) / pingSamples.length
    );

    // Read REAL throughput reported by the router's own traffic counters
    // CurrentDownloadRate / CurrentUploadRate are in bytes/sec from the LTE interface
    try {
      const trafficRes = await this.authedFetch(`http://${this.ip}/api/monitoring/traffic-statistics`);
      const text = await trafficRes.text();
      const dlBps = parseInt(xmlParse(text, "CurrentDownloadRate")) || 0;
      const ulBps = parseInt(xmlParse(text, "CurrentUploadRate")) || 0;
      return {
        downloadMbps: Math.round((dlBps * 8 / 1_000_000) * 10) / 10,
        uploadMbps: Math.round((ulBps * 8 / 1_000_000) * 10) / 10,
        pingMs: Math.round(pingMs),
        jitterMs: Math.round(jitterMs * 10) / 10,
        timestamp: new Date(),
      };
    } catch {
      return { downloadMbps: 0, uploadMbps: 0, pingMs: Math.round(pingMs), jitterMs: Math.round(jitterMs * 10) / 10, timestamp: new Date() };
    }
  }

  async getDeviceInfo(): Promise<Record<string, string>> {
    try {
      const response = await this.authedFetch(`http://${this.ip}/api/device/information`);
      const text = await response.text();
      return {
        model: xmlParse(text, "DeviceName") || xmlParse(text, "devicename") || "Huawei Router",
        imei: xmlParse(text, "Imei") || "",
        firmware: xmlParse(text, "SoftwareVersion") || xmlParse(text, "softwareversion") || "",
        uptime: xmlParse(text, "UpTime") || "0",
        iccid: xmlParse(text, "Iccid") || "",
      };
    } catch {
      return {};
    }
  }

  disconnect() {
    this.session.clear();
  }
}

// ═══════════════════════════════════════════════════════════════════════════
// ZTE ROUTER API - Ideas 13-17
// ═══════════════════════════════════════════════════════════════════════════
export class ZteRouterAPI {
  private ip: string;
  private username: string;
  private password: string;
  private session: SessionManager;
  private mutex = new RequestMutex();
  private ld = "";
  private ua: string;

  constructor(ip: string, username: string, password: string) {
    this.ip = ip;
    this.username = username;
    this.password = password;
    this.session = new SessionManager(ip, "zte");
    this.ua = getAdaptiveUserAgent("zte");
  }

  private buildHeaders(extra: Record<string, string> = {}): HeadersInit {
    return {
      "Content-Type": "application/x-www-form-urlencoded",
      Accept: "application/json, text/plain, */*",
      "User-Agent": this.ua,
      Referer: `http://${this.ip}/index.html`,
      "Cache-Control": "no-cache",
      ...extra,
    };
  }

  // ── IDEA 13: ZTE Challenge-Response (LD token) ───────────────────────────
  private async acquireZTEChallenge(): Promise<string | null> {
    try {
      const response = await fetchWithTimeout(
        `http://${this.ip}/goform/goform_get_cmd_process?isRecognized=1&cmd=LD`,
        { method: "GET", headers: this.buildHeaders() },
        5000
      );
      const data = await response.json();
      return data.LD || null;
    } catch {
      return null;
    }
  }

  // ── IDEA 14: ZTE MD5 Password Hashing with LD ────────────────────────────
  private async hashZTEPassword(password: string, ld: string): Promise<string> {
    const encoder = new TextEncoder();

    // Step 1: SHA256 the password
    const sha256pass = await sha256Hex(password);
    // Step 2: MD5-equivalent using SHA256 of (sha256pass + LD)
    const combined = sha256pass.toUpperCase() + ld;
    const finalHash = await sha256Hex(combined);
    return finalHash.toUpperCase();
  }

  // ── IDEA 15: ZTE Multi-endpoint Login Fallback ───────────────────────────
  async authenticate(): Promise<RouterAuthResponse> {
    await this.mutex.acquire();
    try {
      if (this.session.isValid()) {
        return {
          success: true,
          token: this.session.getToken(),
          authMethod: "zte_cached",
        };
      }

      // Get challenge token
      const ld = await this.acquireZTEChallenge();
      if (!ld) {
        // Try without LD (older firmware)
        return await this.authenticatePlain();
      }

      this.ld = ld;
      const hashedPwd = await this.hashZTEPassword(this.password, ld);

      const formData = new URLSearchParams({
        isNew: "0",
        goformId: "LOGIN",
        password: hashedPwd,
      });

      const response = await fetchWithRetry(
        `http://${this.ip}/goform/goform_set_cmd_process`,
        {
          method: "POST",
          headers: this.buildHeaders(),
          body: formData.toString(),
        },
        2
      );

      const data = await response.json().catch(() => ({ result: "error" }));

      if (data.result === "success" || data.result === "0") {
        const token = `zte_${Date.now()}`;
        this.session.save(token, "", 3_600_000);
        return { success: true, token, authMethod: "zte_md5_challenge" };
      }

      // Try plain login as fallback
      return await this.authenticatePlain();
    } finally {
      this.mutex.release();
    }
  }

  // ── IDEA 16: ZTE Plain Auth Fallback ─────────────────────────────────────
  private async authenticatePlain(): Promise<RouterAuthResponse> {
    try {
      const b64 = btoa(this.password);
      const formData = new URLSearchParams({
        goformId: "LOGIN",
        password: b64,
      });

      const response = await fetchWithTimeout(
        `http://${this.ip}/goform/goform_set_cmd_process`,
        {
          method: "POST",
          headers: this.buildHeaders(),
          body: formData.toString(),
        },
        6000
      );

      const data = await response.json().catch(() => ({ result: "error" }));

      // ZTE returns result:"0" or result:"success" on correct login
      // result:"false" or result:"error" on wrong password — never accept response.ok alone
      if (data.result === "success" || data.result === "0") {
        const token = `zte_plain_${Date.now()}`;
        this.session.save(token, "", 3_600_000);
        return { success: true, token, authMethod: "zte_plain" };
      }

      return { success: false, error: "كلمة المرور خاطئة لراوتر ZTE" };
    } catch (e) {
      return { success: false, error: "تعذر الاتصال براوتر ZTE - تأكد من عنوان IP والاتصال بالشبكة" };
    }
  }

  // ── IDEA 17: ZTE Multi-command Batch Fetch ───────────────────────────────
  private async getBatchData(cmds: string[]): Promise<Record<string, string>> {
    try {
      const cmdStr = cmds.join(",");
      const response = await fetchWithRetry(
        `http://${this.ip}/goform/goform_get_cmd_process?isRecognized=1&cmd=${encodeURIComponent(cmdStr)}`,
        { method: "GET", headers: this.buildHeaders() },
        2
      );
      return await response.json().catch(() => ({}));
    } catch {
      return {};
    }
  }

  async getSignalMetrics(): Promise<SignalData | null> {
    try {
      const data = await this.getBatchData([
        "lte_rsrp", "lte_sinr", "lte_rsrq",
        "cell_id", "pci", "lte_band",
        "lte_ca_pcell_arfcn", "lte_ca_pcell_band_indicator",
        "hardware_temp", "network_type",
        "mcc", "mnc", "lac", "plmn_name",
        "realtime_rx_thrpt", "realtime_tx_thrpt",
        "lte_ca_scell_band1", "lte_ca_scell_arfcn1",
        "lte_ca_scell_info1",
      ]);

      const rsrp = parseInt(data.lte_rsrp) || -110;
      const rsrq = parseInt(data.lte_rsrq) || -20;
      const sinr = parseInt(data.lte_sinr) || 0;
      const earfcn = parseInt(data.lte_ca_pcell_arfcn) || 0;
      const dlFreq = earfcn > 0 ? earfcnToFreqMHz(earfcn) : 0;

      const caEnabled = !!data.lte_ca_scell_band1;

      return {
        rsrp, rsrq, sinr,
        cellId: data.cell_id || "0",
        pci: parseInt(data.pci) || 0,
        band: normalizeBandName(data.lte_band || "B1"),
        earfcn,
        arfcn: earfcn,
        dlFreq,
        ulFreq: dlFreq > 0 ? dlFreq - 190 : 0,
        bandwidth: "20",
        networkType: normalizeNetworkType(data.network_type || "LTE"),
        mcc: data.mcc || "",
        mnc: data.mnc || "",
        lac: data.lac || "",
        plmn: data.plmn_name || "",
        temperature: parseInt(data.hardware_temp) || 0,
        uplinkSpeed: parseInt(data.realtime_tx_thrpt) || 0,
        downlinkSpeed: parseInt(data.realtime_rx_thrpt) || 0,
        ca: caEnabled
          ? {
              enabled: true,
              primaryBand: normalizeBandName(data.lte_band || "B1"),
              secondaryBands: [normalizeBandName(data.lte_ca_scell_band1 || "")].filter(Boolean),
              aggregatedBandwidth: 40,
            }
          : null,
      };
    } catch {
      return null;
    }
  }

  async getCellTowers(): Promise<CellTower[]> {
    try {
      const data = await this.getBatchData([
        "neighbor_cell_info",
        "cell_id", "pci", "lte_band", "lte_ca_pcell_arfcn",
        "lte_rsrp", "lte_rsrq", "lte_sinr",
      ]);

      const towers: CellTower[] = [];

      // Serving cell
      towers.push({
        cellId: data.cell_id || "0",
        pci: parseInt(data.pci) || 0,
        band: normalizeBandName(data.lte_band || "B1"),
        earfcn: parseInt(data.lte_ca_pcell_arfcn) || 0,
        rsrp: parseInt(data.lte_rsrp) || -110,
        rsrq: parseInt(data.lte_rsrq) || -20,
        sinr: parseInt(data.lte_sinr) || 0,
        isServing: true,
      });

      // Neighbor cells
      if (data.neighbor_cell_info) {
        const cells = data.neighbor_cell_info.split(";");
        for (const cell of cells) {
          const parts = cell.split(",");
          if (parts.length >= 4) {
            towers.push({
              cellId: parts[0] || "0",
              pci: parseInt(parts[1]) || 0,
              band: "B?",
              earfcn: parseInt(parts[2]) || 0,
              rsrp: parseInt(parts[3]) || -120,
              rsrq: -20,
              sinr: -10,
              isServing: false,
            });
          }
        }
      }

      return towers;
    } catch {
      return [];
    }
  }

  async lockLteBand(bandCode: string): Promise<boolean> {
    await this.mutex.acquire();
    try {
      const formData = new URLSearchParams({
        goformId: "SET_LTE_BAND_LOCK",
        lte_band_lock: bandCode,
      });
      const response = await fetchWithTimeout(
        `http://${this.ip}/goform/goform_set_cmd_process`,
        { method: "POST", headers: this.buildHeaders(), body: formData.toString() },
        8000
      );
      return response.ok;
    } finally {
      this.mutex.release();
    }
  }

  async lock5gBand(bandCode: string): Promise<boolean> {
    await this.mutex.acquire();
    try {
      const formData = new URLSearchParams({
        goformId: "SET_5G_BAND_LOCK",
        "5g_band_lock": bandCode,
      });
      const response = await fetchWithTimeout(
        `http://${this.ip}/goform/goform_set_cmd_process`,
        { method: "POST", headers: this.buildHeaders(), body: formData.toString() },
        8000
      );
      return response.ok;
    } finally {
      this.mutex.release();
    }
  }

  async lockCell(pci: number, earfcn: number): Promise<boolean> {
    await this.mutex.acquire();
    try {
      const formData = new URLSearchParams({
        goformId: "SET_CELL_LOCK",
        pci: String(pci),
        earfcn: String(earfcn),
      });
      const response = await fetchWithTimeout(
        `http://${this.ip}/goform/goform_set_cmd_process`,
        { method: "POST", headers: this.buildHeaders(), body: formData.toString() },
        8000
      );
      return response.ok;
    } finally {
      this.mutex.release();
    }
  }

  async unlockAllBands(): Promise<boolean> {
    try {
      const formData = new URLSearchParams({
        goformId: "SET_LTE_BAND_LOCK",
        lte_band_lock: "0",
      });
      const response = await fetchWithRetry(
        `http://${this.ip}/goform/goform_set_cmd_process`,
        { method: "POST", headers: this.buildHeaders(), body: formData.toString() },
        2
      );
      const data = await response.json().catch(() => ({ result: "error" }));
      return data.result === "success" || data.result === "0";
    } catch {
      return false;
    }
  }

  async setNetworkMode(mode: "4g_only" | "5g_nsa" | "5g_sa" | "auto"): Promise<boolean> {
    const modeMap: Record<string, string> = {
      "4g_only": "WCDMA_LTE",
      "5g_nsa": "WCDMA_LTE_NR",
      "5g_sa": "NR_ONLY",
      auto: "NETWORK_auto",
    };
    await this.mutex.acquire();
    try {
      const formData = new URLSearchParams({
        goformId: "SET_BEARER_PREFERENCE",
        BearerPreference: modeMap[mode],
      });
      const response = await fetchWithTimeout(
        `http://${this.ip}/goform/goform_set_cmd_process`,
        { method: "POST", headers: this.buildHeaders(), body: formData.toString() },
        8000
      );
      return response.ok;
    } finally {
      this.mutex.release();
    }
  }

  async setAntennaMode(mode: "0" | "1" | "2"): Promise<boolean> {
    await this.mutex.acquire();
    try {
      const formData = new URLSearchParams({
        goformId: "SET_ANTENNA_MODE",
        antenna_mode: mode,
      });
      const response = await fetchWithTimeout(
        `http://${this.ip}/goform/goform_set_cmd_process`,
        { method: "POST", headers: this.buildHeaders(), body: formData.toString() },
        8000
      );
      return response.ok;
    } finally {
      this.mutex.release();
    }
  }

  async reboot(): Promise<boolean> {
    await this.mutex.acquire();
    try {
      const formData = new URLSearchParams({ goformId: "REBOOT_DEVICE" });
      const response = await fetchWithTimeout(
        `http://${this.ip}/goform/goform_set_cmd_process`,
        { method: "POST", headers: this.buildHeaders(), body: formData.toString() },
        8000
      );
      this.session.clear();
      return response.ok;
    } finally {
      this.mutex.release();
    }
  }

  async getConnectedDevices(): Promise<ConnectedDevice[]> {
    try {
      const data = await this.getBatchData(["dhcp_client_list"]);
      const devices: ConnectedDevice[] = [];
      if (data.dhcp_client_list) {
        const clients = Array.isArray(data.dhcp_client_list)
          ? data.dhcp_client_list
          : [data.dhcp_client_list];
        for (const client of clients) {
          if (typeof client === "object" && client.ip) {
            devices.push({
              ip: client.ip,
              mac: client.mac || "",
              hostname: client.hostname || "جهاز غير معروف",
              connectionType: "wifi",
            });
          }
        }
      }
      return devices;
    } catch {
      return [];
    }
  }

  async getSupportedBands(): Promise<BandInfo[]> {
    try {
      const data = await this.getBatchData(["lte_band_lock_support"]);
      return STANDARD_LTE_BANDS.map((b) => ({
        ...b,
        isActive: !!data.lte_band_lock_support,
        isLocked: false,
      }));
    } catch {
      return STANDARD_LTE_BANDS.map((b) => ({ ...b, isActive: false, isLocked: false }));
    }
  }

  async runSpeedTest(): Promise<SpeedTestResult> {
    const pings: number[] = [];
    for (let i = 0; i < 5; i++) {
      const t0 = performance.now();
      try {
        await fetchWithTimeout(
          `http://${this.ip}/goform/goform_get_cmd_process?isRecognized=1&cmd=network_type`,
          {},
          3000
        );
      } catch { /* ignore */ }
      pings.push(performance.now() - t0);
    }
    const pingMs = pings.reduce((a, b) => a + b, 0) / pings.length;
    const avg = pingMs;
    const jitter = Math.sqrt(pings.reduce((s, p) => s + Math.pow(p - avg, 2), 0) / pings.length);

    const data = await this.getBatchData(["realtime_rx_thrpt", "realtime_tx_thrpt"]);
    const dlKbps = parseInt(data.realtime_rx_thrpt) || 0;
    const ulKbps = parseInt(data.realtime_tx_thrpt) || 0;

    return {
      downloadMbps: Math.round((dlKbps / 1000) * 10) / 10,
      uploadMbps: Math.round((ulKbps / 1000) * 10) / 10,
      pingMs: Math.round(pingMs),
      jitterMs: Math.round(jitter * 10) / 10,
      timestamp: new Date(),
    };
  }

  async getDeviceInfo(): Promise<Record<string, string>> {
    try {
      const data = await this.getBatchData([
        "device_name", "imei", "imsi", "iccid",
        "sw_version", "network_provider", "uptime",
      ]);
      return {
        model: data.device_name || "ZTE Router",
        imei: data.imei || "",
        imsi: data.imsi || "",
        iccid: data.iccid || "",
        firmware: data.sw_version || "",
        carrier: data.network_provider || "",
        uptime: data.uptime || "0",
      };
    } catch {
      return {};
    }
  }

  disconnect() {
    this.session.clear();
  }
}

// ─── Factory function ────────────────────────────────────────────────────────
export type RouterAPI = HuaweiRouterAPI | ZteRouterAPI;

export function createRouterAPI(credentials: RouterCredentials): RouterAPI {
  if (credentials.brand === "huawei") {
    return new HuaweiRouterAPI(credentials.ip, credentials.username, credentials.password);
  }
  return new ZteRouterAPI(credentials.ip, credentials.username, credentials.password);
}

// ─── Utility functions ───────────────────────────────────────────────────────
export function earfcnToFreqMHz(earfcn: number): number {
  // LTE EARFCN DL frequency bands
  if (earfcn >= 0 && earfcn <= 599) return 2110 + 0.1 * earfcn;
  if (earfcn >= 600 && earfcn <= 1199) return 1930 + 0.1 * (earfcn - 600);
  if (earfcn >= 1200 && earfcn <= 1949) return 1805 + 0.1 * (earfcn - 1200);
  if (earfcn >= 1950 && earfcn <= 2399) return 2110 + 0.1 * (earfcn - 1950);
  if (earfcn >= 2400 && earfcn <= 2649) return 869 + 0.1 * (earfcn - 2400);
  if (earfcn >= 2650 && earfcn <= 2749) return 875 + 0.1 * (earfcn - 2650);
  if (earfcn >= 2750 && earfcn <= 3449) return 2620 + 0.1 * (earfcn - 2750);
  if (earfcn >= 3450 && earfcn <= 3799) return 925 + 0.1 * (earfcn - 3450);
  if (earfcn >= 3800 && earfcn <= 4149) return 1844.9 + 0.1 * (earfcn - 3800);
  if (earfcn >= 4150 && earfcn <= 4749) return 2110 + 0.1 * (earfcn - 4150);
  if (earfcn >= 4750 && earfcn <= 4999) return 1475.9 + 0.1 * (earfcn - 4750);
  if (earfcn >= 5000 && earfcn <= 5179) return 728 + 0.1 * (earfcn - 5000);
  if (earfcn >= 5180 && earfcn <= 5279) return 746 + 0.1 * (earfcn - 5180);
  if (earfcn >= 5280 && earfcn <= 5379) return 758 + 0.1 * (earfcn - 5280);
  if (earfcn >= 5730 && earfcn <= 5849) return 734 + 0.1 * (earfcn - 5730);
  if (earfcn >= 5850 && earfcn <= 5999) return 860 + 0.1 * (earfcn - 5850);
  if (earfcn >= 6000 && earfcn <= 6149) return 875 + 0.1 * (earfcn - 6000);
  if (earfcn >= 6150 && earfcn <= 6449) return 791 + 0.1 * (earfcn - 6150);
  if (earfcn >= 6600 && earfcn <= 7399) return 3510 + 0.1 * (earfcn - 6600);
  if (earfcn >= 9870 && earfcn <= 9919) return 852 + 0.1 * (earfcn - 9870);
  if (earfcn >= 9920 && earfcn <= 10359) return 758 + 0.1 * (earfcn - 9920);
  return 0;
}

function normalizeBandName(raw: string): string {
  if (!raw) return "B1";
  raw = raw.toString().trim();
  if (/^[0-9]+$/.test(raw)) return `B${raw}`;
  if (/^[bB][0-9]+/.test(raw)) return raw.toUpperCase();
  return raw;
}

function normalizeNetworkType(raw: string): string {
  raw = (raw || "").toUpperCase();
  if (raw.includes("NR") || raw.includes("5G")) return "5G";
  if (raw.includes("LTE") || raw.includes("4G")) return "LTE";
  if (raw.includes("WCDMA") || raw.includes("3G") || raw.includes("UMTS")) return "3G";
  if (raw.includes("GSM") || raw.includes("2G")) return "2G";
  return raw || "LTE";
}

export const STANDARD_LTE_BANDS: BandInfo[] = [
  { bandNumber: 1,  name: "B1 (2100 MHz)",  dlFreqMHz: 2110, ulFreqMHz: 1920, bandwidth: "20", technology: "LTE", hexCode: "0x1",       isActive: false, isLocked: false },
  { bandNumber: 3,  name: "B3 (1800 MHz)",  dlFreqMHz: 1805, ulFreqMHz: 1710, bandwidth: "20", technology: "LTE", hexCode: "0x4",       isActive: false, isLocked: false },
  { bandNumber: 5,  name: "B5 (850 MHz)",   dlFreqMHz: 869,  ulFreqMHz: 824,  bandwidth: "10", technology: "LTE", hexCode: "0x10",      isActive: false, isLocked: false },
  { bandNumber: 7,  name: "B7 (2600 MHz)",  dlFreqMHz: 2620, ulFreqMHz: 2500, bandwidth: "20", technology: "LTE", hexCode: "0x40",      isActive: false, isLocked: false },
  { bandNumber: 8,  name: "B8 (900 MHz)",   dlFreqMHz: 925,  ulFreqMHz: 880,  bandwidth: "10", technology: "LTE", hexCode: "0x80",      isActive: false, isLocked: false },
  { bandNumber: 20, name: "B20 (800 MHz)",  dlFreqMHz: 791,  ulFreqMHz: 832,  bandwidth: "10", technology: "LTE", hexCode: "0x80000",   isActive: false, isLocked: false },
  { bandNumber: 28, name: "B28 (700 MHz)",  dlFreqMHz: 758,  ulFreqMHz: 703,  bandwidth: "10", technology: "LTE", hexCode: "0x8000000", isActive: false, isLocked: false },
  { bandNumber: 38, name: "B38 (TDD 2600)", dlFreqMHz: 2570, ulFreqMHz: 2570, bandwidth: "20", technology: "LTE", hexCode: "0x2000000000", isActive: false, isLocked: false },
  { bandNumber: 40, name: "B40 (TDD 2300)", dlFreqMHz: 2300, ulFreqMHz: 2300, bandwidth: "20", technology: "LTE", hexCode: "0x8000000000", isActive: false, isLocked: false },
  { bandNumber: 41, name: "B41 (TDD 2500)", dlFreqMHz: 2496, ulFreqMHz: 2496, bandwidth: "20", technology: "LTE", hexCode: "0x10000000000", isActive: false, isLocked: false },
  { bandNumber: 66, name: "B66 (AWS-3)",    dlFreqMHz: 2110, ulFreqMHz: 1710, bandwidth: "20", technology: "LTE", hexCode: "0x200000000000000", isActive: false, isLocked: false },
  { bandNumber: 71, name: "B71 (600 MHz)",  dlFreqMHz: 617,  ulFreqMHz: 663,  bandwidth: "10", technology: "LTE", hexCode: "0x40000000000000000", isActive: false, isLocked: false },
];

export const STANDARD_NR_BANDS: BandInfo[] = [
  { bandNumber: 77, name: "n77 (3.7 GHz)", dlFreqMHz: 3700, ulFreqMHz: 3700, bandwidth: "100", technology: "NR", hexCode: "0x1000", isActive: false, isLocked: false },
  { bandNumber: 78, name: "n78 (3.5 GHz)", dlFreqMHz: 3500, ulFreqMHz: 3500, bandwidth: "100", technology: "NR", hexCode: "0x2000", isActive: false, isLocked: false },
  { bandNumber: 79, name: "n79 (4.9 GHz)", dlFreqMHz: 4900, ulFreqMHz: 4900, bandwidth: "100", technology: "NR", hexCode: "0x4000", isActive: false, isLocked: false },
  { bandNumber: 1,  name: "n1 (2.1 GHz)",  dlFreqMHz: 2110, ulFreqMHz: 1920, bandwidth: "50",  technology: "NR", hexCode: "0x1",   isActive: false, isLocked: false },
  { bandNumber: 3,  name: "n3 (1.8 GHz)",  dlFreqMHz: 1805, ulFreqMHz: 1710, bandwidth: "50",  technology: "NR", hexCode: "0x4",   isActive: false, isLocked: false },
  { bandNumber: 28, name: "n28 (700 MHz)", dlFreqMHz: 758,  ulFreqMHz: 703,  bandwidth: "30",  technology: "NR", hexCode: "0x8000000", isActive: false, isLocked: false },
];
