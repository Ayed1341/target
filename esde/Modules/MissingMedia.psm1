<#
.SYNOPSIS
    Missing-media analyzer and BIOS validator.
.DESCRIPTION
    For every game in a system (resolved from the gamelist or the ROM files),
    determines which ES-DE media types are missing (covers, screenshots, videos,
    marquees, fanart, manuals, titlescreens) by checking downloaded_media by stem.
    Also validates BIOS folders against a known requirement table (report only).
#>

Set-StrictMode -Version Latest

# Media types considered "important" for the missing-media report.
$script:ReportTypes = @('covers','screenshots','videos','marquees','fanart','titlescreens','manuals')

# ROM extensions to ignore when enumerating games from the filesystem.
$script:NonRomExt = @('.txt','.xml','.dat','.cfg','.ini','.jpg','.png','.bin','.cue','.m3u','.srm','.state')

function Get-SystemGameStems {
    <#
    .SYNOPSIS
        Returns the set of game "stems" (ROM file names without extension) for a
        system, preferring gamelist paths and falling back to the ROM folder.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string] $SystemRomDir,
        [string] $GamelistPath
    )
    $stems = New-Object System.Collections.Generic.HashSet[string] ([StringComparer]::OrdinalIgnoreCase)

    if ($GamelistPath -and (Test-Path -LiteralPath $GamelistPath)) {
        $g = Read-Gamelist -Path $GamelistPath
        if ($g.Ok) {
            foreach ($game in @($g.Games)) {
                $pn = $game.SelectSingleNode('path')
                if ($pn -and $pn.InnerText) { [void]$stems.Add([System.IO.Path]::GetFileNameWithoutExtension($pn.InnerText)) }
            }
        }
    }
    if ($stems.Count -eq 0 -and (Test-Path -LiteralPath $SystemRomDir)) {
        Get-ChildItem -LiteralPath $SystemRomDir -File -ErrorAction SilentlyContinue | ForEach-Object {
            if ($_.Extension.ToLower() -in $script:NonRomExt) { return }
            [void]$stems.Add([System.IO.Path]::GetFileNameWithoutExtension($_.Name))
        }
    }
    # Return with the unary comma so PowerShell does not enumerate the HashSet
    # (a single-element set would otherwise unroll to a bare string).
    return ,$stems
}

function Get-MissingMediaForSystem {
    <#
    .SYNOPSIS
        Returns per-game missing-media records for a system.
    .OUTPUTS
        Hashtable: System, Games(int), Records(array of @{Game;Missing[]}), Totals(hashtable by type)
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string] $SystemName,
        [Parameter(Mandatory = $true)][string] $SystemRomDir,
        [Parameter(Mandatory = $true)][string] $SystemMediaDir,
        [string] $GamelistPath
    )

    $stems = Get-SystemGameStems -SystemRomDir $SystemRomDir -GamelistPath $GamelistPath

    # Build presence index: type -> set of stems present.
    $present = @{}
    foreach ($t in $script:ReportTypes) {
        $present[$t] = New-Object System.Collections.Generic.HashSet[string] ([StringComparer]::OrdinalIgnoreCase)
        $dir = Join-Path $SystemMediaDir $t
        if (Test-Path -LiteralPath $dir) {
            Get-ChildItem -LiteralPath $dir -File -ErrorAction SilentlyContinue | ForEach-Object {
                [void]$present[$t].Add([System.IO.Path]::GetFileNameWithoutExtension($_.Name))
            }
        }
    }

    $records = New-Object System.Collections.Generic.List[object]
    $totals  = @{}; foreach ($t in $script:ReportTypes) { $totals[$t] = 0 }

    foreach ($stem in $stems) {
        $missing = New-Object System.Collections.Generic.List[string]
        foreach ($t in $script:ReportTypes) {
            if (-not $present[$t].Contains($stem)) { $missing.Add($t); $totals[$t]++ }
        }
        if ($missing.Count -gt 0) {
            $records.Add(@{ Game = $stem; Missing = $missing.ToArray() })
        }
    }

    return @{ System = $SystemName; Games = $stems.Count; Records = $records.ToArray(); Totals = $totals }
}

function Test-BiosDirectory {
    <#
    .SYNOPSIS
        Reports which known BIOS files are missing under a BIOS directory.
        Never deletes anything.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string] $BiosDir,
        [Parameter(Mandatory = $true)][object[]] $Requirements,
        [Parameter(Mandatory = $true)][scriptblock] $Logger
    )
    $issues = New-Object System.Collections.Generic.List[object]
    if (-not (Test-Path -LiteralPath $BiosDir)) {
        & $Logger "BIOS directory not found: $BiosDir" 'WARN'
        return @{ Dir = $BiosDir; Missing = $issues.ToArray(); Present = 0 }
    }
    $present = @{}
    Get-ChildItem -LiteralPath $BiosDir -Recurse -File -ErrorAction SilentlyContinue | ForEach-Object {
        $present[$_.Name.ToLower()] = $_.FullName
    }
    foreach ($req in $Requirements) {
        if (-not $present.ContainsKey($req.file.ToLower())) {
            & $Logger "Missing BIOS: $($req.file) (needed for $($req.system))" 'WARN'
            $issues.Add(@{ File = $req.file; System = $req.system })
        }
    }
    return @{ Dir = $BiosDir; Missing = $issues.ToArray(); Present = $present.Count }
}

Export-ModuleMember -Function Get-SystemGameStems, Get-MissingMediaForSystem, Test-BiosDirectory
