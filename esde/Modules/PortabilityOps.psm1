<#
.SYNOPSIS
    Portability & ops: export controller config bundle, forecast media-download disk
    needs, detect network-share paths, and export a portable library bundle.
#>

Set-StrictMode -Version Latest

function Export-ControllerBundle {
    <#
    .SYNOPSIS
        Copies es_input.xml and every gamecontrollerdb.txt into one bundle folder so
        controller setup can be moved to another machine. Returns count.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][System.Collections.Specialized.OrderedDictionary] $Layout,
        [string[]] $EmulatorRoots = @(),
        [Parameter(Mandatory = $true)][string] $OutDir,
        [Parameter(Mandatory = $true)][scriptblock] $Logger,
        [switch] $DryRun
    )
    $count = 0
    $sources = New-Object System.Collections.Generic.List[string]
    $sources.Add($Layout.InputFile)
    $sources.Add((Join-Path $Layout.DataDir 'gamecontrollerdb.txt'))
    foreach ($r in $EmulatorRoots) { if ($r) { $sources.Add((Join-Path $r 'retroarch\gamecontrollerdb.txt')); $sources.Add((Join-Path $r 'retroarch\autoconfig')) } }
    if (-not $DryRun -and -not (Test-Path -LiteralPath $OutDir)) { New-Item -Path $OutDir -ItemType Directory -Force | Out-Null }
    foreach ($s in ($sources | Select-Object -Unique)) {
        if (-not $s -or -not (Test-Path -LiteralPath $s)) { continue }
        if ($DryRun) { $count++; continue }
        if (Test-Path -LiteralPath $s -PathType Container) {
            $dst = Join-Path $OutDir (Split-Path $s -Leaf)
            Copy-Item -LiteralPath $s -Destination $dst -Recurse -Force -ErrorAction SilentlyContinue
        } else {
            Copy-Item -LiteralPath $s -Destination (Join-Path $OutDir (Split-Path $s -Leaf)) -Force -ErrorAction SilentlyContinue
        }
        $count++
    }
    if ($count -gt 0 -and -not $DryRun) { & $Logger "Exported controller bundle ($count item(s)) to $OutDir." 'SUCCESS' }
    return $count
}

function Get-DiskSpaceForecast {
    <#
    .SYNOPSIS
        Estimates disk space needed to fill missing media, using average sizes of
        existing media of each type. Returns estimated MB.
    .PARAMETER MissingPerSystem
        From the report: array of @{ System; Totals=@{covers;videos;...} }.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string] $MediaDir,
        [Parameter(Mandatory = $true)][object[]] $MissingPerSystem
    )
    # Average size per media type from existing files.
    $avg = @{}
    if (Test-Path -LiteralPath $MediaDir) {
        Get-ChildItem -LiteralPath $MediaDir -Directory -ErrorAction SilentlyContinue | ForEach-Object {
            Get-ChildItem -LiteralPath $_.FullName -Directory -ErrorAction SilentlyContinue | ForEach-Object {
                $t = $_.Name.ToLower()
                $files = @(Get-ChildItem -LiteralPath $_.FullName -File -ErrorAction SilentlyContinue)
                if ($files.Count -eq 0) { return }
                $sum = 0; foreach ($f in $files) { $sum += $f.Length }
                if (-not $avg.ContainsKey($t)) { $avg[$t] = @{ Sum=0; N=0 } }
                $avg[$t].Sum += $sum; $avg[$t].N += $files.Count
            }
        }
    }
    $defaults = @{ covers=120KB; screenshots=80KB; videos=3MB; marquees=40KB; fanart=400KB; titlescreens=80KB; manuals=2MB }
    $totalBytes = [int64]0
    foreach ($ms in $MissingPerSystem) {
        foreach ($t in @('covers','screenshots','videos','marquees','fanart','titlescreens','manuals')) {
            $missing = 0; if ($ms.Totals -and $ms.Totals.$t) { $missing = [int]$ms.Totals.$t }
            if ($missing -le 0) { continue }
            $per = if ($avg.ContainsKey($t) -and $avg[$t].N -gt 0) { [int64]($avg[$t].Sum / $avg[$t].N) } else { [int64]$defaults[$t] }
            $totalBytes += ($per * $missing)
        }
    }
    return [math]::Round($totalBytes / 1MB, 1)
}

function Test-NetworkPaths {
    <#
    .SYNOPSIS
        Flags ROM/media directories that live on a network share (UNC or mapped),
        which can slow ES-DE. Returns the list of network paths found.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][string[]] $Paths)
    $net = New-Object System.Collections.Generic.List[string]
    foreach ($p in $Paths) {
        if (-not $p) { continue }
        if ($p.StartsWith('\\')) { $net.Add($p); continue }
        try {
            $root = [System.IO.Path]::GetPathRoot($p)
            if ($root -and (Test-Path -LiteralPath $root)) {
                $di = New-Object System.IO.DriveInfo($root)
                if ($di.DriveType -eq [System.IO.DriveType]::Network) { $net.Add($p) }
            }
        } catch { }
    }
    return $net.ToArray()
}

function Export-PortableBundle {
    <#
    .SYNOPSIS
        Writes a portable.json describing the install (data dir, rom dir, media dir,
        system list) so the configuration can be reproduced elsewhere. Returns path.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][System.Collections.Specialized.OrderedDictionary] $Layout,
        [Parameter(Mandatory = $true)][object[]] $Systems,
        [Parameter(Mandatory = $true)][string]   $OutFile
    )
    $data = @{
        generated = (Get-Date -Format o)
        dataDir   = $Layout.DataDir
        romDir    = $Layout.RomDir
        mediaDir  = $Layout.MediaDir
        esdeVersion = $Layout.Version
        systems   = @($Systems | ForEach-Object { @{ name=$_.Name; hasRoms=[bool]$_.HasRoms; hasGamelist=[bool]$_.HasGamelist; hasMedia=[bool]$_.HasMedia } })
    }
    $dir = Split-Path $OutFile -Parent
    if ($dir -and -not (Test-Path -LiteralPath $dir)) { New-Item -Path $dir -ItemType Directory -Force | Out-Null }
    ($data | ConvertTo-Json -Depth 6) | Set-Content -LiteralPath $OutFile -Encoding UTF8
    return $OutFile
}

Export-ModuleMember -Function Export-ControllerBundle, Get-DiskSpaceForecast, Test-NetworkPaths, Export-PortableBundle
