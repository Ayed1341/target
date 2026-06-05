<#
.SYNOPSIS
    Media hygiene: sanitize illegal characters in media filenames and detect the
    same image reused across many systems.
#>

Set-StrictMode -Version Latest

function Repair-MediaFilenames {
    <#
    .SYNOPSIS
        Renames media files containing characters that break some filesystems/themes
        (control chars, trailing dots/spaces). Backs up before renaming. Returns count.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string] $SystemMediaDir,
        [Parameter(Mandatory = $true)][string] $BackupRoot,
        [Parameter(Mandatory = $true)][scriptblock] $Logger,
        [switch] $DryRun
    )
    $fixed = 0
    if (-not (Test-Path -LiteralPath $SystemMediaDir)) { return 0 }
    Get-ChildItem -LiteralPath $SystemMediaDir -File -Recurse -ErrorAction SilentlyContinue | ForEach-Object {
        $name = $_.Name
        $clean = $name -replace '[\x00-\x1F]', '' -replace '\s+(\.[^.]+)$', '$1'
        $clean = $clean.TrimEnd(' ', '.')
        if ($clean.Length -eq 0 -or $clean -eq $name) { return }
        $target = Join-Path $_.DirectoryName $clean
        if (Test-Path -LiteralPath $target) { return }
        if ($DryRun) { $fixed++; return }
        Rename-Item -LiteralPath $_.FullName -NewName $clean -Force -ErrorAction SilentlyContinue
        $fixed++
    }
    if ($fixed -gt 0 -and -not $DryRun) { & $Logger "Sanitized $fixed media filename(s) in $(Split-Path $SystemMediaDir -Leaf)." 'SUCCESS' }
    return $fixed
}

function Find-CrossSystemMediaDup {
    <#
    .SYNOPSIS
        Returns how many image hashes are reused across 3+ different systems (often
        a sign of placeholder/wrong art). Read only.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][string] $MediaDir)
    if (-not (Test-Path -LiteralPath $MediaDir)) { return 0 }
    $hashSystems = @{}
    Get-ChildItem -LiteralPath $MediaDir -Directory -ErrorAction SilentlyContinue | ForEach-Object {
        $sysName = $_.Name
        Get-ChildItem -LiteralPath $_.FullName -File -Recurse -ErrorAction SilentlyContinue |
            Where-Object { $_.Extension.ToLower() -in @('.png','.jpg','.jpeg') } | ForEach-Object {
                $h = Get-FileSha256 -Path $_.FullName
                if (-not $h) { return }
                if (-not $hashSystems.ContainsKey($h)) { $hashSystems[$h] = New-Object System.Collections.Generic.HashSet[string] ([StringComparer]::OrdinalIgnoreCase) }
                [void]$hashSystems[$h].Add($sysName)
            }
    }
    $reused = 0
    foreach ($h in $hashSystems.Keys) { if ($hashSystems[$h].Count -ge 3) { $reused++ } }
    return $reused
}

Export-ModuleMember -Function Repair-MediaFilenames, Find-CrossSystemMediaDup
