param([Parameter(Mandatory=$true)][ValidatePattern('^[a-z][a-z0-9-]{0,63}$')][string]$Project,
    [Parameter(Mandatory=$true)][ValidatePattern('^[0-9a-f]{32}$')][string]$Original,
    [Parameter(Mandatory=$true)][ValidatePattern('^[0-9a-f]{32}$')][string]$Duplicate)
$ErrorActionPreference='Stop'
if($Original -eq $Duplicate){throw 'Original and duplicate model roots must differ'}
$workspace=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$projectRoot=Join-Path $workspace ('artifacts\runner-readiness-next-twenty-project-pass\'+$Project)
$parent=Join-Path $projectRoot 'audit-controls'
$source=Join-Path $parent $Original;$target=Join-Path $parent $Duplicate
foreach($root in @($source,$target)){
    if((Resolve-Path -LiteralPath $root).ProviderPath -ne $root -or -not $root.StartsWith($projectRoot+'\',[StringComparison]::OrdinalIgnoreCase)){throw 'Audit deduplication escapes owned project'}
    $ancestor=$root
    while($ancestor -ne $workspace){
        if((Get-Item -LiteralPath $ancestor -Force).Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'Linked audit ancestor'}
        $ancestor=[IO.Path]::GetDirectoryName($ancestor)
    }
}
$files=@(Get-ChildItem -LiteralPath $target -Force)
$originalFiles=@(Get-ChildItem -LiteralPath $source -Force)
if($files.Count -gt 100 -or $files.Count -ne $originalFiles.Count){throw 'Audit duplicate file count bound/mismatch'}
$aliases=@{}
foreach($file in $files){
    if($file.PSIsContainer -or $file.Attributes -band [IO.FileAttributes]::ReparsePoint -or $file.Name -notmatch '^[a-zA-Z0-9-]+\.json$'){throw 'Unknown duplicate audit payload'}
    $reference=Join-Path $source $file.Name
    if(-not(Test-Path -LiteralPath $reference -PathType Leaf) -or (Get-Item -LiteralPath $reference -Force).Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'Missing/linked original audit payload'}
    $digest=(Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
    if($file.Length -ne (Get-Item -LiteralPath $reference).Length -or $digest -ne (Get-FileHash -LiteralPath $reference -Algorithm SHA256).Hash.ToLowerInvariant()){throw 'Audit models differ; preserve both for investigation'}
    $aliases[$file.Name]=@{bytes=$file.Length;sha256=$digest;reference=('audit-controls/'+$Original+'/'+$file.Name)}
}
$receipt=Join-Path $parent ($Duplicate+'-aliases.json')
if(Test-Path -LiteralPath $receipt){throw 'Existing audit alias receipt'}
@{schema_version=1;original=$Original;duplicate=$Duplicate;files=$aliases;scope='Identical derivative model payloads only. Distinct revalidation command/event IDs remain preserved; no execution deduplication.'} |
    ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $receipt -Encoding UTF8
$read=Get-Content -LiteralPath $receipt -Raw | ConvertFrom-Json
if(@($read.files.PSObject.Properties).Count -ne $files.Count){throw 'Incomplete persisted audit alias index'}
Remove-Item -LiteralPath $target -Recurse -Force
if(Test-Path -LiteralPath $target){throw 'Duplicate model expansion remains'}
Write-Output 'Verified every duplicate audit-model byte against retained originals; persisted one-level aliases and removed only the exact duplicate derivative tree.'
