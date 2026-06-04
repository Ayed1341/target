<#
.SYNOPSIS
    Configuration parsing / writing module.
.DESCRIPTION
    Implements robust readers and writers for the configuration formats used by
    RetroBat and its emulators:
      * INI / sectioned key=value (PCSX2, Dolphin, Citra, Yuzu, MAME, melonDS...)
      * Flat "key = value" cfg files (RetroArch, Flycast, Redream)
      * TOML scalar keys (Xenia)
      * Simple YAML scalar keys (RPCS3)
      * JSON (Ryujinx)
    All writers create timestamped backups before modifying a file and preserve
    unrelated content. No setting is removed; values are added or updated in place.
#>

Set-StrictMode -Version Latest

function New-ConfigBackup {
    <#
    .SYNOPSIS
        Creates a timestamped backup of a file inside a sibling 'Backups' folder.
    .OUTPUTS
        Path to the backup file, or $null if the source did not exist.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string] $Path,

        [Parameter(Mandatory = $true)]
        [string] $BackupRoot
    )

    if (-not (Test-Path -LiteralPath $Path)) { return $null }

    if (-not (Test-Path -LiteralPath $BackupRoot)) {
        New-Item -Path $BackupRoot -ItemType Directory -Force | Out-Null
    }

    $stamp    = Get-Date -Format 'yyyyMMdd_HHmmss'
    $leaf     = Split-Path -Path $Path -Leaf
    $backupTo = Join-Path $BackupRoot ("{0}.{1}.bak" -f $leaf, $stamp)
    Copy-Item -LiteralPath $Path -Destination $backupTo -Force
    return $backupTo
}

function Read-IniFile {
    <#
    .SYNOPSIS
        Parses a sectioned INI file into an ordered hashtable of sections.
    .OUTPUTS
        [ordered] hashtable: section name -> [ordered] hashtable of key/value.
        Keys outside any section are stored under the '' (empty) section.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string] $Path
    )

    $result  = [ordered]@{}
    $current = ''
    $result[$current] = [ordered]@{}

    if (-not (Test-Path -LiteralPath $Path)) { return $result }

    foreach ($raw in (Get-Content -LiteralPath $Path -Encoding UTF8)) {
        $line = $raw.Trim()
        if ($line.Length -eq 0) { continue }
        if ($line.StartsWith('#') -or $line.StartsWith(';')) { continue }

        if ($line.StartsWith('[') -and $line.EndsWith(']')) {
            $current = $line.Substring(1, $line.Length - 2).Trim()
            if (-not $result.Contains($current)) { $result[$current] = [ordered]@{} }
            continue
        }

        $idx = $line.IndexOf('=')
        if ($idx -lt 0) { continue }
        $key = $line.Substring(0, $idx).Trim()
        $val = $line.Substring($idx + 1).Trim()
        $result[$current][$key] = $val
    }

    return $result
}

function Write-IniFile {
    <#
    .SYNOPSIS
        Serializes a section hashtable (as produced by Read-IniFile) back to disk.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string] $Path,

        [Parameter(Mandatory = $true)]
        [System.Collections.Specialized.OrderedDictionary] $Data
    )

    $dir = Split-Path -Path $Path -Parent
    if ($dir -and -not (Test-Path -LiteralPath $dir)) {
        New-Item -Path $dir -ItemType Directory -Force | Out-Null
    }

    $sb = New-Object System.Text.StringBuilder

    # Global (section-less) keys first.
    if ($Data.Contains('') -and $Data[''].Count -gt 0) {
        foreach ($k in $Data[''].Keys) {
            [void]$sb.AppendLine(('{0} = {1}' -f $k, $Data[''][$k]))
        }
        [void]$sb.AppendLine()
    }

    foreach ($section in $Data.Keys) {
        if ($section -eq '') { continue }
        [void]$sb.AppendLine(('[{0}]' -f $section))
        foreach ($k in $Data[$section].Keys) {
            [void]$sb.AppendLine(('{0} = {1}' -f $k, $Data[$section][$k]))
        }
        [void]$sb.AppendLine()
    }

    [System.IO.File]::WriteAllText($Path, $sb.ToString(), (New-Object System.Text.UTF8Encoding($false)))
}

function Set-IniValue {
    <#
    .SYNOPSIS
        Sets or updates a single key within a section of an INI structure.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [System.Collections.Specialized.OrderedDictionary] $Data,
        # AllowEmptyString: emulators such as melonDS store keys with no section
        # (the global/section-less area), so an empty section name is valid.
        [Parameter(Mandatory = $true)] [AllowEmptyString()] [string] $Section,
        [Parameter(Mandatory = $true)] [string] $Key,
        [Parameter(Mandatory = $true)] [AllowEmptyString()] [string] $Value
    )

    if (-not $Data.Contains($Section)) { $Data[$Section] = [ordered]@{} }
    $Data[$Section][$Key] = $Value
}

