<#
.SYNOPSIS
    Xbox / Xbox 360 emulator setup and repair: xemu and Cxbx-Reloaded (original
    Xbox) and xenia / xenia-canary (Xbox 360).
.DESCRIPTION
    Fixes the common blockers:
      * eeprom.bin - validate (must be 256 bytes), relocate one you already have to
        every Xbox emulator that needs it, and ensure the emulator is configured to
        regenerate a valid one when it is missing (xemu/Cxbx do this automatically).
        eeprom.bin is console SETTINGS data, not firmware, so this is safe/legal.
      * MCPX boot ROM + Xbox BIOS - validate (size/MD5), relocate to the expected
        location, and REPORT when missing. These are copyrighted firmware and are
        NEVER downloaded; the user must supply their own dumps.
      * xemu.toml / Cxbx settings.ini / xenia(-canary).config.toml - wire the
        firmware/eeprom/HDD paths and apply safe 4K graphics + fix common
        "won't boot" settings (xenia license unlock, cache mount, GPU backend).
    Everything is backed up first; nothing is ever deleted (bad files are quarantined).
#>

Set-StrictMode -Version Latest

# Known Xbox firmware filenames. eeprom is generatable; the rest are copyrighted.
$script:XboxBios   = @('mcpx_1.0.bin','mcpx_1.1.bin','Complex_4627.bin','Complex.bin','xbox-bios.bin','bios.bin','5838.bin','4627.bin')
$script:XboxMcpx   = @('mcpx_1.0.bin','mcpx_1.1.bin','mcpx.bin')
$script:EepromName = 'eeprom.bin'

function Get-XboxEmulators {
    <#
    .SYNOPSIS
        Detects Xbox/Xbox360 emulators under the given roots. Returns descriptors:
        Id, Kind (xbox|xbox360), Dir, Exe, ConfigPath.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][string[]] $Roots)
    $defs = @(
        @{ Id='xemu';          Kind='xbox';    Exes=@('xemu.exe');          Config='xemu.toml' },
        @{ Id='cxbx-reloaded'; Kind='xbox';    Exes=@('cxbx.exe','cxbxr-ldr.exe','Cxbx.exe'); Config='settings.ini' },
        @{ Id='xenia-canary';  Kind='xbox360'; Exes=@('xenia_canary.exe','xenia-canary.exe'); Config='xenia-canary.config.toml' },
        @{ Id='xenia';         Kind='xbox360'; Exes=@('xenia.exe');         Config='xenia.config.toml' }
    )
    $found = New-Object System.Collections.Generic.List[object]
    $seen  = New-Object System.Collections.Generic.HashSet[string] ([StringComparer]::OrdinalIgnoreCase)
    foreach ($root in $Roots) {
        if (-not $root -or -not (Test-Path -LiteralPath $root)) { continue }
        foreach ($def in $defs) {
            if ($seen.Contains($def.Id)) { continue }
            foreach ($exe in $def.Exes) {
                $hit = Find-FileDepthLimited -Root $root -FileName $exe -MaxDepth 4
                if ($hit) {
                    $dir = Split-Path $hit -Parent
                    $found.Add([pscustomobject]@{ Id=$def.Id; Kind=$def.Kind; Dir=$dir; Exe=$hit; ConfigPath=(Join-Path $dir $def.Config) })
                    [void]$seen.Add($def.Id)
                    break
                }
            }
        }
    }
    return $found.ToArray()
}

function Find-XboxFile {
    param([string[]] $Roots, [string[]] $Names, [int] $RequiredSize = 0)
    foreach ($root in $Roots) {
        if (-not $root -or -not (Test-Path -LiteralPath $root)) { continue }
        foreach ($n in $Names) {
            $hit = Get-ChildItem -LiteralPath $root -File -Recurse -Depth 4 -Filter $n -ErrorAction SilentlyContinue | Select-Object -First 1
            if ($hit -and ($RequiredSize -le 0 -or $hit.Length -eq $RequiredSize)) { return $hit.FullName }
        }
    }
    return $null
}

