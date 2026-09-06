# Release candidate process

Playtestr uses Apache License 2.0 and supports Go 1.25 or newer. Release binaries carry their version through the `github.com/Wyrcan-io/playtestr/internal/buildinfo.Version` linker variable.

Build and package one native target from the repository root:

```powershell
$version = 'v0.1.0-rc.1'
go test ./...
go build -trimpath -ldflags "-s -w -X github.com/Wyrcan-io/playtestr/internal/buildinfo.Version=$version" -o bin/playtestr.exe ./cmd/playtestr
go run ./cmd/package-release -binary bin/playtestr.exe -version $version -os windows -arch amd64 -out dist
```

The package command creates a ZIP on Windows or a tar.gz on Unix. Each archive contains the native binary, `README.md`, and `LICENSE`, with an adjacent SHA-256 file. It packages an already-built native binary and does not turn cross-compilation into a platform-support claim.

The release-candidate workflow builds and exercises each advertised native runner before uploading archives as workflow artifacts. Publishing a GitHub Release and tag remains a separate explicit action after those jobs and a clean packaged-binary walkthrough pass.
