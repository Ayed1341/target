<#
.SYNOPSIS
    Library analytics: statistics, duplicate-ROM detection, ROM extension checks,
    cheat-file inventory, custom-systems suggestions and a portable library manifest.
#>

Set-StrictMode -Version Latest

$script:AnNonRom = @('.txt','.xml','.dat','.jpg','.png','.bin','.m3u','.srm','.state','.cfg','.sav','.cht')

function Get-LibraryStatistics {
    <#
    .SYNOPSIS
        Aggregates genre distribution, release-decade distribution, total games and
        total playtime across all systems' gamelists.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][object[]] $Systems)
    $genres = @{}; $decades = @{}; $totalGames = 0; $totalPlaytime = 0
    foreach ($sys in $Systems) {
        if (-not (Test-Path -LiteralPath $sys.Gamelist)) { continue }
        $g = Read-Gamelist -Path $sys.Gamelist
        if (-not $g.Ok) { continue }
        foreach ($game in @($g.Games)) {
            $totalGames++
            $gn = $game.SelectSingleNode('genre')
            if ($gn -and $gn.InnerText) {
                $key = ($gn.InnerText -split '[,/]')[0].Trim()
                if ($key) { if (-not $genres.ContainsKey($key)) { $genres[$key]=0 }; $genres[$key]++ }
            }
            $rd = $game.SelectSingleNode('releasedate')
            if ($rd -and $rd.InnerText -match '^(\d{4})') {
                $decade = [string]([int]([int]$Matches[1] / 10) * 10) + 's'
                if (-not $decades.ContainsKey($decade)) { $decades[$decade]=0 }; $decades[$decade]++
            }
            $pt = $game.SelectSingleNode('playtime')
            if ($pt) { $v=0; if ([int]::TryParse($pt.InnerText,[ref]$v)) { $totalPlaytime += $v } }
        }
    }
    $topGenres = @($genres.GetEnumerator() | Sort-Object Value -Descending | Select-Object -First 10 | ForEach-Object { @{ Genre=$_.Key; Count=$_.Value } })
    $decadeArr = @($decades.GetEnumerator() | Sort-Object Name | ForEach-Object { @{ Decade=$_.Key; Count=$_.Value } })
    return @{ TotalGames=$totalGames; TotalPlaytimeHours=[math]::Round($totalPlaytime/3600,1); TopGenres=$topGenres; Decades=$decadeArr }
}

function Test-RomExtensions {
    <#
    .SYNOPSIS
        Reports ROM files whose extension is not in the system's allowed list.
    .PARAMETER ExtMap
        Hashtable system-name -> array of allowed extensions (lowercase, with dot).
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][object[]]  $Systems,
        [Parameter(Mandatory = $true)][hashtable] $ExtMap
    )
    $records = New-Object System.Collections.Generic.List[object]
    foreach ($sys in $Systems) {
        if (-not $ExtMap.ContainsKey($sys.Name)) { continue }
        $allowed = @($ExtMap[$sys.Name]) + @('.m3u','.txt')
        if (-not (Test-Path -LiteralPath $sys.RomPath)) { continue }
        $bad = New-Object System.Collections.Generic.List[string]
        Get-ChildItem -LiteralPath $sys.RomPath -File -ErrorAction SilentlyContinue | ForEach-Object {
            $e = $_.Extension.ToLower()
            if ($script:AnNonRom -contains $e) { return }
            if ($allowed -notcontains $e) { $bad.Add($_.Name) }
        }
        if ($bad.Count -gt 0) { $records.Add(@{ System=$sys.Name; Count=$bad.Count }) }
    }
    return $records.ToArray()
}

