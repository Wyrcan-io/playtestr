param([Parameter(Mandatory=$true)][ValidatePattern('^[a-z][a-z0-9-]{0,63}$')][string]$Project)
$ErrorActionPreference='Stop'
$workspace=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$campaign=Join-Path $workspace 'artifacts\runner-readiness-next-twenty-project-pass'
$target=(Resolve-Path -LiteralPath (Join-Path $campaign ('active\'+$Project))).ProviderPath
if (-not $target.StartsWith($campaign+'\active\',[StringComparison]::OrdinalIgnoreCase)) { throw 'Target process proof escapes campaign' }
$matches=@()
foreach($candidate in Get-CimInstance Win32_Process) {
    $ownedExecutable=$candidate.ExecutablePath -and $candidate.ExecutablePath.StartsWith($target+'\',[StringComparison]::OrdinalIgnoreCase)
    $ownedArguments=$candidate.CommandLine -and $candidate.CommandLine.IndexOf($target,[StringComparison]::OrdinalIgnoreCase) -ge 0
    if (-not ($ownedExecutable -or $ownedArguments)) { continue }
    $current=Get-CimInstance Win32_Process -Filter ('ProcessId='+$candidate.ProcessId)
    if ($null -eq $current -or $current.CreationDate -ne $candidate.CreationDate) { continue }
    $matches+=@{pid=$current.ProcessId;parent_pid=$current.ParentProcessId;birth=$current.CreationDate.ToUniversalTime().ToString('o')}
}
$record=@{project=$Project;owned_target=$target;checked_at_utc=[DateTime]::UtcNow.ToString('o');
    matching_live_processes=$matches;confirmed_no_matching_live_processes=($matches.Count -eq 0);
    scope='Rechecked native PID/birth and owned executable/argument roots; no unrelated process arguments or environment persisted.'}
$proof=Join-Path $campaign ($Project+'\process-proof.json')
if (Test-Path -LiteralPath $proof) { throw 'Preserve existing process proof; do not overwrite' }
$record | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $proof -Encoding UTF8
if ($matches.Count) { throw 'Owned target processes remain; no deletion authorized by this proof' }
Write-Output 'Native Windows owned target process proof: no matching live PID/birth identities.'
