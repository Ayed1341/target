/**
 * Pollinations.ai client — completely free, no API key required.
 * Handles rate limiting (429) via automatic retry with backoff,
 * and serializes concurrent requests to stay within the 1-request-per-IP limit.
 */

const POLLINATIONS_TEXT = "https://text.pollinations.ai";

// Serialize all Pollinations calls — the service allows only 1 concurrent request per IP.
// Queuing on the client avoids 429 entirely.
let _queue: Promise<unknown> = Promise.resolve();

function enqueue<T>(fn: () => Promise<T>): Promise<T> {
  const next = _queue.then(() => fn()).catch(() => fn()); // catch so queue never stalls
  _queue = next.catch(() => {});
  return next as Promise<T>;
}

// Maps app model IDs to real Pollinations model names
export function resolvePollinationsModel(modelId: string): string {
  const id = (modelId || "").toLowerCase().trim();
  const MAP: Record<string, string> = {
    "qwen-2.5-72b":           "qwen-coder",
    "deepseek-v3":            "mistral",
    "kimi-chat-v1":           "openai",
    "claude-3-haiku":         "openai",
    "gemini-2.0-flash":       "openai",
    "gemini-2.0-flash-lite":  "openai",
    "gemini-1.5-pro":         "openai-large",
    "gemini-3.5-flash":       "openai",
    "gemini-3.1-flash-lite":  "openai",
    "gemini-3.1-pro-preview": "openai-large",
    "gemini-2.5-flash":       "openai",
    "gemini-2.5-pro":         "openai-large",
  };
  return MAP[id] || "openai";
}

async function sleep(ms: number) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function callPollinationsOnce(
  model: string,
  messages: { role: string; content: any }[],
): Promise<Response> {
  return fetch(`${POLLINATIONS_TEXT}/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      messages,
      model,
      seed: Math.floor(Math.random() * 9999),
      stream: false,
    }),
  });
}

async function callPollinations(
  model: string,
  messages: { role: string; content: any }[],
): Promise<string> {
  // Retry up to 4 times with increasing delay on 429 or transient errors
  const delays = [2000, 4000, 6000, 8000];
  let lastErr = "";

  for (let i = 0; i <= delays.length; i++) {
    const resp = await callPollinationsOnce(model, messages);

    if (resp.ok) return extractText(await resp.text());

    const errText = await resp.text().catch(() => resp.statusText);

    if (resp.status === 429) {
      // Rate limited — wait, then retry
      if (i < delays.length) {
        await sleep(delays[i]);
        continue;
      }
      lastErr = "الخدمة المجانية مشغولة حالياً، حاول مرة أخرى بعد لحظات.";
      break;
    }

    // Non-429 failure: try with fallback "openai" model once
    if (model !== "openai") {
      const r2 = await callPollinationsOnce("openai", messages);
      if (r2.ok) return extractText(await r2.text());
    }

    lastErr = `خطأ في الاتصال بالخدمة المجانية (${resp.status}).`;
    break;
  }

  throw new Error(lastErr || "فشل الاتصال بالخدمة المجانية.");
}

function extractText(raw: string): string {
  try {
    const json = JSON.parse(raw);
    if (json?.choices?.[0]?.message?.content) return json.choices[0].message.content;
    if (json?.content) return json.content;
    if (typeof json?.text === "string") return json.text;
  } catch {}
  return raw;
}

/** Ask a text question. Queued to prevent concurrent 429s. No API key needed. */
export async function askPollinationsText(
  modelId: string,
  systemPrompt: string,
  userMessage: string,
): Promise<string> {
  const model = resolvePollinationsModel(modelId);
  const messages: { role: string; content: any }[] = [];
  if (systemPrompt) messages.push({ role: "system", content: systemPrompt });
  messages.push({ role: "user", content: userMessage });
  return enqueue(() => callPollinations(model, messages));
}

/** Analyze an image. Uses openai-large (GPT-4o) which supports vision. */
export async function analyzeImageWithPollinations(
  base64Data: string,
  mimeType: string,
  prompt: string,
): Promise<string> {
  const messages = [
    {
      role: "user",
      content: [
        { type: "image_url", image_url: { url: `data:${mimeType};base64,${base64Data}` } },
        { type: "text", text: prompt },
      ],
    },
  ];
  return enqueue(() => callPollinations("openai-large", messages));
}
