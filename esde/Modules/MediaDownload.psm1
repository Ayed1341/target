<#
.SYNOPSIS
    Media download engine - downloads ONLY missing assets from ScreenScraper, the
    official scraping source used by ES-DE, while strictly respecting the account's
    quota.
.DESCRIPTION
    Uses the ScreenScraper jeuInfos API. Credentials are supplied EITHER via
    environment variables or a local, git-ignored credential file (never hard-coded
    into the script, never committed, never logged):
        SS_DEVID, SS_DEVPASSWORD   (developer API id/password)
        SS_USER,  SS_PASSWORD      (a ScreenScraper member account)
    The engine plays by ScreenScraper's rules instead of trying to evade them:
      * it reads the per-account allowance the API returns (max threads, requests
        per minute, requests per day) and throttles itself to stay under it;
      * it backs off on transient "server busy" (HTTP 429) responses;
      * it stops cleanly for the day when the daily quota is reached or the API is
        closed - it does NOT spoof devices or rotate identities to get more;
      * it only ever fetches media that is still missing and never re-downloads an
        existing file, so simply re-running on another day resumes where it left
        off until the whole library is complete.
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

# Live quota / rate-limit state for the current run (server-reported values win).
$script:ScraperState = @{
    Closed          = $false   # daily quota reached or API closed - stop for now
    ClosedReason    = ''
    MaxRequestsMin  = 0
    MaxRequestsDay  = 0
    RequestsToday   = 0
    MaxThreads      = 0
    ThrottleMs      = 1500     # conservative default between calls until the API tells us better
    Requests        = 0        # calls made this run
    LastRequestTick = 0
}

function Reset-ScraperState {
    [CmdletBinding()] param()
    $script:ScraperState.Closed = $false
    $script:ScraperState.ClosedReason = ''
    $script:ScraperState.Requests = 0
    $script:ScraperState.LastRequestTick = 0
}

function Import-ScraperCredentials {
    <#
    .SYNOPSIS
        Loads ScreenScraper credentials from a local git-ignored file when the
        environment variables are not already set. Returns $true if all four
        credentials are available afterwards. The password is never logged.
    .DESCRIPTION
        Looked-up file names (first match wins) in each search dir:
            screenscraper.txt / screenscraper.cfg / .screenscraper
        Accepted line formats (case-insensitive keys, '#' comments ignored):
            user= / ssid=            -> SS_USER
            password= / sspassword=  -> SS_PASSWORD
            devid=                   -> SS_DEVID
            devpassword=             -> SS_DEVPASSWORD
    #>
    [CmdletBinding()]
    param(
        [string[]] $SearchDirs = @(),
        [scriptblock] $Logger
    )
    $keymap = @{
        'user' = 'SS_USER'; 'ssid' = 'SS_USER'
        'password' = 'SS_PASSWORD'; 'sspassword' = 'SS_PASSWORD'
        'devid' = 'SS_DEVID'; 'devpassword' = 'SS_DEVPASSWORD'
    }
    $names = @('screenscraper.txt', 'screenscraper.cfg', '.screenscraper')
    foreach ($dir in ($SearchDirs | Where-Object { $_ } | Select-Object -Unique)) {
        foreach ($n in $names) {
            $file = Join-Path $dir $n
            if (-not (Test-Path -LiteralPath $file)) { continue }
            $user = $null
            foreach ($raw in (Get-Content -LiteralPath $file -ErrorAction SilentlyContinue)) {
                $line = $raw.Trim()
                if ($line.Length -eq 0 -or $line.StartsWith('#') -or $line.StartsWith(';')) { continue }
                $idx = $line.IndexOf('='); if ($idx -lt 1) { continue }
                $k = $line.Substring(0, $idx).Trim().ToLower()
                $v = $line.Substring($idx + 1).Trim().Trim('"')
                if (-not $keymap.ContainsKey($k) -or [string]::IsNullOrWhiteSpace($v)) { continue }
                $envName = $keymap[$k]
                # Only fill in what the environment has not already provided.
                if ([string]::IsNullOrWhiteSpace([Environment]::GetEnvironmentVariable($envName))) {
                    Set-Item -Path ("env:" + $envName) -Value $v
                }
                if ($envName -eq 'SS_USER') { $user = $v }
            }
            if ($Logger) {
                $who = if ($user) { "user '$user'" } else { 'credentials' }
                & $Logger "Loaded ScreenScraper $who from $file (password not shown)." 'INFO'
            }
            break
        }
    }
    return (Test-ScraperCredentials)
}

function Test-ScraperCredentials {
    [CmdletBinding()] param()
    return -not ([string]::IsNullOrWhiteSpace($env:SS_DEVID) -or
                 [string]::IsNullOrWhiteSpace($env:SS_DEVPASSWORD) -or
                 [string]::IsNullOrWhiteSpace($env:SS_USER) -or
                 [string]::IsNullOrWhiteSpace($env:SS_PASSWORD))
}

