import React from "react";
import { History, Trash2, ArrowUpRight, ShieldAlert, Sparkles, Orbit } from "lucide-react";
import { DetectedObject } from "../types";

interface HistoryLogProps {
  logs: DetectedObject[];
  onSelectLog: (log: DetectedObject) => void;
  onClearLogs: () => void;
  onRemoveLog: (id: string, e: React.MouseEvent) => void;
  activeLogId: string | null;
}

export default function HistoryLog({
  logs,
  onSelectLog,
  onClearLogs,
  onRemoveLog,
  activeLogId
}: HistoryLogProps) {
  return (
    <div className="w-full bg-slate-900 border border-slate-800 rounded-2xl p-4 md:p-5 flex flex-col gap-4 shadow-xl">
      <div className="flex items-center justify-between gap-3 border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <History className="w-5 h-5 text-emerald-400" />
          <div>
            <h3 className="font-extrabold text-sm text-slate-100 flex items-center gap-1.5">
              TELEMETRY AUDIT REGISTRY
              <span className="text-[10px] bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 px-2.5 py-0.5 rounded-full font-mono font-bold">
                {logs.length} REGISTERED
              </span>
            </h3>
            <p className="text-[11px] text-slate-400 font-mono mt-0.5">
              Log registry tracking spatial boundaries and malware device flags.
            </p>
          </div>
        </div>

        {logs.length > 0 && (
          <button
            id="btn-clear-history"
            onClick={onClearLogs}
            className="text-[10px] font-bold font-mono px-2.5 py-1.5 bg-red-950/20 border border-red-500/30 text-red-400 hover:bg-red-900 hover:text-slate-100 rounded-lg transition flex items-center gap-1.5 shadow"
          >
            <Trash2 className="w-3.5 h-3.5" />
            WIPE CACHE
          </button>
        )}
      </div>

      <div className="flex flex-col gap-2 max-h-[220px] overflow-y-auto pr-1 no-scrollbar">
        {logs.length > 0 ? (
          logs.map((log) => {
            const isActive = activeLogId === log.id;
            const isHighRisk = log.hideCameraStatus.toLowerCase().includes("warning") ||
                               log.hideCameraStatus.toLowerCase().includes("suspected");

            return (
              <div
                key={log.id}
                onClick={() => onSelectLog(log)}
                className={`text-left p-3 rounded-xl border transition-all flex items-center justify-between gap-3 cursor-pointer ${
                  isActive
                    ? "bg-slate-950 border-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.1)]"
                    : "bg-slate-950 border-slate-850 hover:border-slate-800 hover:bg-slate-850/40"
                }`}
              >
                <div className="flex items-center gap-3 overflow-hidden">
                  {/* Miniature Image capture view */}
                  <div className="relative w-11 h-11 rounded-lg overflow-hidden bg-slate-900 border border-slate-800 flex-shrink-0 flex items-center justify-center">
                    {log.imageUrl ? (
                      <img src={log.imageUrl} alt={log.name} className="w-full h-full object-cover" />
                    ) : (
                      <Orbit className="w-5 h-5 text-slate-600 animate-spin" />
                    )}
                    {isHighRisk && (
                      <div className="absolute top-0 right-0 w-3 h-3 bg-red-500 rounded-bl flex items-center justify-center">
                        <ShieldAlert className="w-2.5 h-2.5 text-slate-100" />
                      </div>
                    )}
                  </div>

                  <div className="overflow-hidden">
                    <span className="text-[9px] font-mono font-bold tracking-wider text-slate-500 uppercase">
                      {log.category} // CONF: {log.confidence}%
                    </span>
                    <h4 className="text-[12px] font-extrabold text-slate-200 tracking-tight leading-snug truncate">
                      {log.name}
                    </h4>
                    <p className="text-[10px] text-slate-400 font-mono mt-0.5 truncate max-w-[180px]">
                      {log.size} // {new Date(log.scannedAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-1 flex-shrink-0">
                  <button
                    id={`btn-remove-log-${log.id}`}
                    onClick={(e) => onRemoveLog(log.id, e)}
                    className="p-1.5 hover:bg-red-950/30 border border-transparent hover:border-red-500/20 text-slate-500 hover:text-red-400 rounded-lg transition c-pointer"
                    title="Remove item"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                  <ArrowUpRight className="w-4 h-4 text-slate-600" />
                </div>
              </div>
            );
          })
        ) : (
          <div className="py-6 text-center bg-slate-950 rounded-xl border border-dotted border-slate-850">
            <p className="text-xs text-slate-500 font-mono">
              TELEMETRY LOGISTRY CACHE IS EMPTY.
            </p>
            <p className="text-[11px] text-slate-600 font-mono mt-0.5">
              Identified items will appear in real-time as they are processed.
            </p>
          </div>
        )}
      </div>

    </div>
  );
}
