param([ValidateSet('plop','poetry','rubygems','edit','vis','fff','papis','frogmouth','hygen','rclone','old-cookiecutter','old-copier','old-lf','old-superfile')][string]$Project = 'plop')
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
$repository = @{plop='plopjs/plop';poetry='python-poetry/poetry';rubygems='ruby/rubygems';edit='microsoft/edit';vis='martanne/vis';fff='dylanaraps/fff';papis='papis/papis';frogmouth='Textualize/frogmouth';hygen='jondot/hygen';rclone='rclone/rclone';'old-cookiecutter'='cookiecutter/cookiecutter';'old-copier'='copier-org/copier';'old-lf'='gokcehan/lf';'old-superfile'='yorukot/superfile'}[$Project]
$pin = @{plop='0c90e7ef93ffa5f40b10fe8f53d3cc23adee5a8e';poetry='38a86661d2ae58694c76d0bb4e628e1400d6dc6f';rubygems='f033df93676007227d1ae0bd7326008e6396b3e9';edit='cb6de0a8966aecd01d19a3541dab1829d0e679ca';vis='10b630af09404cf2c887e2d7e6e24ecda9d05ea7';fff='6f2dc6f3a003d24e8b3fd48b046241b486022ad5';papis='c744b5efe9b307b9664f3e96c154cb620e140a8f';frogmouth='15c3e85a6e84b2e4a6845723acf12beb54c81eb2';hygen='26f76d8dede565b2bf38d0b9e9f3009ee2c8f9ae';rclone='d369079a1448c487d09d85bfe11382e16ea4e345';'old-cookiecutter'='c88fbe921c97c58b65f1883ba90a0ab53cc91b34';'old-copier'='04a8619f3b083bc278b70e556bd085551a2b3f79';'old-lf'='5d3c7b702515dfb72d8d496673fa1c4144d1dbed';'old-superfile'='66fe169b87021f7424522ed5aadd711c5676601e'}[$Project]
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
$filter = if ($Project -in @('plop','hygen')) { "Name='node.exe'" } elseif ($Project -eq 'rubygems') { "Name='ruby.exe' OR Name='rubyw.exe' OR Name='git.exe' OR Name='less.exe' OR Name='diff.exe'" } elseif ($Project -eq 'edit') { "Name='edit.exe' OR Name='cargo.exe' OR Name='rustc.exe' OR Name='rustdoc.exe' OR Name='link.exe' OR Name='rc.exe' OR Name='cl.exe'" } elseif ($Project -eq 'vis') { "Name='vis.exe' OR Name='gcc.exe' OR Name='clang.exe' OR Name='cc1.exe' OR Name='make.exe' OR Name='ld.exe'" } elseif ($Project -eq 'fff') { "Name='bash.exe' OR Name='sh.exe' OR Name='cp.exe' OR Name='mv.exe' OR Name='rm.exe' OR Name='mkdir.exe'" } else { "Name='python.exe' OR Name='pythonw.exe' OR Name='poetry.exe' OR Name='papis.exe' OR Name='frogmouth.exe' OR Name='pip.exe'" }
if ($Project -in @('rclone','old-lf','old-superfile')) {
    $filter = "Name='rclone.exe' OR Name='lf.exe' OR Name='superfile.exe' OR Name='go.exe' OR Name='compile.exe' OR Name='link.exe' OR Name='asm.exe' OR Name='cgo.exe'"
}
if ($Project -eq 'old-cookiecutter') { $filter += " OR Name='cookiecutter.exe'" }
if ($Project -eq 'old-copier') { $filter += " OR Name='copier.exe' OR Name='git.exe' OR Name='less.exe' OR Name='diff.exe'" }
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
