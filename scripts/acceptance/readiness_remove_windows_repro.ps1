param([Parameter(Mandatory=$true)][ValidateSet('superfile','glow')][string]$Project)
$ErrorActionPreference='Stop'
$workspace=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$campaign=Join-Path $workspace 'artifacts\runner-readiness-ten-project-pass'
$target=[IO.Path]::GetFullPath((Join-Path $campaign ('active\r3-windows-'+$Project)))
$expected=Join-Path $workspace ('artifacts\runner-readiness-ten-project-pass\active\r3-windows-'+$Project)
if($target -ne $expected -or !(Test-Path -LiteralPath $target)){throw 'Diagnostic removal ownership boundary differs'}
$retained=Join-Path $campaign ('r3-windows-'+$Project+'\retained-evidence')
$indexPath=Join-Path $retained 'retention-index.json'
$index=Get-Content -LiteralPath $indexPath -Raw | ConvertFrom-Json
if($index.owned_relative_path -ne ('active/r3-windows-'+$Project) -or
    (Get-FileHash -LiteralPath (Join-Path $target 'task-owned.json') -Algorithm SHA256).Hash.ToLowerInvariant() -ne $index.owner_sha256){throw 'Diagnostic marker changed'}
foreach($entry in $index.files.PSObject.Properties){
    $file=[IO.Path]::GetFullPath((Join-Path $retained $entry.Name))
    if(!$file.StartsWith($retained+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase) -or
        (Get-Item -LiteralPath $file -Force).Attributes -band [IO.FileAttributes]::ReparsePoint -or
        (Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash.ToLowerInvariant() -ne $entry.Value){throw 'Retained diagnostic evidence differs'}
}
foreach($path in @((Join-Path $workspace 'artifacts'),$campaign,(Join-Path $campaign 'active'),$target,$retained)){
    if((Get-Item -LiteralPath $path -Force).Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'Linked diagnostic ancestor'}
}
$processes=@(Get-CimInstance Win32_Process | Where-Object {
    ($_.ExecutablePath -and $_.ExecutablePath.StartsWith($target+'\',[StringComparison]::OrdinalIgnoreCase)) -or
    ($_.CommandLine -and $_.CommandLine.IndexOf($target,[StringComparison]::OrdinalIgnoreCase) -ge 0)
})
if($processes.Count){throw 'Owned diagnostic process remains; refuse deletion'}
$pending=[Collections.Generic.Queue[string]]::new();$pending.Enqueue($target)
while($pending.Count){foreach($entry in Get-ChildItem -LiteralPath $pending.Dequeue() -Force){
    if($entry.Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'Linked diagnostic removal descendant'}
    if($entry.PSIsContainer){$pending.Enqueue($entry.FullName)}
}}
Remove-Item -LiteralPath $target -Recurse -Force
if(Test-Path -LiteralPath $target){throw 'Owned diagnostic root remains'}
@{removed=$true;owned_relative_path=$index.owned_relative_path;index_sha256=(Get-FileHash -LiteralPath $indexPath -Algorithm SHA256).Hash.ToLowerInvariant();runtime_processes_verified=$true} |
    ConvertTo-Json | Set-Content -LiteralPath (Join-Path $retained 'removed.json') -Encoding UTF8
Write-Output 'Removed only the verified owned Windows diagnostic source/runtime/cache root after retention and process checks.'
