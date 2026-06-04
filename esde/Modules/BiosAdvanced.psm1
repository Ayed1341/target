<#
.SYNOPSIS
    Advanced BIOS validation: presence, MD5 verification against known-good hashes,
    and wrong-location detection. Never deletes or downloads BIOS (copyright); it
    only reports, and points each file at the correct expected location.
#>

Set-StrictMode -Version Latest

function Get-FileMd5 {
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][string] $Path)
    try {
        $md5 = [System.Security.Cryptography.MD5]::Create()
        $fs  = [System.IO.File]::OpenRead($Path)
        try { return ([BitConverter]::ToString($md5.ComputeHash($fs))).Replace('-','').ToLower() }
        finally { $fs.Dispose(); $md5.Dispose() }
    } catch { return $null }
}

function Test-BiosAdvanced {
    <#
    .SYNOPSIS
        Validates BIOS files. For each requirement returns a record with Status:
          Present | WrongHash | WrongLocation | Missing
    .PARAMETER BiosDir
        The canonical BIOS directory (files are expected directly here).
    .PARAMETER Requirements
        Array of @{ file; system; md5(optional) }.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string]   $BiosDir,
        [Parameter(Mandatory = $true)][object[]] $Requirements,
        [Parameter(Mandatory = $true)][scriptblock] $Logger
    )
    $records = New-Object System.Collections.Generic.List[object]
    if (-not (Test-Path -LiteralPath $BiosDir)) {
        & $Logger "BIOS directory not found: $BiosDir" 'WARN'
    }

    # Index every file under the BIOS tree (recursive) for location detection.
    $allByName = @{}
    if (Test-Path -LiteralPath $BiosDir) {
        Get-ChildItem -LiteralPath $BiosDir -Recurse -File -ErrorAction SilentlyContinue | ForEach-Object {
            $k = $_.Name.ToLower()
            if (-not $allByName.ContainsKey($k)) { $allByName[$k] = $_.FullName }
        }
    }

    foreach ($req in $Requirements) {
        $name   = $req.file
        $expectAt = Join-Path $BiosDir $name
        $status = 'Missing'; $detail = "Place '$name' in $BiosDir (needed for $($req.system))."
        $foundAt = $null
        $reqMd5 = if ($req.PSObject.Properties.Name -contains 'md5' -and $req.md5) { ([string]$req.md5).ToLower() } else { $null }

        if (Test-Path -LiteralPath $expectAt) {
            $foundAt = $expectAt
            if ($reqMd5) {
                $actual = Get-FileMd5 -Path $expectAt
                if ($actual -eq $reqMd5) { $status = 'Present'; $detail = 'Present and hash-verified.' }
                else { $status = 'WrongHash'; $detail = "Present but MD5 mismatch (expected $reqMd5, got $actual)." }
            } else { $status = 'Present'; $detail = 'Present (no known hash to verify).' }
        }
        elseif ($allByName.ContainsKey($name.ToLower())) {
            $status = 'WrongLocation'
            $foundAt = $allByName[$name.ToLower()]
            $detail = "Found at $foundAt but ES-DE expects it at $expectAt."
        }

        if ($status -ne 'Present') { & $Logger "BIOS $status`: $name ($($req.system))" 'WARN' }
        $records.Add([ordered]@{ File = $name; System = $req.system; Status = $status; Detail = $detail; ExpectedAt = $expectAt; FoundAt = $foundAt; Md5 = $reqMd5 })
    }

    $present = @($records | Where-Object { $_.Status -eq 'Present' }).Count
    & $Logger "BIOS check: $present/$($records.Count) present and valid." 'INFO'
    return $records.ToArray()
}

function Invoke-BiosRelocate {
    <#
    .SYNOPSIS
        "Fixes directions" for BIOS the user already owns - it NEVER downloads
        copyrighted BIOS. Two safe, legal actions:
          1. Relocate: a required BIOS found elsewhere in the tree is copied to the
             canonical location ES-DE expects (the source is left in place).
          2. Propagate: a BIOS present in the canonical folder is copied into every
             other emulator BIOS directory that is missing it, so all emulators see
             it. Existing destination files are backed up first; nothing is deleted.
    .OUTPUTS
        Hashtable: Relocated, Propagated.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][object[]] $Records,
        [Parameter(Mandatory = $true)][string]   $CanonicalDir,
        [string[]] $CandidateDirs = @(),
        [Parameter(Mandatory = $true)][string]   $BackupRoot,
        [Parameter(Mandatory = $true)][scriptblock] $Logger,
        [switch] $DryRun
    )
    $relocated = 0; $propagated = 0
    $targets = @(@($CandidateDirs) + $CanonicalDir | Where-Object { $_ } | Select-Object -Unique)

    foreach ($rec in $Records) {
        # 1) Relocate wrong-location files into the canonical folder.
        if ($rec.Status -eq 'WrongLocation' -and $rec.FoundAt -and (Test-Path -LiteralPath $rec.FoundAt)) {
            if ($DryRun) { & $Logger "[DRY-RUN] Would relocate $($rec.File) -> $($rec.ExpectedAt)" 'INFO'; $relocated++; continue }
            $dstDir = Split-Path $rec.ExpectedAt -Parent
            if (-not (Test-Path -LiteralPath $dstDir)) { New-Item -Path $dstDir -ItemType Directory -Force | Out-Null }
            Copy-Item -LiteralPath $rec.FoundAt -Destination $rec.ExpectedAt -Force
            & $Logger "Relocated BIOS $($rec.File) to canonical location $($rec.ExpectedAt)." 'SUCCESS'
            $relocated++
            $rec.FoundAt = $rec.ExpectedAt; $rec.Status = 'Present'
        }
    }

    # 2) Propagate every BIOS that now exists in the canonical folder to all other
    #    emulator BIOS directories that are missing it.
    foreach ($rec in $Records) {
        $src = Join-Path $CanonicalDir $rec.File
        if (-not (Test-Path -LiteralPath $src)) { continue }
        foreach ($dir in $targets) {
            if ($dir -eq $CanonicalDir) { continue }
            $dst = Join-Path $dir $rec.File
            if (Test-Path -LiteralPath $dst) { continue }   # already there
            if ($DryRun) { & $Logger "[DRY-RUN] Would copy $($rec.File) -> $dir" 'INFO'; $propagated++; continue }
            if (-not (Test-Path -LiteralPath $dir)) { New-Item -Path $dir -ItemType Directory -Force | Out-Null }
            Copy-Item -LiteralPath $src -Destination $dst -Force
            $propagated++
        }
    }
    if ($propagated -gt 0) { & $Logger "Propagated BIOS to $propagated additional emulator location(s)." 'SUCCESS' }
    return @{ Relocated = $relocated; Propagated = $propagated }
}

Export-ModuleMember -Function Get-FileMd5, Test-BiosAdvanced, Invoke-BiosRelocate
