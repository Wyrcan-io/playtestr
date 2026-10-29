param([Parameter(Mandatory=$true)][ValidatePattern('^[a-z][a-z0-9-]{0,63}$')][string]$Project,
    [Parameter(Mandatory=$true)][ValidateRange(1,1000)][int]$Generation,
    [switch]$Staged)
$ErrorActionPreference='Stop'
$workspace=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$campaign=Join-Path $workspace 'artifacts\runner-readiness-next-twenty-project-pass'
$retained=Join-Path $campaign ($Project+'\retained-native-v'+$Generation)
if($Staged){
    $retained=Join-Path $campaign ('tmp\direct-native-zip\'+$Project+'\retained-native-v'+$Generation)
    foreach($part in @('tmp','tmp\direct-native-zip',('tmp\direct-native-zip\'+$Project))){
        $path=Join-Path $campaign $part
        if((Resolve-Path -LiteralPath $path).ProviderPath -ne $path -or ((Get-Item -LiteralPath $path -Force).Attributes -band [IO.FileAttributes]::ReparsePoint)){throw 'Linked staged retention ancestor'}
    }
}
foreach($path in @((Join-Path $workspace 'artifacts'),$campaign,(Join-Path $campaign 'native'),(Join-Path $campaign $Project),$retained)) {
    $resolved=(Resolve-Path -LiteralPath $path).ProviderPath
    if ($resolved -ne $path -or ((Get-Item -LiteralPath $path -Force).Attributes -band [IO.FileAttributes]::ReparsePoint)) { throw 'Linked or unexpected packet removal ancestor' }
}
$indexPath=Join-Path $retained 'index.json'
$verified=Get-Content -LiteralPath (Join-Path $retained 'verified.json') -Raw | ConvertFrom-Json
if ((Get-FileHash -LiteralPath $indexPath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $verified.index_sha256) { throw 'Compaction index changed' }
$index=Get-Content -LiteralPath $indexPath -Raw | ConvertFrom-Json
$archiveName='packets.tar.gz'
if ($null -ne $index.PSObject.Properties['compression']) {
    if ($index.compression -eq 'tar.xz') {$archiveName='packets.tar.xz'}
    elseif ($index.compression -ne 'tar.gz') {throw 'Unreviewed native packet compression'}
}
if ($index.project -ne $Project -or $index.generation -ne $Generation -or
    (Get-FileHash -LiteralPath (Join-Path $retained $archiveName) -Algorithm SHA256).Hash.ToLowerInvariant() -ne $index.archive_sha256) { throw 'Compaction ownership/archive mismatch' }
$actual=@{};$targets=@()
$logicalFiles=@{}
foreach($property in $index.files.PSObject.Properties){$logicalFiles[$property.Name]=$property.Value}
if($null -ne $index.PSObject.Properties['external_exact_payloads']) {
    $required=$index.required_canonical_packet
    if($index.schema_version -ne 3 -or $required.generation -lt 1 -or $required.generation -ge $Generation){throw 'Unsafe canonical exact-payload reference'}
    $base=Join-Path $campaign ($Project+'\retained-native-v'+$required.generation)
    if((Resolve-Path -LiteralPath $base).ProviderPath -ne $base -or ((Get-Item -LiteralPath $base -Force).Attributes -band [IO.FileAttributes]::ReparsePoint)){throw 'Linked canonical reference root'}
    if((Get-FileHash -LiteralPath (Join-Path $base 'index.json') -Algorithm SHA256).Hash.ToLowerInvariant() -ne $required.index_sha256){throw 'Canonical reference index changed'}
    $baseIndex=Get-Content -LiteralPath (Join-Path $base 'index.json') -Raw | ConvertFrom-Json
    $baseArchive='packets.tar.gz';if($baseIndex.compression -eq 'tar.xz'){$baseArchive='packets.tar.xz'}
    if((Get-FileHash -LiteralPath (Join-Path $base $baseArchive) -Algorithm SHA256).Hash.ToLowerInvariant() -ne $required.archive_sha256){throw 'Canonical reference archive changed'}
    $fullReadback=Get-Content -LiteralPath (Join-Path $retained 'complete-readback.json') -Raw | ConvertFrom-Json
    if($fullReadback.index_sha256 -ne $verified.index_sha256 -or $fullReadback.members_compared_byte_exact -ne $verified.members_verified){throw 'Complete exact-reference readback missing'}
    foreach($property in $index.external_exact_payloads.PSObject.Properties){
        if($logicalFiles.ContainsKey($property.Name)){throw 'Overlapping external/current logical payload'}
        $logicalFiles[$property.Name]=$property.Value
    }
}
foreach($run in $index.runs) {
    if ($run -notmatch '^[0-9]{1,20}$') { throw 'Invalid native run' }
    $expectedRoot=Join-Path $campaign ('native\'+$run)
    $target=(Resolve-Path -LiteralPath $expectedRoot).ProviderPath
    if ($target -ne $expectedRoot -or -not $target.StartsWith($campaign+'\',[StringComparison]::OrdinalIgnoreCase)) { throw 'Removal escapes exact campaign root' }
    $targets+=$target;$pending=[Collections.Generic.Queue[string]]::new();$pending.Enqueue($target)
    while($pending.Count) {
        $directory=$pending.Dequeue()
        if ((Get-Item -LiteralPath $directory -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Linked native removal directory' }
        foreach($entry in Get-ChildItem -LiteralPath $directory -Force) {
            if ($entry.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Unreviewed native packet link' }
            if ($entry.PSIsContainer) { $pending.Enqueue($entry.FullName);continue }
            if ($actual.Count -ge 40000) { throw 'Packet count bound' }
            $relative=$entry.FullName.Substring($campaign.Length+1).Replace('\','/')
            $expected=$logicalFiles[$relative]
            if ($null -eq $expected -or $entry.Length -ne $expected.bytes -or
                (Get-FileHash -LiteralPath $entry.FullName -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expected.sha256) { throw 'Expanded packet differs from retained bytes' }
            $actual[$relative]=$true
        }
    }
}
if ($actual.Count -ne $verified.members_verified -or $actual.Count -ne $logicalFiles.Count) { throw 'Incomplete expanded packet inventory' }
foreach($target in $targets) {
    Remove-Item -LiteralPath $target -Recurse -Force
    if(Test-Path -LiteralPath $target){throw 'Expanded native packet remains'}
}
@{removed_runs=$index.runs;index_sha256=$verified.index_sha256;archive_sha256=$index.archive_sha256;all_expanded_removed=$true} |
    ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $retained 'expanded-removed.json') -Encoding UTF8
Write-Output 'Removed only exact new-campaign native packets after complete archive/inventory verification.'
