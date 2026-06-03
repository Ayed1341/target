<#
.SYNOPSIS
    Configuration validation and repair module.
.DESCRIPTION
    Validates the RetroBat environment: missing BIOS files (against a known
    requirement table), broken/missing critical paths, malformed emulator
    configuration files. Repairs what is safe to repair (recreating missing
    folders, restoring a config from its most recent backup when corrupted) and
    reports the rest. Never deletes ROMs, saves, BIOS or user configs.
#>

Set-StrictMode -Version Latest

# Minimal, well-known BIOS requirement table (filename -> systems needing it).
# Used to flag missing BIOS; the script never downloads copyrighted BIOS files.
$script:BiosRequirements = @(
    @{ File = 'scph5500.bin'; System = 'PlayStation (PSX/JP)' },
    @{ File = 'scph5501.bin'; System = 'PlayStation (PSX/US)' },
    @{ File = 'scph5502.bin'; System = 'PlayStation (PSX/EU)' },
    @{ File = 'ps2-0200a-20040614.bin'; System = 'PlayStation 2' },
    @{ File = 'dc_boot.bin'; System = 'Dreamcast' },
    @{ File = 'dc_flash.bin'; System = 'Dreamcast' },
    @{ File = 'bios7.bin'; System = 'Nintendo DS' },
    @{ File = 'bios9.bin'; System = 'Nintendo DS' },
    @{ File = 'firmware.bin'; System = 'Nintendo DS' },
    @{ File = 'gba_bios.bin'; System = 'Game Boy Advance' },
    @{ File = 'syscard3.pce'; System = 'PC Engine CD' }
)

function Test-RetroBatPaths {
    <#
    .SYNOPSIS
        Verifies critical RetroBat folders exist; recreates safe-to-create ones.
    .OUTPUTS
        Array of issue hashtables: Type, Item, Severity, Repaired, Detail.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)] [System.Collections.Specialized.OrderedDictionary] $Layout,
        [Parameter(Mandatory = $true)] [scriptblock] $Logger
    )

    $issues = New-Object System.Collections.Generic.List[object]

    # Folders we may safely (re)create if missing - never touches user content.
    $createable = @('Emulators','Bios','Roms','Saves','System','Configs','Backups','Logs',
                    'EmulationStation','EmulationStationData')

    foreach ($key in $createable) {
        if (-not $Layout.Contains($key)) { continue }
        $path = $Layout[$key]
        if (-not (Test-Path -LiteralPath $path)) {
            try {
                New-Item -Path $path -ItemType Directory -Force | Out-Null
                & $Logger "Recreated missing folder: $path" 'WARN'
                $issues.Add(@{ Type='Path'; Item=$path; Severity='Warning'; Repaired=$true; Detail='Folder recreated.' })
            } catch {
                & $Logger "Failed to recreate folder ${path}: $($_.Exception.Message)" 'ERROR'
                $issues.Add(@{ Type='Path'; Item=$path; Severity='Error'; Repaired=$false; Detail=$_.Exception.Message })
            }
        }
    }
    return $issues.ToArray()
}

function Test-BiosFiles {
    <#
    .SYNOPSIS
        Reports which known BIOS files are missing from the bios folder.
        Does NOT download BIOS (copyright); only flags for the user.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)] [string] $BiosDir,
        [Parameter(Mandatory = $true)] [scriptblock] $Logger
    )

    $issues = New-Object System.Collections.Generic.List[object]
    if (-not (Test-Path -LiteralPath $BiosDir)) {
        & $Logger "BIOS directory not found: $BiosDir" 'WARN'
        return $issues.ToArray()
    }

    # Index existing files (recursively) by lowercase name for fast lookup.
    $present = @{}
    Get-ChildItem -LiteralPath $BiosDir -Recurse -File -ErrorAction SilentlyContinue | ForEach-Object {
        $present[$_.Name.ToLower()] = $_.FullName
    }

    foreach ($req in $script:BiosRequirements) {
        if (-not $present.ContainsKey($req.File.ToLower())) {
            & $Logger "Missing BIOS: $($req.File) (needed for $($req.System))" 'WARN'
            $issues.Add(@{ Type='Bios'; Item=$req.File; Severity='Warning'; Repaired=$false; Detail="Required for $($req.System). Provide this file in $BiosDir." })
        }
    }
    if ($issues.Count -eq 0) {
        & $Logger "All tracked BIOS files are present." 'SUCCESS'
    }
    return $issues.ToArray()
}

function Test-EmulatorConfigs {
    <#
    .SYNOPSIS
        Validates installed emulator config files for basic corruption (e.g.
        truncated/empty INI, invalid JSON). Restores from the latest backup when
        a config is corrupt and a backup exists.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)] [object[]] $Emulators,
        [Parameter(Mandatory = $true)] [string]   $BackupRoot,
        [Parameter(Mandatory = $true)] [scriptblock] $Logger
    )

    $issues = New-Object System.Collections.Generic.List[object]

    foreach ($emu in ($Emulators | Where-Object { $_.Installed -and $_.ConfigFiles.Count -gt 0 })) {
        foreach ($rel in $emu.ConfigFiles) {
            $cfg = Join-Path $emu.FolderPath $rel
            if (-not (Test-Path -LiteralPath $cfg)) { continue }   # absent != corrupt

            $corrupt = $false
            $reason  = ''
            try {
                $len = (Get-Item -LiteralPath $cfg).Length
                if ($len -eq 0) { $corrupt = $true; $reason = 'empty file' }
                elseif ($emu.ConfigType -eq 'json') {
                    $null = Get-Content -LiteralPath $cfg -Raw -Encoding UTF8 | ConvertFrom-Json -ErrorAction Stop
                }
            } catch {
                $corrupt = $true
                $reason  = "parse error: $($_.Exception.Message)"
            }

            if ($corrupt) {
                & $Logger "Corrupt config for $($emu.DisplayName): $cfg ($reason)" 'ERROR'
                $restored = Restore-LatestBackup -OriginalPath $cfg -BackupRoot $BackupRoot -Logger $Logger
                $issues.Add(@{
                    Type='Config'; Item=$cfg; Severity='Error'
                    Repaired=$restored; Detail=$reason
                })
            }
        }
    }
    if ($issues.Count -eq 0) {
        & $Logger "No corrupt emulator configuration files detected." 'SUCCESS'
    }
    return $issues.ToArray()
}

function Restore-LatestBackup {
    <#
    .SYNOPSIS
        Restores a file from its most recent timestamped backup, if one exists.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)] [string] $OriginalPath,
        [Parameter(Mandatory = $true)] [string] $BackupRoot,
        [Parameter(Mandatory = $true)] [scriptblock] $Logger
    )

    if (-not (Test-Path -LiteralPath $BackupRoot)) { return $false }
    $leaf    = Split-Path $OriginalPath -Leaf
    $pattern = "$leaf.*.bak"
    $backup  = Get-ChildItem -LiteralPath $BackupRoot -Filter $pattern -File -ErrorAction SilentlyContinue |
               Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if ($backup) {
        try {
            Copy-Item -LiteralPath $backup.FullName -Destination $OriginalPath -Force
            & $Logger "Restored $OriginalPath from backup $($backup.Name)." 'SUCCESS'
            return $true
        } catch {
            & $Logger "Failed to restore from backup: $($_.Exception.Message)" 'ERROR'
        }
    } else {
        & $Logger "No backup available to restore $OriginalPath." 'WARN'
    }
    return $false
}

Export-ModuleMember -Function Test-RetroBatPaths, Test-BiosFiles, Test-EmulatorConfigs, Restore-LatestBackup
