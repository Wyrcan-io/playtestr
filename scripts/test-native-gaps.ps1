param(
    [string] $EvidenceDirectory = 'artifacts/native-gaps'
)

$ErrorActionPreference = 'Stop'

$projectRoot = Split-Path -Parent $PSScriptRoot
$evidenceRoot = if ([IO.Path]::IsPathRooted($EvidenceDirectory)) {
    $EvidenceDirectory
} else {
    Join-Path $projectRoot $EvidenceDirectory
}
[IO.Directory]::CreateDirectory($evidenceRoot) | Out-Null

$targetOS = (& go env GOOS).Trim()
$targetArch = (& go env GOARCH).Trim()
if ($LASTEXITCODE -ne 0) {
    throw 'go env failed'
}
$target = "$targetOS/$targetArch"
if (@('windows/amd64', 'linux/amd64', 'darwin/arm64') -notcontains $target) {
    throw "native gap checks require an advertised host, got $target"
}

$powerShell = Get-Command pwsh, powershell -ErrorAction SilentlyContinue | Select-Object -First 1
if (-not $powerShell) {
    throw 'PowerShell is required; installer tests would otherwise skip without exercising install.ps1'
}

$cases = @(
    @{
        Name = 'installer'
        Package = './internal/setupaction'
        Pattern = ''
        Required = @(
            'TestSetupActionInstallsVerifiedBinaryAndOverridesStalePath',
            'TestSetupActionRejectsUnsafeOrUnverifiedInputs',
            'TestSetupActionBoundsNetworkTimeout',
            'TestSetupActionDownloadsVerifiedArchiveAndRunsOffline',
            'TestSetupActionRejectsPartialAndOversizedDownloads',
            'TestSetupActionRollsBackFailedOutputPublication'
        )
        AllowedSkips = @()
    },
    @{
        Name = 'workspace'
        Package = './internal/runner'
        Pattern = '^TestWorkspace'
        Required = @(
            'TestWorkspaceSpecValidation',
            'TestWorkspaceRunsTwiceFromFreshFixtureAndCleans',
            'TestWorkspaceFailureCleanupAndExplicitRetention',
            'TestWorkspaceCleanupFailurePreventsSnapshotCommit',
            'TestWorkspaceFixtureCopyRejectsUnsafeAndBoundedInputs',
            'TestWorkspaceSetupFailureDoesNotLaunchTarget',
            'TestWorkspaceLifecycleOutcomesCleanOwnedState',
            'TestWorkspaceCancellationCleansAfterTarget',
            'TestWorkspaceCommandResolutionPrecedesFixtureCWD',
            'TestWorkspaceCleanupHonorsCancellation'
        )
        AllowedSkips = if ($targetOS -eq 'windows') {
            @('TestWorkspaceFixtureCopyRejectsUnsafeAndBoundedInputs/symbolic_link')
        } else {
            @()
        }
    },
    @{
        Name = 'report-v2'
        Package = './internal/report'
        Pattern = '^TestRenderHTML'
        Required = @(
            'TestRenderHTMLMixedSuiteIsOfflineEscapedAndComplete',
            'TestRenderHTMLReportV2WorkspaceOutcome'
        )
        AllowedSkips = @()
    },
    @{
        Name = 'lifecycle-cleanup'
        Package = './internal/runner'
        Pattern = '^(TestExpectedExitZero|TestExpectedNonzeroExit|TestWrongExitCode|TestExitWhileWaitingForText|TestExitTimeout|TestLaunchFailure|TestStartupTimeout|TestRunTimeout|TestCancellation$|TestOutputLimit|TestChildProcessCleanup|TestRepeatedSessionCleanup|TestSessionStopIsIdempotent|TestBlockedInputHonorsContext)$'
        Required = @(
            'TestExpectedExitZero',
            'TestExpectedNonzeroExit',
            'TestWrongExitCode',
            'TestExitWhileWaitingForText',
            'TestExitTimeout',
            'TestLaunchFailure',
            'TestStartupTimeout',
            'TestRunTimeout',
            'TestCancellation',
            'TestOutputLimit',
            'TestChildProcessCleanup',
            'TestRepeatedSessionCleanup',
            'TestSessionStopIsIdempotent',
            'TestBlockedInputHonorsContext'
        )
        AllowedSkips = @()
    }
)

$workspaceCase = $cases | Where-Object Name -eq 'workspace'
if ($targetOS -eq 'windows') {
    $workspaceCase.Required += @(
        'TestWorkspaceCopyRejectsWindowsJunction',
        'TestWorkspaceCleanupDoesNotFollowWindowsJunction',
        'TestWorkspaceCleanupReportsLockedFile'
    )
} else {
    $workspaceCase.Required += 'TestWorkspaceCleanupDoesNotFollowTargetCreatedSymlink'
}

$summaries = @()
$failed = $false
foreach ($case in $cases) {
    $arguments = @('test', '-count=1', '-json')
    if ($case.Pattern) {
        $arguments += @('-run', $case.Pattern)
    }
    $arguments += $case.Package

    $lines = @(& go @arguments 2>&1)
    $exitCode = $LASTEXITCODE
    $logPath = Join-Path $evidenceRoot ($case.Name + '.jsonl')
    $lines | Out-File -LiteralPath $logPath -Encoding utf8

    $events = @($lines | ForEach-Object { $_.ToString() | ConvertFrom-Json })
    $terminal = @($events | Where-Object { $_.Test -and $_.Action -in @('pass', 'fail', 'skip') })
    $topLevel = @($terminal | Where-Object { $_.Test -notmatch '/' })
    $passedNames = @($topLevel | Where-Object Action -eq 'pass' | ForEach-Object Test)
    $skippedNames = @($terminal | Where-Object Action -eq 'skip' | ForEach-Object Test)
    $missing = @($case.Required | Where-Object { $passedNames -notcontains $_ })
    $unexpectedSkips = @($skippedNames | Where-Object { $case.AllowedSkips -notcontains $_ })
    $allowedSkips = @($skippedNames | Where-Object { $case.AllowedSkips -contains $_ })

    $caseFailed = $exitCode -ne 0 -or $missing.Count -ne 0 -or $unexpectedSkips.Count -ne 0
    if ($caseFailed) {
        $failed = $true
    }
    $relativeLog = if ($logPath.StartsWith($projectRoot + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
        $logPath.Substring($projectRoot.Length + 1).Replace('\', '/')
    } else {
        $logPath.Replace('\', '/')
    }
    $summary = [ordered]@{
        name = $case.Name
        target = $target
        command = 'go ' + ($arguments -join ' ')
        exit_code = $exitCode
        top_level_passes = @($topLevel | Where-Object Action -eq 'pass').Count
        failures = @($terminal | Where-Object Action -eq 'fail' | ForEach-Object Test)
        allowed_skips = $allowedSkips
        unexpected_skips = $unexpectedSkips
        missing_required_tests = $missing
        event_log = $relativeLog
        status = if ($caseFailed) { 'failed' } else { 'passed' }
    }
    $summaries += [pscustomobject]$summary
    $summary | ConvertTo-Json -Depth 4
}

$summaryPath = Join-Path $evidenceRoot 'summary.json'
$summaries | ConvertTo-Json -Depth 5 | Out-File -LiteralPath $summaryPath -Encoding utf8
if ($failed) {
    exit 1
}
