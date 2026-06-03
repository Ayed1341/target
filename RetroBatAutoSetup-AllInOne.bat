@echo off
setlocal EnableExtensions EnableDelayedExpansion

REM ===========================================================================
REM  RetroBat Auto Setup - ALL-IN-ONE single-file launcher.
REM  Self-contained: the entire PowerShell engine (all modules, the emulator
REM  database and the orchestrator) is embedded below the payload
REM  Place this .bat in the RetroBat root folder and run it.
REM
REM  Usage:
REM    RetroBatAutoSetup-AllInOne.bat              Full setup pipeline.
REM    RetroBatAutoSetup-AllInOne.bat /watch       Controller hotswap watcher.
REM    RetroBatAutoSetup-AllInOne.bat /noinstall   Skip auto-installing emulators.
REM    RetroBatAutoSetup-AllInOne.bat /nogit       Skip git commit/push.
REM ===========================================================================

set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"
title RetroBat Auto Setup (All-in-One)

echo.
echo  ============================================================
echo    RetroBat Auto Setup (All-in-One)
echo    Root: %ROOT%
echo  ============================================================
echo.

REM --- Self-elevate to Administrator, forwarding all arguments --------------
net session >nul 2>&1
if %errorlevel% NEQ 0 (
    echo [INFO] Requesting administrator privileges...
    set "ELEV_VBS=%TEMP%\rb_elev_%RANDOM%.vbs"
    > "!ELEV_VBS!" echo Set UAC = CreateObject^("Shell.Application"^)
    >> "!ELEV_VBS!" echo UAC.ShellExecute "%~f0", "%*", "%ROOT%", "runas", 1
    cscript //nologo "!ELEV_VBS!"
    del "!ELEV_VBS!" >nul 2>&1
    exit /b 0
)

REM --- Locate PowerShell -----------------------------------------------------
set "PWSH="
where pwsh.exe >nul 2>&1 && set "PWSH=pwsh.exe"
if not defined PWSH ( where powershell.exe >nul 2>&1 && set "PWSH=powershell.exe" )
if not defined PWSH (
    echo [ERROR] PowerShell was not found on this system.
    pause
    exit /b 3
)

REM --- Parse launcher flags --------------------------------------------------
set "MODE=Setup"
set "EXTRA="
:parse_args
if "%~1"=="" goto run
if /i "%~1"=="/watch"     set "MODE=Watch"
if /i "%~1"=="-watch"     set "MODE=Watch"
if /i "%~1"=="/noinstall" set "EXTRA=!EXTRA! -SkipInstall"
if /i "%~1"=="-noinstall" set "EXTRA=!EXTRA! -SkipInstall"
if /i "%~1"=="/nogit"     set "EXTRA=!EXTRA! -SkipGit"
if /i "%~1"=="-nogit"     set "EXTRA=!EXTRA! -SkipGit"
shift
goto parse_args

:run
echo [INFO] Running with administrator privileges. Mode: !MODE!
echo.
REM Extract the embedded PowerShell payload (after the LAST marker) to a temp
REM file and execute it, then clean up. Using LastIndexOf so the marker
REM referenced inside this command does not match before the real payload.
"%PWSH%" -NoProfile -ExecutionPolicy Bypass -Command "$self=[IO.File]::ReadAllText('%~f0'); $m='#PSPAYLOAD_BEGIN'; $i=$self.LastIndexOf($m); if($i -lt 0){ Write-Host 'Payload marker not found' -ForegroundColor Red; exit 9 }; $code=$self.Substring($i+$m.Length); $tmp=Join-Path $env:TEMP ('RBAllInOne_'+[Guid]::NewGuid().ToString('N')+'.ps1'); [IO.File]::WriteAllText($tmp,$code,(New-Object Text.UTF8Encoding($false))); try { & $tmp -RetroBatRoot '%ROOT%' -Mode %MODE%%EXTRA% } finally { Remove-Item $tmp -Force -ErrorAction SilentlyContinue }"
set "RC=%errorlevel%"

echo.
if "%RC%"=="0" ( echo [DONE] Finished successfully. Logs are in "%ROOT%\Logs". ) else ( echo [WARN] Exited with code %RC%. Check "%ROOT%\Logs". )
if /i not "!MODE!"=="Watch" ( echo. & pause )
endlocal & exit /b %RC%

#PSPAYLOAD_BEGIN
# === RetroBat Auto Setup - ALL-IN-ONE (generated from verified modules) ===
[CmdletBinding()]
param(
    [string] $RetroBatRoot,
    [ValidateSet("Setup","Watch")] [string] $Mode = "Setup",
    [switch] $SkipInstall,
    [switch] $SkipGit,
    [int] $WatchIntervalSeconds = 5
)
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$script:EmbeddedEmulatorJson = @'
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
            "folder": "dolphin",
            "executables": [ "Dolphin.exe", "DolphinR.exe" ],
            "configType": "ini",
            "configFiles": [ "User/Config/GFX.ini", "User/Config/Dolphin.ini" ],
            "systems": [ "gc", "wii" ],
            "supports4K": true,
            "download": {
                "type": "direct",
                "url": "https://dl.dolphin-emu.org/builds/5e/4e/dolphin-master-5.0-21088-x64.7z",
                "archive": "7z",
                "stripRootFolder": true
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
                "assetPattern": "win_x64.zip$",
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
                "assetPattern": "64bit.exe$",
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
                "assetPattern": "win64.zip$",
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
        "28DE": "Valve",
        "2DC8": "8BitDo",
        "0F0D": "Hori",
        "146B": "BigBen / Nacon",
        "0079": "DragonRise / Generic USB",
        "1532": "Razer",
        "24C6": "PowerA",
        "0E6F": "PDP",
        "1689": "Razer Onza",
        "2563": " ShanWan Generic"
    }
}

'@

# ----- module: Logging -----
<#
.SYNOPSIS
    Centralized logging module for the RetroBat automation suite.
.DESCRIPTION
    Provides timestamped, leveled logging to multiple log files and the console.
    Every other module routes output through Write-Log so that all activity is
    captured under <RetroBatRoot>\Logs.
#>

Set-StrictMode -Version Latest

# Module-scoped state shared across all logging calls.
$script:LogRoot      = $null
$script:LogTargets   = @{}
$script:DefaultLog   = 'Setup'
$script:Initialized  = $false

# Mapping of logical log names to file names. The suite writes to these four
# files as mandated by the specification, plus a general fallback.
$script:LogFileMap = [ordered]@{
    'Setup'        = 'Setup.log'
    'Emulator'     = 'EmulatorOptimization.log'
    'Controller'   = 'ControllerSetup.log'
    'Installation' = 'Installation.log'
}

