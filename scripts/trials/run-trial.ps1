[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$Runner,
    [Parameter(Mandatory = $true)][string]$Spec,
    [Parameter(Mandatory = $true)][string]$Oracle,
    [string[]]$OracleArguments = @(),
    [string]$AttemptRoot = ".trial-results",
    [ValidateRange(1, 600)][int]$OracleTimeoutSeconds = 30,
    [ValidateRange(1024, 10485760)][int64]$OracleMaxOutputBytes = 1048576
)

$ErrorActionPreference = "Stop"

function ConvertTo-NativeArgument {
    param([string]$Value)
    if ($Value -notmatch '[\s"]') { return $Value }
    return '"' + ($Value -replace '(\\*)"', '$1$1\"' -replace '(\\+)$', '$1$1') + '"'
}

$runnerPath = (Resolve-Path -LiteralPath $Runner).Path
$specPath = (Resolve-Path -LiteralPath $Spec).Path
$oraclePath = (Get-Command $Oracle -ErrorAction Stop).Source
$attemptID = "{0}-{1}" -f ([DateTime]::UtcNow.ToString("yyyyMMddTHHmmssfffZ")), ([Guid]::NewGuid().ToString("N").Substring(0, 8))
$attemptDir = Join-Path $AttemptRoot $attemptID
New-Item -ItemType Directory -Path $attemptDir -Force | Out-Null
$attemptDir = (Resolve-Path -LiteralPath $attemptDir).Path

$reportPath = Join-Path $attemptDir "runner-report.json"
$runnerStdout = Join-Path $attemptDir "runner.stdout.txt"
$runnerStderr = Join-Path $attemptDir "runner.stderr.txt"
$oracleStdout = Join-Path $attemptDir "oracle.stdout.txt"
$oracleStderr = Join-Path $attemptDir "oracle.stderr.txt"

$savedErrorPreference = $ErrorActionPreference
$ErrorActionPreference = "Continue"
& $runnerPath test --report $reportPath $specPath 1> $runnerStdout 2> $runnerStderr
$runnerExit = $LASTEXITCODE
$ErrorActionPreference = $savedErrorPreference

$argumentLine = ($OracleArguments | ForEach-Object { ConvertTo-NativeArgument $_ }) -join ' '
$processArguments = @{
    FilePath = $oraclePath
    RedirectStandardOutput = $oracleStdout
    RedirectStandardError = $oracleStderr
    NoNewWindow = $true
    PassThru = $true
}
if ($argumentLine) { $processArguments.ArgumentList = $argumentLine }
$oracleProcess = Start-Process @processArguments
# Windows PowerShell 5 can leave ExitCode unset unless the process handle is
# materialized before waiting.
$oracleHandle = $oracleProcess.Handle
$oracleDeadline = [DateTime]::UtcNow.AddSeconds($OracleTimeoutSeconds)
$oracleTimedOut = $false
$oracleOutputLimitExceeded = $false
while (-not $oracleProcess.HasExited) {
    Start-Sleep -Milliseconds 100
    $outputBytes = 0
    if (Test-Path -LiteralPath $oracleStdout) { $outputBytes += (Get-Item -LiteralPath $oracleStdout).Length }
    if (Test-Path -LiteralPath $oracleStderr) { $outputBytes += (Get-Item -LiteralPath $oracleStderr).Length }
    if ($outputBytes -gt $OracleMaxOutputBytes) {
        $oracleOutputLimitExceeded = $true
        break
    }
    if ([DateTime]::UtcNow -ge $oracleDeadline) {
        $oracleTimedOut = $true
        break
    }
}
if (-not $oracleOutputLimitExceeded) {
    $finalOutputBytes = 0
    if (Test-Path -LiteralPath $oracleStdout) { $finalOutputBytes += (Get-Item -LiteralPath $oracleStdout).Length }
    if (Test-Path -LiteralPath $oracleStderr) { $finalOutputBytes += (Get-Item -LiteralPath $oracleStderr).Length }
    $oracleOutputLimitExceeded = $finalOutputBytes -gt $OracleMaxOutputBytes
}
if ($oracleTimedOut -or $oracleOutputLimitExceeded) {
    if (-not $oracleProcess.HasExited) { $oracleProcess.Kill() }
    $oracleProcess.WaitForExit()
}
$oracleExit = if ($oracleTimedOut) { 124 } elseif ($oracleOutputLimitExceeded) { 125 } else { $oracleProcess.ExitCode }
$status = if ($runnerExit -eq 0 -and $oracleExit -eq 0) { "passed" } else { "failed" }

$result = [ordered]@{
    schema_version = 1
    attempt_id = $attemptID
    status = $status
    runner = [ordered]@{ exit_code = $runnerExit; report = "runner-report.json"; stdout = "runner.stdout.txt"; stderr = "runner.stderr.txt" }
    oracle = [ordered]@{ exit_code = $oracleExit; timed_out = $oracleTimedOut; output_limit_exceeded = $oracleOutputLimitExceeded; stdout = "oracle.stdout.txt"; stderr = "oracle.stderr.txt" }
}
$result | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $attemptDir "harness-result.json") -Encoding UTF8
Write-Output $attemptDir
if ($status -ne "passed") { exit 1 }
