$ErrorActionPreference='Stop'
$workspace=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$campaign=Join-Path $workspace 'artifacts\runner-readiness-next-twenty-project-pass'
$project=Join-Path $campaign 'cargo-generate'
$retained=Join-Path $project 'retained-source'
$path=Join-Path $retained 'dependency-source-catalog.json'
$referencePath=Join-Path $retained 'dependency-source-catalog.reference.json'
$reference=Get-Content -LiteralPath $referencePath -Raw | ConvertFrom-Json
if (Test-Path -LiteralPath (Join-Path $campaign 'active\cargo-generate')) {throw 'Target still active before catalog duplicate disposal'}
foreach($item in @($campaign,$project,$retained,$path,(Join-Path $project 'retained-native-v2'))) {
    if ((Resolve-Path -LiteralPath $item).ProviderPath -ne $item -or ((Get-Item -LiteralPath $item -Force).Attributes -band [IO.FileAttributes]::ReparsePoint)) {throw 'Unsafe canonical catalog reference path'}
}
if ($reference.logical_file -ne 'retained-source/dependency-source-catalog.json' -or
    $reference.required_archive -ne 'cargo-generate/retained-native-v2/packets.tar.gz' -or
    $reference.required_index -ne 'cargo-generate/retained-native-v2/index.json') {throw 'Unexpected canonical catalog reference'}
foreach($pair in @(@((Join-Path $campaign $reference.required_archive),$reference.required_archive_sha256),@((Join-Path $campaign $reference.required_index),$reference.required_index_sha256),@($path,$reference.sha256))) {
    if ((Get-FileHash -LiteralPath $pair[0] -Algorithm SHA256).Hash.ToLowerInvariant() -ne $pair[1]) {throw 'Required canonical catalog or duplicate changed'}
}
if ((Get-Item -LiteralPath $path).Length -ne $reference.bytes) {throw 'Local duplicate catalog size changed'}
Remove-Item -LiteralPath $path -Force
if (Test-Path -LiteralPath $path) {throw 'Expanded identical catalog duplicate remains'}
@{schema_version=1;exact_duplicate_removed=$true;required_canonical_packet_preserved=$true;
    reference_sha256=(Get-FileHash -LiteralPath $referencePath -Algorithm SHA256).Hash.ToLowerInvariant();checked_at_utc=[DateTime]::UtcNow.ToString('o')} |
    ConvertTo-Json | Set-Content -LiteralPath (Join-Path $retained 'dependency-source-catalog-duplicate-removed.json') -Encoding UTF8
Write-Output 'Exact identical source catalog duplicate removed; fully verified required canonical native packet retained.'
