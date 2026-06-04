<#
.SYNOPSIS
    Controller detection and auto-configuration module.
.DESCRIPTION
    Enumerates connected game controllers via PnP/HID, identifies vendor and
    product IDs, classifies the controller family (Xbox / PlayStation / Nintendo /
    generic XInput / DirectInput), and writes mappings for EmulationStation
    (es_input.cfg) and RetroArch (autoconfig profile) including standard hotkeys.
    Provides a hotswap watcher that reconfigures on connect and cleanly updates
    on disconnect.
#>

Set-StrictMode -Version Latest

function Get-ConnectedControllers {
    <#
    .SYNOPSIS
        Returns descriptor objects for connected game controllers.
    .DESCRIPTION
        Queries Win32_PnPEntity for present HID / XInput / game controller devices,
        extracts VID/PID and classifies each device.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)] [hashtable] $VendorMap
    )

    $controllers = New-Object System.Collections.Generic.List[object]
    $seen        = New-Object System.Collections.Generic.HashSet[string] ([StringComparer]::OrdinalIgnoreCase)

    try {
        $devices = Get-CimInstance -ClassName Win32_PnPEntity -ErrorAction Stop | Where-Object {
            $_.Present -ne $false -and (
                ($_.PNPClass -in @('HIDClass', 'XnaComposite', 'XboxComposite')) -or
                ($_.Name -match '(?i)controller|gamepad|joystick|xbox|wireless controller|dualshock|dualsense|pro controller')
            ) -and ($_.PNPDeviceID -match '(?i)VID_[0-9A-F]{4}')
        }
    } catch {
        $devices = @()
    }

    foreach ($d in $devices) {
        $id  = $d.PNPDeviceID
        # NOTE: do not use $pid here - it is a read-only PowerShell automatic
        # variable (the current process id) and assigning to it throws.
        $vendorId = $null; $productId = $null
        if ($id -match '(?i)VID_([0-9A-F]{4})') { $vendorId = $Matches[1].ToUpper() }
        if ($id -match '(?i)PID_([0-9A-F]{4})') { $productId = $Matches[1].ToUpper() }
        if (-not $vendorId) { continue }

        # Deduplicate on VID+PID (composite devices expose multiple PnP nodes).
        $key = "${vendorId}:${productId}"
        if ($seen.Contains($key)) { continue }
        [void]$seen.Add($key)

        $vendor = if ($vendorId -and $VendorMap.ContainsKey($vendorId)) { $VendorMap[$vendorId] } else { 'Unknown vendor' }
        $family = Get-ControllerFamily -Vid $vendorId -Name $d.Name -PnpId $id
        $conn   = Get-ControllerConnection -PnpId $id
        $friendly = Get-ControllerFriendlyName -Name $d.Name -Family $family -Vendor $vendor

        $controllers.Add([pscustomobject]@{
            Name       = $d.Name
            FriendlyName = $friendly
            Vid        = $vendorId
            Pid        = $productId
            Vendor     = $vendor
            Family     = $family
            ApiType    = (Get-ControllerApiType -PnpId $id -Family $family)
            Connection = $conn
            PnpId      = $id
        })
    }

    return $controllers.ToArray()
}

function Get-ControllerFamily {
    param([string] $Vid, [string] $Name, [string] $PnpId)
    $n = ($Name + ' ' + $PnpId).ToLower()
    switch ($Vid) {
        '045E' { return 'Xbox' }
        '054C' { return 'PlayStation' }
        '057E' { return 'Nintendo' }
        '28DE' { return 'Steam' }
        '2DC8' { if ($n -match 'xbox|xinput') { return 'Xbox' } else { return '8BitDo' } }
    }
    if ($n -match 'xbox|xinput')                 { return 'Xbox' }
    if ($n -match 'dualshock|dualsense|playstation') { return 'PlayStation' }
    if ($n -match 'switch|pro controller|joy-con') { return 'Nintendo' }
    return 'Generic'
}

function Get-ControllerApiType {
    param([string] $PnpId, [string] $Family)
    if ($PnpId -match '(?i)IG_') { return 'XInput' }     # IG_ marks XInput devices
    if ($Family -eq 'Xbox')      { return 'XInput' }
    return 'DirectInput'
}