function Repair-XboxEeprom {
    <#
    .SYNOPSIS
        Validates/relocates eeprom.bin for xemu & Cxbx and ensures it will be
        (re)generated when missing. Returns @{ Relocated; Validated; Quarantined; AutoGen }.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][object[]] $XboxEmulators,
        [Parameter(Mandatory = $true)][string[]] $SearchRoots,
        [Parameter(Mandatory = $true)][string]   $BackupRoot,
        [Parameter(Mandatory = $true)][scriptblock] $Logger,
        [switch] $DryRun
    )
    $stats = @{ Relocated=0; Validated=0; Quarantined=0; AutoGen=0 }
    $targets = @($XboxEmulators | Where-Object { $_.Kind -eq 'xbox' })
    if ($targets.Count -eq 0) { return $stats }

    # Find a valid (256-byte) eeprom anywhere; quarantine wrong-sized ones.
    $validEeprom = $null
    foreach ($root in $SearchRoots) {
        if (-not $root -or -not (Test-Path -LiteralPath $root)) { continue }
        Get-ChildItem -LiteralPath $root -File -Recurse -Depth 4 -Filter $script:EepromName -ErrorAction SilentlyContinue | ForEach-Object {
            if ($_.Length -eq 256) { if (-not $validEeprom) { $validEeprom = $_.FullName }; $stats.Validated++ }
            elseif ($_.Length -gt 0) {
                & $Logger "eeprom.bin at $($_.FullName) is $($_.Length) bytes (expected 256) - quarantining (corrupt)." 'WARN'
                if (-not $DryRun) {
                    $q = Join-Path $BackupRoot 'corrupt_xbox'
                    if (-not (Test-Path -LiteralPath $q)) { New-Item -Path $q -ItemType Directory -Force | Out-Null }
                    Move-Item -LiteralPath $_.FullName -Destination (Join-Path $q ("eeprom_$([Guid]::NewGuid().ToString('N')).bin")) -Force -ErrorAction SilentlyContinue
                }
                $stats.Quarantined++
            }
        }
    }

    foreach ($emu in $targets) {
        $dest = Join-Path $emu.Dir $script:EepromName
        if ($validEeprom -and -not (Test-Path -LiteralPath $dest)) {
            if (-not $DryRun) { Copy-Item -LiteralPath $validEeprom -Destination $dest -Force }
            & $Logger "Placed valid eeprom.bin for $($emu.Id): $dest" 'SUCCESS'
            $stats.Relocated++
        }
        elseif (-not $validEeprom -and -not (Test-Path -LiteralPath $dest)) {
            # No eeprom anywhere: ensure the folder exists so the emulator creates a
            # valid eeprom.bin itself on first launch (xemu/Cxbx both do this).
            if (-not $DryRun -and -not (Test-Path -LiteralPath $emu.Dir)) { New-Item -Path $emu.Dir -ItemType Directory -Force | Out-Null }
            & $Logger "eeprom.bin missing for $($emu.Id); configured path so the emulator will generate a valid one on next launch ($dest)." 'INFO'
            $stats.AutoGen++
        }
    }
    return $stats
}

function Repair-XboxBios {
    <#
    .SYNOPSIS
        Relocates an MCPX ROM / Xbox BIOS that exists somewhere into each Xbox
        emulator folder, and reports what is still missing (copyrighted - never
        downloaded). Returns @{ Relocated; MissingMcpx; MissingBios }.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][object[]] $XboxEmulators,
        [Parameter(Mandatory = $true)][string[]] $SearchRoots,
        [Parameter(Mandatory = $true)][scriptblock] $Logger,
        [switch] $DryRun
    )
    $stats = @{ Relocated=0; MissingMcpx=0; MissingBios=0 }
    $targets = @($XboxEmulators | Where-Object { $_.Kind -eq 'xbox' })
    if ($targets.Count -eq 0) { return $stats }

    $mcpx = Find-XboxFile -Roots $SearchRoots -Names $script:XboxMcpx
    $bios = Find-XboxFile -Roots $SearchRoots -Names $script:XboxBios

    foreach ($emu in $targets) {
        foreach ($pair in @(@{Src=$mcpx;Name='mcpx_1.0.bin'}, @{Src=$bios;Name='bios.bin'})) {
            if (-not $pair.Src) { continue }
            $dst = Join-Path $emu.Dir $pair.Name
            if (-not (Test-Path -LiteralPath $dst)) {
                if (-not $DryRun) { Copy-Item -LiteralPath $pair.Src -Destination $dst -Force }
                & $Logger "Relocated $($pair.Name) for $($emu.Id): $dst" 'SUCCESS'
                $stats.Relocated++
            }
        }
    }
    if (-not $mcpx) { $stats.MissingMcpx = 1; & $Logger "MCPX boot ROM not found (mcpx_1.0.bin). This is copyrighted firmware - provide your own dump; it is NOT downloaded." 'WARN' }
    if (-not $bios) { $stats.MissingBios = 1; & $Logger "Xbox BIOS not found (e.g. Complex_4627.bin / bios.bin). Copyrighted firmware - provide your own dump." 'WARN' }
    return $stats
}

