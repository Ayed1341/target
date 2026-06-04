<#
.SYNOPSIS
    Local media recovery and scrape-list export.
.DESCRIPTION
    * Recovers media that already exists but is named slightly differently from the
      ROM (e.g. region/version tags differ): it fuzzy-matches by a normalized stem
      and copies the file to the exact ROM stem so ES-DE will display it. This finds
      "missing" media you already have, without any download.
    * Exports a scrape list (the ROM files still missing media) that ES-DE's built-in
      scraper or ScreenScraper can consume.
#>

Set-StrictMode -Version Latest

function Get-NormalizedStem {
    <#
    .SYNOPSIS
        Normalizes a game name for fuzzy matching: drops (region)/[flag] groups,
        lowercases and strips non-alphanumerics.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][string] $Name)
    $s = $Name
    $s = [Regex]::Replace($s, '\([^)]*\)', '')   # (USA), (Rev 1) ...
    $s = [Regex]::Replace($s, '\[[^\]]*\]', '')  # [!], [b1] ...
    $s = $s.ToLower()
    $s = [Regex]::Replace($s, '[^a-z0-9]', '')
    return $s.Trim()
}

function Invoke-LocalMediaRecovery {
    <#
    .SYNOPSIS
        For one system, copies mislabeled media to the exact ROM stem when a fuzzy
        (normalized) match is found. Returns count recovered.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string] $SystemMediaDir,
        [System.Collections.Generic.HashSet[string]] $RomStems,
        [Parameter(Mandatory = $true)][string] $BackupRoot,
        [Parameter(Mandatory = $true)][scriptblock] $Logger,
        [switch] $DryRun
    )
    $recovered = 0
    if (-not (Test-Path -LiteralPath $SystemMediaDir)) { return 0 }
    if ($null -eq $RomStems -or $RomStems.Count -eq 0) { return 0 }

    # Map normalized -> exact ROM stem.
    $normToExact = @{}
    foreach ($stem in $RomStems) {
        $n = Get-NormalizedStem -Name $stem
        if ($n -and -not $normToExact.ContainsKey($n)) { $normToExact[$n] = $stem }
    }

    foreach ($sub in (Get-ChildItem -LiteralPath $SystemMediaDir -Directory -ErrorAction SilentlyContinue)) {
        foreach ($file in (Get-ChildItem -LiteralPath $sub.FullName -File -ErrorAction SilentlyContinue)) {
            $stem = [System.IO.Path]::GetFileNameWithoutExtension($file.Name)
            if ($RomStems.Contains($stem)) { continue }   # already correctly named
            $norm = Get-NormalizedStem -Name $stem
            if (-not $norm -or -not $normToExact.ContainsKey($norm)) { continue }
            $exact = $normToExact[$norm]
            $target = Join-Path $sub.FullName ($exact + $file.Extension)
            if (Test-Path -LiteralPath $target) { continue }   # correct one already there
            if ($DryRun) { & $Logger "[DRY-RUN] Would recover $($file.Name) -> $exact$($file.Extension)" 'INFO'; $recovered++; continue }
            Copy-Item -LiteralPath $file.FullName -Destination $target -Force
            $recovered++
        }
    }
    if ($recovered -gt 0) { & $Logger "Recovered $recovered mislabeled media file(s) for '$(Split-Path $SystemMediaDir -Leaf)'." 'SUCCESS' }
    return $recovered
}

function Export-ScrapeList {
    <#
    .SYNOPSIS
        Writes the ROM files of games still missing media to a text file, so the
        ES-DE scraper (or ScreenScraper) can target exactly what is needed.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][object]  $MissingResult,   # from Get-MissingMediaForSystem
        [Parameter(Mandatory = $true)][string]  $SystemRomDir,
        [Parameter(Mandatory = $true)][string]  $OutFile
    )
    $lines = New-Object System.Collections.Generic.List[string]
    $romByStem = @{}
    if (Test-Path -LiteralPath $SystemRomDir) {
        Get-ChildItem -LiteralPath $SystemRomDir -File -ErrorAction SilentlyContinue | ForEach-Object {
            $romByStem[[System.IO.Path]::GetFileNameWithoutExtension($_.Name)] = $_.FullName
        }
    }
    foreach ($rec in @($MissingResult.Records)) {
        $path = if ($romByStem.ContainsKey($rec.Game)) { $romByStem[$rec.Game] } else { $rec.Game }
        $lines.Add(('{0}`t{1}' -f $path, ($rec.Missing -join ',')))
    }
    if ($lines.Count -gt 0) {
        $dir = Split-Path $OutFile -Parent
        if ($dir -and -not (Test-Path -LiteralPath $dir)) { New-Item -Path $dir -ItemType Directory -Force | Out-Null }
        $header = "# ES-DE scrape list for $($MissingResult.System) - ROM<TAB>missing media types"
        Set-Content -LiteralPath $OutFile -Value (@($header) + $lines) -Encoding UTF8
    }
    return $lines.Count
}

Export-ModuleMember -Function Get-NormalizedStem, Invoke-LocalMediaRecovery, Export-ScrapeList
