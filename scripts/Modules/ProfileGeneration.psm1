<#
.SYNOPSIS
    Emulator profile generation module.
.DESCRIPTION
    Generates and persists optimization profiles for LowEnd / MidRange / HighEnd /
    FourK system classes, and selects the most appropriate profile for the
    detected hardware. Profiles are written as JSON under system\profiles so they
    can be inspected, re-applied, or overridden by the user.
#>

Set-StrictMode -Version Latest

function Get-ProfileDefinitions {
    <#
    .SYNOPSIS
        Returns the four canonical profile definitions as a hashtable keyed by tier.
    #>
    [CmdletBinding()]
    param()

    return [ordered]@{
        'LowEnd' = [ordered]@{
            Description       = 'Low-end systems: prioritise stable full speed at native resolution.'
            TargetWidth       = 1280
            TargetHeight      = 720
            InternalScale     = 1
            Anisotropic       = 4
            VSync             = $true
            Backend           = 'auto'
            ShaderCache       = $true
            TextureFiltering  = 'nearest'
        }
        'MidRange' = [ordered]@{
            Description       = 'Mid-range systems: 1080p output with 2x internal scaling.'
            TargetWidth       = 1920
            TargetHeight      = 1080
            InternalScale     = 2
            Anisotropic       = 8
            VSync             = $true
            Backend           = 'vulkan'
            ShaderCache       = $true
            TextureFiltering  = 'bilinear'
        }
        'HighEnd' = [ordered]@{
            Description       = 'High-end systems: 1440p+ output with 4x internal scaling, 16x AF.'
            TargetWidth       = 2560
            TargetHeight      = 1440
            InternalScale     = 4
            Anisotropic       = 16
            VSync             = $true
            Backend           = 'vulkan'
            ShaderCache       = $true
            TextureFiltering  = 'bilinear'
        }
        'FourK' = [ordered]@{
            Description       = '4K systems: native 3840x2160 output, maximum safe internal scaling.'
            TargetWidth       = 3840
            TargetHeight      = 2160
            InternalScale     = 6
            Anisotropic       = 16
            VSync             = $true
            Backend           = 'vulkan'
            ShaderCache       = $true
            TextureFiltering  = 'bilinear'
        }
    }
}

function Save-Profiles {
    <#
    .SYNOPSIS
        Persists all profile definitions to JSON files under the profiles folder.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)] [string] $ProfilesDir,
        [Parameter(Mandatory = $true)] [scriptblock] $Logger
    )

    if (-not (Test-Path -LiteralPath $ProfilesDir)) {
        New-Item -Path $ProfilesDir -ItemType Directory -Force | Out-Null
    }

    $defs = Get-ProfileDefinitions
    foreach ($tier in $defs.Keys) {
        $path = Join-Path $ProfilesDir ("{0}.json" -f $tier)
        ($defs[$tier] | ConvertTo-Json -Depth 10) | Set-Content -LiteralPath $path -Encoding UTF8
        & $Logger "Profile written: $path" 'INFO'
    }
    return $defs
}

function Select-ProfileForHardware {
    <#
    .SYNOPSIS
        Returns the profile definition matching the hardware's resolved tier,
        adjusting the target resolution to the actual display when smaller.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)] [System.Collections.Specialized.OrderedDictionary] $Hardware,
        [Parameter(Mandatory = $true)] [scriptblock] $Logger
    )

    $defs    = Get-ProfileDefinitions
    $tier    = $Hardware.Tier
    if (-not $defs.Contains($tier)) { $tier = 'MidRange' }
    $profile = $defs[$tier]

    # Clamp target resolution to the actual panel if it is smaller than the tier
    # default (never upscale output beyond what the display supports).
    if ($Hardware.DisplayWidth -gt 0 -and $Hardware.DisplayWidth -lt $profile.TargetWidth) {
        $profile.TargetWidth  = $Hardware.DisplayWidth
        $profile.TargetHeight = $Hardware.DisplayHeight
    }

    & $Logger "Selected profile '$tier' -> $($profile.TargetWidth)x$($profile.TargetHeight), scale $($profile.InternalScale)x." 'SUCCESS'
    return @{ Tier = $tier; Profile = $profile }
}

Export-ModuleMember -Function Get-ProfileDefinitions, Save-Profiles, Select-ProfileForHardware
