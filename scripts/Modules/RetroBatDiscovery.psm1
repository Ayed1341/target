<#
.SYNOPSIS
    RetroBat installation discovery module.
.DESCRIPTION
    Locates the RetroBat root and maps every relevant sub-tree: EmulationStation,
    emulators, BIOS, ROMs, saves, configuration and controller-profile folders.
    Also extracts the installed RetroBat version. Designed to run from the
    RetroBat root but capable of probing common install locations as a fallback.
#>

Set-StrictMode -Version Latest

function Find-RetroBatRoot {
    <#
    .SYNOPSIS
        Resolves the RetroBat root directory.
    .DESCRIPTION
        Verifies the supplied StartPath (and its parents) look like a RetroBat
        install; if not, probes well-known install locations.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string] $StartPath
    )

    $candidates = New-Object System.Collections.Generic.List[string]

    # Walk up from the start path: the script may live in RetroBat\ directly.
    $cursor = (Resolve-Path -LiteralPath $StartPath).Path
    for ($i = 0; $i -lt 4 -and $cursor; $i++) {
        $candidates.Add($cursor)
        $parent = Split-Path -Path $cursor -Parent
        if (-not $parent -or $parent -eq $cursor) { break }
        $cursor = $parent
    }

    # Common install locations as a fallback. Built by string composition (not
    # Join-Path) so a drive-qualified root never triggers provider resolution,
    # and any unset base is skipped (safe to exercise on non-Windows hosts too).
    $fallbackBases = @('C:', 'D:', $env:SystemDrive, ${env:ProgramFiles}, $env:USERPROFILE)
    foreach ($base in $fallbackBases) {
        if ([string]::IsNullOrWhiteSpace($base)) { continue }
        $candidates.Add(($base.TrimEnd('\') + '\RetroBat'))
    }

    foreach ($c in ($candidates | Select-Object -Unique)) {
        if (Test-RetroBatRoot -Path $c) { return (Resolve-Path -LiteralPath $c).Path }
    }

    return $null
}

function Test-RetroBatRoot {
    <#
    .SYNOPSIS
        Heuristically validates that a path is a RetroBat root.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][string] $Path)

    if (-not (Test-Path -LiteralPath $Path)) { return $false }

    $markers = @(
        'emulationstation',
        'emulators',
        'roms',
        'bios'
    )
    $hits = 0
    foreach ($m in $markers) {
        if (Test-Path -LiteralPath (Join-Path $Path $m)) { $hits++ }
    }
    # Strong signals: the launcher or retrobat.ini.
    if (Test-Path -LiteralPath (Join-Path $Path 'retrobat.ini')) { $hits += 2 }
    if (Test-Path -LiteralPath (Join-Path $Path 'RetroBat.exe')) { $hits += 2 }

    return ($hits -ge 3)
}

function Get-RetroBatVersion {
    <#
    .SYNOPSIS
        Reads the installed RetroBat version from known locations.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][string] $Root)

    $versionFiles = @(
        (Join-Path $Root 'system\version.info'),
        (Join-Path $Root 'version.info'),
        (Join-Path $Root 'emulationstation\version.info')
    )
    foreach ($vf in $versionFiles) {
        if (Test-Path -LiteralPath $vf) {
            $raw = (Get-Content -LiteralPath $vf -Raw -ErrorAction SilentlyContinue)
            if ($raw) { return $raw.Trim() }
        }
    }

    # retrobat.ini may carry a version under [RetroBat].
    $ini = Join-Path $Root 'retrobat.ini'
    if (Test-Path -LiteralPath $ini) {
        $match = Select-String -LiteralPath $ini -Pattern '^\s*version\s*=\s*(.+)$' -ErrorAction SilentlyContinue |
                 Select-Object -First 1
        if ($match) { return $match.Matches[0].Groups[1].Value.Trim() }
    }

    return 'Unknown'
}

function Get-RetroBatLayout {
    <#
    .SYNOPSIS
        Builds a hashtable of all important RetroBat paths, marking which exist.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][string] $Root)

    $esRoot   = Join-Path $Root 'emulationstation'
    $esData   = Join-Path $esRoot '.emulationstation'

    $layout = [ordered]@{
        Root                 = $Root
        Version              = Get-RetroBatVersion -Root $Root
        EmulationStation     = $esRoot
        EmulationStationData = $esData
        EsSettings           = Join-Path $esData 'es_settings.cfg'
        EsInput              = Join-Path $esData 'es_input.cfg'
        EsSystems            = Join-Path $esData 'es_systems.cfg'
        Emulators            = Join-Path $Root 'emulators'
        Bios                 = Join-Path $Root 'bios'
        Roms                 = Join-Path $Root 'roms'
        Saves                = Join-Path $Root 'saves'
        System               = Join-Path $Root 'system'
        Configs              = Join-Path $Root 'system\configs'
        Decorations          = Join-Path $Root 'decorations'
        RetroBatIni          = Join-Path $Root 'retrobat.ini'
        Backups              = Join-Path $Root 'Backups'
        Logs                 = Join-Path $Root 'Logs'
    }

    $layout.Exists = [ordered]@{}
    foreach ($key in @('EmulationStation','EmulationStationData','EsSettings','EsInput',
                       'EsSystems','Emulators','Bios','Roms','Saves','System','Configs',
                       'RetroBatIni')) {
        $layout.Exists[$key] = Test-Path -LiteralPath $layout[$key]
    }

    return $layout
}

function Get-ControllerProfilePaths {
    <#
    .SYNOPSIS
        Returns existing controller-profile / autoconfig folders within RetroBat.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][System.Collections.Specialized.OrderedDictionary] $Layout)

    $paths = [ordered]@{
        EsInput            = $Layout.EsInput
        RetroArchAutoconf  = Join-Path $Layout.Emulators 'retroarch\autoconfig'
        RetroArchRemaps    = Join-Path $Layout.Emulators 'retroarch\config\remaps'
        SdlGameDb          = Join-Path $Layout.System 'tools\gamecontrollerdb.txt'
    }
    $paths.Exists = [ordered]@{}
    foreach ($k in @('EsInput','RetroArchAutoconf','RetroArchRemaps','SdlGameDb')) {
        $paths.Exists[$k] = Test-Path -LiteralPath $paths[$k]
    }
    return $paths
}

Export-ModuleMember -Function Find-RetroBatRoot, Test-RetroBatRoot, Get-RetroBatVersion, Get-RetroBatLayout, Get-ControllerProfilePaths
