<#
.SYNOPSIS
    Centralized logging for the ES-DE automation suite (8 log files).
#>

Set-StrictMode -Version Latest

$script:LogRoot     = $null
$script:LogTargets  = @{}
$script:Initialized = $false

$script:LogFileMap = [ordered]@{
    'Main'         = 'Main.log'
    'Migration'    = 'Migration.log'
    'Media'        = 'Media.log'
    'Metadata'     = 'Metadata.log'
    'Optimization' = 'Optimization.log'
    'Controllers'  = 'Controllers.log'
    'Downloads'    = 'Downloads.log'
    'Git'          = 'Git.log'
}

function Initialize-EsdeLogging {
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][string] $LogRoot)

    if (-not (Test-Path -LiteralPath $LogRoot)) {
        New-Item -Path $LogRoot -ItemType Directory -Force | Out-Null
    }
    $script:LogRoot    = $LogRoot
    $script:LogTargets = @{}
    foreach ($key in $script:LogFileMap.Keys) {
        $path = Join-Path $LogRoot $script:LogFileMap[$key]
        $script:LogTargets[$key] = $path
        if (-not (Test-Path -LiteralPath $path)) { New-Item -Path $path -ItemType File -Force | Out-Null }
    }
    $script:Initialized = $true
    $header = "================ ES-DE Auto Suite session $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') ================"
    foreach ($key in $script:LogFileMap.Keys) {
        Add-Content -LiteralPath $script:LogTargets[$key] -Value $header -Encoding UTF8
    }
}

function Write-EsdeLog {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true, Position = 0)] [string] $Message,
        [ValidateSet('INFO','WARN','ERROR','SUCCESS','DEBUG')] [string] $Level = 'INFO',
        [ValidateSet('Main','Migration','Media','Metadata','Optimization','Controllers','Downloads','Git')]
        [string] $Category = 'Main',
        [switch] $NoConsole
    )

    $timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss.fff'
    $line      = '[{0}] [{1,-7}] {2}' -f $timestamp, $Level, $Message

    if ($script:Initialized) {
        $targets = New-Object System.Collections.Generic.List[string]
        $targets.Add($script:LogTargets[$Category])
        if (($Level -eq 'ERROR' -or $Level -eq 'WARN') -and $Category -ne 'Main') {
            $targets.Add($script:LogTargets['Main'])
        }
        foreach ($t in ($targets | Select-Object -Unique)) {
            try { Add-Content -LiteralPath $t -Value $line -Encoding UTF8 -ErrorAction Stop }
            catch { Write-Host "LOGGING FAILURE -> $($_.Exception.Message)" -ForegroundColor Red }
        }
    }

    if (-not $NoConsole) {
        $color = switch ($Level) {
            'INFO' {'Gray'} 'WARN' {'Yellow'} 'ERROR' {'Red'} 'SUCCESS' {'Green'} 'DEBUG' {'DarkGray'} default {'White'}
        }
        Write-Host $line -ForegroundColor $color
    }
}

function Write-EsdeSection {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string] $Title,
        [ValidateSet('Main','Migration','Media','Metadata','Optimization','Controllers','Downloads','Git')]
        [string] $Category = 'Main'
    )
    $bar = '-' * 72
    Write-EsdeLog -Message $bar -Level INFO -Category $Category
    Write-EsdeLog -Message ("  {0}" -f $Title.ToUpper()) -Level INFO -Category $Category
    Write-EsdeLog -Message $bar -Level INFO -Category $Category
}

function Get-EsdeLogRoot { return $script:LogRoot }

Export-ModuleMember -Function Initialize-EsdeLogging, Write-EsdeLog, Write-EsdeSection, Get-EsdeLogRoot
