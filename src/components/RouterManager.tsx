/**
 * Router Manager - Advanced 5G/LTE Router Control Panel
 * All features: Band Scanner, Cell Scanner, Signal Monitor, Speed Test, Export Diagnostics & more
 * Developer: عايد عريبي (Ayed Oraybi)
 */

import React, { useState, useEffect, useCallback, useRef } from "react";
import {
  Router, Radio, Signal, Cpu, Zap, RotateCw, Lock,
  TrendingUp, Activity, Wifi, Database, Smartphone,
  Share2, Key, Terminal, Settings, Shield, Play,
  Globe, AlertTriangle, SlidersHorizontal, Clock,
  CheckCircle, Gauge, Award, Download, Copy, RefreshCw,
  Layers, Info, Server, Filter, Search, ArrowRightLeft,
  Satellite, BarChart2, Map, FileText, WifiOff, Antenna,
  ChevronDown, ChevronUp, XCircle, Sliders,
} from "lucide-react";
import { useRouterConnection } from "../hooks/useRouterConnection";
import { STANDARD_LTE_BANDS, STANDARD_NR_BANDS, earfcnToFreqMHz } from "../api/routerApi";
import { AppTab, BandInfo, CellTower, SignalHistoryEntry, SpeedTestResult } from "../types";

// ─── Signal quality helpers ──────────────────────────────────────────────────
function rsrpQuality(v: number): { label: string; color: string } {
  if (v >= -80)  return { label: "ممتاز",  color: "text-emerald-400" };
  if (v >= -90)  return { label: "جيد جداً", color: "text-green-400" };
  if (v >= -100) return { label: "مقبول",   color: "text-yellow-400" };
  if (v >= -110) return { label: "ضعيف",    color: "text-orange-400" };
  return            { label: "سيء",      color: "text-red-400" };
}

function sinrQuality(v: number): { label: string; color: string } {
  if (v >= 20) return { label: "ممتاز",  color: "text-emerald-400" };
  if (v >= 13) return { label: "جيد جداً", color: "text-green-400" };
  if (v >= 0)  return { label: "مقبول",   color: "text-yellow-400" };
  return          { label: "ضعيف",    color: "text-red-400" };
}

function rsrqQuality(v: number): { label: string; color: string } {
  if (v >= -10) return { label: "ممتاز",  color: "text-emerald-400" };
  if (v >= -15) return { label: "جيد",    color: "text-green-400" };
  if (v >= -20) return { label: "مقبول",   color: "text-yellow-400" };
  return           { label: "ضعيف",    color: "text-red-400" };
}

function signalBarWidth(rsrp: number): number {
  return Math.max(5, Math.min(100, ((rsrp + 120) / 80) * 100));
}

