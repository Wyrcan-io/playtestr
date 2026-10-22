param([Parameter(Mandatory=$true)][ValidatePattern('^[0-9a-f]{32}$')][string]$ControlId)
$ErrorActionPreference='Stop'
$workspace=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$campaign=Join-Path $workspace 'artifacts\runner-readiness-ten-project-pass'
$parent=Join-Path $campaign ('product-controls\'+$ControlId)
$binary=Join-Path $parent 'bin\fixture.exe'
foreach($path in @($campaign,(Join-Path $campaign 'product-controls'),$parent,(Join-Path $parent 'bin'),$binary)){
    if((Get-Item -LiteralPath $path -Force).Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'Linked product fixture'}
}
$build=Get-Content -LiteralPath (Join-Path $parent 'build.json') -Raw | ConvertFrom-Json
if((Resolve-Path -LiteralPath $binary).ProviderPath -ne $binary -or
    $build.fixture_relative_path -ne ('artifacts/runner-readiness-ten-project-pass/product-controls/'+$ControlId+'/bin/fixture.exe') -or
    (Get-FileHash -LiteralPath $binary -Algorithm SHA256).Hash.ToLowerInvariant() -ne $build.fixture_sha256){throw 'Product fixture ownership/bytes differ'}
if(@(Get-ChildItem -LiteralPath (Join-Path $parent 'bin') -Force).Count -ne 1){throw 'Unexpected fixture bin entries'}
Remove-Item -LiteralPath $binary -Force
Remove-Item -LiteralPath (Join-Path $parent 'bin') -Force
Write-Output 'Removed only the exact owned synthetic product-control fixture executable.'