function Initialize-Logging {
    <#
    .SYNOPSIS
        Prepares the Logs directory and initializes all log files.
    .PARAMETER LogRoot
        Absolute path to the Logs directory (created if missing).
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string] $LogRoot
    )

    if (-not (Test-Path -LiteralPath $LogRoot)) {
        New-Item -Path $LogRoot -ItemType Directory -Force | Out-Null
    }

    $script:LogRoot    = $LogRoot
    $script:LogTargets = @{}

    foreach ($key in $script:LogFileMap.Keys) {
        $path = Join-Path $LogRoot $script:LogFileMap[$key]
        $script:LogTargets[$key] = $path
        # Touch the file so it always exists even if no message of that type fires.
        if (-not (Test-Path -LiteralPath $path)) {
            New-Item -Path $path -ItemType File -Force | Out-Null
        }
    }

    $script:Initialized = $true

    $header = "================ RetroBat Auto Setup session started $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') ================"
    foreach ($key in $script:LogFileMap.Keys) {
        Add-Content -LiteralPath $script:LogTargets[$key] -Value $header -Encoding UTF8
    }
}

function Write-Log {
    <#
    .SYNOPSIS
        Writes a timestamped, leveled message to a log file and the console.
    .PARAMETER Message
        The text to record.
    .PARAMETER Level
        One of INFO, WARN, ERROR, SUCCESS, DEBUG.
    .PARAMETER Category
        Which log file to write to: Setup, Emulator, Controller, Installation.
    .PARAMETER NoConsole
        Suppress console echo (file only).
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true, Position = 0)]
        [string] $Message,

        [ValidateSet('INFO', 'WARN', 'ERROR', 'SUCCESS', 'DEBUG')]
        [string] $Level = 'INFO',

        [ValidateSet('Setup', 'Emulator', 'Controller', 'Installation')]
        [string] $Category = 'Setup',

        [switch] $NoConsole
    )

    $timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss.fff'
    $line      = '[{0}] [{1,-7}] {2}' -f $timestamp, $Level, $Message

    # File output (always to the chosen category, ERROR/WARN also mirrored to Setup).
    if ($script:Initialized) {
        $targets = New-Object System.Collections.Generic.List[string]
        $targets.Add($script:LogTargets[$Category])
        if (($Level -eq 'ERROR' -or $Level -eq 'WARN') -and $Category -ne 'Setup') {
            $targets.Add($script:LogTargets['Setup'])
        }
        foreach ($t in ($targets | Select-Object -Unique)) {
            try {
                Add-Content -LiteralPath $t -Value $line -Encoding UTF8 -ErrorAction Stop
            } catch {
                # Last-resort: never let logging crash the run.
                Write-Host "LOGGING FAILURE -> $($_.Exception.Message)" -ForegroundColor Red
            }
        }
    }

    # Console output with colour coding.
    if (-not $NoConsole) {
        $color = switch ($Level) {
            'INFO'    { 'Gray' }
            'WARN'    { 'Yellow' }
            'ERROR'   { 'Red' }
            'SUCCESS' { 'Green' }
            'DEBUG'   { 'DarkGray' }
            default   { 'White' }
        }
        Write-Host $line -ForegroundColor $color
    }
}

function Write-LogSection {
    <#
    .SYNOPSIS
        Writes a visually distinct section banner to the log and console.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string] $Title,

        [ValidateSet('Setup', 'Emulator', 'Controller', 'Installation')]
        [string] $Category = 'Setup'
    )

    $bar = '-' * 70
    Write-Log -Message $bar -Level INFO -Category $Category
    Write-Log -Message ("  {0}" -f $Title.ToUpper()) -Level INFO -Category $Category
    Write-Log -Message $bar -Level INFO -Category $Category
}

function Get-LogRoot {
    [CmdletBinding()]
    param()
    return $script:LogRoot
}

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
        [Parameter(Mandatory = $true)] [string] $Section,
        [Parameter(Mandatory = $true)] [string] $Key,
        [Parameter(Mandatory = $true)] [string] $Value
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

# ----- module: RetroBatDiscovery -----
<#
.SYNOPSIS
    RetroBat installation discovery module.
.DESCRIPTION
    Locates the RetroBat root and maps every relevant sub-tree: EmulationStation,
    emulators, BIOS, ROMs, saves, configuration and controller-profile folders.
    Also extracts the installed RetroBat version. Designed to run from the
    RetroBat root but capable of probing common install locations as a fallback.
#>

Set-StrictMode -Version Latest

function Find-RetroBatRoot {
    <#
    .SYNOPSIS
        Resolves the RetroBat root directory.
    .DESCRIPTION
        Verifies the supplied StartPath (and its parents) look like a RetroBat
        install; if not, probes well-known install locations.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string] $StartPath
    )

    $candidates = New-Object System.Collections.Generic.List[string]

    # Walk up from the start path: the script may live in RetroBat\ directly.
    $cursor = (Resolve-Path -LiteralPath $StartPath).Path
    for ($i = 0; $i -lt 4 -and $cursor; $i++) {
        $candidates.Add($cursor)
        $parent = Split-Path -Path $cursor -Parent
        if (-not $parent -or $parent -eq $cursor) { break }
        $cursor = $parent
    }

    # Common install locations as a fallback. Built by string composition (not
    # Join-Path) so a drive-qualified root never triggers provider resolution,
    # and any unset base is skipped (safe to exercise on non-Windows hosts too).
    $fallbackBases = @('C:', 'D:', $env:SystemDrive, ${env:ProgramFiles}, $env:USERPROFILE)
    foreach ($base in $fallbackBases) {
        if ([string]::IsNullOrWhiteSpace($base)) { continue }
        $candidates.Add(($base.TrimEnd('\') + '\RetroBat'))
    }

    foreach ($c in ($candidates | Select-Object -Unique)) {
        if (Test-RetroBatRoot -Path $c) { return (Resolve-Path -LiteralPath $c).Path }
    }

    return $null
}

function Test-RetroBatRoot {
    <#
    .SYNOPSIS
        Heuristically validates that a path is a RetroBat root.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][string] $Path)

    if (-not (Test-Path -LiteralPath $Path)) { return $false }

    $markers = @(
        'emulationstation',
        'emulators',
        'roms',
        'bios'
    )
    $hits = 0
    foreach ($m in $markers) {
        if (Test-Path -LiteralPath (Join-Path $Path $m)) { $hits++ }
    }
    # Strong signals: the launcher or retrobat.ini.
    if (Test-Path -LiteralPath (Join-Path $Path 'retrobat.ini')) { $hits += 2 }
    if (Test-Path -LiteralPath (Join-Path $Path 'RetroBat.exe')) { $hits += 2 }

    return ($hits -ge 3)
}

function Get-RetroBatVersion {
    <#
    .SYNOPSIS
        Reads the installed RetroBat version from known locations.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][string] $Root)

    $versionFiles = @(
        (Join-Path $Root 'system\version.info'),
        (Join-Path $Root 'version.info'),
        (Join-Path $Root 'emulationstation\version.info')
    )
    foreach ($vf in $versionFiles) {
        if (Test-Path -LiteralPath $vf) {
            $raw = (Get-Content -LiteralPath $vf -Raw -ErrorAction SilentlyContinue)
            if ($raw) { return $raw.Trim() }
        }
    }

    # retrobat.ini may carry a version under [RetroBat].
    $ini = Join-Path $Root 'retrobat.ini'
    if (Test-Path -LiteralPath $ini) {
        $match = Select-String -LiteralPath $ini -Pattern '^\s*version\s*=\s*(.+)$' -ErrorAction SilentlyContinue |
                 Select-Object -First 1
        if ($match) { return $match.Matches[0].Groups[1].Value.Trim() }
    }

    return 'Unknown'
}

