<#
.SYNOPSIS
    Media download engine - downloads ONLY missing assets from ScreenScraper, the
    official scraping source used by ES-DE.
.DESCRIPTION
    Uses the ScreenScraper jeuInfos API. Requires API credentials supplied via
    environment variables (never hard-coded, never logged):
        SS_DEVID, SS_DEVPASSWORD   (developer API id/password)
        SS_USER,  SS_PASSWORD      (a ScreenScraper member account)
    For each game missing media, the ROM CRC32 is computed and used to look up the
    game; missing media types are then downloaded into downloaded_media. If no
    credentials are configured the engine reports that scraping is unavailable and
    downloads nothing (the missing-media report still lists what is needed).
#>

Set-StrictMode -Version Latest

# Map ES-DE media folders to ScreenScraper media type identifiers.
$script:EsdeToSsMedia = @{
    'covers'       = 'box-2D'
    '3dboxes'      = 'box-3D'
    'backcovers'   = 'box-2D-back'
    'marquees'     = 'wheel'
    'screenshots'  = 'ss'
    'titlescreens' = 'sstitle'
    'fanart'       = 'fanart'
    'videos'       = 'video'
    'miximages'    = 'mixrbv2'
}

function Test-ScraperCredentials {
    [CmdletBinding()] param()
    return -not ([string]::IsNullOrWhiteSpace($env:SS_DEVID) -or
                 [string]::IsNullOrWhiteSpace($env:SS_DEVPASSWORD) -or
                 [string]::IsNullOrWhiteSpace($env:SS_USER) -or
                 [string]::IsNullOrWhiteSpace($env:SS_PASSWORD))
}

function Get-FileCrc32 {
    <#
    .SYNOPSIS
        Computes the CRC32 (hex, upper) of a file - the identifier ScreenScraper
        uses to match a ROM.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][string] $Path)

    # All arithmetic is done in [long] with an explicit 32-bit mask. Constants use
    # decimal form because the PowerShell literal 0xFFFFFFFF parses as [int] -1.
    $mask = [long]4294967295      # 0xFFFFFFFF
    $poly = [long]3988292384      # 0xEDB88320
    $table = New-Object 'System.UInt32[]' 256
    for ($i = 0; $i -lt 256; $i++) {
        $c = [long]$i
        for ($k = 0; $k -lt 8; $k++) {
            if (($c -band 1) -ne 0) { $c = ($poly -bxor ($c -shr 1)) -band $mask }
            else { $c = ($c -shr 1) -band $mask }
        }
        $table[$i] = [uint32]$c
    }
    $crc = $mask  # 0xFFFFFFFF
    try {
        $fs = [System.IO.File]::OpenRead($Path)
        try {
            $buf = New-Object byte[] 65536
            while (($read = $fs.Read($buf, 0, $buf.Length)) -gt 0) {
                for ($n = 0; $n -lt $read; $n++) {
                    $idx = [int](($crc -bxor [long]$buf[$n]) -band 255)
                    $crc = (($crc -shr 8) -band $mask) -bxor [long]$table[$idx]
                }
            }
        } finally { $fs.Dispose() }
    } catch { return $null }
    $crc = ($crc -bxor $mask) -band $mask
    return ('{0:X8}' -f [uint32]$crc)
}

function Invoke-ScreenScraperLookup {
    <#
    .SYNOPSIS
        Calls jeuInfos for a CRC and returns the parsed jeu object, or $null.
    #>
    [CmdletBinding()]
    param([string] $Crc, [string] $RomName, [int] $SystemId = 0)

    $base = 'https://api.screenscraper.fr/api2/jeuInfos.php'
    $q = @{
        devid       = $env:SS_DEVID
        devpassword = $env:SS_DEVPASSWORD
        softname    = 'ESDEAutoSuite'
        output      = 'json'
        ssid        = $env:SS_USER
        sspassword  = $env:SS_PASSWORD
        crc         = $Crc
        romnom      = $RomName
    }
    if ($SystemId -gt 0) { $q['systemeid'] = $SystemId }
    $query = ($q.GetEnumerator() | ForEach-Object { "{0}={1}" -f $_.Key, [uri]::EscapeDataString([string]$_.Value) }) -join '&'
    $url = "$base`?$query"
    try {
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        $resp = Invoke-RestMethod -Uri $url -TimeoutSec 60 -ErrorAction Stop
        if ($resp -and $resp.response -and $resp.response.jeu) { return $resp.response.jeu }
    } catch { return $null }
    return $null
}

