<#
.SYNOPSIS
    Metadata / gamelist.xml engine: parse, validate, repair and write clean XML.
.DESCRIPTION
    Parses ES-DE / EmulationStation gamelist.xml files, exposes game entries with
    their media tags, repairs broken or missing media references (re-pointing them
    at existing downloaded_media where possible), removes duplicate <game> entries
    and invalid references, and writes back well-formed XML (after a backup).
#>

Set-StrictMode -Version Latest

# Media tags understood in gamelist.xml (ES + ES-DE + RetroBat supersets).
$script:MediaTags = @('image','thumbnail','marquee','video','fanart','titleshot',
                      'titlescreen','manual','boxart','wheel','mix','miximage',
                      'cartridge','boxback','screenshot')

function Read-Gamelist {
    <#
    .SYNOPSIS
        Loads a gamelist.xml and returns @{ Xml; Games(array of XmlNode); Ok; Error }.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][string] $Path)

    $result = @{ Xml = $null; Games = @(); Ok = $false; Error = $null; Prefix = '' }
    if (-not (Test-Path -LiteralPath $Path)) { $result.Error = 'not found'; return $result }
    try {
        $raw = Get-Content -LiteralPath $Path -Raw -Encoding UTF8
        # ES-DE gamelists can contain TWO top-level elements: an optional
        # <alternativeEmulator>...</alternativeEmulator> block followed by
        # <gameList>...</gameList>. That is not a single-rooted XML document, so
        # [xml] rejects it. Extract just the gameList element for parsing and keep
        # everything before it as a prefix to write back verbatim (preserving the
        # per-system standalone-emulator choice).
        $startIdx = $raw.IndexOf('<gameList')
        if ($startIdx -ge 0) {
            $endTag = '</gameList>'
            $endIdx = $raw.LastIndexOf($endTag)
            if ($endIdx -ge 0) {
                $glText = $raw.Substring($startIdx, ($endIdx - $startIdx) + $endTag.Length)
            } else {
                $glText = $raw.Substring($startIdx)   # self-closed / unterminated
            }
            $result.Prefix = $raw.Substring(0, $startIdx).TrimEnd()
            [xml]$xml = $glText
        } else {
            [xml]$xml = $raw
        }
        $result.Xml = $xml
        if ($xml.gameList) {
            $result.Games = @($xml.gameList.SelectNodes('game'))
        }
        $result.Ok = $true
    } catch {
        $result.Error = $_.Exception.Message
    }
    return $result
}

function Get-GameMediaTags { return $script:MediaTags }

function Get-RelativePathManual {
    <#
    .SYNOPSIS
        Returns a forward-slash relative path from a directory to a file, including
        ../ segments when needed (works on Windows PowerShell 5.1 via System.Uri).
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string] $FromDir,
        [Parameter(Mandatory = $true)][string] $ToPath
    )
    try {
        $fromUri = New-Object System.Uri(($FromDir.TrimEnd('\','/') + [System.IO.Path]::DirectorySeparatorChar))
        $toUri   = New-Object System.Uri($ToPath)
        $rel     = [Uri]::UnescapeDataString($fromUri.MakeRelativeUri($toUri).ToString())
        $rel     = $rel -replace '\\','/'
        if (-not $rel.StartsWith('.')) { $rel = './' + $rel }
        return $rel
    } catch {
        return ('./' + (Split-Path $ToPath -Leaf))
    }
}

function Resolve-RelativeMediaPath {
    <#
    .SYNOPSIS
        Resolves a gamelist media path (often "./images/x.png") against the
        gamelist's directory. Returns an absolute path (may not exist).
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string] $BaseDir,
        [Parameter(Mandatory = $true)][string] $RelPath
    )
    $p = $RelPath -replace '/', '\'
    $p = $p -replace '^\.\\', ''
    if ([System.IO.Path]::IsPathRooted($p)) { return $p }
    return [System.IO.Path]::GetFullPath((Join-Path $BaseDir $p))
}

