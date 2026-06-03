<#
.SYNOPSIS
    Emulator auto-installation module.
.DESCRIPTION
    Installs missing emulators required by RetroBat. Resolution of download URLs
    is data-driven (config\emulators.json):
      * type=github : queries the GitHub Releases API for the latest matching asset
      * type=direct : uses a fixed official upstream URL
    Archives are extracted with the RetroBat-bundled 7-Zip when available, falling
    back to .NET ZIP extraction. Every step is logged and the install is verified
    by re-detecting the emulator executable afterwards. Existing files are never
    deleted; downloads land in a temp folder and are copied into place.
#>

Set-StrictMode -Version Latest

function Get-SevenZipPath {
    <#
    .SYNOPSIS
        Locates a usable 7-Zip executable (RetroBat bundles 7za under system\tools).
    #>
    [CmdletBinding()]
    param([string] $RetroBatRoot)

    $candidates = @()
    if ($RetroBatRoot) {
        $candidates += Join-Path $RetroBatRoot 'system\tools\7za.exe'
        $candidates += Join-Path $RetroBatRoot 'system\tools\7z.exe'
        $candidates += Join-Path $RetroBatRoot 'system\7za.exe'
    }
    foreach ($base in @(${env:ProgramFiles}, ${env:ProgramFiles(x86)})) {
        if (-not [string]::IsNullOrWhiteSpace($base)) {
            $candidates += Join-Path $base '7-Zip\7z.exe'
        }
    }

    foreach ($c in $candidates) {
        if ($c -and (Test-Path -LiteralPath $c)) { return $c }
    }
    $cmd = Get-Command -Name '7z.exe', '7za.exe' -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($cmd) { return $cmd.Source }
    return $null
}

function Resolve-DownloadUrl {
    <#
    .SYNOPSIS
        Resolves the concrete download URL + file name for an emulator definition.
    .OUTPUTS
        Hashtable with Url and FileName, or $null when unresolvable.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)] [object] $Download)

    switch ($Download.type) {
        'direct' {
            return @{ Url = $Download.url; FileName = (Split-Path $Download.url -Leaf) }
        }
        'github' {
            $api = "https://api.github.com/repos/$($Download.repo)/releases/latest"
            $headers = @{ 'User-Agent' = 'RetroBat-AutoSetup'; 'Accept' = 'application/vnd.github+json' }
            if ($env:GITHUB_TOKEN) { $headers['Authorization'] = "Bearer $($env:GITHUB_TOKEN)" }
            try {
                $rel    = Invoke-RestMethod -Uri $api -Headers $headers -TimeoutSec 60 -ErrorAction Stop
                $assets = @($rel.assets)
                $match  = $assets | Where-Object { $_.name -match $Download.assetPattern } | Select-Object -First 1
                if (-not $match) {
                    # Loosen: match on extension only if specific pattern failed.
                    $match = $assets | Where-Object { $_.name -match '\.(7z|zip|exe)$' } | Select-Object -First 1
                }
                if ($match) {
                    return @{ Url = $match.browser_download_url; FileName = $match.name }
                }
            } catch {
                throw "GitHub API lookup failed for $($Download.repo): $($_.Exception.Message)"
            }
            return $null
        }
        default { return $null }
    }
}

function Invoke-FileDownload {
    <#
    .SYNOPSIS
        Downloads a file with retry / exponential backoff and verifies it is non-empty.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)] [string] $Url,
        [Parameter(Mandatory = $true)] [string] $Destination,
        [int] $MaxRetries = 4
    )

    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12 -bor [Net.SecurityProtocolType]::Tls11
    $delay = 2
    for ($attempt = 1; $attempt -le $MaxRetries; $attempt++) {
        try {
            $progPref = $ProgressPreference
            $ProgressPreference = 'SilentlyContinue'   # massive speed-up for Invoke-WebRequest
            Invoke-WebRequest -Uri $Url -OutFile $Destination -UseBasicParsing -TimeoutSec 600 -Headers @{ 'User-Agent' = 'RetroBat-AutoSetup' } -ErrorAction Stop
            $ProgressPreference = $progPref

            if ((Test-Path -LiteralPath $Destination) -and ((Get-Item -LiteralPath $Destination).Length -gt 0)) {
                return $true
            }
            throw 'Downloaded file is empty.'
        } catch {
            if ($attempt -ge $MaxRetries) { throw }
            Start-Sleep -Seconds $delay
            $delay *= 2
        }
    }
    return $false
}

function Expand-DownloadedArchive {
    <#
    .SYNOPSIS
        Extracts a downloaded archive into a destination folder.
    .DESCRIPTION
        Uses 7-Zip for .7z (and .zip when present); falls back to Expand-Archive
        for .zip. Self-extracting .exe installers (e.g. MAME) are run with 7-Zip
        which can open them as archives.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)] [string] $ArchivePath,
        [Parameter(Mandatory = $true)] [string] $Destination,
        [Parameter(Mandatory = $true)] [string] $ArchiveType,
        [string] $SevenZip
    )

    if (-not (Test-Path -LiteralPath $Destination)) {
        New-Item -Path $Destination -ItemType Directory -Force | Out-Null
    }

    # .7z and self-extracting .exe archives require 7-Zip. .zip can use 7-Zip
    # when available (faster, handles edge cases) or fall back to .NET extraction.
    $useSevenZip = ($ArchiveType -in @('7z', 'sfx')) -or ($ArchiveType -eq 'zip' -and $SevenZip)

    if ($useSevenZip) {
        if (-not $SevenZip) {
            throw "Archive type '$ArchiveType' requires 7-Zip but none was found."
        }
        $sevenArgs = @('x', $ArchivePath, "-o$Destination", '-y', '-aoa')
        $proc = Start-Process -FilePath $SevenZip -ArgumentList $sevenArgs -NoNewWindow -Wait -PassThru
        if ($proc.ExitCode -ne 0) {
            throw "7-Zip extraction failed (exit code $($proc.ExitCode))."
        }
    }
    elseif ($ArchiveType -eq 'zip') {
        Expand-Archive -LiteralPath $ArchivePath -DestinationPath $Destination -Force
    }
    else {
        throw "Unsupported archive type: $ArchiveType"
    }
}

