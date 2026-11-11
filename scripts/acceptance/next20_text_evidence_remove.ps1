param(
    [string]$PlanPath = 'artifacts/runner-readiness-next-twenty-project-pass/text-evidence-v1/removal-plan.json'
)
$ErrorActionPreference = 'Stop'
$rawRoot = (Resolve-Path -LiteralPath 'artifacts/runner-readiness-next-twenty-project-pass').Path
$packet = Join-Path $rawRoot 'text-evidence-v1'
$planFull = [IO.Path]::GetFullPath((Join-Path (Get-Location).Path $PlanPath))
$rootPrefix = [IO.Path]::GetFullPath($rawRoot) + [IO.Path]::DirectorySeparatorChar
if (-not $planFull.StartsWith([IO.Path]::GetFullPath($packet) + [IO.Path]::DirectorySeparatorChar,
        [StringComparison]::OrdinalIgnoreCase)) { throw 'removal plan escapes the owned packet' }
$packetItem = Get-Item -LiteralPath $packet -Force
if (($packetItem.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { throw 'packet root is linked' }
$plan = Get-Content -LiteralPath $planFull -Raw | ConvertFrom-Json
$prepared = Get-Content -LiteralPath (Join-Path $packet 'prepared.json') -Raw | ConvertFrom-Json
$indexPath = Join-Path $packet 'index.json.xz'
$archivePath = Join-Path $packet 'payload.tar.xz'
$indexHash = (Get-FileHash -LiteralPath $indexPath -Algorithm SHA256).Hash.ToLowerInvariant()
$archiveHash = (Get-FileHash -LiteralPath $archivePath -Algorithm SHA256).Hash.ToLowerInvariant()
if ($plan.schema_version -ne 1 -or $plan.compressed_index_sha256 -ne $indexHash -or
    $prepared.index_sha256 -ne $indexHash -or $plan.archive_sha256 -ne $archiveHash -or
    $prepared.archive_sha256 -ne $archiveHash) { throw 'packet, prepared receipt, and removal plan identities differ' }
$rows = @($plan.files.PSObject.Properties)
if ($rows.Count -ne $plan.members -or $rows.Count -gt 50000 -or
    $plan.expanded_bytes -gt 536870912) { throw 'removal inventory exceeds recorded bounds' }
[long]$bytes = 0
$directories = [Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
foreach ($property in $rows) {
    $relative = [string]$property.Name
    if (-not $relative -or $relative.Contains('\') -or $relative.Contains(':') -or
        @($relative.Split('/')) -contains '..' -or @($relative.Split('/')) -contains '.') {
        throw "unsafe relative path: $relative"
    }
    $path = [IO.Path]::GetFullPath((Join-Path $rawRoot ($relative -replace '/', [string][IO.Path]::DirectorySeparatorChar)))
    if (-not $path.StartsWith($rootPrefix, [StringComparison]::OrdinalIgnoreCase)) { throw "path escapes raw root: $relative" }
    $ancestor = Split-Path -Parent $path
    while ($ancestor -and $ancestor.StartsWith($rootPrefix, [StringComparison]::OrdinalIgnoreCase)) {
        if ($directories.Add($ancestor)) {
            $directoryItem = Get-Item -LiteralPath $ancestor -Force
            if (-not $directoryItem.PSIsContainer -or
                ($directoryItem.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
                throw "unsafe linked or non-directory ancestor: $ancestor"
            }
        }
        $ancestor = Split-Path -Parent $ancestor
    }
    $item = Get-Item -LiteralPath $path -Force
    if ($item.PSIsContainer -or ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0 -or
        $item.Length -ne $property.Value.bytes) { throw "candidate type, link, or size differs: $relative" }
    $digest = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($digest -ne $property.Value.sha256) { throw "candidate hash differs: $relative" }
    $bytes += [long]$property.Value.bytes
}
if ($bytes -ne $plan.expanded_bytes) { throw 'verified source bytes differ from removal plan' }
foreach ($property in $rows) {
    $relative = [string]$property.Name
    $path = [IO.Path]::GetFullPath((Join-Path $rawRoot ($relative -replace '/', [string][IO.Path]::DirectorySeparatorChar)))
    $digest = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($digest -ne $property.Value.sha256) { throw "candidate changed after full preflight: $relative" }
    Remove-Item -LiteralPath $path -Force
    if (Test-Path -LiteralPath $path) { throw "candidate remains after removal: $relative" }
}
Write-Output "Removed only indexed text evidence: $($rows.Count) files, $bytes bytes; all paths absent."
