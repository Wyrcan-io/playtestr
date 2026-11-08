$ErrorActionPreference = 'Stop'
$workspace = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$raw = [IO.Path]::GetFullPath((Join-Path $workspace 'artifacts\runner-readiness-next-twenty-project-pass'))
$stage = [IO.Path]::GetFullPath((Join-Path $workspace '.runner-readiness-compaction-tmp\control-duplicates-v1'))
$sourceRoot = [IO.Path]::GetFullPath((Join-Path $raw 'control-tests'))
$indexPath = Join-Path $stage 'index.json'
$planPath = Join-Path $stage 'removal-plan.json'
$preparedPath = Join-Path $stage 'prepared.json'
$archivePath = Join-Path $stage 'payload.tar.xz'
$helperPath = Join-Path $PSScriptRoot 'next20_control_duplicate_remove.ps1'

foreach ($path in @($workspace, $raw, $sourceRoot, $stage)) {
    $item = Get-Item -LiteralPath $path -Force
    if (-not $item.PSIsContainer -or ($item.Attributes -band [IO.FileAttributes]::ReparsePoint)) {
        throw "Unexpected or linked compaction root: $path"
    }
    if ([IO.Path]::GetFullPath($item.FullName) -ne $path) { throw "Root resolution differs: $path" }
}
$plan = Get-Content -LiteralPath $planPath -Raw | ConvertFrom-Json
$indexHash = (Get-FileHash -LiteralPath $indexPath -Algorithm SHA256).Hash.ToLowerInvariant()
$archiveHash = (Get-FileHash -LiteralPath $archivePath -Algorithm SHA256).Hash.ToLowerInvariant()
$preparedHash = (Get-FileHash -LiteralPath $preparedPath -Algorithm SHA256).Hash.ToLowerInvariant()
$helperHash = (Get-FileHash -LiteralPath $helperPath -Algorithm SHA256).Hash.ToLowerInvariant()
if ($plan.schema_version -ne 1 -or $plan.index_sha256 -ne $indexHash -or
    $plan.archive_sha256 -ne $archiveHash -or $plan.prepared_sha256 -ne $preparedHash -or
    $plan.removal_helper_sha256 -ne $helperHash -or $plan.alias_path_count -le 0 -or
    $plan.alias_path_count -gt 10000 -or $plan.expanded_alias_bytes -gt 96MB) {
    throw 'Compaction removal plan or helper binding differs.'
}
$index = Get-Content -LiteralPath $indexPath -Raw | ConvertFrom-Json
$prepared = Get-Content -LiteralPath $preparedPath -Raw | ConvertFrom-Json
if ($index.schema_version -ne 1 -or $prepared.index_sha256 -ne $indexHash -or
    $prepared.archive_sha256 -ne $archiveHash -or $prepared.source_removal_confirmed -ne $false -or
    $prepared.alias_paths -ne $plan.alias_path_count -or $prepared.compactor_sha256 -ne $plan.compactor_sha256) {
    throw 'Prepared evidence packet does not match the checked removal plan.'
}

$candidates = [Collections.Generic.List[object]]::new()
foreach ($group in $index.groups) {
    if ($group.paths.Count -lt 2 -or $group.bytes -le 0 -or $group.sha256 -notmatch '^[0-9a-f]{64}$') {
        throw 'Invalid duplicate group in the checked evidence index.'
    }
    foreach ($row in $group.paths) {
        if ($row.sha256 -ne $group.sha256 -or $row.bytes -ne $group.bytes -or
            $row.path -notlike 'control-tests/*' -or $row.path.Contains('\') -or
            ($row.path -split '/').Where({ $_ -in @('', '.', '..') }).Count -gt 0) {
            throw 'Invalid source alias in the checked evidence index.'
        }
        $relative = $row.path.Replace('/', [IO.Path]::DirectorySeparatorChar)
        $path = [IO.Path]::GetFullPath((Join-Path $raw $relative))
        if (-not $path.StartsWith($sourceRoot + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
            throw "Source path escapes the owned control-test root: $($row.path)"
        }
        $item = Get-Item -LiteralPath $path -Force
        if ($item.PSIsContainer -or ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -or
            $item.Length -ne $row.bytes -or (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant() -ne $row.sha256) {
            throw "Source bytes or file type differ before removal: $($row.path)"
        }
        $parent = Split-Path -Parent $path
        while ($parent.StartsWith($sourceRoot + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
            $directory = Get-Item -LiteralPath $parent -Force
            if (-not $directory.PSIsContainer -or ($directory.Attributes -band [IO.FileAttributes]::ReparsePoint)) {
                throw "Linked or unexpected source ancestor: $parent"
            }
            $parent = Split-Path -Parent $parent
        }
        $candidates.Add([pscustomobject]@{ Path = $path; Relative = $row.path; Hash = $row.sha256; Bytes = $row.bytes })
    }
}
if ($candidates.Count -ne $plan.alias_path_count -or
    (@($candidates.Relative | Sort-Object -Unique).Count -ne $candidates.Count)) {
    throw 'Checked source alias count or uniqueness differs.'
}

# All indexed sources pass identity, path, type, and ownership checks before any unlink.
foreach ($candidate in $candidates) {
    Remove-Item -LiteralPath $candidate.Path -Force
    if (Test-Path -LiteralPath $candidate.Path) { throw "Checked source alias remains: $($candidate.Relative)" }
}
Write-Output "Removed $($candidates.Count) byte-verified duplicate control aliases ($($plan.expanded_alias_bytes) source bytes); unique payload remains in the checked packet."
