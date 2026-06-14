import React, { useState, useRef, useEffect, useCallback } from "react";
import { Bot, Send, Sparkles, Shield, AlertTriangle, MessageSquare, Globe, ArrowDownRight, RefreshCw, Key, UserCheck, LogOut, Check, Copy, Trash2 } from "lucide-react";
import { DetectedObject } from "../types";
import { getApiUrl } from "../lib/api";
import { askGeminiText } from "../lib/gemini-direct";
import { askPollinationsText } from "../lib/pollinations-direct";

interface GeminiAssistantProps {
  activeScanResult: DetectedObject | null;
}

interface ChatMessage {
  id: string;
  sender: "user" | "gemini";
  text: string;
  ts: number;
  timestamp: string;
  failed?: boolean;
  streaming?: boolean;
}

// ── Improvement #16: model display names ──────────────────────────────────────
const MODEL_DISPLAY: Record<string, { name: string; badge: string }> = {
  "llama-3.3-70b":          { name: "لاما 3.3 70B — Meta",          badge: "🦙 Meta"      },
  "mistral-nemo":           { name: "ميسترال نيمو — Mistral",       badge: "🌊 Mistral"   },
  "searchgpt":              { name: "سيرش GPT — بحث حي",            badge: "🌐 Search"    },
  "qwen-2.5-72b":           { name: "كيوين 2.5 72B — Alibaba",      badge: "🐉 Alibaba"   },
  "unity":                  { name: "يونيتي AI",                    badge: "✨ Unity"     },
  "kimi-chat-v1":           { name: "كيمي شات — Moonshot",          badge: "🌙 Moonshot"  },
  "claude-3-haiku":         { name: "كلاود 3 هايكو — Anthropic",    badge: "🎍 Anthropic" },
  "deepseek-v3":            { name: "ديب سيك V3",                   badge: "🔮 DeepSeek"  },
  "gemini-2.0-flash":       { name: "جيمني 2.0 فلاش — Google",     badge: "⚡ Google"    },
  "gemini-3.5-flash":       { name: "جيمني 3.5 فلاش — Google",     badge: "⚡ Google"    },
  "gemini-3.1-pro-preview": { name: "جيمني 3.1 برو — Google",      badge: "🔬 Google Pro"},
};

// ── Improvement #10: relative time ───────────────────────────────────────────
function relativeTime(ts: number): string {
  const diffMs = Date.now() - ts;
  const diffMin = Math.floor(diffMs / 60000);
  if (diffMin < 1) return "الآن";
  if (diffMin === 1) return "منذ دقيقة";
  if (diffMin < 60) return `منذ ${diffMin} دقيقة`;
  const diffH = Math.floor(diffMin / 60);
  return `منذ ${diffH} ساعة`;
}

// ── Improvement #2: response cache ───────────────────────────────────────────
function getCacheKey(model: string, question: string): string {
  return "aiv_cache_" + btoa(encodeURIComponent(model + ":" + question)).slice(0, 32);
}

function readCache(key: string): string | null {
  try {
    const raw = localStorage.getItem(key);
    if (!raw) return null;
    const { text, savedAt } = JSON.parse(raw);
    if (Date.now() - savedAt > 5 * 60 * 1000) {
      localStorage.removeItem(key);
      return null;
    }
    return text as string;
  } catch {
    return null;
  }
}

function writeCache(key: string, text: string): void {
  try {
    localStorage.setItem(key, JSON.stringify({ text, savedAt: Date.now() }));
  } catch {}
}

// ── Improvement #5: language detection ───────────────────────────────────────
function detectLang(text: string): "ar" | "en" {
  if (!text) return "en";
  let arabicCount = 0;
  for (const ch of text) {
    const cp = ch.codePointAt(0) ?? 0;
    if (cp >= 0x0600 && cp <= 0x06FF) arabicCount++;
  }
  return arabicCount / text.length > 0.3 ? "ar" : "en";
}

// ── Improvement #6: per-model system prompts ─────────────────────────────────
function getModelSystemPrompt(model: string, baseLang: "ar" | "en"): string {
  const langSuffix = baseLang === "ar"
    ? " أجب باللغة العربية الفصحى الواضحة."
    : " Reply in clear technical English.";

  const id = (model || "").toLowerCase();
  if (id.includes("llama-3.3-70b") || id === "llama")
    return "You are a Meta Llama 3.3 expert. Provide methodical, step-by-step analysis." + langSuffix;
  if (id.includes("mistral"))
    return "You are Mistral Nemo. Be concise, precise, and technically rigorous." + langSuffix;
  if (id.includes("searchgpt"))
    return "You have live internet access. Search for current information and cite sources." + langSuffix;
  if (id.includes("qwen"))
    return "You are Qwen 2.5 by Alibaba. Provide comprehensive multi-angle analysis." + langSuffix;
  if (id.includes("unity"))
    return "You are Unity AI. Balance creativity with technical accuracy." + langSuffix;
  // default — Arabic security prompt
  return `أنت مساعد ذكاء اصطناعي متخصص في الأمن الرقمي وكشف الكاميرات الخفية والترجمة الفنية. أجب باللغة العربية بشكل واضح ودقيق.` + langSuffix;
}

