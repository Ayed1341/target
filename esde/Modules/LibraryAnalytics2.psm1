<#
.SYNOPSIS
    Extended library analytics: cross-system duplicates, region distribution,
    completion stats, archive integrity, a health score, playtime leaderboard and
    newest additions.
#>

Set-StrictMode -Version Latest

$script:A2NonRom = @('.txt','.xml','.dat','.jpg','.png','.bin','.m3u','.srm','.state','.cfg','.sav','.cht')

function Find-CrossSystemDuplicates {
    <#
    .SYNOPSIS
        Returns ROM filenames that appear under more than one system's ROM folder.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][object[]] $Systems)
    $seen = @{}
    foreach ($sys in $Systems) {
        if (-not (Test-Path -LiteralPath $sys.RomPath)) { continue }
        Get-ChildItem -LiteralPath $sys.RomPath -File -ErrorAction SilentlyContinue | ForEach-Object {
            if ($script:A2NonRom -contains $_.Extension.ToLower()) { return }
            $k = $_.Name.ToLower()
            if (-not $seen.ContainsKey($k)) { $seen[$k] = New-Object System.Collections.Generic.List[string] }
            $seen[$k].Add($sys.Name)
        }
    }
    $dups = New-Object System.Collections.Generic.List[object]
    foreach ($k in $seen.Keys) { if ($seen[$k].Count -gt 1) { $dups.Add(@{ File=$k; Systems=@($seen[$k]) }) } }
    return $dups.ToArray()
}

function Get-RegionDistribution {
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][object[]] $Systems)
    $r = [ordered]@{ USA=0; Europe=0; Japan=0; World=0; Other=0 }
    foreach ($sys in $Systems) {
        if (-not (Test-Path -LiteralPath $sys.RomPath)) { continue }
        Get-ChildItem -LiteralPath $sys.RomPath -File -ErrorAction SilentlyContinue | ForEach-Object {
            if ($script:A2NonRom -contains $_.Extension.ToLower()) { return }
            $n = $_.Name
            if     ($n -match '(?i)\(USA') { $r.USA++ }
            elseif ($n -match '(?i)\(Europe|\(EUR') { $r.Europe++ }
            elseif ($n -match '(?i)\(Japan|\(JPN|\(JP\)') { $r.Japan++ }
            elseif ($n -match '(?i)\(World') { $r.World++ }
            else { $r.Other++ }
        }
    }
    return $r
}

function Get-CompletionStats {
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][object[]] $Systems)
    $total=0; $played=0; $fav=0
    foreach ($sys in $Systems) {
        if (-not (Test-Path -LiteralPath $sys.Gamelist)) { continue }
        $g = Read-Gamelist -Path $sys.Gamelist
        if (-not $g.Ok) { continue }
        foreach ($game in @($g.Games)) {
            $total++
            $f = $game.SelectSingleNode('favorite'); if ($f -and $f.InnerText -eq 'true') { $fav++ }
            $pc = $game.SelectSingleNode('playcount'); if ($pc) { $v=0; if ([int]::TryParse($pc.InnerText,[ref]$v) -and $v -gt 0) { $played++ } }
        }
    }
    $pct = if ($total -gt 0) { [math]::Round(($played*100.0)/$total,1) } else { 0 }
    return @{ Total=$total; Played=$played; Favorites=$fav; PlayedPercent=$pct }
}

function Test-RomArchives {
    <#
    .SYNOPSIS
        Tests .zip ROM archives for corruption (via .NET ZipArchive). Returns count
        of bad archives.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][object[]] $Systems)
    Add-Type -AssemblyName System.IO.Compression.FileSystem -ErrorAction SilentlyContinue
    $bad = 0
    foreach ($sys in $Systems) {
        if (-not (Test-Path -LiteralPath $sys.RomPath)) { continue }
        Get-ChildItem -LiteralPath $sys.RomPath -File -Filter '*.zip' -ErrorAction SilentlyContinue | ForEach-Object {
            try {
                $z = [System.IO.Compression.ZipFile]::OpenRead($_.FullName)
                try { $null = $z.Entries.Count } finally { $z.Dispose() }
            } catch { $bad++ }
        }
    }
    return $bad
}

function Get-LibraryHealthScore {
    <#
    .SYNOPSIS
        Computes a 0-100 library health score from media coverage, scrape ratio,
        BIOS completeness and emulator gaps.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][hashtable] $Report)
    $score = 100.0
    # Media coverage (average covers %).
    $cov = @($Report.Audit.MediaCoverage)
    if ($cov.Count -gt 0) {
        $avg = 0.0; foreach ($c in $cov) { $avg += [double]$c.Covers }
        $avg = $avg / $cov.Count
        $score -= ((100 - $avg) * 0.25)
    }
    # Missing BIOS penalty.
    $missingBios = @($Report.Bios).Count
    $score -= [math]::Min(20, $missingBios * 1.5)
    # Emulator gaps penalty.
    $gaps = @($Report.EmulatorGaps | Where-Object { $_.Missing }).Count
    $score -= [math]::Min(20, $gaps * 5)
    # Health errors/warnings.
    $score -= [math]::Min(15, $Report.Errors * 5)
    $score -= [math]::Min(10, $Report.Warnings * 1)
    if ($score -lt 0) { $score = 0 }
    return [math]::Round($score)
}

function Get-PlaytimeLeaderboard {
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][object[]] $Systems, [int] $Top = 10)
    $games = New-Object System.Collections.Generic.List[object]
    foreach ($sys in $Systems) {
        if (-not (Test-Path -LiteralPath $sys.Gamelist)) { continue }
        $g = Read-Gamelist -Path $sys.Gamelist
        if (-not $g.Ok) { continue }
        foreach ($game in @($g.Games)) {
            $pt = $game.SelectSingleNode('playtime'); if (-not $pt) { continue }
            $v = 0; if (-not [int]::TryParse($pt.InnerText,[ref]$v) -or $v -le 0) { continue }
            $nm = $game.SelectSingleNode('name')
            $games.Add(@{ Name=$(if($nm){$nm.InnerText}else{''}); System=$sys.Name; Minutes=[math]::Round($v/60) })
        }
    }
    return @($games | Sort-Object { $_.Minutes } -Descending | Select-Object -First $Top)
}

function Get-NewestAdditions {
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][object[]] $Systems, [int] $Top = 15)
    $files = New-Object System.Collections.Generic.List[object]
    foreach ($sys in $Systems) {
        if (-not (Test-Path -LiteralPath $sys.RomPath)) { continue }
        Get-ChildItem -LiteralPath $sys.RomPath -File -ErrorAction SilentlyContinue | ForEach-Object {
            if ($script:A2NonRom -contains $_.Extension.ToLower()) { return }
            $files.Add(@{ Name=$_.Name; System=$sys.Name; Added=$_.CreationTime.ToString('yyyy-MM-dd') ; Ticks=$_.CreationTime.Ticks })
        }
    }
    return @($files | Sort-Object { $_.Ticks } -Descending | Select-Object -First $Top | ForEach-Object { @{ Name=$_.Name; System=$_.System; Added=$_.Added } })
}

Export-ModuleMember -Function Find-CrossSystemDuplicates, Get-RegionDistribution, Get-CompletionStats, Test-RomArchives, Get-LibraryHealthScore, Get-PlaytimeLeaderboard, Get-NewestAdditions
