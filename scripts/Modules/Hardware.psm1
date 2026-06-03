<#
.SYNOPSIS
    Hardware detection module.
.DESCRIPTION
    Detects CPU, GPU, RAM, storage media type, primary display resolution and
    refresh rate via CIM/WMI, then classifies the system into a performance tier
    (LowEnd / MidRange / HighEnd / FourK) used to select emulator profiles.
#>

Set-StrictMode -Version Latest

function Get-SystemHardware {
    <#
    .SYNOPSIS
        Returns a hashtable describing the host hardware and chosen tier.
    #>
    [CmdletBinding()]
    param()

    $info = [ordered]@{
        CpuName          = 'Unknown'
        CpuCores         = 0
        CpuLogical       = 0
        CpuMaxClockMHz   = 0
        GpuName          = 'Unknown'
        GpuVendor        = 'Unknown'
        GpuVramMB        = 0
        GpuDriverVersion = 'Unknown'
        TotalRamGB       = 0
        SystemDriveType  = 'Unknown'
        DisplayWidth     = 0
        DisplayHeight    = 0
        RefreshRateHz    = 0
        Is4KCapable      = $false
        Tier             = 'MidRange'
    }

    # ---- CPU ----
    try {
        $cpu = Get-CimInstance -ClassName Win32_Processor -ErrorAction Stop | Select-Object -First 1
        if ($cpu) {
            $info.CpuName        = ($cpu.Name).Trim()
            $info.CpuCores       = [int]$cpu.NumberOfCores
            $info.CpuLogical     = [int]$cpu.NumberOfLogicalProcessors
            $info.CpuMaxClockMHz = [int]$cpu.MaxClockSpeed
        }
    } catch { }

    # ---- RAM ----
    try {
        $os = Get-CimInstance -ClassName Win32_ComputerSystem -ErrorAction Stop
        if ($os) {
            $info.TotalRamGB = [math]::Round($os.TotalPhysicalMemory / 1GB, 1)
        }
    } catch {
        try {
            $mem = Get-CimInstance -ClassName Win32_PhysicalMemory -ErrorAction Stop |
                   Measure-Object -Property Capacity -Sum
            $info.TotalRamGB = [math]::Round($mem.Sum / 1GB, 1)
        } catch { }
    }

    # ---- GPU (pick the adapter with the most VRAM, i.e. the discrete one) ----
    try {
        $gpus = Get-CimInstance -ClassName Win32_VideoController -ErrorAction Stop |
                Where-Object { $_.Name }
        if ($gpus) {
            $primary = $gpus | Sort-Object -Property AdapterRAM -Descending | Select-Object -First 1
            $info.GpuName          = ($primary.Name).Trim()
            $info.GpuDriverVersion = $primary.DriverVersion
            # AdapterRAM is a signed 32-bit value and wraps above 4 GB; prefer the
            # registry HardwareInformation.qwMemorySize when AdapterRAM looks wrong.
            $vram = [int64]$primary.AdapterRAM
            if ($vram -le 0) { $vram = 0 }
            $info.GpuVramMB = [int]([math]::Round($vram / 1MB))

            $qw = Get-GpuVramFromRegistry
            if ($qw -gt $info.GpuVramMB) { $info.GpuVramMB = $qw }

            $name = $info.GpuName.ToLower()
            if     ($name -match 'nvidia|geforce|rtx|gtx|quadro') { $info.GpuVendor = 'NVIDIA' }
            elseif ($name -match 'amd|radeon|rx ?\d|vega')        { $info.GpuVendor = 'AMD' }
            elseif ($name -match 'intel|arc|iris|uhd|hd graphics'){ $info.GpuVendor = 'Intel' }
        }
    } catch { }

    # ---- Display resolution / refresh ----
    try {
        $disp = Get-CimInstance -ClassName Win32_VideoController -ErrorAction Stop |
                Where-Object { $_.CurrentHorizontalResolution -gt 0 } |
                Sort-Object -Property CurrentHorizontalResolution -Descending |
                Select-Object -First 1
        if ($disp) {
            $info.DisplayWidth  = [int]$disp.CurrentHorizontalResolution
            $info.DisplayHeight = [int]$disp.CurrentVerticalResolution
            $info.RefreshRateHz = [int]$disp.CurrentRefreshRate
        }
    } catch { }

    if ($info.DisplayWidth -ge 3840 -or $info.DisplayHeight -ge 2160) {
        $info.Is4KCapable = $true
    }

    # ---- System drive media type (SSD vs HDD) ----
    try {
        $sysLetter = $env:SystemDrive.TrimEnd(':')
        $partition = Get-CimInstance -ClassName Win32_LogicalDiskToPartition -ErrorAction Stop
        $mediaType = Get-SystemDriveMediaType
        if ($mediaType) { $info.SystemDriveType = $mediaType }
    } catch { }

    $info.Tier = Resolve-PerformanceTier -Hardware $info
    return $info
}

