/**
 * Pollinations.ai client — completely free, no API key required.
 * Used as the primary path for all "free models" (Qwen, Kimi, DeepSeek, etc.)
 * and as fallback when no Gemini key is configured.
 */

const POLLINATIONS_TEXT = "https://text.pollinations.ai";

// Maps app model IDs to real Pollinations model names
export function resolvePollinationsModel(modelId: string): string {
  const id = (modelId || "").toLowerCase().trim();
  const MAP: Record<string, string> = {
    "qwen-2.5-72b":           "qwen-coder",   // actual Qwen 2.5 Coder 32B
    "deepseek-v3":            "mistral",        // Mistral Nemo
    "kimi-chat-v1":           "openai",         // GPT-4o mini (closest free)
    "claude-3-haiku":         "openai",         // GPT-4o mini (closest free)
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

async function callPollinations(
  model: string,
  messages: { role: string; content: any }[],
): Promise<string> {
  const resp = await fetch(`${POLLINATIONS_TEXT}/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      messages,
      model,
      seed: Math.floor(Math.random() * 9999),
      stream: false,
    }),
  });

  if (!resp.ok) {
    const err = await resp.text().catch(() => resp.statusText);
    // Retry with openai model on failure
    if (model !== "openai") {
      const r2 = await fetch(`${POLLINATIONS_TEXT}/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ messages, model: "openai", seed: 42, stream: false }),
      });
      if (r2.ok) {
        const t2 = await r2.text();
        return extractText(t2);
      }
    }
    throw new Error(`Pollinations API error ${resp.status}: ${err}`);
  }

  return extractText(await resp.text());
}

function extractText(raw: string): string {
  // Handle both plain-text and OpenAI-format JSON responses
  try {
    const json = JSON.parse(raw);
    if (json?.choices?.[0]?.message?.content) return json.choices[0].message.content;
    if (json?.content) return json.content;
    if (typeof json?.text === "string") return json.text;
  } catch {}
  return raw;
}

/** Ask a text question with an optional system prompt. No API key needed. */
export async function askPollinationsText(
  modelId: string,
  systemPrompt: string,
  userMessage: string,
): Promise<string> {
  const model = resolvePollinationsModel(modelId);
  const messages: { role: string; content: any }[] = [];
  if (systemPrompt) messages.push({ role: "system", content: systemPrompt });
  messages.push({ role: "user", content: userMessage });
  return callPollinations(model, messages);
}

/** Analyze an image with Pollinations vision (openai-large = GPT-4o, supports images). */
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
  // openai-large (GPT-4o) supports vision
  return callPollinations("openai-large", messages);
}
