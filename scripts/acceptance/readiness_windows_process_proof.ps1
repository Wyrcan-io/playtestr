param([ValidateSet('plop','poetry','rubygems','edit')][string]$Project)
$ErrorActionPreference = 'Stop'
$workspace = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..')).TrimEnd('\')
$campaign = Join-Path $workspace 'artifacts\runner-readiness-ten-project-pass'
$active = [IO.Path]::GetFullPath((Join-Path $campaign ('active\' + $Project)))
if (-not $active.StartsWith($workspace + '\', [StringComparison]::OrdinalIgnoreCase) -or
    (Resolve-Path -LiteralPath $active).ProviderPath -ne $active -or
    ((Get-Item -LiteralPath $active -Force).Attributes -band [IO.FileAttributes]::ReparsePoint)) {
    throw 'Owned active process-check root is redirected or outside checkout'
}
$filter = if ($Project -eq 'plop') { "Name='node.exe'" } elseif ($Project -eq 'rubygems') {
    "Name='ruby.exe' OR Name='rubyw.exe' OR Name='git.exe' OR Name='less.exe' OR Name='diff.exe'"
} elseif ($Project -eq 'edit') {
    "Name='edit.exe' OR Name='cargo.exe' OR Name='rustc.exe' OR Name='rustdoc.exe' OR Name='link.exe' OR Name='rc.exe' OR Name='cl.exe'"
} else { "Name='python.exe' OR Name='pythonw.exe' OR Name='poetry.exe'" }
$matching = @(Get-CimInstance Win32_Process -Filter $filter | Where-Object {
    $_.CommandLine -and ($_.CommandLine.IndexOf($active, [StringComparison]::OrdinalIgnoreCase) -ge 0 -or
    $_.CommandLine.IndexOf($active.Replace('\','/'), [StringComparison]::OrdinalIgnoreCase) -ge 0)
} | Select-Object -ExpandProperty ProcessId)
if ($matching.Count -ne 0) { throw 'Owned runtime remains live; preserve the active tree' }
$proof = [ordered]@{checked_at_utc=[DateTime]::UtcNow.ToString('o');query_succeeded=$true;active_path=$active}
if ($Project -eq 'plop') { $proof.matching_node_pids=@() } else { $proof.matching_runtime_pids=@() }
$destination=Join-Path $campaign ($Project + '\local-process-cleanup.json')
$proof | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $destination -Encoding UTF8
Write-Output 'Fresh owned runtime check passed; no process was killed.'