function Get-GpuVramFromRegistry {
    <#
    .SYNOPSIS
        Reads true VRAM size (in MB) from the display adapter registry key,
        working around the 32-bit AdapterRAM overflow on cards with >4 GB.
    #>
    [CmdletBinding()]
    param()

    $best = 0
    try {
        $base = 'HKLM:\SYSTEM\CurrentControlSet\Control\Class\{4d36e968-e325-11ce-bfc1-08002be10318}'
        if (Test-Path $base) {
            Get-ChildItem $base -ErrorAction SilentlyContinue | ForEach-Object {
                $val = (Get-ItemProperty -Path $_.PSPath -Name 'HardwareInformation.qwMemorySize' -ErrorAction SilentlyContinue).'HardwareInformation.qwMemorySize'
                if ($val) {
                    $mb = [int]([math]::Round([int64]$val / 1MB))
                    if ($mb -gt $best) { $best = $mb }
                }
            }
        }
    } catch { }
    return $best
}

function Get-SystemDriveMediaType {
    <#
    .SYNOPSIS
        Determines whether the OS drive is SSD, HDD or NVMe using Storage cmdlets,
        with a graceful fallback if the Storage module is unavailable.
    #>
    [CmdletBinding()]
    param()

    try {
        if (Get-Command -Name Get-PhysicalDisk -ErrorAction SilentlyContinue) {
            $disks = Get-PhysicalDisk -ErrorAction Stop
            # Prefer a disk reporting bus type NVMe; otherwise use the media type.
            $nvme = $disks | Where-Object { $_.BusType -eq 'NVMe' } | Select-Object -First 1
            if ($nvme) { return 'NVMe SSD' }
            $ssd  = $disks | Where-Object { $_.MediaType -eq 'SSD' } | Select-Object -First 1
            if ($ssd)  { return 'SSD' }
            $hdd  = $disks | Where-Object { $_.MediaType -eq 'HDD' } | Select-Object -First 1
            if ($hdd)  { return 'HDD' }
            $any  = $disks | Select-Object -First 1
            if ($any -and $any.MediaType) { return [string]$any.MediaType }
        }
    } catch { }
    return 'Unknown'
}

function Resolve-PerformanceTier {
    <#
    .SYNOPSIS
        Classifies the system into LowEnd / MidRange / HighEnd / FourK based on a
        weighted scoring of CPU threads, RAM, GPU VRAM/vendor and display.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [System.Collections.Specialized.OrderedDictionary] $Hardware
    )

    $score = 0

    # CPU threads
    if     ($Hardware.CpuLogical -ge 16) { $score += 3 }
    elseif ($Hardware.CpuLogical -ge 8)  { $score += 2 }
    elseif ($Hardware.CpuLogical -ge 4)  { $score += 1 }

    # RAM
    if     ($Hardware.TotalRamGB -ge 32) { $score += 3 }
    elseif ($Hardware.TotalRamGB -ge 16) { $score += 2 }
    elseif ($Hardware.TotalRamGB -ge 8)  { $score += 1 }

    # GPU VRAM
    if     ($Hardware.GpuVramMB -ge 8192) { $score += 3 }
    elseif ($Hardware.GpuVramMB -ge 4096) { $score += 2 }
    elseif ($Hardware.GpuVramMB -ge 2048) { $score += 1 }

    # Discrete NVIDIA/AMD bonus; integrated Intel penalty.
    if ($Hardware.GpuVendor -in @('NVIDIA', 'AMD') -and $Hardware.GpuVramMB -ge 4096) { $score += 1 }
    if ($Hardware.GpuVendor -eq 'Intel') { $score -= 1 }

    # Fast storage bonus.
    if ($Hardware.SystemDriveType -match 'SSD|NVMe') { $score += 1 }

    if ($score -le 3)      { $tier = 'LowEnd' }
    elseif ($score -le 6)  { $tier = 'MidRange' }
    else                   { $tier = 'HighEnd' }

    # Promote a capable HighEnd machine on a 4K panel to the FourK profile.
    if ($tier -eq 'HighEnd' -and $Hardware.Is4KCapable -and $Hardware.GpuVramMB -ge 6144) {
        $tier = 'FourK'
    }

    return $tier
}

Export-ModuleMember -Function Get-SystemHardware, Resolve-PerformanceTier, Get-SystemDriveMediaType, Get-GpuVramFromRegistry
