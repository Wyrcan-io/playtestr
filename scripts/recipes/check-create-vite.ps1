[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$Root,
    [Parameter(Mandatory = $true)][string]$ExpectedName
)

$ErrorActionPreference = "Stop"
$rootPath = (Resolve-Path -LiteralPath $Root).Path
$packagePath = Join-Path $rootPath "package.json"
$package = Get-Content -LiteralPath $packagePath -Raw | ConvertFrom-Json
if ($package.name -ne $ExpectedName) { throw "package name mismatch" }
if ($package.type -ne "module") { throw "package type mismatch" }
foreach ($name in @("dev", "build", "preview")) {
    if (-not $package.scripts.$name) { throw "missing package script $name" }
}
foreach ($path in @("index.html", "src\main.js", "src\style.css")) {
    if (-not (Test-Path -LiteralPath (Join-Path $rootPath $path) -PathType Leaf)) {
        throw "missing generated file $path"
    }
}
if (Test-Path -LiteralPath (Join-Path $rootPath "node_modules")) {
    throw "recipe unexpectedly installed project dependencies"
}
Write-Output "create-vite oracle passed"
