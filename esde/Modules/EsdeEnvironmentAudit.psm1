<#
.SYNOPSIS
    ES-DE environment audit: custom es_systems.xml, themes, collections, alternative
    emulator audit, safe es_settings.xml optimization, language, suite version,
    connectivity, empty-system advisory, custom-systems suggestions, controller
    config verification and a ROM hash manifest.
#>

Set-StrictMode -Version Latest

$script:SuiteVersion = '2.0'

function Get-SuiteVersion { return @{ Version = $script:SuiteVersion; Built = (Get-Date -Format 'yyyy-MM-dd') } }

function Test-EsSystemsXml {
    <#
    .SYNOPSIS
        Validates custom_systems/es_systems.xml is well-formed and counts systems.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][System.Collections.Specialized.OrderedDictionary] $Layout)
    $path = Join-Path $Layout.CustomSystems 'es_systems.xml'
    if (-not (Test-Path -LiteralPath $path)) { return @{ Present = $false; Valid = $true; Count = 0; Path = $path } }
    try {
        [xml]$xml = Get-Content -LiteralPath $path -Raw -Encoding UTF8
        $count = @($xml.SelectNodes('//system')).Count
        return @{ Present = $true; Valid = $true; Count = $count; Path = $path }
    } catch {
        return @{ Present = $true; Valid = $false; Count = 0; Path = $path; Error = $_.Exception.Message }
    }
}

function Get-EsdeThemes {
    <#
    .SYNOPSIS
        Lists installed themes and the active theme (from es_settings 'ThemeSet').
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][System.Collections.Specialized.OrderedDictionary] $Layout)
    $themes = @()
    if (Test-Path -LiteralPath $Layout.Themes) {
        $themes = @(Get-ChildItem -LiteralPath $Layout.Themes -Directory -ErrorAction SilentlyContinue | ForEach-Object { $_.Name })
    }
    $active = Get-EsdeSetting -SettingsFile $Layout.SettingsFile -Name 'ThemeSet'
    $activePresent = ($active -and ($themes -contains $active))
    return @{ Installed = $themes; Active = $active; ActivePresent = $activePresent }
}

function Test-Collections {
    <#
    .SYNOPSIS
        Validates custom collection files (collections/custom-*.cfg); each line is a
        ROM path. Reports broken (non-existent) references per collection.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][System.Collections.Specialized.OrderedDictionary] $Layout)
    $records = New-Object System.Collections.Generic.List[object]
    if (-not (Test-Path -LiteralPath $Layout.Collections)) { return $records.ToArray() }
    Get-ChildItem -LiteralPath $Layout.Collections -Filter 'custom-*.cfg' -File -ErrorAction SilentlyContinue | ForEach-Object {
        $total = 0; $broken = 0
        foreach ($line in (Get-Content -LiteralPath $_.FullName -Encoding UTF8 -ErrorAction SilentlyContinue)) {
            $p = $line.Trim()
            if (-not $p) { continue }
            $total++
            $expanded = $p -replace '%ROMPATH%', $Layout.RomDir
            $expanded = [Environment]::ExpandEnvironmentVariables($expanded) -replace '/', '\'
            if (-not (Test-Path -LiteralPath $expanded)) { $broken++ }
        }
        $records.Add(@{ Collection = $_.BaseName; Entries = $total; Broken = $broken })
    }
    return $records.ToArray()
}

