<#
.SYNOPSIS
    4K graphics optimization module.
.DESCRIPTION
    Applies resolution / quality / backend settings to each detected emulator
    according to the selected performance tier (LowEnd / MidRange / HighEnd /
    FourK). Each emulator family has a dedicated writer that understands its own
    configuration format. Every file is backed up before modification and all
    writes are non-destructive (existing keys updated, others preserved).

    Tier semantics:
      LowEnd   -> native internal resolution, light filtering, VSync on.
      MidRange -> 2x internal resolution, 8x AF, shader cache.
      HighEnd  -> ~4x internal resolution, 16x AF, modern backend.
      FourK    -> maximum safe internal resolution targeting 3840x2160, 16x AF.
#>

Set-StrictMode -Version Latest

# Per-tier integer upscale factors keyed by a logical "native height" bucket.
# Values chosen to stay within safe VRAM/perf envelopes for each tier.
$script:TierScale = @{
    'LowEnd'   = 1
    'MidRange' = 2
    'HighEnd'  = 4
    'FourK'    = 6
}

function Get-TierScale {
    param([string] $Tier, [int] $Max = 8, [int] $Min = 1)
    $s = if ($script:TierScale.ContainsKey($Tier)) { $script:TierScale[$Tier] } else { 2 }
    if ($s -gt $Max) { $s = $Max }
    if ($s -lt $Min) { $s = $Min }
    return $s
}

function Invoke-EmulatorOptimization {
    <#
    .SYNOPSIS
        Dispatches a single emulator to its tier-aware optimization routine.
    .OUTPUTS
        Hashtable: Success, Message, Changed (array of file paths touched).
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)] [object] $Emulator,
        [Parameter(Mandatory = $true)] [string] $Tier,
        [Parameter(Mandatory = $true)] [int]    $TargetWidth,
        [Parameter(Mandatory = $true)] [int]    $TargetHeight,
        [Parameter(Mandatory = $true)] [string] $BackupRoot,
        [Parameter(Mandatory = $true)] [scriptblock] $Logger,
        [string] $GpuVendor = 'Unknown'
    )

    $log = { param($m, $l) & $Logger $m $l }

    if (-not $Emulator.Installed) {
        return @{ Success = $false; Message = 'Not installed; skipped.'; Changed = @() }
    }
    if (-not $Emulator.Supports4K -and $Emulator.Known) {
        & $log "$($Emulator.DisplayName) does not support resolution scaling; applying VSync/backend only where possible." 'INFO'
    }

    try {
        switch ($Emulator.Id) {
            'retroarch'  { return Optimize-RetroArch  @PSBoundParameters }
            'pcsx2'      { return Optimize-PCSX2       @PSBoundParameters }
            'rpcs3'      { return Optimize-RPCS3       @PSBoundParameters }
            'xenia'      { return Optimize-Xenia       @PSBoundParameters }
            'dolphin'    { return Optimize-Dolphin     @PSBoundParameters }
            'primehack'  { return Optimize-Dolphin     @PSBoundParameters }
            'cemu'       { return Optimize-Cemu        @PSBoundParameters }
            'yuzu'       { return Optimize-Yuzu        @PSBoundParameters }
            'ryujinx'    { return Optimize-Ryujinx     @PSBoundParameters }
            'ppsspp'     { return Optimize-PPSSPP      @PSBoundParameters }
            'duckstation'{ return Optimize-DuckStation @PSBoundParameters }
            'melonds'    { return Optimize-MelonDS     @PSBoundParameters }
            'flycast'    { return Optimize-Flycast     @PSBoundParameters }
            'citra'      { return Optimize-Citra       @PSBoundParameters }
            'redream'    { return Optimize-Redream     @PSBoundParameters }
            'mame'       { return Optimize-MAME        @PSBoundParameters }
            default      {
                & $log "No dedicated optimizer for '$($Emulator.Id)'; left untouched." 'INFO'
                return @{ Success = $true; Message = 'No optimizer (unknown emulator).'; Changed = @() }
            }
        }
    } catch {
        & $log "Optimization error for $($Emulator.DisplayName): $($_.Exception.Message)" 'ERROR'
        return @{ Success = $false; Message = $_.Exception.Message; Changed = @() }
    }
}

