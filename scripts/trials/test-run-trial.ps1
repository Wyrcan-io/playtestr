[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$root = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$sandbox = Join-Path $root ".trial-private\harness-self-test"
New-Item -ItemType Directory -Path $sandbox -Force | Out-Null
$runner = Join-Path $sandbox "playtestr.exe"
$fixture = Join-Path $sandbox "fixture.exe"
$spec = Join-Path $sandbox "spec.json"
$oracleSource = Join-Path $sandbox "oracle.go"
$oracle = Join-Path $sandbox "oracle.exe"
$attempts = Join-Path $sandbox "attempts"

& go build -o $runner ./cmd/playtestr
if ($LASTEXITCODE -ne 0) { throw "build playtestr failed" }
& go build -o $fixture ./cmd/fixture
if ($LASTEXITCODE -ne 0) { throw "build fixture failed" }

$document = [ordered]@{
    version = 1
    name = "trial harness external oracle"
    command = @($fixture, "input")
    width = 80
    height = 24
    timeout_ms = 2000
    run_timeout_ms = 5000
    max_output_bytes = 100000
    steps = @(@{ key = "Enter" }, @{ expect = "input received" }, @{ exit = 0 })
}
[System.IO.File]::WriteAllText($spec, ($document | ConvertTo-Json -Depth 8), [System.Text.UTF8Encoding]::new($false))

[System.IO.File]::WriteAllText($oracleSource, 'package main; import "os"; func main() { os.Exit(7) }', [System.Text.Encoding]::ASCII)
& go build -o $oracle $oracleSource
if ($LASTEXITCODE -ne 0) { throw "build failing oracle failed" }
$harness = Join-Path $PSScriptRoot "run-trial.ps1"
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File $harness -Runner $runner -Spec $spec -Oracle $oracle -AttemptRoot $attempts | Out-Null
if ($LASTEXITCODE -eq 0) { throw "screen pass plus failed oracle incorrectly passed overall" }
$failed = Get-ChildItem -LiteralPath $attempts -Directory | Sort-Object Name | Select-Object -Last 1
$failedResult = Get-Content -LiteralPath (Join-Path $failed.FullName "harness-result.json") -Raw | ConvertFrom-Json
$runnerResult = Get-Content -LiteralPath (Join-Path $failed.FullName "runner-report.json") -Raw | ConvertFrom-Json
if ($failedResult.status -ne "failed" -or $failedResult.runner.exit_code -ne 0 -or $failedResult.oracle.exit_code -ne 7) { throw "failed attempt did not preserve separate outcomes" }
if ($runnerResult.results[0].status -ne "passed") { throw "runner result was not preserved as passed" }

[System.IO.File]::WriteAllText($oracleSource, 'package main; func main() {}', [System.Text.Encoding]::ASCII)
& go build -o $oracle $oracleSource
if ($LASTEXITCODE -ne 0) { throw "build passing oracle failed" }
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File $harness -Runner $runner -Spec $spec -Oracle $oracle -AttemptRoot $attempts | Out-Null
if ($LASTEXITCODE -ne 0) { throw "recovered oracle did not pass overall" }
$passed = Get-ChildItem -LiteralPath $attempts -Directory | Sort-Object Name | Select-Object -Last 1
$passedResult = Get-Content -LiteralPath (Join-Path $passed.FullName "harness-result.json") -Raw | ConvertFrom-Json
if ($passedResult.status -ne "passed") { throw "recovery attempt status is not passed" }

Write-Output "PASS trial harness failure and recovery"
