$ErrorActionPreference='Stop'
$workspace=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$project=Join-Path $workspace 'artifacts\runner-readiness-next-twenty-project-pass\cz-cli'
$failed=Join-Path $project 'compaction-attempts\linux-limit16-first'
$complete=Join-Path $project 'retained-native-v3'
foreach($path in @($project,$failed,$complete)){
    if((Resolve-Path -LiteralPath $path).ProviderPath -ne $path -or
       ((Get-Item -LiteralPath $path -Force).Attributes -band [IO.FileAttributes]::ReparsePoint)){throw 'Linked or unexpected partial retention root'}
}
$proofPath=Join-Path $failed 'subset-verified.json'
$proof=Get-Content -LiteralPath $proofPath -Raw | ConvertFrom-Json
if(-not $proof.exact_reconstruction_verified -or $proof.full_packet -ne 'cz-cli/retained-native-v3' -or $proof.physical_prefix_members -ne 3149){throw 'Wrong exact reconstruction proof'}
$partial=Join-Path $failed 'packets.tar.gz'
$checks=@(
    @($partial,$proof.original_partial_sha256),
    @((Join-Path $complete 'packets.tar.gz'),$proof.full_archive_sha256),
    @((Join-Path $complete 'index.json'),$proof.full_index_sha256),
    @((Join-Path $PSScriptRoot 'next20_verify_partial_compaction.py'),$proof.source_helper_sha256))
foreach($check in $checks){
    $path=$check[0]
    if(((Get-Item -LiteralPath $path -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) -or
       (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant() -ne $check[1]){throw 'Changed reconstruction subject'}
}
if((Get-Item -LiteralPath $partial).Length -ne $proof.original_partial_bytes){throw 'Stopped archive size differs'}
$receipt=Join-Path $failed 'partial-payload-removed.json'
if(Test-Path -LiteralPath $receipt){throw 'Preserve original removal receipt'}
Remove-Item -LiteralPath $partial -Force
if(Test-Path -LiteralPath $partial){throw 'Duplicate partial payload remains'}
@{schema_version=1;removed_duplicate_payload=$true;original_partial_sha256=$proof.original_partial_sha256;
  reconstruction_proof_sha256=(Get-FileHash -LiteralPath $proofPath -Algorithm SHA256).Hash.ToLowerInvariant();
  full_archive_sha256=$proof.full_archive_sha256;checked_at_utc=[DateTime]::UtcNow.ToString('o');
  scope='Only the exactly reconstructible stopped archive payload was unlinked. Failed attempt events, original hash, full packet and reconstruction proof remain.'} |
  ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $receipt -Encoding UTF8
Write-Output 'Removed only byte-exact reconstructible stopped compaction payload; original failure and reconstruction evidence retained.'