function Resolve-ConfigPath {
    <#
    .SYNOPSIS
        Returns the first existing configured config file path for an emulator,
        or the first candidate path (which may not yet exist) so it can be created.
    #>
    param([object] $Emulator)
    $first = $null
    foreach ($rel in $Emulator.ConfigFiles) {
        $full = Join-Path $Emulator.FolderPath $rel
        if (-not $first) { $first = $full }
        if (Test-Path -LiteralPath $full) { return $full }
    }
    return $first
}

# ----------------------------------------------------------------------------
# RetroArch (flat key = "value")
# ----------------------------------------------------------------------------
function Optimize-RetroArch {
    param($Emulator, $Tier, $TargetWidth, $TargetHeight, $BackupRoot, $Logger, $GpuVendor = 'Unknown')
    $cfg = Join-Path $Emulator.FolderPath 'retroarch.cfg'
    New-ConfigBackup -Path $cfg -BackupRoot $BackupRoot | Out-Null

    $smooth = if ($Tier -eq 'LowEnd') { 'false' } else { 'true' }
    # GPU-aware backend: Vulkan for NVIDIA/AMD; glcore for Intel iGPUs where
    # Vulkan drivers are historically less reliable in RetroArch.
    $raDriver = if ($GpuVendor -eq 'Intel') { 'glcore' } else { 'vulkan' }
    $map = [ordered]@{
        'video_fullscreen'         = 'true'
        'video_windowed_fullscreen'= 'true'
        'video_fullscreen_x'       = "$TargetWidth"
        'video_fullscreen_y'       = "$TargetHeight"
        'video_vsync'              = 'true'
        'video_hard_sync'          = 'false'
        'video_smooth'             = $smooth
        'video_threaded'           = 'true'
        'video_driver'             = $raDriver
        'video_shader_enable'      = 'true'
        'video_max_swapchain_images' = '3'
        'video_aspect_ratio_auto'  = 'true'
        'menu_driver'              = 'ozone'
    }
    foreach ($k in $map.Keys) { Set-FlatConfigValue -Path $cfg -Key $k -Value $map[$k] -Quote }
    & $Logger "RetroArch optimized for ${TargetWidth}x${TargetHeight} (tier $Tier)." 'SUCCESS'
    return @{ Success = $true; Message = 'RetroArch configured.'; Changed = @($cfg) }
}

# ----------------------------------------------------------------------------
# PCSX2 (INI)
# ----------------------------------------------------------------------------
function Optimize-PCSX2 {
    param($Emulator, $Tier, $TargetWidth, $TargetHeight, $BackupRoot, $Logger, $GpuVendor = 'Unknown')
    $cfg = Resolve-ConfigPath -Emulator $Emulator
    New-ConfigBackup -Path $cfg -BackupRoot $BackupRoot | Out-Null
    $ini = Read-IniFile -Path $cfg

    $scale = Get-TierScale -Tier $Tier -Max 8 -Min 1   # upscale_multiplier
    # PCSX2 Renderer: 14=Vulkan, 12=Direct3D11. Intel iGPUs run most reliably on
    # D3D11; discrete NVIDIA/AMD get Vulkan.
    $pcsxRenderer = if ($GpuVendor -eq 'Intel') { '12' } else { '14' }
    $pcsxBackend  = if ($GpuVendor -eq 'Intel') { 'Direct3D11' } else { 'Vulkan' }
    Set-IniValue -Data $ini -Section 'EmuCore/GS' -Key 'upscale_multiplier' -Value ("{0}" -f $scale)
    Set-IniValue -Data $ini -Section 'EmuCore/GS' -Key 'Renderer'            -Value $pcsxRenderer
    Set-IniValue -Data $ini -Section 'EmuCore/GS' -Key 'AnisotropicFiltering' -Value '16'
    Set-IniValue -Data $ini -Section 'EmuCore/GS' -Key 'TextureFiltering'    -Value '2'    # bilinear (forced)
    Set-IniValue -Data $ini -Section 'EmuCore/GS' -Key 'VsyncEnable'         -Value '1'
    Set-IniValue -Data $ini -Section 'EmuCore/GS' -Key 'mipmap_hw'           -Value '-1'
    Set-IniValue -Data $ini -Section 'EmuCore/GS' -Key 'OsdShowMessages'     -Value 'false'

    Write-IniFile -Path $cfg -Data $ini
    & $Logger "PCSX2 optimized: upscale ${scale}x, $pcsxBackend, 16x AF (tier $Tier)." 'SUCCESS'
    return @{ Success = $true; Message = 'PCSX2 configured.'; Changed = @($cfg) }
}