function Get-AltEmulatorAudit {
    <#
    .SYNOPSIS
        Reads each gamelist's <alternativeEmulator><label> and flags labels whose
        emulator does not appear to be installed (by display-name match).
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][object[]] $Systems,
        [string[]] $InstalledDisplayNames = @()
    )
    $records = New-Object System.Collections.Generic.List[object]
    foreach ($sys in $Systems) {
        if (-not (Test-Path -LiteralPath $sys.Gamelist)) { continue }
        $raw = Get-Content -LiteralPath $sys.Gamelist -Raw -Encoding UTF8 -ErrorAction SilentlyContinue
        if (-not $raw) { continue }
        $m = [Regex]::Match($raw, '<alternativeEmulator>\s*<label>([^<]+)</label>')
        if (-not $m.Success) { continue }
        $label = $m.Groups[1].Value.Trim()
        $core  = ($label -replace '\(.*\)', '').Trim()
        $installed = $false
        foreach ($dn in $InstalledDisplayNames) {
            if ($dn -and ($dn -match [Regex]::Escape($core) -or $core -match [Regex]::Escape(($dn -replace '\s*\(.*\)','')))) { $installed = $true; break }
        }
        $records.Add(@{ System = $sys.Name; Label = $label; Installed = $installed })
    }
    return $records.ToArray()
}

