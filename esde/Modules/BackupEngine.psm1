<#
.SYNOPSIS
    Backup engine - timestamped backups of any file before modification, plus
    snapshot backups of whole config/gamelist trees, with restore support.
#>

Set-StrictMode -Version Latest

function Initialize-BackupRoot {
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][string] $BackupRoot)
    if (-not (Test-Path -LiteralPath $BackupRoot)) {
        New-Item -Path $BackupRoot -ItemType Directory -Force | Out-Null
    }
    return $BackupRoot
}

function Backup-File {
    <#
    .SYNOPSIS
        Copies a file to the backup root as <name>.<timestamp>.bak (no-op if the
        source does not exist). Returns the backup path or $null.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string] $Path,
        [Parameter(Mandatory = $true)][string] $BackupRoot
    )
    if (-not (Test-Path -LiteralPath $Path)) { return $null }
    Initialize-BackupRoot -BackupRoot $BackupRoot | Out-Null
    $stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
    $leaf  = Split-Path -Path $Path -Leaf
    $dest  = Join-Path $BackupRoot ("{0}.{1}.bak" -f $leaf, $stamp)
    Copy-Item -LiteralPath $Path -Destination $dest -Force
    return $dest
}

function Backup-Tree {
    <#
    .SYNOPSIS
        Creates a timestamped snapshot copy of a folder tree (filtered by include
        extensions) under the backup root. Used for gamelists / settings / configs.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string]   $SourceDir,
        [Parameter(Mandatory = $true)][string]   $BackupRoot,
        [Parameter(Mandatory = $true)][string]   $Label,
        [string[]] $IncludeExtensions = @('*.xml','*.cfg','*.ini','*.json','*.yml','*.toml')
    )
    if (-not (Test-Path -LiteralPath $SourceDir)) { return $null }
    $stamp  = Get-Date -Format 'yyyyMMdd_HHmmss'
    $target = Join-Path $BackupRoot ("snapshot_{0}_{1}" -f $Label, $stamp)
    New-Item -Path $target -ItemType Directory -Force | Out-Null

    $count = 0
    Get-ChildItem -LiteralPath $SourceDir -Recurse -File -Include $IncludeExtensions -ErrorAction SilentlyContinue | ForEach-Object {
        $rel = $_.FullName.Substring($SourceDir.Length).TrimStart('\','/')
        $dst = Join-Path $target $rel
        $dstDir = Split-Path $dst -Parent
        if (-not (Test-Path -LiteralPath $dstDir)) { New-Item -Path $dstDir -ItemType Directory -Force | Out-Null }
        Copy-Item -LiteralPath $_.FullName -Destination $dst -Force
        $count++
    }
    return @{ Path = $target; FileCount = $count }
}

function Restore-LatestFile {
    <#
    .SYNOPSIS
        Restores a file from its newest <name>.<timestamp>.bak backup.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string] $OriginalPath,
        [Parameter(Mandatory = $true)][string] $BackupRoot
    )
    if (-not (Test-Path -LiteralPath $BackupRoot)) { return $false }
    $leaf   = Split-Path $OriginalPath -Leaf
    $backup = Get-ChildItem -LiteralPath $BackupRoot -Filter "$leaf.*.bak" -File -ErrorAction SilentlyContinue |
              Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if ($backup) {
        Copy-Item -LiteralPath $backup.FullName -Destination $OriginalPath -Force
        return $true
    }
    return $false
}

Export-ModuleMember -Function Initialize-BackupRoot, Backup-File, Backup-Tree, Restore-LatestFile