# ----------------------------------------------------------------------------
# RPCS3 (YAML scalars)
# ----------------------------------------------------------------------------
function Optimize-RPCS3 {
    param($Emulator, $Tier, $TargetWidth, $TargetHeight, $BackupRoot, $Logger, $GpuVendor = 'Unknown')
    $cfg = Resolve-ConfigPath -Emulator $Emulator
    New-ConfigBackup -Path $cfg -BackupRoot $BackupRoot | Out-Null

    $scalePct = switch ($Tier) { 'LowEnd' {100} 'MidRange' {150} 'HighEnd' {300} 'FourK' {400} default {150} }
    Set-YamlScalar -Path $cfg -Key 'Renderer' -Value 'Vulkan'
    Set-YamlScalar -Path $cfg -Key 'Resolution Scale (%)' -Value "$scalePct"
    Set-YamlScalar -Path $cfg -Key 'Anisotropic Filter Override' -Value '16'
    Set-YamlScalar -Path $cfg -Key 'VSync' -Value 'true'
    Set-YamlScalar -Path $cfg -Key 'Write Color Buffers' -Value 'true'
    & $Logger "RPCS3 optimized: Vulkan, resolution scale ${scalePct}% (tier $Tier)." 'SUCCESS'
    return @{ Success = $true; Message = 'RPCS3 configured.'; Changed = @($cfg) }
}

# ----------------------------------------------------------------------------
# Xenia (TOML scalars)
# ----------------------------------------------------------------------------
function Optimize-Xenia {
    param($Emulator, $Tier, $TargetWidth, $TargetHeight, $BackupRoot, $Logger, $GpuVendor = 'Unknown')
    $cfg = Resolve-ConfigPath -Emulator $Emulator
    New-ConfigBackup -Path $cfg -BackupRoot $BackupRoot | Out-Null

    $resScale = Get-TierScale -Tier $Tier -Max 3 -Min 1   # Xenia supports 1x/2x/3x draw scaling
    Set-TomlValue -Path $cfg -Key 'gpu' -Value '"vulkan"'
    Set-TomlValue -Path $cfg -Key 'draw_resolution_scale_x' -Value "$resScale"
    Set-TomlValue -Path $cfg -Key 'draw_resolution_scale_y' -Value "$resScale"
    Set-TomlValue -Path $cfg -Key 'vsync' -Value 'true'
    Set-TomlValue -Path $cfg -Key 'fullscreen' -Value 'true'
    & $Logger "Xenia optimized: Vulkan, draw scale ${resScale}x (tier $Tier)." 'SUCCESS'
    return @{ Success = $true; Message = 'Xenia configured.'; Changed = @($cfg) }
}