function Set-EsdeSettingValue {
    <#
    .SYNOPSIS
        Sets/creates a typed setting (<int>/<bool>/<string>) in es_settings.xml.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string] $SettingsFile,
        [Parameter(Mandatory = $true)][ValidateSet('int','bool','string')][string] $Type,
        [Parameter(Mandatory = $true)][string] $Name,
        [Parameter(Mandatory = $true)][string] $Value
    )
    if (-not (Test-Path -LiteralPath $SettingsFile)) {
        $dir = Split-Path $SettingsFile -Parent
        if ($dir -and -not (Test-Path -LiteralPath $dir)) { New-Item -Path $dir -ItemType Directory -Force | Out-Null }
        [System.IO.File]::WriteAllText($SettingsFile, "<?xml version=`"1.0`"?>`r`n<settings />", (New-Object System.Text.UTF8Encoding($false)))
    }
    [xml]$xml = Get-Content -LiteralPath $SettingsFile -Raw -Encoding UTF8
    if (-not $xml.DocumentElement) {
        $root = $xml.CreateElement('settings'); $xml.AppendChild($root) | Out-Null
    }
    $node = $xml.SelectSingleNode("//$Type[@name='$Name']")
    if (-not $node) {
        $node = $xml.CreateElement($Type)
        $node.SetAttribute('name', $Name)
        $xml.DocumentElement.AppendChild($node) | Out-Null
    }
    $node.SetAttribute('value', $Value)
    $xml.Save($SettingsFile)
}

function Optimize-EsdeSettings {
    <#
    .SYNOPSIS
        Applies a small set of safe ES-DE settings tuned to the hardware (after
        backup): VRAM cache cap and video audio. Never changes paths.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string] $SettingsFile,
        [Parameter(Mandatory = $true)][System.Collections.Specialized.OrderedDictionary] $Hardware,
        [Parameter(Mandatory = $true)][string] $BackupRoot,
        [Parameter(Mandatory = $true)][scriptblock] $Logger,
        [switch] $DryRun
    )
    if ($DryRun) { & $Logger "[DRY-RUN] Would tune es_settings.xml (MaxVRAM, VideoAudio)." 'INFO'; return $false }
    Backup-File -Path $SettingsFile -BackupRoot $BackupRoot | Out-Null
    # Cap the media VRAM cache sensibly: a quarter of GPU VRAM, clamped 256..1024 MB.
    $vram = 512
    if ($Hardware.Contains('GpuVramMB') -and $Hardware.GpuVramMB -gt 0) {
        $vram = [int]([math]::Min(1024, [math]::Max(256, [math]::Floor($Hardware.GpuVramMB / 4))))
    }
    Set-EsdeSettingValue -SettingsFile $SettingsFile -Type 'int'  -Name 'MaxVRAM'    -Value "$vram"
    Set-EsdeSettingValue -SettingsFile $SettingsFile -Type 'bool' -Name 'VideoAudio' -Value 'true'
    & $Logger "Tuned es_settings.xml: MaxVRAM=$vram MB, VideoAudio=true." 'SUCCESS'
    return $true
}

function Get-EsdeLanguage {
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][string] $SettingsFile)
    $lang = Get-EsdeSetting -SettingsFile $SettingsFile -Name 'ApplicationLanguage'
    if (-not $lang) { $lang = 'automatic' }
    return $lang
}

function Test-Online {
    [CmdletBinding()] param([int] $TimeoutMs = 2500)
    # NB: do not use $host (reserved automatic variable).
    foreach ($endpoint in @('api.screenscraper.fr','github.com','1.1.1.1')) {
        try {
            $c = New-Object System.Net.Sockets.TcpClient
            $iar = $c.BeginConnect($endpoint, 443, $null, $null)
            $ok = $iar.AsyncWaitHandle.WaitOne($TimeoutMs)
            if ($ok -and $c.Connected) { $c.EndConnect($iar); $c.Close(); return $true }
            $c.Close()
        } catch { }
    }
    return $false
}

function Get-EmptySystemsAdvisory {
    <#
    .SYNOPSIS
        Returns systems that have neither ROMs nor media (candidates for removal).
        Advisory only - nothing is deleted.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][object[]] $Systems)
    return @($Systems | Where-Object { -not $_.HasRoms -and -not $_.HasMedia } | ForEach-Object { $_.Name })
}

function Test-ControllerConfigApplied {
    <#
    .SYNOPSIS
        Verifies controller config artifacts were actually written (non-empty).
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][System.Collections.Specialized.OrderedDictionary] $Layout)
    $esInput = (Test-Path -LiteralPath $Layout.InputFile) -and ((Get-Item -LiteralPath $Layout.InputFile -ErrorAction SilentlyContinue).Length -gt 0)
    $db = Join-Path $Layout.DataDir 'gamecontrollerdb.txt'
    $sdlDb = (Test-Path -LiteralPath $db) -and ((Get-Item -LiteralPath $db -ErrorAction SilentlyContinue).Length -gt 0)
    return @{ EsInput = [bool]$esInput; GameControllerDb = [bool]$sdlDb }
}

function Export-RomHashManifest {
    <#
    .SYNOPSIS
        Writes a CRC32 manifest of ROMs (skipping files above MaxSizeMB) for future
        scraping / verification. Returns count hashed.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string] $SystemName,
        [Parameter(Mandatory = $true)][string] $SystemRomDir,
        [Parameter(Mandatory = $true)][string] $OutFile,
        [int] $MaxSizeMB = 256
    )
    if (-not (Test-Path -LiteralPath $SystemRomDir)) { return 0 }
    $limit = $MaxSizeMB * 1MB
    $entries = New-Object System.Collections.Generic.List[object]
    Get-ChildItem -LiteralPath $SystemRomDir -File -ErrorAction SilentlyContinue | ForEach-Object {
        if ($_.Extension.ToLower() -in @('.txt','.xml','.dat','.jpg','.png')) { return }
        if ($_.Length -gt $limit) { return }
        $crc = Get-FileCrc32 -Path $_.FullName
        if ($crc) { $entries.Add(@{ file = $_.Name; size = $_.Length; crc32 = $crc }) }
    }
    if ($entries.Count -gt 0) {
        $dir = Split-Path $OutFile -Parent
        if ($dir -and -not (Test-Path -LiteralPath $dir)) { New-Item -Path $dir -ItemType Directory -Force | Out-Null }
        @{ system = $SystemName; generated = (Get-Date -Format o); roms = $entries.ToArray() } | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $OutFile -Encoding UTF8
    }
    return $entries.Count
}

Export-ModuleMember -Function Get-SuiteVersion, Test-EsSystemsXml, Get-EsdeThemes, Test-Collections, `
    Get-AltEmulatorAudit, Set-EsdeSettingValue, Optimize-EsdeSettings, Get-EsdeLanguage, Test-Online, `
    Get-EmptySystemsAdvisory, Test-ControllerConfigApplied, Export-RomHashManifest
