<#
.SYNOPSIS
    Library insights: per-system gamelist stats, abandoned games, save-state
    inventory and gamelist change diff against the most recent backup.
#>

Set-StrictMode -Version Latest

function Get-PerSystemGamelistStats {
    <#
    .SYNOPSIS
        Per-system: game count, average rating, oldest and newest release year.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][object[]] $Systems)
    $out = New-Object System.Collections.Generic.List[object]
    foreach ($sys in $Systems) {
        if (-not (Test-Path -LiteralPath $sys.Gamelist)) { continue }
        $g = Read-Gamelist -Path $sys.Gamelist
        if (-not $g.Ok) { continue }
        $n=0; $ratingSum=0.0; $ratingN=0; $minY=9999; $maxY=0
        foreach ($game in @($g.Games)) {
            $n++
            $r = $game.SelectSingleNode('rating'); if ($r) { $v=0.0; if ([double]::TryParse($r.InnerText,[ref]$v)) { $ratingSum+=$v; $ratingN++ } }
            $rd = $game.SelectSingleNode('releasedate'); if ($rd -and $rd.InnerText -match '^(\d{4})') { $y=[int]$Matches[1]; if ($y -ge 1970 -and $y -le 2100) { if ($y -lt $minY) {$minY=$y}; if ($y -gt $maxY) {$maxY=$y} } }
        }
        if ($n -eq 0) { continue }
        $out.Add(@{ System=$sys.Name; Games=$n; AvgRating=$(if($ratingN){[math]::Round($ratingSum/$ratingN,2)}else{0}); Oldest=$(if($maxY){$minY}else{0}); Newest=$maxY })
    }
    return $out.ToArray()
}

function Get-AbandonedGames {
    <#
    .SYNOPSIS
        Counts games that were started (playcount>0) but barely played
        (playtime < ThresholdMinutes).
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][object[]] $Systems, [int] $ThresholdMinutes = 5)
    $count = 0; $limit = $ThresholdMinutes * 60
    foreach ($sys in $Systems) {
        if (-not (Test-Path -LiteralPath $sys.Gamelist)) { continue }
        $g = Read-Gamelist -Path $sys.Gamelist
        if (-not $g.Ok) { continue }
        foreach ($game in @($g.Games)) {
            $pc = $game.SelectSingleNode('playcount'); $pcv=0; if ($pc) { [void][int]::TryParse($pc.InnerText,[ref]$pcv) }
            $pt = $game.SelectSingleNode('playtime'); $ptv=0; if ($pt) { [void][int]::TryParse($pt.InnerText,[ref]$ptv) }
            if ($pcv -gt 0 -and $ptv -gt 0 -and $ptv -lt $limit) { $count++ }
        }
    }
    return $count
}

function Get-SavestateInventory {
    <#
    .SYNOPSIS
        Counts save-state files under the emulator roots / ROM dir.
    #>
    [CmdletBinding()]
    param([string[]] $Roots = @())
    $exts = @('.state','.ss0','.ss1','.ss2','.sstate','.p2s','.dsv','.bsv')
    $count = 0
    foreach ($r in $Roots) {
        if (-not $r -or -not (Test-Path -LiteralPath $r)) { continue }
        $count += @(Get-ChildItem -LiteralPath $r -File -Recurse -Depth 5 -ErrorAction SilentlyContinue | Where-Object { $exts -contains $_.Extension.ToLower() -or $_.Name -match '\.state\d*$' }).Count
    }
    return $count
}

function Get-GamelistDiff {
    <#
    .SYNOPSIS
        Compares each system's current gamelist game-count against the most recent
        snapshot backup and returns the net change (added minus removed).
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][object[]] $Systems,
        [Parameter(Mandatory = $true)][string]   $BackupRoot
    )
    $snap = Get-ChildItem -LiteralPath $BackupRoot -Directory -Filter 'snapshot_gamelists_*' -ErrorAction SilentlyContinue |
            Sort-Object Name -Descending | Select-Object -First 1
    if (-not $snap) { return @() }
    $out = New-Object System.Collections.Generic.List[object]
    foreach ($sys in $Systems) {
        if (-not (Test-Path -LiteralPath $sys.Gamelist)) { continue }
        $now = Read-Gamelist -Path $sys.Gamelist
        $nowN = if ($now.Ok) { @($now.Games).Count } else { 0 }
        $oldPath = Join-Path $snap.FullName (Join-Path $sys.Name 'gamelist.xml')
        $oldN = 0
        if (Test-Path -LiteralPath $oldPath) { $old = Read-Gamelist -Path $oldPath; if ($old.Ok) { $oldN = @($old.Games).Count } }
        if ($nowN -ne $oldN) { $out.Add(@{ System=$sys.Name; Was=$oldN; Now=$nowN; Delta=($nowN-$oldN) }) }
    }
    return $out.ToArray()
}

Export-ModuleMember -Function Get-PerSystemGamelistStats, Get-AbandonedGames, Get-SavestateInventory, Get-GamelistDiff
