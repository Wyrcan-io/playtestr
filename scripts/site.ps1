param(
    [Parameter(Position = 0)]
    [ValidateSet('build', 'serve')]
    [string]$Command = 'build'
)

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$localHugo = Join-Path $repoRoot '.tools\hugo-0.164.0\hugo.exe'
$hugo = if (Test-Path -LiteralPath $localHugo) { $localHugo } else { (Get-Command hugo -ErrorAction Stop).Source }
$version = & $hugo version
if ($version -notmatch 'hugo v0\.164\.0') {
    throw "Website requires Hugo v0.164.0; found: $version"
}

if ($Command -eq 'serve') {
    & $hugo server --source $repoRoot --config site/hugo.toml --buildDrafts --disableFastRender
    exit $LASTEXITCODE
}

& $hugo --source $repoRoot --config site/hugo.toml --cleanDestinationDir --minify
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
$schemaOutput = Join-Path $repoRoot 'public\schema'
New-Item -ItemType Directory -Force -Path $schemaOutput | Out-Null
Copy-Item -LiteralPath (Join-Path $repoRoot 'schema\playtestr-spec-v1.schema.json') -Destination $schemaOutput
Copy-Item -LiteralPath (Join-Path $repoRoot 'schema\playtestr-report-v1.schema.json') -Destination $schemaOutput
& node (Join-Path $repoRoot 'scripts\check-site.mjs') (Join-Path $repoRoot 'public')
exit $LASTEXITCODE
