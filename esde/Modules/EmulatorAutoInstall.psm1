<#
.SYNOPSIS
    ES-DE-native "install the best emulator if it is missing" engine (opt-in via
    /install). Emulators are free, legally-redistributable software, so unlike
    BIOS/ROMs they CAN be fetched automatically from their official upstreams.
.DESCRIPTION
    Builds an install plan from the emulator-gap analysis (only systems that have
    ROMs but no working emulator), picks the single best downloadable emulator for
    each, and installs it into the ES-DE Emulators root. Twenty safety/quality
    features layered on top of the low-level download/extract helpers
    (EmulatorInstall.psm1):

      1  ES-DE-native install root (data-parent\Emulators), auto-created
      2  Catalog-driven "best emulator per system" plan from the gap analysis
      3  Multi-system emulators (e.g. Dolphin for gc+wii) de-duplicated to one install
      4  Idempotent: skip anything already installed & verified
      5  Online preflight - skip cleanly when offline
      6  Free-disk-space preflight per install (configurable safety margin)
      7  GitHub latest-release resolution, Windows-x64-only asset filtering
      8  Prerelease/canary-aware resolution (repos that only ship prereleases)
      9  Downloaded-size sanity check against the asset's reported size
     10  Download retry with exponential backoff (reused helper)
     11  Archive-type aware extraction (7z / zip / sfx) with .NET zip fallback
     12  Atomic install with rollback (stage -> swap -> verify -> restore on failure)
     13  Executable re-detection to verify the install really worked
     14  Version manifest (.esde-autoinstall.json) for future update checks
     15  Portable-mode marker for emulators that support it (portable.txt)
     16  ES-DE custom es_find_rules.xml registration (never touches bundled rules)
     17  Post-install auto-configuration handoff (Xbox emulators + graphics tuning)
     18  Dry-run mode (plan + sizes, nothing downloaded)
     19  Per-install logging + report keys + health findings on failure
     20  Post-run remaining-gap summary (systems still needing a manual emulator)
#>

Set-StrictMode -Version Latest

# Known ES-DE emulator names for es_find_rules.xml (only the ones we are sure of).
$script:EsdeFindNames = @{
    retroarch='RETROARCH'; pcsx2='PCSX2'; rpcs3='RPCS3'; xenia='XENIA'; xemu='XEMU'
    dolphin='DOLPHIN'; cemu='CEMU'; ppsspp='PPSSPP'; duckstation='DUCKSTATION'
    melonds='MELONDS'; mame='MAME'; flycast='FLYCAST'; redream='REDREAM'; mgba='MGBA'
}
# Emulators that key off a "portable.txt" marker to keep their data local.
$script:PortableEmulators = @('xenia','xemu','cemu','ppsspp','duckstation')

function Get-EmulatorInstallRoot {
    <#
    .SYNOPSIS
        Resolves the directory new emulators are installed into. Prefers an existing
        ES-DE Emulators root; otherwise data-parent\Emulators (not created here).
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][System.Collections.Specialized.OrderedDictionary] $Layout,
        [string[]] $ExistingRoots = @()
    )
    foreach ($r in $ExistingRoots) { if ($r -and (Test-Path -LiteralPath $r)) { return $r } }
    return (Join-Path (Split-Path $Layout.DataDir -Parent) 'Emulators')
}

function Get-FreeSpaceMB {
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][string] $Path)
    try {
        $probe = $Path
        while ($probe -and -not (Test-Path -LiteralPath $probe)) { $probe = Split-Path $probe -Parent }
        if (-not $probe) { return [double]::MaxValue }
        $root = [System.IO.Path]::GetPathRoot($probe)
        if (-not $root) { return [double]::MaxValue }
        $di = New-Object System.IO.DriveInfo($root)
        return [math]::Round($di.AvailableFreeSpace / 1MB, 1)
    } catch { return [double]::MaxValue }
}

