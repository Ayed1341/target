<#
.SYNOPSIS
    RetroArch playlist (.lpl) generation from a system's ROMs.
.DESCRIPTION
    Writes a RetroArch-format playlist per system into RetroArch\playlists so
    RetroArch can browse the library directly (core auto-detected at launch).
#>

Set-StrictMode -Version Latest

$script:LplNonRom = @('.txt','.xml','.dat','.jpg','.png','.bin','.srm','.state','.cfg','.sav','.cht','.m3u')

function New-RetroArchPlaylists {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][object[]] $Systems,
        [Parameter(Mandatory = $true)][string]   $RetroArchDir,
        [Parameter(Mandatory = $true)][scriptblock] $Logger,
        [switch] $DryRun
    )
    $plDir = Join-Path $RetroArchDir 'playlists'
    $created = 0
    foreach ($sys in $Systems) {
        if (-not (Test-Path -LiteralPath $sys.RomPath)) { continue }
        $items = New-Object System.Collections.Generic.List[object]
        Get-ChildItem -LiteralPath $sys.RomPath -File -ErrorAction SilentlyContinue | ForEach-Object {
            if ($script:LplNonRom -contains $_.Extension.ToLower()) { return }
            if ($_.Extension.ToLower() -eq '.bin' -and (Test-Path -LiteralPath ([System.IO.Path]::ChangeExtension($_.FullName,'cue')))) { return }
            $items.Add([ordered]@{
                path       = $_.FullName
                label      = [System.IO.Path]::GetFileNameWithoutExtension($_.Name)
                core_path  = 'DETECT'
                core_name  = 'DETECT'
                crc32      = '00000000|crc'
                db_name    = "$($sys.Name).lpl"
            })
        }
        if ($items.Count -eq 0) { continue }
        if ($DryRun) { & $Logger "[DRY-RUN] Would write $($sys.Name).lpl ($($items.Count) items)." 'INFO'; $created++; continue }
        if (-not (Test-Path -LiteralPath $plDir)) { New-Item -Path $plDir -ItemType Directory -Force | Out-Null }
        $playlist = [ordered]@{
            version            = '1.5'
            default_core_path  = ''
            default_core_name  = ''
            label_display_mode = 0
            right_thumbnail_mode = 0
            left_thumbnail_mode  = 0
            sort_mode          = 0
            items              = $items.ToArray()
        }
        ($playlist | ConvertTo-Json -Depth 6) | Set-Content -LiteralPath (Join-Path $plDir "$($sys.Name).lpl") -Encoding UTF8
        $created++
    }
    if ($created -gt 0 -and -not $DryRun) { & $Logger "Generated $created RetroArch playlist(s) in $plDir." 'SUCCESS' }
    return $created
}

Export-ModuleMember -Function New-RetroArchPlaylists
