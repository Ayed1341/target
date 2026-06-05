<#
.SYNOPSIS
    ES-DE (EmulationStation Desktop Edition) discovery engine.
.DESCRIPTION
    Locates an ES-DE installation and its user-data tree (settings, gamelists,
    downloaded_media, themes, custom_systems, collections, scraper cache) for
    both portable and installed configurations, and resolves the ROM directory
    from es_settings.xml.
#>

Set-StrictMode -Version Latest

function Find-EsdeDataDir {
    <#
    .SYNOPSIS
        Resolves the ES-DE application-data directory (the "ES-DE" folder that
        holds settings/, gamelists/, downloaded_media/, etc.).
    .PARAMETER StartPath
        A hint location (e.g. the folder the launcher runs from) checked first
        for a portable layout.
    #>
    [CmdletBinding()]
    param([string] $StartPath)

    $candidates = New-Object System.Collections.Generic.List[string]

    if ($StartPath) {
        # Portable: an "ES-DE" folder next to the launcher, or the launcher IS in it.
        $cursor = (Resolve-Path -LiteralPath $StartPath -ErrorAction SilentlyContinue).Path
        if ($cursor) {
            for ($i = 0; $i -lt 4 -and $cursor; $i++) {
                $candidates.Add((Join-Path $cursor 'ES-DE'))
                $candidates.Add($cursor)
                $parent = Split-Path -Path $cursor -Parent
                if (-not $parent -or $parent -eq $cursor) { break }
                $cursor = $parent
            }
        }
    }

    # Standard installed locations (ES-DE 2.x/3.x).
    foreach ($base in @($env:USERPROFILE, $env:HOME, $env:APPDATA, $env:LOCALAPPDATA)) {
        if ([string]::IsNullOrWhiteSpace($base)) { continue }
        $candidates.Add((Join-Path $base 'ES-DE'))
        $candidates.Add((Join-Path $base '.emulationstation'))
    }
    foreach ($drive in @('C:', 'D:', 'E:')) {
        $candidates.Add($drive + '\ES-DE')
        $candidates.Add($drive + '\RetroBat\ES-DE')
    }

    foreach ($c in ($candidates | Select-Object -Unique)) {
        if (Test-EsdeDataDir -Path $c) { return (Resolve-Path -LiteralPath $c).Path }
    }
    return $null
}

function Test-EsdeDataDir {
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][string] $Path)
    if (-not (Test-Path -LiteralPath $Path)) { return $false }
    $markers = @('settings','gamelists','downloaded_media','themes','custom_systems','collections')
    $hits = 0
    foreach ($m in $markers) { if (Test-Path -LiteralPath (Join-Path $Path $m)) { $hits++ } }
    if (Test-Path -LiteralPath (Join-Path $Path 'settings\es_settings.xml')) { $hits += 2 }
    return ($hits -ge 2)
}

function Get-EsdeLayout {
    <#
    .SYNOPSIS
        Builds a hashtable of all important ES-DE paths and resolves the ROM dir.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][string] $DataDir)

    $settingsFile = Join-Path $DataDir 'settings\es_settings.xml'
    $layout = [ordered]@{
        DataDir          = $DataDir
        Settings         = Join-Path $DataDir 'settings'
        SettingsFile     = $settingsFile
        InputFile        = Join-Path $DataDir 'settings\es_input.xml'
        Gamelists        = Join-Path $DataDir 'gamelists'
        DownloadedMedia  = Join-Path $DataDir 'downloaded_media'
        Themes           = Join-Path $DataDir 'themes'
        CustomSystems    = Join-Path $DataDir 'custom_systems'
        Collections      = Join-Path $DataDir 'collections'
        ScraperCache     = Join-Path $DataDir 'cache'
        Logs             = Join-Path $DataDir 'logs'
        Version          = Get-EsdeVersion -DataDir $DataDir
    }
    $layout.RomDir   = Get-EsdeRomDirectory -SettingsFile $settingsFile
    $layout.MediaDir = Get-EsdeMediaDirectory -SettingsFile $settingsFile -DataDir $DataDir

    $layout.Exists = [ordered]@{}
    foreach ($k in @('Settings','SettingsFile','InputFile','Gamelists','DownloadedMedia',
                     'Themes','CustomSystems','Collections','ScraperCache')) {
        $layout.Exists[$k] = Test-Path -LiteralPath $layout[$k]
    }
    return $layout
}

