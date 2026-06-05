<#
.SYNOPSIS
    Safe ES-DE user-experience settings tuning + run history.
.DESCRIPTION
    Writes a small set of safe, widely-liked es_settings.xml options (after backup)
    and configures the built-in scraper to ScreenScraper. Also maintains a run
    history JSON so successive runs can be compared over time.
#>

Set-StrictMode -Version Latest

function Optimize-EsdeUxSettings {
    <#
    .SYNOPSIS
        Applies safe ES-DE UX settings. Returns count of settings applied.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string] $SettingsFile,
        [Parameter(Mandatory = $true)][string] $BackupRoot,
        [Parameter(Mandatory = $true)][scriptblock] $Logger,
        [switch] $DryRun
    )
    if (-not (Test-Path -LiteralPath $SettingsFile)) { return 0 }
    if ($DryRun) { & $Logger "[DRY-RUN] Would apply ES-DE UX settings." 'INFO'; return 0 }
    Backup-File -Path $SettingsFile -BackupRoot $BackupRoot | Out-Null
    $bools = [ordered]@{
        'MediaViewerKeepVideoRunning' = 'true'
        'GamelistVideoPause'          = 'false'
        'FoldersOnTop'                = 'true'
        'ListScrollOverlay'           = 'true'
        'VideoAudio'                  = 'true'
    }
    $strings = [ordered]@{
        'Scraper'       = 'screenscraper'
        'ScraperRegion' = 'us'
    }
    $n = 0
    foreach ($k in $bools.Keys)   { Set-EsdeSettingValue -SettingsFile $SettingsFile -Type 'bool'   -Name $k -Value $bools[$k]; $n++ }
    foreach ($k in $strings.Keys) { Set-EsdeSettingValue -SettingsFile $SettingsFile -Type 'string' -Name $k -Value $strings[$k]; $n++ }
    & $Logger "Applied $n ES-DE UX setting(s) (media viewer, folders-on-top, scraper=screenscraper)." 'SUCCESS'
    return $n
}

function Update-RunHistory {
    <#
    .SYNOPSIS
        Appends a compact summary of this run to history.json (keeps last 50 runs).
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string] $WorkRoot,
        [Parameter(Mandatory = $true)][hashtable] $Summary
    )
    $path = Join-Path $WorkRoot 'history.json'
    $history = @()
    if (Test-Path -LiteralPath $path) {
        try { $history = @(Get-Content -LiteralPath $path -Raw -Encoding UTF8 | ConvertFrom-Json) } catch { $history = @() }
    }
    $history += [pscustomobject]$Summary
    if ($history.Count -gt 50) { $history = $history[($history.Count-50)..($history.Count-1)] }
    ($history | ConvertTo-Json -Depth 6) | Set-Content -LiteralPath $path -Encoding UTF8
    return $path
}

Export-ModuleMember -Function Optimize-EsdeUxSettings, Update-RunHistory
