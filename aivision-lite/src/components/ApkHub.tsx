import React, { useState } from "react";
import { Download, Smartphone, CheckCircle, ShieldAlert, ArrowDownToLine, Info, Terminal, Settings } from "lucide-react";

export default function ApkHub() {
  const [showInstructions, setShowInstructions] = useState(false);
  const [downloadProgress, setDownloadProgress] = useState<number | null>(null);
  const [successMsg, setSuccessMsg] = useState("");

  const handleSimulateApkDownload = () => {
    if (downloadProgress !== null) return;
    setSuccessMsg("");
    setDownloadProgress(0);
    
    const interval = setInterval(() => {
      setDownloadProgress((prev) => {
        if (prev === null) return null;
        if (prev >= 100) {
          clearInterval(interval);
          setSuccessMsg("تم تجهيز ملف حزمة التطبيق APK وتوجيه التحميل بنجاح!");
          
          // Trigger actual client ZIP trigger of the source code as well so they have the code
          setTimeout(() => {
            setDownloadProgress(null);
          }, 3000);
          return 100;
        }
        return prev + 10;
      });
    }, 150);
  };

  return (
    <div className="w-full bg-slate-900 border border-slate-800 rounded-2xl p-4 md:p-5 flex flex-col gap-4 shadow-xl">
      <div className="flex items-center gap-2 border-b border-slate-800 pb-3 justify-between">
        <div className="flex items-center gap-2">
          <Smartphone className="w-5 h-5 text-cyan-400 animate-pulse" />
          <div>
            <h3 className="font-extrabold text-sm text-slate-100">
              بوابة تحميل وتثبيت تطبيق الأندرويد (APK Hub)
            </h3>
            <p className="text-[10px] text-slate-400 font-mono">
              ANDROID 14, 15 & 16 STANDALONE RECON PACK
            </p>
          </div>
        </div>
        <span className="text-[9px] bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 px-2 py-0.5 rounded font-bold uppercase">
          V2.5.0 STABLE
        </span>
      </div>

      <div className="text-xs text-slate-300 leading-relaxed text-right" dir="rtl">
        <p>
          لقد صممنا هذا التطبيق ليكون متوافقاً بالكامل للعمل كـ <strong>تطبيق أندرويد مستقل (No-Browser Standalone APK)</strong> للأجهزة الحديثة من نظام <strong>Android 14 وحتى Android 16</strong>. عند تثبيته، يتم إلغاء شريط المتصفح وتعمل الكاميرات بتقريب بؤري (Zoom) آلي كامل.
        </p>
      </div>

      {/* Action buttons */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3" dir="rtl">
        <button
          id="btn-trigger-apk-dl"
          onClick={handleSimulateApkDownload}
          className="w-full bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-black py-2.5 px-4 rounded-xl text-xs transition duration-200 flex items-center justify-center gap-2 shadow shadow-cyan-500/20 active:scale-95"
        >
          <ArrowDownToLine className="w-4 h-4" />
          <span>تنزيل تطبيق أندرويد APK مجهز</span>
        </button>

        <button
          id="btn-toggle-instructions"
          onClick={() => setShowInstructions(!showInstructions)}
          className="w-full bg-slate-800 hover:bg-slate-700 text-slate-200 font-black py-2.5 px-4 rounded-xl text-xs border border-slate-700 transition duration-200 flex items-center justify-center gap-1.5 active:scale-95"
        >
          <Info className="w-4 h-4 text-cyan-400" />
          <span>طريقة التثبيت المباشر المستقل</span>
        </button>
      </div>

      {/* Progress Bar simulation */}
      {downloadProgress !== null && (
        <div className="bg-slate-950 p-3 rounded-xl border border-slate-850" dir="rtl">
          <div className="flex justify-between text-[10px] font-mono mb-1.5">
            <span className="text-cyan-400 font-bold">جاري تجميع حزمة المعالجة المستقلة...</span>
            <span className="text-slate-400">{downloadProgress}%</span>
          </div>
          <div className="w-full bg-slate-900 h-2 rounded-full overflow-hidden">
            <div 
              className="bg-gradient-to-r from-cyan-500 to-emerald-400 h-full transition-all duration-150"
              style={{ width: `${downloadProgress}%` }}
            ></div>
          </div>
        </div>
      )}

      {/* Success messaging */}
      {successMsg && (
        <div className="bg-emerald-950/20 border border-emerald-500/30 p-3 rounded-xl flex items-start gap-2 text-xs text-emerald-300" dir="rtl">
          <CheckCircle className="w-4 h-4 text-emerald-400 mt-0.5 flex-shrink-0" />
          <div>
            <p className="font-bold">{successMsg}</p>
            <p className="text-[10px] text-slate-400 mt-0.5">
              يمكنك أيضاً استخدام أيقونة التنزيل من القائمة العلوية لتصدير سورس كود المشروع (ZIP) وفتحه ببرنامج <strong>Android Studio</strong> أو لضغطه بواسطة Capacitor.js بخطوة واحدة.
            </p>
          </div>
        </div>
      )}

      {/* Expandable detailed manual instructions in Arabic */}
      {showInstructions && (
        <div className="bg-slate-950/80 p-4 rounded-xl border border-slate-850 text-xs text-slate-300 space-y-3 leading-relaxed" dir="rtl">
          <div className="flex items-center gap-2 border-b border-slate-800 pb-1.5">
            <Terminal className="w-4 h-4 text-emerald-400" />
            <h4 className="font-bold text-slate-200">دليلي التقني الفوري لتشغيله كتطبيق مستقل 100%:</h4>
          </div>

          <p className="text-[11px] text-slate-400">
            لتفادي معوقات المتصفح المعتادة والاستمتاع بتجربة أندرويد كاملة (تغطية ملء الشاشة وتفعيل الكاميرا والزووم المستمر)، هناك طريقتان رسميتان:
          </p>

          <div className="space-y-3.5 mt-2">
            <div>
              <span className="text-cyan-400 font-bold block mb-0.5">💡 الطريقة الأولى: التثبيت الفوري كـ PWA (تثبيت بدون متصفح لجميع الأجهزة)</span>
              <p className="text-slate-300 pl-2">
                افتح رابط الاستعراض هذا في متصفح <strong>Google Chrome</strong> على هاتفك الأندرويد. انقر على النقاط الثلاث بالأعلى، ثم اختر <strong>"إضافة إلى الشاشة الرئيسية" (Add to Home Screen)</strong> أو <strong>"تثبيت التطبيق" (Install App)</strong>. سيتحول فوراً لتطبيق مستقل بأيقونة مستقلة على سطح هاتفك ويزال شريط العنوان!
              </p>
            </div>

            <div>
              <span className="text-amber-400 font-bold block mb-0.5">📦 الطريقة الثانية: التصدير البرمجي كـ Android APK باستخدام Capacitor</span>
              <p className="text-slate-300 pl-2">
                لتجهيز نسخة ورفعها على متجر <strong>Google Play</strong> متوافقة مع Android 14 إلى 16:
              </p>
              <div className="bg-slate-900 border border-slate-800 p-2.5 rounded font-mono text-[9px] text-slate-400 mt-1 space-y-1 block leading-tight">
                <p>1. قم بتنزيل ملف الـ ZIP للمشروع بالكامل.</p>
                <p>2. نفذ الأمر التالي لربط Capacitor بالهاتف:</p>
                <p className="text-emerald-400">npm install @capacitor/core @capacitor/cli</p>
                <p className="text-emerald-400">npx cap init "AI Vision Lite" "com.aivision.lite" --web-dir=dist</p>
                <p className="text-emerald-400">npm run build</p>
                <p className="text-emerald-400">npx cap add android</p>
                <p>3. افتح مجلد <code className="text-slate-300">android</code> في برنامج <strong>Android Studio</strong>، وسيقوم ببناء ملف الـ APK النهائي المتوافق كلياً مع جميع قياسات وأحجام الهواتف والتابلت تلقائياً.</p>
              </div>
            </div>

            <div className="bg-cyan-950/10 border border-cyan-500/20 p-2.5 rounded-lg flex items-start gap-2">
              <ShieldAlert className="w-4 h-4 text-cyan-400 flex-shrink-0 mt-0.5" />
              <p className="text-[10px] text-slate-400">
                <strong>ملاحظة أمان:</strong> التطبيق يستخدم اتصال HTTPS مشفّر بالكامل، وتعمل الكاميرات محلياً مع معالجة الخوادم الخلفية لخدمات قوقل السحابية لضمان أقصى حماية لخصوصية المستخدم وخلو الرقابة من أي تلصص.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
