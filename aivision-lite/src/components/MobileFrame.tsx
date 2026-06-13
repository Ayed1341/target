import React from "react";

interface MobileFrameProps {
  children: React.ReactNode;
  isApkMode: boolean;
  setIsApkMode: (mode: boolean) => void;
}

export default function MobileFrame({ children }: MobileFrameProps) {
  return (
    <div className="w-full h-full flex flex-col bg-slate-950 text-slate-100 min-h-screen antialiased">
      {/* Premium Core Header Banner */}
      <div id="web-top-control" className="w-full bg-slate-900/90 border-b border-slate-800 py-3.5 px-4 md:px-6 flex flex-wrap gap-3 justify-between items-center z-20">
        <div className="flex items-center gap-2.5">
          <span className="bg-emerald-500/10 text-emerald-400 font-mono text-xs px-2.5 py-1 rounded-full border border-emerald-500/20 animate-pulse flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
            نطاق المعالجة المباشر: آمن
          </span>
          <h1 className="text-base md:text-lg font-black tracking-tight bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent">
            AI VISION LITE SCANNER
          </h1>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-[10px] bg-slate-800 text-slate-400 border border-slate-700 px-2 py-1 rounded font-bold uppercase">
            WEBSITE ULTRA MODE
          </span>
        </div>
      </div>
      
      {/* Standard Full Responsive View Container */}
      <div className="flex-1 w-full max-w-7xl mx-auto flex flex-col p-4 md:p-6 transition-all duration-300">
        {children}
      </div>
    </div>
  );
}