function Get-RetroBatLayout {
    <#
    .SYNOPSIS
        Builds a hashtable of all important RetroBat paths, marking which exist.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][string] $Root)

    $esRoot   = Join-Path $Root 'emulationstation'
    $esData   = Join-Path $esRoot '.emulationstation'

    $layout = [ordered]@{
        Root                 = $Root
        Version              = Get-RetroBatVersion -Root $Root
        EmulationStation     = $esRoot
        EmulationStationData = $esData
        EsSettings           = Join-Path $esData 'es_settings.cfg'
        EsInput              = Join-Path $esData 'es_input.cfg'
        EsSystems            = Join-Path $esData 'es_systems.cfg'
        Emulators            = Join-Path $Root 'emulators'
        Bios                 = Join-Path $Root 'bios'
        Roms                 = Join-Path $Root 'roms'
        Saves                = Join-Path $Root 'saves'
        System               = Join-Path $Root 'system'
        Configs              = Join-Path $Root 'system\configs'
        Decorations          = Join-Path $Root 'decorations'
        RetroBatIni          = Join-Path $Root 'retrobat.ini'
        Backups              = Join-Path $Root 'Backups'
        Logs                 = Join-Path $Root 'Logs'
    }

    $layout.Exists = [ordered]@{}
    foreach ($key in @('EmulationStation','EmulationStationData','EsSettings','EsInput',
                       'EsSystems','Emulators','Bios','Roms','Saves','System','Configs',
                       'RetroBatIni')) {
        $layout.Exists[$key] = Test-Path -LiteralPath $layout[$key]
    }

    return $layout
}

function Get-ControllerProfilePaths {
    <#
    .SYNOPSIS
        Returns existing controller-profile / autoconfig folders within RetroBat.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][System.Collections.Specialized.OrderedDictionary] $Layout)

    $paths = [ordered]@{
        EsInput            = $Layout.EsInput
        RetroArchAutoconf  = Join-Path $Layout.Emulators 'retroarch\autoconfig'
        RetroArchRemaps    = Join-Path $Layout.Emulators 'retroarch\config\remaps'
        SdlGameDb          = Join-Path $Layout.System 'tools\gamecontrollerdb.txt'
    }
    $paths.Exists = [ordered]@{}
    foreach ($k in @('EsInput','RetroArchAutoconf','RetroArchRemaps','SdlGameDb')) {
        $paths.Exists[$k] = Test-Path -LiteralPath $paths[$k]
    }
    return $paths
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
    # Fall back to a recursive search (handles versioned sub-folders).
    foreach ($exe in $Executables) {
        $found = Get-ChildItem -LiteralPath $Folder -Filter $exe -Recurse -File -ErrorAction SilentlyContinue |
                 Select-Object -First 1
        if ($found) { return $found.FullName }
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
            $exe = Get-ChildItem -LiteralPath $_.FullName -Filter '*.exe' -Recurse -File -ErrorAction SilentlyContinue |
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

# ----- module: EmulatorInstall -----
<#
.SYNOPSIS
    Emulator auto-installation module.
.DESCRIPTION
    Installs missing emulators required by RetroBat. Resolution of download URLs
    is data-driven (config\emulators.json):
      * type=github : queries the GitHub Releases API for the latest matching asset
      * type=direct : uses a fixed official upstream URL
    Archives are extracted with the RetroBat-bundled 7-Zip when available, falling
    back to .NET ZIP extraction. Every step is logged and the install is verified
    by re-detecting the emulator executable afterwards. Existing files are never
    deleted; downloads land in a temp folder and are copied into place.
#>

Set-StrictMode -Version Latest

function Get-SevenZipPath {
    <#
    .SYNOPSIS
        Locates a usable 7-Zip executable (RetroBat bundles 7za under system\tools).
    #>
    [CmdletBinding()]
    param([string] $RetroBatRoot)

    $candidates = @()
    if ($RetroBatRoot) {
        $candidates += Join-Path $RetroBatRoot 'system\tools\7za.exe'
        $candidates += Join-Path $RetroBatRoot 'system\tools\7z.exe'
        $candidates += Join-Path $RetroBatRoot 'system\7za.exe'
    }
    foreach ($base in @(${env:ProgramFiles}, ${env:ProgramFiles(x86)})) {
        if (-not [string]::IsNullOrWhiteSpace($base)) {
            $candidates += Join-Path $base '7-Zip\7z.exe'
        }
    }

    foreach ($c in $candidates) {
        if ($c -and (Test-Path -LiteralPath $c)) { return $c }
    }
    $cmd = Get-Command -Name '7z.exe', '7za.exe' -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($cmd) { return $cmd.Source }
    return $null
}

function Resolve-DownloadUrl {
    <#
    .SYNOPSIS
        Resolves the concrete download URL + file name for an emulator definition.
    .OUTPUTS
        Hashtable with Url and FileName, or $null when unresolvable.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)] [object] $Download)

    switch ($Download.type) {
        'direct' {
            return @{ Url = $Download.url; FileName = (Split-Path $Download.url -Leaf) }
        }
        'github' {
            $api = "https://api.github.com/repos/$($Download.repo)/releases/latest"
            $headers = @{ 'User-Agent' = 'RetroBat-AutoSetup'; 'Accept' = 'application/vnd.github+json' }
            if ($env:GITHUB_TOKEN) { $headers['Authorization'] = "Bearer $($env:GITHUB_TOKEN)" }
            try {
                $rel    = Invoke-RestMethod -Uri $api -Headers $headers -TimeoutSec 60 -ErrorAction Stop
                $assets = @($rel.assets)
                $match  = $assets | Where-Object { $_.name -match $Download.assetPattern } | Select-Object -First 1
                if (-not $match) {
                    # Loosen: match on extension only if specific pattern failed.
                    $match = $assets | Where-Object { $_.name -match '\.(7z|zip|exe)$' } | Select-Object -First 1
                }
                if ($match) {
                    return @{ Url = $match.browser_download_url; FileName = $match.name }
                }
            } catch {
                throw "GitHub API lookup failed for $($Download.repo): $($_.Exception.Message)"
            }
            return $null
        }
        default { return $null }
    }
}

