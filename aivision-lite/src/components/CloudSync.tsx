import React, { useState, useEffect } from "react";
import { Download, Cloud, Github, CheckCircle, AlertTriangle, RefreshCw, Copy, ExternalLink, HelpCircle } from "lucide-react";
import { DetectedObject } from "../types";
import { getApiUrl } from "../lib/api";

interface CloudSyncProps {
  lastScanResult: DetectedObject | null;
  logs: DetectedObject[];
}

export default function CloudSync({ lastScanResult, logs }: CloudSyncProps) {
  const [activeTab, setActiveTab] = useState<"drive" | "github">("drive");
  const [accessToken, setAccessToken] = useState(() => {
    return localStorage.getItem("aiv_drive_token") || "";
  });
  const [savingProject, setSavingProject] = useState(false);
  const [savingReport, setSavingReport] = useState(false);
  const [statusMsg, setStatusMsg] = useState<{ type: "success" | "error"; text: string } | null>(null);
  const [copiedText, setCopiedText] = useState(false);

  // Sync token to persistent storage
  const handleTokenChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const token = e.target.value;
    setAccessToken(token);
    localStorage.setItem("aiv_drive_token", token);
  };

  // Trigger server-side recursive ZIP generation and client-side browser file download
  const handleDownloadZip = async () => {
    try {
      setStatusMsg(null);
      // Create a native anchor block to download
      window.location.href = getApiUrl("/api/download-project");
    } catch (err: any) {
      console.error(err);
      setStatusMsg({ type: "error", text: "فشل تجميع وتحميل ملف المشروع المضغوط: " + err.message });
    }
  };

  // Upload full project package zip directly to Google Drive
  const handleBackupToDrive = async () => {
    if (!accessToken.trim()) {
      // Automatic fallback simulation when token is not set
      setSavingProject(true);
      setTimeout(() => {
        setSavingProject(false);
        // Let user download it so they don't loose their work, simulating success
        window.location.href = getApiUrl("/api/download-project");
        setStatusMsg({
          type: "success",
          text: "🎉 [طريقة المحاكاة الاحتياطية]: تم تجميع الكود البرمجي للمشروع كتجربة، وتنزيله كملف ZIP بنجاح! للإرسال الفعلي المباشر لـ Google Drive، يرجى تزويد رمز المرور (Access Token) الخاص بحساب Google الخاص بك بالأسفل."
        });
      }, 1500);
      return;
    }

    setSavingProject(true);
    setStatusMsg(null);

    try {
      const res = await fetch(getApiUrl("/api/drive-upload"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ accessToken: accessToken.trim() })
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.error || res.statusText || "خطأ غير معروف في خوادم Google.");
      }

      const data = await res.json();
      setStatusMsg({
        type: "success",
        text: `🚀 تم حفظ وتخزين سورس كود للمشروع بالكامل بنجاح في Google Drive الخاص بك! معرف الملف: ${data.fileId}`
      });
    } catch (err: any) {
      console.error(err);
      setStatusMsg({
        type: "error",
        text: `فشل الرفع المباشر لـ Google Drive. تأكد من صلاحية token المُدخل: ${err.message}`
      });
    } finally {
      setSavingProject(false);
    }
  };

  // Save specific report to Google Drive
  const handleSaveReportToDrive = async () => {
    if (!lastScanResult) {
      setStatusMsg({ type: "error", text: "لا يوجد تقرير فحص نشط حالياً لحفظه!" });
      return;
    }

    const reportContent = `
=============================================
تقرير فحص كاشف الأجهزة وكاميرات التجسس - AI Vision Lite
=============================================
تاريخ الفحص: ${new Date(lastScanResult.scannedAt).toLocaleString("ar-SA")}
اسم العنصر المكشوف: ${lastScanResult.name}
الفئة والمصنف: ${lastScanResult.category}
الحجم المقدر: ${lastScanResult.size}
الوزن المقدر: ${lastScanResult.weight || "N/A"}
الشركة المصنعة / الماركة: ${lastScanResult.brand || "N/A"}
السعر المقدر للسلعة: ${lastScanResult.estimatedPrice || "N/A"}
رابط الشراء المقترح: ${lastScanResult.buyLink || "N/A"}
مستوى دقة الكشف (Confidence): %${lastScanResult.confidence}
حالة فحص وتأمين الكاميرا الخفية: ${lastScanResult.hideCameraStatus}

المكونات الفرعية والمجسات المرصودة:
${lastScanResult.toolsFound.map((t, idx) => ` - [${idx + 1}] ${t}`).join("\n")}

تفاصيل وخصائص فنية تفصيلية:
${lastScanResult.extraDetails.map(d => ` - ${d.key}: ${d.value}`).join("\n")}

الترجمة والوصف العربي الشامل:
${lastScanResult.translationResult?.translatedText || "غير متوفر"}

---------------------------------------------
جميع الحقوق محفوظة - نظام الفحص السحابي ذو الحماية العالية
---------------------------------------------
`;

    if (!accessToken.trim()) {
      // Simulate save and trigger manual local download
      setSavingReport(true);
      setTimeout(() => {
        setSavingReport(false);
        const blob = new Blob([reportContent], { type: "text/plain;charset=utf-8" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `spec_report_${lastScanResult.id}.txt`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        setStatusMsg({
          type: "success",
          text: "🎉 [طريقة المحاكاة الاحتياطية]: تم تجميع تقرير الفحص الفني وتحميله كملف نصي بنجاح! للإرسال التلقائي لحسابك في Google Drive، يرجى ملء رمز OAuth بالأسفل."
        });
      }, 1000);
      return;
    }

    setSavingReport(true);
    setStatusMsg(null);

    try {
      const res = await fetch(getApiUrl("/api/drive-upload-report"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          accessToken: accessToken.trim(),
          reportData: reportContent,
          fileName: `ai_vision_report_${lastScanResult.id}.txt`
        })
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.error || res.statusText || "خطأ غير معروف في خوادم Google.");
      }

      const data = await res.json();
      setStatusMsg({
        type: "success",
        text: `📄 تم بنجاح رفع وحفظ تقرير المسح الفني لـ [${lastScanResult.name}] في Google Drive الخاص بك! معرف الحفظ: ${data.fileId}`
      });
    } catch (err: any) {
      console.error(err);
      setStatusMsg({
        type: "error",
        text: `فشل رفع التقرير لـ Google Drive: ${err.message}`
      });
    } finally {
      setSavingReport(false);
    }
  };

  const handleCopyGitCommands = () => {
    const commands = `git init\ngit add .\ngit commit -m "Initialize AI Vision Lite Project"\ngit branch -M main\ngit remote add origin <رابط_مستودع_github_الخاص_بك>\ngit push -u origin main`;
    navigator.clipboard.writeText(commands);
    setCopiedText(true);
    setTimeout(() => setCopiedText(false), 2000);
  };

  return (
    <div className="w-full bg-slate-900 border border-slate-800 rounded-2xl p-4 md:p-5 flex flex-col gap-4 shadow-xl">
      {/* Title block */}
      <div className="flex items-center gap-2 border-b border-slate-800 pb-3 justify-between">
        <div className="flex items-center gap-2">
          <Cloud className="w-5 h-5 text-emerald-400 animate-pulse" />
          <div>
            <h3 className="font-extrabold text-sm text-slate-105">
              بوابة الحفظ المباشر قوقل درايف وقيثب [CLOUD BACKUP & GITHUB]
            </h3>
            <p className="text-[10px] text-slate-400 font-mono">
              SECURE WORKSPACE SOURCE CONTROL & CLOUD ARCHIVE
            </p>
          </div>
        </div>
        <span className="text-[9px] bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 px-2 py-0.5 rounded font-bold uppercase">
          Cloud-ready
        </span>
      </div>

      {/* Tabs */}
      <div className="grid grid-cols-2 bg-slate-950 p-1 rounded-lg border border-slate-850" dir="rtl">
        <button
          onClick={() => { setActiveTab("drive"); setStatusMsg(null); }}
          className={`flex items-center justify-center gap-2 py-2 text-xs font-bold rounded-md transition ${
            activeTab === "drive"
              ? "bg-emerald-600 text-slate-950 shadow"
              : "text-slate-400 hover:text-slate-200"
          }`}
        >
          <Cloud className="w-4 h-4" />
          <span>مزامنة قوقل درايف (Google Drive)</span>
        </button>

        <button
          onClick={() => { setActiveTab("github"); setStatusMsg(null); }}
          className={`flex items-center justify-center gap-2 py-2 text-xs font-bold rounded-md transition ${
            activeTab === "github"
              ? "bg-emerald-600 text-slate-950 shadow"
              : "text-slate-400 hover:text-slate-200"
          }`}
        >
          <Github className="w-4 h-4" />
          <span>تصدير إلى قيثب (GitHub)</span>
        </button>
      </div>

      {/* Output notifications */}
      {statusMsg && (
        <div 
          className={`p-3 rounded-xl flex items-start gap-2.5 text-xs font-mono leading-relaxed transition ${
            statusMsg.type === "success"
              ? "bg-emerald-950/20 border border-emerald-500/35 text-emerald-300"
              : "bg-red-950/20 border border-red-500/35 text-red-300"
          }`} 
          dir="rtl"
        >
          {statusMsg.type === "success" ? (
            <CheckCircle className="w-4 h-4 text-emerald-400 mt-0.5 flex-shrink-0" />
          ) : (
            <AlertTriangle className="w-4 h-4 text-red-400 mt-0.5 flex-shrink-0" />
          )}
          <div>
            <p className="font-bold">{statusMsg.type === "success" ? "تمت العملية بنجاح" : "تنبيه خطأ في النظام"}</p>
            <p className="text-[11px] mt-1 text-slate-300">{statusMsg.text}</p>
          </div>
        </div>
      )}

      {/* TAB CONTENT: Google Drive */}
      {activeTab === "drive" && (
        <div className="flex flex-col gap-3.5" dir="rtl">
          <div className="text-xs text-slate-300 leading-relaxed text-right">
            <p>
              بصفتك مستخدمًا مصرحًا بـ <strong>Google Drive Integration</strong>، يمكنك مزامنة كامل الكود المصدري للمشروع، أو حفظ تفاصيل فحص الكاميرات الخفيفة الأخير وتخزينه كملف نصي مؤرشف للرجوع إليه بسلاسة في أي مكان.
            </p>
          </div>

          {/* Access Token Input Block */}
          <div className="flex flex-col gap-1.5 p-3 rounded-xl bg-slate-950 border border-slate-850">
            <div className="flex justify-between items-center">
              <span className="text-[11px] text-slate-400 font-bold">رمز ممر OAuth (Google Active Access Token)</span>
              <a 
                href="https://developers.google.com/oauthplayground" 
                target="_blank" 
                rel="no-referrer"
                className="text-[9px] text-emerald-400 hover:underline flex items-center gap-1 font-mono"
              >
                <span>OAuth Playground</span>
                <ExternalLink className="w-2.5 h-2.5" />
              </a>
            </div>
            
            <input
              type="password"
              value={accessToken}
              onChange={handleTokenChange}
              placeholder="تبدأ بـ ya29... (اختياري - اترك فارغاً للتجربة والمحاكاة)"
              className="bg-slate-900 border border-slate-800 text-slate-100 rounded-lg p-2 text-xs font-mono placeholder-slate-600 focus:border-emerald-500/50 outline-none transition text-left"
            />
            <p className="text-[9px] text-slate-500 font-mono">
              * في حالة الرفع الفعلي المباشر، تأكد من صلاحيات النطاق <code className="text-slate-300">drive.file</code> أو <code className="text-slate-300">drive</code>. إذا لم يكن متوفرًا، نظام المحاكاة السحابية سيبدأ فورًا في تجهيز وتنزيل الملفات محليًا مع تعليق الرفع بشكل آمن!
            </p>
          </div>

          {/* Actions */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <button
              onClick={handleSaveReportToDrive}
              disabled={savingReport}
              className="w-full bg-slate-800 hover:bg-slate-700 disabled:opacity-50 text-slate-100 font-black py-2.5 px-4 rounded-xl text-xs border border-slate-705 transition duration-200 flex items-center justify-center gap-2 active:scale-95 cursor-pointer"
            >
              <RefreshCw className={`w-4 h-4 text-emerald-400 ${savingReport ? "animate-spin" : ""}`} />
              <span>حفظ تقرير الفحص الأخير في Drive</span>
            </button>

            <button
              onClick={handleBackupToDrive}
              disabled={savingProject}
              className="w-full bg-emerald-500 hover:bg-emerald-400 disabled:opacity-50 text-slate-950 font-black py-2.5 px-4 rounded-xl text-xs transition duration-200 flex items-center justify-center gap-2 active:scale-95 cursor-pointer"
            >
              <RefreshCw className={`w-4 h-4 text-slate-950 ${savingProject ? "animate-spin" : ""}`} />
              <span>حفظ وأرشفة كامل المشروع في Drive</span>
            </button>
          </div>
        </div>
      )}

      {/* TAB CONTENT: GitHub */}
      {activeTab === "github" && (
        <div className="flex flex-col gap-3.5" dir="rtl">
          <div className="text-xs text-slate-305 leading-relaxed text-right space-y-2">
            <p>
              لتخزين وحفظ المشروع البرمجي للـ <strong>AI Vision Lite</strong> في مستودعك الخاص بـ <strong>GitHub (قيثب)</strong>:
            </p>
            <p className="text-[11px] text-slate-450">
              قمنا بتطوير حل فوري لتجميع وبناء ملف الـ ZIP التقني الذي يعزل الوحدات الضخمة. يمكنك ببساطة تنزيله كملف مضغوط، ثم رفعه كإصدار مستقر على GitHub في دقائق معدودة!
            </p>
          </div>

          {/* Guide boxes */}
          <div className="bg-slate-950 border border-slate-850 p-3 rounded-xl space-y-2.5">
            <div className="flex justify-between items-center text-[10px] font-mono border-b border-slate-850 pb-1.5 text-slate-400">
              <span>أوامر التثبيت الفوري ومزامنة قيثب [GITHUB ACTIONS]</span>
              <button 
                onClick={handleCopyGitCommands}
                className="hover:text-emerald-400 flex items-center gap-1"
                title="نسخ الأوامر"
              >
                <Copy className="w-3 h-3" />
                <span>{copiedText ? "تم النسخ!" : "نسخ الأوامر"}</span>
              </button>
            </div>

            <div className="font-mono text-[9px] text-emerald-400 leading-relaxed space-y-1 text-left">
              <p>1. قم بفك ضغط الملف المنزّل وافتح مجلد المشروع.</p>
              <p>2. افتح سطر الأوامر (Terminal) ونفذ الآتي:</p>
              <p className="text-slate-300">git init</p>
              <p className="text-slate-300">git add .</p>
              <p className="text-slate-300">git commit -m "feat: setup AI Vision scanner with Gemini fallback"</p>
              <p className="text-slate-300">git branch -M main</p>
              <p className="text-slate-300">git remote add origin https://github.com/USERNAME/REPOSITORY.git</p>
              <p className="text-slate-300">git push -u origin main</p>
            </div>
          </div>

          {/* Button Trigger */}
          <button
            onClick={handleDownloadZip}
            className="w-full bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-black py-2.5 px-4 rounded-xl text-xs transition duration-200 flex items-center justify-center gap-2 active:scale-95 cursor-pointer shadow shadow-emerald-500/20"
          >
            <Download className="w-4 h-4" />
            <span>تنزيل ملف سورس كود ZIP لرفع المشروع في قيثب</span>
          </button>
        </div>
      )}
    </div>
  );
}
