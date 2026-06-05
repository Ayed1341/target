<#
.SYNOPSIS
    ROM library analysis and multi-disc .m3u playlist generation.
.DESCRIPTION
    * Per-system ROM statistics: count, total size, by-extension breakdown,
      zero-byte/suspect ROMs, and compressed-format counts.
    * Multi-disc detection: groups "(Disc 1)/(Disc 2)/..." sets and generates an
      .m3u playlist so ES-DE/emulators treat them as a single game (safe, never
      deletes; skips if an .m3u already exists).
    * Compression advisory: lists uncompressed disc images (cue/bin/iso/gdi) that
      could be converted to CHD to save space (advisory only - no conversion).
#>

Set-StrictMode -Version Latest

$script:RomNonGame = @('.txt','.xml','.dat','.jpg','.png','.bin','.sub','.m3u','.srm','.state','.cfg')

function Get-RomLibraryStats {
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][string] $SystemName, [Parameter(Mandatory = $true)][string] $SystemRomDir)
    $count = 0; $bytes = [int64]0; $zero = New-Object System.Collections.Generic.List[string]
    $byExt = @{}; $compressed = 0
    if (Test-Path -LiteralPath $SystemRomDir) {
        Get-ChildItem -LiteralPath $SystemRomDir -File -ErrorAction SilentlyContinue | ForEach-Object {
            $ext = $_.Extension.ToLower()
            if ($ext -eq '.bin' -and (Test-Path -LiteralPath ([System.IO.Path]::ChangeExtension($_.FullName,'cue')))) { return } # part of cue/bin
            if ($script:RomNonGame -contains $ext) { return }
            $count++; $bytes += $_.Length
            if ($_.Length -eq 0) { $zero.Add($_.Name) }
            if (-not $byExt.ContainsKey($ext)) { $byExt[$ext] = 0 }
            $byExt[$ext]++
            if ($ext -in @('.chd','.zip','.7z','.rvz','.cso','.pbp')) { $compressed++ }
        }
    }
    return @{ System=$SystemName; Count=$count; TotalBytes=$bytes; ZeroByte=$zero.ToArray(); ByExt=$byExt; Compressed=$compressed }
}

function New-MultiDiscPlaylists {
    <#
    .SYNOPSIS
        Generates .m3u playlists for multi-disc games. Returns count created.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string] $SystemRomDir,
        [Parameter(Mandatory = $true)][scriptblock] $Logger,
        [switch] $DryRun
    )
    if (-not (Test-Path -LiteralPath $SystemRomDir)) { return 0 }
    $discExt = @('.chd','.cue','.iso','.gdi','.cso','.pbp','.ccd')
    $groups = @{}
    Get-ChildItem -LiteralPath $SystemRomDir -File -ErrorAction SilentlyContinue | ForEach-Object {
        if ($discExt -notcontains $_.Extension.ToLower()) { return }
        $stem = [System.IO.Path]::GetFileNameWithoutExtension($_.Name)
        $m = [Regex]::Match($stem, '^(.*?)[\s_]*\(Disc\s*(\d+)\)(.*)$', 'IgnoreCase')
        if (-not $m.Success) { return }
        $base = ($m.Groups[1].Value.Trim() + $m.Groups[3].Value.Trim()).Trim()
        if (-not $groups.ContainsKey($base)) { $groups[$base] = New-Object System.Collections.Generic.List[object] }
        $groups[$base].Add([pscustomobject]@{ Disc=[int]$m.Groups[2].Value; File=$_.Name })
    }
    $created = 0
    foreach ($base in $groups.Keys) {
        $discs = $groups[$base]
        if ($discs.Count -lt 2) { continue }
        $m3u = Join-Path $SystemRomDir ($base + '.m3u')
        if (Test-Path -LiteralPath $m3u) { continue }
        $lines = @($discs | Sort-Object Disc | ForEach-Object { $_.File })
        if ($DryRun) { & $Logger "[DRY-RUN] Would create playlist $base.m3u ($($lines.Count) discs)." 'INFO'; $created++; continue }
        [System.IO.File]::WriteAllLines($m3u, $lines, (New-Object System.Text.UTF8Encoding($false)))
        $created++
    }
    if ($created -gt 0) { & $Logger "Created $created multi-disc .m3u playlist(s) in $(Split-Path $SystemRomDir -Leaf)." 'SUCCESS' }
    return $created
}

function Get-CompressionAdvisory {
    <#
    .SYNOPSIS
        Returns uncompressed disc images that could be CHD-compressed, with the
        approximate space they currently occupy.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][string] $SystemRomDir)
    $candidates = New-Object System.Collections.Generic.List[object]
    $bytes = [int64]0
    if (Test-Path -LiteralPath $SystemRomDir) {
        Get-ChildItem -LiteralPath $SystemRomDir -File -ErrorAction SilentlyContinue | ForEach-Object {
            if ($_.Extension.ToLower() -in @('.iso','.cue','.gdi')) {
                $candidates.Add($_.Name); $bytes += $_.Length
            }
        }
    }
    return @{ Count=$candidates.Count; ApproxBytes=$bytes }
}

Export-ModuleMember -Function Get-RomLibraryStats, New-MultiDiscPlaylists, Get-CompressionAdvisory