function Invoke-FileDownload {
    <#
    .SYNOPSIS
        Downloads a file with retry / exponential backoff and verifies it is non-empty.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)] [string] $Url,
        [Parameter(Mandatory = $true)] [string] $Destination,
        [int] $MaxRetries = 4
    )

    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12 -bor [Net.SecurityProtocolType]::Tls11
    $delay = 2
    for ($attempt = 1; $attempt -le $MaxRetries; $attempt++) {
        try {
            $progPref = $ProgressPreference
            $ProgressPreference = 'SilentlyContinue'   # massive speed-up for Invoke-WebRequest
            Invoke-WebRequest -Uri $Url -OutFile $Destination -UseBasicParsing -TimeoutSec 600 -Headers @{ 'User-Agent' = 'RetroBat-AutoSetup' } -ErrorAction Stop
            $ProgressPreference = $progPref

            if ((Test-Path -LiteralPath $Destination) -and ((Get-Item -LiteralPath $Destination).Length -gt 0)) {
                return $true
            }
            throw 'Downloaded file is empty.'
        } catch {
            if ($attempt -ge $MaxRetries) { throw }
            Start-Sleep -Seconds $delay
            $delay *= 2
        }
    }
    return $false
}

function Expand-DownloadedArchive {
    <#
    .SYNOPSIS
        Extracts a downloaded archive into a destination folder.
    .DESCRIPTION
        Uses 7-Zip for .7z (and .zip when present); falls back to Expand-Archive
        for .zip. Self-extracting .exe installers (e.g. MAME) are run with 7-Zip
        which can open them as archives.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)] [string] $ArchivePath,
        [Parameter(Mandatory = $true)] [string] $Destination,
        [Parameter(Mandatory = $true)] [string] $ArchiveType,
        [string] $SevenZip
    )

    if (-not (Test-Path -LiteralPath $Destination)) {
        New-Item -Path $Destination -ItemType Directory -Force | Out-Null
    }

    # .7z and self-extracting .exe archives require 7-Zip. .zip can use 7-Zip
    # when available (faster, handles edge cases) or fall back to .NET extraction.
    $useSevenZip = ($ArchiveType -in @('7z', 'sfx')) -or ($ArchiveType -eq 'zip' -and $SevenZip)

    if ($useSevenZip) {
        if (-not $SevenZip) {
            throw "Archive type '$ArchiveType' requires 7-Zip but none was found."
        }
        $sevenArgs = @('x', $ArchivePath, "-o$Destination", '-y', '-aoa')
        $proc = Start-Process -FilePath $SevenZip -ArgumentList $sevenArgs -NoNewWindow -Wait -PassThru
        if ($proc.ExitCode -ne 0) {
            throw "7-Zip extraction failed (exit code $($proc.ExitCode))."
        }
    }
    elseif ($ArchiveType -eq 'zip') {
        Expand-Archive -LiteralPath $ArchivePath -DestinationPath $Destination -Force
    }
    else {
        throw "Unsupported archive type: $ArchiveType"
    }
}

function Move-ExtractedPayload {
    <#
    .SYNOPSIS
        Copies extracted content into the emulator folder, optionally collapsing a
        single redundant top-level folder (stripRootFolder).
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)] [string] $StagingDir,
        [Parameter(Mandatory = $true)] [string] $TargetDir,
        [bool] $StripRootFolder = $false
    )

    if (-not (Test-Path -LiteralPath $TargetDir)) {
        New-Item -Path $TargetDir -ItemType Directory -Force | Out-Null
    }

    $source = $StagingDir
    if ($StripRootFolder) {
        $entries = @(Get-ChildItem -LiteralPath $StagingDir -Force)
        $dirs    = @($entries | Where-Object { $_.PSIsContainer })
        $files   = @($entries | Where-Object { -not $_.PSIsContainer })
        if ($dirs.Count -eq 1 -and $files.Count -eq 0) {
            $source = $dirs[0].FullName
        }
    }

    Get-ChildItem -LiteralPath $source -Force | ForEach-Object {
        Copy-Item -LiteralPath $_.FullName -Destination $TargetDir -Recurse -Force
    }
}

function Install-Emulator {
    <#
    .SYNOPSIS
        Downloads, extracts, installs and verifies a single emulator.
    .OUTPUTS
        Hashtable: Success (bool), Message (string), ExecutablePath (string|null).
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)] [object] $Emulator,
        [Parameter(Mandatory = $true)] [string] $RetroBatRoot,
        [Parameter(Mandatory = $true)] [scriptblock] $Logger
    )

    $log = { param($m, $l) & $Logger $m $l }

    $def = $Emulator.Definition
    & $log "Preparing installation of $($Emulator.DisplayName)..." 'INFO'

    $resolved = Resolve-DownloadUrl -Download $def.download
    if (-not $resolved) {
        return @{ Success = $false; Message = "No download URL could be resolved."; ExecutablePath = $null }
    }
    & $log "Resolved download URL: $($resolved.Url)" 'INFO'

    $tempBase = Join-Path $env:TEMP ("RetroBatSetup_{0}_{1}" -f $Emulator.Id, (Get-Date -Format 'yyyyMMddHHmmss'))
    $dlPath   = Join-Path $tempBase $resolved.FileName
    $staging  = Join-Path $tempBase 'extracted'
    New-Item -Path $tempBase -ItemType Directory -Force | Out-Null

    try {
        & $log "Downloading $($resolved.FileName)..." 'INFO'
        [void](Invoke-FileDownload -Url $resolved.Url -Destination $dlPath)
        $sizeMB = [math]::Round((Get-Item -LiteralPath $dlPath).Length / 1MB, 2)
        & $log "Download complete ($sizeMB MB)." 'SUCCESS'

        $sevenZip = Get-SevenZipPath -RetroBatRoot $RetroBatRoot
        $archType = $def.download.archive
        & $log "Extracting archive (type=$archType)..." 'INFO'
        Expand-DownloadedArchive -ArchivePath $dlPath -Destination $staging -ArchiveType $archType -SevenZip $sevenZip

        $strip = $false
        if ($def.download.PSObject.Properties.Name -contains 'stripRootFolder') {
            $strip = [bool]$def.download.stripRootFolder
        }
        & $log "Installing into $($Emulator.FolderPath)..." 'INFO'
        Move-ExtractedPayload -StagingDir $staging -TargetDir $Emulator.FolderPath -StripRootFolder $strip

        # ---- Verify ----
        $exe = Find-EmulatorExecutable -Folder $Emulator.FolderPath -Executables $def.executables
        if ($exe) {
            & $log "Verified: $($Emulator.DisplayName) executable present at $exe" 'SUCCESS'
            return @{ Success = $true; Message = 'Installed and verified.'; ExecutablePath = $exe }
        } else {
            & $log "Installation completed but no expected executable was found." 'WARN'
            return @{ Success = $false; Message = 'Executable not found after extraction.'; ExecutablePath = $null }
        }
    } catch {
        & $log "Installation failed: $($_.Exception.Message)" 'ERROR'
        return @{ Success = $false; Message = $_.Exception.Message; ExecutablePath = $null }
    } finally {
        if (Test-Path -LiteralPath $tempBase) {
            Remove-Item -LiteralPath $tempBase -Recurse -Force -ErrorAction SilentlyContinue
        }
    }
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
        [Parameter(Mandatory = $true)] [scriptblock] $Logger
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
    param($Emulator, $Tier, $TargetWidth, $TargetHeight, $BackupRoot, $Logger)
    $cfg = Join-Path $Emulator.FolderPath 'retroarch.cfg'
    New-ConfigBackup -Path $cfg -BackupRoot $BackupRoot | Out-Null

    $smooth = if ($Tier -eq 'LowEnd') { 'false' } else { 'true' }
    $map = [ordered]@{
        'video_fullscreen'         = 'true'
        'video_windowed_fullscreen'= 'true'
        'video_fullscreen_x'       = "$TargetWidth"
        'video_fullscreen_y'       = "$TargetHeight"
        'video_vsync'              = 'true'
        'video_hard_sync'          = 'false'
        'video_smooth'             = $smooth
        'video_threaded'           = 'true'
        'video_driver'             = 'vulkan'
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
    param($Emulator, $Tier, $TargetWidth, $TargetHeight, $BackupRoot, $Logger)
    $cfg = Resolve-ConfigPath -Emulator $Emulator
    New-ConfigBackup -Path $cfg -BackupRoot $BackupRoot | Out-Null
    $ini = Read-IniFile -Path $cfg

    $scale = Get-TierScale -Tier $Tier -Max 8 -Min 1   # upscale_multiplier
    Set-IniValue -Data $ini -Section 'EmuCore/GS' -Key 'upscale_multiplier' -Value ("{0}" -f $scale)
    Set-IniValue -Data $ini -Section 'EmuCore/GS' -Key 'Renderer'            -Value '14'   # 14 = Vulkan
    Set-IniValue -Data $ini -Section 'EmuCore/GS' -Key 'AnisotropicFiltering' -Value '16'
    Set-IniValue -Data $ini -Section 'EmuCore/GS' -Key 'TextureFiltering'    -Value '2'    # bilinear (forced)
    Set-IniValue -Data $ini -Section 'EmuCore/GS' -Key 'VsyncEnable'         -Value '1'
    Set-IniValue -Data $ini -Section 'EmuCore/GS' -Key 'mipmap_hw'           -Value '-1'
    Set-IniValue -Data $ini -Section 'EmuCore/GS' -Key 'OsdShowMessages'     -Value 'false'

    Write-IniFile -Path $cfg -Data $ini
    & $Logger "PCSX2 optimized: upscale ${scale}x, Vulkan, 16x AF (tier $Tier)." 'SUCCESS'
    return @{ Success = $true; Message = 'PCSX2 configured.'; Changed = @($cfg) }
}

