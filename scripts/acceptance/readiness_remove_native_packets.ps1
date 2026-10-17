param([Parameter(Mandatory=$true)][ValidatePattern('^[a-z][a-z0-9-]{0,63}$')][string]$Project,
    [ValidateRange(1,1000)][int]$Generation=1)
$ErrorActionPreference='Stop'
$workspace=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$campaign=Join-Path $workspace 'artifacts\runner-readiness-ten-project-pass'
$retained=Join-Path $campaign ($Project+'\retained-native-v'+$Generation)
foreach($path in @((Join-Path $workspace 'artifacts'),$campaign,(Join-Path $campaign 'native'),(Join-Path $campaign $Project),$retained)) {
    if ((Get-Item -LiteralPath $path -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Linked packet removal ancestor' }
}
$indexPath=Join-Path $retained 'index.json'
$verified=Get-Content -LiteralPath (Join-Path $retained 'verified.json') -Raw | ConvertFrom-Json
if ((Get-FileHash -LiteralPath $indexPath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $verified.index_sha256) { throw 'Compaction index changed' }
$index=Get-Content -LiteralPath $indexPath -Raw | ConvertFrom-Json
if (($Generation -ne 1 -and $null -eq $index.generation) -or
    ($null -ne $index.generation -and $index.generation -ne $Generation)) { throw 'Compaction generation mismatch' }
if ($index.project -ne $Project -or (Get-FileHash -LiteralPath (Join-Path $retained 'packets.tar.gz') -Algorithm SHA256).Hash.ToLowerInvariant() -ne $index.archive_sha256) { throw 'Compaction ownership or archive changed' }
$actual=@{};$targets=@()
foreach($run in $index.runs) {
    if ($run -notmatch '^[0-9]{1,20}$') { throw 'Invalid packet removal run' }
    $target=(Resolve-Path -LiteralPath (Join-Path $campaign ('native\'+$run))).ProviderPath
    if ($target -ne (Join-Path $campaign ('native\'+$run)) -or ((Get-Item -LiteralPath $target -Force).Attributes -band [IO.FileAttributes]::ReparsePoint)) { throw 'Packet removal escapes exact owned root' }
    $targets+=$target;$pending=[Collections.Generic.Queue[string]]::new();$pending.Enqueue($target)
    while($pending.Count) {
        foreach($entry in Get-ChildItem -LiteralPath $pending.Dequeue() -Force) {
            if ($entry.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Unreviewed packet link' }
            if ($entry.PSIsContainer) { $pending.Enqueue($entry.FullName);continue }
            if ($actual.Count -ge 40000) { throw 'Packet inventory bound' }
            $relative=$entry.FullName.Substring($campaign.Length+1).Replace('\','/')
            $expected=$index.files.PSObject.Properties[$relative].Value
            if ($null -eq $expected -or $entry.Length -ne $expected.bytes -or (Get-FileHash -LiteralPath $entry.FullName -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expected.sha256) { throw 'Expanded evidence differs from verified archive inventory' }
            $actual[$relative]=$true
        }
    }
}
if ($actual.Count -ne $verified.members_verified -or $actual.Count -ne @($index.files.PSObject.Properties).Count) { throw 'Expanded packet coverage changed' }
foreach($target in $targets) { Remove-Item -LiteralPath $target -Recurse -Force; if(Test-Path -LiteralPath $target){throw 'Expanded packet remains'} }
@{removed_runs=$index.runs;index_sha256=$verified.index_sha256;archive_sha256=$index.archive_sha256;all_expanded_removed=$true} | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $retained 'expanded-removed.json') -Encoding UTF8
Write-Output 'Removed only expanded packets whose complete bytes matched the verified retained archive.'
