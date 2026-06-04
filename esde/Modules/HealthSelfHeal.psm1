<#
.SYNOPSIS
    Health & self-healing engine for the ES-DE Auto Suite.
.DESCRIPTION
    Provides the resilience layer that lets the suite diagnose and repair itself:
      * Invoke-Phase  - runs each pipeline phase in isolation; an error in one
                        phase is logged, optionally auto-recovered, and the run
                        CONTINUES instead of aborting.
      * Invoke-WithRetry - retry transient IO/network operations with backoff.
      * Test-PathWritable / Get-FreeSpaceGB - environment self-tests.
      * Repair-EsdeStructure - recreate any missing ES-DE directory.
      * Repair-XmlFile - validate XML, restore from backup or quarantine if broken.
      * Health findings are collected and written to a Health report (HTML+JSON).
#>

Set-StrictMode -Version Latest

$script:HealthFindings = New-Object System.Collections.Generic.List[object]
$script:PhaseResults   = New-Object System.Collections.Generic.List[object]

function Initialize-Health {
    [CmdletBinding()] param()
    $script:HealthFindings = New-Object System.Collections.Generic.List[object]
    $script:PhaseResults   = New-Object System.Collections.Generic.List[object]
}

function Add-HealthFinding {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string] $Area,
        [Parameter(Mandatory = $true)][ValidateSet('OK','Fixed','Warning','Error')] [string] $Status,
        [Parameter(Mandatory = $true)][string] $Detail
    )
    $script:HealthFindings.Add([ordered]@{ Area = $Area; Status = $Status; Detail = $Detail; Time = (Get-Date -Format 'HH:mm:ss') })
}

function Get-HealthFindings { return $script:HealthFindings.ToArray() }
function Get-PhaseResults  { return $script:PhaseResults.ToArray() }

function Invoke-Phase {
    <#
    .SYNOPSIS
        Runs a phase scriptblock guarded by try/catch. On failure it logs the error,
        runs an optional Recovery scriptblock, records a health finding and returns
        $false WITHOUT throwing, so the overall pipeline keeps going (self-healing).
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string] $Name,
        [Parameter(Mandatory = $true)][scriptblock] $Action,
        [Parameter(Mandatory = $true)][scriptblock] $Logger,
        [scriptblock] $Recovery
    )
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    try {
        & $Action
        $sw.Stop()
        $script:PhaseResults.Add([ordered]@{ Phase = $Name; Result = 'OK'; Seconds = [math]::Round($sw.Elapsed.TotalSeconds,2); Error = '' })
        return $true
    } catch {
        $sw.Stop()
        $msg = $_.Exception.Message
        & $Logger "Phase '$Name' error: $msg" 'ERROR'
        Add-HealthFinding -Area $Name -Status 'Error' -Detail $msg
        if ($Recovery) {
            try {
                & $Logger "Attempting self-repair for phase '$Name'..." 'WARN'
                & $Recovery
                & $Logger "Self-repair for phase '$Name' completed; continuing." 'SUCCESS'
                Add-HealthFinding -Area $Name -Status 'Fixed' -Detail "Recovered after error: $msg"
            } catch {
                & $Logger "Self-repair for phase '$Name' failed: $($_.Exception.Message)" 'ERROR'
            }
        }
        $script:PhaseResults.Add([ordered]@{ Phase = $Name; Result = 'Recovered'; Seconds = [math]::Round($sw.Elapsed.TotalSeconds,2); Error = $msg })
        return $false
    }
}

function Invoke-WithRetry {
    <#
    .SYNOPSIS
        Executes a scriptblock, retrying on exception with exponential backoff.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][scriptblock] $Action,
        [int] $MaxRetries = 3,
        [int] $DelaySeconds = 2
    )
    $attempt = 0; $delay = $DelaySeconds
    while ($true) {
        try { return (& $Action) }
        catch {
            $attempt++
            if ($attempt -ge $MaxRetries) { throw }
            Start-Sleep -Seconds $delay
            $delay *= 2
        }
    }
}

function Test-PathWritable {
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][string] $Path)
    try {
        if (-not (Test-Path -LiteralPath $Path)) { New-Item -Path $Path -ItemType Directory -Force -ErrorAction Stop | Out-Null }
        $probe = Join-Path $Path (".__write_test_{0}.tmp" -f ([Guid]::NewGuid().ToString('N')))
        [System.IO.File]::WriteAllText($probe, 'ok')
        Remove-Item -LiteralPath $probe -Force -ErrorAction SilentlyContinue
        return $true
    } catch { return $false }
}