# ----------------------------------------------------------------------------
# RPCS3 (YAML scalars)
# ----------------------------------------------------------------------------
function Optimize-RPCS3 {
    param($Emulator, $Tier, $TargetWidth, $TargetHeight, $BackupRoot, $Logger)
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
    param($Emulator, $Tier, $TargetWidth, $TargetHeight, $BackupRoot, $Logger)
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
    param($Emulator, $Tier, $TargetWidth, $TargetHeight, $BackupRoot, $Logger)
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
    param($Emulator, $Tier, $TargetWidth, $TargetHeight, $BackupRoot, $Logger)
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
    param($Emulator, $Tier, $TargetWidth, $TargetHeight, $BackupRoot, $Logger)
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
    param($Emulator, $Tier, $TargetWidth, $TargetHeight, $BackupRoot, $Logger)
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
    param($Emulator, $Tier, $TargetWidth, $TargetHeight, $BackupRoot, $Logger)
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
    param($Emulator, $Tier, $TargetWidth, $TargetHeight, $BackupRoot, $Logger)
    $cfg = Resolve-ConfigPath -Emulator $Emulator
    New-ConfigBackup -Path $cfg -BackupRoot $BackupRoot | Out-Null
    $ini = Read-IniFile -Path $cfg

    $scale = switch ($Tier) { 'LowEnd' {2} 'MidRange' {4} 'HighEnd' {8} 'FourK' {9} default {4} }
    Set-IniValue -Data $ini -Section 'GPU' -Key 'Renderer' -Value 'Vulkan'
    Set-IniValue -Data $ini -Section 'GPU' -Key 'ResolutionScale' -Value "$scale"
    Set-IniValue -Data $ini -Section 'GPU' -Key 'TextureFilter' -Value 'Bilinear'
    Set-IniValue -Data $ini -Section 'GPU' -Key 'PGXPEnable' -Value 'true'
    Set-IniValue -Data $ini -Section 'GPU' -Key 'PGXPCulling' -Value 'true'
    Set-IniValue -Data $ini -Section 'Display' -Key 'VSync' -Value 'true'
    Set-IniValue -Data $ini -Section 'Display' -Key 'Fullscreen' -Value 'true'
    Write-IniFile -Path $cfg -Data $ini
    & $Logger "DuckStation optimized: Vulkan, resolution scale ${scale}x, PGXP on (tier $Tier)." 'SUCCESS'
    return @{ Success = $true; Message = 'DuckStation configured.'; Changed = @($cfg) }
}

