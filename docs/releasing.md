# Release candidate process

Playtestr uses Apache License 2.0 and supports Go 1.25 or newer. Release binaries carry their version through the `github.com/Wyrcan-io/playtestr/internal/buildinfo.Version` linker variable.

Build and package one native target from the repository root:

```powershell
$version = 'v0.1.0-rc.1'
go test ./...
go build -trimpath -ldflags "-s -w -X github.com/Wyrcan-io/playtestr/internal/buildinfo.Version=$version" -o bin/playtestr.exe ./cmd/playtestr
go run ./cmd/package-release -binary bin/playtestr.exe -version $version -os windows -arch amd64 -out dist
```

The package command creates a ZIP on Windows or a tar.gz on Unix. Each archive contains the native binary, `README.md`, `LICENSE`, and `THIRD_PARTY_NOTICES.md`, with an adjacent SHA-256 file. It packages an already-built native binary and does not turn cross-compilation into a platform-support claim.

The release-candidate workflow builds each advertised native runner, packages it, validates the archive checksum and exact member list, extracts it into a path containing spaces, and invokes that extracted binary. It checks version/help output, passing specs, a deliberate snapshot-mismatch category, its evidence, and a writable report before uploading the same archive as a workflow artifact.

Publishing a GitHub Release and tag remains a separate explicit action after every native job passes. Release assets must be downloaded from the published release afterward and compared with the workflow outputs; an uploaded archive is not accepted merely because its build job succeeded.
