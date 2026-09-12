# Release process

Playtestr uses Apache License 2.0 and supports Go 1.25 or newer. Release binaries carry their version through the `github.com/Wyrcan-io/playtestr/internal/buildinfo.Version` linker variable.

Build and package one native target from the repository root:

```powershell
$version = 'v0.1.0'
go test ./...
go build -trimpath -ldflags "-s -w -X github.com/Wyrcan-io/playtestr/internal/buildinfo.Version=$version" -o bin/playtestr.exe ./cmd/playtestr
go run ./cmd/package-release -binary bin/playtestr.exe -version $version -os windows -arch amd64 -out dist
```

The package command creates a ZIP on Windows or a tar.gz on Unix. Each archive contains the native binary, `README.md`, `LICENSE`, and `THIRD_PARTY_NOTICES.md`, with an adjacent SHA-256 file. It packages an already-built native binary and does not turn cross-compilation into a platform-support claim.

The **Native release build** workflow builds each advertised native runner, packages it, validates the archive checksum and exact member list, extracts it into a path containing spaces, and invokes that extracted binary. It checks version/help output, passing specs, a deliberate snapshot-mismatch category and its exact evidence, a writable report, and signal cancellation with exit 130 and confirmed cleanup. Linux and macOS also run a target that opens and exchanges input through `/dev/tty`, preventing the controlling-terminal regression found in rc.1 from escaping again.

The separate **Published install smoke** workflow accepts release candidates and stable semantic versions. Its `verify_controlling_tty` input defaults to true. Disable that check only when recording the known-bad rc.1 baseline; every later candidate and stable release must leave it enabled. The workflow places a sentinel `go` command first in the shell's `PATH` and confirms that lookup reaches the sentinel. Released binaries then run with `GOROOT` and `GOPATH` cleared while preserving the host path required by native target runtimes and ConPTY. This proves the tested shell lookup is shadowed; it does not prove that the hosted image has no Go installation elsewhere.

Publishing a GitHub Release and tag remains a separate explicit action after every native job passes. Use the exact workflow commit, create each versioned tag once, and never replace a published asset under that version. Release assets must be downloaded from the published release afterward and compared with the workflow outputs; an uploaded archive is not accepted merely because its build job succeeded. Record the commit, workflow runs, archive hashes, and public verification in the versioned release record.