function Get-EsdeVersion {
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][string] $DataDir)
    $vf = Join-Path $DataDir 'LATEST_VERSION.txt'
    if (Test-Path -LiteralPath $vf) {
        $raw = Get-Content -LiteralPath $vf -Raw -ErrorAction SilentlyContinue
        if ($raw) { return $raw.Trim() }
    }
    return 'Unknown'
}

function Get-EsdeSetting {
    <#
    .SYNOPSIS
        Reads a single string/value setting out of es_settings.xml.
        ES-DE stores settings as <string name="X" value="Y" /> elements.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string] $SettingsFile,
        [Parameter(Mandatory = $true)][string] $Name
    )
    if (-not (Test-Path -LiteralPath $SettingsFile)) { return $null }
    try {
        # XmlDocument.Load reads the file with correct encoding/BOM detection;
        # [xml](Get-Content -Raw) fails on a UTF-8 BOM ("Data at the root level
        # is invalid"), which would make us silently fall back to default paths.
        $xml = New-Object System.Xml.XmlDocument
        $xml.Load($SettingsFile)
        $node = $xml.SelectSingleNode("//*[@name='$Name']")
        if ($node -and $node.Attributes['value']) { return $node.Attributes['value'].Value }
    } catch { }
    return $null
}

function Get-EsdeRomDirectory {
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][string] $SettingsFile)
    $rd = Get-EsdeSetting -SettingsFile $SettingsFile -Name 'ROMDirectory'
    if ($rd) {
        $rd = $rd -replace '%ESPATH%', (Split-Path (Split-Path $SettingsFile -Parent) -Parent)
        $rd = [Environment]::ExpandEnvironmentVariables($rd)
        if ($rd) { return $rd }
    }
    foreach ($p in @((Join-Path $env:USERPROFILE 'ROMs'), 'C:\RetroBat\roms', 'D:\RetroBat\roms')) {
        if ($p -and (Test-Path -LiteralPath $p)) { return $p }
    }
    return (Join-Path $env:USERPROFILE 'ROMs')
}

function Get-EsdeMediaDirectory {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string] $SettingsFile,
        [Parameter(Mandatory = $true)][string] $DataDir
    )
    $md = Get-EsdeSetting -SettingsFile $SettingsFile -Name 'MediaDirectory'
    if ($md) {
        $md = [Environment]::ExpandEnvironmentVariables($md)
        if ($md) { return $md }
    }
    return (Join-Path $DataDir 'downloaded_media')
}

function Get-EsdeSystems {
    <#
    .SYNOPSIS
        Enumerates ES-DE systems by inspecting the ROM directory, gamelists and
        downloaded_media folders, returning a descriptor per system.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][System.Collections.Specialized.OrderedDictionary] $Layout)

    $systems = @{}

    function Add-Sys($name) {
        if (-not $systems.ContainsKey($name)) {
            $systems[$name] = [ordered]@{
                Name        = $name
                RomPath     = Join-Path $Layout.RomDir $name
                GamelistDir = Join-Path $Layout.Gamelists $name
                Gamelist    = Join-Path (Join-Path $Layout.Gamelists $name) 'gamelist.xml'
                MediaDir    = Join-Path $Layout.MediaDir $name
                HasRoms     = $false
                HasGamelist = $false
                HasMedia    = $false
            }
        }
        return $systems[$name]
    }

    if (Test-Path -LiteralPath $Layout.RomDir) {
        Get-ChildItem -LiteralPath $Layout.RomDir -Directory -ErrorAction SilentlyContinue | ForEach-Object {
            if ($_.Name -in @('media','downloaded_media')) { return }
            (Add-Sys $_.Name).HasRoms = $true
        }
    }
    if (Test-Path -LiteralPath $Layout.Gamelists) {
        Get-ChildItem -LiteralPath $Layout.Gamelists -Directory -ErrorAction SilentlyContinue | ForEach-Object {
            $s = Add-Sys $_.Name
            $s.HasGamelist = Test-Path -LiteralPath $s.Gamelist
        }
    }
    if (Test-Path -LiteralPath $Layout.MediaDir) {
        Get-ChildItem -LiteralPath $Layout.MediaDir -Directory -ErrorAction SilentlyContinue | ForEach-Object {
            (Add-Sys $_.Name).HasMedia = $true
        }
    }

    return @($systems.Values | Sort-Object Name)
}

Export-ModuleMember -Function Find-EsdeDataDir, Test-EsdeDataDir, Get-EsdeLayout, Get-EsdeVersion, Get-EsdeSetting, Get-EsdeRomDirectory, Get-EsdeMediaDirectory, Get-EsdeSystems
