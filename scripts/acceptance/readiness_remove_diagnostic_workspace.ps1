param([Parameter(Mandatory=$true)][string]$Report,[Parameter(Mandatory=$true)][ValidatePattern('^[a-f0-9]{64}$')][string]$MarkerSHA256)
$ErrorActionPreference='Stop'
$workspace=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$campaign=Join-Path $workspace 'artifacts\runner-readiness-ten-project-pass'
$reportPath=(Resolve-Path -LiteralPath $Report).ProviderPath
if (-not $reportPath.StartsWith((Join-Path $campaign 'experimental\native-root-diagnosis\'),[StringComparison]::OrdinalIgnoreCase)) { throw 'Unexpected diagnostic report' }
$result=(Get-Content -LiteralPath $reportPath -Raw | ConvertFrom-Json).results[0]
if (-not $result.cleanup.confirmed_exited -or -not $result.workspace.retained) { throw 'Diagnostic target termination or retention unconfirmed' }
$temporary=Join-Path $campaign 'tmp'
$target=(Resolve-Path -LiteralPath $result.workspace.retained_path).ProviderPath
if ([IO.Path]::GetDirectoryName($target) -ne $temporary -or [IO.Path]::GetFileName($target) -notmatch '^playtestr-workspace-[0-9]+$') { throw 'Diagnostic removal escapes owned temporary root' }
foreach ($path in @((Join-Path $workspace 'artifacts'),$campaign,$temporary,$target)) {
    if ((Get-Item -LiteralPath $path -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Linked removal ancestor' }
}
$pending=[Collections.Generic.Queue[string]]::new();$pending.Enqueue($target);$count=0
while ($pending.Count) {
    foreach ($entry in Get-ChildItem -LiteralPath $pending.Dequeue() -Force) {
        $count++;if ($count -gt 2000) { throw 'Diagnostic cleanup entry bound' }
        if ($entry.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Diagnostic contains an unreviewed link' }
        if ($entry.PSIsContainer) { $pending.Enqueue($entry.FullName) }
    }
}
$marker=Join-Path $target '.playtestr-owner'
if (-not (Test-Path -LiteralPath $marker -PathType Leaf) -or (Get-Content -LiteralPath $marker -Raw) -notmatch '^[a-f0-9]{32}$') { throw 'Diagnostic workspace marker invalid' }
if ((Get-FileHash -LiteralPath $marker -Algorithm SHA256).Hash.ToLowerInvariant() -ne $MarkerSHA256) { throw 'Diagnostic workspace marker changed' }
Remove-Item -LiteralPath $target -Recurse -Force
if (Test-Path -LiteralPath $target) { throw 'Diagnostic workspace remains' }
Write-Output 'Checked diagnostic workspace removal confirmed.'