function Move-ExtractedPayload {
    <#
    .SYNOPSIS
        Copies extracted content into the emulator folder, optionally collapsing a
        single redundant top-level folder (stripRootFolder).
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)] [string] $StagingDir,
        [Parameter(Mandatory = $true)] [string] $TargetDir,
        [bool] $StripRootFolder = $false
    )

    if (-not (Test-Path -LiteralPath $TargetDir)) {
        New-Item -Path $TargetDir -ItemType Directory -Force | Out-Null
    }

    $source = $StagingDir
    if ($StripRootFolder) {
        $entries = @(Get-ChildItem -LiteralPath $StagingDir -Force)
        $dirs    = @($entries | Where-Object { $_.PSIsContainer })
        $files   = @($entries | Where-Object { -not $_.PSIsContainer })
        if ($dirs.Count -eq 1 -and $files.Count -eq 0) {
            $source = $dirs[0].FullName
        }
    }

    Get-ChildItem -LiteralPath $source -Force | ForEach-Object {
        Copy-Item -LiteralPath $_.FullName -Destination $TargetDir -Recurse -Force
    }
}

function Install-Emulator {
    <#
    .SYNOPSIS
        Downloads, extracts, installs and verifies a single emulator.
    .OUTPUTS
        Hashtable: Success (bool), Message (string), ExecutablePath (string|null).
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)] [object] $Emulator,
        [Parameter(Mandatory = $true)] [string] $RetroBatRoot,
        [Parameter(Mandatory = $true)] [scriptblock] $Logger
    )

    $log = { param($m, $l) & $Logger $m $l }

    $def = $Emulator.Definition
    & $log "Preparing installation of $($Emulator.DisplayName)..." 'INFO'

    $resolved = Resolve-DownloadUrl -Download $def.download
    if (-not $resolved) {
        return @{ Success = $false; Message = "No download URL could be resolved."; ExecutablePath = $null }
    }
    & $log "Resolved download URL: $($resolved.Url)" 'INFO'

    $tempBase = Join-Path $env:TEMP ("RetroBatSetup_{0}_{1}" -f $Emulator.Id, (Get-Date -Format 'yyyyMMddHHmmss'))
    $dlPath   = Join-Path $tempBase $resolved.FileName
    $staging  = Join-Path $tempBase 'extracted'
    New-Item -Path $tempBase -ItemType Directory -Force | Out-Null

    try {
        & $log "Downloading $($resolved.FileName)..." 'INFO'
        [void](Invoke-FileDownload -Url $resolved.Url -Destination $dlPath)
        $sizeMB = [math]::Round((Get-Item -LiteralPath $dlPath).Length / 1MB, 2)
        & $log "Download complete ($sizeMB MB)." 'SUCCESS'

        $sevenZip = Get-SevenZipPath -RetroBatRoot $RetroBatRoot
        $archType = $def.download.archive
        & $log "Extracting archive (type=$archType)..." 'INFO'
        Expand-DownloadedArchive -ArchivePath $dlPath -Destination $staging -ArchiveType $archType -SevenZip $sevenZip

        $strip = $false
        if ($def.download.PSObject.Properties.Name -contains 'stripRootFolder') {
            $strip = [bool]$def.download.stripRootFolder
        }
        & $log "Installing into $($Emulator.FolderPath)..." 'INFO'
        Move-ExtractedPayload -StagingDir $staging -TargetDir $Emulator.FolderPath -StripRootFolder $strip

        # ---- Verify ----
        $exe = Find-EmulatorExecutable -Folder $Emulator.FolderPath -Executables $def.executables
        if ($exe) {
            & $log "Verified: $($Emulator.DisplayName) executable present at $exe" 'SUCCESS'
            return @{ Success = $true; Message = 'Installed and verified.'; ExecutablePath = $exe }
        } else {
            & $log "Installation completed but no expected executable was found." 'WARN'
            return @{ Success = $false; Message = 'Executable not found after extraction.'; ExecutablePath = $null }
        }
    } catch {
        & $log "Installation failed: $($_.Exception.Message)" 'ERROR'
        return @{ Success = $false; Message = $_.Exception.Message; ExecutablePath = $null }
    } finally {
        if (Test-Path -LiteralPath $tempBase) {
            Remove-Item -LiteralPath $tempBase -Recurse -Force -ErrorAction SilentlyContinue
        }
    }
}

Export-ModuleMember -Function Get-SevenZipPath, Resolve-DownloadUrl, Invoke-FileDownload, Expand-DownloadedArchive, Move-ExtractedPayload, Install-Emulator
