<#
.SYNOPSIS
    ES-DE custom collections generation and 1G1R region hiding.
.DESCRIPTION
    * New-EsdeCollections - builds custom collection files ES-DE reads from the
      collections folder: Favorites (from <favorite>) and Played (from <playcount>).
    * Invoke-RegionHide - for region-duplicate ROM sets, keeps the preferred-region
      copy visible and marks the others <hidden> in the gamelist (reversible via the
      backup/restore system; never deletes ROMs).
#>

Set-StrictMode -Version Latest

function New-EsdeCollections {
    <#
    .SYNOPSIS
        Writes custom-Favorites.cfg and custom-Played.cfg into the collections dir,
        using full ROM paths (the format ES-DE custom collections accept).
        Returns @{ Favorites; Played }.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][object[]] $Systems,
        [Parameter(Mandatory = $true)][string]   $CollectionsDir,
        [Parameter(Mandatory = $true)][scriptblock] $Logger,
        [switch] $DryRun
    )
    $fav = New-Object System.Collections.Generic.List[string]
    $played = New-Object System.Collections.Generic.List[string]
    foreach ($sys in $Systems) {
        if (-not (Test-Path -LiteralPath $sys.Gamelist)) { continue }
        $g = Read-Gamelist -Path $sys.Gamelist
        if (-not $g.Ok) { continue }
        foreach ($game in @($g.Games)) {
            $pn = $game.SelectSingleNode('path'); if (-not $pn -or -not $pn.InnerText) { continue }
            $rel = ($pn.InnerText -replace '/','\') -replace '^\.\\',''
            $full = Join-Path $sys.RomPath $rel
            $f = $game.SelectSingleNode('favorite')
            if ($f -and $f.InnerText -eq 'true') { $fav.Add($full) }
            $pc = $game.SelectSingleNode('playcount')
            if ($pc) { $v = 0; if ([int]::TryParse($pc.InnerText, [ref]$v) -and $v -gt 0) { $played.Add($full) } }
        }
    }
    if (-not $DryRun) {
        if (-not (Test-Path -LiteralPath $CollectionsDir)) { New-Item -Path $CollectionsDir -ItemType Directory -Force | Out-Null }
        if ($fav.Count -gt 0)    { [System.IO.File]::WriteAllLines((Join-Path $CollectionsDir 'custom-Favorites.cfg'), $fav.ToArray(), (New-Object System.Text.UTF8Encoding($false))) }
        if ($played.Count -gt 0) { [System.IO.File]::WriteAllLines((Join-Path $CollectionsDir 'custom-Played.cfg'), $played.ToArray(), (New-Object System.Text.UTF8Encoding($false))) }
    }
    & $Logger "Collections: $($fav.Count) favorite(s), $($played.Count) played title(s)." 'INFO'
    return @{ Favorites = $fav.Count; Played = $played.Count }
}

function Invoke-RegionHide {
    <#
    .SYNOPSIS
        For each region-duplicate group in a system, keeps the preferred-region copy
        and marks the rest <hidden>. Returns count hidden.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string] $GamelistPath,
        [string[]] $PreferredRegions = @('USA','World','Europe','Japan'),
        [Parameter(Mandatory = $true)][string] $BackupRoot,
        [Parameter(Mandatory = $true)][scriptblock] $Logger,
        [switch] $DryRun
    )
    $hidden = 0
    if (-not (Test-Path -LiteralPath $GamelistPath)) { return 0 }
    $g = Read-Gamelist -Path $GamelistPath
    if (-not $g.Ok) { return 0 }
    $xml = $g.Xml

    # Group games by region-insensitive base name.
    $groups = @{}
    foreach ($game in @($xml.gameList.SelectNodes('game'))) {
        $nm = $game.SelectSingleNode('name'); $pn = $game.SelectSingleNode('path')
        $label = if ($nm -and $nm.InnerText) { $nm.InnerText } elseif ($pn -and $pn.InnerText) { [System.IO.Path]::GetFileNameWithoutExtension($pn.InnerText) } else { $null }
        if (-not $label) { continue }
        $base = ([Regex]::Replace($label, '\s*[\(\[].*$', '')).Trim().ToLower()
        if (-not $base) { continue }
        if (-not $groups.ContainsKey($base)) { $groups[$base] = New-Object System.Collections.Generic.List[object] }
        $groups[$base].Add([pscustomobject]@{ Node=$game; Label=$label })
    }

    function RegionRank([string]$label, [string[]]$prefs) {
        for ($i=0; $i -lt $prefs.Count; $i++) { if ($label -match ('(?i)\(' + [Regex]::Escape($prefs[$i])) ) { return $i } }
        return 999
    }

    $changed = $false
    foreach ($base in $groups.Keys) {
        $items = $groups[$base]
        if ($items.Count -lt 2) { continue }
        $ranked = $items | Sort-Object @{ Expression = { RegionRank $_.Label $PreferredRegions } }
        $keep = $ranked[0]
        foreach ($it in $ranked) {
            if ($it -eq $keep) { continue }
            $h = $it.Node.SelectSingleNode('hidden')
            if (-not $h) { $h = $xml.CreateElement('hidden'); [void]$it.Node.AppendChild($h) }
            if ($h.InnerText -ne 'true') { if (-not $DryRun) { $h.InnerText = 'true' }; $hidden++; $changed = $true }
        }
    }

    if ($changed -and -not $DryRun) {
        Backup-File -Path $GamelistPath -BackupRoot $BackupRoot | Out-Null
        Save-Gamelist -Xml $xml -Prefix $g.Prefix -Path $GamelistPath
        & $Logger "1G1R: hid $hidden non-preferred-region duplicate(s) in $(Split-Path (Split-Path $GamelistPath -Parent) -Leaf)." 'SUCCESS'
    }
    return $hidden
}

Export-ModuleMember -Function New-EsdeCollections, Invoke-RegionHide
