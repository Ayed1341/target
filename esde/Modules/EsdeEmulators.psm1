<#
.SYNOPSIS
    ES-DE-native emulator discovery.
.DESCRIPTION
    Discovers emulators the way ES-DE itself does, with NO dependency on a RetroBat
    folder layout:
      1. Parses ES-DE's es_find_rules.xml (staticpath rules) and resolves the
         real emulator binaries, expanding %ESPATH% / %ROMPATH% / %EMUPATH% / ~.
      2. Scans the ES-DE "Emulators" tree(s) next to the installation.
    Emulators are matched by EXECUTABLE name (retroarch.exe, pcsx2-qt.exe, ...)
    rather than folder name, so ES-DE naming (RetroArch-Win64, PCSX2-Qt, ...) is
    handled correctly. Each match is returned as a descriptor compatible with the
    graphics optimizer.
#>

Set-StrictMode -Version Latest

function Get-EsdeFindRulesPath {
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][System.Collections.Specialized.OrderedDictionary] $Layout)
    $dataParent = Split-Path $Layout.DataDir -Parent
    $cands = @(
        (Join-Path $Layout.CustomSystems 'es_find_rules.xml'),
        (Join-Path $Layout.DataDir 'resources\systems\windows\es_find_rules.xml'),
        (Join-Path $dataParent 'resources\systems\windows\es_find_rules.xml'),
        (Join-Path $dataParent 'ES-DE\resources\systems\windows\es_find_rules.xml')
    )
    foreach ($c in $cands) { if ($c -and (Test-Path -LiteralPath $c)) { return $c } }
    return $null
}

function Expand-EsdePath {
    <#
    .SYNOPSIS
        Expands ES-DE path variables and environment variables in a rule entry.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string] $Entry,
        [Parameter(Mandatory = $true)][string] $EsPath,
        [Parameter(Mandatory = $true)][string] $RomPath
    )
    $p = $Entry
    $p = $p.Replace('%ESPATH%', $EsPath).Replace('%ROMPATH%', $RomPath).Replace('%EMUPATH%', $EsPath)
    if ($p.StartsWith('~')) {
        $home2 = if ($env:USERPROFILE) { $env:USERPROFILE } else { $env:HOME }
        if ($home2) { $p = $home2 + $p.Substring(1) }
    }
    $p = [Environment]::ExpandEnvironmentVariables($p)
    return ($p -replace '/', '\')
}

function Get-EsdeEmulatorsRoots {
    <#
    .SYNOPSIS
        Returns existing candidate "Emulators" roots derived from the ES-DE install
        plus an optional explicit extra root. No RetroBat paths are assumed.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][System.Collections.Specialized.OrderedDictionary] $Layout,
        [string] $ExtraRoot
    )
    $dataParent = Split-Path $Layout.DataDir -Parent
    $roots = New-Object System.Collections.Generic.List[string]
    foreach ($c in @(
        (Join-Path $Layout.DataDir 'Emulators'),
        (Join-Path $dataParent 'Emulators'),
        (Join-Path $dataParent 'emulators'),
        (Join-Path $Layout.DataDir 'emulators')
    )) { if ($c) { $roots.Add($c) } }
    if ($ExtraRoot) {
        $roots.Add($ExtraRoot)
        $roots.Add((Join-Path $ExtraRoot 'emulators'))
        $roots.Add((Join-Path $ExtraRoot 'Emulators'))
    }

    # Derive roots from es_find_rules.xml: any existing staticpath exe whose path
    # contains an 'Emulators' segment yields that segment as a root.
    $frp = Get-EsdeFindRulesPath -Layout $Layout
    if ($frp) {
        $esPath = $dataParent
        try {
            [xml]$xml = Get-Content -LiteralPath $frp -Raw -Encoding UTF8
            foreach ($entry in $xml.SelectNodes("//rule[@type='staticpath']/entry")) {
                $abs = Expand-EsdePath -Entry $entry.InnerText -EsPath $esPath -RomPath $Layout.RomDir
                if (Test-Path -LiteralPath $abs) {
                    $parts = $abs -split '\\'
                    for ($i = $parts.Length - 1; $i -ge 0; $i--) {
                        if ($parts[$i] -ieq 'Emulators') {
                            $roots.Add(($parts[0..$i] -join '\'))
                            break
                        }
                    }
                }
            }
        } catch { }
    }

    return @($roots | Where-Object { $_ -and (Test-Path -LiteralPath $_) } | Select-Object -Unique)
}

function Get-EsdeEmulators {
    <#
    .SYNOPSIS
        Returns emulator descriptors by matching known executables (from the
        definition database) anywhere under the given roots. Folder naming is
        irrelevant; FolderPath is set to the directory containing the executable.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string[]] $Roots,
        [Parameter(Mandatory = $true)][object]   $Definitions
    )

    $results = New-Object System.Collections.Generic.List[object]
    $foundIds = New-Object System.Collections.Generic.HashSet[string] ([StringComparer]::OrdinalIgnoreCase)

    foreach ($def in $Definitions.emulators) {
        if ($foundIds.Contains($def.id)) { continue }
        $hit = $null
        foreach ($root in $Roots) {
            foreach ($exe in $def.executables) {
                $found = Find-FileDepthLimited -Root $root -FileName $exe -MaxDepth 4
                if ($found) { $hit = $found; break }
            }
            if ($hit) { break }
        }
        $descriptor = [ordered]@{
            Id             = $def.id
            DisplayName    = $def.displayName
            Folder         = $def.folder
            FolderPath     = if ($hit) { Split-Path $hit -Parent } else { $null }
            Installed      = [bool]$hit
            ExecutablePath = $hit
            ConfigType     = $def.configType
            ConfigFiles    = @($def.configFiles)
            Supports4K     = [bool]$def.supports4K
            Known          = $true
            Definition     = $def
        }
        $results.Add([pscustomobject]$descriptor)
        if ($hit) { [void]$foundIds.Add($def.id) }
    }

    return $results.ToArray()
}

Export-ModuleMember -Function Get-EsdeFindRulesPath, Expand-EsdePath, Get-EsdeEmulatorsRoots, Get-EsdeEmulators
