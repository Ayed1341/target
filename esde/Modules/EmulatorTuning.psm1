<#
.SYNOPSIS
    Deeper, safe emulator tuning beyond resolution, plus a config archive.
.DESCRIPTION
    Applies extra quality/UX settings that are safe defaults:
      * RetroArch: rewind, run-ahead off, on-screen notifications off, fast-forward
        ratio, savestate thumbnails, threaded video, menu driver.
    And archives every emulator config file into a single timestamped backup folder
    so the whole emulator configuration can be restored together.
#>

Set-StrictMode -Version Latest

function Set-RetroArchExtras {
    <#
    .SYNOPSIS
        Applies safe extra RetroArch options to retroarch.cfg. Returns $true if applied.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string] $RetroArchDir,
        [Parameter(Mandatory = $true)][string] $BackupRoot,
        [Parameter(Mandatory = $true)][scriptblock] $Logger,
        [switch] $DryRun
    )
    $cfg = Join-Path $RetroArchDir 'retroarch.cfg'
    if (-not (Test-Path -LiteralPath $cfg)) { return $false }
    if ($DryRun) { & $Logger "[DRY-RUN] Would apply RetroArch extra options." 'INFO'; return $false }
    Backup-File -Path $cfg -BackupRoot $BackupRoot | Out-Null
    $opts = [ordered]@{
        'rewind_enable'                 = 'true'
        'rewind_buffer_size'            = '20971520'
        'run_ahead_enabled'             = 'false'
        'video_font_enable'             = 'true'
        'menu_show_load_content_animation' = 'false'
        'fastforward_ratio'             = '0.000000'
        'savestate_thumbnail_enable'    = 'true'
        'savestate_auto_save'           = 'false'
        'video_threaded'                = 'true'
        'notification_show_when_menu_is_alive' = 'false'
    }
    foreach ($k in $opts.Keys) { Set-FlatConfigValue -Path $cfg -Key $k -Value $opts[$k] -Quote }
    & $Logger "Applied RetroArch extra options (rewind, run-ahead, savestate thumbnails, fast-forward)." 'SUCCESS'
    return $true
}

