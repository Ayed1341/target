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
    [switch] $EnrichMeta,
    [switch] $OneGameOneRegion,
    [switch] $Themes,
    [switch] $Schedule,
    [switch] $Shortcut,
    [switch] $AutoFav,
    [switch] $Compress,
    [switch] $InstallEmulators,
    [switch] $AllowPrerelease,
    [switch] $ScrapeAll,
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
                     'MetadataRepair','GamelistEnrich','GamelistQuality','DuplicateDetection','MissingMedia','MediaRecovery','MediaAudit','MediaIntegrity','MediaHygiene','MediaDownload','Cleanup',
                     'EmulatorDetection','EsdeEmulators','EmulatorGap','EmulatorTuning','AdvancedTuning','SystemTuning','RomLibrary','RomVerify','RomCompress','RaPlaylists','LibraryAnalytics','LibraryAnalytics2','LibraryInsights','SaveManager','CollectionsManager','CollectionsPlus','ThemeManager',
                     'BiosAdvanced','EsdeEnvironmentAudit','EsdeUx','SystemOps','PortabilityOps','GraphicsOptimization','XboxEmulators','EmulatorInstall','EmulatorAutoInstall',
                     'ControllerManagement','Reporting','ReportingPlus','GitIntegration')) {
        Import-Module (Join-Path $ModulesDir "$m.psm1") -Force -DisableNameChecking
    }
}