# ----------------------------------------------------------------------------
# melonDS (melonDS.ini)
# ----------------------------------------------------------------------------
function Optimize-MelonDS {
    param($Emulator, $Tier, $TargetWidth, $TargetHeight, $BackupRoot, $Logger)
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
    param($Emulator, $Tier, $TargetWidth, $TargetHeight, $BackupRoot, $Logger)
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
    param($Emulator, $Tier, $TargetWidth, $TargetHeight, $BackupRoot, $Logger)
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
    param($Emulator, $Tier, $TargetWidth, $TargetHeight, $BackupRoot, $Logger)
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
    param($Emulator, $Tier, $TargetWidth, $TargetHeight, $BackupRoot, $Logger)
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
        $vid = $null; $pid = $null
        if ($id -match '(?i)VID_([0-9A-F]{4})') { $vid = $Matches[1].ToUpper() }
        if ($id -match '(?i)PID_([0-9A-F]{4})') { $pid = $Matches[1].ToUpper() }
        if (-not $vid) { continue }

        # Deduplicate on VID+PID (composite devices expose multiple PnP nodes).
        $key = "${vid}:${pid}"
        if ($seen.Contains($key)) { continue }
        [void]$seen.Add($key)

        $vendor = if ($vid -and $VendorMap.ContainsKey($vid)) { $VendorMap[$vid] } else { 'Unknown vendor' }
        $family = Get-ControllerFamily -Vid $vid -Name $d.Name -PnpId $id

        $controllers.Add([pscustomobject]@{
            Name       = $d.Name
            Vid        = $vid
            Pid        = $pid
            Vendor     = $vendor
            Family     = $family
            ApiType    = (Get-ControllerApiType -PnpId $id -Family $family)
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
    $file     = Join-Path $AutoconfigDir ("{0}.cfg" -f $safeName)

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

# ----- module: ConfigValidation -----
<#
.SYNOPSIS
    Configuration validation and repair module.
.DESCRIPTION
    Validates the RetroBat environment: missing BIOS files (against a known
    requirement table), broken/missing critical paths, malformed emulator
    configuration files. Repairs what is safe to repair (recreating missing
    folders, restoring a config from its most recent backup when corrupted) and
    reports the rest. Never deletes ROMs, saves, BIOS or user configs.
#>

Set-StrictMode -Version Latest

# Minimal, well-known BIOS requirement table (filename -> systems needing it).
# Used to flag missing BIOS; the script never downloads copyrighted BIOS files.
$script:BiosRequirements = @(
    @{ File = 'scph5500.bin'; System = 'PlayStation (PSX/JP)' },
    @{ File = 'scph5501.bin'; System = 'PlayStation (PSX/US)' },
    @{ File = 'scph5502.bin'; System = 'PlayStation (PSX/EU)' },
    @{ File = 'ps2-0200a-20040614.bin'; System = 'PlayStation 2' },
    @{ File = 'dc_boot.bin'; System = 'Dreamcast' },
    @{ File = 'dc_flash.bin'; System = 'Dreamcast' },
    @{ File = 'bios7.bin'; System = 'Nintendo DS' },
    @{ File = 'bios9.bin'; System = 'Nintendo DS' },
    @{ File = 'firmware.bin'; System = 'Nintendo DS' },
    @{ File = 'gba_bios.bin'; System = 'Game Boy Advance' },
    @{ File = 'syscard3.pce'; System = 'PC Engine CD' }
)

function Test-RetroBatPaths {
    <#
    .SYNOPSIS
        Verifies critical RetroBat folders exist; recreates safe-to-create ones.
    .OUTPUTS
        Array of issue hashtables: Type, Item, Severity, Repaired, Detail.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)] [System.Collections.Specialized.OrderedDictionary] $Layout,
        [Parameter(Mandatory = $true)] [scriptblock] $Logger
    )

    $issues = New-Object System.Collections.Generic.List[object]

    # Folders we may safely (re)create if missing - never touches user content.
    $createable = @('Emulators','Bios','Roms','Saves','System','Configs','Backups','Logs',
                    'EmulationStation','EmulationStationData')

    foreach ($key in $createable) {
        if (-not $Layout.Contains($key)) { continue }
        $path = $Layout[$key]
        if (-not (Test-Path -LiteralPath $path)) {
            try {
                New-Item -Path $path -ItemType Directory -Force | Out-Null
                & $Logger "Recreated missing folder: $path" 'WARN'
                $issues.Add(@{ Type='Path'; Item=$path; Severity='Warning'; Repaired=$true; Detail='Folder recreated.' })
            } catch {
                & $Logger "Failed to recreate folder ${path}: $($_.Exception.Message)" 'ERROR'
                $issues.Add(@{ Type='Path'; Item=$path; Severity='Error'; Repaired=$false; Detail=$_.Exception.Message })
            }
        }
    }
    return $issues.ToArray()
}

function Test-BiosFiles {
    <#
    .SYNOPSIS
        Reports which known BIOS files are missing from the bios folder.
        Does NOT download BIOS (copyright); only flags for the user.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)] [string] $BiosDir,
        [Parameter(Mandatory = $true)] [scriptblock] $Logger
    )

    $issues = New-Object System.Collections.Generic.List[object]
    if (-not (Test-Path -LiteralPath $BiosDir)) {
        & $Logger "BIOS directory not found: $BiosDir" 'WARN'
        return $issues.ToArray()
    }

    # Index existing files (recursively) by lowercase name for fast lookup.
    $present = @{}
    Get-ChildItem -LiteralPath $BiosDir -Recurse -File -ErrorAction SilentlyContinue | ForEach-Object {
        $present[$_.Name.ToLower()] = $_.FullName
    }

    foreach ($req in $script:BiosRequirements) {
        if (-not $present.ContainsKey($req.File.ToLower())) {
            & $Logger "Missing BIOS: $($req.File) (needed for $($req.System))" 'WARN'
            $issues.Add(@{ Type='Bios'; Item=$req.File; Severity='Warning'; Repaired=$false; Detail="Required for $($req.System). Provide this file in $BiosDir." })
        }
    }
    if ($issues.Count -eq 0) {
        & $Logger "All tracked BIOS files are present." 'SUCCESS'
    }
    return $issues.ToArray()
}

function Test-EmulatorConfigs {
    <#
    .SYNOPSIS
        Validates installed emulator config files for basic corruption (e.g.
        truncated/empty INI, invalid JSON). Restores from the latest backup when
        a config is corrupt and a backup exists.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)] [object[]] $Emulators,
        [Parameter(Mandatory = $true)] [string]   $BackupRoot,
        [Parameter(Mandatory = $true)] [scriptblock] $Logger
    )

    $issues = New-Object System.Collections.Generic.List[object]

    foreach ($emu in ($Emulators | Where-Object { $_.Installed -and $_.ConfigFiles.Count -gt 0 })) {
        foreach ($rel in $emu.ConfigFiles) {
            $cfg = Join-Path $emu.FolderPath $rel
            if (-not (Test-Path -LiteralPath $cfg)) { continue }   # absent != corrupt

            $corrupt = $false
            $reason  = ''
            try {
                $len = (Get-Item -LiteralPath $cfg).Length
                if ($len -eq 0) { $corrupt = $true; $reason = 'empty file' }
                elseif ($emu.ConfigType -eq 'json') {
                    $null = Get-Content -LiteralPath $cfg -Raw -Encoding UTF8 | ConvertFrom-Json -ErrorAction Stop
                }
            } catch {
                $corrupt = $true
                $reason  = "parse error: $($_.Exception.Message)"
            }

            if ($corrupt) {
                & $Logger "Corrupt config for $($emu.DisplayName): $cfg ($reason)" 'ERROR'
                $restored = Restore-LatestBackup -OriginalPath $cfg -BackupRoot $BackupRoot -Logger $Logger
                $issues.Add(@{
                    Type='Config'; Item=$cfg; Severity='Error'
                    Repaired=$restored; Detail=$reason
                })
            }
        }
    }
    if ($issues.Count -eq 0) {
        & $Logger "No corrupt emulator configuration files detected." 'SUCCESS'
    }
    return $issues.ToArray()
}

