<#
.SYNOPSIS
    Duplicate detection engine (SHA256). Finds byte-identical media files and
    reclaims space only for redundant copies inside the SAME media subfolder
    (after backing them up). Cross-folder identical files (legitimately shared,
    e.g. a cover reused as a miximage source) are reported but never removed.
#>

Set-StrictMode -Version Latest

function Find-DuplicateMedia {
    <#
    .SYNOPSIS
        Hashes every media file under a media directory and groups identical files.
    .OUTPUTS
        Hashtable: Groups (array of @{Hash;Files}), TotalFiles, DuplicateFiles,
        ReclaimableBytes.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string] $MediaDir,
        [string] $CacheFile
    )

    # Optional persistent hash cache keyed by path -> "size|mtimeTicks|sha256" so
    # unchanged files are not re-hashed on subsequent runs (big speed-up on large
    # libraries). Cache is validated by size+last-write-time.
    $cache = @{}
    if ($CacheFile -and (Test-Path -LiteralPath $CacheFile)) {
        try {
            foreach ($line in (Get-Content -LiteralPath $CacheFile -Encoding UTF8 -ErrorAction SilentlyContinue)) {
                $i = $line.IndexOf('|'); if ($i -lt 1) { continue }
                $cache[$line.Substring(0,$i)] = $line.Substring($i+1)
            }
        } catch { }
    }
    $newCache = New-Object System.Collections.Generic.List[string]

    $byHash = @{}
    $total  = 0
    if (Test-Path -LiteralPath $MediaDir) {
        Get-ChildItem -LiteralPath $MediaDir -File -Recurse -ErrorAction SilentlyContinue | ForEach-Object {
            $sig = "$($_.Length)|$($_.LastWriteTimeUtc.Ticks)"
            $h = $null
            if ($cache.ContainsKey($_.FullName)) {
                $cached = $cache[$_.FullName]
                $bar = $cached.LastIndexOf('|')
                if ($bar -gt 0 -and $cached.Substring(0,$bar) -eq $sig) { $h = $cached.Substring($bar+1) }
            }
            if (-not $h) { $h = Get-FileSha256 -Path $_.FullName }
            if (-not $h) { return }
            if ($CacheFile) { $newCache.Add("$($_.FullName)|$sig|$h") }
            $total++
            if (-not $byHash.ContainsKey($h)) { $byHash[$h] = New-Object System.Collections.Generic.List[object] }
            $byHash[$h].Add($_)
        }
    }
    if ($CacheFile -and $newCache.Count -gt 0) {
        try {
            $cd = Split-Path $CacheFile -Parent
            if ($cd -and -not (Test-Path -LiteralPath $cd)) { New-Item -Path $cd -ItemType Directory -Force | Out-Null }
            [System.IO.File]::WriteAllLines($CacheFile, $newCache.ToArray(), (New-Object System.Text.UTF8Encoding($false)))
        } catch { }
    }

    $groups = New-Object System.Collections.Generic.List[object]
    $dupCount = 0; $reclaim = 0
    foreach ($h in $byHash.Keys) {
        $files = $byHash[$h]
        if ($files.Count -gt 1) {
            $dupCount += ($files.Count - 1)
            $reclaim  += ($files[0].Length * ($files.Count - 1))
            $groups.Add(@{ Hash = $h; Files = @($files | ForEach-Object { $_.FullName }) })
        }
    }
    return @{ Groups = $groups.ToArray(); TotalFiles = $total; DuplicateFiles = $dupCount; ReclaimableBytes = $reclaim }
}

function Invoke-DuplicateCleanup {
    <#
    .SYNOPSIS
        Removes redundant duplicates that share the SAME parent folder (keeping the
        first), backing each up first. Returns count removed.
    #>
    [CmdletBinding()]
    param(
        [object[]] $Groups = @(),
        [Parameter(Mandatory = $true)][string]   $BackupRoot,
        [Parameter(Mandatory = $true)][scriptblock] $Logger,
        [switch] $DryRun
    )
    $removed = 0
    if (-not $Groups -or $Groups.Count -eq 0) { return 0 }
    foreach ($g in $Groups) {
        $byFolder = @{}
        foreach ($f in $g.Files) {
            $dir = Split-Path $f -Parent
            if (-not $byFolder.ContainsKey($dir)) { $byFolder[$dir] = New-Object System.Collections.Generic.List[string] }
            $byFolder[$dir].Add($f)
        }
        foreach ($dir in $byFolder.Keys) {
            $list = $byFolder[$dir]
            if ($list.Count -le 1) { continue }   # keep cross-folder copies
            for ($i = 1; $i -lt $list.Count; $i++) {
                if ($DryRun) { & $Logger "[DRY-RUN] Would remove duplicate: $($list[$i])" 'INFO'; $removed++; continue }
                Backup-File -Path $list[$i] -BackupRoot $BackupRoot | Out-Null
                Remove-Item -LiteralPath $list[$i] -Force -ErrorAction SilentlyContinue
                & $Logger "Removed duplicate (backed up): $($list[$i])" 'SUCCESS'
                $removed++
            }
        }
    }
    return $removed
}

Export-ModuleMember -Function Find-DuplicateMedia, Invoke-DuplicateCleanup
