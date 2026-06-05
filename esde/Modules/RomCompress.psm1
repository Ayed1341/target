<#
.SYNOPSIS
    Real CD/DVD ROM compression to CHD using chdman (part of MAME tools, free).
.DESCRIPTION
    Converts cue/bin, iso and gdi disc images to CHD, which is lossless and saves a
    lot of space. Requires chdman.exe (found on PATH or under an emulator/MAME
    folder). The original is moved to a quarantine folder only AFTER the CHD is
    created and verified non-empty - so nothing is ever lost. Opt-in (/compress).
#>

Set-StrictMode -Version Latest

function Find-Chdman {
    [CmdletBinding()]
    param([string[]] $EmulatorRoots = @())
    $cmd = Get-Command chdman -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    foreach ($r in $EmulatorRoots) {
        if (-not $r -or -not (Test-Path -LiteralPath $r)) { continue }
        $hit = Get-ChildItem -LiteralPath $r -File -Recurse -Depth 4 -Filter 'chdman.exe' -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($hit) { return $hit.FullName }
    }
    return $null
}

function Invoke-ChdCompression {
    <#
    .SYNOPSIS
        Compresses cue/iso/gdi disc images to CHD for a system. Returns
        @{ Converted; SavedMB }.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string] $SystemRomDir,
        [Parameter(Mandatory = $true)][string] $Chdman,
        [Parameter(Mandatory = $true)][string] $BackupRoot,
        [Parameter(Mandatory = $true)][scriptblock] $Logger,
        [switch] $DryRun
    )
    $stats = @{ Converted = 0; SavedMB = 0.0 }
    if (-not (Test-Path -LiteralPath $SystemRomDir)) { return $stats }
    $qRoot = Join-Path $BackupRoot ('precompress\' + (Split-Path $SystemRomDir -Leaf))

    Get-ChildItem -LiteralPath $SystemRomDir -File -ErrorAction SilentlyContinue |
        Where-Object { $_.Extension.ToLower() -in @('.cue','.iso','.gdi') } | ForEach-Object {
            $src = $_
            $chd = [System.IO.Path]::ChangeExtension($src.FullName, 'chd')
            if (Test-Path -LiteralPath $chd) { return }   # already converted
            if ($DryRun) { & $Logger "[DRY-RUN] Would compress $($src.Name) -> CHD." 'INFO'; $stats.Converted++; return }
            try {
                $subcmd = if ($src.Extension.ToLower() -eq '.gdi') { 'createcd' } elseif ($src.Extension.ToLower() -eq '.cue') { 'createcd' } else { 'createcd' }
                $p = Start-Process -FilePath $Chdman -ArgumentList @($subcmd,'-i',$src.FullName,'-o',$chd) -NoNewWindow -Wait -PassThru
                if ($p.ExitCode -eq 0 -and (Test-Path -LiteralPath $chd) -and ((Get-Item -LiteralPath $chd).Length -gt 0)) {
                    $origSize = $src.Length
                    # Also move companion .bin files for a .cue.
                    $companions = @()
                    if ($src.Extension.ToLower() -eq '.cue') {
                        Get-Content -LiteralPath $src.FullName -ErrorAction SilentlyContinue | ForEach-Object {
                            if ($_ -match 'FILE\s+"([^"]+)"') { $bin = Join-Path $src.DirectoryName $Matches[1]; if (Test-Path -LiteralPath $bin) { $companions += $bin } }
                        }
                    }
                    if (-not (Test-Path -LiteralPath $qRoot)) { New-Item -Path $qRoot -ItemType Directory -Force | Out-Null }
                    Move-Item -LiteralPath $src.FullName -Destination (Join-Path $qRoot $src.Name) -Force -ErrorAction SilentlyContinue
                    foreach ($c in $companions) { $origSize += (Get-Item -LiteralPath $c).Length; Move-Item -LiteralPath $c -Destination (Join-Path $qRoot (Split-Path $c -Leaf)) -Force -ErrorAction SilentlyContinue }
                    $stats.Converted++
                    $stats.SavedMB += [math]::Round(($origSize - (Get-Item -LiteralPath $chd).Length)/1MB, 1)
                } else {
                    if (Test-Path -LiteralPath $chd) { Remove-Item -LiteralPath $chd -Force -ErrorAction SilentlyContinue }
                    & $Logger "chdman failed for $($src.Name) (exit $($p.ExitCode)); original left untouched." 'WARN'
                }
            } catch { & $Logger "chdman error for $($src.Name): $($_.Exception.Message)" 'WARN' }
        }
    if ($stats.Converted -gt 0 -and -not $DryRun) { & $Logger "Compressed $($stats.Converted) image(s) to CHD in $(Split-Path $SystemRomDir -Leaf), saved ~$($stats.SavedMB) MB (originals quarantined)." 'SUCCESS' }
    return $stats
}

Export-ModuleMember -Function Find-Chdman, Invoke-ChdCompression
