# ES-DE Auto Suite

A complete, production-ready Windows automation suite for **ES-DE (EmulationStation
Desktop Edition)**. You run **one file** — `ESDEAutoSuite.bat` — which embeds the
entire PowerShell engine (20 modules + 2 databases) after a payload marker,
extracts it to a temp file and executes it. Nothing else to install.

```
ESDEAutoSuite.bat          <- run this (single self-contained file)
esde/                      <- modular source (for maintenance / auditing)
```

## What it does

| Engine | Module |
|--------|--------|
| **ES-DE discovery** (install, settings, gamelists, downloaded_media, themes, custom_systems, collections, cache, ROM dir; portable + installed) | `EsdeDiscovery.psm1` |
| **RetroBat → ES-DE migration** (media folders + gamelist references mapped to ES-DE `downloaded_media`, matched to ROMs by stem) | `RetroBatMigration.psm1` |
| **Media classification** (gamelist tag → source folder → filename suffix → extension → image dimensions) | `MediaClassification.psm1` |
| **Media reorganization** (creates every ES-DE media folder, moves loose/misplaced files into the right subfolder) | `MediaReorganization.psm1` |
| **Metadata repair** (validates gamelist.xml, removes duplicate `<game>` entries, re-points broken media paths, strips dead references, writes clean XML) | `MetadataRepair.psm1` |
| **Duplicate detection** (SHA256; removes only redundant same-folder copies, after backup) | `DuplicateDetection.psm1` |
| **Missing-media analyzer** (per game: covers/screenshots/videos/marquees/fanart/titlescreens/manuals) | `MissingMedia.psm1` |
| **Media download** (ScreenScraper — official source; downloads only missing assets; credential-gated) | `MediaDownload.psm1` |
| **Emulator discovery + 4K graphics optimization** (GPU-vendor aware) | `EmulatorDetection.psm1`, `GraphicsOptimization.psm1` |
| **Hardware detection + profiles** (Low/Mid/High/Ultra/4K, auto-selected) | `Hardware.psm1`, `ProfileGeneration.psm1` |
| **Controller discovery + configuration + hotswap** (Xbox/PS/Nintendo/USB/Bluetooth; ES-DE input + RetroArch) | `ControllerManagement.psm1` |
| **BIOS validation** (report only, never deletes) | `MissingMedia.psm1` |
| **Cleanup** (orphan media quarantined to backups, empty folders removed) | `Cleanup.psm1` |
| **Backup engine** (timestamped, before every change; full restore) | `BackupEngine.psm1` |
| **Logging** (8 logs: Main/Migration/Media/Metadata/Optimization/Controllers/Downloads/Git) | `EsdeLogging.psm1` |
| **Reporting** (Full_Report.html/.json + Migration/Media/Metadata/Optimization/Controllers/Missing_Media/Duplicate) | `Reporting.psm1` |
| **Git integration** (detect repo/branch, commit, push; no credential exposure) | `GitIntegration.psm1` |

All output is forced to **English** (culture + `chcp 65001`) regardless of OS locale.

## Usage

Run as administrator (the launcher self-elevates):

```bat
ESDEAutoSuite.bat              :: full pipeline
ESDEAutoSuite.bat /dryrun      :: preview everything, write nothing
ESDEAutoSuite.bat /restore     :: roll back from the newest backups
ESDEAutoSuite.bat /watch       :: controller hotswap watcher
ESDEAutoSuite.bat /nomigrate   :: skip RetroBat migration
ESDEAutoSuite.bat /nodownload  :: skip ScreenScraper downloads
ESDEAutoSuite.bat /nooptimize  :: skip emulator graphics optimization
ESDEAutoSuite.bat /nogit       :: skip git commit/push
```

Outputs are written under `<your ES-DE data dir>\ESDEAutoSuite\`:

```
Logs\      Main.log, Migration.log, Media.log, Metadata.log,
           Optimization.log, Controllers.log, Downloads.log, Git.log
Reports\   Full_Report.html, Full_Report.json, Migration_Report.html,
           Media_Report.html, Metadata_Report.html, Optimization_Report.html,
           Controllers_Report.html, Missing_Media_Report.html, Duplicate_Report.html
Backups\   timestamped backups + orphaned_media\ quarantine
profiles\  Low/Mid/High/4K profile JSON
```

## Media download (ScreenScraper)

Scraping requires a ScreenScraper account. Provide credentials via environment
variables (never hard-coded, never logged):

```
SS_DEVID, SS_DEVPASSWORD   (developer API id/password)
SS_USER,  SS_PASSWORD      (your ScreenScraper member account)
```

If they are not set, the suite skips downloads and still generates the
missing-media report (use `/nodownload`, or ES-DE's built-in scraper).

## Safety guarantees

- **Never** deletes ROMs, saves, BIOS or controller profiles.
- Every file is **backed up** before modification; orphans are **quarantined**
  (moved into `Backups\orphaned_media`), never hard-deleted.
- Migration **copies** (never moves) source media — your RetroBat tree is untouched.
- Identical files are skipped; differing destinations are backed up first.
- Missing BIOS is **reported only** (copyright).
- `/dryrun` writes nothing at all.

## Extending it

Add new media mappings (gamelist tags, source folders, filename suffixes) in
`esde/config/esde-media.json`; add emulators in `esde/config/emulators.json`.
After editing, regenerate the single-file launcher from the modular source.
