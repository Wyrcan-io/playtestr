$ErrorActionPreference='Stop'
$workspace=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$campaign=Join-Path $workspace 'artifacts\runner-readiness-next-twenty-project-pass'
$project=Join-Path $campaign 'cargo-generate'
$source=Join-Path $campaign 'tmp\direct-native-zip\cargo-generate\retained-native-v12'
$history=Join-Path $project 'retained-native-v12'
$current=Join-Path $project 'retained-native-v13'
if (Test-Path -LiteralPath $history) {throw 'Preserve existing history'}
$planPath=Join-Path $current 'working-retirement-plan.json'
$plan=Get-Content -LiteralPath $planPath -Raw | ConvertFrom-Json
if ($plan.source_root -ne $source -or $plan.historical_destination -ne $history -or $plan.obsolete_generated_archive -ne 'packets.tar.xz' -or
    -not $plan.all_four_actual_executable_bytes_compared -or $plan.original_logical_records_verified -ne 3810 -or $plan.current_logical_records_verified -ne 3813 -or $plan.projected_retained_bytes_with_margin -gt 67108864) {throw 'Unexpected working-packet retirement scope'}
foreach($starting in @($source,$current,(Join-Path $project 'retained-native-v2'))) {
    $checked=$starting
    while($checked -ne $workspace) {
        if (-not $checked.StartsWith($workspace+'\',[StringComparison]::OrdinalIgnoreCase) -or
            (Resolve-Path -LiteralPath $checked).ProviderPath -ne $checked -or ((Get-Item -LiteralPath $checked -Force).Attributes -band [IO.FileAttributes]::ReparsePoint)) {throw 'Unsafe checked retirement path/ancestor'}
        $checked=[IO.Path]::GetDirectoryName($checked)
    }
}
foreach($pair in @(@((Join-Path $current 'index.json'),$plan.current_index_sha256),@((Join-Path $current 'packets.tar.xz'),$plan.current_archive_sha256),
    @((Join-Path $project 'retained-native-v2\index.json'),$plan.canonical_index_sha256),@((Join-Path $project 'retained-native-v2\packets.tar.gz'),$plan.canonical_archive_sha256))) {
    if ((Get-FileHash -LiteralPath $pair[0] -Algorithm SHA256).Hash.ToLowerInvariant() -ne $pair[1]) {throw 'Required complete payload/dictionary changed'}
}
$entries=@(Get-ChildItem -LiteralPath $source -Force)
if ($entries.Count -ne @($plan.source_files.PSObject.Properties).Count -or $entries.Count -gt 12) {throw 'Working inventory count differs'}
foreach($entry in $entries) {
    $row=$plan.source_files.PSObject.Properties[$entry.Name].Value
    if ($entry.PSIsContainer -or ($entry.Attributes -band [IO.FileAttributes]::ReparsePoint) -or $null -eq $row -or $entry.Length -ne $row.bytes -or
        $entry.Length -gt 16777216 -or (Get-FileHash -LiteralPath $entry.FullName -Algorithm SHA256).Hash.ToLowerInvariant() -ne $row.sha256) {throw 'Working inventory bytes/type changed'}
}
# Exact nonrecursive file removal, followed by a checked move within this workspace.
Remove-Item -LiteralPath (Join-Path $source 'packets.tar.xz') -Force
Move-Item -LiteralPath $source -Destination $history
if ((Test-Path -LiteralPath $source) -or (Test-Path -LiteralPath (Join-Path $history 'packets.tar.xz'))) {throw 'Working wrapper retirement incomplete'}
@{schema_version=1;only_superseded_generated_encoding_removed=$true;all_original_indices_and_provenance_retained=$true;
    all_actual_report_input_metadata_and_four_executable_bytes_preserved=$true;required_current_generation=13;
    required_replacement_index_sha256=$plan.current_index_sha256;required_replacement_archive_sha256=$plan.current_archive_sha256;
    original_compression_wrappers_reconstructible=$false;retirement_plan_sha256=(Get-FileHash -LiteralPath $planPath -Algorithm SHA256).Hash.ToLowerInvariant();
    checked_at_utc=[DateTime]::UtcNow.ToString('o')} | ConvertTo-Json |
    Set-Content -LiteralPath (Join-Path $history 'retention-promotion.json') -Encoding UTF8
Write-Output 'Working encoding retired after complete comparison; all original indices/provenance retained and required complete actual payloads preserved.'
