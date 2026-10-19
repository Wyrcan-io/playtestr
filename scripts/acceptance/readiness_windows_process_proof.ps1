param([ValidateSet('plop','poetry','rubygems','edit','vis','fff','papis','frogmouth','hygen','rclone','old-cookiecutter')][string]$Project)
$ErrorActionPreference = 'Stop'
$workspace = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..')).TrimEnd('\')
$campaign = Join-Path $workspace 'artifacts\runner-readiness-ten-project-pass'
$active = [IO.Path]::GetFullPath((Join-Path $campaign ('active\' + $Project)))
if (-not $active.StartsWith($workspace + '\', [StringComparison]::OrdinalIgnoreCase) -or
    (Resolve-Path -LiteralPath $active).ProviderPath -ne $active -or
    ((Get-Item -LiteralPath $active -Force).Attributes -band [IO.FileAttributes]::ReparsePoint)) {
    throw 'Owned active process-check root is redirected or outside checkout'
}
$filter = if ($Project -in @('plop','hygen')) { "Name='node.exe'" } elseif ($Project -eq 'rubygems') {
    "Name='ruby.exe' OR Name='rubyw.exe' OR Name='git.exe' OR Name='less.exe' OR Name='diff.exe'"
} elseif ($Project -eq 'edit') {
    "Name='edit.exe' OR Name='cargo.exe' OR Name='rustc.exe' OR Name='rustdoc.exe' OR Name='link.exe' OR Name='rc.exe' OR Name='cl.exe'"
} elseif ($Project -eq 'rclone') {
    "Name='rclone.exe' OR Name='go.exe' OR Name='compile.exe' OR Name='link.exe' OR Name='asm.exe' OR Name='cgo.exe'"
} elseif ($Project -eq 'vis') {
    "Name='vis.exe' OR Name='gcc.exe' OR Name='clang.exe' OR Name='cc1.exe' OR Name='make.exe' OR Name='ld.exe'"
} elseif ($Project -eq 'fff') { "Name='bash.exe' OR Name='sh.exe' OR Name='cp.exe' OR Name='mv.exe' OR Name='rm.exe' OR Name='mkdir.exe'" } else { "Name='python.exe' OR Name='pythonw.exe' OR Name='poetry.exe' OR Name='papis.exe' OR Name='frogmouth.exe' OR Name='pip.exe'" }
if ($Project -eq 'old-cookiecutter') { $filter += " OR Name='cookiecutter.exe'" }
$matching = @(Get-CimInstance Win32_Process -Filter $filter | Where-Object {
    $_.CommandLine -and ($_.CommandLine.IndexOf($active, [StringComparison]::OrdinalIgnoreCase) -ge 0 -or
    $_.CommandLine.IndexOf($active.Replace('\','/'), [StringComparison]::OrdinalIgnoreCase) -ge 0)
} | Select-Object -ExpandProperty ProcessId)
if ($matching.Count -ne 0) {
    $unconfirmed = Join-Path $campaign ($Project + '\runtime-unconfirmed-' + [Guid]::NewGuid().ToString('N') + '.json')
    [ordered]@{checked_at_utc=[DateTime]::UtcNow.ToString('o');query_succeeded=$true;
        active_path=$active;matching_runtime_pids=$matching;command_values_persisted=$false;cleanup_confirmed=$false} |
        ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $unconfirmed -Encoding UTF8
    throw 'Owned runtime remains live; preserve the active tree'
}
$proof = [ordered]@{checked_at_utc=[DateTime]::UtcNow.ToString('o');query_succeeded=$true;active_path=$active}
if ($Project -eq 'plop') { $proof.matching_node_pids=@() } else { $proof.matching_runtime_pids=@() }
$destination=Join-Path $campaign ($Project + '\local-process-cleanup.json')
$proof | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $destination -Encoding UTF8
Write-Output 'Fresh owned runtime check passed; no process was killed.'
