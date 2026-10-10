$ErrorActionPreference='Stop'
$workspace=(Resolve-Path -LiteralPath '.').Path
$ledger=Get-Content -LiteralPath 'docs/validation/ten-project-user-pass/ledger.json' -Raw -Encoding UTF8 | ConvertFrom-Json
if ($ledger.status -ne 'completed_early_p5_reliability' -or $ledger.projects.Count -ne 10 -or @($ledger.projects | Where-Object { -not $_.deleted }).Count) { throw 'Incomplete application evidence/cleanup' }
$linuxWorkspace='/mnt/c/'+$workspace.Substring(3).Replace('\','/')
$audit=wsl -d Ubuntu -- python3 ($linuxWorkspace+'/scripts/acceptance/user_cleanup_checks.py')
if ($LASTEXITCODE -ne 0) { throw 'Native cleanup audit failed' }
$native=$audit | ConvertFrom-Json
$target=(Resolve-Path -LiteralPath '.tools/ten-project-runtime').Path
$toolsRoot=(Resolve-Path -LiteralPath '.tools').Path
if ($target -ne (Join-Path $toolsRoot 'ten-project-runtime') -or -not $target.StartsWith($workspace+[IO.Path]::DirectorySeparatorChar)) { throw 'Unsafe runtime target' }
if ((Get-Item -LiteralPath $target -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Runtime root is a link' }
$allowed=@('node-v24.7.0-linux-x64','uv-x86_64-unknown-linux-gnu','node-integrity.txt','node-v24.7.0-linux-x64.tar.xz','uv-integrity.json','uv-x86_64-unknown-linux-gnu.tar.gz')
foreach ($entry in Get-ChildItem -LiteralPath $target -Force) { if ($entry.Name -notin $allowed) { throw 'Unknown runtime entry' } }
$integrity=Get-Content -LiteralPath 'docs/validation/ten-project-user-pass/toolchains.json' -Raw -Encoding UTF8 | ConvertFrom-Json
if ((Get-FileHash -LiteralPath (Join-Path $target 'node-v24.7.0-linux-x64.tar.xz') -Algorithm SHA256).Hash.ToLowerInvariant() -ne $integrity.node.sha256) { throw 'Node ownership/integrity mismatch' }
if ((Get-FileHash -LiteralPath (Join-Path $target 'uv-x86_64-unknown-linux-gnu.tar.gz') -Algorithm SHA256).Hash.ToLowerInvariant() -ne $integrity.uv.sha256) { throw 'uv ownership/integrity mismatch' }
$links=Get-ChildItem -LiteralPath $target -Recurse -Force -Attributes ReparsePoint
if ($links) {
 Add-Type @'
using System;
using System.Runtime.InteropServices;
public static class PlaytestrRuntimeLinks {
 [DllImport("kernel32.dll", CharSet=CharSet.Unicode, SetLastError=true)] public static extern bool RemoveDirectory(string path);
 [DllImport("kernel32.dll", CharSet=CharSet.Unicode, SetLastError=true)] public static extern bool DeleteFile(string path);
}
'@
 foreach ($link in $links) {
  if (-not $link.FullName.StartsWith($target+[IO.Path]::DirectorySeparatorChar)) { throw 'Unsafe link entry' }
  $metadata=fsutil reparsepoint query $link.FullName
  if ($LASTEXITCODE -ne 0 -or -not ($metadata -match '0xa000001d|0xa000000c')) { throw 'Unknown reparse point' }
  if ($link.PSIsContainer) { $removed=[PlaytestrRuntimeLinks]::RemoveDirectory($link.FullName) }
  else { $removed=[PlaytestrRuntimeLinks]::DeleteFile($link.FullName) }
  if (-not $removed) { throw 'Cannot unlink owned prerequisite entry' }
 }
}
Remove-Item -LiteralPath $target -Recurse -Force
if (Test-Path -LiteralPath $target) { throw 'Runtime removal failed' }
$record=@{ verified_date='2026-10-10'; applications_removed=10; native_audit=$native; prerequisite_runtime_removed=$true; removed_prerequisites=@('task-local Node 24.7.0','task-local uv 0.12.23','verified downloaded archives','all per-application native venv/build/cache directories'); preserved=@('Playtestr source and binaries','reports/specs/baselines/synthetic fixtures/licensed patches','pre-existing shared Go module/compiler caches','pre-existing .tools/winlibs compiler','earlier P0-P2 worktrees/evidence'); clean_source_worktree_removed=$false }
$utf8=New-Object System.Text.UTF8Encoding($false)
[IO.File]::WriteAllText((Join-Path $workspace 'docs/validation/ten-project-user-pass/cleanup.json'),($record | ConvertTo-Json -Depth 10)+[Environment]::NewLine,$utf8)
Write-Output 'Removed verified task-only prerequisite runtime; applications, native runtimes and target processes absent.'
