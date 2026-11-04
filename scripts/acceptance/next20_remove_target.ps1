param([Parameter(Mandatory=$true)][ValidatePattern('^[a-z][a-z0-9-]{0,63}$')][string]$Project,
    [ValidateSet('rebuild-v1')][string]$Window,
    [ValidateSet(40000,60000)][int]$MaxFiles=40000,
    [ValidateSet(1073741824,2147483648)][long]$MaxBytes=1073741824,[switch]$Staged)
$ErrorActionPreference='Stop'
$workspace=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$campaign=Join-Path $workspace 'artifacts\runner-readiness-next-twenty-project-pass'
$target=(Resolve-Path -LiteralPath (Join-Path $campaign ('active\'+$Project))).ProviderPath
$expected=Join-Path $campaign ('active\'+$Project)
if ($target -ne $expected -or -not $target.StartsWith($campaign+'\active\',[StringComparison]::OrdinalIgnoreCase)) { throw 'Target removal escapes exact owned root' }
foreach($path in @((Join-Path $workspace 'artifacts'),$campaign,(Join-Path $campaign 'active'),$target)) {
    if ((Get-Item -LiteralPath $path -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Linked target removal ancestor' }
}
$retainedName='retained-source'
if ($Window) {$retainedName+='-'+$Window}
$retained=Join-Path $campaign ($Project+'\'+$retainedName)
$inventoryRoot=if($Staged){Join-Path $campaign 'tmp\cargo-window3-cleanup'}else{$retained}
if($Staged -and ((Resolve-Path -LiteralPath $inventoryRoot).ProviderPath -ne $inventoryRoot -or
    ((Get-Item -LiteralPath $inventoryRoot -Force).Attributes -band [IO.FileAttributes]::ReparsePoint))) {throw 'Unsafe staged target inventory root'}
$prepared=Get-Content -LiteralPath (Join-Path $retained 'prepared.json') -Raw | ConvertFrom-Json
$indexPath=Join-Path $inventoryRoot 'cleanup-inventory.json'
if ((Get-FileHash -LiteralPath $indexPath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $prepared.cleanup_inventory_sha256) { throw 'Target cleanup inventory changed' }
$index=Get-Content -LiteralPath $indexPath -Raw | ConvertFrom-Json
$declaredMaxFiles=40000
if ($null -ne $index.PSObject.Properties['max_files']) {$declaredMaxFiles=[int]$index.max_files}
if ($declaredMaxFiles -ne $MaxFiles) {throw 'Target cleanup bound differs from prepared inventory'}
$declaredMaxBytes=1073741824
if ($null -ne $index.PSObject.Properties['max_bytes']) {$declaredMaxBytes=[long]$index.max_bytes}
if ($declaredMaxBytes -ne $MaxBytes) {throw 'Target cleanup byte bound differs from prepared inventory'}
if ($index.owned_target -ne $target -or -not $index.source_restored_exact) { throw 'Target ownership/restoration mismatch' }
$ownerPath=Join-Path $target 'task-owned.json'
if ((Get-FileHash -LiteralPath $ownerPath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $index.owner_sha256) { throw 'Target ownership marker changed' }
$actual=@{};$actualLinks=@{};$totalBytes=[long]0;$pending=[Collections.Generic.Queue[string]]::new();$pending.Enqueue($target)
while($pending.Count) {
    foreach($entry in Get-ChildItem -LiteralPath $pending.Dequeue() -Force) {
        if ($entry.Attributes -band [IO.FileAttributes]::ReparsePoint) {
            $relative=$entry.FullName.Substring($target.Length+1).Replace('\','/')
            $link=$index.owned_links.PSObject.Properties[$relative]
            if($null -eq $link){throw 'Unknown target link/reparse point'}
            $resolved=(Resolve-Path -LiteralPath $entry.FullName).ProviderPath
            $expectedLink=Join-Path $target ([string]$link.Value)
            $query=@(& (Join-Path $env:SystemRoot 'System32\fsutil.exe') reparsepoint query $entry.FullName 2>&1)
            if($LASTEXITCODE -ne 0 -or $query.Count -gt 80){throw 'Could not inspect owned target junction'}
            $targetLines=@($query | ForEach-Object {if([string]$_ -match '^Print Name:\s+(.+)$'){$Matches[1].Trim()}} | Where-Object {$_})
            if($resolved -ne $entry.FullName -or $targetLines.Count -ne 1 -or
                -not $targetLines[0].Equals($expectedLink,[StringComparison]::OrdinalIgnoreCase) -or
                -not $expectedLink.StartsWith($target+'\',[StringComparison]::OrdinalIgnoreCase) -or
                -not (Test-Path -LiteralPath $expectedLink -PathType Container)){throw 'Owned target junction escaped its exact target root'}
            $actualLinks[$relative]=[string]$link.Value
            continue
        }
        if ($entry.PSIsContainer) {$pending.Enqueue($entry.FullName);continue}
        if ($actual.Count -ge $MaxFiles) { throw 'Target cleanup file bound' }
        $totalBytes+=$entry.Length
        if ($totalBytes -gt $MaxBytes -or $entry.Length -gt 134217728) {throw 'Target cleanup byte bound'}
        $relative=$entry.FullName.Substring($target.Length+1).Replace('\','/')
        $record=$index.files.PSObject.Properties[$relative].Value
        if ($null -eq $record -or $entry.Length -ne $record.bytes -or
            (Get-FileHash -LiteralPath $entry.FullName -Algorithm SHA256).Hash.ToLowerInvariant() -ne $record.sha256) { throw 'Target payload changed after checked retention' }
        $actual[$relative]=$true
    }
}
if ($actual.Count -ne @($index.files.PSObject.Properties).Count -or $actualLinks.Count -ne @($index.owned_links.PSObject.Properties).Count) { throw 'Target cleanup coverage/link mismatch' }
foreach($candidate in Get-CimInstance Win32_Process) {
    $ownedExecutable=$candidate.ExecutablePath -and $candidate.ExecutablePath.StartsWith($target+'\',[StringComparison]::OrdinalIgnoreCase)
    $ownedArguments=$candidate.CommandLine -and $candidate.CommandLine.IndexOf($target,[StringComparison]::OrdinalIgnoreCase) -ge 0
    if (-not ($ownedExecutable -or $ownedArguments)) {continue}
    $current=Get-CimInstance Win32_Process -Filter ('ProcessId='+$candidate.ProcessId)
    if ($null -ne $current -and $current.CreationDate -eq $candidate.CreationDate) {throw 'Owned target PID/birth remains before removal'}
}
foreach($relative in $actualLinks.Keys) {
    $linkPath=Join-Path $target ($relative.Replace('/','\'));$resolvedBefore=Join-Path $target ([string]$actualLinks[$relative])
    Remove-Item -LiteralPath $linkPath -Force
    if(Test-Path -LiteralPath $linkPath){throw 'Owned target junction remains'}
    if(-not (Test-Path -LiteralPath $resolvedBefore -PathType Container) -or (Resolve-Path -LiteralPath $resolvedBefore).ProviderPath -ne $resolvedBefore){throw 'Owned junction removal changed or lost its in-root target'}
}
Remove-Item -LiteralPath $target -Recurse -Force
if (Test-Path -LiteralPath $target) {throw 'Target remains after native removal'}
@{schema_version=1;removed=$true;owned_relative_path=('active/'+$Project);source_restored_exact=$true;
    cleanup_inventory_sha256=$prepared.cleanup_inventory_sha256;removed_owned_junctions=@($actualLinks.Keys);checked_at_utc=[DateTime]::UtcNow.ToString('o')} |
    ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $retained 'removed.json') -Encoding UTF8
Write-Output 'Native Windows checked removal: exact owned target source/runtime absent; retained provenance preserved.'