# ----------------------------------------------------------------------------
# Dolphin / PrimeHack (GFX.ini + Dolphin.ini)
# ----------------------------------------------------------------------------
function Optimize-Dolphin {
    param($Emulator, $Tier, $TargetWidth, $TargetHeight, $BackupRoot, $Logger, $GpuVendor = 'Unknown')
    $gfx     = Join-Path $Emulator.FolderPath 'User\Config\GFX.ini'
    $general = Join-Path $Emulator.FolderPath 'User\Config\Dolphin.ini'

    New-ConfigBackup -Path $gfx -BackupRoot $BackupRoot | Out-Null
    $g = Read-IniFile -Path $gfx
    # InternalResolution: 0=auto(window), otherwise integer multiplier of native.
    $ir = switch ($Tier) { 'LowEnd' {1} 'MidRange' {3} 'HighEnd' {5} 'FourK' {6} default {3} }
    Set-IniValue -Data $g -Section 'Settings' -Key 'InternalResolution' -Value "$ir"
    Set-IniValue -Data $g -Section 'Settings' -Key 'MaxAnisotropy' -Value '4'        # 4 -> 16x
    Set-IniValue -Data $g -Section 'Settings' -Key 'ShaderCompilationMode' -Value '0'
    Set-IniValue -Data $g -Section 'Settings' -Key 'WaitForShadersBeforeStarting' -Value 'True'
    Set-IniValue -Data $g -Section 'Hardware' -Key 'VSync' -Value 'True'
    Set-IniValue -Data $g -Section 'Enhancements' -Key 'ForceFiltering' -Value 'True'
    Set-IniValue -Data $g -Section 'Enhancements' -Key 'MaxAnisotropy' -Value '4'
    Write-IniFile -Path $gfx -Data $g

    New-ConfigBackup -Path $general -BackupRoot $BackupRoot | Out-Null
    $d = Read-IniFile -Path $general
    Set-IniValue -Data $d -Section 'Core' -Key 'GFXBackend' -Value 'Vulkan'
    Write-IniFile -Path $general -Data $d

    & $Logger "$($Emulator.DisplayName) optimized: internal res ${ir}x, Vulkan, 16x AF (tier $Tier)." 'SUCCESS'
    return @{ Success = $true; Message = 'Dolphin family configured.'; Changed = @($gfx, $general) }
}

# ----------------------------------------------------------------------------
# Cemu (settings.xml)
# ----------------------------------------------------------------------------
function Optimize-Cemu {
    param($Emulator, $Tier, $TargetWidth, $TargetHeight, $BackupRoot, $Logger, $GpuVendor = 'Unknown')
    $cfg = Resolve-ConfigPath -Emulator $Emulator
    New-ConfigBackup -Path $cfg -BackupRoot $BackupRoot | Out-Null

    # Cemu internal resolution is driven by graphic packs; here we set the global
    # rendering backend, VSync and async shader compile which are in settings.xml.
    if (-not (Test-Path -LiteralPath $cfg)) {
        $xml = @'
<?xml version="1.0" encoding="UTF-8"?>
<content>
    <GraphicAPI>1</GraphicAPI>
    <VSync>1</VSync>
    <AsyncCompile>true</AsyncCompile>
    <Fullscreen>true</Fullscreen>
</content>
'@
        $dir = Split-Path $cfg -Parent
        if ($dir -and -not (Test-Path $dir)) { New-Item -Path $dir -ItemType Directory -Force | Out-Null }
        [System.IO.File]::WriteAllText($cfg, $xml, (New-Object System.Text.UTF8Encoding($false)))
    } else {
        $content = Get-Content -LiteralPath $cfg -Raw -Encoding UTF8
        $content = Set-XmlElement -Content $content -Element 'GraphicAPI' -Value '1'   # 1 = Vulkan
        $content = Set-XmlElement -Content $content -Element 'VSync' -Value '1'
        $content = Set-XmlElement -Content $content -Element 'AsyncCompile' -Value 'true'
        $content = Set-XmlElement -Content $content -Element 'Fullscreen' -Value 'true'
        [System.IO.File]::WriteAllText($cfg, $content, (New-Object System.Text.UTF8Encoding($false)))
    }
    & $Logger "Cemu optimized: Vulkan backend, VSync, async shader compile (tier $Tier)." 'SUCCESS'
    return @{ Success = $true; Message = 'Cemu configured.'; Changed = @($cfg) }
}