function Resolve-EmulatorAsset {
    <#
    .SYNOPSIS
        Resolves @{ Url; FileName; Tag; SizeBytes } for a download definition.
        Supports prerelease/canary repos and Windows-x64-only asset filtering.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][object] $Download,
        [switch] $AllowPrerelease
    )
    if ($Download.type -eq 'direct') {
        return @{ Url = $Download.url; FileName = (Split-Path $Download.url -Leaf); Tag = 'direct'; SizeBytes = 0 }
    }
    if ($Download.type -ne 'github') { return $null }

    $headers = @{ 'User-Agent' = 'ESDE-AutoSuite'; 'Accept' = 'application/vnd.github+json' }
    if ($env:GITHUB_TOKEN) { $headers['Authorization'] = "Bearer $($env:GITHUB_TOKEN)" }
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

    $wantPre = $AllowPrerelease.IsPresent
    if ($Download.PSObject.Properties.Name -contains 'prerelease') { $wantPre = $wantPre -or [bool]$Download.prerelease }

    $rel = $null
    try {
        if ($wantPre) {
            # Some projects (canary builds) only publish prereleases: take the newest
            # release of any kind.
            $list = Invoke-RestMethod -Uri "https://api.github.com/repos/$($Download.repo)/releases?per_page=10" -Headers $headers -TimeoutSec 60 -ErrorAction Stop
            $rel  = @($list | Sort-Object { [datetime]$_.published_at } -Descending | Select-Object -First 1)[0]
        } else {
            $rel = Invoke-RestMethod -Uri "https://api.github.com/repos/$($Download.repo)/releases/latest" -Headers $headers -TimeoutSec 60 -ErrorAction Stop
        }
    } catch {
        throw "GitHub lookup failed for $($Download.repo): $($_.Exception.Message)"
    }
    if (-not $rel) { return $null }

    $assets  = @($rel.assets)
    $foreign = '(?i)(arm64|aarch64|armhf|armv7|riscv|linux|ubuntu|debian|mac|macos|osx|darwin|android|appimage|ios|\.dmg$|\.deb$|\.rpm$|\.tar\.|\.apk$|symbols|debug|pdb)'
    $winAssets = @($assets | Where-Object { $_.name -match '(?i)\.(7z|zip|exe)$' -and $_.name -notmatch $foreign })

    $match = $null
    if ($Download.PSObject.Properties.Name -contains 'assetPattern' -and $Download.assetPattern) {
        $match = $winAssets | Where-Object { $_.name -match $Download.assetPattern } | Select-Object -First 1
    }
    if (-not $match) { $match = $winAssets | Where-Object { $_.name -match '(?i)(win|windows|x64|x86_64|64bit|amd64)' } | Select-Object -First 1 }
    if (-not $match) { $match = $winAssets | Select-Object -First 1 }
    if (-not $match) { return $null }

    $size = 0; if ($match.PSObject.Properties.Name -contains 'size') { $size = [int64]$match.size }
    $tag  = 'unknown'; if ($rel.PSObject.Properties.Name -contains 'tag_name' -and $rel.tag_name) { $tag = [string]$rel.tag_name }
    return @{ Url = $match.browser_download_url; FileName = $match.name; Tag = $tag; SizeBytes = $size }
}

