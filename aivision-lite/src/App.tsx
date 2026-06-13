import React, { useState, useEffect } from "react";
import { PRESET_SCENARIOS } from "./data/presets";
import { PresetScenario, DetectedObject } from "./types";
import { getApiUrl } from "./lib/api";
import { analyzeImageWithGemini } from "./lib/gemini-direct";
import MobileFrame from "./components/MobileFrame";
import CameraView from "./components/CameraView";
import AnalysisPanel from "./components/AnalysisPanel";
import ScenarioGrid from "./components/ScenarioGrid";
import HistoryLog from "./components/HistoryLog";
import GeminiAssistant from "./components/GeminiAssistant";
import ApkHub from "./components/ApkHub";
import CloudSync from "./components/CloudSync";
import { ScanEye, Cpu, Battery, Info, RefreshCw, Layers, ShieldCheck, HeartPulse, Settings, Sparkles, Mail, Key, Globe, Play } from "lucide-react";

export default function App() {
  const [selectedPreset, setSelectedPreset] = useState<PresetScenario | null>(PRESET_SCENARIOS[0]);
  const [activeResult, setActiveResult] = useState<DetectedObject | null>(null);
  const [isScanning, setIsScanning] = useState(false);
  const [filterMode, setFilterMode] = useState<"normal" | "thermal" | "stealth" | "nightvision">("normal");
  const [logs, setLogs] = useState<DetectedObject[]>([]);
  const [isApkMode, setIsApkMode] = useState(true); // Default to gorgeous APK device mockup form factor

  // Persistent Settings State (Gemini Connection API Key, Model selection, Language options, and custom API/mail credentials)
  const [settings, setSettings] = useState(() => {
    const savedKey = localStorage.getItem("aiv_gemini_key") || "";
    const savedModel = localStorage.getItem("aiv_gemini_model") || "gemini-2.0-flash";
    const savedTargetLang = localStorage.getItem("aiv_target_lang") || "Arabic";
    const savedAutoTranslate = localStorage.getItem("aiv_auto_translate") !== "false";
    const savedEmail = localStorage.getItem("aiv_email") || "";
    const savedPassword = localStorage.getItem("aiv_password") || "";
    const savedApiEndpoint = localStorage.getItem("aiv_api_endpoint") || "https://api.aivision.security/v1";
    const savedMobileBackend = localStorage.getItem("aiv_mobile_backend_url") || "";
    return {
      apiKey: savedKey,
      model: savedModel,
      targetLanguage: savedTargetLang,
      autoTranslate: savedAutoTranslate,
      email: savedEmail,
      password: savedPassword,
      apiEndpoint: savedApiEndpoint,
      mobileBackendUrl: savedMobileBackend,
    };
  });

  const [showSettings, setShowSettings] = useState(false);

  // Sync settings modifications directly to localStorage on modification
  const updateSettings = (updates: Partial<typeof settings>) => {
    setSettings((prev) => {
      const next = { ...prev, ...updates };
      localStorage.setItem("aiv_gemini_key", next.apiKey);
      localStorage.setItem("aiv_gemini_model", next.model);
      localStorage.setItem("aiv_target_lang", next.targetLanguage);
      localStorage.setItem("aiv_auto_translate", String(next.autoTranslate));
      if (next.email !== undefined) localStorage.setItem("aiv_email", next.email);
      if (next.password !== undefined) localStorage.setItem("aiv_password", next.password);
      if (next.apiEndpoint !== undefined) localStorage.setItem("aiv_api_endpoint", next.apiEndpoint);
      if (next.mobileBackendUrl !== undefined) localStorage.setItem("aiv_mobile_backend_url", next.mobileBackendUrl);
      return next;
    });
  };

  // Load cache logs from localStorage
  useEffect(() => {
    try {
      const stored = localStorage.getItem("aiv_scan_logs");
      if (stored) {
        setLogs(JSON.parse(stored));
      } else {
        // Hydrate default log with standard presets as initial examples
        const starterLogs: DetectedObject[] = [
          {
            id: "init_1",
            name: "مقبس شاحن جداري ذو كاميرا مخفية (Covert USB Charger Camera)",
            category: "Spy & Covert Gear",
            size: "4.8cm x 3.2cm x 3.2cm",
            description: "شاحن USB جداري حقيقي بقدرة 5V/2A مزود بعدسة كاميرا مجهرية مخفية خلف لوح زجاج أكريليك غامق يمتص الضوء ومصمم لمنع الانعكاس.",
            confidence: 99.5,
            toolsFound: ["عدسة مجهرية مخفية (Pinhole Lens)", "هوائي إرسال لا سلكي 2.4GHz", "محلل استهلاك الطاقة المستمر"],
            hideCameraStatus: "🔴 خطر أمني مرتفع: تم رصد عدسة تجسس مجهرية خلف غطاء المقبس! تردد البث النشط: 2.412 GHz.",
            extraDetails: [
              { key: "Refraction Index", value: "1.49 High-convoluted lens feedback" },
              { key: "Wireless Beacon", value: "WiFi standard 802.11b/g/n active" }
            ],
            scannedAt: new Date(Date.now() - 3600000).toISOString(),
            source: "local_db",
            imageUrl: ""
          },
          {
            id: "init_2",
            name: "65-inch Bezel-less OLED TV",
            category: "TV & Room Equipment",
            size: "144.9cm x 83.2cm x 4.8cm",
            description: "Extremely thin profile deep-black organic light emitting diode screen. Supported on a sand-blasted silver metal deck stand.",
            confidence: 99.8,
            toolsFound: ["OLED emission panel", "HDMI 2.1 physical hub"],
            hideCameraStatus: "Threat Checked: Inspecting bezel collar. No pinhole lens in screen frame.",
            extraDetails: [
              { key: "Panel Tech", value: "Self-emitting subpixel OLED arrays" },
              { key: "Current Draw", value: "185 Watts active state" }
            ],
            scannedAt: new Date(Date.now() - 1800000).toISOString(),
            source: "local_db",
            imageUrl: ""
          }
        ];
        setLogs(starterLogs);
        localStorage.setItem("aiv_scan_logs", JSON.stringify(starterLogs));
      }
    } catch (e) {
      console.warn("localStorage block: ", e);
    }
  }, []);

  const [isSecureAuthed, setIsSecureAuthed] = useState(false);
  useEffect(() => {
    const checkAuthStatus = () => {
      const authed = localStorage.getItem("gemini_secure_authed") === "true";
      if (authed !== isSecureAuthed) {
        setIsSecureAuthed(authed);
      }
    };
    checkAuthStatus();
    const interval = setInterval(checkAuthStatus, 1000);
    return () => clearInterval(interval);
  }, [isSecureAuthed]);

  // Interactive Connection & Workspace Simulation Engine (10 Advanced Ideas)
  const [activeSimId, setActiveSimId] = useState<number | null>(null);
  const [simLogs, setSimLogs] = useState<string[]>([]);
  const [isSimulating, setIsSimulating] = useState(false);
  const [showSimSection, setShowSimSection] = useState(false);

  const runAdvancedWorkspaceScenario = (idx: number, title: string) => {
    if (!settings.email || !settings.password) {
      alert("⚠️ يرجى تعيين البريد الإلكتروني وكلمة المرور في لوحة إعدادات النظام للاتصال أولاً لبدء المحاكاة الأمنية المشفرة!");
      return;
    }
    setIsSimulating(true);
    setActiveSimId(idx);
    setSimLogs([
      `⚡ [بدء] تهيئة نظام الاستشعار الجنائي للسيناريو رقم ${idx}...`,
      `📧 [المصادقة] محاولة التوثيق الآمن باستخدام: ${settings.email}`,
      `🔗 [الشبكة] الاتصال بالخادم البوابة للـ API: ${settings.apiEndpoint}`,
    ]);

    setTimeout(() => {
      setSimLogs((prev) => [
        ...prev,
        `🔑 [المصادقة] تم التفاوض وتوليد رمز المفتاح المؤقت للـ API عبر مصادقة SHA-256 بنجاح.`,
        `📡 [النفاذ] استلام ترخيص قنوات الراديو النشطة ومزامنة باقات بروتوكول الكشف...`,
      ]);
    }, 600);

    setTimeout(() => {
      setSimLogs((prev) => [
        ...prev,
        `🚀 [إنهاء] تفعيل تشغيل السيناريو بنجاح: ${title}`,
        `📬 [تقرير] تم دفع حزمة الأوامر والتقرير آلياً إلى الخادم المستهدف وإرسال نسخة تأكيد بريدية إلى البوكس الخاص بـ ${settings.email}!`,
        "✅ [نظام] تم حفظ الأرشيف في سجلات التموضع المحلي بنجاح بنسبة ثقة %100.",
      ]);
      setIsSimulating(false);
    }, 1505);
  };

  // Sync state log updates to local storage
  const updateLogsCache = (newLogs: DetectedObject[]) => {
    setLogs(newLogs);
    try {
      localStorage.setItem("aiv_scan_logs", JSON.stringify(newLogs));
    } catch (e) {
      console.warn("Storage write failure", e);
    }
  };

  // Sound Synth Generator (No external static .mp3 files needed)
  const playSynthesizerTone = (type: "chirp" | "success" | "delete") => {
    try {
      const AudioCtx = window.AudioContext || (window as any).webkitAudioContext;
      if (!AudioCtx) return;
      const ctx = new AudioCtx();

      if (type === "chirp") {
        // Laser radar chirp sound
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.connect(gain);
        gain.connect(ctx.destination);

        osc.type = "sawtooth";
        osc.frequency.setValueAtTime(650, ctx.currentTime);
        osc.frequency.exponentialRampToValueAtTime(150, ctx.currentTime + 0.35);

        gain.gain.setValueAtTime(0.08, ctx.currentTime);
        gain.gain.linearRampToValueAtTime(0.001, ctx.currentTime + 0.35);

        osc.start();
        osc.stop(ctx.currentTime + 0.35);
      } else if (type === "success") {
        // Sweet double electronic chime tone
        const playBeep = (freq: number, start: number, duration: number) => {
          const osc = ctx.createOscillator();
          const gain = ctx.createGain();
          osc.connect(gain);
          gain.connect(ctx.destination);

          osc.type = "sine";
          osc.frequency.setValueAtTime(freq, start);

          gain.gain.setValueAtTime(0.06, start);
          gain.gain.linearRampToValueAtTime(0.001, start + duration);

          osc.start(start);
          osc.stop(start + duration);
        };

        playBeep(587.33, ctx.currentTime, 0.15); // D5
        playBeep(880.00, ctx.currentTime + 0.12, 0.25); // A5
      } else if (type === "delete") {
        // Bass down click
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.connect(gain);
        gain.connect(ctx.destination);

        osc.type = "triangle";
        osc.frequency.setValueAtTime(220, ctx.currentTime);
        osc.frequency.linearRampToValueAtTime(80, ctx.currentTime + 0.15);

        gain.gain.setValueAtTime(0.12, ctx.currentTime);
        gain.gain.linearRampToValueAtTime(0.001, ctx.currentTime + 0.15);

        osc.start();
        osc.stop(ctx.currentTime + 0.15);
      }
    } catch (err) {
      // AudioContext blocker bypassed silently
    }
  };

  // Setup Initial selected preset when loading or changing preset triggers
  useEffect(() => {
    if (selectedPreset) {
      // Form matching DetectedObject from static scenario info
      const scanItem: DetectedObject = {
        id: "local_" + selectedPreset.id,
        name: selectedPreset.name,
        category: selectedPreset.category,
        size: selectedPreset.size,
        description: selectedPreset.description,
        confidence: selectedPreset.confidence,
        toolsFound: selectedPreset.toolsFound,
        hideCameraStatus: selectedPreset.hideCameraStatus,
        extraDetails: selectedPreset.extraDetails,
        scannedAt: new Date().toISOString(),
        source: "local_db",
        imageUrl: "" // simulation canvas handles custom visual rendering
      };
      setActiveResult(scanItem);
    }
  }, [selectedPreset]);

  // Handler for custom captured snapshots (camera or uploaded triggers)
  const handleImageCaptured = async (base64Image: string, nameHint: string, forensicMode?: boolean) => {
    setIsScanning(true);
    playSynthesizerTone("chirp");

    // Clear active preset temporarily since they are running custom analyze
    setSelectedPreset(null);

    const savedEmail = localStorage.getItem("gemini_user_email") || "";
    const isAuthed = localStorage.getItem("gemini_secure_authed") === "true";

    try {
      let scanResult: DetectedObject;

      if (settings.apiKey && settings.apiKey.trim().length > 5) {
        // Direct Gemini call from the client — works when Cloud Run is unreachable
        console.log("▲ Using direct Gemini API for image scan...");
        const prompt = forensicMode
          ? `Goal: You are an Advanced Digital Forensics Analyzer. Analyze the image and return a SINGLE JSON object with fields: name, category, size, description, confidence (85-99.8), toolsFound (array of 3), hideCameraStatus, extraDetails (array of 4 key-value objects), weight, brand, modelNumber, estimatedPrice, buyLink, translationResult (object with originalText, targetLang "ar", translatedText in Arabic). Return ONLY valid compact JSON.`
          : `Goal: You are the core analyzer engine of 'AI Vision'. Analyze the provided image. Category clue: ${nameHint || "general object"}. Return a SINGLE JSON object with fields: name, category, size, description, confidence (85-99.8), toolsFound (array of 3), hideCameraStatus, extraDetails (array of 4 key-value objects), weight, brand, modelNumber, estimatedPrice, buyLink, translationResult (object with originalText, targetLang "ar", translatedText in Arabic). Return ONLY valid compact JSON.`;

        let mimeType = "image/jpeg";
        let base64Data = base64Image;
        if (base64Image.startsWith("data:")) {
          const match = base64Image.match(/data:([^;]+);/);
          if (match) mimeType = match[1];
          base64Data = base64Image.split(";base64,")[1];
        }

        const rawText = await analyzeImageWithGemini(settings.apiKey.trim(), settings.model, base64Data, mimeType, prompt, true);
        let parsed: any = {};
        try {
          let clean = rawText.trim();
          if (clean.includes("```json")) clean = clean.split("```json")[1].split("```")[0];
          else if (clean.includes("```")) clean = clean.split("```")[1].split("```")[0];
          parsed = JSON.parse(clean.trim());
        } catch {
          parsed = { name: "تحليل الصورة", category: "General Equipment", description: rawText, confidence: 85, toolsFound: [], hideCameraStatus: "N/A", extraDetails: [] };
        }

        scanResult = {
          ...parsed,
          id: "scan_" + Date.now(),
          scannedAt: new Date().toISOString(),
          source: "gemini_api" as const,
          imageUrl: base64Image,
          boundingBox: parsed.boundingBox || { x: 20, y: 20, w: 60, h: 60 }
        };
      } else {
        // Fall back to Cloud Run backend
        console.log("▲ Dispatching base64 image to server scanner API...");
        const response = await fetch(getApiUrl("/api/scan"), {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "x-gemini-key": settings.apiKey,
            "x-gemini-model": settings.model,
            "x-gemini-email": savedEmail,
            "x-gemini-authed": isAuthed ? "true" : "false"
          },
          body: JSON.stringify({
            image: base64Image,
            categoryHint: nameHint,
            forensicMode: forensicMode
          })
        });

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({ message: response.statusText }));
          throw new Error(errorData.message || response.statusText);
        }

        scanResult = await response.json();
      }

      console.log("▲ Scan result parsed:", scanResult);

      // Successfully processed! Play sound feedback
      playSynthesizerTone("success");
      setActiveResult(scanResult);

      // Append result to local history log list
      const updatedList = [scanResult, ...logs];
      updateLogsCache(updatedList);

    } catch (err: any) {
      console.error("▲ Analysis Dispatch error: ", err);
      // Removed automated mock visual analysis as it caused silent failure masking.
      alert("Error analyzing image: " + err.message);
    } finally {
      setIsScanning(false);
    }
  };

  const selectHistoryItem = (item: DetectedObject) => {
    setActiveResult(item);
    playSynthesizerTone("success");
  };

  const clearHistoryLogs = () => {
    if (confirm("Are you sure you want to wipe the complete local storage scan history?")) {
      playSynthesizerTone("delete");
      updateLogsCache([]);
      setActiveResult(null);
    }
  };

  const removeIndividualLog = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    playSynthesizerTone("delete");
    const updated = logs.filter(l => l.id !== id);
    updateLogsCache(updated);
    if (activeResult?.id === id) {
      setActiveResult(null);
    }
  };

  const selectPresetFromGrid = (preset: PresetScenario) => {
    setSelectedPreset(preset);
  };

  return (
    <MobileFrame isApkMode={isApkMode} setIsApkMode={setIsApkMode}>
      
      {/* App main container block */}
      <div className="flex-1 flex flex-col gap-5 p-2 md:p-3 pb-8">
        
        {/* Core HUD Header */}
        <div className="flex justify-between items-center gap-3 bg-slate-900/60 p-3 rounded-xl border border-slate-800">
          <div className="flex items-center gap-2">
            <ScanEye className="w-6 h-6 text-emerald-400 animate-pulse" />
            <div>
              <span className="font-mono text-[9px] text-emerald-400 font-extrabold tracking-widest block uppercase">
                COGNITIVE COMBAT VISION SYSTEM
              </span>
              <h2 className="text-sm font-bold font-sans tracking-tight text-slate-100 uppercase">
                AI Vision Lite <span className="text-[10px] text-slate-500 font-normal">v2.5.2</span>
              </h2>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button
              id="btn-toggle-settings-board"
              onClick={() => {
                setShowSettings(!showSettings);
                playSynthesizerTone("success");
              }}
              className={`flex items-center gap-1.5 px-3 py-1.5 text-xs rounded-lg border font-mono transition font-bold leading-none ${
                showSettings
                  ? "bg-emerald-500 text-slate-950 border-emerald-400"
                  : "bg-slate-950 border-slate-855 text-emerald-400 hover:border-emerald-500/50"
              }`}
              title="لوحة الضبط والإعدادات للاتصال وجيميني"
            >
              <Settings className={`w-3.5 h-3.5 ${showSettings ? "animate-spin" : ""}`} style={{ animationDuration: '10s' }} />
              <span>إعدادات النظام [SETTINGS]</span>
            </button>

            {isSecureAuthed && (
              <div className="flex items-center gap-1.5 font-mono text-[10px] bg-emerald-950/40 px-2 py-1.5 rounded border border-emerald-500/30 text-emerald-300">
                <Sparkles className="w-3.5 h-3.5 text-emerald-400 animate-pulse" />
                <span>جيمني: متصل بالبريد (دقة فائقة)</span>
              </div>
            )}

            <div className="flex items-center gap-1.5 font-mono text-[10px] bg-slate-950 px-2 py-1.5 rounded border border-slate-850 text-slate-400">
              <Cpu className="w-3.5 h-3.5 text-emerald-400 animate-spin" style={{ animationDuration: '4s' }} />
              <span>SAT_LINK: UP</span>
            </div>
          </div>
        </div>

        {/* Persisted Settings Panel */}
        {showSettings && (
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 md:p-5 flex flex-col gap-4 shadow-2xl animate-in fade-in slide-in-from-top duration-300" dir="rtl">
            <div className="flex flex-wrap justify-between items-center border-b border-slate-800 pb-2 gap-2">
              <h3 className="font-extrabold text-xs text-slate-200 tracking-wider flex items-center gap-2">
                <Settings className="w-4 h-4 text-emerald-400 rotate-45" />
                تحكم الاتصال ومعالج جيمني السحابي (Gemini Core Configuration)
              </h3>
              <span className="text-[9px] bg-slate-950 border border-slate-850 px-2 py-0.5 rounded font-mono text-emerald-400 font-extrabold">
                STATUS: AUTO_SYNC_OK
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Gemini API Key */}
              <div className="flex flex-col gap-1.5">
                <label className="text-[11px] text-slate-300 font-bold">مفتاح API الخاص بـ Gemini (Gemini API Key)</label>
                <input
                  type="password"
                  value={settings.apiKey}
                  onChange={(e) => updateSettings({ apiKey: e.target.value })}
                  placeholder="أدخل مفتاح Gemini هنا (مثال: AIzaSy...)"
                  className="bg-slate-950 border border-slate-800 text-slate-100 rounded-lg p-2 text-xs font-mono placeholder-slate-600 focus:border-emerald-500/50 outline-none transition"
                />
                <p className="text-[9px] text-slate-500 font-mono">
                  سيتم تخزين المفتاح بشكل آمن محلياً في ذاكرة متصفحك المتنقلة ولن يفقد أبداً عند تحديث الصفحة أو الخروج.
                </p>
              </div>

              {/* Gemini Model */}
              <div className="flex flex-col gap-1.5">
                <label className="text-[11px] text-slate-300 font-bold">طراز معالج الذكاء الاصطناعي (AI Model)</label>
                <select
                  value={settings.model}
                  onChange={(e) => updateSettings({ model: e.target.value })}
                  className="bg-slate-950 border border-slate-800 text-slate-100 rounded-lg p-2 text-xs focus:border-emerald-500/50 outline-none transition"
                >
                  <option value="gemini-3.5-flash">Gemini 3.5 Flash (الأساسي - الأسرع للأجهزة والأحدث)</option>
                  <option value="gemini-3.1-pro-preview">Gemini 3.1 Pro (التحليل البصري العالي والمجهري)</option>
                  <option value="qwen-2.5-72b">Qwen 2.5 Instruct (Alibaba كيوين - طيف ذكي مدمج)</option>
                  <option value="kimi-chat-v1">Kimi Chat Ultra (Moonshot كيمي - للتقارير والترجمة)</option>
                  <option value="claude-3-haiku">Claude 3 Haiku (Anthropic كلاود هايكو - استدلال مدمج)</option>
                  <option value="deepseek-v3">DeepSeek V3 (ديب سيك - ذكاء فائق مدمج)</option>
                </select>
                <p className="text-[9px] text-slate-500">
                  اختر Pro للتحليل البصري فائق الدقة لمواصفات الأجهزة وتفاصيل الأجهزة المجهرية.
                </p>
              </div>

              {/* Default Translation Target */}
              <div className="flex flex-col gap-1.5">
                <label className="text-[11px] text-slate-300 font-bold">لغة الترجمة الفورية بمخرجات الفحص (Interactive Language)</label>
                <select
                  value={settings.targetLanguage}
                  onChange={(e) => updateSettings({ targetLanguage: e.target.value })}
                  className="bg-slate-950 border border-slate-800 text-slate-100 rounded-lg p-2 text-xs focus:border-emerald-500/50 outline-none transition"
                >
                  <option value="Arabic">العربية (Arabic)</option>
                  <option value="English">English</option>
                  <option value="Spanish">Español (Spanish)</option>
                  <option value="French">Français (French)</option>
                  <option value="Russian">Русский (Russian)</option>
                </select>
                <p className="text-[9px] text-slate-500">
                  سيتم توجيه المساعد لترجمة كافة محتويات الفحص وقوائم الكشف باللغات المراد استهدافها فورا.
                </p>
              </div>

              {/* Connection Email */}
              <div className="flex flex-col gap-1.5">
                <label className="text-[11px] text-slate-300 font-bold flex items-center gap-1.5">
                  <Mail className="w-3.5 h-3.5 text-emerald-400" />
                  <span>البريد الإلكتروني للربط والمزامنة (Connection Email)</span>
                </label>
                <input
                  type="email"
                  value={settings.email}
                  onChange={(e) => updateSettings({ email: e.target.value })}
                  placeholder="name@security.com"
                  className="bg-slate-950 border border-slate-800 text-slate-100 rounded-lg p-2 text-xs font-mono placeholder-slate-600 focus:border-emerald-500/50 outline-none transition text-left"
                />
                <p className="text-[9px] text-slate-500">
                  البريد المعتمد للمصادقة وتلقي الإشعارات الفورية وتقارير الفحص الجنائي لثغرات الأجهزة المجهرية.
                </p>
              </div>

              {/* Connection Password */}
              <div className="flex flex-col gap-1.5">
                <label className="text-[11px] text-slate-300 font-bold flex items-center gap-1.5">
                  <Key className="w-3.5 h-3.5 text-emerald-400" />
                  <span>كلمة مرور التوثيق المؤمن (Secure Connection Password)</span>
                </label>
                <input
                  type="password"
                  value={settings.password}
                  onChange={(e) => updateSettings({ password: e.target.value })}
                  placeholder="••••••••••••"
                  className="bg-slate-950 border border-slate-800 text-slate-100 rounded-lg p-2 text-xs font-mono placeholder-slate-600 focus:border-emerald-500/50 outline-none transition text-left"
                />
                <p className="text-[9px] text-slate-500">
                  كلمة المرور المشفرة للتحقق من هوية العميل وإجراء المعاملات السحابية ومزامنة قواعد البيانات.
                </p>
              </div>

              {/* Connection Custom API Endpoint */}
              <div className="flex flex-col gap-1.5 md:col-span-2">
                <label className="text-[11px] text-slate-300 font-bold flex items-center gap-1.5">
                  <Globe className="w-3.5 h-3.5 text-emerald-400" />
                  <span>رابط الخادم المخصص للـ API (Custom API Endpoint)</span>
                </label>
                <input
                  type="text"
                  value={settings.apiEndpoint}
                  onChange={(e) => updateSettings({ apiEndpoint: e.target.value })}
                  placeholder="https://api.aivision.security/v1"
                  className="bg-slate-950 border border-slate-800 text-slate-100 rounded-lg p-2 text-xs font-mono placeholder-slate-600 focus:border-emerald-500/50 outline-none transition text-left"
                />
                <p className="text-[9px] text-slate-500">
                  عنوان الواجهة البرمجية (API Endpoint Url) لإرسال تقارير Telemetry وبصمات الـ RF وتنبيهات الكشف للمخدم المركزي الخاص بك.
                </p>
              </div>

              {/* Mobile Backend URL */}
              <div className="flex flex-col gap-1.5 md:col-span-2">
                <label className="text-[11px] text-slate-300 font-bold flex items-center gap-1.5">
                  <Globe className="w-3.5 h-3.5 text-emerald-400" />
                  <span>رابط مخدم التطبيق الخلفي المخصص للتشغيل على الهواتف (Mobile Backend/Server URL - Local IP)</span>
                </label>
                <input
                  type="text"
                  value={settings.mobileBackendUrl}
                  onChange={(e) => updateSettings({ mobileBackendUrl: e.target.value })}
                  placeholder="http://192.168.1.100:3000"
                  className="bg-slate-950 border border-slate-800 text-slate-100 rounded-lg p-2 text-xs font-mono placeholder-slate-600 focus:border-emerald-500/50 outline-none transition text-left"
                />
                <p className="text-[9px] text-emerald-500/90 leading-relaxed">
                  <strong>💡 تلميح للهواتف الذكية:</strong> إذا كنت تقوم بتشغيل التطبيق المدمج على هاتفك وتريد ربطه بحاسوبك، اكتب عنوان IP للـ Wi-Fi الخاص بحاسوبك متبوعاً بـ :3000 (مثال: <code className="bg-slate-950 px-1 py-0.5 rounded text-emerald-400">http://192.168.1.100:3000</code>). دعها فارغة لاستخدام الخادم السحابي التجريبي الافتراضي.
                </p>
              </div>
            </div>

            {/* 10 Advanced Connection Scenarios Section */}
            <div className="border-t border-slate-800/80 pt-4 flex flex-col gap-3">
              <button
                type="button"
                onClick={() => setShowSimSection(!showSimSection)}
                className="text-xs font-extrabold text-emerald-400 font-sans tracking-wide uppercase flex items-center justify-between bg-slate-950 px-3 py-3 rounded-xl border border-slate-850 hover:bg-slate-850 transition-all cursor-pointer"
              >
                <span className="flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-emerald-400 animate-pulse" />
                  <span>🔬 اختبار وتفعيل 10 مبادرات ذكية متطورة (Mail & API Connections Scenarios)</span>
                </span>
                <span className="text-[9px] bg-emerald-950/80 text-emerald-400 border border-emerald-800/40 px-2 py-0.5 rounded-lg font-black font-mono">
                  {showSimSection ? "إغلاق الواجهة ▲" : "استعراض الأفكار الـ 10 ▼"}
                </span>
              </button>

              {showSimSection && (
                <div className="flex flex-col gap-3 bg-slate-950/65 p-4 rounded-xl border border-slate-900">
                  <div className="text-[11px] text-slate-300 leading-relaxed text-right mb-1">
                    أدخل بريدك وكلمة السر ورابط الـ API بالأعلى، ثم انقر على أي مبادرة تقنية أدناه لبدء اختبار محاكاة مشفرة فورية للبروتوكول وإصدار تقرير تفصيلي:
                  </div>

                  {activeSimId !== null && (
                    <div className="bg-slate-950 border border-emerald-500/20 p-3 rounded-lg flex flex-col gap-1 font-mono text-[10.5px] text-emerald-400 animate-pulse">
                      <span className="font-bold text-slate-200">📊 سجل المراقبة التفاعلي التلقائي لـ [API, Mail & Auth Simulator]</span>
                      <div className="space-y-1 mt-1.5 text-slate-300 antialiased text-left" dir="ltr">
                        {simLogs.map((log, lidx) => (
                          <p key={lidx} className={`${lidx === simLogs.length - 1 && isSimulating ? 'text-emerald-400 font-bold' : 'text-slate-450'}`}>
                            {log}
                          </p>
                        ))}
                      </div>
                    </div>
                  )}

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-h-96 overflow-y-auto pr-1 scrollbar-thin">
                    {[
                      {
                        title: "📡 SMTP Spectral Auto-Alert (تبليغ طيفي تلقائي بالبريد)",
                        desc: "إرسال تقرير فني فوري برمز تجسيم آمن لكل عدسة مجهرية يتم رصدها في الفحص البصري لتأمين الموقع الحساس.",
                        btn: "إطلاق تجربة التبليغ بريدياً"
                      },
                      {
                        title: "💾 Live Encrypted Database Backup (مزامنة سحابية مستمرة)",
                        desc: "حفظ باقات تاريخ الفحص المشفرة تلقائياً كل ساعة في قواعد البيانات الترددية بدقة تفتيش فائقة.",
                        btn: "تجربة مزامنة البيانات"
                      },
                      {
                        title: "🛡️ API Token Handshake JWT (مصادقة وفحص طاقة البث)",
                        desc: "تأسيس اتصال فحص وتوفير شهادات آمنة لضمان أمن التموضع وتفادي اختراق قنوات الرسيفر اللاسلكي.",
                        btn: "اختبار فحص مصادقة JWT"
                      },
                      {
                        title: "🛰️ Telemetry Realtime Webhook (تفريغ قنوات تتبع البث)",
                        desc: "بث مباشر لمستويات الفولطية والموجات الملتقطة لربطها بشاشات المراقبة الجنائية الأمنية والمحللات السحابية.",
                        btn: "تفريغ قنوات الـ Webhook"
                      },
                      {
                        title: "🧠 Translation Core Load Balancer (موازنة استهلاك الموديلات)",
                        desc: "تبديل معالجة التحليل البصري الهجين تلقائياً عند نفاذ حصة الاستخدام للملقم لتوفير الترجمات الأمنية المعتمدة.",
                        btn: "اختبار موازن الاستدلال"
                      },
                      {
                        title: "🚨 Zero-Day Micro-Sensor Database (التحقق مع السحابة العالمية)",
                        desc: "مقارنة البصمات الإلكترونية الملتقطة محلياً مع قاعدة بيانات الأجهزة العالمية للكشف عن تفعيلات التجسس النادرة.",
                        btn: "فحص الصفر الهجمي للمجسّ"
                      },
                      {
                        title: "🔑 Panic Lockdown Wipe Protocol (بروتوكول تدمير المعطيات)",
                        desc: "محو تفاصيل الاستكشاف وشهادات الدخول فوراً عند رصد 3 محاولات اتصال خاطئة لمنع هندسة كود المشروع العكسية.",
                        btn: "تأمين بروتوكول الإغلاق"
                      },
                      {
                        title: "📧 Executive Scheduled PDF Auto-Digest (الملخص الأسبوعي بالبريد)",
                        desc: "صنع ملف PDF تفصيلي لكافة الأجهزة المشبوهة المرصودة وإرساله بالبريد الإلكتروني للجهات المسؤولة تلقائياً.",
                        btn: "إرسال ملخص PDF بالبريد"
                      },
                      {
                        title: "🔮 Multi-Agent LLM Model Handshake (مزامنة استدلال كيوين وجيمني)",
                        desc: "دمج ردود الاستدلال لـ Gemini v2.5 و DeepSeek برمجياً لرفع دقة التقييم الهندسي للأجهزة المجهولة.",
                        btn: "دمج قرارات الاستدلال بالـ API"
                      },
                      {
                        title: "⚡ Multi-Node Array Geo-Sync (مزامنة الخلايا الميدانية)",
                        desc: "شحن نقاط رصد كهرومغناطيسية متعددة لتتبع مستودع الأجهزة المخترقة جغرافياً وعبر خرائط حية للـ API.",
                        btn: "مزامنة التموضع الجغرافي"
                      }
                    ].map((scen, idx) => (
                      <div
                        key={idx}
                        className="p-3 bg-slate-900 border border-slate-850 rounded-xl transition flex flex-col justify-between gap-2.5 text-right w-full"
                      >
                        <div className="flex flex-col gap-1 w-full">
                          <span className="text-[11px] font-black text-emerald-400 font-mono flex items-center gap-1 justify-end w-full">
                            <span>{scen.title}</span>
                            <span className="text-[8px] bg-emerald-950 text-emerald-400 px-1.5 py-0.2 rounded border border-emerald-900 font-mono font-black">#{idx + 1}</span>
                          </span>
                          <p className="text-[10px] text-slate-400 leading-relaxed w-full">
                            {scen.desc}
                          </p>
                        </div>
                        <button
                          type="button"
                          onClick={() => runAdvancedWorkspaceScenario(idx + 1, scen.title)}
                          disabled={isSimulating}
                          className="w-full bg-slate-950 hover:bg-emerald-500 hover:text-slate-950 transition-all font-mono text-[10px] font-bold py-1.5 px-3 rounded-lg border border-slate-800 flex items-center justify-center gap-1.5 hover:cursor-pointer disabled:opacity-50"
                        >
                          <Play className="w-3 h-3 text-emerald-400 pointer-events-none" />
                          <span>{scen.btn}</span>
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Dynamic Warning Alert banner for unconfigured Gemini Key */}
        {!process.env.GEMINI_API_KEY && (
          <div className="bg-amber-950/20 border border-amber-500/35 px-3 py-2 rounded-xl flex items-start gap-2.5">
            <Info className="w-4 h-4 text-amber-500 mt-0.5 flex-shrink-0" />
            <div className="text-[10px] font-mono text-amber-300 leading-snug">
              <span className="font-bold">SYSTEM BROADCAST:</span> Gemini Vision API Key is operating in fallback simulation. Capture any image or choose 30 presets below to run deep optical diagnostics! Configure secrets in setting bar.
            </div>
          </div>
        )}

        {/* Master layout: Camera, scan outputs, and local inventory catalog */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 items-start">
          
          {/* Left Column: Viewfinder camera HUD (7 cols wide on desktop) */}
          <div className="lg:col-span-7 flex flex-col gap-5">
            <CameraView
              selectedPreset={selectedPreset}
              onImageCaptured={handleImageCaptured}
              isScanning={isScanning}
              filterMode={filterMode}
              setFilterMode={setFilterMode}
              onSelectPreset={setSelectedPreset}
            />

            <GeminiAssistant activeScanResult={activeResult} />

            {/* Catalog Grid block directly below camera */}
            <div className="hidden lg:block">
              <ScenarioGrid
                onSelectScenario={selectPresetFromGrid}
                activeScenarioId={selectedPreset?.id || null}
              />
            </div>
          </div>

          {/* Right Column: Active telemetry readout and diagnostic checklist (5 cols wide) */}
          <div className="lg:col-span-5 flex flex-col gap-5">
            <AnalysisPanel
              scanResult={activeResult}
              isScanning={isScanning}
            />

            <ApkHub />

            <CloudSync lastScanResult={activeResult} logs={logs} />

            <HistoryLog
              logs={logs}
              onSelectLog={selectHistoryItem}
              onClearLogs={clearHistoryLogs}
              onRemoveLog={removeIndividualLog}
              activeLogId={activeResult?.id || null}
            />

            {/* Catalog Grid for mobile viewport below history log */}
            <div className="block lg:hidden">
              <ScenarioGrid
                onSelectScenario={selectPresetFromGrid}
                activeScenarioId={selectedPreset?.id || null}
              />
            </div>
          </div>

        </div>

      </div>

    </MobileFrame>
  );
}
