[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$AccessLog,
    [Parameter(Mandatory = $true)][string]$Fixture,
    [Parameter(Mandatory = $true)][string]$ExpectedRequest,
    [Parameter(Mandatory = $true)][string]$ExpectedMarker
)

$ErrorActionPreference = "Stop"

$logPath = (Resolve-Path -LiteralPath $AccessLog).Path
$fixturePath = (Resolve-Path -LiteralPath $Fixture).Path
$log = Get-Content -LiteralPath $logPath -Raw
$fixtureText = Get-Content -LiteralPath $fixturePath -Raw -Encoding UTF8

if ($log -notmatch [regex]::Escape($ExpectedRequest)) {
    throw "expected request was not recorded"
}
if ($fixtureText -notmatch [regex]::Escape($ExpectedMarker)) {
    throw "fixture marker does not match the frozen oracle"
}

Write-Output "PASS exact HTTP request and fixture marker"
