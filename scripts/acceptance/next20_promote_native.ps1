param([Parameter(Mandatory=$true)][ValidatePattern('^[a-z][a-z0-9-]{0,63}$')][string]$Project,
    [Parameter(Mandatory=$true)][ValidateRange(1,1000)][int]$Generation)
$ErrorActionPreference='Stop'
$workspace=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$campaign=Join-Path $workspace 'artifacts\runner-readiness-next-twenty-project-pass'
$projectRoot=Join-Path $campaign $Project
$stageRoot=Join-Path $campaign ('tmp\direct-native-zip\'+$Project)
$source=Join-Path $stageRoot ('retained-native-v'+$Generation)
$destination=Join-Path $projectRoot ('retained-native-v'+$Generation)
foreach($path in @((Join-Path $workspace 'artifacts'),$campaign,(Join-Path $campaign 'tmp'),(Join-Path $campaign 'tmp\direct-native-zip'),$stageRoot,$source,$projectRoot)){
    if((Resolve-Path -LiteralPath $path).ProviderPath -ne $path -or ((Get-Item -LiteralPath $path -Force).Attributes -band [IO.FileAttributes]::ReparsePoint)){throw 'Linked native promotion ancestor'}
}
if((Test-Path -LiteralPath $destination) -or [IO.Path]::GetFullPath($destination) -ne $destination -or
    -not $destination.StartsWith($projectRoot+'\',[StringComparison]::OrdinalIgnoreCase) -or
    -not $source.StartsWith($stageRoot+'\',[StringComparison]::OrdinalIgnoreCase)){throw 'Promotion escapes checked roots or overwrites a packet'}
$expected=@('index.json','packets.tar.gz','verified.json','complete-readback.json','expanded-removed.json','selected-restore.bin')
$actual=@(Get-ChildItem -LiteralPath $source -Force)
if($actual.Count -ne $expected.Count){throw 'Unexpected promotion payload count'}
foreach($entry in $actual){if($entry.PSIsContainer -or ($entry.Attributes -band [IO.FileAttributes]::ReparsePoint) -or $entry.Name -notin $expected){throw 'Unexpected or linked promotion payload'}}
$index=Get-Content -LiteralPath (Join-Path $source 'index.json') -Raw | ConvertFrom-Json
$verified=Get-Content -LiteralPath (Join-Path $source 'verified.json') -Raw | ConvertFrom-Json
$readback=Get-Content -LiteralPath (Join-Path $source 'complete-readback.json') -Raw | ConvertFrom-Json
$removed=Get-Content -LiteralPath (Join-Path $source 'expanded-removed.json') -Raw | ConvertFrom-Json
$indexHash=(Get-FileHash -LiteralPath (Join-Path $source 'index.json') -Algorithm SHA256).Hash.ToLowerInvariant()
$archiveHash=(Get-FileHash -LiteralPath (Join-Path $source 'packets.tar.gz') -Algorithm SHA256).Hash.ToLowerInvariant()
if($index.project -ne $Project -or $index.generation -ne $Generation -or $indexHash -ne $verified.index_sha256 -or
    $indexHash -ne $readback.index_sha256 -or $indexHash -ne $removed.index_sha256 -or $archiveHash -ne $index.archive_sha256 -or
    $archiveHash -ne $verified.archive_sha256 -or $archiveHash -ne $removed.archive_sha256 -or -not $removed.all_expanded_removed -or
    $readback.members_compared_byte_exact -ne $verified.members_verified){throw 'Promotion lacks exact full retention and expanded removal proofs'}
Move-Item -LiteralPath $source -Destination $destination
if((Test-Path -LiteralPath $source) -or (Resolve-Path -LiteralPath $destination).ProviderPath -ne $destination){throw 'Native promotion incomplete'}
@{schema_version=1;source=$source;destination=$destination;index_sha256=$indexHash;archive_sha256=$archiveHash;
  all_expanded_removed_before_promotion=$true;checked_at_utc=[DateTime]::UtcNow.ToString('o')} |
  ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $destination 'promoted.json') -Encoding UTF8
Write-Output 'Promoted only the fully verified native packet after checked expanded removal.'