function Repair-Gamelist {
    <#
    .SYNOPSIS
        Repairs a gamelist: removes duplicate <game> entries (same <path>),
        re-points media tags to existing files in the system's downloaded_media
        when the referenced file is missing, strips media references that cannot
        be resolved, and writes clean XML after backing up.
    .OUTPUTS
        Hashtable of statistics.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string] $GamelistPath,
        [Parameter(Mandatory = $true)][string] $MediaDir,       # downloaded_media\<system>
        [Parameter(Mandatory = $true)][string] $BackupRoot,
        [Parameter(Mandatory = $true)][scriptblock] $Logger,
        [switch] $DryRun
    )

    $stats = @{ Games = 0; Duplicates = 0; Repaired = 0; Removed = 0; Invalid = $false; Changed = $false }

    $g = Read-Gamelist -Path $GamelistPath
    if (-not $g.Ok) {
        & $Logger "Invalid/parse-failed gamelist: $GamelistPath ($($g.Error))" 'ERROR'
        $stats.Invalid = $true
        return $stats
    }
    $baseDir = Split-Path $GamelistPath -Parent
    $xml     = $g.Xml
    $prefix  = $g.Prefix
    $stats.Games = @($g.Games).Count

    # Index existing media files by stem within each ES-DE media subfolder.
    $mediaIndex = @{}
    if (Test-Path -LiteralPath $MediaDir) {
        Get-ChildItem -LiteralPath $MediaDir -Directory -ErrorAction SilentlyContinue | ForEach-Object {
            $folder = $_.Name.ToLower()
            $mediaIndex[$folder] = @{}
            Get-ChildItem -LiteralPath $_.FullName -File -ErrorAction SilentlyContinue | ForEach-Object {
                $mediaIndex[$folder][[System.IO.Path]::GetFileNameWithoutExtension($_.Name).ToLower()] = $_.FullName
            }
        }
    }

    # 1) De-duplicate games by <path>.
    $seen = @{}
    foreach ($game in @($g.Games)) {
        $path = $null
        if ($game.SelectSingleNode('path')) { $path = $game.SelectSingleNode('path').InnerText }
        if (-not $path) { continue }
        $key = $path.ToLower()
        if ($seen.ContainsKey($key)) {
            $stats.Duplicates++
            if (-not $DryRun) { [void]$game.ParentNode.RemoveChild($game) }
            continue
        }
        $seen[$key] = $true
    }

    # 2) Repair / strip media references.
    $tagToFolder = @{
        image='covers'; thumbnail='covers'; boxart='covers'; marquee='marquees'; wheel='marquees';
        fanart='fanart'; video='videos'; manual='manuals'; titleshot='titlescreens'; titlescreen='titlescreens';
        mix='miximages'; miximage='miximages'; cartridge='physicalmedia'; boxback='backcovers'; screenshot='screenshots'
    }
    foreach ($game in @($xml.gameList.SelectNodes('game'))) {
        $romStem = $null
        if ($game.SelectSingleNode('path')) {
            $romStem = [System.IO.Path]::GetFileNameWithoutExtension($game.SelectSingleNode('path').InnerText)
        }
        foreach ($tag in $script:MediaTags) {
            $node = $game.SelectSingleNode($tag)
            if (-not $node) { continue }
            $ref = $node.InnerText
            if ([string]::IsNullOrWhiteSpace($ref)) { continue }
            $abs = Resolve-RelativeMediaPath -BaseDir $baseDir -RelPath $ref
            if (Test-Path -LiteralPath $abs) { continue }   # reference is valid

            # Try to re-point to an existing downloaded_media file by stem.
            $folder = if ($tagToFolder.ContainsKey($tag)) { $tagToFolder[$tag] } else { $null }
            $fixed = $false
            if ($folder -and $romStem -and $mediaIndex.ContainsKey($folder)) {
                $stemKey = $romStem.ToLower()
                if ($mediaIndex[$folder].ContainsKey($stemKey)) {
                    $target = $mediaIndex[$folder][$stemKey]
                    # downloaded_media is a SIBLING of gamelists, so compute a true
                    # relative path (handles ../) rather than assuming containment.
                    $rel = Get-RelativePathManual -FromDir $baseDir -ToPath $target
                    if (-not $DryRun) { $node.InnerText = $rel }
                    $stats.Repaired++; $stats.Changed = $true; $fixed = $true
                }
            }
            if (-not $fixed) {
                # Unresolvable reference -> remove it so ES-DE falls back to auto media.
                if (-not $DryRun) { [void]$game.RemoveChild($node) }
                $stats.Removed++; $stats.Changed = $true
            }
        }
    }

    if (($stats.Changed -or $stats.Duplicates -gt 0) -and -not $DryRun) {
        Backup-File -Path $GamelistPath -BackupRoot $BackupRoot | Out-Null
        Save-Gamelist -Xml $xml -Prefix $prefix -Path $GamelistPath
        & $Logger "Repaired gamelist $GamelistPath (dupes=$($stats.Duplicates), fixed=$($stats.Repaired), stripped=$($stats.Removed))." 'SUCCESS'
    } elseif ($DryRun -and ($stats.Changed -or $stats.Duplicates -gt 0)) {
        & $Logger "[DRY-RUN] Would repair $GamelistPath (dupes=$($stats.Duplicates), fixed=$($stats.Repaired), stripped=$($stats.Removed))." 'INFO'
    }
    return $stats
}

