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
        $reqMd5 = if ($req.PSObject.Properties.Name -contains 'md5' -and $req.md5) { ([string]$req.md5).ToLower() } else { $null }

        if (Test-Path -LiteralPath $expectAt) {
            if ($reqMd5) {
                $actual = Get-FileMd5 -Path $expectAt
                if ($actual -eq $reqMd5) { $status = 'Present'; $detail = 'Present and hash-verified.' }
                else { $status = 'WrongHash'; $detail = "Present but MD5 mismatch (expected $reqMd5, got $actual)." }
            } else { $status = 'Present'; $detail = 'Present (no known hash to verify).' }
        }
        elseif ($allByName.ContainsKey($name.ToLower())) {
            $status = 'WrongLocation'
            $detail = "Found at $($allByName[$name.ToLower()]) but ES-DE expects it at $expectAt."
        }

        if ($status -ne 'Present') { & $Logger "BIOS $status`: $name ($($req.system))" 'WARN' }
        $records.Add([ordered]@{ File = $name; System = $req.system; Status = $status; Detail = $detail; ExpectedAt = $expectAt })
    }

    $present = @($records | Where-Object { $_.Status -eq 'Present' }).Count
    & $Logger "BIOS check: $present/$($records.Count) present and valid." 'INFO'
    return $records.ToArray()
}

Export-ModuleMember -Function Get-FileMd5, Test-BiosAdvanced
