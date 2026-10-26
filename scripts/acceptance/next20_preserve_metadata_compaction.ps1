$ErrorActionPreference='Stop'
$workspace=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$project=(Resolve-Path -LiteralPath (Join-Path $workspace 'artifacts\runner-readiness-next-twenty-project-pass\cz-cli')).ProviderPath
$source=Join-Path $project 'retained-native-v4'
if((Resolve-Path -LiteralPath $source).ProviderPath -ne $source -or ((Get-Item -LiteralPath $source -Force).Attributes -band [IO.FileAttributes]::ReparsePoint)){throw 'Unexpected metadata-only packet root'}
$verified=Get-Content -LiteralPath (Join-Path $source 'verified.json') -Raw | ConvertFrom-Json
$indexPath=Join-Path $source 'index.json'
if((Get-FileHash -LiteralPath $indexPath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $verified.index_sha256){throw 'Changed metadata-only index'}
$index=Get-Content -LiteralPath $indexPath -Raw | ConvertFrom-Json
if($index.project -ne 'cz-cli' -or $index.generation -ne 4 -or @($index.files.PSObject.Properties).Count -ne 1 -or
   @($index.files.PSObject.Properties)[0].Name -ne 'native/40026867471/run-metadata.json'){throw 'Not the exact premature metadata-only compaction'}
if((Get-FileHash -LiteralPath (Join-Path $source 'packets.tar.gz') -Algorithm SHA256).Hash.ToLowerInvariant() -ne $index.archive_sha256){throw 'Changed metadata-only archive'}
$destination=Join-Path $project 'compaction-attempts\windows-metadata-only'
if(-not $destination.StartsWith($project+'\',[StringComparison]::OrdinalIgnoreCase) -or (Test-Path -LiteralPath $destination)){throw 'Unsafe preservation destination'}
Move-Item -LiteralPath $source -Destination $destination
Write-Output 'Preserved the premature metadata-only compaction in its separate attempt directory; it has zero application/native qualification credit.'
