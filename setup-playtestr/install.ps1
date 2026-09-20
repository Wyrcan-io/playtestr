[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string] $Version,

    [string] $InstallRoot = $(if ($env:RUNNER_TEMP) {
        Join-Path $env:RUNNER_TEMP 'playtestr-setup'
    } else {
        Join-Path ([System.IO.Path]::GetTempPath()) 'playtestr-setup'
    }),

    [string] $OutputFile = $env:GITHUB_OUTPUT,
    [string] $PathFile = $env:GITHUB_PATH,

    # Test seams are intentionally not action inputs. Production downloads are
    # fixed to the public GitHub release origin and the current native host.
    [string] $DownloadDirectory,
    [string] $DownloadBaseUrl = 'https://github.com/Wyrcan-io/playtestr/releases/download',
    [string] $TargetOS,
    [string] $TargetArch,
    [ValidateRange(1, 600)]
    [int] $RequestTimeoutSeconds = 120,
    [ValidateRange(1, 5)]
    [int] $DownloadAttempts = 3
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2.0

$archiveLimit = 64MB
$checksumLimit = 4KB
$expandedFileLimit = 128MB
$expectedDocumentNames = @('LICENSE', 'README.md', 'THIRD_PARTY_NOTICES.md')

function Write-EnvironmentLine {
    param([string] $File, [string] $Line)
    if ([string]::IsNullOrWhiteSpace($File)) {
        return
    }
    $encoding = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::AppendAllText($File, $Line + [Environment]::NewLine, $encoding)
}

function Get-NativeTarget {
    param([string] $RequestedOS, [string] $RequestedArch)

    if ([string]::IsNullOrEmpty($RequestedOS)) {
        if ([Environment]::OSVersion.Platform -eq [PlatformID]::Win32NT) {
            $RequestedOS = 'windows'
        } elseif ($IsMacOS) {
            $RequestedOS = 'darwin'
        } elseif ($IsLinux) {
            $RequestedOS = 'linux'
        } else {
            throw "unsupported operating system: $([Environment]::OSVersion.Platform)"
        }
    }
    if ([string]::IsNullOrEmpty($RequestedArch)) {
        $RequestedArch = switch ([System.Runtime.InteropServices.RuntimeInformation]::OSArchitecture.ToString()) {
            'X64' { 'amd64' }
            'Arm64' { 'arm64' }
            default { throw "unsupported architecture: $([System.Runtime.InteropServices.RuntimeInformation]::OSArchitecture)" }
        }
    }

    $supported = @('linux/amd64', 'darwin/arm64', 'windows/amd64')
    $target = "$RequestedOS/$RequestedArch"
    if ($supported -notcontains $target) {
        throw "unsupported Playtestr release target $target; supported targets: $($supported -join ', ')"
    }
    return @{ OS = $RequestedOS; Arch = $RequestedArch }
}

function Copy-BoundedFile {
    param([string] $Source, [string] $Destination, [long] $Limit)
    $sourceInfo = Get-Item -LiteralPath $Source
    if ($sourceInfo.Length -gt $Limit) {
        throw "download exceeds the $Limit byte limit: $Source"
    }
    Copy-Item -LiteralPath $Source -Destination $Destination
}

function Receive-BoundedFile {
    param([uri] $Uri, [string] $Destination, [long] $Limit)

    Add-Type -AssemblyName System.Net.Http
    $lastError = $null
    for ($attempt = 1; $attempt -le $DownloadAttempts; $attempt++) {
        $response = $null
        $inputStream = $null
        $outputStream = $null
        $client = New-Object System.Net.Http.HttpClient
        $client.Timeout = [System.Threading.Timeout]::InfiniteTimeSpan
        $requestCancellation = New-Object System.Threading.CancellationTokenSource
        $requestCancellation.CancelAfter([TimeSpan]::FromSeconds($RequestTimeoutSeconds))
        try {
            $response = $client.GetAsync($Uri, [System.Net.Http.HttpCompletionOption]::ResponseHeadersRead, $requestCancellation.Token).GetAwaiter().GetResult()
            if (-not $response.IsSuccessStatusCode) {
                throw "HTTP $([int]$response.StatusCode) $($response.ReasonPhrase)"
            }
            if ($response.Content.Headers.ContentLength -and $response.Content.Headers.ContentLength -gt $Limit) {
                throw "download exceeds the $Limit byte limit"
            }
            $inputStream = $response.Content.ReadAsStreamAsync().GetAwaiter().GetResult()
            $outputStream = [System.IO.File]::Open($Destination, [System.IO.FileMode]::CreateNew, [System.IO.FileAccess]::Write, [System.IO.FileShare]::None)
            try {
                $buffer = New-Object byte[] 65536
                [long] $written = 0
                while (($read = $inputStream.ReadAsync($buffer, 0, $buffer.Length, $requestCancellation.Token).GetAwaiter().GetResult()) -gt 0) {
                    $written += $read
                    if ($written -gt $Limit) {
                        throw "download exceeds the $Limit byte limit"
                    }
                    $outputStream.Write($buffer, 0, $read)
                }
            } finally {
                if ($outputStream) { $outputStream.Dispose() }
                if ($inputStream) { $inputStream.Dispose() }
            }
            return
        } catch {
            $lastError = $_
            Remove-Item -LiteralPath $Destination -Force -ErrorAction SilentlyContinue
            if ($attempt -lt $DownloadAttempts) {
                Start-Sleep -Milliseconds (200 * $attempt)
            }
        } finally {
            if ($response) { $response.Dispose() }
            $requestCancellation.Dispose()
            $client.Dispose()
        }
    }
    throw "download $Uri failed after $DownloadAttempts attempts: $lastError"
}

