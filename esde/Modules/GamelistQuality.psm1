<#
.SYNOPSIS
    Gamelist quality engine: m3u validation, metadata sanity repair, players-field
    normalization, region metadata, and adding unlisted ROMs to the gamelist.
    All write operations back up first and are dual-root safe.
#>

Set-StrictMode -Version Latest

function Test-M3uPlaylists {
    <#
    .SYNOPSIS
        Validates that .m3u entries reference existing files. Returns count of
        playlists with at least one broken reference.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][string] $SystemRomDir)
    $broken = 0
    if (-not (Test-Path -LiteralPath $SystemRomDir)) { return 0 }
    Get-ChildItem -LiteralPath $SystemRomDir -File -Filter '*.m3u' -Recurse -Depth 2 -ErrorAction SilentlyContinue | ForEach-Object {
        $dir = Split-Path $_.FullName -Parent
        $bad = $false
        foreach ($line in (Get-Content -LiteralPath $_.FullName -Encoding UTF8 -ErrorAction SilentlyContinue)) {
            $p = $line.Trim(); if (-not $p -or $p.StartsWith('#')) { continue }
            $target = if ([System.IO.Path]::IsPathRooted($p)) { $p } else { Join-Path $dir $p }
            if (-not (Test-Path -LiteralPath $target)) { $bad = $true }
        }
        if ($bad) { $broken++ }
    }
    return $broken
}

function Repair-MetadataSanity {
    <#
    .SYNOPSIS
        Fixes obviously-invalid metadata: ratings outside 0..1, future release dates,
        negative playtime/playcount. Returns count of fields corrected.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string] $GamelistPath,
        [Parameter(Mandatory = $true)][string] $BackupRoot,
        [Parameter(Mandatory = $true)][scriptblock] $Logger,
        [switch] $DryRun
    )
    if (-not (Test-Path -LiteralPath $GamelistPath)) { return 0 }
    $g = Read-Gamelist -Path $GamelistPath
    if (-not $g.Ok) { return 0 }
    $fixed = 0; $changed = $false
    $thisYear = (Get-Date).Year
    foreach ($game in @($g.Xml.gameList.SelectNodes('game'))) {
        $r = $game.SelectSingleNode('rating')
        if ($r -and $r.InnerText) { $v=0.0; if ([double]::TryParse($r.InnerText,[ref]$v)) { if ($v -gt 1 -or $v -lt 0) { if (-not $DryRun) { $r.InnerText = ([math]::Min(1,[math]::Max(0,$v/([math]::Ceiling($v))))).ToString('0.0') }; $fixed++; $changed=$true } } }
        $rd = $game.SelectSingleNode('releasedate')
        if ($rd -and $rd.InnerText -match '^(\d{4})') { if ([int]$Matches[1] -gt ($thisYear+1)) { if (-not $DryRun) { [void]$game.RemoveChild($rd) }; $fixed++; $changed=$true } }
        foreach ($tag in @('playtime','playcount')) {
            $n = $game.SelectSingleNode($tag)
            if ($n -and $n.InnerText) { $iv=0; if ([int]::TryParse($n.InnerText,[ref]$iv)) { if ($iv -lt 0) { if (-not $DryRun) { $n.InnerText = '0' }; $fixed++; $changed=$true } } }
        }
    }
    if ($changed -and -not $DryRun) {
        Backup-File -Path $GamelistPath -BackupRoot $BackupRoot | Out-Null
        Save-Gamelist -Xml $g.Xml -Prefix $g.Prefix -Path $GamelistPath
        & $Logger "Sanity-fixed $fixed metadata field(s) in $(Split-Path (Split-Path $GamelistPath -Parent) -Leaf)." 'SUCCESS'
    }
    return $fixed
}

function Add-UnlistedGames {
    <#
    .SYNOPSIS
        Adds <game> entries for ROM files present on disk but missing from the
        gamelist (so ES-DE shows them with at least a name). Returns count added.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string] $GamelistPath,
        [Parameter(Mandatory = $true)][string] $SystemRomDir,
        [Parameter(Mandatory = $true)][string] $BackupRoot,
        [Parameter(Mandatory = $true)][scriptblock] $Logger,
        [switch] $DryRun
    )
    if (-not (Test-Path -LiteralPath $SystemRomDir)) { return 0 }
    $nonRom = @('.txt','.xml','.dat','.jpg','.png','.bin','.srm','.state','.cfg','.sav','.cht')
    $g = Read-Gamelist -Path $GamelistPath
    $xml = $null; $prefix = ''
    if ($g.Ok) { $xml = $g.Xml; $prefix = $g.Prefix }
    else {
        $xml = New-Object System.Xml.XmlDocument
        [void]$xml.AppendChild($xml.CreateElement('gameList'))
        $prefix = '<?xml version="1.0"?>'
    }
    $listed = New-Object System.Collections.Generic.HashSet[string] ([StringComparer]::OrdinalIgnoreCase)
    foreach ($game in @($xml.gameList.SelectNodes('game'))) {
        $pn = $game.SelectSingleNode('path'); if ($pn -and $pn.InnerText) { [void]$listed.Add([System.IO.Path]::GetFileName(($pn.InnerText -replace '/','\'))) }
    }
    $added = 0
    Get-ChildItem -LiteralPath $SystemRomDir -File -ErrorAction SilentlyContinue | ForEach-Object {
        if ($nonRom -contains $_.Extension.ToLower()) { return }
        if ($_.Extension.ToLower() -eq '.bin' -and (Test-Path -LiteralPath ([System.IO.Path]::ChangeExtension($_.FullName,'cue')))) { return }
        if ($listed.Contains($_.Name)) { return }
        if (-not $DryRun) {
            $game = $xml.CreateElement('game')
            $p = $xml.CreateElement('path'); $p.InnerText = './' + $_.Name; [void]$game.AppendChild($p)
            $n = $xml.CreateElement('name'); $n.InnerText = [System.IO.Path]::GetFileNameWithoutExtension($_.Name); [void]$game.AppendChild($n)
            [void]$xml.gameList.AppendChild($game)
        }
        $added++
    }
    if ($added -gt 0 -and -not $DryRun) {
        Backup-File -Path $GamelistPath -BackupRoot $BackupRoot | Out-Null
        Save-Gamelist -Xml $xml -Prefix $prefix -Path $GamelistPath
        & $Logger "Added $added unlisted ROM(s) to $(Split-Path (Split-Path $GamelistPath -Parent) -Leaf) gamelist." 'SUCCESS'
    }
    return $added
}

Export-ModuleMember -Function Test-M3uPlaylists, Repair-MetadataSanity, Add-UnlistedGames
