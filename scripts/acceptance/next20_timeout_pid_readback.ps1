param([Parameter(Mandatory=$true)][ValidatePattern('^[0-9a-f]{32}$')][string]$ControlId,
      [Parameter(Mandatory=$true)][ValidatePattern('^[0-9a-f]{32}$')][string]$AttemptId)
$ErrorActionPreference='Stop'
$workspace=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$campaign=Join-Path $workspace 'artifacts\runner-readiness-next-twenty-project-pass'
$control=Join-Path $campaign ('control-tests\'+$ControlId)
$events=Join-Path $control 'events'
foreach($path in @($campaign,(Join-Path $campaign 'control-tests'),$control,$events)) {
    if((Resolve-Path -LiteralPath $path).ProviderPath -ne $path -or
        ((Get-Item -LiteralPath $path -Force).Attributes -band [IO.FileAttributes]::ReparsePoint)){throw 'Linked/unexpected timeout observation root'}
}
$startedPath=Join-Path $events ($AttemptId+'-started.json')
$launchedPath=Join-Path $events ($AttemptId+'-launched.json')
$finishedPath=Join-Path $events ($AttemptId+'-finished.json')
$started=Get-Content -LiteralPath $startedPath -Raw | ConvertFrom-Json
$launched=Get-Content -LiteralPath $launchedPath -Raw | ConvertFrom-Json
$finished=Get-Content -LiteralPath $finishedPath -Raw | ConvertFrom-Json
foreach($event in @($started,$launched,$finished)) {
    if($event.id -ne $AttemptId -or $event.campaign -ne 'runner-readiness-next-twenty-project-pass' -or
       $event.label -ne 'adapter-timeout' -or $event.project -ne 'core'){throw 'Wrong original timeout event identity'}
}
if($finished.category -ne 'harness_timeout' -or $finished.harness_cleanup -ne 'harness_cleanup_unconfirmed' -or
   $started.timeout_seconds -ne 1 -or $launched.pid -le 0){throw 'Not the explicit original unconfirmed timeout control'}
$originalStart=[DateTimeOffset]::Parse($started.utc,[Globalization.CultureInfo]::InvariantCulture)
$latestOriginalBirth=$originalStart.AddSeconds([Math]::Max([double]$finished.seconds,1)+60)
$observed=Get-CimInstance Win32_Process -Filter ('ProcessId='+[int]$launched.pid)
$absent=$null -eq $observed
$reused=$false
if(-not $absent) {$reused=$observed.CreationDate.ToUniversalTime() -gt $latestOriginalBirth.UtcDateTime}
if(-not ($absent -or $reused)){throw 'Original PID may still be live; no process signaled or unrelated details retained'}
$output=Join-Path $campaign 'harness\timeout-pid-readback'
foreach($path in @((Join-Path $campaign 'harness'),$output)) {
    if((Test-Path -LiteralPath $path) -and ((Resolve-Path -LiteralPath $path).ProviderPath -ne $path -or
        ((Get-Item -LiteralPath $path -Force).Attributes -band [IO.FileAttributes]::ReparsePoint))){throw 'Linked timeout observation output'}
}
New-Item -ItemType Directory -Path $output -Force | Out-Null
$receipt=Join-Path $output ($AttemptId+'.json')
if(Test-Path -LiteralPath $receipt){throw 'Preserve existing timeout PID observation'}
@{schema_version=1;attempt=$AttemptId;control=$ControlId;original_pid=[int]$launched.pid;
    original_start_utc=$originalStart.ToString('o');pid_currently_absent=$absent;
    pid_reused_after_original_attempt=$reused;original_recorded_pid_not_currently_live=$true;
    observed_at_utc=[DateTime]::UtcNow.ToString('o');processes_signaled=0;
    started_sha256=(Get-FileHash -LiteralPath $startedPath -Algorithm SHA256).Hash.ToLowerInvariant();
    launched_sha256=(Get-FileHash -LiteralPath $launchedPath -Algorithm SHA256).Hash.ToLowerInvariant();
    finished_sha256=(Get-FileHash -LiteralPath $finishedPath -Algorithm SHA256).Hash.ToLowerInvariant();
    scope='Targeted current PID/birth observation only. Original unconfirmed harness cleanup event remains unchanged. No broader original descendant-cleanup claim or unrelated process arguments retained.'} |
    ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $receipt -Encoding UTF8
Write-Output 'Original recorded timeout PID is absent or demonstrably reused after the original attempt; no process signaled.'
