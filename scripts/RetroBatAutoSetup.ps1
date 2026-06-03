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
.PARAMETER SkipInstall
    Skip auto-installation of missing emulators.
.PARAMETER SkipGit
    Skip the git commit/push phase.
.PARAMETER WatchIntervalSeconds
    Polling interval for the hotswap watcher (default 5).
#>

[CmdletBinding()]
param(
    [string] $RetroBatRoot,
    [ValidateSet('Setup', 'Watch')]
    [string] $Mode = 'Setup',
    [switch] $SkipInstall,
    [switch] $SkipGit,
    [int]    $WatchIntervalSeconds = 5
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

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
        $defPath     = Join-Path $ConfigDir 'emulators.json'
        $definitions = Get-EmulatorDefinitions -DefinitionPath $defPath
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
