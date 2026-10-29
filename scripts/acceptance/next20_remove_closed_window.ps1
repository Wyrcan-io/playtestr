param([Parameter(Mandatory=$true)][ValidateSet('pdm','hatch')][string]$Project,[switch]$Complete)
$ErrorActionPreference='Stop'
$workspace=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$campaign=Join-Path $workspace 'artifacts\runner-readiness-next-twenty-project-pass'
$projectRoot=Join-Path $campaign $Project
$packetName='retained-failed-final-v1';$subsetName='final-series-native-exit-v1';$expectedCategory='exit_mismatch'
if($Complete){$packetName='retained-complete-final-v2';$subsetName+='-v2';$expectedCategory='passed'}
if($Project -eq 'hatch') {
    if(-not $Complete){throw 'Hatch has no rejected final window'}
    $packetName='retained-complete-final-v1';$subsetName='final-series-native-exit-v1'
}
$retained=Join-Path $projectRoot $packetName
$subset=Join-Path $projectRoot $subsetName
foreach($path in @((Join-Path $workspace 'artifacts'),$campaign,$projectRoot,$retained,$subset)) {
    if((Resolve-Path -LiteralPath $path).ProviderPath -ne $path -or ((Get-Item -LiteralPath $path -Force).Attributes -band [IO.FileAttributes]::ReparsePoint)){throw 'Unsafe closed-window ancestor'}
}
$prepared=Get-Content -LiteralPath (Join-Path $retained 'prepared.json') -Raw | ConvertFrom-Json
$indexPath=Join-Path $retained 'index.json';$archive=Join-Path $retained 'packets.tar.xz'
if((Get-FileHash -LiteralPath $indexPath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $prepared.index_sha256 -or
   (Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash.ToLowerInvariant() -ne $prepared.archive_sha256){throw 'Closed-window retained packet changed'}
$index=Get-Content -LiteralPath $indexPath -Raw | ConvertFrom-Json
if($index.project -ne $Project -or $index.closed_subset -ne $subsetName -or $index.closed_wrapper -ne $prepared.closed_wrapper -or
   $prepared.closed_subset -ne $index.closed_subset -or $index.closed_wrapper -notmatch '^[0-9a-f]{32}$' -or
   $prepared.files_compared_byte_exact -ne @($index.files.PSObject.Properties).Count -or $prepared.files_compared_byte_exact -gt 4000 -or
   (Get-Item -LiteralPath $archive).Length -gt 8388608){throw 'Closed-window scope/bounds differ'}
$event=Get-Content -LiteralPath (Join-Path $campaign ('events\'+$index.closed_wrapper+'-finished.json')) -Raw | ConvertFrom-Json
if($event.category -ne $expectedCategory -or $event.harness_cleanup -ne 'harness_process_reaped' -or @($event.cleanup_errors).Count -ne 0){throw 'Window is not confirmed closed'}
if((Get-FileHash -LiteralPath (Join-Path $retained 'selected-restore.bin') -Algorithm SHA256).Hash.ToLowerInvariant() -ne $prepared.selected_restore.sha256){throw 'Original failed report restore changed'}
$actual=@{};$paths=@();$bytes=[long]0;$pending=[Collections.Generic.Queue[string]]::new();$pending.Enqueue($subset)
while($pending.Count) {
    $directory=$pending.Dequeue()
    foreach($entry in Get-ChildItem -LiteralPath $directory -Force) {
        if($entry.Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'Linked closed-window entry'}
        if($entry.PSIsContainer){$pending.Enqueue($entry.FullName);continue}
        $name=$entry.FullName.Substring($campaign.Length+1).Replace('\','/')
        $row=$index.files.PSObject.Properties[$name].Value
        if($null -eq $row -or $entry.Length -ne $row.bytes -or $entry.Length -gt 16777216 -or
           (Get-FileHash -LiteralPath $entry.FullName -Algorithm SHA256).Hash.ToLowerInvariant() -ne $row.sha256){throw 'Closed-window bytes differ from retained payload'}
        $actual[$name]=$true;$paths+=,$entry.FullName;$bytes+=$entry.Length
    }
}
if($actual.Count -ne $prepared.files_compared_byte_exact -or $bytes -ne $index.expanded_bytes -or $bytes -gt 33554432){throw 'Closed-window full inventory differs'}
foreach($path in $paths){
    $resolved=(Resolve-Path -LiteralPath $path).ProviderPath
    if($resolved -ne $path -or -not $resolved.StartsWith($subset+'\',[StringComparison]::OrdinalIgnoreCase)){throw 'Removal escapes exact closed window'}
    Remove-Item -LiteralPath $path -Force
}
foreach($path in $paths){if(Test-Path -LiteralPath $path){throw 'Closed-window duplicate remains'}}
@{schema_version=1;all_expanded_removed=$true;files=$paths.Count;expanded_bytes=$bytes;index_sha256=$prepared.index_sha256;
  archive_sha256=$prepared.archive_sha256;closed_wrapper=$index.closed_wrapper;source_runtime_removed=$false;checked_at_utc=[DateTime]::UtcNow.ToString('o')} |
  ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $retained 'expanded-removed.json') -Encoding UTF8
Write-Output ('Verified and removed '+$paths.Count+' exact duplicates from the closed window; active source/runtime untouched.')
