<#
.SYNOPSIS
    Save-data protection: archives emulator save files / save states / memory cards
    (the most precious, irreplaceable user data) and reports orphaned saves.
.DESCRIPTION
    Never deletes anything. Copies known save locations into a timestamped archive
    under the backup tree so a bad emulator update or config change can't lose your
    progress. Also flags save files that no longer have a matching ROM.
#>

Set-StrictMode -Version Latest

# Folder names that typically hold saves/states/memory cards across emulators.
$script:SaveFolderNames = @('saves','states','savestates','memcards','memorycards','sav','battery','nand','saveData')
$script:SaveExtensions  = @('.srm','.sav','.state','.ss0','.ss1','.mcr','.mcd','.ps2','.gme','.dsv','.fs','.bsv')

function Backup-SaveData {
    <#
    .SYNOPSIS
        Archives save data found under the emulator roots and the ROM directory.
        Returns count of files archived.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string]   $RomDir,
        [string[]] $EmulatorRoots = @(),
        [Parameter(Mandatory = $true)][string]   $BackupRoot,
        [Parameter(Mandatory = $true)][scriptblock] $Logger,
        [switch] $DryRun
    )
    $stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
    $dest  = Join-Path $BackupRoot ("savedata_$stamp")
    $count = 0
    $roots = @(@($EmulatorRoots) + $RomDir | Where-Object { $_ -and (Test-Path -LiteralPath $_) } | Select-Object -Unique)

    foreach ($root in $roots) {
        # 1) Whole save/state folders.
        foreach ($folderName in $script:SaveFolderNames) {
            Get-ChildItem -LiteralPath $root -Directory -Recurse -Depth 4 -ErrorAction SilentlyContinue |
                Where-Object { $_.Name -ieq $folderName } | ForEach-Object {
                    $files = @(Get-ChildItem -LiteralPath $_.FullName -File -Recurse -ErrorAction SilentlyContinue)
                    foreach ($f in $files) {
                        if ($f.FullName.Length -gt 240) { continue }
                        if ($DryRun) { $count++; continue }
                        $rel = $f.FullName.Substring($root.Length).TrimStart('\','/')
                        $dst = Join-Path (Join-Path $dest (Split-Path $root -Leaf)) $rel
                        $dstDir = Split-Path $dst -Parent
                        if (-not (Test-Path -LiteralPath $dstDir)) { New-Item -Path $dstDir -ItemType Directory -Force | Out-Null }
                        Copy-Item -LiteralPath $f.FullName -Destination $dst -Force -ErrorAction SilentlyContinue
                        $count++
                    }
                }
        }
    }
    # 2) Loose save files sitting next to ROMs.
    if (Test-Path -LiteralPath $RomDir) {
        Get-ChildItem -LiteralPath $RomDir -File -Recurse -Depth 3 -ErrorAction SilentlyContinue |
            Where-Object { $script:SaveExtensions -contains $_.Extension.ToLower() } | ForEach-Object {
                if ($DryRun) { $count++; return }
                $rel = $_.FullName.Substring($RomDir.Length).TrimStart('\','/')
                $dst = Join-Path (Join-Path $dest 'roms') $rel
                $dstDir = Split-Path $dst -Parent
                if (-not (Test-Path -LiteralPath $dstDir)) { New-Item -Path $dstDir -ItemType Directory -Force | Out-Null }
                Copy-Item -LiteralPath $_.FullName -Destination $dst -Force -ErrorAction SilentlyContinue
                $count++
            }
    }
    if ($count -gt 0 -and -not $DryRun) { & $Logger "Archived $count save/state file(s) to $dest." 'SUCCESS' }
    elseif ($count -gt 0) { & $Logger "[DRY-RUN] Would archive $count save/state file(s)." 'INFO' }
    return $count
}

function Get-OrphanedSaves {
    <#
    .SYNOPSIS
        Returns save files (by stem) under the ROM dir that have no matching ROM.
        Report only - never deleted (saves are irreplaceable).
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][string] $SystemRomDir)
    $orphans = New-Object System.Collections.Generic.List[string]
    if (-not (Test-Path -LiteralPath $SystemRomDir)) { return @() }
    $romStems = New-Object System.Collections.Generic.HashSet[string] ([StringComparer]::OrdinalIgnoreCase)
    Get-ChildItem -LiteralPath $SystemRomDir -File -ErrorAction SilentlyContinue | ForEach-Object {
        if ($script:SaveExtensions -notcontains $_.Extension.ToLower()) {
            [void]$romStems.Add([System.IO.Path]::GetFileNameWithoutExtension($_.Name))
        }
    }
    Get-ChildItem -LiteralPath $SystemRomDir -File -Recurse -Depth 3 -ErrorAction SilentlyContinue |
        Where-Object { $script:SaveExtensions -contains $_.Extension.ToLower() } | ForEach-Object {
            $stem = [System.IO.Path]::GetFileNameWithoutExtension($_.Name)
            if (-not $romStems.Contains($stem)) { $orphans.Add($_.Name) }
        }
    return $orphans.ToArray()
}

Export-ModuleMember -Function Backup-SaveData, Get-OrphanedSaves