// ─── Mini Sparkline SVG ──────────────────────────────────────────────────────
function Sparkline({ data, color = "#10b981" }: { data: number[]; color?: string }) {
  if (data.length < 2) return <div className="h-12 flex items-center justify-center text-slate-600 text-[10px]">جاري التسجيل...</div>;
  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;
  const W = 300, H = 48;
  const pts = data.map((v, i) => {
    const x = (i / (data.length - 1)) * W;
    const y = H - ((v - min) / range) * H * 0.9 - H * 0.05;
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  });
  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full h-12" preserveAspectRatio="none">
      <polyline
        points={pts.join(" ")}
        fill="none"
        stroke={color}
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

// ─── Tab Button ──────────────────────────────────────────────────────────────
function TabBtn({
  id, active, onClick, icon: Icon, label,
}: {
  id: string; active: boolean; onClick: (id: AppTab) => void; icon: any; label: string;
}) {
  return (
    <button
      onClick={() => onClick(id as AppTab)}
      className={`flex items-center gap-1.5 px-3 py-2 text-[11px] font-bold whitespace-nowrap transition-all rounded-t-lg ${
        active
          ? "bg-emerald-500/10 text-emerald-400 border-b-2 border-emerald-400"
          : "text-slate-400 hover:text-slate-300 hover:bg-slate-800/40"
      }`}
    >
      <Icon className="w-3.5 h-3.5" />
      {label}
    </button>
  );
}

// ─── Card wrapper ─────────────────────────────────────────────────────────────
function Card({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return (
    <div className={`bg-slate-950/70 border border-slate-800 rounded-xl p-4 ${className}`}>
      {children}
    </div>
  );
}

// ─── Metric Card ─────────────────────────────────────────────────────────────
function MetricCard({
  label, value, unit, quality, sub,
}: {
  label: string; value: string | number; unit?: string; quality?: { label: string; color: string }; sub?: string;
}) {
  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-3 flex flex-col gap-1">
      <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wide">{label}</span>
      <div className="flex items-end gap-1">
        <span className={`text-xl font-black ${quality?.color || "text-emerald-400"}`}>{value}</span>
        {unit && <span className="text-xs text-slate-500 mb-0.5">{unit}</span>}
      </div>
      {quality && <span className={`text-[10px] font-bold ${quality.color}`}>{quality.label}</span>}
      {sub && <span className="text-[10px] text-slate-500">{sub}</span>}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════
// MAIN COMPONENT
// ═══════════════════════════════════════════════════════════════════════════
export default function RouterManager() {
  const DEV_SIGN = "عايد عريبي";
  const DEV_SIGN_EN = "Ayed Oraybi";

  // ── Connection form state ──────────────────────────────────────────────────
  const [routerIp, setRouterIp] = useState(() => localStorage.getItem("rm_ip") || "192.168.8.1");
  const [routerUser, setRouterUser] = useState(() => localStorage.getItem("rm_user") || "admin");
  const [routerPass, setRouterPass] = useState(() => localStorage.getItem("rm_pass") || "");
  const [routerBrand, setRouterBrand] = useState<"huawei" | "zte">(() =>
    (localStorage.getItem("rm_brand") as "huawei" | "zte") || "huawei"
  );
  const [showPass, setShowPass] = useState(false);

  const conn = useRouterConnection();

  // ── UI state ───────────────────────────────────────────────────────────────
  const [activeTab, setActiveTab] = useState<AppTab>("dashboard");
  const [logs, setLogs] = useState<string[]>([]);
  const [copied, setCopied] = useState<string | null>(null);
  const [lockedBands, setLockedBands] = useState<Set<string>>(new Set());
  const [lockedCell, setLockedCell] = useState<CellTower | null>(null);
  const [isRunningSpeed, setIsRunningSpeed] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const [networkMode, setNetworkMode] = useState<"4g_only" | "5g_nsa" | "5g_sa" | "auto">("auto");
  const [antennaMode, setAntennaMode] = useState<"0" | "1" | "2">("2");
  const [bandFilter, setBandFilter] = useState<"all" | "LTE" | "NR">("all");
  const [isScanning, setIsScanning] = useState(false);
  const [expandedCell, setExpandedCell] = useState<string | null>(null);
  const logRef = useRef<HTMLDivElement>(null);

  const addLog = useCallback((msg: string) => {
    const time = new Date().toLocaleTimeString("ar-EG");
    setLogs((prev) => [...prev.slice(-99), `[${time}] ${msg}`]);
    setTimeout(() => {
      if (logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight;
    }, 50);
  }, []);

  // ── Persist credentials ────────────────────────────────────────────────────
  useEffect(() => {
    localStorage.setItem("rm_ip", routerIp);
    localStorage.setItem("rm_user", routerUser);
    localStorage.setItem("rm_brand", routerBrand);
  }, [routerIp, routerUser, routerBrand]);

  // ── Connect handler ────────────────────────────────────────────────────────
  const handleConnect = async (e: React.FormEvent) => {
    e.preventDefault();
    localStorage.setItem("rm_pass", routerPass);
    setLogs([]);
    addLog(`🔗 بدء الاتصال بالعنوان ${routerIp} (${routerBrand === "huawei" ? "Huawei" : "ZTE"})`);
    addLog("⚙️ تطبيق تقنيات المصادقة المتقدمة (17 طريقة)...");

    const ok = await conn.connect({ ip: routerIp, username: routerUser, password: routerPass, brand: routerBrand });

    if (ok) {
      addLog(`✅ تم الاتصال بنجاح! طريقة المصادقة: ${conn.authMethod}`);
      addLog(`📡 بيانات الإشارة: RSRP=${conn.signalData?.rsrp || "—"} dBm | SINR=${conn.signalData?.sinr || "—"} dB`);
    } else {
      addLog(`❌ فشل الاتصال: ${conn.error}`);
    }
  };

  const handleDisconnect = () => {
    conn.disconnect();
    addLog("🔌 تم قطع الاتصال");
  };

  // ── Band Lock ──────────────────────────────────────────────────────────────
  const handleLockBand = async (band: BandInfo) => {
    if (!conn.isConnected) { addLog("⚠️ اتصل بالراوتر أولاً"); return; }
    addLog(`🔒 جاري قفل النطاق ${band.name}...`);
    const ok = await conn.lockBand(band.hexCode, band.technology === "NR");
    if (ok) {
      setLockedBands((prev) => new Set([...prev, band.hexCode]));
      addLog(`✅ تم قفل النطاق ${band.name} بنجاح`);
    } else {
      addLog(`❌ فشل قفل النطاق ${band.name}`);
    }
  };

  const handleUnlockBand = async (band: BandInfo) => {
    if (!conn.isConnected) { addLog("⚠️ اتصل بالراوتر أولاً"); return; }
    addLog(`🔓 جاري إلغاء قفل ${band.name}...`);
    const ok = await conn.lockBand("3FFFFFFF", false);
    if (ok) {
      setLockedBands((prev) => { const s = new Set(prev); s.delete(band.hexCode); return s; });
      addLog(`✅ تم إلغاء القفل لـ ${band.name}`);
    }
  };

  // ── Cell Lock ─────────────────────────────────────────────────────────────
  const handleLockCell = async (cell: CellTower) => {
    if (!conn.isConnected) { addLog("⚠️ اتصل بالراوتر أولاً"); return; }
    addLog(`📌 جاري قفل البرج PCI=${cell.pci} EARFCN=${cell.earfcn}...`);
    const ok = await conn.lockCell(cell.pci, cell.earfcn);
    if (ok) {
      setLockedCell(cell);
      addLog(`✅ تم قفل البرج بنجاح: PCI ${cell.pci}`);
    } else {
      addLog(`❌ فشل قفل البرج PCI=${cell.pci}`);
    }
  };

  const handleUnlockCell = async () => {
    if (!conn.isConnected) { addLog("⚠️ اتصل بالراوتر أولاً"); return; }
    const ok = await conn.lockCell(0, 0);
    if (ok) {
      setLockedCell(null);
      addLog("✅ تم إلغاء قفل البرج - الراوتر يختار تلقائياً");
    }
  };

  // ── Cell Scan ─────────────────────────────────────────────────────────────
  const handleScanCells = async () => {
    if (!conn.isConnected) { addLog("⚠️ اتصل بالراوتر أولاً"); return; }
    setIsScanning(true);
    addLog("🔍 جاري مسح أبراج الاتصال المجاورة...");
    const ok = await conn.scanCellTowers();
    setIsScanning(false);
    if (ok) {
      addLog(`✅ تم العثور على ${conn.cellTowers.length} برج`);
    } else {
      addLog("⚠️ لم يتم العثور على أبراج مجاورة أو الراوتر لا يدعم هذه الميزة");
    }
  };

  // ── Network Mode ──────────────────────────────────────────────────────────
  const handleSetNetworkMode = async (mode: typeof networkMode) => {
    if (!conn.isConnected) { addLog("⚠️ اتصل بالراوتر أولاً"); return; }
    const labels = { "4g_only": "4G فقط", "5g_nsa": "5G NSA", "5g_sa": "5G SA", auto: "تلقائي" };
    addLog(`📶 تغيير وضع الشبكة إلى ${labels[mode]}...`);
    const ok = await conn.setNetworkMode(mode);
    if (ok) {
      setNetworkMode(mode);
      addLog(`✅ تم تغيير وضع الشبكة إلى ${labels[mode]}`);
    } else {
      addLog(`❌ فشل تغيير وضع الشبكة`);
    }
  };

  // ── Antenna ───────────────────────────────────────────────────────────────
  const handleSetAntenna = async (mode: "0" | "1" | "2") => {
    if (!conn.isConnected) { addLog("⚠️ اتصل بالراوتر أولاً"); return; }
    const labels = { "0": "داخلي", "1": "خارجي", "2": "هجين تلقائي" };
    addLog(`📡 تغيير وضع الهوائي إلى ${labels[mode]}...`);
    const ok = await conn.setAntennaMode(mode);
    if (ok) {
      setAntennaMode(mode);
      addLog(`✅ وضع الهوائي: ${labels[mode]}`);
    } else {
      addLog(`❌ فشل تغيير وضع الهوائي`);
    }
  };

  // ── Reboot ────────────────────────────────────────────────────────────────
  const handleReboot = async () => {
    if (!conn.isConnected) { addLog("⚠️ اتصل بالراوتر أولاً"); return; }
    addLog("🔄 إرسال أمر إعادة التشغيل...");
    const ok = await conn.reboot();
    if (ok) {
      addLog("✅ تم إرسال أمر إعادة التشغيل - الراوتر سيعيد التشغيل خلال ثوانٍ");
    } else {
      addLog("❌ فشل إرسال أمر إعادة التشغيل");
    }
  };

  // ── Speed Test ────────────────────────────────────────────────────────────
  const handleSpeedTest = async () => {
    if (!conn.isConnected) { addLog("⚠️ اتصل بالراوتر أولاً"); return; }
    setIsRunningSpeed(true);
    addLog("⚡ بدء اختبار السرعة...");
    const result = await conn.runSpeedTest();
    setIsRunningSpeed(false);
    if (result) {
      addLog(`✅ نتيجة اختبار السرعة: ↓${result.downloadMbps} Mbps | ↑${result.uploadMbps} Mbps | Ping: ${result.pingMs}ms`);
    } else {
      addLog("❌ فشل اختبار السرعة");
    }
  };

  // ── Best Band ────────────────────────────────────────────────────────────
  const handleFindBestBand = async () => {
    if (!conn.isConnected) { addLog("⚠️ اتصل بالراوتر أولاً"); return; }
    addLog("🔬 تحليل أفضل نطاق ترددي...");
    const best = await conn.findBestBand();
    if (best) {
      addLog(`🏆 أفضل نطاق متاح: ${best.name} (${best.dlFreqMHz} MHz) - كود: ${best.hexCode}`);
    } else {
      addLog("⚠️ لا يمكن تحديد أفضل نطاق حالياً");
    }
  };

  // ── Copy ──────────────────────────────────────────────────────────────────
  const copyText = (text: string, id: string) => {
    navigator.clipboard.writeText(text).catch(() => {});
    setCopied(id);
    setTimeout(() => setCopied(null), 2000);
  };

  // ── Export Diagnostics ────────────────────────────────────────────────────
  const handleExport = async () => {
    setIsExporting(true);
    addLog("📤 جاري تصدير بيانات التشخيص...");

    const report = {
      exportTime: new Date().toISOString(),
      developer: `${DEV_SIGN} (${DEV_SIGN_EN})`,
      routerInfo: { ip: routerIp, brand: routerBrand, authMethod: conn.authMethod },
      deviceInfo: conn.deviceInfo,
      signalData: conn.signalData,
      connectedDevices: conn.connectedDevices,
      cellTowers: conn.cellTowers,
      signalHistory: conn.signalHistory.slice(-30),
      lastSpeedTest: conn.lastSpeedTest,
      lockedBands: [...lockedBands],
      lockedCell,
      networkMode,
      antennaMode,
      logs: logs.slice(-50),
    };

    const json = JSON.stringify(report, null, 2);
    const blob = new Blob([json], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `router_diagnostics_${new Date().toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);

    setIsExporting(false);
    addLog("✅ تم تصدير ملف التشخيص بنجاح");
  };

  // ── Bands to display ──────────────────────────────────────────────────────
  const allBands = [...STANDARD_LTE_BANDS, ...STANDARD_NR_BANDS].map((b) => ({
    ...b,
    isLocked: lockedBands.has(b.hexCode),
    isActive: conn.signalData?.band === b.name || conn.supportedBands.some((sb) => sb.hexCode === b.hexCode && sb.isActive),
  }));
  const displayBands = bandFilter === "all" ? allBands : allBands.filter((b) => b.technology === bandFilter);

  const sig = conn.signalData;

  // ─────────────────────────────────────────────────────────────────────────
  return (
    <div className="w-full bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl flex flex-col gap-0 overflow-hidden" dir="rtl">

      {/* ── Header ── */}
      <div className="flex items-center justify-between px-5 py-4 border-b border-slate-800 bg-slate-950/80">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-emerald-500/10 border border-emerald-500/20 rounded-xl">
            <Router className="w-6 h-6 text-emerald-400" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-base font-black text-slate-100">
                منظومة إدارة الراوتر - {DEV_SIGN}
              </h2>
              <span className={`text-[9px] px-2 py-0.5 rounded-full font-bold border ${
                conn.isConnected
                  ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-400"
                  : "bg-red-500/10 border-red-500/30 text-red-400"
              }`}>
                {conn.isConnected ? "● متصل" : "○ غير متصل"}
              </span>
              {conn.isConnected && conn.signalData && (
                <span className="text-[9px] px-2 py-0.5 rounded-full font-bold border bg-blue-500/10 border-blue-500/20 text-blue-400">
                  {conn.signalData.networkType} | {conn.signalData.band}
                </span>
              )}
            </div>
            <p className="text-[11px] text-slate-400 mt-0.5">
              تطوير: <span className="text-emerald-400 font-bold">{DEV_SIGN} ({DEV_SIGN_EN})</span>
            </p>
          </div>
        </div>
        <div className="hidden md:flex items-center gap-2">
          <span className="text-[9px] bg-slate-900 border border-slate-800 text-slate-400 px-2.5 py-1 rounded-md font-mono">
            v8.0 BUILD
          </span>
          <span className="text-[9px] bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 px-2.5 py-1 rounded-md font-mono font-bold">
            17 AUTH LAYERS
          </span>
        </div>
      </div>

      {/* ── Connection Panel ── */}
      <div className="bg-slate-950/60 border-b border-slate-800 p-4 md:p-5">
        <form onSubmit={handleConnect} className="flex flex-col gap-3">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <div className="flex flex-col gap-1">
              <label className="text-[10px] font-bold text-slate-400 uppercase">عنوان IP</label>
              <input
                type="text"
                value={routerIp}
                onChange={(e) => setRouterIp(e.target.value)}
                className="bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-emerald-500 placeholder:text-slate-600"
                placeholder="192.168.8.1"
              />
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-[10px] font-bold text-slate-400 uppercase">المستخدم</label>
              <input
                type="text"
                value={routerUser}
                onChange={(e) => setRouterUser(e.target.value)}
                className="bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-emerald-500"
                placeholder="admin"
              />
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-[10px] font-bold text-slate-400 uppercase">كلمة المرور</label>
              <div className="relative">
                <input
                  type={showPass ? "text" : "password"}
                  value={routerPass}
                  onChange={(e) => setRouterPass(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-emerald-500 pr-8"
                  placeholder="••••••••"
                />
                <button
                  type="button"
                  onClick={() => setShowPass((v) => !v)}
                  className="absolute left-2 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300"
                >
                  <Key className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-[10px] font-bold text-slate-400 uppercase">نوع الراوتر</label>
              <select
                value={routerBrand}
                onChange={(e) => setRouterBrand(e.target.value as "huawei" | "zte")}
                className="bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-emerald-500"
              >
                <option value="huawei">Huawei</option>
                <option value="zte">ZTE</option>
              </select>
            </div>
          </div>
          <div className="flex gap-2">
            <button
              type="submit"
              disabled={conn.isLoading}
              className="flex-1 bg-emerald-600 hover:bg-emerald-700 disabled:bg-slate-700 text-white font-bold py-2 px-4 rounded-lg transition-all text-sm flex items-center justify-center gap-2"
            >
              {conn.isLoading ? (
                <><RefreshCw className="w-4 h-4 animate-spin" /> جاري الاتصال...</>
              ) : (
                <><Wifi className="w-4 h-4" /> اتصال ومصادقة</>
              )}
            </button>
            {conn.isConnected && (
              <button
                type="button"
                onClick={handleDisconnect}
                className="bg-red-900/50 hover:bg-red-900 border border-red-800 text-red-400 font-bold py-2 px-4 rounded-lg transition-all text-sm flex items-center gap-2"
              >
                <WifiOff className="w-4 h-4" />
                قطع
              </button>
            )}
            <button
              type="button"
              onClick={() => { setRouterIp("192.168.8.1"); setRouterUser("admin"); setRouterBrand("huawei"); }}
              className="bg-slate-800 hover:bg-slate-700 text-slate-300 font-bold py-2 px-3 rounded-lg transition-all text-xs"
            >
              افتراضي
            </button>
          </div>
          {conn.error && (
            <div className="flex items-center gap-2 bg-red-950/40 border border-red-900 text-red-400 p-3 rounded-lg text-xs">
              <XCircle className="w-4 h-4 flex-shrink-0" />
              {conn.error}
            </div>
          )}
        </form>
      </div>

      {/* ── Quick Signal Bar ── */}
      {sig && (
        <div className="grid grid-cols-2 md:grid-cols-6 gap-0 border-b border-slate-800">
          {[
            { label: "RSRP", value: sig.rsrp, unit: "dBm", q: rsrpQuality(sig.rsrp) },
            { label: "RSRQ", value: sig.rsrq, unit: "dB",  q: rsrqQuality(sig.rsrq) },
            { label: "SINR", value: sig.sinr, unit: "dB",  q: sinrQuality(sig.sinr) },
            { label: "Band", value: sig.band, unit: "",    q: { label: sig.networkType, color: "text-blue-400" } },
            { label: "Cell ID", value: sig.cellId || "—", unit: "", q: { label: `PCI: ${sig.pci}`, color: "text-slate-400" } },
            { label: "Temp", value: sig.temperature, unit: "°C", q: { label: sig.temperature > 60 ? "حار!" : "طبيعي", color: sig.temperature > 60 ? "text-orange-400" : "text-emerald-400" } },
          ].map((m, i) => (
            <div key={i} className="flex flex-col px-3 py-2 border-l border-slate-800 last:border-0">
              <span className="text-[9px] text-slate-500 font-bold uppercase">{m.label}</span>
              <span className={`text-sm font-black ${m.q.color}`}>{m.value}{m.unit}</span>
              <span className={`text-[9px] font-bold ${m.q.color}`}>{m.q.label}</span>
            </div>
          ))}
        </div>
      )}

      {/* ── Tabs ── */}
      <div className="flex gap-0 border-b border-slate-800 bg-slate-950/50 overflow-x-auto">
        <TabBtn id="dashboard" active={activeTab === "dashboard"} onClick={setActiveTab} icon={Gauge}      label="لوحة التحكم" />
        <TabBtn id="bands"     active={activeTab === "bands"}     onClick={setActiveTab} icon={Radio}      label="الترددات" />
        <TabBtn id="cells"     active={activeTab === "cells"}     onClick={setActiveTab} icon={Satellite}  label="الأبراج" />
        <TabBtn id="signal"    active={activeTab === "signal"}    onClick={setActiveTab} icon={Signal}     label="الإشارة" />
        <TabBtn id="network"   active={activeTab === "network"}   onClick={setActiveTab} icon={Globe}      label="الشبكة" />
        <TabBtn id="devices"   active={activeTab === "devices"}   onClick={setActiveTab} icon={Smartphone} label="الأجهزة" />
        <TabBtn id="speed"     active={activeTab === "speed"}     onClick={setActiveTab} icon={Zap}        label="السرعة" />
        <TabBtn id="history"   active={activeTab === "history"}   onClick={setActiveTab} icon={BarChart2}  label="السجل" />
        <TabBtn id="export"    active={activeTab === "export"}    onClick={setActiveTab} icon={Download}   label="تصدير" />
        <TabBtn id="commands"  active={activeTab === "commands"}  onClick={setActiveTab} icon={Terminal}   label="أوامر" />
      </div>

      {/* ── Tab content ── */}
      <div className="p-4 md:p-5 min-h-72">

        {/* ════ DASHBOARD ════ */}
        {activeTab === "dashboard" && (
          <div className="flex flex-col gap-4">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <MetricCard label="RSRP" value={sig?.rsrp ?? "—"} unit="dBm" quality={sig ? rsrpQuality(sig.rsrp) : undefined} sub="قوة الإشارة المرجعية" />
              <MetricCard label="RSRQ" value={sig?.rsrq ?? "—"} unit="dB"  quality={sig ? rsrqQuality(sig.rsrq) : undefined} sub="جودة الإشارة" />
              <MetricCard label="SINR" value={sig?.sinr ?? "—"} unit="dB"  quality={sig ? sinrQuality(sig.sinr) : undefined} sub="نسبة الإشارة للضوضاء" />
              <MetricCard label="Band" value={sig?.band ?? "—"} quality={sig ? { label: sig.networkType, color: "text-blue-400" } : undefined} sub={sig ? `${sig.dlFreq} MHz` : ""} />
            </div>

            {sig && (
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                <MetricCard label="Cell ID"  value={sig.cellId || "—"}   sub={`PCI: ${sig.pci}`} />
                <MetricCard label="EARFCN"   value={sig.earfcn || "—"}   sub={`DL: ${sig.dlFreq} MHz`} />
                <MetricCard label="MCC/MNC"  value={`${sig.mcc}/${sig.mnc}`} sub={sig.plmn} />
                <MetricCard label="درجة الحرارة" value={sig.temperature} unit="°C"
                  quality={{ label: sig.temperature > 60 ? "حار!" : "طبيعي", color: sig.temperature > 60 ? "text-orange-400" : "text-emerald-400" }}
                />
              </div>
            )}

            {sig?.ca && (
              <Card className="flex flex-col gap-2">
                <div className="flex items-center gap-2">
                  <Layers className="w-4 h-4 text-purple-400" />
                  <span className="text-xs font-black text-slate-200">تجميع النطاقات (CA) - نشط</span>
                  <span className="text-[9px] bg-purple-500/10 border border-purple-500/20 text-purple-400 px-2 py-0.5 rounded font-bold">ACTIVE</span>
                </div>
                <div className="flex flex-wrap gap-2 mt-1">
                  <span className="text-[11px] bg-blue-950/50 border border-blue-900 text-blue-300 px-2 py-1 rounded font-bold">
                    PCell: {sig.ca.primaryBand}
                  </span>
                  {sig.ca.secondaryBands.map((b, i) => (
                    <span key={i} className="text-[11px] bg-emerald-950/50 border border-emerald-900 text-emerald-300 px-2 py-1 rounded font-bold">
                      SCell: {b}
                    </span>
                  ))}
                  <span className="text-[11px] bg-slate-800 border border-slate-700 text-slate-300 px-2 py-1 rounded font-bold">
                    BW مجمع: {sig.ca.aggregatedBandwidth} MHz
                  </span>
                </div>
              </Card>
            )}

            {/* Antenna & network mode quick controls */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Card>
                <span className="text-xs font-black text-slate-300 mb-3 block">🏠 وضع الهوائي</span>
                <div className="grid grid-cols-3 gap-2">
                  {(["0","1","2"] as const).map((m) => (
                    <button key={m} onClick={() => handleSetAntenna(m)}
                      className={`py-2 rounded-lg text-xs font-bold transition-all ${
                        antennaMode === m ? "bg-emerald-600 text-white" : "bg-slate-800 text-slate-400 hover:bg-slate-700"
                      }`}>
                      {m === "0" ? "داخلي" : m === "1" ? "خارجي" : "هجين"}
                    </button>
                  ))}
                </div>
              </Card>
              <Card>
                <span className="text-xs font-black text-slate-300 mb-3 block">📶 وضع الشبكة</span>
                <div className="grid grid-cols-2 gap-2">
                  {(["auto","4g_only","5g_nsa","5g_sa"] as const).map((m) => (
                    <button key={m} onClick={() => handleSetNetworkMode(m)}
                      className={`py-2 rounded-lg text-xs font-bold transition-all ${
                        networkMode === m ? "bg-blue-700 text-white" : "bg-slate-800 text-slate-400 hover:bg-slate-700"
                      }`}>
                      {m === "auto" ? "تلقائي" : m === "4g_only" ? "4G فقط" : m === "5g_nsa" ? "5G NSA" : "5G SA"}
                    </button>
                  ))}
                </div>
              </Card>
            </div>

            {/* Reboot */}
            <button
              onClick={handleReboot}
              disabled={!conn.isConnected || conn.isLoading}
              className="w-full flex items-center justify-center gap-2 py-2.5 bg-red-900/30 hover:bg-red-900/60 border border-red-900 text-red-400 font-bold rounded-lg transition-all disabled:opacity-40 text-sm"
            >
              <RotateCw className="w-4 h-4" />
              إعادة تشغيل الراوتر
            </button>

            {/* Logs */}
            <Card>
              <span className="text-[10px] font-black text-slate-400 block mb-2">سجل العمليات</span>
              <div ref={logRef} className="max-h-40 overflow-y-auto flex flex-col gap-0.5">
                {logs.length === 0 ? (
                  <span className="text-[11px] text-slate-600">لا يوجد سجلات بعد...</span>
                ) : (
                  logs.map((l, i) => (
                    <div key={i} className="text-[10px] text-slate-400 font-mono leading-relaxed">{l}</div>
                  ))
                )}
              </div>
            </Card>
          </div>
        )}

        {/* ════ BANDS ════ */}
        {activeTab === "bands" && (
          <div className="flex flex-col gap-4">
            <div className="flex items-center justify-between flex-wrap gap-2">
              <div className="flex gap-2">
                {(["all","LTE","NR"] as const).map((f) => (
                  <button key={f} onClick={() => setBandFilter(f)}
                    className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                      bandFilter === f ? "bg-emerald-600 text-white" : "bg-slate-800 text-slate-400 hover:bg-slate-700"
                    }`}>{f === "all" ? "الكل" : f}</button>
                ))}
              </div>
              <button onClick={handleFindBestBand} disabled={!conn.isConnected}
                className="flex items-center gap-2 px-3 py-1.5 bg-yellow-900/40 hover:bg-yellow-900/70 border border-yellow-800 text-yellow-400 rounded-lg text-xs font-bold transition-all disabled:opacity-40">
                <TrendingUp className="w-3.5 h-3.5" />
                أفضل نطاق
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {displayBands.map((band) => (
                <div key={band.hexCode}
                  className={`border rounded-xl p-3 transition-all ${
                    band.isLocked
                      ? "bg-emerald-950/30 border-emerald-700"
                      : band.isActive
                      ? "bg-blue-950/20 border-blue-800"
                      : "bg-slate-900/60 border-slate-800"
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <Radio className={`w-4 h-4 ${band.technology === "NR" ? "text-purple-400" : "text-blue-400"}`} />
                      <span className="text-sm font-black text-slate-200">{band.name}</span>
                      {band.isLocked && (
                        <span className="text-[9px] bg-emerald-900/50 text-emerald-400 px-1.5 py-0.5 rounded font-bold">LOCKED</span>
                      )}
                      {band.isActive && !band.isLocked && (
                        <span className="text-[9px] bg-blue-900/50 text-blue-400 px-1.5 py-0.5 rounded font-bold">ACTIVE</span>
                      )}
                    </div>
                    <span className={`text-[9px] px-1.5 py-0.5 rounded font-bold border ${
                      band.technology === "NR"
                        ? "bg-purple-950/50 border-purple-800 text-purple-400"
                        : "bg-blue-950/50 border-blue-800 text-blue-400"
                    }`}>{band.technology}</span>
                  </div>
                  <div className="grid grid-cols-3 gap-2 mb-3 text-[10px]">
                    <div className="bg-slate-950/50 rounded p-1.5 text-center">
                      <span className="text-slate-500 block">DL</span>
                      <span className="text-slate-200 font-bold">{band.dlFreqMHz} MHz</span>
                    </div>
                    <div className="bg-slate-950/50 rounded p-1.5 text-center">
                      <span className="text-slate-500 block">UL</span>
                      <span className="text-slate-200 font-bold">{band.ulFreqMHz} MHz</span>
                    </div>
                    <div className="bg-slate-950/50 rounded p-1.5 text-center">
                      <span className="text-slate-500 block">BW</span>
                      <span className="text-slate-200 font-bold">{band.bandwidth} MHz</span>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    {band.isLocked ? (
                      <button onClick={() => handleUnlockBand(band)} disabled={!conn.isConnected}
                        className="flex-1 py-1.5 bg-slate-700 hover:bg-slate-600 text-slate-200 text-xs font-bold rounded-lg transition-all disabled:opacity-40 flex items-center justify-center gap-1">
                        <Lock className="w-3 h-3" />
                        إلغاء القفل
                      </button>
                    ) : (
                      <button onClick={() => handleLockBand(band)} disabled={!conn.isConnected}
                        className="flex-1 py-1.5 bg-emerald-700 hover:bg-emerald-600 text-white text-xs font-bold rounded-lg transition-all disabled:opacity-40 flex items-center justify-center gap-1">
                        <Lock className="w-3 h-3" />
                        قفل النطاق
                      </button>
                    )}
                    <button onClick={() => copyText(band.hexCode, band.hexCode)}
                      className="px-2.5 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-400 text-xs rounded-lg transition-all flex items-center gap-1">
                      {copied === band.hexCode ? <CheckCircle className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                      {band.hexCode}
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ════ CELL TOWERS ════ */}
        {activeTab === "cells" && (
          <div className="flex flex-col gap-4">
            <div className="flex items-center justify-between">
              <span className="text-sm font-black text-slate-200">أبراج الاتصال المجاورة</span>
              <div className="flex gap-2">
                {lockedCell && (
                  <button onClick={handleUnlockCell}
                    className="flex items-center gap-1.5 px-3 py-1.5 bg-red-900/40 border border-red-800 text-red-400 text-xs font-bold rounded-lg hover:bg-red-900/60 transition-all">
                    <XCircle className="w-3.5 h-3.5" />
                    إلغاء قفل البرج
                  </button>
                )}
                <button onClick={handleScanCells} disabled={!conn.isConnected || isScanning}
                  className="flex items-center gap-2 px-4 py-1.5 bg-emerald-700 hover:bg-emerald-600 text-white text-xs font-bold rounded-lg disabled:opacity-40 transition-all">
                  {isScanning ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Search className="w-3.5 h-3.5" />}
                  {isScanning ? "جاري المسح..." : "مسح الأبراج"}
                </button>
              </div>
            </div>

            {lockedCell && (
              <div className="flex items-center gap-2 bg-emerald-950/30 border border-emerald-800 p-3 rounded-xl text-xs text-emerald-400 font-bold">
                <Lock className="w-3.5 h-3.5" />
                البرج المقفل: PCI {lockedCell.pci} | EARFCN {lockedCell.earfcn} | {lockedCell.band}
              </div>
            )}

            {conn.cellTowers.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-12 text-slate-600">
                <Satellite className="w-10 h-10 mb-3 opacity-30" />
                <span className="text-sm">اضغط "مسح الأبراج" لعرض الأبراج المجاورة</span>
              </div>
            ) : (
              <div className="flex flex-col gap-3">
                {conn.cellTowers.map((cell, i) => (
                  <div key={i}
                    className={`border rounded-xl transition-all ${
                      lockedCell?.pci === cell.pci && lockedCell?.earfcn === cell.earfcn
                        ? "bg-emerald-950/30 border-emerald-700"
                        : cell.isServing
                        ? "bg-blue-950/20 border-blue-800"
                        : "bg-slate-900/60 border-slate-800"
                    }`}
                  >
                    <div
                      className="flex items-center justify-between p-3 cursor-pointer"
                      onClick={() => setExpandedCell(expandedCell === `${cell.pci}_${cell.earfcn}` ? null : `${cell.pci}_${cell.earfcn}`)}
                    >
                      <div className="flex items-center gap-3">
                        <div className={`w-2 h-2 rounded-full ${cell.isServing ? "bg-emerald-400 animate-pulse" : "bg-slate-600"}`} />
                        <div>
                          <span className="text-sm font-black text-slate-200">
                            {cell.isServing ? "🏆 برج خادم" : `برج ${i + 1}`}
                          </span>
                          <div className="flex gap-2 mt-0.5">
                            <span className="text-[10px] text-slate-400">PCI: <strong>{cell.pci}</strong></span>
                            <span className="text-[10px] text-slate-400">EARFCN: <strong>{cell.earfcn}</strong></span>
                            <span className="text-[10px] text-blue-400 font-bold">{cell.band}</span>
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center gap-3">
                        <div className="text-right">
                          <span className={`text-sm font-black ${rsrpQuality(cell.rsrp).color}`}>{cell.rsrp} dBm</span>
                          <div className="w-20 h-1.5 bg-slate-800 rounded-full mt-1">
                            <div
                              className={`h-1.5 rounded-full ${cell.rsrp >= -90 ? "bg-emerald-400" : cell.rsrp >= -105 ? "bg-yellow-400" : "bg-red-400"}`}
                              style={{ width: `${signalBarWidth(cell.rsrp)}%` }}
                            />
                          </div>
                        </div>
                        {expandedCell === `${cell.pci}_${cell.earfcn}` ? <ChevronUp className="w-4 h-4 text-slate-400" /> : <ChevronDown className="w-4 h-4 text-slate-400" />}
                      </div>
                    </div>
                    {expandedCell === `${cell.pci}_${cell.earfcn}` && (
                      <div className="px-3 pb-3 flex flex-col gap-3 border-t border-slate-800 pt-3">
                        <div className="grid grid-cols-3 gap-2 text-[10px]">
                          <div className="bg-slate-950/50 rounded p-1.5 text-center">
                            <span className="text-slate-500 block">RSRP</span>
                            <span className={`font-bold ${rsrpQuality(cell.rsrp).color}`}>{cell.rsrp} dBm</span>
                          </div>
                          <div className="bg-slate-950/50 rounded p-1.5 text-center">
                            <span className="text-slate-500 block">RSRQ</span>
                            <span className={`font-bold ${rsrqQuality(cell.rsrq).color}`}>{cell.rsrq} dB</span>
                          </div>
                          <div className="bg-slate-950/50 rounded p-1.5 text-center">
                            <span className="text-slate-500 block">SINR</span>
                            <span className={`font-bold ${sinrQuality(cell.sinr).color}`}>{cell.sinr} dB</span>
                          </div>
                        </div>
                        <div className="flex gap-2">
                          <button
                            onClick={() => handleLockCell(cell)}
                            disabled={!conn.isConnected}
                            className="flex-1 py-1.5 bg-emerald-700 hover:bg-emerald-600 text-white text-xs font-bold rounded-lg disabled:opacity-40 flex items-center justify-center gap-1"
                          >
                            <Lock className="w-3 h-3" />
                            قفل على هذا البرج
                          </button>
                          <button
                            onClick={() => copyText(`PCI:${cell.pci} EARFCN:${cell.earfcn} RSRP:${cell.rsrp}`, `cell_${i}`)}
                            className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-400 text-xs rounded-lg flex items-center gap-1"
                          >
                            {copied === `cell_${i}` ? <CheckCircle className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* ════ SIGNAL MONITOR ════ */}
        {activeTab === "signal" && (
          <div className="flex flex-col gap-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <MetricCard label="RSRP" value={sig?.rsrp ?? "—"} unit="dBm" quality={sig ? rsrpQuality(sig.rsrp) : undefined} sub="Reference Signal Received Power" />
              <MetricCard label="RSRQ" value={sig?.rsrq ?? "—"} unit="dB"  quality={sig ? rsrqQuality(sig.rsrq) : undefined} sub="Reference Signal Received Quality" />
              <MetricCard label="SINR" value={sig?.sinr ?? "—"} unit="dB"  quality={sig ? sinrQuality(sig.sinr) : undefined} sub="Signal to Interference + Noise Ratio" />
            </div>

            <Card>
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-black text-slate-300">مخطط RSRP اللحظي</span>
                <span className="text-[10px] text-slate-500">{conn.signalHistory.length} نقطة</span>
              </div>
              <Sparkline data={conn.signalHistory.map((h) => h.rsrp)} color="#10b981" />
              <div className="flex justify-between text-[9px] text-slate-600 mt-1">
                <span>-120 dBm</span>
                <span className="text-emerald-400">RSRP</span>
                <span>-40 dBm</span>
              </div>
            </Card>

            <Card>
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-black text-slate-300">مخطط SINR اللحظي</span>
              </div>
              <Sparkline data={conn.signalHistory.map((h) => h.sinr)} color="#3b82f6" />
              <div className="flex justify-between text-[9px] text-slate-600 mt-1">
                <span>-20 dB</span>
                <span className="text-blue-400">SINR</span>
                <span>30 dB</span>
              </div>
            </Card>

            {sig && (
              <div className="grid grid-cols-2 gap-3">
                <MetricCard label="EARFCN (DL)" value={sig.earfcn || "—"} sub={`${sig.dlFreq} MHz`} />
                <MetricCard label="ARFCN (UL)"  value={sig.arfcn || "—"} sub={`${sig.ulFreq} MHz`} />
                <MetricCard label="Bandwidth"   value={sig.bandwidth} unit="MHz" sub="عرض النطاق" />
                <MetricCard label="LAC"          value={sig.lac || "—"} sub={`PLMN: ${sig.plmn || "—"}`} />
              </div>
            )}

            {!conn.isConnected && (
              <div className="flex items-center justify-center py-8 text-slate-600">
                <Signal className="w-8 h-8 mb-2 opacity-30" />
              </div>
            )}
          </div>
        )}

        {/* ════ NETWORK ════ */}
        {activeTab === "network" && (
          <div className="flex flex-col gap-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Card>
                <span className="text-xs font-black text-slate-300 mb-3 block">📶 وضع الشبكة</span>
                <div className="grid grid-cols-2 gap-2">
                  {(["auto","4g_only","5g_nsa","5g_sa"] as const).map((m) => (
                    <button key={m} onClick={() => handleSetNetworkMode(m)}
                      className={`py-3 rounded-xl text-xs font-bold transition-all flex flex-col items-center gap-1 ${
                        networkMode === m
                          ? "bg-blue-700 text-white border border-blue-500"
                          : "bg-slate-800 text-slate-400 border border-slate-700 hover:border-blue-700"
                      }`}>
                      <Globe className="w-4 h-4" />
                      {m === "auto" ? "تلقائي" : m === "4g_only" ? "4G فقط" : m === "5g_nsa" ? "5G NSA" : "5G SA"}
                    </button>
                  ))}
                </div>
              </Card>

              <Card>
                <span className="text-xs font-black text-slate-300 mb-3 block">📡 وضع الهوائي</span>
                <div className="flex flex-col gap-2">
                  {([
                    { id: "0", label: "هوائي داخلي فقط", desc: "استخدم الهوائيات المدمجة" },
                    { id: "1", label: "هوائي خارجي فقط", desc: "استخدم منفذ MIMO الخارجي" },
                    { id: "2", label: "هجين تلقائي",      desc: "الراوتر يختار الأفضل" },
                  ] as const).map((a) => (
                    <button key={a.id} onClick={() => handleSetAntenna(a.id)}
                      className={`flex items-center gap-3 p-3 rounded-xl text-sm transition-all text-right ${
                        antennaMode === a.id
                          ? "bg-emerald-900/40 border border-emerald-700"
                          : "bg-slate-800/60 border border-slate-700 hover:border-emerald-700"
                      }`}>
                      <div className={`w-2.5 h-2.5 rounded-full ${antennaMode === a.id ? "bg-emerald-400" : "bg-slate-600"}`} />
                      <div className="flex-1 text-right">
                        <span className={`font-bold block text-xs ${antennaMode === a.id ? "text-emerald-400" : "text-slate-300"}`}>{a.label}</span>
                        <span className="text-[10px] text-slate-500">{a.desc}</span>
                      </div>
                    </button>
                  ))}
                </div>
              </Card>
            </div>

            {sig && (
              <Card>
                <span className="text-xs font-black text-slate-300 mb-3 block">🌐 معلومات الشبكة</span>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-3 text-[11px]">
                  {[
                    ["نوع الشبكة", sig.networkType],
                    ["MCC", sig.mcc],
                    ["MNC", sig.mnc],
                    ["LAC", sig.lac],
                    ["PLMN", sig.plmn],
                    ["Cell ID", sig.cellId],
                    ["PCI", String(sig.pci)],
                    ["EARFCN", String(sig.earfcn)],
                    ["تردد DL", `${sig.dlFreq} MHz`],
                  ].map(([k, v]) => (
                    <div key={k} className="bg-slate-900/50 rounded-lg p-2 flex flex-col gap-0.5">
                      <span className="text-slate-500 text-[9px] font-bold uppercase">{k}</span>
                      <span className="text-slate-200 font-bold">{v || "—"}</span>
                    </div>
                  ))}
                </div>
              </Card>
            )}

            {conn.deviceInfo && Object.keys(conn.deviceInfo).length > 0 && (
              <Card>
                <span className="text-xs font-black text-slate-300 mb-3 block">🔧 معلومات الجهاز</span>
                <div className="grid grid-cols-2 gap-2 text-[11px]">
                  {Object.entries(conn.deviceInfo).map(([k, v]) => (
                    <div key={k} className="bg-slate-900/50 rounded-lg p-2">
                      <span className="text-slate-500 text-[9px] block font-bold uppercase">{k}</span>
                      <span className="text-slate-200 font-mono">{v || "—"}</span>
                    </div>
                  ))}
                </div>
              </Card>
            )}
          </div>
        )}

        {/* ════ DEVICES ════ */}
        {activeTab === "devices" && (
          <div className="flex flex-col gap-4">
            <div className="flex items-center justify-between">
              <span className="text-sm font-black text-slate-200">
                الأجهزة المتصلة ({conn.connectedDevices.length})
              </span>
              <button
                onClick={async () => {
                  addLog("🔍 جاري تحديث قائمة الأجهزة...");
                  await conn.refreshDevices();
                  addLog(`✅ تم العثور على ${conn.connectedDevices.length} جهاز`);
                }}
                disabled={!conn.isConnected}
                className="flex items-center gap-2 px-3 py-1.5 bg-emerald-700 hover:bg-emerald-600 text-white text-xs font-bold rounded-lg disabled:opacity-40"
              >
                <RefreshCw className="w-3.5 h-3.5" />
                تحديث
              </button>
            </div>

            {conn.connectedDevices.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-12 text-slate-600">
                <Smartphone className="w-10 h-10 mb-3 opacity-30" />
                <span className="text-sm">لا توجد أجهزة - اتصل بالراوتر واضغط تحديث</span>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {conn.connectedDevices.map((d, i) => (
                  <div key={i} className="bg-slate-900/60 border border-slate-800 rounded-xl p-3 flex items-center gap-3">
                    <div className="p-2 bg-blue-950/50 rounded-lg">
                      <Smartphone className="w-4 h-4 text-blue-400" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="font-bold text-sm text-slate-200 truncate">{d.hostname}</div>
                      <div className="text-[10px] text-slate-400 font-mono">{d.ip}</div>
                      <div className="text-[10px] text-slate-500 font-mono">{d.mac}</div>
                    </div>
                    <div className="flex flex-col items-end gap-1">
                      <span className="text-[9px] bg-emerald-950/50 border border-emerald-900 text-emerald-400 px-2 py-0.5 rounded font-bold">
                        {d.connectionType}
                      </span>
                      <button onClick={() => copyText(`${d.ip} ${d.mac}`, `dev_${i}`)}
                        className="text-slate-500 hover:text-slate-300">
                        {copied === `dev_${i}` ? <CheckCircle className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* ════ SPEED TEST ════ */}
        {activeTab === "speed" && (
          <div className="flex flex-col gap-4">
            <button
              onClick={handleSpeedTest}
              disabled={!conn.isConnected || isRunningSpeed}
              className="w-full py-5 bg-gradient-to-r from-emerald-700 to-blue-700 hover:from-emerald-600 hover:to-blue-600 disabled:from-slate-700 disabled:to-slate-700 text-white font-black text-lg rounded-2xl transition-all flex items-center justify-center gap-3"
            >
              {isRunningSpeed ? (
                <><RefreshCw className="w-6 h-6 animate-spin" /> جاري اختبار السرعة...</>
              ) : (
                <><Zap className="w-6 h-6" /> بدء اختبار السرعة</>
              )}
            </button>

            {conn.lastSpeedTest && (
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                <Card className="text-center">
                  <Download className="w-5 h-5 text-emerald-400 mx-auto mb-1" />
                  <span className="text-2xl font-black text-emerald-400">{conn.lastSpeedTest.downloadMbps}</span>
                  <span className="text-xs text-slate-400 block">Mbps تنزيل</span>
                </Card>
                <Card className="text-center">
                  <ArrowRightLeft className="w-5 h-5 text-blue-400 mx-auto mb-1" />
                  <span className="text-2xl font-black text-blue-400">{conn.lastSpeedTest.uploadMbps}</span>
                  <span className="text-xs text-slate-400 block">Mbps رفع</span>
                </Card>
                <Card className="text-center">
                  <Activity className="w-5 h-5 text-yellow-400 mx-auto mb-1" />
                  <span className="text-2xl font-black text-yellow-400">{conn.lastSpeedTest.pingMs}</span>
                  <span className="text-xs text-slate-400 block">ms تأخير</span>
                </Card>
                <Card className="text-center">
                  <Sliders className="w-5 h-5 text-purple-400 mx-auto mb-1" />
                  <span className="text-2xl font-black text-purple-400">{conn.lastSpeedTest.jitterMs}</span>
                  <span className="text-xs text-slate-400 block">ms تذبذب</span>
                </Card>
              </div>
            )}

            {conn.signalData && (
              <Card>
                <span className="text-xs font-black text-slate-300 mb-3 block">📊 بيانات الإنتاجية اللحظية</span>
                <div className="grid grid-cols-2 gap-3">
                  <div className="text-center">
                    <span className="text-2xl font-black text-emerald-400">
                      {((conn.signalData.downlinkSpeed || 0) / 1024).toFixed(1)}
                    </span>
                    <span className="text-xs text-slate-400 block">Mbps DL (من الراوتر)</span>
                  </div>
                  <div className="text-center">
                    <span className="text-2xl font-black text-blue-400">
                      {((conn.signalData.uplinkSpeed || 0) / 1024).toFixed(1)}
                    </span>
                    <span className="text-xs text-slate-400 block">Mbps UL (من الراوتر)</span>
                  </div>
                </div>
              </Card>
            )}

            {!conn.isConnected && (
              <div className="text-center py-8 text-slate-500">
                <Zap className="w-10 h-10 mx-auto mb-2 opacity-20" />
                <span className="text-sm">اتصل بالراوتر أولاً لإجراء اختبار السرعة</span>
              </div>
            )}
          </div>
        )}

        {/* ════ HISTORY ════ */}
        {activeTab === "history" && (
          <div className="flex flex-col gap-4">
            <div className="flex items-center justify-between">
              <span className="text-sm font-black text-slate-200">سجل الإشارة ({conn.signalHistory.length} نقطة)</span>
              <span className="text-[10px] text-slate-500">تحديث كل 4 ثوانٍ</span>
            </div>

            <div className="grid grid-cols-1 gap-4">
              <Card>
                <span className="text-xs font-bold text-slate-400 mb-2 block">RSRP عبر الزمن (dBm)</span>
                <Sparkline data={conn.signalHistory.map((h) => h.rsrp)} color="#10b981" />
              </Card>
              <Card>
                <span className="text-xs font-bold text-slate-400 mb-2 block">RSRQ عبر الزمن (dB)</span>
                <Sparkline data={conn.signalHistory.map((h) => h.rsrq)} color="#f59e0b" />
              </Card>
              <Card>
                <span className="text-xs font-bold text-slate-400 mb-2 block">SINR عبر الزمن (dB)</span>
                <Sparkline data={conn.signalHistory.map((h) => h.sinr)} color="#3b82f6" />
              </Card>
            </div>

            {conn.signalHistory.length > 0 && (
              <div className="overflow-x-auto">
                <table className="w-full text-[10px] font-mono border-collapse">
                  <thead>
                    <tr className="border-b border-slate-800">
                      <th className="text-slate-500 p-2 text-right">الوقت</th>
                      <th className="text-slate-500 p-2">RSRP</th>
                      <th className="text-slate-500 p-2">RSRQ</th>
                      <th className="text-slate-500 p-2">SINR</th>
                      <th className="text-slate-500 p-2">Band</th>
                    </tr>
                  </thead>
                  <tbody>
                    {[...conn.signalHistory].reverse().slice(0, 20).map((h, i) => (
                      <tr key={i} className="border-b border-slate-800/40 hover:bg-slate-800/20">
                        <td className="p-2 text-slate-400">{h.time}</td>
                        <td className={`p-2 text-center font-bold ${rsrpQuality(h.rsrp).color}`}>{h.rsrp}</td>
                        <td className={`p-2 text-center font-bold ${rsrqQuality(h.rsrq).color}`}>{h.rsrq}</td>
                        <td className={`p-2 text-center font-bold ${sinrQuality(h.sinr).color}`}>{h.sinr}</td>
                        <td className="p-2 text-center text-blue-400">{h.band}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* ════ EXPORT ════ */}
        {activeTab === "export" && (
          <div className="flex flex-col gap-4">
            <Card>
              <div className="flex items-center gap-3 mb-4">
                <div className="p-2 bg-emerald-950/50 rounded-lg">
                  <FileText className="w-5 h-5 text-emerald-400" />
                </div>
                <div>
                  <span className="text-sm font-black text-slate-200 block">تصدير تقرير التشخيص الكامل</span>
                  <span className="text-[10px] text-slate-400">يشمل: الإشارة، الأبراج، الأجهزة، اختبار السرعة، السجلات</span>
                </div>
              </div>
              <button
                onClick={handleExport}
                disabled={isExporting}
                className="w-full py-3 bg-emerald-700 hover:bg-emerald-600 disabled:bg-slate-700 text-white font-bold rounded-xl transition-all flex items-center justify-center gap-2"
              >
                {isExporting ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
                {isExporting ? "جاري التصدير..." : "تصدير JSON"}
              </button>
            </Card>

            <Card>
              <span className="text-xs font-black text-slate-300 mb-3 block">📋 ملخص البيانات الحالية</span>
              <div className="grid grid-cols-2 gap-2 text-[11px]">
                {[
                  ["الراوتر", `${routerBrand} (${routerIp})`],
                  ["نقاط الإشارة", String(conn.signalHistory.length)],
                  ["الأبراج المرصودة", String(conn.cellTowers.length)],
                  ["الأجهزة المتصلة", String(conn.connectedDevices.length)],
                  ["النطاقات المقفلة", String(lockedBands.size)],
                  ["آخر تحديث", conn.lastUpdate ? conn.lastUpdate.toLocaleTimeString("ar-EG") : "—"],
                ].map(([k, v]) => (
                  <div key={k} className="bg-slate-900/50 rounded-lg p-2">
                    <span className="text-slate-500 text-[9px] block">{k}</span>
                    <span className="text-slate-200 font-bold">{v}</span>
                  </div>
                ))}
              </div>
            </Card>

            <Card>
              <span className="text-xs font-black text-slate-300 mb-2 block">🔑 نسخ معلومات الاتصال</span>
              <div className="bg-slate-900 rounded-lg p-3 font-mono text-[10px] text-slate-300">
                <pre>{JSON.stringify({ ip: routerIp, brand: routerBrand, signal: sig ? { rsrp: sig.rsrp, sinr: sig.sinr, band: sig.band } : null }, null, 2)}</pre>
              </div>
              <button
                onClick={() => copyText(JSON.stringify({ ip: routerIp, brand: routerBrand, signal: sig }, null, 2), "conn_info")}
                className="mt-2 flex items-center gap-2 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-400 text-xs rounded-lg"
              >
                {copied === "conn_info" ? <CheckCircle className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                نسخ
              </button>
            </Card>
          </div>
        )}

        {/* ════ COMMANDS ════ */}
        {activeTab === "commands" && (
          <div className="flex flex-col gap-4">
            <Card>
              <span className="text-xs font-black text-slate-300 mb-3 block">⌨️ أوامر Huawei API</span>
              <div className="bg-slate-900 rounded-lg p-3 overflow-x-auto">
                <pre className="text-[10px] text-emerald-400 font-mono whitespace-pre leading-relaxed">{`# استخراج Token
TOKEN=$(curl -s http://${routerIp}/api/webserver/token | grep -oP '(?<=<token>)[^<]+')

# تسجيل الدخول (Type 4 - SHA256)
curl -X POST http://${routerIp}/api/user/login \\
  -H "Content-Type: application/xml" \\
  -H "__RequestVerificationToken: $TOKEN" \\
  -d '<request><Username>admin</Username><Password>HASHED</Password><password_type>4</password_type></request>'

# جلب بيانات الإشارة
curl -s http://${routerIp}/api/net/current-plmn \\
  -H "__RequestVerificationToken: $TOKEN"

# قفل نطاق B3
curl -X POST http://${routerIp}/api/net/net-mode \\
  -H "Content-Type: application/xml" \\
  -H "__RequestVerificationToken: $TOKEN" \\
  -d '<request><NetworkMode>03</NetworkMode><LTEBand>0x4</LTEBand></request>'

# إعادة التشغيل
curl -X POST http://${routerIp}/api/device/control \\
  -H "__RequestVerificationToken: $TOKEN" \\
  -d '<request><control>1</control></request>'`}</pre>
              </div>
              <button onClick={() => copyText(
                `TOKEN=$(curl -s http://${routerIp}/api/webserver/token | grep -oP '(?<=<token>)[^<]+')`,
                "huawei_cmd"
              )} className="mt-2 flex items-center gap-2 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-400 text-xs rounded-lg">
                {copied === "huawei_cmd" ? <CheckCircle className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                نسخ
              </button>
            </Card>

            <Card>
              <span className="text-xs font-black text-slate-300 mb-3 block">⌨️ أوامر ZTE API</span>
              <div className="bg-slate-900 rounded-lg p-3 overflow-x-auto">
                <pre className="text-[10px] text-blue-400 font-mono whitespace-pre leading-relaxed">{`# جلب Token التحقق
curl http://${routerIp}/goform/goform_get_cmd_process?cmd=LD

# تسجيل الدخول (MD5 + LD)
curl -X POST http://${routerIp}/goform/goform_set_cmd_process \\
  -d "goformId=LOGIN&password=HASHED_PASSWORD"

# جلب بيانات الإشارة (دفعة واحدة)
curl "http://${routerIp}/goform/goform_get_cmd_process?isRecognized=1&cmd=lte_rsrp,lte_sinr,lte_rsrq,cell_id,pci,lte_band,hardware_temp"

# قفل نطاق LTE
curl -X POST http://${routerIp}/goform/goform_set_cmd_process \\
  -d "goformId=SET_LTE_BAND_LOCK&lte_band_lock=3"

# اختبار السرعة اللحظي
curl "http://${routerIp}/goform/goform_get_cmd_process?isRecognized=1&cmd=realtime_rx_thrpt,realtime_tx_thrpt"`}</pre>
              </div>
            </Card>

            <Card>
              <span className="text-xs font-black text-slate-300 mb-2 block">🔐 17 طريقة مصادقة متقدمة مُطبّقة</span>
              <div className="grid grid-cols-1 gap-1">
                {[
                  "SHA256 HMAC كلمة المرور المتقدمة",
                  "Mutex منع تعارض الطلبات",
                  "Retry مع تراجع أسي (Exponential Backoff)",
                  "XML Parser متعدد التنسيقات",
                  "Cookie Jar وإدارة الجلسات",
                  "كشف إصدار Firmware هواوي تلقائياً",
                  "User-Agent تكيفي لكل راوتر",
                  "اكتشاف Gateway تلقائياً (8 عناوين IP)",
                  "استخراج Token متعدد المصادر",
                  "كشف نوع كلمة المرور (Type 1/2/3/4)",
                  "تفاوض نوع كلمة المرور التكيفي",
                  "إعادة المصادقة على 401/403 تلقائياً",
                  "ZTE Challenge-Response مع LD Token",
                  "ZTE MD5 Hash مع طبقة SHA256",
                  "ZTE Multi-endpoint Login Fallback",
                  "ZTE Plain Auth احتياطي",
                  "ZTE Batch Data Fetch (أوامر مجمعة)",
                ].map((idea, i) => (
                  <div key={i} className="flex items-center gap-2 text-[10px] py-0.5">
                    <CheckCircle className="w-3 h-3 text-emerald-400 flex-shrink-0" />
                    <span className="text-slate-300">
                      <span className="text-slate-500 ml-1">#{i + 1}</span>
                      {idea}
                    </span>
                  </div>
                ))}
              </div>
            </Card>
          </div>
        )}
      </div>

      {/* ── Footer ── */}
      <div className="border-t border-slate-800 px-5 py-3 flex items-center justify-between bg-slate-950/60">
        <div className="flex items-center gap-2">
          <Award className="w-4 h-4 text-emerald-400" />
          <span className="text-[11px] text-slate-400">
            تطوير: <strong className="text-emerald-400">{DEV_SIGN}</strong>
            <span className="text-slate-600 mx-1">|</span>
            <strong className="text-slate-400">{DEV_SIGN_EN}</strong>
          </span>
        </div>
        <div className="flex items-center gap-2">
          {conn.lastUpdate && (
            <span className="text-[9px] text-slate-600 font-mono">
              آخر تحديث: {conn.lastUpdate.toLocaleTimeString("ar-EG")}
            </span>
          )}
          <span className="text-[9px] bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 px-2 py-0.5 rounded font-mono font-bold">
            REAL API
          </span>
        </div>
      </div>
    </div>
  );
}
