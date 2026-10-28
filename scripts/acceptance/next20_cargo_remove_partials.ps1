$ErrorActionPreference='Stop'
$workspace=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$campaign=Join-Path $workspace 'artifacts\runner-readiness-next-twenty-project-pass'
$project=Join-Path $campaign 'cargo-generate'
foreach($generation in @(8,10)) {
    $root=Join-Path $project ('retained-native-v'+$generation)
    $recordPath=Join-Path $root 'incomplete-encoding-disposition-v2.json'
    $record=Get-Content -LiteralPath $recordPath -Raw | ConvertFrom-Json
    $expectedFile=if($generation -eq 8){'packets.tar.xz'}else{'packets.tar.gz'}
    $replacement=if($generation -eq 8){9}else{11}
    if ($record.generation -ne $generation -or $record.generated_file -ne $expectedFile -or $record.replacement_generation -ne $replacement -or $record.fully_read_back_logical_records -lt 1) {throw 'Unexpected partial cleanup scope'}
    if ((Test-Path -LiteralPath (Join-Path $root 'index.json')) -or (Test-Path -LiteralPath (Join-Path $root 'verified.json'))) {throw 'Completed evidence cannot be removed'}
    $path=Join-Path $root $expectedFile
    $archive=Join-Path $project ('retained-native-v'+$replacement+'\'+$expectedFile)
    $index=Join-Path $project ('retained-native-v'+$replacement+'\index.json')
    foreach($starting in @($path,$archive,$index)) {
        $checked=$starting
        while($checked -ne $workspace) {
            if (-not $checked.StartsWith($workspace+'\',[StringComparison]::OrdinalIgnoreCase) -or
                (Resolve-Path -LiteralPath $checked).ProviderPath -ne $checked -or ((Get-Item -LiteralPath $checked -Force).Attributes -band [IO.FileAttributes]::ReparsePoint)) {throw 'Unsafe partial cleanup path/ancestor'}
            $checked=[IO.Path]::GetDirectoryName($checked)
        }
    }
    if ($record.complete_archive -ne ('cargo-generate/retained-native-v'+$replacement+'/'+$expectedFile)) {throw 'Replacement archive escaped scope'}
    foreach($pair in @(@($path,$record.sha256),@($archive,$record.complete_archive_sha256),@($index,$record.complete_index_sha256))) {
        if ((Get-FileHash -LiteralPath $pair[0] -Algorithm SHA256).Hash.ToLowerInvariant() -ne $pair[1]) {throw 'Partial or required replacement changed'}
    }
    if ((Get-Item -LiteralPath $path).Length -ne $record.bytes -or $record.bytes -ge 4194304) {throw 'Partial byte bound changed'}
    Remove-Item -LiteralPath $path -Force
    if (Test-Path -LiteralPath $path) {throw 'Incomplete encoding still exists'}
    @{schema_version=1;only_incomplete_generated_encoding_removed=$true;required_completed_payload_preserved=$true;
        disposition_sha256=(Get-FileHash -LiteralPath $recordPath -Algorithm SHA256).Hash.ToLowerInvariant();checked_at_utc=[DateTime]::UtcNow.ToString('o')} |
        ConvertTo-Json | Set-Content -LiteralPath (Join-Path $root 'incomplete-encoding-removed-v2.json') -Encoding UTF8
}
Write-Output 'Two bounded incomplete generated encodings removed; completed payloads and failed command records preserved.'
