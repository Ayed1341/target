<#
.SYNOPSIS
    ES-DE theme installation (open-source themes) and active-theme selection.
.DESCRIPTION
    ES-DE themes are open-source (MIT/CC) and freely redistributable, so they CAN
    be installed automatically. Uses git clone when git is available, else a zip
    download. Also sets the active theme in es_settings.xml.
#>

Set-StrictMode -Version Latest

# A small curated list of well-known, open-source ES-DE themes.
$script:KnownThemes = @(
    @{ Name='slate-es-de';        Git='https://gitlab.com/es-de/themes/slate-es-de.git' },
    @{ Name='modern-es-de';       Git='https://gitlab.com/es-de/themes/modern-es-de.git' },
    @{ Name='art-book-next-es-de';Git='https://github.com/anthonycaccese/art-book-next-es-de.git' }
)

function Install-EsdeThemes {
    <#
    .SYNOPSIS
        Installs any missing curated themes into the themes directory. Returns count.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string] $ThemesDir,
        [Parameter(Mandatory = $true)][scriptblock] $Logger,
        [switch] $DryRun
    )
    $git = Get-Command git -ErrorAction SilentlyContinue
    $installed = 0
    if (-not (Test-Path -LiteralPath $ThemesDir)) {
        if (-not $DryRun) { New-Item -Path $ThemesDir -ItemType Directory -Force | Out-Null }
    }
    foreach ($t in $script:KnownThemes) {
        $dest = Join-Path $ThemesDir $t.Name
        if (Test-Path -LiteralPath $dest) { continue }
        if ($DryRun) { & $Logger "[DRY-RUN] Would install theme $($t.Name)." 'INFO'; $installed++; continue }
        try {
            if ($git) {
                $p = Start-Process -FilePath $git.Source -ArgumentList @('clone','--depth','1',$t.Git,$dest) -NoNewWindow -Wait -PassThru
                if ($p.ExitCode -eq 0 -and (Test-Path -LiteralPath $dest)) { & $Logger "Installed theme $($t.Name) (git)." 'SUCCESS'; $installed++ }
            } else {
                & $Logger "git not found; cannot auto-install theme $($t.Name). Install git or add themes manually." 'WARN'
            }
        } catch { & $Logger "Theme install failed ($($t.Name)): $($_.Exception.Message)" 'WARN' }
    }
    return $installed
}

function Set-ActiveTheme {
    <#
    .SYNOPSIS
        Sets es_settings ThemeSet to an installed theme if the current one is missing.
        Returns the theme name applied, or ''.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string] $SettingsFile,
        [Parameter(Mandatory = $true)][string] $ThemesDir,
        [Parameter(Mandatory = $true)][string] $BackupRoot,
        [Parameter(Mandatory = $true)][scriptblock] $Logger,
        [switch] $DryRun
    )
    $installed = @()
    if (Test-Path -LiteralPath $ThemesDir) { $installed = @(Get-ChildItem -LiteralPath $ThemesDir -Directory -ErrorAction SilentlyContinue | ForEach-Object { $_.Name }) }
    if ($installed.Count -eq 0) { return '' }
    $current = Get-EsdeSetting -SettingsFile $SettingsFile -Name 'ThemeSet'
    if ($current -and ($installed -contains $current)) { return $current }   # already valid
    $pick = $installed | Select-Object -First 1
    if ($DryRun) { & $Logger "[DRY-RUN] Would set active theme to $pick." 'INFO'; return $pick }
    Backup-File -Path $SettingsFile -BackupRoot $BackupRoot | Out-Null
    Set-EsdeSettingValue -SettingsFile $SettingsFile -Type 'string' -Name 'ThemeSet' -Value $pick
    & $Logger "Set active ES-DE theme to '$pick'." 'SUCCESS'
    return $pick
}

Export-ModuleMember -Function Install-EsdeThemes, Set-ActiveTheme
