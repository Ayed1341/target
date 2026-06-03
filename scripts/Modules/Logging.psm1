<#
.SYNOPSIS
    Centralized logging module for the RetroBat automation suite.
.DESCRIPTION
    Provides timestamped, leveled logging to multiple log files and the console.
    Every other module routes output through Write-Log so that all activity is
    captured under <RetroBatRoot>\Logs.
#>

Set-StrictMode -Version Latest

# Module-scoped state shared across all logging calls.
$script:LogRoot      = $null
$script:LogTargets   = @{}
$script:DefaultLog   = 'Setup'
$script:Initialized  = $false

# Mapping of logical log names to file names. The suite writes to these four
# files as mandated by the specification, plus a general fallback.
$script:LogFileMap = [ordered]@{
    'Setup'        = 'Setup.log'
    'Emulator'     = 'EmulatorOptimization.log'
    'Controller'   = 'ControllerSetup.log'
    'Installation' = 'Installation.log'
}

function Initialize-Logging {
    <#
    .SYNOPSIS
        Prepares the Logs directory and initializes all log files.
    .PARAMETER LogRoot
        Absolute path to the Logs directory (created if missing).
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string] $LogRoot
    )

    if (-not (Test-Path -LiteralPath $LogRoot)) {
        New-Item -Path $LogRoot -ItemType Directory -Force | Out-Null
    }

    $script:LogRoot    = $LogRoot
    $script:LogTargets = @{}

    foreach ($key in $script:LogFileMap.Keys) {
        $path = Join-Path $LogRoot $script:LogFileMap[$key]
        $script:LogTargets[$key] = $path
        # Touch the file so it always exists even if no message of that type fires.
        if (-not (Test-Path -LiteralPath $path)) {
            New-Item -Path $path -ItemType File -Force | Out-Null
        }
    }

    $script:Initialized = $true

    $header = "================ RetroBat Auto Setup session started $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') ================"
    foreach ($key in $script:LogFileMap.Keys) {
        Add-Content -LiteralPath $script:LogTargets[$key] -Value $header -Encoding UTF8
    }
}

function Write-Log {
    <#
    .SYNOPSIS
        Writes a timestamped, leveled message to a log file and the console.
    .PARAMETER Message
        The text to record.
    .PARAMETER Level
        One of INFO, WARN, ERROR, SUCCESS, DEBUG.
    .PARAMETER Category
        Which log file to write to: Setup, Emulator, Controller, Installation.
    .PARAMETER NoConsole
        Suppress console echo (file only).
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true, Position = 0)]
        [string] $Message,

        [ValidateSet('INFO', 'WARN', 'ERROR', 'SUCCESS', 'DEBUG')]
        [string] $Level = 'INFO',

        [ValidateSet('Setup', 'Emulator', 'Controller', 'Installation')]
        [string] $Category = 'Setup',

        [switch] $NoConsole
    )

    $timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss.fff'
    $line      = '[{0}] [{1,-7}] {2}' -f $timestamp, $Level, $Message

    # File output (always to the chosen category, ERROR/WARN also mirrored to Setup).
    if ($script:Initialized) {
        $targets = New-Object System.Collections.Generic.List[string]
        $targets.Add($script:LogTargets[$Category])
        if (($Level -eq 'ERROR' -or $Level -eq 'WARN') -and $Category -ne 'Setup') {
            $targets.Add($script:LogTargets['Setup'])
        }
        foreach ($t in ($targets | Select-Object -Unique)) {
            try {
                Add-Content -LiteralPath $t -Value $line -Encoding UTF8 -ErrorAction Stop
            } catch {
                # Last-resort: never let logging crash the run.
                Write-Host "LOGGING FAILURE -> $($_.Exception.Message)" -ForegroundColor Red
            }
        }
    }

    # Console output with colour coding.
    if (-not $NoConsole) {
        $color = switch ($Level) {
            'INFO'    { 'Gray' }
            'WARN'    { 'Yellow' }
            'ERROR'   { 'Red' }
            'SUCCESS' { 'Green' }
            'DEBUG'   { 'DarkGray' }
            default   { 'White' }
        }
        Write-Host $line -ForegroundColor $color
    }
}

function Write-LogSection {
    <#
    .SYNOPSIS
        Writes a visually distinct section banner to the log and console.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string] $Title,

        [ValidateSet('Setup', 'Emulator', 'Controller', 'Installation')]
        [string] $Category = 'Setup'
    )

    $bar = '-' * 70
    Write-Log -Message $bar -Level INFO -Category $Category
    Write-Log -Message ("  {0}" -f $Title.ToUpper()) -Level INFO -Category $Category
    Write-Log -Message $bar -Level INFO -Category $Category
}

function Get-LogRoot {
    [CmdletBinding()]
    param()
    return $script:LogRoot
}

Export-ModuleMember -Function Initialize-Logging, Write-Log, Write-LogSection, Get-LogRoot