function Find-DuplicateRoms {
    <#
    .SYNOPSIS
        Finds byte-identical ROMs (same content, different names) within a system,
        hashing only same-size candidates and skipping files above MaxSizeMB.
        Report only - never deletes.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][string] $SystemRomDir, [int] $MaxSizeMB = 512)
    if (-not (Test-Path -LiteralPath $SystemRomDir)) { return @() }
    $limit = $MaxSizeMB * 1MB
    $bySize = @{}
    Get-ChildItem -LiteralPath $SystemRomDir -File -ErrorAction SilentlyContinue | ForEach-Object {
        if ($script:AnNonRom -contains $_.Extension.ToLower()) { return }
        if ($_.Length -gt $limit -or $_.Length -eq 0) { return }
        if (-not $bySize.ContainsKey($_.Length)) { $bySize[$_.Length] = New-Object System.Collections.Generic.List[object] }
        $bySize[$_.Length].Add($_)
    }
    $dups = New-Object System.Collections.Generic.List[object]
    foreach ($sz in $bySize.Keys) {
        $cands = $bySize[$sz]
        if ($cands.Count -lt 2) { continue }
        $byHash = @{}
        foreach ($f in $cands) {
            $h = Get-FileSha256 -Path $f.FullName
            if (-not $h) { continue }
            if (-not $byHash.ContainsKey($h)) { $byHash[$h] = New-Object System.Collections.Generic.List[string] }
            $byHash[$h].Add($f.Name)
        }
        foreach ($h in $byHash.Keys) { if ($byHash[$h].Count -gt 1) { $dups.Add(@{ Files=@($byHash[$h]) }) } }
    }
    return $dups.ToArray()
}

function Get-CheatFiles {
    [CmdletBinding()]
    param([string[]] $Roots = @())
    $count = 0
    foreach ($r in $Roots) {
        if (-not $r -or -not (Test-Path -LiteralPath $r)) { continue }
        $count += @(Get-ChildItem -LiteralPath $r -File -Recurse -Depth 5 -Filter '*.cht' -ErrorAction SilentlyContinue).Count
    }
    return $count
}

function Get-CustomSystemsSuggestion {
    <#
    .SYNOPSIS
        ROM sub-folders that are not declared in custom es_systems.xml - candidates
        for a custom system entry. Returns names.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][System.Collections.Specialized.OrderedDictionary] $Layout,
        [Parameter(Mandatory = $true)][object[]] $Systems
    )
    $known = New-Object System.Collections.Generic.HashSet[string] ([StringComparer]::OrdinalIgnoreCase)
    $ess = Join-Path $Layout.CustomSystems 'es_systems.xml'
    if (Test-Path -LiteralPath $ess) {
        try {
            $doc = New-Object System.Xml.XmlDocument; $doc.Load($ess)
            foreach ($n in $doc.SelectNodes('//system/name')) { [void]$known.Add($n.InnerText) }
        } catch { }
    }
    return @($Systems | Where-Object { $_.HasRoms -and -not $known.Contains($_.Name) } | ForEach-Object { $_.Name })
}

function Export-LibraryManifest {
    <#
    .SYNOPSIS
        Writes a portable JSON manifest of systems, game counts and media counts.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][object[]] $Systems,
        [Parameter(Mandatory = $true)][string]   $OutFile
    )
    $entries = New-Object System.Collections.Generic.List[object]
    foreach ($sys in $Systems) {
        $games = 0
        if (Test-Path -LiteralPath $sys.Gamelist) { $g = Read-Gamelist -Path $sys.Gamelist; if ($g.Ok) { $games = @($g.Games).Count } }
        $mediaCount = 0
        if (Test-Path -LiteralPath $sys.MediaDir) { $mediaCount = @(Get-ChildItem -LiteralPath $sys.MediaDir -File -Recurse -ErrorAction SilentlyContinue).Count }
        $entries.Add(@{ system=$sys.Name; games=$games; mediaFiles=$mediaCount; hasRoms=[bool]$sys.HasRoms })
    }
    $dir = Split-Path $OutFile -Parent
    if ($dir -and -not (Test-Path -LiteralPath $dir)) { New-Item -Path $dir -ItemType Directory -Force | Out-Null }
    @{ generated=(Get-Date -Format o); systems=$entries.ToArray() } | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $OutFile -Encoding UTF8
    return $entries.Count
}

Export-ModuleMember -Function Get-LibraryStatistics, Test-RomExtensions, Find-DuplicateRoms, Get-CheatFiles, Get-CustomSystemsSuggestion, Export-LibraryManifest
