[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][int]$ProcessID,
    [Parameter(Mandatory = $true)][string]$ExpectedPath
)

$ErrorActionPreference = "Stop"
$expected = (Resolve-Path -LiteralPath $ExpectedPath).Path
$process = Get-Process -Id $ProcessID -ErrorAction Stop
if ($process.Path -ne $expected) { throw "process identity mismatch" }
Write-Output "process oracle passed"