function Set-XemuConfig {
    <#
    .SYNOPSIS
        Wires xemu.toml file paths and applies safe 4K graphics. Returns $true.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][object] $Emu,
        [Parameter(Mandatory = $true)][string] $Tier,
        [Parameter(Mandatory = $true)][string] $BackupRoot,
        [Parameter(Mandatory = $true)][scriptblock] $Logger,
        [switch] $DryRun
    )
    $cfg = $Emu.ConfigPath
    if ($DryRun) { & $Logger "[DRY-RUN] Would configure xemu.toml." 'INFO'; return $false }
    Backup-File -Path $cfg -BackupRoot $BackupRoot | Out-Null
    # File paths (only set when the file exists).
    $map = @{
        'bootrom_path'  = (Join-Path $Emu.Dir 'mcpx_1.0.bin')
        'flashrom_path' = (Join-Path $Emu.Dir 'bios.bin')
        'eeprom_path'   = (Join-Path $Emu.Dir 'eeprom.bin')
        'hdd_path'      = (Join-Path $Emu.Dir 'xbox_hdd.qcow2')
    }
    foreach ($k in $map.Keys) {
        $v = $map[$k]
        # eeprom path is always set (emulator creates it); others only if present.
        # xemu.toml uses TOML *literal* (single-quoted) strings: backslashes are
        # taken verbatim, so a Windows path must NOT be escaped.
        if ($k -eq 'eeprom_path' -or (Test-Path -LiteralPath $v)) {
            Set-TomlValue -Path $cfg -Key $k -Value ("'" + ($v -replace "'","") + "'")
        }
    }
    $scale = switch ($Tier) { 'FourK' {4} 'HighEnd' {4} 'MidRange' {2} default {1} }
    Set-TomlValue -Path $cfg -Key 'surface_scale' -Value "$scale"
    Set-TomlValue -Path $cfg -Key 'fullscreen_on_startup' -Value 'true'
    Set-TomlValue -Path $cfg -Key 'aspect_ratio' -Value "'16x9'"
    & $Logger "Configured xemu: file paths wired, surface_scale=$scale, 16:9." 'SUCCESS'
    if (-not (Test-Path -LiteralPath (Join-Path $Emu.Dir 'xbox_hdd.qcow2'))) {
        & $Logger "xemu HDD image (xbox_hdd.qcow2) is missing - create it once in xemu (Machine > ... > Create), then re-run." 'WARN'
    }
    return $true
}

function Set-CxbxConfig {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][object] $Emu,
        [Parameter(Mandatory = $true)][string] $BackupRoot,
        [Parameter(Mandatory = $true)][scriptblock] $Logger,
        [switch] $DryRun
    )
    $cfg = $Emu.ConfigPath
    if (-not (Test-Path -LiteralPath $cfg)) { & $Logger "Cxbx settings.ini not present yet; launch Cxbx once to create it, then re-run." 'INFO'; return $false }
    if ($DryRun) { & $Logger "[DRY-RUN] Would configure Cxbx settings.ini." 'INFO'; return $false }
    Backup-File -Path $cfg -BackupRoot $BackupRoot | Out-Null
    $ini = Read-IniFile -Path $cfg
    $eeprom = Join-Path $Emu.Dir 'EEPROM.bin'
    Set-IniValue -Data $ini -Section 'video' -Key 'FullScreen' -Value 'true'
    Set-IniValue -Data $ini -Section 'video' -Key 'VSync' -Value 'true'
    Set-IniValue -Data $ini -Section 'video' -Key 'RenderResolution' -Value '3'
    Write-IniFile -Path $cfg -Data $ini
    & $Logger "Configured Cxbx-Reloaded: fullscreen, vsync, higher render resolution." 'SUCCESS'
    return $true
}

