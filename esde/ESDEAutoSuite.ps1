<#
.SYNOPSIS
    ES-DE Auto Suite - master orchestrator.
.DESCRIPTION
    Discovers ES-DE, migrates RetroBat media, reorganizes and classifies media,
    repairs gamelist metadata, de-duplicates, analyzes and (optionally) downloads
    missing media, detects hardware/emulators/controllers, optimizes emulator
    graphics, validates BIOS, cleans orphans, generates HTML/JSON reports and
    commits to git. Designed to be launched by ESDEAutoSuite.bat.
.PARAMETER Mode
    Setup (default) | Restore (roll back from backups) | Watch (controller hotswap)
#>

[CmdletBinding()]
param(
    [string] $EsdeRoot,
    [string] $RetroBatRoot,
    [ValidateSet('Setup','Restore','Watch')] [string] $Mode = 'Setup',
    [switch] $SkipMigration,
    [switch] $SkipDownload,
    [switch] $SkipOptimize,
    [switch] $SkipGit,
    [switch] $DryRun,
    [int]    $WatchIntervalSeconds = 5
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

try {
    $enUS = [System.Globalization.CultureInfo]::GetCultureInfo('en-US')
    [System.Threading.Thread]::CurrentThread.CurrentCulture   = $enUS
    [System.Threading.Thread]::CurrentThread.CurrentUICulture = $enUS
    [System.Globalization.CultureInfo]::DefaultThreadCurrentCulture   = $enUS
    [System.Globalization.CultureInfo]::DefaultThreadCurrentUICulture = $enUS
} catch { }

# ---------------------------------------------------------------------------
# Bootstrap (modular run): import modules. The all-in-one launcher inlines them.
# ---------------------------------------------------------------------------
$ScriptDir  = Split-Path -Parent $MyInvocation.MyCommand.Path
$ModulesDir = Join-Path $ScriptDir 'Modules'
$ConfigDir  = Join-Path $ScriptDir 'config'
if (Test-Path -LiteralPath $ModulesDir) {
    foreach ($m in @('EsdeLogging','ConfigParser','Hardware','ProfileGeneration','EsdeDiscovery',
                     'BackupEngine','MediaClassification','MediaReorganization','RetroBatMigration',
                     'MetadataRepair','DuplicateDetection','MissingMedia','MediaDownload','Cleanup',
                     'EmulatorDetection','GraphicsOptimization','ControllerManagement','Reporting','GitIntegration')) {
        Import-Module (Join-Path $ModulesDir "$m.psm1") -Force -DisableNameChecking
    }
}

# ---------------------------------------------------------------------------
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

function Resolve-EmulatorsRoot {
    param([string] $RetroBatRoot, [System.Collections.Specialized.OrderedDictionary] $Layout)
    $cands = New-Object System.Collections.Generic.List[string]
    if ($RetroBatRoot) { $cands.Add((Join-Path $RetroBatRoot 'emulators')) }
    $cands.Add((Join-Path (Split-Path $Layout.DataDir -Parent) 'emulators'))
    foreach ($p in @('C:\RetroBat\emulators','D:\RetroBat\emulators','E:\RetroBat\emulators')) { $cands.Add($p) }
    foreach ($c in ($cands | Select-Object -Unique)) { if ($c -and (Test-Path -LiteralPath $c)) { return $c } }
    return $null
}

function Resolve-RetroBatRoms {
    param([string] $RetroBatRoot, [System.Collections.Specialized.OrderedDictionary] $Layout)
    $cands = New-Object System.Collections.Generic.List[string]
    if ($RetroBatRoot) { $cands.Add((Join-Path $RetroBatRoot 'roms')) }
    $cands.Add($Layout.RomDir)
    foreach ($p in @('C:\RetroBat\roms','D:\RetroBat\roms','E:\RetroBat\roms')) { $cands.Add($p) }
    foreach ($c in ($cands | Select-Object -Unique)) { if ($c -and (Test-Path -LiteralPath $c)) { return $c } }
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
    foreach ($c in $Controllers) {
        & $LCtl "Controller: $($c.FriendlyName) [VID=$($c.Vid) PID=$($c.Pid)] $($c.Family)/$($c.ApiType)/$($c.Connection) - $($c.Vendor)" 'INFO'
    }
    $emuRoot = Resolve-EmulatorsRoot -RetroBatRoot $RetroBatRoot -Layout $Layout
    if ($emuRoot) {
        $ra = Join-Path $emuRoot 'retroarch\autoconfig'
        foreach ($c in $Controllers) { Write-RetroArchControllerProfile -Controller $c -AutoconfigDir $ra -Logger $LCtl | Out-Null }
    }
    if (-not $DryRun) {
        Write-EmulationStationInput -Controllers $Controllers -EsInputPath $Layout.InputFile -BackupRoot $BackupDir -Logger $LCtl | Out-Null
    }
}

# ===========================================================================
# FULL SETUP PIPELINE
# ===========================================================================
function Invoke-EsdeSetup {
    $report = [ordered]@{
        GeneratedAt = (Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
        EsdeVersion = $Layout.Version; DataDir = $Layout.DataDir; RomDir = $Layout.RomDir; MediaDir = $Layout.MediaDir
        Tier = ''; Profile = @{ TargetWidth = 0; TargetHeight = 0 }; Hardware = @{}
        Systems = @(); Migration = @{ PerSystem = @(); TotalCopied = 0 }
        Media = @{ PerSystem = @(); TotalMoved = 0 }; Metadata = @{ PerSystem = @() }
        Optimization = @(); Controllers = @(); MissingMedia = @{ PerSystem = @() }
        Duplicates = @{ Groups=@(); TotalFiles=0; DuplicateFiles=0; ReclaimableBytes=0 }
        Bios = @(); Warnings = 0; Errors = 0
    }

    Write-EsdeSection -Title 'ES-DE Auto Suite' -Category 'Main'
    & $LMain "ES-DE data dir: $($Layout.DataDir)  (version $($Layout.Version))" 'INFO'
    & $LMain "ROM dir: $($Layout.RomDir)" 'INFO'
    & $LMain "Media dir: $($Layout.MediaDir)" 'INFO'
    if ($DryRun) { & $LMain "DRY-RUN: no files will be written." 'WARN' }

    $mediaDefs = Get-MediaDefinitions -DefinitionPath (Join-Path $ConfigDir 'esde-media.json')
    $emuDefs   = Get-EmulatorDefinitions -DefinitionPath (Join-Path $ConfigDir 'emulators.json')

    # ---- Phase 1: discovery ----
    Write-EsdeSection -Title 'Phase 1 - ES-DE Discovery' -Category 'Main'
    foreach ($k in $Layout.Exists.Keys) { & $LMain ("  {0,-18} {1}" -f $k, $(if($Layout.Exists[$k]){'present'}else{'MISSING'})) 'INFO' }
    $systems = @(Get-EsdeSystems -Layout $Layout)
    & $LMain "Detected $($systems.Count) system(s)." 'SUCCESS'
    $report.Systems = @($systems | ForEach-Object { @{ Name=$_.Name; Roms=$_.HasRoms; Gamelist=$_.HasGamelist; Media=$_.HasMedia } })

    # ---- Phase 2: hardware + profile ----
    Write-EsdeSection -Title 'Phase 2 - Hardware Detection & Profile' -Category 'Main'
    $hw = Get-SystemHardware
    & $LMain "CPU: $($hw.CpuName) | GPU: $($hw.GpuName) [$($hw.GpuVendor)] $($hw.GpuVramMB)MB | RAM: $($hw.TotalRamGB)GB | $($hw.DisplayWidth)x$($hw.DisplayHeight)" 'INFO'
    Save-Profiles -ProfilesDir (Join-Path $WorkRoot 'profiles') -Logger $LMain | Out-Null
    $sel = Select-ProfileForHardware -Hardware $hw -Logger $LMain
    $tier = $sel.Tier; $profile = $sel.Profile
    $report.Tier = $tier
    $report.Profile = @{ TargetWidth = $profile.TargetWidth; TargetHeight = $profile.TargetHeight }
    $report.Hardware = @{ CpuName=$hw.CpuName; GpuName=$hw.GpuName; GpuVendor=$hw.GpuVendor; GpuVramMB=$hw.GpuVramMB; TotalRamGB=$hw.TotalRamGB; DisplayWidth=$hw.DisplayWidth; DisplayHeight=$hw.DisplayHeight; RefreshRateHz=$hw.RefreshRateHz }

    # ---- Phase 3: backup snapshot ----
    Write-EsdeSection -Title 'Phase 3 - Backup Snapshot' -Category 'Main'
    if (-not $DryRun) {
        $snap = Backup-Tree -SourceDir $Layout.Gamelists -BackupRoot $BackupDir -Label 'gamelists'
        if ($snap) { & $LMain "Backed up $($snap.FileCount) gamelist file(s)." 'SUCCESS' }
        Backup-File -Path $Layout.SettingsFile -BackupRoot $BackupDir | Out-Null
    } else { & $LMain "[DRY-RUN] Backup snapshot skipped." 'INFO' }

    # ---- Phase 4: RetroBat migration ----
    Write-EsdeSection -Title 'Phase 4 - RetroBat Media Migration' -Category 'Migration'
    if (-not $SkipMigration) {
        $rbRoms = Resolve-RetroBatRoms -RetroBatRoot $RetroBatRoot -Layout $Layout
        if ($rbRoms) {
            & $LMig "RetroBat ROM/media source: $rbRoms" 'INFO'
            foreach ($sysDir in (Get-ChildItem -LiteralPath $rbRoms -Directory -ErrorAction SilentlyContinue)) {
                if (-not (Test-RetroBatMediaLayout -SystemRomDir $sysDir.FullName)) { continue }
                $sysMedia = Join-Path $Layout.MediaDir $sysDir.Name
                $st = Invoke-SystemMigration -SystemRomDir $sysDir.FullName -SystemMediaDir $sysMedia -Definitions $mediaDefs -BackupRoot $BackupDir -Logger $LMig -DryRun:$DryRun
                $report.Migration.PerSystem += @{ System=$sysDir.Name; FromGamelist=$st.FromGamelist; FromFolders=$st.FromFolders; Skipped=$st.Skipped }
                $report.Migration.TotalCopied += ($st.FromGamelist + $st.FromFolders)
            }
            & $LMig "Migration total: $($report.Migration.TotalCopied) media file(s) copied." 'SUCCESS'
        } else { & $LMig "No RetroBat ROM/media source found; skipping migration." 'WARN' }
    } else { & $LMig "Migration skipped by request." 'INFO' }

    # ---- Phase 5: media reorganization ----
    Write-EsdeSection -Title 'Phase 5 - Media Reorganization' -Category 'Media'
    foreach ($sys in $systems) {
        $st = Invoke-MediaReorganization -SystemMediaDir $sys.MediaDir -Definitions $mediaDefs -BackupRoot $BackupDir -Logger $LMedia -DryRun:$DryRun
        $report.Media.PerSystem += @{ System=$sys.Name; FoldersCreated=$st.FoldersCreated; Moved=$st.Moved; Skipped=$st.Skipped }
        $report.Media.TotalMoved += $st.Moved
    }
    & $LMedia "Reorganization total: $($report.Media.TotalMoved) file(s) moved." 'SUCCESS'

    # ---- Phase 6: metadata repair ----
    Write-EsdeSection -Title 'Phase 6 - Metadata Repair' -Category 'Metadata'
    foreach ($sys in $systems) {
        if (-not (Test-Path -LiteralPath $sys.Gamelist)) { continue }
        $st = Repair-Gamelist -GamelistPath $sys.Gamelist -MediaDir $sys.MediaDir -BackupRoot $BackupDir -Logger $LMeta -DryRun:$DryRun
        $report.Metadata.PerSystem += @{ System=$sys.Name; Games=$st.Games; Duplicates=$st.Duplicates; Repaired=$st.Repaired; Removed=$st.Removed; Invalid=$st.Invalid }
    }

    # ---- Phase 7: duplicate detection ----
    Write-EsdeSection -Title 'Phase 7 - Duplicate Detection' -Category 'Media'
    $dup = Find-DuplicateMedia -MediaDir $Layout.MediaDir
    & $LMedia "Hashed $($dup.TotalFiles) media file(s): $($dup.DuplicateFiles) duplicate(s), $([math]::Round($dup.ReclaimableBytes/1MB,2)) MB reclaimable." 'INFO'
    $removed = Invoke-DuplicateCleanup -Groups @($dup.Groups) -BackupRoot $BackupDir -Logger $LMedia -DryRun:$DryRun
    if ($removed -gt 0) { & $LMedia "Removed $removed redundant same-folder duplicate(s)." 'SUCCESS' }
    $report.Duplicates = @{ Groups = @($dup.Groups); TotalFiles=$dup.TotalFiles; DuplicateFiles=$dup.DuplicateFiles; ReclaimableBytes=$dup.ReclaimableBytes }

    # ---- Phase 8: missing media analysis ----
    Write-EsdeSection -Title 'Phase 8 - Missing Media Analysis' -Category 'Media'
    $missingPerSystem = @()
    foreach ($sys in $systems) {
        $mm = Get-MissingMediaForSystem -SystemName $sys.Name -SystemRomDir $sys.RomPath -SystemMediaDir $sys.MediaDir -GamelistPath $sys.Gamelist
        $missingPerSystem += $mm
        $report.MissingMedia.PerSystem += @{ System=$mm.System; Games=$mm.Games; Totals=$mm.Totals }
        & $LMedia "$($sys.Name): $($mm.Games) game(s); missing covers=$($mm.Totals.covers) videos=$($mm.Totals.videos) ss=$($mm.Totals.screenshots)." 'INFO'
    }

    # ---- Phase 9: media download (missing only) ----
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
            & $LDown "ScreenScraper credentials not set; downloads skipped (set SS_DEVID/SS_DEVPASSWORD/SS_USER/SS_PASSWORD). Missing-media report still generated." 'WARN'
        }
    } else { & $LDown "Media download skipped by request." 'INFO' }

    # ---- Phase 10: orphan + empty-folder cleanup ----
    Write-EsdeSection -Title 'Phase 10 - Cleanup' -Category 'Media'
    foreach ($sys in $systems) {
        $stems = Get-SystemGameStems -SystemRomDir $sys.RomPath -GamelistPath $sys.Gamelist
        Invoke-OrphanCleanup -SystemName $sys.Name -SystemRomDir $sys.RomPath -SystemMediaDir $sys.MediaDir -RomStems $stems -BackupRoot $BackupDir -Logger $LMedia -DryRun:$DryRun | Out-Null
    }
    $emptyRemoved = Remove-EmptyFolders -Root $Layout.MediaDir -DryRun:$DryRun
    & $LMedia "Removed $emptyRemoved empty media folder(s)." 'INFO'

    # ---- Phase 11: emulator graphics optimization ----
    Write-EsdeSection -Title 'Phase 11 - Emulator Graphics Optimization' -Category 'Optimization'
    if (-not $SkipOptimize) {
        $emuRoot = Resolve-EmulatorsRoot -RetroBatRoot $RetroBatRoot -Layout $Layout
        if ($emuRoot) {
            & $LOpt "Emulators root: $emuRoot (GPU vendor: $($hw.GpuVendor))" 'INFO'
            $emulators = @(Get-InstalledEmulators -EmulatorsRoot $emuRoot -Definitions $emuDefs)
            foreach ($e in ($emulators | Where-Object { $_.Installed })) {
                if ($DryRun) { if ($e.Known -and $e.Supports4K) { & $LOpt "[DRY-RUN] Would optimize $($e.DisplayName)." 'INFO' }; continue }
                $r = Invoke-EmulatorOptimization -Emulator $e -Tier $tier -TargetWidth $profile.TargetWidth -TargetHeight $profile.TargetHeight -BackupRoot $BackupDir -Logger $LOpt -GpuVendor $hw.GpuVendor
                $report.Optimization += @{ Emulator=$e.DisplayName; Result=$(if($r.Success){'optimized'}else{$r.Message}) }
            }
        } else { & $LOpt "No emulators root found; skipping graphics optimization." 'WARN' }
    } else { & $LOpt "Optimization skipped by request." 'INFO' }

    # ---- Phase 12: controllers ----
    Write-EsdeSection -Title 'Phase 12 - Controller Configuration' -Category 'Controllers'
    $vendorMap = ConvertTo-Ht $emuDefs.controllerVendors
    $controllers = @(Get-ConnectedControllers -VendorMap $vendorMap)
    if ($controllers.Count -eq 0) { & $LCtl "No controllers connected. Use Watch mode for hotswap." 'WARN' }
    else {
        if (-not $DryRun) { Set-EsdeControllers -Controllers $controllers } else { foreach($c in $controllers){ & $LCtl "[DRY-RUN] Would configure $($c.FriendlyName)." 'INFO' } }
        $report.Controllers = @($controllers | ForEach-Object { @{ Name=$_.FriendlyName; Vendor=$_.Vendor; Family=$_.Family; Api=$_.ApiType; Connection=$_.Connection; VidPid="$($_.Vid):$($_.Pid)" } })
    }

    # ---- Phase 13: BIOS validation ----
    Write-EsdeSection -Title 'Phase 13 - BIOS Validation' -Category 'Main'
    $biosDir = $null
    $emuRoot2 = Resolve-EmulatorsRoot -RetroBatRoot $RetroBatRoot -Layout $Layout
    $biosCandidates = New-Object System.Collections.Generic.List[string]
    $biosCandidates.Add((Join-Path (Split-Path $Layout.RomDir -Parent) 'bios'))
    $biosCandidates.Add((Join-Path $Layout.RomDir 'bios'))
    if ($emuRoot2)     { $biosCandidates.Add((Join-Path $emuRoot2 'retroarch\system')) }
    if ($RetroBatRoot) { $biosCandidates.Add((Join-Path $RetroBatRoot 'bios')) }
    foreach ($cand in $biosCandidates) {
        if ($cand -and (Test-Path -LiteralPath $cand)) { $biosDir = $cand; break }
    }
    if ($biosDir) {
        $b = Test-BiosDirectory -BiosDir $biosDir -Requirements @($mediaDefs.biosRequirements) -Logger $LMain
        $report.Bios = @($b.Missing)
        & $LMain "BIOS dir: $biosDir ($($b.Present) present, $(@($b.Missing).Count) missing)." 'INFO'
    } else { & $LMain "No BIOS directory found." 'WARN' }

    # ---- Phase 14: reports ----
    Write-EsdeSection -Title 'Phase 14 - Reports' -Category 'Main'
    $report.Warnings = 0; $report.Errors = 0
    Write-EsdeReports -ReportsDir $ReportsDir -Data $report -Logger $LMain

    # ---- Phase 15: git ----
    if (-not $SkipGit -and -not $DryRun) {
        Write-EsdeSection -Title 'Phase 15 - Git Integration' -Category 'Git'
        $msg = "ES-DE auto suite: $($report.Migration.TotalCopied) migrated, $($report.Media.TotalMoved) reorganized, $(@($systems).Count) systems, tier=$tier."
        Invoke-GitCommitAndPush -RepoPath $Layout.DataDir -CommitMessage $msg -Logger $LGit | Out-Null
    } elseif ($DryRun) { & $LGit "[DRY-RUN] Git skipped." 'INFO' } else { & $LGit "Git skipped by request." 'INFO' }

    Write-EsdeSection -Title 'ES-DE Auto Suite Complete' -Category 'Main'
    & $LMain "Done. Logs: $LogsDir | Reports: $ReportsDir | Backups: $BackupDir" 'SUCCESS'
}

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
try {
    $emuDefsForMode = Get-EmulatorDefinitions -DefinitionPath (Join-Path $ConfigDir 'emulators.json')
    switch ($Mode) {
        'Watch'   { Start-EsdeWatcher -EmuDefs $emuDefsForMode }
        'Restore' { Invoke-EsdeRestore }
        default   { Invoke-EsdeSetup }
    }
    exit 0
} catch {
    Write-EsdeLog -Message "FATAL: $($_.Exception.Message)" -Level ERROR -Category 'Main'
    Write-EsdeLog -Message $_.ScriptStackTrace -Level DEBUG -Category 'Main'
    exit 1
}
