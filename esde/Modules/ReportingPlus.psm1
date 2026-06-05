<#
.SYNOPSIS
    Additional report formats: CSV (spreadsheet-friendly) and a Markdown summary.
#>

Set-StrictMode -Version Latest

function Export-CsvReports {
    <#
    .SYNOPSIS
        Writes per-system summary and missing-media CSV files to the reports dir.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string] $ReportsDir,
        [Parameter(Mandatory = $true)][hashtable] $Data
    )
    if (-not (Test-Path -LiteralPath $ReportsDir)) { New-Item -Path $ReportsDir -ItemType Directory -Force | Out-Null }

    # Per-system summary CSV.
    $rows = New-Object System.Collections.Generic.List[object]
    foreach ($s in @($Data.Systems)) {
        $mm = @($Data.MissingMedia.PerSystem | Where-Object { $_.System -eq $s.Name }) | Select-Object -First 1
        $cov = @($Data.Audit.MediaCoverage | Where-Object { $_.System -eq $s.Name }) | Select-Object -First 1
        $rows.Add([pscustomobject]@{
            System      = $s.Name
            HasRoms     = $s.Roms
            HasGamelist = $s.Gamelist
            Games       = if ($mm) { $mm.Games } else { 0 }
            CoversPct   = if ($cov) { $cov.Covers } else { '' }
            MissingCovers = if ($mm) { $mm.Totals.covers } else { '' }
            MissingVideos = if ($mm) { $mm.Totals.videos } else { '' }
        })
    }
    if ($rows.Count -gt 0) { $rows | Export-Csv -LiteralPath (Join-Path $ReportsDir 'Systems_Summary.csv') -NoTypeInformation -Encoding UTF8 }

    # Missing-media flat CSV.
    $mrows = New-Object System.Collections.Generic.List[object]
    foreach ($ps in @($Data.MissingMedia.PerSystem)) {
        $t = $ps.Totals
        $mrows.Add([pscustomobject]@{
            System=$ps.System; Games=$ps.Games; Covers=$t.covers; Screenshots=$t.screenshots
            Videos=$t.videos; Marquees=$t.marquees; Fanart=$t.fanart; Titlescreens=$t.titlescreens; Manuals=$t.manuals
        })
    }
    if ($mrows.Count -gt 0) { $mrows | Export-Csv -LiteralPath (Join-Path $ReportsDir 'Missing_Media.csv') -NoTypeInformation -Encoding UTF8 }
    return $true
}

function Export-MarkdownSummary {
    <#
    .SYNOPSIS
        Writes a concise Markdown summary of the run.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string] $ReportsDir,
        [Parameter(Mandatory = $true)][hashtable] $Data
    )
    $sb = New-Object System.Text.StringBuilder
    [void]$sb.AppendLine("# ES-DE Auto Suite - Summary")
    [void]$sb.AppendLine("")
    [void]$sb.AppendLine("- Generated: $($Data.GeneratedAt)")
    [void]$sb.AppendLine("- ES-DE: $($Data.EsdeVersion)  |  Tier: $($Data.Tier)  |  Target: $($Data.Profile.TargetWidth)x$($Data.Profile.TargetHeight)")
    [void]$sb.AppendLine("- Systems: $(@($Data.Systems).Count)  |  Controllers: $(@($Data.Controllers).Count)")
    [void]$sb.AppendLine("- Media migrated: $($Data.Migration.TotalCopied)  |  reorganized: $($Data.Media.TotalMoved)  |  duplicates removed scan: $($Data.Duplicates.DuplicateFiles)")
    [void]$sb.AppendLine("- Health: $($Data.Errors) error(s), $($Data.Warnings) warning(s)")
    [void]$sb.AppendLine("")
    [void]$sb.AppendLine("## Systems")
    [void]$sb.AppendLine("")
    [void]$sb.AppendLine("| System | ROMs | Gamelist | Media |")
    [void]$sb.AppendLine("|---|---|---|---|")
    foreach ($s in @($Data.Systems)) {
        [void]$sb.AppendLine("| $($s.Name) | $(if($s.Roms){'yes'}else{'-'}) | $(if($s.Gamelist){'yes'}else{'-'}) | $(if($s.Media){'yes'}else{'-'}) |")
    }
    [void]$sb.AppendLine("")
    [void]$sb.AppendLine("## Missing BIOS")
    [void]$sb.AppendLine("")
    foreach ($b in @($Data.Bios)) { [void]$sb.AppendLine("- $($b.File) - $($b.System)") }
    Set-Content -LiteralPath (Join-Path $ReportsDir 'Summary.md') -Value $sb.ToString() -Encoding UTF8
    return $true
}

Export-ModuleMember -Function Export-CsvReports, Export-MarkdownSummary
