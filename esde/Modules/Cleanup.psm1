<#
.SYNOPSIS
    Cleanup engine. Removes ONLY: orphaned media (media whose stem matches no ROM),
    empty media folders, and obsolete cache entries. Orphans are quarantined into
    the backup tree (never hard-deleted) so nothing is ever lost. ROMs, saves,
    BIOS and controller profiles are never touched.
#>

Set-StrictMode -Version Latest

function Invoke-OrphanCleanup {
    <#
    .SYNOPSIS
        Moves media files whose stem has no corresponding ROM into a quarantine
        folder under the backup root. Returns count quarantined.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string] $SystemName,
        [Parameter(Mandatory = $true)][string] $SystemRomDir,
        [Parameter(Mandatory = $true)][string] $SystemMediaDir,
        [Parameter(Mandatory = $true)][System.Collections.Generic.HashSet[string]] $RomStems,
        [Parameter(Mandatory = $true)][string] $BackupRoot,
        [Parameter(Mandatory = $true)][scriptblock] $Logger,
        [switch] $DryRun
    )
    $quarantined = 0
    if (-not (Test-Path -LiteralPath $SystemMediaDir)) { return 0 }
    if ($RomStems.Count -eq 0) {
        # No ROMs known: do not treat everything as orphaned (safety).
        & $Logger "Skipping orphan cleanup for '$SystemName' (no ROMs detected)." 'INFO'
        return 0
    }

    $qRoot = Join-Path $BackupRoot ("orphaned_media\{0}" -f $SystemName)
    Get-ChildItem -LiteralPath $SystemMediaDir -File -Recurse -ErrorAction SilentlyContinue | ForEach-Object {
        $stem = [System.IO.Path]::GetFileNameWithoutExtension($_.Name)
        if ($RomStems.Contains($stem)) { return }
        if ($DryRun) { & $Logger "[DRY-RUN] Would quarantine orphan: $($_.FullName)" 'INFO'; $quarantined++; return }
        $rel = $_.FullName.Substring($SystemMediaDir.Length).TrimStart('\','/')
        $dst = Join-Path $qRoot $rel
        $dstDir = Split-Path $dst -Parent
        if (-not (Test-Path -LiteralPath $dstDir)) { New-Item -Path $dstDir -ItemType Directory -Force | Out-Null }
        Move-Item -LiteralPath $_.FullName -Destination $dst -Force
        $quarantined++
    }
    if ($quarantined -gt 0) { & $Logger "Quarantined $quarantined orphan media file(s) for '$SystemName'." 'SUCCESS' }
    return $quarantined
}

function Remove-EmptyFolders {
    <#
    .SYNOPSIS
        Recursively removes empty directories under a root (deepest first).
        Returns count removed.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string] $Root,
        [switch] $DryRun
    )
    if (-not (Test-Path -LiteralPath $Root)) { return 0 }
    $removed = 0
    $dirs = Get-ChildItem -LiteralPath $Root -Directory -Recurse -ErrorAction SilentlyContinue |
            Sort-Object { $_.FullName.Length } -Descending
    foreach ($d in $dirs) {
        $hasChild = Get-ChildItem -LiteralPath $d.FullName -Force -ErrorAction SilentlyContinue | Select-Object -First 1
        if (-not $hasChild) {
            if ($DryRun) { $removed++; continue }
            Remove-Item -LiteralPath $d.FullName -Force -ErrorAction SilentlyContinue
            $removed++
        }
    }
    return $removed
}

function Get-CacheSize {
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][string] $CacheDir)
    if (-not (Test-Path -LiteralPath $CacheDir)) { return 0 }
    $sum = (Get-ChildItem -LiteralPath $CacheDir -File -Recurse -ErrorAction SilentlyContinue |
            Measure-Object -Property Length -Sum).Sum
    if (-not $sum) { return 0 }
    return [int64]$sum
}

Export-ModuleMember -Function Invoke-OrphanCleanup, Remove-EmptyFolders, Get-CacheSize