function Save-XmlClean {
    <#
    .SYNOPSIS
        Writes an [xml] document with consistent indentation and UTF-8 (no BOM).
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][xml] $Xml,
        [Parameter(Mandatory = $true)][string] $Path
    )
    $dir = Split-Path $Path -Parent
    if ($dir -and -not (Test-Path -LiteralPath $dir)) { New-Item -Path $dir -ItemType Directory -Force | Out-Null }

    $settings = New-Object System.Xml.XmlWriterSettings
    $settings.Indent = $true
    $settings.IndentChars = '  '
    $settings.Encoding = New-Object System.Text.UTF8Encoding($false)
    $settings.OmitXmlDeclaration = $false
    $writer = [System.Xml.XmlWriter]::Create($Path, $settings)
    try { $Xml.Save($writer) } finally { $writer.Dispose() }
}

function Save-Gamelist {
    <#
    .SYNOPSIS
        Writes a gamelist back in ES-DE's exact format: an optional prefix (the XML
        declaration and any <alternativeEmulator> block) followed by the indented
        <gameList> element. Preserves the per-system standalone-emulator choice.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][xml] $Xml,
        [AllowEmptyString()][string] $Prefix = '',
        [Parameter(Mandatory = $true)][string] $Path
    )
    $dir = Split-Path $Path -Parent
    if ($dir -and -not (Test-Path -LiteralPath $dir)) { New-Item -Path $dir -ItemType Directory -Force | Out-Null }

    # Serialize just the gameList element (no XML declaration) with indentation.
    $settings = New-Object System.Xml.XmlWriterSettings
    $settings.Indent = $true
    $settings.IndentChars = '  '
    $settings.OmitXmlDeclaration = $true
    $sb = New-Object System.Text.StringBuilder
    $sw = New-Object System.IO.StringWriter($sb)
    $writer = [System.Xml.XmlWriter]::Create($sw, $settings)
    try { $Xml.Save($writer) } finally { $writer.Dispose(); $sw.Dispose() }
    $glText = $sb.ToString()

    $nl = "`r`n"
    if ([string]::IsNullOrWhiteSpace($Prefix)) {
        $out = '<?xml version="1.0"?>' + $nl + $glText
    } elseif ($Prefix -match '<\?xml') {
        $out = $Prefix + $nl + $glText
    } else {
        $out = '<?xml version="1.0"?>' + $nl + $Prefix + $nl + $glText
    }
    [System.IO.File]::WriteAllText($Path, $out, (New-Object System.Text.UTF8Encoding($false)))
}

Export-ModuleMember -Function Read-Gamelist, Get-GameMediaTags, Resolve-RelativeMediaPath, Repair-Gamelist, Save-XmlClean, Save-Gamelist
