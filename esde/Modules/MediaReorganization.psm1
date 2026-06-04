<#
.SYNOPSIS
    Media reorganization engine: creates the ES-DE media folder structure and
    moves misplaced / loose media files into their correct ES-DE subfolders.
#>

Set-StrictMode -Version Latest

function Get-FileSha256 {
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][string] $Path)
    try {
        $sha = [System.Security.Cryptography.SHA256]::Create()
        $fs  = [System.IO.File]::OpenRead($Path)
        try { return ([BitConverter]::ToString($sha.ComputeHash($fs))).Replace('-','') }
        finally { $fs.Dispose(); $sha.Dispose() }
    } catch { return $null }
}

function New-EsdeMediaFolders {
    <#
    .SYNOPSIS
        Creates every ES-DE media subfolder for a system under downloaded_media.
    .OUTPUTS
        Count of folders created.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string]   $SystemMediaDir,
        [Parameter(Mandatory = $true)][string[]] $MediaFolders,
        [switch] $DryRun
    )
    $created = 0
    foreach ($f in $MediaFolders) {
        $p = Join-Path $SystemMediaDir $f
        if (-not (Test-Path -LiteralPath $p)) {
            if (-not $DryRun) { New-Item -Path $p -ItemType Directory -Force | Out-Null }
            $created++
        }
    }
    return $created
}

function Copy-MediaSafe {
    <#
    .SYNOPSIS
        Copies (or moves) a media file to its destination without ever losing data:
        identical files are skipped, differing destinations are backed up first.
    .OUTPUTS
        One of: 'copied','moved','skipped-identical','overwritten','dryrun','error'.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string] $Source,
        [Parameter(Mandatory = $true)][string] $Dest,
        [Parameter(Mandatory = $true)][string] $BackupRoot,
        [switch] $Move,
        [switch] $DryRun
    )
    if (-not (Test-Path -LiteralPath $Source)) { return 'error' }
    $destDir = Split-Path $Dest -Parent

    if (Test-Path -LiteralPath $Dest) {
        $hs = Get-FileSha256 -Path $Source
        $hd = Get-FileSha256 -Path $Dest
        if ($hs -and $hd -and $hs -eq $hd) {
            if (-not $DryRun -and $Move) { Remove-Item -LiteralPath $Source -Force -ErrorAction SilentlyContinue }
            return 'skipped-identical'
        }
        if ($DryRun) { return 'dryrun' }
        Backup-File -Path $Dest -BackupRoot $BackupRoot | Out-Null
        if (-not (Test-Path -LiteralPath $destDir)) { New-Item -Path $destDir -ItemType Directory -Force | Out-Null }
        if ($Move) { Move-Item -LiteralPath $Source -Destination $Dest -Force }
        else { Copy-Item -LiteralPath $Source -Destination $Dest -Force }
        return 'overwritten'
    }

    if ($DryRun) { return 'dryrun' }
    if (-not (Test-Path -LiteralPath $destDir)) { New-Item -Path $destDir -ItemType Directory -Force | Out-Null }
    if ($Move) { Move-Item -LiteralPath $Source -Destination $Dest -Force; return 'moved' }
    else { Copy-Item -LiteralPath $Source -Destination $Dest -Force; return 'copied' }
}

function Invoke-MediaReorganization {
    <#
    .SYNOPSIS
        For a system, ensures all ES-DE media folders exist and moves any media
        files sitting loose in the media root (or in a wrongly-named subfolder)
        into the correct ES-DE subfolder, classified by name/folder/dimensions.
    .OUTPUTS
        Hashtable of statistics.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string]   $SystemMediaDir,
        [Parameter(Mandatory = $true)][object]   $Definitions,
        [Parameter(Mandatory = $true)][string]   $BackupRoot,
        [Parameter(Mandatory = $true)][scriptblock] $Logger,
        [switch] $DryRun
    )

    $stats = @{ FoldersCreated = 0; Moved = 0; Skipped = 0; Errors = 0 }

    # Always manage the full ES-DE media folder set for the system, creating the
    # media directory itself if it does not exist yet (so every system ends up
    # with a complete, correct downloaded_media structure).
    $esdeFolders = @($Definitions.esdeMediaFolders)
    if (-not (Test-Path -LiteralPath $SystemMediaDir) -and -not $DryRun) {
        New-Item -Path $SystemMediaDir -ItemType Directory -Force | Out-Null
    }
    $stats.FoldersCreated = New-EsdeMediaFolders -SystemMediaDir $SystemMediaDir -MediaFolders $esdeFolders -DryRun:$DryRun
    if (-not (Test-Path -LiteralPath $SystemMediaDir)) { return $stats }   # dry-run with no dir

    $valid = @{}; foreach ($f in $esdeFolders) { $valid[$f.ToLower()] = $true }

    # Loose files directly in the media root.
    Get-ChildItem -LiteralPath $SystemMediaDir -File -ErrorAction SilentlyContinue | ForEach-Object {
        $cls = Get-MediaClassification -FilePath $_.FullName -Definitions $Definitions -SourceFolderName ''
        if ($cls.EsdeFolder) {
            $dest = Join-Path (Join-Path $SystemMediaDir $cls.EsdeFolder) $_.Name
            $r = Copy-MediaSafe -Source $_.FullName -Dest $dest -BackupRoot $BackupRoot -Move -DryRun:$DryRun
            if ($r -in @('moved','overwritten','copied')) { $stats.Moved++ } else { $stats.Skipped++ }
        } else { $stats.Skipped++ }
    }

    # Files inside non-ES-DE-named subfolders (wrongly named) -> reclassify.
    Get-ChildItem -LiteralPath $SystemMediaDir -Directory -ErrorAction SilentlyContinue | ForEach-Object {
        $folderName = $_.Name
        if ($valid.ContainsKey($folderName.ToLower())) { return }   # already a valid ES-DE folder
        Get-ChildItem -LiteralPath $_.FullName -File -Recurse -ErrorAction SilentlyContinue | ForEach-Object {
            $cls = Get-MediaClassification -FilePath $_.FullName -Definitions $Definitions -SourceFolderName $folderName
            if ($cls.EsdeFolder) {
                $dest = Join-Path (Join-Path $SystemMediaDir $cls.EsdeFolder) $_.Name
                $r = Copy-MediaSafe -Source $_.FullName -Dest $dest -BackupRoot $BackupRoot -Move -DryRun:$DryRun
                if ($r -in @('moved','overwritten','copied')) { $stats.Moved++ } else { $stats.Skipped++ }
            } else { $stats.Skipped++ }
        }
    }

    & $Logger "Reorg $(Split-Path $SystemMediaDir -Leaf): +$($stats.FoldersCreated) folders, $($stats.Moved) moved, $($stats.Skipped) skipped." 'INFO'
    return $stats
}

Export-ModuleMember -Function Get-FileSha256, New-EsdeMediaFolders, Copy-MediaSafe, Invoke-MediaReorganization
