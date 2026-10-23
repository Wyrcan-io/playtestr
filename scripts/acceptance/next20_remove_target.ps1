param([Parameter(Mandatory=$true)][ValidatePattern('^[a-z][a-z0-9-]{0,63}$')][string]$Project)
$ErrorActionPreference='Stop'
$workspace=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$campaign=Join-Path $workspace 'artifacts\runner-readiness-next-twenty-project-pass'
$target=(Resolve-Path -LiteralPath (Join-Path $campaign ('active\'+$Project))).ProviderPath
$expected=Join-Path $campaign ('active\'+$Project)
if ($target -ne $expected -or -not $target.StartsWith($campaign+'\active\',[StringComparison]::OrdinalIgnoreCase)) { throw 'Target removal escapes exact owned root' }
foreach($path in @((Join-Path $workspace 'artifacts'),$campaign,(Join-Path $campaign 'active'),$target)) {
    if ((Get-Item -LiteralPath $path -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Linked target removal ancestor' }
}
$retained=Join-Path $campaign ($Project+'\retained-source')
$prepared=Get-Content -LiteralPath (Join-Path $retained 'prepared.json') -Raw | ConvertFrom-Json
$indexPath=Join-Path $retained 'cleanup-inventory.json'
if ((Get-FileHash -LiteralPath $indexPath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $prepared.cleanup_inventory_sha256) { throw 'Target cleanup inventory changed' }
$index=Get-Content -LiteralPath $indexPath -Raw | ConvertFrom-Json
if ($index.owned_target -ne $target -or -not $index.source_restored_exact) { throw 'Target ownership/restoration mismatch' }
$ownerPath=Join-Path $target 'task-owned.json'
if ((Get-FileHash -LiteralPath $ownerPath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $index.owner_sha256) { throw 'Target ownership marker changed' }
$actual=@{};$pending=[Collections.Generic.Queue[string]]::new();$pending.Enqueue($target)
while($pending.Count) {
    foreach($entry in Get-ChildItem -LiteralPath $pending.Dequeue() -Force) {
        if ($entry.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Unknown target link/reparse point' }
        if ($entry.PSIsContainer) {$pending.Enqueue($entry.FullName);continue}
        if ($actual.Count -ge 40000) { throw 'Target cleanup file bound' }
        $relative=$entry.FullName.Substring($target.Length+1).Replace('\','/')
        $record=$index.files.PSObject.Properties[$relative].Value
        if ($null -eq $record -or $entry.Length -ne $record.bytes -or
            (Get-FileHash -LiteralPath $entry.FullName -Algorithm SHA256).Hash.ToLowerInvariant() -ne $record.sha256) { throw 'Target payload changed after checked retention' }
        $actual[$relative]=$true
    }
}
if ($actual.Count -ne @($index.files.PSObject.Properties).Count -or @($index.owned_links.PSObject.Properties).Count) { throw 'Target cleanup coverage/link mismatch' }
foreach($candidate in Get-CimInstance Win32_Process) {
    $ownedExecutable=$candidate.ExecutablePath -and $candidate.ExecutablePath.StartsWith($target+'\',[StringComparison]::OrdinalIgnoreCase)
    $ownedArguments=$candidate.CommandLine -and $candidate.CommandLine.IndexOf($target,[StringComparison]::OrdinalIgnoreCase) -ge 0
    if (-not ($ownedExecutable -or $ownedArguments)) {continue}
    $current=Get-CimInstance Win32_Process -Filter ('ProcessId='+$candidate.ProcessId)
    if ($null -ne $current -and $current.CreationDate -eq $candidate.CreationDate) {throw 'Owned target PID/birth remains before removal'}
}
Remove-Item -LiteralPath $target -Recurse -Force
if (Test-Path -LiteralPath $target) {throw 'Target remains after native removal'}
@{schema_version=1;removed=$true;owned_relative_path=('active/'+$Project);source_restored_exact=$true;
    cleanup_inventory_sha256=$prepared.cleanup_inventory_sha256;checked_at_utc=[DateTime]::UtcNow.ToString('o')} |
    ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $retained 'removed.json') -Encoding UTF8
Write-Output 'Native Windows checked removal: exact owned target source/runtime absent; retained provenance preserved.'
