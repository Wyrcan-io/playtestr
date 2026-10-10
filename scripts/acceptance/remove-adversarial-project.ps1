param([Parameter(Mandatory=$true)][string]$Project)
$ErrorActionPreference='Stop'
if ($Project -notmatch '^[a-z0-9-]+$') { throw 'Invalid owned application name' }
$workspace=(Resolve-Path -LiteralPath '.').Path
$root=(Resolve-Path -LiteralPath '.cache/ten-new-project-apps').Path
$target=(Resolve-Path -LiteralPath (Join-Path $root $Project)).Path
if ($target -ne (Join-Path $root $Project) -or -not $target.StartsWith($root+[IO.Path]::DirectorySeparatorChar)) { throw 'Unsafe deletion target' }
$owner=Get-Content -LiteralPath (Join-Path $target 'task-owned.json') -Raw -Encoding UTF8 | ConvertFrom-Json
if ($owner.campaign -ne 'ten-new-project-adversarial-pass' -or $owner.workspace -ne $workspace -or $owner.project -ne $Project) { throw 'Unknown target ownership' }
$qualification=Get-Content -LiteralPath 'artifacts/ten-new-project-adversarial-pass/native-cookiecutter-Windows.json' -Raw -Encoding UTF8 | ConvertFrom-Json
if ($qualification.project -ne $Project -or $qualification.terminal_repetitions -ne 100) { throw 'Native evidence incomplete' }
$live=Get-CimInstance Win32_Process | Where-Object { $_.ProcessId -ne $PID -and $_.CommandLine -and $_.CommandLine.Contains($target) }
if ($live) { throw 'Task-owned application still has live references' }
$links=Get-ChildItem -LiteralPath $target -Recurse -Force -Attributes ReparsePoint
if ($links) {
    Add-Type @'
using System;
using System.Runtime.InteropServices;
public static class PlaytestrAdversarialLinks {
 [DllImport("kernel32.dll", CharSet=CharSet.Unicode, SetLastError=true)]
 public static extern bool RemoveDirectory(string path);
 [DllImport("kernel32.dll", CharSet=CharSet.Unicode, SetLastError=true)]
 public static extern bool DeleteFile(string path);
}
'@
    foreach ($link in $links) {
        if (-not $link.FullName.StartsWith($target+[IO.Path]::DirectorySeparatorChar)) { throw 'Unsafe link path' }
        $metadata=fsutil reparsepoint query $link.FullName
        if ($LASTEXITCODE -ne 0 -or -not ($metadata -match '0xa000000c|0xa000001d')) { throw 'Unknown reparse tag; refuse deletion' }
        # Nonrecursive native unlink never follows the target of an owned link.
        if ($link.PSIsContainer) { $removed=[PlaytestrAdversarialLinks]::RemoveDirectory($link.FullName) }
        else { $removed=[PlaytestrAdversarialLinks]::DeleteFile($link.FullName) }
        if (-not $removed) { throw ('Owned link unlink failed: '+$link.FullName) }
    }
}
Remove-Item -LiteralPath $target -Recurse -Force
if (Test-Path -LiteralPath $target) { throw 'Owned application deletion failed' }
@{ project=$Project; removed=$true; canonical_target=$target; process_check='no owned references'; native_host='Windows'; source=$qualification.source } | ConvertTo-Json | Set-Content -LiteralPath 'artifacts/ten-new-project-adversarial-pass/cleanup-Windows.json' -Encoding UTF8
Write-Output 'Owned application removed after native evidence and process checks'