function Get-ControllerConnection {
    <#
    .SYNOPSIS
        Determines whether a controller is connected over Bluetooth or USB based
        on its PnP device id enumerator prefix.
    #>
    param([string] $PnpId)
    if ($PnpId -match '(?i)^BTHLE')    { return 'Bluetooth LE' }
    if ($PnpId -match '(?i)^BTHENUM')  { return 'Bluetooth' }
    if ($PnpId -match '(?i)^BTH')      { return 'Bluetooth' }
    if ($PnpId -match '(?i)^USB')      { return 'USB' }
    if ($PnpId -match '(?i)^HID')      { return 'HID (USB)' }
    return 'Unknown'
}

function Get-ControllerFriendlyName {
    <#
    .SYNOPSIS
        Builds a readable controller label from family + vendor when the raw HID
        name is generic (e.g. "USB Input Device").
    #>
    param([string] $Name, [string] $Family, [string] $Vendor)
    if ($Name -match '(?i)^(usb input device|hid-compliant.*|hid game.*|usb gamepad)$' -or [string]::IsNullOrWhiteSpace($Name)) {
        $label = switch ($Family) {
            'Xbox'        { 'Xbox-compatible controller' }
            'PlayStation' { 'PlayStation-compatible controller' }
            'Nintendo'    { 'Nintendo-compatible controller' }
            '8BitDo'      { '8BitDo controller' }
            default       { 'Generic controller' }
        }
        if ($Vendor -and $Vendor -ne 'Unknown vendor') { $label = "$label ($Vendor)" }
        return $label
    }
    return $Name
}

function Get-ControllerInputProfile {
    <#
    .SYNOPSIS
        Returns the standard SDL/RetroArch button index map for a controller family.
        Indices follow the SDL GameController convention used by RetroArch & ES.
    #>
    param([string] $Family)

    # Base XInput / SDL standard layout.
    $base = [ordered]@{
        a = 0; b = 1; x = 2; y = 3
        leftshoulder = 4; rightshoulder = 5
        back = 6; start = 7
        leftstick = 8; rightstick = 9
        dpup = 11; dpdown = 12; dpleft = 13; dpright = 14
        guide = 10
    }

    switch ($Family) {
        'Nintendo' {
            # Nintendo physical A/B and X/Y are swapped relative to XInput layout.
            $base.a = 1; $base.b = 0; $base.x = 3; $base.y = 2
        }
        default { }
    }
    return $base
}

