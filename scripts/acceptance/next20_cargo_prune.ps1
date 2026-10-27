param([Parameter(Mandatory=$true)][ValidatePattern('^[0-9a-f]{32}$')][string]$Inventory)
$ErrorActionPreference='Stop'
$workspace=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$campaign=Join-Path $workspace 'artifacts\runner-readiness-next-twenty-project-pass'
$project=Join-Path $campaign 'cargo-generate'
$recordPath=Join-Path $project ('checked-pruning\'+$Inventory+'.json')
$record=Get-Content -LiteralPath $recordPath -Raw | ConvertFrom-Json
$cache=Join-Path $campaign 'r'
$target=Join-Path $campaign 'active\cargo-generate'
function Assert-OwnedPath([string]$OwnedPath) {
    $checked=[IO.Path]::GetFullPath($OwnedPath)
    if (-not $checked.StartsWith($campaign+'\',[StringComparison]::OrdinalIgnoreCase)) {throw 'Checked pruning path escaped campaign'}
    while($checked -ne $campaign) {
        if ((Resolve-Path -LiteralPath $checked).ProviderPath -ne $checked -or
            ((Get-Item -LiteralPath $checked -Force).Attributes -band [IO.FileAttributes]::ReparsePoint)) {throw 'Linked/redirected pruning path ancestor'}
        $checked=[IO.Path]::GetDirectoryName($checked)
    }
}
if ($record.workspace -ne $workspace -or $record.cache_root -ne $cache -or $record.target_root -ne $target) {throw 'Foreign pruning scope'}
foreach($path in @((Join-Path $workspace 'artifacts'),$campaign,$project,$cache,$target)) {
    if ((Resolve-Path -LiteralPath $path).ProviderPath -ne $path -or
        ((Get-Item -LiteralPath $path -Force).Attributes -band [IO.FileAttributes]::ReparsePoint)) {throw 'Unsafe pruning ancestor'}
}
foreach($pair in @(@($record.required_archive,$record.required_archive_sha256),@($record.required_source_archive,$record.required_source_archive_sha256))) {
    $resolved=(Resolve-Path -LiteralPath $pair[0]).ProviderPath
    Assert-OwnedPath $pair[0]
    if (-not $resolved.StartsWith($project+'\',[StringComparison]::OrdinalIgnoreCase) -or
        (Get-FileHash -LiteralPath $resolved -Algorithm SHA256).Hash.ToLowerInvariant() -ne $pair[1]) {throw 'Required retained corpus changed'}
}
$expected=@{};$total=[long]0
foreach($property in $record.cache_files.PSObject.Properties) {$expected[$property.Name]=$property.Value}
foreach($property in $record.files.PSObject.Properties) {
    if ($property.Name -notmatch '^artifacts/runner-readiness-next-twenty-project-pass/cargo-generate/(native-variant-retention/windows/F0[123]\.xor\.xz|native-preflight/windows/compiled-binary\.tar\.xz)$') {throw 'Unexpected disposable representation'}
    $expected[$property.Name]=$property.Value
}
$actual=@{};$pending=[Collections.Generic.Queue[string]]::new();$pending.Enqueue($cache)
while($pending.Count) {
    foreach($entry in Get-ChildItem -LiteralPath $pending.Dequeue() -Force) {
        if ($entry.Attributes -band [IO.FileAttributes]::ReparsePoint) {throw 'Linked disposable compiler cache'}
        if ($entry.PSIsContainer) {$pending.Enqueue($entry.FullName);continue}
        $relative=$entry.FullName.Substring($workspace.Length+1).Replace('\','/')
        $actual[$relative]=$entry.FullName
    }
}
foreach($property in $record.files.PSObject.Properties) {
    $path=[IO.Path]::GetFullPath((Join-Path $workspace $property.Name))
    if (-not $path.StartsWith($project+'\',[StringComparison]::OrdinalIgnoreCase)) {throw 'Pruning path escaped project'}
    Assert-OwnedPath $path
    $actual[$property.Name]=$path
}
if ($actual.Count -ne $expected.Count -or $actual.Count -gt 25004) {throw 'Pruning inventory coverage/count differs'}
foreach($relative in $actual.Keys) {
    $path=$actual[$relative];$entry=Get-Item -LiteralPath $path -Force;$row=$expected[$relative]
    if ($null -eq $row -or $entry.PSIsContainer -or ($entry.Attributes -band [IO.FileAttributes]::ReparsePoint) -or
        $entry.Length -ne $row.bytes -or (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant() -ne $row.sha256) {throw 'Disposable payload changed after inventory'}
    $total+=$entry.Length
}
if ($total -ne $record.total_bytes -or $total -gt 536870912) {throw 'Pruning inventory byte bound differs'}
foreach($process in Get-CimInstance Win32_Process) {
    $matched=$false
    foreach($root in @($cache,$target,$record.cache_short,$record.target_short)) {
        if (($process.ExecutablePath -and $process.ExecutablePath.StartsWith($root+'\',[StringComparison]::OrdinalIgnoreCase)) -or
            ($process.CommandLine -and $process.CommandLine.IndexOf($root,[StringComparison]::OrdinalIgnoreCase) -ge 0)) {$matched=$true}
    }
    if ($matched) {
        $current=Get-CimInstance Win32_Process -Filter ('ProcessId='+$process.ProcessId)
        if ($null -ne $current -and $current.CreationDate -eq $process.CreationDate) {throw 'Owned compiler/target PID and birth remains before pruning'}
    }
}
Remove-Item -LiteralPath $cache -Recurse -Force
foreach($property in $record.files.PSObject.Properties) {Remove-Item -LiteralPath $actual[$property.Name] -Force}
if (Test-Path -LiteralPath $cache) {throw 'Redundant short compiler cache remains'}
foreach($property in $record.files.PSObject.Properties) {if (Test-Path -LiteralPath $actual[$property.Name]) {throw 'Superseded representation remains'}}
@{schema_version=1;inventory_sha256=(Get-FileHash -LiteralPath $recordPath -Algorithm SHA256).Hash.ToLowerInvariant();
    removed_bytes=$total;removed_files=$actual.Count;confirmed_no_owned_processes=$true;original_registry_preserved=$true;
    source_and_all_executable_bytes_retained=$true;checked_at_utc=[DateTime]::UtcNow.ToString('o')} |
    ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $project ('checked-pruning\'+$Inventory+'-removed.json')) -Encoding UTF8
Write-Output ('Checked native pruning complete: '+$total+' redundant bytes removed; exact source/executable corpus and original registry retained.')
