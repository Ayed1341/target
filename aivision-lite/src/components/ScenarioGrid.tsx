import React, { useState } from "react";
import { Search, Database, Tv, Hammer, Eye, Compass, UserCheck } from "lucide-react";
import { PRESET_SCENARIOS } from "../data/presets";
import { PresetScenario, ScanCategory } from "../types";

interface ScenarioGridProps {
  onSelectScenario: (scenario: PresetScenario) => void;
  activeScenarioId: string | null;
}

export default function ScenarioGrid({ onSelectScenario, activeScenarioId }: ScenarioGridProps) {
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedCategory, setSelectedCategory] = useState<ScanCategory | "All">("All");

  const categories: ("All" | Exclude<ScanCategory, "Auto Detect">)[] = [
    "All",
    "Spy & Covert Gear",
    "TV & Room Equipment",
    "Objects & Tools",
    "Animals & Creatures",
    "Humans & Action"
  ];

  // Map category name to icon
  const getCategoryIcon = (cat: string) => {
    switch (cat) {
      case "Spy & Covert Gear":
        return <Eye className="w-3.5 h-3.5 text-rose-500 font-bold animate-pulse" />;
      case "TV & Room Equipment":
        return <Tv className="w-3.5 h-3.5 text-blue-400" />;
      case "Objects & Tools":
        return <Hammer className="w-3.5 h-3.5 text-amber-500" />;
      case "Animals & Creatures":
        return <Compass className="w-3.5 h-3.5 text-emerald-400" />;
      case "Humans & Action":
        return <UserCheck className="w-3.5 h-3.5 text-sky-400" />;
      default:
        return <Database className="w-3.5 h-3.5 text-slate-400" />;
    }
  };

  // Filter preset scenarios
  const filteredScenarios = PRESET_SCENARIOS.filter((item) => {
    const matchesSearch = item.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                          item.description.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesCategory = selectedCategory === "All" || item.category === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  return (
    <div className="w-full bg-slate-900 border border-slate-800 rounded-2xl p-4 md:p-5 flex flex-col gap-4 shadow-xl">
      
      {/* Header section with counts */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <Database className="w-5 h-5 text-emerald-400" />
          <div>
            <h3 className="font-extrabold text-sm text-slate-100 flex items-center gap-1.5">
              LOCAL OBJECT RECOGNITION DATABASE
              <span className="text-[10px] bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 px-1.5 py-0.5 rounded-full font-mono font-bold">
                {PRESET_SCENARIOS.length} ITEMS DEFINED
              </span>
            </h3>
            <p className="text-[11px] text-slate-400 font-mono mt-0.5">
              Instant hardware scan specs matching military optic telemetry datasets.
            </p>
          </div>
        </div>
      </div>

      {/* Filter and Search Action bar */}
      <div className="flex flex-col md:flex-row gap-3">
        {/* Search bar inputs */}
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
          <input
            id="input-search-db"
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="البحث عن كاميرات مخفية، أجهزة تجسس، شبكات، أجهزة، كائنات... Search spy wear, cameras, networks..."
            className="w-full bg-slate-950 check outline-none border border-slate-850 focus:border-emerald-500/80 rounded-xl py-2 pl-9 pr-4 text-xs font-mono text-slate-200 transition placeholder-slate-600"
          />
        </div>

        {/* Categories sliding tab */}
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 max-w-full no-scrollbar">
          {categories.map((cat) => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              className={`text-[10.5px] font-bold font-mono px-3 py-1.5 rounded-lg border transition flex-shrink-0 flex items-center gap-1.5 ${
                selectedCategory === cat
                  ? "bg-emerald-600/15 border-emerald-500/60 text-emerald-400"
                  : "bg-slate-950 border-slate-850 hover:bg-slate-850 text-slate-400 hover:text-slate-200"
              }`}
            >
              {cat !== "All" && getCategoryIcon(cat)}
              {cat === "All" ? "ALL CATS" : cat.split(" & ")[0].toUpperCase()}
            </button>
          ))}
        </div>
      </div>

      {/* Scenarios Grid List viewport */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2.5 max-h-[360px] overflow-y-auto pr-1 no-scrollbar">
        {filteredScenarios.length > 0 ? (
          filteredScenarios.map((item) => {
            const isActive = activeScenarioId === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onSelectScenario(item)}
                className={`text-left p-3 rounded-xl border transition-all duration-150 flex flex-col justify-between h-28 ${
                  isActive
                    ? "bg-slate-950 border-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.15)] ring-1 ring-emerald-500/30"
                    : "bg-slate-950 border-slate-850 hover:border-slate-700 hover:bg-slate-850/50"
                }`}
              >
                <div>
                  <div className="flex items-start justify-between gap-1.5">
                    <span className="text-[9px] font-mono text-slate-500 font-bold block truncate max-w-[125px]">
                      {item.category.toUpperCase()}
                    </span>
                    <span className="flex-shrink-0 bg-slate-900 border border-slate-800 p-1 rounded-md text-slate-400">
                      {getCategoryIcon(item.category)}
                    </span>
                  </div>
                  <h4 className="text-[12px] font-extrabold text-slate-200 tracking-tight mt-1 line-clamp-1">
                    {item.name}
                  </h4>
                  <p className="text-[10px] text-slate-400 line-clamp-2 mt-0.5 leading-snug">
                    {item.description}
                  </p>
                </div>

                <div className="flex justify-between items-center mt-2 border-t border-slate-850 pt-1.5 w-full text-[9px] font-mono">
                  <span className="text-emerald-500 font-bold">SIZE: {item.size}</span>
                  <span className="text-slate-400 bg-slate-900 px-1.5 py-0.5 rounded border border-slate-800 font-black">
                    {item.confidence}%
                  </span>
                </div>
              </button>
            );
          })
        ) : (
          <div className="col-span-full py-8 text-center bg-slate-950 rounded-xl border border-dotted border-slate-850">
            <p className="text-xs text-slate-500 font-mono">
              NO PRESETS FOUND MATCHING SEARCH FILTERS.
            </p>
            <p className="text-[11px] text-slate-600 font-mono mt-0.5">
              Snap a custom picture using Analyze Camera to probe the internet knowledge fallback.
            </p>
          </div>
        )}
      </div>

    </div>
  );
}
