/**
 * Direct Gemini API client — calls Google's REST API from the browser/WebView.
 * Used as primary path when an API key is configured, bypassing the Cloud Run
 * backend entirely. Falls back to the server for email-authenticated sessions.
 */

const GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta/models";

// Maps any model alias (including invalid legacy IDs) to a real Gemini model ID.
export function resolveGeminiModel(modelId: string): string {
  const id = (modelId || "").toLowerCase().trim();
  const MAP: Record<string, string> = {
    "gemini-3.5-flash":       "gemini-2.0-flash",
    "gemini-3.1-flash-lite":  "gemini-2.0-flash-lite",
    "gemini-3.1-pro-preview": "gemini-1.5-pro",
    "gemini-2.5-flash":       "gemini-2.0-flash",
    "gemini-2.5-pro":         "gemini-1.5-pro",
    "qwen-2.5-72b":           "gemini-2.0-flash",
    "kimi-chat-v1":           "gemini-2.0-flash",
    "claude-3-haiku":         "gemini-2.0-flash-lite",
    "deepseek-v3":            "gemini-2.0-flash",
  };
  return MAP[id] ?? modelId;
}

export interface GeminiTextPart { text: string }
export interface GeminiInlineDataPart { inlineData: { mimeType: string; data: string } }
export type GeminiPart = GeminiTextPart | GeminiInlineDataPart;

interface GeminiRequestBody {
  systemInstruction?: { parts: GeminiTextPart[] };
  contents: { role?: string; parts: GeminiPart[] }[];
  generationConfig?: Record<string, unknown>;
}

export async function callGeminiDirect(
  apiKey: string,
  modelId: string,
  body: GeminiRequestBody,
): Promise<string> {
  const model = resolveGeminiModel(modelId);
  const url = `${GEMINI_BASE}/${model}:generateContent?key=${apiKey}`;

  const resp = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!resp.ok) {
    const errText = await resp.text().catch(() => resp.statusText);
    // Retry with backup model on model-not-found errors
    if (resp.status === 404 || resp.status === 400) {
      const backup = "gemini-2.0-flash-lite";
      const r2 = await fetch(`${GEMINI_BASE}/${backup}:generateContent?key=${apiKey}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (r2.ok) {
        const d2 = await r2.json();
        return d2?.candidates?.[0]?.content?.parts?.[0]?.text ?? "";
      }
    }
    throw new Error(`Gemini API error ${resp.status}: ${errText}`);
  }

  const data = await resp.json();
  return data?.candidates?.[0]?.content?.parts?.[0]?.text ?? "";
}

/** Ask Gemini a text question with an optional system prompt. */
export async function askGeminiText(
  apiKey: string,
  modelId: string,
  systemPrompt: string,
  userQuestion: string,
): Promise<string> {
  return callGeminiDirect(apiKey, modelId, {
    systemInstruction: systemPrompt ? { parts: [{ text: systemPrompt }] } : undefined,
    contents: [{ role: "user", parts: [{ text: userQuestion }] }],
  });
}

/** Analyze an image + prompt with Gemini Vision. Returns raw text (JSON string). */
export async function analyzeImageWithGemini(
  apiKey: string,
  modelId: string,
  base64Data: string,
  mimeType: string,
  prompt: string,
  responseJson = true,
): Promise<string> {
  return callGeminiDirect(apiKey, modelId, {
    contents: [
      {
        role: "user",
        parts: [
          { inlineData: { mimeType, data: base64Data } },
          { text: prompt },
        ],
      },
    ],
    generationConfig: responseJson ? { responseMimeType: "application/json" } : undefined,
  });
}