function Set-XmlElement {
    <#
    .SYNOPSIS
        Replaces or inserts a simple <Element>value</Element> in an XML string.
    #>
    param([string] $Content, [string] $Element, [string] $Value)
    $pattern = "<$Element>.*?</$Element>"
    $replace = "<$Element>$Value</$Element>"
    if ($Content -match $pattern) {
        return [Regex]::Replace($Content, $pattern, $replace)
    }
    # Insert before closing root tag (assumes </content> style root).
    if ($Content -match '</[A-Za-z0-9_]+>\s*$') {
        return [Regex]::Replace($Content, '(</[A-Za-z0-9_]+>\s*)$', "    $replace`r`n`$1")
    }
    return $Content + "`r`n$replace"
}

# ----------------------------------------------------------------------------
# Yuzu / compatible (qt-config.ini)
# ----------------------------------------------------------------------------
function Optimize-Yuzu {
    param($Emulator, $Tier, $TargetWidth, $TargetHeight, $BackupRoot, $Logger, $GpuVendor = 'Unknown')
    $cfg = Resolve-ConfigPath -Emulator $Emulator
    New-ConfigBackup -Path $cfg -BackupRoot $BackupRoot | Out-Null
    $ini = Read-IniFile -Path $cfg

    # resolution_setup index: 2=1x,3=2x,4=3x,5=4x (matches emulator UI ordering).
    $resSetup = switch ($Tier) { 'LowEnd' {2} 'MidRange' {3} 'HighEnd' {5} 'FourK' {5} default {3} }
    Set-IniValue -Data $ini -Section 'Renderer' -Key 'backend' -Value '1'             # 1 = Vulkan
    Set-IniValue -Data $ini -Section 'Renderer' -Key 'backend\default' -Value 'false'
    Set-IniValue -Data $ini -Section 'Renderer' -Key 'resolution_setup' -Value "$resSetup"
    Set-IniValue -Data $ini -Section 'Renderer' -Key 'resolution_setup\default' -Value 'false'
    Set-IniValue -Data $ini -Section 'Renderer' -Key 'max_anisotropy' -Value '5'      # 5 -> 16x
    Set-IniValue -Data $ini -Section 'Renderer' -Key 'max_anisotropy\default' -Value 'false'
    Set-IniValue -Data $ini -Section 'Renderer' -Key 'use_vsync' -Value '1'
    Set-IniValue -Data $ini -Section 'Renderer' -Key 'use_asynchronous_shaders' -Value 'true'
    Write-IniFile -Path $cfg -Data $ini
    & $Logger "Yuzu-family optimized: Vulkan, resolution setup $resSetup, 16x AF (tier $Tier)." 'SUCCESS'
    return @{ Success = $true; Message = 'Yuzu configured.'; Changed = @($cfg) }
}

# ----------------------------------------------------------------------------
# Ryujinx (Config.json)
# ----------------------------------------------------------------------------
function Optimize-Ryujinx {
    param($Emulator, $Tier, $TargetWidth, $TargetHeight, $BackupRoot, $Logger, $GpuVendor = 'Unknown')
    $cfg = Resolve-ConfigPath -Emulator $Emulator
    if (-not (Test-Path -LiteralPath $cfg)) {
        & $Logger "Ryujinx Config.json not present yet; will be created on first launch. Skipping." 'WARN'
        return @{ Success = $false; Message = 'Config.json absent.'; Changed = @() }
    }
    New-ConfigBackup -Path $cfg -BackupRoot $BackupRoot | Out-Null

    $resScale = switch ($Tier) { 'LowEnd' {1} 'MidRange' {2} 'HighEnd' {3} 'FourK' {4} default {2} }
    $json = Get-Content -LiteralPath $cfg -Raw -Encoding UTF8 | ConvertFrom-Json
    $json | Add-Member -NotePropertyName 'res_scale' -NotePropertyValue $resScale -Force
    $json | Add-Member -NotePropertyName 'graphics_backend' -NotePropertyValue 'Vulkan' -Force
    $json | Add-Member -NotePropertyName 'enable_vsync' -NotePropertyValue $true -Force
    $json | Add-Member -NotePropertyName 'max_anisotropy' -NotePropertyValue 16 -Force
    ($json | ConvertTo-Json -Depth 50) | Set-Content -LiteralPath $cfg -Encoding UTF8
    & $Logger "Ryujinx optimized: Vulkan, res scale ${resScale}x, 16x AF (tier $Tier)." 'SUCCESS'
    return @{ Success = $true; Message = 'Ryujinx configured.'; Changed = @($cfg) }
}

