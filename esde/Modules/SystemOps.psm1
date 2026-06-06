<#
.SYNOPSIS
    System operations: storage health, telemetry, scheduled task, desktop shortcut,
    log rotation, emulator config-drift detection and a suite update check.
#>

Set-StrictMode -Version Latest

function Get-StorageHealth {
    <#
    .SYNOPSIS
        Returns SMART/health status for physical disks (best-effort via CIM).
    #>
    [CmdletBinding()] param()
    $disks = New-Object System.Collections.Generic.List[object]
    try {
        if (Get-Command Get-PhysicalDisk -ErrorAction SilentlyContinue) {
            Get-PhysicalDisk -ErrorAction Stop | ForEach-Object {
                $disks.Add(@{ Name=$_.FriendlyName; Health=[string]$_.HealthStatus; Media=[string]$_.MediaType; SizeGB=[math]::Round($_.Size/1GB,0) })
            }
        } else {
            Get-CimInstance -ClassName Win32_DiskDrive -ErrorAction Stop | ForEach-Object {
                $disks.Add(@{ Name=$_.Model; Health=[string]$_.Status; Media='Unknown'; SizeGB=[math]::Round([int64]$_.Size/1GB,0) })
            }
        }
    } catch { }
    return $disks.ToArray()
}

function Get-SystemTelemetry {
    <#
    .SYNOPSIS
        Returns a snapshot of uptime, memory usage and OS info (best-effort).
    #>
    [CmdletBinding()] param()
    $t = @{ UptimeHours=0; MemoryUsedPct=0; OS='' }
    try {
        $os = Get-CimInstance -ClassName Win32_OperatingSystem -ErrorAction Stop
        if ($os) {
            $t.OS = $os.Caption
            $last = $os.LastBootUpTime
            if ($last) { $t.UptimeHours = [math]::Round(((Get-Date) - $last).TotalHours,1) }
            if ($os.TotalVisibleMemorySize -gt 0) {
                $used = $os.TotalVisibleMemorySize - $os.FreePhysicalMemory
                $t.MemoryUsedPct = [math]::Round(($used * 100.0) / $os.TotalVisibleMemorySize,1)
            }
        }
    } catch { }
    return $t
}

function Register-EsdeScheduledTask {
    <#
    .SYNOPSIS
        Creates/updates a weekly scheduled task to run the suite. Returns $true.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string] $LauncherPath,
        [Parameter(Mandatory = $true)][scriptblock] $Logger,
        [switch] $DryRun
    )
    if (-not (Test-Path -LiteralPath $LauncherPath)) { return $false }
    if ($DryRun) { & $Logger "[DRY-RUN] Would register weekly scheduled task." 'INFO'; return $false }
    try {
        $name = 'ES-DE Auto Suite Weekly'
        $cmd  = "schtasks /Create /F /SC WEEKLY /D SUN /TN `"$name`" /TR `"'$LauncherPath' /nogit`" /ST 03:00"
        $p = Start-Process -FilePath 'cmd.exe' -ArgumentList @('/c', $cmd) -NoNewWindow -Wait -PassThru
        if ($p.ExitCode -eq 0) { & $Logger "Registered weekly scheduled task '$name' (Sun 03:00)." 'SUCCESS'; return $true }
        & $Logger "Could not register scheduled task (exit $($p.ExitCode))." 'WARN'
    } catch { & $Logger "Scheduled task error: $($_.Exception.Message)" 'WARN' }
    return $false
}

function New-EsdeShortcut {
    <#
    .SYNOPSIS
        Creates a desktop shortcut to a target. Returns $true if created.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string] $Target,
        [Parameter(Mandatory = $true)][string] $ShortcutName,
        [Parameter(Mandatory = $true)][scriptblock] $Logger,
        [switch] $DryRun
    )
    if (-not (Test-Path -LiteralPath $Target)) { return $false }
    $desktop = [Environment]::GetFolderPath('Desktop')
    if (-not $desktop) { return $false }
    $lnk = Join-Path $desktop ($ShortcutName + '.lnk')
    if ($DryRun) { & $Logger "[DRY-RUN] Would create desktop shortcut $ShortcutName." 'INFO'; return $false }
    try {
        $sh = New-Object -ComObject WScript.Shell
        $sc = $sh.CreateShortcut($lnk)
        $sc.TargetPath = $Target
        $sc.WorkingDirectory = (Split-Path $Target -Parent)
        $sc.Save()
        & $Logger "Created desktop shortcut: $lnk" 'SUCCESS'
        return $true
    } catch { & $Logger "Shortcut error: $($_.Exception.Message)" 'WARN'; return $false }
}