function Get-AutoInstallPlan {
    <#
    .SYNOPSIS
        From gap records + the catalog, returns one install item per missing
        emulator: @{ EmulatorId; Def; FolderPath; Systems[] }.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][object[]] $Gaps,
        [Parameter(Mandatory = $true)][object]   $Catalog,
        [Parameter(Mandatory = $true)][hashtable] $SystemMap,
        [Parameter(Mandatory = $true)][string]   $InstallRoot,
        [string[]] $InstalledIds = @()
    )
    $byId = @{}
    foreach ($def in @($Catalog.emulators)) { $byId[[string]$def.id] = $def }
    $installed = New-Object System.Collections.Generic.HashSet[string] ([StringComparer]::OrdinalIgnoreCase)
    foreach ($i in $InstalledIds) { [void]$installed.Add($i) }

    $plan = [ordered]@{}
    foreach ($g in ($Gaps | Where-Object { $_.Missing })) {
        # Preference order: the system's emulator list (best first).
        $options = @()
        if ($SystemMap.ContainsKey($g.System)) { $options = @($SystemMap[$g.System]) }
        if ($options.Count -eq 0 -and $g.Recommended) { $options = @($g.Recommended) }
        $chosen = $null
        foreach ($opt in $options) {
            $id = [string]$opt
            if ($installed.Contains($id)) { $chosen = $null; break }   # already covered
            if ($byId.ContainsKey($id) -and $byId[$id].PSObject.Properties.Name -contains 'download' -and $byId[$id].download -and $byId[$id].download.type -ne 'none') {
                $chosen = $id; break
            }
        }
        if (-not $chosen) { continue }
        if ($plan.Contains($chosen)) { $plan[$chosen].Systems += $g.System; continue }
        $def = $byId[$chosen]
        $plan[$chosen] = @{
            EmulatorId = $chosen
            Def        = $def
            FolderPath = (Join-Path $InstallRoot $def.folder)
            Systems    = @($g.System)
        }
    }
    return @($plan.Values)
}

function Register-EmulatorFindRule {
    <#
    .SYNOPSIS
        Adds/updates a staticpath entry in the USER's custom es_find_rules.xml so
        ES-DE finds the freshly-installed emulator. The bundled resources file is
        never modified. Returns $true when written.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][System.Collections.Specialized.OrderedDictionary] $Layout,
        [Parameter(Mandatory = $true)][string] $EmulatorId,
        [Parameter(Mandatory = $true)][string] $ExePath,
        [Parameter(Mandatory = $true)][scriptblock] $Logger,
        [switch] $DryRun
    )
    if (-not $script:EsdeFindNames.ContainsKey($EmulatorId)) { return $false }
    $name = $script:EsdeFindNames[$EmulatorId]
    $custom = Join-Path $Layout.CustomSystems 'es_find_rules.xml'
    if ($DryRun) { & $Logger "[DRY-RUN] Would register $name in custom es_find_rules.xml." 'INFO'; return $false }

    $dir = Split-Path $custom -Parent
    if ($dir -and -not (Test-Path -LiteralPath $dir)) { New-Item -Path $dir -ItemType Directory -Force | Out-Null }

    $doc = New-Object System.Xml.XmlDocument
    if (Test-Path -LiteralPath $custom) {
        try { $doc.Load($custom) } catch { $doc = New-Object System.Xml.XmlDocument }
    }
    $root = $doc.DocumentElement
    if (-not $root -or $root.Name -ne 'ruleList') {
        $doc.RemoveAll()
        [void]$doc.AppendChild($doc.CreateXmlDeclaration('1.0', $null, $null))
        $root = $doc.CreateElement('ruleList'); [void]$doc.AppendChild($root)
    }
    # Replace any existing emulator node of this name.
    foreach ($n in @($root.SelectNodes("emulator[@name='$name']"))) { [void]$root.RemoveChild($n) }

    $emu = $doc.CreateElement('emulator'); $emu.SetAttribute('name', $name)
    $rule = $doc.CreateElement('rule'); $rule.SetAttribute('type', 'staticpath')
    $entry = $doc.CreateElement('entry'); $entry.InnerText = $ExePath
    [void]$rule.AppendChild($entry); [void]$emu.AppendChild($rule); [void]$root.AppendChild($emu)
    $doc.Save($custom)
    & $Logger "Registered $name in custom es_find_rules.xml so ES-DE can locate it." 'SUCCESS'
    return $true
}

