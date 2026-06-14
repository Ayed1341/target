/**
 * App Root - 5G Router Manager
 * Developer: عايد عريبي (Ayed Oraybi)
 */

import React, { useState, useEffect } from "react";
import RouterManager from "./components/RouterManager";
import { Shield, Clock, Wifi, Award, Terminal } from "lucide-react";

export default function App() {
  const [currentTime, setCurrentTime] = useState("");

  useEffect(() => {
    const update = () =>
      setCurrentTime(
        new Date().toLocaleTimeString("ar-EG", {
          hour: "2-digit",
          minute: "2-digit",
          second: "2-digit",
        })
      );
    update();
    const t = setInterval(update, 1000);
    return () => clearInterval(t);
  }, []);

  return (
    <div className="w-full min-h-screen bg-slate-950 text-slate-100 antialiased font-sans flex flex-col">
      {/* Header */}
      <header className="w-full bg-slate-900/80 border-b border-slate-800/85 backdrop-blur-md px-4 py-3 md:px-8 z-20">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-3" dir="rtl">
          <div className="flex items-center gap-3">
            <div className="relative">
              <div className="absolute inset-0 bg-emerald-500/20 rounded-lg blur-md animate-pulse" />
              <div className="relative border border-emerald-500/30 bg-slate-950 text-emerald-400 p-2 rounded-lg">
                <Wifi className="w-5 h-5 animate-pulse" />
              </div>
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-sm md:text-base font-black tracking-tight text-slate-100">
                  منظومة عايد عريبي لإدارة راوترات الجيل الخامس 5G
                </h1>
                <span className="text-[9px] bg-emerald-500/15 border border-emerald-500/30 text-emerald-400 px-2 py-0.5 rounded font-bold uppercase">
                  v8.0 Active
                </span>
              </div>
              <p className="text-[11px] text-slate-400 font-medium mt-0.5">
                تطوير المهندس:{" "}
                <span className="text-emerald-400 font-bold">عايد عريبي (Ayed Oraybi)</span>
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 font-mono text-xs">
            <div className="flex items-center gap-1.5 bg-slate-950/80 border border-slate-800 px-2.5 py-1.5 rounded-lg text-slate-300">
              <Clock className="w-3 h-3 text-emerald-400" />
              <span>{currentTime || "--:--:--"}</span>
            </div>
            <div className="hidden md:flex items-center gap-1.5 bg-slate-950/80 border border-slate-800 px-2.5 py-1.5 rounded-lg">
              <Shield className="w-3 h-3 text-emerald-400" />
              <span className="text-emerald-400 font-bold text-[11px]">آمن 100%</span>
            </div>
            <div className="flex items-center gap-1.5 bg-emerald-500/10 border border-emerald-500/20 px-2.5 py-1.5 rounded-lg text-emerald-400 font-sans font-bold text-[11px]">
              <Award className="w-3 h-3" />
              <span>عايد عريبي</span>
            </div>
          </div>
        </div>
      </header>

      {/* Main */}
      <main className="flex-1 w-full max-w-7xl mx-auto p-3 md:p-5 flex flex-col gap-4 z-10">
        <section
          className="bg-slate-900/40 border border-slate-800/60 p-4 rounded-2xl flex flex-col md:flex-row items-start justify-between gap-4"
          dir="rtl"
        >
          <div className="flex items-start gap-3">
            <div className="p-2 bg-gradient-to-br from-indigo-500/10 to-emerald-500/10 border border-slate-800 rounded-xl mt-0.5 hidden sm:block">
              <Terminal className="w-5 h-5 text-emerald-400" />
            </div>
            <div>
              <h3 className="text-sm font-black text-slate-200">
                مركز التحكم الاحترافي في ترددات 4G/5G وإدارة الشبكة
              </h3>
              <p className="text-xs text-slate-400 mt-1 leading-relaxed max-w-3xl">
                منظومة متكاملة للتحكم الكامل في راوترات Huawei وZTE. تشمل: ماسح الترددات الحي،
                قفل الأبراج، مراقبة الإشارة RSRP/RSRQ/SINR، اختبار السرعة، تصدير التشخيص،
                و17 طريقة مصادقة متقدمة بدون أي محاكاة أو بيانات وهمية.
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2 bg-slate-950 px-3 py-2 rounded-xl border border-slate-800 shrink-0">
            <Wifi className="w-4 h-4 text-emerald-400" />
            <span className="text-[11px] text-slate-300 font-bold">Real API Only</span>
          </div>
        </section>

        <RouterManager />
      </main>

      {/* Footer */}
      <footer className="w-full bg-slate-950 border-t border-slate-900 py-4 px-4 z-20">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-2 text-xs text-slate-500">
          <p dir="rtl">
            حقوق التطوير محفوظة © 2026 للمهندس:{" "}
            <strong className="text-slate-300">عايد عريبي (Ayed Oraybi)</strong>
          </p>
          <div className="flex items-center gap-3 text-[11px]">
            <span className="text-slate-600">بيانات حقيقية 100% — لا محاكاة</span>
            <span className="text-emerald-400 font-bold">Router Manager v8.0</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
