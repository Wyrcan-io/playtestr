param([Parameter(Mandatory=$true)][ValidateSet('cz-cli')][string]$Project)
$ErrorActionPreference='Stop'
$workspace=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$campaign=Join-Path $workspace 'artifacts\runner-readiness-next-twenty-project-pass'
$projectRoot=Join-Path $campaign $Project
$retained=Join-Path $projectRoot 'retained-catalogs-v1'
$indexPath=Join-Path $retained 'index.json'
foreach($path in @($campaign,$projectRoot,$retained,$indexPath,(Join-Path $retained 'packets.tar.gz'),(Join-Path $retained 'verified.json'))){
    if((Resolve-Path -LiteralPath $path).ProviderPath -ne $path -or
        ((Get-Item -LiteralPath $path -Force).Attributes -band [IO.FileAttributes]::ReparsePoint)){throw 'Linked/unexpected catalog retention path'}
}
$verified=Get-Content -LiteralPath (Join-Path $retained 'verified.json') -Raw | ConvertFrom-Json
if((Get-FileHash -LiteralPath $indexPath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $verified.index_sha256){throw 'Changed catalog index'}
$index=Get-Content -LiteralPath $indexPath -Raw | ConvertFrom-Json
if($index.kind -ne 'local-compiled-runtime-catalogs' -or $index.project -ne $Project -or
    (Get-FileHash -LiteralPath (Join-Path $retained 'packets.tar.gz') -Algorithm SHA256).Hash.ToLowerInvariant() -ne $index.archive_sha256){throw 'Changed/foreign catalog archive'}
$targets=@()
foreach($entry in $index.files.PSObject.Properties){
    $relative=$entry.Name
    $pattern='^'+[Regex]::Escape($Project)+'/(runtime-catalogs/[0-9a-f]{64}\.json|rebuilds/[0-9a-f]{32}/runtime-catalog\.json|faults/[0-9a-f]{32}/F0[123]-(baseline|mutated|restored|terminal-only)-runtime-catalog\.json)$'
    if($relative -notmatch $pattern){throw 'Unsafe catalog removal scope'}
    $expected=[IO.Path]::GetFullPath((Join-Path $campaign $relative))
    if(-not $expected.StartsWith($projectRoot+'\',[StringComparison]::OrdinalIgnoreCase)){throw 'Catalog removal escapes project'}
    $target=(Resolve-Path -LiteralPath $expected).ProviderPath
    if($target -ne $expected){throw 'Unexpected resolved catalog'}
    $ancestor=$target
    while($ancestor -ne $workspace){
        if((Get-Item -LiteralPath $ancestor -Force).Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'Linked catalog ancestor'}
        $ancestor=[IO.Path]::GetDirectoryName($ancestor)
    }
    $file=Get-Item -LiteralPath $target -Force
    if($file.PSIsContainer -or $file.Length -ne $entry.Value.bytes -or
        (Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash.ToLowerInvariant() -ne $entry.Value.sha256){throw 'Changed actual catalog bytes'}
    $targets+=@{path=$target;bytes=$entry.Value.bytes;sha256=$entry.Value.sha256}
}
if($targets.Count -ne $verified.logical_catalogs -or $targets.Count -eq 0){throw 'Missing catalog removal inventory'}
foreach($entry in $targets){
    if((Get-Item -LiteralPath $entry.path -Force).Length -ne $entry.bytes -or
        (Get-FileHash -LiteralPath $entry.path -Algorithm SHA256).Hash.ToLowerInvariant() -ne $entry.sha256){throw 'Catalog changed after verification'}
    Remove-Item -LiteralPath $entry.path -Force
    if(Test-Path -LiteralPath $entry.path){throw 'Catalog expansion remains'}
}
$receipt=Join-Path $retained 'expanded-removed.json'
if(Test-Path -LiteralPath $receipt){throw 'Preserve existing catalog removal receipt'}
@{schema_version=1;project=$Project;all_expanded_removed=$true;files_removed=$targets.Count;index_sha256=$verified.index_sha256;archive_sha256=$index.archive_sha256}|ConvertTo-Json -Depth 5|Set-Content -LiteralPath $receipt -Encoding UTF8
Write-Output 'Removed only exact archived local catalog files; all reports, events, patches and source receipts remain.'