function Write-RetroArchControllerProfile {
    <#
    .SYNOPSIS
        Writes a RetroArch autoconfig .cfg for a controller, including hotkeys.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)] [object] $Controller,
        [Parameter(Mandatory = $true)] [string] $AutoconfigDir,
        [Parameter(Mandatory = $true)] [scriptblock] $Logger
    )

    if (-not (Test-Path -LiteralPath $AutoconfigDir)) {
        New-Item -Path $AutoconfigDir -ItemType Directory -Force | Out-Null
    }

    $profile  = Get-ControllerInputProfile -Family $Controller.Family
    $driver   = if ($Controller.ApiType -eq 'XInput') { 'xinput' } else { 'dinput' }
    $safeName = ($Controller.Name -replace '[\\/:*?"<>|]', '_').Trim()
    # Unique filename per device (VID/PID) so multiple generic "USB Input Device"
    # pads do not overwrite each other's profile.
    $pidPart  = if ($Controller.Pid) { $Controller.Pid } else { '0000' }
    $file     = Join-Path $AutoconfigDir ("{0}_{1}_{2}.cfg" -f $safeName, $Controller.Vid, $pidPart)

    $lines = @()
    $lines += 'input_driver = "' + $driver + '"'
    $lines += 'input_device = "' + $Controller.Name + '"'
    $lines += 'input_vendor_id = "' + [Convert]::ToInt32($Controller.Vid, 16) + '"'
    if ($Controller.Pid) {
        $lines += 'input_product_id = "' + [Convert]::ToInt32($Controller.Pid, 16) + '"'
    }
    # Face buttons / shoulders / sticks.
    $lines += 'input_a_btn = "' + $profile.a + '"'
    $lines += 'input_b_btn = "' + $profile.b + '"'
    $lines += 'input_x_btn = "' + $profile.x + '"'
    $lines += 'input_y_btn = "' + $profile.y + '"'
    $lines += 'input_l_btn = "' + $profile.leftshoulder + '"'
    $lines += 'input_r_btn = "' + $profile.rightshoulder + '"'
    $lines += 'input_select_btn = "' + $profile.back + '"'
    $lines += 'input_start_btn = "' + $profile.start + '"'
    $lines += 'input_l3_btn = "' + $profile.leftstick + '"'
    $lines += 'input_r3_btn = "' + $profile.rightstick + '"'
    $lines += 'input_up_btn = "' + $profile.dpup + '"'
    $lines += 'input_down_btn = "' + $profile.dpdown + '"'
    $lines += 'input_left_btn = "' + $profile.dpleft + '"'
    $lines += 'input_right_btn = "' + $profile.dpright + '"'
    # Analog axes (standard XInput/SDL axis ordering).
    $lines += 'input_l_x_plus_axis = "+0"'
    $lines += 'input_l_x_minus_axis = "-0"'
    $lines += 'input_l_y_plus_axis = "+1"'
    $lines += 'input_l_y_minus_axis = "-1"'
    $lines += 'input_r_x_plus_axis = "+2"'
    $lines += 'input_r_x_minus_axis = "-2"'
    $lines += 'input_r_y_plus_axis = "+3"'
    $lines += 'input_r_y_minus_axis = "-3"'
    $lines += 'input_l2_axis = "+4"'
    $lines += 'input_r2_axis = "+5"'
    # Hotkeys: hold Select(=back) as enable, then face/shoulder combos.
    $lines += 'input_enable_hotkey_btn = "' + $profile.back + '"'
    $lines += 'input_exit_emulator_btn = "' + $profile.start + '"'
    $lines += 'input_menu_toggle_btn = "' + $profile.guide + '"'
    $lines += 'input_save_state_btn = "' + $profile.a + '"'
    $lines += 'input_load_state_btn = "' + $profile.y + '"'
    $lines += 'input_state_slot_increase_btn = "' + $profile.dpright + '"'
    $lines += 'input_state_slot_decrease_btn = "' + $profile.dpleft + '"'
    $lines += 'input_screenshot_btn = "' + $profile.x + '"'
    $lines += 'input_toggle_fast_forward_btn = "' + $profile.rightshoulder + '"'

    [System.IO.File]::WriteAllLines($file, $lines, (New-Object System.Text.UTF8Encoding($false)))
    & $Logger "RetroArch profile written: $file ($($Controller.Family)/$driver)." 'SUCCESS'
    return $file
}

