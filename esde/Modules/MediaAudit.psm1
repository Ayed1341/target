<#
.SYNOPSIS
    Media audit engine - deep analysis and safe fixes for the ES-DE media library.
.DESCRIPTION
    Adds: media coverage %, per-system/per-type disk usage, image format/extension
    mismatch detection + safe fix, oversized-media detection, video container audit,
    optional ffmpeg frame extraction for games missing a screenshot, ROM<->gamelist
    consistency (orphan entries / unlisted ROMs), play statistics, and a 1G1R
    region-duplicate advisory.
#>

Set-StrictMode -Version Latest

$script:CoverageTypes = @('covers','screenshots','videos','marquees','fanart','titlescreens','manuals','3dboxes')

function Get-MediaCoverage {
    <#
    .SYNOPSIS
        Returns per-system media coverage: for each media type, how many of the
        system's games have that media (count + percentage).
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string] $SystemName,
        [System.Collections.Generic.HashSet[string]] $RomStems,
        [Parameter(Mandatory = $true)][string] $SystemMediaDir
    )
    if ($null -eq $RomStems) { $RomStems = New-Object System.Collections.Generic.HashSet[string] }
    $total = $RomStems.Count
    $cov = [ordered]@{}
    foreach ($t in $script:CoverageTypes) {
        $have = 0
        $dir = Join-Path $SystemMediaDir $t
        if ($total -gt 0 -and (Test-Path -LiteralPath $dir)) {
            $present = New-Object System.Collections.Generic.HashSet[string] ([StringComparer]::OrdinalIgnoreCase)
            Get-ChildItem -LiteralPath $dir -File -ErrorAction SilentlyContinue | ForEach-Object {
                [void]$present.Add([System.IO.Path]::GetFileNameWithoutExtension($_.Name))
            }
            foreach ($s in $RomStems) { if ($present.Contains($s)) { $have++ } }
        }
        $pct = if ($total -gt 0) { [math]::Round(($have * 100.0) / $total, 1) } else { 0 }
        $cov[$t] = @{ Have = $have; Total = $total; Percent = $pct }
    }
    return @{ System = $SystemName; Coverage = $cov }
}

function Get-MediaDiskUsage {
    <#
    .SYNOPSIS
        Returns total bytes and per-type bytes for a system's media folder.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][string] $SystemName, [Parameter(Mandatory = $true)][string] $SystemMediaDir)
    $perType = [ordered]@{}; $total = [int64]0
    if (Test-Path -LiteralPath $SystemMediaDir) {
        foreach ($sub in (Get-ChildItem -LiteralPath $SystemMediaDir -Directory -ErrorAction SilentlyContinue)) {
            $files = @(Get-ChildItem -LiteralPath $sub.FullName -File -Recurse -ErrorAction SilentlyContinue)
            $sum = 0
            if ($files.Count -gt 0) { $sum = ($files | Measure-Object -Property Length -Sum).Sum }
            if (-not $sum) { $sum = 0 }
            $perType[$sub.Name] = [int64]$sum; $total += [int64]$sum
        }
    }
    return @{ System = $SystemName; TotalBytes = $total; PerType = $perType }
}

function Get-ImageMagicType {
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][string] $Path)
    try {
        $fs = [System.IO.File]::OpenRead($Path)
        try {
            $b = New-Object byte[] 12
            $n = $fs.Read($b, 0, 12)
            if ($n -ge 8 -and $b[0] -eq 0x89 -and $b[1] -eq 0x50 -and $b[2] -eq 0x4E -and $b[3] -eq 0x47) { return 'png' }
            if ($n -ge 3 -and $b[0] -eq 0xFF -and $b[1] -eq 0xD8 -and $b[2] -eq 0xFF) { return 'jpg' }
            if ($n -ge 3 -and $b[0] -eq 0x47 -and $b[1] -eq 0x49 -and $b[2] -eq 0x46) { return 'gif' }
            if ($n -ge 2 -and $b[0] -eq 0x42 -and $b[1] -eq 0x4D) { return 'bmp' }
            if ($n -ge 12 -and $b[0] -eq 0x52 -and $b[1] -eq 0x49 -and $b[8] -eq 0x57 -and $b[9] -eq 0x45) { return 'webp' }
        } finally { $fs.Dispose() }
    } catch { }
    return $null
}

