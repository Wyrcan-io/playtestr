param(
    [string] $EvidenceDirectory = 'artifacts/integrated-hardening'
)

$ErrorActionPreference = 'Stop'

$projectRoot = Split-Path -Parent $PSScriptRoot
$evidenceRoot = if ([IO.Path]::IsPathRooted($EvidenceDirectory)) {
    $EvidenceDirectory
} else {
    Join-Path $projectRoot $EvidenceDirectory
}
$commandEvidenceRoot = if ([IO.Path]::IsPathRooted($EvidenceDirectory)) {
    $EvidenceDirectory
} else {
    $EvidenceDirectory
}
[IO.Directory]::CreateDirectory($evidenceRoot) | Out-Null
$env:GOCACHE = Join-Path $projectRoot '.cache'

$targetOS = (& go env GOOS).Trim()
$targetArch = (& go env GOARCH).Trim()
$target = "$targetOS/$targetArch"
if (@('windows/amd64', 'linux/amd64', 'darwin/arm64') -notcontains $target) {
    throw "integrated hardening requires an advertised native host, got $target"
}

$commit = (& git rev-parse HEAD).Trim()
$dirty = [bool](& git status --porcelain)
$goVersion = (& go version).Trim()
$osDescription = [Runtime.InteropServices.RuntimeInformation]::OSDescription
$powerShellVersion = $PSVersionTable.PSVersion.ToString()
$rows = [Collections.Generic.List[object]]::new()
$failed = $false

