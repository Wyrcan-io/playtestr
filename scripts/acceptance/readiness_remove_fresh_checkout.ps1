param([Parameter(Mandatory=$true)][ValidatePattern('^[0-9a-f]{32}$')][string]$CheckoutId)
$ErrorActionPreference='Stop'
$workspace=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$campaign=Join-Path $workspace 'artifacts\runner-readiness-ten-project-pass'
$parent=Join-Path $campaign ('fresh-checkout\'+$CheckoutId)
$target=Join-Path $parent 'payload'
foreach($path in @((Join-Path $workspace 'artifacts'),$campaign,(Join-Path $campaign 'fresh-checkout'),$parent,$target)) {
    if((Get-Item -LiteralPath $path -Force).Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'Linked checkout ancestor'}
}
if((Resolve-Path -LiteralPath $target).ProviderPath -ne $target -or -not $target.StartsWith($campaign+'\',[StringComparison]::OrdinalIgnoreCase)){throw 'Checkout removal escapes exact owned root'}
$intent=Get-Content -LiteralPath (Join-Path $parent 'intent.json') -Raw | ConvertFrom-Json
if($intent.id -ne $CheckoutId -or $intent.source -ne $workspace -or $intent.revision -notmatch '^[0-9a-f]{40}$'){throw 'Fresh checkout ownership differs'}
$index=Get-Content -LiteralPath (Join-Path $parent 'payload-index.json') -Raw | ConvertFrom-Json
$queue=[Collections.Generic.Queue[string]]::new();$queue.Enqueue($target);$count=0;$bytes=0
while($queue.Count){
    foreach($entry in Get-ChildItem -LiteralPath $queue.Dequeue() -Force){
        if($entry.Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'Linked fresh checkout member'}
        if($entry.PSIsContainer){$queue.Enqueue($entry.FullName);continue}
        $count++;$bytes+=$entry.Length
        if($count -gt 50000 -or $bytes -gt 1GB){throw 'Fresh checkout removal bound'}
        $relative=$entry.FullName.Substring($target.Length+1).Replace('\','/')
        $expected=$index.files.PSObject.Properties[$relative].Value
        if($null -eq $expected -or (Get-FileHash -LiteralPath $entry.FullName -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expected){throw 'Fresh checkout payload changed'}
    }
}
if($count -ne @($index.files.PSObject.Properties).Count -or $bytes -ne $index.bytes){throw 'Fresh checkout removal inventory incomplete'}
Remove-Item -LiteralPath $target -Recurse -Force
if(Test-Path -LiteralPath $target){throw 'Fresh checkout payload remains'}
@{removed=$true;files_verified=$count;bytes_verified=$bytes;owned_relative_path=('fresh-checkout/'+$CheckoutId+'/payload')} |
    ConvertTo-Json | Set-Content -LiteralPath (Join-Path $parent 'powershell-removed.json') -Encoding UTF8
Write-Output 'Removed only the owned fresh checkout and cache after native complete hash verification.'