# ---------------------------------------------------------------------------
# Resolve ES-DE + working directories
# ---------------------------------------------------------------------------
# /scrapeall is a focused "just fill my media" mode: force downloads on and skip
# the heavy non-media phases so it stays fast to re-run day after day.
if ($ScrapeAll) { $SkipDownload = $false; $SkipOptimize = $true; $SkipGit = $true }
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
            XboxEmulators = @(); XboxEepromRelocated = 0; XboxEepromValidated = 0; XboxEepromQuarantined = 0
            XboxEepromAutoGen = 0; XboxBiosRelocated = 0; XboxBiosMissing = @(); XboxConfigured = 0; XboxReadiness = @()
            EmulatorsInstalled = @(); EmulatorsInstallFailed = @(); EmulatorsInstallPlanned = 0; EmulatorsRemainingGaps = @()
            ScraperQuota = @{}; MediaDownloaded = 0
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
            # Load credentials from a local git-ignored file if env vars are not set.
            $credDirs = @((Split-Path $LauncherSelfPath -Parent), $EsdeRoot, $Layout.DataDir, (Split-Path $Layout.DataDir -Parent)) | Where-Object { $_ }
            [void](Import-ScraperCredentials -SearchDirs $credDirs -Logger $LDown)
            Reset-ScraperState
            if (Test-ScraperCredentials) {
                if ($ScrapeAll) { & $LDown "Scrape-all mode: filling every missing media item until the library is complete or the daily quota stops us (it resumes on the next run)." 'INFO' }
                $totDl = 0; $closed = $false
                $maxPasses = if ($ScrapeAll) { 25 } else { 1 }
                $pass = 0
                do {
                    $pass++
                    $passDl = 0
                    foreach ($sys in $systems) {
                        if ($closed) { break }
                        # Re-scan missing media each pass in scrape-all mode so already
                        # downloaded items drop out and we converge on a full library.
                        if ($ScrapeAll) {
                            $mm = Get-MissingMediaForSystem -SystemName $sys.Name -SystemRomDir $sys.RomPath -SystemMediaDir $sys.MediaDir -GamelistPath $sys.Gamelist
                        } else {
                            $mm = $missingPerSystem | Where-Object { $_.System -eq $sys.Name } | Select-Object -First 1
                        }
                        if (-not $mm -or @($mm.Records).Count -eq 0) { continue }
                        $d = Invoke-MediaDownloadForSystem -SystemRomDir $sys.RomPath -SystemMediaDir $sys.MediaDir -MissingResult $mm -Logger $LDown -DryRun:$DryRun
                        $totDl += [int]$d.Downloaded; $passDl += [int]$d.Downloaded
                        if (-not $ScrapeAll -or $d.Downloaded -gt 0) { & $LDown "$($sys.Name): attempted=$($d.Attempted) downloaded=$($d.Downloaded) skipped=$($d.Skipped)." 'INFO' }
                        if ($d.Closed) { $closed = $true; break }
                    }
                    if ($ScrapeAll -and -not $closed) { & $LDown "Scrape-all pass $pass complete: $passDl new file(s)." 'INFO' }
                } while ($ScrapeAll -and -not $closed -and $passDl -gt 0 -and $pass -lt $maxPasses -and -not $DryRun)
                $q = Get-ScraperQuotaSummary
                $report.Audit.ScraperQuota = $q
                $report.Audit.MediaDownloaded = $totDl
                # Persist a small resume marker for the user.
                try {
                    $state = @{ lastRun = (Get-Date -Format o); downloadedThisRun = $totDl; quota = $q }
                    ($state | ConvertTo-Json -Depth 5) | Set-Content -LiteralPath (Join-Path $ReportsDir 'scrape_state.json') -Encoding UTF8
                } catch { }
                if ($closed) {
                    & $LDown "Daily ScreenScraper quota reached ($($q.RequestsToday)/$($q.MaxRequestsDay)). $totDl file(s) downloaded this run. Re-run later - it resumes automatically and only fetches what is still missing." 'WARN'
                    Add-HealthFinding 'Downloads' 'Warning' 'ScreenScraper daily quota reached - re-run later to continue (auto-resume).'
                } else {
                    & $LDown "Media download finished: $totDl file(s) this run (quota used $($q.RequestsToday)/$($q.MaxRequestsDay) today)." 'SUCCESS'
                }
            } else {
                $miss = Get-MissingScraperCredentials
                & $LDown "ScreenScraper credentials incomplete (missing: $($miss -join ', ')). Set them as environment variables or in a local 'screenscraper.txt' next to the launcher. Scrape lists exported to Reports." 'WARN'
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

    # ---- Phase 11g: auto-install the best missing emulators (opt-in: /install) ----
    try {
        Write-EsdeSection -Title 'Phase 11g - Auto-Install Emulators' -Category 'Optimization'
        if (-not $InstallEmulators) {
            & $LOpt "Emulator auto-install skipped (pass /install to download & install the best missing emulators)." 'INFO'
        } else {
            $installRoot = Get-EmulatorInstallRoot -Layout $Layout -ExistingRoots @(Get-EmuRoots)
            $plan = @(Get-AutoInstallPlan -Gaps @($report.EmulatorGaps) -Catalog $emuDefs -SystemMap $sysEmuMap -InstallRoot $installRoot -InstalledIds $installedEmuIds)
            $report.Audit.EmulatorsInstallPlanned = $plan.Count
            if ($plan.Count -eq 0) {
                & $LOpt "Nothing to install - every system with ROMs already has a working (or non-downloadable) emulator." 'SUCCESS'
            } elseif (-not (Test-Online)) {
                & $LOpt "Auto-install requested but no internet connection detected; skipping $($plan.Count) install(s)." 'WARN'
                Add-HealthFinding 'EmulatorInstall' 'Warning' 'Offline - emulator installs skipped'
            } else {
                if (-not $DryRun -and -not (Test-Path -LiteralPath $installRoot)) { New-Item -Path $installRoot -ItemType Directory -Force | Out-Null }
                & $LOpt "Install plan: $(@($plan | ForEach-Object { $_.EmulatorId }) -join ', ') -> $installRoot" 'INFO'
                $sevenZip = Get-SevenZipPath -RetroBatRoot $RetroBatRoot
                $installedNow = @()
                foreach ($item in $plan) {
                    $res = Install-EsdeEmulator -Item $item -BackupRoot $BackupDir -Logger $LOpt -SevenZip $sevenZip -AllowPrerelease:$AllowPrerelease -DryRun:$DryRun
                    if ($res.Success) {
                        $report.Audit.EmulatorsInstalled += @{ Id=$item.EmulatorId; Tag=$res.Tag; Systems=@($item.Systems); Exe=$res.ExePath }
                        $installedNow += $item.EmulatorId
                        # (16) Register in ES-DE so it is actually found.
                        Register-EmulatorFindRule -Layout $Layout -EmulatorId $item.EmulatorId -ExePath $res.ExePath -Logger $LOpt -DryRun:$DryRun | Out-Null
                        # (17) Configuration handoff for Xbox emulators we just installed.
                        try {
                            $edir = Split-Path $res.ExePath -Parent
                            if ($item.EmulatorId -eq 'xemu' -and (Get-Command Set-XemuConfig -ErrorAction SilentlyContinue)) {
                                $desc = [pscustomobject]@{ Id='xemu'; Kind='xbox'; Dir=$edir; Exe=$res.ExePath; ConfigPath=(Join-Path $edir 'xemu.toml') }
                                Set-XemuConfig -Emu $desc -Tier $tier -BackupRoot $BackupDir -Logger $LOpt -DryRun:$DryRun | Out-Null
                            } elseif ($item.EmulatorId -eq 'xenia' -and (Get-Command Initialize-XeniaDirs -ErrorAction SilentlyContinue)) {
                                $cfg = if (Test-Path -LiteralPath (Join-Path $edir 'xenia-canary.config.toml')) { 'xenia-canary.config.toml' } else { 'xenia.config.toml' }
                                $desc = [pscustomobject]@{ Id='xenia'; Kind='xbox360'; Dir=$edir; Exe=$res.ExePath; ConfigPath=(Join-Path $edir $cfg) }
                                Initialize-XeniaDirs -Emu $desc -Logger $LOpt -DryRun:$DryRun | Out-Null
                                Set-XeniaConfig -Emu $desc -Tier $tier -GpuVendor $hw.GpuVendor -BackupRoot $BackupDir -Logger $LOpt -DryRun:$DryRun | Out-Null
                            }
                        } catch { & $LOpt "Post-install config for $($item.EmulatorId): $($_.Exception.Message)" 'WARN' }
                    } elseif (-not $DryRun) {
                        $report.Audit.EmulatorsInstallFailed += @{ Id=$item.EmulatorId; Reason=$res.Message }
                        Add-HealthFinding 'EmulatorInstall' 'Warning' "$($item.EmulatorId): $($res.Message)"
                    }
                }
                # (17) Apply graphics optimization to the freshly-installed emulators.
                if (-not $DryRun -and $installedNow.Count -gt 0) {
                    try {
                        $fresh = @(Get-EsdeEmulators -Roots @(Get-EmuRoots) -Definitions $emuDefs) | Where-Object { $_.Installed -and ($installedNow -contains $_.Id) -and $_.Known -and $_.Supports4K }
                        foreach ($e in $fresh) {
                            $r = Invoke-EmulatorOptimization -Emulator $e -Tier $tier -TargetWidth $profile.TargetWidth -TargetHeight $profile.TargetHeight -BackupRoot $BackupDir -Logger $LOpt -GpuVendor $hw.GpuVendor
                            $report.Optimization += @{ Emulator=$e.DisplayName; Result=$(if($r.Success){'optimized (new install)'}else{$r.Message}) }
                        }
                    } catch { & $LOpt "Optimizing new installs: $($_.Exception.Message)" 'WARN' }
                }
                $okN = @($report.Audit.EmulatorsInstalled).Count
                & $LOpt "Auto-install complete: $okN installed, $(@($report.Audit.EmulatorsInstallFailed).Count) failed." $(if ($okN -gt 0) { 'SUCCESS' } else { 'INFO' })
            }
            # (20) Remaining gaps (systems still without a usable / downloadable emulator).
            $installedAfter = @($installedEmuIds + @($report.Audit.EmulatorsInstalled | ForEach-Object { $_.Id }))
            $remaining = @(Get-EmulatorGaps -Systems $systems -InstalledIds $installedAfter -SystemMap $sysEmuMap | Where-Object { $_.Missing } | ForEach-Object { $_.System })
            $report.Audit.EmulatorsRemainingGaps = $remaining
            if ($remaining.Count -gt 0) { & $LOpt "Still needing a manual emulator (no auto-downloadable option, or proprietary keys required): $($remaining -join ', ')." 'WARN' }
        }
    } catch { & $LOpt "Phase 11g error: $($_.Exception.Message)" 'ERROR'; Add-HealthFinding 'EmulatorInstall' 'Error' $_.Exception.Message }

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

    # ---- Phase 13a-xbox: Xbox / Xbox 360 emulators (xemu, Cxbx-Reloaded, xenia) ----
    try {
        Write-EsdeSection -Title 'Phase 13a - Xbox / Xbox 360 Setup' -Category 'Main'
        # $biosDir / $allBiosDirs may be unset if Phase 13 threw early - guard them.
        if (-not (Get-Variable -Name biosDir -Scope Local -ErrorAction SilentlyContinue)) { $biosDir = $null }
        if (-not (Get-Variable -Name allBiosDirs -Scope Local -ErrorAction SilentlyContinue)) { $allBiosDirs = @() }
        # Search roots: emulator roots, ROM dir, BIOS dirs, ES-DE data dir.
        $xboxRoots = New-Object System.Collections.Generic.List[string]
        foreach ($er in @(Get-EmuRoots)) { if ($er) { $xboxRoots.Add($er) } }
        if ($Layout.RomDir)  { $xboxRoots.Add($Layout.RomDir); $xboxRoots.Add((Join-Path $Layout.RomDir 'xbox')); $xboxRoots.Add((Join-Path $Layout.RomDir 'xbox360')) }
        if ($Layout.DataDir) { $xboxRoots.Add($Layout.DataDir) }
        if ($biosDir)        { $xboxRoots.Add($biosDir) }
        foreach ($cand in @($allBiosDirs)) { if ($cand) { $xboxRoots.Add($cand) } }
        $xboxRoots2 = @($xboxRoots | Where-Object { $_ -and (Test-Path -LiteralPath $_) } | Select-Object -Unique)

        $xemus = @(Get-XboxEmulators -Roots $xboxRoots2)
        if ($xemus.Count -eq 0) {
            & $LMain "No Xbox / Xbox 360 emulator (xemu, Cxbx-Reloaded, xenia) detected - skipping Xbox setup." 'INFO'
        } else {
            & $LMain "Detected Xbox emulator(s): $(@($xemus | ForEach-Object { $_.Id }) -join ', ')." 'INFO'
            $report.Audit.XboxEmulators = @($xemus | ForEach-Object { @{ Id=$_.Id; Kind=$_.Kind; Dir=$_.Dir } })

            # eeprom.bin: validate / relocate / enable auto-generation (settings data, safe).
            $ee = Repair-XboxEeprom -XboxEmulators $xemus -SearchRoots $xboxRoots2 -BackupRoot $BackupDir -Logger $LMain -DryRun:$DryRun
            $report.Audit.XboxEepromRelocated   = [int]$ee.Relocated
            $report.Audit.XboxEepromValidated   = [int]$ee.Validated
            $report.Audit.XboxEepromQuarantined = [int]$ee.Quarantined
            $report.Audit.XboxEepromAutoGen     = [int]$ee.AutoGen
            if ($ee.Quarantined -gt 0) { Add-HealthFinding 'Xbox' 'Warning' "$($ee.Quarantined) corrupt eeprom.bin quarantined (regenerated on next launch)" }

            # MCPX boot ROM + Xbox BIOS: relocate/propagate only - copyrighted, never downloaded.
            $xb = Repair-XboxBios -XboxEmulators $xemus -SearchRoots $xboxRoots2 -Logger $LMain -DryRun:$DryRun
            $report.Audit.XboxBiosRelocated = [int]$xb.Relocated
            $missingBios = New-Object System.Collections.Generic.List[string]
            if ($xb.MissingMcpx -gt 0) { $missingBios.Add('mcpx_1.0.bin (MCPX boot ROM)') }
            if ($xb.MissingBios -gt 0) { $missingBios.Add('Xbox BIOS (e.g. Complex_4627.bin)') }
            $report.Audit.XboxBiosMissing = @($missingBios)
            if ($missingBios.Count -gt 0) {
                Add-HealthFinding 'Xbox' 'Warning' "Missing copyrighted Xbox firmware: $($missingBios -join ', ') - supply your own dumps"
            }

            # Per-emulator configuration (paths + 4K graphics + no-boot fixes).
            $configured = 0
            foreach ($emu in $xemus) {
                try {
                    switch ($emu.Id) {
                        'xemu'          { if (Set-XemuConfig  -Emu $emu -Tier $tier -BackupRoot $BackupDir -Logger $LMain -DryRun:$DryRun) { $configured++ } }
                        'cxbx-reloaded' { if (Set-CxbxConfig  -Emu $emu -BackupRoot $BackupDir -Logger $LMain -DryRun:$DryRun) { $configured++ } }
                        default {
                            if ($emu.Kind -eq 'xbox360') {
                                Initialize-XeniaDirs -Emu $emu -Logger $LMain -DryRun:$DryRun | Out-Null
                                if (Set-XeniaConfig -Emu $emu -Tier $tier -GpuVendor $hw.GpuVendor -BackupRoot $BackupDir -Logger $LMain -DryRun:$DryRun) { $configured++ }
                            }
                        }
                    }
                } catch { & $LMain "Xbox config error for $($emu.Id): $($_.Exception.Message)" 'WARN'; Add-HealthFinding 'Xbox' 'Warning' "$($emu.Id) config: $($_.Exception.Message)" }
            }
            $report.Audit.XboxConfigured = $configured

            $report.Audit.XboxReadiness = @(Get-XboxReadiness -XboxEmulators $xemus)
            foreach ($rd in $report.Audit.XboxReadiness) {
                if (-not $rd.Ready) {
                    $lack = @(); if (-not $rd.Mcpx) { $lack += 'MCPX' }; if (-not $rd.Bios) { $lack += 'BIOS' }; if (-not $rd.Hdd) { $lack += 'HDD image' }
                    if ($lack.Count -gt 0) { & $LMain "$($rd.Emulator): not yet bootable - still need $($lack -join ', ')." 'WARN' }
                }
            }
        }
    } catch { & $LMain "Phase 13a (Xbox) error: $($_.Exception.Message)" 'ERROR'; Add-HealthFinding 'Xbox' 'Error' $_.Exception.Message }

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