function Invoke-EvidenceCommand {
    param(
        [string] $Name,
        [string] $File,
        [string[]] $Arguments,
        [int] $ExpectedExit = 0,
        [string] $ExpectedResult,
        [string] $RemainingLimitation = 'None'
    )

    $started = [DateTimeOffset]::UtcNow
    $timer = [Diagnostics.Stopwatch]::StartNew()
    $previousErrorAction = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    $lines = @(& $File @Arguments 2>&1)
    $exitCode = $LASTEXITCODE
    $ErrorActionPreference = $previousErrorAction
    $timer.Stop()
    $logPath = Join-Path $evidenceRoot "$Name.log"
    $lines | Out-File -LiteralPath $logPath -Encoding utf8
    $status = if ($exitCode -eq $ExpectedExit) { 'passed' } else { 'failed' }
    if ($status -eq 'failed') {
        $script:failed = $true
    }
    $rows.Add([pscustomobject][ordered]@{
        name = $Name
        commit = $commit
        dirty = $dirty
        os_architecture = $target
        os_description = $osDescription
        toolchain = $goVersion
        powershell = $powerShellVersion
        command = $File + ' ' + ($Arguments -join ' ')
        expected_result = $ExpectedResult
        expected_exit_status = $ExpectedExit
        observed_result = $status
        exit_status = $exitCode
        started_utc = $started.ToString('o')
        elapsed_milliseconds = $timer.ElapsedMilliseconds
        artifact_location = $logPath.Substring($projectRoot.Length + 1).Replace('\', '/')
        remaining_limitation = $RemainingLimitation
    })
}

function Invoke-EvidenceCheck {
    param(
        [string] $Name,
        [string] $Command,
        [string] $ExpectedResult,
        [scriptblock] $Check
    )

    $started = [DateTimeOffset]::UtcNow
    $timer = [Diagnostics.Stopwatch]::StartNew()
    $exitCode = 0
    $lines = @()
    try {
        & $Check
        $lines += 'evidence check passed'
    } catch {
        $exitCode = 1
        $lines += $_.Exception.Message
        $script:failed = $true
    }
    $timer.Stop()
    $logPath = Join-Path $evidenceRoot "$Name.log"
    $lines | Out-File -LiteralPath $logPath -Encoding utf8
    $rows.Add([pscustomobject][ordered]@{
        name = $Name
        commit = $commit
        dirty = $dirty
        os_architecture = $target
        os_description = $osDescription
        toolchain = $goVersion
        powershell = $powerShellVersion
        command = $Command
        expected_result = $ExpectedResult
        expected_exit_status = 0
        observed_result = if ($exitCode -eq 0) { 'passed' } else { 'failed' }
        exit_status = $exitCode
        started_utc = $started.ToString('o')
        elapsed_milliseconds = $timer.ElapsedMilliseconds
        artifact_location = $logPath.Substring($projectRoot.Length + 1).Replace('\', '/')
        remaining_limitation = 'None'
    })
}

Invoke-EvidenceCommand -Name 'full-tests' -File 'go' -Arguments @('test', '-count=1', './...') `
    -ExpectedResult 'Every package passes without the Go test cache.'
Invoke-EvidenceCommand -Name 'vet' -File 'go' -Arguments @('vet', './...') `
    -ExpectedResult 'Static analysis exits successfully.'

$raceCompiler = $null
if ($targetOS -eq 'windows') {
    $projectCompiler = Join-Path $projectRoot '.tools\winlibs\mingw64\bin\gcc.exe'
    if (Test-Path -LiteralPath $projectCompiler) {
        $raceCompiler = $projectCompiler
        $env:PATH = "$(Split-Path -Parent $projectCompiler);$env:PATH"
        $env:CC = 'gcc'
    } else {
        $raceCompiler = (Get-Command gcc -ErrorAction SilentlyContinue | Select-Object -First 1).Source
        if ($raceCompiler) { $env:CC = 'gcc' }
    }
} else {
    $raceCompiler = (Get-Command cc, clang, gcc -ErrorAction SilentlyContinue | Select-Object -First 1).Source
}

if ($raceCompiler) {
    $env:CGO_ENABLED = '1'
    Invoke-EvidenceCommand -Name 'race' -File 'go' -Arguments @('test', '-race', '-count=1', './...') `
        -ExpectedResult 'Every package passes with the race detector.'
} else {
    $rows.Add([pscustomobject][ordered]@{
        name = 'race'
        commit = $commit
        dirty = $dirty
        os_architecture = $target
        os_description = $osDescription
        toolchain = $goVersion
        powershell = $powerShellVersion
        command = 'go test -race -count=1 ./...'
        expected_result = 'Every package passes with the race detector.'
        expected_exit_status = 0
        observed_result = 'blocked_missing_c_compiler'
        exit_status = $null
        started_utc = [DateTimeOffset]::UtcNow.ToString('o')
        elapsed_milliseconds = 0
        artifact_location = $null
        remaining_limitation = 'A native C compiler is required; this row is not a pass.'
    })
}

$nativeGapScript = Join-Path $PSScriptRoot 'test-native-gaps.ps1'
Invoke-EvidenceCommand -Name 'focused-native-gaps' -File $nativeGapScript `
    -Arguments @((Join-Path $evidenceRoot 'focused')) `
    -ExpectedResult 'All required installer, workspace, report, lifecycle, and native filesystem events pass without unexpected skips.'

$binaryName = if ($targetOS -eq 'windows') { 'playtestr.exe' } else { 'playtestr' }
$demoName = if ($targetOS -eq 'windows') { 'demo.exe' } else { 'demo' }
$fixtureName = if ($targetOS -eq 'windows') { 'fixture.exe' } else { 'fixture' }
$demoPath = Join-Path $projectRoot "bin/$demoName"
$fixturePath = Join-Path $projectRoot "bin/$fixtureName"
Invoke-EvidenceCommand -Name 'build-demo' -File 'go' -Arguments @('build', '-trimpath', '-o', $demoPath, './cmd/demo') `
    -ExpectedResult 'The real-PTY demo target builds for the native host.'
Invoke-EvidenceCommand -Name 'build-fixture' -File 'go' -Arguments @('build', '-trimpath', '-o', $fixturePath, './cmd/fixture') `
    -ExpectedResult 'The workspace fixture target builds for the native host.'
$binaryPath = Join-Path $evidenceRoot $binaryName
Invoke-EvidenceCommand -Name 'build-runner' -File 'go' -Arguments @('build', '-trimpath', '-o', $binaryPath, './cmd/playtestr') `
    -ExpectedResult 'The current-source runner builds for the native host.'

$manualArtifacts = Join-Path $commandEvidenceRoot 'manual-artifacts'
[IO.Directory]::CreateDirectory((Join-Path $evidenceRoot 'manual-artifacts')) | Out-Null
$mixedReport = Join-Path $commandEvidenceRoot 'mixed-v1-v2.json'
Invoke-EvidenceCommand -Name 'mixed-v1-v2' -File $binaryPath `
    -Arguments @('test', '--artifacts-dir', $manualArtifacts, '--report', $mixedReport, 'examples/menu.json', 'examples/workspace.json') `
    -ExpectedResult 'A mixed spec-v1/spec-v2 suite passes and emits report v2 with successful workspace cleanup.'
Invoke-EvidenceCheck -Name 'mixed-v1-v2-contract' `
    -Command "inspect $mixedReport for report-v2, two passes, spec-v1/spec-v2, and prepared/cleaned workspace" `
    -ExpectedResult 'The report proves both contract versions passed and the v2 workspace was prepared and cleaned.' `
    -Check {
        $document = Get-Content -Raw -LiteralPath $mixedReport | ConvertFrom-Json
        if ($document.report_version -ne 2 -or $document.summary.total -ne 2 -or $document.summary.passed -ne 2) {
            throw 'mixed suite summary or report version is incorrect'
        }
        if ($document.results[0].spec_version -ne 1 -or $document.results[1].spec_version -ne 2) {
            throw 'mixed suite does not preserve spec-v1/spec-v2 identities'
        }
        if (-not $document.results[1].workspace.prepared -or -not $document.results[1].workspace.cleaned) {
            throw 'workspace preparation or cleanup was not positively observed'
        }
    }
Invoke-EvidenceCommand -Name 'mixed-v1-v2-html' -File $binaryPath `
    -Arguments @('report', '--input', $mixedReport, '--evidence-root', '.', '--output', (Join-Path $commandEvidenceRoot 'mixed-v1-v2.html')) `
    -ExpectedResult 'The mixed report renders to bounded offline HTML.'

$failureReport = Join-Path $commandEvidenceRoot 'deliberate-failure.json'
Invoke-EvidenceCommand -Name 'deliberate-failure' -File $binaryPath `
    -Arguments @('test', '--artifacts-dir', $manualArtifacts, '--report', $failureReport, 'examples/snapshot-mismatch.json') `
    -ExpectedExit 1 -ExpectedResult 'The deliberate snapshot mismatch exits 1 and retains evidence.'
Invoke-EvidenceCheck -Name 'deliberate-failure-contract' `
    -Command "inspect $failureReport for snapshot_mismatch, exited target, and retained screen/diff evidence" `
    -ExpectedResult 'The nonzero result is the intended snapshot mismatch, not an unrelated launch or harness failure.' `
    -Check {
        $document = Get-Content -Raw -LiteralPath $failureReport | ConvertFrom-Json
        $result = $document.results[0]
        if ($document.summary.failed -ne 1 -or $result.failure.category -ne 'snapshot_mismatch') {
            throw "deliberate failure category was $($result.failure.category), expected snapshot_mismatch"
        }
        if (-not $result.target.exited -or -not $result.evidence.screen_path -or -not $result.evidence.diff_path) {
            throw 'deliberate failure lacks target-exit or retained-evidence proof'
        }
    }
Invoke-EvidenceCommand -Name 'deliberate-failure-html' -File $binaryPath `
    -Arguments @('report', '--input', $failureReport, '--evidence-root', '.', '--output', (Join-Path $commandEvidenceRoot 'deliberate-failure.html')) `
    -ExpectedResult 'The retained deliberate failure renders to offline HTML.'
Invoke-EvidenceCommand -Name 'recovery' -File $binaryPath `
    -Arguments @('test', '--artifacts-dir', $manualArtifacts, '--report', (Join-Path $commandEvidenceRoot 'recovery.json'), 'examples/menu.json') `
    -ExpectedResult 'The corrected recovery run passes after the deliberate failure.'
$recoveryReport = Join-Path $commandEvidenceRoot 'recovery.json'
Invoke-EvidenceCheck -Name 'recovery-contract' `
    -Command "inspect $recoveryReport for one pass and no stale evidence references" `
    -ExpectedResult 'Recovery positively passes and does not reuse retained failure evidence.' `
    -Check {
        $document = Get-Content -Raw -LiteralPath $recoveryReport | ConvertFrom-Json
        $result = $document.results[0]
        if ($document.summary.passed -ne 1 -or $result.status -ne 'passed') {
            throw 'recovery result did not pass'
        }
        $screen = $result.evidence.PSObject.Properties['screen_path']
        $diff = $result.evidence.PSObject.Properties['diff_path']
        if (($screen -and $screen.Value) -or ($diff -and $diff.Value)) {
            throw 'recovery report contains stale failure evidence'
        }
    }

$environment = [ordered]@{
    commit = $commit
    dirty = $dirty
    os_architecture = $target
    os_description = $osDescription
    toolchain = $goVersion
    powershell = $powerShellVersion
    race_compiler = $raceCompiler
    generated_utc = [DateTimeOffset]::UtcNow.ToString('o')
}
$environment | ConvertTo-Json -Depth 4 | Out-File -LiteralPath (Join-Path $evidenceRoot 'environment.json') -Encoding utf8
$rows | ConvertTo-Json -Depth 5 | Out-File -LiteralPath (Join-Path $evidenceRoot 'commands.json') -Encoding utf8
$rows | Format-Table -AutoSize

if ($failed) {
    exit 1
}