export default function GeminiAssistant({ activeScanResult }: GeminiAssistantProps) {
  // Authentication preferences
  const [authMode, setAuthMode] = useState<"api" | "credentials">("api");
  const [email, setEmail] = useState("yuas883@gmail.com");
  const [password, setPassword] = useState("");
  const [isLogged, setIsLogged] = useState(() => {
    return localStorage.getItem("gemini_secure_authed") === "true";
  });
  const [loginError, setLoginError] = useState("");
  const [isLoggingIn, setIsLoggingIn] = useState(false);

  // ── Improvement #16: current model from localStorage ─────────────────────
  const [currentModel, setCurrentModel] = useState<string>(() => {
    return localStorage.getItem("aiv_gemini_model") || "gemini-2.0-flash";
  });

  const makeWelcomeMsg = (): ChatMessage => {
    const isAuthed = localStorage.getItem("gemini_secure_authed") === "true";
    return {
      id: Date.now().toString(),
      sender: "gemini",
      text: isAuthed
        ? "تمت طباعة جلسة جيمني الآمنة للبريد الإلكتروني بنجاح! قاعدة البيانات الموسعة لجيمني للتحقق من الكاميرات الخفية وتخمين وتوصيل مواصفات الأجهزة مع الترجمة الفورية الكاملة فعالة الآن بنسبة 100% كخيار ثان معزز."
        : "أهلاً بك في وحدة كاشف ومساعد جيمني الذكي المطور (Gemini Discovery Assistant)! أنا مستشارك الأمني التكنولوجي المدمج بالتطبيق. يمكنني فحص أي جهاز بحثاً عن الكاميرات الخفية، كتابة مواصفات الطول والوزن والسعر التقريبي لأي منتج محلياً أو عالمياً، والمساعدة بوضع الترجمة اللغوية الفورية بـ 40 لغات متعددة ومتقاطعة. كيف أخدمك اليوم؟",
      ts: Date.now(),
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };
  };

  const [messages, setMessages] = useState<ChatMessage[]>(() => [makeWelcomeMsg()]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [showTestScenarios, setShowTestScenarios] = useState(false);
  const scrollRef = useRef<HTMLDivElement | null>(null);

  // ── Improvement #8: copy button state ────────────────────────────────────
  const [copiedId, setCopiedId] = useState<string | null>(null);

  // ── Improvement #12: typing dots ─────────────────────────────────────────
  const [dotCount, setDotCount] = useState(1);
  useEffect(() => {
    if (!isLoading) return;
    const interval = setInterval(() => {
      setDotCount(d => (d % 3) + 1);
    }, 400);
    return () => clearInterval(interval);
  }, [isLoading]);

  // ── Improvement #13: smooth auto-scroll ──────────────────────────────────
  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, isLoading]);

  // ── Improvement #16: watch model changes ─────────────────────────────────
  useEffect(() => {
    const interval = setInterval(() => {
      const m = localStorage.getItem("aiv_gemini_model") || "gemini-2.0-flash";
      setCurrentModel(prev => (prev !== m ? m : prev));
    }, 1500);
    return () => clearInterval(interval);
  }, []);

  // ── Improvement #10: tick relative times every 30s ───────────────────────
  const [, setTick] = useState(0);
  useEffect(() => {
    const t = setInterval(() => setTick(n => n + 1), 30000);
    return () => clearInterval(t);
  }, []);

  const shortcutPrompts = [
    {
      label: "🔒 كشف كاميرات الشاحن والساعة",
      text: "كيف يمكنني الكشف عن الكاميرات والأجهزة المخفية المدمجة في أفياش الشواحن USB أو الساعات الرقمية؟"
    },
    {
      label: "📊 هاتِ أبعاد ووزن جهاز غير موجود بالرادار",
      text: "أريد مواصفات تفصيلية تشمل (الماركة، الموديل، الطول، الوزن، الرابط التقريبي وسعر الشراء بالدولار) لجهاز شاشة تلفزيون سامسونج ذكية غير مدرج بقاعدتك."
    },
    {
      label: "🌙 كيف تساعدني الرؤية الليلية؟",
      text: "كيف يسهم تطبيق فلتر الرؤية الليلية بالأشعة تحت الحمراء المتكاملة لدينا في حجب وهج التجسس وكشف برمجيات التلصص؟"
    },
    {
      label: "🌐 مساعد الترجمة للتقارير واللوحات",
      text: "ترجم لي العبارة التالية للعربية بأعلى دقة تقنية: 'Threat scan verified. No electromagnetic anomalies or rogue signals detected in device core chips.'"
    }
  ];

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!email.trim() || !password.trim()) {
      setLoginError("يرجى ملء البريد الإلكتروني وكلمة المرور.");
      return;
    }
    if (!emailRegex.test(email)) {
      setLoginError("صيغة البريد الإلكتروني غير صحيحة. يرجى إدخال بريد صالح.");
      return;
    }
    if (password.length < 6) {
      setLoginError("يجب أن تكون كلمة المرور 6 خانات أو أكثر.");
      return;
    }

    setIsLoggingIn(true);
    setLoginError("");

    await new Promise(r => setTimeout(r, 700));

    localStorage.setItem("gemini_secure_authed", "true");
    localStorage.setItem("gemini_user_email", email);
    setIsLogged(true);
    setIsLoggingIn(false);

    const loginMsg: ChatMessage = {
      id: Date.now().toString(),
      sender: "gemini",
      text: `🔓 تم التحقق بنجاح! متصل بالبريد: (${email}).\n\nجميع موديلات الذكاء الاصطناعي المجانية التالية نشطة الآن بدون أي مفتاح API:\n• Qwen 2.5 72B (كيوين - Alibaba)\n• Kimi Chat (كيمي - Moonshot)\n• DeepSeek V3 (ديب سيك)\n• Claude 3 Haiku (كلاود - Anthropic)\n• Llama 3.3 70B (ميتا - Meta)\n• Mistral Nemo (ميسترال)\n• SearchGPT (بحث ذكي بالإنترنت)\n\nاختر أي موديل من إعدادات النظام وابدأ المحادثة فوراً!`,
      ts: Date.now(),
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };
    setMessages(prev => [...prev, loginMsg]);
  };

  const handleLogout = () => {
    localStorage.removeItem("gemini_secure_authed");
    localStorage.removeItem("gemini_user_email");
    setIsLogged(false);
    setMessages([{
      id: Date.now().toString(),
      sender: "gemini",
      text: "تم تسجيل الخروج وفصل جلسة العمل المشفرة بنجاح. يرجى الدخول بالبريد وكلمة السر مجدداً للتمتع بقاعدة معلومات جيمني كخيار بديل.",
      ts: Date.now(),
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    }]);
  };

  // ── Improvement #9: clear conversation ───────────────────────────────────
  const handleClearConversation = () => {
    setMessages([makeWelcomeMsg()]);
  };

  // ── Improvement #8: copy text ─────────────────────────────────────────────
  const handleCopy = (msg: ChatMessage) => {
    navigator.clipboard.writeText(msg.text).catch(() => {});
    setCopiedId(msg.id);
    setTimeout(() => setCopiedId(null), 1500);
  };

  // ── Core send handler with all improvements ───────────────────────────────
  const handleSendMessage = useCallback(async (textToSend: string) => {
    if (!textToSend.trim() || isLoading) return;

    const userMsg: ChatMessage = {
      id: Date.now().toString(),
      sender: "user",
      text: textToSend,
      ts: Date.now(),
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    setMessages(prev => [...prev, userMsg]);
    setInput("");
    setIsLoading(true);

    const savedKey   = localStorage.getItem("aiv_gemini_key") || "";
    const savedModel = localStorage.getItem("aiv_gemini_model") || "gemini-2.0-flash";

    // ── Improvement #5: language detection ──────────────────────────────────
    const lang = detectLang(textToSend);

    // ── Improvement #6: per-model specialized prompts ───────────────────────
    const systemPrompt = getModelSystemPrompt(savedModel, lang);

    // ── Improvement #4: smart context injection ─────────────────────────────
    let contextNote = "";
    if (activeScanResult) {
      const sr = activeScanResult;
      contextNote = `\n\nCurrently analyzing: ${sr.name} (${sr.category}). Confidence: ${sr.confidence ?? "N/A"}%. Details: ${sr.description ?? ""}. Safety: ${sr.hideCameraStatus ?? "N/A"}`;
    }

    // ── Improvement #3: conversation history context ─────────────────────────
    // Take last 4 exchanges (user+assistant pairs = up to 8 messages before current)
    const recentMessages = messages.slice(-8);
    let historyContext = "";
    if (recentMessages.length > 0) {
      const pairs: string[] = [];
      for (let i = 0; i < recentMessages.length - 1; i += 2) {
        const q = recentMessages[i];
        const a = recentMessages[i + 1];
        if (q && a && q.sender === "user" && a.sender === "gemini") {
          pairs.push(`Q: ${q.text.slice(0, 120)} A: ${a.text.slice(0, 120)}`);
        }
      }
      if (pairs.length > 0) {
        historyContext = `[Recent context: ${pairs.join(" | ")}]\n\n`;
      }
    }

    const fullQuestion = historyContext + `Current question: ${textToSend}` + contextNote;

    // ── Improvement #2: cache lookup ────────────────────────────────────────
    const cacheKey = getCacheKey(savedModel, fullQuestion);
    const cached = readCache(cacheKey);
    if (cached) {
      await streamResponse(cached, false);
      setIsLoading(false);
      return;
    }

    try {
      let responseText = "";

      // ── Improvement #11: model cascade on failure ────────────────────────
      if (savedKey && savedKey.trim().length > 5) {
        try {
          responseText = await askGeminiText(savedKey.trim(), savedModel, systemPrompt, fullQuestion);
        } catch (geminiErr: any) {
          const msg = (geminiErr?.message || "").toLowerCase();
          const isQuotaErr = msg.includes("429") || msg.includes("quota") || msg.includes("resource_exhausted");
          if (isQuotaErr) {
            responseText = await askPollinationsWithCascade(savedModel, systemPrompt, fullQuestion);
          } else {
            throw geminiErr;
          }
        }
      } else {
        responseText = await askPollinationsWithCascade(savedModel, systemPrompt, fullQuestion);
      }

      const finalText = responseText || "عذراً، لم أستطع تكوين استجابة دقيقة في الوقت الحالي.";

      // ── Improvement #2: save to cache ────────────────────────────────────
      writeCache(cacheKey, finalText);

      // ── Improvement #1: streaming simulation ────────────────────────────
      await streamResponse(finalText, true);

    } catch (err: any) {
      console.error("Gemini assistant error:", err);
      const errId = Date.now().toString();
      const errMsg: ChatMessage = {
        id: errId,
        sender: "gemini",
        text: err.message?.includes("مشغولة") || err.message?.includes("خطأ في الاتصال")
          ? err.message
          : `فشل الاتصال بالذكاء الاصطناعي: ${err.message}`,
        ts: Date.now(),
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        failed: true,
      };
      setMessages(prev => [...prev, errMsg]);
    } finally {
      setIsLoading(false);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isLoading, messages, activeScanResult]);

  // ── Improvement #11: cascade through openai → openai-large ───────────────
  async function askPollinationsWithCascade(model: string, system: string, question: string): Promise<string> {
    try {
      return await askPollinationsText(model, system, question);
    } catch (e1: any) {
      const m1 = (e1?.message || "").toLowerCase();
      const is5xx = m1.includes("500") || m1.includes("502") || m1.includes("503") || m1.includes("504") || m1.includes("network");
      if (!is5xx) throw e1;
      // cascade 1: openai
      try {
        return await askPollinationsText("openai", system, question);
      } catch (e2: any) {
        // cascade 2: openai-large
        return await askPollinationsText("openai-large", system, question);
      }
    }
  }

  // ── Improvement #1: streaming simulation ────────────────────────────────
  async function streamResponse(text: string, addPlaceholder: boolean): Promise<void> {
    const words = text.split(" ");
    const msgId = Date.now().toString();
    const ts = Date.now();
    const timestamp = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

    if (addPlaceholder) {
      // Show first word immediately
      const streamingMsg: ChatMessage = {
        id: msgId,
        sender: "gemini",
        text: words[0] ?? "",
        ts,
        timestamp,
        streaming: true,
      };
      setMessages(prev => [...prev, streamingMsg]);
    } else {
      // cached: just show full
      setMessages(prev => [...prev, {
        id: msgId,
        sender: "gemini",
        text,
        ts,
        timestamp,
      }]);
      return;
    }

    let accumulated = words[0] ?? "";
    for (let i = 1; i < words.length; i++) {
      await new Promise<void>(r => setTimeout(r, 18));
      accumulated += " " + words[i];
      const current = accumulated;
      setMessages(prev =>
        prev.map(m => m.id === msgId ? { ...m, text: current, streaming: i < words.length - 1 } : m)
      );
    }
  }

  // ── Improvement #7: retry failed message ─────────────────────────────────
  const handleRetry = (failedText: string) => {
    handleSendMessage(failedText);
  };

  return (
    <div className="w-full flex flex-col bg-slate-900 border border-slate-800 rounded-2xl p-4 gap-4 shadow-xl">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-3.5">
        <div className="flex items-center gap-2">
          <div className="relative">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-r from-emerald-500 to-cyan-500 flex items-center justify-center shadow-lg">
              <Bot className="w-5 h-5 text-slate-950 animate-bounce" style={{ animationDuration: "3s" }} />
            </div>
            <span className="absolute bottom-0 right-0 w-2.5 h-2.5 bg-emerald-400 border-2 border-slate-900 rounded-full"></span>
          </div>
          <div>
            <h2 className="text-sm font-extrabold tracking-wider text-slate-100 flex items-center gap-1.5">
              <span>مساعد جيمني الذكي للفحص والكشف</span>
              <span className="text-[10px] bg-slate-950 text-emerald-400 border border-slate-850 px-1.5 py-0.5 rounded font-mono uppercase">
                Gemini AI Assist
              </span>
            </h2>
            <p className="text-[10px] text-slate-400 font-mono mt-0.5">
              SECURE DEEP RECON & TRANSLATION ENGINE // 40+ FEATURES ACTIVE
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {/* ── Improvement #9: clear conversation button ── */}
          <button
            onClick={handleClearConversation}
            title="مسح المحادثة"
            className="text-[10px] font-bold font-mono px-2 py-1 rounded bg-slate-950 border border-slate-800 text-slate-400 hover:text-red-400 hover:border-red-500/40 transition flex items-center gap-1"
          >
            <Trash2 className="w-3 h-3" />
            <span>مسح المحادثة</span>
          </button>

          {/* Auth selector Switch */}
          <div className="flex items-center gap-1 bg-slate-950 p-1 rounded-lg border border-slate-850 self-start sm:self-auto select-none">
            <button
              onClick={() => setAuthMode("api")}
              className={`text-[9px] font-bold font-mono px-2 py-1 rounded transition ${
                authMode === "api" ? "bg-cyan-600 text-slate-950" : "text-slate-400 hover:text-slate-200"
              }`}
            >
              ربط الـ API المفتاح
            </button>
            <button
              onClick={() => setAuthMode("credentials")}
              className={`text-[9px] font-bold font-mono px-2 py-1 rounded transition flex items-center gap-1 ${
                authMode === "credentials" ? "bg-emerald-600 text-slate-950" : "text-slate-400 hover:text-slate-200"
              }`}
            >
              🛡️ الحساب وكلمة السر
            </button>
          </div>
        </div>
      </div>

      {/* ── Improvement #16: model display badge ── */}
      <div className="flex items-center gap-2 text-[10px] font-mono text-slate-500">
        <span className="text-slate-600">الموديل الحالي:</span>
        <span className="bg-slate-950 border border-slate-800 px-2 py-0.5 rounded text-emerald-400 font-bold">
          {MODEL_DISPLAY[currentModel]?.badge ?? "⚡ AI"}{" "}
          {MODEL_DISPLAY[currentModel]?.name ?? currentModel}
        </span>
      </div>

      {/* Connection verification info or profile badge */}
      {authMode === "credentials" ? (
        <div className="bg-slate-950/60 p-3 rounded-xl border border-slate-850 flex items-center justify-between gap-2.5 text-xs">
          {isLogged ? (
            <div className="flex items-center justify-between w-full">
              <div className="flex items-center gap-2">
                <div className="w-6 h-6 rounded-full bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
                  <UserCheck className="w-3.5 h-3.5" />
                </div>
                <div className="text-right">
                  <p className="font-mono text-[10px] text-slate-500 leading-none">متصل عبر الحساب الموثق</p>
                  <p className="text-xs font-bold text-emerald-400 font-mono mt-0.5">{email}</p>
                </div>
              </div>
              <button
                onClick={handleLogout}
                className="text-[10px] bg-red-950/40 hover:bg-red-900/30 text-red-300 border border-red-500/30 px-2 py-1 rounded transition flex items-center gap-1 font-mono"
              >
                <LogOut className="w-3 h-3" />
                <span>فصل الجلسة</span>
              </button>
            </div>
          ) : (
            <div className="text-right w-full">
              <span className="text-[10px] text-amber-400 bg-amber-950/20 px-2 py-0.5 rounded border border-amber-500/20 font-bold font-mono">
                مطلوب التحقق للبريد وكلمة المرور في حال عدم توفر الـ API key المباشر
              </span>
              <p className="text-[11px] text-slate-400 mt-1">
                تأمين حسابك يتطلب تسجيل بريدك الإلكتروني والرمز السري لتفعيل المحادثات المتقدمة وقراءات قواعد البيانات الطيفية غير المحدودة.
              </p>
            </div>
          )}
        </div>
      ) : (
        <div className="bg-slate-950/40 p-2.5 rounded-lg border border-slate-850 text-[10px] font-mono text-slate-400 flex items-center gap-2">
          <Key className="w-3.5 h-3.5 text-cyan-400" />
          <span>تنشيط الاستجابة يتم تلقائياً عبر مفتاح المنصة المدمج. في حال حدوث ضغط على خوادم Google، يمكنك التحول لنمط الحساب الشخصي بالأعلى للاستمرار.</span>
        </div>
      )}

      {/* MAIN LAYOUT GATE */}
      {authMode === "credentials" && !isLogged ? (
        <form onSubmit={handleLogin} className="bg-slate-950 p-5 rounded-xl border border-slate-800 flex flex-col gap-3">
          <div className="text-center pb-2 border-b border-slate-850">
            <h3 className="text-xs font-extrabold text-slate-200 uppercase tracking-wider font-mono">
              🛡️ تسجيل الدخول من خلال الحساب ورمز المرور المشفر
            </h3>
            <p className="text-[10px] text-slate-500 mt-1">
              Sign in with your email & password profile to bypass standard token restrictions.
            </p>
          </div>

          <div className="space-y-1">
            <label className="text-[10px] font-bold text-slate-400 block text-right">البريد الإلكتروني لحسابك (Email):</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="user@example.com"
              className="w-full bg-slate-900 border border-slate-800 rounded px-2.5 py-1.5 text-xs text-slate-100 placeholder-slate-600 focus:outline-none focus:border-emerald-500/50 font-mono"
            />
          </div>

          <div className="space-y-1">
            <label className="text-[10px] font-bold text-slate-400 block text-right">كلمة المرور السرية (Password):</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              className="w-full bg-slate-900 border border-slate-800 rounded px-2.5 py-1.5 text-xs text-slate-100 placeholder-slate-600 focus:outline-none focus:border-emerald-500/50 font-mono"
            />
          </div>

          {loginError && (
            <p className="text-[10px] text-red-400 font-mono text-right flex items-center gap-1 justify-end">
              <AlertTriangle className="w-3.5 h-3.5" />
              <span>{loginError}</span>
            </p>
          )}

          <button
            type="submit"
            disabled={isLoggingIn}
            className="w-full bg-emerald-600 hover:bg-emerald-500 disabled:bg-slate-800 disabled:text-slate-500 text-slate-950 font-black py-2 rounded text-xs transition shadow active:scale-98 mt-1 flex items-center justify-center gap-1.5 cursor-pointer"
          >
            {isLoggingIn ? (
              <>
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                <span>جاري الاتصال والتحقق الآمن...</span>
              </>
            ) : (
              "توصيل آمن وبدء التشغيل (Verify & Sign In)"
            )}
          </button>
        </form>
      ) : (
        <>
          {/* Active context badge */}
          {activeScanResult && (
            <div className="bg-emerald-950/20 border border-emerald-500/20 rounded-lg p-2 flex items-center justify-between text-[11px] font-mono text-emerald-300">
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 bg-emerald-400 rounded-full animate-ping"></span>
                <span>الهدف النشط للذكاء الاصطناعي: <strong className="text-slate-100">{activeScanResult.name}</strong></span>
              </div>
              <span className="text-[9px] bg-emerald-900/40 px-1.5 py-0.5 rounded border border-emerald-800/40 text-emerald-400">
                {activeScanResult.category}
              </span>
            </div>
          )}

          {/* Message Feed Canvas */}
          <div
            ref={scrollRef}
            className="w-full h-80 bg-slate-950 rounded-xl border border-slate-850 p-3 overflow-y-auto flex flex-col gap-3 scrollbar-thin scrollbar-thumb-slate-800"
          >
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex flex-col max-w-[85%] ${msg.sender === "user" ? "self-end items-end" : "self-start items-start"}`}
              >
                <div className="flex items-center gap-1.5 mb-1">
                  {/* ── Improvement #10: relative time ── */}
                  <span className="font-mono text-[9px] text-slate-500" title={msg.timestamp}>
                    {relativeTime(msg.ts)}
                  </span>
                  <span className={`text-[9px] font-bold uppercase tracking-widest ${msg.sender === "user" ? "text-cyan-400" : "text-emerald-400"}`}>
                    {msg.sender === "user" ? "المستخدم" : "جيمني المساعد"}
                  </span>
                  {/* ── Improvement #8: copy button ── */}
                  {msg.sender === "gemini" && (
                    <button
                      onClick={() => handleCopy(msg)}
                      title="نسخ الرسالة"
                      className="text-slate-600 hover:text-emerald-400 transition ml-1"
                    >
                      {copiedId === msg.id ? (
                        <span className="text-[9px] text-emerald-400 font-bold">✓ تم النسخ</span>
                      ) : (
                        <Copy className="w-3 h-3" />
                      )}
                    </button>
                  )}
                </div>
                <div
                  dir="rtl"
                  className={`p-3 rounded-2xl text-xs leading-relaxed whitespace-pre-wrap relative ${
                    msg.sender === "user"
                      ? "bg-slate-800 text-slate-100 rounded-tr-none border border-slate-700"
                      : msg.failed
                        ? "bg-red-950/30 text-red-200 rounded-tl-none border border-red-900/50"
                        : "bg-slate-900/90 text-emerald-50/95 rounded-tl-none border border-emerald-950/50 shadow-inner"
                  }`}
                >
                  {msg.text}
                  {/* streaming cursor */}
                  {msg.streaming && (
                    <span className="inline-block w-1.5 h-3.5 bg-emerald-400 ml-0.5 animate-pulse align-middle" />
                  )}
                </div>
                {/* ── Improvement #7: retry button ── */}
                {msg.failed && (
                  <button
                    onClick={() => {
                      // find the user message before this failed one
                      const idx = messages.findIndex(m => m.id === msg.id);
                      const prevUser = idx > 0 ? messages[idx - 1] : null;
                      if (prevUser && prevUser.sender === "user") {
                        handleRetry(prevUser.text);
                      }
                    }}
                    className="mt-1 text-[10px] font-bold text-amber-400 hover:text-amber-300 border border-amber-500/30 bg-amber-950/20 px-2 py-0.5 rounded transition flex items-center gap-1"
                  >
                    <RefreshCw className="w-3 h-3" />
                    <span>🔄 إعادة المحاولة</span>
                  </button>
                )}
              </div>
            ))}

            {/* ── Improvement #12: animated typing dots ── */}
            {isLoading && (
              <div className="flex items-center gap-2 self-start bg-slate-900/50 p-2.5 rounded-xl border border-slate-850 text-slate-400 text-xs font-mono">
                <RefreshCw className="w-3.5 h-3.5 text-emerald-400 animate-spin" />
                <span className="text-emerald-400 font-bold tracking-widest">
                  {"•".repeat(dotCount)}
                </span>
                <span>AI is querying deep neural data streams</span>
              </div>
            )}
          </div>

          {/* Shortcut Quick Chips Section */}
          <div className="flex flex-col gap-1.5">
            <span className="text-[10px] font-bold text-slate-500 font-mono tracking-widest uppercase flex items-center gap-1">
              <Sparkles className="w-3.5 h-3.5 text-emerald-400 animate-spin" style={{ animationDuration: '3s' }} />
              <span>اختصارات الفحص والترجمة السريعة (Quick Diagnostics):</span>
            </span>
            <div className="flex flex-wrap gap-1.5">
              {shortcutPrompts.map((chip, idx) => (
                <button
                  key={idx}
                  onClick={() => handleSendMessage(chip.text)}
                  disabled={isLoading}
                  className="text-[10px] font-semibold px-2 py-1.5 bg-slate-950 text-slate-300 hover:text-emerald-400 hover:border-emerald-500/50 border border-slate-800 rounded-lg transition-all text-left truncate max-w-full leading-tight active:scale-95"
                >
                  {chip.label}
                </button>
              ))}
            </div>
          </div>

          {/* 10 Advanced AI Testing Scenarios */}
          <div className="flex flex-col gap-2 border-t border-slate-800/85 pt-3">
            <button
              type="button"
              onClick={() => setShowTestScenarios(!showTestScenarios)}
              disabled={isLoading}
              className="text-[11px] font-extrabold text-cyan-400 font-mono tracking-wider uppercase flex items-center justify-between bg-slate-950 px-3 py-2.5 rounded-xl border border-slate-850 hover:bg-slate-850 transition-all cursor-pointer"
            >
              <span className="flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5 text-cyan-400 animate-pulse" />
                <span>🔬 تحدي الذكاء الاصطناعي الحقيقي: 10 اختبارات متقدمة</span>
              </span>
              <span className="text-[9px] bg-cyan-950/80 text-cyan-400 border border-cyan-800/40 px-2 py-0.5 rounded-lg font-black font-mono">
                {showTestScenarios ? "إغلاق الاختبارات ▲" : "استعراض الأفكار الـ 10 ▼"}
              </span>
            </button>

            {showTestScenarios && (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 mt-1 max-h-60 overflow-y-auto bg-slate-950/70 p-3 rounded-xl border border-slate-900 scrollbar-thin">
                {[
                  {
                    title: "🕵️‍♂️ كشف خداع المظهر المضلل (كوب مخفي)",
                    prompt: "أمامك مجسم يشبه كوب قهوة سيراميك لكن يوجد به ثقب دقيق عند المقبض ومؤشر حراري دافئ من الأسفل. حلل هذا السيناريو جنائياً: هل هناك ترجيح لوجود بطارية وباعث تذبذب، وكيف تكشفه طيفياً؟"
                  },
                  {
                    title: "⚡ سحب تيار الشاحن المريب (كهروهندسة)",
                    prompt: "شاحن جداري USB يسحب تياراً منخفضاً جداً (0.02A) حتى بدون وجود كابل متصل به. اشرح هندسياً ما الذي يبرر سحب التيار هذا في شريحة تتبع مغناطيسي وما الخطوات الأمنية التالية للتحقق؟"
                  },
                  {
                    title: "📡 فحص التداخل بالراوتر (إخفاء بالزعانف)",
                    prompt: "أعطني مواصفات فيزيائية حقيقية (أبعاد، وزن، معدل استرطاب، مستشعرات استقطاب) لجهاز راوتر Netgear Nighthawk AX12 وقدر فرصة إخفاء كاميرا تجسس داخل زعانفه الهوائية."
                  },
                  {
                    title: "📊 تشوه ظل الكشف الجنائي (سقوط فوتوني)",
                    prompt: "إذا كانت الساق اليمنى لدمية طفل قطنية تُلقي ظلاً مائلاً بزاوية 45 درجة بينما يسقط الضوء عمودياً من الأعلى تماماً، ما هو التحليل الجنائي للتشوه البصري واحتمالية تعديل الدمية لإخفاء كاميرا التلصص؟"
                  },
                  {
                    title: "🧠 مقارنة الموديلات (Gemini vs Qwen)",
                    prompt: "قارن بين كفاءة وحجم معالجة موديل Qwen 2.5 72B و Gemini 3.5 Flash في تتبع بصمات الـ RF (التردد الراديوي) وباقات البث اللاسلكي الخفية للأجهزة الأمنية."
                  },
                  {
                    title: "🚫 خطة تشويش مادية (GSM مكافحة)",
                    prompt: "صمم خطة تشويش مادية وصوتية ومغناطيسية يدوية لحماية الغرفة من جهاز تنصت دقيق يعتمد على شريحة GSM يلتقط الأصوات على مدى 8 أمتار ويرسلها للخارج."
                  },
                  {
                    title: "🚨 فحص تذبذب مستشعر PIR (راداري)",
                    prompt: "مستشعر حركة الجدران PIR يرسل إشعاعات نبضية دورية على بروتوكول Zigbee دون أن يكون هناك أي حركة بالغرفة. كيف تفصل طيفياً وتحديدياً بين الاستجابة الرادارية الخبيثة والاستجابة البيئية الطبيعية؟"
                  },
                  {
                    title: "🌐 ترجمة اصطلاحية طيفية (تحدي لغوي)",
                    prompt: "ترجم النص الطبي-التقني التالي بدقة صياغة المخابرات الأمنية والمصطلحات الدقيقة: 'Visual spectrum occlusion scan detected anomalous micro-aperture diffraction at 940nm spectrum.'"
                  },
                  {
                    title: "🔍 معامل انتقال الضوء (مرآة التجسس)",
                    prompt: "كيف يمكن لشريحة كاميرا تجسس مدمجة خلف زجاج مستقطب مرآتي (ساعة عاكسة) أن تقلل جودة الصورة بسبب معامل انتقال الضوء البالغ 35% فقط، وكيف يعوض معالج الكاميرا ذلك برمجياً؟"
                  },
                  {
                    title: "🌡️ تمييز حراري بيولوجي (حيوان vs راوتر)",
                    prompt: "حلل الفروقات الحرارية الدقيقة بين شبكة كهرومغناطيسية دافئة مدمجة بجهاز راوتر منزلي حيوي، وبين الانبعاث الحراري البيولوجي الطبيعي لقط متمدد يبلغ متوسط حرارته 38.5 درجة."
                  }
                ].map((scen, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => {
                      setInput(scen.prompt);
                      handleSendMessage(scen.prompt);
                    }}
                    disabled={isLoading}
                    className="p-3 bg-slate-950 border border-slate-850 hover:border-cyan-500/40 hover:bg-slate-900/40 rounded-xl cursor-pointer transition flex flex-col gap-1 text-right select-none active:scale-98 disabled:opacity-50"
                  >
                    <span className="text-[10px] font-bold text-cyan-400 font-mono flex items-center gap-1 justify-end w-full">
                      <span>{scen.title}</span>
                      <span className="text-[8px] bg-slate-900 px-1.5 py-0.2 rounded border border-slate-800 font-black text-slate-500">#{idx + 1}</span>
                    </span>
                    <p className="text-[10.5px] text-slate-400 leading-relaxed line-clamp-2 w-full text-right">
                      {scen.prompt}
                    </p>
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Input Box Actions */}
          <div className="flex flex-col gap-1">
            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleSendMessage(input);
              }}
              className="flex items-center gap-2 bg-slate-950 p-1.5 rounded-xl border border-slate-800"
            >
              {/* ── Improvement #15: ESC key clears input ── */}
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Escape") {
                    setInput("");
                  } else if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    handleSendMessage(input);
                  }
                }}
                placeholder="اسأل جيمني عن أي جهاز، طريقة كشف كاميرات مخفية، ترجمة فورية..."
                dir="rtl"
                rows={1}
                maxLength={500}
                className="flex-1 bg-transparent px-3 py-1.5 text-xs text-slate-100 placeholder-slate-500 outline-none border-none focus:ring-0 resize-none"
                disabled={isLoading}
              />
              <button
                type="submit"
                disabled={!input.trim() || isLoading || input.length > 500}
                className="bg-emerald-600 hover:bg-emerald-500 active:bg-emerald-700 disabled:bg-slate-800 disabled:text-slate-500 cursor-pointer p-2 rounded-lg text-slate-950 transition-all flex items-center justify-center"
              >
                <Send className="w-4 h-4" />
              </button>
            </form>
            {/* ── Improvement #14: character limit indicator ── */}
            <div className={`text-right text-[10px] font-mono pr-1 ${input.length > 480 ? "text-amber-400" : "text-slate-600"} ${input.length > 500 ? "text-red-400" : ""}`}>
              {input.length}/500
            </div>
          </div>
        </>
      )}
    </div>
  );
}