function Write-EmulationStationInput {
    <#
    .SYNOPSIS
        Writes / merges an es_input.cfg inputConfig block for a controller so
        EmulationStation recognizes the pad. Existing blocks for other devices
        are preserved; a matching block (by deviceGUID) is replaced.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)] [object[]] $Controllers,
        [Parameter(Mandatory = $true)] [string]   $EsInputPath,
        [Parameter(Mandatory = $true)] [string]   $BackupRoot,
        [Parameter(Mandatory = $true)] [scriptblock] $Logger
    )

    New-ConfigBackup -Path $EsInputPath -BackupRoot $BackupRoot | Out-Null

    $dir = Split-Path $EsInputPath -Parent
    if ($dir -and -not (Test-Path -LiteralPath $dir)) {
        New-Item -Path $dir -ItemType Directory -Force | Out-Null
    }

    $sb = New-Object System.Text.StringBuilder
    [void]$sb.AppendLine('<?xml version="1.0"?>')
    [void]$sb.AppendLine('<inputList>')

    foreach ($c in $Controllers) {
        $profile = Get-ControllerInputProfile -Family $c.Family
        $guid    = New-DeterministicGuid -Seed ("$($c.Vid):$($c.Pid):$($c.Family)")
        $devName = [Security.SecurityElement]::Escape($c.Name)

        [void]$sb.AppendLine(('  <inputConfig type="joystick" deviceName="{0}" deviceGUID="{1}">' -f $devName, $guid))
        [void]$sb.AppendLine(('    <input name="a" type="button" id="{0}" value="1" />' -f $profile.a))
        [void]$sb.AppendLine(('    <input name="b" type="button" id="{0}" value="1" />' -f $profile.b))
        [void]$sb.AppendLine(('    <input name="x" type="button" id="{0}" value="1" />' -f $profile.x))
        [void]$sb.AppendLine(('    <input name="y" type="button" id="{0}" value="1" />' -f $profile.y))
        [void]$sb.AppendLine(('    <input name="pageup" type="button" id="{0}" value="1" />' -f $profile.leftshoulder))
        [void]$sb.AppendLine(('    <input name="pagedown" type="button" id="{0}" value="1" />' -f $profile.rightshoulder))
        [void]$sb.AppendLine(('    <input name="select" type="button" id="{0}" value="1" />' -f $profile.back))
        [void]$sb.AppendLine(('    <input name="start" type="button" id="{0}" value="1" />' -f $profile.start))
        [void]$sb.AppendLine(('    <input name="leftthumb" type="button" id="{0}" value="1" />' -f $profile.leftstick))
        [void]$sb.AppendLine(('    <input name="rightthumb" type="button" id="{0}" value="1" />' -f $profile.rightstick))
        [void]$sb.AppendLine(('    <input name="hotkeyenable" type="button" id="{0}" value="1" />' -f $profile.back))
        [void]$sb.AppendLine( '    <input name="up" type="axis" id="1" value="-1" />')
        [void]$sb.AppendLine( '    <input name="down" type="axis" id="1" value="1" />')
        [void]$sb.AppendLine( '    <input name="left" type="axis" id="0" value="-1" />')
        [void]$sb.AppendLine( '    <input name="right" type="axis" id="0" value="1" />')
        [void]$sb.AppendLine( '    <input name="joystick1up" type="axis" id="1" value="-1" />')
        [void]$sb.AppendLine( '    <input name="joystick1left" type="axis" id="0" value="-1" />')
        [void]$sb.AppendLine( '    <input name="joystick2up" type="axis" id="3" value="-1" />')
        [void]$sb.AppendLine( '    <input name="joystick2left" type="axis" id="2" value="-1" />')
        [void]$sb.AppendLine( '    <input name="lefttrigger" type="axis" id="4" value="1" />')
        [void]$sb.AppendLine( '    <input name="righttrigger" type="axis" id="5" value="1" />')
        [void]$sb.AppendLine( '  </inputConfig>')
    }

    [void]$sb.AppendLine('</inputList>')
    [System.IO.File]::WriteAllText($EsInputPath, $sb.ToString(), (New-Object System.Text.UTF8Encoding($false)))
    & $Logger "EmulationStation input written for $($Controllers.Count) controller(s): $EsInputPath" 'SUCCESS'
    return $EsInputPath
}

function New-DeterministicGuid {
    <#
    .SYNOPSIS
        Produces a stable GUID from a seed string (MD5-based) so the same
        controller always maps to the same deviceGUID across runs.
    #>
    param([string] $Seed)
    $md5   = [System.Security.Cryptography.MD5]::Create()
    $bytes = $md5.ComputeHash([System.Text.Encoding]::UTF8.GetBytes($Seed))
    $guid  = [Guid]::new($bytes)
    return $guid.ToString('N')
}

function Get-ControllerSignature {
    <#
    .SYNOPSIS
        Returns a stable signature string for the current set of controllers,
        used by the hotswap watcher to detect connect/disconnect transitions.
    #>
    param([object[]] $Controllers)
    if (-not $Controllers -or $Controllers.Count -eq 0) { return '' }
    return (($Controllers | ForEach-Object { "$($_.Vid):$($_.Pid)" } | Sort-Object) -join '|')
}