function Get-MissingScraperCredentials {
    <#
    .SYNOPSIS
        Returns the friendly names of any credentials still missing (for a helpful
        message), e.g. @('SS_DEVID','SS_DEVPASSWORD').
    #>
    [CmdletBinding()] param()
    $miss = New-Object System.Collections.Generic.List[string]
    foreach ($p in @('SS_DEVID','SS_DEVPASSWORD','SS_USER','SS_PASSWORD')) {
        if ([string]::IsNullOrWhiteSpace([Environment]::GetEnvironmentVariable($p))) { $miss.Add($p) }
    }
    return $miss.ToArray()
}

function Get-ScraperQuotaSummary {
    <#
    .SYNOPSIS
        Returns a snapshot of the current quota state for reporting / persistence.
    #>
    [CmdletBinding()] param()
    return @{
        Closed         = [bool]$script:ScraperState.Closed
        ClosedReason   = [string]$script:ScraperState.ClosedReason
        RequestsToday  = [int]$script:ScraperState.RequestsToday
        MaxRequestsDay = [int]$script:ScraperState.MaxRequestsDay
        MaxRequestsMin = [int]$script:ScraperState.MaxRequestsMin
        MaxThreads     = [int]$script:ScraperState.MaxThreads
        RequestsThisRun= [int]$script:ScraperState.Requests
    }
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

function Update-ScraperQuotaFromResponse {
    <#
    .SYNOPSIS
        Reads the per-account allowance ScreenScraper returns in response.ssuser and
        updates throttle / stop state so we stay within the quota.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][object] $Response)
    if (-not ($Response.PSObject.Properties.Name -contains 'response')) { return }
    $r = $Response.response
    if (-not ($r.PSObject.Properties.Name -contains 'ssuser') -or -not $r.ssuser) { return }
    $u = $r.ssuser
    function _num($o, $n) { if ($o.PSObject.Properties.Name -contains $n -and $o.$n) { $v = 0; [void][int]::TryParse([string]$o.$n, [ref]$v); return $v } return 0 }

    $maxMin = _num $u 'maxrequestspermin'
    $maxDay = _num $u 'maxrequestsperday'
    $today  = _num $u 'requeststoday'
    $thr    = _num $u 'maxthreads'
    if ($maxMin -gt 0) { $script:ScraperState.MaxRequestsMin = $maxMin; $script:ScraperState.ThrottleMs = [int][math]::Ceiling(60000.0 / $maxMin) }
    if ($maxDay -gt 0) { $script:ScraperState.MaxRequestsDay = $maxDay }
    if ($today  -gt 0) { $script:ScraperState.RequestsToday  = $today }
    if ($thr    -gt 0) { $script:ScraperState.MaxThreads     = $thr }

    # Stop a little before the hard cap so we never trip a soft-ban.
    if ($maxDay -gt 0 -and $today -ge ($maxDay - 1)) {
        $script:ScraperState.Closed = $true
        $script:ScraperState.ClosedReason = "Daily quota reached ($today/$maxDay)."
    }
}

