<#
.SYNOPSIS
    Media classification engine.
.DESCRIPTION
    Classifies a media file into an ES-DE media folder (covers, marquees, videos,
    manuals, fanart, screenshots, 3dboxes, backcovers, miximages, physicalmedia,
    titlescreens) using, in priority order:
      1. an explicit gamelist tag association (passed in),
      2. the source sub-folder name,
      3. a scraper filename suffix (e.g. -marquee),
      4. file extension (video/manual),
      5. image dimensions / aspect ratio heuristics.
#>

Set-StrictMode -Version Latest

function Get-MediaDefinitions {
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][string] $DefinitionPath)
    if (-not (Test-Path -LiteralPath $DefinitionPath)) { throw "Media definition file not found: $DefinitionPath" }
    return (Get-Content -LiteralPath $DefinitionPath -Raw -Encoding UTF8 | ConvertFrom-Json)
}

function ConvertTo-Hashtable {
    param([object] $Object)
    $ht = @{}
    if ($null -eq $Object) { return $ht }
    foreach ($p in $Object.PSObject.Properties) { $ht[$p.Name.ToLower()] = $p.Value }
    return $ht
}

function Get-ImageDimensions {
    <#
    .SYNOPSIS
        Returns @{Width;Height} for an image using System.Drawing, or $null.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][string] $Path)
    try {
        Add-Type -AssemblyName System.Drawing -ErrorAction Stop
        $img = [System.Drawing.Image]::FromFile($Path)
        try { return @{ Width = $img.Width; Height = $img.Height } }
        finally { $img.Dispose() }
    } catch { return $null }
}

function Get-MediaClassification {
    <#
    .SYNOPSIS
        Returns the ES-DE media folder name for a file, plus the method used.
    .OUTPUTS
        Hashtable: EsdeFolder (string|null), Method (string), Kind (image/video/manual/unknown)
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)] [string] $FilePath,
        [Parameter(Mandatory = $true)] [object] $Definitions,
        [string] $SourceFolderName = '',
        [string] $GamelistTag = ''
    )

    $ext  = [System.IO.Path]::GetExtension($FilePath).ToLower()
    $stem = [System.IO.Path]::GetFileNameWithoutExtension($FilePath).ToLower()

    $imgExt = @($Definitions.mediaExtensions.image)
    $vidExt = @($Definitions.mediaExtensions.video)
    $manExt = @($Definitions.mediaExtensions.manual)

    $kind =
        if ($vidExt -contains $ext) { 'video' }
        elseif ($manExt -contains $ext) { 'manual' }
        elseif ($imgExt -contains $ext) { 'image' }
        else { 'unknown' }

    # 1) Explicit gamelist tag.
    if ($GamelistTag) {
        $map = ConvertTo-Hashtable $Definitions.gamelistTagToEsdeFolder
        $k = $GamelistTag.ToLower()
        if ($map.ContainsKey($k)) { return @{ EsdeFolder = $map[$k]; Method = 'gamelist-tag'; Kind = $kind } }
    }

    # Hard rule: videos and manuals are unambiguous by extension.
    if ($kind -eq 'video')  { return @{ EsdeFolder = 'videos';  Method = 'extension'; Kind = $kind } }
    if ($kind -eq 'manual') { return @{ EsdeFolder = 'manuals'; Method = 'extension'; Kind = $kind } }

    # 2) Source folder name.
    if ($SourceFolderName) {
        $fmap = ConvertTo-Hashtable $Definitions.sourceFolderToEsdeFolder
        $fk = $SourceFolderName.ToLower()
        if ($fmap.ContainsKey($fk)) { return @{ EsdeFolder = $fmap[$fk]; Method = 'source-folder'; Kind = $kind } }
    }

    # 3) Filename suffix (e.g. mygame-marquee.png).
    $smap = ConvertTo-Hashtable $Definitions.filenameSuffixToEsdeFolder
    foreach ($suffix in ($smap.Keys | Sort-Object { $_.Length } -Descending)) {
        if ($stem.EndsWith($suffix)) { return @{ EsdeFolder = $smap[$suffix]; Method = 'filename-suffix'; Kind = $kind } }
    }

    # 4/5) Image dimension heuristic for images with no other signal.
    if ($kind -eq 'image') {
        $dim = Get-ImageDimensions -Path $FilePath
        if ($dim -and $dim.Height -gt 0) {
            $ar = [double]$dim.Width / [double]$dim.Height
            if ($ar -ge 1.6)      { return @{ EsdeFolder = 'screenshots'; Method = 'dimensions'; Kind = $kind } } # widescreen -> screenshot
            elseif ($ar -le 0.85) { return @{ EsdeFolder = 'covers';      Method = 'dimensions'; Kind = $kind } } # portrait -> box/cover
            else                  { return @{ EsdeFolder = 'miximages';   Method = 'dimensions'; Kind = $kind } } # near-square -> mix
        }
        # Last resort: treat a lone image as a cover.
        return @{ EsdeFolder = 'covers'; Method = 'default-image'; Kind = $kind }
    }

    return @{ EsdeFolder = $null; Method = 'unclassified'; Kind = $kind }
}

Export-ModuleMember -Function Get-MediaDefinitions, Get-MediaClassification, Get-ImageDimensions, ConvertTo-Hashtable