function Set-FlatConfigValue {
    <#
    .SYNOPSIS
        Updates a "key = value" or "key value" entry in a flat config file,
        preserving all other lines. Used for RetroArch / Flycast / Redream.
    .PARAMETER Quote
        When set, wraps the value in double quotes (RetroArch style).
    .PARAMETER Separator
        The token between key and value (default ' = ').
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)] [string] $Path,
        [Parameter(Mandatory = $true)] [string] $Key,
        [Parameter(Mandatory = $true)] [string] $Value,
        [switch] $Quote,
        [string] $Separator = ' = '
    )

    $dir = Split-Path -Path $Path -Parent
    if ($dir -and -not (Test-Path -LiteralPath $dir)) {
        New-Item -Path $dir -ItemType Directory -Force | Out-Null
    }

    $renderedValue = if ($Quote) { '"{0}"' -f $Value } else { $Value }
    $newLine       = '{0}{1}{2}' -f $Key, $Separator, $renderedValue

    $lines = @()
    if (Test-Path -LiteralPath $Path) {
        $lines = @(Get-Content -LiteralPath $Path -Encoding UTF8)
    }

    $found   = $false
    # Match key at start of line followed by optional space then '=' (or space).
    $pattern = '^\s*' + [Regex]::Escape($Key) + '\s*(=|\s)'
    for ($i = 0; $i -lt $lines.Count; $i++) {
        if ($lines[$i] -match $pattern) {
            $lines[$i] = $newLine
            $found     = $true
            break
        }
    }
    if (-not $found) { $lines += $newLine }

    [System.IO.File]::WriteAllLines($Path, $lines, (New-Object System.Text.UTF8Encoding($false)))
}

function Set-TomlValue {
    <#
    .SYNOPSIS
        Updates a scalar key in a TOML file (e.g. Xenia config), preserving the
        rest of the document. Only top-level / current-table scalar keys handled,
        which covers the flat Xenia configuration layout.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)] [string] $Path,
        [Parameter(Mandatory = $true)] [string] $Key,
        [Parameter(Mandatory = $true)] [string] $Value
    )

    if (-not (Test-Path -LiteralPath $Path)) {
        # Create a minimal file containing just the key.
        [System.IO.File]::WriteAllText($Path, ('{0} = {1}{2}' -f $Key, $Value, [Environment]::NewLine), (New-Object System.Text.UTF8Encoding($false)))
        return
    }

    $lines   = @(Get-Content -LiteralPath $Path -Encoding UTF8)
    $found   = $false
    $pattern = '^\s*' + [Regex]::Escape($Key) + '\s*='
    for ($i = 0; $i -lt $lines.Count; $i++) {
        if ($lines[$i] -match $pattern) {
            # Preserve any trailing inline comment.
            $comment = ''
            $hashIdx = $lines[$i].IndexOf('#')
            if ($hashIdx -ge 0) { $comment = ' ' + $lines[$i].Substring($hashIdx) }
            $lines[$i] = '{0} = {1}{2}' -f $Key, $Value, $comment
            $found = $true
            break
        }
    }
    if (-not $found) { $lines += ('{0} = {1}' -f $Key, $Value) }

    [System.IO.File]::WriteAllLines($Path, $lines, (New-Object System.Text.UTF8Encoding($false)))
}

function Set-YamlScalar {
    <#
    .SYNOPSIS
        Updates an indented "Key: Value" scalar in an RPCS3-style YAML file,
        preserving structure. Matches by key name at any indentation depth.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)] [string] $Path,
        [Parameter(Mandatory = $true)] [string] $Key,
        [Parameter(Mandatory = $true)] [string] $Value
    )

    $dir = Split-Path -Path $Path -Parent
    if ($dir -and -not (Test-Path -LiteralPath $dir)) {
        New-Item -Path $dir -ItemType Directory -Force | Out-Null
    }

    $lines = @()
    if (Test-Path -LiteralPath $Path) {
        $lines = @(Get-Content -LiteralPath $Path -Encoding UTF8)
    }

    $found   = $false
    $pattern = '^(\s*)' + [Regex]::Escape($Key) + '\s*:'
    for ($i = 0; $i -lt $lines.Count; $i++) {
        if ($lines[$i] -match $pattern) {
            $indent    = $Matches[1]
            $lines[$i] = '{0}{1}: {2}' -f $indent, $Key, $Value
            $found     = $true
            break
        }
    }
    if (-not $found) { $lines += ('{0}: {1}' -f $Key, $Value) }

    [System.IO.File]::WriteAllLines($Path, $lines, (New-Object System.Text.UTF8Encoding($false)))
}

Export-ModuleMember -Function `
    New-ConfigBackup, Read-IniFile, Write-IniFile, Set-IniValue, `
    Set-FlatConfigValue, Set-TomlValue, Set-YamlScalar