function Get-ReleaseFile {
    param([string] $Name, [string] $Destination, [long] $Limit)
    if ($DownloadDirectory) {
        Copy-BoundedFile -Source (Join-Path $DownloadDirectory $Name) -Destination $Destination -Limit $Limit
        return
    }
    $escapedVersion = [Uri]::EscapeDataString($Version)
    $escapedName = [Uri]::EscapeDataString($Name)
    $uri = [uri]("$($DownloadBaseUrl.TrimEnd('/'))/$escapedVersion/$escapedName")
    if ($uri.Scheme -ne 'https' -and -not $uri.IsLoopback) {
        throw "release downloads require HTTPS"
    }
    Receive-BoundedFile -Uri $uri -Destination $Destination -Limit $Limit
}

function Confirm-Checksum {
    param([string] $Archive, [string] $Checksum, [string] $ArchiveName)
    $checksumText = [System.IO.File]::ReadAllText($Checksum).Trim()
    $match = [regex]::Match($checksumText, '^([0-9a-fA-F]{64})  ([^\r\n]+)$')
    if (-not $match.Success -or $match.Groups[2].Value -ne $ArchiveName) {
        throw "checksum file must contain one SHA-256 entry for $ArchiveName"
    }
    $actual = (Get-FileHash -LiteralPath $Archive -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actual -ne $match.Groups[1].Value.ToLowerInvariant()) {
        throw "checksum mismatch for $ArchiveName"
    }
    return $actual
}

function Expand-VerifiedZip {
    param([string] $Archive, [string] $Destination, [string[]] $ExpectedMembers)
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    try {
        $zip = [System.IO.Compression.ZipFile]::OpenRead($Archive)
    } catch {
        throw "cannot inspect release archive: $_"
    }
    try {
        $actual = @($zip.Entries | ForEach-Object { $_.FullName })
        if (($actual.Count -ne $ExpectedMembers.Count) -or (Compare-Object $actual $ExpectedMembers)) {
            throw "archive members do not match the published layout"
        }
        foreach ($entry in $zip.Entries) {
            $unixType = (($entry.ExternalAttributes -shr 16) -band 0xF000)
            if ($entry.FullName.EndsWith('/') -or ($unixType -ne 0 -and $unixType -ne 0x8000)) {
                throw "archive member is not a regular file: $($entry.FullName)"
            }
            if ($entry.Length -gt $expandedFileLimit) {
                throw "archive member exceeds the $expandedFileLimit byte expanded limit: $($entry.FullName)"
            }
            $destinationPath = Join-Path $Destination ($entry.FullName.Replace('/', [IO.Path]::DirectorySeparatorChar))
            $parent = Split-Path -Parent $destinationPath
            [System.IO.Directory]::CreateDirectory($parent) | Out-Null
            [System.IO.Compression.ZipFileExtensions]::ExtractToFile($entry, $destinationPath, $false)
        }
    } finally {
        $zip.Dispose()
    }
}

function Expand-VerifiedTar {
    param([string] $Archive, [string] $Destination, [string[]] $ExpectedMembers)
    $actual = @(& tar -tzf $Archive 2>&1)
    if ($LASTEXITCODE -ne 0) {
        throw "cannot inspect release archive: $($actual -join ' ')"
    }
    if (($actual.Count -ne $ExpectedMembers.Count) -or (Compare-Object $actual $ExpectedMembers)) {
        throw "archive members do not match the published layout"
    }
    $verbose = @(& tar -tvzf $Archive 2>&1)
    if ($LASTEXITCODE -ne 0 -or $verbose.Count -ne $ExpectedMembers.Count) {
        throw "cannot inspect release archive members"
    }
    foreach ($line in $verbose) {
        if (-not $line.ToString().StartsWith('-')) {
            throw "archive contains a non-regular member: $line"
        }
    }
    $extractOutput = @(& tar -xzf $Archive -C $Destination 2>&1)
    if ($LASTEXITCODE -ne 0) {
        throw "cannot extract release archive: $($extractOutput -join ' ')"
    }
}

