<#
.SYNOPSIS
    Emulator auto-detection module.
.DESCRIPTION
    Enumerates every emulator present under the RetroBat 'emulators' tree. It uses
    the data-driven definitions in config\emulators.json for known emulators AND
    dynamically discovers any other emulator folder (so future emulators added to
    RetroBat are reported automatically).
#>

Set-StrictMode -Version Latest

function Get-EmulatorDefinitions {
    <#
    .SYNOPSIS
        Loads and returns the emulator definition objects from emulators.json.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][string] $DefinitionPath)

    if (-not (Test-Path -LiteralPath $DefinitionPath)) {
        throw "Emulator definition file not found: $DefinitionPath"
    }
    $json = Get-Content -LiteralPath $DefinitionPath -Raw -Encoding UTF8 | ConvertFrom-Json
    return $json
}

function Find-EmulatorExecutable {
    <#
    .SYNOPSIS
        Searches a folder (recursively, shallow-first) for any of the candidate
        executable names and returns the first match.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)] [string]   $Folder,
        [Parameter(Mandatory = $true)] [string[]] $Executables
    )

    if (-not (Test-Path -LiteralPath $Folder)) { return $null }

    foreach ($exe in $Executables) {
        # Direct hit at folder root is the common case.
        $direct = Join-Path $Folder $exe
        if (Test-Path -LiteralPath $direct) { return $direct }
    }
    # Fall back to a recursive search (handles versioned sub-folders).
    foreach ($exe in $Executables) {
        $found = Get-ChildItem -LiteralPath $Folder -Filter $exe -Recurse -File -ErrorAction SilentlyContinue |
                 Select-Object -First 1
        if ($found) { return $found.FullName }
    }
    return $null
}

function Get-InstalledEmulators {
    <#
    .SYNOPSIS
        Returns an array of emulator descriptor hashtables for everything found.
    .DESCRIPTION
        Combines known definitions with dynamic folder discovery. Each descriptor:
          Id, DisplayName, Folder, FolderPath, Installed, ExecutablePath,
          ConfigType, ConfigFiles, Supports4K, Known, Definition
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)] [string] $EmulatorsRoot,
        [Parameter(Mandatory = $true)] [object] $Definitions
    )

    $results       = New-Object System.Collections.Generic.List[object]
    $accountedDirs = New-Object System.Collections.Generic.HashSet[string] ([StringComparer]::OrdinalIgnoreCase)

    # ---- Known emulators from the definition database ----
    foreach ($def in $Definitions.emulators) {
        $folderPath = Join-Path $EmulatorsRoot $def.folder
        $exe        = Find-EmulatorExecutable -Folder $folderPath -Executables $def.executables
        $descriptor = [ordered]@{
            Id             = $def.id
            DisplayName    = $def.displayName
            Folder         = $def.folder
            FolderPath     = $folderPath
            Installed      = [bool]$exe
            ExecutablePath = $exe
            ConfigType     = $def.configType
            ConfigFiles    = @($def.configFiles)
            Supports4K     = [bool]$def.supports4K
            Known          = $true
            Definition     = $def
        }
        $results.Add([pscustomobject]$descriptor)
        [void]$accountedDirs.Add($def.folder)
    }

    # ---- Dynamic discovery of unknown emulator folders ----
    if (Test-Path -LiteralPath $EmulatorsRoot) {
        Get-ChildItem -LiteralPath $EmulatorsRoot -Directory -ErrorAction SilentlyContinue | ForEach-Object {
            $dirName = $_.Name
            if ($accountedDirs.Contains($dirName)) { return }

            # Treat a folder containing at least one .exe as a candidate emulator.
            $exe = Get-ChildItem -LiteralPath $_.FullName -Filter '*.exe' -Recurse -File -ErrorAction SilentlyContinue |
                   Where-Object { $_.Name -notmatch '(?i)(unins|setup|vc_redist|crash|update|helper)\b' } |
                   Sort-Object Length -Descending |
                   Select-Object -First 1

            $descriptor = [ordered]@{
                Id             = $dirName.ToLower()
                DisplayName    = "$dirName (auto-discovered)"
                Folder         = $dirName
                FolderPath     = $_.FullName
                Installed      = [bool]$exe
                ExecutablePath = if ($exe) { $exe.FullName } else { $null }
                ConfigType     = 'unknown'
                ConfigFiles    = @()
                Supports4K     = $false
                Known          = $false
                Definition     = $null
            }
            $results.Add([pscustomobject]$descriptor)
        }
    }

    return $results.ToArray()
}

function Get-MissingRequiredEmulators {
    <#
    .SYNOPSIS
        Returns the known emulators that are not installed but have a usable
        download definition (so they can be auto-installed).
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)] [object[]] $Emulators
    )

    return @($Emulators | Where-Object {
        $_.Known -and
        -not $_.Installed -and
        $_.Definition -and
        $_.Definition.download -and
        $_.Definition.download.type -ne 'none'
    })
}

Export-ModuleMember -Function Get-EmulatorDefinitions, Find-EmulatorExecutable, Get-InstalledEmulators, Get-MissingRequiredEmulators
