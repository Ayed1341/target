# RetroBat Auto Setup

A complete, production-ready Windows automation suite for [RetroBat](https://www.retrobat.org/).
Drop it into your RetroBat root folder and run a single `.bat` to discover the
installation, detect and install emulators, optimize every compatible emulator
for 4K, auto-configure controllers (with hotswap support), validate and repair
the environment, and commit the result to git.

```
RetroBatAutoSetup.bat            <- run this (modular: launcher + scripts\ modules)
RetroBatAutoSetup-AllInOne.bat   <- OR run this (single self-contained file)
```

There are two equivalent ways to run the suite:

- **Modular** – `RetroBatAutoSetup.bat` calls `scripts\RetroBatAutoSetup.ps1`,
  which loads the PowerShell modules under `scripts\Modules\`. Easiest to read,
  extend and audit.
- **All-in-one** – `RetroBatAutoSetup-AllInOne.bat` is a single file with the
  entire engine (every module, the emulator database and the orchestrator)
  embedded after a `#PSPAYLOAD_BEGIN` marker. The batch part extracts the
  PowerShell payload to a temp file and runs it. Copy one file, run it. Both
  files accept the same flags (`/watch`, `/noinstall`, `/nogit`).

## What it does

| # | Capability | Where |
|---|------------|-------|
| 1 | **RetroBat discovery** – root, version, EmulationStation, emulators, BIOS, configs, controller profiles | `RetroBatDiscovery.psm1` |
| 2 | **Emulator auto-detection** – RetroArch, PCSX2, RPCS3, Xenia, Dolphin, Cemu, Yuzu, Ryujinx, PPSSPP, DuckStation, melonDS, MAME, Flycast, Citra, PrimeHack, Redream **+ dynamic discovery of any future emulator folder** | `EmulatorDetection.psm1` |
| 3 | **Auto-install missing emulators** – resolves official upstream / GitHub release downloads, extracts with bundled 7-Zip, verifies | `EmulatorInstall.psm1` |
| 4 | **4K graphics optimization** – per-emulator config writers: resolution, internal scaling, anisotropic filtering, shader cache, VSync, modern backend | `GraphicsOptimization.psm1` |
| 5 | **Controller auto-configuration** – VID/PID identification, family detection, RetroArch + EmulationStation mappings, hotkeys | `ControllerManagement.psm1` |
| 6 | **Hotswap support** – `/watch` mode reconfigures on connect, cleanly updates on disconnect | `RetroBatAutoSetup.ps1` (Watch mode) |
| 7 | **Profile generation** – LowEnd / MidRange / HighEnd / 4K profiles, auto-selected by hardware | `ProfileGeneration.psm1` |
| 8 | **Hardware detection** – CPU, GPU (+VRAM), RAM, storage type, display resolution & refresh | `Hardware.psm1` |
| 9 | **Validation & repair** – missing BIOS, broken paths, corrupt configs (restored from backup) | `ConfigValidation.psm1` |
| 10 | **Logging** – `Logs\Setup.log`, `EmulatorOptimization.log`, `ControllerSetup.log`, `Installation.log` with timestamps | `Logging.psm1` |
| 11 | **GitHub integration** – detects git/repo/branch, commits, pushes with retry; auth failures handled safely | `GitIntegration.psm1` |
| 12 | **Safety** – never deletes ROMs/saves/BIOS/user configs; timestamped backups before every change | `ConfigParser.psm1` |

## Project structure

```
RetroBatAutoSetup.bat              Main launcher (self-elevates, calls orchestrator)
config\
  emulators.json                   Data-driven emulator + controller-vendor database
scripts\
  RetroBatAutoSetup.ps1            Master orchestrator (Setup / Watch modes)
  Modules\
    Logging.psm1                   Timestamped multi-file logging
    ConfigParser.psm1              INI / flat-cfg / TOML / YAML / backup helpers
    Hardware.psm1                  Hardware detection + performance tiering
    RetroBatDiscovery.psm1         RetroBat root / version / path mapping
    EmulatorDetection.psm1         Known + dynamic emulator enumeration
    EmulatorInstall.psm1           Download / extract / verify installation
    GraphicsOptimization.psm1      Per-emulator 4K-aware config writers
    ControllerManagement.psm1      Controller detection, mapping, hotswap
    ProfileGeneration.psm1         Performance-profile generation & selection
    ConfigValidation.psm1          BIOS / path / config validation & repair
    GitIntegration.psm1            git detect / commit / push
docs\
  ARCHITECTURE.md                  Design notes
```

At runtime the suite also creates (inside the RetroBat root):

```
Logs\                              Setup / EmulatorOptimization / ControllerSetup / Installation logs
Backups\                           Timestamped backups of every modified config
system\profiles\                   Generated LowEnd/MidRange/HighEnd/FourK profile JSON
```

## Usage

Run from an **elevated** prompt (the launcher will request elevation automatically):

```bat
RetroBatAutoSetup.bat              :: full pipeline (discover, install, optimize, controllers, git)
RetroBatAutoSetup.bat /watch       :: controller hotswap watcher (runs until Ctrl+C)
RetroBatAutoSetup.bat /noinstall   :: skip auto-installing missing emulators
RetroBatAutoSetup.bat /nogit       :: skip the git commit/push phase
RetroBatAutoSetup.bat /noinstall /nogit
```

You can also run the orchestrator directly:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\RetroBatAutoSetup.ps1 -Mode Setup
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\RetroBatAutoSetup.ps1 -Mode Watch -WatchIntervalSeconds 5
```

## Requirements

- Windows 10 or Windows 11
- A RetroBat installation (the `.bat` should sit in the RetroBat root)
- Windows PowerShell 5.1 (built in) or PowerShell 7+ (`pwsh`) — the launcher prefers `pwsh` when present
- For auto-install: internet access; the bundled `system\tools\7za.exe` (RetroBat ships it) or 7-Zip for `.7z` archives
- For git push: a configured credential helper or `GITHUB_TOKEN` environment variable (never printed)

## Extending it

To support a **new emulator**, add an object to the `emulators` array in
`config\emulators.json` (folder, executables, configType, configFiles, optional
`download`). Detection and validation pick it up automatically. For full 4K
tuning, add a matching `Optimize-<Name>` writer in `GraphicsOptimization.psm1`
and a `case` in `Invoke-EmulatorOptimization`. Even without a writer, any new
emulator folder is auto-discovered and reported.

## Safety guarantees

- ROMs, saves and BIOS files are **never** deleted or modified.
- Every configuration file is **backed up** (timestamped) under `Backups\` before
  any change; corrupt configs are restored from the most recent backup.
- Missing BIOS files are **reported only** — never downloaded (copyright).
- Git credentials are never written to logs or the console.