if ($Version -notmatch '^v(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)(?:-rc\.(?:0|[1-9][0-9]*))?$') {
    throw 'version must be an exact release such as v0.3.0 or v0.3.0-rc.1'
}

$target = Get-NativeTarget -RequestedOS $TargetOS -RequestedArch $TargetArch
$extension = if ($target.OS -eq 'windows') { 'zip' } else { 'tar.gz' }
$executableName = if ($target.OS -eq 'windows') { 'playtestr.exe' } else { 'playtestr' }
$baseName = "playtestr_$($Version.Substring(1))_$($target.OS)_$($target.Arch)"
$archiveName = "$baseName.$extension"
$expectedMembers = @($expectedDocumentNames | ForEach-Object { "$baseName/$_" }) + @("$baseName/$executableName")
$expectedMembers = @($expectedMembers | Sort-Object)

[System.IO.Directory]::CreateDirectory($InstallRoot) | Out-Null
$workRoot = Join-Path $InstallRoot ('.staging-' + [Guid]::NewGuid().ToString('N'))
$downloadRoot = Join-Path $workRoot 'download'
$extractRoot = Join-Path $workRoot 'extract'
[System.IO.Directory]::CreateDirectory($downloadRoot) | Out-Null
[System.IO.Directory]::CreateDirectory($extractRoot) | Out-Null

try {
    $archivePath = Join-Path $downloadRoot $archiveName
    $checksumPath = "$archivePath.sha256"
    Get-ReleaseFile -Name $archiveName -Destination $archivePath -Limit $archiveLimit
    Get-ReleaseFile -Name "$archiveName.sha256" -Destination $checksumPath -Limit $checksumLimit
    $archiveHash = Confirm-Checksum -Archive $archivePath -Checksum $checksumPath -ArchiveName $archiveName

    if ($target.OS -eq 'windows') {
        Expand-VerifiedZip -Archive $archivePath -Destination $extractRoot -ExpectedMembers $expectedMembers
    } else {
        Expand-VerifiedTar -Archive $archivePath -Destination $extractRoot -ExpectedMembers $expectedMembers
    }

    $stagedDirectory = Join-Path $extractRoot $baseName
    foreach ($member in $expectedMembers) {
        $memberPath = Join-Path $extractRoot ($member.Replace('/', [IO.Path]::DirectorySeparatorChar))
        $item = Get-Item -LiteralPath $memberPath
        if ($item.PSIsContainer -or ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -or $item.Length -gt $expandedFileLimit) {
            throw "extracted member is not a bounded regular file: $member"
        }
    }
    $stagedBinary = Join-Path $stagedDirectory $executableName
    if ($target.OS -ne 'windows') {
        & chmod 755 $stagedBinary
        if ($LASTEXITCODE -ne 0) { throw "cannot make Playtestr executable" }
    }
    $reportedVersion = (& $stagedBinary --version 2>&1 | Out-String).Trim()
    if ($LASTEXITCODE -ne 0 -or $reportedVersion -ne "playtestr $Version") {
        throw "downloaded binary reported '$reportedVersion', expected 'playtestr $Version'"
    }

    $installDirectory = Join-Path $InstallRoot ("$baseName-" + [Guid]::NewGuid().ToString('N'))
    Move-Item -LiteralPath $stagedDirectory -Destination $installDirectory
    $binaryPath = Join-Path $installDirectory $executableName
    $installedVersion = (& $binaryPath --version 2>&1 | Out-String).Trim()
    if ($LASTEXITCODE -ne 0 -or $installedVersion -ne "playtestr $Version") {
        Remove-Item -LiteralPath $installDirectory -Recurse -Force -ErrorAction SilentlyContinue
        throw "installed binary failed its absolute-path version check"
    }

    Write-EnvironmentLine -File $OutputFile -Line "version=$Version"
    Write-EnvironmentLine -File $OutputFile -Line "binary-path=$binaryPath"
    Write-EnvironmentLine -File $OutputFile -Line "install-dir=$installDirectory"
    Write-EnvironmentLine -File $OutputFile -Line "archive-sha256=$archiveHash"
    Write-EnvironmentLine -File $PathFile -Line $installDirectory
    Write-Host "Installed and verified Playtestr $Version at $binaryPath"
} finally {
    Remove-Item -LiteralPath $workRoot -Recurse -Force -ErrorAction SilentlyContinue
}
