# Architecture

## Overview

The suite uses a thin batch launcher plus a PowerShell orchestrator that loads a
set of focused, single-responsibility modules. Behaviour that varies per
emulator is data-driven via `config\emulators.json`, so most extensions require
no code changes.

```
RetroBatAutoSetup.bat
        │  (elevates, sets per-process ExecutionPolicy Bypass)
        ▼
scripts\RetroBatAutoSetup.ps1   ── Mode=Setup ─▶ 9-phase pipeline
        │                        └─ Mode=Watch ─▶ hotswap watcher loop
        ▼
scripts\Modules\*.psm1          ── imported, each exports cohesive functions
        ▲
config\emulators.json           ── emulator + controller-vendor definitions
```

## Execution phases (Setup mode)

1. **Discovery** – `Get-RetroBatLayout` maps the root and reports which sub-trees exist.
2. **Hardware detection** – `Get-SystemHardware` queries CIM/WMI and registry, then
   `Resolve-PerformanceTier` scores CPU threads, RAM, VRAM, GPU vendor and storage
   into one of LowEnd / MidRange / HighEnd / FourK.
3. **Profiles** – `Save-Profiles` persists the four profiles to `system\profiles`;
   `Select-ProfileForHardware` picks one and clamps the target to the real display.
4. **Emulator detection** – `Get-InstalledEmulators` merges the known definitions
   with dynamic folder discovery so future emulators are found automatically.
5. **Auto-install** – `Get-MissingRequiredEmulators` → `Install-Emulator` resolves a
   download URL (GitHub Releases API or a direct official URL), downloads with
   retry/backoff, extracts (7-Zip or .NET ZIP), installs and verifies the executable.
6. **Graphics optimization** – `Invoke-EmulatorOptimization` dispatches each
   installed emulator to a format-aware writer that applies tier-appropriate
   resolution, internal scaling, anisotropic filtering, shader cache, VSync and a
   modern graphics backend.
7. **Controllers** – `Get-ConnectedControllers` identifies VID/PID and family;
   `Write-RetroArchControllerProfile` and `Write-EmulationStationInput` emit
   mappings + hotkeys.
8. **Validation & repair** – path, BIOS and config checks; safe repairs only.
9. **Git** – `Invoke-GitCommitAndPush` commits and pushes the resulting config.

## Configuration writers

Each emulator family stores configuration differently, so `ConfigParser.psm1`
provides format-specific primitives that **preserve unrelated content**:

| Format | Used by | Writer |
|--------|---------|--------|
| Sectioned INI | PCSX2, Dolphin, Yuzu, Citra, PPSSPP, DuckStation, melonDS, MAME | `Read-IniFile` / `Set-IniValue` / `Write-IniFile` |
| Flat `key = "value"` | RetroArch | `Set-FlatConfigValue -Quote` |
| Flat `key=value` | Redream, Flycast | `Set-FlatConfigValue` |
| TOML scalar | Xenia | `Set-TomlValue` |
| YAML scalar | RPCS3 | `Set-YamlScalar` |
| JSON | Ryujinx | native `ConvertFrom/To-Json` |
| XML | Cemu | `Set-XmlElement` |

Every writer calls `New-ConfigBackup` first, copying the original to
`Backups\<file>.<timestamp>.bak`.

## Performance tiers → emulator settings

`GraphicsOptimization.psm1` maps the resolved tier to per-emulator scale factors.
Examples:

| Emulator | LowEnd | MidRange | HighEnd | FourK |
|----------|--------|----------|---------|-------|
| PCSX2 `upscale_multiplier` | 1 | 2 | 4 | 6 |
| Dolphin `InternalResolution` | 1 | 3 | 5 | 6 |
| DuckStation `ResolutionScale` | 2 | 4 | 8 | 9 |
| PPSSPP `InternalResolution` | 2 | 5 | 8 | 10 |
| RPCS3 `Resolution Scale (%)` | 100 | 150 | 300 | 400 |
| Citra `resolution_factor` | 1 | 2 | 4 | 6 |

All write a modern backend (Vulkan where supported), 16x anisotropic filtering on
mid-tier and above, VSync on, and shader compilation tuned for stutter-free play.

## Hotswap watcher (Watch mode)

`Start-HotswapWatcher` polls connected controllers on an interval and computes a
stable signature (sorted VID:PID list). When the signature changes it reconfigures
on connect, or logs a clean state on full disconnect — without deleting existing
profiles.

## Safety model

- Destructive operations are limited to writing config files that were first
  backed up. ROMs, saves and BIOS are never touched.
- Folder *creation* is the only auto-repair for paths; nothing is removed.
- BIOS files are reported when missing but never downloaded.
- Git stderr is captured (not echoed) and auth failures short-circuit with a
  clear message and no credential exposure.