function Restore-LatestBackup {
    <#
    .SYNOPSIS
        Restores a file from its most recent timestamped backup, if one exists.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)] [string] $OriginalPath,
        [Parameter(Mandatory = $true)] [string] $BackupRoot,
        [Parameter(Mandatory = $true)] [scriptblock] $Logger
    )

    if (-not (Test-Path -LiteralPath $BackupRoot)) { return $false }
    $leaf    = Split-Path $OriginalPath -Leaf
    $pattern = "$leaf.*.bak"
    $backup  = Get-ChildItem -LiteralPath $BackupRoot -Filter $pattern -File -ErrorAction SilentlyContinue |
               Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if ($backup) {
        try {
            Copy-Item -LiteralPath $backup.FullName -Destination $OriginalPath -Force
            & $Logger "Restored $OriginalPath from backup $($backup.Name)." 'SUCCESS'
            return $true
        } catch {
            & $Logger "Failed to restore from backup: $($_.Exception.Message)" 'ERROR'
        }
    } else {
        & $Logger "No backup available to restore $OriginalPath." 'WARN'
    }
    return $false
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
# Resolve RetroBat root. The .bat passes its own folder; fall back to discovery.
# ----------------------------------------------------------------------------
if (-not $RetroBatRoot) {
    # The script lives in <RetroBatRoot>\scripts, so the parent is the candidate.
    $RetroBatRoot = Split-Path -Parent $ScriptDir
}
$resolvedRoot = Find-RetroBatRoot -StartPath $RetroBatRoot
if (-not $resolvedRoot) {
    # If discovery fails, proceed with the provided root but warn loudly later.
    $resolvedRoot = (Resolve-Path -LiteralPath $RetroBatRoot).Path
}

$Layout    = Get-RetroBatLayout -Root $resolvedRoot
$LogsDir   = $Layout.Logs
$BackupDir = $Layout.Backups

Initialize-Logging -LogRoot $LogsDir

# Category-specific loggers: plain scriptblocks (NOT closures) so they remain
# bound to this script's scope where Write-Log is defined/imported. This resolves
# correctly whether the script is run via -File or via the call operator (&),
# which is how the all-in-one launcher invokes the embedded payload.
$LogSetup      = { param($Message, $Level = 'INFO') Write-Log -Message $Message -Level $Level -Category 'Setup' }
$LogEmulator   = { param($Message, $Level = 'INFO') Write-Log -Message $Message -Level $Level -Category 'Emulator' }
$LogController = { param($Message, $Level = 'INFO') Write-Log -Message $Message -Level $Level -Category 'Controller' }
$LogInstall    = { param($Message, $Level = 'INFO') Write-Log -Message $Message -Level $Level -Category 'Installation' }

# ============================================================================
# HOTSWAP WATCHER MODE
# ============================================================================
function Start-HotswapWatcher {
    param(
        [System.Collections.Specialized.OrderedDictionary] $Layout,
        [object] $Definitions,
        [string] $BackupDir,
        [int] $Interval
    )

    Write-LogSection -Title 'Controller Hotswap Watcher' -Category 'Controller'
    Write-Log -Message "Watcher started (interval ${Interval}s). Press Ctrl+C to stop." -Level INFO -Category 'Controller'

    $vendorMap = ConvertTo-Hashtable -Object $Definitions.controllerVendors
    $lastSig   = [string]::Empty
    $primed    = $false

    while ($true) {
        try {
            $controllers = @(Get-ConnectedControllers -VendorMap $vendorMap)
            $sig         = Get-ControllerSignature -Controllers $controllers

            if ($sig -ne $lastSig) {
                if ($primed) {
                    if ($sig -eq '') {
                        Write-Log -Message "All controllers disconnected. Configuration left intact (clean state)." -Level WARN -Category 'Controller'
                    } else {
                        Write-Log -Message "Controller change detected ($($controllers.Count) connected). Reconfiguring..." -Level INFO -Category 'Controller'
                        Set-ControllerConfiguration -Controllers $controllers -Layout $Layout -BackupDir $BackupDir -Logger $LogController
                    }
                }
                $lastSig = $sig
                $primed  = $true
            }
        } catch {
            Write-Log -Message "Watcher iteration error: $($_.Exception.Message)" -Level ERROR -Category 'Controller'
        }
        Start-Sleep -Seconds $Interval
    }
}

function ConvertTo-Hashtable {
    param([object] $Object)
    $ht = @{}
    if ($null -eq $Object) { return $ht }
    foreach ($p in $Object.PSObject.Properties) { $ht[$p.Name] = $p.Value }
    return $ht
}

function Set-ControllerConfiguration {
    param(
        [object[]] $Controllers,
        [System.Collections.Specialized.OrderedDictionary] $Layout,
        [string] $BackupDir,
        [scriptblock] $Logger
    )

    if (-not $Controllers -or $Controllers.Count -eq 0) {
        & $Logger "No controllers connected; nothing to configure." 'INFO'
        return
    }

    foreach ($c in $Controllers) {
        & $Logger "Detected controller: $($c.Name) [VID=$($c.Vid) PID=$($c.Pid)] family=$($c.Family) api=$($c.ApiType) vendor=$($c.Vendor)" 'INFO'
    }

    $raAutoconf = Join-Path $Layout.Emulators 'retroarch\autoconfig'
    foreach ($c in $Controllers) {
        Write-RetroArchControllerProfile -Controller $c -AutoconfigDir $raAutoconf -Logger $Logger | Out-Null
    }
    Write-EmulationStationInput -Controllers $Controllers -EsInputPath $Layout.EsInput -BackupRoot $BackupDir -Logger $Logger | Out-Null

    # Verify the written files exist.
    if (Test-Path -LiteralPath $Layout.EsInput) {
        & $Logger "Verified es_input.cfg present." 'SUCCESS'
    } else {
        & $Logger "es_input.cfg was not created as expected." 'ERROR'
    }
}

