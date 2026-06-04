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
        [xml]$xml = Get-Content -LiteralPath $SettingsFile -Raw -Encoding UTF8
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
        }
        $null = [xml]$raw
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
    param([Parameter(Mandatory = $true)][string] $MediaDir)

    $byHash = @{}
    $total  = 0
    if (Test-Path -LiteralPath $MediaDir) {
        Get-ChildItem -LiteralPath $MediaDir -File -Recurse -ErrorAction SilentlyContinue | ForEach-Object {
            $h = Get-FileSha256 -Path $_.FullName
            if (-not $h) { return }
            $total++
            if (-not $byHash.ContainsKey($h)) { $byHash[$h] = New-Object System.Collections.Generic.List[object] }
            $byHash[$h].Add($_)
        }
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
        $reqMd5 = if ($req.PSObject.Properties.Name -contains 'md5' -and $req.md5) { ([string]$req.md5).ToLower() } else { $null }

        if (Test-Path -LiteralPath $expectAt) {
            if ($reqMd5) {
                $actual = Get-FileMd5 -Path $expectAt
                if ($actual -eq $reqMd5) { $status = 'Present'; $detail = 'Present and hash-verified.' }
                else { $status = 'WrongHash'; $detail = "Present but MD5 mismatch (expected $reqMd5, got $actual)." }
            } else { $status = 'Present'; $detail = 'Present (no known hash to verify).' }
        }
        elseif ($allByName.ContainsKey($name.ToLower())) {
            $status = 'WrongLocation'
            $detail = "Found at $($allByName[$name.ToLower()]) but ES-DE expects it at $expectAt."
        }

        if ($status -ne 'Present') { & $Logger "BIOS $status`: $name ($($req.system))" 'WARN' }
        $records.Add([ordered]@{ File = $name; System = $req.system; Status = $status; Detail = $detail; ExpectedAt = $expectAt })
    }

    $present = @($records | Where-Object { $_.Status -eq 'Present' }).Count
    & $Logger "BIOS check: $present/$($records.Count) present and valid." 'INFO'
    return $records.ToArray()
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
        [xml]$xml = Get-Content -LiteralPath $path -Raw -Encoding UTF8
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

    # ---- Phase 7: duplicate detection ----
    try {
        Write-EsdeSection -Title 'Phase 7 - Duplicate Detection' -Category 'Media'
        $dup = Find-DuplicateMedia -MediaDir $Layout.MediaDir
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

    # ---- Phase 13: advanced BIOS validation (MD5 + wrong-location) ----
    try {
        Write-EsdeSection -Title 'Phase 13 - BIOS Validation' -Category 'Main'
        $biosDir = $null
        $biosCandidates = New-Object System.Collections.Generic.List[string]
        $biosCandidates.Add((Join-Path (Split-Path $Layout.RomDir -Parent) 'bios'))
        $biosCandidates.Add((Join-Path $Layout.RomDir 'bios'))
        $biosCandidates.Add((Join-Path $Layout.DataDir 'bios'))
        $raExe2 = Find-RetroArchExe
        if ($raExe2) { $biosCandidates.Add((Join-Path (Split-Path $raExe2 -Parent) 'system')) }
        foreach ($cand in $biosCandidates) { if ($cand -and (Test-Path -LiteralPath $cand)) { $biosDir = $cand; break } }
        if (-not $biosDir) { $biosDir = Join-Path (Split-Path $Layout.RomDir -Parent) 'bios' }
        $bd = @(Test-BiosAdvanced -BiosDir $biosDir -Requirements @($mediaDefs.biosRequirements) -Logger $LMain)
        $report.BiosDetailed = $bd
        $report.Bios = @($bd | Where-Object { $_.Status -ne 'Present' } | ForEach-Object { @{ File=$_.File; System="$($_.System) [$($_.Status)]" } })
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

    # ---- Phase 14: reports (incl. health) ----
    try {
        Write-EsdeSection -Title 'Phase 14 - Reports' -Category 'Main'
        $report.Health = @(Get-HealthFindings)
        $report.PhaseResults = @(Get-PhaseResults)
        $report.Warnings = @($report.Health | Where-Object { $_.Status -eq 'Warning' }).Count
        $report.Errors   = @($report.Health | Where-Object { $_.Status -eq 'Error' }).Count
        Write-EsdeReports -ReportsDir $ReportsDir -Data $report -Logger $LMain
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


