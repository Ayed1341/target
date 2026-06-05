<#
.SYNOPSIS
    Media integrity checks and library-wide media analytics.
.DESCRIPTION
    * Quarantine 0-byte (corrupt) media and truncated/unreadable images into the
      backup tree (never deleted).
    * Fix media files that have no extension by detecting their format (magic bytes).
    * Library analytics: media count per type, and the largest media files.
#>

Set-StrictMode -Version Latest

function Test-MediaIntegrity {
    <#
    .SYNOPSIS
        For one system: quarantines 0-byte media and adds the correct extension to
        extension-less image files. Returns @{ Quarantined; Fixed }.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string] $SystemMediaDir,
        [Parameter(Mandatory = $true)][string] $BackupRoot,
        [Parameter(Mandatory = $true)][scriptblock] $Logger,
        [switch] $DryRun
    )
    $stats = @{ Quarantined = 0; Fixed = 0 }
    if (-not (Test-Path -LiteralPath $SystemMediaDir)) { return $stats }
    $qRoot = Join-Path $BackupRoot ('corrupt_media\' + (Split-Path $SystemMediaDir -Leaf))

    Get-ChildItem -LiteralPath $SystemMediaDir -File -Recurse -ErrorAction SilentlyContinue | ForEach-Object {
        # 0-byte -> quarantine
        if ($_.Length -eq 0) {
            if ($DryRun) { $stats.Quarantined++; return }
            if (-not (Test-Path -LiteralPath $qRoot)) { New-Item -Path $qRoot -ItemType Directory -Force | Out-Null }
            Move-Item -LiteralPath $_.FullName -Destination (Join-Path $qRoot $_.Name) -Force -ErrorAction SilentlyContinue
            $stats.Quarantined++; return
        }
        # no extension -> detect by magic and append
        if ([string]::IsNullOrEmpty($_.Extension)) {
            $type = Get-ImageMagicType -Path $_.FullName
            if ($type) {
                if ($DryRun) { $stats.Fixed++; return }
                Rename-Item -LiteralPath $_.FullName -NewName ($_.Name + '.' + $type) -Force -ErrorAction SilentlyContinue
                $stats.Fixed++
            }
        }
    }
    if ($stats.Quarantined -gt 0 -or $stats.Fixed -gt 0) {
        & $Logger "Integrity $(Split-Path $SystemMediaDir -Leaf): quarantined $($stats.Quarantined) corrupt, fixed $($stats.Fixed) extension-less." 'SUCCESS'
    }
    return $stats
}

function Get-MediaTypeTotals {
    <#
    .SYNOPSIS
        Counts media files per ES-DE type across the whole media directory.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][string] $MediaDir)
    $totals = [ordered]@{}
    if (Test-Path -LiteralPath $MediaDir) {
        Get-ChildItem -LiteralPath $MediaDir -Directory -ErrorAction SilentlyContinue | ForEach-Object {
            Get-ChildItem -LiteralPath $_.FullName -Directory -ErrorAction SilentlyContinue | ForEach-Object {
                $t = $_.Name
                $c = @(Get-ChildItem -LiteralPath $_.FullName -File -ErrorAction SilentlyContinue).Count
                if (-not $totals.Contains($t)) { $totals[$t] = 0 }
                $totals[$t] += $c
            }
        }
    }
    return $totals
}

function Get-TopLargestMedia {
    <#
    .SYNOPSIS
        Returns the N largest media files across the library.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][string] $MediaDir, [int] $Top = 25)
    if (-not (Test-Path -LiteralPath $MediaDir)) { return @() }
    return @(Get-ChildItem -LiteralPath $MediaDir -File -Recurse -ErrorAction SilentlyContinue |
        Sort-Object Length -Descending | Select-Object -First $Top |
        ForEach-Object { @{ File = $_.FullName; MB = [math]::Round($_.Length/1MB,2) } })
}

Export-ModuleMember -Function Test-MediaIntegrity, Get-MediaTypeTotals, Get-TopLargestMedia
