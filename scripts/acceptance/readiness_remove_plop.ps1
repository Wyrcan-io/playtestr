param([ValidateSet('plop','poetry','rubygems')][string]$Project = 'plop')
$ErrorActionPreference = 'Stop'
$workspace = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..')).TrimEnd('\')
$campaign = Join-Path $workspace 'artifacts\runner-readiness-ten-project-pass'
$relative = 'active\' + $Project
$active = [IO.Path]::GetFullPath((Join-Path $campaign $relative))
$retained = Join-Path $campaign ($Project + '\retained-source')
if ($active -ne (Join-Path $campaign $relative) -or
    -not $active.StartsWith($workspace + '\', [StringComparison]::OrdinalIgnoreCase)) {
    throw 'Removal target is outside the exact owned project root'
}
foreach ($ancestor in @((Join-Path $workspace 'artifacts'), $campaign, (Join-Path $campaign 'active'))) {
    $resolved = (Resolve-Path -LiteralPath $ancestor).ProviderPath
    if (-not $resolved.StartsWith($workspace + '\', [StringComparison]::OrdinalIgnoreCase) -or
        ((Get-Item -LiteralPath $ancestor -Force).Attributes -band [IO.FileAttributes]::ReparsePoint)) {
        throw 'Owned removal ancestor redirects or escapes the workspace'
    }
}
$marker = Get-Content -LiteralPath (Join-Path $active 'task-owned.json') -Raw | ConvertFrom-Json
$repository = @{plop='plopjs/plop';poetry='python-poetry/poetry';rubygems='ruby/rubygems'}[$Project]
$pin = @{plop='0c90e7ef93ffa5f40b10fe8f53d3cc23adee5a8e';poetry='38a86661d2ae58694c76d0bb4e628e1400d6dc6f';rubygems='f033df93676007227d1ae0bd7326008e6396b3e9'}[$Project]
if ($marker.workspace -ne $workspace -or $marker.project -ne $repository -or
    $marker.campaign -ne 'runner-readiness-ten-project-pass' -or
    $marker.pin -ne $pin) { throw 'Ownership mismatch' }
$prepared = Get-Content -LiteralPath (Join-Path $retained 'removal-prepared.json') -Raw | ConvertFrom-Json
$index = Get-Content -LiteralPath (Join-Path $retained 'verified-index.json') -Raw | ConvertFrom-Json
if (-not $prepared.source_archive_verified -or -not $prepared.managed_cleanup_verified -or
    -not ($prepared.runtime_processes_verified -or ($Project -eq 'plop' -and $prepared.node_processes_verified)) -or
    $prepared.owned_relative_path -ne ('active/' + $Project)) {
    throw 'Archive/restore/cleanup preparation is incomplete'
}
$archive = Join-Path $retained 'source.tar.gz'
if ((Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash.ToLowerInvariant() -ne $index.archive_sha256) {
    throw 'Retained archive identity changed'
}
$filter = if ($Project -eq 'plop') { "Name='node.exe'" } elseif ($Project -eq 'rubygems') { "Name='ruby.exe' OR Name='rubyw.exe' OR Name='git.exe' OR Name='less.exe' OR Name='diff.exe'" } else { "Name='python.exe' OR Name='pythonw.exe' OR Name='poetry.exe'" }
$nodes = @(Get-CimInstance Win32_Process -Filter $filter | Where-Object {
    $_.CommandLine -and ($_.CommandLine.IndexOf($active, [StringComparison]::OrdinalIgnoreCase) -ge 0 -or
    $_.CommandLine.IndexOf($active.Replace('\','/'), [StringComparison]::OrdinalIgnoreCase) -ge 0)
})
if ($nodes.Count -ne 0) { throw 'Owned runtime process remains; do not remove live state' }
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
[ordered]@{ removed=$true; owned_relative_path=('active/' + $Project);
    source_archive_sha256=$index.archive_sha256; entries=$entries;
    reviewed_links_removed=$links.Count; checked_at_utc=[DateTime]::UtcNow.ToString('o') } |
    ConvertTo-Json | Set-Content -LiteralPath $receipt -Encoding UTF8
Write-Output "Removed only the checked owned $Project tree; retained archive and restore evidence preserved."