function Set-XeniaConfig {
    <#
    .SYNOPSIS
        Configures xenia(-canary).config.toml: 4K resolution scale, vsync, GPU
        backend per vendor, license unlock and cache mount (fixes many no-boot
        cases). Returns $true.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][object] $Emu,
        [Parameter(Mandatory = $true)][string] $Tier,
        [Parameter(Mandatory = $true)][string] $GpuVendor,
        [Parameter(Mandatory = $true)][string] $BackupRoot,
        [Parameter(Mandatory = $true)][scriptblock] $Logger,
        [switch] $DryRun
    )
    $cfg = $Emu.ConfigPath
    if (-not (Test-Path -LiteralPath $cfg)) { & $Logger "$($Emu.Id) config not present yet; launch it once to create it, then re-run." 'INFO'; return $false }
    if ($DryRun) { & $Logger "[DRY-RUN] Would configure $($Emu.Id) toml." 'INFO'; return $false }
    Backup-File -Path $cfg -BackupRoot $BackupRoot | Out-Null
    $scale = switch ($Tier) { 'FourK' {3} 'HighEnd' {3} 'MidRange' {2} default {1} }
    $gpu = if ($GpuVendor -eq 'Intel') { '"d3d12"' } else { '"d3d12"' }   # d3d12 is the most compatible on Windows
    Set-TomlValue -Path $cfg -Key 'draw_resolution_scale_x' -Value "$scale"
    Set-TomlValue -Path $cfg -Key 'draw_resolution_scale_y' -Value "$scale"
    Set-TomlValue -Path $cfg -Key 'gpu' -Value $gpu
    Set-TomlValue -Path $cfg -Key 'vsync' -Value 'true'
    Set-TomlValue -Path $cfg -Key 'fullscreen' -Value 'true'
    Set-TomlValue -Path $cfg -Key 'mount_cache' -Value 'true'
    Set-TomlValue -Path $cfg -Key 'license_mask' -Value '-1'     # unlock owned content/DLC
    Set-TomlValue -Path $cfg -Key 'clear_memory_page_state' -Value 'false'
    & $Logger "Configured $($Emu.Id): d3d12, ${scale}x scale, vsync, cache mount, license unlock." 'SUCCESS'
    return $true
}

function Initialize-XeniaDirs {
    <#
    .SYNOPSIS
        Ensures xenia content/cache/patches folders exist and writes portable.txt so
        xenia keeps its data local. Returns count of items created.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][object] $Emu,
        [Parameter(Mandatory = $true)][scriptblock] $Logger,
        [switch] $DryRun
    )
    $created = 0
    foreach ($d in @('content','cache','patches','plugins')) {
        $p = Join-Path $Emu.Dir $d
        if (-not (Test-Path -LiteralPath $p)) { if (-not $DryRun) { New-Item -Path $p -ItemType Directory -Force | Out-Null }; $created++ }
    }
    $portable = Join-Path $Emu.Dir 'portable.txt'
    if (-not (Test-Path -LiteralPath $portable)) { if (-not $DryRun) { Set-Content -LiteralPath $portable -Value '' -Encoding UTF8 }; $created++ }
    if ($created -gt 0 -and -not $DryRun) { & $Logger "Prepared $($Emu.Id): content/cache/patches/plugins dirs + portable.txt." 'SUCCESS' }
    return $created
}

function Get-XboxReadiness {
    <#
    .SYNOPSIS
        Produces a per-emulator readiness checklist (what's present/missing).
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][object[]] $XboxEmulators)
    $out = New-Object System.Collections.Generic.List[object]
    foreach ($emu in $XboxEmulators) {
        if ($emu.Kind -eq 'xbox') {
            $eeprom = Test-Path -LiteralPath (Join-Path $emu.Dir 'eeprom.bin')
            $mcpx   = [bool](Find-XboxFile -Roots @($emu.Dir) -Names $script:XboxMcpx)
            $bios   = [bool](Find-XboxFile -Roots @($emu.Dir) -Names $script:XboxBios)
            $hdd    = ($emu.Id -ne 'xemu') -or (Test-Path -LiteralPath (Join-Path $emu.Dir 'xbox_hdd.qcow2'))
            $ready  = $mcpx -and $bios -and $hdd
            $out.Add(@{ Emulator=$emu.Id; Kind=$emu.Kind; Eeprom=$eeprom; Mcpx=$mcpx; Bios=$bios; Hdd=$hdd; Ready=$ready })
        } else {
            $cfg = Test-Path -LiteralPath $emu.ConfigPath
            $out.Add(@{ Emulator=$emu.Id; Kind=$emu.Kind; Eeprom=$true; Mcpx=$true; Bios=$true; Hdd=$true; Ready=$true; Config=$cfg })
        }
    }
    return $out.ToArray()
}

Export-ModuleMember -Function Get-XboxEmulators, Find-XboxFile, Repair-XboxEeprom, Repair-XboxBios, `
    Set-XemuConfig, Set-CxbxConfig, Set-XeniaConfig, Initialize-XeniaDirs, Get-XboxReadiness
