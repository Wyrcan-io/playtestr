param([Parameter(Mandatory=$true)][ValidatePattern('^[a-z][a-z0-9-]{0,63}$')][string]$Project,
    [Parameter(Mandatory=$true)][ValidateRange(1,1000)][int]$Generation)
$ErrorActionPreference='Stop'
$workspace=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$campaign=Join-Path $workspace 'artifacts\runner-readiness-next-twenty-project-pass'
$projectRoot=Join-Path $campaign $Project
$root=Join-Path $projectRoot ('retained-native-v'+$Generation)
$recordPath=Join-Path $root 'archive-representation.json'
$record=Get-Content -LiteralPath $recordPath -Raw | ConvertFrom-Json
$proof=Get-Content -LiteralPath (Join-Path $root 'archive-representation-verified.json') -Raw | ConvertFrom-Json
if ($record.format -ne 'exact-original-gzip+copy-insert-v1' -or $record.original_archive -ne 'packets.tar.gz' -or $record.delta_file -ne 'archive.delta.xz' -or
    $record.required_dictionary -notmatch ('^'+[Regex]::Escape($Project)+'/retained-native-v[0-9]{1,4}/packets\.tar\.gz$')) {throw 'Unexpected archive representation scope'}
$original=Join-Path $root 'packets.tar.gz'
$base=[IO.Path]::GetFullPath((Join-Path $campaign $record.required_dictionary))
if (-not $base.StartsWith($projectRoot+'\',[StringComparison]::OrdinalIgnoreCase) -or [IO.Path]::GetDirectoryName($base) -eq $root) {throw 'Archive dictionary escaped project or formed cycle'}
foreach($path in @($original,$base,(Join-Path $root 'archive.delta.xz'),$recordPath)) {
    $checked=$path
    while($checked -ne $workspace) {
        if (-not $checked.StartsWith($workspace+'\',[StringComparison]::OrdinalIgnoreCase) -or
            (Resolve-Path -LiteralPath $checked).ProviderPath -ne $checked -or ((Get-Item -LiteralPath $checked -Force).Attributes -band [IO.FileAttributes]::ReparsePoint)) {throw 'Unsafe archive representation path/ancestor'}
        $checked=[IO.Path]::GetDirectoryName($checked)
    }
}
if (Test-Path -LiteralPath (Join-Path ([IO.Path]::GetDirectoryName($base)) 'archive-representation.json')) {throw 'Archive dictionary representation chain'}
foreach($pair in @(@($recordPath,$proof.representation_sha256),@((Join-Path $root 'index.json'),$record.original_index_sha256),
    @((Join-Path $root 'archive.delta.xz'),$record.codec.delta_sha256),@($base,$record.required_dictionary_archive_sha256),
    @((Join-Path ([IO.Path]::GetDirectoryName($base)) 'index.json'),$record.required_dictionary_index_sha256),@($original,$record.codec.target_sha256))) {
    if ((Get-FileHash -LiteralPath $pair[0] -Algorithm SHA256).Hash.ToLowerInvariant() -ne $pair[1]) {throw 'Required original/dictionary/encoded archive changed'}
}
if (-not $proof.full_original_gzip_byte_roundtrip -or (Get-Item -LiteralPath $original).Length -ne $record.codec.target_bytes) {throw 'Exact original archive roundtrip missing'}
Remove-Item -LiteralPath $original -Force
if (Test-Path -LiteralPath $original) {throw 'Expanded duplicate archive remains'}
@{schema_version=1;expanded_archive_removed=$true;exact_original_archive_bytes_reconstructible=$true;
    original_archive_sha256=$record.codec.target_sha256;required_dictionary_preserved=$true;
    representation_sha256=$proof.representation_sha256;checked_at_utc=[DateTime]::UtcNow.ToString('o')} |
    ConvertTo-Json | Set-Content -LiteralPath (Join-Path $root 'archive-duplicate-removed.json') -Encoding UTF8
Write-Output 'Exact original archive duplicate removed; lossless representation, unchanged original index and required physical dictionary retained.'
