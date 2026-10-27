param([Parameter(Mandatory=$true)][ValidatePattern('^[a-z][a-z0-9-]{0,63}$')][string]$Project)
$ErrorActionPreference='Stop'
$workspace=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$campaign=Join-Path $workspace 'artifacts\runner-readiness-next-twenty-project-pass'
$projectRoot=Join-Path $campaign $Project
$root=Join-Path $projectRoot 'retained-local-v1'
if (Test-Path -LiteralPath (Join-Path $campaign ('active\'+$Project))) {throw 'Target source/runtime still active before evidence compaction removal'}
foreach($path in @((Join-Path $workspace 'artifacts'),$campaign,$projectRoot,$root)) {
    if ((Resolve-Path -LiteralPath $path).ProviderPath -ne $path -or ((Get-Item -LiteralPath $path -Force).Attributes -band [IO.FileAttributes]::ReparsePoint)) {throw 'Unsafe retained local record ancestor'}
}
$prepared=Get-Content -LiteralPath (Join-Path $root 'prepared.json') -Raw | ConvertFrom-Json
$indexPath=Join-Path $root 'index.json';$archive=Join-Path $root 'packets.tar.xz'
if ((Get-FileHash -LiteralPath $indexPath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $prepared.index_sha256 -or
    (Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash.ToLowerInvariant() -ne $prepared.archive_sha256) {throw 'Retained local record packet changed'}
$index=Get-Content -LiteralPath $indexPath -Raw | ConvertFrom-Json
if ($index.project -ne $Project -or $index.compression -ne 'tar.xz' -or @($index.files.PSObject.Properties).Count -gt 4000 -or
    (Get-Item -LiteralPath $archive).Length -gt 8388608) {throw 'Local record packet scope/bounds differ'}
$paths=@();$total=[long]0
foreach($property in $index.files.PSObject.Properties) {
    $relative=$property.Name
    if (-not $relative.StartsWith($Project+'/') -or $relative -match '(^|/)(\.|\.\.|)($|/)' -or $relative.Contains(':') -or $relative.Contains('\')) {throw 'Unsafe local logical path'}
    $path=[IO.Path]::GetFullPath((Join-Path $campaign $relative))
    if (-not $path.StartsWith($projectRoot+'\',[StringComparison]::OrdinalIgnoreCase) -or $path.StartsWith($root+'\',[StringComparison]::OrdinalIgnoreCase)) {throw 'Local record removal escaped exact project or targets own packet'}
    $checked=$path
    while($checked -ne $projectRoot) {
        if ((Resolve-Path -LiteralPath $checked).ProviderPath -ne $checked -or ((Get-Item -LiteralPath $checked -Force).Attributes -band [IO.FileAttributes]::ReparsePoint)) {throw 'Linked local record path/ancestor'}
        $checked=[IO.Path]::GetDirectoryName($checked)
    }
    $entry=Get-Item -LiteralPath $path -Force;$row=$property.Value;$total+=$entry.Length
    if ($entry.PSIsContainer -or $entry.Length -ne $row.bytes -or $entry.Length -gt 16777216 -or
        (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant() -ne $row.sha256) {throw 'Local logical bytes changed after exact retention'}
    $paths+=,$path
}
if ($total -ne $index.expanded_bytes -or $total -gt 33554432) {throw 'Local logical expansion bound differs'}
$selected=Join-Path $root 'selected-restore.bin'
if ((Get-FileHash -LiteralPath $selected -Algorithm SHA256).Hash.ToLowerInvariant() -ne $prepared.selected_restore.sha256) {throw 'Selected actual report restore changed'}
foreach($path in $paths) {Remove-Item -LiteralPath $path -Force}
foreach($path in $paths) {if (Test-Path -LiteralPath $path) {throw 'Expanded local record duplicate remains'}}
@{schema_version=1;all_expanded_removed=$true;files=$paths.Count;expanded_bytes=$total;
    index_sha256=$prepared.index_sha256;archive_sha256=$prepared.archive_sha256;
    selected_restore=$prepared.selected_restore;checked_at_utc=[DateTime]::UtcNow.ToString('o')} |
    ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $root 'expanded-removed.json') -Encoding UTF8
Write-Output ('Exact original local records retained and '+$paths.Count+' expanded duplicates checked-removed natively.')