# ----------------------------------------------------------------------------
# PPSSPP (ppsspp.ini)
# ----------------------------------------------------------------------------
function Optimize-PPSSPP {
    param($Emulator, $Tier, $TargetWidth, $TargetHeight, $BackupRoot, $Logger, $GpuVendor = 'Unknown')
    $cfg = Resolve-ConfigPath -Emulator $Emulator
    New-ConfigBackup -Path $cfg -BackupRoot $BackupRoot | Out-Null
    $ini = Read-IniFile -Path $cfg

    $ir = switch ($Tier) { 'LowEnd' {2} 'MidRange' {5} 'HighEnd' {8} 'FourK' {10} default {5} }
    Set-IniValue -Data $ini -Section 'Graphics' -Key 'InternalResolution' -Value "$ir"
    Set-IniValue -Data $ini -Section 'Graphics' -Key 'AndroidHwScale' -Value '0'
    Set-IniValue -Data $ini -Section 'Graphics' -Key 'TextureFiltering' -Value '3'     # linear
    Set-IniValue -Data $ini -Section 'Graphics' -Key 'AnisotropyLevel' -Value '4'      # 16x
    Set-IniValue -Data $ini -Section 'Graphics' -Key 'VSync' -Value 'True'
    Set-IniValue -Data $ini -Section 'Graphics' -Key 'GraphicsBackend' -Value '3'      # Vulkan
    Set-IniValue -Data $ini -Section 'Graphics' -Key 'FullScreen' -Value 'True'
    Write-IniFile -Path $cfg -Data $ini
    & $Logger "PPSSPP optimized: internal res ${ir}x, Vulkan, 16x AF (tier $Tier)." 'SUCCESS'
    return @{ Success = $true; Message = 'PPSSPP configured.'; Changed = @($cfg) }
}

# ----------------------------------------------------------------------------
# DuckStation (settings.ini)
# ----------------------------------------------------------------------------
function Optimize-DuckStation {
    param($Emulator, $Tier, $TargetWidth, $TargetHeight, $BackupRoot, $Logger, $GpuVendor = 'Unknown')
    $cfg = Resolve-ConfigPath -Emulator $Emulator
    New-ConfigBackup -Path $cfg -BackupRoot $BackupRoot | Out-Null
    $ini = Read-IniFile -Path $cfg

    $scale = switch ($Tier) { 'LowEnd' {2} 'MidRange' {4} 'HighEnd' {8} 'FourK' {9} default {4} }
    $dsRenderer = if ($GpuVendor -eq 'Intel') { 'D3D11' } else { 'Vulkan' }
    Set-IniValue -Data $ini -Section 'GPU' -Key 'Renderer' -Value $dsRenderer
    Set-IniValue -Data $ini -Section 'GPU' -Key 'ResolutionScale' -Value "$scale"
    Set-IniValue -Data $ini -Section 'GPU' -Key 'TextureFilter' -Value 'Bilinear'
    Set-IniValue -Data $ini -Section 'GPU' -Key 'PGXPEnable' -Value 'true'
    Set-IniValue -Data $ini -Section 'GPU' -Key 'PGXPCulling' -Value 'true'
    Set-IniValue -Data $ini -Section 'Display' -Key 'VSync' -Value 'true'
    Set-IniValue -Data $ini -Section 'Display' -Key 'Fullscreen' -Value 'true'
    Write-IniFile -Path $cfg -Data $ini
    & $Logger "DuckStation optimized: $dsRenderer, resolution scale ${scale}x, PGXP on (tier $Tier)." 'SUCCESS'
    return @{ Success = $true; Message = 'DuckStation configured.'; Changed = @($cfg) }
}

