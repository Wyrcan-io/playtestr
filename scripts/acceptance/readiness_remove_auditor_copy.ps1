param([Parameter(Mandatory=$true)][ValidatePattern('^[0-9a-f]{32}$')][string]$ControlId)
$ErrorActionPreference='Stop'
$workspace=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$campaign=Join-Path $workspace 'artifacts\runner-readiness-ten-project-pass'
$parent=Join-Path $campaign ('final-auditor-controls\'+$ControlId)
$target=Join-Path $parent 'payload'
foreach($path in @((Join-Path $workspace 'artifacts'),$campaign,(Join-Path $campaign 'final-auditor-controls'),$parent,$target)) {
    $item=Get-Item -LiteralPath $path -Force
    if($item.Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'Linked auditor copy ancestor'}
}
if((Resolve-Path -LiteralPath $target).ProviderPath -ne $target -or
    -not $target.StartsWith($campaign+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)) {
    throw 'Auditor copy escapes exact owned payload'
}
$intent=Get-Content -LiteralPath (Join-Path $parent 'intent.json') -Raw | ConvertFrom-Json
if($intent.project -ne 'plop' -or $intent.host -ne 'linux' -or $intent.run -notmatch '^[0-9]{1,20}$'){throw 'Auditor copy owner differs'}
$index=Get-Content -LiteralPath (Join-Path $parent 'payload-index.json') -Raw | ConvertFrom-Json
$queue=[Collections.Generic.Queue[string]]::new();$queue.Enqueue($target);$count=0;$total=0
while($queue.Count) {
    foreach($entry in Get-ChildItem -LiteralPath $queue.Dequeue() -Force) {
        if($entry.Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'Linked auditor copy member'}
        if($entry.PSIsContainer){$queue.Enqueue($entry.FullName);continue}
        $count++;$total+=$entry.Length
        if($count -gt 10000 -or $total -gt 32MB -or $entry.Length -gt 4MB){throw 'Auditor copy removal inventory bound'}
        $relative=$entry.FullName.Substring($target.Length+1).Replace('\','/')
        $expected=$index.files.PSObject.Properties[$relative].Value
        if($null -eq $expected -or (Get-FileHash -LiteralPath $entry.FullName -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expected){
            throw 'Auditor copy differs from restored inventory'
        }
    }
}
if($count -ne @($index.files.PSObject.Properties).Count){throw 'Auditor copy inventory incomplete'}
Remove-Item -LiteralPath $target -Recurse -Force
if(Test-Path -LiteralPath $target){throw 'Auditor copy remains'}
@{owned_relative_path=('final-auditor-controls/'+$ControlId+'/payload');removed=$true;files_verified=$count;bytes_verified=$total;
    index_sha256=(Get-FileHash -LiteralPath (Join-Path $parent 'payload-index.json') -Algorithm SHA256).Hash.ToLowerInvariant()} |
    ConvertTo-Json | Set-Content -LiteralPath (Join-Path $parent 'powershell-removed.json') -Encoding UTF8
Write-Output 'Removed only the exact owned auditor payload after native PowerShell hash verification.'
