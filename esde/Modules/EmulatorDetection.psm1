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
    # UPGRADE (performance): fall back to a DEPTH-LIMITED search instead of a full
    # recursive scan. RetroBat emulators keep their executable at the root or one
    # or two levels down, so capping depth turns a multi-second scan over large
    # installs (100+ emulators) into a near-instant lookup.
    foreach ($exe in $Executables) {
        $found = Find-FileDepthLimited -Root $Folder -FileName $exe -MaxDepth 3
        if ($found) { return $found }
    }
    return $null
}

function Find-FileDepthLimited {
    <#
    .SYNOPSIS
        Breadth-first search for a file name up to a maximum directory depth.
    .OUTPUTS
        Full path of the first match, or $null.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)] [string] $Root,
        [Parameter(Mandatory = $true)] [string] $FileName,
        [int] $MaxDepth = 3
    )
    if (-not (Test-Path -LiteralPath $Root)) { return $null }

    $queue = [System.Collections.Generic.Queue[object]]::new()
    $queue.Enqueue([pscustomobject]@{ Path = $Root; Depth = 0 })
    while ($queue.Count -gt 0) {
        $node = $queue.Dequeue()
        $hit  = Join-Path $node.Path $FileName
        if (Test-Path -LiteralPath $hit -PathType Leaf) { return $hit }
        if ($node.Depth -lt $MaxDepth) {
            foreach ($sub in (Get-ChildItem -LiteralPath $node.Path -Directory -ErrorAction SilentlyContinue)) {
                $queue.Enqueue([pscustomobject]@{ Path = $sub.FullName; Depth = $node.Depth + 1 })
            }
        }
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
            # UPGRADE (performance): cap recursion depth so discovery over very
            # large RetroBat installs stays fast.
            $exe = Get-ChildItem -LiteralPath $_.FullName -Filter '*.exe' -File -Recurse -Depth 2 -ErrorAction SilentlyContinue |
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

Export-ModuleMember -Function Get-EmulatorDefinitions, Find-EmulatorExecutable, Find-FileDepthLimited, Get-InstalledEmulators, Get-MissingRequiredEmulators
