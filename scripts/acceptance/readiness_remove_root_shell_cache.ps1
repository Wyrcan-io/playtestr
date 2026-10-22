param([Parameter(Mandatory=$true)][ValidatePattern('^[0-9a-f]{32}$')][string]$EvidenceId)
$ErrorActionPreference='Stop'
$workspace=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$campaign=Join-Path $workspace 'artifacts\runner-readiness-ten-project-pass'
$evidence=Join-Path $campaign ('shell-cache-control\'+$EvidenceId)
$observation=Get-Content -LiteralPath (Join-Path $evidence 'original.json') -Raw | ConvertFrom-Json
$source=Join-Path $workspace 'Microsoft\Windows\PowerShell\ModuleAnalysisCache'
$copy=Join-Path $evidence 'original-ModuleAnalysisCache.bin'
foreach($path in @($campaign,(Join-Path $campaign 'shell-cache-control'),$evidence,(Join-Path $workspace 'Microsoft'),(Join-Path $workspace 'Microsoft\Windows'),(Join-Path $workspace 'Microsoft\Windows\PowerShell'),$source,$copy)){
    if((Get-Item -LiteralPath $path -Force).Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'Linked shell-cache observation'}
}
if((Resolve-Path -LiteralPath $source).ProviderPath -ne $source -or $observation.path -ne 'Microsoft/Windows/PowerShell/ModuleAnalysisCache'){throw 'Unexpected cache source path'}
if($observation.bytes -ne (Get-Item -LiteralPath $source).Length -or
    (Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash.ToLowerInvariant() -ne $observation.sha256 -or
    (Get-FileHash -LiteralPath $copy -Algorithm SHA256).Hash.ToLowerInvariant() -ne $observation.sha256){throw 'Original cache retention differs'}
$expected=@('Windows','Windows/PowerShell','Windows/PowerShell/ModuleAnalysisCache')
$entries=@(Get-ChildItem -LiteralPath (Join-Path $workspace 'Microsoft') -Recurse -Force)
if($entries.Count -ne $expected.Count){throw 'Unexpected Microsoft tree members; no removal'}
foreach($entry in $entries){
    if($entry.Attributes -band [IO.FileAttributes]::ReparsePoint -or
        $entry.FullName.Substring((Join-Path $workspace 'Microsoft').Length+1).Replace('\','/') -notin $expected){throw 'Unexpected cache tree; no removal'}
}
Remove-Item -LiteralPath $source -Force
foreach($folder in @('Microsoft\Windows\PowerShell','Microsoft\Windows','Microsoft')){
    $path=Join-Path $workspace $folder
    if(@(Get-ChildItem -LiteralPath $path -Force).Count -ne 0){throw 'Cache parent is not empty'}
    Remove-Item -LiteralPath $path -Force
}
@{removed=$true;original_sha256=$observation.sha256;original_bytes=$observation.bytes;scope='Only exact copied task-created module cache and now-empty parents removed with native PowerShell.'} |
    ConvertTo-Json | Set-Content -LiteralPath (Join-Path $evidence 'original-removed.json') -Encoding UTF8
Write-Output 'Retained and removed only the exact observed root module cache and empty parents.'