function Install-EsdeEmulator {
    <#
    .SYNOPSIS
        Installs one emulator from its catalog definition with disk preflight,
        size sanity, atomic+rollback, verification, version manifest and a
        portable marker. Returns @{ Success; ExePath; Tag; SizeMB; Message }.
    .PARAMETER LocalArchiveOverride
        Test hook: when supplied, the archive is taken from this local path instead
        of being downloaded (the resolve/download network steps are skipped).
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][object] $Item,
        [Parameter(Mandatory = $true)][string] $BackupRoot,
        [Parameter(Mandatory = $true)][scriptblock] $Logger,
        [string] $SevenZip,
        [int] $MinFreeMB = 600,
        [switch] $AllowPrerelease,
        [switch] $DryRun,
        [string] $LocalArchiveOverride
    )
    $def = $Item.Def
    $target = $Item.FolderPath
    $name = $def.displayName

    # (6) Disk-space preflight.
    $free = Get-FreeSpaceMB -Path $target
    if ($free -lt $MinFreeMB) {
        & $Logger "Skipping $name - only $free MB free (need >= $MinFreeMB MB)." 'WARN'
        return @{ Success = $false; ExePath = $null; Tag = ''; SizeMB = 0; Message = 'Insufficient disk space.' }
    }

    if ($DryRun -and -not $LocalArchiveOverride) {
        try {
            $r = Resolve-EmulatorAsset -Download $def.download -AllowPrerelease:$AllowPrerelease
            $sz = if ($r -and $r.SizeBytes) { [math]::Round($r.SizeBytes/1MB,1) } else { 0 }
            & $Logger "[DRY-RUN] Would install $name for [$($Item.Systems -join ', ')] (~$sz MB) -> $target." 'INFO'
            return @{ Success = $false; ExePath = $null; Tag = $(if($r){$r.Tag}else{''}); SizeMB = $sz; Message = 'Dry-run.' }
        } catch {
            & $Logger "[DRY-RUN] Could not resolve a download for ${name}: $($_.Exception.Message)" 'WARN'
            return @{ Success = $false; ExePath = $null; Tag = ''; SizeMB = 0; Message = $_.Exception.Message }
        }
    }

    $tempBase = Join-Path ([System.IO.Path]::GetTempPath()) ("ESDEInstall_{0}_{1}" -f $Item.EmulatorId, [Guid]::NewGuid().ToString('N'))
    $staging  = Join-Path $tempBase 'extracted'
    New-Item -Path $tempBase -ItemType Directory -Force | Out-Null
    $rollbackDir = $null
    try {
        $archType = if ($def.download.PSObject.Properties.Name -contains 'archive') { [string]$def.download.archive } else { 'zip' }
        if ($LocalArchiveOverride) {
            $dlPath = $LocalArchiveOverride
            $tag = 'test-local'
        } else {
            # (7/8) Resolve, (9) size sanity, (10) retry download.
            $resolved = Resolve-EmulatorAsset -Download $def.download -AllowPrerelease:$AllowPrerelease
            if (-not $resolved) { throw 'No Windows x64 download asset could be resolved.' }
            $tag = $resolved.Tag
            $dlPath = Join-Path $tempBase $resolved.FileName
            & $Logger "Downloading $name $tag ($($resolved.FileName))..." 'INFO'
            [void](Invoke-FileDownload -Url $resolved.Url -Destination $dlPath)
            $actual = (Get-Item -LiteralPath $dlPath).Length
            if ($resolved.SizeBytes -gt 0 -and [math]::Abs($actual - $resolved.SizeBytes) -gt [math]::Max(4096, $resolved.SizeBytes * 0.02)) {
                throw "Downloaded size $actual B does not match expected $($resolved.SizeBytes) B (corrupt/incomplete)."
            }
            & $Logger "Downloaded $([math]::Round($actual/1MB,1)) MB." 'SUCCESS'
        }

        # (11) Extract.
        Expand-DownloadedArchive -ArchivePath $dlPath -Destination $staging -ArchiveType $archType -SevenZip $SevenZip

        # (12) Verify the staging actually contains the expected exe BEFORE swapping.
        $strip = $false
        if ($def.download.PSObject.Properties.Name -contains 'stripRootFolder') { $strip = [bool]$def.download.stripRootFolder }
        $probeDir = $staging
        if ($strip) {
            $entries = @(Get-ChildItem -LiteralPath $staging -Force)
            $dirs = @($entries | Where-Object { $_.PSIsContainer }); $files = @($entries | Where-Object { -not $_.PSIsContainer })
            if ($dirs.Count -eq 1 -and $files.Count -eq 0) { $probeDir = $dirs[0].FullName }
        }
        $stagedExe = Find-EmulatorExecutable -Folder $probeDir -Executables @($def.executables)
        if (-not $stagedExe) { throw 'Extracted archive did not contain the expected executable.' }

        # (12) Atomic swap with rollback: move any prior install aside first.
        if (Test-Path -LiteralPath $target) {
            $rollbackDir = Join-Path $BackupRoot ('emu_replaced\' + $def.folder + '_' + (Get-Date -Format 'yyyyMMddHHmmss'))
            New-Item -Path (Split-Path $rollbackDir -Parent) -ItemType Directory -Force | Out-Null
            Move-Item -LiteralPath $target -Destination $rollbackDir -Force
        }
        Move-ExtractedPayload -StagingDir $staging -TargetDir $target -StripRootFolder $strip

        # (13) Re-detect in the real target.
        $exe = Find-EmulatorExecutable -Folder $target -Executables @($def.executables)
        if (-not $exe) { throw 'Executable not found after install.' }

        # (14) Version manifest.
        $manifest = @{ id = $Item.EmulatorId; tag = $tag; installed = (Get-Date -Format o); systems = @($Item.Systems); exe = $exe }
        ($manifest | ConvertTo-Json -Depth 5) | Set-Content -LiteralPath (Join-Path $target '.esde-autoinstall.json') -Encoding UTF8

        # (15) Portable marker.
        if ($script:PortableEmulators -contains $Item.EmulatorId) {
            $pt = Join-Path $target 'portable.txt'
            if (-not (Test-Path -LiteralPath $pt)) { Set-Content -LiteralPath $pt -Value '' -Encoding UTF8 }
        }

        $sizeMB = [math]::Round((Get-Item -LiteralPath $exe).Length/1MB, 1)
        & $Logger "Installed $name $tag for [$($Item.Systems -join ', ')] -> $exe" 'SUCCESS'
        if ($rollbackDir) { & $Logger "Previous $name kept at $rollbackDir (delete once the new build is confirmed good)." 'INFO' }
        return @{ Success = $true; ExePath = $exe; Tag = $tag; SizeMB = $sizeMB; Message = 'Installed.' }
    } catch {
        & $Logger "Install of $name failed: $($_.Exception.Message)" 'ERROR'
        # Roll back to the previous install if we moved it aside.
        if ($rollbackDir -and (Test-Path -LiteralPath $rollbackDir) -and -not (Test-Path -LiteralPath $target)) {
            try { Move-Item -LiteralPath $rollbackDir -Destination $target -Force; & $Logger "Rolled back to previous $name." 'INFO' } catch { }
        }
        return @{ Success = $false; ExePath = $null; Tag = ''; SizeMB = 0; Message = $_.Exception.Message }
    } finally {
        if (Test-Path -LiteralPath $tempBase) { Remove-Item -LiteralPath $tempBase -Recurse -Force -ErrorAction SilentlyContinue }
    }
}

Export-ModuleMember -Function Get-EmulatorInstallRoot, Get-FreeSpaceMB, Resolve-EmulatorAsset, `
    Get-AutoInstallPlan, Register-EmulatorFindRule, Install-EsdeEmulator