function Get-EmulatorConfigFiles {
    <#
    .SYNOPSIS
        Fast, depth-bounded walk that returns user/emulator config files while
        PRUNING the big bundled directories emulators ship (RetroArch's shaders,
        assets, autoconfig, cores, database, thumbnails, ...). Those folders hold
        thousands of *.cfg/*.json/*.xml files that are not the user's settings, and
        descending into them is what made config archiving slow.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string] $Root,
        [int] $MaxDepth = 4,
        [int] $MaxFiles = 4000
    )
    $excludeDirs = New-Object System.Collections.Generic.HashSet[string] ([StringComparer]::OrdinalIgnoreCase)
    foreach ($d in @('shaders','assets','autoconfig','cores','info','database','databases',
                     'thumbnails','system','bios','saves','states','savestates','screenshots',
                     'recordings','downloaded_media','media','overlays','overlay','filters',
                     'cheats','logs','playlists','wallpapers','sounds','languages','records',
                     'runtime','blocks','cache','roms','rom','content','patches','.git')) { [void]$excludeDirs.Add($d) }
    $incExt = New-Object System.Collections.Generic.HashSet[string] ([StringComparer]::OrdinalIgnoreCase)
    foreach ($e in @('.cfg','.ini','.xml','.yml','.yaml','.toml','.json','.config')) { [void]$incExt.Add($e) }

    $out   = New-Object System.Collections.Generic.List[System.IO.FileInfo]
    $stack = New-Object System.Collections.Generic.Stack[object]
    $stack.Push([pscustomobject]@{ Dir = $Root; Depth = 0 })
    while ($stack.Count -gt 0 -and $out.Count -lt $MaxFiles) {
        $cur = $stack.Pop()
        $di = $null
        try { $di = New-Object System.IO.DirectoryInfo($cur.Dir) } catch { continue }
        $entries = $null
        try { $entries = $di.EnumerateFileSystemInfos() } catch { continue }
        foreach ($e in $entries) {
            if ($e -is [System.IO.DirectoryInfo]) {
                if ($cur.Depth -lt $MaxDepth -and -not $excludeDirs.Contains($e.Name)) {
                    $stack.Push([pscustomobject]@{ Dir = $e.FullName; Depth = $cur.Depth + 1 })
                }
            } elseif ($incExt.Contains($e.Extension) -and $e.FullName.Length -le 240) {
                $out.Add([System.IO.FileInfo]$e)
                if ($out.Count -ge $MaxFiles) { break }
            }
        }
    }
    return $out
}

function Backup-AllEmulatorConfigs {
    <#
    .SYNOPSIS
        Snapshots the user's emulator config files into one timestamped archive,
        skipping emulators' bundled folders and re-archiving only when something
        actually changed since the last snapshot. Returns count archived (or the
        unchanged count when nothing changed).
    #>
    [CmdletBinding()]
    param(
        [string[]] $EmulatorRoots = @(),
        [Parameter(Mandatory = $true)][string]   $BackupRoot,
        [Parameter(Mandatory = $true)][scriptblock] $Logger,
        [switch] $DryRun
    )
    if (-not $EmulatorRoots -or $EmulatorRoots.Count -eq 0) { return 0 }

    # Collect candidate files (pruned + depth-bounded) and build a change signature.
    $jobs = New-Object System.Collections.Generic.List[object]
    $sigSb = New-Object System.Text.StringBuilder
    foreach ($root in ($EmulatorRoots | Where-Object { $_ -and (Test-Path -LiteralPath $_) })) {
        $leaf = Split-Path $root -Leaf
        foreach ($f in (Get-EmulatorConfigFiles -Root $root)) {
            $rel = $f.FullName.Substring($root.Length).TrimStart('\','/')
            $jobs.Add([pscustomobject]@{ Src = $f.FullName; Dst = (Join-Path $leaf $rel) })
            [void]$sigSb.Append($leaf).Append('|').Append($rel).Append('|').Append($f.Length).Append('|').Append($f.LastWriteTimeUtc.Ticks).Append("`n")
        }
    }
    if ($jobs.Count -eq 0) { return 0 }

    # Skip re-archiving when nothing changed since the last snapshot.
    $sig = [Convert]::ToBase64String([System.Security.Cryptography.MD5]::Create().ComputeHash([System.Text.Encoding]::UTF8.GetBytes($sigSb.ToString())))
    $sigFile = Join-Path $BackupRoot 'emulator_configs.last.txt'
    if ($DryRun) { return $jobs.Count }
    if (Test-Path -LiteralPath $sigFile) {
        $prev = (Get-Content -LiteralPath $sigFile -Raw -ErrorAction SilentlyContinue)
        if ($prev -and $prev.Trim() -eq $sig) {
            & $Logger "Emulator configs unchanged since last archive ($($jobs.Count) file(s)); skipped re-archiving." 'INFO'
            return $jobs.Count
        }
    }

    $stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
    $dest  = Join-Path $BackupRoot ("emulator_configs_$stamp")
    $count = 0
    foreach ($j in $jobs) {
        $dst = Join-Path $dest $j.Dst
        $dstDir = Split-Path $dst -Parent
        if (-not (Test-Path -LiteralPath $dstDir)) { New-Item -Path $dstDir -ItemType Directory -Force | Out-Null }
        Copy-Item -LiteralPath $j.Src -Destination $dst -Force -ErrorAction SilentlyContinue
        $count++
    }
    if (-not (Test-Path -LiteralPath $BackupRoot)) { New-Item -Path $BackupRoot -ItemType Directory -Force | Out-Null }
    Set-Content -LiteralPath $sigFile -Value $sig -Encoding UTF8
    if ($count -gt 0) { & $Logger "Archived $count emulator config file(s) to $dest." 'SUCCESS' }
    return $count
}

Export-ModuleMember -Function Set-RetroArchExtras, Backup-AllEmulatorConfigs, Get-EmulatorConfigFiles
