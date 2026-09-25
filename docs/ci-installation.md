# Install Playtestr in GitHub Actions

Status: the setup action is implemented and source-tested, but the proposed
immutable revision `f6ffeb76a7ec3b826052690ab53071dcdf0e565f` is **not a
supported installer for v0.4.0-rc.1**. It requests per-archive checksum assets,
while that release publishes one aggregate checksum file. Public run
[36168381776](https://github.com/Wyrcan-io/playtestr/actions/runs/36168381776)
failed safely on all three hosts before publishing PATH or successful outputs.
Use the [direct archive installation](releases/v0.1.0-installation-walkthrough.md)
fallback and do not use the placeholder below until a new immutable action
revision is explicitly selected and verified. Do not replace it with a branch
name.

The setup action installs exactly one published Playtestr runner release. It
does not install the target application, run tests, update snapshots, cache
downloads, upload artifacts, or write to the repository.

## Pinned CI workflow

Pin the action implementation and runner version independently. After the
action revision is published, replace `<ACTION_COMMIT_SHA>` with its full
40-character commit SHA:

```yaml
name: terminal regression

on: [push, pull_request]

permissions:
  contents: read

jobs:
  playtestr:
    runs-on: ubuntu-latest
    timeout-minutes: 10
    env:
      PLAYTESTR_VERSION: v0.3.0-rc.1
    steps:
      - uses: actions/checkout@v6
      - name: Install Playtestr
        id: playtestr
        uses: Wyrcan-io/playtestr/setup-playtestr@<ACTION_COMMIT_SHA>
        with:
          version: ${{ env.PLAYTESTR_VERSION }}
      - name: Verify selected version
        shell: bash
        run: test "$(playtestr --version)" = "playtestr $PLAYTESTR_VERSION"
      - name: Run terminal tests
        run: playtestr test --artifacts-dir artifacts/playtestr --report artifacts/results.json tests/terminal
      - name: Upload failure evidence
        if: always()
        uses: actions/upload-artifact@v6
        with:
          name: playtestr-evidence-${{ runner.os }}
          path: |
            artifacts/results.json
            artifacts/playtestr/**
          if-no-files-found: warn
          retention-days: 14
```

Keep setup and execution in separate steps. A failing Playtestr command must
remain a failed workflow step; do not add blanket `continue-on-error`. The
`if: always()` belongs only on evidence upload so diagnostics survive a real
regression.

Change `PLAYTESTR_VERSION` to select another exact published release. The
action does not need rebuilding when an existing supported host uses the same
release asset contract. Review release notes before changing the pin, then
confirm `playtestr --version`, one passing test, and one controlled regression.

## Supported hosts and outputs

The action deliberately maps only the release assets proved by native release
jobs:

| GitHub runner host | Release asset suffix |
| --- | --- |
| Linux x86-64 | `linux_amd64.tar.gz` |
| Apple silicon macOS | `darwin_arm64.tar.gz` |
| Windows x86-64 | `windows_amd64.zip` |

Other OS/architecture pairs fail before download. The action outputs
`version`, `binary-path`, `install-dir`, `archive-sha256`, and
`binary-sha256`. `binary-path` is
absolute and is useful when a workflow must avoid all PATH ambiguity.

GitHub-hosted runners provide the action's prerequisites. A self-hosted runner
must provide PowerShell 7 as `pwsh`; Linux and macOS also need `tar` and
`chmod`. The installed Playtestr runner itself does not require Go. The target
application and its runtime remain the workflow owner's responsibility.

The installer accepts an exact `vMAJOR.MINOR.PATCH` or
`vMAJOR.MINOR.PATCH-rc.NUMBER`; aliases such as `latest`, version ranges, and
branches are rejected. It downloads the matching archive and adjacent checksum
over verified HTTPS with three attempts, a 120-second timeout per attempt, a
64 MiB archive limit, and a 4 KiB checksum-file limit. A checksum from the same
GitHub Release proves transport/storage integrity, not independent authorship.

Before extraction, the action requires the checksum filename and SHA-256 to
match and requires exactly the binary, `README.md`, `LICENSE`, and
`THIRD_PARTY_NOTICES.md` beneath the expected versioned directory. Non-regular,
escaping, missing, duplicate, and extra members are rejected. Extraction uses
a fresh job-owned staging directory. The action invokes the staged and final
binary by absolute path and requires its output to equal the requested version
before writing to `GITHUB_PATH`; a stale executable already on PATH cannot
satisfy this check. Download, validation, or extraction failure publishes no
PATH entry or action output.

## Lifetime, fallback, and removal

Installations are unique directories beneath `RUNNER_TEMP/playtestr-setup` and
need no elevation or machine-wide change. GitHub removes the hosted runner
workspace after the job. On a persistent self-hosted runner, remove only the
directory emitted as `steps.<id>.outputs.install-dir` after its consumers have
finished; do not recursively remove `RUNNER_TEMP` or a shared parent. Failed
staging directories are removed automatically. The action has no upgrade or
self-update operation: change the exact version pin to install a new directory.

If the action is unavailable, use the direct archive route linked above:
download the exact host archive and adjacent `.sha256`, verify the named digest,
inspect/extract the expected versioned directory, and invoke the binary by its
absolute path. Do not treat a same-version archive fetched from another source
as equivalent.

## Maintenance ownership and release updates

The Playtestr repository maintainers own `setup-playtestr/`, its integration
tests, this contract, and the published-install smoke workflow. For every
change to the action, they must:

1. run the focused normal/failure installer tests and the repository checks;
2. run the local action against a real published release on every promised
   native host;
3. publish an immutable commit, record its full SHA, and keep old pins usable;
4. update the usage example only after that commit is publicly available; and
5. run the published-install pass/failure/recovery workflow and record its run.

A runner release that preserves the three asset names and archive layout needs
no action-code change; the release owner runs the smoke workflow with the new
exact version. Adding a platform or changing layout/limits requires action code,
native failure coverage, documentation, and a new immutable action revision.
Package-manager channels, caching, self-update, and mutable major tags remain
out of scope.
