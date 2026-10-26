$ErrorActionPreference='Stop'
$workspace=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$campaign=Join-Path $workspace 'artifacts\runner-readiness-next-twenty-project-pass'
$retained=Join-Path $campaign 'cz-cli\retained-catalogs-v1'
$proofPath=Join-Path $retained 'duplicate-aliases.json'
$proof=Get-Content -LiteralPath $proofPath -Raw | ConvertFrom-Json
if((Get-FileHash -LiteralPath (Join-Path $retained 'index.json') -Algorithm SHA256).Hash.ToLowerInvariant() -ne $proof.original_index_sha256 -or
   (Get-FileHash -LiteralPath (Join-Path $retained 'packets.tar.gz') -Algorithm SHA256).Hash.ToLowerInvariant() -ne $proof.archive_sha256){throw 'Changed original catalog packet'}
$paths=@()
foreach($property in $proof.files.PSObject.Properties){
    $relative=$property.Name
    if($relative -notmatch '^cz-cli/(runtime-catalogs/[0-9a-f]{64}\.json|retained-source/launch-runtime-catalog\.json|retained-catalogs-v1/selected-restore\.json)$'){throw 'Unapproved duplicate alias path'}
    $expected=[IO.Path]::GetFullPath((Join-Path $campaign $relative))
    if(-not $expected.StartsWith($campaign+'\cz-cli\',[StringComparison]::OrdinalIgnoreCase) -or (Resolve-Path -LiteralPath $expected).ProviderPath -ne $expected){throw 'Duplicate alias escapes owned project'}
    $ancestor=$expected
    while($ancestor -ne $workspace){
        if((Get-Item -LiteralPath $ancestor -Force).Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'Linked duplicate alias ancestor'}
        $ancestor=[IO.Path]::GetDirectoryName($ancestor)
    }
    if((Get-Item -LiteralPath $expected).Length -ne $property.Value.bytes -or
       (Get-FileHash -LiteralPath $expected -Algorithm SHA256).Hash.ToLowerInvariant() -ne $property.Value.sha256){throw 'Duplicate alias bytes changed'}
    $paths+=@($expected)
}
if($paths.Count -ne 4){throw 'Unexpected exact duplicate count'}
$receipt=Join-Path $retained 'duplicate-aliases-removed.json'
if(Test-Path -LiteralPath $receipt){throw 'Preserve existing duplicate removal proof'}
foreach($path in $paths){Remove-Item -LiteralPath $path -Force;if(Test-Path -LiteralPath $path){throw 'Exact duplicate remains'}}
@{schema_version=1;all_exact_duplicates_removed=$true;files=$paths.Count;
  aliases_sha256=(Get-FileHash -LiteralPath $proofPath -Algorithm SHA256).Hash.ToLowerInvariant();
  original_index_sha256=$proof.original_index_sha256;selected_restore_sha256=$proof.selected_restore_sha256;
  checked_at_utc=[DateTime]::UtcNow.ToString('o')} | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $receipt -Encoding UTF8
Write-Output 'Removed only four exact catalog duplicates against the unchanged verified archive; all original logical bytes remain readable.'
