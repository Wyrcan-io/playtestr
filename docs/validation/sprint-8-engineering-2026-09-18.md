# Sprint 8 engineering validation — 18 September 2026

Status: setup-action engineering is implemented locally. Windows native checks
are recorded below. The first public action revision, Linux/macOS native action
runs, and independent adoption are still open and are not inferred from a
configured workflow. Maintainer adoption and outside feedback are deliberately
deferred until after Sprint 10 by product decision.

## Route selection and observed setup friction

Sprint 8 selects one route only: a setup-only GitHub Action. The Playtestr
repository maintainers own the action and its release smoke workflow.

Two existing, concrete operator paths selected this route:

| Observation | Attempt and prerequisites | Assistance/time record | Concrete friction |
| --- | --- | --- | --- |
| `.github/workflows/install-smoke.yml` manually installed every published binary | Each native job constructed an OS/architecture asset name, invoked `curl`, parsed a checksum, selected `sha256sum` or `shasum`, selected `tar` or `unzip`, constructed an absolute binary path, and only then ran the first test. | Repository-specific workflow logic supplied the asset map and commands. No participant timing was collected. | About 40 setup lines were mixed into the adopter test. The default still selected `v0.1.0` after the workflow began calling the later `report` command, so its default runner pin no longer matched its commands. |
| The stable binary walkthrough requires three platform-specific branches | The operator must identify architecture, fetch two assets, choose the platform checksum command, extract, invoke a nested path, and optionally edit PATH. | The written walkthrough provides all commands. No participant timing was collected. | Archive naming, checksum filename validation, executable permission, PATH precedence, and cleanup remain operator responsibilities and differ by host. |

These are engineering observations, not independent-user evidence. They justify
removing repeated CI setup work while direct archive installation remains the
fallback. No package channel, cache, self-update, hosted upload, or repository
write permission was added.

## Frozen installation contract

- Action code and runner version are separate pins. Consumers select the action
  by an immutable 40-character commit SHA and pass an exact runner version.
- Accepted runner versions are `vMAJOR.MINOR.PATCH` and
  `vMAJOR.MINOR.PATCH-rc.NUMBER`; `latest`, branches, and ranges are rejected.
- The only advertised mappings are Linux amd64, macOS arm64, and Windows amd64,
  matching published native assets.
- HTTPS certificate verification remains enabled. Downloads have three
  attempts, a 120-second timeout per attempt, a 64 MiB archive cap, and a 4 KiB
  checksum cap.
- The adjacent checksum must contain exactly the requested archive filename and
  matching SHA-256. This is same-origin integrity evidence, not a signature.
- Exact regular archive members are checked before extraction. Extraction uses
  a fresh owned staging directory; every resulting file is bounded and checked
  against links before the binary is exposed.
- The staged and final binaries are invoked by absolute path and must report the
  requested version. Only then are outputs and `GITHUB_PATH` written.
- Failure removes staging and emits no ready binary path. Installations are
  unique job-temporary directories, need no elevation, and make no persistent
  machine-wide change.

The action outputs the selected version, absolute binary and install directory,
and verified archive hash. It installs only Playtestr. Target setup, runner
execution, baseline review, and explicit artifact upload remain ordinary steps.

## Focused Windows native checks

`go test -count=1 ./internal/setupaction` exercises the actual PowerShell
installer with a natively executable fixture archive. The test matrix covers:

- a normal install beneath a path containing spaces;
- absolute version verification and PATH precedence over a stale executable;
- a missing release asset;
- a wrong checksum;
- a corrupt archive whose checksum matches its corrupt bytes;
- an escaping extra archive member;
- an unsupported OS/architecture mapping;
- a non-exact version; and
- a loopback server that exceeds the one-second test timeout.

Every failure case checks that neither action outputs nor a PATH entry were
published and that the staging directory was removed. The public-release smoke
uses the local action as its own setup step and separately exercises pass,
controlled assertion failure, retained screen/HTML evidence, recovery,
missing-target failure, invalid-spec prelaunch rejection, report-write failure,
no-Go execution, and the applicable controlling-terminal regression. Its
artifact paths are explicit, retention is 14 days, permissions are read-only,
and ordinary test failures are not continued.

The focused test command passed all cases in about 21 seconds. The setup script
then downloaded and installed the actual public `v0.3.0-rc.1` Windows amd64
archive in about 14 seconds into a
path containing spaces, verified SHA-256
`3ed1f69faa0abf970ee6cf1f17b59bd3d72f89e305ac2cf7b9687833a6a457f6`,
and reported `playtestr v0.3.0-rc.1` from the absolute installed binary.

The pass/failure/recovery exercise completed in about 17 seconds. That binary
ran the Windows greeting fixture successfully, rejected the
controlled regression with exit 1 and `assertion_timeout`, retained its screen,
rendered a 7,300-byte offline HTML diagnosis, and passed after the good spec was
restored. The recovered report had no evidence reference; the old screen was
retained as historical evidence until explicit cleanup. A configured
Linux/macOS workflow is not recorded as a pass.

## Publication, upgrade, and adoption boundary

Local preparation consists of `setup-playtestr/action.yml`, the bounded
installer, focused integration tests, the converted published-install workflow,
and the complete usage/maintenance contract in `docs/ci-installation.md`.

Publication remains separate and requires an authorized commit/push. After the
action commit exists publicly, record its immutable SHA in the documentation,
run the published-install workflow on all three native hosts, and link that run
here. Do not publish a dummy runner version. A later real runner release is the
upgrade check: change only the workflow's exact runner pin, retain the action
pin, and repeat pass/failure/recovery.

Independent adoption and outside usability feedback remain explicitly open
until after Sprint 10. No participant, external publication, upstream
submission, Linux/macOS action result, or later-release upgrade is claimed in
this record.

## Repository verification

The following local Windows checks passed after the installer work. The first
full and race runs exposed a test-only fixed 100 ms cancellation trigger that
could cancel before its helper process started under package load. The test now
waits for its existing start sentinel with a four-second test-only fallback;
product session deadlines and cancellation behavior are unchanged. Ten focused
repetitions, the replacement full run, and the replacement race run passed.

```text
go test -count=1 ./internal/setupaction
go test -count=10 -run TestCancellationReturns130AndStopsLaterSpecs ./cmd/playtestr
go test -count=1 ./...
go vet ./...
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\test-race.ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\site.ps1 build
```

The website build produced 25 pages and its link/metadata/budget validation
passed. Action metadata and the edited workflow also parsed as YAML locally.
