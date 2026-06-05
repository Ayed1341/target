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

Export-ModuleMember -Function Set-RetroArchExtras, Backup-AllEmulatorConfigs