function Invoke-LogRotation {
    <#
    .SYNOPSIS
        Compresses log files older than $Days into a dated zip and removes the
        originals. Returns count compressed.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string] $LogsDir,
        [int] $Days = 7,
        [switch] $DryRun
    )
    if (-not (Test-Path -LiteralPath $LogsDir)) { return 0 }
    $cutoff = (Get-Date).AddDays(-$Days)
    $old = @(Get-ChildItem -LiteralPath $LogsDir -File -Filter '*.log' -ErrorAction SilentlyContinue | Where-Object { $_.LastWriteTime -lt $cutoff })
    if ($old.Count -eq 0) { return 0 }
    if ($DryRun) { return $old.Count }
    $zip = Join-Path $LogsDir ("logs_archive_{0}.zip" -f (Get-Date -Format 'yyyyMMdd_HHmmss'))
    try {
        Add-Type -AssemblyName System.IO.Compression.FileSystem -ErrorAction SilentlyContinue
        $archive = [System.IO.Compression.ZipFile]::Open($zip, [System.IO.Compression.ZipArchiveMode]::Create)
        try {
            foreach ($f in $old) { [System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile($archive, $f.FullName, $f.Name) | Out-Null }
        } finally { $archive.Dispose() }
        foreach ($f in $old) { Remove-Item -LiteralPath $f.FullName -Force -ErrorAction SilentlyContinue }
        return $old.Count
    } catch { return 0 }
}

function Test-ConfigDrift {
    <#
    .SYNOPSIS
        Compares current emulator config files against the newest emulator_configs_*
        archive and returns the count of changed files.
    #>
    [CmdletBinding()]
    param(
        [string[]] $EmulatorRoots = @(),
        [Parameter(Mandatory = $true)][string]   $BackupRoot
    )
    if (-not $EmulatorRoots -or $EmulatorRoots.Count -eq 0) { return -1 }
    if (-not (Test-Path -LiteralPath $BackupRoot)) { return -1 }
    $latest = Get-ChildItem -LiteralPath $BackupRoot -Directory -Filter 'emulator_configs_*' -ErrorAction SilentlyContinue |
              Sort-Object Name -Descending | Select-Object -First 1
    if (-not $latest) { return -1 }   # no baseline yet
    $changed = 0
    foreach ($root in $EmulatorRoots) {
        if (-not (Test-Path -LiteralPath $root)) { continue }
        $leaf = Split-Path $root -Leaf
        $base = Join-Path $latest.FullName $leaf
        if (-not (Test-Path -LiteralPath $base)) { continue }
        # Pruned, depth-bounded walk (shared with the config archive) so drift
        # detection no longer hashes emulators' thousands of bundled config files.
        Get-EmulatorConfigFiles -Root $root | ForEach-Object {
            $rel = $_.FullName.Substring($root.Length).TrimStart('\','/')
            $old = Join-Path $base $rel
            if (Test-Path -LiteralPath $old) {
                $h1 = (Get-FileSha256 -Path $_.FullName); $h2 = (Get-FileSha256 -Path $old)
                if ($h1 -and $h2 -and $h1 -ne $h2) { $changed++ }
            }
        }
    }
    return $changed
}

function Test-SuiteUpdate {
    <#
    .SYNOPSIS
        Best-effort check of a remote VERSION marker against the local suite version.
        Returns @{ Local; Remote; UpdateAvailable }.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][string] $LocalVersion)
    $result = @{ Local=$LocalVersion; Remote=''; UpdateAvailable=$false }
    try {
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        $url = 'https://raw.githubusercontent.com/Ayed1341/target/claude/retrobat-windows-automation-d2ilQ/esde/VERSION'
        $r = Invoke-WebRequest -Uri $url -TimeoutSec 8 -UseBasicParsing -ErrorAction Stop
        $remote = ($r.Content).Trim()
        if ($remote) {
            $result.Remote = $remote
            try { $result.UpdateAvailable = ([version]$remote -gt [version]$LocalVersion) } catch { $result.UpdateAvailable = ($remote -ne $LocalVersion) }
        }
    } catch { }
    return $result
}

Export-ModuleMember -Function Get-StorageHealth, Get-SystemTelemetry, Register-EsdeScheduledTask, New-EsdeShortcut, Invoke-LogRotation, Test-ConfigDrift, Test-SuiteUpdate