# ----------------------------------------------------------------------------
# melonDS (melonDS.ini)
# ----------------------------------------------------------------------------
function Optimize-MelonDS {
    param($Emulator, $Tier, $TargetWidth, $TargetHeight, $BackupRoot, $Logger, $GpuVendor = 'Unknown')
    $cfg = Resolve-ConfigPath -Emulator $Emulator
    New-ConfigBackup -Path $cfg -BackupRoot $BackupRoot | Out-Null
    $ini = Read-IniFile -Path $cfg

    $scale = switch ($Tier) { 'LowEnd' {1} 'MidRange' {4} 'HighEnd' {6} 'FourK' {8} default {4} }
    # melonDS stores most keys in the global (section-less) area.
    Set-IniValue -Data $ini -Section '' -Key '3DRenderer' -Value '1'        # 1 = OpenGL
    Set-IniValue -Data $ini -Section '' -Key 'GL_ScaleFactor' -Value "$scale"
    Set-IniValue -Data $ini -Section '' -Key 'GL_BetterPolygons' -Value '1'
    Set-IniValue -Data $ini -Section '' -Key 'ScreenVSync' -Value '1'
    Write-IniFile -Path $cfg -Data $ini
    & $Logger "melonDS optimized: OpenGL renderer, scale ${scale}x (tier $Tier)." 'SUCCESS'
    return @{ Success = $true; Message = 'melonDS configured.'; Changed = @($cfg) }
}

# ----------------------------------------------------------------------------
# Flycast (emu.cfg)
# ----------------------------------------------------------------------------
function Optimize-Flycast {
    param($Emulator, $Tier, $TargetWidth, $TargetHeight, $BackupRoot, $Logger, $GpuVendor = 'Unknown')
    $cfg = Resolve-ConfigPath -Emulator $Emulator
    New-ConfigBackup -Path $cfg -BackupRoot $BackupRoot | Out-Null
    $ini = Read-IniFile -Path $cfg

    $res = switch ($Tier) { 'LowEnd' {480} 'MidRange' {1080} 'HighEnd' {1440} 'FourK' {2160} default {1080} }
    Set-IniValue -Data $ini -Section 'config' -Key 'rend.Resolution' -Value "$res"
    Set-IniValue -Data $ini -Section 'config' -Key 'rend.vsync' -Value 'yes'
    Set-IniValue -Data $ini -Section 'config' -Key 'rend.AnisotropicFiltering' -Value '16'
    Set-IniValue -Data $ini -Section 'config' -Key 'rend.WideScreen' -Value 'yes'
    Set-IniValue -Data $ini -Section 'config' -Key 'pvr.rend' -Value '4'    # 4 = Vulkan
    Write-IniFile -Path $cfg -Data $ini
    & $Logger "Flycast optimized: internal height ${res}p, Vulkan, 16x AF (tier $Tier)." 'SUCCESS'
    return @{ Success = $true; Message = 'Flycast configured.'; Changed = @($cfg) }
}

