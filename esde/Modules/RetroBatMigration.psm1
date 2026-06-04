<#
.SYNOPSIS
    RetroBat -> ES-DE migration engine.
.DESCRIPTION
    Detects RetroBat media layouts (roms\<system>\images|videos|manuals|media|...
    plus gamelist.xml media references) and migrates every asset into the ES-DE
    downloaded_media\<system>\<type> structure, matching files to ROMs by stem and
    classifying media by gamelist tag, source folder and filename. Existing,
    identical destination files are skipped; differing ones are backed up first.
    No source data is ever deleted (copy, not move).
#>

Set-StrictMode -Version Latest

function Test-RetroBatMediaLayout {
    <#
    .SYNOPSIS
        Returns $true if a system folder looks like it holds RetroBat-style media
        (recognised media sub-folders or a gamelist.xml with media references).
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][string] $SystemRomDir)
    if (-not (Test-Path -LiteralPath $SystemRomDir)) { return $false }
    $hintFolders = @('images','media','videos','manuals','fanart','marquees','wheels',
                     'screenshots','boxart','box3d','thumbnails','supports','downloaded_images')
    foreach ($h in $hintFolders) {
        if (Test-Path -LiteralPath (Join-Path $SystemRomDir $h)) { return $true }
    }
    if (Test-Path -LiteralPath (Join-Path $SystemRomDir 'gamelist.xml')) { return $true }
    return $false
}

function Invoke-SystemMigration {
    <#
    .SYNOPSIS
        Migrates a single system's RetroBat media into ES-DE downloaded_media.
    .OUTPUTS
        Hashtable of statistics.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string]   $SystemRomDir,     # roms\<system>
        [Parameter(Mandatory = $true)][string]   $SystemMediaDir,   # downloaded_media\<system>
        [Parameter(Mandatory = $true)][object]   $Definitions,
        [Parameter(Mandatory = $true)][string]   $BackupRoot,
        [Parameter(Mandatory = $true)][scriptblock] $Logger,
        [switch] $DryRun
    )

    $stats = @{ FromGamelist = 0; FromFolders = 0; Skipped = 0; Errors = 0 }
    if (-not (Test-Path -LiteralPath $SystemRomDir)) { return $stats }

    $tagMap    = ConvertTo-Hashtable $Definitions.gamelistTagToEsdeFolder
    $folderMap = ConvertTo-Hashtable $Definitions.sourceFolderToEsdeFolder

    # ---- 1) Migrate media referenced by gamelist.xml (most reliable) ----
    $gl = Join-Path $SystemRomDir 'gamelist.xml'
    if (Test-Path -LiteralPath $gl) {
        $parsed = Read-Gamelist -Path $gl
        if ($parsed.Ok) {
            foreach ($game in @($parsed.Games)) {
                $pathNode = $game.SelectSingleNode('path')
                if (-not $pathNode) { continue }
                $romStem = [System.IO.Path]::GetFileNameWithoutExtension($pathNode.InnerText)
                foreach ($tag in (Get-GameMediaTags)) {
                    $node = $game.SelectSingleNode($tag)
                    if (-not $node -or [string]::IsNullOrWhiteSpace($node.InnerText)) { continue }
                    $src = Resolve-RelativeMediaPath -BaseDir $SystemRomDir -RelPath $node.InnerText
                    if (-not (Test-Path -LiteralPath $src)) { continue }
                    $folder = if ($tagMap.ContainsKey($tag.ToLower())) { $tagMap[$tag.ToLower()] } else { $null }
                    if (-not $folder) { continue }
                    $ext  = [System.IO.Path]::GetExtension($src)
                    $dest = Join-Path (Join-Path $SystemMediaDir $folder) ($romStem + $ext)
                    $r = Copy-MediaSafe -Source $src -Dest $dest -BackupRoot $BackupRoot -DryRun:$DryRun
                    if ($r -in @('copied','overwritten')) { $stats.FromGamelist++ }
                    elseif ($r -eq 'error') { $stats.Errors++ }
                    else { $stats.Skipped++ }
                }
            }
        } else {
            & $Logger "Could not parse RetroBat gamelist: $gl ($($parsed.Error))" 'WARN'
        }
    }

    # ---- 2) Migrate loose media folders (images\, videos\, media\<type>\ ...) ----
    foreach ($dir in (Get-ChildItem -LiteralPath $SystemRomDir -Directory -ErrorAction SilentlyContinue)) {
        $name = $dir.Name.ToLower()
        if ($name -eq 'media') {
            # Batocera/RetroBat "media" holds typed sub-folders (box2dfront, etc.).
            foreach ($sub in (Get-ChildItem -LiteralPath $dir.FullName -Directory -ErrorAction SilentlyContinue)) {
                Move-FolderMedia -SrcDir $sub.FullName -SrcFolderName $sub.Name -SystemMediaDir $SystemMediaDir `
                    -Definitions $Definitions -BackupRoot $BackupRoot -Stats $stats -DryRun:$DryRun
            }
            continue
        }
        if ($folderMap.ContainsKey($name) -or $folderMap.ContainsKey(($name -replace 's$',''))) {
            Move-FolderMedia -SrcDir $dir.FullName -SrcFolderName $dir.Name -SystemMediaDir $SystemMediaDir `
                -Definitions $Definitions -BackupRoot $BackupRoot -Stats $stats -DryRun:$DryRun
        }
    }

    & $Logger "Migrated $(Split-Path $SystemRomDir -Leaf): $($stats.FromGamelist) via gamelist, $($stats.FromFolders) via folders, $($stats.Skipped) skipped." 'SUCCESS'
    return $stats
}

function Move-FolderMedia {
    <#
    .SYNOPSIS
        Copies every media file from a RetroBat media sub-folder into the correct
        ES-DE media subfolder, classifying each file. Updates $Stats by reference.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string]   $SrcDir,
        [Parameter(Mandatory = $true)][string]   $SrcFolderName,
        [Parameter(Mandatory = $true)][string]   $SystemMediaDir,
        [Parameter(Mandatory = $true)][object]   $Definitions,
        [Parameter(Mandatory = $true)][string]   $BackupRoot,
        [Parameter(Mandatory = $true)][hashtable] $Stats,
        [switch] $DryRun
    )
    Get-ChildItem -LiteralPath $SrcDir -File -Recurse -ErrorAction SilentlyContinue | ForEach-Object {
        $cls = Get-MediaClassification -FilePath $_.FullName -Definitions $Definitions -SourceFolderName $SrcFolderName
        if (-not $cls.EsdeFolder) { $Stats.Skipped++; return }
        # Normalise the destination name: strip a scraper suffix so it matches the ROM stem.
        $stem = [System.IO.Path]::GetFileNameWithoutExtension($_.Name)
        $stem = ($stem -replace '(-image|-thumb|-thumbnail|-boxart|-box2dfront|-cover|-marquee|-wheel|-logo|-fanart|-video|-manual|-title|-titleshot|-screenshot|-ss|-mix|-cart|-cartridge|-disc|-box3d|-boxback|-backcover)$', '')
        $dest = Join-Path (Join-Path $SystemMediaDir $cls.EsdeFolder) ($stem + $_.Extension)
        $r = Copy-MediaSafe -Source $_.FullName -Dest $dest -BackupRoot $BackupRoot -DryRun:$DryRun
        if ($r -in @('copied','overwritten')) { $Stats.FromFolders++ }
        elseif ($r -eq 'error') { $Stats.Errors++ }
        else { $Stats.Skipped++ }
    }
}

Export-ModuleMember -Function Test-RetroBatMediaLayout, Invoke-SystemMigration, Move-FolderMedia