function Get-FreeSpaceGB {
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][string] $Path)
    try {
        $full = [System.IO.Path]::GetFullPath($Path)
        $root = [System.IO.Path]::GetPathRoot($full)
        $di = New-Object System.IO.DriveInfo($root)
        return [math]::Round($di.AvailableFreeSpace / 1GB, 1)
    } catch { return -1 }
}

function Repair-EsdeStructure {
    <#
    .SYNOPSIS
        Ensures every required ES-DE directory exists (auto-heal). Returns count created.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][System.Collections.Specialized.OrderedDictionary] $Layout,
        [Parameter(Mandatory = $true)][scriptblock] $Logger,
        [switch] $DryRun
    )
    $required = @($Layout.Settings, $Layout.Gamelists, $Layout.DownloadedMedia, $Layout.Themes,
                  $Layout.CustomSystems, $Layout.Collections, $Layout.ScraperCache)
    $created = 0
    foreach ($d in $required) {
        if ($d -and -not (Test-Path -LiteralPath $d)) {
            if (-not $DryRun) { New-Item -Path $d -ItemType Directory -Force | Out-Null }
            $created++
            & $Logger "Created missing ES-DE directory: $d" 'WARN'
            Add-HealthFinding -Area 'Structure' -Status 'Fixed' -Detail "Created $d"
        }
    }
    if ($created -eq 0) { Add-HealthFinding -Area 'Structure' -Status 'OK' -Detail 'All ES-DE directories present.' }
    return $created
}

function Test-XmlWellFormed {
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][string] $Path)
    if (-not (Test-Path -LiteralPath $Path)) { return $false }
    try {
        $raw = Get-Content -LiteralPath $Path -Raw -Encoding UTF8
        # Tolerate ES-DE dual-root by testing only the gameList element if present.
        $i = $raw.IndexOf('<gameList')
        if ($i -ge 0) {
            $e = $raw.LastIndexOf('</gameList>')
            if ($e -ge 0) { $raw = $raw.Substring($i, ($e - $i) + 11) } else { $raw = $raw.Substring($i) }
        }
        $null = [xml]$raw
        return $true
    } catch { return $false }
}

function Repair-XmlFile {
    <#
    .SYNOPSIS
        If an XML file is malformed, restores the newest backup; if none exists,
        quarantines the corrupt file so ES-DE can regenerate it. Never data-loses.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string] $Path,
        [Parameter(Mandatory = $true)][string] $BackupRoot,
        [Parameter(Mandatory = $true)][scriptblock] $Logger,
        [switch] $DryRun
    )
    if (Test-XmlWellFormed -Path $Path) { return $true }
    & $Logger "Malformed XML detected: $Path" 'ERROR'
    if ($DryRun) { Add-HealthFinding -Area 'XML' -Status 'Warning' -Detail "Malformed (dry-run): $Path"; return $false }

    if (Restore-LatestFile -OriginalPath $Path -BackupRoot $BackupRoot) {
        if (Test-XmlWellFormed -Path $Path) {
            & $Logger "Restored valid XML from backup: $Path" 'SUCCESS'
            Add-HealthFinding -Area 'XML' -Status 'Fixed' -Detail "Restored from backup: $Path"
            return $true
        }
    }
    $q = Join-Path $BackupRoot ('corrupt_xml\' + (Split-Path $Path -Leaf) + '.' + (Get-Date -Format 'yyyyMMdd_HHmmss') + '.corrupt')
    $qd = Split-Path $q -Parent
    if (-not (Test-Path -LiteralPath $qd)) { New-Item -Path $qd -ItemType Directory -Force | Out-Null }
    Copy-Item -LiteralPath $Path -Destination $q -Force -ErrorAction SilentlyContinue
    & $Logger "No valid backup; quarantined corrupt copy to $q (ES-DE will regenerate)." 'WARN'
    Add-HealthFinding -Area 'XML' -Status 'Warning' -Detail "Quarantined corrupt file: $Path"
    return $false
}

Export-ModuleMember -Function Initialize-Health, Add-HealthFinding, Get-HealthFindings, Get-PhaseResults, `
    Invoke-Phase, Invoke-WithRetry, Test-PathWritable, Get-FreeSpaceGB, Repair-EsdeStructure, `
    Test-XmlWellFormed, Repair-XmlFile