function Get-SdlGuid {
    <#
    .SYNOPSIS
        Builds an SDL2 controller GUID (Windows layout) from VID/PID and bus type.
        Layout (16 bytes, little-endian fields): bus, crc(0), vendor, 0, product, 0,
        version(0), 0 - matching the format used by SDL_GameControllerDB.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string] $Vid,
        [string] $Pid = '0000',
        [string] $Connection = 'USB'
    )
    function leHex([string]$h) {
        $h = ($h.PadLeft(4,'0')).Substring(0,4)
        return ($h.Substring(2,2) + $h.Substring(0,2)).ToLower()
    }
    $bus = if ($Connection -match '(?i)bluetooth') { '0500' } else { '0300' }
    $v = leHex $Vid
    $p = if ($Pid) { leHex $Pid } else { '0000' }
    return ($bus + '0000' + $v + '0000' + $p + '0000' + '00000000').ToLower()
}

function New-SdlMappingLine {
    <#
    .SYNOPSIS
        Produces an SDL_GameControllerDB mapping line for a controller using its
        family's standard button layout. Universal across SDL-based emulators
        (RetroArch, DuckStation, PCSX2, PPSSPP, Flycast, ...).
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][object] $Controller)
    $p    = Get-ControllerInputProfile -Family $Controller.Family
    $guid = Get-SdlGuid -Vid $Controller.Vid -Pid $Controller.Pid -Connection $Controller.Connection
    $name = ($Controller.FriendlyName -replace ',', ' ')
    $map  = @(
        "a:b$($p.a)","b:b$($p.b)","x:b$($p.x)","y:b$($p.y)",
        "back:b$($p.back)","start:b$($p.start)","guide:b$($p.guide)",
        "leftshoulder:b$($p.leftshoulder)","rightshoulder:b$($p.rightshoulder)",
        "leftstick:b$($p.leftstick)","rightstick:b$($p.rightstick)",
        "dpup:b$($p.dpup)","dpdown:b$($p.dpdown)","dpleft:b$($p.dpleft)","dpright:b$($p.dpright)",
        "leftx:a0","lefty:a1","rightx:a2","righty:a3","lefttrigger:a4","righttrigger:a5",
        "platform:Windows"
    )
    return ('{0},{1},{2},' -f $guid, $name, ($map -join ','))
}

function Write-GameControllerDb {
    <#
    .SYNOPSIS
        Writes/updates an SDL gamecontrollerdb.txt with one mapping per controller,
        replacing any existing line for the same GUID and preserving the rest.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][object[]] $Controllers,
        [Parameter(Mandatory = $true)][string]   $Path,
        [Parameter(Mandatory = $true)][scriptblock] $Logger
    )
    $dir = Split-Path $Path -Parent
    if ($dir -and -not (Test-Path -LiteralPath $dir)) { New-Item -Path $dir -ItemType Directory -Force | Out-Null }

    $existing = @()
    if (Test-Path -LiteralPath $Path) { $existing = @(Get-Content -LiteralPath $Path -Encoding UTF8) }

    $byGuid = [ordered]@{}
    foreach ($line in $existing) {
        if ($line -match '^[0-9a-fA-F]{32},') { $byGuid[$line.Substring(0,32).ToLower()] = $line }
        elseif ($line.Trim().Length -gt 0 -and -not $line.StartsWith('#')) { } # drop malformed
    }
    $added = 0
    foreach ($c in $Controllers) {
        $line = New-SdlMappingLine -Controller $c
        $guid = $line.Substring(0,32).ToLower()
        $byGuid[$guid] = $line
        $added++
    }
    $out = @('# SDL Game Controller DB - generated by ES-DE Auto Suite') + @($byGuid.Values)
    [System.IO.File]::WriteAllLines($Path, $out, (New-Object System.Text.UTF8Encoding($false)))
    & $Logger "Wrote $added controller mapping(s) to $Path" 'SUCCESS'
    return $Path
}

Export-ModuleMember -Function `
    Get-ConnectedControllers, Get-ControllerFamily, Get-ControllerApiType, `
    Get-ControllerConnection, Get-ControllerFriendlyName, `
    Get-ControllerInputProfile, Write-RetroArchControllerProfile, `
    Write-EmulationStationInput, New-DeterministicGuid, Get-ControllerSignature, `
    Get-SdlGuid, New-SdlMappingLine, Write-GameControllerDb
