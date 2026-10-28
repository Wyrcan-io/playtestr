$ErrorActionPreference='Stop'
$workspace=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$campaign=Join-Path $workspace 'artifacts\runner-readiness-next-twenty-project-pass'
$project=Join-Path $campaign 'cargo-generate'
$root=Join-Path $project 'retained-native-v7'
$path=Join-Path $root 'packets.tar.xz'
if ((Test-Path -LiteralPath (Join-Path $root 'index.json')) -or (Test-Path -LiteralPath (Join-Path $root 'verified.json'))) {throw 'Completed evidence packet cannot be discarded'}
foreach($item in @((Join-Path $workspace 'artifacts'),$campaign,$project,$root,$path)) {
    if ((Resolve-Path -LiteralPath $item).ProviderPath -ne $item -or ((Get-Item -LiteralPath $item -Force).Attributes -band [IO.FileAttributes]::ReparsePoint)) {throw 'Unsafe incomplete-encoding ancestor'}
}
$recordPath=Join-Path $root 'incomplete-encoding-disposition.json'
$record=Get-Content -LiteralPath $recordPath -Raw | ConvertFrom-Json
if ($record.generated_file -ne 'packets.tar.xz' -or -not $record.source_payload_and_first_failures_preserved -or
    $record.complete_source_archive -ne 'cargo-generate/retained-native-v6/packets.tar.gz') {throw 'Unexpected incomplete encoding scope'}
foreach($pair in @(@($path,$record.sha256),@((Join-Path $project 'retained-native-v6\packets.tar.gz'),$record.complete_source_archive_sha256),
    @((Join-Path $project 'retained-native-v6\index.json'),$record.complete_source_index_sha256),@((Join-Path $project 'retained-native-v2\packets.tar.gz'),$record.canonical_dictionary_archive_sha256))) {
    if ((Get-FileHash -LiteralPath $pair[0] -Algorithm SHA256).Hash.ToLowerInvariant() -ne $pair[1]) {throw 'Incomplete file or fully retained original source changed'}
}
if ((Get-Item -LiteralPath $path).Length -ne $record.bytes -or $record.bytes -ge 2097152) {throw 'Incomplete encoding byte bound changed'}
Remove-Item -LiteralPath $path -Force
if (Test-Path -LiteralPath $path) {throw 'Unusable generated partial remains'}
@{schema_version=1;only_incomplete_generated_encoding_removed=$true;complete_original_source_preserved=$true;
    disposition_sha256=(Get-FileHash -LiteralPath $recordPath -Algorithm SHA256).Hash.ToLowerInvariant();checked_at_utc=[DateTime]::UtcNow.ToString('o')} |
    ConvertTo-Json | Set-Content -LiteralPath (Join-Path $root 'incomplete-encoding-removed.json') -Encoding UTF8
Write-Output 'Unusable generated encoding removed; complete original source, every first failure and failed-command evidence preserved.'
