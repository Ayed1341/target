<#
.SYNOPSIS
    Reporting engine. Generates Full_Report.json plus Full_Report.html and the
    per-area HTML reports (Migration, Media, Metadata, Optimization, Controllers,
    Missing_Media, Duplicate) from a single structured report object.
#>

Set-StrictMode -Version Latest

function HtmlEnc { param([string]$s) if ($null -eq $s) { return '' } [System.Net.WebUtility]::HtmlEncode([string]$s) }

$script:Css = @'
<style>
 body{font-family:Segoe UI,Arial,sans-serif;background:#11131a;color:#e6e6e6;margin:0;padding:24px}
 h1{color:#7fd1ff;margin:0 0 4px} h2{color:#9ad19a;border-bottom:1px solid #2a2f3a;padding-bottom:6px;margin-top:26px}
 a{color:#7fd1ff} .sub{color:#8a93a6;margin-bottom:16px}
 .cards{display:flex;flex-wrap:wrap;gap:12px;margin-bottom:8px}
 .card{background:#1b1f29;border:1px solid #2a2f3a;border-radius:10px;padding:12px 16px;min-width:150px}
 .card .k{color:#8a93a6;font-size:12px;text-transform:uppercase} .card .v{font-size:18px;margin-top:4px}
 table{border-collapse:collapse;width:100%;margin-top:8px;background:#1b1f29;border-radius:8px;overflow:hidden}
 th,td{padding:7px 11px;text-align:left;border-bottom:1px solid #2a2f3a;font-size:13px}
 th{background:#222735;color:#bcd} .ok{color:#7ee27e} .warn{color:#e2a05a} .mono{font-family:Consolas,monospace;color:#9fb3c8}
 .footer{margin-top:24px;color:#6b7280;font-size:12px}
</style>
'@

function New-HtmlDocument {
    param([string]$Title, [string]$Body)
    return "<!DOCTYPE html><html lang=`"en`"><head><meta charset=`"utf-8`"><meta name=`"viewport`" content=`"width=device-width, initial-scale=1`"><title>$(HtmlEnc $Title)</title>$script:Css</head><body>$Body<div class=`"footer`">ES-DE Auto Suite &bull; generated $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')</div></body></html>"
}

function ConvertTo-HtmlTable {
    param([string[]]$Headers, [object[]]$Rows)
    $sb = New-Object System.Text.StringBuilder
    [void]$sb.Append('<table><tr>')
    foreach ($h in $Headers) { [void]$sb.Append("<th>$(HtmlEnc $h)</th>") }
    [void]$sb.Append('</tr>')
    if (-not $Rows -or @($Rows).Count -eq 0) {
        [void]$sb.Append("<tr><td colspan='$($Headers.Count)'>No data.</td></tr>")
    } else {
        foreach ($row in $Rows) {
            [void]$sb.Append('<tr>')
            foreach ($cell in $row) { [void]$sb.Append("<td>$(HtmlEnc ([string]$cell))</td>") }
            [void]$sb.Append('</tr>')
        }
    }
    [void]$sb.Append('</table>')
    return $sb.ToString()
}

function Write-EsdeReports {
    <#
    .SYNOPSIS
        Writes every report file into $ReportsDir from the $Data report object.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string] $ReportsDir,
        [Parameter(Mandatory = $true)][hashtable] $Data,
        [Parameter(Mandatory = $true)][scriptblock] $Logger
    )
    if (-not (Test-Path -LiteralPath $ReportsDir)) { New-Item -Path $ReportsDir -ItemType Directory -Force | Out-Null }

    # ---- JSON ----
    $jsonPath = Join-Path $ReportsDir 'Full_Report.json'
    ($Data | ConvertTo-Json -Depth 12) | Set-Content -LiteralPath $jsonPath -Encoding UTF8

    # ---- Migration report ----
    $migRows = @($Data.Migration.PerSystem | ForEach-Object { ,@($_.System, $_.FromGamelist, $_.FromFolders, $_.Skipped) })
    $migBody = "<h1>Migration Report</h1><div class='sub'>RetroBat &rarr; ES-DE media migration</div>" +
               (ConvertTo-HtmlTable -Headers @('System','From gamelist','From folders','Skipped') -Rows $migRows)
    Set-Content (Join-Path $ReportsDir 'Migration_Report.html') (New-HtmlDocument 'Migration Report' $migBody) -Encoding UTF8

    # ---- Media report ----
    $medRows = @($Data.Media.PerSystem | ForEach-Object { ,@($_.System, $_.FoldersCreated, $_.Moved, $_.Skipped) })
    $medBody = "<h1>Media Report</h1><div class='sub'>Folder creation &amp; reorganization</div>" +
               (ConvertTo-HtmlTable -Headers @('System','Folders created','Files moved','Skipped') -Rows $medRows)
    Set-Content (Join-Path $ReportsDir 'Media_Report.html') (New-HtmlDocument 'Media Report' $medBody) -Encoding UTF8

    # ---- Metadata report ----
    $metRows = @($Data.Metadata.PerSystem | ForEach-Object { ,@($_.System, $_.Games, $_.Duplicates, $_.Repaired, $_.Removed, $(if ($_.Invalid) {'YES'} else {'no'})) })
    $metBody = "<h1>Metadata Report</h1><div class='sub'>gamelist.xml validation &amp; repair</div>" +
               (ConvertTo-HtmlTable -Headers @('System','Games','Duplicates removed','Paths repaired','Refs stripped','Was invalid') -Rows $metRows)
    Set-Content (Join-Path $ReportsDir 'Metadata_Report.html') (New-HtmlDocument 'Metadata Report' $metBody) -Encoding UTF8

    # ---- Optimization report ----
    $optRows = @($Data.Optimization | ForEach-Object { ,@($_.Emulator, $_.Result) })
    $optBody = "<h1>Optimization Report</h1><div class='sub'>Emulator graphics configuration</div>" +
               (ConvertTo-HtmlTable -Headers @('Emulator','Result') -Rows $optRows)
    Set-Content (Join-Path $ReportsDir 'Optimization_Report.html') (New-HtmlDocument 'Optimization Report' $optBody) -Encoding UTF8

    # ---- Controllers report ----
    $ctlRows = @($Data.Controllers | ForEach-Object { ,@($_.Name, $_.Vendor, $_.Family, $_.Api, $_.Connection, $_.VidPid) })
    $ctlBody = "<h1>Controllers Report</h1><div class='sub'>Detected controllers &amp; mappings</div>" +
               (ConvertTo-HtmlTable -Headers @('Name','Vendor','Family','API','Connection','VID:PID') -Rows $ctlRows)
    Set-Content (Join-Path $ReportsDir 'Controllers_Report.html') (New-HtmlDocument 'Controllers Report' $ctlBody) -Encoding UTF8

    # ---- Missing media report ----
    $mmRows = @($Data.MissingMedia.PerSystem | ForEach-Object {
        $t = $_.Totals
        ,@($_.System, $_.Games, $t.covers, $t.screenshots, $t.videos, $t.marquees, $t.fanart, $t.titlescreens, $t.manuals)
    })
    $mmBody = "<h1>Missing Media Report</h1><div class='sub'>Games missing each media type</div>" +
              (ConvertTo-HtmlTable -Headers @('System','Games','covers','screenshots','videos','marquees','fanart','titlescreens','manuals') -Rows $mmRows)
    Set-Content (Join-Path $ReportsDir 'Missing_Media_Report.html') (New-HtmlDocument 'Missing Media Report' $mmBody) -Encoding UTF8

    # ---- Duplicate report ----
    $dupRows = @($Data.Duplicates.Groups | Select-Object -First 500 | ForEach-Object { ,@($_.Hash.Substring(0,12), @($_.Files).Count, ($_.Files -join '  |  ')) })
    $dupBody = "<h1>Duplicate Report</h1><div class='sub'>$($Data.Duplicates.DuplicateFiles) duplicate file(s), $([math]::Round($Data.Duplicates.ReclaimableBytes/1MB,2)) MB reclaimable</div>" +
               (ConvertTo-HtmlTable -Headers @('SHA256 (short)','Copies','Files') -Rows $dupRows)
    Set-Content (Join-Path $ReportsDir 'Duplicate_Report.html') (New-HtmlDocument 'Duplicate Report' $dupBody) -Encoding UTF8

    # ---- Missing emulators report ----
    $gapRows = @()
    if ($Data.Keys -contains 'EmulatorGaps') {
        $gapRows = @($Data.EmulatorGaps | Where-Object { $_.Missing } | ForEach-Object { ,@($_.System, ($_.Required -join ', '), $_.Recommended) })
    }
    $gapBody = "<h1>Missing Emulators Report</h1><div class='sub'>Systems that have ROMs but no installed emulator</div>" +
               (ConvertTo-HtmlTable -Headers @('System','Compatible emulators','Recommended') -Rows $gapRows)
    Set-Content (Join-Path $ReportsDir 'Missing_Emulators_Report.html') (New-HtmlDocument 'Missing Emulators Report' $gapBody) -Encoding UTF8

    # ---- BIOS report ----
    $biosDetRows = @()
    if ($Data.Keys -contains 'BiosDetailed') {
        $biosDetRows = @($Data.BiosDetailed | ForEach-Object { ,@($_.File, $_.System, $_.Status, $_.Detail) })
    }
    $biosBody = "<h1>BIOS Report</h1><div class='sub'>Presence, MD5 verification and location</div>" +
                (ConvertTo-HtmlTable -Headers @('File','System','Status','Detail') -Rows $biosDetRows)
    Set-Content (Join-Path $ReportsDir 'Bios_Report.html') (New-HtmlDocument 'BIOS Report' $biosBody) -Encoding UTF8

    # ---- Health report ----
    $healthRows = @()
    if ($Data.Keys -contains 'Health') { $healthRows = @($Data.Health | ForEach-Object { ,@($_.Time, $_.Area, $_.Status, $_.Detail) }) }
    $phaseRows = @()
    if ($Data.Keys -contains 'PhaseResults') { $phaseRows = @($Data.PhaseResults | ForEach-Object { ,@($_.Phase, $_.Result, $_.Seconds, $_.Error) }) }
    $healthBody = "<h1>Health &amp; Self-Repair Report</h1><div class='sub'>$($Data.Errors) error(s), $($Data.Warnings) warning(s) - the suite continued through every phase</div>" +
                  "<h2>Findings</h2>" + (ConvertTo-HtmlTable -Headers @('Time','Area','Status','Detail') -Rows $healthRows) +
                  "<h2>Phase timings</h2>" + (ConvertTo-HtmlTable -Headers @('Phase','Result','Seconds','Error') -Rows $phaseRows)
    Set-Content (Join-Path $ReportsDir 'Health_Report.html') (New-HtmlDocument 'Health Report' $healthBody) -Encoding UTF8

    # ---- Full report (overview + links) ----
    $hw = $Data.Hardware
    $biosRows = @($Data.Bios | ForEach-Object { ,@($_.File, $_.System) })
    $sysRows  = @($Data.Systems | ForEach-Object { ,@($_.Name, $(if($_.Roms){'yes'}else{'-'}), $(if($_.Gamelist){'yes'}else{'-'}), $(if($_.Media){'yes'}else{'-'})) })
    $links = @('Migration_Report.html','Media_Report.html','Metadata_Report.html','Optimization_Report.html','Missing_Emulators_Report.html','Controllers_Report.html','Missing_Media_Report.html','Duplicate_Report.html','Bios_Report.html','Health_Report.html')
    $linkHtml = ($links | ForEach-Object { "<a href='$_'>$($_ -replace '_',' ' -replace '\.html','')</a>" }) -join ' &bull; '

    $body = @"
<h1>ES-DE Auto Suite &mdash; Full Report</h1>
<div class="sub">Generated $(HtmlEnc $Data.GeneratedAt) &bull; ES-DE $(HtmlEnc $Data.EsdeVersion) &bull; Data: $(HtmlEnc $Data.DataDir)</div>
<div class="cards">
 <div class="card"><div class="k">Performance tier</div><div class="v">$(HtmlEnc $Data.Tier)</div></div>
 <div class="card"><div class="k">Target resolution</div><div class="v">$($Data.Profile.TargetWidth) x $($Data.Profile.TargetHeight)</div></div>
 <div class="card"><div class="k">Systems</div><div class="v">$(@($Data.Systems).Count)</div></div>
 <div class="card"><div class="k">Media migrated</div><div class="v">$($Data.Migration.TotalCopied)</div></div>
 <div class="card"><div class="k">Media reorganized</div><div class="v">$($Data.Media.TotalMoved)</div></div>
 <div class="card"><div class="k">Duplicates</div><div class="v">$($Data.Duplicates.DuplicateFiles)</div></div>
 <div class="card"><div class="k">Controllers</div><div class="v">$(@($Data.Controllers).Count)</div></div>
 <div class="card"><div class="k">Warnings</div><div class="v">$($Data.Warnings)</div></div>
</div>
<h2>Reports</h2><div class="sub">$linkHtml</div>
<h2>Hardware</h2>
<div class="cards">
 <div class="card"><div class="k">CPU</div><div class="v">$(HtmlEnc $hw.CpuName)</div></div>
 <div class="card"><div class="k">GPU</div><div class="v">$(HtmlEnc $hw.GpuName) ($(HtmlEnc $hw.GpuVendor))</div></div>
 <div class="card"><div class="k">VRAM</div><div class="v">$($hw.GpuVramMB) MB</div></div>
 <div class="card"><div class="k">RAM</div><div class="v">$($hw.TotalRamGB) GB</div></div>
 <div class="card"><div class="k">Display</div><div class="v">$($hw.DisplayWidth)x$($hw.DisplayHeight)@$($hw.RefreshRateHz)Hz</div></div>
</div>
<h2>Systems</h2>
$(ConvertTo-HtmlTable -Headers @('System','ROMs','Gamelist','Media') -Rows $sysRows)
<h2>Missing BIOS</h2>
$(ConvertTo-HtmlTable -Headers @('File','Needed for') -Rows $biosRows)
"@
    Set-Content (Join-Path $ReportsDir 'Full_Report.html') (New-HtmlDocument 'ES-DE Auto Suite Full Report' $body) -Encoding UTF8

    & $Logger "Reports written to $ReportsDir (Full_Report.html/.json + 7 section reports)." 'SUCCESS'
}

Export-ModuleMember -Function Write-EsdeReports, New-HtmlDocument, ConvertTo-HtmlTable
