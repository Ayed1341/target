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

Export-ModuleMember -Function Set-RetroArchShaderPreset, Set-RetroArchLatency