function Save-ScreenScraperMedia {
    <#
    .SYNOPSIS
        Downloads the requested media types for one game into downloaded_media.
    .OUTPUTS
        Count of files downloaded.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][object]   $Jeu,
        [Parameter(Mandatory = $true)][string]   $RomStem,
        [Parameter(Mandatory = $true)][string]   $SystemMediaDir,
        [Parameter(Mandatory = $true)][string[]] $MissingTypes,
        [Parameter(Mandatory = $true)][scriptblock] $Logger
    )
    $downloaded = 0
    if (-not ($Jeu.PSObject.Properties.Name -contains 'medias')) { return 0 }
    $medias = @($Jeu.medias)

    foreach ($type in $MissingTypes) {
        if (-not $script:EsdeToSsMedia.ContainsKey($type)) { continue }
        $ssType = $script:EsdeToSsMedia[$type]
        $media = $medias | Where-Object { $_.type -eq $ssType } | Select-Object -First 1
        if (-not $media -or -not $media.url) { continue }
        $ext = if ($media.PSObject.Properties.Name -contains 'format' -and $media.format) { '.' + $media.format } else { if ($type -eq 'videos') { '.mp4' } else { '.png' } }
        $destDir = Join-Path $SystemMediaDir $type
        if (-not (Test-Path -LiteralPath $destDir)) { New-Item -Path $destDir -ItemType Directory -Force | Out-Null }
        $dest = Join-Path $destDir ($RomStem + $ext)
        if (Test-Path -LiteralPath $dest) { continue }   # never re-download existing
        try {
            $prog = $ProgressPreference; $ProgressPreference = 'SilentlyContinue'
            Invoke-WebRequest -Uri $media.url -OutFile $dest -TimeoutSec 120 -UseBasicParsing -ErrorAction Stop
            $ProgressPreference = $prog
            if ((Test-Path -LiteralPath $dest) -and (Get-Item -LiteralPath $dest).Length -gt 0) {
                $downloaded++
                & $Logger "Downloaded $type for '$RomStem'." 'SUCCESS'
            }
        } catch {
            & $Logger "Download failed ($type/$RomStem): $($_.Exception.Message)" 'WARN'
        }
    }
    return $downloaded
}

function Invoke-MediaDownloadForSystem {
    <#
    .SYNOPSIS
        Downloads missing media for a system's games via ScreenScraper.
    .OUTPUTS
        Hashtable: Attempted, Downloaded, Skipped.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string] $SystemRomDir,
        [Parameter(Mandatory = $true)][string] $SystemMediaDir,
        [Parameter(Mandatory = $true)][object] $MissingResult,    # from Get-MissingMediaForSystem
        [Parameter(Mandatory = $true)][scriptblock] $Logger,
        [int] $MaxGames = 0,
        [switch] $DryRun
    )
    $stats = @{ Attempted = 0; Downloaded = 0; Skipped = 0 }
    if (-not (Test-ScraperCredentials)) {
        & $Logger "ScreenScraper credentials not configured (SS_DEVID/SS_DEVPASSWORD/SS_USER/SS_PASSWORD). Skipping downloads; see missing-media report." 'WARN'
        return $stats
    }

    # Build a stem -> ROM file lookup for CRC computation.
    $romByStem = @{}
    if (Test-Path -LiteralPath $SystemRomDir) {
        Get-ChildItem -LiteralPath $SystemRomDir -File -ErrorAction SilentlyContinue | ForEach-Object {
            $romByStem[[System.IO.Path]::GetFileNameWithoutExtension($_.Name)] = $_.FullName
        }
    }

    $records = @($MissingResult.Records)
    foreach ($rec in $records) {
        if ($MaxGames -gt 0 -and $stats.Attempted -ge $MaxGames) { break }
        $stem = $rec.Game
        if (-not $romByStem.ContainsKey($stem)) { $stats.Skipped++; continue }
        $stats.Attempted++
        if ($DryRun) { & $Logger "[DRY-RUN] Would scrape '$stem' for: $($rec.Missing -join ', ')" 'INFO'; continue }

        $rom = $romByStem[$stem]
        $crc = Get-FileCrc32 -Path $rom
        $jeu = Invoke-ScreenScraperLookup -Crc $crc -RomName (Split-Path $rom -Leaf)
        if (-not $jeu) { $stats.Skipped++; continue }
        $stats.Downloaded += (Save-ScreenScraperMedia -Jeu $jeu -RomStem $stem -SystemMediaDir $SystemMediaDir -MissingTypes $rec.Missing -Logger $Logger)
    }
    return $stats
}

Export-ModuleMember -Function Test-ScraperCredentials, Get-FileCrc32, Invoke-ScreenScraperLookup, Save-ScreenScraperMedia, Invoke-MediaDownloadForSystem
