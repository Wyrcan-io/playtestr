$ErrorActionPreference = 'Stop'

$projectRoot = Split-Path -Parent $PSScriptRoot
$compilerBin = Join-Path $projectRoot '.tools\winlibs\mingw64\bin'
$compiler = Join-Path $compilerBin 'gcc.exe'

if (-not (Test-Path -LiteralPath $compiler)) {
    throw "Project-local GCC was not found at $compiler"
}

$env:PATH = "$compilerBin;$env:PATH"
$env:CGO_ENABLED = '1'
$env:CC = 'gcc'
$env:GOCACHE = Join-Path $projectRoot '.cache'

& $compiler --print-file-name libsynchronization.a
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& go test -race -count=1 ./...
exit $LASTEXITCODE
