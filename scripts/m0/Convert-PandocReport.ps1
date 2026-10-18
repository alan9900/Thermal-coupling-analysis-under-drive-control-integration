param(
    [Parameter(Mandatory = $true)][string]$InputPath,
    [string]$OutputPath,
    [string]$ReferenceDoc
)

$ErrorActionPreference = 'Stop'
$source = (Resolve-Path -LiteralPath $InputPath).Path
if ([IO.Path]::GetExtension($source).ToLowerInvariant() -notin @('.md', '.markdown')) {
    throw 'Input must be a Markdown file (.md or .markdown).'
}

if (-not $OutputPath) {
    $OutputPath = [IO.Path]::ChangeExtension($source, '.docx')
}
$target = [IO.Path]::GetFullPath($OutputPath)
$targetDir = [IO.Path]::GetDirectoryName($target)
New-Item -ItemType Directory -Force -Path $targetDir | Out-Null

$pandoc = (Get-Command pandoc -ErrorAction SilentlyContinue | Select-Object -First 1 -ExpandProperty Source)
if (-not $pandoc) {
    $pandoc = 'C:\Users\90521\.codex\tools\pandoc-3.11\pandoc.exe'
}
if (-not (Test-Path -LiteralPath $pandoc)) {
    throw 'Pandoc is unavailable. Install it from https://github.com/jgm/pandoc/releases.'
}

$sourceDir = [IO.Path]::GetDirectoryName($source)
$arguments = @(
    $source,
    '--from=markdown+tex_math_dollars+pipe_tables+grid_tables',
    '--to=docx',
    '--standalone',
    '--citeproc',
    '--fail-if-warnings',
    "--resource-path=$sourceDir",
    "--output=$target"
)
if ($ReferenceDoc) {
    $reference = (Resolve-Path -LiteralPath $ReferenceDoc).Path
    $arguments += "--reference-doc=$reference"
}

& $pandoc @arguments
if ($LASTEXITCODE -ne 0) {
    throw "Pandoc failed with exit code $LASTEXITCODE."
}
if (-not (Test-Path -LiteralPath $target)) {
    throw "Pandoc did not create $target."
}
Write-Output $target
