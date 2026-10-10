param([Parameter(Mandatory=$true)][string]$Project,[Parameter(Mandatory=$true)][string]$Application)
$ErrorActionPreference='Stop'
if ($Application -notmatch '^[a-z0-9-]+-[0-9]{2}$' -or $Project -notmatch '^[a-z0-9-]+$') { throw 'Invalid task directory name' }
$workspace=(Resolve-Path -LiteralPath '.').Path
$targetRoot=(Resolve-Path -LiteralPath '.cache/ten-project-apps').Path
$appPath=(Resolve-Path -LiteralPath (Join-Path $targetRoot $Application)).Path
if (-not $appPath.StartsWith($targetRoot+[IO.Path]::DirectorySeparatorChar) -or $appPath -eq $targetRoot) { throw 'Unsafe deletion target' }
$owner=Get-Content -LiteralPath (Join-Path $appPath 'task-owned.json') -Raw -Encoding UTF8 | ConvertFrom-Json
if ($owner.created_by -ne 'ten-project-user-pass' -or $owner.project -ne $Project -or $owner.workspace -ne $workspace) { throw 'Unknown application ownership' }
$resultPath=Join-Path $workspace ('docs/validation/ten-project-user-pass/'+$Project+'/result.json')
$result=Get-Content -LiteralPath $resultPath -Raw -Encoding UTF8 | ConvertFrom-Json
if (-not $result.defect_recovery_contract_hashes_equal) { throw 'Evidence incomplete' }
$linuxScript='/mnt/c/Users/abhir/OneDrive/Documents/playtestr/scripts/acceptance/user_journeys.py'
wsl -d Ubuntu -- python3 $linuxScript check-process $Application
if ($LASTEXITCODE -ne 0) { throw 'Target processes still live or native check failed' }
$links=Get-ChildItem -LiteralPath $appPath -Recurse -Force -Attributes ReparsePoint
if ($links) {
    # WSL creates LX symlinks, which Windows PowerShell cannot classify. Unlink
    # only verified symlink entries with native nonrecursive APIs; never traverse.
    Add-Type @'
using System;
using System.Runtime.InteropServices;
public static class PlaytestrTaskLinks {
 [DllImport("kernel32.dll", CharSet=CharSet.Unicode, SetLastError=true)]
 public static extern bool RemoveDirectory(string path);
 [DllImport("kernel32.dll", CharSet=CharSet.Unicode, SetLastError=true)]
 public static extern bool DeleteFile(string path);
}
'@
    foreach ($link in $links) {
        if (-not $link.FullName.StartsWith($appPath+[IO.Path]::DirectorySeparatorChar)) { throw 'Unsafe link entry' }
        $metadata=fsutil reparsepoint query $link.FullName
        if ($LASTEXITCODE -ne 0 -or -not ($metadata -match '0xa000001d|0xa000000c')) { throw 'Unknown reparse point; refuse deletion' }
        if ($link.PSIsContainer) { $removed=[PlaytestrTaskLinks]::RemoveDirectory($link.FullName) }
        else { $removed=[PlaytestrTaskLinks]::DeleteFile($link.FullName) }
        if (-not $removed) { throw ('Cannot unlink task entry: '+$link.FullName) }
    }
}
Remove-Item -LiteralPath $appPath -Recurse -Force
if (Test-Path -LiteralPath $appPath) { throw 'Application removal failed' }
$result.deleted=$true
$utf8=New-Object System.Text.UTF8Encoding($false)
[IO.File]::WriteAllText($resultPath,($result | ConvertTo-Json -Depth 40)+[Environment]::NewLine,$utf8)
$ledgerPath=Join-Path $workspace 'docs/validation/ten-project-user-pass/ledger.json'
$ledger=Get-Content -LiteralPath $ledgerPath -Raw -Encoding UTF8 | ConvertFrom-Json
$ledger.projects=@($ledger.projects | ForEach-Object { if ($_.project -eq $Project) { $result } else { $_ } })
[IO.File]::WriteAllText($ledgerPath,($ledger | ConvertTo-Json -Depth 40)+[Environment]::NewLine,$utf8)
Write-Output ('Application removed after evidence/process checks: '+$appPath)
