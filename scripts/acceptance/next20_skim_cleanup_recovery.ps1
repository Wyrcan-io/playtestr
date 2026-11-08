$ErrorActionPreference = 'Stop'
$workspace = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$target = [IO.Path]::GetFullPath((Join-Path $workspace 'artifacts\runner-readiness-next-twenty-project-pass\active\skim'))
$active = [IO.Path]::GetFullPath((Join-Path $workspace 'artifacts\runner-readiness-next-twenty-project-pass\active'))
if (-not $target.StartsWith($active + '\', [StringComparison]::OrdinalIgnoreCase)) { throw 'Skim target escapes active campaign root' }
foreach ($path in @($workspace, (Join-Path $workspace 'artifacts'), (Join-Path $workspace 'artifacts\runner-readiness-next-twenty-project-pass'), $active, $target)) {
    $item = Get-Item -LiteralPath $path -Force
    if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { throw "Linked cleanup ancestor: $path" }
}
$matches = @()
foreach ($candidate in Get-CimInstance Win32_Process) {
    $ownedExecutable = $candidate.ExecutablePath -and $candidate.ExecutablePath.StartsWith($target + '\', [StringComparison]::OrdinalIgnoreCase)
    $ownedArguments = $candidate.CommandLine -and $candidate.CommandLine.IndexOf($target, [StringComparison]::OrdinalIgnoreCase) -ge 0
    if ($ownedExecutable -or $ownedArguments) { $matches += $candidate.ProcessId }
}
if ($matches.Count) { throw ('Owned Skim processes remain: ' + ($matches -join ',')) }
$proof = Join-Path $workspace 'artifacts\runner-readiness-next-twenty-project-pass\skim\process-proof-final-cleanup.json'
if (Test-Path -LiteralPath $proof) {
    $priorProof = Get-Content -LiteralPath $proof -Raw | ConvertFrom-Json
    if ($priorProof.owned_target -ne $target -or -not $priorProof.confirmed_no_matching_live_processes -or $priorProof.matching_live_processes.Count -ne 0) { throw 'Existing final cleanup process proof is invalid' }
} else {
    @{owned_target=$target; confirmed_no_matching_live_processes=$true; matching_live_processes=@(); checked_at_utc=[DateTime]::UtcNow.ToString('o'); scope='Fresh native Windows Win32_Process executable and command-line inspection before exact owned-target removal.'} | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $proof -Encoding UTF8
}
$helper = Join-Path $PSScriptRoot 'next20_skim_cleanup_recovery.py'
Push-Location -LiteralPath $workspace
try {
    & python $helper prepare
    if ($LASTEXITCODE -ne 0) { throw 'Skim cleanup preparation failed' }
    & python $helper verify
    if ($LASTEXITCODE -ne 0) { throw 'Skim cleanup revalidation failed' }
    $fresh = Get-Item -LiteralPath $target -Force
    if (($fresh.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { throw 'Skim target became a reparse point' }
    Remove-Item -LiteralPath $target -Recurse -Force
    if (Test-Path -LiteralPath $target) { throw 'Skim target still exists after removal' }
    & python $helper finalize
    if ($LASTEXITCODE -ne 0) { throw 'Skim cleanup finalization failed' }
} finally { Pop-Location }
