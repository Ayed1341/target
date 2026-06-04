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
    [ValidateSet('Setup','Restore','Watch','Doctor')] [string] $Mode = 'Setup',
    [switch] $SkipMigration,
    [switch] $SkipDownload,
    [switch] $SkipOptimize,
    [switch] $SkipGit,
    [switch] $DryRun,
    [switch] $HashRoms,
    [switch] $GenerateMedia,
    [switch] $TuneEsde,
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
                     'HealthSelfHeal','BackupEngine','MediaClassification','MediaReorganization','RetroBatMigration',
                     'MetadataRepair','DuplicateDetection','MissingMedia','MediaRecovery','MediaAudit','MediaDownload','Cleanup',
                     'EmulatorDetection','EsdeEmulators','EmulatorGap','BiosAdvanced','EsdeEnvironmentAudit','GraphicsOptimization',
                     'ControllerManagement','Reporting','GitIntegration')) {
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
    foreach ($c in $Controllers) {
        & $LCtl "Controller: $($c.FriendlyName) [VID=$($c.Vid) PID=$($c.Pid)] $($c.Family)/$($c.ApiType)/$($c.Connection) - $($c.Vendor)" 'INFO'
    }
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

    $mediaDefs = Get-MediaDefinitions -DefinitionPath (Join-Path $ConfigDir 'esde-media.json')
    $emuDefs   = Get-EmulatorDefinitions -DefinitionPath (Join-Path $ConfigDir 'emulators.json')
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
    $emuDefsForMode = Get-EmulatorDefinitions -DefinitionPath (Join-Path $ConfigDir 'emulators.json')
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
