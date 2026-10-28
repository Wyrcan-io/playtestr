param([Parameter(Mandatory=$true)][ValidatePattern('^[a-z][a-z0-9-]{0,63}$')][string]$Project,
    [Parameter(Mandatory=$true)][ValidateRange(1,1000)][int]$Generation)
$ErrorActionPreference='Stop'
$workspace=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$campaign=Join-Path $workspace 'artifacts\runner-readiness-next-twenty-project-pass'
$projectRoot=Join-Path $campaign $Project
$stage=Join-Path $campaign ('tmp\native-runtime-reference\'+$Project+'-v'+$Generation)
$final=Join-Path $projectRoot ('retained-native-v'+$Generation)
if (Test-Path -LiteralPath $final) {throw 'Preserve existing retained destination'}
if (-not $final.StartsWith($projectRoot+'\',[StringComparison]::OrdinalIgnoreCase) -or
    -not $stage.StartsWith($campaign+'\tmp\native-runtime-reference\',[StringComparison]::OrdinalIgnoreCase)) {throw 'Staged move escapes exact owned paths'}
foreach($starting in @($stage,$projectRoot)) {
    $checked=$starting
    while($checked -ne $workspace) {
        if (-not $checked.StartsWith($workspace+'\',[StringComparison]::OrdinalIgnoreCase) -or
            (Resolve-Path -LiteralPath $checked).ProviderPath -ne $checked -or ((Get-Item -LiteralPath $checked -Force).Attributes -band [IO.FileAttributes]::ReparsePoint)) {throw 'Unsafe staged move path/ancestor'}
        $checked=[IO.Path]::GetDirectoryName($checked)
    }
}
$prepared=Get-Content -LiteralPath (Join-Path $stage 'staged-prepared.json') -Raw | ConvertFrom-Json
$owner=Get-Content -LiteralPath (Join-Path $stage 'task-owned.json') -Raw | ConvertFrom-Json
if ($owner.workspace -ne $workspace -or $owner.project -ne $Project -or $owner.generation -ne $Generation -or
    $owner.desired_retained_root -ne $final -or $prepared.staged_root -ne $stage -or $prepared.desired_retained_root -ne $final -or
    -not $prepared.all_required_original_report_input_metadata_and_actual_executable_bytes_verified -or
    $prepared.projected_retained_bytes_with_margin -gt 67108864) {throw 'Staged runtime representation proof/scope/headroom differs'}
$source=$prepared.source_retained_root
if ($owner.source_retained_root -ne $source -or -not $source.StartsWith($projectRoot+'\retained-native-v',[StringComparison]::OrdinalIgnoreCase) -or
    [IO.Path]::GetDirectoryName($source) -ne $projectRoot) {throw 'Source retention root escaped project'}
foreach($path in @($source,(Join-Path $source 'packets.tar.gz'))) {
    if ((Resolve-Path -LiteralPath $path).ProviderPath -ne $path -or ((Get-Item -LiteralPath $path -Force).Attributes -band [IO.FileAttributes]::ReparsePoint)) {throw 'Unsafe superseded generated source archive'}
}
$dictionaryReference=$prepared.required_canonical_runtime
if ($dictionaryReference.archive -notmatch ('^'+[Regex]::Escape($Project)+'/retained-native-v[0-9]{1,4}/packets\.tar\.gz$')) {throw 'Unsafe canonical runtime dictionary reference'}
$dictionary=[IO.Path]::GetFullPath((Join-Path $campaign $dictionaryReference.archive))
$checked=$dictionary
while($checked -ne $workspace) {
    if (-not $checked.StartsWith($workspace+'\',[StringComparison]::OrdinalIgnoreCase) -or
        (Resolve-Path -LiteralPath $checked).ProviderPath -ne $checked -or ((Get-Item -LiteralPath $checked -Force).Attributes -band [IO.FileAttributes]::ReparsePoint)) {throw 'Unsafe canonical runtime dictionary ancestor'}
    $checked=[IO.Path]::GetDirectoryName($checked)
}
foreach($pair in @(@((Join-Path $source 'packets.tar.gz'),$prepared.source_archive_sha256),@((Join-Path $source 'index.json'),$prepared.source_index_sha256),
    @($dictionary,$dictionaryReference.archive_sha256),@((Join-Path ([IO.Path]::GetDirectoryName($dictionary)) 'index.json'),$dictionaryReference.index_sha256))) {
    if ((Get-FileHash -LiteralPath $pair[0] -Algorithm SHA256).Hash.ToLowerInvariant() -ne $pair[1]) {throw 'Required original archive/index/canonical runtime changed'}
}
$count=0;$bytes=[long]0
foreach($entry in Get-ChildItem -LiteralPath $stage -Force) {
    if ($entry.PSIsContainer -or ($entry.Attributes -band [IO.FileAttributes]::ReparsePoint)) {throw 'Unknown staged directory/link'}
    if ($entry.Name -eq 'staged-prepared.json') {continue}
    $row=$prepared.files.PSObject.Properties[$entry.Name].Value
    if ($null -eq $row -or $entry.Length -ne $row.bytes -or (Get-FileHash -LiteralPath $entry.FullName -Algorithm SHA256).Hash.ToLowerInvariant() -ne $row.sha256) {throw 'Staged exact payload changed'}
    $count++;$bytes+=$entry.Length
}
if ($count -ne @($prepared.files.PSObject.Properties).Count -or $count -gt 20 -or $bytes -gt 16777216) {throw 'Staged inventory coverage/count/byte bound differs'}
# Every substantive byte already has a verified durable replacement in stage.
# Remove only the superseded generated transport wrapper, then atomically move
# its complete replacement within this workspace using one native shell.
Remove-Item -LiteralPath (Join-Path $source 'packets.tar.gz') -Force
Move-Item -LiteralPath $stage -Destination $final
if ((Test-Path -LiteralPath $stage) -or -not (Test-Path -LiteralPath (Join-Path $final 'verified.json'))) {throw 'Checked staged promotion incomplete; preserve working data'}
@{schema_version=1;complete_replacement_promoted=$true;superseded_transport_archive_removed=$true;
    source_index_sha256=$prepared.source_index_sha256;source_archive_sha256=$prepared.source_archive_sha256;
    required_replacement=$final;required_replacement_index_sha256=(Get-FileHash -LiteralPath (Join-Path $final 'index.json') -Algorithm SHA256).Hash.ToLowerInvariant();
    required_canonical_dictionary_preserved=$true;all_actual_executable_and_report_input_metadata_bytes_preserved=$true;
    obsolete_compression_wrapper_bytes_reconstructible=$false;checked_at_utc=[DateTime]::UtcNow.ToString('o')} |
    ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $source 'retention-promotion.json') -Encoding UTF8
Write-Output 'Checked promotion complete: substantive actual bytes retained; required canonical dictionary preserved; obsolete generated transport wrapper superseded explicitly.'
