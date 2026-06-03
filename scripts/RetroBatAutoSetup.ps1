<#
.SYNOPSIS
    RetroBat Auto Setup - master orchestrator.
.DESCRIPTION
    Discovers RetroBat, detects and (optionally) installs emulators, detects
    hardware and selects a profile, applies 4K-aware graphics optimization,
    configures controllers, validates and repairs the environment, and commits
    the resulting configuration to git. Also hosts the controller hotswap watcher.

    This script is normally invoked by RetroBatAutoSetup.bat but can be run
    directly:  powershell -ExecutionPolicy Bypass -File RetroBatAutoSetup.ps1

.PARAMETER RetroBatRoot
    Override the auto-detected RetroBat root.
.PARAMETER Mode
    Setup (default) runs the full pipeline once.
    Watch runs the controller hotswap watcher (blocking).
    Restore rolls back every configuration file from its most recent backup.
.PARAMETER SkipInstall
    Skip auto-installation of missing emulators.
.PARAMETER SkipGit
    Skip the git commit/push phase.
.PARAMETER DryRun
    Preview every change without writing anything (read-only).
.PARAMETER WatchIntervalSeconds
    Polling interval for the hotswap watcher (default 5).
#>

[CmdletBinding()]
param(
    [string] $RetroBatRoot,
    [ValidateSet('Setup', 'Watch', 'Restore')]
    [string] $Mode = 'Setup',
    [switch] $SkipInstall,
    [switch] $SkipGit,
    [switch] $DryRun,
    [int]    $WatchIntervalSeconds = 5
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# ---------------------------------------------------------------------------
# UPGRADE: force all output, formatting and .NET exception messages to English
# regardless of the host OS locale. Without this, errors surface in the system
# language (e.g. Arabic) which makes logs hard to share and search.
# ---------------------------------------------------------------------------
try {
    $enUS = [System.Globalization.CultureInfo]::GetCultureInfo('en-US')
    [System.Threading.Thread]::CurrentThread.CurrentCulture   = $enUS
    [System.Threading.Thread]::CurrentThread.CurrentUICulture = $enUS
    [System.Globalization.CultureInfo]::DefaultThreadCurrentCulture   = $enUS
    [System.Globalization.CultureInfo]::DefaultThreadCurrentUICulture = $enUS
    $PSDefaultParameterValues['*:Encoding'] = 'utf8'
} catch { }

# ----------------------------------------------------------------------------
# Bootstrap: locate ourselves and import modules.
# ----------------------------------------------------------------------------
$ScriptDir  = Split-Path -Parent $MyInvocation.MyCommand.Path
$ModulesDir = Join-Path $ScriptDir 'Modules'
$ConfigDir  = Join-Path (Split-Path -Parent $ScriptDir) 'config'

$moduleFiles = @(
    'Logging.psm1', 'ConfigParser.psm1', 'Hardware.psm1', 'RetroBatDiscovery.psm1',
    'EmulatorDetection.psm1', 'EmulatorInstall.psm1', 'GraphicsOptimization.psm1',
    'ControllerManagement.psm1', 'ProfileGeneration.psm1', 'ConfigValidation.psm1',
    'GitIntegration.psm1'
)
foreach ($m in $moduleFiles) {
    $path = Join-Path $ModulesDir $m
    if (-not (Test-Path -LiteralPath $path)) {
        Write-Host "FATAL: required module missing: $path" -ForegroundColor Red
        exit 2
    }
    Import-Module $path -Force -DisableNameChecking
}

# ----------------------------------------------------------------------------
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
        & $Logger "Detected controller: $($c.FriendlyName) [VID=$($c.Vid) PID=$($c.Pid)] family=$($c.Family) api=$($c.ApiType) conn=$($c.Connection) vendor=$($c.Vendor)" 'INFO'
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
    $defPath     = Join-Path $ConfigDir 'emulators.json'
    $definitions = Get-EmulatorDefinitions -DefinitionPath $defPath
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
    $emulators = @(Get-InstalledEmulators -EmulatorsRoot $Layout.Emulators -Definitions $definitions)
    foreach ($e in $emulators) {
        $state = if ($e.Installed) { 'INSTALLED' } else { 'missing' }
        $kind  = if ($e.Known) { 'known' } else { 'discovered' }
        & $LogEmulator ("  [{0,-10}] {1,-12} {2}" -f $state, $kind, $e.DisplayName) 'INFO'
    }

    # ---- Phase 5: Auto-install missing emulators ----
    if (-not $SkipInstall) {
        Write-LogSection -Title 'Phase 5 - Auto-Install Missing Emulators' -Category 'Installation'
        # NOTE: wrap in @() so a single result is not unwrapped to a scalar;
        # Windows PowerShell + StrictMode would otherwise throw on .Count.
        $missing = @(Get-MissingRequiredEmulators -Emulators $emulators)
        if ($missing.Count -eq 0) {
            & $LogInstall "No installable emulators are missing." 'SUCCESS'
        } elseif ($DryRun) {
            & $LogInstall "[DRY-RUN] Would install: $(( $missing | ForEach-Object { $_.Id }) -join ', ')" 'INFO'
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

    # ---- Phase 6: Graphics optimization (GPU-vendor aware) ----
    Write-LogSection -Title 'Phase 6 - 4K Graphics Optimization' -Category 'Emulator'
    & $LogEmulator "GPU-aware tuning active for vendor: $($hw.GpuVendor)." 'INFO'
    $optimizedCount = 0
    foreach ($e in @($emulators | Where-Object { $_.Installed })) {
        if ($DryRun) {
            if ($e.Known -and $e.Supports4K) { & $LogEmulator "[DRY-RUN] Would optimize $($e.DisplayName) for $($profile.TargetWidth)x$($profile.TargetHeight)." 'INFO' }
            continue
        }
        $r = Invoke-EmulatorOptimization -Emulator $e -Tier $tier `
                -TargetWidth $profile.TargetWidth -TargetHeight $profile.TargetHeight `
                -BackupRoot $BackupDir -Logger $LogEmulator -GpuVendor $hw.GpuVendor
        if ($r.Success) { $optimizedCount++ }
        elseif ($r.Message -ne 'No optimizer (unknown emulator).') {
            & $LogEmulator "  -> $($e.DisplayName): $($r.Message)" 'WARN'
        }
    }

    # ---- Phase 7: Controller configuration ----
    Write-LogSection -Title 'Phase 7 - Controller Auto-Configuration' -Category 'Controller'
    $vendorMap   = ConvertTo-Hashtable -Object $definitions.controllerVendors
    $controllers = @(Get-ConnectedControllers -VendorMap $vendorMap)
    if ($controllers.Count -eq 0) {
        & $LogController "No controllers currently connected. Use Watch mode for hotswap configuration." 'WARN'
    } elseif ($DryRun) {
        foreach ($c in $controllers) { & $LogController "[DRY-RUN] Would configure $($c.Name) [$($c.Vendor)] ($($c.Connection))." 'INFO' }
    } else {
        Set-ControllerConfiguration -Controllers $controllers -Layout $Layout -BackupDir $BackupDir -Logger $LogController
    }

    # ---- Phase 8: Validation & repair ----
    Write-LogSection -Title 'Phase 8 - Configuration Validation & Repair' -Category 'Setup'
    $allIssues = New-Object System.Collections.Generic.List[object]
    if ($DryRun) {
        & $LogSetup "[DRY-RUN] Validation runs read-only; no repairs are applied." 'INFO'
        Test-BiosFiles -BiosDir $Layout.Bios -Logger $LogSetup | ForEach-Object { $allIssues.Add($_) }
    } else {
        Test-RetroBatPaths   -Layout $Layout -Logger $LogSetup            | ForEach-Object { $allIssues.Add($_) }
        Test-BiosFiles       -BiosDir $Layout.Bios -Logger $LogSetup      | ForEach-Object { $allIssues.Add($_) }
        Test-EmulatorConfigs -Emulators $emulators -BackupRoot $BackupDir -Logger $LogSetup | ForEach-Object { $allIssues.Add($_) }
    }

    $errors   = @($allIssues | Where-Object { $_.Severity -eq 'Error'   -and -not $_.Repaired })
    $warnings = @($allIssues | Where-Object { $_.Severity -eq 'Warning' -and -not $_.Repaired })
    & $LogSetup "Validation complete: $($errors.Count) unresolved error(s), $($warnings.Count) warning(s)." `
        $(if ($errors.Count -gt 0) { 'WARN' } else { 'SUCCESS' })

    # ---- UPGRADE: HTML dashboard report ----
    try {
        $reportPath = Join-Path $LogsDir 'RetroBatAutoSetup-Report.html'
        Write-HtmlReport -Path $reportPath -Hardware $hw -Layout $Layout -Tier $tier `
            -Profile $profile -Emulators $emulators -Controllers $controllers -Issues $allIssues.ToArray()
        & $LogSetup "HTML report written: $reportPath" 'SUCCESS'
    } catch {
        & $LogSetup "Could not write HTML report: $($_.Exception.Message)" 'WARN'
    }

    # ---- Phase 9: Git integration ----
    if ($DryRun) {
        & $LogSetup "[DRY-RUN] Git commit/push skipped." 'INFO'
    } elseif (-not $SkipGit) {
        Write-LogSection -Title 'Phase 9 - Git Integration' -Category 'Setup'
        $installedCount = @($emulators | Where-Object { $_.Installed }).Count
        $msg  = "RetroBat auto-setup: tier=$tier, $($profile.TargetWidth)x$($profile.TargetHeight), "
        $msg += "$installedCount emulator(s) configured, $($controllers.Count) controller(s)."
        Invoke-GitCommitAndPush -RepoPath $resolvedRoot -CommitMessage $msg -Logger $LogSetup | Out-Null
    } else {
        & $LogSetup "Git integration skipped by request (-SkipGit)." 'INFO'
    }

    # ---- Final summary ----
    Write-LogSection -Title 'RetroBat Auto Setup Complete' -Category 'Setup'
    $installedTotal = @($emulators | Where-Object { $_.Installed }).Count
    & $LogSetup "Summary: $installedTotal emulator(s) installed, $optimizedCount optimized for $($profile.TargetWidth)x$($profile.TargetHeight), $($controllers.Count) controller(s), $($warnings.Count) warning(s)." 'SUCCESS'
    & $LogSetup "All phases finished. Logs are in: $LogsDir" 'SUCCESS'
}

function Write-HtmlReport {
    <#
    .SYNOPSIS
        UPGRADE: writes a self-contained HTML dashboard summarizing the run.
    #>
    [CmdletBinding()]
    param(
        [string] $Path,
        [System.Collections.Specialized.OrderedDictionary] $Hardware,
        [System.Collections.Specialized.OrderedDictionary] $Layout,
        [string] $Tier,
        [System.Collections.Specialized.OrderedDictionary] $Profile,
        [object[]] $Emulators,
        [object[]] $Controllers,
        [object[]] $Issues
    )

    function HtmlEnc([string]$s) { if ($null -eq $s) { return '' } [System.Net.WebUtility]::HtmlEncode($s) }

    $installed = @($Emulators | Where-Object { $_.Installed })
    $known     = @($Emulators | Where-Object { $_.Known })
    $generated = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'

    $emuRows = ($Emulators | Sort-Object @{e={-([int]$_.Known)}}, DisplayName | ForEach-Object {
        $badge = if ($_.Installed) { '<span class="ok">INSTALLED</span>' } else { '<span class="miss">missing</span>' }
        $kind  = if ($_.Known) { 'known' } else { 'discovered' }
        "<tr><td>$(HtmlEnc $_.DisplayName)</td><td>$kind</td><td>$badge</td><td class='mono'>$(HtmlEnc $_.ConfigType)</td></tr>"
    }) -join "`n"

    $ctrlRows = if ($Controllers -and $Controllers.Count) {
        ($Controllers | ForEach-Object {
            "<tr><td>$(HtmlEnc $_.FriendlyName)</td><td>$(HtmlEnc $_.Vendor)</td><td>$(HtmlEnc $_.Family)</td><td>$(HtmlEnc $_.ApiType)</td><td>$(HtmlEnc $_.Connection)</td><td class='mono'>$(HtmlEnc $_.Vid):$(HtmlEnc $_.Pid)</td></tr>"
        }) -join "`n"
    } else { "<tr><td colspan='6'>No controllers connected.</td></tr>" }

    $biosMissing = @($Issues | Where-Object { $_.Type -eq 'Bios' })
    $biosRows = if ($biosMissing.Count) {
        ($biosMissing | ForEach-Object { "<tr><td class='mono'>$(HtmlEnc $_.Item)</td><td>$(HtmlEnc $_.Detail)</td></tr>" }) -join "`n"
    } else { "<tr><td colspan='2' class='ok'>All tracked BIOS files present.</td></tr>" }

    $html = @"
<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>RetroBat Auto Setup Report</title>
<style>
 body{font-family:Segoe UI,Arial,sans-serif;background:#12141a;color:#e6e6e6;margin:0;padding:24px}
 h1{color:#7fd1ff;margin:0 0 4px} h2{color:#9ad19a;border-bottom:1px solid #2a2f3a;padding-bottom:6px;margin-top:28px}
 .sub{color:#8a93a6;margin-bottom:18px}
 .cards{display:flex;flex-wrap:wrap;gap:12px}
 .card{background:#1b1f29;border:1px solid #2a2f3a;border-radius:10px;padding:14px 18px;min-width:160px}
 .card .k{color:#8a93a6;font-size:12px;text-transform:uppercase} .card .v{font-size:18px;margin-top:4px}
 table{border-collapse:collapse;width:100%;margin-top:10px;background:#1b1f29;border-radius:8px;overflow:hidden}
 th,td{padding:8px 12px;text-align:left;border-bottom:1px solid #2a2f3a;font-size:14px}
 th{background:#222735;color:#bcd}
 .ok{color:#7ee27e;font-weight:600} .miss{color:#e2a05a} .mono{font-family:Consolas,monospace;color:#9fb3c8}
 .footer{margin-top:26px;color:#6b7280;font-size:12px}
</style></head><body>
<h1>RetroBat Auto Setup &mdash; Report</h1>
<div class="sub">Generated $generated &bull; Root: $(HtmlEnc $Layout.Root) &bull; RetroBat $(HtmlEnc $Layout.Version)</div>
<div class="cards">
 <div class="card"><div class="k">Performance tier</div><div class="v">$Tier</div></div>
 <div class="card"><div class="k">Target resolution</div><div class="v">$($Profile.TargetWidth) x $($Profile.TargetHeight)</div></div>
 <div class="card"><div class="k">Emulators installed</div><div class="v">$($installed.Count) / $($known.Count) known</div></div>
 <div class="card"><div class="k">Controllers</div><div class="v">$(@($Controllers).Count)</div></div>
</div>
<h2>Hardware</h2>
<div class="cards">
 <div class="card"><div class="k">CPU</div><div class="v">$(HtmlEnc $Hardware.CpuName)</div></div>
 <div class="card"><div class="k">GPU</div><div class="v">$(HtmlEnc $Hardware.GpuName) ($(HtmlEnc $Hardware.GpuVendor))</div></div>
 <div class="card"><div class="k">VRAM</div><div class="v">$($Hardware.GpuVramMB) MB</div></div>
 <div class="card"><div class="k">RAM</div><div class="v">$($Hardware.TotalRamGB) GB</div></div>
 <div class="card"><div class="k">Storage</div><div class="v">$(HtmlEnc $Hardware.SystemDriveType)</div></div>
 <div class="card"><div class="k">Display</div><div class="v">$($Hardware.DisplayWidth)x$($Hardware.DisplayHeight) @ $($Hardware.RefreshRateHz)Hz</div></div>
</div>
<h2>Emulators</h2>
<table><tr><th>Emulator</th><th>Source</th><th>Status</th><th>Config</th></tr>
$emuRows
</table>
<h2>Controllers</h2>
<table><tr><th>Name</th><th>Vendor</th><th>Family</th><th>API</th><th>Connection</th><th>VID:PID</th></tr>
$ctrlRows
</table>
<h2>Missing BIOS</h2>
<table><tr><th>File</th><th>Needed for</th></tr>
$biosRows
</table>
<div class="footer">RetroBat Auto Setup &bull; This report is regenerated on every run.</div>
</body></html>
"@
    [System.IO.File]::WriteAllText($Path, $html, (New-Object System.Text.UTF8Encoding($false)))
}

function Invoke-RestoreMode {
    <#
    .SYNOPSIS
        UPGRADE: rolls back every configuration file from its most recent backup
        in the Backups folder, restoring the state before the last optimization.
    #>
    Write-LogSection -Title 'RetroBat Auto Setup - Restore From Backups' -Category 'Setup'
    if (-not (Test-Path -LiteralPath $BackupDir)) {
        & $LogSetup "No Backups folder found at $BackupDir. Nothing to restore." 'WARN'
        return
    }

    # Backups are named <originalfilename>.<timestamp>.bak; group by original name
    # and restore the newest backup of each, writing it next to where it belongs.
    $backups = Get-ChildItem -LiteralPath $BackupDir -Filter '*.bak' -File -ErrorAction SilentlyContinue
    if (-not $backups -or @($backups).Count -eq 0) {
        & $LogSetup "Backups folder is empty. Nothing to restore." 'WARN'
        return
    }

    # Build an index of every config file currently under the RetroBat tree so we
    # can map a backup's original leaf name back to its real location(s).
    & $LogSetup "Indexing current configuration files under $($Layout.Root)..." 'INFO'
    $index = @{}
    foreach ($root in @($Layout.Emulators, $Layout.EmulationStationData, $Layout.System)) {
        if (-not (Test-Path -LiteralPath $root)) { continue }
        Get-ChildItem -LiteralPath $root -Recurse -File -Include *.ini,*.cfg,*.xml,*.yml,*.json,*.toml,*.config -ErrorAction SilentlyContinue | ForEach-Object {
            $key = $_.Name.ToLower()
            if (-not $index.ContainsKey($key)) { $index[$key] = New-Object System.Collections.Generic.List[string] }
            $index[$key].Add($_.FullName)
        }
    }

    $restored = 0; $skipped = 0
    $groups = $backups | Group-Object { ($_.Name -replace '\.\d{8}_\d{6}\.bak$', '') }
    foreach ($g in $groups) {
        $newest = $g.Group | Sort-Object LastWriteTime -Descending | Select-Object -First 1
        $leaf   = $g.Name.ToLower()
        if ($index.ContainsKey($leaf)) {
            foreach ($target in $index[$leaf]) {
                Copy-Item -LiteralPath $newest.FullName -Destination $target -Force
                & $LogSetup "Restored $target  <-  $($newest.Name)" 'SUCCESS'
                $restored++
            }
        } else {
            & $LogSetup "No current location found for '$($g.Name)'; left backup in place." 'WARN'
            $skipped++
        }
    }
    & $LogSetup "Restore complete: $restored file(s) restored, $skipped backup(s) had no current target." 'SUCCESS'
}

# ----------------------------------------------------------------------------
# Entry point
# ----------------------------------------------------------------------------
try {
    if ($DryRun) { Write-Log -Message "DRY-RUN mode: no files will be written." -Level WARN -Category 'Setup' }
    if ($Mode -eq 'Watch') {
        $defPath     = Join-Path $ConfigDir 'emulators.json'
        $definitions = Get-EmulatorDefinitions -DefinitionPath $defPath
        Start-HotswapWatcher -Layout $Layout -Definitions $definitions -BackupDir $BackupDir -Interval $WatchIntervalSeconds
    } elseif ($Mode -eq 'Restore') {
        Invoke-RestoreMode
    } else {
        Invoke-FullSetup
    }
    exit 0
} catch {
    Write-Log -Message "FATAL: $($_.Exception.Message)" -Level ERROR -Category 'Setup'
    Write-Log -Message $_.ScriptStackTrace -Level DEBUG -Category 'Setup'
    exit 1
}