# ----------------------------------------------------------------------------
# Citra / compatible (qt-config.ini)
# ----------------------------------------------------------------------------
function Optimize-Citra {
    param($Emulator, $Tier, $TargetWidth, $TargetHeight, $BackupRoot, $Logger, $GpuVendor = 'Unknown')
    $cfg = Resolve-ConfigPath -Emulator $Emulator
    New-ConfigBackup -Path $cfg -BackupRoot $BackupRoot | Out-Null
    $ini = Read-IniFile -Path $cfg

    $factor = switch ($Tier) { 'LowEnd' {1} 'MidRange' {2} 'HighEnd' {4} 'FourK' {6} default {2} }
    Set-IniValue -Data $ini -Section 'Renderer' -Key 'resolution_factor' -Value "$factor"
    Set-IniValue -Data $ini -Section 'Renderer' -Key 'resolution_factor\default' -Value 'false'
    Set-IniValue -Data $ini -Section 'Renderer' -Key 'use_vsync_new' -Value 'true'
    Set-IniValue -Data $ini -Section 'Renderer' -Key 'use_vsync_new\default' -Value 'false'
    Set-IniValue -Data $ini -Section 'Renderer' -Key 'graphics_api' -Value '1'   # 1 = OpenGL
    Set-IniValue -Data $ini -Section 'Renderer' -Key 'filter_mode' -Value 'true'
    Write-IniFile -Path $cfg -Data $ini
    & $Logger "Citra-family optimized: resolution factor ${factor}x (tier $Tier)." 'SUCCESS'
    return @{ Success = $true; Message = 'Citra configured.'; Changed = @($cfg) }
}

# ----------------------------------------------------------------------------
# Redream (redream.cfg)
# ----------------------------------------------------------------------------
function Optimize-Redream {
    param($Emulator, $Tier, $TargetWidth, $TargetHeight, $BackupRoot, $Logger, $GpuVendor = 'Unknown')
    $cfg = Resolve-ConfigPath -Emulator $Emulator
    New-ConfigBackup -Path $cfg -BackupRoot $BackupRoot | Out-Null

    # Redream uses flat key=value; res is 1=native,2=2x,3=4x,4=8x equivalents.
    $res = switch ($Tier) { 'LowEnd' {1} 'MidRange' {2} 'HighEnd' {3} 'FourK' {4} default {2} }
    Set-FlatConfigValue -Path $cfg -Key 'res' -Value "$res" -Separator '='
    Set-FlatConfigValue -Path $cfg -Key 'vsync' -Value '1' -Separator '='
    Set-FlatConfigValue -Path $cfg -Key 'aspect' -Value '16:9' -Separator '='
    Set-FlatConfigValue -Path $cfg -Key 'fullmode' -Value 'exclusive fullscreen' -Separator '='
    & $Logger "Redream optimized: internal res level ${res} (tier $Tier)." 'SUCCESS'
    return @{ Success = $true; Message = 'Redream configured.'; Changed = @($cfg) }
}

# ----------------------------------------------------------------------------
# MAME (mame.ini) - arcade hardware is fixed-res; tune presentation/VSync only.
# ----------------------------------------------------------------------------
function Optimize-MAME {
    param($Emulator, $Tier, $TargetWidth, $TargetHeight, $BackupRoot, $Logger, $GpuVendor = 'Unknown')
    $cfg = Resolve-ConfigPath -Emulator $Emulator
    if (-not (Test-Path -LiteralPath $cfg)) {
        & $Logger "mame.ini not present; MAME generates it via 'mame -createconfig'. Skipping." 'WARN'
        return @{ Success = $false; Message = 'mame.ini absent.'; Changed = @() }
    }
    New-ConfigBackup -Path $cfg -BackupRoot $BackupRoot | Out-Null
    # MAME ini is whitespace-delimited "key value".
    Set-FlatConfigValue -Path $cfg -Key 'video' -Value 'bgfx' -Separator '                  '
    Set-FlatConfigValue -Path $cfg -Key 'waitvsync' -Value '1' -Separator '             '
    Set-FlatConfigValue -Path $cfg -Key 'filter' -Value '1' -Separator '                 '
    Set-FlatConfigValue -Path $cfg -Key 'prescale' -Value '0' -Separator '               '
    & $Logger "MAME optimized: BGFX renderer, VSync, bilinear filter (tier $Tier)." 'SUCCESS'
    return @{ Success = $true; Message = 'MAME configured.'; Changed = @($cfg) }
}

Export-ModuleMember -Function Invoke-EmulatorOptimization, Get-TierScale, Resolve-ConfigPath, Set-XmlElement
