<#
.SYNOPSIS
    Missing-emulator gap analysis + executable integrity verification.
.DESCRIPTION
    Cross-references each ES-DE system that has ROMs against the emulators actually
    installed, using a system->emulator map. Reports, per system, which emulator is
    required, which are available, and whether a usable emulator is missing. Also
    verifies that detected emulator executables are real (non-empty, valid PE header)
    and flags "partially installed" emulator folders.
#>

Set-StrictMode -Version Latest

function Test-ExecutableIntegrity {
    <#
    .SYNOPSIS
        Returns $true if the file exists, is non-empty and begins with the 'MZ'
        DOS/PE signature (i.e. a real Windows executable, not a 0-byte stub).
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][string] $Path)
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { return $false }
    try {
        $fi = Get-Item -LiteralPath $Path
        if ($fi.Length -lt 2) { return $false }
        $fs = [System.IO.File]::OpenRead($Path)
        try {
            $b0 = $fs.ReadByte(); $b1 = $fs.ReadByte()
            return ($b0 -eq 0x4D -and $b1 -eq 0x5A)   # 'M','Z'
        } finally { $fs.Dispose() }
    } catch { return $false }
}

function Get-EmulatorGaps {
    <#
    .SYNOPSIS
        Builds per-system emulator gap records.
    .PARAMETER Systems
        System descriptors (from Get-EsdeSystems): need .Name and .HasRoms.
    .PARAMETER InstalledIds
        Array of emulator ids that were detected as installed.
    .PARAMETER SystemMap
        Hashtable system-name -> array of emulator ids (from esde-media.json).
    .OUTPUTS
        Array of records: System, HasRoms, Required[], Available[], Missing(bool), Recommended
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][object[]]  $Systems,
        [string[]]  $InstalledIds = @(),
        [Parameter(Mandatory = $true)][hashtable] $SystemMap
    )
    $installed = New-Object System.Collections.Generic.HashSet[string] ([StringComparer]::OrdinalIgnoreCase)
    foreach ($id in $InstalledIds) { [void]$installed.Add($id) }

    $records = New-Object System.Collections.Generic.List[object]
    foreach ($sys in $Systems) {
        $name = $sys.Name
        $required = @()
        if ($SystemMap.ContainsKey($name)) { $required = @($SystemMap[$name]) }
        $available = @($required | Where-Object { $installed.Contains($_) })
        # A system is only a "gap" if it actually has ROMs and we know what it needs.
        $missing = ($sys.HasRoms -and $required.Count -gt 0 -and $available.Count -eq 0)
        $recommended = if ($required.Count -gt 0) { $required[0] } else { '' }
        $records.Add([ordered]@{
            System      = $name
            HasRoms     = [bool]$sys.HasRoms
            Required    = $required
            Available   = $available
            Missing     = $missing
            Recommended = $recommended
        })
    }
    return $records.ToArray()
}

function Test-EmulatorInstalls {
    <#
    .SYNOPSIS
        Verifies integrity of each installed emulator's executable and flags
        partial installs (known folder present but no valid exe). Returns records.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][object[]] $Emulators,
        [Parameter(Mandatory = $true)][scriptblock] $Logger
    )
    $records = New-Object System.Collections.Generic.List[object]
    foreach ($e in ($Emulators | Where-Object { $_.Installed })) {
        $ok = Test-ExecutableIntegrity -Path $e.ExecutablePath
        if (-not $ok) {
            & $Logger "Emulator '$($e.DisplayName)' executable failed integrity check: $($e.ExecutablePath)" 'WARN'
        }
        $records.Add([ordered]@{ Id = $e.Id; DisplayName = $e.DisplayName; Exe = $e.ExecutablePath; IntegrityOk = $ok })
    }
    return $records.ToArray()
}

Export-ModuleMember -Function Test-ExecutableIntegrity, Get-EmulatorGaps, Test-EmulatorInstalls
