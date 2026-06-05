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

Export-ModuleMember -Function Set-RetroArchFeatures, Set-StandaloneHotkeys