# ============================================================================
# FULL SETUP PIPELINE
# ============================================================================
function Invoke-FullSetup {
    Write-LogSection -Title 'RetroBat Auto Setup' -Category 'Setup'
    & $LogSetup "RetroBat root: $resolvedRoot" 'INFO'
    & $LogSetup "RetroBat version: $($Layout.Version)" 'INFO'

    if (-not (Test-RetroBatRoot -Path $resolvedRoot)) {
        & $LogSetup "WARNING: this folder does not look like a complete RetroBat install. Continuing best-effort." 'WARN'
    }

    # ---- Load emulator definitions ----
    $definitions = $script:EmbeddedEmulatorJson | ConvertFrom-Json
    & $LogSetup "Loaded $($definitions.emulators.Count) emulator definitions." 'INFO'

    # ---- Phase 1: Discovery report ----
    Write-LogSection -Title 'Phase 1 - RetroBat Discovery' -Category 'Setup'
    foreach ($k in $Layout.Exists.Keys) {
        $state = if ($Layout.Exists[$k]) { 'present' } else { 'MISSING' }
        & $LogSetup ("  {0,-22} {1} ({2})" -f $k, $state, $Layout[$k]) 'INFO'
    }
    $ctrlPaths = Get-ControllerProfilePaths -Layout $Layout
    foreach ($k in $ctrlPaths.Exists.Keys) {
        $state = if ($ctrlPaths.Exists[$k]) { 'present' } else { 'absent' }
        & $LogSetup ("  controller:{0,-12} {1}" -f $k, $state) 'INFO'
    }

    # ---- Phase 2: Hardware detection ----
    Write-LogSection -Title 'Phase 2 - Hardware Detection' -Category 'Setup'
    $hw = Get-SystemHardware
    & $LogSetup "CPU : $($hw.CpuName) ($($hw.CpuCores)C/$($hw.CpuLogical)T @ $($hw.CpuMaxClockMHz)MHz)" 'INFO'
    & $LogSetup "GPU : $($hw.GpuName) [$($hw.GpuVendor)] $($hw.GpuVramMB)MB VRAM, driver $($hw.GpuDriverVersion)" 'INFO'
    & $LogSetup "RAM : $($hw.TotalRamGB) GB" 'INFO'
    & $LogSetup "Disk: $($hw.SystemDriveType)" 'INFO'
    & $LogSetup "Display: $($hw.DisplayWidth)x$($hw.DisplayHeight) @ $($hw.RefreshRateHz)Hz (4K capable: $($hw.Is4KCapable))" 'INFO'
    & $LogSetup "Resolved performance tier: $($hw.Tier)" 'SUCCESS'

    # ---- Phase 3: Profiles ----
    Write-LogSection -Title 'Phase 3 - Profile Generation & Selection' -Category 'Setup'
    $profilesDir = Join-Path $Layout.System 'profiles'
    Save-Profiles -ProfilesDir $profilesDir -Logger $LogSetup | Out-Null
    $selected = Select-ProfileForHardware -Hardware $hw -Logger $LogSetup
    $profile  = $selected.Profile
    $tier     = $selected.Tier

    # ---- Phase 4: Emulator detection ----
    Write-LogSection -Title 'Phase 4 - Emulator Detection' -Category 'Emulator'
    $emulators = Get-InstalledEmulators -EmulatorsRoot $Layout.Emulators -Definitions $definitions
    foreach ($e in $emulators) {
        $state = if ($e.Installed) { 'INSTALLED' } else { 'missing' }
        $kind  = if ($e.Known) { 'known' } else { 'discovered' }
        & $LogEmulator ("  [{0,-10}] {1,-12} {2}" -f $state, $kind, $e.DisplayName) 'INFO'
    }

    # ---- Phase 5: Auto-install missing emulators ----
    if (-not $SkipInstall) {
        Write-LogSection -Title 'Phase 5 - Auto-Install Missing Emulators' -Category 'Installation'
        $missing = Get-MissingRequiredEmulators -Emulators $emulators
        if ($missing.Count -eq 0) {
            & $LogInstall "No installable emulators are missing." 'SUCCESS'
        } else {
            & $LogInstall "$($missing.Count) emulator(s) missing and installable: $(( $missing | ForEach-Object { $_.Id }) -join ', ')" 'INFO'
            foreach ($m in $missing) {
                $res = Install-Emulator -Emulator $m -RetroBatRoot $resolvedRoot -Logger $LogInstall
                if ($res.Success) {
                    # Refresh descriptor so optimization can run on it.
                    $m.Installed      = $true
                    $m.ExecutablePath = $res.ExecutablePath
                } else {
                    & $LogInstall "Could not install $($m.DisplayName): $($res.Message)" 'WARN'
                }
            }
        }
    } else {
        & $LogInstall "Auto-install skipped by request (-SkipInstall)." 'INFO'
    }

    # ---- Phase 6: Graphics optimization ----
    Write-LogSection -Title 'Phase 6 - 4K Graphics Optimization' -Category 'Emulator'
    foreach ($e in ($emulators | Where-Object { $_.Installed })) {
        $r = Invoke-EmulatorOptimization -Emulator $e -Tier $tier `
                -TargetWidth $profile.TargetWidth -TargetHeight $profile.TargetHeight `
                -BackupRoot $BackupDir -Logger $LogEmulator
        if (-not $r.Success -and $r.Message -ne 'No optimizer (unknown emulator).') {
            & $LogEmulator "  -> $($e.DisplayName): $($r.Message)" 'WARN'
        }
    }

    # ---- Phase 7: Controller configuration ----
    Write-LogSection -Title 'Phase 7 - Controller Auto-Configuration' -Category 'Controller'
    $vendorMap   = ConvertTo-Hashtable -Object $definitions.controllerVendors
    $controllers = @(Get-ConnectedControllers -VendorMap $vendorMap)
    if ($controllers.Count -eq 0) {
        & $LogController "No controllers currently connected. Use Watch mode for hotswap configuration." 'WARN'
    } else {
        Set-ControllerConfiguration -Controllers $controllers -Layout $Layout -BackupDir $BackupDir -Logger $LogController
    }

    # ---- Phase 8: Validation & repair ----
    Write-LogSection -Title 'Phase 8 - Configuration Validation & Repair' -Category 'Setup'
    $allIssues = New-Object System.Collections.Generic.List[object]
    Test-RetroBatPaths   -Layout $Layout -Logger $LogSetup            | ForEach-Object { $allIssues.Add($_) }
    Test-BiosFiles       -BiosDir $Layout.Bios -Logger $LogSetup      | ForEach-Object { $allIssues.Add($_) }
    Test-EmulatorConfigs -Emulators $emulators -BackupRoot $BackupDir -Logger $LogSetup | ForEach-Object { $allIssues.Add($_) }

    $errors   = @($allIssues | Where-Object { $_.Severity -eq 'Error'   -and -not $_.Repaired })
    $warnings = @($allIssues | Where-Object { $_.Severity -eq 'Warning' -and -not $_.Repaired })
    & $LogSetup "Validation complete: $($errors.Count) unresolved error(s), $($warnings.Count) warning(s)." `
        $(if ($errors.Count -gt 0) { 'WARN' } else { 'SUCCESS' })

    # ---- Phase 9: Git integration ----
    if (-not $SkipGit) {
        Write-LogSection -Title 'Phase 9 - Git Integration' -Category 'Setup'
        $installedCount = @($emulators | Where-Object { $_.Installed }).Count
        $msg  = "RetroBat auto-setup: tier=$tier, $($profile.TargetWidth)x$($profile.TargetHeight), "
        $msg += "$installedCount emulator(s) configured, $($controllers.Count) controller(s)."
        Invoke-GitCommitAndPush -RepoPath $resolvedRoot -CommitMessage $msg -Logger $LogSetup | Out-Null
    } else {
        & $LogSetup "Git integration skipped by request (-SkipGit)." 'INFO'
    }

    Write-LogSection -Title 'RetroBat Auto Setup Complete' -Category 'Setup'
    & $LogSetup "All phases finished. Logs are in: $LogsDir" 'SUCCESS'
}

# ----------------------------------------------------------------------------
# Entry point
# ----------------------------------------------------------------------------
try {
    if ($Mode -eq 'Watch') {
        $definitions = $script:EmbeddedEmulatorJson | ConvertFrom-Json
        Start-HotswapWatcher -Layout $Layout -Definitions $definitions -BackupDir $BackupDir -Interval $WatchIntervalSeconds
    } else {
        Invoke-FullSetup
    }
    exit 0
} catch {
    Write-Log -Message "FATAL: $($_.Exception.Message)" -Level ERROR -Category 'Setup'
    Write-Log -Message $_.ScriptStackTrace -Level DEBUG -Category 'Setup'
    exit 1
}


