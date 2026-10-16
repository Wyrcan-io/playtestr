param()
$ErrorActionPreference = 'Stop'
$workspace = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..')).TrimEnd('\')
$campaign = Join-Path $workspace 'artifacts\runner-readiness-ten-project-pass'
$active = [IO.Path]::GetFullPath((Join-Path $campaign 'active\plop'))
$retained = Join-Path $campaign 'plop\retained-source'
if ($active -ne (Join-Path $campaign 'active\plop') -or
    -not $active.StartsWith($workspace + '\', [StringComparison]::OrdinalIgnoreCase)) {
    throw 'Removal target is outside the exact owned project root'
}
$marker = Get-Content -LiteralPath (Join-Path $active 'task-owned.json') -Raw | ConvertFrom-Json
if ($marker.workspace -ne $workspace -or $marker.project -ne 'plopjs/plop' -or
    $marker.campaign -ne 'runner-readiness-ten-project-pass' -or
    $marker.pin -ne '0c90e7ef93ffa5f40b10fe8f53d3cc23adee5a8e') { throw 'Ownership mismatch' }
$prepared = Get-Content -LiteralPath (Join-Path $retained 'removal-prepared.json') -Raw | ConvertFrom-Json
$index = Get-Content -LiteralPath (Join-Path $retained 'verified-index.json') -Raw | ConvertFrom-Json
if (-not $prepared.source_archive_verified -or -not $prepared.managed_cleanup_verified -or
    -not $prepared.node_processes_verified -or $prepared.owned_relative_path -ne 'active/plop') {
    throw 'Archive/restore/cleanup preparation is incomplete'
}
$archive = Join-Path $retained 'source.tar.gz'
if ((Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash.ToLowerInvariant() -ne $index.archive_sha256) {
    throw 'Retained archive identity changed'
}
$nodes = @(Get-CimInstance Win32_Process -Filter "Name='node.exe'" | Where-Object {
    $_.CommandLine -and ($_.CommandLine.IndexOf($active, [StringComparison]::OrdinalIgnoreCase) -ge 0 -or
    $_.CommandLine.IndexOf($active.Replace('\','/'), [StringComparison]::OrdinalIgnoreCase) -ge 0)
})
if ($nodes.Count -ne 0) { throw 'Owned Node process remains; do not remove live state' }
if ((Get-Item -LiteralPath $active -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) {
    throw 'Active root is a reparse point'
}
$queue = New-Object 'System.Collections.Generic.Queue[string]'
$queue.Enqueue($active)
$links = @()
$entries = 0
while ($queue.Count -gt 0) {
    foreach ($item in Get-ChildItem -LiteralPath $queue.Dequeue() -Force) {
        $entries++
        if ($entries -gt 100000) { throw 'Owned inventory bound exceeded' }
        if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) {
            $relative = $item.FullName.Substring($active.Length + 1).Replace('\','/')
            if ($prepared.owned_links -notcontains $relative) { throw 'Unreviewed reparse point' }
            $links += $item
        } elseif ($item.PSIsContainer) { $queue.Enqueue($item.FullName) }
    }
}
if ($links.Count -ne @($prepared.owned_links).Count) { throw 'Prepared link inventory changed' }
# Remove the reviewed link itself through the native API, without traversal.
foreach ($item in $links) {
    if ($item.PSIsContainer) { [IO.Directory]::Delete($item.FullName, $false) }
    else { [IO.File]::Delete($item.FullName) }
}
Remove-Item -LiteralPath $active -Recurse -Force
if (Test-Path -LiteralPath $active) { throw 'Owned project removal failed' }
$receipt = Join-Path $retained 'removed.json'
if (Test-Path -LiteralPath $receipt) { throw 'Removal receipt already exists' }
[ordered]@{ removed=$true; owned_relative_path='active/plop';
    source_archive_sha256=$index.archive_sha256; entries=$entries;
    reviewed_links_removed=$links.Count; checked_at_utc=[DateTime]::UtcNow.ToString('o') } |
    ConvertTo-Json | Set-Content -LiteralPath $receipt -Encoding UTF8
Write-Output 'Removed only the checked owned Plop tree; retained archive and restore evidence preserved.'
