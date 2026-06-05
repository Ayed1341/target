@echo off
setlocal EnableExtensions EnableDelayedExpansion

REM =========================================================================
REM  ES-DE Auto Suite - ALL-IN-ONE single-file launcher.
REM  Self-contained: all engines + databases are embedded below the payload
REM  marker. Place this .bat anywhere (ideally near your ES-DE folder) and run.
REM
REM  Usage:
REM    ESDEAutoSuite.bat                Full pipeline (discover/migrate/optimize).
REM    ESDEAutoSuite.bat /dryrun        Preview everything, write nothing.
REM    ESDEAutoSuite.bat /restore       Roll back from the newest backups.
REM    ESDEAutoSuite.bat /watch         Controller hotswap watcher.
REM    ESDEAutoSuite.bat /nomigrate     Skip RetroBat media migration.
REM    ESDEAutoSuite.bat /nodownload    Skip ScreenScraper downloads.
REM    ESDEAutoSuite.bat /nooptimize    Skip emulator graphics optimization.
REM    ESDEAutoSuite.bat /nogit         Skip git commit/push.
REM =========================================================================

set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"
title ES-DE Auto Suite
chcp 65001 >nul 2>&1

echo.
echo  ============================================================
echo    ES-DE Auto Suite (All-in-One)
echo    Root: %ROOT%
echo  ============================================================
echo.

REM --- Self-elevate to Administrator, forwarding all arguments --------------
net session >nul 2>&1
if %errorlevel% NEQ 0 (
    echo [INFO] Requesting administrator privileges...
    set "ELEV_VBS=%TEMP%\esde_elev_%RANDOM%.vbs"
    > "!ELEV_VBS!" echo Set UAC = CreateObject^("Shell.Application"^)
    >> "!ELEV_VBS!" echo UAC.ShellExecute "%~f0", "%*", "%ROOT%", "runas", 1
    cscript //nologo "!ELEV_VBS!"
    del "!ELEV_VBS!" >nul 2>&1
    exit /b 0
)

set "PWSH="
where pwsh.exe >nul 2>&1 && set "PWSH=pwsh.exe"
if not defined PWSH ( where powershell.exe >nul 2>&1 && set "PWSH=powershell.exe" )
if not defined PWSH ( echo [ERROR] PowerShell was not found. & pause & exit /b 3 )

set "MODE=Setup"
set "EXTRA="
:parse
if "%~1"=="" goto run
if /i "%~1"=="/watch"      set "MODE=Watch"
if /i "%~1"=="-watch"      set "MODE=Watch"
if /i "%~1"=="/restore"    set "MODE=Restore"
if /i "%~1"=="-restore"    set "MODE=Restore"
if /i "%~1"=="/dryrun"     set "EXTRA=!EXTRA! -DryRun"
if /i "%~1"=="-dryrun"     set "EXTRA=!EXTRA! -DryRun"
if /i "%~1"=="/hashroms"   set "EXTRA=!EXTRA! -HashRoms"
if /i "%~1"=="/genmedia"   set "EXTRA=!EXTRA! -GenerateMedia"
if /i "%~1"=="/tune"       set "EXTRA=!EXTRA! -TuneEsde"
if /i "%~1"=="/enrich"     set "EXTRA=!EXTRA! -EnrichMeta"
if /i "%~1"=="/onegame"    set "EXTRA=!EXTRA! -OneGameOneRegion"
if /i "%~1"=="/themes"     set "EXTRA=!EXTRA! -Themes"
if /i "%~1"=="/schedule"   set "EXTRA=!EXTRA! -Schedule"
if /i "%~1"=="/shortcut"   set "EXTRA=!EXTRA! -Shortcut"
if /i "%~1"=="/autofav"    set "EXTRA=!EXTRA! -AutoFav"
if /i "%~1"=="/compress"   set "EXTRA=!EXTRA! -Compress"
if /i "%~1"=="/nomigrate"  set "EXTRA=!EXTRA! -SkipMigration"
if /i "%~1"=="-nomigrate"  set "EXTRA=!EXTRA! -SkipMigration"
if /i "%~1"=="/nodownload" set "EXTRA=!EXTRA! -SkipDownload"
if /i "%~1"=="-nodownload" set "EXTRA=!EXTRA! -SkipDownload"
if /i "%~1"=="/nooptimize" set "EXTRA=!EXTRA! -SkipOptimize"
if /i "%~1"=="-nooptimize" set "EXTRA=!EXTRA! -SkipOptimize"
if /i "%~1"=="/nogit"      set "EXTRA=!EXTRA! -SkipGit"
if /i "%~1"=="-nogit"      set "EXTRA=!EXTRA! -SkipGit"
shift
goto parse

:run
set "ESDE_LAUNCHER=%~f0"
echo [INFO] Running. Mode: !MODE!
echo.
"%PWSH%" -NoProfile -ExecutionPolicy Bypass -Command "$self=[IO.File]::ReadAllText('%~f0'); $m='#PSPAYLOAD_BEGIN'; $i=$self.LastIndexOf($m); if($i -lt 0){ Write-Host 'payload marker missing' -ForegroundColor Red; exit 9 }; $code=$self.Substring($i+$m.Length); $tmp=Join-Path $env:TEMP ('ESDE_'+[Guid]::NewGuid().ToString('N')+'.ps1'); [IO.File]::WriteAllText($tmp,$code,(New-Object Text.UTF8Encoding($false))); try { & $tmp -EsdeRoot '%ROOT%' -Mode %MODE%%EXTRA% } finally { Remove-Item $tmp -Force -ErrorAction SilentlyContinue }"
set "RC=%errorlevel%"
echo.
if "%RC%"=="0" ( echo [DONE] Finished. See the ESDEAutoSuite\Logs and \Reports folders inside your ES-DE data dir. ) else ( echo [WARN] Exited with code %RC%. )
if /i not "!MODE!"=="Watch" ( echo. & pause )
endlocal & exit /b %RC%

#PSPAYLOAD_BEGIN
# === ES-DE Auto Suite - ALL-IN-ONE (generated from verified modules) ===
[CmdletBinding()]
param(
    [string] $EsdeRoot,
    [string] $RetroBatRoot,
    [ValidateSet("Setup","Restore","Watch")] [string] $Mode = "Setup",
    [switch] $SkipMigration,
    [switch] $SkipDownload,
    [switch] $SkipOptimize,
    [switch] $SkipGit,
    [switch] $DryRun,
    [switch] $HashRoms,
    [switch] $GenerateMedia,
    [switch] $TuneEsde,
    [switch] $EnrichMeta,
    [switch] $OneGameOneRegion,
    [switch] $Shortcut,
    [switch] $Compress,
    [switch] $AutoFav,
    [switch] $Schedule,
    [switch] $Themes,
    [int] $WatchIntervalSeconds = 5
)
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
try {
  $enUS=[System.Globalization.CultureInfo]::GetCultureInfo("en-US")
  [System.Threading.Thread]::CurrentThread.CurrentCulture=$enUS
  [System.Threading.Thread]::CurrentThread.CurrentUICulture=$enUS
  [System.Globalization.CultureInfo]::DefaultThreadCurrentCulture=$enUS
  [System.Globalization.CultureInfo]::DefaultThreadCurrentUICulture=$enUS
} catch {}

$script:EmbeddedMediaJson = @'
{
    "schemaVersion": 1,
    "description": "ES-DE media-type definitions and RetroBat->ES-DE migration mapping. Drives the discovery, classification, migration and reorganization engines.",

    "esdeMediaFolders": [
        "3dboxes",
        "backcovers",
        "covers",
        "fanart",
        "manuals",
        "marquees",
        "miximages",
        "physicalmedia",
        "screenshots",
        "titlescreens",
        "videos"
    ],

    "gamelistTagToEsdeFolder": {
        "image": "covers",
        "thumbnail": "covers",
        "boxart": "covers",
        "box2dfront": "covers",
        "cover": "covers",
        "boxback": "backcovers",
        "box2dback": "backcovers",
        "backcover": "backcovers",
        "box3d": "3dboxes",
        "box3dfront": "3dboxes",
        "marquee": "marquees",
        "wheel": "marquees",
        "logo": "marquees",
        "fanart": "fanart",
        "background": "fanart",
        "video": "videos",
        "manual": "manuals",
        "titleshot": "titlescreens",
        "titlescreen": "titlescreens",
        "screenshot": "screenshots",
        "ss": "screenshots",
        "mix": "miximages",
        "miximage": "miximages",
        "cartridge": "physicalmedia",
        "support": "physicalmedia",
        "disc": "physicalmedia",
        "physicalmedia": "physicalmedia"
    },

    "sourceFolderToEsdeFolder": {
        "images": "covers",
        "boxart": "covers",
        "box2dfront": "covers",
        "covers": "covers",
        "thumbnails": "covers",
        "downloaded_images": "covers",
        "boxback": "backcovers",
        "box2dback": "backcovers",
        "backcovers": "backcovers",
        "box3d": "3dboxes",
        "3dboxes": "3dboxes",
        "marquees": "marquees",
        "marquee": "marquees",
        "wheels": "marquees",
        "wheel": "marquees",
        "logos": "marquees",
        "fanart": "fanart",
        "fanarts": "fanart",
        "backgrounds": "fanart",
        "videos": "videos",
        "video": "videos",
        "downloaded_videos": "videos",
        "manuals": "manuals",
        "manual": "manuals",
        "titles": "titlescreens",
        "titleshots": "titlescreens",
        "titlescreens": "titlescreens",
        "screenshots": "screenshots",
        "screenshot": "screenshots",
        "ss": "screenshots",
        "mixes": "miximages",
        "miximages": "miximages",
        "supports": "physicalmedia",
        "support": "physicalmedia",
        "cartridges": "physicalmedia",
        "cartridge": "physicalmedia",
        "discs": "physicalmedia",
        "physicalmedia": "physicalmedia"
    },

    "filenameSuffixToEsdeFolder": {
        "-image": "covers",
        "-boxart": "covers",
        "-box2dfront": "covers",
        "-cover": "covers",
        "-thumb": "covers",
        "-thumbnail": "covers",
        "-boxback": "backcovers",
        "-box2dback": "backcovers",
        "-backcover": "backcovers",
        "-box3d": "3dboxes",
        "-marquee": "marquees",
        "-wheel": "marquees",
        "-logo": "marquees",
        "-fanart": "fanart",
        "-background": "fanart",
        "-video": "videos",
        "-manual": "manuals",
        "-title": "titlescreens",
        "-titleshot": "titlescreens",
        "-titlescreen": "titlescreens",
        "-screenshot": "screenshots",
        "-ss": "screenshots",
        "-mix": "miximages",
        "-miximage": "miximages",
        "-cart": "physicalmedia",
        "-cartridge": "physicalmedia",
        "-disc": "physicalmedia",
        "-support": "physicalmedia"
    },

    "mediaExtensions": {
        "image": [ ".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp" ],
        "video": [ ".mp4", ".webm", ".avi", ".mkv", ".mov" ],
        "manual": [ ".pdf", ".cbz", ".cbr" ]
    },

    "videoFolders": [ "videos" ],
    "manualFolders": [ "manuals" ],

    "systemEmulators": {
        "nes": [ "retroarch", "mesen" ],
        "snes": [ "retroarch", "snes9x" ],
        "n64": [ "retroarch", "mupen64", "project64" ],
        "gc": [ "dolphin" ],
        "gamecube": [ "dolphin" ],
        "wii": [ "dolphin" ],
        "wiiu": [ "cemu" ],
        "switch": [ "yuzu", "ryujinx" ],
        "gb": [ "retroarch", "mgba" ],
        "gba": [ "retroarch", "mgba" ],
        "gbc": [ "retroarch", "mgba" ],
        "nds": [ "melonds", "retroarch" ],
        "3ds": [ "citra" ],
        "psx": [ "duckstation", "retroarch" ],
        "ps2": [ "pcsx2" ],
        "ps3": [ "rpcs3" ],
        "psp": [ "ppsspp", "retroarch" ],
        "psvita": [ "vita3k" ],
        "vita": [ "vita3k" ],
        "xbox": [ "xemu", "cxbx-reloaded" ],
        "xbox360": [ "xenia" ],
        "dreamcast": [ "flycast", "redream" ],
        "saturn": [ "retroarch", "kronos", "ssf" ],
        "segacd": [ "retroarch" ],
        "genesis": [ "retroarch", "kega-fusion" ],
        "megadrive": [ "retroarch", "kega-fusion" ],
        "mastersystem": [ "retroarch" ],
        "gamegear": [ "retroarch" ],
        "arcade": [ "retroarch", "mame", "fbneo" ],
        "mame": [ "mame", "retroarch" ],
        "naomi": [ "flycast" ],
        "atari2600": [ "retroarch", "stella" ],
        "atari5200": [ "retroarch" ],
        "atari7800": [ "retroarch" ],
        "c64": [ "retroarch" ],
        "amiga": [ "retroarch", "winuae" ],
        "amigacd32": [ "retroarch", "winuae" ],
        "3do": [ "retroarch" ],
        "pcengine": [ "retroarch" ],
        "pcenginecd": [ "retroarch" ],
        "epic": [ "steam" ],
        "steam": [ "steam" ]
    },

    "systemExtensions": {
        "nes": [ ".nes", ".zip", ".7z", ".unif", ".fds" ],
        "famicom": [ ".nes", ".zip", ".7z", ".fds" ],
        "snes": [ ".sfc", ".smc", ".zip", ".7z", ".bs" ],
        "n64": [ ".n64", ".z64", ".v64", ".zip", ".7z" ],
        "gc": [ ".iso", ".gcm", ".gcz", ".rvz", ".ciso" ],
        "wii": [ ".iso", ".wbfs", ".rvz", ".gcz", ".wad" ],
        "wiiu": [ ".wua", ".rpx", ".wux" ],
        "switch": [ ".nsp", ".xci", ".nca", ".nso" ],
        "gb": [ ".gb", ".zip", ".7z" ],
        "gba": [ ".gba", ".zip", ".7z" ],
        "gbc": [ ".gbc", ".gb", ".zip", ".7z" ],
        "nds": [ ".nds", ".zip", ".7z" ],
        "3ds": [ ".3ds", ".cia", ".cci", ".cxi" ],
        "psx": [ ".chd", ".cue", ".pbp", ".m3u", ".ccd", ".iso" ],
        "ps2": [ ".chd", ".iso", ".cso", ".gz", ".bin" ],
        "ps3": [ ".ps3", ".iso" ],
        "psp": [ ".iso", ".cso", ".pbp", ".chd" ],
        "dreamcast": [ ".chd", ".gdi", ".cdi", ".cue" ],
        "saturn": [ ".chd", ".cue", ".iso", ".ccd", ".mds" ],
        "genesis": [ ".md", ".gen", ".bin", ".smd", ".zip", ".7z" ],
        "megadrive": [ ".md", ".gen", ".bin", ".smd", ".zip", ".7z" ],
        "atari2600": [ ".a26", ".bin", ".zip", ".7z" ],
        "atari5200": [ ".a52", ".bin", ".zip", ".7z" ],
        "c64": [ ".d64", ".t64", ".crt", ".prg", ".zip", ".7z" ],
        "amiga": [ ".adf", ".hdf", ".lha", ".zip", ".7z", ".ipf" ],
        "amigacd32": [ ".chd", ".cue", ".iso" ],
        "3do": [ ".chd", ".cue", ".iso" ],
        "arcade": [ ".zip", ".7z", ".chd" ],
        "mame": [ ".zip", ".7z", ".chd" ],
        "xbox": [ ".iso", ".xbe" ],
        "xbox360": [ ".iso", ".xex", ".god" ]
    },

    "biosRequirements": [
        { "file": "scph5500.bin", "system": "PlayStation (JP)" },
        { "file": "scph5501.bin", "system": "PlayStation (US)" },
        { "file": "scph5502.bin", "system": "PlayStation (EU)" },
        { "file": "dc_boot.bin",  "system": "Dreamcast" },
        { "file": "dc_flash.bin", "system": "Dreamcast" },
        { "file": "bios7.bin",    "system": "Nintendo DS" },
        { "file": "bios9.bin",    "system": "Nintendo DS" },
        { "file": "firmware.bin", "system": "Nintendo DS" },
        { "file": "gba_bios.bin", "system": "Game Boy Advance" },
        { "file": "syscard3.pce", "system": "PC Engine CD" },
        { "file": "saturn_bios.bin", "system": "Sega Saturn" }
    ]
}

'@

$script:EmbeddedEmuJson = @'
{
    "schemaVersion": 2,
    "description": "RetroBat emulator definition database. Drives detection, auto-install and 4K optimization. Add new objects to the 'emulators' array to support future emulators without touching script code.",
    "emulators": [
        {
            "id": "retroarch",
            "displayName": "RetroArch",
            "folder": "retroarch",
            "executables": [ "retroarch.exe" ],
            "configType": "retroarch",
            "configFiles": [ "retroarch.cfg" ],
            "systems": [ "multi" ],
            "supports4K": true,
            "download": {
                "type": "direct",
                "url": "https://buildbot.libretro.com/stable/1.19.1/windows/x86_64/RetroArch.7z",
                "archive": "7z",
                "stripRootFolder": true
            }
        },
        {
            "id": "pcsx2",
            "displayName": "PCSX2 (PlayStation 2)",
            "folder": "pcsx2",
            "executables": [ "pcsx2-qt.exe", "pcsx2x64.exe", "pcsx2.exe" ],
            "configType": "ini",
            "configFiles": [ "inis/PCSX2.ini" ],
            "systems": [ "ps2" ],
            "supports4K": true,
            "download": {
                "type": "github",
                "repo": "PCSX2/pcsx2",
                "assetPattern": "windows-x64-Qt.7z$",
                "archive": "7z",
                "stripRootFolder": true
            }
        },
        {
            "id": "rpcs3",
            "displayName": "RPCS3 (PlayStation 3)",
            "folder": "rpcs3",
            "executables": [ "rpcs3.exe" ],
            "configType": "yaml",
            "configFiles": [ "config.yml" ],
            "systems": [ "ps3" ],
            "supports4K": true,
            "download": {
                "type": "github",
                "repo": "RPCS3/rpcs3-binaries-win",
                "assetPattern": "win64.7z$",
                "archive": "7z",
                "stripRootFolder": false
            }
        },
        {
            "id": "xenia",
            "displayName": "Xenia (Xbox 360)",
            "folder": "xenia",
            "executables": [ "xenia_canary.exe", "xenia.exe" ],
            "configType": "toml",
            "configFiles": [ "xenia-canary.config.toml", "xenia.config.toml" ],
            "systems": [ "xbox360" ],
            "supports4K": true,
            "download": {
                "type": "github",
                "repo": "xenia-canary/xenia-canary-releases",
                "assetPattern": "windows.zip$",
                "archive": "zip",
                "stripRootFolder": false
            }
        },
        {
            "id": "dolphin",
            "displayName": "Dolphin (GameCube / Wii)",
            "folder": "dolphin-emu",
            "executables": [ "Dolphin.exe", "DolphinR.exe" ],
            "configType": "ini",
            "configFiles": [ "User/Config/GFX.ini", "User/Config/Dolphin.ini" ],
            "systems": [ "gc", "wii" ],
            "supports4K": true,
            "download": {
                "type": "none"
            }
        },
        {
            "id": "cemu",
            "displayName": "Cemu (Wii U)",
            "folder": "cemu",
            "executables": [ "Cemu.exe" ],
            "configType": "xml",
            "configFiles": [ "settings.xml" ],
            "systems": [ "wiiu" ],
            "supports4K": true,
            "download": {
                "type": "github",
                "repo": "cemu-project/Cemu",
                "assetPattern": "windows-x64.zip$",
                "archive": "zip",
                "stripRootFolder": true
            }
        },
        {
            "id": "yuzu",
            "displayName": "Yuzu / compatible (Switch)",
            "folder": "yuzu",
            "executables": [ "yuzu.exe" ],
            "configType": "ini",
            "configFiles": [ "user/config/qt-config.ini" ],
            "systems": [ "switch" ],
            "supports4K": true,
            "download": {
                "type": "none"
            }
        },
        {
            "id": "ryujinx",
            "displayName": "Ryujinx (Switch)",
            "folder": "ryujinx",
            "executables": [ "Ryujinx.exe", "Ryujinx.Ava.exe" ],
            "configType": "json",
            "configFiles": [ "portable/Config.json" ],
            "systems": [ "switch" ],
            "supports4K": true,
            "download": {
                "type": "none"
            }
        },
        {
            "id": "ppsspp",
            "displayName": "PPSSPP (PSP)",
            "folder": "ppsspp",
            "executables": [ "PPSSPPWindows64.exe", "PPSSPPWindows.exe" ],
            "configType": "ini",
            "configFiles": [ "memstick/PSP/SYSTEM/ppsspp.ini" ],
            "systems": [ "psp" ],
            "supports4K": true,
            "download": {
                "type": "direct",
                "url": "https://www.ppsspp.org/files/1_17_1/ppsspp_win.zip",
                "archive": "zip",
                "stripRootFolder": false
            }
        },
        {
            "id": "duckstation",
            "displayName": "DuckStation (PlayStation 1)",
            "folder": "duckstation",
            "executables": [ "duckstation-qt-x64-ReleaseLTCG.exe", "duckstation.exe" ],
            "configType": "ini",
            "configFiles": [ "settings.ini" ],
            "systems": [ "psx" ],
            "supports4K": true,
            "download": {
                "type": "github",
                "repo": "stenzek/duckstation",
                "assetPattern": "windows-x64-release.zip$",
                "archive": "zip",
                "stripRootFolder": false
            }
        },
        {
            "id": "melonds",
            "displayName": "melonDS (Nintendo DS)",
            "folder": "melonds",
            "executables": [ "melonDS.exe" ],
            "configType": "ini",
            "configFiles": [ "melonDS.ini" ],
            "systems": [ "nds" ],
            "supports4K": true,
            "download": {
                "type": "github",
                "repo": "melonDS-emu/melonDS",
                "assetPattern": "(?i)windows.*\\.zip$",
                "archive": "zip",
                "stripRootFolder": false
            }
        },
        {
            "id": "mame",
            "displayName": "MAME (Arcade)",
            "folder": "mame",
            "executables": [ "mame.exe", "mame64.exe" ],
            "configType": "ini",
            "configFiles": [ "ini/mame.ini" ],
            "systems": [ "arcade", "mame" ],
            "supports4K": false,
            "download": {
                "type": "github",
                "repo": "mamedev/mame",
                "assetPattern": "(?i)(x64|64bit)\\.exe$",
                "archive": "sfx",
                "stripRootFolder": false
            }
        },
        {
            "id": "flycast",
            "displayName": "Flycast (Dreamcast / NAOMI)",
            "folder": "flycast",
            "executables": [ "flycast.exe" ],
            "configType": "ini",
            "configFiles": [ "emu.cfg" ],
            "systems": [ "dreamcast", "naomi" ],
            "supports4K": true,
            "download": {
                "type": "github",
                "repo": "flyinghead/flycast",
                "assetPattern": "(?i)windows.*\\.zip$",
                "archive": "zip",
                "stripRootFolder": false
            }
        },
        {
            "id": "citra",
            "displayName": "Citra / compatible (Nintendo 3DS)",
            "folder": "citra",
            "executables": [ "citra-qt.exe", "citra.exe" ],
            "configType": "ini",
            "configFiles": [ "user/config/qt-config.ini" ],
            "systems": [ "3ds" ],
            "supports4K": true,
            "download": {
                "type": "none"
            }
        },
        {
            "id": "primehack",
            "displayName": "PrimeHack (Metroid Prime)",
            "folder": "primehack",
            "executables": [ "DolphinWX.exe", "primehack.exe", "Dolphin.exe" ],
            "configType": "ini",
            "configFiles": [ "User/Config/GFX.ini", "User/Config/Dolphin.ini" ],
            "systems": [ "gc", "wii" ],
            "supports4K": true,
            "download": {
                "type": "none"
            }
        },
        {
            "id": "redream",
            "displayName": "Redream (Dreamcast)",
            "folder": "redream",
            "executables": [ "redream.exe" ],
            "configType": "ini",
            "configFiles": [ "redream.cfg" ],
            "systems": [ "dreamcast" ],
            "supports4K": true,
            "download": {
                "type": "direct",
                "url": "https://redream.io/download/redream.x86_64-windows-v1.5.0.zip",
                "archive": "zip",
                "stripRootFolder": false
            }
        }
    ],
    "controllerVendors": {
        "045E": "Microsoft (Xbox)",
        "054C": "Sony (PlayStation)",
        "057E": "Nintendo",
        "28DE": "Valve (Steam)",
        "2DC8": "8BitDo",
        "0F0D": "Hori",
        "146B": "BigBen / Nacon",
        "0079": "DragonRise / Generic USB",
        "1532": "Razer",
        "24C6": "PowerA",
        "0E6F": "PDP",
        "1689": "Razer Onza",
        "2563": "ShanWan / Generic",
        "20D6": "PowerA / BDA",
        "0E8F": "GreenAsia / Generic",
        "11C0": "Betop",
        "1A34": "Afterglow / PDP",
        "06A3": "Saitek",
        "044F": "ThrustMaster",
        "0738": "Mad Catz",
        "1BAD": "Mad Catz (Rock Band)",
        "045B": "Hitachi",
        "0810": "Personal Communication Systems",
        "0B05": "ASUS (ROG)",
        "1038": "SteelSeries",
        "1B1C": "Corsair",
        "320F": "Generic / 8BitDo-compatible",
        "048D": "ITE (built-in HID)",
        "045A": "Logitech",
        "046D": "Logitech",
        "0955": "NVIDIA (Shield)",
        "18D1": "Google (Stadia)",
        "2DC8 ": "8BitDo",
        "3537": "GuliKit",
        "3250": "GameSir",
        "3285": "Nacon",
        "0C12": "Zeroplus",
        "12BD": "Generic USB Gamepad",
        "25F0": "ShanWan / SZMY-Power",
        "2C22": "Qanba (Arcade Stick)",
        "0D62": "Darfon",
        "1345": "Sino Lite / Generic"
    }
}

'@

# ----- module: EsdeLogging -----
<#
.SYNOPSIS
    Centralized logging for the ES-DE automation suite (8 log files).
#>

Set-StrictMode -Version Latest

$script:LogRoot     = $null
$script:LogTargets  = @{}
$script:Initialized = $false

$script:LogFileMap = [ordered]@{
    'Main'         = 'Main.log'
    'Migration'    = 'Migration.log'
    'Media'        = 'Media.log'
    'Metadata'     = 'Metadata.log'
    'Optimization' = 'Optimization.log'
    'Controllers'  = 'Controllers.log'
    'Downloads'    = 'Downloads.log'
    'Git'          = 'Git.log'
}

function Initialize-EsdeLogging {
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][string] $LogRoot)

    if (-not (Test-Path -LiteralPath $LogRoot)) {
        New-Item -Path $LogRoot -ItemType Directory -Force | Out-Null
    }
    $script:LogRoot    = $LogRoot
    $script:LogTargets = @{}
    foreach ($key in $script:LogFileMap.Keys) {
        $path = Join-Path $LogRoot $script:LogFileMap[$key]
        $script:LogTargets[$key] = $path
        if (-not (Test-Path -LiteralPath $path)) { New-Item -Path $path -ItemType File -Force | Out-Null }
    }
    $script:Initialized = $true
    $header = "================ ES-DE Auto Suite session $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') ================"
    foreach ($key in $script:LogFileMap.Keys) {
        Add-Content -LiteralPath $script:LogTargets[$key] -Value $header -Encoding UTF8
    }
}

function Write-EsdeLog {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true, Position = 0)] [string] $Message,
        [ValidateSet('INFO','WARN','ERROR','SUCCESS','DEBUG')] [string] $Level = 'INFO',
        [ValidateSet('Main','Migration','Media','Metadata','Optimization','Controllers','Downloads','Git')]
        [string] $Category = 'Main',
        [switch] $NoConsole
    )

    $timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss.fff'
    $line      = '[{0}] [{1,-7}] {2}' -f $timestamp, $Level, $Message

    if ($script:Initialized) {
        $targets = New-Object System.Collections.Generic.List[string]
        $targets.Add($script:LogTargets[$Category])
        if (($Level -eq 'ERROR' -or $Level -eq 'WARN') -and $Category -ne 'Main') {
            $targets.Add($script:LogTargets['Main'])
        }
        foreach ($t in ($targets | Select-Object -Unique)) {
            try { Add-Content -LiteralPath $t -Value $line -Encoding UTF8 -ErrorAction Stop }
            catch { Write-Host "LOGGING FAILURE -> $($_.Exception.Message)" -ForegroundColor Red }
        }
    }

    if (-not $NoConsole) {
        $color = switch ($Level) {
            'INFO' {'Gray'} 'WARN' {'Yellow'} 'ERROR' {'Red'} 'SUCCESS' {'Green'} 'DEBUG' {'DarkGray'} default {'White'}
        }
        Write-Host $line -ForegroundColor $color
    }
}

function Write-EsdeSection {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string] $Title,
        [ValidateSet('Main','Migration','Media','Metadata','Optimization','Controllers','Downloads','Git')]
        [string] $Category = 'Main'
    )
    $bar = '-' * 72
    Write-EsdeLog -Message $bar -Level INFO -Category $Category
    Write-EsdeLog -Message ("  {0}" -f $Title.ToUpper()) -Level INFO -Category $Category
    Write-EsdeLog -Message $bar -Level INFO -Category $Category
}

function Get-EsdeLogRoot { return $script:LogRoot }

# ----- module: ConfigParser -----
<#
.SYNOPSIS
    Configuration parsing / writing module.
.DESCRIPTION
    Implements robust readers and writers for the configuration formats used by
    RetroBat and its emulators:
      * INI / sectioned key=value (PCSX2, Dolphin, Citra, Yuzu, MAME, melonDS...)
      * Flat "key = value" cfg files (RetroArch, Flycast, Redream)
      * TOML scalar keys (Xenia)
      * Simple YAML scalar keys (RPCS3)
      * JSON (Ryujinx)
    All writers create timestamped backups before modifying a file and preserve
    unrelated content. No setting is removed; values are added or updated in place.
#>

Set-StrictMode -Version Latest

function New-ConfigBackup {
    <#
    .SYNOPSIS
        Creates a timestamped backup of a file inside a sibling 'Backups' folder.
    .OUTPUTS
        Path to the backup file, or $null if the source did not exist.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string] $Path,

        [Parameter(Mandatory = $true)]
        [string] $BackupRoot
    )

    if (-not (Test-Path -LiteralPath $Path)) { return $null }

    if (-not (Test-Path -LiteralPath $BackupRoot)) {
        New-Item -Path $BackupRoot -ItemType Directory -Force | Out-Null
    }

    $stamp    = Get-Date -Format 'yyyyMMdd_HHmmss'
    $leaf     = Split-Path -Path $Path -Leaf
    $backupTo = Join-Path $BackupRoot ("{0}.{1}.bak" -f $leaf, $stamp)
    Copy-Item -LiteralPath $Path -Destination $backupTo -Force
    return $backupTo
}

function Read-IniFile {
    <#
    .SYNOPSIS
        Parses a sectioned INI file into an ordered hashtable of sections.
    .OUTPUTS
        [ordered] hashtable: section name -> [ordered] hashtable of key/value.
        Keys outside any section are stored under the '' (empty) section.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string] $Path
    )

    $result  = [ordered]@{}
    $current = ''
    $result[$current] = [ordered]@{}

    if (-not (Test-Path -LiteralPath $Path)) { return $result }

    foreach ($raw in (Get-Content -LiteralPath $Path -Encoding UTF8)) {
        $line = $raw.Trim()
        if ($line.Length -eq 0) { continue }
        if ($line.StartsWith('#') -or $line.StartsWith(';')) { continue }

        if ($line.StartsWith('[') -and $line.EndsWith(']')) {
            $current = $line.Substring(1, $line.Length - 2).Trim()
            if (-not $result.Contains($current)) { $result[$current] = [ordered]@{} }
            continue
        }

        $idx = $line.IndexOf('=')
        if ($idx -lt 0) { continue }
        $key = $line.Substring(0, $idx).Trim()
        $val = $line.Substring($idx + 1).Trim()
        $result[$current][$key] = $val
    }

    return $result
}

function Write-IniFile {
    <#
    .SYNOPSIS
        Serializes a section hashtable (as produced by Read-IniFile) back to disk.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string] $Path,

        [Parameter(Mandatory = $true)]
        [System.Collections.Specialized.OrderedDictionary] $Data
    )

    $dir = Split-Path -Path $Path -Parent
    if ($dir -and -not (Test-Path -LiteralPath $dir)) {
        New-Item -Path $dir -ItemType Directory -Force | Out-Null
    }

    $sb = New-Object System.Text.StringBuilder

    # Global (section-less) keys first.
    if ($Data.Contains('') -and $Data[''].Count -gt 0) {
        foreach ($k in $Data[''].Keys) {
            [void]$sb.AppendLine(('{0} = {1}' -f $k, $Data[''][$k]))
        }
        [void]$sb.AppendLine()
    }

    foreach ($section in $Data.Keys) {
        if ($section -eq '') { continue }
        [void]$sb.AppendLine(('[{0}]' -f $section))
        foreach ($k in $Data[$section].Keys) {
            [void]$sb.AppendLine(('{0} = {1}' -f $k, $Data[$section][$k]))
        }
        [void]$sb.AppendLine()
    }

    [System.IO.File]::WriteAllText($Path, $sb.ToString(), (New-Object System.Text.UTF8Encoding($false)))
}

function Set-IniValue {
    <#
    .SYNOPSIS
        Sets or updates a single key within a section of an INI structure.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [System.Collections.Specialized.OrderedDictionary] $Data,
        # AllowEmptyString: emulators such as melonDS store keys with no section
        # (the global/section-less area), so an empty section name is valid.
        [Parameter(Mandatory = $true)] [AllowEmptyString()] [string] $Section,
        [Parameter(Mandatory = $true)] [string] $Key,
        [Parameter(Mandatory = $true)] [AllowEmptyString()] [string] $Value
    )

    if (-not $Data.Contains($Section)) { $Data[$Section] = [ordered]@{} }
    $Data[$Section][$Key] = $Value
}

function Set-FlatConfigValue {
    <#
    .SYNOPSIS
        Updates a "key = value" or "key value" entry in a flat config file,
        preserving all other lines. Used for RetroArch / Flycast / Redream.
    .PARAMETER Quote
        When set, wraps the value in double quotes (RetroArch style).
    .PARAMETER Separator
        The token between key and value (default ' = ').
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)] [string] $Path,
        [Parameter(Mandatory = $true)] [string] $Key,
        [Parameter(Mandatory = $true)] [string] $Value,
        [switch] $Quote,
        [string] $Separator = ' = '
    )

    $dir = Split-Path -Path $Path -Parent
    if ($dir -and -not (Test-Path -LiteralPath $dir)) {
        New-Item -Path $dir -ItemType Directory -Force | Out-Null
    }

    $renderedValue = if ($Quote) { '"{0}"' -f $Value } else { $Value }
    $newLine       = '{0}{1}{2}' -f $Key, $Separator, $renderedValue

    $lines = @()
    if (Test-Path -LiteralPath $Path) {
        $lines = @(Get-Content -LiteralPath $Path -Encoding UTF8)
    }

    $found   = $false
    # Match key at start of line followed by optional space then '=' (or space).
    $pattern = '^\s*' + [Regex]::Escape($Key) + '\s*(=|\s)'
    for ($i = 0; $i -lt $lines.Count; $i++) {
        if ($lines[$i] -match $pattern) {
            $lines[$i] = $newLine
            $found     = $true
            break
        }
    }
    if (-not $found) { $lines += $newLine }

    [System.IO.File]::WriteAllLines($Path, $lines, (New-Object System.Text.UTF8Encoding($false)))
}

function Set-TomlValue {
    <#
    .SYNOPSIS
        Updates a scalar key in a TOML file (e.g. Xenia config), preserving the
        rest of the document. Only top-level / current-table scalar keys handled,
        which covers the flat Xenia configuration layout.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)] [string] $Path,
        [Parameter(Mandatory = $true)] [string] $Key,
        [Parameter(Mandatory = $true)] [string] $Value
    )

    if (-not (Test-Path -LiteralPath $Path)) {
        # Create a minimal file containing just the key.
        [System.IO.File]::WriteAllText($Path, ('{0} = {1}{2}' -f $Key, $Value, [Environment]::NewLine), (New-Object System.Text.UTF8Encoding($false)))
        return
    }

    $lines   = @(Get-Content -LiteralPath $Path -Encoding UTF8)
    $found   = $false
    $pattern = '^\s*' + [Regex]::Escape($Key) + '\s*='
    for ($i = 0; $i -lt $lines.Count; $i++) {
        if ($lines[$i] -match $pattern) {
            # Preserve any trailing inline comment.
            $comment = ''
            $hashIdx = $lines[$i].IndexOf('#')
            if ($hashIdx -ge 0) { $comment = ' ' + $lines[$i].Substring($hashIdx) }
            $lines[$i] = '{0} = {1}{2}' -f $Key, $Value, $comment
            $found = $true
            break
        }
    }
    if (-not $found) { $lines += ('{0} = {1}' -f $Key, $Value) }

    [System.IO.File]::WriteAllLines($Path, $lines, (New-Object System.Text.UTF8Encoding($false)))
}

function Set-YamlScalar {
    <#
    .SYNOPSIS
        Updates an indented "Key: Value" scalar in an RPCS3-style YAML file,
        preserving structure. Matches by key name at any indentation depth.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)] [string] $Path,
        [Parameter(Mandatory = $true)] [string] $Key,
        [Parameter(Mandatory = $true)] [string] $Value
    )

    $dir = Split-Path -Path $Path -Parent
    if ($dir -and -not (Test-Path -LiteralPath $dir)) {
        New-Item -Path $dir -ItemType Directory -Force | Out-Null
    }

    $lines = @()
    if (Test-Path -LiteralPath $Path) {
        $lines = @(Get-Content -LiteralPath $Path -Encoding UTF8)
    }

    $found   = $false
    $pattern = '^(\s*)' + [Regex]::Escape($Key) + '\s*:'
    for ($i = 0; $i -lt $lines.Count; $i++) {
        if ($lines[$i] -match $pattern) {
            $indent    = $Matches[1]
            $lines[$i] = '{0}{1}: {2}' -f $indent, $Key, $Value
            $found     = $true
            break
        }
    }
    if (-not $found) { $lines += ('{0}: {1}' -f $Key, $Value) }

    [System.IO.File]::WriteAllLines($Path, $lines, (New-Object System.Text.UTF8Encoding($false)))
}

# ----- module: Hardware -----
<#
.SYNOPSIS
    Hardware detection module.
.DESCRIPTION
    Detects CPU, GPU, RAM, storage media type, primary display resolution and
    refresh rate via CIM/WMI, then classifies the system into a performance tier
    (LowEnd / MidRange / HighEnd / FourK) used to select emulator profiles.
#>

Set-StrictMode -Version Latest

function Get-SystemHardware {
    <#
    .SYNOPSIS
        Returns a hashtable describing the host hardware and chosen tier.
    #>
    [CmdletBinding()]
    param()

    $info = [ordered]@{
        CpuName          = 'Unknown'
        CpuCores         = 0
        CpuLogical       = 0
        CpuMaxClockMHz   = 0
        GpuName          = 'Unknown'
        GpuVendor        = 'Unknown'
        GpuVramMB        = 0
        GpuDriverVersion = 'Unknown'
        TotalRamGB       = 0
        SystemDriveType  = 'Unknown'
        DisplayWidth     = 0
        DisplayHeight    = 0
        RefreshRateHz    = 0
        Is4KCapable      = $false
        Tier             = 'MidRange'
    }

    # ---- CPU ----
    try {
        $cpu = Get-CimInstance -ClassName Win32_Processor -ErrorAction Stop | Select-Object -First 1
        if ($cpu) {
            $info.CpuName        = ($cpu.Name).Trim()
            $info.CpuCores       = [int]$cpu.NumberOfCores
            $info.CpuLogical     = [int]$cpu.NumberOfLogicalProcessors
            $info.CpuMaxClockMHz = [int]$cpu.MaxClockSpeed
        }
    } catch { }

    # ---- RAM ----
    try {
        $os = Get-CimInstance -ClassName Win32_ComputerSystem -ErrorAction Stop
        if ($os) {
            $info.TotalRamGB = [math]::Round($os.TotalPhysicalMemory / 1GB, 1)
        }
    } catch {
        try {
            $mem = Get-CimInstance -ClassName Win32_PhysicalMemory -ErrorAction Stop |
                   Measure-Object -Property Capacity -Sum
            $info.TotalRamGB = [math]::Round($mem.Sum / 1GB, 1)
        } catch { }
    }

    # ---- GPU (pick the adapter with the most VRAM, i.e. the discrete one) ----
    try {
        $gpus = Get-CimInstance -ClassName Win32_VideoController -ErrorAction Stop |
                Where-Object { $_.Name }
        if ($gpus) {
            $primary = $gpus | Sort-Object -Property AdapterRAM -Descending | Select-Object -First 1
            $info.GpuName          = ($primary.Name).Trim()
            $info.GpuDriverVersion = $primary.DriverVersion
            # AdapterRAM is a signed 32-bit value and wraps above 4 GB; prefer the
            # registry HardwareInformation.qwMemorySize when AdapterRAM looks wrong.
            $vram = [int64]$primary.AdapterRAM
            if ($vram -le 0) { $vram = 0 }
            $info.GpuVramMB = [int]([math]::Round($vram / 1MB))

            $qw = Get-GpuVramFromRegistry
            if ($qw -gt $info.GpuVramMB) { $info.GpuVramMB = $qw }

            $name = $info.GpuName.ToLower()
            if     ($name -match 'nvidia|geforce|rtx|gtx|quadro') { $info.GpuVendor = 'NVIDIA' }
            elseif ($name -match 'amd|radeon|rx ?\d|vega')        { $info.GpuVendor = 'AMD' }
            elseif ($name -match 'intel|arc|iris|uhd|hd graphics'){ $info.GpuVendor = 'Intel' }
        }
    } catch { }

    # ---- Display resolution / refresh ----
    try {
        $disp = Get-CimInstance -ClassName Win32_VideoController -ErrorAction Stop |
                Where-Object { $_.CurrentHorizontalResolution -gt 0 } |
                Sort-Object -Property CurrentHorizontalResolution -Descending |
                Select-Object -First 1
        if ($disp) {
            $info.DisplayWidth  = [int]$disp.CurrentHorizontalResolution
            $info.DisplayHeight = [int]$disp.CurrentVerticalResolution
            $info.RefreshRateHz = [int]$disp.CurrentRefreshRate
        }
    } catch { }

    if ($info.DisplayWidth -ge 3840 -or $info.DisplayHeight -ge 2160) {
        $info.Is4KCapable = $true
    }

    # ---- System drive media type (SSD vs HDD) ----
    try {
        $sysLetter = $env:SystemDrive.TrimEnd(':')
        $partition = Get-CimInstance -ClassName Win32_LogicalDiskToPartition -ErrorAction Stop
        $mediaType = Get-SystemDriveMediaType
        if ($mediaType) { $info.SystemDriveType = $mediaType }
    } catch { }

    $info.Tier = Resolve-PerformanceTier -Hardware $info
    return $info
}

function Get-GpuVramFromRegistry {
    <#
    .SYNOPSIS
        Reads true VRAM size (in MB) from the display adapter registry key,
        working around the 32-bit AdapterRAM overflow on cards with >4 GB.
    #>
    [CmdletBinding()]
    param()

    $best = 0
    try {
        $base = 'HKLM:\SYSTEM\CurrentControlSet\Control\Class\{4d36e968-e325-11ce-bfc1-08002be10318}'
        if (Test-Path $base) {
            Get-ChildItem $base -ErrorAction SilentlyContinue | ForEach-Object {
                $val = (Get-ItemProperty -Path $_.PSPath -Name 'HardwareInformation.qwMemorySize' -ErrorAction SilentlyContinue).'HardwareInformation.qwMemorySize'
                if ($val) {
                    $mb = [int]([math]::Round([int64]$val / 1MB))
                    if ($mb -gt $best) { $best = $mb }
                }
            }
        }
    } catch { }
    return $best
}

function Get-SystemDriveMediaType {
    <#
    .SYNOPSIS
        Determines whether the OS drive is SSD, HDD or NVMe using Storage cmdlets,
        with a graceful fallback if the Storage module is unavailable.
    #>
    [CmdletBinding()]
    param()

    try {
        if (Get-Command -Name Get-PhysicalDisk -ErrorAction SilentlyContinue) {
            $disks = Get-PhysicalDisk -ErrorAction Stop
            # Prefer a disk reporting bus type NVMe; otherwise use the media type.
            $nvme = $disks | Where-Object { $_.BusType -eq 'NVMe' } | Select-Object -First 1
            if ($nvme) { return 'NVMe SSD' }
            $ssd  = $disks | Where-Object { $_.MediaType -eq 'SSD' } | Select-Object -First 1
            if ($ssd)  { return 'SSD' }
            $hdd  = $disks | Where-Object { $_.MediaType -eq 'HDD' } | Select-Object -First 1
            if ($hdd)  { return 'HDD' }
            $any  = $disks | Select-Object -First 1
            if ($any -and $any.MediaType) { return [string]$any.MediaType }
        }
    } catch { }
    return 'Unknown'
}

function Resolve-PerformanceTier {
    <#
    .SYNOPSIS
        Classifies the system into LowEnd / MidRange / HighEnd / FourK based on a
        weighted scoring of CPU threads, RAM, GPU VRAM/vendor and display.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [System.Collections.Specialized.OrderedDictionary] $Hardware
    )

    $score = 0

    # CPU threads
    if     ($Hardware.CpuLogical -ge 16) { $score += 3 }
    elseif ($Hardware.CpuLogical -ge 8)  { $score += 2 }
    elseif ($Hardware.CpuLogical -ge 4)  { $score += 1 }

    # RAM
    if     ($Hardware.TotalRamGB -ge 32) { $score += 3 }
    elseif ($Hardware.TotalRamGB -ge 16) { $score += 2 }
    elseif ($Hardware.TotalRamGB -ge 8)  { $score += 1 }

    # GPU VRAM
    if     ($Hardware.GpuVramMB -ge 8192) { $score += 3 }
    elseif ($Hardware.GpuVramMB -ge 4096) { $score += 2 }
    elseif ($Hardware.GpuVramMB -ge 2048) { $score += 1 }

    # Discrete NVIDIA/AMD bonus; integrated Intel penalty.
    if ($Hardware.GpuVendor -in @('NVIDIA', 'AMD') -and $Hardware.GpuVramMB -ge 4096) { $score += 1 }
    if ($Hardware.GpuVendor -eq 'Intel') { $score -= 1 }

    # Fast storage bonus.
    if ($Hardware.SystemDriveType -match 'SSD|NVMe') { $score += 1 }

    if ($score -le 3)      { $tier = 'LowEnd' }
    elseif ($score -le 6)  { $tier = 'MidRange' }
    else                   { $tier = 'HighEnd' }

    # Promote a capable HighEnd machine on a 4K panel to the FourK profile.
    if ($tier -eq 'HighEnd' -and $Hardware.Is4KCapable -and $Hardware.GpuVramMB -ge 6144) {
        $tier = 'FourK'
    }

    return $tier
}

# ----- module: ProfileGeneration -----
<#
.SYNOPSIS
    Emulator profile generation module.
.DESCRIPTION
    Generates and persists optimization profiles for LowEnd / MidRange / HighEnd /
    FourK system classes, and selects the most appropriate profile for the
    detected hardware. Profiles are written as JSON under system\profiles so they
    can be inspected, re-applied, or overridden by the user.
#>

Set-StrictMode -Version Latest

function Get-ProfileDefinitions {
    <#
    .SYNOPSIS
        Returns the four canonical profile definitions as a hashtable keyed by tier.
    #>
    [CmdletBinding()]
    param()

    return [ordered]@{
        'LowEnd' = [ordered]@{
            Description       = 'Low-end systems: prioritise stable full speed at native resolution.'
            TargetWidth       = 1280
            TargetHeight      = 720
            InternalScale     = 1
            Anisotropic       = 4
            VSync             = $true
            Backend           = 'auto'
            ShaderCache       = $true
            TextureFiltering  = 'nearest'
        }
        'MidRange' = [ordered]@{
            Description       = 'Mid-range systems: 1080p output with 2x internal scaling.'
            TargetWidth       = 1920
            TargetHeight      = 1080
            InternalScale     = 2
            Anisotropic       = 8
            VSync             = $true
            Backend           = 'vulkan'
            ShaderCache       = $true
            TextureFiltering  = 'bilinear'
        }
        'HighEnd' = [ordered]@{
            Description       = 'High-end systems: 1440p+ output with 4x internal scaling, 16x AF.'
            TargetWidth       = 2560
            TargetHeight      = 1440
            InternalScale     = 4
            Anisotropic       = 16
            VSync             = $true
            Backend           = 'vulkan'
            ShaderCache       = $true
            TextureFiltering  = 'bilinear'
        }
        'FourK' = [ordered]@{
            Description       = '4K systems: native 3840x2160 output, maximum safe internal scaling.'
            TargetWidth       = 3840
            TargetHeight      = 2160
            InternalScale     = 6
            Anisotropic       = 16
            VSync             = $true
            Backend           = 'vulkan'
            ShaderCache       = $true
            TextureFiltering  = 'bilinear'
        }
    }
}

function Save-Profiles {
    <#
    .SYNOPSIS
        Persists all profile definitions to JSON files under the profiles folder.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)] [string] $ProfilesDir,
        [Parameter(Mandatory = $true)] [scriptblock] $Logger
    )

    if (-not (Test-Path -LiteralPath $ProfilesDir)) {
        New-Item -Path $ProfilesDir -ItemType Directory -Force | Out-Null
    }

    $defs = Get-ProfileDefinitions
    foreach ($tier in $defs.Keys) {
        $path = Join-Path $ProfilesDir ("{0}.json" -f $tier)
        ($defs[$tier] | ConvertTo-Json -Depth 10) | Set-Content -LiteralPath $path -Encoding UTF8
        & $Logger "Profile written: $path" 'INFO'
    }
    return $defs
}

function Select-ProfileForHardware {
    <#
    .SYNOPSIS
        Returns the profile definition matching the hardware's resolved tier,
        adjusting the target resolution to the actual display when smaller.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)] [System.Collections.Specialized.OrderedDictionary] $Hardware,
        [Parameter(Mandatory = $true)] [scriptblock] $Logger
    )

    $defs    = Get-ProfileDefinitions
    $tier    = $Hardware.Tier
    if (-not $defs.Contains($tier)) { $tier = 'MidRange' }
    $profile = $defs[$tier]

    # Clamp target resolution to the actual panel if it is smaller than the tier
    # default (never upscale output beyond what the display supports).
    if ($Hardware.DisplayWidth -gt 0 -and $Hardware.DisplayWidth -lt $profile.TargetWidth) {
        $profile.TargetWidth  = $Hardware.DisplayWidth
        $profile.TargetHeight = $Hardware.DisplayHeight
    }

    & $Logger "Selected profile '$tier' -> $($profile.TargetWidth)x$($profile.TargetHeight), scale $($profile.InternalScale)x." 'SUCCESS'
    return @{ Tier = $tier; Profile = $profile }
}

# ----- module: EsdeDiscovery -----
<#
.SYNOPSIS
    ES-DE (EmulationStation Desktop Edition) discovery engine.
.DESCRIPTION
    Locates an ES-DE installation and its user-data tree (settings, gamelists,
    downloaded_media, themes, custom_systems, collections, scraper cache) for
    both portable and installed configurations, and resolves the ROM directory
    from es_settings.xml.
#>

Set-StrictMode -Version Latest

function Find-EsdeDataDir {
    <#
    .SYNOPSIS
        Resolves the ES-DE application-data directory (the "ES-DE" folder that
        holds settings/, gamelists/, downloaded_media/, etc.).
    .PARAMETER StartPath
        A hint location (e.g. the folder the launcher runs from) checked first
        for a portable layout.
    #>
    [CmdletBinding()]
    param([string] $StartPath)

    $candidates = New-Object System.Collections.Generic.List[string]

    if ($StartPath) {
        # Portable: an "ES-DE" folder next to the launcher, or the launcher IS in it.
        $cursor = (Resolve-Path -LiteralPath $StartPath -ErrorAction SilentlyContinue).Path
        if ($cursor) {
            for ($i = 0; $i -lt 4 -and $cursor; $i++) {
                $candidates.Add((Join-Path $cursor 'ES-DE'))
                $candidates.Add($cursor)
                $parent = Split-Path -Path $cursor -Parent
                if (-not $parent -or $parent -eq $cursor) { break }
                $cursor = $parent
            }
        }
    }

    # Standard installed locations (ES-DE 2.x/3.x).
    foreach ($base in @($env:USERPROFILE, $env:HOME, $env:APPDATA, $env:LOCALAPPDATA)) {
        if ([string]::IsNullOrWhiteSpace($base)) { continue }
        $candidates.Add((Join-Path $base 'ES-DE'))
        $candidates.Add((Join-Path $base '.emulationstation'))
    }
    foreach ($drive in @('C:', 'D:', 'E:')) {
        $candidates.Add($drive + '\ES-DE')
        $candidates.Add($drive + '\RetroBat\ES-DE')
    }

    foreach ($c in ($candidates | Select-Object -Unique)) {
        if (Test-EsdeDataDir -Path $c) { return (Resolve-Path -LiteralPath $c).Path }
    }
    return $null
}

function Test-EsdeDataDir {
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][string] $Path)
    if (-not (Test-Path -LiteralPath $Path)) { return $false }
    $markers = @('settings','gamelists','downloaded_media','themes','custom_systems','collections')
    $hits = 0
    foreach ($m in $markers) { if (Test-Path -LiteralPath (Join-Path $Path $m)) { $hits++ } }
    if (Test-Path -LiteralPath (Join-Path $Path 'settings\es_settings.xml')) { $hits += 2 }
    return ($hits -ge 2)
}

function Get-EsdeLayout {
    <#
    .SYNOPSIS
        Builds a hashtable of all important ES-DE paths and resolves the ROM dir.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][string] $DataDir)

    $settingsFile = Join-Path $DataDir 'settings\es_settings.xml'
    $layout = [ordered]@{
        DataDir          = $DataDir
        Settings         = Join-Path $DataDir 'settings'
        SettingsFile     = $settingsFile
        InputFile        = Join-Path $DataDir 'settings\es_input.xml'
        Gamelists        = Join-Path $DataDir 'gamelists'
        DownloadedMedia  = Join-Path $DataDir 'downloaded_media'
        Themes           = Join-Path $DataDir 'themes'
        CustomSystems    = Join-Path $DataDir 'custom_systems'
        Collections      = Join-Path $DataDir 'collections'
        ScraperCache     = Join-Path $DataDir 'cache'
        Logs             = Join-Path $DataDir 'logs'
        Version          = Get-EsdeVersion -DataDir $DataDir
    }
    $layout.RomDir   = Get-EsdeRomDirectory -SettingsFile $settingsFile
    $layout.MediaDir = Get-EsdeMediaDirectory -SettingsFile $settingsFile -DataDir $DataDir

    $layout.Exists = [ordered]@{}
    foreach ($k in @('Settings','SettingsFile','InputFile','Gamelists','DownloadedMedia',
                     'Themes','CustomSystems','Collections','ScraperCache')) {
        $layout.Exists[$k] = Test-Path -LiteralPath $layout[$k]
    }
    return $layout
}

function Get-EsdeVersion {
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][string] $DataDir)
    $vf = Join-Path $DataDir 'LATEST_VERSION.txt'
    if (Test-Path -LiteralPath $vf) {
        $raw = Get-Content -LiteralPath $vf -Raw -ErrorAction SilentlyContinue
        if ($raw) { return $raw.Trim() }
    }
    return 'Unknown'
}

function Get-EsdeSetting {
    <#
    .SYNOPSIS
        Reads a single string/value setting out of es_settings.xml.
        ES-DE stores settings as <string name="X" value="Y" /> elements.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string] $SettingsFile,
        [Parameter(Mandatory = $true)][string] $Name
    )
    if (-not (Test-Path -LiteralPath $SettingsFile)) { return $null }
    try {
        # XmlDocument.Load reads the file with correct encoding/BOM detection;
        # [xml](Get-Content -Raw) fails on a UTF-8 BOM ("Data at the root level
        # is invalid"), which would make us silently fall back to default paths.
        $xml = New-Object System.Xml.XmlDocument
        $xml.Load($SettingsFile)
        $node = $xml.SelectSingleNode("//*[@name='$Name']")
        if ($node -and $node.Attributes['value']) { return $node.Attributes['value'].Value }
    } catch { }
    return $null
}

function Get-EsdeRomDirectory {
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][string] $SettingsFile)
    $rd = Get-EsdeSetting -SettingsFile $SettingsFile -Name 'ROMDirectory'
    if ($rd) {
        $rd = $rd -replace '%ESPATH%', (Split-Path (Split-Path $SettingsFile -Parent) -Parent)
        $rd = [Environment]::ExpandEnvironmentVariables($rd)
        if ($rd) { return $rd }
    }
    foreach ($p in @((Join-Path $env:USERPROFILE 'ROMs'), 'C:\RetroBat\roms', 'D:\RetroBat\roms')) {
        if ($p -and (Test-Path -LiteralPath $p)) { return $p }
    }
    return (Join-Path $env:USERPROFILE 'ROMs')
}

function Get-EsdeMediaDirectory {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string] $SettingsFile,
        [Parameter(Mandatory = $true)][string] $DataDir
    )
    $md = Get-EsdeSetting -SettingsFile $SettingsFile -Name 'MediaDirectory'
    if ($md) {
        $md = [Environment]::ExpandEnvironmentVariables($md)
        if ($md) { return $md }
    }
    return (Join-Path $DataDir 'downloaded_media')
}

function Get-EsdeSystems {
    <#
    .SYNOPSIS
        Enumerates ES-DE systems by inspecting the ROM directory, gamelists and
        downloaded_media folders, returning a descriptor per system.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][System.Collections.Specialized.OrderedDictionary] $Layout)

    $systems = @{}

    function Add-Sys($name) {
        if (-not $systems.ContainsKey($name)) {
            $systems[$name] = [ordered]@{
                Name        = $name
                RomPath     = Join-Path $Layout.RomDir $name
                GamelistDir = Join-Path $Layout.Gamelists $name
                Gamelist    = Join-Path (Join-Path $Layout.Gamelists $name) 'gamelist.xml'
                MediaDir    = Join-Path $Layout.MediaDir $name
                HasRoms     = $false
                HasGamelist = $false
                HasMedia    = $false
            }
        }
        return $systems[$name]
    }

    if (Test-Path -LiteralPath $Layout.RomDir) {
        Get-ChildItem -LiteralPath $Layout.RomDir -Directory -ErrorAction SilentlyContinue | ForEach-Object {
            if ($_.Name -in @('media','downloaded_media')) { return }
            (Add-Sys $_.Name).HasRoms = $true
        }
    }
    if (Test-Path -LiteralPath $Layout.Gamelists) {
        Get-ChildItem -LiteralPath $Layout.Gamelists -Directory -ErrorAction SilentlyContinue | ForEach-Object {
            $s = Add-Sys $_.Name
            $s.HasGamelist = Test-Path -LiteralPath $s.Gamelist
        }
    }
    if (Test-Path -LiteralPath $Layout.MediaDir) {
        Get-ChildItem -LiteralPath $Layout.MediaDir -Directory -ErrorAction SilentlyContinue | ForEach-Object {
            (Add-Sys $_.Name).HasMedia = $true
        }
    }

    return @($systems.Values | Sort-Object Name)
}

# ----- module: HealthSelfHeal -----
<#
.SYNOPSIS
    Health & self-healing engine for the ES-DE Auto Suite.
.DESCRIPTION
    Provides the resilience layer that lets the suite diagnose and repair itself:
      * Invoke-Phase  - runs each pipeline phase in isolation; an error in one
                        phase is logged, optionally auto-recovered, and the run
                        CONTINUES instead of aborting.
      * Invoke-WithRetry - retry transient IO/network operations with backoff.
      * Test-PathWritable / Get-FreeSpaceGB - environment self-tests.
      * Repair-EsdeStructure - recreate any missing ES-DE directory.
      * Repair-XmlFile - validate XML, restore from backup or quarantine if broken.
      * Health findings are collected and written to a Health report (HTML+JSON).
#>

Set-StrictMode -Version Latest

$script:HealthFindings = New-Object System.Collections.Generic.List[object]
$script:PhaseResults   = New-Object System.Collections.Generic.List[object]

function Initialize-Health {
    [CmdletBinding()] param()
    $script:HealthFindings = New-Object System.Collections.Generic.List[object]
    $script:PhaseResults   = New-Object System.Collections.Generic.List[object]
}

function Add-HealthFinding {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string] $Area,
        [Parameter(Mandatory = $true)][ValidateSet('OK','Fixed','Warning','Error')] [string] $Status,
        [Parameter(Mandatory = $true)][string] $Detail
    )
    $script:HealthFindings.Add([ordered]@{ Area = $Area; Status = $Status; Detail = $Detail; Time = (Get-Date -Format 'HH:mm:ss') })
}

function Get-HealthFindings { return $script:HealthFindings.ToArray() }
function Get-PhaseResults  { return $script:PhaseResults.ToArray() }

function Invoke-Phase {
    <#
    .SYNOPSIS
        Runs a phase scriptblock guarded by try/catch. On failure it logs the error,
        runs an optional Recovery scriptblock, records a health finding and returns
        $false WITHOUT throwing, so the overall pipeline keeps going (self-healing).
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string] $Name,
        [Parameter(Mandatory = $true)][scriptblock] $Action,
        [Parameter(Mandatory = $true)][scriptblock] $Logger,
        [scriptblock] $Recovery
    )
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    try {
        & $Action
        $sw.Stop()
        $script:PhaseResults.Add([ordered]@{ Phase = $Name; Result = 'OK'; Seconds = [math]::Round($sw.Elapsed.TotalSeconds,2); Error = '' })
        return $true
    } catch {
        $sw.Stop()
        $msg = $_.Exception.Message
        & $Logger "Phase '$Name' error: $msg" 'ERROR'
        Add-HealthFinding -Area $Name -Status 'Error' -Detail $msg
        if ($Recovery) {
            try {
                & $Logger "Attempting self-repair for phase '$Name'..." 'WARN'
                & $Recovery
                & $Logger "Self-repair for phase '$Name' completed; continuing." 'SUCCESS'
                Add-HealthFinding -Area $Name -Status 'Fixed' -Detail "Recovered after error: $msg"
            } catch {
                & $Logger "Self-repair for phase '$Name' failed: $($_.Exception.Message)" 'ERROR'
            }
        }
        $script:PhaseResults.Add([ordered]@{ Phase = $Name; Result = 'Recovered'; Seconds = [math]::Round($sw.Elapsed.TotalSeconds,2); Error = $msg })
        return $false
    }
}

function Invoke-WithRetry {
    <#
    .SYNOPSIS
        Executes a scriptblock, retrying on exception with exponential backoff.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][scriptblock] $Action,
        [int] $MaxRetries = 3,
        [int] $DelaySeconds = 2
    )
    $attempt = 0; $delay = $DelaySeconds
    while ($true) {
        try { return (& $Action) }
        catch {
            $attempt++
            if ($attempt -ge $MaxRetries) { throw }
            Start-Sleep -Seconds $delay
            $delay *= 2
        }
    }
}

function Test-PathWritable {
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][string] $Path)
    try {
        if (-not (Test-Path -LiteralPath $Path)) { New-Item -Path $Path -ItemType Directory -Force -ErrorAction Stop | Out-Null }
        $probe = Join-Path $Path (".__write_test_{0}.tmp" -f ([Guid]::NewGuid().ToString('N')))
        [System.IO.File]::WriteAllText($probe, 'ok')
        Remove-Item -LiteralPath $probe -Force -ErrorAction SilentlyContinue
        return $true
    } catch { return $false }
}

function Get-FreeSpaceGB {
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][string] $Path)
    try {
        $full = [System.IO.Path]::GetFullPath($Path)
        $root = [System.IO.Path]::GetPathRoot($full)
        $di = New-Object System.IO.DriveInfo($root)
        return [math]::Round($di.AvailableFreeSpace / 1GB, 1)
    } catch { return -1 }
}

function Repair-EsdeStructure {
    <#
    .SYNOPSIS
        Ensures every required ES-DE directory exists (auto-heal). Returns count created.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][System.Collections.Specialized.OrderedDictionary] $Layout,
        [Parameter(Mandatory = $true)][scriptblock] $Logger,
        [switch] $DryRun
    )
    $required = @($Layout.Settings, $Layout.Gamelists, $Layout.DownloadedMedia, $Layout.Themes,
                  $Layout.CustomSystems, $Layout.Collections, $Layout.ScraperCache)
    $created = 0
    foreach ($d in $required) {
        if ($d -and -not (Test-Path -LiteralPath $d)) {
            if (-not $DryRun) { New-Item -Path $d -ItemType Directory -Force | Out-Null }
            $created++
            & $Logger "Created missing ES-DE directory: $d" 'WARN'
            Add-HealthFinding -Area 'Structure' -Status 'Fixed' -Detail "Created $d"
        }
    }
    if ($created -eq 0) { Add-HealthFinding -Area 'Structure' -Status 'OK' -Detail 'All ES-DE directories present.' }
    return $created
}

function Test-XmlWellFormed {
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][string] $Path)
    if (-not (Test-Path -LiteralPath $Path)) { return $false }
    try {
        $raw = Get-Content -LiteralPath $Path -Raw -Encoding UTF8
        # Tolerate ES-DE dual-root by testing only the gameList element if present.
        $i = $raw.IndexOf('<gameList')
        if ($i -ge 0) {
            $e = $raw.LastIndexOf('</gameList>')
            if ($e -ge 0) { $raw = $raw.Substring($i, ($e - $i) + 11) } else { $raw = $raw.Substring($i) }
            $null = [xml]$raw
        } else {
            # Single-root file (e.g. es_settings.xml): load from disk so a UTF-8 BOM
            # or declared encoding is handled correctly (a valid file is not flagged).
            $doc = New-Object System.Xml.XmlDocument
            $doc.Load($Path)
        }
        return $true
    } catch { return $false }
}

function Repair-XmlFile {
    <#
    .SYNOPSIS
        If an XML file is malformed, restores the newest backup; if none exists,
        quarantines the corrupt file so ES-DE can regenerate it. Never data-loses.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string] $Path,
        [Parameter(Mandatory = $true)][string] $BackupRoot,
        [Parameter(Mandatory = $true)][scriptblock] $Logger,
        [switch] $DryRun
    )
    if (Test-XmlWellFormed -Path $Path) { return $true }
    & $Logger "Malformed XML detected: $Path" 'ERROR'
    if ($DryRun) { Add-HealthFinding -Area 'XML' -Status 'Warning' -Detail "Malformed (dry-run): $Path"; return $false }

    if (Restore-LatestFile -OriginalPath $Path -BackupRoot $BackupRoot) {
        if (Test-XmlWellFormed -Path $Path) {
            & $Logger "Restored valid XML from backup: $Path" 'SUCCESS'
            Add-HealthFinding -Area 'XML' -Status 'Fixed' -Detail "Restored from backup: $Path"
            return $true
        }
    }
    $q = Join-Path $BackupRoot ('corrupt_xml\' + (Split-Path $Path -Leaf) + '.' + (Get-Date -Format 'yyyyMMdd_HHmmss') + '.corrupt')
    $qd = Split-Path $q -Parent
    if (-not (Test-Path -LiteralPath $qd)) { New-Item -Path $qd -ItemType Directory -Force | Out-Null }
    Copy-Item -LiteralPath $Path -Destination $q -Force -ErrorAction SilentlyContinue
    & $Logger "No valid backup; quarantined corrupt copy to $q (ES-DE will regenerate)." 'WARN'
    Add-HealthFinding -Area 'XML' -Status 'Warning' -Detail "Quarantined corrupt file: $Path"
    return $false
}

# ----- module: BackupEngine -----
<#
.SYNOPSIS
    Backup engine - timestamped backups of any file before modification, plus
    snapshot backups of whole config/gamelist trees, with restore support.
#>

Set-StrictMode -Version Latest

function Initialize-BackupRoot {
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][string] $BackupRoot)
    if (-not (Test-Path -LiteralPath $BackupRoot)) {
        New-Item -Path $BackupRoot -ItemType Directory -Force | Out-Null
    }
    return $BackupRoot
}

function Backup-File {
    <#
    .SYNOPSIS
        Copies a file to the backup root as <name>.<timestamp>.bak (no-op if the
        source does not exist). Returns the backup path or $null.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string] $Path,
        [Parameter(Mandatory = $true)][string] $BackupRoot
    )
    if (-not (Test-Path -LiteralPath $Path)) { return $null }
    Initialize-BackupRoot -BackupRoot $BackupRoot | Out-Null
    $stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
    $leaf  = Split-Path -Path $Path -Leaf
    $dest  = Join-Path $BackupRoot ("{0}.{1}.bak" -f $leaf, $stamp)
    Copy-Item -LiteralPath $Path -Destination $dest -Force
    return $dest
}

function Backup-Tree {
    <#
    .SYNOPSIS
        Creates a timestamped snapshot copy of a folder tree (filtered by include
        extensions) under the backup root. Used for gamelists / settings / configs.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string]   $SourceDir,
        [Parameter(Mandatory = $true)][string]   $BackupRoot,
        [Parameter(Mandatory = $true)][string]   $Label,
        [string[]] $IncludeExtensions = @('*.xml','*.cfg','*.ini','*.json','*.yml','*.toml')
    )
    if (-not (Test-Path -LiteralPath $SourceDir)) { return $null }
    $stamp  = Get-Date -Format 'yyyyMMdd_HHmmss'
    $target = Join-Path $BackupRoot ("snapshot_{0}_{1}" -f $Label, $stamp)
    New-Item -Path $target -ItemType Directory -Force | Out-Null

    $count = 0
    Get-ChildItem -LiteralPath $SourceDir -Recurse -File -Include $IncludeExtensions -ErrorAction SilentlyContinue | ForEach-Object {
        $rel = $_.FullName.Substring($SourceDir.Length).TrimStart('\','/')
        $dst = Join-Path $target $rel
        $dstDir = Split-Path $dst -Parent
        if (-not (Test-Path -LiteralPath $dstDir)) { New-Item -Path $dstDir -ItemType Directory -Force | Out-Null }
        Copy-Item -LiteralPath $_.FullName -Destination $dst -Force
        $count++
    }
    return @{ Path = $target; FileCount = $count }
}

function Restore-LatestFile {
    <#
    .SYNOPSIS
        Restores a file from its newest <name>.<timestamp>.bak backup.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string] $OriginalPath,
        [Parameter(Mandatory = $true)][string] $BackupRoot
    )
    if (-not (Test-Path -LiteralPath $BackupRoot)) { return $false }
    $leaf   = Split-Path $OriginalPath -Leaf
    $backup = Get-ChildItem -LiteralPath $BackupRoot -Filter "$leaf.*.bak" -File -ErrorAction SilentlyContinue |
              Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if ($backup) {
        Copy-Item -LiteralPath $backup.FullName -Destination $OriginalPath -Force
        return $true
    }
    return $false
}

# ----- module: MediaClassification -----
<#
.SYNOPSIS
    Media classification engine.
.DESCRIPTION
    Classifies a media file into an ES-DE media folder (covers, marquees, videos,
    manuals, fanart, screenshots, 3dboxes, backcovers, miximages, physicalmedia,
    titlescreens) using, in priority order:
      1. an explicit gamelist tag association (passed in),
      2. the source sub-folder name,
      3. a scraper filename suffix (e.g. -marquee),
      4. file extension (video/manual),
      5. image dimensions / aspect ratio heuristics.
#>

Set-StrictMode -Version Latest

function Get-MediaDefinitions {
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][string] $DefinitionPath)
    if (-not (Test-Path -LiteralPath $DefinitionPath)) { throw "Media definition file not found: $DefinitionPath" }
    return (Get-Content -LiteralPath $DefinitionPath -Raw -Encoding UTF8 | ConvertFrom-Json)
}

function ConvertTo-Hashtable {
    param([object] $Object)
    $ht = @{}
    if ($null -eq $Object) { return $ht }
    foreach ($p in $Object.PSObject.Properties) { $ht[$p.Name.ToLower()] = $p.Value }
    return $ht
}

function Get-ImageDimensions {
    <#
    .SYNOPSIS
        Returns @{Width;Height} for an image using System.Drawing, or $null.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][string] $Path)
    try {
        Add-Type -AssemblyName System.Drawing -ErrorAction Stop
        $img = [System.Drawing.Image]::FromFile($Path)
        try { return @{ Width = $img.Width; Height = $img.Height } }
        finally { $img.Dispose() }
    } catch { return $null }
}

function Get-MediaClassification {
    <#
    .SYNOPSIS
        Returns the ES-DE media folder name for a file, plus the method used.
    .OUTPUTS
        Hashtable: EsdeFolder (string|null), Method (string), Kind (image/video/manual/unknown)
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)] [string] $FilePath,
        [Parameter(Mandatory = $true)] [object] $Definitions,
        [string] $SourceFolderName = '',
        [string] $GamelistTag = ''
    )

    $ext  = [System.IO.Path]::GetExtension($FilePath).ToLower()
    $stem = [System.IO.Path]::GetFileNameWithoutExtension($FilePath).ToLower()

    $imgExt = @($Definitions.mediaExtensions.image)
    $vidExt = @($Definitions.mediaExtensions.video)
    $manExt = @($Definitions.mediaExtensions.manual)

    $kind =
        if ($vidExt -contains $ext) { 'video' }
        elseif ($manExt -contains $ext) { 'manual' }
        elseif ($imgExt -contains $ext) { 'image' }
        else { 'unknown' }

    # 1) Explicit gamelist tag.
    if ($GamelistTag) {
        $map = ConvertTo-Hashtable $Definitions.gamelistTagToEsdeFolder
        $k = $GamelistTag.ToLower()
        if ($map.ContainsKey($k)) { return @{ EsdeFolder = $map[$k]; Method = 'gamelist-tag'; Kind = $kind } }
    }

    # Hard rule: videos and manuals are unambiguous by extension.
    if ($kind -eq 'video')  { return @{ EsdeFolder = 'videos';  Method = 'extension'; Kind = $kind } }
    if ($kind -eq 'manual') { return @{ EsdeFolder = 'manuals'; Method = 'extension'; Kind = $kind } }

    # 2) Source folder name.
    if ($SourceFolderName) {
        $fmap = ConvertTo-Hashtable $Definitions.sourceFolderToEsdeFolder
        $fk = $SourceFolderName.ToLower()
        if ($fmap.ContainsKey($fk)) { return @{ EsdeFolder = $fmap[$fk]; Method = 'source-folder'; Kind = $kind } }
    }

    # 3) Filename suffix (e.g. mygame-marquee.png).
    $smap = ConvertTo-Hashtable $Definitions.filenameSuffixToEsdeFolder
    foreach ($suffix in ($smap.Keys | Sort-Object { $_.Length } -Descending)) {
        if ($stem.EndsWith($suffix)) { return @{ EsdeFolder = $smap[$suffix]; Method = 'filename-suffix'; Kind = $kind } }
    }

    # 4/5) Image dimension heuristic for images with no other signal.
    if ($kind -eq 'image') {
        $dim = Get-ImageDimensions -Path $FilePath
        if ($dim -and $dim.Height -gt 0) {
            $ar = [double]$dim.Width / [double]$dim.Height
            if ($ar -ge 1.6)      { return @{ EsdeFolder = 'screenshots'; Method = 'dimensions'; Kind = $kind } } # widescreen -> screenshot
            elseif ($ar -le 0.85) { return @{ EsdeFolder = 'covers';      Method = 'dimensions'; Kind = $kind } } # portrait -> box/cover
            else                  { return @{ EsdeFolder = 'miximages';   Method = 'dimensions'; Kind = $kind } } # near-square -> mix
        }
        # Last resort: treat a lone image as a cover.
        return @{ EsdeFolder = 'covers'; Method = 'default-image'; Kind = $kind }
    }

    return @{ EsdeFolder = $null; Method = 'unclassified'; Kind = $kind }
}

# ----- module: MediaReorganization -----
<#
.SYNOPSIS
    Media reorganization engine: creates the ES-DE media folder structure and
    moves misplaced / loose media files into their correct ES-DE subfolders.
#>

Set-StrictMode -Version Latest

function Get-FileSha256 {
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][string] $Path)
    try {
        $sha = [System.Security.Cryptography.SHA256]::Create()
        $fs  = [System.IO.File]::OpenRead($Path)
        try { return ([BitConverter]::ToString($sha.ComputeHash($fs))).Replace('-','') }
        finally { $fs.Dispose(); $sha.Dispose() }
    } catch { return $null }
}

function New-EsdeMediaFolders {
    <#
    .SYNOPSIS
        Creates every ES-DE media subfolder for a system under downloaded_media.
    .OUTPUTS
        Count of folders created.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string]   $SystemMediaDir,
        [Parameter(Mandatory = $true)][string[]] $MediaFolders,
        [switch] $DryRun
    )
    $created = 0
    foreach ($f in $MediaFolders) {
        $p = Join-Path $SystemMediaDir $f
        if (-not (Test-Path -LiteralPath $p)) {
            if (-not $DryRun) { New-Item -Path $p -ItemType Directory -Force | Out-Null }
            $created++
        }
    }
    return $created
}

function Copy-MediaSafe {
    <#
    .SYNOPSIS
        Copies (or moves) a media file to its destination without ever losing data:
        identical files are skipped, differing destinations are backed up first.
    .OUTPUTS
        One of: 'copied','moved','skipped-identical','overwritten','dryrun','error'.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string] $Source,
        [Parameter(Mandatory = $true)][string] $Dest,
        [Parameter(Mandatory = $true)][string] $BackupRoot,
        [switch] $Move,
        [switch] $DryRun
    )
    if (-not (Test-Path -LiteralPath $Source)) { return 'error' }
    $destDir = Split-Path $Dest -Parent

    if (Test-Path -LiteralPath $Dest) {
        $hs = Get-FileSha256 -Path $Source
        $hd = Get-FileSha256 -Path $Dest
        if ($hs -and $hd -and $hs -eq $hd) {
            if (-not $DryRun -and $Move) { Remove-Item -LiteralPath $Source -Force -ErrorAction SilentlyContinue }
            return 'skipped-identical'
        }
        if ($DryRun) { return 'dryrun' }
        Backup-File -Path $Dest -BackupRoot $BackupRoot | Out-Null
        if (-not (Test-Path -LiteralPath $destDir)) { New-Item -Path $destDir -ItemType Directory -Force | Out-Null }
        if ($Move) { Move-Item -LiteralPath $Source -Destination $Dest -Force }
        else { Copy-Item -LiteralPath $Source -Destination $Dest -Force }
        return 'overwritten'
    }

    if ($DryRun) { return 'dryrun' }
    if (-not (Test-Path -LiteralPath $destDir)) { New-Item -Path $destDir -ItemType Directory -Force | Out-Null }
    if ($Move) { Move-Item -LiteralPath $Source -Destination $Dest -Force; return 'moved' }
    else { Copy-Item -LiteralPath $Source -Destination $Dest -Force; return 'copied' }
}

function Invoke-MediaReorganization {
    <#
    .SYNOPSIS
        For a system, ensures all ES-DE media folders exist and moves any media
        files sitting loose in the media root (or in a wrongly-named subfolder)
        into the correct ES-DE subfolder, classified by name/folder/dimensions.
    .OUTPUTS
        Hashtable of statistics.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string]   $SystemMediaDir,
        [Parameter(Mandatory = $true)][object]   $Definitions,
        [Parameter(Mandatory = $true)][string]   $BackupRoot,
        [Parameter(Mandatory = $true)][scriptblock] $Logger,
        [switch] $DryRun
    )

    $stats = @{ FoldersCreated = 0; Moved = 0; Skipped = 0; Errors = 0 }

    # Always manage the full ES-DE media folder set for the system, creating the
    # media directory itself if it does not exist yet (so every system ends up
    # with a complete, correct downloaded_media structure).
    $esdeFolders = @($Definitions.esdeMediaFolders)
    if (-not (Test-Path -LiteralPath $SystemMediaDir) -and -not $DryRun) {
        New-Item -Path $SystemMediaDir -ItemType Directory -Force | Out-Null
    }
    $stats.FoldersCreated = New-EsdeMediaFolders -SystemMediaDir $SystemMediaDir -MediaFolders $esdeFolders -DryRun:$DryRun
    if (-not (Test-Path -LiteralPath $SystemMediaDir)) { return $stats }   # dry-run with no dir

    $valid = @{}; foreach ($f in $esdeFolders) { $valid[$f.ToLower()] = $true }

    # Loose files directly in the media root.
    Get-ChildItem -LiteralPath $SystemMediaDir -File -ErrorAction SilentlyContinue | ForEach-Object {
        $cls = Get-MediaClassification -FilePath $_.FullName -Definitions $Definitions -SourceFolderName ''
        if ($cls.EsdeFolder) {
            $dest = Join-Path (Join-Path $SystemMediaDir $cls.EsdeFolder) $_.Name
            $r = Copy-MediaSafe -Source $_.FullName -Dest $dest -BackupRoot $BackupRoot -Move -DryRun:$DryRun
            if ($r -in @('moved','overwritten','copied')) { $stats.Moved++ } else { $stats.Skipped++ }
        } else { $stats.Skipped++ }
    }

    # Files inside non-ES-DE-named subfolders (wrongly named) -> reclassify.
    Get-ChildItem -LiteralPath $SystemMediaDir -Directory -ErrorAction SilentlyContinue | ForEach-Object {
        $folderName = $_.Name
        if ($valid.ContainsKey($folderName.ToLower())) { return }   # already a valid ES-DE folder
        Get-ChildItem -LiteralPath $_.FullName -File -Recurse -ErrorAction SilentlyContinue | ForEach-Object {
            $cls = Get-MediaClassification -FilePath $_.FullName -Definitions $Definitions -SourceFolderName $folderName
            if ($cls.EsdeFolder) {
                $dest = Join-Path (Join-Path $SystemMediaDir $cls.EsdeFolder) $_.Name
                $r = Copy-MediaSafe -Source $_.FullName -Dest $dest -BackupRoot $BackupRoot -Move -DryRun:$DryRun
                if ($r -in @('moved','overwritten','copied')) { $stats.Moved++ } else { $stats.Skipped++ }
            } else { $stats.Skipped++ }
        }
    }

    & $Logger "Reorg $(Split-Path $SystemMediaDir -Leaf): +$($stats.FoldersCreated) folders, $($stats.Moved) moved, $($stats.Skipped) skipped." 'INFO'
    return $stats
}

# ----- module: RetroBatMigration -----
<#
.SYNOPSIS
    RetroBat -> ES-DE migration engine.
.DESCRIPTION
    Detects RetroBat media layouts (roms\<system>\images|videos|manuals|media|...
    plus gamelist.xml media references) and migrates every asset into the ES-DE
    downloaded_media\<system>\<type> structure, matching files to ROMs by stem and
    classifying media by gamelist tag, source folder and filename. Existing,
    identical destination files are skipped; differing ones are backed up first.
    No source data is ever deleted (copy, not move).
#>

Set-StrictMode -Version Latest

function Test-RetroBatMediaLayout {
    <#
    .SYNOPSIS
        Returns $true if a system folder looks like it holds RetroBat-style media
        (recognised media sub-folders or a gamelist.xml with media references).
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][string] $SystemRomDir)
    if (-not (Test-Path -LiteralPath $SystemRomDir)) { return $false }
    $hintFolders = @('images','media','videos','manuals','fanart','marquees','wheels',
                     'screenshots','boxart','box3d','thumbnails','supports','downloaded_images')
    foreach ($h in $hintFolders) {
        if (Test-Path -LiteralPath (Join-Path $SystemRomDir $h)) { return $true }
    }
    if (Test-Path -LiteralPath (Join-Path $SystemRomDir 'gamelist.xml')) { return $true }
    return $false
}

function Invoke-SystemMigration {
    <#
    .SYNOPSIS
        Migrates a single system's RetroBat media into ES-DE downloaded_media.
    .OUTPUTS
        Hashtable of statistics.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string]   $SystemRomDir,     # roms\<system>
        [Parameter(Mandatory = $true)][string]   $SystemMediaDir,   # downloaded_media\<system>
        [Parameter(Mandatory = $true)][object]   $Definitions,
        [Parameter(Mandatory = $true)][string]   $BackupRoot,
        [Parameter(Mandatory = $true)][scriptblock] $Logger,
        [switch] $DryRun
    )

    $stats = @{ FromGamelist = 0; FromFolders = 0; Skipped = 0; Errors = 0 }
    if (-not (Test-Path -LiteralPath $SystemRomDir)) { return $stats }

    $tagMap    = ConvertTo-Hashtable $Definitions.gamelistTagToEsdeFolder
    $folderMap = ConvertTo-Hashtable $Definitions.sourceFolderToEsdeFolder

    # ---- 1) Migrate media referenced by gamelist.xml (most reliable) ----
    $gl = Join-Path $SystemRomDir 'gamelist.xml'
    if (Test-Path -LiteralPath $gl) {
        $parsed = Read-Gamelist -Path $gl
        if ($parsed.Ok) {
            foreach ($game in @($parsed.Games)) {
                $pathNode = $game.SelectSingleNode('path')
                if (-not $pathNode) { continue }
                $romStem = [System.IO.Path]::GetFileNameWithoutExtension($pathNode.InnerText)
                foreach ($tag in (Get-GameMediaTags)) {
                    $node = $game.SelectSingleNode($tag)
                    if (-not $node -or [string]::IsNullOrWhiteSpace($node.InnerText)) { continue }
                    $src = Resolve-RelativeMediaPath -BaseDir $SystemRomDir -RelPath $node.InnerText
                    if (-not (Test-Path -LiteralPath $src)) { continue }
                    $folder = if ($tagMap.ContainsKey($tag.ToLower())) { $tagMap[$tag.ToLower()] } else { $null }
                    if (-not $folder) { continue }
                    $ext  = [System.IO.Path]::GetExtension($src)
                    $dest = Join-Path (Join-Path $SystemMediaDir $folder) ($romStem + $ext)
                    $r = Copy-MediaSafe -Source $src -Dest $dest -BackupRoot $BackupRoot -DryRun:$DryRun
                    if ($r -in @('copied','overwritten')) { $stats.FromGamelist++ }
                    elseif ($r -eq 'error') { $stats.Errors++ }
                    else { $stats.Skipped++ }
                }
            }
        } else {
            & $Logger "Could not parse RetroBat gamelist: $gl ($($parsed.Error))" 'WARN'
        }
    }

    # ---- 2) Migrate loose media folders (images\, videos\, media\<type>\ ...) ----
    foreach ($dir in (Get-ChildItem -LiteralPath $SystemRomDir -Directory -ErrorAction SilentlyContinue)) {
        $name = $dir.Name.ToLower()
        if ($name -eq 'media') {
            # Batocera/RetroBat "media" holds typed sub-folders (box2dfront, etc.).
            foreach ($sub in (Get-ChildItem -LiteralPath $dir.FullName -Directory -ErrorAction SilentlyContinue)) {
                Move-FolderMedia -SrcDir $sub.FullName -SrcFolderName $sub.Name -SystemMediaDir $SystemMediaDir `
                    -Definitions $Definitions -BackupRoot $BackupRoot -Stats $stats -DryRun:$DryRun
            }
            continue
        }
        if ($folderMap.ContainsKey($name) -or $folderMap.ContainsKey(($name -replace 's$',''))) {
            Move-FolderMedia -SrcDir $dir.FullName -SrcFolderName $dir.Name -SystemMediaDir $SystemMediaDir `
                -Definitions $Definitions -BackupRoot $BackupRoot -Stats $stats -DryRun:$DryRun
        }
    }

    & $Logger "Migrated $(Split-Path $SystemRomDir -Leaf): $($stats.FromGamelist) via gamelist, $($stats.FromFolders) via folders, $($stats.Skipped) skipped." 'SUCCESS'
    return $stats
}

function Move-FolderMedia {
    <#
    .SYNOPSIS
        Copies every media file from a RetroBat media sub-folder into the correct
        ES-DE media subfolder, classifying each file. Updates $Stats by reference.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string]   $SrcDir,
        [Parameter(Mandatory = $true)][string]   $SrcFolderName,
        [Parameter(Mandatory = $true)][string]   $SystemMediaDir,
        [Parameter(Mandatory = $true)][object]   $Definitions,
        [Parameter(Mandatory = $true)][string]   $BackupRoot,
        [Parameter(Mandatory = $true)][hashtable] $Stats,
        [switch] $DryRun
    )
    Get-ChildItem -LiteralPath $SrcDir -File -Recurse -ErrorAction SilentlyContinue | ForEach-Object {
        $cls = Get-MediaClassification -FilePath $_.FullName -Definitions $Definitions -SourceFolderName $SrcFolderName
        if (-not $cls.EsdeFolder) { $Stats.Skipped++; return }
        # Normalise the destination name: strip a scraper suffix so it matches the ROM stem.
        $stem = [System.IO.Path]::GetFileNameWithoutExtension($_.Name)
        $stem = ($stem -replace '(-image|-thumb|-thumbnail|-boxart|-box2dfront|-cover|-marquee|-wheel|-logo|-fanart|-video|-manual|-title|-titleshot|-screenshot|-ss|-mix|-cart|-cartridge|-disc|-box3d|-boxback|-backcover)$', '')
        $dest = Join-Path (Join-Path $SystemMediaDir $cls.EsdeFolder) ($stem + $_.Extension)
        $r = Copy-MediaSafe -Source $_.FullName -Dest $dest -BackupRoot $BackupRoot -DryRun:$DryRun
        if ($r -in @('copied','overwritten')) { $Stats.FromFolders++ }
        elseif ($r -eq 'error') { $Stats.Errors++ }
        else { $Stats.Skipped++ }
    }
}

# ----- module: MetadataRepair -----
<#
.SYNOPSIS
    Metadata / gamelist.xml engine: parse, validate, repair and write clean XML.
.DESCRIPTION
    Parses ES-DE / EmulationStation gamelist.xml files, exposes game entries with
    their media tags, repairs broken or missing media references (re-pointing them
    at existing downloaded_media where possible), removes duplicate <game> entries
    and invalid references, and writes back well-formed XML (after a backup).
#>

Set-StrictMode -Version Latest

# Media tags understood in gamelist.xml (ES + ES-DE + RetroBat supersets).
$script:MediaTags = @('image','thumbnail','marquee','video','fanart','titleshot',
                      'titlescreen','manual','boxart','wheel','mix','miximage',
                      'cartridge','boxback','screenshot')

function Read-Gamelist {
    <#
    .SYNOPSIS
        Loads a gamelist.xml and returns @{ Xml; Games(array of XmlNode); Ok; Error }.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][string] $Path)

    $result = @{ Xml = $null; Games = @(); Ok = $false; Error = $null; Prefix = '' }
    if (-not (Test-Path -LiteralPath $Path)) { $result.Error = 'not found'; return $result }
    try {
        $raw = Get-Content -LiteralPath $Path -Raw -Encoding UTF8
        # ES-DE gamelists can contain TWO top-level elements: an optional
        # <alternativeEmulator>...</alternativeEmulator> block followed by
        # <gameList>...</gameList>. That is not a single-rooted XML document, so
        # [xml] rejects it. Extract just the gameList element for parsing and keep
        # everything before it as a prefix to write back verbatim (preserving the
        # per-system standalone-emulator choice).
        $startIdx = $raw.IndexOf('<gameList')
        if ($startIdx -ge 0) {
            $endTag = '</gameList>'
            $endIdx = $raw.LastIndexOf($endTag)
            if ($endIdx -ge 0) {
                $glText = $raw.Substring($startIdx, ($endIdx - $startIdx) + $endTag.Length)
            } else {
                $glText = $raw.Substring($startIdx)   # self-closed / unterminated
            }
            $result.Prefix = $raw.Substring(0, $startIdx).TrimEnd()
            [xml]$xml = $glText
        } else {
            [xml]$xml = $raw
        }
        $result.Xml = $xml
        if ($xml.gameList) {
            $result.Games = @($xml.gameList.SelectNodes('game'))
        }
        $result.Ok = $true
    } catch {
        $result.Error = $_.Exception.Message
    }
    return $result
}

function Get-GameMediaTags { return $script:MediaTags }

function Get-RelativePathManual {
    <#
    .SYNOPSIS
        Returns a forward-slash relative path from a directory to a file, including
        ../ segments when needed (works on Windows PowerShell 5.1 via System.Uri).
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string] $FromDir,
        [Parameter(Mandatory = $true)][string] $ToPath
    )
    try {
        $fromUri = New-Object System.Uri(($FromDir.TrimEnd('\','/') + [System.IO.Path]::DirectorySeparatorChar))
        $toUri   = New-Object System.Uri($ToPath)
        $rel     = [Uri]::UnescapeDataString($fromUri.MakeRelativeUri($toUri).ToString())
        $rel     = $rel -replace '\\','/'
        if (-not $rel.StartsWith('.')) { $rel = './' + $rel }
        return $rel
    } catch {
        return ('./' + (Split-Path $ToPath -Leaf))
    }
}

function Resolve-RelativeMediaPath {
    <#
    .SYNOPSIS
        Resolves a gamelist media path (often "./images/x.png") against the
        gamelist's directory. Returns an absolute path (may not exist).
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string] $BaseDir,
        [Parameter(Mandatory = $true)][string] $RelPath
    )
    $p = $RelPath -replace '/', '\'
    $p = $p -replace '^\.\\', ''
    if ([System.IO.Path]::IsPathRooted($p)) { return $p }
    return [System.IO.Path]::GetFullPath((Join-Path $BaseDir $p))
}

function Repair-Gamelist {
    <#
    .SYNOPSIS
        Repairs a gamelist: removes duplicate <game> entries (same <path>),
        re-points media tags to existing files in the system's downloaded_media
        when the referenced file is missing, strips media references that cannot
        be resolved, and writes clean XML after backing up.
    .OUTPUTS
        Hashtable of statistics.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string] $GamelistPath,
        [Parameter(Mandatory = $true)][string] $MediaDir,       # downloaded_media\<system>
        [Parameter(Mandatory = $true)][string] $BackupRoot,
        [Parameter(Mandatory = $true)][scriptblock] $Logger,
        [switch] $DryRun
    )

    $stats = @{ Games = 0; Duplicates = 0; Repaired = 0; Removed = 0; Invalid = $false; Changed = $false }

    $g = Read-Gamelist -Path $GamelistPath
    if (-not $g.Ok) {
        & $Logger "Invalid/parse-failed gamelist: $GamelistPath ($($g.Error))" 'ERROR'
        $stats.Invalid = $true
        return $stats
    }
    $baseDir = Split-Path $GamelistPath -Parent
    $xml     = $g.Xml
    $prefix  = $g.Prefix
    $stats.Games = @($g.Games).Count

    # Index existing media files by stem within each ES-DE media subfolder.
    $mediaIndex = @{}
    if (Test-Path -LiteralPath $MediaDir) {
        Get-ChildItem -LiteralPath $MediaDir -Directory -ErrorAction SilentlyContinue | ForEach-Object {
            $folder = $_.Name.ToLower()
            $mediaIndex[$folder] = @{}
            Get-ChildItem -LiteralPath $_.FullName -File -ErrorAction SilentlyContinue | ForEach-Object {
                $mediaIndex[$folder][[System.IO.Path]::GetFileNameWithoutExtension($_.Name).ToLower()] = $_.FullName
            }
        }
    }

    # 1) De-duplicate games by <path>.
    $seen = @{}
    foreach ($game in @($g.Games)) {
        $path = $null
        if ($game.SelectSingleNode('path')) { $path = $game.SelectSingleNode('path').InnerText }
        if (-not $path) { continue }
        $key = $path.ToLower()
        if ($seen.ContainsKey($key)) {
            $stats.Duplicates++
            if (-not $DryRun) { [void]$game.ParentNode.RemoveChild($game) }
            continue
        }
        $seen[$key] = $true
    }

    # 2) Repair / strip media references.
    $tagToFolder = @{
        image='covers'; thumbnail='covers'; boxart='covers'; marquee='marquees'; wheel='marquees';
        fanart='fanart'; video='videos'; manual='manuals'; titleshot='titlescreens'; titlescreen='titlescreens';
        mix='miximages'; miximage='miximages'; cartridge='physicalmedia'; boxback='backcovers'; screenshot='screenshots'
    }
    foreach ($game in @($xml.gameList.SelectNodes('game'))) {
        $romStem = $null
        if ($game.SelectSingleNode('path')) {
            $romStem = [System.IO.Path]::GetFileNameWithoutExtension($game.SelectSingleNode('path').InnerText)
        }
        foreach ($tag in $script:MediaTags) {
            $node = $game.SelectSingleNode($tag)
            if (-not $node) { continue }
            $ref = $node.InnerText
            if ([string]::IsNullOrWhiteSpace($ref)) { continue }
            $abs = Resolve-RelativeMediaPath -BaseDir $baseDir -RelPath $ref
            if (Test-Path -LiteralPath $abs) { continue }   # reference is valid

            # Try to re-point to an existing downloaded_media file by stem.
            $folder = if ($tagToFolder.ContainsKey($tag)) { $tagToFolder[$tag] } else { $null }
            $fixed = $false
            if ($folder -and $romStem -and $mediaIndex.ContainsKey($folder)) {
                $stemKey = $romStem.ToLower()
                if ($mediaIndex[$folder].ContainsKey($stemKey)) {
                    $target = $mediaIndex[$folder][$stemKey]
                    # downloaded_media is a SIBLING of gamelists, so compute a true
                    # relative path (handles ../) rather than assuming containment.
                    $rel = Get-RelativePathManual -FromDir $baseDir -ToPath $target
                    if (-not $DryRun) { $node.InnerText = $rel }
                    $stats.Repaired++; $stats.Changed = $true; $fixed = $true
                }
            }
            if (-not $fixed) {
                # Unresolvable reference -> remove it so ES-DE falls back to auto media.
                if (-not $DryRun) { [void]$game.RemoveChild($node) }
                $stats.Removed++; $stats.Changed = $true
            }
        }
    }

    if (($stats.Changed -or $stats.Duplicates -gt 0) -and -not $DryRun) {
        Backup-File -Path $GamelistPath -BackupRoot $BackupRoot | Out-Null
        Save-Gamelist -Xml $xml -Prefix $prefix -Path $GamelistPath
        & $Logger "Repaired gamelist $GamelistPath (dupes=$($stats.Duplicates), fixed=$($stats.Repaired), stripped=$($stats.Removed))." 'SUCCESS'
    } elseif ($DryRun -and ($stats.Changed -or $stats.Duplicates -gt 0)) {
        & $Logger "[DRY-RUN] Would repair $GamelistPath (dupes=$($stats.Duplicates), fixed=$($stats.Repaired), stripped=$($stats.Removed))." 'INFO'
    }
    return $stats
}

function Save-XmlClean {
    <#
    .SYNOPSIS
        Writes an [xml] document with consistent indentation and UTF-8 (no BOM).
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][xml] $Xml,
        [Parameter(Mandatory = $true)][string] $Path
    )
    $dir = Split-Path $Path -Parent
    if ($dir -and -not (Test-Path -LiteralPath $dir)) { New-Item -Path $dir -ItemType Directory -Force | Out-Null }

    $settings = New-Object System.Xml.XmlWriterSettings
    $settings.Indent = $true
    $settings.IndentChars = '  '
    $settings.Encoding = New-Object System.Text.UTF8Encoding($false)
    $settings.OmitXmlDeclaration = $false
    $writer = [System.Xml.XmlWriter]::Create($Path, $settings)
    try { $Xml.Save($writer) } finally { $writer.Dispose() }
}

function Save-Gamelist {
    <#
    .SYNOPSIS
        Writes a gamelist back in ES-DE's exact format: an optional prefix (the XML
        declaration and any <alternativeEmulator> block) followed by the indented
        <gameList> element. Preserves the per-system standalone-emulator choice.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][xml] $Xml,
        [AllowEmptyString()][string] $Prefix = '',
        [Parameter(Mandatory = $true)][string] $Path
    )
    $dir = Split-Path $Path -Parent
    if ($dir -and -not (Test-Path -LiteralPath $dir)) { New-Item -Path $dir -ItemType Directory -Force | Out-Null }

    # Serialize just the gameList element (no XML declaration) with indentation.
    $settings = New-Object System.Xml.XmlWriterSettings
    $settings.Indent = $true
    $settings.IndentChars = '  '
    $settings.OmitXmlDeclaration = $true
    $sb = New-Object System.Text.StringBuilder
    $sw = New-Object System.IO.StringWriter($sb)
    $writer = [System.Xml.XmlWriter]::Create($sw, $settings)
    try { $Xml.Save($writer) } finally { $writer.Dispose(); $sw.Dispose() }
    $glText = $sb.ToString()

    $nl = "`r`n"
    if ([string]::IsNullOrWhiteSpace($Prefix)) {
        $out = '<?xml version="1.0"?>' + $nl + $glText
    } elseif ($Prefix -match '<\?xml') {
        $out = $Prefix + $nl + $glText
    } else {
        $out = '<?xml version="1.0"?>' + $nl + $Prefix + $nl + $glText
    }
    [System.IO.File]::WriteAllText($Path, $out, (New-Object System.Text.UTF8Encoding($false)))
}

# ----- module: GamelistEnrich -----
<#
.SYNOPSIS
    Gamelist metadata enrichment & hygiene (dual-root aware, backup-first).
.DESCRIPTION
    Improves gamelist.xml quality in a single safe pass:
      * fill missing <name> from the ROM filename
      * add <sortname> for leading articles (The/A/An) so ES-DE sorts correctly
      * strip empty/whitespace-only metadata tags
      * convert absolute media paths to portable relative ones
      * mark obvious BIOS/boot-disc entries as <hidden>
    Plus read-only analytics: scraped-vs-unscraped ratio and duplicate names.
#>

Set-StrictMode -Version Latest

$script:HygieneTags = @('desc','rating','releasedate','developer','publisher','genre','players',
                        'image','thumbnail','marquee','video','fanart','titleshot','manual','boxback')

function Optimize-GamelistMetadata {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string] $GamelistPath,
        [Parameter(Mandatory = $true)][string] $SystemRomDir,
        [Parameter(Mandatory = $true)][string] $BackupRoot,
        [Parameter(Mandatory = $true)][scriptblock] $Logger,
        [switch] $DryRun
    )
    $stats = @{ Filled=0; SortNames=0; Emptied=0; Relativized=0; Hidden=0; Changed=$false }
    if (-not (Test-Path -LiteralPath $GamelistPath)) { return $stats }
    $g = Read-Gamelist -Path $GamelistPath
    if (-not $g.Ok) { return $stats }
    $xml = $g.Xml; $baseDir = Split-Path $GamelistPath -Parent

    foreach ($game in @($xml.gameList.SelectNodes('game'))) {
        $pathNode = $game.SelectSingleNode('path')
        $romStem = if ($pathNode -and $pathNode.InnerText) { [System.IO.Path]::GetFileNameWithoutExtension($pathNode.InnerText) } else { $null }

        # 1) Fill missing <name>.
        $nameNode = $game.SelectSingleNode('name')
        if ((-not $nameNode -or [string]::IsNullOrWhiteSpace($nameNode.InnerText)) -and $romStem) {
            if (-not $nameNode) { $nameNode = $xml.CreateElement('name'); [void]$game.AppendChild($nameNode) }
            $nameNode.InnerText = $romStem; $stats.Filled++; $stats.Changed = $true
        }

        # 2) <sortname> for leading articles.
        if ($nameNode -and $nameNode.InnerText -match '^(The|A|An)\s+(.*)$') {
            $sort = ('{0}, {1}' -f $Matches[2], $Matches[1])
            $sn = $game.SelectSingleNode('sortname')
            if (-not $sn) { $sn = $xml.CreateElement('sortname'); [void]$game.AppendChild($sn) }
            if ($sn.InnerText -ne $sort) { $sn.InnerText = $sort; $stats.SortNames++; $stats.Changed = $true }
        }

        # 3) Strip empty metadata tags.
        foreach ($tag in $script:HygieneTags) {
            foreach ($n in @($game.SelectNodes($tag))) {
                if (-not $n.HasChildNodes -or [string]::IsNullOrWhiteSpace($n.InnerText)) {
                    [void]$game.RemoveChild($n); $stats.Emptied++; $stats.Changed = $true
                }
            }
        }

        # 4) Absolute media paths -> relative.
        foreach ($tag in @('image','thumbnail','marquee','video','fanart','titleshot','manual','boxback')) {
            $n = $game.SelectSingleNode($tag)
            if (-not $n -or [string]::IsNullOrWhiteSpace($n.InnerText)) { continue }
            $val = $n.InnerText
            if ([System.IO.Path]::IsPathRooted($val) -and (Test-Path -LiteralPath $val)) {
                $n.InnerText = Get-RelativePathManual -FromDir $baseDir -ToPath $val
                $stats.Relativized++; $stats.Changed = $true
            }
        }

        # 5) Mark BIOS/boot-disc as hidden.
        $hay = ''
        if ($nameNode) { $hay += $nameNode.InnerText }
        if ($pathNode) { $hay += ' ' + $pathNode.InnerText }
        if ($hay -match '(?i)\b(bios|boot ?disc|\[bios\]|firmware)\b') {
            $h = $game.SelectSingleNode('hidden')
            if (-not $h) { $h = $xml.CreateElement('hidden'); [void]$game.AppendChild($h) }
            if ($h.InnerText -ne 'true') { $h.InnerText = 'true'; $stats.Hidden++; $stats.Changed = $true }
        }
    }

    if ($stats.Changed -and -not $DryRun) {
        Backup-File -Path $GamelistPath -BackupRoot $BackupRoot | Out-Null
        Save-Gamelist -Xml $xml -Prefix $g.Prefix -Path $GamelistPath
        & $Logger "Enriched $(Split-Path (Split-Path $GamelistPath -Parent) -Leaf): names+$($stats.Filled), sortnames+$($stats.SortNames), emptied-$($stats.Emptied), rel+$($stats.Relativized), hidden+$($stats.Hidden)." 'SUCCESS'
    } elseif ($stats.Changed -and $DryRun) {
        & $Logger "[DRY-RUN] Would enrich $GamelistPath (filled=$($stats.Filled), sortnames=$($stats.SortNames))." 'INFO'
    }
    return $stats
}

function Get-ScrapeRatio {
    <#
    .SYNOPSIS
        Returns how many games are 'scraped' (have a description) vs total.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][string] $SystemName, [string] $GamelistPath)
    $total = 0; $scraped = 0; $dupNames = 0
    if ($GamelistPath -and (Test-Path -LiteralPath $GamelistPath)) {
        $g = Read-Gamelist -Path $GamelistPath
        if ($g.Ok) {
            $names = @{}
            foreach ($game in @($g.Games)) {
                $total++
                $d = $game.SelectSingleNode('desc')
                if ($d -and -not [string]::IsNullOrWhiteSpace($d.InnerText)) { $scraped++ }
                $nm = $game.SelectSingleNode('name')
                if ($nm -and $nm.InnerText) {
                    $k = $nm.InnerText.ToLower()
                    if ($names.ContainsKey($k)) { $dupNames++ } else { $names[$k] = $true }
                }
            }
        }
    }
    $pct = if ($total -gt 0) { [math]::Round(($scraped*100.0)/$total,1) } else { 0 }
    return @{ System=$SystemName; Total=$total; Scraped=$scraped; Percent=$pct; DuplicateNames=$dupNames }
}

# ----- module: GamelistQuality -----
<#
.SYNOPSIS
    Gamelist quality engine: m3u validation, metadata sanity repair, players-field
    normalization, region metadata, and adding unlisted ROMs to the gamelist.
    All write operations back up first and are dual-root safe.
#>

Set-StrictMode -Version Latest

function Test-M3uPlaylists {
    <#
    .SYNOPSIS
        Validates that .m3u entries reference existing files. Returns count of
        playlists with at least one broken reference.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][string] $SystemRomDir)
    $broken = 0
    if (-not (Test-Path -LiteralPath $SystemRomDir)) { return 0 }
    Get-ChildItem -LiteralPath $SystemRomDir -File -Filter '*.m3u' -Recurse -Depth 2 -ErrorAction SilentlyContinue | ForEach-Object {
        $dir = Split-Path $_.FullName -Parent
        $bad = $false
        foreach ($line in (Get-Content -LiteralPath $_.FullName -Encoding UTF8 -ErrorAction SilentlyContinue)) {
            $p = $line.Trim(); if (-not $p -or $p.StartsWith('#')) { continue }
            $target = if ([System.IO.Path]::IsPathRooted($p)) { $p } else { Join-Path $dir $p }
            if (-not (Test-Path -LiteralPath $target)) { $bad = $true }
        }
        if ($bad) { $broken++ }
    }
    return $broken
}

function Repair-MetadataSanity {
    <#
    .SYNOPSIS
        Fixes obviously-invalid metadata: ratings outside 0..1, future release dates,
        negative playtime/playcount. Returns count of fields corrected.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string] $GamelistPath,
        [Parameter(Mandatory = $true)][string] $BackupRoot,
        [Parameter(Mandatory = $true)][scriptblock] $Logger,
        [switch] $DryRun
    )
    if (-not (Test-Path -LiteralPath $GamelistPath)) { return 0 }
    $g = Read-Gamelist -Path $GamelistPath
    if (-not $g.Ok) { return 0 }
    $fixed = 0; $changed = $false
    $thisYear = (Get-Date).Year
    foreach ($game in @($g.Xml.gameList.SelectNodes('game'))) {
        $r = $game.SelectSingleNode('rating')
        if ($r -and $r.InnerText) { $v=0.0; if ([double]::TryParse($r.InnerText,[ref]$v)) { if ($v -gt 1 -or $v -lt 0) { if (-not $DryRun) { $r.InnerText = ([math]::Min(1,[math]::Max(0,$v/([math]::Ceiling($v))))).ToString('0.0') }; $fixed++; $changed=$true } } }
        $rd = $game.SelectSingleNode('releasedate')
        if ($rd -and $rd.InnerText -match '^(\d{4})') { if ([int]$Matches[1] -gt ($thisYear+1)) { if (-not $DryRun) { [void]$game.RemoveChild($rd) }; $fixed++; $changed=$true } }
        foreach ($tag in @('playtime','playcount')) {
            $n = $game.SelectSingleNode($tag)
            if ($n -and $n.InnerText) { $iv=0; if ([int]::TryParse($n.InnerText,[ref]$iv)) { if ($iv -lt 0) { if (-not $DryRun) { $n.InnerText = '0' }; $fixed++; $changed=$true } } }
        }
    }
    if ($changed -and -not $DryRun) {
        Backup-File -Path $GamelistPath -BackupRoot $BackupRoot | Out-Null
        Save-Gamelist -Xml $g.Xml -Prefix $g.Prefix -Path $GamelistPath
        & $Logger "Sanity-fixed $fixed metadata field(s) in $(Split-Path (Split-Path $GamelistPath -Parent) -Leaf)." 'SUCCESS'
    }
    return $fixed
}

function Add-UnlistedGames {
    <#
    .SYNOPSIS
        Adds <game> entries for ROM files present on disk but missing from the
        gamelist (so ES-DE shows them with at least a name). Returns count added.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string] $GamelistPath,
        [Parameter(Mandatory = $true)][string] $SystemRomDir,
        [Parameter(Mandatory = $true)][string] $BackupRoot,
        [Parameter(Mandatory = $true)][scriptblock] $Logger,
        [switch] $DryRun
    )
    if (-not (Test-Path -LiteralPath $SystemRomDir)) { return 0 }
    $nonRom = @('.txt','.xml','.dat','.jpg','.png','.bin','.srm','.state','.cfg','.sav','.cht')
    $g = Read-Gamelist -Path $GamelistPath
    $xml = $null; $prefix = ''
    if ($g.Ok) { $xml = $g.Xml; $prefix = $g.Prefix }
    else {
        $xml = New-Object System.Xml.XmlDocument
        [void]$xml.AppendChild($xml.CreateElement('gameList'))
        $prefix = '<?xml version="1.0"?>'
    }
    $listed = New-Object System.Collections.Generic.HashSet[string] ([StringComparer]::OrdinalIgnoreCase)
    foreach ($game in @($xml.gameList.SelectNodes('game'))) {
        $pn = $game.SelectSingleNode('path'); if ($pn -and $pn.InnerText) { [void]$listed.Add([System.IO.Path]::GetFileName(($pn.InnerText -replace '/','\'))) }
    }
    $added = 0
    Get-ChildItem -LiteralPath $SystemRomDir -File -ErrorAction SilentlyContinue | ForEach-Object {
        if ($nonRom -contains $_.Extension.ToLower()) { return }
        if ($_.Extension.ToLower() -eq '.bin' -and (Test-Path -LiteralPath ([System.IO.Path]::ChangeExtension($_.FullName,'cue')))) { return }
        if ($listed.Contains($_.Name)) { return }
        if (-not $DryRun) {
            $game = $xml.CreateElement('game')
            $p = $xml.CreateElement('path'); $p.InnerText = './' + $_.Name; [void]$game.AppendChild($p)
            $n = $xml.CreateElement('name'); $n.InnerText = [System.IO.Path]::GetFileNameWithoutExtension($_.Name); [void]$game.AppendChild($n)
            [void]$xml.gameList.AppendChild($game)
        }
        $added++
    }
    if ($added -gt 0 -and -not $DryRun) {
        Backup-File -Path $GamelistPath -BackupRoot $BackupRoot | Out-Null
        Save-Gamelist -Xml $xml -Prefix $prefix -Path $GamelistPath
        & $Logger "Added $added unlisted ROM(s) to $(Split-Path (Split-Path $GamelistPath -Parent) -Leaf) gamelist." 'SUCCESS'
    }
    return $added
}

# ----- module: DuplicateDetection -----
<#
.SYNOPSIS
    Duplicate detection engine (SHA256). Finds byte-identical media files and
    reclaims space only for redundant copies inside the SAME media subfolder
    (after backing them up). Cross-folder identical files (legitimately shared,
    e.g. a cover reused as a miximage source) are reported but never removed.
#>

Set-StrictMode -Version Latest

function Find-DuplicateMedia {
    <#
    .SYNOPSIS
        Hashes every media file under a media directory and groups identical files.
    .OUTPUTS
        Hashtable: Groups (array of @{Hash;Files}), TotalFiles, DuplicateFiles,
        ReclaimableBytes.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string] $MediaDir,
        [string] $CacheFile
    )

    # Optional persistent hash cache keyed by path -> "size|mtimeTicks|sha256" so
    # unchanged files are not re-hashed on subsequent runs (big speed-up on large
    # libraries). Cache is validated by size+last-write-time.
    $cache = @{}
    if ($CacheFile -and (Test-Path -LiteralPath $CacheFile)) {
        try {
            foreach ($line in (Get-Content -LiteralPath $CacheFile -Encoding UTF8 -ErrorAction SilentlyContinue)) {
                $i = $line.IndexOf('|'); if ($i -lt 1) { continue }
                $cache[$line.Substring(0,$i)] = $line.Substring($i+1)
            }
        } catch { }
    }
    $newCache = New-Object System.Collections.Generic.List[string]

    $byHash = @{}
    $total  = 0
    if (Test-Path -LiteralPath $MediaDir) {
        Get-ChildItem -LiteralPath $MediaDir -File -Recurse -ErrorAction SilentlyContinue | ForEach-Object {
            $sig = "$($_.Length)|$($_.LastWriteTimeUtc.Ticks)"
            $h = $null
            if ($cache.ContainsKey($_.FullName)) {
                $cached = $cache[$_.FullName]
                $bar = $cached.LastIndexOf('|')
                if ($bar -gt 0 -and $cached.Substring(0,$bar) -eq $sig) { $h = $cached.Substring($bar+1) }
            }
            if (-not $h) { $h = Get-FileSha256 -Path $_.FullName }
            if (-not $h) { return }
            if ($CacheFile) { $newCache.Add("$($_.FullName)|$sig|$h") }
            $total++
            if (-not $byHash.ContainsKey($h)) { $byHash[$h] = New-Object System.Collections.Generic.List[object] }
            $byHash[$h].Add($_)
        }
    }
    if ($CacheFile -and $newCache.Count -gt 0) {
        try {
            $cd = Split-Path $CacheFile -Parent
            if ($cd -and -not (Test-Path -LiteralPath $cd)) { New-Item -Path $cd -ItemType Directory -Force | Out-Null }
            [System.IO.File]::WriteAllLines($CacheFile, $newCache.ToArray(), (New-Object System.Text.UTF8Encoding($false)))
        } catch { }
    }

    $groups = New-Object System.Collections.Generic.List[object]
    $dupCount = 0; $reclaim = 0
    foreach ($h in $byHash.Keys) {
        $files = $byHash[$h]
        if ($files.Count -gt 1) {
            $dupCount += ($files.Count - 1)
            $reclaim  += ($files[0].Length * ($files.Count - 1))
            $groups.Add(@{ Hash = $h; Files = @($files | ForEach-Object { $_.FullName }) })
        }
    }
    return @{ Groups = $groups.ToArray(); TotalFiles = $total; DuplicateFiles = $dupCount; ReclaimableBytes = $reclaim }
}

function Invoke-DuplicateCleanup {
    <#
    .SYNOPSIS
        Removes redundant duplicates that share the SAME parent folder (keeping the
        first), backing each up first. Returns count removed.
    #>
    [CmdletBinding()]
    param(
        [object[]] $Groups = @(),
        [Parameter(Mandatory = $true)][string]   $BackupRoot,
        [Parameter(Mandatory = $true)][scriptblock] $Logger,
        [switch] $DryRun
    )
    $removed = 0
    if (-not $Groups -or $Groups.Count -eq 0) { return 0 }
    foreach ($g in $Groups) {
        $byFolder = @{}
        foreach ($f in $g.Files) {
            $dir = Split-Path $f -Parent
            if (-not $byFolder.ContainsKey($dir)) { $byFolder[$dir] = New-Object System.Collections.Generic.List[string] }
            $byFolder[$dir].Add($f)
        }
        foreach ($dir in $byFolder.Keys) {
            $list = $byFolder[$dir]
            if ($list.Count -le 1) { continue }   # keep cross-folder copies
            for ($i = 1; $i -lt $list.Count; $i++) {
                if ($DryRun) { & $Logger "[DRY-RUN] Would remove duplicate: $($list[$i])" 'INFO'; $removed++; continue }
                Backup-File -Path $list[$i] -BackupRoot $BackupRoot | Out-Null
                Remove-Item -LiteralPath $list[$i] -Force -ErrorAction SilentlyContinue
                & $Logger "Removed duplicate (backed up): $($list[$i])" 'SUCCESS'
                $removed++
            }
        }
    }
    return $removed
}

# ----- module: MissingMedia -----
<#
.SYNOPSIS
    Missing-media analyzer and BIOS validator.
.DESCRIPTION
    For every game in a system (resolved from the gamelist or the ROM files),
    determines which ES-DE media types are missing (covers, screenshots, videos,
    marquees, fanart, manuals, titlescreens) by checking downloaded_media by stem.
    Also validates BIOS folders against a known requirement table (report only).
#>

Set-StrictMode -Version Latest

# Media types considered "important" for the missing-media report.
$script:ReportTypes = @('covers','screenshots','videos','marquees','fanart','titlescreens','manuals')

# ROM extensions to ignore when enumerating games from the filesystem.
$script:NonRomExt = @('.txt','.xml','.dat','.cfg','.ini','.jpg','.png','.bin','.cue','.m3u','.srm','.state')

function Get-SystemGameStems {
    <#
    .SYNOPSIS
        Returns the set of game "stems" (ROM file names without extension) for a
        system, preferring gamelist paths and falling back to the ROM folder.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string] $SystemRomDir,
        [string] $GamelistPath
    )
    $stems = New-Object System.Collections.Generic.HashSet[string] ([StringComparer]::OrdinalIgnoreCase)

    if ($GamelistPath -and (Test-Path -LiteralPath $GamelistPath)) {
        $g = Read-Gamelist -Path $GamelistPath
        if ($g.Ok) {
            foreach ($game in @($g.Games)) {
                $pn = $game.SelectSingleNode('path')
                if ($pn -and $pn.InnerText) { [void]$stems.Add([System.IO.Path]::GetFileNameWithoutExtension($pn.InnerText)) }
            }
        }
    }
    if ($stems.Count -eq 0 -and (Test-Path -LiteralPath $SystemRomDir)) {
        Get-ChildItem -LiteralPath $SystemRomDir -File -ErrorAction SilentlyContinue | ForEach-Object {
            if ($_.Extension.ToLower() -in $script:NonRomExt) { return }
            [void]$stems.Add([System.IO.Path]::GetFileNameWithoutExtension($_.Name))
        }
    }
    # Return with the unary comma so PowerShell does not enumerate the HashSet
    # (a single-element set would otherwise unroll to a bare string).
    return ,$stems
}

function Get-MissingMediaForSystem {
    <#
    .SYNOPSIS
        Returns per-game missing-media records for a system.
    .OUTPUTS
        Hashtable: System, Games(int), Records(array of @{Game;Missing[]}), Totals(hashtable by type)
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string] $SystemName,
        [Parameter(Mandatory = $true)][string] $SystemRomDir,
        [Parameter(Mandatory = $true)][string] $SystemMediaDir,
        [string] $GamelistPath
    )

    $stems = Get-SystemGameStems -SystemRomDir $SystemRomDir -GamelistPath $GamelistPath

    # Build presence index: type -> set of stems present.
    $present = @{}
    foreach ($t in $script:ReportTypes) {
        $present[$t] = New-Object System.Collections.Generic.HashSet[string] ([StringComparer]::OrdinalIgnoreCase)
        $dir = Join-Path $SystemMediaDir $t
        if (Test-Path -LiteralPath $dir) {
            Get-ChildItem -LiteralPath $dir -File -ErrorAction SilentlyContinue | ForEach-Object {
                [void]$present[$t].Add([System.IO.Path]::GetFileNameWithoutExtension($_.Name))
            }
        }
    }

    $records = New-Object System.Collections.Generic.List[object]
    $totals  = @{}; foreach ($t in $script:ReportTypes) { $totals[$t] = 0 }

    foreach ($stem in $stems) {
        $missing = New-Object System.Collections.Generic.List[string]
        foreach ($t in $script:ReportTypes) {
            if (-not $present[$t].Contains($stem)) { $missing.Add($t); $totals[$t]++ }
        }
        if ($missing.Count -gt 0) {
            $records.Add(@{ Game = $stem; Missing = $missing.ToArray() })
        }
    }

    return @{ System = $SystemName; Games = $stems.Count; Records = $records.ToArray(); Totals = $totals }
}

function Test-BiosDirectory {
    <#
    .SYNOPSIS
        Reports which known BIOS files are missing under a BIOS directory.
        Never deletes anything.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string] $BiosDir,
        [Parameter(Mandatory = $true)][object[]] $Requirements,
        [Parameter(Mandatory = $true)][scriptblock] $Logger
    )
    $issues = New-Object System.Collections.Generic.List[object]
    if (-not (Test-Path -LiteralPath $BiosDir)) {
        & $Logger "BIOS directory not found: $BiosDir" 'WARN'
        return @{ Dir = $BiosDir; Missing = $issues.ToArray(); Present = 0 }
    }
    $present = @{}
    Get-ChildItem -LiteralPath $BiosDir -Recurse -File -ErrorAction SilentlyContinue | ForEach-Object {
        $present[$_.Name.ToLower()] = $_.FullName
    }
    foreach ($req in $Requirements) {
        if (-not $present.ContainsKey($req.file.ToLower())) {
            & $Logger "Missing BIOS: $($req.file) (needed for $($req.system))" 'WARN'
            $issues.Add(@{ File = $req.file; System = $req.system })
        }
    }
    return @{ Dir = $BiosDir; Missing = $issues.ToArray(); Present = $present.Count }
}

# ----- module: MediaRecovery -----
<#
.SYNOPSIS
    Local media recovery and scrape-list export.
.DESCRIPTION
    * Recovers media that already exists but is named slightly differently from the
      ROM (e.g. region/version tags differ): it fuzzy-matches by a normalized stem
      and copies the file to the exact ROM stem so ES-DE will display it. This finds
      "missing" media you already have, without any download.
    * Exports a scrape list (the ROM files still missing media) that ES-DE's built-in
      scraper or ScreenScraper can consume.
#>

Set-StrictMode -Version Latest

function Get-NormalizedStem {
    <#
    .SYNOPSIS
        Normalizes a game name for fuzzy matching: drops (region)/[flag] groups,
        lowercases and strips non-alphanumerics.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][string] $Name)
    $s = $Name
    $s = [Regex]::Replace($s, '\([^)]*\)', '')   # (USA), (Rev 1) ...
    $s = [Regex]::Replace($s, '\[[^\]]*\]', '')  # [!], [b1] ...
    $s = $s.ToLower()
    $s = [Regex]::Replace($s, '[^a-z0-9]', '')
    return $s.Trim()
}

function Invoke-LocalMediaRecovery {
    <#
    .SYNOPSIS
        For one system, copies mislabeled media to the exact ROM stem when a fuzzy
        (normalized) match is found. Returns count recovered.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string] $SystemMediaDir,
        [System.Collections.Generic.HashSet[string]] $RomStems,
        [Parameter(Mandatory = $true)][string] $BackupRoot,
        [Parameter(Mandatory = $true)][scriptblock] $Logger,
        [switch] $DryRun
    )
    $recovered = 0
    if (-not (Test-Path -LiteralPath $SystemMediaDir)) { return 0 }
    if ($null -eq $RomStems -or $RomStems.Count -eq 0) { return 0 }

    # Map normalized -> exact ROM stem.
    $normToExact = @{}
    foreach ($stem in $RomStems) {
        $n = Get-NormalizedStem -Name $stem
        if ($n -and -not $normToExact.ContainsKey($n)) { $normToExact[$n] = $stem }
    }

    foreach ($sub in (Get-ChildItem -LiteralPath $SystemMediaDir -Directory -ErrorAction SilentlyContinue)) {
        foreach ($file in (Get-ChildItem -LiteralPath $sub.FullName -File -ErrorAction SilentlyContinue)) {
            $stem = [System.IO.Path]::GetFileNameWithoutExtension($file.Name)
            if ($RomStems.Contains($stem)) { continue }   # already correctly named
            $norm = Get-NormalizedStem -Name $stem
            if (-not $norm -or -not $normToExact.ContainsKey($norm)) { continue }
            $exact = $normToExact[$norm]
            $target = Join-Path $sub.FullName ($exact + $file.Extension)
            if (Test-Path -LiteralPath $target) { continue }   # correct one already there
            if ($DryRun) { & $Logger "[DRY-RUN] Would recover $($file.Name) -> $exact$($file.Extension)" 'INFO'; $recovered++; continue }
            Copy-Item -LiteralPath $file.FullName -Destination $target -Force
            $recovered++
        }
    }
    if ($recovered -gt 0) { & $Logger "Recovered $recovered mislabeled media file(s) for '$(Split-Path $SystemMediaDir -Leaf)'." 'SUCCESS' }
    return $recovered
}

function Export-ScrapeList {
    <#
    .SYNOPSIS
        Writes the ROM files of games still missing media to a text file, so the
        ES-DE scraper (or ScreenScraper) can target exactly what is needed.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][object]  $MissingResult,   # from Get-MissingMediaForSystem
        [Parameter(Mandatory = $true)][string]  $SystemRomDir,
        [Parameter(Mandatory = $true)][string]  $OutFile
    )
    $lines = New-Object System.Collections.Generic.List[string]
    $romByStem = @{}
    if (Test-Path -LiteralPath $SystemRomDir) {
        Get-ChildItem -LiteralPath $SystemRomDir -File -ErrorAction SilentlyContinue | ForEach-Object {
            $romByStem[[System.IO.Path]::GetFileNameWithoutExtension($_.Name)] = $_.FullName
        }
    }
    foreach ($rec in @($MissingResult.Records)) {
        $path = if ($romByStem.ContainsKey($rec.Game)) { $romByStem[$rec.Game] } else { $rec.Game }
        $lines.Add(('{0}`t{1}' -f $path, ($rec.Missing -join ',')))
    }
    if ($lines.Count -gt 0) {
        $dir = Split-Path $OutFile -Parent
        if ($dir -and -not (Test-Path -LiteralPath $dir)) { New-Item -Path $dir -ItemType Directory -Force | Out-Null }
        $header = "# ES-DE scrape list for $($MissingResult.System) - ROM<TAB>missing media types"
        Set-Content -LiteralPath $OutFile -Value (@($header) + $lines) -Encoding UTF8
    }
    return $lines.Count
}

# ----- module: MediaAudit -----
<#
.SYNOPSIS
    Media audit engine - deep analysis and safe fixes for the ES-DE media library.
.DESCRIPTION
    Adds: media coverage %, per-system/per-type disk usage, image format/extension
    mismatch detection + safe fix, oversized-media detection, video container audit,
    optional ffmpeg frame extraction for games missing a screenshot, ROM<->gamelist
    consistency (orphan entries / unlisted ROMs), play statistics, and a 1G1R
    region-duplicate advisory.
#>

Set-StrictMode -Version Latest

$script:CoverageTypes = @('covers','screenshots','videos','marquees','fanart','titlescreens','manuals','3dboxes')

function Get-MediaCoverage {
    <#
    .SYNOPSIS
        Returns per-system media coverage: for each media type, how many of the
        system's games have that media (count + percentage).
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string] $SystemName,
        [System.Collections.Generic.HashSet[string]] $RomStems,
        [Parameter(Mandatory = $true)][string] $SystemMediaDir
    )
    if ($null -eq $RomStems) { $RomStems = New-Object System.Collections.Generic.HashSet[string] }
    $total = $RomStems.Count
    $cov = [ordered]@{}
    foreach ($t in $script:CoverageTypes) {
        $have = 0
        $dir = Join-Path $SystemMediaDir $t
        if ($total -gt 0 -and (Test-Path -LiteralPath $dir)) {
            $present = New-Object System.Collections.Generic.HashSet[string] ([StringComparer]::OrdinalIgnoreCase)
            Get-ChildItem -LiteralPath $dir -File -ErrorAction SilentlyContinue | ForEach-Object {
                [void]$present.Add([System.IO.Path]::GetFileNameWithoutExtension($_.Name))
            }
            foreach ($s in $RomStems) { if ($present.Contains($s)) { $have++ } }
        }
        $pct = if ($total -gt 0) { [math]::Round(($have * 100.0) / $total, 1) } else { 0 }
        $cov[$t] = @{ Have = $have; Total = $total; Percent = $pct }
    }
    return @{ System = $SystemName; Coverage = $cov }
}

function Get-MediaDiskUsage {
    <#
    .SYNOPSIS
        Returns total bytes and per-type bytes for a system's media folder.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][string] $SystemName, [Parameter(Mandatory = $true)][string] $SystemMediaDir)
    $perType = [ordered]@{}; $total = [int64]0
    if (Test-Path -LiteralPath $SystemMediaDir) {
        foreach ($sub in (Get-ChildItem -LiteralPath $SystemMediaDir -Directory -ErrorAction SilentlyContinue)) {
            $files = @(Get-ChildItem -LiteralPath $sub.FullName -File -Recurse -ErrorAction SilentlyContinue)
            $sum = 0
            if ($files.Count -gt 0) { $sum = ($files | Measure-Object -Property Length -Sum).Sum }
            if (-not $sum) { $sum = 0 }
            $perType[$sub.Name] = [int64]$sum; $total += [int64]$sum
        }
    }
    return @{ System = $SystemName; TotalBytes = $total; PerType = $perType }
}

function Get-ImageMagicType {
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][string] $Path)
    try {
        $fs = [System.IO.File]::OpenRead($Path)
        try {
            $b = New-Object byte[] 12
            $n = $fs.Read($b, 0, 12)
            if ($n -ge 8 -and $b[0] -eq 0x89 -and $b[1] -eq 0x50 -and $b[2] -eq 0x4E -and $b[3] -eq 0x47) { return 'png' }
            if ($n -ge 3 -and $b[0] -eq 0xFF -and $b[1] -eq 0xD8 -and $b[2] -eq 0xFF) { return 'jpg' }
            if ($n -ge 3 -and $b[0] -eq 0x47 -and $b[1] -eq 0x49 -and $b[2] -eq 0x46) { return 'gif' }
            if ($n -ge 2 -and $b[0] -eq 0x42 -and $b[1] -eq 0x4D) { return 'bmp' }
            if ($n -ge 12 -and $b[0] -eq 0x52 -and $b[1] -eq 0x49 -and $b[8] -eq 0x57 -and $b[9] -eq 0x45) { return 'webp' }
        } finally { $fs.Dispose() }
    } catch { }
    return $null
}

function Repair-MediaExtensions {
    <#
    .SYNOPSIS
        Detects image files whose extension does not match their real format and
        renames them to the correct extension (after backup). Returns count fixed.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string] $SystemMediaDir,
        [Parameter(Mandatory = $true)][string] $BackupRoot,
        [Parameter(Mandatory = $true)][scriptblock] $Logger,
        [switch] $DryRun
    )
    $fixed = 0
    if (-not (Test-Path -LiteralPath $SystemMediaDir)) { return 0 }
    $imgExt = @('.png','.jpg','.jpeg','.gif','.bmp','.webp')
    Get-ChildItem -LiteralPath $SystemMediaDir -File -Recurse -ErrorAction SilentlyContinue | Where-Object { $imgExt -contains $_.Extension.ToLower() } | ForEach-Object {
        $real = Get-ImageMagicType -Path $_.FullName
        if (-not $real) { return }
        $cur = $_.Extension.TrimStart('.').ToLower()
        if ($cur -eq 'jpeg') { $cur = 'jpg' }
        if ($real -ne $cur) {
            $target = [System.IO.Path]::ChangeExtension($_.FullName, $real)
            if (Test-Path -LiteralPath $target) { return }
            if ($DryRun) { & $Logger "[DRY-RUN] Would fix extension: $($_.Name) is actually $real" 'INFO'; $fixed++; return }
            Backup-File -Path $_.FullName -BackupRoot $BackupRoot | Out-Null
            Rename-Item -LiteralPath $_.FullName -NewName (Split-Path $target -Leaf) -Force
            $fixed++
        }
    }
    if ($fixed -gt 0) { & $Logger "Fixed $fixed mislabeled image extension(s) in $(Split-Path $SystemMediaDir -Leaf)." 'SUCCESS' }
    return $fixed
}

function Get-OversizedMedia {
    <#
    .SYNOPSIS
        Returns media files larger than a threshold (MB) that may slow ES-DE.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][string] $SystemMediaDir, [int] $ThresholdMB = 8)
    $hits = New-Object System.Collections.Generic.List[object]
    if (Test-Path -LiteralPath $SystemMediaDir) {
        $limit = $ThresholdMB * 1MB
        Get-ChildItem -LiteralPath $SystemMediaDir -File -Recurse -ErrorAction SilentlyContinue | Where-Object { $_.Length -gt $limit -and $_.Extension -notin @('.mp4','.webm','.mkv','.avi') } | ForEach-Object {
            $hits.Add(@{ File = $_.FullName; SizeMB = [math]::Round($_.Length/1MB,1) })
        }
    }
    return $hits.ToArray()
}

function Get-VideoAudit {
    <#
    .SYNOPSIS
        Reports videos whose container is not the ES-DE-friendly mp4/webm, and
        whether ffmpeg is available to convert/extract.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][string] $SystemMediaDir)
    $vids = Join-Path $SystemMediaDir 'videos'
    $nonFriendly = New-Object System.Collections.Generic.List[string]
    $count = 0
    if (Test-Path -LiteralPath $vids) {
        Get-ChildItem -LiteralPath $vids -File -ErrorAction SilentlyContinue | ForEach-Object {
            $count++
            if ($_.Extension.ToLower() -notin @('.mp4','.webm')) { $nonFriendly.Add($_.FullName) }
        }
    }
    return @{ Total = $count; NonFriendly = $nonFriendly.ToArray() }
}

function Test-FfmpegAvailable {
    [CmdletBinding()] param()
    $cmd = Get-Command ffmpeg -ErrorAction SilentlyContinue
    return [bool]$cmd
}

function Invoke-VideoFrameForMissingScreens {
    <#
    .SYNOPSIS
        For games that have a video but no screenshot, extracts a representative
        frame with ffmpeg to create the missing screenshot. Requires ffmpeg.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string] $SystemMediaDir,
        [Parameter(Mandatory = $true)][scriptblock] $Logger,
        [switch] $DryRun
    )
    if (-not (Test-FfmpegAvailable)) { return 0 }
    $vids = Join-Path $SystemMediaDir 'videos'
    $shots = Join-Path $SystemMediaDir 'screenshots'
    if (-not (Test-Path -LiteralPath $vids)) { return 0 }
    if (-not (Test-Path -LiteralPath $shots) -and -not $DryRun) { New-Item -Path $shots -ItemType Directory -Force | Out-Null }
    $made = 0
    Get-ChildItem -LiteralPath $vids -File -ErrorAction SilentlyContinue | ForEach-Object {
        $stem = [System.IO.Path]::GetFileNameWithoutExtension($_.Name)
        $out = Join-Path $shots ($stem + '.png')
        if (Test-Path -LiteralPath $out) { return }
        if ($DryRun) { & $Logger "[DRY-RUN] Would extract screenshot for $stem" 'INFO'; $made++; return }
        try {
            $p = Start-Process -FilePath 'ffmpeg' -ArgumentList @('-y','-ss','3','-i',$_.FullName,'-frames:v','1','-q:v','3',$out) -NoNewWindow -Wait -PassThru -RedirectStandardError ([System.IO.Path]::GetTempFileName())
            if ($p.ExitCode -eq 0 -and (Test-Path -LiteralPath $out)) { $made++ }
        } catch { }
    }
    if ($made -gt 0) { & $Logger "Generated $made screenshot(s) from video via ffmpeg." 'SUCCESS' }
    return $made
}

function Get-RomGamelistConsistency {
    <#
    .SYNOPSIS
        Returns gamelist entries whose ROM file is missing (orphan entries) and
        ROM files not present in the gamelist (unlisted).
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string] $SystemRomDir,
        [string] $GamelistPath
    )
    $orphanEntries = New-Object System.Collections.Generic.List[string]
    $listed = New-Object System.Collections.Generic.HashSet[string] ([StringComparer]::OrdinalIgnoreCase)
    if ($GamelistPath -and (Test-Path -LiteralPath $GamelistPath)) {
        $g = Read-Gamelist -Path $GamelistPath
        if ($g.Ok) {
            foreach ($game in @($g.Games)) {
                $pn = $game.SelectSingleNode('path')
                if (-not $pn -or -not $pn.InnerText) { continue }
                $rel = ($pn.InnerText -replace '/', '\') -replace '^\.\\',''
                [void]$listed.Add([System.IO.Path]::GetFileName($rel))
                $abs = Join-Path $SystemRomDir $rel
                if (-not (Test-Path -LiteralPath $abs)) { $orphanEntries.Add($pn.InnerText) }
            }
        }
    }
    $unlisted = New-Object System.Collections.Generic.List[string]
    if (Test-Path -LiteralPath $SystemRomDir) {
        Get-ChildItem -LiteralPath $SystemRomDir -File -ErrorAction SilentlyContinue | ForEach-Object {
            if ($_.Extension.ToLower() -in @('.txt','.xml','.dat','.jpg','.png')) { return }
            if (-not $listed.Contains($_.Name)) { $unlisted.Add($_.Name) }
        }
    }
    return @{ OrphanEntries = $orphanEntries.ToArray(); Unlisted = $unlisted.ToArray() }
}

function Get-PlayStats {
    <#
    .SYNOPSIS
        Aggregates favorites / playcount / total playtime / most-played title from
        a system's gamelist.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][string] $SystemName, [string] $GamelistPath)
    $fav = 0; $played = 0; $totalTime = 0; $top = ''; $topTime = -1
    if ($GamelistPath -and (Test-Path -LiteralPath $GamelistPath)) {
        $g = Read-Gamelist -Path $GamelistPath
        if ($g.Ok) {
            foreach ($game in @($g.Games)) {
                $f = $game.SelectSingleNode('favorite'); if ($f -and $f.InnerText -eq 'true') { $fav++ }
                $pc = $game.SelectSingleNode('playcount')
                if ($pc -and [int]::TryParse($pc.InnerText, [ref]([int]$null))) { if ([int]$pc.InnerText -gt 0) { $played++ } }
                $pt = $game.SelectSingleNode('playtime')
                if ($pt) { $v = 0; if ([int]::TryParse($pt.InnerText, [ref]$v)) { $totalTime += $v; if ($v -gt $topTime) { $topTime = $v; $n = $game.SelectSingleNode('name'); $top = if ($n) { $n.InnerText } else { '' } } } }
            }
        }
    }
    return @{ System = $SystemName; Favorites = $fav; Played = $played; TotalPlaytimeMin = [math]::Round($totalTime/60); MostPlayed = $top }
}

function Get-RegionDuplicates {
    <#
    .SYNOPSIS
        1G1R advisory: groups ROMs by region-insensitive base name and reports
        groups with more than one regional variant.
    #>
    [CmdletBinding()]
    param([System.Collections.Generic.HashSet[string]] $RomStems)
    if ($null -eq $RomStems -or $RomStems.Count -eq 0) { return @() }
    $byBase = @{}
    foreach ($s in $RomStems) {
        $base = [Regex]::Replace($s, '\s*[\(\[].*$', '').Trim().ToLower()
        if (-not $base) { continue }
        if (-not $byBase.ContainsKey($base)) { $byBase[$base] = New-Object System.Collections.Generic.List[string] }
        $byBase[$base].Add($s)
    }
    $groups = New-Object System.Collections.Generic.List[object]
    foreach ($k in $byBase.Keys) { if ($byBase[$k].Count -gt 1) { $groups.Add(@{ Base = $k; Variants = @($byBase[$k]) }) } }
    return $groups.ToArray()
}

# ----- module: MediaIntegrity -----
<#
.SYNOPSIS
    Media integrity checks and library-wide media analytics.
.DESCRIPTION
    * Quarantine 0-byte (corrupt) media and truncated/unreadable images into the
      backup tree (never deleted).
    * Fix media files that have no extension by detecting their format (magic bytes).
    * Library analytics: media count per type, and the largest media files.
#>

Set-StrictMode -Version Latest

function Test-MediaIntegrity {
    <#
    .SYNOPSIS
        For one system: quarantines 0-byte media and adds the correct extension to
        extension-less image files. Returns @{ Quarantined; Fixed }.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string] $SystemMediaDir,
        [Parameter(Mandatory = $true)][string] $BackupRoot,
        [Parameter(Mandatory = $true)][scriptblock] $Logger,
        [switch] $DryRun
    )
    $stats = @{ Quarantined = 0; Fixed = 0 }
    if (-not (Test-Path -LiteralPath $SystemMediaDir)) { return $stats }
    $qRoot = Join-Path $BackupRoot ('corrupt_media\' + (Split-Path $SystemMediaDir -Leaf))

    Get-ChildItem -LiteralPath $SystemMediaDir -File -Recurse -ErrorAction SilentlyContinue | ForEach-Object {
        # 0-byte -> quarantine
        if ($_.Length -eq 0) {
            if ($DryRun) { $stats.Quarantined++; return }
            if (-not (Test-Path -LiteralPath $qRoot)) { New-Item -Path $qRoot -ItemType Directory -Force | Out-Null }
            Move-Item -LiteralPath $_.FullName -Destination (Join-Path $qRoot $_.Name) -Force -ErrorAction SilentlyContinue
            $stats.Quarantined++; return
        }
        # no extension -> detect by magic and append
        if ([string]::IsNullOrEmpty($_.Extension)) {
            $type = Get-ImageMagicType -Path $_.FullName
            if ($type) {
                if ($DryRun) { $stats.Fixed++; return }
                Rename-Item -LiteralPath $_.FullName -NewName ($_.Name + '.' + $type) -Force -ErrorAction SilentlyContinue
                $stats.Fixed++
            }
        }
    }
    if ($stats.Quarantined -gt 0 -or $stats.Fixed -gt 0) {
        & $Logger "Integrity $(Split-Path $SystemMediaDir -Leaf): quarantined $($stats.Quarantined) corrupt, fixed $($stats.Fixed) extension-less." 'SUCCESS'
    }
    return $stats
}

function Get-MediaTypeTotals {
    <#
    .SYNOPSIS
        Counts media files per ES-DE type across the whole media directory.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][string] $MediaDir)
    $totals = [ordered]@{}
    if (Test-Path -LiteralPath $MediaDir) {
        Get-ChildItem -LiteralPath $MediaDir -Directory -ErrorAction SilentlyContinue | ForEach-Object {
            Get-ChildItem -LiteralPath $_.FullName -Directory -ErrorAction SilentlyContinue | ForEach-Object {
                $t = $_.Name
                $c = @(Get-ChildItem -LiteralPath $_.FullName -File -ErrorAction SilentlyContinue).Count
                if (-not $totals.Contains($t)) { $totals[$t] = 0 }
                $totals[$t] += $c
            }
        }
    }
    return $totals
}

function Get-TopLargestMedia {
    <#
    .SYNOPSIS
        Returns the N largest media files across the library.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][string] $MediaDir, [int] $Top = 25)
    if (-not (Test-Path -LiteralPath $MediaDir)) { return @() }
    return @(Get-ChildItem -LiteralPath $MediaDir -File -Recurse -ErrorAction SilentlyContinue |
        Sort-Object Length -Descending | Select-Object -First $Top |
        ForEach-Object { @{ File = $_.FullName; MB = [math]::Round($_.Length/1MB,2) } })
}

# ----- module: MediaHygiene -----
<#
.SYNOPSIS
    Media hygiene: sanitize illegal characters in media filenames and detect the
    same image reused across many systems.
#>

Set-StrictMode -Version Latest

function Repair-MediaFilenames {
    <#
    .SYNOPSIS
        Renames media files containing characters that break some filesystems/themes
        (control chars, trailing dots/spaces). Backs up before renaming. Returns count.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string] $SystemMediaDir,
        [Parameter(Mandatory = $true)][string] $BackupRoot,
        [Parameter(Mandatory = $true)][scriptblock] $Logger,
        [switch] $DryRun
    )
    $fixed = 0
    if (-not (Test-Path -LiteralPath $SystemMediaDir)) { return 0 }
    Get-ChildItem -LiteralPath $SystemMediaDir -File -Recurse -ErrorAction SilentlyContinue | ForEach-Object {
        $name = $_.Name
        $clean = $name -replace '[\x00-\x1F]', '' -replace '\s+(\.[^.]+)$', '$1'
        $clean = $clean.TrimEnd(' ', '.')
        if ($clean.Length -eq 0 -or $clean -eq $name) { return }
        $target = Join-Path $_.DirectoryName $clean
        if (Test-Path -LiteralPath $target) { return }
        if ($DryRun) { $fixed++; return }
        Rename-Item -LiteralPath $_.FullName -NewName $clean -Force -ErrorAction SilentlyContinue
        $fixed++
    }
    if ($fixed -gt 0 -and -not $DryRun) { & $Logger "Sanitized $fixed media filename(s) in $(Split-Path $SystemMediaDir -Leaf)." 'SUCCESS' }
    return $fixed
}

function Find-CrossSystemMediaDup {
    <#
    .SYNOPSIS
        Returns how many image hashes are reused across 3+ different systems (often
        a sign of placeholder/wrong art). Read only.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][string] $MediaDir)
    if (-not (Test-Path -LiteralPath $MediaDir)) { return 0 }
    $hashSystems = @{}
    Get-ChildItem -LiteralPath $MediaDir -Directory -ErrorAction SilentlyContinue | ForEach-Object {
        $sysName = $_.Name
        Get-ChildItem -LiteralPath $_.FullName -File -Recurse -ErrorAction SilentlyContinue |
            Where-Object { $_.Extension.ToLower() -in @('.png','.jpg','.jpeg') } | ForEach-Object {
                $h = Get-FileSha256 -Path $_.FullName
                if (-not $h) { return }
                if (-not $hashSystems.ContainsKey($h)) { $hashSystems[$h] = New-Object System.Collections.Generic.HashSet[string] ([StringComparer]::OrdinalIgnoreCase) }
                [void]$hashSystems[$h].Add($sysName)
            }
    }
    $reused = 0
    foreach ($h in $hashSystems.Keys) { if ($hashSystems[$h].Count -ge 3) { $reused++ } }
    return $reused
}

# ----- module: MediaDownload -----
<#
.SYNOPSIS
    Media download engine - downloads ONLY missing assets from ScreenScraper, the
    official scraping source used by ES-DE.
.DESCRIPTION
    Uses the ScreenScraper jeuInfos API. Requires API credentials supplied via
    environment variables (never hard-coded, never logged):
        SS_DEVID, SS_DEVPASSWORD   (developer API id/password)
        SS_USER,  SS_PASSWORD      (a ScreenScraper member account)
    For each game missing media, the ROM CRC32 is computed and used to look up the
    game; missing media types are then downloaded into downloaded_media. If no
    credentials are configured the engine reports that scraping is unavailable and
    downloads nothing (the missing-media report still lists what is needed).
#>

Set-StrictMode -Version Latest

# Map ES-DE media folders to ScreenScraper media type identifiers.
$script:EsdeToSsMedia = @{
    'covers'       = 'box-2D'
    '3dboxes'      = 'box-3D'
    'backcovers'   = 'box-2D-back'
    'marquees'     = 'wheel'
    'screenshots'  = 'ss'
    'titlescreens' = 'sstitle'
    'fanart'       = 'fanart'
    'videos'       = 'video'
    'miximages'    = 'mixrbv2'
}

function Test-ScraperCredentials {
    [CmdletBinding()] param()
    return -not ([string]::IsNullOrWhiteSpace($env:SS_DEVID) -or
                 [string]::IsNullOrWhiteSpace($env:SS_DEVPASSWORD) -or
                 [string]::IsNullOrWhiteSpace($env:SS_USER) -or
                 [string]::IsNullOrWhiteSpace($env:SS_PASSWORD))
}

function Get-FileCrc32 {
    <#
    .SYNOPSIS
        Computes the CRC32 (hex, upper) of a file - the identifier ScreenScraper
        uses to match a ROM.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][string] $Path)

    # All arithmetic is done in [long] with an explicit 32-bit mask. Constants use
    # decimal form because the PowerShell literal 0xFFFFFFFF parses as [int] -1.
    $mask = [long]4294967295      # 0xFFFFFFFF
    $poly = [long]3988292384      # 0xEDB88320
    $table = New-Object 'System.UInt32[]' 256
    for ($i = 0; $i -lt 256; $i++) {
        $c = [long]$i
        for ($k = 0; $k -lt 8; $k++) {
            if (($c -band 1) -ne 0) { $c = ($poly -bxor ($c -shr 1)) -band $mask }
            else { $c = ($c -shr 1) -band $mask }
        }
        $table[$i] = [uint32]$c
    }
    $crc = $mask  # 0xFFFFFFFF
    try {
        $fs = [System.IO.File]::OpenRead($Path)
        try {
            $buf = New-Object byte[] 65536
            while (($read = $fs.Read($buf, 0, $buf.Length)) -gt 0) {
                for ($n = 0; $n -lt $read; $n++) {
                    $idx = [int](($crc -bxor [long]$buf[$n]) -band 255)
                    $crc = (($crc -shr 8) -band $mask) -bxor [long]$table[$idx]
                }
            }
        } finally { $fs.Dispose() }
    } catch { return $null }
    $crc = ($crc -bxor $mask) -band $mask
    return ('{0:X8}' -f [uint32]$crc)
}

function Invoke-ScreenScraperLookup {
    <#
    .SYNOPSIS
        Calls jeuInfos for a CRC and returns the parsed jeu object, or $null.
    #>
    [CmdletBinding()]
    param([string] $Crc, [string] $RomName, [int] $SystemId = 0)

    $base = 'https://api.screenscraper.fr/api2/jeuInfos.php'
    $q = @{
        devid       = $env:SS_DEVID
        devpassword = $env:SS_DEVPASSWORD
        softname    = 'ESDEAutoSuite'
        output      = 'json'
        ssid        = $env:SS_USER
        sspassword  = $env:SS_PASSWORD
        crc         = $Crc
        romnom      = $RomName
    }
    if ($SystemId -gt 0) { $q['systemeid'] = $SystemId }
    $query = ($q.GetEnumerator() | ForEach-Object { "{0}={1}" -f $_.Key, [uri]::EscapeDataString([string]$_.Value) }) -join '&'
    $url = "$base`?$query"
    try {
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        $resp = Invoke-RestMethod -Uri $url -TimeoutSec 60 -ErrorAction Stop
        if ($resp -and $resp.response -and $resp.response.jeu) { return $resp.response.jeu }
    } catch { return $null }
    return $null
}

function Save-ScreenScraperMedia {
    <#
    .SYNOPSIS
        Downloads the requested media types for one game into downloaded_media.
    .OUTPUTS
        Count of files downloaded.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][object]   $Jeu,
        [Parameter(Mandatory = $true)][string]   $RomStem,
        [Parameter(Mandatory = $true)][string]   $SystemMediaDir,
        [Parameter(Mandatory = $true)][string[]] $MissingTypes,
        [Parameter(Mandatory = $true)][scriptblock] $Logger
    )
    $downloaded = 0
    if (-not ($Jeu.PSObject.Properties.Name -contains 'medias')) { return 0 }
    $medias = @($Jeu.medias)

    foreach ($type in $MissingTypes) {
        if (-not $script:EsdeToSsMedia.ContainsKey($type)) { continue }
        $ssType = $script:EsdeToSsMedia[$type]
        $media = $medias | Where-Object { $_.type -eq $ssType } | Select-Object -First 1
        if (-not $media -or -not $media.url) { continue }
        $ext = if ($media.PSObject.Properties.Name -contains 'format' -and $media.format) { '.' + $media.format } else { if ($type -eq 'videos') { '.mp4' } else { '.png' } }
        $destDir = Join-Path $SystemMediaDir $type
        if (-not (Test-Path -LiteralPath $destDir)) { New-Item -Path $destDir -ItemType Directory -Force | Out-Null }
        $dest = Join-Path $destDir ($RomStem + $ext)
        if (Test-Path -LiteralPath $dest) { continue }   # never re-download existing
        try {
            $prog = $ProgressPreference; $ProgressPreference = 'SilentlyContinue'
            Invoke-WebRequest -Uri $media.url -OutFile $dest -TimeoutSec 120 -UseBasicParsing -ErrorAction Stop
            $ProgressPreference = $prog
            if ((Test-Path -LiteralPath $dest) -and (Get-Item -LiteralPath $dest).Length -gt 0) {
                $downloaded++
                & $Logger "Downloaded $type for '$RomStem'." 'SUCCESS'
            }
        } catch {
            & $Logger "Download failed ($type/$RomStem): $($_.Exception.Message)" 'WARN'
        }
    }
    return $downloaded
}

function Invoke-MediaDownloadForSystem {
    <#
    .SYNOPSIS
        Downloads missing media for a system's games via ScreenScraper.
    .OUTPUTS
        Hashtable: Attempted, Downloaded, Skipped.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string] $SystemRomDir,
        [Parameter(Mandatory = $true)][string] $SystemMediaDir,
        [Parameter(Mandatory = $true)][object] $MissingResult,    # from Get-MissingMediaForSystem
        [Parameter(Mandatory = $true)][scriptblock] $Logger,
        [int] $MaxGames = 0,
        [switch] $DryRun
    )
    $stats = @{ Attempted = 0; Downloaded = 0; Skipped = 0 }
    if (-not (Test-ScraperCredentials)) {
        & $Logger "ScreenScraper credentials not configured (SS_DEVID/SS_DEVPASSWORD/SS_USER/SS_PASSWORD). Skipping downloads; see missing-media report." 'WARN'
        return $stats
    }

    # Build a stem -> ROM file lookup for CRC computation.
    $romByStem = @{}
    if (Test-Path -LiteralPath $SystemRomDir) {
        Get-ChildItem -LiteralPath $SystemRomDir -File -ErrorAction SilentlyContinue | ForEach-Object {
            $romByStem[[System.IO.Path]::GetFileNameWithoutExtension($_.Name)] = $_.FullName
        }
    }

    $records = @($MissingResult.Records)
    foreach ($rec in $records) {
        if ($MaxGames -gt 0 -and $stats.Attempted -ge $MaxGames) { break }
        $stem = $rec.Game
        if (-not $romByStem.ContainsKey($stem)) { $stats.Skipped++; continue }
        $stats.Attempted++
        if ($DryRun) { & $Logger "[DRY-RUN] Would scrape '$stem' for: $($rec.Missing -join ', ')" 'INFO'; continue }

        $rom = $romByStem[$stem]
        $crc = Get-FileCrc32 -Path $rom
        $jeu = Invoke-ScreenScraperLookup -Crc $crc -RomName (Split-Path $rom -Leaf)
        if (-not $jeu) { $stats.Skipped++; continue }
        $stats.Downloaded += (Save-ScreenScraperMedia -Jeu $jeu -RomStem $stem -SystemMediaDir $SystemMediaDir -MissingTypes $rec.Missing -Logger $Logger)
    }
    return $stats
}

# ----- module: Cleanup -----
<#
.SYNOPSIS
    Cleanup engine. Removes ONLY: orphaned media (media whose stem matches no ROM),
    empty media folders, and obsolete cache entries. Orphans are quarantined into
    the backup tree (never hard-deleted) so nothing is ever lost. ROMs, saves,
    BIOS and controller profiles are never touched.
#>

Set-StrictMode -Version Latest

function Invoke-OrphanCleanup {
    <#
    .SYNOPSIS
        Moves media files whose stem has no corresponding ROM into a quarantine
        folder under the backup root. Returns count quarantined.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string] $SystemName,
        [Parameter(Mandatory = $true)][string] $SystemRomDir,
        [Parameter(Mandatory = $true)][string] $SystemMediaDir,
        # Not mandatory: a system may have zero detected ROM stems, and a mandatory
        # parameter rejects an empty collection.
        [System.Collections.Generic.HashSet[string]] $RomStems,
        [Parameter(Mandatory = $true)][string] $BackupRoot,
        [Parameter(Mandatory = $true)][scriptblock] $Logger,
        [switch] $DryRun
    )
    $quarantined = 0
    if (-not (Test-Path -LiteralPath $SystemMediaDir)) { return 0 }
    if ($null -eq $RomStems -or $RomStems.Count -eq 0) {
        # No ROMs known: do not treat everything as orphaned (safety).
        & $Logger "Skipping orphan cleanup for '$SystemName' (no ROMs detected)." 'INFO'
        return 0
    }

    $qRoot = Join-Path $BackupRoot ("orphaned_media\{0}" -f $SystemName)
    Get-ChildItem -LiteralPath $SystemMediaDir -File -Recurse -ErrorAction SilentlyContinue | ForEach-Object {
        $stem = [System.IO.Path]::GetFileNameWithoutExtension($_.Name)
        if ($RomStems.Contains($stem)) { return }
        if ($DryRun) { & $Logger "[DRY-RUN] Would quarantine orphan: $($_.FullName)" 'INFO'; $quarantined++; return }
        $rel = $_.FullName.Substring($SystemMediaDir.Length).TrimStart('\','/')
        $dst = Join-Path $qRoot $rel
        $dstDir = Split-Path $dst -Parent
        if (-not (Test-Path -LiteralPath $dstDir)) { New-Item -Path $dstDir -ItemType Directory -Force | Out-Null }
        Move-Item -LiteralPath $_.FullName -Destination $dst -Force
        $quarantined++
    }
    if ($quarantined -gt 0) { & $Logger "Quarantined $quarantined orphan media file(s) for '$SystemName'." 'SUCCESS' }
    return $quarantined
}

function Remove-EmptyFolders {
    <#
    .SYNOPSIS
        Recursively removes empty directories under a root (deepest first).
        Returns count removed.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string] $Root,
        [switch] $DryRun
    )
    if (-not (Test-Path -LiteralPath $Root)) { return 0 }
    $removed = 0
    $dirs = Get-ChildItem -LiteralPath $Root -Directory -Recurse -ErrorAction SilentlyContinue |
            Sort-Object { $_.FullName.Length } -Descending
    foreach ($d in $dirs) {
        $hasChild = Get-ChildItem -LiteralPath $d.FullName -Force -ErrorAction SilentlyContinue | Select-Object -First 1
        if (-not $hasChild) {
            if ($DryRun) { $removed++; continue }
            Remove-Item -LiteralPath $d.FullName -Force -ErrorAction SilentlyContinue
            $removed++
        }
    }
    return $removed
}

function Get-CacheSize {
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][string] $CacheDir)
    if (-not (Test-Path -LiteralPath $CacheDir)) { return 0 }
    $files = @(Get-ChildItem -LiteralPath $CacheDir -File -Recurse -ErrorAction SilentlyContinue)
    $sum = 0
    if ($files.Count -gt 0) { $sum = ($files | Measure-Object -Property Length -Sum).Sum }
    if (-not $sum) { return 0 }
    return [int64]$sum
}

# ----- module: EmulatorDetection -----
<#
.SYNOPSIS
    Emulator auto-detection module.
.DESCRIPTION
    Enumerates every emulator present under the RetroBat 'emulators' tree. It uses
    the data-driven definitions in config\emulators.json for known emulators AND
    dynamically discovers any other emulator folder (so future emulators added to
    RetroBat are reported automatically).
#>

Set-StrictMode -Version Latest

function Get-EmulatorDefinitions {
    <#
    .SYNOPSIS
        Loads and returns the emulator definition objects from emulators.json.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][string] $DefinitionPath)

    if (-not (Test-Path -LiteralPath $DefinitionPath)) {
        throw "Emulator definition file not found: $DefinitionPath"
    }
    $json = Get-Content -LiteralPath $DefinitionPath -Raw -Encoding UTF8 | ConvertFrom-Json
    return $json
}

function Find-EmulatorExecutable {
    <#
    .SYNOPSIS
        Searches a folder (recursively, shallow-first) for any of the candidate
        executable names and returns the first match.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)] [string]   $Folder,
        [Parameter(Mandatory = $true)] [string[]] $Executables
    )

    if (-not (Test-Path -LiteralPath $Folder)) { return $null }

    foreach ($exe in $Executables) {
        # Direct hit at folder root is the common case.
        $direct = Join-Path $Folder $exe
        if (Test-Path -LiteralPath $direct) { return $direct }
    }
    # UPGRADE (performance): fall back to a DEPTH-LIMITED search instead of a full
    # recursive scan. RetroBat emulators keep their executable at the root or one
    # or two levels down, so capping depth turns a multi-second scan over large
    # installs (100+ emulators) into a near-instant lookup.
    foreach ($exe in $Executables) {
        $found = Find-FileDepthLimited -Root $Folder -FileName $exe -MaxDepth 3
        if ($found) { return $found }
    }
    return $null
}

function Find-FileDepthLimited {
    <#
    .SYNOPSIS
        Breadth-first search for a file name up to a maximum directory depth.
    .OUTPUTS
        Full path of the first match, or $null.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)] [string] $Root,
        [Parameter(Mandatory = $true)] [string] $FileName,
        [int] $MaxDepth = 3
    )
    if (-not (Test-Path -LiteralPath $Root)) { return $null }

    $queue = [System.Collections.Generic.Queue[object]]::new()
    $queue.Enqueue([pscustomobject]@{ Path = $Root; Depth = 0 })
    while ($queue.Count -gt 0) {
        $node = $queue.Dequeue()
        $hit  = Join-Path $node.Path $FileName
        if (Test-Path -LiteralPath $hit -PathType Leaf) { return $hit }
        if ($node.Depth -lt $MaxDepth) {
            foreach ($sub in (Get-ChildItem -LiteralPath $node.Path -Directory -ErrorAction SilentlyContinue)) {
                $queue.Enqueue([pscustomobject]@{ Path = $sub.FullName; Depth = $node.Depth + 1 })
            }
        }
    }
    return $null
}

function Get-InstalledEmulators {
    <#
    .SYNOPSIS
        Returns an array of emulator descriptor hashtables for everything found.
    .DESCRIPTION
        Combines known definitions with dynamic folder discovery. Each descriptor:
          Id, DisplayName, Folder, FolderPath, Installed, ExecutablePath,
          ConfigType, ConfigFiles, Supports4K, Known, Definition
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)] [string] $EmulatorsRoot,
        [Parameter(Mandatory = $true)] [object] $Definitions
    )

    $results       = New-Object System.Collections.Generic.List[object]
    $accountedDirs = New-Object System.Collections.Generic.HashSet[string] ([StringComparer]::OrdinalIgnoreCase)

    # ---- Known emulators from the definition database ----
    foreach ($def in $Definitions.emulators) {
        $folderPath = Join-Path $EmulatorsRoot $def.folder
        $exe        = Find-EmulatorExecutable -Folder $folderPath -Executables $def.executables
        $descriptor = [ordered]@{
            Id             = $def.id
            DisplayName    = $def.displayName
            Folder         = $def.folder
            FolderPath     = $folderPath
            Installed      = [bool]$exe
            ExecutablePath = $exe
            ConfigType     = $def.configType
            ConfigFiles    = @($def.configFiles)
            Supports4K     = [bool]$def.supports4K
            Known          = $true
            Definition     = $def
        }
        $results.Add([pscustomobject]$descriptor)
        [void]$accountedDirs.Add($def.folder)
    }

    # ---- Dynamic discovery of unknown emulator folders ----
    if (Test-Path -LiteralPath $EmulatorsRoot) {
        Get-ChildItem -LiteralPath $EmulatorsRoot -Directory -ErrorAction SilentlyContinue | ForEach-Object {
            $dirName = $_.Name
            if ($accountedDirs.Contains($dirName)) { return }

            # Treat a folder containing at least one .exe as a candidate emulator.
            # UPGRADE (performance): cap recursion depth so discovery over very
            # large RetroBat installs stays fast.
            $exe = Get-ChildItem -LiteralPath $_.FullName -Filter '*.exe' -File -Recurse -Depth 2 -ErrorAction SilentlyContinue |
                   Where-Object { $_.Name -notmatch '(?i)(unins|setup|vc_redist|crash|update|helper)\b' } |
                   Sort-Object Length -Descending |
                   Select-Object -First 1

            $descriptor = [ordered]@{
                Id             = $dirName.ToLower()
                DisplayName    = "$dirName (auto-discovered)"
                Folder         = $dirName
                FolderPath     = $_.FullName
                Installed      = [bool]$exe
                ExecutablePath = if ($exe) { $exe.FullName } else { $null }
                ConfigType     = 'unknown'
                ConfigFiles    = @()
                Supports4K     = $false
                Known          = $false
                Definition     = $null
            }
            $results.Add([pscustomobject]$descriptor)
        }
    }

    return $results.ToArray()
}

function Get-MissingRequiredEmulators {
    <#
    .SYNOPSIS
        Returns the known emulators that are not installed but have a usable
        download definition (so they can be auto-installed).
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)] [object[]] $Emulators
    )

    return @($Emulators | Where-Object {
        $_.Known -and
        -not $_.Installed -and
        $_.Definition -and
        $_.Definition.download -and
        $_.Definition.download.type -ne 'none'
    })
}

# ----- module: EsdeEmulators -----
<#
.SYNOPSIS
    ES-DE-native emulator discovery.
.DESCRIPTION
    Discovers emulators the way ES-DE itself does, with NO dependency on a RetroBat
    folder layout:
      1. Parses ES-DE's es_find_rules.xml (staticpath rules) and resolves the
         real emulator binaries, expanding %ESPATH% / %ROMPATH% / %EMUPATH% / ~.
      2. Scans the ES-DE "Emulators" tree(s) next to the installation.
    Emulators are matched by EXECUTABLE name (retroarch.exe, pcsx2-qt.exe, ...)
    rather than folder name, so ES-DE naming (RetroArch-Win64, PCSX2-Qt, ...) is
    handled correctly. Each match is returned as a descriptor compatible with the
    graphics optimizer.
#>

Set-StrictMode -Version Latest

function Get-EsdeFindRulesPath {
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][System.Collections.Specialized.OrderedDictionary] $Layout)
    $dataParent = Split-Path $Layout.DataDir -Parent
    $cands = @(
        (Join-Path $Layout.CustomSystems 'es_find_rules.xml'),
        (Join-Path $Layout.DataDir 'resources\systems\windows\es_find_rules.xml'),
        (Join-Path $dataParent 'resources\systems\windows\es_find_rules.xml'),
        (Join-Path $dataParent 'ES-DE\resources\systems\windows\es_find_rules.xml')
    )
    foreach ($c in $cands) { if ($c -and (Test-Path -LiteralPath $c)) { return $c } }
    return $null
}

function Expand-EsdePath {
    <#
    .SYNOPSIS
        Expands ES-DE path variables and environment variables in a rule entry.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string] $Entry,
        [Parameter(Mandatory = $true)][string] $EsPath,
        [Parameter(Mandatory = $true)][string] $RomPath
    )
    $p = $Entry
    $p = $p.Replace('%ESPATH%', $EsPath).Replace('%ROMPATH%', $RomPath).Replace('%EMUPATH%', $EsPath)
    if ($p.StartsWith('~')) {
        $home2 = if ($env:USERPROFILE) { $env:USERPROFILE } else { $env:HOME }
        if ($home2) { $p = $home2 + $p.Substring(1) }
    }
    $p = [Environment]::ExpandEnvironmentVariables($p)
    return ($p -replace '/', '\')
}

function Get-EsdeEmulatorsRoots {
    <#
    .SYNOPSIS
        Returns existing candidate "Emulators" roots derived from the ES-DE install
        plus an optional explicit extra root. No RetroBat paths are assumed.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][System.Collections.Specialized.OrderedDictionary] $Layout,
        [string] $ExtraRoot
    )
    $dataParent = Split-Path $Layout.DataDir -Parent
    $roots = New-Object System.Collections.Generic.List[string]
    foreach ($c in @(
        (Join-Path $Layout.DataDir 'Emulators'),
        (Join-Path $dataParent 'Emulators'),
        (Join-Path $dataParent 'emulators'),
        (Join-Path $Layout.DataDir 'emulators')
    )) { if ($c) { $roots.Add($c) } }
    if ($ExtraRoot) {
        $roots.Add($ExtraRoot)
        $roots.Add((Join-Path $ExtraRoot 'emulators'))
        $roots.Add((Join-Path $ExtraRoot 'Emulators'))
    }

    # Derive roots from es_find_rules.xml: any existing staticpath exe whose path
    # contains an 'Emulators' segment yields that segment as a root.
    $frp = Get-EsdeFindRulesPath -Layout $Layout
    if ($frp) {
        $esPath = $dataParent
        try {
            [xml]$xml = Get-Content -LiteralPath $frp -Raw -Encoding UTF8
            foreach ($entry in $xml.SelectNodes("//rule[@type='staticpath']/entry")) {
                $abs = Expand-EsdePath -Entry $entry.InnerText -EsPath $esPath -RomPath $Layout.RomDir
                if (Test-Path -LiteralPath $abs) {
                    $parts = $abs -split '\\'
                    for ($i = $parts.Length - 1; $i -ge 0; $i--) {
                        if ($parts[$i] -ieq 'Emulators') {
                            $roots.Add(($parts[0..$i] -join '\'))
                            break
                        }
                    }
                }
            }
        } catch { }
    }

    return @($roots | Where-Object { $_ -and (Test-Path -LiteralPath $_) } | Select-Object -Unique)
}

function Get-EsdeEmulators {
    <#
    .SYNOPSIS
        Returns emulator descriptors by matching known executables (from the
        definition database) anywhere under the given roots. Folder naming is
        irrelevant; FolderPath is set to the directory containing the executable.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string[]] $Roots,
        [Parameter(Mandatory = $true)][object]   $Definitions
    )

    $results = New-Object System.Collections.Generic.List[object]
    $foundIds = New-Object System.Collections.Generic.HashSet[string] ([StringComparer]::OrdinalIgnoreCase)

    foreach ($def in $Definitions.emulators) {
        if ($foundIds.Contains($def.id)) { continue }
        $hit = $null
        foreach ($root in $Roots) {
            foreach ($exe in $def.executables) {
                $found = Find-FileDepthLimited -Root $root -FileName $exe -MaxDepth 4
                if ($found) { $hit = $found; break }
            }
            if ($hit) { break }
        }
        $descriptor = [ordered]@{
            Id             = $def.id
            DisplayName    = $def.displayName
            Folder         = $def.folder
            FolderPath     = if ($hit) { Split-Path $hit -Parent } else { $null }
            Installed      = [bool]$hit
            ExecutablePath = $hit
            ConfigType     = $def.configType
            ConfigFiles    = @($def.configFiles)
            Supports4K     = [bool]$def.supports4K
            Known          = $true
            Definition     = $def
        }
        $results.Add([pscustomobject]$descriptor)
        if ($hit) { [void]$foundIds.Add($def.id) }
    }

    return $results.ToArray()
}

# ----- module: EmulatorGap -----
<#
.SYNOPSIS
    Missing-emulator gap analysis + executable integrity verification.
.DESCRIPTION
    Cross-references each ES-DE system that has ROMs against the emulators actually
    installed, using a system->emulator map. Reports, per system, which emulator is
    required, which are available, and whether a usable emulator is missing. Also
    verifies that detected emulator executables are real (non-empty, valid PE header)
    and flags "partially installed" emulator folders.
#>

Set-StrictMode -Version Latest

function Test-ExecutableIntegrity {
    <#
    .SYNOPSIS
        Returns $true if the file exists, is non-empty and begins with the 'MZ'
        DOS/PE signature (i.e. a real Windows executable, not a 0-byte stub).
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][string] $Path)
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { return $false }
    try {
        $fi = Get-Item -LiteralPath $Path
        if ($fi.Length -lt 2) { return $false }
        $fs = [System.IO.File]::OpenRead($Path)
        try {
            $b0 = $fs.ReadByte(); $b1 = $fs.ReadByte()
            return ($b0 -eq 0x4D -and $b1 -eq 0x5A)   # 'M','Z'
        } finally { $fs.Dispose() }
    } catch { return $false }
}

function Get-EmulatorGaps {
    <#
    .SYNOPSIS
        Builds per-system emulator gap records.
    .PARAMETER Systems
        System descriptors (from Get-EsdeSystems): need .Name and .HasRoms.
    .PARAMETER InstalledIds
        Array of emulator ids that were detected as installed.
    .PARAMETER SystemMap
        Hashtable system-name -> array of emulator ids (from esde-media.json).
    .OUTPUTS
        Array of records: System, HasRoms, Required[], Available[], Missing(bool), Recommended
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][object[]]  $Systems,
        [string[]]  $InstalledIds = @(),
        [Parameter(Mandatory = $true)][hashtable] $SystemMap
    )
    $installed = New-Object System.Collections.Generic.HashSet[string] ([StringComparer]::OrdinalIgnoreCase)
    foreach ($id in $InstalledIds) { [void]$installed.Add($id) }

    $records = New-Object System.Collections.Generic.List[object]
    foreach ($sys in $Systems) {
        $name = $sys.Name
        $required = @()
        if ($SystemMap.ContainsKey($name)) { $required = @($SystemMap[$name]) }
        $available = @($required | Where-Object { $installed.Contains($_) })
        # A system is only a "gap" if it actually has ROMs and we know what it needs.
        $missing = ($sys.HasRoms -and $required.Count -gt 0 -and $available.Count -eq 0)
        $recommended = if ($required.Count -gt 0) { $required[0] } else { '' }
        $records.Add([ordered]@{
            System      = $name
            HasRoms     = [bool]$sys.HasRoms
            Required    = $required
            Available   = $available
            Missing     = $missing
            Recommended = $recommended
        })
    }
    return $records.ToArray()
}

function Test-EmulatorInstalls {
    <#
    .SYNOPSIS
        Verifies integrity of each installed emulator's executable and flags
        partial installs (known folder present but no valid exe). Returns records.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][object[]] $Emulators,
        [Parameter(Mandatory = $true)][scriptblock] $Logger
    )
    $records = New-Object System.Collections.Generic.List[object]
    foreach ($e in ($Emulators | Where-Object { $_.Installed })) {
        $ok = Test-ExecutableIntegrity -Path $e.ExecutablePath
        if (-not $ok) {
            & $Logger "Emulator '$($e.DisplayName)' executable failed integrity check: $($e.ExecutablePath)" 'WARN'
        }
        $records.Add([ordered]@{ Id = $e.Id; DisplayName = $e.DisplayName; Exe = $e.ExecutablePath; IntegrityOk = $ok })
    }
    return $records.ToArray()
}

# ----- module: EmulatorTuning -----
<#
.SYNOPSIS
    Deeper, safe emulator tuning beyond resolution, plus a config archive.
.DESCRIPTION
    Applies extra quality/UX settings that are safe defaults:
      * RetroArch: rewind, run-ahead off, on-screen notifications off, fast-forward
        ratio, savestate thumbnails, threaded video, menu driver.
    And archives every emulator config file into a single timestamped backup folder
    so the whole emulator configuration can be restored together.
#>

Set-StrictMode -Version Latest

function Set-RetroArchExtras {
    <#
    .SYNOPSIS
        Applies safe extra RetroArch options to retroarch.cfg. Returns $true if applied.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string] $RetroArchDir,
        [Parameter(Mandatory = $true)][string] $BackupRoot,
        [Parameter(Mandatory = $true)][scriptblock] $Logger,
        [switch] $DryRun
    )
    $cfg = Join-Path $RetroArchDir 'retroarch.cfg'
    if (-not (Test-Path -LiteralPath $cfg)) { return $false }
    if ($DryRun) { & $Logger "[DRY-RUN] Would apply RetroArch extra options." 'INFO'; return $false }
    Backup-File -Path $cfg -BackupRoot $BackupRoot | Out-Null
    $opts = [ordered]@{
        'rewind_enable'                 = 'true'
        'rewind_buffer_size'            = '20971520'
        'run_ahead_enabled'             = 'false'
        'video_font_enable'             = 'true'
        'menu_show_load_content_animation' = 'false'
        'fastforward_ratio'             = '0.000000'
        'savestate_thumbnail_enable'    = 'true'
        'savestate_auto_save'           = 'false'
        'video_threaded'                = 'true'
        'notification_show_when_menu_is_alive' = 'false'
    }
    foreach ($k in $opts.Keys) { Set-FlatConfigValue -Path $cfg -Key $k -Value $opts[$k] -Quote }
    & $Logger "Applied RetroArch extra options (rewind, run-ahead, savestate thumbnails, fast-forward)." 'SUCCESS'
    return $true
}

function Backup-AllEmulatorConfigs {
    <#
    .SYNOPSIS
        Copies every emulator config file (by extension) under the emulator roots
        into one timestamped archive folder. Returns count archived.
    #>
    [CmdletBinding()]
    param(
        [string[]] $EmulatorRoots = @(),
        [Parameter(Mandatory = $true)][string]   $BackupRoot,
        [Parameter(Mandatory = $true)][scriptblock] $Logger,
        [switch] $DryRun
    )
    if (-not $EmulatorRoots -or $EmulatorRoots.Count -eq 0) { return 0 }
    $stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
    $dest  = Join-Path $BackupRoot ("emulator_configs_$stamp")
    $inc   = @('*.cfg','*.ini','*.xml','*.yml','*.toml','*.json','*.config')
    $count = 0
    foreach ($root in $EmulatorRoots) {
        if (-not (Test-Path -LiteralPath $root)) { continue }
        Get-ChildItem -LiteralPath $root -Recurse -File -Include $inc -ErrorAction SilentlyContinue | ForEach-Object {
            if ($_.FullName.Length -gt 240) { return }
            $rel = $_.FullName.Substring($root.Length).TrimStart('\','/')
            $dst = Join-Path (Join-Path $dest (Split-Path $root -Leaf)) $rel
            if ($DryRun) { $count++; return }
            $dstDir = Split-Path $dst -Parent
            if (-not (Test-Path -LiteralPath $dstDir)) { New-Item -Path $dstDir -ItemType Directory -Force | Out-Null }
            Copy-Item -LiteralPath $_.FullName -Destination $dst -Force -ErrorAction SilentlyContinue
            $count++
        }
    }
    if ($count -gt 0 -and -not $DryRun) { & $Logger "Archived $count emulator config file(s) to $dest." 'SUCCESS' }
    return $count
}

# ----- module: AdvancedTuning -----
<#
.SYNOPSIS
    Advanced RetroArch tuning: 4K-appropriate shader preset and latency settings.
.DESCRIPTION
    Only applies what the install actually supports - a shader preset is set just
    when a matching preset file exists, and latency settings scale with the
    performance tier. retroarch.cfg is backed up before any change.
#>

Set-StrictMode -Version Latest

function Set-RetroArchShaderPreset {
    <#
    .SYNOPSIS
        Enables a sensible shader preset if one is present in the RetroArch shaders
        tree (prefers a sharp-bilinear/CRT preset). Returns the preset path or ''.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string] $RetroArchDir,
        [Parameter(Mandatory = $true)][string] $BackupRoot,
        [Parameter(Mandatory = $true)][scriptblock] $Logger,
        [switch] $DryRun
    )
    $cfg = Join-Path $RetroArchDir 'retroarch.cfg'
    if (-not (Test-Path -LiteralPath $cfg)) { return '' }
    $preset = $null
    foreach ($sub in @('shaders\shaders_slang','shaders\shaders_glsl')) {
        $base = Join-Path $RetroArchDir $sub
        if (-not (Test-Path -LiteralPath $base)) { continue }
        foreach ($pat in @('sharp-bilinear-simple.*','sharp-bilinear.*','crt-geom.*','crt-lottes.*')) {
            $hit = Get-ChildItem -LiteralPath $base -Recurse -File -Filter ($pat) -ErrorAction SilentlyContinue | Select-Object -First 1
            if ($hit) { $preset = $hit.FullName; break }
        }
        if ($preset) { break }
    }
    if (-not $preset) { & $Logger "No RetroArch shader presets found; skipping shader config." 'INFO'; return '' }
    if ($DryRun) { & $Logger "[DRY-RUN] Would set shader preset $preset." 'INFO'; return $preset }
    Backup-File -Path $cfg -BackupRoot $BackupRoot | Out-Null
    Set-FlatConfigValue -Path $cfg -Key 'video_shader_enable' -Value 'true' -Quote
    Set-FlatConfigValue -Path $cfg -Key 'video_shader' -Value $preset -Quote
    & $Logger "Applied RetroArch shader preset: $(Split-Path $preset -Leaf)." 'SUCCESS'
    return $preset
}

function Set-RetroArchLatency {
    <#
    .SYNOPSIS
        Applies latency-reduction settings scaled to the performance tier (a strong
        rig can afford frame delay / run-ahead). Returns $true if applied.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string] $RetroArchDir,
        [Parameter(Mandatory = $true)][string] $Tier,
        [Parameter(Mandatory = $true)][string] $BackupRoot,
        [Parameter(Mandatory = $true)][scriptblock] $Logger,
        [switch] $DryRun
    )
    $cfg = Join-Path $RetroArchDir 'retroarch.cfg'
    if (-not (Test-Path -LiteralPath $cfg)) { return $false }
    if ($DryRun) { & $Logger "[DRY-RUN] Would apply RetroArch latency tuning ($Tier)." 'INFO'; return $false }
    Backup-File -Path $cfg -BackupRoot $BackupRoot | Out-Null
    # Frame delay (ms shaved off; higher tier can sustain more); run-ahead 1 frame
    # only for high/ultra tiers which have CPU headroom.
    $frameDelay = switch ($Tier) { 'FourK' {4} 'HighEnd' {4} 'MidRange' {2} default {0} }
    $runAhead   = if ($Tier -in @('FourK','HighEnd')) { 'true' } else { 'false' }
    Set-FlatConfigValue -Path $cfg -Key 'video_frame_delay' -Value "$frameDelay" -Quote
    Set-FlatConfigValue -Path $cfg -Key 'video_frame_delay_auto' -Value 'true' -Quote
    Set-FlatConfigValue -Path $cfg -Key 'run_ahead_enabled' -Value $runAhead -Quote
    Set-FlatConfigValue -Path $cfg -Key 'run_ahead_frames' -Value '1' -Quote
    Set-FlatConfigValue -Path $cfg -Key 'run_ahead_secondary_instance' -Value 'true' -Quote
    & $Logger "Applied RetroArch latency tuning (frame_delay=$frameDelay, run_ahead=$runAhead) for tier $Tier." 'SUCCESS'
    return $true
}

# ----- module: SystemTuning -----
<#
.SYNOPSIS
    Extra RetroArch feature configuration (achievements, netplay, input) and
    standardized hotkeys for standalone emulators.
.DESCRIPTION
    All settings are safe defaults; retroarch.cfg is backed up first. Credentials
    are never written (RetroAchievements/netplay are enabled but left unauthenticated
    for the user to log in).
#>

Set-StrictMode -Version Latest

function Set-RetroArchFeatures {
    <#
    .SYNOPSIS
        Enables RetroAchievements (non-hardcore), netplay defaults and tunes input
        (deadzone, analog-to-dpad, rumble). Returns $true if applied.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string] $RetroArchDir,
        [Parameter(Mandatory = $true)][string] $BackupRoot,
        [Parameter(Mandatory = $true)][scriptblock] $Logger,
        [switch] $DryRun
    )
    $cfg = Join-Path $RetroArchDir 'retroarch.cfg'
    if (-not (Test-Path -LiteralPath $cfg)) { return $false }
    if ($DryRun) { & $Logger "[DRY-RUN] Would set RetroArch features (achievements/netplay/input)." 'INFO'; return $false }
    Backup-File -Path $cfg -BackupRoot $BackupRoot | Out-Null
    $opts = [ordered]@{
        'cheevos_enable'                 = 'true'
        'cheevos_hardcore_mode_enable'   = 'false'
        'cheevos_richpresence_enable'    = 'true'
        'cheevos_badges_enable'          = 'true'
        'netplay_public_announce'        = 'false'
        'netplay_nat_traversal'          = 'true'
        'input_axis_threshold'           = '0.500000'
        'input_analog_deadzone'          = '0.150000'
        'input_player1_analog_dpad_mode' = '1'
        'input_rumble_gain'              = '100'
        'input_auto_game_focus'          = '2'
    }
    foreach ($k in $opts.Keys) { Set-FlatConfigValue -Path $cfg -Key $k -Value $opts[$k] -Quote }
    & $Logger "Applied RetroArch features: achievements (casual), netplay defaults, input deadzone/rumble." 'SUCCESS'
    return $true
}

function Set-StandaloneHotkeys {
    <#
    .SYNOPSIS
        Writes standardized hotkeys to standalone emulator configs where the format
        is well-defined and safe (DuckStation). Returns count of emulators tuned.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][object[]] $Emulators,
        [Parameter(Mandatory = $true)][string]   $BackupRoot,
        [Parameter(Mandatory = $true)][scriptblock] $Logger,
        [switch] $DryRun
    )
    $tuned = 0
    foreach ($e in ($Emulators | Where-Object { $_.Installed -and $_.Id -eq 'duckstation' })) {
        $cfg = Join-Path $e.FolderPath 'settings.ini'
        if (-not (Test-Path -LiteralPath $cfg)) { continue }
        if ($DryRun) { $tuned++; continue }
        $ini = Read-IniFile -Path $cfg
        Set-IniValue -Data $ini -Section 'Hotkeys' -Key 'FastForward' -Value 'Keyboard/Tab'
        Set-IniValue -Data $ini -Section 'Hotkeys' -Key 'TogglePause'  -Value 'Keyboard/Space'
        Set-IniValue -Data $ini -Section 'Hotkeys' -Key 'Screenshot'   -Value 'Keyboard/F10'
        Set-IniValue -Data $ini -Section 'Hotkeys' -Key 'SaveSelectedSaveState' -Value 'Keyboard/F1'
        Set-IniValue -Data $ini -Section 'Hotkeys' -Key 'LoadSelectedSaveState' -Value 'Keyboard/F3'
        Backup-File -Path $cfg -BackupRoot $BackupRoot | Out-Null
        Write-IniFile -Path $cfg -Data $ini
        $tuned++
    }
    if ($tuned -gt 0 -and -not $DryRun) { & $Logger "Applied standardized hotkeys to $tuned standalone emulator(s)." 'SUCCESS' }
    return $tuned
}

# ----- module: RomLibrary -----
<#
.SYNOPSIS
    ROM library analysis and multi-disc .m3u playlist generation.
.DESCRIPTION
    * Per-system ROM statistics: count, total size, by-extension breakdown,
      zero-byte/suspect ROMs, and compressed-format counts.
    * Multi-disc detection: groups "(Disc 1)/(Disc 2)/..." sets and generates an
      .m3u playlist so ES-DE/emulators treat them as a single game (safe, never
      deletes; skips if an .m3u already exists).
    * Compression advisory: lists uncompressed disc images (cue/bin/iso/gdi) that
      could be converted to CHD to save space (advisory only - no conversion).
#>

Set-StrictMode -Version Latest

$script:RomNonGame = @('.txt','.xml','.dat','.jpg','.png','.bin','.sub','.m3u','.srm','.state','.cfg')

function Get-RomLibraryStats {
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][string] $SystemName, [Parameter(Mandatory = $true)][string] $SystemRomDir)
    $count = 0; $bytes = [int64]0; $zero = New-Object System.Collections.Generic.List[string]
    $byExt = @{}; $compressed = 0
    if (Test-Path -LiteralPath $SystemRomDir) {
        Get-ChildItem -LiteralPath $SystemRomDir -File -ErrorAction SilentlyContinue | ForEach-Object {
            $ext = $_.Extension.ToLower()
            if ($ext -eq '.bin' -and (Test-Path -LiteralPath ([System.IO.Path]::ChangeExtension($_.FullName,'cue')))) { return } # part of cue/bin
            if ($script:RomNonGame -contains $ext) { return }
            $count++; $bytes += $_.Length
            if ($_.Length -eq 0) { $zero.Add($_.Name) }
            if (-not $byExt.ContainsKey($ext)) { $byExt[$ext] = 0 }
            $byExt[$ext]++
            if ($ext -in @('.chd','.zip','.7z','.rvz','.cso','.pbp')) { $compressed++ }
        }
    }
    return @{ System=$SystemName; Count=$count; TotalBytes=$bytes; ZeroByte=$zero.ToArray(); ByExt=$byExt; Compressed=$compressed }
}

function New-MultiDiscPlaylists {
    <#
    .SYNOPSIS
        Generates .m3u playlists for multi-disc games. Returns count created.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string] $SystemRomDir,
        [Parameter(Mandatory = $true)][scriptblock] $Logger,
        [switch] $DryRun
    )
    if (-not (Test-Path -LiteralPath $SystemRomDir)) { return 0 }
    $discExt = @('.chd','.cue','.iso','.gdi','.cso','.pbp','.ccd')
    $groups = @{}
    Get-ChildItem -LiteralPath $SystemRomDir -File -ErrorAction SilentlyContinue | ForEach-Object {
        if ($discExt -notcontains $_.Extension.ToLower()) { return }
        $stem = [System.IO.Path]::GetFileNameWithoutExtension($_.Name)
        $m = [Regex]::Match($stem, '^(.*?)[\s_]*\(Disc\s*(\d+)\)(.*)$', 'IgnoreCase')
        if (-not $m.Success) { return }
        $base = ($m.Groups[1].Value.Trim() + $m.Groups[3].Value.Trim()).Trim()
        if (-not $groups.ContainsKey($base)) { $groups[$base] = New-Object System.Collections.Generic.List[object] }
        $groups[$base].Add([pscustomobject]@{ Disc=[int]$m.Groups[2].Value; File=$_.Name })
    }
    $created = 0
    foreach ($base in $groups.Keys) {
        $discs = $groups[$base]
        if ($discs.Count -lt 2) { continue }
        $m3u = Join-Path $SystemRomDir ($base + '.m3u')
        if (Test-Path -LiteralPath $m3u) { continue }
        $lines = @($discs | Sort-Object Disc | ForEach-Object { $_.File })
        if ($DryRun) { & $Logger "[DRY-RUN] Would create playlist $base.m3u ($($lines.Count) discs)." 'INFO'; $created++; continue }
        [System.IO.File]::WriteAllLines($m3u, $lines, (New-Object System.Text.UTF8Encoding($false)))
        $created++
    }
    if ($created -gt 0) { & $Logger "Created $created multi-disc .m3u playlist(s) in $(Split-Path $SystemRomDir -Leaf)." 'SUCCESS' }
    return $created
}

function Get-CompressionAdvisory {
    <#
    .SYNOPSIS
        Returns uncompressed disc images that could be CHD-compressed, with the
        approximate space they currently occupy.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][string] $SystemRomDir)
    $candidates = New-Object System.Collections.Generic.List[object]
    $bytes = [int64]0
    if (Test-Path -LiteralPath $SystemRomDir) {
        Get-ChildItem -LiteralPath $SystemRomDir -File -ErrorAction SilentlyContinue | ForEach-Object {
            if ($_.Extension.ToLower() -in @('.iso','.cue','.gdi')) {
                $candidates.Add($_.Name); $bytes += $_.Length
            }
        }
    }
    return @{ Count=$candidates.Count; ApproxBytes=$bytes }
}

# ----- module: RomVerify -----
<#
.SYNOPSIS
    DAT-based ROM verification (No-Intro / Redump / MAME / clrmamepro XML DATs).
.DESCRIPTION
    If the user provides .dat files, ROMs are CRC32-checked against them and
    classified verified / unknown. Reports only - never deletes or renames.
    Looks for DATs in a 'dats' folder next to the ROM dir or under the work dir.
#>

Set-StrictMode -Version Latest

$script:VfNonRom = @('.txt','.xml','.dat','.jpg','.png','.srm','.state','.cfg','.sav','.cht','.m3u')

function Find-DatDirectory {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string] $RomDir,
        [Parameter(Mandatory = $true)][string] $WorkRoot
    )
    foreach ($c in @(
        (Join-Path (Split-Path $RomDir -Parent) 'dats'),
        (Join-Path $RomDir 'dats'),
        (Join-Path $WorkRoot 'dats')
    )) {
        if ($c -and (Test-Path -LiteralPath $c)) { return $c }
    }
    return $null
}

function Get-DatCrcSet {
    <#
    .SYNOPSIS
        Parses all .dat files in a directory and returns a set of known CRC32 values
        (uppercased) plus the number of game entries found.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][string] $DatDir)
    $crcs = New-Object System.Collections.Generic.HashSet[string] ([StringComparer]::OrdinalIgnoreCase)
    $games = 0
    if (-not (Test-Path -LiteralPath $DatDir)) { return @{ Crcs=$crcs; Games=0 } }
    Get-ChildItem -LiteralPath $DatDir -File -Filter '*.dat' -ErrorAction SilentlyContinue | ForEach-Object {
        try {
            $doc = New-Object System.Xml.XmlDocument
            $doc.Load($_.FullName)
            foreach ($rom in $doc.SelectNodes('//rom')) {
                $crc = $rom.GetAttribute('crc')
                if ($crc) { [void]$crcs.Add($crc.ToUpper().PadLeft(8,'0')); $games++ }
            }
        } catch { }
    }
    return @{ Crcs=$crcs; Games=$games }
}

function Test-RomsAgainstDat {
    <#
    .SYNOPSIS
        Verifies each system's ROMs against the DAT CRC set. Returns per-system
        @{ System; Verified; Unknown }.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][object[]] $Systems,
        [Parameter(Mandatory = $true)][System.Collections.Generic.HashSet[string]] $KnownCrcs,
        [Parameter(Mandatory = $true)][scriptblock] $Logger,
        [int] $MaxSizeMB = 256
    )
    $records = New-Object System.Collections.Generic.List[object]
    if ($KnownCrcs.Count -eq 0) { return @() }
    $limit = $MaxSizeMB * 1MB
    foreach ($sys in $Systems) {
        if (-not (Test-Path -LiteralPath $sys.RomPath)) { continue }
        $ok = 0; $unk = 0
        Get-ChildItem -LiteralPath $sys.RomPath -File -ErrorAction SilentlyContinue | ForEach-Object {
            if ($script:VfNonRom -contains $_.Extension.ToLower()) { return }
            if ($_.Length -gt $limit -or $_.Length -eq 0) { return }
            $crc = Get-FileCrc32 -Path $_.FullName
            if ($crc -and $KnownCrcs.Contains($crc)) { $ok++ } else { $unk++ }
        }
        if (($ok + $unk) -gt 0) { $records.Add(@{ System=$sys.Name; Verified=$ok; Unknown=$unk }) }
    }
    return $records.ToArray()
}

# ----- module: RomCompress -----
<#
.SYNOPSIS
    Real CD/DVD ROM compression to CHD using chdman (part of MAME tools, free).
.DESCRIPTION
    Converts cue/bin, iso and gdi disc images to CHD, which is lossless and saves a
    lot of space. Requires chdman.exe (found on PATH or under an emulator/MAME
    folder). The original is moved to a quarantine folder only AFTER the CHD is
    created and verified non-empty - so nothing is ever lost. Opt-in (/compress).
#>

Set-StrictMode -Version Latest

function Find-Chdman {
    [CmdletBinding()]
    param([string[]] $EmulatorRoots = @())
    $cmd = Get-Command chdman -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    foreach ($r in $EmulatorRoots) {
        if (-not $r -or -not (Test-Path -LiteralPath $r)) { continue }
        $hit = Get-ChildItem -LiteralPath $r -File -Recurse -Depth 4 -Filter 'chdman.exe' -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($hit) { return $hit.FullName }
    }
    return $null
}

function Invoke-ChdCompression {
    <#
    .SYNOPSIS
        Compresses cue/iso/gdi disc images to CHD for a system. Returns
        @{ Converted; SavedMB }.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string] $SystemRomDir,
        [Parameter(Mandatory = $true)][string] $Chdman,
        [Parameter(Mandatory = $true)][string] $BackupRoot,
        [Parameter(Mandatory = $true)][scriptblock] $Logger,
        [switch] $DryRun
    )
    $stats = @{ Converted = 0; SavedMB = 0.0 }
    if (-not (Test-Path -LiteralPath $SystemRomDir)) { return $stats }
    $qRoot = Join-Path $BackupRoot ('precompress\' + (Split-Path $SystemRomDir -Leaf))

    Get-ChildItem -LiteralPath $SystemRomDir -File -ErrorAction SilentlyContinue |
        Where-Object { $_.Extension.ToLower() -in @('.cue','.iso','.gdi') } | ForEach-Object {
            $src = $_
            $chd = [System.IO.Path]::ChangeExtension($src.FullName, 'chd')
            if (Test-Path -LiteralPath $chd) { return }   # already converted
            if ($DryRun) { & $Logger "[DRY-RUN] Would compress $($src.Name) -> CHD." 'INFO'; $stats.Converted++; return }
            try {
                $subcmd = if ($src.Extension.ToLower() -eq '.gdi') { 'createcd' } elseif ($src.Extension.ToLower() -eq '.cue') { 'createcd' } else { 'createcd' }
                $p = Start-Process -FilePath $Chdman -ArgumentList @($subcmd,'-i',$src.FullName,'-o',$chd) -NoNewWindow -Wait -PassThru
                if ($p.ExitCode -eq 0 -and (Test-Path -LiteralPath $chd) -and ((Get-Item -LiteralPath $chd).Length -gt 0)) {
                    $origSize = $src.Length
                    # Also move companion .bin files for a .cue.
                    $companions = @()
                    if ($src.Extension.ToLower() -eq '.cue') {
                        Get-Content -LiteralPath $src.FullName -ErrorAction SilentlyContinue | ForEach-Object {
                            if ($_ -match 'FILE\s+"([^"]+)"') { $bin = Join-Path $src.DirectoryName $Matches[1]; if (Test-Path -LiteralPath $bin) { $companions += $bin } }
                        }
                    }
                    if (-not (Test-Path -LiteralPath $qRoot)) { New-Item -Path $qRoot -ItemType Directory -Force | Out-Null }
                    Move-Item -LiteralPath $src.FullName -Destination (Join-Path $qRoot $src.Name) -Force -ErrorAction SilentlyContinue
                    foreach ($c in $companions) { $origSize += (Get-Item -LiteralPath $c).Length; Move-Item -LiteralPath $c -Destination (Join-Path $qRoot (Split-Path $c -Leaf)) -Force -ErrorAction SilentlyContinue }
                    $stats.Converted++
                    $stats.SavedMB += [math]::Round(($origSize - (Get-Item -LiteralPath $chd).Length)/1MB, 1)
                } else {
                    if (Test-Path -LiteralPath $chd) { Remove-Item -LiteralPath $chd -Force -ErrorAction SilentlyContinue }
                    & $Logger "chdman failed for $($src.Name) (exit $($p.ExitCode)); original left untouched." 'WARN'
                }
            } catch { & $Logger "chdman error for $($src.Name): $($_.Exception.Message)" 'WARN' }
        }
    if ($stats.Converted -gt 0 -and -not $DryRun) { & $Logger "Compressed $($stats.Converted) image(s) to CHD in $(Split-Path $SystemRomDir -Leaf), saved ~$($stats.SavedMB) MB (originals quarantined)." 'SUCCESS' }
    return $stats
}

# ----- module: RaPlaylists -----
<#
.SYNOPSIS
    RetroArch playlist (.lpl) generation from a system's ROMs.
.DESCRIPTION
    Writes a RetroArch-format playlist per system into RetroArch\playlists so
    RetroArch can browse the library directly (core auto-detected at launch).
#>

Set-StrictMode -Version Latest

$script:LplNonRom = @('.txt','.xml','.dat','.jpg','.png','.bin','.srm','.state','.cfg','.sav','.cht','.m3u')

function New-RetroArchPlaylists {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][object[]] $Systems,
        [Parameter(Mandatory = $true)][string]   $RetroArchDir,
        [Parameter(Mandatory = $true)][scriptblock] $Logger,
        [switch] $DryRun
    )
    $plDir = Join-Path $RetroArchDir 'playlists'
    $created = 0
    foreach ($sys in $Systems) {
        if (-not (Test-Path -LiteralPath $sys.RomPath)) { continue }
        $items = New-Object System.Collections.Generic.List[object]
        Get-ChildItem -LiteralPath $sys.RomPath -File -ErrorAction SilentlyContinue | ForEach-Object {
            if ($script:LplNonRom -contains $_.Extension.ToLower()) { return }
            if ($_.Extension.ToLower() -eq '.bin' -and (Test-Path -LiteralPath ([System.IO.Path]::ChangeExtension($_.FullName,'cue')))) { return }
            $items.Add([ordered]@{
                path       = $_.FullName
                label      = [System.IO.Path]::GetFileNameWithoutExtension($_.Name)
                core_path  = 'DETECT'
                core_name  = 'DETECT'
                crc32      = '00000000|crc'
                db_name    = "$($sys.Name).lpl"
            })
        }
        if ($items.Count -eq 0) { continue }
        if ($DryRun) { & $Logger "[DRY-RUN] Would write $($sys.Name).lpl ($($items.Count) items)." 'INFO'; $created++; continue }
        if (-not (Test-Path -LiteralPath $plDir)) { New-Item -Path $plDir -ItemType Directory -Force | Out-Null }
        $playlist = [ordered]@{
            version            = '1.5'
            default_core_path  = ''
            default_core_name  = ''
            label_display_mode = 0
            right_thumbnail_mode = 0
            left_thumbnail_mode  = 0
            sort_mode          = 0
            items              = $items.ToArray()
        }
        ($playlist | ConvertTo-Json -Depth 6) | Set-Content -LiteralPath (Join-Path $plDir "$($sys.Name).lpl") -Encoding UTF8
        $created++
    }
    if ($created -gt 0 -and -not $DryRun) { & $Logger "Generated $created RetroArch playlist(s) in $plDir." 'SUCCESS' }
    return $created
}

# ----- module: LibraryAnalytics -----
<#
.SYNOPSIS
    Library analytics: statistics, duplicate-ROM detection, ROM extension checks,
    cheat-file inventory, custom-systems suggestions and a portable library manifest.
#>

Set-StrictMode -Version Latest

$script:AnNonRom = @('.txt','.xml','.dat','.jpg','.png','.bin','.m3u','.srm','.state','.cfg','.sav','.cht')

function Get-LibraryStatistics {
    <#
    .SYNOPSIS
        Aggregates genre distribution, release-decade distribution, total games and
        total playtime across all systems' gamelists.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][object[]] $Systems)
    $genres = @{}; $decades = @{}; $totalGames = 0; $totalPlaytime = 0
    foreach ($sys in $Systems) {
        if (-not (Test-Path -LiteralPath $sys.Gamelist)) { continue }
        $g = Read-Gamelist -Path $sys.Gamelist
        if (-not $g.Ok) { continue }
        foreach ($game in @($g.Games)) {
            $totalGames++
            $gn = $game.SelectSingleNode('genre')
            if ($gn -and $gn.InnerText) {
                $key = ($gn.InnerText -split '[,/]')[0].Trim()
                if ($key) { if (-not $genres.ContainsKey($key)) { $genres[$key]=0 }; $genres[$key]++ }
            }
            $rd = $game.SelectSingleNode('releasedate')
            if ($rd -and $rd.InnerText -match '^(\d{4})') {
                $decade = [string]([int]([int]$Matches[1] / 10) * 10) + 's'
                if (-not $decades.ContainsKey($decade)) { $decades[$decade]=0 }; $decades[$decade]++
            }
            $pt = $game.SelectSingleNode('playtime')
            if ($pt) { $v=0; if ([int]::TryParse($pt.InnerText,[ref]$v)) { $totalPlaytime += $v } }
        }
    }
    $topGenres = @($genres.GetEnumerator() | Sort-Object Value -Descending | Select-Object -First 10 | ForEach-Object { @{ Genre=$_.Key; Count=$_.Value } })
    $decadeArr = @($decades.GetEnumerator() | Sort-Object Name | ForEach-Object { @{ Decade=$_.Key; Count=$_.Value } })
    return @{ TotalGames=$totalGames; TotalPlaytimeHours=[math]::Round($totalPlaytime/3600,1); TopGenres=$topGenres; Decades=$decadeArr }
}

function Test-RomExtensions {
    <#
    .SYNOPSIS
        Reports ROM files whose extension is not in the system's allowed list.
    .PARAMETER ExtMap
        Hashtable system-name -> array of allowed extensions (lowercase, with dot).
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][object[]]  $Systems,
        [Parameter(Mandatory = $true)][hashtable] $ExtMap
    )
    $records = New-Object System.Collections.Generic.List[object]
    foreach ($sys in $Systems) {
        if (-not $ExtMap.ContainsKey($sys.Name)) { continue }
        $allowed = @($ExtMap[$sys.Name]) + @('.m3u','.txt')
        if (-not (Test-Path -LiteralPath $sys.RomPath)) { continue }
        $bad = New-Object System.Collections.Generic.List[string]
        Get-ChildItem -LiteralPath $sys.RomPath -File -ErrorAction SilentlyContinue | ForEach-Object {
            $e = $_.Extension.ToLower()
            if ($script:AnNonRom -contains $e) { return }
            if ($allowed -notcontains $e) { $bad.Add($_.Name) }
        }
        if ($bad.Count -gt 0) { $records.Add(@{ System=$sys.Name; Count=$bad.Count }) }
    }
    return $records.ToArray()
}

function Find-DuplicateRoms {
    <#
    .SYNOPSIS
        Finds byte-identical ROMs (same content, different names) within a system,
        hashing only same-size candidates and skipping files above MaxSizeMB.
        Report only - never deletes.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][string] $SystemRomDir, [int] $MaxSizeMB = 512)
    if (-not (Test-Path -LiteralPath $SystemRomDir)) { return @() }
    $limit = $MaxSizeMB * 1MB
    $bySize = @{}
    Get-ChildItem -LiteralPath $SystemRomDir -File -ErrorAction SilentlyContinue | ForEach-Object {
        if ($script:AnNonRom -contains $_.Extension.ToLower()) { return }
        if ($_.Length -gt $limit -or $_.Length -eq 0) { return }
        if (-not $bySize.ContainsKey($_.Length)) { $bySize[$_.Length] = New-Object System.Collections.Generic.List[object] }
        $bySize[$_.Length].Add($_)
    }
    $dups = New-Object System.Collections.Generic.List[object]
    foreach ($sz in $bySize.Keys) {
        $cands = $bySize[$sz]
        if ($cands.Count -lt 2) { continue }
        $byHash = @{}
        foreach ($f in $cands) {
            $h = Get-FileSha256 -Path $f.FullName
            if (-not $h) { continue }
            if (-not $byHash.ContainsKey($h)) { $byHash[$h] = New-Object System.Collections.Generic.List[string] }
            $byHash[$h].Add($f.Name)
        }
        foreach ($h in $byHash.Keys) { if ($byHash[$h].Count -gt 1) { $dups.Add(@{ Files=@($byHash[$h]) }) } }
    }
    return $dups.ToArray()
}

function Get-CheatFiles {
    [CmdletBinding()]
    param([string[]] $Roots = @())
    $count = 0
    foreach ($r in $Roots) {
        if (-not $r -or -not (Test-Path -LiteralPath $r)) { continue }
        $count += @(Get-ChildItem -LiteralPath $r -File -Recurse -Depth 5 -Filter '*.cht' -ErrorAction SilentlyContinue).Count
    }
    return $count
}

function Get-CustomSystemsSuggestion {
    <#
    .SYNOPSIS
        ROM sub-folders that are not declared in custom es_systems.xml - candidates
        for a custom system entry. Returns names.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][System.Collections.Specialized.OrderedDictionary] $Layout,
        [Parameter(Mandatory = $true)][object[]] $Systems
    )
    $known = New-Object System.Collections.Generic.HashSet[string] ([StringComparer]::OrdinalIgnoreCase)
    $ess = Join-Path $Layout.CustomSystems 'es_systems.xml'
    if (Test-Path -LiteralPath $ess) {
        try {
            $doc = New-Object System.Xml.XmlDocument; $doc.Load($ess)
            foreach ($n in $doc.SelectNodes('//system/name')) { [void]$known.Add($n.InnerText) }
        } catch { }
    }
    return @($Systems | Where-Object { $_.HasRoms -and -not $known.Contains($_.Name) } | ForEach-Object { $_.Name })
}

function Export-LibraryManifest {
    <#
    .SYNOPSIS
        Writes a portable JSON manifest of systems, game counts and media counts.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][object[]] $Systems,
        [Parameter(Mandatory = $true)][string]   $OutFile
    )
    $entries = New-Object System.Collections.Generic.List[object]
    foreach ($sys in $Systems) {
        $games = 0
        if (Test-Path -LiteralPath $sys.Gamelist) { $g = Read-Gamelist -Path $sys.Gamelist; if ($g.Ok) { $games = @($g.Games).Count } }
        $mediaCount = 0
        if (Test-Path -LiteralPath $sys.MediaDir) { $mediaCount = @(Get-ChildItem -LiteralPath $sys.MediaDir -File -Recurse -ErrorAction SilentlyContinue).Count }
        $entries.Add(@{ system=$sys.Name; games=$games; mediaFiles=$mediaCount; hasRoms=[bool]$sys.HasRoms })
    }
    $dir = Split-Path $OutFile -Parent
    if ($dir -and -not (Test-Path -LiteralPath $dir)) { New-Item -Path $dir -ItemType Directory -Force | Out-Null }
    @{ generated=(Get-Date -Format o); systems=$entries.ToArray() } | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $OutFile -Encoding UTF8
    return $entries.Count
}

# ----- module: LibraryAnalytics2 -----
<#
.SYNOPSIS
    Extended library analytics: cross-system duplicates, region distribution,
    completion stats, archive integrity, a health score, playtime leaderboard and
    newest additions.
#>

Set-StrictMode -Version Latest

$script:A2NonRom = @('.txt','.xml','.dat','.jpg','.png','.bin','.m3u','.srm','.state','.cfg','.sav','.cht')

function Find-CrossSystemDuplicates {
    <#
    .SYNOPSIS
        Returns ROM filenames that appear under more than one system's ROM folder.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][object[]] $Systems)
    $seen = @{}
    foreach ($sys in $Systems) {
        if (-not (Test-Path -LiteralPath $sys.RomPath)) { continue }
        Get-ChildItem -LiteralPath $sys.RomPath -File -ErrorAction SilentlyContinue | ForEach-Object {
            if ($script:A2NonRom -contains $_.Extension.ToLower()) { return }
            $k = $_.Name.ToLower()
            if (-not $seen.ContainsKey($k)) { $seen[$k] = New-Object System.Collections.Generic.List[string] }
            $seen[$k].Add($sys.Name)
        }
    }
    $dups = New-Object System.Collections.Generic.List[object]
    foreach ($k in $seen.Keys) { if ($seen[$k].Count -gt 1) { $dups.Add(@{ File=$k; Systems=@($seen[$k]) }) } }
    return $dups.ToArray()
}

function Get-RegionDistribution {
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][object[]] $Systems)
    $r = [ordered]@{ USA=0; Europe=0; Japan=0; World=0; Other=0 }
    foreach ($sys in $Systems) {
        if (-not (Test-Path -LiteralPath $sys.RomPath)) { continue }
        Get-ChildItem -LiteralPath $sys.RomPath -File -ErrorAction SilentlyContinue | ForEach-Object {
            if ($script:A2NonRom -contains $_.Extension.ToLower()) { return }
            $n = $_.Name
            if     ($n -match '(?i)\(USA') { $r.USA++ }
            elseif ($n -match '(?i)\(Europe|\(EUR') { $r.Europe++ }
            elseif ($n -match '(?i)\(Japan|\(JPN|\(JP\)') { $r.Japan++ }
            elseif ($n -match '(?i)\(World') { $r.World++ }
            else { $r.Other++ }
        }
    }
    return $r
}

function Get-CompletionStats {
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][object[]] $Systems)
    $total=0; $played=0; $fav=0
    foreach ($sys in $Systems) {
        if (-not (Test-Path -LiteralPath $sys.Gamelist)) { continue }
        $g = Read-Gamelist -Path $sys.Gamelist
        if (-not $g.Ok) { continue }
        foreach ($game in @($g.Games)) {
            $total++
            $f = $game.SelectSingleNode('favorite'); if ($f -and $f.InnerText -eq 'true') { $fav++ }
            $pc = $game.SelectSingleNode('playcount'); if ($pc) { $v=0; if ([int]::TryParse($pc.InnerText,[ref]$v) -and $v -gt 0) { $played++ } }
        }
    }
    $pct = if ($total -gt 0) { [math]::Round(($played*100.0)/$total,1) } else { 0 }
    return @{ Total=$total; Played=$played; Favorites=$fav; PlayedPercent=$pct }
}

function Test-RomArchives {
    <#
    .SYNOPSIS
        Tests .zip ROM archives for corruption (via .NET ZipArchive). Returns count
        of bad archives.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][object[]] $Systems)
    Add-Type -AssemblyName System.IO.Compression.FileSystem -ErrorAction SilentlyContinue
    $bad = 0
    foreach ($sys in $Systems) {
        if (-not (Test-Path -LiteralPath $sys.RomPath)) { continue }
        Get-ChildItem -LiteralPath $sys.RomPath -File -Filter '*.zip' -ErrorAction SilentlyContinue | ForEach-Object {
            try {
                $z = [System.IO.Compression.ZipFile]::OpenRead($_.FullName)
                try { $null = $z.Entries.Count } finally { $z.Dispose() }
            } catch { $bad++ }
        }
    }
    return $bad
}

function Get-LibraryHealthScore {
    <#
    .SYNOPSIS
        Computes a 0-100 library health score from media coverage, scrape ratio,
        BIOS completeness and emulator gaps.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][hashtable] $Report)
    $score = 100.0
    # Media coverage (average covers %).
    $cov = @($Report.Audit.MediaCoverage)
    if ($cov.Count -gt 0) {
        $avg = 0.0; foreach ($c in $cov) { $avg += [double]$c.Covers }
        $avg = $avg / $cov.Count
        $score -= ((100 - $avg) * 0.25)
    }
    # Missing BIOS penalty.
    $missingBios = @($Report.Bios).Count
    $score -= [math]::Min(20, $missingBios * 1.5)
    # Emulator gaps penalty.
    $gaps = @($Report.EmulatorGaps | Where-Object { $_.Missing }).Count
    $score -= [math]::Min(20, $gaps * 5)
    # Health errors/warnings.
    $score -= [math]::Min(15, $Report.Errors * 5)
    $score -= [math]::Min(10, $Report.Warnings * 1)
    if ($score -lt 0) { $score = 0 }
    return [math]::Round($score)
}

function Get-PlaytimeLeaderboard {
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][object[]] $Systems, [int] $Top = 10)
    $games = New-Object System.Collections.Generic.List[object]
    foreach ($sys in $Systems) {
        if (-not (Test-Path -LiteralPath $sys.Gamelist)) { continue }
        $g = Read-Gamelist -Path $sys.Gamelist
        if (-not $g.Ok) { continue }
        foreach ($game in @($g.Games)) {
            $pt = $game.SelectSingleNode('playtime'); if (-not $pt) { continue }
            $v = 0; if (-not [int]::TryParse($pt.InnerText,[ref]$v) -or $v -le 0) { continue }
            $nm = $game.SelectSingleNode('name')
            $games.Add(@{ Name=$(if($nm){$nm.InnerText}else{''}); System=$sys.Name; Minutes=[math]::Round($v/60) })
        }
    }
    return @($games | Sort-Object { $_.Minutes } -Descending | Select-Object -First $Top)
}

function Get-NewestAdditions {
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][object[]] $Systems, [int] $Top = 15)
    $files = New-Object System.Collections.Generic.List[object]
    foreach ($sys in $Systems) {
        if (-not (Test-Path -LiteralPath $sys.RomPath)) { continue }
        Get-ChildItem -LiteralPath $sys.RomPath -File -ErrorAction SilentlyContinue | ForEach-Object {
            if ($script:A2NonRom -contains $_.Extension.ToLower()) { return }
            $files.Add(@{ Name=$_.Name; System=$sys.Name; Added=$_.CreationTime.ToString('yyyy-MM-dd') ; Ticks=$_.CreationTime.Ticks })
        }
    }
    return @($files | Sort-Object { $_.Ticks } -Descending | Select-Object -First $Top | ForEach-Object { @{ Name=$_.Name; System=$_.System; Added=$_.Added } })
}

# ----- module: LibraryInsights -----
<#
.SYNOPSIS
    Library insights: per-system gamelist stats, abandoned games, save-state
    inventory and gamelist change diff against the most recent backup.
#>

Set-StrictMode -Version Latest

function Get-PerSystemGamelistStats {
    <#
    .SYNOPSIS
        Per-system: game count, average rating, oldest and newest release year.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][object[]] $Systems)
    $out = New-Object System.Collections.Generic.List[object]
    foreach ($sys in $Systems) {
        if (-not (Test-Path -LiteralPath $sys.Gamelist)) { continue }
        $g = Read-Gamelist -Path $sys.Gamelist
        if (-not $g.Ok) { continue }
        $n=0; $ratingSum=0.0; $ratingN=0; $minY=9999; $maxY=0
        foreach ($game in @($g.Games)) {
            $n++
            $r = $game.SelectSingleNode('rating'); if ($r) { $v=0.0; if ([double]::TryParse($r.InnerText,[ref]$v)) { $ratingSum+=$v; $ratingN++ } }
            $rd = $game.SelectSingleNode('releasedate'); if ($rd -and $rd.InnerText -match '^(\d{4})') { $y=[int]$Matches[1]; if ($y -ge 1970 -and $y -le 2100) { if ($y -lt $minY) {$minY=$y}; if ($y -gt $maxY) {$maxY=$y} } }
        }
        if ($n -eq 0) { continue }
        $out.Add(@{ System=$sys.Name; Games=$n; AvgRating=$(if($ratingN){[math]::Round($ratingSum/$ratingN,2)}else{0}); Oldest=$(if($maxY){$minY}else{0}); Newest=$maxY })
    }
    return $out.ToArray()
}

function Get-AbandonedGames {
    <#
    .SYNOPSIS
        Counts games that were started (playcount>0) but barely played
        (playtime < ThresholdMinutes).
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][object[]] $Systems, [int] $ThresholdMinutes = 5)
    $count = 0; $limit = $ThresholdMinutes * 60
    foreach ($sys in $Systems) {
        if (-not (Test-Path -LiteralPath $sys.Gamelist)) { continue }
        $g = Read-Gamelist -Path $sys.Gamelist
        if (-not $g.Ok) { continue }
        foreach ($game in @($g.Games)) {
            $pc = $game.SelectSingleNode('playcount'); $pcv=0; if ($pc) { [void][int]::TryParse($pc.InnerText,[ref]$pcv) }
            $pt = $game.SelectSingleNode('playtime'); $ptv=0; if ($pt) { [void][int]::TryParse($pt.InnerText,[ref]$ptv) }
            if ($pcv -gt 0 -and $ptv -gt 0 -and $ptv -lt $limit) { $count++ }
        }
    }
    return $count
}

function Get-SavestateInventory {
    <#
    .SYNOPSIS
        Counts save-state files under the emulator roots / ROM dir.
    #>
    [CmdletBinding()]
    param([string[]] $Roots = @())
    $exts = @('.state','.ss0','.ss1','.ss2','.sstate','.p2s','.dsv','.bsv')
    $count = 0
    foreach ($r in $Roots) {
        if (-not $r -or -not (Test-Path -LiteralPath $r)) { continue }
        $count += @(Get-ChildItem -LiteralPath $r -File -Recurse -Depth 5 -ErrorAction SilentlyContinue | Where-Object { $exts -contains $_.Extension.ToLower() -or $_.Name -match '\.state\d*$' }).Count
    }
    return $count
}

function Get-GamelistDiff {
    <#
    .SYNOPSIS
        Compares each system's current gamelist game-count against the most recent
        snapshot backup and returns the net change (added minus removed).
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][object[]] $Systems,
        [Parameter(Mandatory = $true)][string]   $BackupRoot
    )
    $snap = Get-ChildItem -LiteralPath $BackupRoot -Directory -Filter 'snapshot_gamelists_*' -ErrorAction SilentlyContinue |
            Sort-Object Name -Descending | Select-Object -First 1
    if (-not $snap) { return @() }
    $out = New-Object System.Collections.Generic.List[object]
    foreach ($sys in $Systems) {
        if (-not (Test-Path -LiteralPath $sys.Gamelist)) { continue }
        $now = Read-Gamelist -Path $sys.Gamelist
        $nowN = if ($now.Ok) { @($now.Games).Count } else { 0 }
        $oldPath = Join-Path $snap.FullName (Join-Path $sys.Name 'gamelist.xml')
        $oldN = 0
        if (Test-Path -LiteralPath $oldPath) { $old = Read-Gamelist -Path $oldPath; if ($old.Ok) { $oldN = @($old.Games).Count } }
        if ($nowN -ne $oldN) { $out.Add(@{ System=$sys.Name; Was=$oldN; Now=$nowN; Delta=($nowN-$oldN) }) }
    }
    return $out.ToArray()
}

# ----- module: SaveManager -----
<#
.SYNOPSIS
    Save-data protection: archives emulator save files / save states / memory cards
    (the most precious, irreplaceable user data) and reports orphaned saves.
.DESCRIPTION
    Never deletes anything. Copies known save locations into a timestamped archive
    under the backup tree so a bad emulator update or config change can't lose your
    progress. Also flags save files that no longer have a matching ROM.
#>

Set-StrictMode -Version Latest

# Folder names that typically hold saves/states/memory cards across emulators.
$script:SaveFolderNames = @('saves','states','savestates','memcards','memorycards','sav','battery','nand','saveData')
$script:SaveExtensions  = @('.srm','.sav','.state','.ss0','.ss1','.mcr','.mcd','.ps2','.gme','.dsv','.fs','.bsv')

function Backup-SaveData {
    <#
    .SYNOPSIS
        Archives save data found under the emulator roots and the ROM directory.
        Returns count of files archived.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string]   $RomDir,
        [string[]] $EmulatorRoots = @(),
        [Parameter(Mandatory = $true)][string]   $BackupRoot,
        [Parameter(Mandatory = $true)][scriptblock] $Logger,
        [switch] $DryRun
    )
    $stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
    $dest  = Join-Path $BackupRoot ("savedata_$stamp")
    $count = 0
    $roots = @(@($EmulatorRoots) + $RomDir | Where-Object { $_ -and (Test-Path -LiteralPath $_) } | Select-Object -Unique)

    foreach ($root in $roots) {
        # 1) Whole save/state folders.
        foreach ($folderName in $script:SaveFolderNames) {
            Get-ChildItem -LiteralPath $root -Directory -Recurse -Depth 4 -ErrorAction SilentlyContinue |
                Where-Object { $_.Name -ieq $folderName } | ForEach-Object {
                    $files = @(Get-ChildItem -LiteralPath $_.FullName -File -Recurse -ErrorAction SilentlyContinue)
                    foreach ($f in $files) {
                        if ($f.FullName.Length -gt 240) { continue }
                        if ($DryRun) { $count++; continue }
                        $rel = $f.FullName.Substring($root.Length).TrimStart('\','/')
                        $dst = Join-Path (Join-Path $dest (Split-Path $root -Leaf)) $rel
                        $dstDir = Split-Path $dst -Parent
                        if (-not (Test-Path -LiteralPath $dstDir)) { New-Item -Path $dstDir -ItemType Directory -Force | Out-Null }
                        Copy-Item -LiteralPath $f.FullName -Destination $dst -Force -ErrorAction SilentlyContinue
                        $count++
                    }
                }
        }
    }
    # 2) Loose save files sitting next to ROMs.
    if (Test-Path -LiteralPath $RomDir) {
        Get-ChildItem -LiteralPath $RomDir -File -Recurse -Depth 3 -ErrorAction SilentlyContinue |
            Where-Object { $script:SaveExtensions -contains $_.Extension.ToLower() } | ForEach-Object {
                if ($DryRun) { $count++; return }
                $rel = $_.FullName.Substring($RomDir.Length).TrimStart('\','/')
                $dst = Join-Path (Join-Path $dest 'roms') $rel
                $dstDir = Split-Path $dst -Parent
                if (-not (Test-Path -LiteralPath $dstDir)) { New-Item -Path $dstDir -ItemType Directory -Force | Out-Null }
                Copy-Item -LiteralPath $_.FullName -Destination $dst -Force -ErrorAction SilentlyContinue
                $count++
            }
    }
    if ($count -gt 0 -and -not $DryRun) { & $Logger "Archived $count save/state file(s) to $dest." 'SUCCESS' }
    elseif ($count -gt 0) { & $Logger "[DRY-RUN] Would archive $count save/state file(s)." 'INFO' }
    return $count
}

function Get-OrphanedSaves {
    <#
    .SYNOPSIS
        Returns save files (by stem) under the ROM dir that have no matching ROM.
        Report only - never deleted (saves are irreplaceable).
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][string] $SystemRomDir)
    $orphans = New-Object System.Collections.Generic.List[string]
    if (-not (Test-Path -LiteralPath $SystemRomDir)) { return @() }
    $romStems = New-Object System.Collections.Generic.HashSet[string] ([StringComparer]::OrdinalIgnoreCase)
    Get-ChildItem -LiteralPath $SystemRomDir -File -ErrorAction SilentlyContinue | ForEach-Object {
        if ($script:SaveExtensions -notcontains $_.Extension.ToLower()) {
            [void]$romStems.Add([System.IO.Path]::GetFileNameWithoutExtension($_.Name))
        }
    }
    Get-ChildItem -LiteralPath $SystemRomDir -File -Recurse -Depth 3 -ErrorAction SilentlyContinue |
        Where-Object { $script:SaveExtensions -contains $_.Extension.ToLower() } | ForEach-Object {
            $stem = [System.IO.Path]::GetFileNameWithoutExtension($_.Name)
            if (-not $romStems.Contains($stem)) { $orphans.Add($_.Name) }
        }
    return $orphans.ToArray()
}

# ----- module: CollectionsManager -----
<#
.SYNOPSIS
    ES-DE custom collections generation and 1G1R region hiding.
.DESCRIPTION
    * New-EsdeCollections - builds custom collection files ES-DE reads from the
      collections folder: Favorites (from <favorite>) and Played (from <playcount>).
    * Invoke-RegionHide - for region-duplicate ROM sets, keeps the preferred-region
      copy visible and marks the others <hidden> in the gamelist (reversible via the
      backup/restore system; never deletes ROMs).
#>

Set-StrictMode -Version Latest

function New-EsdeCollections {
    <#
    .SYNOPSIS
        Writes custom-Favorites.cfg and custom-Played.cfg into the collections dir,
        using full ROM paths (the format ES-DE custom collections accept).
        Returns @{ Favorites; Played }.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][object[]] $Systems,
        [Parameter(Mandatory = $true)][string]   $CollectionsDir,
        [Parameter(Mandatory = $true)][scriptblock] $Logger,
        [switch] $DryRun
    )
    $fav = New-Object System.Collections.Generic.List[string]
    $played = New-Object System.Collections.Generic.List[string]
    foreach ($sys in $Systems) {
        if (-not (Test-Path -LiteralPath $sys.Gamelist)) { continue }
        $g = Read-Gamelist -Path $sys.Gamelist
        if (-not $g.Ok) { continue }
        foreach ($game in @($g.Games)) {
            $pn = $game.SelectSingleNode('path'); if (-not $pn -or -not $pn.InnerText) { continue }
            $rel = ($pn.InnerText -replace '/','\') -replace '^\.\\',''
            $full = Join-Path $sys.RomPath $rel
            $f = $game.SelectSingleNode('favorite')
            if ($f -and $f.InnerText -eq 'true') { $fav.Add($full) }
            $pc = $game.SelectSingleNode('playcount')
            if ($pc) { $v = 0; if ([int]::TryParse($pc.InnerText, [ref]$v) -and $v -gt 0) { $played.Add($full) } }
        }
    }
    if (-not $DryRun) {
        if (-not (Test-Path -LiteralPath $CollectionsDir)) { New-Item -Path $CollectionsDir -ItemType Directory -Force | Out-Null }
        if ($fav.Count -gt 0)    { [System.IO.File]::WriteAllLines((Join-Path $CollectionsDir 'custom-Favorites.cfg'), $fav.ToArray(), (New-Object System.Text.UTF8Encoding($false))) }
        if ($played.Count -gt 0) { [System.IO.File]::WriteAllLines((Join-Path $CollectionsDir 'custom-Played.cfg'), $played.ToArray(), (New-Object System.Text.UTF8Encoding($false))) }
    }
    & $Logger "Collections: $($fav.Count) favorite(s), $($played.Count) played title(s)." 'INFO'
    return @{ Favorites = $fav.Count; Played = $played.Count }
}

function Invoke-RegionHide {
    <#
    .SYNOPSIS
        For each region-duplicate group in a system, keeps the preferred-region copy
        and marks the rest <hidden>. Returns count hidden.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string] $GamelistPath,
        [string[]] $PreferredRegions = @('USA','World','Europe','Japan'),
        [Parameter(Mandatory = $true)][string] $BackupRoot,
        [Parameter(Mandatory = $true)][scriptblock] $Logger,
        [switch] $DryRun
    )
    $hidden = 0
    if (-not (Test-Path -LiteralPath $GamelistPath)) { return 0 }
    $g = Read-Gamelist -Path $GamelistPath
    if (-not $g.Ok) { return 0 }
    $xml = $g.Xml

    # Group games by region-insensitive base name.
    $groups = @{}
    foreach ($game in @($xml.gameList.SelectNodes('game'))) {
        $nm = $game.SelectSingleNode('name'); $pn = $game.SelectSingleNode('path')
        $label = if ($nm -and $nm.InnerText) { $nm.InnerText } elseif ($pn -and $pn.InnerText) { [System.IO.Path]::GetFileNameWithoutExtension($pn.InnerText) } else { $null }
        if (-not $label) { continue }
        $base = ([Regex]::Replace($label, '\s*[\(\[].*$', '')).Trim().ToLower()
        if (-not $base) { continue }
        if (-not $groups.ContainsKey($base)) { $groups[$base] = New-Object System.Collections.Generic.List[object] }
        $groups[$base].Add([pscustomobject]@{ Node=$game; Label=$label })
    }

    function RegionRank([string]$label, [string[]]$prefs) {
        for ($i=0; $i -lt $prefs.Count; $i++) { if ($label -match ('(?i)\(' + [Regex]::Escape($prefs[$i])) ) { return $i } }
        return 999
    }

    $changed = $false
    foreach ($base in $groups.Keys) {
        $items = $groups[$base]
        if ($items.Count -lt 2) { continue }
        $ranked = $items | Sort-Object @{ Expression = { RegionRank $_.Label $PreferredRegions } }
        $keep = $ranked[0]
        foreach ($it in $ranked) {
            if ($it -eq $keep) { continue }
            $h = $it.Node.SelectSingleNode('hidden')
            if (-not $h) { $h = $xml.CreateElement('hidden'); [void]$it.Node.AppendChild($h) }
            if ($h.InnerText -ne 'true') { if (-not $DryRun) { $h.InnerText = 'true' }; $hidden++; $changed = $true }
        }
    }

    if ($changed -and -not $DryRun) {
        Backup-File -Path $GamelistPath -BackupRoot $BackupRoot | Out-Null
        Save-Gamelist -Xml $xml -Prefix $g.Prefix -Path $GamelistPath
        & $Logger "1G1R: hid $hidden non-preferred-region duplicate(s) in $(Split-Path (Split-Path $GamelistPath -Parent) -Leaf)." 'SUCCESS'
    }
    return $hidden
}

# ----- module: CollectionsPlus -----
<#
.SYNOPSIS
    Additional ES-DE custom collections and auto-favorites.
.DESCRIPTION
    Builds genre, decade, never-played and kid-game custom collections from the
    gamelists, and (opt-in) marks the most-played titles as favorites. Reads every
    gamelist once via Get-AllGameRecords for efficiency.
#>

Set-StrictMode -Version Latest

function Get-AllGameRecords {
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][object[]] $Systems)
    $recs = New-Object System.Collections.Generic.List[object]
    foreach ($sys in $Systems) {
        if (-not (Test-Path -LiteralPath $sys.Gamelist)) { continue }
        $g = Read-Gamelist -Path $sys.Gamelist
        if (-not $g.Ok) { continue }
        foreach ($game in @($g.Games)) {
            $pn = $game.SelectSingleNode('path'); if (-not $pn -or -not $pn.InnerText) { continue }
            $rel = ($pn.InnerText -replace '/','\') -replace '^\.\\',''
            $full = Join-Path $sys.RomPath $rel
            $nm = $game.SelectSingleNode('name')
            $gn = $game.SelectSingleNode('genre')
            $rd = $game.SelectSingleNode('releasedate')
            $pc = $game.SelectSingleNode('playcount'); $pcv = 0; if ($pc) { [void][int]::TryParse($pc.InnerText,[ref]$pcv) }
            $pt = $game.SelectSingleNode('playtime');  $ptv = 0; if ($pt) { [void][int]::TryParse($pt.InnerText,[ref]$ptv) }
            $fv = $game.SelectSingleNode('favorite')
            $kg = $game.SelectSingleNode('kidgame')
            $year = $null
            if ($rd -and $rd.InnerText -match '^(\d{4})') { $year = [int]$Matches[1] }
            $recs.Add([pscustomobject]@{
                FullPath=$full; Name=$(if($nm){$nm.InnerText}else{[System.IO.Path]::GetFileNameWithoutExtension($rel)})
                System=$sys.Name; Genre=$(if($gn){($gn.InnerText -split '[,/]')[0].Trim()}else{''})
                Year=$year; PlayCount=$pcv; PlayTime=$ptv
                Favorite=($fv -and $fv.InnerText -eq 'true'); KidGame=($kg -and $kg.InnerText -eq 'true')
            })
        }
    }
    return $recs.ToArray()
}

function Write-CollectionFile {
    param([string]$Dir, [string]$Name, [string[]]$Paths, [switch]$DryRun)
    if (@($Paths).Count -eq 0) { return 0 }
    if ($DryRun) { return @($Paths).Count }
    if (-not (Test-Path -LiteralPath $Dir)) { New-Item -Path $Dir -ItemType Directory -Force | Out-Null }
    $safe = ($Name -replace '[\\/:*?"<>|]', '_').Trim()
    [System.IO.File]::WriteAllLines((Join-Path $Dir ("custom-$safe.cfg")), @($Paths), (New-Object System.Text.UTF8Encoding($false)))
    return @($Paths).Count
}

function New-AutoCollections {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][object[]] $Records,
        [Parameter(Mandatory = $true)][string]   $CollectionsDir,
        [Parameter(Mandatory = $true)][scriptblock] $Logger,
        [switch] $DryRun
    )
    $byGenre = @{}
    foreach ($r in $Records) { if ($r.Genre) { if (-not $byGenre.ContainsKey($r.Genre)) { $byGenre[$r.Genre]=New-Object System.Collections.Generic.List[string] }; $byGenre[$r.Genre].Add($r.FullPath) } }
    $genreCount = 0
    foreach ($k in ($byGenre.Keys | Sort-Object { $byGenre[$_].Count } -Descending | Select-Object -First 15)) {
        if ($byGenre[$k].Count -lt 5) { continue }
        if ((Write-CollectionFile -Dir $CollectionsDir -Name $k -Paths $byGenre[$k] -DryRun:$DryRun) -gt 0) { $genreCount++ }
    }
    $byDecade = @{}
    foreach ($r in $Records) { if ($r.Year) { $d = [string]([int]($r.Year/10)*10) + 's'; if (-not $byDecade.ContainsKey($d)) { $byDecade[$d]=New-Object System.Collections.Generic.List[string] }; $byDecade[$d].Add($r.FullPath) } }
    $decadeCount = 0
    foreach ($k in $byDecade.Keys) { if ((Write-CollectionFile -Dir $CollectionsDir -Name $k -Paths $byDecade[$k] -DryRun:$DryRun) -gt 0) { $decadeCount++ } }
    $never = @($Records | Where-Object { $_.PlayCount -eq 0 } | ForEach-Object { $_.FullPath })
    $kids  = @($Records | Where-Object { $_.KidGame } | ForEach-Object { $_.FullPath })
    $neverN = Write-CollectionFile -Dir $CollectionsDir -Name 'Never Played' -Paths $never -DryRun:$DryRun
    $kidsN  = Write-CollectionFile -Dir $CollectionsDir -Name 'Kids' -Paths $kids -DryRun:$DryRun
    & $Logger "Collections: $genreCount genre, $decadeCount decade, never-played ($neverN), kids ($kidsN)." 'INFO'
    return @{ Genres=$genreCount; Decades=$decadeCount; NeverPlayed=$neverN; KidGames=$kidsN }
}

function Set-AutoFavorites {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][object[]] $Systems,
        [int] $TopPerSystem = 5,
        [Parameter(Mandatory = $true)][string] $BackupRoot,
        [Parameter(Mandatory = $true)][scriptblock] $Logger,
        [switch] $DryRun
    )
    $favorited = 0
    foreach ($sys in $Systems) {
        if (-not (Test-Path -LiteralPath $sys.Gamelist)) { continue }
        $g = Read-Gamelist -Path $sys.Gamelist
        if (-not $g.Ok) { continue }
        $games = @($g.Games | ForEach-Object {
            $pt = $_.SelectSingleNode('playtime'); $v=0; if ($pt) { [void][int]::TryParse($pt.InnerText,[ref]$v) }
            [pscustomobject]@{ Node=$_; Play=$v }
        } | Where-Object { $_.Play -gt 0 } | Sort-Object Play -Descending | Select-Object -First $TopPerSystem)
        if ($games.Count -eq 0) { continue }
        $changed = $false
        foreach ($g2 in $games) {
            $fv = $g2.Node.SelectSingleNode('favorite')
            if (-not $fv) { $fv = $g.Xml.CreateElement('favorite'); [void]$g2.Node.AppendChild($fv) }
            if ($fv.InnerText -ne 'true') { if (-not $DryRun) { $fv.InnerText = 'true' }; $favorited++; $changed = $true }
        }
        if ($changed -and -not $DryRun) {
            Backup-File -Path $sys.Gamelist -BackupRoot $BackupRoot | Out-Null
            Save-Gamelist -Xml $g.Xml -Prefix $g.Prefix -Path $sys.Gamelist
        }
    }
    if ($favorited -gt 0) { & $Logger "Auto-favorited $favorited most-played title(s)." 'SUCCESS' }
    return $favorited
}

# ----- module: ThemeManager -----
<#
.SYNOPSIS
    ES-DE theme installation (open-source themes) and active-theme selection.
.DESCRIPTION
    ES-DE themes are open-source (MIT/CC) and freely redistributable, so they CAN
    be installed automatically. Uses git clone when git is available, else a zip
    download. Also sets the active theme in es_settings.xml.
#>

Set-StrictMode -Version Latest

# A small curated list of well-known, open-source ES-DE themes.
$script:KnownThemes = @(
    @{ Name='slate-es-de';        Git='https://gitlab.com/es-de/themes/slate-es-de.git' },
    @{ Name='modern-es-de';       Git='https://gitlab.com/es-de/themes/modern-es-de.git' },
    @{ Name='art-book-next-es-de';Git='https://github.com/anthonycaccese/art-book-next-es-de.git' }
)

function Install-EsdeThemes {
    <#
    .SYNOPSIS
        Installs any missing curated themes into the themes directory. Returns count.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string] $ThemesDir,
        [Parameter(Mandatory = $true)][scriptblock] $Logger,
        [switch] $DryRun
    )
    $git = Get-Command git -ErrorAction SilentlyContinue
    $installed = 0
    if (-not (Test-Path -LiteralPath $ThemesDir)) {
        if (-not $DryRun) { New-Item -Path $ThemesDir -ItemType Directory -Force | Out-Null }
    }
    foreach ($t in $script:KnownThemes) {
        $dest = Join-Path $ThemesDir $t.Name
        if (Test-Path -LiteralPath $dest) { continue }
        if ($DryRun) { & $Logger "[DRY-RUN] Would install theme $($t.Name)." 'INFO'; $installed++; continue }
        try {
            if ($git) {
                $p = Start-Process -FilePath $git.Source -ArgumentList @('clone','--depth','1',$t.Git,$dest) -NoNewWindow -Wait -PassThru
                if ($p.ExitCode -eq 0 -and (Test-Path -LiteralPath $dest)) { & $Logger "Installed theme $($t.Name) (git)." 'SUCCESS'; $installed++ }
            } else {
                & $Logger "git not found; cannot auto-install theme $($t.Name). Install git or add themes manually." 'WARN'
            }
        } catch { & $Logger "Theme install failed ($($t.Name)): $($_.Exception.Message)" 'WARN' }
    }
    return $installed
}

function Set-ActiveTheme {
    <#
    .SYNOPSIS
        Sets es_settings ThemeSet to an installed theme if the current one is missing.
        Returns the theme name applied, or ''.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string] $SettingsFile,
        [Parameter(Mandatory = $true)][string] $ThemesDir,
        [Parameter(Mandatory = $true)][string] $BackupRoot,
        [Parameter(Mandatory = $true)][scriptblock] $Logger,
        [switch] $DryRun
    )
    $installed = @()
    if (Test-Path -LiteralPath $ThemesDir) { $installed = @(Get-ChildItem -LiteralPath $ThemesDir -Directory -ErrorAction SilentlyContinue | ForEach-Object { $_.Name }) }
    if ($installed.Count -eq 0) { return '' }
    $current = Get-EsdeSetting -SettingsFile $SettingsFile -Name 'ThemeSet'
    if ($current -and ($installed -contains $current)) { return $current }   # already valid
    $pick = $installed | Select-Object -First 1
    if ($DryRun) { & $Logger "[DRY-RUN] Would set active theme to $pick." 'INFO'; return $pick }
    Backup-File -Path $SettingsFile -BackupRoot $BackupRoot | Out-Null
    Set-EsdeSettingValue -SettingsFile $SettingsFile -Type 'string' -Name 'ThemeSet' -Value $pick
    & $Logger "Set active ES-DE theme to '$pick'." 'SUCCESS'
    return $pick
}

# ----- module: BiosAdvanced -----
<#
.SYNOPSIS
    Advanced BIOS validation: presence, MD5 verification against known-good hashes,
    and wrong-location detection. Never deletes or downloads BIOS (copyright); it
    only reports, and points each file at the correct expected location.
#>

Set-StrictMode -Version Latest

function Get-FileMd5 {
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][string] $Path)
    try {
        $md5 = [System.Security.Cryptography.MD5]::Create()
        $fs  = [System.IO.File]::OpenRead($Path)
        try { return ([BitConverter]::ToString($md5.ComputeHash($fs))).Replace('-','').ToLower() }
        finally { $fs.Dispose(); $md5.Dispose() }
    } catch { return $null }
}

function Test-BiosAdvanced {
    <#
    .SYNOPSIS
        Validates BIOS files. For each requirement returns a record with Status:
          Present | WrongHash | WrongLocation | Missing
    .PARAMETER BiosDir
        The canonical BIOS directory (files are expected directly here).
    .PARAMETER Requirements
        Array of @{ file; system; md5(optional) }.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string]   $BiosDir,
        [Parameter(Mandatory = $true)][object[]] $Requirements,
        [Parameter(Mandatory = $true)][scriptblock] $Logger
    )
    $records = New-Object System.Collections.Generic.List[object]
    if (-not (Test-Path -LiteralPath $BiosDir)) {
        & $Logger "BIOS directory not found: $BiosDir" 'WARN'
    }

    # Index every file under the BIOS tree (recursive) for location detection.
    $allByName = @{}
    if (Test-Path -LiteralPath $BiosDir) {
        Get-ChildItem -LiteralPath $BiosDir -Recurse -File -ErrorAction SilentlyContinue | ForEach-Object {
            $k = $_.Name.ToLower()
            if (-not $allByName.ContainsKey($k)) { $allByName[$k] = $_.FullName }
        }
    }

    foreach ($req in $Requirements) {
        $name   = $req.file
        $expectAt = Join-Path $BiosDir $name
        $status = 'Missing'; $detail = "Place '$name' in $BiosDir (needed for $($req.system))."
        $foundAt = $null
        $reqMd5 = if ($req.PSObject.Properties.Name -contains 'md5' -and $req.md5) { ([string]$req.md5).ToLower() } else { $null }

        if (Test-Path -LiteralPath $expectAt) {
            $foundAt = $expectAt
            if ($reqMd5) {
                $actual = Get-FileMd5 -Path $expectAt
                if ($actual -eq $reqMd5) { $status = 'Present'; $detail = 'Present and hash-verified.' }
                else { $status = 'WrongHash'; $detail = "Present but MD5 mismatch (expected $reqMd5, got $actual)." }
            } else { $status = 'Present'; $detail = 'Present (no known hash to verify).' }
        }
        elseif ($allByName.ContainsKey($name.ToLower())) {
            $status = 'WrongLocation'
            $foundAt = $allByName[$name.ToLower()]
            $detail = "Found at $foundAt but ES-DE expects it at $expectAt."
        }

        if ($status -ne 'Present') { & $Logger "BIOS $status`: $name ($($req.system))" 'WARN' }
        $records.Add([ordered]@{ File = $name; System = $req.system; Status = $status; Detail = $detail; ExpectedAt = $expectAt; FoundAt = $foundAt; Md5 = $reqMd5 })
    }

    $present = @($records | Where-Object { $_.Status -eq 'Present' }).Count
    & $Logger "BIOS check: $present/$($records.Count) present and valid." 'INFO'
    return $records.ToArray()
}

function Invoke-BiosRelocate {
    <#
    .SYNOPSIS
        "Fixes directions" for BIOS the user already owns - it NEVER downloads
        copyrighted BIOS. Two safe, legal actions:
          1. Relocate: a required BIOS found elsewhere in the tree is copied to the
             canonical location ES-DE expects (the source is left in place).
          2. Propagate: a BIOS present in the canonical folder is copied into every
             other emulator BIOS directory that is missing it, so all emulators see
             it. Existing destination files are backed up first; nothing is deleted.
    .OUTPUTS
        Hashtable: Relocated, Propagated.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][object[]] $Records,
        [Parameter(Mandatory = $true)][string]   $CanonicalDir,
        [string[]] $CandidateDirs = @(),
        [Parameter(Mandatory = $true)][string]   $BackupRoot,
        [Parameter(Mandatory = $true)][scriptblock] $Logger,
        [switch] $DryRun
    )
    $relocated = 0; $propagated = 0
    $targets = @(@($CandidateDirs) + $CanonicalDir | Where-Object { $_ } | Select-Object -Unique)

    foreach ($rec in $Records) {
        # 1) Relocate wrong-location files into the canonical folder.
        if ($rec.Status -eq 'WrongLocation' -and $rec.FoundAt -and (Test-Path -LiteralPath $rec.FoundAt)) {
            if ($DryRun) { & $Logger "[DRY-RUN] Would relocate $($rec.File) -> $($rec.ExpectedAt)" 'INFO'; $relocated++; continue }
            $dstDir = Split-Path $rec.ExpectedAt -Parent
            if (-not (Test-Path -LiteralPath $dstDir)) { New-Item -Path $dstDir -ItemType Directory -Force | Out-Null }
            Copy-Item -LiteralPath $rec.FoundAt -Destination $rec.ExpectedAt -Force
            & $Logger "Relocated BIOS $($rec.File) to canonical location $($rec.ExpectedAt)." 'SUCCESS'
            $relocated++
            $rec.FoundAt = $rec.ExpectedAt; $rec.Status = 'Present'
        }
    }

    # 2) Propagate every BIOS that now exists in the canonical folder to all other
    #    emulator BIOS directories that are missing it.
    foreach ($rec in $Records) {
        $src = Join-Path $CanonicalDir $rec.File
        if (-not (Test-Path -LiteralPath $src)) { continue }
        foreach ($dir in $targets) {
            if ($dir -eq $CanonicalDir) { continue }
            $dst = Join-Path $dir $rec.File
            if (Test-Path -LiteralPath $dst) { continue }   # already there
            if ($DryRun) { & $Logger "[DRY-RUN] Would copy $($rec.File) -> $dir" 'INFO'; $propagated++; continue }
            if (-not (Test-Path -LiteralPath $dir)) { New-Item -Path $dir -ItemType Directory -Force | Out-Null }
            Copy-Item -LiteralPath $src -Destination $dst -Force
            $propagated++
        }
    }
    if ($propagated -gt 0) { & $Logger "Propagated BIOS to $propagated additional emulator location(s)." 'SUCCESS' }
    return @{ Relocated = $relocated; Propagated = $propagated }
}

# ----- module: EsdeEnvironmentAudit -----
<#
.SYNOPSIS
    ES-DE environment audit: custom es_systems.xml, themes, collections, alternative
    emulator audit, safe es_settings.xml optimization, language, suite version,
    connectivity, empty-system advisory, custom-systems suggestions, controller
    config verification and a ROM hash manifest.
#>

Set-StrictMode -Version Latest

$script:SuiteVersion = '2.0'

function Get-SuiteVersion { return @{ Version = $script:SuiteVersion; Built = (Get-Date -Format 'yyyy-MM-dd') } }

function Test-EsSystemsXml {
    <#
    .SYNOPSIS
        Validates custom_systems/es_systems.xml is well-formed and counts systems.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][System.Collections.Specialized.OrderedDictionary] $Layout)
    $path = Join-Path $Layout.CustomSystems 'es_systems.xml'
    if (-not (Test-Path -LiteralPath $path)) { return @{ Present = $false; Valid = $true; Count = 0; Path = $path } }
    try {
        $xml = New-Object System.Xml.XmlDocument
        $xml.Load($path)
        $count = @($xml.SelectNodes('//system')).Count
        return @{ Present = $true; Valid = $true; Count = $count; Path = $path }
    } catch {
        return @{ Present = $true; Valid = $false; Count = 0; Path = $path; Error = $_.Exception.Message }
    }
}

function Get-EsdeThemes {
    <#
    .SYNOPSIS
        Lists installed themes and the active theme (from es_settings 'ThemeSet').
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][System.Collections.Specialized.OrderedDictionary] $Layout)
    $themes = @()
    if (Test-Path -LiteralPath $Layout.Themes) {
        $themes = @(Get-ChildItem -LiteralPath $Layout.Themes -Directory -ErrorAction SilentlyContinue | ForEach-Object { $_.Name })
    }
    $active = Get-EsdeSetting -SettingsFile $Layout.SettingsFile -Name 'ThemeSet'
    $activePresent = ($active -and ($themes -contains $active))
    return @{ Installed = $themes; Active = $active; ActivePresent = $activePresent }
}

function Test-Collections {
    <#
    .SYNOPSIS
        Validates custom collection files (collections/custom-*.cfg); each line is a
        ROM path. Reports broken (non-existent) references per collection.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][System.Collections.Specialized.OrderedDictionary] $Layout)
    $records = New-Object System.Collections.Generic.List[object]
    if (-not (Test-Path -LiteralPath $Layout.Collections)) { return $records.ToArray() }
    Get-ChildItem -LiteralPath $Layout.Collections -Filter 'custom-*.cfg' -File -ErrorAction SilentlyContinue | ForEach-Object {
        $total = 0; $broken = 0
        foreach ($line in (Get-Content -LiteralPath $_.FullName -Encoding UTF8 -ErrorAction SilentlyContinue)) {
            $p = $line.Trim()
            if (-not $p) { continue }
            $total++
            $expanded = $p -replace '%ROMPATH%', $Layout.RomDir
            $expanded = [Environment]::ExpandEnvironmentVariables($expanded) -replace '/', '\'
            if (-not (Test-Path -LiteralPath $expanded)) { $broken++ }
        }
        $records.Add(@{ Collection = $_.BaseName; Entries = $total; Broken = $broken })
    }
    return $records.ToArray()
}

function Get-AltEmulatorAudit {
    <#
    .SYNOPSIS
        Reads each gamelist's <alternativeEmulator><label> and flags labels whose
        emulator does not appear to be installed (by display-name match).
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][object[]] $Systems,
        [string[]] $InstalledDisplayNames = @()
    )
    $records = New-Object System.Collections.Generic.List[object]
    foreach ($sys in $Systems) {
        if (-not (Test-Path -LiteralPath $sys.Gamelist)) { continue }
        $raw = Get-Content -LiteralPath $sys.Gamelist -Raw -Encoding UTF8 -ErrorAction SilentlyContinue
        if (-not $raw) { continue }
        $m = [Regex]::Match($raw, '<alternativeEmulator>\s*<label>([^<]+)</label>')
        if (-not $m.Success) { continue }
        $label = $m.Groups[1].Value.Trim()
        $core  = ($label -replace '\(.*\)', '').Trim()
        $installed = $false
        foreach ($dn in $InstalledDisplayNames) {
            if ($dn -and ($dn -match [Regex]::Escape($core) -or $core -match [Regex]::Escape(($dn -replace '\s*\(.*\)','')))) { $installed = $true; break }
        }
        $records.Add(@{ System = $sys.Name; Label = $label; Installed = $installed })
    }
    return $records.ToArray()
}

function Set-EsdeSettingValue {
    <#
    .SYNOPSIS
        Sets/creates a typed setting (<int>/<bool>/<string>) in es_settings.xml.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string] $SettingsFile,
        [Parameter(Mandatory = $true)][ValidateSet('int','bool','string')][string] $Type,
        [Parameter(Mandatory = $true)][string] $Name,
        [Parameter(Mandatory = $true)][string] $Value
    )
    if (-not (Test-Path -LiteralPath $SettingsFile)) {
        $dir = Split-Path $SettingsFile -Parent
        if ($dir -and -not (Test-Path -LiteralPath $dir)) { New-Item -Path $dir -ItemType Directory -Force | Out-Null }
        [System.IO.File]::WriteAllText($SettingsFile, "<?xml version=`"1.0`"?>`r`n<settings />", (New-Object System.Text.UTF8Encoding($false)))
    }
    [xml]$xml = Get-Content -LiteralPath $SettingsFile -Raw -Encoding UTF8
    if (-not $xml.DocumentElement) {
        $root = $xml.CreateElement('settings'); $xml.AppendChild($root) | Out-Null
    }
    $node = $xml.SelectSingleNode("//$Type[@name='$Name']")
    if (-not $node) {
        $node = $xml.CreateElement($Type)
        $node.SetAttribute('name', $Name)
        $xml.DocumentElement.AppendChild($node) | Out-Null
    }
    $node.SetAttribute('value', $Value)
    $xml.Save($SettingsFile)
}

function Optimize-EsdeSettings {
    <#
    .SYNOPSIS
        Applies a small set of safe ES-DE settings tuned to the hardware (after
        backup): VRAM cache cap and video audio. Never changes paths.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string] $SettingsFile,
        [Parameter(Mandatory = $true)][System.Collections.Specialized.OrderedDictionary] $Hardware,
        [Parameter(Mandatory = $true)][string] $BackupRoot,
        [Parameter(Mandatory = $true)][scriptblock] $Logger,
        [switch] $DryRun
    )
    if ($DryRun) { & $Logger "[DRY-RUN] Would tune es_settings.xml (MaxVRAM, VideoAudio)." 'INFO'; return $false }
    Backup-File -Path $SettingsFile -BackupRoot $BackupRoot | Out-Null
    # Cap the media VRAM cache sensibly: a quarter of GPU VRAM, clamped 256..1024 MB.
    $vram = 512
    if ($Hardware.Contains('GpuVramMB') -and $Hardware.GpuVramMB -gt 0) {
        $vram = [int]([math]::Min(1024, [math]::Max(256, [math]::Floor($Hardware.GpuVramMB / 4))))
    }
    Set-EsdeSettingValue -SettingsFile $SettingsFile -Type 'int'  -Name 'MaxVRAM'    -Value "$vram"
    Set-EsdeSettingValue -SettingsFile $SettingsFile -Type 'bool' -Name 'VideoAudio' -Value 'true'
    & $Logger "Tuned es_settings.xml: MaxVRAM=$vram MB, VideoAudio=true." 'SUCCESS'
    return $true
}

function Get-EsdeLanguage {
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][string] $SettingsFile)
    $lang = Get-EsdeSetting -SettingsFile $SettingsFile -Name 'ApplicationLanguage'
    if (-not $lang) { $lang = 'automatic' }
    return $lang
}

function Test-Online {
    [CmdletBinding()] param([int] $TimeoutMs = 2500)
    # NB: do not use $host (reserved automatic variable).
    foreach ($endpoint in @('api.screenscraper.fr','github.com','1.1.1.1')) {
        try {
            $c = New-Object System.Net.Sockets.TcpClient
            $iar = $c.BeginConnect($endpoint, 443, $null, $null)
            $ok = $iar.AsyncWaitHandle.WaitOne($TimeoutMs)
            if ($ok -and $c.Connected) { $c.EndConnect($iar); $c.Close(); return $true }
            $c.Close()
        } catch { }
    }
    return $false
}

function Get-EmptySystemsAdvisory {
    <#
    .SYNOPSIS
        Returns systems that have neither ROMs nor media (candidates for removal).
        Advisory only - nothing is deleted.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][object[]] $Systems)
    return @($Systems | Where-Object { -not $_.HasRoms -and -not $_.HasMedia } | ForEach-Object { $_.Name })
}

function Test-ControllerConfigApplied {
    <#
    .SYNOPSIS
        Verifies controller config artifacts were actually written (non-empty).
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][System.Collections.Specialized.OrderedDictionary] $Layout)
    $esInput = (Test-Path -LiteralPath $Layout.InputFile) -and ((Get-Item -LiteralPath $Layout.InputFile -ErrorAction SilentlyContinue).Length -gt 0)
    $db = Join-Path $Layout.DataDir 'gamecontrollerdb.txt'
    $sdlDb = (Test-Path -LiteralPath $db) -and ((Get-Item -LiteralPath $db -ErrorAction SilentlyContinue).Length -gt 0)
    return @{ EsInput = [bool]$esInput; GameControllerDb = [bool]$sdlDb }
}

function Export-RomHashManifest {
    <#
    .SYNOPSIS
        Writes a CRC32 manifest of ROMs (skipping files above MaxSizeMB) for future
        scraping / verification. Returns count hashed.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string] $SystemName,
        [Parameter(Mandatory = $true)][string] $SystemRomDir,
        [Parameter(Mandatory = $true)][string] $OutFile,
        [int] $MaxSizeMB = 256
    )
    if (-not (Test-Path -LiteralPath $SystemRomDir)) { return 0 }
    $limit = $MaxSizeMB * 1MB
    $entries = New-Object System.Collections.Generic.List[object]
    Get-ChildItem -LiteralPath $SystemRomDir -File -ErrorAction SilentlyContinue | ForEach-Object {
        if ($_.Extension.ToLower() -in @('.txt','.xml','.dat','.jpg','.png')) { return }
        if ($_.Length -gt $limit) { return }
        $crc = Get-FileCrc32 -Path $_.FullName
        if ($crc) { $entries.Add(@{ file = $_.Name; size = $_.Length; crc32 = $crc }) }
    }
    if ($entries.Count -gt 0) {
        $dir = Split-Path $OutFile -Parent
        if ($dir -and -not (Test-Path -LiteralPath $dir)) { New-Item -Path $dir -ItemType Directory -Force | Out-Null }
        @{ system = $SystemName; generated = (Get-Date -Format o); roms = $entries.ToArray() } | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $OutFile -Encoding UTF8
    }
    return $entries.Count
}

# ----- module: EsdeUx -----
<#
.SYNOPSIS
    Safe ES-DE user-experience settings tuning + run history.
.DESCRIPTION
    Writes a small set of safe, widely-liked es_settings.xml options (after backup)
    and configures the built-in scraper to ScreenScraper. Also maintains a run
    history JSON so successive runs can be compared over time.
#>

Set-StrictMode -Version Latest

function Optimize-EsdeUxSettings {
    <#
    .SYNOPSIS
        Applies safe ES-DE UX settings. Returns count of settings applied.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string] $SettingsFile,
        [Parameter(Mandatory = $true)][string] $BackupRoot,
        [Parameter(Mandatory = $true)][scriptblock] $Logger,
        [switch] $DryRun
    )
    if (-not (Test-Path -LiteralPath $SettingsFile)) { return 0 }
    if ($DryRun) { & $Logger "[DRY-RUN] Would apply ES-DE UX settings." 'INFO'; return 0 }
    Backup-File -Path $SettingsFile -BackupRoot $BackupRoot | Out-Null
    $bools = [ordered]@{
        'MediaViewerKeepVideoRunning' = 'true'
        'GamelistVideoPause'          = 'false'
        'FoldersOnTop'                = 'true'
        'ListScrollOverlay'           = 'true'
        'VideoAudio'                  = 'true'
    }
    $strings = [ordered]@{
        'Scraper'       = 'screenscraper'
        'ScraperRegion' = 'us'
    }
    $n = 0
    foreach ($k in $bools.Keys)   { Set-EsdeSettingValue -SettingsFile $SettingsFile -Type 'bool'   -Name $k -Value $bools[$k]; $n++ }
    foreach ($k in $strings.Keys) { Set-EsdeSettingValue -SettingsFile $SettingsFile -Type 'string' -Name $k -Value $strings[$k]; $n++ }
    & $Logger "Applied $n ES-DE UX setting(s) (media viewer, folders-on-top, scraper=screenscraper)." 'SUCCESS'
    return $n
}

function Update-RunHistory {
    <#
    .SYNOPSIS
        Appends a compact summary of this run to history.json (keeps last 50 runs).
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string] $WorkRoot,
        [Parameter(Mandatory = $true)][hashtable] $Summary
    )
    $path = Join-Path $WorkRoot 'history.json'
    $history = @()
    if (Test-Path -LiteralPath $path) {
        try { $history = @(Get-Content -LiteralPath $path -Raw -Encoding UTF8 | ConvertFrom-Json) } catch { $history = @() }
    }
    $history += [pscustomobject]$Summary
    if ($history.Count -gt 50) { $history = $history[($history.Count-50)..($history.Count-1)] }
    ($history | ConvertTo-Json -Depth 6) | Set-Content -LiteralPath $path -Encoding UTF8
    return $path
}

# ----- module: SystemOps -----
<#
.SYNOPSIS
    System operations: storage health, telemetry, scheduled task, desktop shortcut,
    log rotation, emulator config-drift detection and a suite update check.
#>

Set-StrictMode -Version Latest

function Get-StorageHealth {
    <#
    .SYNOPSIS
        Returns SMART/health status for physical disks (best-effort via CIM).
    #>
    [CmdletBinding()] param()
    $disks = New-Object System.Collections.Generic.List[object]
    try {
        if (Get-Command Get-PhysicalDisk -ErrorAction SilentlyContinue) {
            Get-PhysicalDisk -ErrorAction Stop | ForEach-Object {
                $disks.Add(@{ Name=$_.FriendlyName; Health=[string]$_.HealthStatus; Media=[string]$_.MediaType; SizeGB=[math]::Round($_.Size/1GB,0) })
            }
        } else {
            Get-CimInstance -ClassName Win32_DiskDrive -ErrorAction Stop | ForEach-Object {
                $disks.Add(@{ Name=$_.Model; Health=[string]$_.Status; Media='Unknown'; SizeGB=[math]::Round([int64]$_.Size/1GB,0) })
            }
        }
    } catch { }
    return $disks.ToArray()
}

function Get-SystemTelemetry {
    <#
    .SYNOPSIS
        Returns a snapshot of uptime, memory usage and OS info (best-effort).
    #>
    [CmdletBinding()] param()
    $t = @{ UptimeHours=0; MemoryUsedPct=0; OS='' }
    try {
        $os = Get-CimInstance -ClassName Win32_OperatingSystem -ErrorAction Stop
        if ($os) {
            $t.OS = $os.Caption
            $last = $os.LastBootUpTime
            if ($last) { $t.UptimeHours = [math]::Round(((Get-Date) - $last).TotalHours,1) }
            if ($os.TotalVisibleMemorySize -gt 0) {
                $used = $os.TotalVisibleMemorySize - $os.FreePhysicalMemory
                $t.MemoryUsedPct = [math]::Round(($used * 100.0) / $os.TotalVisibleMemorySize,1)
            }
        }
    } catch { }
    return $t
}

function Register-EsdeScheduledTask {
    <#
    .SYNOPSIS
        Creates/updates a weekly scheduled task to run the suite. Returns $true.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string] $LauncherPath,
        [Parameter(Mandatory = $true)][scriptblock] $Logger,
        [switch] $DryRun
    )
    if (-not (Test-Path -LiteralPath $LauncherPath)) { return $false }
    if ($DryRun) { & $Logger "[DRY-RUN] Would register weekly scheduled task." 'INFO'; return $false }
    try {
        $name = 'ES-DE Auto Suite Weekly'
        $cmd  = "schtasks /Create /F /SC WEEKLY /D SUN /TN `"$name`" /TR `"'$LauncherPath' /nogit`" /ST 03:00"
        $p = Start-Process -FilePath 'cmd.exe' -ArgumentList @('/c', $cmd) -NoNewWindow -Wait -PassThru
        if ($p.ExitCode -eq 0) { & $Logger "Registered weekly scheduled task '$name' (Sun 03:00)." 'SUCCESS'; return $true }
        & $Logger "Could not register scheduled task (exit $($p.ExitCode))." 'WARN'
    } catch { & $Logger "Scheduled task error: $($_.Exception.Message)" 'WARN' }
    return $false
}

function New-EsdeShortcut {
    <#
    .SYNOPSIS
        Creates a desktop shortcut to a target. Returns $true if created.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string] $Target,
        [Parameter(Mandatory = $true)][string] $ShortcutName,
        [Parameter(Mandatory = $true)][scriptblock] $Logger,
        [switch] $DryRun
    )
    if (-not (Test-Path -LiteralPath $Target)) { return $false }
    $desktop = [Environment]::GetFolderPath('Desktop')
    if (-not $desktop) { return $false }
    $lnk = Join-Path $desktop ($ShortcutName + '.lnk')
    if ($DryRun) { & $Logger "[DRY-RUN] Would create desktop shortcut $ShortcutName." 'INFO'; return $false }
    try {
        $sh = New-Object -ComObject WScript.Shell
        $sc = $sh.CreateShortcut($lnk)
        $sc.TargetPath = $Target
        $sc.WorkingDirectory = (Split-Path $Target -Parent)
        $sc.Save()
        & $Logger "Created desktop shortcut: $lnk" 'SUCCESS'
        return $true
    } catch { & $Logger "Shortcut error: $($_.Exception.Message)" 'WARN'; return $false }
}

function Invoke-LogRotation {
    <#
    .SYNOPSIS
        Compresses log files older than $Days into a dated zip and removes the
        originals. Returns count compressed.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string] $LogsDir,
        [int] $Days = 7,
        [switch] $DryRun
    )
    if (-not (Test-Path -LiteralPath $LogsDir)) { return 0 }
    $cutoff = (Get-Date).AddDays(-$Days)
    $old = @(Get-ChildItem -LiteralPath $LogsDir -File -Filter '*.log' -ErrorAction SilentlyContinue | Where-Object { $_.LastWriteTime -lt $cutoff })
    if ($old.Count -eq 0) { return 0 }
    if ($DryRun) { return $old.Count }
    $zip = Join-Path $LogsDir ("logs_archive_{0}.zip" -f (Get-Date -Format 'yyyyMMdd_HHmmss'))
    try {
        Add-Type -AssemblyName System.IO.Compression.FileSystem -ErrorAction SilentlyContinue
        $archive = [System.IO.Compression.ZipFile]::Open($zip, [System.IO.Compression.ZipArchiveMode]::Create)
        try {
            foreach ($f in $old) { [System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile($archive, $f.FullName, $f.Name) | Out-Null }
        } finally { $archive.Dispose() }
        foreach ($f in $old) { Remove-Item -LiteralPath $f.FullName -Force -ErrorAction SilentlyContinue }
        return $old.Count
    } catch { return 0 }
}

function Test-ConfigDrift {
    <#
    .SYNOPSIS
        Compares current emulator config files against the newest emulator_configs_*
        archive and returns the count of changed files.
    #>
    [CmdletBinding()]
    param(
        [string[]] $EmulatorRoots = @(),
        [Parameter(Mandatory = $true)][string]   $BackupRoot
    )
    if (-not $EmulatorRoots -or $EmulatorRoots.Count -eq 0) { return -1 }
    if (-not (Test-Path -LiteralPath $BackupRoot)) { return -1 }
    $latest = Get-ChildItem -LiteralPath $BackupRoot -Directory -Filter 'emulator_configs_*' -ErrorAction SilentlyContinue |
              Sort-Object Name -Descending | Select-Object -First 1
    if (-not $latest) { return -1 }   # no baseline yet
    $changed = 0
    foreach ($root in $EmulatorRoots) {
        if (-not (Test-Path -LiteralPath $root)) { continue }
        $leaf = Split-Path $root -Leaf
        $base = Join-Path $latest.FullName $leaf
        if (-not (Test-Path -LiteralPath $base)) { continue }
        Get-ChildItem -LiteralPath $root -Recurse -File -Include *.cfg,*.ini,*.xml,*.yml,*.toml,*.json -ErrorAction SilentlyContinue | ForEach-Object {
            $rel = $_.FullName.Substring($root.Length).TrimStart('\','/')
            $old = Join-Path $base $rel
            if (Test-Path -LiteralPath $old) {
                $h1 = (Get-FileSha256 -Path $_.FullName); $h2 = (Get-FileSha256 -Path $old)
                if ($h1 -and $h2 -and $h1 -ne $h2) { $changed++ }
            }
        }
    }
    return $changed
}

function Test-SuiteUpdate {
    <#
    .SYNOPSIS
        Best-effort check of a remote VERSION marker against the local suite version.
        Returns @{ Local; Remote; UpdateAvailable }.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][string] $LocalVersion)
    $result = @{ Local=$LocalVersion; Remote=''; UpdateAvailable=$false }
    try {
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        $url = 'https://raw.githubusercontent.com/Ayed1341/target/claude/retrobat-windows-automation-d2ilQ/esde/VERSION'
        $r = Invoke-WebRequest -Uri $url -TimeoutSec 8 -UseBasicParsing -ErrorAction Stop
        $remote = ($r.Content).Trim()
        if ($remote) {
            $result.Remote = $remote
            try { $result.UpdateAvailable = ([version]$remote -gt [version]$LocalVersion) } catch { $result.UpdateAvailable = ($remote -ne $LocalVersion) }
        }
    } catch { }
    return $result
}

# ----- module: PortabilityOps -----
<#
.SYNOPSIS
    Portability & ops: export controller config bundle, forecast media-download disk
    needs, detect network-share paths, and export a portable library bundle.
#>

Set-StrictMode -Version Latest

function Export-ControllerBundle {
    <#
    .SYNOPSIS
        Copies es_input.xml and every gamecontrollerdb.txt into one bundle folder so
        controller setup can be moved to another machine. Returns count.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][System.Collections.Specialized.OrderedDictionary] $Layout,
        [string[]] $EmulatorRoots = @(),
        [Parameter(Mandatory = $true)][string] $OutDir,
        [Parameter(Mandatory = $true)][scriptblock] $Logger,
        [switch] $DryRun
    )
    $count = 0
    $sources = New-Object System.Collections.Generic.List[string]
    $sources.Add($Layout.InputFile)
    $sources.Add((Join-Path $Layout.DataDir 'gamecontrollerdb.txt'))
    foreach ($r in $EmulatorRoots) { if ($r) { $sources.Add((Join-Path $r 'retroarch\gamecontrollerdb.txt')); $sources.Add((Join-Path $r 'retroarch\autoconfig')) } }
    if (-not $DryRun -and -not (Test-Path -LiteralPath $OutDir)) { New-Item -Path $OutDir -ItemType Directory -Force | Out-Null }
    foreach ($s in ($sources | Select-Object -Unique)) {
        if (-not $s -or -not (Test-Path -LiteralPath $s)) { continue }
        if ($DryRun) { $count++; continue }
        if (Test-Path -LiteralPath $s -PathType Container) {
            $dst = Join-Path $OutDir (Split-Path $s -Leaf)
            Copy-Item -LiteralPath $s -Destination $dst -Recurse -Force -ErrorAction SilentlyContinue
        } else {
            Copy-Item -LiteralPath $s -Destination (Join-Path $OutDir (Split-Path $s -Leaf)) -Force -ErrorAction SilentlyContinue
        }
        $count++
    }
    if ($count -gt 0 -and -not $DryRun) { & $Logger "Exported controller bundle ($count item(s)) to $OutDir." 'SUCCESS' }
    return $count
}

function Get-DiskSpaceForecast {
    <#
    .SYNOPSIS
        Estimates disk space needed to fill missing media, using average sizes of
        existing media of each type. Returns estimated MB.
    .PARAMETER MissingPerSystem
        From the report: array of @{ System; Totals=@{covers;videos;...} }.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string] $MediaDir,
        [Parameter(Mandatory = $true)][object[]] $MissingPerSystem
    )
    # Average size per media type from existing files.
    $avg = @{}
    if (Test-Path -LiteralPath $MediaDir) {
        Get-ChildItem -LiteralPath $MediaDir -Directory -ErrorAction SilentlyContinue | ForEach-Object {
            Get-ChildItem -LiteralPath $_.FullName -Directory -ErrorAction SilentlyContinue | ForEach-Object {
                $t = $_.Name.ToLower()
                $files = @(Get-ChildItem -LiteralPath $_.FullName -File -ErrorAction SilentlyContinue)
                if ($files.Count -eq 0) { return }
                $sum = 0; foreach ($f in $files) { $sum += $f.Length }
                if (-not $avg.ContainsKey($t)) { $avg[$t] = @{ Sum=0; N=0 } }
                $avg[$t].Sum += $sum; $avg[$t].N += $files.Count
            }
        }
    }
    $defaults = @{ covers=120KB; screenshots=80KB; videos=3MB; marquees=40KB; fanart=400KB; titlescreens=80KB; manuals=2MB }
    $totalBytes = [int64]0
    foreach ($ms in $MissingPerSystem) {
        foreach ($t in @('covers','screenshots','videos','marquees','fanart','titlescreens','manuals')) {
            $missing = 0; if ($ms.Totals -and $ms.Totals.$t) { $missing = [int]$ms.Totals.$t }
            if ($missing -le 0) { continue }
            $per = if ($avg.ContainsKey($t) -and $avg[$t].N -gt 0) { [int64]($avg[$t].Sum / $avg[$t].N) } else { [int64]$defaults[$t] }
            $totalBytes += ($per * $missing)
        }
    }
    return [math]::Round($totalBytes / 1MB, 1)
}

function Test-NetworkPaths {
    <#
    .SYNOPSIS
        Flags ROM/media directories that live on a network share (UNC or mapped),
        which can slow ES-DE. Returns the list of network paths found.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][string[]] $Paths)
    $net = New-Object System.Collections.Generic.List[string]
    foreach ($p in $Paths) {
        if (-not $p) { continue }
        if ($p.StartsWith('\\')) { $net.Add($p); continue }
        try {
            $root = [System.IO.Path]::GetPathRoot($p)
            if ($root -and (Test-Path -LiteralPath $root)) {
                $di = New-Object System.IO.DriveInfo($root)
                if ($di.DriveType -eq [System.IO.DriveType]::Network) { $net.Add($p) }
            }
        } catch { }
    }
    return $net.ToArray()
}

function Export-PortableBundle {
    <#
    .SYNOPSIS
        Writes a portable.json describing the install (data dir, rom dir, media dir,
        system list) so the configuration can be reproduced elsewhere. Returns path.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][System.Collections.Specialized.OrderedDictionary] $Layout,
        [Parameter(Mandatory = $true)][object[]] $Systems,
        [Parameter(Mandatory = $true)][string]   $OutFile
    )
    $data = @{
        generated = (Get-Date -Format o)
        dataDir   = $Layout.DataDir
        romDir    = $Layout.RomDir
        mediaDir  = $Layout.MediaDir
        esdeVersion = $Layout.Version
        systems   = @($Systems | ForEach-Object { @{ name=$_.Name; hasRoms=[bool]$_.HasRoms; hasGamelist=[bool]$_.HasGamelist; hasMedia=[bool]$_.HasMedia } })
    }
    $dir = Split-Path $OutFile -Parent
    if ($dir -and -not (Test-Path -LiteralPath $dir)) { New-Item -Path $dir -ItemType Directory -Force | Out-Null }
    ($data | ConvertTo-Json -Depth 6) | Set-Content -LiteralPath $OutFile -Encoding UTF8
    return $OutFile
}

# ----- module: GraphicsOptimization -----
<#
.SYNOPSIS
    4K graphics optimization module.
.DESCRIPTION
    Applies resolution / quality / backend settings to each detected emulator
    according to the selected performance tier (LowEnd / MidRange / HighEnd /
    FourK). Each emulator family has a dedicated writer that understands its own
    configuration format. Every file is backed up before modification and all
    writes are non-destructive (existing keys updated, others preserved).

    Tier semantics:
      LowEnd   -> native internal resolution, light filtering, VSync on.
      MidRange -> 2x internal resolution, 8x AF, shader cache.
      HighEnd  -> ~4x internal resolution, 16x AF, modern backend.
      FourK    -> maximum safe internal resolution targeting 3840x2160, 16x AF.
#>

Set-StrictMode -Version Latest

# Per-tier integer upscale factors keyed by a logical "native height" bucket.
# Values chosen to stay within safe VRAM/perf envelopes for each tier.
$script:TierScale = @{
    'LowEnd'   = 1
    'MidRange' = 2
    'HighEnd'  = 4
    'FourK'    = 6
}

function Get-TierScale {
    param([string] $Tier, [int] $Max = 8, [int] $Min = 1)
    $s = if ($script:TierScale.ContainsKey($Tier)) { $script:TierScale[$Tier] } else { 2 }
    if ($s -gt $Max) { $s = $Max }
    if ($s -lt $Min) { $s = $Min }
    return $s
}

function Invoke-EmulatorOptimization {
    <#
    .SYNOPSIS
        Dispatches a single emulator to its tier-aware optimization routine.
    .OUTPUTS
        Hashtable: Success, Message, Changed (array of file paths touched).
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)] [object] $Emulator,
        [Parameter(Mandatory = $true)] [string] $Tier,
        [Parameter(Mandatory = $true)] [int]    $TargetWidth,
        [Parameter(Mandatory = $true)] [int]    $TargetHeight,
        [Parameter(Mandatory = $true)] [string] $BackupRoot,
        [Parameter(Mandatory = $true)] [scriptblock] $Logger,
        [string] $GpuVendor = 'Unknown'
    )

    $log = { param($m, $l) & $Logger $m $l }

    if (-not $Emulator.Installed) {
        return @{ Success = $false; Message = 'Not installed; skipped.'; Changed = @() }
    }
    if (-not $Emulator.Supports4K -and $Emulator.Known) {
        & $log "$($Emulator.DisplayName) does not support resolution scaling; applying VSync/backend only where possible." 'INFO'
    }

    try {
        switch ($Emulator.Id) {
            'retroarch'  { return Optimize-RetroArch  @PSBoundParameters }
            'pcsx2'      { return Optimize-PCSX2       @PSBoundParameters }
            'rpcs3'      { return Optimize-RPCS3       @PSBoundParameters }
            'xenia'      { return Optimize-Xenia       @PSBoundParameters }
            'dolphin'    { return Optimize-Dolphin     @PSBoundParameters }
            'primehack'  { return Optimize-Dolphin     @PSBoundParameters }
            'cemu'       { return Optimize-Cemu        @PSBoundParameters }
            'yuzu'       { return Optimize-Yuzu        @PSBoundParameters }
            'ryujinx'    { return Optimize-Ryujinx     @PSBoundParameters }
            'ppsspp'     { return Optimize-PPSSPP      @PSBoundParameters }
            'duckstation'{ return Optimize-DuckStation @PSBoundParameters }
            'melonds'    { return Optimize-MelonDS     @PSBoundParameters }
            'flycast'    { return Optimize-Flycast     @PSBoundParameters }
            'citra'      { return Optimize-Citra       @PSBoundParameters }
            'redream'    { return Optimize-Redream     @PSBoundParameters }
            'mame'       { return Optimize-MAME        @PSBoundParameters }
            default      {
                & $log "No dedicated optimizer for '$($Emulator.Id)'; left untouched." 'INFO'
                return @{ Success = $true; Message = 'No optimizer (unknown emulator).'; Changed = @() }
            }
        }
    } catch {
        & $log "Optimization error for $($Emulator.DisplayName): $($_.Exception.Message)" 'ERROR'
        return @{ Success = $false; Message = $_.Exception.Message; Changed = @() }
    }
}

function Resolve-ConfigPath {
    <#
    .SYNOPSIS
        Returns the first existing configured config file path for an emulator,
        or the first candidate path (which may not yet exist) so it can be created.
    #>
    param([object] $Emulator)
    $first = $null
    foreach ($rel in $Emulator.ConfigFiles) {
        $full = Join-Path $Emulator.FolderPath $rel
        if (-not $first) { $first = $full }
        if (Test-Path -LiteralPath $full) { return $full }
    }
    return $first
}

# ----------------------------------------------------------------------------
# RetroArch (flat key = "value")
# ----------------------------------------------------------------------------
function Optimize-RetroArch {
    param($Emulator, $Tier, $TargetWidth, $TargetHeight, $BackupRoot, $Logger, $GpuVendor = 'Unknown')
    $cfg = Join-Path $Emulator.FolderPath 'retroarch.cfg'
    New-ConfigBackup -Path $cfg -BackupRoot $BackupRoot | Out-Null

    $smooth = if ($Tier -eq 'LowEnd') { 'false' } else { 'true' }
    # GPU-aware backend: Vulkan for NVIDIA/AMD; glcore for Intel iGPUs where
    # Vulkan drivers are historically less reliable in RetroArch.
    $raDriver = if ($GpuVendor -eq 'Intel') { 'glcore' } else { 'vulkan' }
    $map = [ordered]@{
        'video_fullscreen'         = 'true'
        'video_windowed_fullscreen'= 'true'
        'video_fullscreen_x'       = "$TargetWidth"
        'video_fullscreen_y'       = "$TargetHeight"
        'video_vsync'              = 'true'
        'video_hard_sync'          = 'false'
        'video_smooth'             = $smooth
        'video_threaded'           = 'true'
        'video_driver'             = $raDriver
        'video_shader_enable'      = 'true'
        'video_max_swapchain_images' = '3'
        'video_aspect_ratio_auto'  = 'true'
        'menu_driver'              = 'ozone'
    }
    foreach ($k in $map.Keys) { Set-FlatConfigValue -Path $cfg -Key $k -Value $map[$k] -Quote }
    & $Logger "RetroArch optimized for ${TargetWidth}x${TargetHeight} (tier $Tier)." 'SUCCESS'
    return @{ Success = $true; Message = 'RetroArch configured.'; Changed = @($cfg) }
}

# ----------------------------------------------------------------------------
# PCSX2 (INI)
# ----------------------------------------------------------------------------
function Optimize-PCSX2 {
    param($Emulator, $Tier, $TargetWidth, $TargetHeight, $BackupRoot, $Logger, $GpuVendor = 'Unknown')
    $cfg = Resolve-ConfigPath -Emulator $Emulator
    New-ConfigBackup -Path $cfg -BackupRoot $BackupRoot | Out-Null
    $ini = Read-IniFile -Path $cfg

    $scale = Get-TierScale -Tier $Tier -Max 8 -Min 1   # upscale_multiplier
    # PCSX2 Renderer: 14=Vulkan, 12=Direct3D11. Intel iGPUs run most reliably on
    # D3D11; discrete NVIDIA/AMD get Vulkan.
    $pcsxRenderer = if ($GpuVendor -eq 'Intel') { '12' } else { '14' }
    $pcsxBackend  = if ($GpuVendor -eq 'Intel') { 'Direct3D11' } else { 'Vulkan' }
    Set-IniValue -Data $ini -Section 'EmuCore/GS' -Key 'upscale_multiplier' -Value ("{0}" -f $scale)
    Set-IniValue -Data $ini -Section 'EmuCore/GS' -Key 'Renderer'            -Value $pcsxRenderer
    Set-IniValue -Data $ini -Section 'EmuCore/GS' -Key 'AnisotropicFiltering' -Value '16'
    Set-IniValue -Data $ini -Section 'EmuCore/GS' -Key 'TextureFiltering'    -Value '2'    # bilinear (forced)
    Set-IniValue -Data $ini -Section 'EmuCore/GS' -Key 'VsyncEnable'         -Value '1'
    Set-IniValue -Data $ini -Section 'EmuCore/GS' -Key 'mipmap_hw'           -Value '-1'
    Set-IniValue -Data $ini -Section 'EmuCore/GS' -Key 'OsdShowMessages'     -Value 'false'

    Write-IniFile -Path $cfg -Data $ini
    & $Logger "PCSX2 optimized: upscale ${scale}x, $pcsxBackend, 16x AF (tier $Tier)." 'SUCCESS'
    return @{ Success = $true; Message = 'PCSX2 configured.'; Changed = @($cfg) }
}

# ----------------------------------------------------------------------------
# RPCS3 (YAML scalars)
# ----------------------------------------------------------------------------
function Optimize-RPCS3 {
    param($Emulator, $Tier, $TargetWidth, $TargetHeight, $BackupRoot, $Logger, $GpuVendor = 'Unknown')
    $cfg = Resolve-ConfigPath -Emulator $Emulator
    New-ConfigBackup -Path $cfg -BackupRoot $BackupRoot | Out-Null

    $scalePct = switch ($Tier) { 'LowEnd' {100} 'MidRange' {150} 'HighEnd' {300} 'FourK' {400} default {150} }
    Set-YamlScalar -Path $cfg -Key 'Renderer' -Value 'Vulkan'
    Set-YamlScalar -Path $cfg -Key 'Resolution Scale (%)' -Value "$scalePct"
    Set-YamlScalar -Path $cfg -Key 'Anisotropic Filter Override' -Value '16'
    Set-YamlScalar -Path $cfg -Key 'VSync' -Value 'true'
    Set-YamlScalar -Path $cfg -Key 'Write Color Buffers' -Value 'true'
    & $Logger "RPCS3 optimized: Vulkan, resolution scale ${scalePct}% (tier $Tier)." 'SUCCESS'
    return @{ Success = $true; Message = 'RPCS3 configured.'; Changed = @($cfg) }
}

# ----------------------------------------------------------------------------
# Xenia (TOML scalars)
# ----------------------------------------------------------------------------
function Optimize-Xenia {
    param($Emulator, $Tier, $TargetWidth, $TargetHeight, $BackupRoot, $Logger, $GpuVendor = 'Unknown')
    $cfg = Resolve-ConfigPath -Emulator $Emulator
    New-ConfigBackup -Path $cfg -BackupRoot $BackupRoot | Out-Null

    $resScale = Get-TierScale -Tier $Tier -Max 3 -Min 1   # Xenia supports 1x/2x/3x draw scaling
    Set-TomlValue -Path $cfg -Key 'gpu' -Value '"vulkan"'
    Set-TomlValue -Path $cfg -Key 'draw_resolution_scale_x' -Value "$resScale"
    Set-TomlValue -Path $cfg -Key 'draw_resolution_scale_y' -Value "$resScale"
    Set-TomlValue -Path $cfg -Key 'vsync' -Value 'true'
    Set-TomlValue -Path $cfg -Key 'fullscreen' -Value 'true'
    & $Logger "Xenia optimized: Vulkan, draw scale ${resScale}x (tier $Tier)." 'SUCCESS'
    return @{ Success = $true; Message = 'Xenia configured.'; Changed = @($cfg) }
}

# ----------------------------------------------------------------------------
# Dolphin / PrimeHack (GFX.ini + Dolphin.ini)
# ----------------------------------------------------------------------------
function Optimize-Dolphin {
    param($Emulator, $Tier, $TargetWidth, $TargetHeight, $BackupRoot, $Logger, $GpuVendor = 'Unknown')
    $gfx     = Join-Path $Emulator.FolderPath 'User\Config\GFX.ini'
    $general = Join-Path $Emulator.FolderPath 'User\Config\Dolphin.ini'

    New-ConfigBackup -Path $gfx -BackupRoot $BackupRoot | Out-Null
    $g = Read-IniFile -Path $gfx
    # InternalResolution: 0=auto(window), otherwise integer multiplier of native.
    $ir = switch ($Tier) { 'LowEnd' {1} 'MidRange' {3} 'HighEnd' {5} 'FourK' {6} default {3} }
    Set-IniValue -Data $g -Section 'Settings' -Key 'InternalResolution' -Value "$ir"
    Set-IniValue -Data $g -Section 'Settings' -Key 'MaxAnisotropy' -Value '4'        # 4 -> 16x
    Set-IniValue -Data $g -Section 'Settings' -Key 'ShaderCompilationMode' -Value '0'
    Set-IniValue -Data $g -Section 'Settings' -Key 'WaitForShadersBeforeStarting' -Value 'True'
    Set-IniValue -Data $g -Section 'Hardware' -Key 'VSync' -Value 'True'
    Set-IniValue -Data $g -Section 'Enhancements' -Key 'ForceFiltering' -Value 'True'
    Set-IniValue -Data $g -Section 'Enhancements' -Key 'MaxAnisotropy' -Value '4'
    Write-IniFile -Path $gfx -Data $g

    New-ConfigBackup -Path $general -BackupRoot $BackupRoot | Out-Null
    $d = Read-IniFile -Path $general
    Set-IniValue -Data $d -Section 'Core' -Key 'GFXBackend' -Value 'Vulkan'
    Write-IniFile -Path $general -Data $d

    & $Logger "$($Emulator.DisplayName) optimized: internal res ${ir}x, Vulkan, 16x AF (tier $Tier)." 'SUCCESS'
    return @{ Success = $true; Message = 'Dolphin family configured.'; Changed = @($gfx, $general) }
}

# ----------------------------------------------------------------------------
# Cemu (settings.xml)
# ----------------------------------------------------------------------------
function Optimize-Cemu {
    param($Emulator, $Tier, $TargetWidth, $TargetHeight, $BackupRoot, $Logger, $GpuVendor = 'Unknown')
    $cfg = Resolve-ConfigPath -Emulator $Emulator
    New-ConfigBackup -Path $cfg -BackupRoot $BackupRoot | Out-Null

    # Cemu internal resolution is driven by graphic packs; here we set the global
    # rendering backend, VSync and async shader compile which are in settings.xml.
    if (-not (Test-Path -LiteralPath $cfg)) {
        $xml = @'
<?xml version="1.0" encoding="UTF-8"?>
<content>
    <GraphicAPI>1</GraphicAPI>
    <VSync>1</VSync>
    <AsyncCompile>true</AsyncCompile>
    <Fullscreen>true</Fullscreen>
</content>
'@
        $dir = Split-Path $cfg -Parent
        if ($dir -and -not (Test-Path $dir)) { New-Item -Path $dir -ItemType Directory -Force | Out-Null }
        [System.IO.File]::WriteAllText($cfg, $xml, (New-Object System.Text.UTF8Encoding($false)))
    } else {
        $content = Get-Content -LiteralPath $cfg -Raw -Encoding UTF8
        $content = Set-XmlElement -Content $content -Element 'GraphicAPI' -Value '1'   # 1 = Vulkan
        $content = Set-XmlElement -Content $content -Element 'VSync' -Value '1'
        $content = Set-XmlElement -Content $content -Element 'AsyncCompile' -Value 'true'
        $content = Set-XmlElement -Content $content -Element 'Fullscreen' -Value 'true'
        [System.IO.File]::WriteAllText($cfg, $content, (New-Object System.Text.UTF8Encoding($false)))
    }
    & $Logger "Cemu optimized: Vulkan backend, VSync, async shader compile (tier $Tier)." 'SUCCESS'
    return @{ Success = $true; Message = 'Cemu configured.'; Changed = @($cfg) }
}

function Set-XmlElement {
    <#
    .SYNOPSIS
        Replaces or inserts a simple <Element>value</Element> in an XML string.
    #>
    param([string] $Content, [string] $Element, [string] $Value)
    $pattern = "<$Element>.*?</$Element>"
    $replace = "<$Element>$Value</$Element>"
    if ($Content -match $pattern) {
        return [Regex]::Replace($Content, $pattern, $replace)
    }
    # Insert before closing root tag (assumes </content> style root).
    if ($Content -match '</[A-Za-z0-9_]+>\s*$') {
        return [Regex]::Replace($Content, '(</[A-Za-z0-9_]+>\s*)$', "    $replace`r`n`$1")
    }
    return $Content + "`r`n$replace"
}

# ----------------------------------------------------------------------------
# Yuzu / compatible (qt-config.ini)
# ----------------------------------------------------------------------------
function Optimize-Yuzu {
    param($Emulator, $Tier, $TargetWidth, $TargetHeight, $BackupRoot, $Logger, $GpuVendor = 'Unknown')
    $cfg = Resolve-ConfigPath -Emulator $Emulator
    New-ConfigBackup -Path $cfg -BackupRoot $BackupRoot | Out-Null
    $ini = Read-IniFile -Path $cfg

    # resolution_setup index: 2=1x,3=2x,4=3x,5=4x (matches emulator UI ordering).
    $resSetup = switch ($Tier) { 'LowEnd' {2} 'MidRange' {3} 'HighEnd' {5} 'FourK' {5} default {3} }
    Set-IniValue -Data $ini -Section 'Renderer' -Key 'backend' -Value '1'             # 1 = Vulkan
    Set-IniValue -Data $ini -Section 'Renderer' -Key 'backend\default' -Value 'false'
    Set-IniValue -Data $ini -Section 'Renderer' -Key 'resolution_setup' -Value "$resSetup"
    Set-IniValue -Data $ini -Section 'Renderer' -Key 'resolution_setup\default' -Value 'false'
    Set-IniValue -Data $ini -Section 'Renderer' -Key 'max_anisotropy' -Value '5'      # 5 -> 16x
    Set-IniValue -Data $ini -Section 'Renderer' -Key 'max_anisotropy\default' -Value 'false'
    Set-IniValue -Data $ini -Section 'Renderer' -Key 'use_vsync' -Value '1'
    Set-IniValue -Data $ini -Section 'Renderer' -Key 'use_asynchronous_shaders' -Value 'true'
    Write-IniFile -Path $cfg -Data $ini
    & $Logger "Yuzu-family optimized: Vulkan, resolution setup $resSetup, 16x AF (tier $Tier)." 'SUCCESS'
    return @{ Success = $true; Message = 'Yuzu configured.'; Changed = @($cfg) }
}

# ----------------------------------------------------------------------------
# Ryujinx (Config.json)
# ----------------------------------------------------------------------------
function Optimize-Ryujinx {
    param($Emulator, $Tier, $TargetWidth, $TargetHeight, $BackupRoot, $Logger, $GpuVendor = 'Unknown')
    $cfg = Resolve-ConfigPath -Emulator $Emulator
    if (-not (Test-Path -LiteralPath $cfg)) {
        & $Logger "Ryujinx Config.json not present yet; will be created on first launch. Skipping." 'WARN'
        return @{ Success = $false; Message = 'Config.json absent.'; Changed = @() }
    }
    New-ConfigBackup -Path $cfg -BackupRoot $BackupRoot | Out-Null

    $resScale = switch ($Tier) { 'LowEnd' {1} 'MidRange' {2} 'HighEnd' {3} 'FourK' {4} default {2} }
    $json = Get-Content -LiteralPath $cfg -Raw -Encoding UTF8 | ConvertFrom-Json
    $json | Add-Member -NotePropertyName 'res_scale' -NotePropertyValue $resScale -Force
    $json | Add-Member -NotePropertyName 'graphics_backend' -NotePropertyValue 'Vulkan' -Force
    $json | Add-Member -NotePropertyName 'enable_vsync' -NotePropertyValue $true -Force
    $json | Add-Member -NotePropertyName 'max_anisotropy' -NotePropertyValue 16 -Force
    ($json | ConvertTo-Json -Depth 50) | Set-Content -LiteralPath $cfg -Encoding UTF8
    & $Logger "Ryujinx optimized: Vulkan, res scale ${resScale}x, 16x AF (tier $Tier)." 'SUCCESS'
    return @{ Success = $true; Message = 'Ryujinx configured.'; Changed = @($cfg) }
}

# ----------------------------------------------------------------------------
# PPSSPP (ppsspp.ini)
# ----------------------------------------------------------------------------
function Optimize-PPSSPP {
    param($Emulator, $Tier, $TargetWidth, $TargetHeight, $BackupRoot, $Logger, $GpuVendor = 'Unknown')
    $cfg = Resolve-ConfigPath -Emulator $Emulator
    New-ConfigBackup -Path $cfg -BackupRoot $BackupRoot | Out-Null
    $ini = Read-IniFile -Path $cfg

    $ir = switch ($Tier) { 'LowEnd' {2} 'MidRange' {5} 'HighEnd' {8} 'FourK' {10} default {5} }
    Set-IniValue -Data $ini -Section 'Graphics' -Key 'InternalResolution' -Value "$ir"
    Set-IniValue -Data $ini -Section 'Graphics' -Key 'AndroidHwScale' -Value '0'
    Set-IniValue -Data $ini -Section 'Graphics' -Key 'TextureFiltering' -Value '3'     # linear
    Set-IniValue -Data $ini -Section 'Graphics' -Key 'AnisotropyLevel' -Value '4'      # 16x
    Set-IniValue -Data $ini -Section 'Graphics' -Key 'VSync' -Value 'True'
    Set-IniValue -Data $ini -Section 'Graphics' -Key 'GraphicsBackend' -Value '3'      # Vulkan
    Set-IniValue -Data $ini -Section 'Graphics' -Key 'FullScreen' -Value 'True'
    Write-IniFile -Path $cfg -Data $ini
    & $Logger "PPSSPP optimized: internal res ${ir}x, Vulkan, 16x AF (tier $Tier)." 'SUCCESS'
    return @{ Success = $true; Message = 'PPSSPP configured.'; Changed = @($cfg) }
}

# ----------------------------------------------------------------------------
# DuckStation (settings.ini)
# ----------------------------------------------------------------------------
function Optimize-DuckStation {
    param($Emulator, $Tier, $TargetWidth, $TargetHeight, $BackupRoot, $Logger, $GpuVendor = 'Unknown')
    $cfg = Resolve-ConfigPath -Emulator $Emulator
    New-ConfigBackup -Path $cfg -BackupRoot $BackupRoot | Out-Null
    $ini = Read-IniFile -Path $cfg

    $scale = switch ($Tier) { 'LowEnd' {2} 'MidRange' {4} 'HighEnd' {8} 'FourK' {9} default {4} }
    $dsRenderer = if ($GpuVendor -eq 'Intel') { 'D3D11' } else { 'Vulkan' }
    Set-IniValue -Data $ini -Section 'GPU' -Key 'Renderer' -Value $dsRenderer
    Set-IniValue -Data $ini -Section 'GPU' -Key 'ResolutionScale' -Value "$scale"
    Set-IniValue -Data $ini -Section 'GPU' -Key 'TextureFilter' -Value 'Bilinear'
    Set-IniValue -Data $ini -Section 'GPU' -Key 'PGXPEnable' -Value 'true'
    Set-IniValue -Data $ini -Section 'GPU' -Key 'PGXPCulling' -Value 'true'
    Set-IniValue -Data $ini -Section 'Display' -Key 'VSync' -Value 'true'
    Set-IniValue -Data $ini -Section 'Display' -Key 'Fullscreen' -Value 'true'
    Write-IniFile -Path $cfg -Data $ini
    & $Logger "DuckStation optimized: $dsRenderer, resolution scale ${scale}x, PGXP on (tier $Tier)." 'SUCCESS'
    return @{ Success = $true; Message = 'DuckStation configured.'; Changed = @($cfg) }
}

# ----------------------------------------------------------------------------
# melonDS (melonDS.ini)
# ----------------------------------------------------------------------------
function Optimize-MelonDS {
    param($Emulator, $Tier, $TargetWidth, $TargetHeight, $BackupRoot, $Logger, $GpuVendor = 'Unknown')
    $cfg = Resolve-ConfigPath -Emulator $Emulator
    New-ConfigBackup -Path $cfg -BackupRoot $BackupRoot | Out-Null
    $ini = Read-IniFile -Path $cfg

    $scale = switch ($Tier) { 'LowEnd' {1} 'MidRange' {4} 'HighEnd' {6} 'FourK' {8} default {4} }
    # melonDS stores most keys in the global (section-less) area.
    Set-IniValue -Data $ini -Section '' -Key '3DRenderer' -Value '1'        # 1 = OpenGL
    Set-IniValue -Data $ini -Section '' -Key 'GL_ScaleFactor' -Value "$scale"
    Set-IniValue -Data $ini -Section '' -Key 'GL_BetterPolygons' -Value '1'
    Set-IniValue -Data $ini -Section '' -Key 'ScreenVSync' -Value '1'
    Write-IniFile -Path $cfg -Data $ini
    & $Logger "melonDS optimized: OpenGL renderer, scale ${scale}x (tier $Tier)." 'SUCCESS'
    return @{ Success = $true; Message = 'melonDS configured.'; Changed = @($cfg) }
}

# ----------------------------------------------------------------------------
# Flycast (emu.cfg)
# ----------------------------------------------------------------------------
function Optimize-Flycast {
    param($Emulator, $Tier, $TargetWidth, $TargetHeight, $BackupRoot, $Logger, $GpuVendor = 'Unknown')
    $cfg = Resolve-ConfigPath -Emulator $Emulator
    New-ConfigBackup -Path $cfg -BackupRoot $BackupRoot | Out-Null
    $ini = Read-IniFile -Path $cfg

    $res = switch ($Tier) { 'LowEnd' {480} 'MidRange' {1080} 'HighEnd' {1440} 'FourK' {2160} default {1080} }
    Set-IniValue -Data $ini -Section 'config' -Key 'rend.Resolution' -Value "$res"
    Set-IniValue -Data $ini -Section 'config' -Key 'rend.vsync' -Value 'yes'
    Set-IniValue -Data $ini -Section 'config' -Key 'rend.AnisotropicFiltering' -Value '16'
    Set-IniValue -Data $ini -Section 'config' -Key 'rend.WideScreen' -Value 'yes'
    Set-IniValue -Data $ini -Section 'config' -Key 'pvr.rend' -Value '4'    # 4 = Vulkan
    Write-IniFile -Path $cfg -Data $ini
    & $Logger "Flycast optimized: internal height ${res}p, Vulkan, 16x AF (tier $Tier)." 'SUCCESS'
    return @{ Success = $true; Message = 'Flycast configured.'; Changed = @($cfg) }
}

# ----------------------------------------------------------------------------
# Citra / compatible (qt-config.ini)
# ----------------------------------------------------------------------------
function Optimize-Citra {
    param($Emulator, $Tier, $TargetWidth, $TargetHeight, $BackupRoot, $Logger, $GpuVendor = 'Unknown')
    $cfg = Resolve-ConfigPath -Emulator $Emulator
    New-ConfigBackup -Path $cfg -BackupRoot $BackupRoot | Out-Null
    $ini = Read-IniFile -Path $cfg

    $factor = switch ($Tier) { 'LowEnd' {1} 'MidRange' {2} 'HighEnd' {4} 'FourK' {6} default {2} }
    Set-IniValue -Data $ini -Section 'Renderer' -Key 'resolution_factor' -Value "$factor"
    Set-IniValue -Data $ini -Section 'Renderer' -Key 'resolution_factor\default' -Value 'false'
    Set-IniValue -Data $ini -Section 'Renderer' -Key 'use_vsync_new' -Value 'true'
    Set-IniValue -Data $ini -Section 'Renderer' -Key 'use_vsync_new\default' -Value 'false'
    Set-IniValue -Data $ini -Section 'Renderer' -Key 'graphics_api' -Value '1'   # 1 = OpenGL
    Set-IniValue -Data $ini -Section 'Renderer' -Key 'filter_mode' -Value 'true'
    Write-IniFile -Path $cfg -Data $ini
    & $Logger "Citra-family optimized: resolution factor ${factor}x (tier $Tier)." 'SUCCESS'
    return @{ Success = $true; Message = 'Citra configured.'; Changed = @($cfg) }
}

# ----------------------------------------------------------------------------
# Redream (redream.cfg)
# ----------------------------------------------------------------------------
function Optimize-Redream {
    param($Emulator, $Tier, $TargetWidth, $TargetHeight, $BackupRoot, $Logger, $GpuVendor = 'Unknown')
    $cfg = Resolve-ConfigPath -Emulator $Emulator
    New-ConfigBackup -Path $cfg -BackupRoot $BackupRoot | Out-Null

    # Redream uses flat key=value; res is 1=native,2=2x,3=4x,4=8x equivalents.
    $res = switch ($Tier) { 'LowEnd' {1} 'MidRange' {2} 'HighEnd' {3} 'FourK' {4} default {2} }
    Set-FlatConfigValue -Path $cfg -Key 'res' -Value "$res" -Separator '='
    Set-FlatConfigValue -Path $cfg -Key 'vsync' -Value '1' -Separator '='
    Set-FlatConfigValue -Path $cfg -Key 'aspect' -Value '16:9' -Separator '='
    Set-FlatConfigValue -Path $cfg -Key 'fullmode' -Value 'exclusive fullscreen' -Separator '='
    & $Logger "Redream optimized: internal res level ${res} (tier $Tier)." 'SUCCESS'
    return @{ Success = $true; Message = 'Redream configured.'; Changed = @($cfg) }
}

# ----------------------------------------------------------------------------
# MAME (mame.ini) - arcade hardware is fixed-res; tune presentation/VSync only.
# ----------------------------------------------------------------------------
function Optimize-MAME {
    param($Emulator, $Tier, $TargetWidth, $TargetHeight, $BackupRoot, $Logger, $GpuVendor = 'Unknown')
    $cfg = Resolve-ConfigPath -Emulator $Emulator
    if (-not (Test-Path -LiteralPath $cfg)) {
        & $Logger "mame.ini not present; MAME generates it via 'mame -createconfig'. Skipping." 'WARN'
        return @{ Success = $false; Message = 'mame.ini absent.'; Changed = @() }
    }
    New-ConfigBackup -Path $cfg -BackupRoot $BackupRoot | Out-Null
    # MAME ini is whitespace-delimited "key value".
    Set-FlatConfigValue -Path $cfg -Key 'video' -Value 'bgfx' -Separator '                  '
    Set-FlatConfigValue -Path $cfg -Key 'waitvsync' -Value '1' -Separator '             '
    Set-FlatConfigValue -Path $cfg -Key 'filter' -Value '1' -Separator '                 '
    Set-FlatConfigValue -Path $cfg -Key 'prescale' -Value '0' -Separator '               '
    & $Logger "MAME optimized: BGFX renderer, VSync, bilinear filter (tier $Tier)." 'SUCCESS'
    return @{ Success = $true; Message = 'MAME configured.'; Changed = @($cfg) }
}

# ----- module: ControllerManagement -----
<#
.SYNOPSIS
    Controller detection and auto-configuration module.
.DESCRIPTION
    Enumerates connected game controllers via PnP/HID, identifies vendor and
    product IDs, classifies the controller family (Xbox / PlayStation / Nintendo /
    generic XInput / DirectInput), and writes mappings for EmulationStation
    (es_input.cfg) and RetroArch (autoconfig profile) including standard hotkeys.
    Provides a hotswap watcher that reconfigures on connect and cleanly updates
    on disconnect.
#>

Set-StrictMode -Version Latest

function Get-ConnectedControllers {
    <#
    .SYNOPSIS
        Returns descriptor objects for connected game controllers.
    .DESCRIPTION
        Queries Win32_PnPEntity for present HID / XInput / game controller devices,
        extracts VID/PID and classifies each device.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)] [hashtable] $VendorMap
    )

    $controllers = New-Object System.Collections.Generic.List[object]
    $seen        = New-Object System.Collections.Generic.HashSet[string] ([StringComparer]::OrdinalIgnoreCase)

    try {
        $devices = Get-CimInstance -ClassName Win32_PnPEntity -ErrorAction Stop | Where-Object {
            $_.Present -ne $false -and (
                ($_.PNPClass -in @('HIDClass', 'XnaComposite', 'XboxComposite')) -or
                ($_.Name -match '(?i)controller|gamepad|joystick|xbox|wireless controller|dualshock|dualsense|pro controller')
            ) -and ($_.PNPDeviceID -match '(?i)VID_[0-9A-F]{4}')
        }
    } catch {
        $devices = @()
    }

    foreach ($d in $devices) {
        $id  = $d.PNPDeviceID
        # NOTE: do not use $pid here - it is a read-only PowerShell automatic
        # variable (the current process id) and assigning to it throws.
        $vendorId = $null; $productId = $null
        if ($id -match '(?i)VID_([0-9A-F]{4})') { $vendorId = $Matches[1].ToUpper() }
        if ($id -match '(?i)PID_([0-9A-F]{4})') { $productId = $Matches[1].ToUpper() }
        if (-not $vendorId) { continue }

        # Deduplicate on VID+PID (composite devices expose multiple PnP nodes).
        $key = "${vendorId}:${productId}"
        if ($seen.Contains($key)) { continue }
        [void]$seen.Add($key)

        $vendor = if ($vendorId -and $VendorMap.ContainsKey($vendorId)) { $VendorMap[$vendorId] } else { 'Unknown vendor' }
        $family = Get-ControllerFamily -Vid $vendorId -Name $d.Name -PnpId $id
        $conn   = Get-ControllerConnection -PnpId $id
        $friendly = Get-ControllerFriendlyName -Name $d.Name -Family $family -Vendor $vendor

        $controllers.Add([pscustomobject]@{
            Name       = $d.Name
            FriendlyName = $friendly
            Vid        = $vendorId
            Pid        = $productId
            Vendor     = $vendor
            Family     = $family
            ApiType    = (Get-ControllerApiType -PnpId $id -Family $family)
            Connection = $conn
            PnpId      = $id
        })
    }

    return $controllers.ToArray()
}

function Get-ControllerFamily {
    param([string] $Vid, [string] $Name, [string] $PnpId)
    $n = ($Name + ' ' + $PnpId).ToLower()
    switch ($Vid) {
        '045E' { return 'Xbox' }
        '054C' { return 'PlayStation' }
        '057E' { return 'Nintendo' }
        '28DE' { return 'Steam' }
        '2DC8' { if ($n -match 'xbox|xinput') { return 'Xbox' } else { return '8BitDo' } }
    }
    if ($n -match 'xbox|xinput')                 { return 'Xbox' }
    if ($n -match 'dualshock|dualsense|playstation') { return 'PlayStation' }
    if ($n -match 'switch|pro controller|joy-con') { return 'Nintendo' }
    return 'Generic'
}

function Get-ControllerApiType {
    param([string] $PnpId, [string] $Family)
    if ($PnpId -match '(?i)IG_') { return 'XInput' }     # IG_ marks XInput devices
    if ($Family -eq 'Xbox')      { return 'XInput' }
    return 'DirectInput'
}

function Get-ControllerConnection {
    <#
    .SYNOPSIS
        Determines whether a controller is connected over Bluetooth or USB based
        on its PnP device id enumerator prefix.
    #>
    param([string] $PnpId)
    if ($PnpId -match '(?i)^BTHLE')    { return 'Bluetooth LE' }
    if ($PnpId -match '(?i)^BTHENUM')  { return 'Bluetooth' }
    if ($PnpId -match '(?i)^BTH')      { return 'Bluetooth' }
    if ($PnpId -match '(?i)^USB')      { return 'USB' }
    if ($PnpId -match '(?i)^HID')      { return 'HID (USB)' }
    return 'Unknown'
}

function Get-ControllerFriendlyName {
    <#
    .SYNOPSIS
        Builds a readable controller label from family + vendor when the raw HID
        name is generic (e.g. "USB Input Device").
    #>
    param([string] $Name, [string] $Family, [string] $Vendor)
    if ($Name -match '(?i)^(usb input device|hid-compliant.*|hid game.*|usb gamepad)$' -or [string]::IsNullOrWhiteSpace($Name)) {
        $label = switch ($Family) {
            'Xbox'        { 'Xbox-compatible controller' }
            'PlayStation' { 'PlayStation-compatible controller' }
            'Nintendo'    { 'Nintendo-compatible controller' }
            '8BitDo'      { '8BitDo controller' }
            default       { 'Generic controller' }
        }
        if ($Vendor -and $Vendor -ne 'Unknown vendor') { $label = "$label ($Vendor)" }
        return $label
    }
    return $Name
}

function Get-ControllerInputProfile {
    <#
    .SYNOPSIS
        Returns the standard SDL/RetroArch button index map for a controller family.
        Indices follow the SDL GameController convention used by RetroArch & ES.
    #>
    param([string] $Family)

    # Base XInput / SDL standard layout.
    $base = [ordered]@{
        a = 0; b = 1; x = 2; y = 3
        leftshoulder = 4; rightshoulder = 5
        back = 6; start = 7
        leftstick = 8; rightstick = 9
        dpup = 11; dpdown = 12; dpleft = 13; dpright = 14
        guide = 10
    }

    switch ($Family) {
        'Nintendo' {
            # Nintendo physical A/B and X/Y are swapped relative to XInput layout.
            $base.a = 1; $base.b = 0; $base.x = 3; $base.y = 2
        }
        default { }
    }
    return $base
}

function Write-RetroArchControllerProfile {
    <#
    .SYNOPSIS
        Writes a RetroArch autoconfig .cfg for a controller, including hotkeys.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)] [object] $Controller,
        [Parameter(Mandatory = $true)] [string] $AutoconfigDir,
        [Parameter(Mandatory = $true)] [scriptblock] $Logger
    )

    if (-not (Test-Path -LiteralPath $AutoconfigDir)) {
        New-Item -Path $AutoconfigDir -ItemType Directory -Force | Out-Null
    }

    $profile  = Get-ControllerInputProfile -Family $Controller.Family
    $driver   = if ($Controller.ApiType -eq 'XInput') { 'xinput' } else { 'dinput' }
    $safeName = ($Controller.Name -replace '[\\/:*?"<>|]', '_').Trim()
    # Unique filename per device (VID/PID) so multiple generic "USB Input Device"
    # pads do not overwrite each other's profile.
    $pidPart  = if ($Controller.Pid) { $Controller.Pid } else { '0000' }
    $file     = Join-Path $AutoconfigDir ("{0}_{1}_{2}.cfg" -f $safeName, $Controller.Vid, $pidPart)

    $lines = @()
    $lines += 'input_driver = "' + $driver + '"'
    $lines += 'input_device = "' + $Controller.Name + '"'
    $lines += 'input_vendor_id = "' + [Convert]::ToInt32($Controller.Vid, 16) + '"'
    if ($Controller.Pid) {
        $lines += 'input_product_id = "' + [Convert]::ToInt32($Controller.Pid, 16) + '"'
    }
    # Face buttons / shoulders / sticks.
    $lines += 'input_a_btn = "' + $profile.a + '"'
    $lines += 'input_b_btn = "' + $profile.b + '"'
    $lines += 'input_x_btn = "' + $profile.x + '"'
    $lines += 'input_y_btn = "' + $profile.y + '"'
    $lines += 'input_l_btn = "' + $profile.leftshoulder + '"'
    $lines += 'input_r_btn = "' + $profile.rightshoulder + '"'
    $lines += 'input_select_btn = "' + $profile.back + '"'
    $lines += 'input_start_btn = "' + $profile.start + '"'
    $lines += 'input_l3_btn = "' + $profile.leftstick + '"'
    $lines += 'input_r3_btn = "' + $profile.rightstick + '"'
    $lines += 'input_up_btn = "' + $profile.dpup + '"'
    $lines += 'input_down_btn = "' + $profile.dpdown + '"'
    $lines += 'input_left_btn = "' + $profile.dpleft + '"'
    $lines += 'input_right_btn = "' + $profile.dpright + '"'
    # Analog axes (standard XInput/SDL axis ordering).
    $lines += 'input_l_x_plus_axis = "+0"'
    $lines += 'input_l_x_minus_axis = "-0"'
    $lines += 'input_l_y_plus_axis = "+1"'
    $lines += 'input_l_y_minus_axis = "-1"'
    $lines += 'input_r_x_plus_axis = "+2"'
    $lines += 'input_r_x_minus_axis = "-2"'
    $lines += 'input_r_y_plus_axis = "+3"'
    $lines += 'input_r_y_minus_axis = "-3"'
    $lines += 'input_l2_axis = "+4"'
    $lines += 'input_r2_axis = "+5"'
    # Hotkeys: hold Select(=back) as enable, then face/shoulder combos.
    $lines += 'input_enable_hotkey_btn = "' + $profile.back + '"'
    $lines += 'input_exit_emulator_btn = "' + $profile.start + '"'
    $lines += 'input_menu_toggle_btn = "' + $profile.guide + '"'
    $lines += 'input_save_state_btn = "' + $profile.a + '"'
    $lines += 'input_load_state_btn = "' + $profile.y + '"'
    $lines += 'input_state_slot_increase_btn = "' + $profile.dpright + '"'
    $lines += 'input_state_slot_decrease_btn = "' + $profile.dpleft + '"'
    $lines += 'input_screenshot_btn = "' + $profile.x + '"'
    $lines += 'input_toggle_fast_forward_btn = "' + $profile.rightshoulder + '"'

    [System.IO.File]::WriteAllLines($file, $lines, (New-Object System.Text.UTF8Encoding($false)))
    & $Logger "RetroArch profile written: $file ($($Controller.Family)/$driver)." 'SUCCESS'
    return $file
}

function Write-EmulationStationInput {
    <#
    .SYNOPSIS
        Writes / merges an es_input.cfg inputConfig block for a controller so
        EmulationStation recognizes the pad. Existing blocks for other devices
        are preserved; a matching block (by deviceGUID) is replaced.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)] [object[]] $Controllers,
        [Parameter(Mandatory = $true)] [string]   $EsInputPath,
        [Parameter(Mandatory = $true)] [string]   $BackupRoot,
        [Parameter(Mandatory = $true)] [scriptblock] $Logger
    )

    New-ConfigBackup -Path $EsInputPath -BackupRoot $BackupRoot | Out-Null

    $dir = Split-Path $EsInputPath -Parent
    if ($dir -and -not (Test-Path -LiteralPath $dir)) {
        New-Item -Path $dir -ItemType Directory -Force | Out-Null
    }

    $sb = New-Object System.Text.StringBuilder
    [void]$sb.AppendLine('<?xml version="1.0"?>')
    [void]$sb.AppendLine('<inputList>')

    foreach ($c in $Controllers) {
        $profile = Get-ControllerInputProfile -Family $c.Family
        $guid    = New-DeterministicGuid -Seed ("$($c.Vid):$($c.Pid):$($c.Family)")
        $devName = [Security.SecurityElement]::Escape($c.Name)

        [void]$sb.AppendLine(('  <inputConfig type="joystick" deviceName="{0}" deviceGUID="{1}">' -f $devName, $guid))
        [void]$sb.AppendLine(('    <input name="a" type="button" id="{0}" value="1" />' -f $profile.a))
        [void]$sb.AppendLine(('    <input name="b" type="button" id="{0}" value="1" />' -f $profile.b))
        [void]$sb.AppendLine(('    <input name="x" type="button" id="{0}" value="1" />' -f $profile.x))
        [void]$sb.AppendLine(('    <input name="y" type="button" id="{0}" value="1" />' -f $profile.y))
        [void]$sb.AppendLine(('    <input name="pageup" type="button" id="{0}" value="1" />' -f $profile.leftshoulder))
        [void]$sb.AppendLine(('    <input name="pagedown" type="button" id="{0}" value="1" />' -f $profile.rightshoulder))
        [void]$sb.AppendLine(('    <input name="select" type="button" id="{0}" value="1" />' -f $profile.back))
        [void]$sb.AppendLine(('    <input name="start" type="button" id="{0}" value="1" />' -f $profile.start))
        [void]$sb.AppendLine(('    <input name="leftthumb" type="button" id="{0}" value="1" />' -f $profile.leftstick))
        [void]$sb.AppendLine(('    <input name="rightthumb" type="button" id="{0}" value="1" />' -f $profile.rightstick))
        [void]$sb.AppendLine(('    <input name="hotkeyenable" type="button" id="{0}" value="1" />' -f $profile.back))
        [void]$sb.AppendLine( '    <input name="up" type="axis" id="1" value="-1" />')
        [void]$sb.AppendLine( '    <input name="down" type="axis" id="1" value="1" />')
        [void]$sb.AppendLine( '    <input name="left" type="axis" id="0" value="-1" />')
        [void]$sb.AppendLine( '    <input name="right" type="axis" id="0" value="1" />')
        [void]$sb.AppendLine( '    <input name="joystick1up" type="axis" id="1" value="-1" />')
        [void]$sb.AppendLine( '    <input name="joystick1left" type="axis" id="0" value="-1" />')
        [void]$sb.AppendLine( '    <input name="joystick2up" type="axis" id="3" value="-1" />')
        [void]$sb.AppendLine( '    <input name="joystick2left" type="axis" id="2" value="-1" />')
        [void]$sb.AppendLine( '    <input name="lefttrigger" type="axis" id="4" value="1" />')
        [void]$sb.AppendLine( '    <input name="righttrigger" type="axis" id="5" value="1" />')
        [void]$sb.AppendLine( '  </inputConfig>')
    }

    [void]$sb.AppendLine('</inputList>')
    [System.IO.File]::WriteAllText($EsInputPath, $sb.ToString(), (New-Object System.Text.UTF8Encoding($false)))
    & $Logger "EmulationStation input written for $($Controllers.Count) controller(s): $EsInputPath" 'SUCCESS'
    return $EsInputPath
}

function New-DeterministicGuid {
    <#
    .SYNOPSIS
        Produces a stable GUID from a seed string (MD5-based) so the same
        controller always maps to the same deviceGUID across runs.
    #>
    param([string] $Seed)
    $md5   = [System.Security.Cryptography.MD5]::Create()
    $bytes = $md5.ComputeHash([System.Text.Encoding]::UTF8.GetBytes($Seed))
    $guid  = [Guid]::new($bytes)
    return $guid.ToString('N')
}

function Get-ControllerSignature {
    <#
    .SYNOPSIS
        Returns a stable signature string for the current set of controllers,
        used by the hotswap watcher to detect connect/disconnect transitions.
    #>
    param([object[]] $Controllers)
    if (-not $Controllers -or $Controllers.Count -eq 0) { return '' }
    return (($Controllers | ForEach-Object { "$($_.Vid):$($_.Pid)" } | Sort-Object) -join '|')
}

function Get-SdlGuid {
    <#
    .SYNOPSIS
        Builds an SDL2 controller GUID (Windows layout) from VID/PID and bus type.
        Layout (16 bytes, little-endian fields): bus, crc(0), vendor, 0, product, 0,
        version(0), 0 - matching the format used by SDL_GameControllerDB.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string] $Vid,
        [string] $ProductId = '0000',
        [string] $Connection = 'USB'
    )
    function leHex([string]$h) {
        $h = ($h.PadLeft(4,'0')).Substring(0,4)
        return ($h.Substring(2,2) + $h.Substring(0,2)).ToLower()
    }
    $bus = if ($Connection -match '(?i)bluetooth') { '0500' } else { '0300' }
    $v = leHex $Vid
    $p = if ($ProductId) { leHex $ProductId } else { '0000' }
    return ($bus + '0000' + $v + '0000' + $p + '0000' + '00000000').ToLower()
}

function New-SdlMappingLine {
    <#
    .SYNOPSIS
        Produces an SDL_GameControllerDB mapping line for a controller using its
        family's standard button layout. Universal across SDL-based emulators
        (RetroArch, DuckStation, PCSX2, PPSSPP, Flycast, ...).
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][object] $Controller)
    $p    = Get-ControllerInputProfile -Family $Controller.Family
    $guid = Get-SdlGuid -Vid $Controller.Vid -ProductId $Controller.Pid -Connection $Controller.Connection
    $name = ($Controller.FriendlyName -replace ',', ' ')
    $map  = @(
        "a:b$($p.a)","b:b$($p.b)","x:b$($p.x)","y:b$($p.y)",
        "back:b$($p.back)","start:b$($p.start)","guide:b$($p.guide)",
        "leftshoulder:b$($p.leftshoulder)","rightshoulder:b$($p.rightshoulder)",
        "leftstick:b$($p.leftstick)","rightstick:b$($p.rightstick)",
        "dpup:b$($p.dpup)","dpdown:b$($p.dpdown)","dpleft:b$($p.dpleft)","dpright:b$($p.dpright)",
        "leftx:a0","lefty:a1","rightx:a2","righty:a3","lefttrigger:a4","righttrigger:a5",
        "platform:Windows"
    )
    return ('{0},{1},{2},' -f $guid, $name, ($map -join ','))
}

function Write-GameControllerDb {
    <#
    .SYNOPSIS
        Writes/updates an SDL gamecontrollerdb.txt with one mapping per controller,
        replacing any existing line for the same GUID and preserving the rest.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][object[]] $Controllers,
        [Parameter(Mandatory = $true)][string]   $Path,
        [Parameter(Mandatory = $true)][scriptblock] $Logger
    )
    $dir = Split-Path $Path -Parent
    if ($dir -and -not (Test-Path -LiteralPath $dir)) { New-Item -Path $dir -ItemType Directory -Force | Out-Null }

    $existing = @()
    if (Test-Path -LiteralPath $Path) { $existing = @(Get-Content -LiteralPath $Path -Encoding UTF8) }

    $byGuid = [ordered]@{}
    foreach ($line in $existing) {
        if ($line -match '^[0-9a-fA-F]{32},') { $byGuid[$line.Substring(0,32).ToLower()] = $line }
        elseif ($line.Trim().Length -gt 0 -and -not $line.StartsWith('#')) { } # drop malformed
    }
    $added = 0
    foreach ($c in $Controllers) {
        $line = New-SdlMappingLine -Controller $c
        $guid = $line.Substring(0,32).ToLower()
        $byGuid[$guid] = $line
        $added++
    }
    $out = @('# SDL Game Controller DB - generated by ES-DE Auto Suite') + @($byGuid.Values)
    [System.IO.File]::WriteAllLines($Path, $out, (New-Object System.Text.UTF8Encoding($false)))
    & $Logger "Wrote $added controller mapping(s) to $Path" 'SUCCESS'
    return $Path
}

# ----- module: Reporting -----
<#
.SYNOPSIS
    Reporting engine. Generates Full_Report.json plus Full_Report.html and the
    per-area HTML reports (Migration, Media, Metadata, Optimization, Controllers,
    Missing_Media, Duplicate) from a single structured report object.
#>

Set-StrictMode -Version Latest

function HtmlEnc { param([string]$s) if ($null -eq $s) { return '' } [System.Net.WebUtility]::HtmlEncode([string]$s) }

$script:Css = @'
<style>
 body{font-family:Segoe UI,Arial,sans-serif;background:#11131a;color:#e6e6e6;margin:0;padding:24px}
 h1{color:#7fd1ff;margin:0 0 4px} h2{color:#9ad19a;border-bottom:1px solid #2a2f3a;padding-bottom:6px;margin-top:26px}
 a{color:#7fd1ff} .sub{color:#8a93a6;margin-bottom:16px}
 .cards{display:flex;flex-wrap:wrap;gap:12px;margin-bottom:8px}
 .card{background:#1b1f29;border:1px solid #2a2f3a;border-radius:10px;padding:12px 16px;min-width:150px}
 .card .k{color:#8a93a6;font-size:12px;text-transform:uppercase} .card .v{font-size:18px;margin-top:4px}
 table{border-collapse:collapse;width:100%;margin-top:8px;background:#1b1f29;border-radius:8px;overflow:hidden}
 th,td{padding:7px 11px;text-align:left;border-bottom:1px solid #2a2f3a;font-size:13px}
 th{background:#222735;color:#bcd} .ok{color:#7ee27e} .warn{color:#e2a05a} .mono{font-family:Consolas,monospace;color:#9fb3c8}
 .footer{margin-top:24px;color:#6b7280;font-size:12px}
</style>
'@

function New-HtmlDocument {
    param([string]$Title, [string]$Body)
    return "<!DOCTYPE html><html lang=`"en`"><head><meta charset=`"utf-8`"><meta name=`"viewport`" content=`"width=device-width, initial-scale=1`"><title>$(HtmlEnc $Title)</title>$script:Css</head><body>$Body<div class=`"footer`">ES-DE Auto Suite &bull; generated $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')</div></body></html>"
}

function ConvertTo-HtmlTable {
    param([string[]]$Headers, [object[]]$Rows)
    $sb = New-Object System.Text.StringBuilder
    [void]$sb.Append('<table><tr>')
    foreach ($h in $Headers) { [void]$sb.Append("<th>$(HtmlEnc $h)</th>") }
    [void]$sb.Append('</tr>')
    if (-not $Rows -or @($Rows).Count -eq 0) {
        [void]$sb.Append("<tr><td colspan='$($Headers.Count)'>No data.</td></tr>")
    } else {
        foreach ($row in $Rows) {
            [void]$sb.Append('<tr>')
            foreach ($cell in $row) { [void]$sb.Append("<td>$(HtmlEnc ([string]$cell))</td>") }
            [void]$sb.Append('</tr>')
        }
    }
    [void]$sb.Append('</table>')
    return $sb.ToString()
}

function Write-EsdeReports {
    <#
    .SYNOPSIS
        Writes every report file into $ReportsDir from the $Data report object.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string] $ReportsDir,
        [Parameter(Mandatory = $true)][hashtable] $Data,
        [Parameter(Mandatory = $true)][scriptblock] $Logger
    )
    if (-not (Test-Path -LiteralPath $ReportsDir)) { New-Item -Path $ReportsDir -ItemType Directory -Force | Out-Null }

    # ---- JSON ----
    $jsonPath = Join-Path $ReportsDir 'Full_Report.json'
    ($Data | ConvertTo-Json -Depth 12) | Set-Content -LiteralPath $jsonPath -Encoding UTF8

    # ---- Migration report ----
    $migRows = @($Data.Migration.PerSystem | ForEach-Object { ,@($_.System, $_.FromGamelist, $_.FromFolders, $_.Skipped) })
    $migBody = "<h1>Migration Report</h1><div class='sub'>RetroBat &rarr; ES-DE media migration</div>" +
               (ConvertTo-HtmlTable -Headers @('System','From gamelist','From folders','Skipped') -Rows $migRows)
    Set-Content (Join-Path $ReportsDir 'Migration_Report.html') (New-HtmlDocument 'Migration Report' $migBody) -Encoding UTF8

    # ---- Media report ----
    $medRows = @($Data.Media.PerSystem | ForEach-Object { ,@($_.System, $_.FoldersCreated, $_.Moved, $_.Skipped) })
    $medBody = "<h1>Media Report</h1><div class='sub'>Folder creation &amp; reorganization</div>" +
               (ConvertTo-HtmlTable -Headers @('System','Folders created','Files moved','Skipped') -Rows $medRows)
    Set-Content (Join-Path $ReportsDir 'Media_Report.html') (New-HtmlDocument 'Media Report' $medBody) -Encoding UTF8

    # ---- Metadata report ----
    $metRows = @($Data.Metadata.PerSystem | ForEach-Object { ,@($_.System, $_.Games, $_.Duplicates, $_.Repaired, $_.Removed, $(if ($_.Invalid) {'YES'} else {'no'})) })
    $metBody = "<h1>Metadata Report</h1><div class='sub'>gamelist.xml validation &amp; repair</div>" +
               (ConvertTo-HtmlTable -Headers @('System','Games','Duplicates removed','Paths repaired','Refs stripped','Was invalid') -Rows $metRows)
    Set-Content (Join-Path $ReportsDir 'Metadata_Report.html') (New-HtmlDocument 'Metadata Report' $metBody) -Encoding UTF8

    # ---- Optimization report ----
    $optRows = @($Data.Optimization | ForEach-Object { ,@($_.Emulator, $_.Result) })
    $optBody = "<h1>Optimization Report</h1><div class='sub'>Emulator graphics configuration</div>" +
               (ConvertTo-HtmlTable -Headers @('Emulator','Result') -Rows $optRows)
    Set-Content (Join-Path $ReportsDir 'Optimization_Report.html') (New-HtmlDocument 'Optimization Report' $optBody) -Encoding UTF8

    # ---- Controllers report ----
    $ctlRows = @($Data.Controllers | ForEach-Object { ,@($_.Name, $_.Vendor, $_.Family, $_.Api, $_.Connection, $_.VidPid) })
    $ctlBody = "<h1>Controllers Report</h1><div class='sub'>Detected controllers &amp; mappings</div>" +
               (ConvertTo-HtmlTable -Headers @('Name','Vendor','Family','API','Connection','VID:PID') -Rows $ctlRows)
    Set-Content (Join-Path $ReportsDir 'Controllers_Report.html') (New-HtmlDocument 'Controllers Report' $ctlBody) -Encoding UTF8

    # ---- Missing media report ----
    $mmRows = @($Data.MissingMedia.PerSystem | ForEach-Object {
        $t = $_.Totals
        ,@($_.System, $_.Games, $t.covers, $t.screenshots, $t.videos, $t.marquees, $t.fanart, $t.titlescreens, $t.manuals)
    })
    $mmBody = "<h1>Missing Media Report</h1><div class='sub'>Games missing each media type</div>" +
              (ConvertTo-HtmlTable -Headers @('System','Games','covers','screenshots','videos','marquees','fanart','titlescreens','manuals') -Rows $mmRows)
    Set-Content (Join-Path $ReportsDir 'Missing_Media_Report.html') (New-HtmlDocument 'Missing Media Report' $mmBody) -Encoding UTF8

    # ---- Duplicate report ----
    $dupRows = @($Data.Duplicates.Groups | Select-Object -First 500 | ForEach-Object { ,@($_.Hash.Substring(0,12), @($_.Files).Count, ($_.Files -join '  |  ')) })
    $dupBody = "<h1>Duplicate Report</h1><div class='sub'>$($Data.Duplicates.DuplicateFiles) duplicate file(s), $([math]::Round($Data.Duplicates.ReclaimableBytes/1MB,2)) MB reclaimable</div>" +
               (ConvertTo-HtmlTable -Headers @('SHA256 (short)','Copies','Files') -Rows $dupRows)
    Set-Content (Join-Path $ReportsDir 'Duplicate_Report.html') (New-HtmlDocument 'Duplicate Report' $dupBody) -Encoding UTF8

    # ---- Missing emulators report ----
    $gapRows = @()
    if ($Data.Keys -contains 'EmulatorGaps') {
        $gapRows = @($Data.EmulatorGaps | Where-Object { $_.Missing } | ForEach-Object { ,@($_.System, ($_.Required -join ', '), $_.Recommended) })
    }
    $gapBody = "<h1>Missing Emulators Report</h1><div class='sub'>Systems that have ROMs but no installed emulator</div>" +
               (ConvertTo-HtmlTable -Headers @('System','Compatible emulators','Recommended') -Rows $gapRows)
    Set-Content (Join-Path $ReportsDir 'Missing_Emulators_Report.html') (New-HtmlDocument 'Missing Emulators Report' $gapBody) -Encoding UTF8

    # ---- BIOS report ----
    $biosDetRows = @()
    if ($Data.Keys -contains 'BiosDetailed') {
        $biosDetRows = @($Data.BiosDetailed | ForEach-Object { ,@($_.File, $_.System, $_.Status, $_.Detail) })
    }
    $biosBody = "<h1>BIOS Report</h1><div class='sub'>Presence, MD5 verification and location</div>" +
                (ConvertTo-HtmlTable -Headers @('File','System','Status','Detail') -Rows $biosDetRows)
    Set-Content (Join-Path $ReportsDir 'Bios_Report.html') (New-HtmlDocument 'BIOS Report' $biosBody) -Encoding UTF8

    # ---- Health report ----
    $healthRows = @()
    if ($Data.Keys -contains 'Health') { $healthRows = @($Data.Health | ForEach-Object { ,@($_.Time, $_.Area, $_.Status, $_.Detail) }) }
    $phaseRows = @()
    if ($Data.Keys -contains 'PhaseResults') { $phaseRows = @($Data.PhaseResults | ForEach-Object { ,@($_.Phase, $_.Result, $_.Seconds, $_.Error) }) }
    $healthBody = "<h1>Health &amp; Self-Repair Report</h1><div class='sub'>$($Data.Errors) error(s), $($Data.Warnings) warning(s) - the suite continued through every phase</div>" +
                  "<h2>Findings</h2>" + (ConvertTo-HtmlTable -Headers @('Time','Area','Status','Detail') -Rows $healthRows) +
                  "<h2>Phase timings</h2>" + (ConvertTo-HtmlTable -Headers @('Phase','Result','Seconds','Error') -Rows $phaseRows)
    Set-Content (Join-Path $ReportsDir 'Health_Report.html') (New-HtmlDocument 'Health Report' $healthBody) -Encoding UTF8

    # ---- Full report (overview + links) ----
    $hw = $Data.Hardware
    $biosRows = @($Data.Bios | ForEach-Object { ,@($_.File, $_.System) })
    $sysRows  = @($Data.Systems | ForEach-Object { ,@($_.Name, $(if($_.Roms){'yes'}else{'-'}), $(if($_.Gamelist){'yes'}else{'-'}), $(if($_.Media){'yes'}else{'-'})) })
    $links = @('Migration_Report.html','Media_Report.html','Metadata_Report.html','Optimization_Report.html','Missing_Emulators_Report.html','Controllers_Report.html','Missing_Media_Report.html','Duplicate_Report.html','Bios_Report.html','Health_Report.html')
    $linkHtml = ($links | ForEach-Object { "<a href='$_'>$($_ -replace '_',' ' -replace '\.html','')</a>" }) -join ' &bull; '

    $body = @"
<h1>ES-DE Auto Suite &mdash; Full Report</h1>
<div class="sub">Generated $(HtmlEnc $Data.GeneratedAt) &bull; ES-DE $(HtmlEnc $Data.EsdeVersion) &bull; Data: $(HtmlEnc $Data.DataDir)</div>
<div class="cards">
 <div class="card"><div class="k">Performance tier</div><div class="v">$(HtmlEnc $Data.Tier)</div></div>
 <div class="card"><div class="k">Target resolution</div><div class="v">$($Data.Profile.TargetWidth) x $($Data.Profile.TargetHeight)</div></div>
 <div class="card"><div class="k">Systems</div><div class="v">$(@($Data.Systems).Count)</div></div>
 <div class="card"><div class="k">Media migrated</div><div class="v">$($Data.Migration.TotalCopied)</div></div>
 <div class="card"><div class="k">Media reorganized</div><div class="v">$($Data.Media.TotalMoved)</div></div>
 <div class="card"><div class="k">Duplicates</div><div class="v">$($Data.Duplicates.DuplicateFiles)</div></div>
 <div class="card"><div class="k">Controllers</div><div class="v">$(@($Data.Controllers).Count)</div></div>
 <div class="card"><div class="k">Warnings</div><div class="v">$($Data.Warnings)</div></div>
</div>
<h2>Reports</h2><div class="sub">$linkHtml</div>
<h2>Hardware</h2>
<div class="cards">
 <div class="card"><div class="k">CPU</div><div class="v">$(HtmlEnc $hw.CpuName)</div></div>
 <div class="card"><div class="k">GPU</div><div class="v">$(HtmlEnc $hw.GpuName) ($(HtmlEnc $hw.GpuVendor))</div></div>
 <div class="card"><div class="k">VRAM</div><div class="v">$($hw.GpuVramMB) MB</div></div>
 <div class="card"><div class="k">RAM</div><div class="v">$($hw.TotalRamGB) GB</div></div>
 <div class="card"><div class="k">Display</div><div class="v">$($hw.DisplayWidth)x$($hw.DisplayHeight)@$($hw.RefreshRateHz)Hz</div></div>
</div>
<h2>Systems</h2>
$(ConvertTo-HtmlTable -Headers @('System','ROMs','Gamelist','Media') -Rows $sysRows)
<h2>Missing BIOS</h2>
$(ConvertTo-HtmlTable -Headers @('File','Needed for') -Rows $biosRows)
"@
    Set-Content (Join-Path $ReportsDir 'Full_Report.html') (New-HtmlDocument 'ES-DE Auto Suite Full Report' $body) -Encoding UTF8

    & $Logger "Reports written to $ReportsDir (Full_Report.html/.json + 7 section reports)." 'SUCCESS'
}

# ----- module: ReportingPlus -----
<#
.SYNOPSIS
    Additional report formats: CSV (spreadsheet-friendly) and a Markdown summary.
#>

Set-StrictMode -Version Latest

function Export-CsvReports {
    <#
    .SYNOPSIS
        Writes per-system summary and missing-media CSV files to the reports dir.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string] $ReportsDir,
        [Parameter(Mandatory = $true)][hashtable] $Data
    )
    if (-not (Test-Path -LiteralPath $ReportsDir)) { New-Item -Path $ReportsDir -ItemType Directory -Force | Out-Null }

    # Per-system summary CSV.
    $rows = New-Object System.Collections.Generic.List[object]
    foreach ($s in @($Data.Systems)) {
        $mm = @($Data.MissingMedia.PerSystem | Where-Object { $_.System -eq $s.Name }) | Select-Object -First 1
        $cov = @($Data.Audit.MediaCoverage | Where-Object { $_.System -eq $s.Name }) | Select-Object -First 1
        $rows.Add([pscustomobject]@{
            System      = $s.Name
            HasRoms     = $s.Roms
            HasGamelist = $s.Gamelist
            Games       = if ($mm) { $mm.Games } else { 0 }
            CoversPct   = if ($cov) { $cov.Covers } else { '' }
            MissingCovers = if ($mm) { $mm.Totals.covers } else { '' }
            MissingVideos = if ($mm) { $mm.Totals.videos } else { '' }
        })
    }
    if ($rows.Count -gt 0) { $rows | Export-Csv -LiteralPath (Join-Path $ReportsDir 'Systems_Summary.csv') -NoTypeInformation -Encoding UTF8 }

    # Missing-media flat CSV.
    $mrows = New-Object System.Collections.Generic.List[object]
    foreach ($ps in @($Data.MissingMedia.PerSystem)) {
        $t = $ps.Totals
        $mrows.Add([pscustomobject]@{
            System=$ps.System; Games=$ps.Games; Covers=$t.covers; Screenshots=$t.screenshots
            Videos=$t.videos; Marquees=$t.marquees; Fanart=$t.fanart; Titlescreens=$t.titlescreens; Manuals=$t.manuals
        })
    }
    if ($mrows.Count -gt 0) { $mrows | Export-Csv -LiteralPath (Join-Path $ReportsDir 'Missing_Media.csv') -NoTypeInformation -Encoding UTF8 }
    return $true
}

function Export-MarkdownSummary {
    <#
    .SYNOPSIS
        Writes a concise Markdown summary of the run.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string] $ReportsDir,
        [Parameter(Mandatory = $true)][hashtable] $Data
    )
    $sb = New-Object System.Text.StringBuilder
    [void]$sb.AppendLine("# ES-DE Auto Suite - Summary")
    [void]$sb.AppendLine("")
    [void]$sb.AppendLine("- Generated: $($Data.GeneratedAt)")
    [void]$sb.AppendLine("- ES-DE: $($Data.EsdeVersion)  |  Tier: $($Data.Tier)  |  Target: $($Data.Profile.TargetWidth)x$($Data.Profile.TargetHeight)")
    [void]$sb.AppendLine("- Systems: $(@($Data.Systems).Count)  |  Controllers: $(@($Data.Controllers).Count)")
    [void]$sb.AppendLine("- Media migrated: $($Data.Migration.TotalCopied)  |  reorganized: $($Data.Media.TotalMoved)  |  duplicates removed scan: $($Data.Duplicates.DuplicateFiles)")
    [void]$sb.AppendLine("- Health: $($Data.Errors) error(s), $($Data.Warnings) warning(s)")
    [void]$sb.AppendLine("")
    [void]$sb.AppendLine("## Systems")
    [void]$sb.AppendLine("")
    [void]$sb.AppendLine("| System | ROMs | Gamelist | Media |")
    [void]$sb.AppendLine("|---|---|---|---|")
    foreach ($s in @($Data.Systems)) {
        [void]$sb.AppendLine("| $($s.Name) | $(if($s.Roms){'yes'}else{'-'}) | $(if($s.Gamelist){'yes'}else{'-'}) | $(if($s.Media){'yes'}else{'-'}) |")
    }
    [void]$sb.AppendLine("")
    [void]$sb.AppendLine("## Missing BIOS")
    [void]$sb.AppendLine("")
    foreach ($b in @($Data.Bios)) { [void]$sb.AppendLine("- $($b.File) - $($b.System)") }
    Set-Content -LiteralPath (Join-Path $ReportsDir 'Summary.md') -Value $sb.ToString() -Encoding UTF8
    return $true
}

# ----- module: GitIntegration -----
<#
.SYNOPSIS
    Git integration module.
.DESCRIPTION
    Detects Git, the current repository and branch, stages changes, creates a
    descriptive commit and pushes to the current branch. Authentication failures
    are handled gracefully and never cause credentials to be printed. If the
    working tree is not a git repository, the module reports this and does nothing.
#>

Set-StrictMode -Version Latest

function Test-GitAvailable {
    <#
    .SYNOPSIS
        Returns the git executable path, or $null if git is not installed.
    #>
    [CmdletBinding()]
    param()
    $cmd = Get-Command -Name git -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    foreach ($base in @(${env:ProgramFiles}, ${env:ProgramFiles(x86)})) {
        if ([string]::IsNullOrWhiteSpace($base)) { continue }
        $p = Join-Path $base 'Git\cmd\git.exe'
        if (Test-Path -LiteralPath $p) { return $p }
    }
    return $null
}

function Invoke-Git {
    <#
    .SYNOPSIS
        Runs a git command in a repo directory and returns Output + ExitCode.
        stderr is captured to avoid leaking to the console (may contain URLs).
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)] [string]   $GitExe,
        [Parameter(Mandatory = $true)] [string]   $RepoPath,
        [Parameter(Mandatory = $true)] [string[]] $GitArgs
    )

    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName               = $GitExe
    $psi.WorkingDirectory       = $RepoPath
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError  = $true
    $psi.UseShellExecute        = $false
    $psi.CreateNoWindow         = $true
    # Prevent git from launching interactive credential prompts that would hang.
    $psi.EnvironmentVariables['GIT_TERMINAL_PROMPT'] = '0'
    $psi.EnvironmentVariables['GCM_INTERACTIVE']     = 'never'
    foreach ($a in $GitArgs) { $psi.ArgumentList.Add($a) }

    $proc = [System.Diagnostics.Process]::Start($psi)
    $out  = $proc.StandardOutput.ReadToEnd()
    $err  = $proc.StandardError.ReadToEnd()
    $proc.WaitForExit()

    return @{ Output = $out.Trim(); Error = $err.Trim(); ExitCode = $proc.ExitCode }
}

function Get-GitContext {
    <#
    .SYNOPSIS
        Returns repository context: IsRepo, Branch, Remote, HasChanges.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)] [string] $GitExe,
        [Parameter(Mandatory = $true)] [string] $RepoPath
    )

    $ctx = @{ IsRepo = $false; Branch = $null; Remote = $null; HasChanges = $false }

    $inside = Invoke-Git -GitExe $GitExe -RepoPath $RepoPath -GitArgs @('rev-parse','--is-inside-work-tree')
    if ($inside.ExitCode -ne 0 -or $inside.Output -ne 'true') { return $ctx }
    $ctx.IsRepo = $true

    # 'branch --show-current' (git 2.22+) reports the branch even on an unborn
    # HEAD (a freshly created branch with no commits yet); fall back as needed.
    $branch = Invoke-Git -GitExe $GitExe -RepoPath $RepoPath -GitArgs @('branch','--show-current')
    if ($branch.ExitCode -eq 0 -and $branch.Output) {
        $ctx.Branch = $branch.Output
    } else {
        $sym = Invoke-Git -GitExe $GitExe -RepoPath $RepoPath -GitArgs @('symbolic-ref','--short','HEAD')
        if ($sym.ExitCode -eq 0 -and $sym.Output) { $ctx.Branch = $sym.Output }
    }

    $remote = Invoke-Git -GitExe $GitExe -RepoPath $RepoPath -GitArgs @('remote')
    if ($remote.ExitCode -eq 0 -and $remote.Output) {
        $ctx.Remote = ($remote.Output -split "`n")[0].Trim()
    }

    $status = Invoke-Git -GitExe $GitExe -RepoPath $RepoPath -GitArgs @('status','--porcelain')
    $ctx.HasChanges = ($status.ExitCode -eq 0 -and $status.Output.Length -gt 0)

    return $ctx
}

function Invoke-GitCommitAndPush {
    <#
    .SYNOPSIS
        Stages all changes, commits with a descriptive message and pushes to the
        current branch with retry/backoff. Returns a result hashtable.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)] [string] $RepoPath,
        [Parameter(Mandatory = $true)] [string] $CommitMessage,
        [Parameter(Mandatory = $true)] [scriptblock] $Logger,
        [int] $MaxRetries = 4
    )

    $git = Test-GitAvailable
    if (-not $git) {
        & $Logger "Git is not installed; skipping repository integration." 'WARN'
        return @{ Success = $false; Message = 'git not found' }
    }

    $ctx = Get-GitContext -GitExe $git -RepoPath $RepoPath
    if (-not $ctx.IsRepo) {
        & $Logger "Not a git repository: $RepoPath. Skipping commit/push." 'WARN'
        return @{ Success = $false; Message = 'not a repo' }
    }

    & $Logger "Git repository detected. Branch: $($ctx.Branch); Remote: $($ctx.Remote)" 'INFO'

    if (-not $ctx.HasChanges) {
        & $Logger "No changes to commit." 'INFO'
        return @{ Success = $true; Message = 'nothing to commit' }
    }

    $add = Invoke-Git -GitExe $git -RepoPath $RepoPath -GitArgs @('add','-A')
    if ($add.ExitCode -ne 0) {
        & $Logger "git add failed: $($add.Error)" 'ERROR'
        return @{ Success = $false; Message = 'git add failed' }
    }

    $commit = Invoke-Git -GitExe $git -RepoPath $RepoPath -GitArgs @('commit','-m',$CommitMessage)
    if ($commit.ExitCode -ne 0) {
        # A non-zero here is usually "nothing to commit" after add; report and stop.
        & $Logger "git commit returned non-zero: $($commit.Output) $($commit.Error)" 'WARN'
        return @{ Success = $false; Message = 'commit failed or nothing staged' }
    }
    & $Logger "Committed changes to '$($ctx.Branch)'." 'SUCCESS'

    if (-not $ctx.Remote) {
        & $Logger "No remote configured; commit created locally only." 'WARN'
        return @{ Success = $true; Message = 'committed locally (no remote)' }
    }

    # Push with exponential backoff. Auth failures are detected and reported
    # without echoing any credential material.
    $delay = 2
    for ($attempt = 1; $attempt -le $MaxRetries; $attempt++) {
        $push = Invoke-Git -GitExe $git -RepoPath $RepoPath -GitArgs @('push','-u',$ctx.Remote,$ctx.Branch)
        if ($push.ExitCode -eq 0) {
            & $Logger "Pushed to $($ctx.Remote)/$($ctx.Branch)." 'SUCCESS'
            return @{ Success = $true; Message = 'pushed' }
        }

        $errLower = $push.Error.ToLower()
        if ($errLower -match 'authentication|could not read username|permission denied|403|terminal prompts disabled|invalid credentials') {
            & $Logger "Push failed due to authentication/permission. Configure a credential helper or token and retry. (No credentials were displayed.)" 'ERROR'
            return @{ Success = $false; Message = 'auth failure' }
        }

        if ($attempt -lt $MaxRetries) {
            & $Logger "Push attempt $attempt failed (network/other). Retrying in ${delay}s..." 'WARN'
            Start-Sleep -Seconds $delay
            $delay *= 2
        } else {
            & $Logger "Push failed after $MaxRetries attempts: $($push.Error)" 'ERROR'
        }
    }
    return @{ Success = $false; Message = 'push failed' }
}

# ----- orchestrator -----
# Resolve ES-DE + working directories
# ---------------------------------------------------------------------------
if (-not $EsdeRoot) { $EsdeRoot = $ScriptDir }
$dataDir = Find-EsdeDataDir -StartPath $EsdeRoot
if (-not $dataDir) {
    # Create a minimal ES-DE data dir under the launcher so the suite still runs.
    $dataDir = Join-Path $EsdeRoot 'ES-DE'
    foreach ($d in @('settings','gamelists','downloaded_media','themes','custom_systems','collections')) {
        New-Item -Path (Join-Path $dataDir $d) -ItemType Directory -Force | Out-Null
    }
}

$Layout   = Get-EsdeLayout -DataDir $dataDir
$WorkRoot = Join-Path $dataDir 'ESDEAutoSuite'
$LogsDir  = Join-Path $WorkRoot 'Logs'
$BackupDir= Join-Path $WorkRoot 'Backups'
$ReportsDir = Join-Path $WorkRoot 'Reports'
foreach ($d in @($WorkRoot,$LogsDir,$BackupDir,$ReportsDir)) { if (-not (Test-Path -LiteralPath $d)) { New-Item -Path $d -ItemType Directory -Force | Out-Null } }

Initialize-EsdeLogging -LogRoot $LogsDir

# Path to the launcher (the all-in-one .bat sets ESDE_LAUNCHER=%~f0). Used by the
# optional scheduled-task and desktop-shortcut features.
$LauncherSelfPath = if ($env:ESDE_LAUNCHER -and (Test-Path -LiteralPath $env:ESDE_LAUNCHER)) { $env:ESDE_LAUNCHER }
                    elseif ($MyInvocation.MyCommand.Path) { $MyInvocation.MyCommand.Path }
                    else { Join-Path $EsdeRoot 'ESDEAutoSuite.bat' }

# Category loggers (plain scriptblocks bound to script scope; resolve Write-EsdeLog).
$LMain  = { param($m,$l='INFO') Write-EsdeLog -Message $m -Level $l -Category 'Main' }
$LMig   = { param($m,$l='INFO') Write-EsdeLog -Message $m -Level $l -Category 'Migration' }
$LMedia = { param($m,$l='INFO') Write-EsdeLog -Message $m -Level $l -Category 'Media' }
$LMeta  = { param($m,$l='INFO') Write-EsdeLog -Message $m -Level $l -Category 'Metadata' }
$LOpt   = { param($m,$l='INFO') Write-EsdeLog -Message $m -Level $l -Category 'Optimization' }
$LCtl   = { param($m,$l='INFO') Write-EsdeLog -Message $m -Level $l -Category 'Controllers' }
$LDown  = { param($m,$l='INFO') Write-EsdeLog -Message $m -Level $l -Category 'Downloads' }
$LGit   = { param($m,$l='INFO') Write-EsdeLog -Message $m -Level $l -Category 'Git' }

function ConvertTo-Ht { param([object]$o) $h=@{}; if($o){ foreach($p in $o.PSObject.Properties){ $h[$p.Name]=$p.Value } }; return $h }

function Resolve-MediaSource {
    # The media to migrate lives in the ES-DE ROM directory (per-system media
    # sub-folders / gamelist references). An optional -RetroBatRoot is honoured as
    # an explicit override only; nothing is assumed about RetroBat's location.
    param([string] $RetroBatRoot, [System.Collections.Specialized.OrderedDictionary] $Layout)
    if ($RetroBatRoot) {
        $rr = Join-Path $RetroBatRoot 'roms'
        if (Test-Path -LiteralPath $rr) { return $rr }
        if (Test-Path -LiteralPath $RetroBatRoot) { return $RetroBatRoot }
    }
    if (Test-Path -LiteralPath $Layout.RomDir) { return $Layout.RomDir }
    return $null
}

function Get-EmuRoots {
    # ES-DE-native emulator roots (no RetroBat assumptions); $RetroBatRoot is an
    # optional explicit override only.
    return @(Get-EsdeEmulatorsRoots -Layout $Layout -ExtraRoot $RetroBatRoot)
}

function Find-RetroArchExe {
    foreach ($root in (Get-EmuRoots)) {
        $exe = Find-FileDepthLimited -Root $root -FileName 'retroarch.exe' -MaxDepth 4
        if ($exe) { return $exe }
    }
    return $null
}

# ===========================================================================
# RESTORE MODE
# ===========================================================================
function Invoke-EsdeRestore {
    Write-EsdeSection -Title 'ES-DE Auto Suite - Restore From Backups' -Category 'Main'
    if (-not (Test-Path -LiteralPath $BackupDir)) { & $LMain "No backups at $BackupDir." 'WARN'; return }
    $backups = @(Get-ChildItem -LiteralPath $BackupDir -Filter '*.bak' -File -ErrorAction SilentlyContinue)
    if ($backups.Count -eq 0) { & $LMain "Backup folder is empty." 'WARN'; return }

    # Index current files by leaf name across data dir + rom dir.
    $index = @{}
    foreach ($root in @($Layout.DataDir, $Layout.RomDir, $Layout.MediaDir)) {
        if (-not (Test-Path -LiteralPath $root)) { continue }
        Get-ChildItem -LiteralPath $root -Recurse -File -ErrorAction SilentlyContinue | ForEach-Object {
            $k = $_.Name.ToLower()
            if (-not $index.ContainsKey($k)) { $index[$k] = New-Object System.Collections.Generic.List[string] }
            $index[$k].Add($_.FullName)
        }
    }
    $restored = 0
    foreach ($grp in ($backups | Group-Object { ($_.Name -replace '\.\d{8}_\d{6}\.bak$','') })) {
        $newest = $grp.Group | Sort-Object LastWriteTime -Descending | Select-Object -First 1
        $leaf = $grp.Name.ToLower()
        if ($index.ContainsKey($leaf)) {
            foreach ($t in $index[$leaf]) { Copy-Item -LiteralPath $newest.FullName -Destination $t -Force; & $LMain "Restored $t" 'SUCCESS'; $restored++ }
        }
    }
    & $LMain "Restore complete: $restored file(s) restored." 'SUCCESS'
}

# ===========================================================================
# HOTSWAP WATCHER
# ===========================================================================
function Start-EsdeWatcher {
    param([object] $EmuDefs)
    Write-EsdeSection -Title 'Controller Hotswap Watcher' -Category 'Controllers'
    & $LCtl "Watcher started (interval ${WatchIntervalSeconds}s). Ctrl+C to stop." 'INFO'
    $vendorMap = ConvertTo-Ht $EmuDefs.controllerVendors
    $lastSig = ''; $primed = $false
    while ($true) {
        try {
            $controllers = @(Get-ConnectedControllers -VendorMap $vendorMap)
            $sig = Get-ControllerSignature -Controllers $controllers
            if ($sig -ne $lastSig) {
                if ($primed) {
                    if ($sig -eq '') { & $LCtl "All controllers disconnected; configuration left intact." 'WARN' }
                    else { & $LCtl "Controller change ($($controllers.Count) connected); reconfiguring..." 'INFO'; Set-EsdeControllers -Controllers $controllers }
                }
                $lastSig = $sig; $primed = $true
            }
        } catch { & $LCtl "Watcher error: $($_.Exception.Message)" 'ERROR' }
        Start-Sleep -Seconds $WatchIntervalSeconds
    }
}

function Set-EsdeControllers {
    param([object[]] $Controllers)
    if (-not $Controllers -or $Controllers.Count -eq 0) { & $LCtl "No controllers connected." 'INFO'; return }
    $raExe = Find-RetroArchExe
    if ($raExe) {
        $raDir = Split-Path $raExe -Parent
        $ra = Join-Path $raDir 'autoconfig'
        foreach ($c in $Controllers) { Write-RetroArchControllerProfile -Controller $c -AutoconfigDir $ra -Logger $LCtl | Out-Null }
        # Universal SDL mapping DB - consumed by RetroArch and all SDL-based
        # standalone emulators (DuckStation, PCSX2, PPSSPP, Flycast, ...).
        Write-GameControllerDb -Controllers $Controllers -Path (Join-Path $raDir 'gamecontrollerdb.txt') -Logger $LCtl | Out-Null
    }
    # Also drop a gamecontrollerdb in the ES-DE data dir for portability.
    Write-GameControllerDb -Controllers $Controllers -Path (Join-Path $Layout.DataDir 'gamecontrollerdb.txt') -Logger $LCtl | Out-Null
    Write-EmulationStationInput -Controllers $Controllers -EsInputPath $Layout.InputFile -BackupRoot $BackupDir -Logger $LCtl | Out-Null
}

# ===========================================================================
# FULL SETUP PIPELINE
# ===========================================================================
function Invoke-EsdeSetup {
    Initialize-Health
    $report = [ordered]@{
        GeneratedAt = (Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
        EsdeVersion = $Layout.Version; DataDir = $Layout.DataDir; RomDir = $Layout.RomDir; MediaDir = $Layout.MediaDir
        Tier = ''; Profile = @{ TargetWidth = 0; TargetHeight = 0 }; Hardware = @{}
        Systems = @(); Migration = @{ PerSystem = @(); TotalCopied = 0 }
        Media = @{ PerSystem = @(); TotalMoved = 0; Recovered = 0 }; Metadata = @{ PerSystem = @() }
        Optimization = @(); Controllers = @(); MissingMedia = @{ PerSystem = @() }
        Duplicates = @{ Groups=@(); TotalFiles=0; DuplicateFiles=0; ReclaimableBytes=0 }
        Bios = @(); BiosDetailed = @(); EmulatorGaps = @(); EmulatorIntegrity = @()
        Health = @(); PhaseResults = @(); Warnings = 0; Errors = 0
        Audit = [ordered]@{
            SuiteVersion = ''; Online = $false; Language = ''
            EsSystems = @{}; Themes = @{}; Collections = @(); AltEmulators = @()
            EmptySystems = @(); ControllerVerify = @{}; SettingsTuned = $false
            ExtensionsFixed = 0; ScreenshotsGenerated = 0; RomsHashed = 0
            MediaCoverage = @(); DiskUsage = @(); OversizedMedia = 0; NonFriendlyVideos = 0
            PlayStats = @(); RegionDuplicates = @(); Consistency = @()
            Enriched = 0; IntegrityQuarantined = 0; IntegrityFixed = 0
            RomStats = @(); ScrapeRatio = @(); MultiDiscPlaylists = 0; CompressionAdvisory = @()
            MediaTypeTotals = @{}; TopLargest = @(); ConfigsArchived = 0
            RetroArchExtras = $false; UxApplied = 0; UxTuned = $false
            SavesArchived = 0; OrphanSaves = 0; CustomCollections = @{}; RegionHidden = 0
            Statistics = @{}; DuplicateRoms = 0; BadExtensions = @(); CheatFiles = 0
            CustomSystemSuggestions = @(); ManifestSystems = 0
            ShaderApplied = ''; LatencyTuned = $false
            Playlists = 0; DatVerify = @(); RaFeatures = $false; StandaloneHotkeys = 0
            ThemesInstalled = 0; ActiveTheme = ''; ScheduledTask = $false; ShortcutCreated = $false
            StorageHealth = @(); Telemetry = @{}; LogsRotated = 0; ConfigDrift = 0; Update = @{}
            CrossSystemDuplicates = 0; RegionDistribution = @{}; Completion = @{}; BadArchives = 0
            HealthScore = 100; PlaytimeTop = @(); NewestAdditions = @()
            AutoCollections = @{}; AutoFavorited = 0; SanityFixed = 0; UnlistedAdded = 0
            MediaNamesFixed = 0; CrossSystemMediaDup = 0; BrokenM3u = 0
            PerSystemStats = @(); AbandonedGames = 0; Savestates = 0; GamelistDiff = @()
            ControllerBundle = 0; DiskForecastMB = 0; NetworkPaths = @(); ChdConverted = 0; ChdSavedMB = 0.0
        }
    }

    # Shared state with safe defaults so a failing phase never breaks later phases.
    $systems = @(); $hw = $null; $tier = 'MidRange'
    $profile = @{ TargetWidth = 1920; TargetHeight = 1080; InternalScale = 2 }
    $missingPerSystem = @(); $installedEmuIds = @(); $controllers = @()

    Write-EsdeSection -Title 'ES-DE Auto Suite' -Category 'Main'
    & $LMain "ES-DE data dir: $($Layout.DataDir)  (version $($Layout.Version))" 'INFO'
    & $LMain "ROM dir: $($Layout.RomDir)" 'INFO'
    & $LMain "Media dir: $($Layout.MediaDir)" 'INFO'
    if ($DryRun) { & $LMain "DRY-RUN: no files will be written." 'WARN' }

    $mediaDefs = ($script:EmbeddedMediaJson | ConvertFrom-Json)
    $emuDefs   = ($script:EmbeddedEmuJson | ConvertFrom-Json)
    $sysEmuMap = ConvertTo-Ht $mediaDefs.systemEmulators

    # ---- Phase 0: health preflight + self-heal of the ES-DE structure ----
    Write-EsdeSection -Title 'Phase 0 - Health Preflight & Self-Repair' -Category 'Main'
    try {
        $freeGB = Get-FreeSpaceGB -Path $Layout.DataDir
        & $LMain "Free space on data drive: $freeGB GB" 'INFO'
        if ($freeGB -ge 0 -and $freeGB -lt 1) { & $LMain "Low disk space (<1GB); media operations may be limited." 'WARN'; Add-HealthFinding 'Disk' 'Warning' "Only $freeGB GB free." }
        if (-not (Test-PathWritable -Path $WorkRoot)) { & $LMain "Work directory is not writable: $WorkRoot" 'ERROR'; Add-HealthFinding 'Permissions' 'Error' "Not writable: $WorkRoot" }
        else { Add-HealthFinding 'Permissions' 'OK' "Work directory writable." }
        if (-not $DryRun) { Repair-EsdeStructure -Layout $Layout -Logger $LMain | Out-Null }
        # Self-heal a malformed es_settings.xml before anything reads it.
        if ((Test-Path -LiteralPath $Layout.SettingsFile) -and -not (Test-XmlWellFormed -Path $Layout.SettingsFile)) {
            Repair-XmlFile -Path $Layout.SettingsFile -BackupRoot $BackupDir -Logger $LMain -DryRun:$DryRun | Out-Null
        }
    } catch { & $LMain "Preflight error: $($_.Exception.Message)" 'ERROR'; Add-HealthFinding 'Preflight' 'Error' $_.Exception.Message }

    # ---- Phase 1: discovery ----
    try {
        Write-EsdeSection -Title 'Phase 1 - ES-DE Discovery' -Category 'Main'
        foreach ($k in $Layout.Exists.Keys) { & $LMain ("  {0,-18} {1}" -f $k, $(if($Layout.Exists[$k]){'present'}else{'MISSING'})) 'INFO' }
        $systems = @(Get-EsdeSystems -Layout $Layout)
        & $LMain "Detected $($systems.Count) system(s)." 'SUCCESS'
        $report.Systems = @($systems | ForEach-Object { @{ Name=$_.Name; Roms=$_.HasRoms; Gamelist=$_.HasGamelist; Media=$_.HasMedia } })
    } catch { & $LMain "Phase 1 error: $($_.Exception.Message)" 'ERROR'; Add-HealthFinding 'Discovery' 'Error' $_.Exception.Message }

    # ---- Phase 2: hardware + profile ----
    try {
        Write-EsdeSection -Title 'Phase 2 - Hardware Detection & Profile' -Category 'Main'
        $hw = Get-SystemHardware
        & $LMain "CPU: $($hw.CpuName) | GPU: $($hw.GpuName) [$($hw.GpuVendor)] $($hw.GpuVramMB)MB | RAM: $($hw.TotalRamGB)GB | $($hw.DisplayWidth)x$($hw.DisplayHeight)" 'INFO'
        Save-Profiles -ProfilesDir (Join-Path $WorkRoot 'profiles') -Logger $LMain | Out-Null
        $sel = Select-ProfileForHardware -Hardware $hw -Logger $LMain
        $tier = $sel.Tier; $profile = $sel.Profile
        $report.Tier = $tier
        $report.Profile = @{ TargetWidth = $profile.TargetWidth; TargetHeight = $profile.TargetHeight }
        $report.Hardware = @{ CpuName=$hw.CpuName; GpuName=$hw.GpuName; GpuVendor=$hw.GpuVendor; GpuVramMB=$hw.GpuVramMB; TotalRamGB=$hw.TotalRamGB; DisplayWidth=$hw.DisplayWidth; DisplayHeight=$hw.DisplayHeight; RefreshRateHz=$hw.RefreshRateHz }
    } catch { & $LMain "Phase 2 error: $($_.Exception.Message)" 'ERROR'; Add-HealthFinding 'Hardware' 'Error' $_.Exception.Message }
    if (-not $hw) { $hw = [ordered]@{ GpuVendor='Unknown' } }

    # ---- Phase 3: backup snapshot ----
    try {
        Write-EsdeSection -Title 'Phase 3 - Backup Snapshot' -Category 'Main'
        if (-not $DryRun) {
            $snap = Backup-Tree -SourceDir $Layout.Gamelists -BackupRoot $BackupDir -Label 'gamelists'
            if ($snap) { & $LMain "Backed up $($snap.FileCount) gamelist file(s)." 'SUCCESS' }
            Backup-File -Path $Layout.SettingsFile -BackupRoot $BackupDir | Out-Null
        } else { & $LMain "[DRY-RUN] Backup snapshot skipped." 'INFO' }
    } catch { & $LMain "Phase 3 error: $($_.Exception.Message)" 'ERROR'; Add-HealthFinding 'Backup' 'Error' $_.Exception.Message }

    # ---- Phase 3b: protect save data (saves / states / memory cards) ----
    try {
        Write-EsdeSection -Title 'Phase 3b - Save Data Protection' -Category 'Main'
        $report.Audit.SavesArchived = (Backup-SaveData -RomDir $Layout.RomDir -EmulatorRoots @(Get-EmuRoots) -BackupRoot $BackupDir -Logger $LMain -DryRun:$DryRun)
        & $LMain "Save data archived: $($report.Audit.SavesArchived) file(s)." 'INFO'
    } catch { & $LMain "Phase 3b error: $($_.Exception.Message)" 'ERROR'; Add-HealthFinding 'SaveBackup' 'Error' $_.Exception.Message }

    # ---- Phase 4: RetroBat / in-place media migration ----
    try {
        Write-EsdeSection -Title 'Phase 4 - Media Migration' -Category 'Migration'
        if (-not $SkipMigration) {
            $rbRoms = Resolve-MediaSource -RetroBatRoot $RetroBatRoot -Layout $Layout
            if ($rbRoms) {
                & $LMig "Media migration source (ES-DE ROM dir): $rbRoms" 'INFO'
                foreach ($sysDir in (Get-ChildItem -LiteralPath $rbRoms -Directory -ErrorAction SilentlyContinue)) {
                    if (-not (Test-RetroBatMediaLayout -SystemRomDir $sysDir.FullName)) { continue }
                    $sysMedia = Join-Path $Layout.MediaDir $sysDir.Name
                    $st = Invoke-SystemMigration -SystemRomDir $sysDir.FullName -SystemMediaDir $sysMedia -Definitions $mediaDefs -BackupRoot $BackupDir -Logger $LMig -DryRun:$DryRun
                    $report.Migration.PerSystem += @{ System=$sysDir.Name; FromGamelist=$st.FromGamelist; FromFolders=$st.FromFolders; Skipped=$st.Skipped }
                    $report.Migration.TotalCopied += ($st.FromGamelist + $st.FromFolders)
                }
                & $LMig "Migration total: $($report.Migration.TotalCopied) media file(s) copied." 'SUCCESS'
            } else { & $LMig "No media source found; skipping migration." 'WARN' }
        } else { & $LMig "Migration skipped by request." 'INFO' }
    } catch { & $LMig "Phase 4 error: $($_.Exception.Message)" 'ERROR'; Add-HealthFinding 'Migration' 'Error' $_.Exception.Message }

    # ---- Phase 5: media reorganization ----
    try {
        Write-EsdeSection -Title 'Phase 5 - Media Reorganization' -Category 'Media'
        foreach ($sys in $systems) {
            $st = Invoke-MediaReorganization -SystemMediaDir $sys.MediaDir -Definitions $mediaDefs -BackupRoot $BackupDir -Logger $LMedia -DryRun:$DryRun
            $report.Media.PerSystem += @{ System=$sys.Name; FoldersCreated=$st.FoldersCreated; Moved=$st.Moved; Skipped=$st.Skipped }
            $report.Media.TotalMoved += $st.Moved
        }
        & $LMedia "Reorganization total: $($report.Media.TotalMoved) file(s) moved." 'SUCCESS'
    } catch { & $LMedia "Phase 5 error: $($_.Exception.Message)" 'ERROR'; Add-HealthFinding 'Reorg' 'Error' $_.Exception.Message }

    # ---- Phase 5b: local media recovery (find mislabeled media you already have) ----
    try {
        Write-EsdeSection -Title 'Phase 5b - Local Media Recovery' -Category 'Media'
        foreach ($sys in $systems) {
            $stems = Get-SystemGameStems -SystemRomDir $sys.RomPath -GamelistPath $sys.Gamelist
            $rec = Invoke-LocalMediaRecovery -SystemMediaDir $sys.MediaDir -RomStems $stems -BackupRoot $BackupDir -Logger $LMedia -DryRun:$DryRun
            $report.Media.Recovered += $rec
        }
        & $LMedia "Local media recovered (re-matched to ROMs): $($report.Media.Recovered)." 'SUCCESS'
    } catch { & $LMedia "Phase 5b error: $($_.Exception.Message)" 'ERROR'; Add-HealthFinding 'Recovery' 'Error' $_.Exception.Message }

    # ---- Phase 5c: media format/extension repair (+ optional ffmpeg frame grab) ----
    try {
        Write-EsdeSection -Title 'Phase 5c - Media Format Repair' -Category 'Media'
        foreach ($sys in $systems) {
            $report.Audit.ExtensionsFixed += (Repair-MediaExtensions -SystemMediaDir $sys.MediaDir -BackupRoot $BackupDir -Logger $LMedia -DryRun:$DryRun)
        }
        & $LMedia "Mislabeled image extensions fixed: $($report.Audit.ExtensionsFixed)." 'INFO'
        if ($GenerateMedia) {
            if (Test-FfmpegAvailable) {
                foreach ($sys in $systems) { $report.Audit.ScreenshotsGenerated += (Invoke-VideoFrameForMissingScreens -SystemMediaDir $sys.MediaDir -Logger $LMedia -DryRun:$DryRun) }
                & $LMedia "Screenshots generated from video (ffmpeg): $($report.Audit.ScreenshotsGenerated)." 'SUCCESS'
            } else { & $LMedia "ffmpeg not found; skipping video frame extraction (install ffmpeg to enable)." 'WARN' }
        }
    } catch { & $LMedia "Phase 5c error: $($_.Exception.Message)" 'ERROR'; Add-HealthFinding 'MediaFormat' 'Error' $_.Exception.Message }

    # ---- Phase 5d: media integrity (quarantine corrupt, fix extension-less) ----
    try {
        Write-EsdeSection -Title 'Phase 5d - Media Integrity' -Category 'Media'
        foreach ($sys in $systems) {
            $mi = Test-MediaIntegrity -SystemMediaDir $sys.MediaDir -BackupRoot $BackupDir -Logger $LMedia -DryRun:$DryRun
            $report.Audit.IntegrityQuarantined += $mi.Quarantined
            $report.Audit.IntegrityFixed += $mi.Fixed
        }
        & $LMedia "Integrity: $($report.Audit.IntegrityQuarantined) corrupt quarantined, $($report.Audit.IntegrityFixed) extension-less fixed." 'INFO'
    } catch { & $LMedia "Phase 5d error: $($_.Exception.Message)" 'ERROR'; Add-HealthFinding 'MediaIntegrity' 'Error' $_.Exception.Message }

    # ---- Phase 5e: media filename hygiene ----
    try {
        Write-EsdeSection -Title 'Phase 5e - Media Filename Hygiene' -Category 'Media'
        foreach ($sys in $systems) { $report.Audit.MediaNamesFixed += (Repair-MediaFilenames -SystemMediaDir $sys.MediaDir -BackupRoot $BackupDir -Logger $LMedia -DryRun:$DryRun) }
        $report.Audit.CrossSystemMediaDup = (Find-CrossSystemMediaDup -MediaDir $Layout.MediaDir)
        & $LMedia "Filename hygiene: $($report.Audit.MediaNamesFixed) renamed; $($report.Audit.CrossSystemMediaDup) image(s) reused across 3+ systems." 'INFO'
    } catch { & $LMedia "Phase 5e error: $($_.Exception.Message)" 'ERROR'; Add-HealthFinding 'MediaHygiene' 'Error' $_.Exception.Message }

    # ---- Phase 6: metadata repair (self-heals malformed gamelists) ----
    try {
        Write-EsdeSection -Title 'Phase 6 - Metadata Repair' -Category 'Metadata'
        foreach ($sys in $systems) {
            if (-not (Test-Path -LiteralPath $sys.Gamelist)) { continue }
            if (-not (Test-XmlWellFormed -Path $sys.Gamelist)) {
                Repair-XmlFile -Path $sys.Gamelist -BackupRoot $BackupDir -Logger $LMeta -DryRun:$DryRun | Out-Null
            }
            $st = Repair-Gamelist -GamelistPath $sys.Gamelist -MediaDir $sys.MediaDir -BackupRoot $BackupDir -Logger $LMeta -DryRun:$DryRun
            $report.Metadata.PerSystem += @{ System=$sys.Name; Games=$st.Games; Duplicates=$st.Duplicates; Repaired=$st.Repaired; Removed=$st.Removed; Invalid=$st.Invalid }
        }
    } catch { & $LMeta "Phase 6 error: $($_.Exception.Message)" 'ERROR'; Add-HealthFinding 'Metadata' 'Error' $_.Exception.Message }

    # ---- Phase 6b: gamelist metadata enrichment (opt-in: -EnrichMeta) ----
    try {
        Write-EsdeSection -Title 'Phase 6b - Metadata Enrichment' -Category 'Metadata'
        if ($EnrichMeta) {
            foreach ($sys in $systems) {
                $en = Optimize-GamelistMetadata -GamelistPath $sys.Gamelist -SystemRomDir $sys.RomPath -BackupRoot $BackupDir -Logger $LMeta -DryRun:$DryRun
                $report.Audit.Enriched += ($en.Filled + $en.SortNames + $en.Relativized + $en.Hidden)
            }
            & $LMeta "Metadata enrichment applied: $($report.Audit.Enriched) field change(s)." 'SUCCESS'
        } else { & $LMeta "Metadata enrichment skipped (pass /enrich to enable)." 'INFO' }
        foreach ($sys in $systems) {
            $sr = Get-ScrapeRatio -SystemName $sys.Name -GamelistPath $sys.Gamelist
            if ($sr.Total -gt 0) { $report.Audit.ScrapeRatio += @{ System=$sr.System; Total=$sr.Total; Scraped=$sr.Scraped; Percent=$sr.Percent; DuplicateNames=$sr.DuplicateNames } }
        }
    } catch { & $LMeta "Phase 6b error: $($_.Exception.Message)" 'ERROR'; Add-HealthFinding 'Enrich' 'Error' $_.Exception.Message }

    # ---- Phase 6c: gamelist quality (m3u check; sanity/unlisted under /enrich) ----
    try {
        Write-EsdeSection -Title 'Phase 6c - Gamelist Quality' -Category 'Metadata'
        foreach ($sys in $systems) { $report.Audit.BrokenM3u += (Test-M3uPlaylists -SystemRomDir $sys.RomPath) }
        if ($EnrichMeta) {
            foreach ($sys in $systems) {
                $report.Audit.SanityFixed   += (Repair-MetadataSanity -GamelistPath $sys.Gamelist -BackupRoot $BackupDir -Logger $LMeta -DryRun:$DryRun)
                $report.Audit.UnlistedAdded += (Add-UnlistedGames -GamelistPath $sys.Gamelist -SystemRomDir $sys.RomPath -BackupRoot $BackupDir -Logger $LMeta -DryRun:$DryRun)
            }
        }
        & $LMeta "Gamelist quality: $($report.Audit.BrokenM3u) broken .m3u, $($report.Audit.SanityFixed) sanity fix(es), $($report.Audit.UnlistedAdded) unlisted ROM(s) added." 'INFO'
    } catch { & $LMeta "Phase 6c error: $($_.Exception.Message)" 'ERROR'; Add-HealthFinding 'GamelistQuality' 'Error' $_.Exception.Message }

    # ---- Phase 7: duplicate detection ----
    try {
        Write-EsdeSection -Title 'Phase 7 - Duplicate Detection' -Category 'Media'
        $dup = Find-DuplicateMedia -MediaDir $Layout.MediaDir -CacheFile (Join-Path $WorkRoot 'mediahash.cache')
        & $LMedia "Hashed $($dup.TotalFiles) media file(s): $($dup.DuplicateFiles) duplicate(s), $([math]::Round($dup.ReclaimableBytes/1MB,2)) MB reclaimable." 'INFO'
        $removed = Invoke-DuplicateCleanup -Groups @($dup.Groups) -BackupRoot $BackupDir -Logger $LMedia -DryRun:$DryRun
        if ($removed -gt 0) { & $LMedia "Removed $removed redundant same-folder duplicate(s)." 'SUCCESS' }
        $report.Duplicates = @{ Groups = @($dup.Groups); TotalFiles=$dup.TotalFiles; DuplicateFiles=$dup.DuplicateFiles; ReclaimableBytes=$dup.ReclaimableBytes }
    } catch { & $LMedia "Phase 7 error: $($_.Exception.Message)" 'ERROR'; Add-HealthFinding 'Duplicates' 'Error' $_.Exception.Message }

    # ---- Phase 8: missing media analysis + scrape-list export ----
    try {
        Write-EsdeSection -Title 'Phase 8 - Missing Media Analysis' -Category 'Media'
        $missingPerSystem = @()
        foreach ($sys in $systems) {
            $mm = Get-MissingMediaForSystem -SystemName $sys.Name -SystemRomDir $sys.RomPath -SystemMediaDir $sys.MediaDir -GamelistPath $sys.Gamelist
            $missingPerSystem += $mm
            $report.MissingMedia.PerSystem += @{ System=$mm.System; Games=$mm.Games; Totals=$mm.Totals }
            & $LMedia "$($sys.Name): $($mm.Games) game(s); missing covers=$($mm.Totals.covers) videos=$($mm.Totals.videos) ss=$($mm.Totals.screenshots)." 'INFO'
            $scrapeFile = Join-Path $ReportsDir ("scrapelist_{0}.txt" -f $sys.Name)
            if (-not $DryRun) { Export-ScrapeList -MissingResult $mm -SystemRomDir $sys.RomPath -OutFile $scrapeFile | Out-Null }
        }
    } catch { & $LMedia "Phase 8 error: $($_.Exception.Message)" 'ERROR'; Add-HealthFinding 'MissingMedia' 'Error' $_.Exception.Message }

    # ---- Phase 8b: deep media audit (coverage, disk usage, consistency, stats) ----
    try {
        Write-EsdeSection -Title 'Phase 8b - Media Audit' -Category 'Media'
        foreach ($sys in $systems) {
            $stems = Get-SystemGameStems -SystemRomDir $sys.RomPath -GamelistPath $sys.Gamelist
            $cov = Get-MediaCoverage -SystemName $sys.Name -RomStems $stems -SystemMediaDir $sys.MediaDir
            $report.Audit.MediaCoverage += @{ System=$sys.Name; Covers=$cov.Coverage.covers.Percent; Screenshots=$cov.Coverage.screenshots.Percent; Videos=$cov.Coverage.videos.Percent; Marquees=$cov.Coverage.marquees.Percent }
            $du = Get-MediaDiskUsage -SystemName $sys.Name -SystemMediaDir $sys.MediaDir
            $report.Audit.DiskUsage += @{ System=$sys.Name; MB=[math]::Round($du.TotalBytes/1MB,1) }
            $report.Audit.OversizedMedia += @(Get-OversizedMedia -SystemMediaDir $sys.MediaDir).Count
            $va = Get-VideoAudit -SystemMediaDir $sys.MediaDir
            $report.Audit.NonFriendlyVideos += @($va.NonFriendly).Count
            $cons = Get-RomGamelistConsistency -SystemRomDir $sys.RomPath -GamelistPath $sys.Gamelist
            if (@($cons.OrphanEntries).Count -gt 0 -or @($cons.Unlisted).Count -gt 0) {
                $report.Audit.Consistency += @{ System=$sys.Name; OrphanEntries=@($cons.OrphanEntries).Count; Unlisted=@($cons.Unlisted).Count }
            }
            $ps = Get-PlayStats -SystemName $sys.Name -GamelistPath $sys.Gamelist
            if ($ps.Favorites -gt 0 -or $ps.Played -gt 0) { $report.Audit.PlayStats += $ps }
            $rd = @(Get-RegionDuplicates -RomStems $stems)
            if ($rd.Count -gt 0) { $report.Audit.RegionDuplicates += @{ System=$sys.Name; Groups=$rd.Count } }
        }
        $totalMB = 0.0; foreach ($d in $report.Audit.DiskUsage) { $totalMB += [double]$d.MB }
        & $LMedia "Media audit: $([math]::Round($totalMB,1)) MB total, $($report.Audit.OversizedMedia) oversized, $($report.Audit.NonFriendlyVideos) non-mp4 video(s)." 'SUCCESS'
    } catch { & $LMedia "Phase 8b error: $($_.Exception.Message)" 'ERROR'; Add-HealthFinding 'MediaAudit' 'Error' $_.Exception.Message }

    # ---- Phase 8c: ROM library analysis + multi-disc playlists ----
    try {
        Write-EsdeSection -Title 'Phase 8c - ROM Library' -Category 'Media'
        foreach ($sys in $systems) {
            $rl = Get-RomLibraryStats -SystemName $sys.Name -SystemRomDir $sys.RomPath
            if ($rl.Count -gt 0) { $report.Audit.RomStats += @{ System=$rl.System; Count=$rl.Count; MB=[math]::Round($rl.TotalBytes/1MB,1); Compressed=$rl.Compressed; ZeroByte=@($rl.ZeroByte).Count } }
            $report.Audit.MultiDiscPlaylists += (New-MultiDiscPlaylists -SystemRomDir $sys.RomPath -Logger $LMedia -DryRun:$DryRun)
            $ca = Get-CompressionAdvisory -SystemRomDir $sys.RomPath
            if ($ca.Count -gt 0) { $report.Audit.CompressionAdvisory += @{ System=$sys.Name; Files=$ca.Count; MB=[math]::Round($ca.ApproxBytes/1MB,1) } }
        }
        $report.Audit.MediaTypeTotals = (Get-MediaTypeTotals -MediaDir $Layout.MediaDir)
        $report.Audit.TopLargest = @(Get-TopLargestMedia -MediaDir $Layout.MediaDir -Top 25)
        $totalRoms = 0; foreach ($r in $report.Audit.RomStats) { $totalRoms += [int]$r.Count }
        & $LMedia "ROM library: $totalRoms ROM(s) across $(@($report.Audit.RomStats).Count) system(s); $($report.Audit.MultiDiscPlaylists) multi-disc playlist(s) created." 'SUCCESS'
    } catch { & $LMedia "Phase 8c error: $($_.Exception.Message)" 'ERROR'; Add-HealthFinding 'RomLibrary' 'Error' $_.Exception.Message }

    # ---- Phase 8d: library analytics (stats, dup ROMs, extensions, saves, manifest) ----
    try {
        Write-EsdeSection -Title 'Phase 8d - Library Analytics' -Category 'Media'
        $report.Audit.Statistics = (Get-LibraryStatistics -Systems $systems)
        $extMap = ConvertTo-Ht $mediaDefs.systemExtensions
        $report.Audit.BadExtensions = @(Test-RomExtensions -Systems $systems -ExtMap $extMap)
        $dupRomTotal = 0; $orphanSaveTotal = 0
        foreach ($sys in $systems) {
            $dupRomTotal += @(Find-DuplicateRoms -SystemRomDir $sys.RomPath).Count
            $orphanSaveTotal += @(Get-OrphanedSaves -SystemRomDir $sys.RomPath).Count
        }
        $report.Audit.DuplicateRoms = $dupRomTotal
        $report.Audit.OrphanSaves = $orphanSaveTotal
        $report.Audit.CheatFiles = (Get-CheatFiles -Roots @(@(Get-EmuRoots) + $Layout.RomDir))
        $report.Audit.CustomSystemSuggestions = @(Get-CustomSystemsSuggestion -Layout $Layout -Systems $systems)
        $report.Audit.ManifestSystems = (Export-LibraryManifest -Systems $systems -OutFile (Join-Path $ReportsDir 'Library_Manifest.json'))
        $st = $report.Audit.Statistics
        & $LMedia "Analytics: $($st.TotalGames) games, $($st.TotalPlaytimeHours)h played, $dupRomTotal dup ROM set(s), $orphanSaveTotal orphan save(s), $($report.Audit.CheatFiles) cheat file(s)." 'SUCCESS'
    } catch { & $LMedia "Phase 8d error: $($_.Exception.Message)" 'ERROR'; Add-HealthFinding 'Analytics' 'Error' $_.Exception.Message }

    # ---- Phase 8e: extended analytics + DAT verification ----
    try {
        Write-EsdeSection -Title 'Phase 8e - Extended Analytics' -Category 'Media'
        $report.Audit.CrossSystemDuplicates = @(Find-CrossSystemDuplicates -Systems $systems).Count
        $report.Audit.RegionDistribution = (Get-RegionDistribution -Systems $systems)
        $report.Audit.Completion = (Get-CompletionStats -Systems $systems)
        $report.Audit.BadArchives = (Test-RomArchives -Systems $systems)
        $report.Audit.PlaytimeTop = @(Get-PlaytimeLeaderboard -Systems $systems -Top 10)
        $report.Audit.NewestAdditions = @(Get-NewestAdditions -Systems $systems -Top 15)
        # DAT-based verification only runs when the user supplies .dat files.
        $datDir = Find-DatDirectory -RomDir $Layout.RomDir -WorkRoot $WorkRoot
        if ($datDir) {
            $datSet = Get-DatCrcSet -DatDir $datDir
            & $LMedia "DAT verification: $($datSet.Games) known entries from $datDir." 'INFO'
            $report.Audit.DatVerify = @(Test-RomsAgainstDat -Systems $systems -KnownCrcs $datSet.Crcs -Logger $LMedia)
        } else { & $LMedia "No DAT files found (put No-Intro/Redump .dat in a 'dats' folder to enable ROM verification)." 'INFO' }
        $comp = $report.Audit.Completion
        & $LMedia "Extended: $($report.Audit.CrossSystemDuplicates) cross-system dup(s), $($comp.PlayedPercent)% played, $($report.Audit.BadArchives) bad archive(s)." 'SUCCESS'
    } catch { & $LMedia "Phase 8e error: $($_.Exception.Message)" 'ERROR'; Add-HealthFinding 'ExtAnalytics' 'Error' $_.Exception.Message }

    # ---- Phase 8f: library insights (stats, abandoned, savestates, diff, forecast) ----
    try {
        Write-EsdeSection -Title 'Phase 8f - Library Insights' -Category 'Media'
        $report.Audit.PerSystemStats = @(Get-PerSystemGamelistStats -Systems $systems)
        $report.Audit.AbandonedGames = (Get-AbandonedGames -Systems $systems)
        $report.Audit.Savestates = (Get-SavestateInventory -Roots @(@(Get-EmuRoots) + $Layout.RomDir))
        $report.Audit.GamelistDiff = @(Get-GamelistDiff -Systems $systems -BackupRoot $BackupDir)
        $report.Audit.DiskForecastMB = (Get-DiskSpaceForecast -MediaDir $Layout.MediaDir -MissingPerSystem @($report.MissingMedia.PerSystem))
        $report.Audit.NetworkPaths = @(Test-NetworkPaths -Paths @($Layout.RomDir, $Layout.MediaDir, $Layout.DataDir))
        foreach ($np in $report.Audit.NetworkPaths) { Add-HealthFinding 'Network' 'Warning' "On a network share (slower): $np" }
        & $LMedia "Insights: $($report.Audit.AbandonedGames) abandoned, $($report.Audit.Savestates) save-state(s), ~$($report.Audit.DiskForecastMB) MB to fill missing media." 'SUCCESS'
    } catch { & $LMedia "Phase 8f error: $($_.Exception.Message)" 'ERROR'; Add-HealthFinding 'Insights' 'Error' $_.Exception.Message }

    # ---- Phase 9: media download (missing only) ----
    try {
        Write-EsdeSection -Title 'Phase 9 - Media Download (missing only)' -Category 'Downloads'
        if (-not $SkipDownload) {
            if (Test-ScraperCredentials) {
                foreach ($sys in $systems) {
                    $mm = $missingPerSystem | Where-Object { $_.System -eq $sys.Name } | Select-Object -First 1
                    if (-not $mm -or @($mm.Records).Count -eq 0) { continue }
                    $d = Invoke-MediaDownloadForSystem -SystemRomDir $sys.RomPath -SystemMediaDir $sys.MediaDir -MissingResult $mm -Logger $LDown -DryRun:$DryRun
                    & $LDown "$($sys.Name): attempted=$($d.Attempted) downloaded=$($d.Downloaded) skipped=$($d.Skipped)." 'INFO'
                }
            } else {
                & $LDown "ScreenScraper credentials not set; downloads skipped (set SS_DEVID/SS_DEVPASSWORD/SS_USER/SS_PASSWORD). Scrape lists exported to Reports." 'WARN'
            }
        } else { & $LDown "Media download skipped by request." 'INFO' }
    } catch { & $LDown "Phase 9 error: $($_.Exception.Message)" 'ERROR'; Add-HealthFinding 'Downloads' 'Error' $_.Exception.Message }

    # ---- Phase 10: orphan + empty-folder cleanup ----
    try {
        Write-EsdeSection -Title 'Phase 10 - Cleanup' -Category 'Media'
        foreach ($sys in $systems) {
            $stems = Get-SystemGameStems -SystemRomDir $sys.RomPath -GamelistPath $sys.Gamelist
            Invoke-OrphanCleanup -SystemName $sys.Name -SystemRomDir $sys.RomPath -SystemMediaDir $sys.MediaDir -RomStems $stems -BackupRoot $BackupDir -Logger $LMedia -DryRun:$DryRun | Out-Null
        }
        $emptyRemoved = Remove-EmptyFolders -Root $Layout.MediaDir -DryRun:$DryRun
        & $LMedia "Removed $emptyRemoved empty media folder(s)." 'INFO'
    } catch { & $LMedia "Phase 10 error: $($_.Exception.Message)" 'ERROR'; Add-HealthFinding 'Cleanup' 'Error' $_.Exception.Message }

    # ---- Phase 11: emulator graphics optimization (GPU-aware, self-creates configs) ----
    try {
        Write-EsdeSection -Title 'Phase 11 - Emulator Graphics Optimization' -Category 'Optimization'
        if (-not $SkipOptimize) {
            $emuRoots = @(Get-EmuRoots)
            if ($emuRoots.Count -gt 0) {
                & $LOpt "ES-DE emulator root(s): $($emuRoots -join '; ') (GPU vendor: $($hw.GpuVendor))" 'INFO'
                $emulators = @(Get-EsdeEmulators -Roots $emuRoots -Definitions $emuDefs)
                $installedEmuIds = @($emulators | Where-Object { $_.Installed } | ForEach-Object { $_.Id })
                $report.EmulatorIntegrity = @(Test-EmulatorInstalls -Emulators $emulators -Logger $LOpt)
                foreach ($e in ($emulators | Where-Object { $_.Installed })) {
                    if ($DryRun) { if ($e.Known -and $e.Supports4K) { & $LOpt "[DRY-RUN] Would optimize $($e.DisplayName)." 'INFO' }; continue }
                    $r = Invoke-EmulatorOptimization -Emulator $e -Tier $tier -TargetWidth $profile.TargetWidth -TargetHeight $profile.TargetHeight -BackupRoot $BackupDir -Logger $LOpt -GpuVendor $hw.GpuVendor
                    $report.Optimization += @{ Emulator=$e.DisplayName; Result=$(if($r.Success){'optimized'}else{$r.Message}) }
                }
            } else { & $LOpt "No ES-DE emulator folder found; skipping graphics optimization." 'WARN' }
        } else { & $LOpt "Optimization skipped by request." 'INFO' }
    } catch { & $LOpt "Phase 11 error: $($_.Exception.Message)" 'ERROR'; Add-HealthFinding 'Optimization' 'Error' $_.Exception.Message }

    # ---- Phase 11c: extra emulator tuning + config archive ----
    try {
        Write-EsdeSection -Title 'Phase 11c - Emulator Tuning & Config Archive' -Category 'Optimization'
        $emuRootsT = @(Get-EmuRoots)
        $report.Audit.ConfigsArchived = (Backup-AllEmulatorConfigs -EmulatorRoots $emuRootsT -BackupRoot $BackupDir -Logger $LOpt -DryRun:$DryRun)
        if ($TuneEsde) {
            $raExeT = Find-RetroArchExe
            if ($raExeT) { $report.Audit.RetroArchExtras = (Set-RetroArchExtras -RetroArchDir (Split-Path $raExeT -Parent) -BackupRoot $BackupDir -Logger $LOpt -DryRun:$DryRun) }
        } else { & $LOpt "RetroArch extra tuning skipped (pass /tune to enable)." 'INFO' }
    } catch { & $LOpt "Phase 11c error: $($_.Exception.Message)" 'ERROR'; Add-HealthFinding 'EmulatorTuning' 'Error' $_.Exception.Message }

    # ---- Phase 11d: advanced RetroArch tuning (shader + latency; /tune) ----
    try {
        Write-EsdeSection -Title 'Phase 11d - Advanced Tuning' -Category 'Optimization'
        if ($TuneEsde) {
            $raExeA = Find-RetroArchExe
            if ($raExeA) {
                $raDirA = Split-Path $raExeA -Parent
                $report.Audit.ShaderApplied = (Set-RetroArchShaderPreset -RetroArchDir $raDirA -BackupRoot $BackupDir -Logger $LOpt -DryRun:$DryRun)
                $report.Audit.LatencyTuned  = (Set-RetroArchLatency -RetroArchDir $raDirA -Tier $tier -BackupRoot $BackupDir -Logger $LOpt -DryRun:$DryRun)
            } else { & $LOpt "RetroArch not found; advanced tuning skipped." 'INFO' }
        } else { & $LOpt "Advanced tuning skipped (pass /tune to enable)." 'INFO' }
    } catch { & $LOpt "Phase 11d error: $($_.Exception.Message)" 'ERROR'; Add-HealthFinding 'AdvancedTuning' 'Error' $_.Exception.Message }

    # ---- Phase 11e: RA features/hotkeys + RetroArch playlists ----
    try {
        Write-EsdeSection -Title 'Phase 11e - RA Features & Playlists' -Category 'Optimization'
        $raExeE = Find-RetroArchExe
        if ($raExeE) {
            $raDirE = Split-Path $raExeE -Parent
            $report.Audit.Playlists = (New-RetroArchPlaylists -Systems $systems -RetroArchDir $raDirE -Logger $LOpt -DryRun:$DryRun)
            if ($TuneEsde) {
                $report.Audit.RaFeatures = (Set-RetroArchFeatures -RetroArchDir $raDirE -BackupRoot $BackupDir -Logger $LOpt -DryRun:$DryRun)
                $emuAll = @(Get-EsdeEmulators -Roots @(Get-EmuRoots) -Definitions $emuDefs)
                $report.Audit.StandaloneHotkeys = (Set-StandaloneHotkeys -Emulators $emuAll -BackupRoot $BackupDir -Logger $LOpt -DryRun:$DryRun)
            }
        } else { & $LOpt "RetroArch not found; playlists/features skipped." 'INFO' }
    } catch { & $LOpt "Phase 11e error: $($_.Exception.Message)" 'ERROR'; Add-HealthFinding 'RaFeatures' 'Error' $_.Exception.Message }

    # ---- Phase 11f: CHD compression (opt-in: /compress; needs chdman) ----
    try {
        Write-EsdeSection -Title 'Phase 11f - CHD Compression' -Category 'Optimization'
        if ($Compress) {
            $chdman = Find-Chdman -EmulatorRoots @(Get-EmuRoots)
            if ($chdman) {
                & $LOpt "Using chdman: $chdman" 'INFO'
                foreach ($sys in $systems) {
                    $cr = Invoke-ChdCompression -SystemRomDir $sys.RomPath -Chdman $chdman -BackupRoot $BackupDir -Logger $LOpt -DryRun:$DryRun
                    $report.Audit.ChdConverted += $cr.Converted; $report.Audit.ChdSavedMB += $cr.SavedMB
                }
                & $LOpt "CHD: converted $($report.Audit.ChdConverted) image(s), saved ~$($report.Audit.ChdSavedMB) MB." 'SUCCESS'
            } else { & $LOpt "chdman not found; install MAME tools or place chdman.exe under an emulator folder." 'WARN' }
        } else { & $LOpt "CHD compression skipped (pass /compress to enable)." 'INFO' }
    } catch { & $LOpt "Phase 11f error: $($_.Exception.Message)" 'ERROR'; Add-HealthFinding 'ChdCompress' 'Error' $_.Exception.Message }

    # ---- Phase 11b: missing-emulator gap analysis ----
    try {
        Write-EsdeSection -Title 'Phase 11b - Missing Emulator Analysis' -Category 'Optimization'
        $gaps = @(Get-EmulatorGaps -Systems $systems -InstalledIds $installedEmuIds -SystemMap $sysEmuMap)
        $report.EmulatorGaps = $gaps
        foreach ($g in ($gaps | Where-Object { $_.Missing })) {
            & $LOpt "System '$($g.System)' has ROMs but no installed emulator. Recommended: $($g.Recommended) (options: $($g.Required -join ', '))." 'WARN'
            Add-HealthFinding 'EmulatorGap' 'Warning' "$($g.System): install $($g.Recommended)"
        }
        $gapCount = @($gaps | Where-Object { $_.Missing }).Count
        & $LOpt "Missing-emulator analysis: $gapCount system(s) need an emulator." $(if ($gapCount -gt 0) { 'WARN' } else { 'SUCCESS' })
    } catch { & $LOpt "Phase 11b error: $($_.Exception.Message)" 'ERROR'; Add-HealthFinding 'EmulatorGap' 'Error' $_.Exception.Message }

    # ---- Phase 12: controllers (ES-DE input + RetroArch + SDL gamecontrollerdb) ----
    try {
        Write-EsdeSection -Title 'Phase 12 - Controller Configuration' -Category 'Controllers'
        $vendorMap = ConvertTo-Ht $emuDefs.controllerVendors
        $controllers = @(Get-ConnectedControllers -VendorMap $vendorMap)
        if ($controllers.Count -eq 0) { & $LCtl "No controllers connected. Use Watch mode for hotswap." 'WARN' }
        else {
            $port = 0
            foreach ($c in $controllers) { $port++; & $LCtl ("Player {0}: {1} [{2}] {3}/{4}/{5}" -f $port, $c.FriendlyName, $c.Vendor, $c.Family, $c.ApiType, $c.Connection) 'INFO' }
            if (-not $DryRun) { Set-EsdeControllers -Controllers $controllers } else { foreach($c in $controllers){ & $LCtl "[DRY-RUN] Would configure $($c.FriendlyName)." 'INFO' } }
            $report.Controllers = @($controllers | ForEach-Object { @{ Name=$_.FriendlyName; Vendor=$_.Vendor; Family=$_.Family; Api=$_.ApiType; Connection=$_.Connection; VidPid="$($_.Vid):$($_.Pid)" } })
        }
    } catch { & $LCtl "Phase 12 error: $($_.Exception.Message)" 'ERROR'; Add-HealthFinding 'Controllers' 'Error' $_.Exception.Message }

    # ---- Phase 13: advanced BIOS validation + relocate/propagate (no downloads) ----
    try {
        Write-EsdeSection -Title 'Phase 13 - BIOS Validation' -Category 'Main'
        $biosCandidates = New-Object System.Collections.Generic.List[string]
        $biosCandidates.Add((Join-Path (Split-Path $Layout.RomDir -Parent) 'bios'))
        $biosCandidates.Add((Join-Path $Layout.RomDir 'bios'))
        $biosCandidates.Add((Join-Path $Layout.DataDir 'bios'))
        $raExe2 = Find-RetroArchExe
        if ($raExe2) { $biosCandidates.Add((Join-Path (Split-Path $raExe2 -Parent) 'system')) }
        foreach ($emuRoot3 in (Get-EmuRoots)) {
            foreach ($sub in @('pcsx2\bios','duckstation\bios','rpcs3\dev_flash','flycast\data','dolphin\Sys','bios')) {
                $biosCandidates.Add((Join-Path $emuRoot3 $sub))
            }
        }
        $allBiosDirs = @($biosCandidates | Where-Object { $_ } | Select-Object -Unique)
        $biosDir = $null
        foreach ($cand in $allBiosDirs) { if (Test-Path -LiteralPath $cand) { $biosDir = $cand; break } }
        if (-not $biosDir) { $biosDir = Join-Path (Split-Path $Layout.RomDir -Parent) 'bios' }

        $bd = @(Test-BiosAdvanced -BiosDir $biosDir -Requirements @($mediaDefs.biosRequirements) -Logger $LMain)
        # Fix directions: relocate wrong-placed BIOS and propagate present ones to
        # every emulator BIOS folder. Copyrighted BIOS are NEVER downloaded.
        $fix = Invoke-BiosRelocate -Records $bd -CanonicalDir $biosDir -CandidateDirs $allBiosDirs -BackupRoot $BackupDir -Logger $LMain -DryRun:$DryRun
        if (-not $DryRun -and ($fix.Relocated -gt 0 -or $fix.Propagated -gt 0)) {
            $bd = @(Test-BiosAdvanced -BiosDir $biosDir -Requirements @($mediaDefs.biosRequirements) -Logger $LMain)
        }
        $report.BiosDetailed = $bd
        $report.Bios = @($bd | Where-Object { $_.Status -ne 'Present' } | ForEach-Object { @{ File=$_.File; System="$($_.System) [$($_.Status)]" } })
        $stillMissing = @($bd | Where-Object { $_.Status -eq 'Missing' }).Count
        if ($stillMissing -gt 0) {
            & $LMain "$stillMissing BIOS file(s) are genuinely missing. These are copyrighted console firmware and are NOT downloaded - provide your own dumps in $biosDir (see Bios_Report.html for filenames/locations)." 'WARN'
            Add-HealthFinding 'BIOS' 'Warning' "$stillMissing BIOS missing - supply legally-obtained dumps in $biosDir"
        }
    } catch { & $LMain "Phase 13 error: $($_.Exception.Message)" 'ERROR'; Add-HealthFinding 'BIOS' 'Error' $_.Exception.Message }

    # ---- Phase 13b: ES-DE environment audit ----
    try {
        Write-EsdeSection -Title 'Phase 13b - Environment Audit' -Category 'Main'
        $sv = Get-SuiteVersion; $report.Audit.SuiteVersion = "$($sv.Version) ($($sv.Built))"
        $report.Audit.Online   = Test-Online
        $report.Audit.Language = Get-EsdeLanguage -SettingsFile $Layout.SettingsFile
        $ess = Test-EsSystemsXml -Layout $Layout
        $report.Audit.EsSystems = @{ Present=$ess.Present; Valid=$ess.Valid; Count=$ess.Count }
        if ($ess.Present -and -not $ess.Valid) { Add-HealthFinding 'es_systems' 'Warning' "Malformed custom es_systems.xml" }
        $th = Get-EsdeThemes -Layout $Layout
        $report.Audit.Themes = @{ Installed=@($th.Installed); Active=$th.Active; ActivePresent=$th.ActivePresent }
        if ($th.Active -and -not $th.ActivePresent) { & $LMain "Active theme '$($th.Active)' is not installed." 'WARN'; Add-HealthFinding 'Theme' 'Warning' "Active theme missing: $($th.Active)" }
        $report.Audit.Collections = @(Test-Collections -Layout $Layout)
        $installedDisplay = @($report.EmulatorIntegrity | ForEach-Object { $_.DisplayName })
        $report.Audit.AltEmulators = @(Get-AltEmulatorAudit -Systems $systems -InstalledDisplayNames $installedDisplay)
        foreach ($ae in ($report.Audit.AltEmulators | Where-Object { -not $_.Installed })) {
            & $LMain "System '$($ae.System)' is set to use '$($ae.Label)' but that emulator was not detected." 'WARN'
            Add-HealthFinding 'AltEmulator' 'Warning' "$($ae.System): $($ae.Label) not installed"
        }
        $report.Audit.EmptySystems = @(Get-EmptySystemsAdvisory -Systems $systems)
        if (($TuneEsde) -and (Test-Path -LiteralPath $Layout.SettingsFile)) {
            $report.Audit.SettingsTuned = (Optimize-EsdeSettings -SettingsFile $Layout.SettingsFile -Hardware $hw -BackupRoot $BackupDir -Logger $LMain -DryRun:$DryRun)
            $report.Audit.UxApplied = (Optimize-EsdeUxSettings -SettingsFile $Layout.SettingsFile -BackupRoot $BackupDir -Logger $LMain -DryRun:$DryRun)
            $report.Audit.UxTuned = ($report.Audit.UxApplied -gt 0)
        }
        $report.Audit.ControllerVerify = Test-ControllerConfigApplied -Layout $Layout
        if ($HashRoms) {
            foreach ($sys in $systems) {
                $hf = Join-Path $ReportsDir ("romhashes_{0}.json" -f $sys.Name)
                if (-not $DryRun) { $report.Audit.RomsHashed += (Export-RomHashManifest -SystemName $sys.Name -SystemRomDir $sys.RomPath -OutFile $hf) }
            }
            & $LMain "ROM hash manifest: $($report.Audit.RomsHashed) ROM(s) hashed." 'SUCCESS'
        }
        & $LMain "Environment audit: online=$($report.Audit.Online), language=$($report.Audit.Language), themes=$(@($th.Installed).Count), es_systems=$($ess.Count), empty systems=$(@($report.Audit.EmptySystems).Count)." 'SUCCESS'
    } catch { & $LMain "Phase 13b error: $($_.Exception.Message)" 'ERROR'; Add-HealthFinding 'EnvAudit' 'Error' $_.Exception.Message }

    # ---- Phase 13c: custom collections + optional 1G1R region hiding ----
    try {
        Write-EsdeSection -Title 'Phase 13c - Collections & 1G1R' -Category 'Main'
        $col = New-EsdeCollections -Systems $systems -CollectionsDir $Layout.Collections -Logger $LMain -DryRun:$DryRun
        $report.Audit.CustomCollections = @{ Favorites=$col.Favorites; Played=$col.Played }
        if ($OneGameOneRegion) {
            foreach ($sys in $systems) {
                $report.Audit.RegionHidden += (Invoke-RegionHide -GamelistPath $sys.Gamelist -BackupRoot $BackupDir -Logger $LMain -DryRun:$DryRun)
            }
            & $LMain "1G1R: hid $($report.Audit.RegionHidden) non-preferred-region duplicate(s)." 'SUCCESS'
        } else { & $LMain "1G1R region hiding skipped (pass /onegame to enable)." 'INFO' }
    } catch { & $LMain "Phase 13c error: $($_.Exception.Message)" 'ERROR'; Add-HealthFinding 'Collections' 'Error' $_.Exception.Message }

    # ---- Phase 13d: themes + system ops (storage, drift, scheduling, shortcut) ----
    try {
        Write-EsdeSection -Title 'Phase 13d - Themes & System Ops' -Category 'Main'
        if ($Themes) {
            $report.Audit.ThemesInstalled = (Install-EsdeThemes -ThemesDir $Layout.Themes -Logger $LMain -DryRun:$DryRun)
        }
        $report.Audit.ActiveTheme = (Set-ActiveTheme -SettingsFile $Layout.SettingsFile -ThemesDir $Layout.Themes -BackupRoot $BackupDir -Logger $LMain -DryRun:$DryRun)
        $report.Audit.StorageHealth = @(Get-StorageHealth)
        foreach ($d in $report.Audit.StorageHealth) { if ($d.Health -and $d.Health -notmatch '(?i)healthy|ok') { Add-HealthFinding 'Storage' 'Warning' "Disk '$($d.Name)' health: $($d.Health)" } }
        $report.Audit.Telemetry = (Get-SystemTelemetry)
        $report.Audit.ConfigDrift = (Test-ConfigDrift -EmulatorRoots @(Get-EmuRoots) -BackupRoot $BackupDir)
        $report.Audit.LogsRotated = (Invoke-LogRotation -LogsDir $LogsDir -Days 7 -DryRun:$DryRun)
        $report.Audit.Update = (Test-SuiteUpdate -LocalVersion (Get-SuiteVersion).Version)
        if ($report.Audit.Update.UpdateAvailable) { & $LMain "A newer ES-DE Auto Suite version ($($report.Audit.Update.Remote)) is available." 'WARN' }
        if ($Schedule) { $report.Audit.ScheduledTask = (Register-EsdeScheduledTask -LauncherPath $LauncherSelfPath -Logger $LMain -DryRun:$DryRun) }
        if ($Shortcut) { $report.Audit.ShortcutCreated = (New-EsdeShortcut -Target $LauncherSelfPath -ShortcutName 'ES-DE Auto Suite' -Logger $LMain -DryRun:$DryRun) }
        & $LMain "System ops: storage $(@($report.Audit.StorageHealth).Count) disk(s), config drift $($report.Audit.ConfigDrift) file(s), logs rotated $($report.Audit.LogsRotated)." 'SUCCESS'
    } catch { & $LMain "Phase 13d error: $($_.Exception.Message)" 'ERROR'; Add-HealthFinding 'SystemOps' 'Error' $_.Exception.Message }

    # ---- Phase 13e: auto-collections, auto-favorites and portable bundles ----
    try {
        Write-EsdeSection -Title 'Phase 13e - Smart Collections & Bundles' -Category 'Main'
        $records = @(Get-AllGameRecords -Systems $systems)
        $report.Audit.AutoCollections = (New-AutoCollections -Records $records -CollectionsDir $Layout.Collections -Logger $LMain -DryRun:$DryRun)
        if ($AutoFav) { $report.Audit.AutoFavorited = (Set-AutoFavorites -Systems $systems -TopPerSystem 5 -BackupRoot $BackupDir -Logger $LMain -DryRun:$DryRun) }
        $report.Audit.ControllerBundle = (Export-ControllerBundle -Layout $Layout -EmulatorRoots @(Get-EmuRoots) -OutDir (Join-Path $ReportsDir 'controller_bundle') -Logger $LMain -DryRun:$DryRun)
        Export-PortableBundle -Layout $Layout -Systems $systems -OutFile (Join-Path $ReportsDir 'portable.json') | Out-Null
        & $LMain "Smart collections + bundles written (genre/decade/never-played/kids; controller bundle; portable.json)." 'SUCCESS'
    } catch { & $LMain "Phase 13e error: $($_.Exception.Message)" 'ERROR'; Add-HealthFinding 'SmartCollections' 'Error' $_.Exception.Message }

    # ---- Phase 14: reports (incl. health) ----
    try {
        Write-EsdeSection -Title 'Phase 14 - Reports' -Category 'Main'
        $report.Health = @(Get-HealthFindings)
        $report.PhaseResults = @(Get-PhaseResults)
        $report.Warnings = @($report.Health | Where-Object { $_.Status -eq 'Warning' }).Count
        $report.Errors   = @($report.Health | Where-Object { $_.Status -eq 'Error' }).Count
        $report.Audit.HealthScore = (Get-LibraryHealthScore -Report $report)
        & $LMain "Library health score: $($report.Audit.HealthScore)/100." 'SUCCESS'
        Write-EsdeReports -ReportsDir $ReportsDir -Data $report -Logger $LMain
        Export-CsvReports -ReportsDir $ReportsDir -Data $report | Out-Null
        Export-MarkdownSummary -ReportsDir $ReportsDir -Data $report | Out-Null
        Update-RunHistory -WorkRoot $WorkRoot -Summary @{
            Time=$report.GeneratedAt; Tier=$report.Tier; Systems=@($report.Systems).Count
            Migrated=$report.Migration.TotalCopied; Reorganized=$report.Media.TotalMoved
            Duplicates=$report.Duplicates.DuplicateFiles; Enriched=$report.Audit.Enriched
            Playlists=$report.Audit.MultiDiscPlaylists; Errors=$report.Errors; Warnings=$report.Warnings
        } | Out-Null
        & $LMain "Reports: HTML + JSON + CSV (Systems_Summary, Missing_Media) + Summary.md + run history." 'SUCCESS'
    } catch { & $LMain "Phase 14 error: $($_.Exception.Message)" 'ERROR' }

    # ---- Phase 15: git ----
    try {
        if (-not $SkipGit -and -not $DryRun) {
            Write-EsdeSection -Title 'Phase 15 - Git Integration' -Category 'Git'
            $msg = "ES-DE auto suite: $($report.Migration.TotalCopied) migrated, $($report.Media.TotalMoved) reorganized, $(@($systems).Count) systems, tier=$tier."
            Invoke-GitCommitAndPush -RepoPath $Layout.DataDir -CommitMessage $msg -Logger $LGit | Out-Null
        } elseif ($DryRun) { & $LGit "[DRY-RUN] Git skipped." 'INFO' } else { & $LGit "Git skipped by request." 'INFO' }
    } catch { & $LGit "Phase 15 error: $($_.Exception.Message)" 'ERROR'; Add-HealthFinding 'Git' 'Error' $_.Exception.Message }

    Write-EsdeSection -Title 'ES-DE Auto Suite Complete' -Category 'Main'
    & $LMain "Health: $($report.Errors) error(s), $($report.Warnings) warning(s) - all phases ran (self-healing)." $(if ($report.Errors -gt 0) { 'WARN' } else { 'SUCCESS' })
    & $LMain "Done. Logs: $LogsDir | Reports: $ReportsDir | Backups: $BackupDir" 'SUCCESS'
}

function Invoke-EsdeDoctor {
    # Diagnostics + safe self-repair only (no media/emulator/git changes).
    Initialize-Health
    Write-EsdeSection -Title 'ES-DE Auto Suite - Doctor (diagnose & self-repair)' -Category 'Main'
    & $LMain "Data dir: $($Layout.DataDir) | ROM dir: $($Layout.RomDir) | Media dir: $($Layout.MediaDir)" 'INFO'
    $freeGB = Get-FreeSpaceGB -Path $Layout.DataDir
    & $LMain "Free space: $freeGB GB | Work dir writable: $(Test-PathWritable -Path $WorkRoot)" 'INFO'
    Repair-EsdeStructure -Layout $Layout -Logger $LMain -DryRun:$DryRun | Out-Null
    if ((Test-Path -LiteralPath $Layout.SettingsFile) -and -not (Test-XmlWellFormed -Path $Layout.SettingsFile)) {
        Repair-XmlFile -Path $Layout.SettingsFile -BackupRoot $BackupDir -Logger $LMain -DryRun:$DryRun | Out-Null
    }
    $bad = 0
    foreach ($sys in @(Get-EsdeSystems -Layout $Layout)) {
        if ((Test-Path -LiteralPath $sys.Gamelist) -and -not (Test-XmlWellFormed -Path $sys.Gamelist)) {
            Repair-XmlFile -Path $sys.Gamelist -BackupRoot $BackupDir -Logger $LMain -DryRun:$DryRun | Out-Null
            $bad++
        }
    }
    & $LMain "Doctor complete: structure verified, $bad malformed gamelist(s) handled. Findings: $(@(Get-HealthFindings).Count)." 'SUCCESS'
}

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
try {
    $emuDefsForMode = ($script:EmbeddedEmuJson | ConvertFrom-Json)
    switch ($Mode) {
        'Watch'   { Start-EsdeWatcher -EmuDefs $emuDefsForMode }
        'Restore' { Invoke-EsdeRestore }
        'Doctor'  { Invoke-EsdeDoctor }
        default   { Invoke-EsdeSetup }
    }
    exit 0
} catch {
    Write-EsdeLog -Message "FATAL: $($_.Exception.Message)" -Level ERROR -Category 'Main'
    Write-EsdeLog -Message $_.ScriptStackTrace -Level DEBUG -Category 'Main'
    exit 1
}