function Repair-MediaExtensions {
    <#
    .SYNOPSIS
        Detects image files whose extension does not match their real format and
        renames them to the correct extension (after backup). Returns count fixed.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string] $SystemMediaDir,
        [Parameter(Mandatory = $true)][string] $BackupRoot,
        [Parameter(Mandatory = $true)][scriptblock] $Logger,
        [switch] $DryRun
    )
    $fixed = 0
    if (-not (Test-Path -LiteralPath $SystemMediaDir)) { return 0 }
    $imgExt = @('.png','.jpg','.jpeg','.gif','.bmp','.webp')
    Get-ChildItem -LiteralPath $SystemMediaDir -File -Recurse -ErrorAction SilentlyContinue | Where-Object { $imgExt -contains $_.Extension.ToLower() } | ForEach-Object {
        $real = Get-ImageMagicType -Path $_.FullName
        if (-not $real) { return }
        $cur = $_.Extension.TrimStart('.').ToLower()
        if ($cur -eq 'jpeg') { $cur = 'jpg' }
        if ($real -ne $cur) {
            $target = [System.IO.Path]::ChangeExtension($_.FullName, $real)
            if (Test-Path -LiteralPath $target) { return }
            if ($DryRun) { & $Logger "[DRY-RUN] Would fix extension: $($_.Name) is actually $real" 'INFO'; $fixed++; return }
            Backup-File -Path $_.FullName -BackupRoot $BackupRoot | Out-Null
            Rename-Item -LiteralPath $_.FullName -NewName (Split-Path $target -Leaf) -Force
            $fixed++
        }
    }
    if ($fixed -gt 0) { & $Logger "Fixed $fixed mislabeled image extension(s) in $(Split-Path $SystemMediaDir -Leaf)." 'SUCCESS' }
    return $fixed
}

function Get-OversizedMedia {
    <#
    .SYNOPSIS
        Returns media files larger than a threshold (MB) that may slow ES-DE.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][string] $SystemMediaDir, [int] $ThresholdMB = 8)
    $hits = New-Object System.Collections.Generic.List[object]
    if (Test-Path -LiteralPath $SystemMediaDir) {
        $limit = $ThresholdMB * 1MB
        Get-ChildItem -LiteralPath $SystemMediaDir -File -Recurse -ErrorAction SilentlyContinue | Where-Object { $_.Length -gt $limit -and $_.Extension -notin @('.mp4','.webm','.mkv','.avi') } | ForEach-Object {
            $hits.Add(@{ File = $_.FullName; SizeMB = [math]::Round($_.Length/1MB,1) })
        }
    }
    return $hits.ToArray()
}

function Get-VideoAudit {
    <#
    .SYNOPSIS
        Reports videos whose container is not the ES-DE-friendly mp4/webm, and
        whether ffmpeg is available to convert/extract.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][string] $SystemMediaDir)
    $vids = Join-Path $SystemMediaDir 'videos'
    $nonFriendly = New-Object System.Collections.Generic.List[string]
    $count = 0
    if (Test-Path -LiteralPath $vids) {
        Get-ChildItem -LiteralPath $vids -File -ErrorAction SilentlyContinue | ForEach-Object {
            $count++
            if ($_.Extension.ToLower() -notin @('.mp4','.webm')) { $nonFriendly.Add($_.FullName) }
        }
    }
    return @{ Total = $count; NonFriendly = $nonFriendly.ToArray() }
}

function Test-FfmpegAvailable {
    [CmdletBinding()] param()
    $cmd = Get-Command ffmpeg -ErrorAction SilentlyContinue
    return [bool]$cmd
}

function Invoke-VideoFrameForMissingScreens {
    <#
    .SYNOPSIS
        For games that have a video but no screenshot, extracts a representative
        frame with ffmpeg to create the missing screenshot. Requires ffmpeg.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string] $SystemMediaDir,
        [Parameter(Mandatory = $true)][scriptblock] $Logger,
        [switch] $DryRun
    )
    if (-not (Test-FfmpegAvailable)) { return 0 }
    $vids = Join-Path $SystemMediaDir 'videos'
    $shots = Join-Path $SystemMediaDir 'screenshots'
    if (-not (Test-Path -LiteralPath $vids)) { return 0 }
    if (-not (Test-Path -LiteralPath $shots) -and -not $DryRun) { New-Item -Path $shots -ItemType Directory -Force | Out-Null }
    $made = 0
    Get-ChildItem -LiteralPath $vids -File -ErrorAction SilentlyContinue | ForEach-Object {
        $stem = [System.IO.Path]::GetFileNameWithoutExtension($_.Name)
        $out = Join-Path $shots ($stem + '.png')
        if (Test-Path -LiteralPath $out) { return }
        if ($DryRun) { & $Logger "[DRY-RUN] Would extract screenshot for $stem" 'INFO'; $made++; return }
        try {
            $p = Start-Process -FilePath 'ffmpeg' -ArgumentList @('-y','-ss','3','-i',$_.FullName,'-frames:v','1','-q:v','3',$out) -NoNewWindow -Wait -PassThru -RedirectStandardError ([System.IO.Path]::GetTempFileName())
            if ($p.ExitCode -eq 0 -and (Test-Path -LiteralPath $out)) { $made++ }
        } catch { }
    }
    if ($made -gt 0) { & $Logger "Generated $made screenshot(s) from video via ffmpeg." 'SUCCESS' }
    return $made
}