function Invoke-ScreenScraperLookup {
    <#
    .SYNOPSIS
        Calls jeuInfos for a CRC, honours throttle/backoff and updates quota state.
        Returns the parsed jeu object, or $null. Sets $script:ScraperState.Closed
        when the daily quota is reached / the API is closed.
    #>
    [CmdletBinding()]
    param([string] $Crc, [string] $RomName, [int] $SystemId = 0)

    if ($script:ScraperState.Closed) { return $null }

    # Throttle: keep at least ThrottleMs between requests.
    $now = [Environment]::TickCount
    $since = $now - [int]$script:ScraperState.LastRequestTick
    if ($script:ScraperState.LastRequestTick -ne 0 -and $since -lt $script:ScraperState.ThrottleMs) {
        Start-Sleep -Milliseconds ([int]($script:ScraperState.ThrottleMs - $since))
    }

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

    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    $maxBusyRetry = 3
    $delay = 4
    for ($attempt = 1; $attempt -le ($maxBusyRetry + 1); $attempt++) {
        try {
            $resp = Invoke-RestMethod -Uri $url -TimeoutSec 60 -ErrorAction Stop
            $script:ScraperState.Requests++
            $script:ScraperState.LastRequestTick = [Environment]::TickCount
            try { Update-ScraperQuotaFromResponse -Response $resp } catch { }
            if ($resp -and $resp.response -and $resp.response.jeu) { return $resp.response.jeu }
            return $null
        } catch {
            $script:ScraperState.LastRequestTick = [Environment]::TickCount
            $code = 0
            try {
                $r = $_.Exception.Response
                if ($r) { $code = [int]$r.StatusCode }
            } catch { }
            # 429 = server busy right now: back off and retry the same request.
            if ($code -eq 429 -and $attempt -le $maxBusyRetry) {
                Start-Sleep -Seconds $delay; $delay *= 2; continue
            }
            # 423/426/430/431 = quota exceeded / API closed for this account: stop.
            if ($code -in @(423, 426, 430, 431)) {
                $script:ScraperState.Closed = $true
                $script:ScraperState.ClosedReason = "API returned HTTP $code (quota exhausted or API closed)."
                return $null
            }
            # Anything else (404/timeout/no-match): just skip this game.
            return $null
        }
    }
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
        if ($script:ScraperState.Closed) { break }
        if (-not $script:EsdeToSsMedia.ContainsKey($type)) { continue }
        $ssType = $script:EsdeToSsMedia[$type]
        $media = $medias | Where-Object { $_.type -eq $ssType } | Select-Object -First 1
        if (-not $media -or -not $media.url) { continue }
        $ext = if ($media.PSObject.Properties.Name -contains 'format' -and $media.format) { '.' + $media.format } else { if ($type -eq 'videos') { '.mp4' } else { '.png' } }
        $destDir = Join-Path $SystemMediaDir $type
        if (-not (Test-Path -LiteralPath $destDir)) { New-Item -Path $destDir -ItemType Directory -Force | Out-Null }
        $dest = Join-Path $destDir ($RomStem + $ext)
        if (Test-Path -LiteralPath $dest) { continue }   # never re-download existing (resume)
        try {
            $prog = $ProgressPreference; $ProgressPreference = 'SilentlyContinue'
            Invoke-WebRequest -Uri $media.url -OutFile $dest -TimeoutSec 120 -UseBasicParsing -ErrorAction Stop
            $ProgressPreference = $prog
            if ((Test-Path -LiteralPath $dest) -and (Get-Item -LiteralPath $dest).Length -gt 0) {
                $downloaded++
                & $Logger "Downloaded $type for '$RomStem'." 'SUCCESS'
            } else {
                if (Test-Path -LiteralPath $dest) { Remove-Item -LiteralPath $dest -Force -ErrorAction SilentlyContinue }
            }
        } catch {
            if (Test-Path -LiteralPath $dest) { Remove-Item -LiteralPath $dest -Force -ErrorAction SilentlyContinue }
            $code = 0; try { if ($_.Exception.Response) { $code = [int]$_.Exception.Response.StatusCode } } catch { }
            if ($code -in @(423, 426, 429, 430, 431)) {
                $script:ScraperState.Closed = $true
                $script:ScraperState.ClosedReason = "Media download returned HTTP $code (quota/bandwidth limit)."
                break
            }
            & $Logger "Download failed ($type/$RomStem): $($_.Exception.Message)" 'WARN'
        }
    }
    return $downloaded
}

function Invoke-MediaDownloadForSystem {
    <#
    .SYNOPSIS
        Downloads missing media for a system's games via ScreenScraper, stopping
        cleanly when the account quota is reached.
    .OUTPUTS
        Hashtable: Attempted, Downloaded, Skipped, Closed.
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
    $stats = @{ Attempted = 0; Downloaded = 0; Skipped = 0; Closed = $false }
    if (-not (Test-ScraperCredentials)) {
        & $Logger "ScreenScraper credentials not configured (SS_DEVID/SS_DEVPASSWORD/SS_USER/SS_PASSWORD). Skipping downloads; see missing-media report." 'WARN'
        return $stats
    }
    if ($script:ScraperState.Closed) { $stats.Closed = $true; return $stats }

    # Build a stem -> ROM file lookup for CRC computation.
    $romByStem = @{}
    if (Test-Path -LiteralPath $SystemRomDir) {
        Get-ChildItem -LiteralPath $SystemRomDir -File -ErrorAction SilentlyContinue | ForEach-Object {
            $romByStem[[System.IO.Path]::GetFileNameWithoutExtension($_.Name)] = $_.FullName
        }
    }

    $records = @($MissingResult.Records)
    foreach ($rec in $records) {
        if ($script:ScraperState.Closed) { $stats.Closed = $true; break }
        if ($MaxGames -gt 0 -and $stats.Attempted -ge $MaxGames) { break }
        $stem = $rec.Game
        if (-not $romByStem.ContainsKey($stem)) { $stats.Skipped++; continue }
        $stats.Attempted++
        if ($DryRun) { & $Logger "[DRY-RUN] Would scrape '$stem' for: $($rec.Missing -join ', ')" 'INFO'; continue }

        $rom = $romByStem[$stem]
        $crc = Get-FileCrc32 -Path $rom
        $jeu = Invoke-ScreenScraperLookup -Crc $crc -RomName (Split-Path $rom -Leaf)
        if ($script:ScraperState.Closed) { $stats.Closed = $true; break }
        if (-not $jeu) { $stats.Skipped++; continue }
        $stats.Downloaded += (Save-ScreenScraperMedia -Jeu $jeu -RomStem $stem -SystemMediaDir $SystemMediaDir -MissingTypes $rec.Missing -Logger $Logger)
    }
    if ($script:ScraperState.Closed) { $stats.Closed = $true }
    return $stats
}

Export-ModuleMember -Function Test-ScraperCredentials, Get-MissingScraperCredentials, Import-ScraperCredentials, `
    Reset-ScraperState, Get-ScraperQuotaSummary, Update-ScraperQuotaFromResponse, Get-FileCrc32, `
    Invoke-ScreenScraperLookup, Save-ScreenScraperMedia, Invoke-MediaDownloadForSystem
