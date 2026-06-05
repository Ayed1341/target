<#
.SYNOPSIS
    Gamelist metadata enrichment & hygiene (dual-root aware, backup-first).
.DESCRIPTION
    Improves gamelist.xml quality in a single safe pass:
      * fill missing <name> from the ROM filename
      * add <sortname> for leading articles (The/A/An) so ES-DE sorts correctly
      * strip empty/whitespace-only metadata tags
      * convert absolute media paths to portable relative ones
      * mark obvious BIOS/boot-disc entries as <hidden>
    Plus read-only analytics: scraped-vs-unscraped ratio and duplicate names.
#>

Set-StrictMode -Version Latest

$script:HygieneTags = @('desc','rating','releasedate','developer','publisher','genre','players',
                        'image','thumbnail','marquee','video','fanart','titleshot','manual','boxback')

function Optimize-GamelistMetadata {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string] $GamelistPath,
        [Parameter(Mandatory = $true)][string] $SystemRomDir,
        [Parameter(Mandatory = $true)][string] $BackupRoot,
        [Parameter(Mandatory = $true)][scriptblock] $Logger,
        [switch] $DryRun
    )
    $stats = @{ Filled=0; SortNames=0; Emptied=0; Relativized=0; Hidden=0; Changed=$false }
    if (-not (Test-Path -LiteralPath $GamelistPath)) { return $stats }
    $g = Read-Gamelist -Path $GamelistPath
    if (-not $g.Ok) { return $stats }
    $xml = $g.Xml; $baseDir = Split-Path $GamelistPath -Parent

    foreach ($game in @($xml.gameList.SelectNodes('game'))) {
        $pathNode = $game.SelectSingleNode('path')
        $romStem = if ($pathNode -and $pathNode.InnerText) { [System.IO.Path]::GetFileNameWithoutExtension($pathNode.InnerText) } else { $null }

        # 1) Fill missing <name>.
        $nameNode = $game.SelectSingleNode('name')
        if ((-not $nameNode -or [string]::IsNullOrWhiteSpace($nameNode.InnerText)) -and $romStem) {
            if (-not $nameNode) { $nameNode = $xml.CreateElement('name'); [void]$game.AppendChild($nameNode) }
            $nameNode.InnerText = $romStem; $stats.Filled++; $stats.Changed = $true
        }

        # 2) <sortname> for leading articles.
        if ($nameNode -and $nameNode.InnerText -match '^(The|A|An)\s+(.*)$') {
            $sort = ('{0}, {1}' -f $Matches[2], $Matches[1])
            $sn = $game.SelectSingleNode('sortname')
            if (-not $sn) { $sn = $xml.CreateElement('sortname'); [void]$game.AppendChild($sn) }
            if ($sn.InnerText -ne $sort) { $sn.InnerText = $sort; $stats.SortNames++; $stats.Changed = $true }
        }

        # 3) Strip empty metadata tags.
        foreach ($tag in $script:HygieneTags) {
            foreach ($n in @($game.SelectNodes($tag))) {
                if (-not $n.HasChildNodes -or [string]::IsNullOrWhiteSpace($n.InnerText)) {
                    [void]$game.RemoveChild($n); $stats.Emptied++; $stats.Changed = $true
                }
            }
        }

        # 4) Absolute media paths -> relative.
        foreach ($tag in @('image','thumbnail','marquee','video','fanart','titleshot','manual','boxback')) {
            $n = $game.SelectSingleNode($tag)
            if (-not $n -or [string]::IsNullOrWhiteSpace($n.InnerText)) { continue }
            $val = $n.InnerText
            if ([System.IO.Path]::IsPathRooted($val) -and (Test-Path -LiteralPath $val)) {
                $n.InnerText = Get-RelativePathManual -FromDir $baseDir -ToPath $val
                $stats.Relativized++; $stats.Changed = $true
            }
        }

        # 5) Mark BIOS/boot-disc as hidden.
        $hay = ''
        if ($nameNode) { $hay += $nameNode.InnerText }
        if ($pathNode) { $hay += ' ' + $pathNode.InnerText }
        if ($hay -match '(?i)\b(bios|boot ?disc|\[bios\]|firmware)\b') {
            $h = $game.SelectSingleNode('hidden')
            if (-not $h) { $h = $xml.CreateElement('hidden'); [void]$game.AppendChild($h) }
            if ($h.InnerText -ne 'true') { $h.InnerText = 'true'; $stats.Hidden++; $stats.Changed = $true }
        }
    }

    if ($stats.Changed -and -not $DryRun) {
        Backup-File -Path $GamelistPath -BackupRoot $BackupRoot | Out-Null
        Save-Gamelist -Xml $xml -Prefix $g.Prefix -Path $GamelistPath
        & $Logger "Enriched $(Split-Path (Split-Path $GamelistPath -Parent) -Leaf): names+$($stats.Filled), sortnames+$($stats.SortNames), emptied-$($stats.Emptied), rel+$($stats.Relativized), hidden+$($stats.Hidden)." 'SUCCESS'
    } elseif ($stats.Changed -and $DryRun) {
        & $Logger "[DRY-RUN] Would enrich $GamelistPath (filled=$($stats.Filled), sortnames=$($stats.SortNames))." 'INFO'
    }
    return $stats
}

function Get-ScrapeRatio {
    <#
    .SYNOPSIS
        Returns how many games are 'scraped' (have a description) vs total.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][string] $SystemName, [string] $GamelistPath)
    $total = 0; $scraped = 0; $dupNames = 0
    if ($GamelistPath -and (Test-Path -LiteralPath $GamelistPath)) {
        $g = Read-Gamelist -Path $GamelistPath
        if ($g.Ok) {
            $names = @{}
            foreach ($game in @($g.Games)) {
                $total++
                $d = $game.SelectSingleNode('desc')
                if ($d -and -not [string]::IsNullOrWhiteSpace($d.InnerText)) { $scraped++ }
                $nm = $game.SelectSingleNode('name')
                if ($nm -and $nm.InnerText) {
                    $k = $nm.InnerText.ToLower()
                    if ($names.ContainsKey($k)) { $dupNames++ } else { $names[$k] = $true }
                }
            }
        }
    }
    $pct = if ($total -gt 0) { [math]::Round(($scraped*100.0)/$total,1) } else { 0 }
    return @{ System=$SystemName; Total=$total; Scraped=$scraped; Percent=$pct; DuplicateNames=$dupNames }
}

Export-ModuleMember -Function Optimize-GamelistMetadata, Get-ScrapeRatio