function Get-RomGamelistConsistency {
    <#
    .SYNOPSIS
        Returns gamelist entries whose ROM file is missing (orphan entries) and
        ROM files not present in the gamelist (unlisted).
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string] $SystemRomDir,
        [string] $GamelistPath
    )
    $orphanEntries = New-Object System.Collections.Generic.List[string]
    $listed = New-Object System.Collections.Generic.HashSet[string] ([StringComparer]::OrdinalIgnoreCase)
    if ($GamelistPath -and (Test-Path -LiteralPath $GamelistPath)) {
        $g = Read-Gamelist -Path $GamelistPath
        if ($g.Ok) {
            foreach ($game in @($g.Games)) {
                $pn = $game.SelectSingleNode('path')
                if (-not $pn -or -not $pn.InnerText) { continue }
                $rel = ($pn.InnerText -replace '/', '\') -replace '^\.\\',''
                [void]$listed.Add([System.IO.Path]::GetFileName($rel))
                $abs = Join-Path $SystemRomDir $rel
                if (-not (Test-Path -LiteralPath $abs)) { $orphanEntries.Add($pn.InnerText) }
            }
        }
    }
    $unlisted = New-Object System.Collections.Generic.List[string]
    if (Test-Path -LiteralPath $SystemRomDir) {
        Get-ChildItem -LiteralPath $SystemRomDir -File -ErrorAction SilentlyContinue | ForEach-Object {
            if ($_.Extension.ToLower() -in @('.txt','.xml','.dat','.jpg','.png')) { return }
            if (-not $listed.Contains($_.Name)) { $unlisted.Add($_.Name) }
        }
    }
    return @{ OrphanEntries = $orphanEntries.ToArray(); Unlisted = $unlisted.ToArray() }
}

function Get-PlayStats {
    <#
    .SYNOPSIS
        Aggregates favorites / playcount / total playtime / most-played title from
        a system's gamelist.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][string] $SystemName, [string] $GamelistPath)
    $fav = 0; $played = 0; $totalTime = 0; $top = ''; $topTime = -1
    if ($GamelistPath -and (Test-Path -LiteralPath $GamelistPath)) {
        $g = Read-Gamelist -Path $GamelistPath
        if ($g.Ok) {
            foreach ($game in @($g.Games)) {
                $f = $game.SelectSingleNode('favorite'); if ($f -and $f.InnerText -eq 'true') { $fav++ }
                $pc = $game.SelectSingleNode('playcount')
                if ($pc -and [int]::TryParse($pc.InnerText, [ref]([int]$null))) { if ([int]$pc.InnerText -gt 0) { $played++ } }
                $pt = $game.SelectSingleNode('playtime')
                if ($pt) { $v = 0; if ([int]::TryParse($pt.InnerText, [ref]$v)) { $totalTime += $v; if ($v -gt $topTime) { $topTime = $v; $n = $game.SelectSingleNode('name'); $top = if ($n) { $n.InnerText } else { '' } } } }
            }
        }
    }
    return @{ System = $SystemName; Favorites = $fav; Played = $played; TotalPlaytimeMin = [math]::Round($totalTime/60); MostPlayed = $top }
}

function Get-RegionDuplicates {
    <#
    .SYNOPSIS
        1G1R advisory: groups ROMs by region-insensitive base name and reports
        groups with more than one regional variant.
    #>
    [CmdletBinding()]
    param([System.Collections.Generic.HashSet[string]] $RomStems)
    if ($null -eq $RomStems -or $RomStems.Count -eq 0) { return @() }
    $byBase = @{}
    foreach ($s in $RomStems) {
        $base = [Regex]::Replace($s, '\s*[\(\[].*$', '').Trim().ToLower()
        if (-not $base) { continue }
        if (-not $byBase.ContainsKey($base)) { $byBase[$base] = New-Object System.Collections.Generic.List[string] }
        $byBase[$base].Add($s)
    }
    $groups = New-Object System.Collections.Generic.List[object]
    foreach ($k in $byBase.Keys) { if ($byBase[$k].Count -gt 1) { $groups.Add(@{ Base = $k; Variants = @($byBase[$k]) }) } }
    return $groups.ToArray()
}

Export-ModuleMember -Function Get-MediaCoverage, Get-MediaDiskUsage, Get-ImageMagicType, Repair-MediaExtensions, `
    Get-OversizedMedia, Get-VideoAudit, Test-FfmpegAvailable, Invoke-VideoFrameForMissingScreens, `
    Get-RomGamelistConsistency, Get-PlayStats, Get-RegionDuplicates
