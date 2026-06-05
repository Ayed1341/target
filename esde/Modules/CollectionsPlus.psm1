<#
.SYNOPSIS
    Additional ES-DE custom collections and auto-favorites.
.DESCRIPTION
    Builds genre, decade, never-played and kid-game custom collections from the
    gamelists, and (opt-in) marks the most-played titles as favorites. Reads every
    gamelist once via Get-AllGameRecords for efficiency.
#>

Set-StrictMode -Version Latest

function Get-AllGameRecords {
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][object[]] $Systems)
    $recs = New-Object System.Collections.Generic.List[object]
    foreach ($sys in $Systems) {
        if (-not (Test-Path -LiteralPath $sys.Gamelist)) { continue }
        $g = Read-Gamelist -Path $sys.Gamelist
        if (-not $g.Ok) { continue }
        foreach ($game in @($g.Games)) {
            $pn = $game.SelectSingleNode('path'); if (-not $pn -or -not $pn.InnerText) { continue }
            $rel = ($pn.InnerText -replace '/','\') -replace '^\.\\',''
            $full = Join-Path $sys.RomPath $rel
            $nm = $game.SelectSingleNode('name')
            $gn = $game.SelectSingleNode('genre')
            $rd = $game.SelectSingleNode('releasedate')
            $pc = $game.SelectSingleNode('playcount'); $pcv = 0; if ($pc) { [void][int]::TryParse($pc.InnerText,[ref]$pcv) }
            $pt = $game.SelectSingleNode('playtime');  $ptv = 0; if ($pt) { [void][int]::TryParse($pt.InnerText,[ref]$ptv) }
            $fv = $game.SelectSingleNode('favorite')
            $kg = $game.SelectSingleNode('kidgame')
            $year = $null
            if ($rd -and $rd.InnerText -match '^(\d{4})') { $year = [int]$Matches[1] }
            $recs.Add([pscustomobject]@{
                FullPath=$full; Name=$(if($nm){$nm.InnerText}else{[System.IO.Path]::GetFileNameWithoutExtension($rel)})
                System=$sys.Name; Genre=$(if($gn){($gn.InnerText -split '[,/]')[0].Trim()}else{''})
                Year=$year; PlayCount=$pcv; PlayTime=$ptv
                Favorite=($fv -and $fv.InnerText -eq 'true'); KidGame=($kg -and $kg.InnerText -eq 'true')
            })
        }
    }
    return $recs.ToArray()
}

function Write-CollectionFile {
    param([string]$Dir, [string]$Name, [string[]]$Paths, [switch]$DryRun)
    if (@($Paths).Count -eq 0) { return 0 }
    if ($DryRun) { return @($Paths).Count }
    if (-not (Test-Path -LiteralPath $Dir)) { New-Item -Path $Dir -ItemType Directory -Force | Out-Null }
    $safe = ($Name -replace '[\\/:*?"<>|]', '_').Trim()
    [System.IO.File]::WriteAllLines((Join-Path $Dir ("custom-$safe.cfg")), @($Paths), (New-Object System.Text.UTF8Encoding($false)))
    return @($Paths).Count
}

function New-AutoCollections {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][object[]] $Records,
        [Parameter(Mandatory = $true)][string]   $CollectionsDir,
        [Parameter(Mandatory = $true)][scriptblock] $Logger,
        [switch] $DryRun
    )
    $byGenre = @{}
    foreach ($r in $Records) { if ($r.Genre) { if (-not $byGenre.ContainsKey($r.Genre)) { $byGenre[$r.Genre]=New-Object System.Collections.Generic.List[string] }; $byGenre[$r.Genre].Add($r.FullPath) } }
    $genreCount = 0
    foreach ($k in ($byGenre.Keys | Sort-Object { $byGenre[$_].Count } -Descending | Select-Object -First 15)) {
        if ($byGenre[$k].Count -lt 5) { continue }
        if ((Write-CollectionFile -Dir $CollectionsDir -Name $k -Paths $byGenre[$k] -DryRun:$DryRun) -gt 0) { $genreCount++ }
    }
    $byDecade = @{}
    foreach ($r in $Records) { if ($r.Year) { $d = [string]([int]($r.Year/10)*10) + 's'; if (-not $byDecade.ContainsKey($d)) { $byDecade[$d]=New-Object System.Collections.Generic.List[string] }; $byDecade[$d].Add($r.FullPath) } }
    $decadeCount = 0
    foreach ($k in $byDecade.Keys) { if ((Write-CollectionFile -Dir $CollectionsDir -Name $k -Paths $byDecade[$k] -DryRun:$DryRun) -gt 0) { $decadeCount++ } }
    $never = @($Records | Where-Object { $_.PlayCount -eq 0 } | ForEach-Object { $_.FullPath })
    $kids  = @($Records | Where-Object { $_.KidGame } | ForEach-Object { $_.FullPath })
    $neverN = Write-CollectionFile -Dir $CollectionsDir -Name 'Never Played' -Paths $never -DryRun:$DryRun
    $kidsN  = Write-CollectionFile -Dir $CollectionsDir -Name 'Kids' -Paths $kids -DryRun:$DryRun
    & $Logger "Collections: $genreCount genre, $decadeCount decade, never-played ($neverN), kids ($kidsN)." 'INFO'
    return @{ Genres=$genreCount; Decades=$decadeCount; NeverPlayed=$neverN; KidGames=$kidsN }
}

function Set-AutoFavorites {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][object[]] $Systems,
        [int] $TopPerSystem = 5,
        [Parameter(Mandatory = $true)][string] $BackupRoot,
        [Parameter(Mandatory = $true)][scriptblock] $Logger,
        [switch] $DryRun
    )
    $favorited = 0
    foreach ($sys in $Systems) {
        if (-not (Test-Path -LiteralPath $sys.Gamelist)) { continue }
        $g = Read-Gamelist -Path $sys.Gamelist
        if (-not $g.Ok) { continue }
        $games = @($g.Games | ForEach-Object {
            $pt = $_.SelectSingleNode('playtime'); $v=0; if ($pt) { [void][int]::TryParse($pt.InnerText,[ref]$v) }
            [pscustomobject]@{ Node=$_; Play=$v }
        } | Where-Object { $_.Play -gt 0 } | Sort-Object Play -Descending | Select-Object -First $TopPerSystem)
        if ($games.Count -eq 0) { continue }
        $changed = $false
        foreach ($g2 in $games) {
            $fv = $g2.Node.SelectSingleNode('favorite')
            if (-not $fv) { $fv = $g.Xml.CreateElement('favorite'); [void]$g2.Node.AppendChild($fv) }
            if ($fv.InnerText -ne 'true') { if (-not $DryRun) { $fv.InnerText = 'true' }; $favorited++; $changed = $true }
        }
        if ($changed -and -not $DryRun) {
            Backup-File -Path $sys.Gamelist -BackupRoot $BackupRoot | Out-Null
            Save-Gamelist -Xml $g.Xml -Prefix $g.Prefix -Path $sys.Gamelist
        }
    }
    if ($favorited -gt 0) { & $Logger "Auto-favorited $favorited most-played title(s)." 'SUCCESS' }
    return $favorited
}

Export-ModuleMember -Function Get-AllGameRecords, New-AutoCollections, Set-AutoFavorites, Write-CollectionFile
