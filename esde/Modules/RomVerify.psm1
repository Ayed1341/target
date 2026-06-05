<#
.SYNOPSIS
    DAT-based ROM verification (No-Intro / Redump / MAME / clrmamepro XML DATs).
.DESCRIPTION
    If the user provides .dat files, ROMs are CRC32-checked against them and
    classified verified / unknown. Reports only - never deletes or renames.
    Looks for DATs in a 'dats' folder next to the ROM dir or under the work dir.
#>

Set-StrictMode -Version Latest

$script:VfNonRom = @('.txt','.xml','.dat','.jpg','.png','.srm','.state','.cfg','.sav','.cht','.m3u')

function Find-DatDirectory {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string] $RomDir,
        [Parameter(Mandatory = $true)][string] $WorkRoot
    )
    foreach ($c in @(
        (Join-Path (Split-Path $RomDir -Parent) 'dats'),
        (Join-Path $RomDir 'dats'),
        (Join-Path $WorkRoot 'dats')
    )) {
        if ($c -and (Test-Path -LiteralPath $c)) { return $c }
    }
    return $null
}

function Get-DatCrcSet {
    <#
    .SYNOPSIS
        Parses all .dat files in a directory and returns a set of known CRC32 values
        (uppercased) plus the number of game entries found.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][string] $DatDir)
    $crcs = New-Object System.Collections.Generic.HashSet[string] ([StringComparer]::OrdinalIgnoreCase)
    $games = 0
    if (-not (Test-Path -LiteralPath $DatDir)) { return @{ Crcs=$crcs; Games=0 } }
    Get-ChildItem -LiteralPath $DatDir -File -Filter '*.dat' -ErrorAction SilentlyContinue | ForEach-Object {
        try {
            $doc = New-Object System.Xml.XmlDocument
            $doc.Load($_.FullName)
            foreach ($rom in $doc.SelectNodes('//rom')) {
                $crc = $rom.GetAttribute('crc')
                if ($crc) { [void]$crcs.Add($crc.ToUpper().PadLeft(8,'0')); $games++ }
            }
        } catch { }
    }
    return @{ Crcs=$crcs; Games=$games }
}

function Test-RomsAgainstDat {
    <#
    .SYNOPSIS
        Verifies each system's ROMs against the DAT CRC set. Returns per-system
        @{ System; Verified; Unknown }.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][object[]] $Systems,
        [Parameter(Mandatory = $true)][System.Collections.Generic.HashSet[string]] $KnownCrcs,
        [Parameter(Mandatory = $true)][scriptblock] $Logger,
        [int] $MaxSizeMB = 256
    )
    $records = New-Object System.Collections.Generic.List[object]
    if ($KnownCrcs.Count -eq 0) { return @() }
    $limit = $MaxSizeMB * 1MB
    foreach ($sys in $Systems) {
        if (-not (Test-Path -LiteralPath $sys.RomPath)) { continue }
        $ok = 0; $unk = 0
        Get-ChildItem -LiteralPath $sys.RomPath -File -ErrorAction SilentlyContinue | ForEach-Object {
            if ($script:VfNonRom -contains $_.Extension.ToLower()) { return }
            if ($_.Length -gt $limit -or $_.Length -eq 0) { return }
            $crc = Get-FileCrc32 -Path $_.FullName
            if ($crc -and $KnownCrcs.Contains($crc)) { $ok++ } else { $unk++ }
        }
        if (($ok + $unk) -gt 0) { $records.Add(@{ System=$sys.Name; Verified=$ok; Unknown=$unk }) }
    }
    return $records.ToArray()
}

Export-ModuleMember -Function Find-DatDirectory, Get-DatCrcSet, Test-RomsAgainstDat
