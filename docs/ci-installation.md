# Install Playtestr in GitHub Actions

Status: immutable action revision
`ae97c62022966cde9699b26169b4dc6ef0a12439` is verified for exact-version
installation of published `v0.4.0-rc.3` on Windows amd64, Linux amd64 and
macOS arm64. [Public distribution/upgrade verification](https://github.com/Wyrcan-io/playtestr/actions/runs/36871693872)
and [binary-only installation checks](https://github.com/Wyrcan-io/playtestr/actions/runs/36871699556)
passed. Pin the full action SHA and runner version independently. Historical
v0.4.0-rc.1 action evidence remains in its own release record.

The setup action installs exactly one published Playtestr runner release. It
does not install the target application, run tests, update snapshots, cache
downloads, upload artifacts, or write to the repository.

## Pinned CI workflow

The complete example below builds this repository's actual mission-control target and runs its committed menu tests. Copy it to `.github/workflows/terminal-pr-example.yml` in a checkout of Playtestr, including `scripts/ci/report_summary.py`, `cmd/demo`, the two menu specs and their reviewed baseline. It requires the existing Go module for the demo and Python 3.12 for the summary helper. The installed runner itself does not require Go or Python.

This workflow and summary helper are source additions, separate from the downloaded runner. On 5 October 2026, hosted [normal execution](https://github.com/Wyrcan-io/playtestr/actions/runs/37328072239) passed, an [injected regression](https://github.com/Wyrcan-io/playtestr/actions/runs/37328099210) correctly failed while HTML, job summary and artifact upload succeeded, and [unchanged recovery](https://github.com/Wyrcan-io/playtestr/actions/runs/37328210937) passed. Downloaded evidence confirmed the snapshot mismatch and process cleanup. The [validation record](https://github.com/Wyrcan-io/playtestr/blob/main/docs/validation/adoption-preparation-2026-10-05.md) also records local checks and native helper tests. These were repository-owned demo executions, not independent adoption or execution of an external fork PR.

```yaml
name: Terminal PR example

on:
  pull_request:
    paths: ['cmd/demo/**', 'examples/**', 'scripts/ci/**', '.github/workflows/terminal-pr-example.yml', 'go.mod', 'go.sum']
  push:
    branches: [main]
    paths: ['cmd/demo/**', 'examples/**', 'scripts/ci/**', '.github/workflows/terminal-pr-example.yml', 'go.mod', 'go.sum']
  workflow_dispatch:
    inputs:
      inject_regression:
        description: 'Seed a demo defect to verify a red check and retained evidence'
        type: boolean
        default: false

permissions:
  contents: read

jobs:
  terminal:
    runs-on: ubuntu-24.04
    timeout-minutes: 10
    env:
      PLAYTESTR_VERSION: v0.4.0-rc.3
    steps:
      - name: Check out tests and target
        id: checkout
        uses: actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803 # v6
        with:
          persist-credentials: false
      - name: Install Python for the summary helper
        uses: actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1 # v6
        with:
          python-version: '3.12'
      - name: Install published Playtestr
        id: install
        uses: Wyrcan-io/playtestr/setup-playtestr@ae97c62022966cde9699b26169b4dc6ef0a12439
        with:
          version: ${{ env.PLAYTESTR_VERSION }}
      - name: Verify exact runner version
        run: test "$(playtestr --version)" = "playtestr $PLAYTESTR_VERSION"
      - name: Install Go for this example target
        uses: actions/setup-go@b7ad1dad31e06c5925ef5d2fc7ad053ef454303e # v7
        with:
          go-version-file: go.mod
      - name: Build the actual demo target
        id: prepare
        env:
          INJECT_REGRESSION: ${{ inputs.inject_regression || false }}
        run: |
          if [ "$INJECT_REGRESSION" = "true" ]; then
            go build -ldflags '-X main.diagnosticsSuffix=REGRESSION' -o bin/demo ./cmd/demo
          else
            go build -o bin/demo ./cmd/demo
          fi
      - name: Test committed terminal interactions
        id: tests
        run: playtestr test --artifacts-dir artifacts/pr-example/screens --report artifacts/pr-example/results.json examples/menu.json examples/menu-exit.json
      - name: Render offline evidence
        id: html
        if: always() && steps.checkout.outcome == 'success'
        run: playtestr report --input artifacts/pr-example/results.json --evidence-root artifacts/pr-example --output artifacts/pr-example/report.html
      - name: Write job summary
        if: always() && steps.checkout.outcome == 'success'
        env:
          SETUP_OUTCOME: ${{ steps.install.outcome || 'unknown' }}
          PREPARE_OUTCOME: ${{ steps.prepare.outcome || 'unknown' }}
          TEST_OUTCOME: ${{ steps.tests.outcome || 'unknown' }}
          HTML_OUTCOME: ${{ steps.html.outcome || 'unknown' }}
          RUN_URL: https://github.com/${{ github.repository }}/actions/runs/${{ github.run_id }}
        run: |
          python scripts/ci/report_summary.py --input artifacts/pr-example/results.json \
            --evidence-root artifacts/pr-example --output "$GITHUB_STEP_SUMMARY" \
            --setup-outcome "$SETUP_OUTCOME" --prepare-outcome "$PREPARE_OUTCOME" \
            --test-outcome "$TEST_OUTCOME" --html-outcome "$HTML_OUTCOME" \
            --artifact-name playtestr-evidence --run-url "$RUN_URL"
      - name: Upload evidence even after failure
        if: always() && steps.checkout.outcome == 'success'
        uses: actions/upload-artifact@b7c566a772e6b6bfb58ed0dc250532a479d7789f # v6
        with:
          name: playtestr-evidence
          path: artifacts/pr-example/
          if-no-files-found: warn
          retention-days: 14
```

For another project, replace the Go setup/build with your target's real prerequisites and build command, then select that project's committed specs. Copy the standalone `scripts/ci/report_summary.py` helper; it has no package dependencies. Keep the report and evidence paths identical across execution, rendering, summary and upload. Pins for third-party Actions were resolved from their public v6/v7 tags on 5 October 2026; review them when updating.

The default run must pass. For a controlled failure, manually dispatch with `inject_regression: true`. This appends `REGRESSION` to the demo's diagnostics output while leaving the spec and snapshot unchanged. The snapshot comparison must fail with exit 1; the test job stays red while later evidence steps run. Dispatch again with the input false to restore a pass. This is a seeded repository-owned demo defect, not an upstream bug.

## Read the summary and failure evidence

Open the workflow run from the PR's Checks tab. Its job summary lists captured counts, each problem spec, failure category, cleanup state and local screen/diff availability. The run link leads to the Artifacts section. Download `playtestr-evidence`, extract it, and open `report.html`; it works offline. If HTML rendering failed, inspect `results.json` and the files under `screens/` instead. The summary does not promise that an upload completed; check the upload step and artifact list.

Installation or target-build failure means tests can be skipped. Missing, malformed, empty, unsupported or inconsistent reports yield an explicit unavailable-report summary and helper exit 2. Cancelled and not-run specs remain separate counts. A hard workflow cancellation may prevent final steps from running at all; missing evidence must not be read as a pass. Renderer and uploader failures are additional workflow failures. No blanket `continue-on-error` or snapshot update is used.

The helper consumes existing report v1/v2 metadata, not raw screens or failure prose. It reads at most 8 MiB, accepts at most 1,000 results and 10,000 steps, checks count/outcome consistency and escapes displayed metadata. At most 100 problem rows are displayed; an omission count points to the full report. Generated text plus existing destination content is bounded to 256 KiB, below GitHub's per-step summary limit. Unknown unused report fields are ignored; this helper is not a replacement for full schema validation. A valid failed report renders with helper exit 0; the earlier test command owns the failed check. An invalid report or unwritable summary returns 2. No report field becomes a shell command, hyperlink, annotation or raw log output.

Evidence presence checks resolve references from the invocation working directory and admit only files inside the selected evidence root, including after symlink resolution. They do not read screens, or certify evidence content or successful upload. Keep sensitive target output out of artifacts. Retention is 14 days in this example. Review artifact visibility before running a target that can print private data.

Fork PR execution uses `pull_request`, `contents: read`, and no target secrets or write credentials. Test only targets you have reviewed and trust; Playtestr is not an execution sandbox. Do not move PR-head execution into privileged `pull_request_target` merely to post comments. This example produces an Actions summary, not a PR comment or hosted bot. [GitHub summary behavior](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-commands#adding-a-job-summary), [fork/privileged-event behavior](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#pull_request_target), and [artifact retrieval](https://docs.github.com/en/actions/tutorials/store-and-share-data) describe the platform boundaries.

## Local verification and removal

From a repository checkout with Go, Python and an installed exact rc.3 runner:

```sh
python -m unittest discover -s scripts/ci -p 'test_*.py' -v
python scripts/ci/capture_demo.py --runner /absolute/path/to/playtestr --output artifacts/adoption-demo
```

The capture command requires a fresh output directory and preserves old attempts. It builds the real demo, runs pass/seeded snapshot failure/recovery against an unchanged spec/baseline, renders HTML and generates a summary for each. Windows may pass a quoted path to `playtestr.exe`. Logs, hashes and `capture.json` remain in ignored artifacts. These local checks do not establish Actions or other-host execution.

To remove this integration, delete its workflow and copied summary helper, then remove test specs/baselines that you no longer want. No GitHub App, account or subscription needs disconnecting. The setup Action installed a binary into the disposable runner's tool directory; a self-hosted installation can be removed using its `install-dir` output when no job is using it. Existing retained artifacts expire under the configured policy or can be deleted by an authorized repository owner.

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
branches are rejected. It downloads the matching archive and checksum over
verified HTTPS with three attempts, a 120-second timeout per attempt, a 64 MiB
archive limit, and a 4 KiB checksum-file limit. It first accepts the historical
adjacent `<archive>.sha256` asset, then falls back to the release's aggregate
`checksums-<version>.txt` manifest. The selected manifest must contain exactly
one valid entry for the requested archive. A checksum from the same GitHub
Release proves transport/storage integrity, not independent authorship.

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
download the exact host archive and the checksum asset published by that
release, verify the named digest, inspect/extract the expected versioned
directory, and invoke the binary by its absolute path. Do not treat a
same-version archive fetched from another source as equivalent.

## Maintenance ownership and release updates

The current source installer bounds each executable version check to ten
seconds and 4,096 characters per output stream. A nonzero exit, unexpected
stderr, excessive output or timeout rejects installation before publishing its
path. On Windows, a deep executable path uses its existing native short alias;
if the path exceeds the native launch limit and no usable alias exists, choose
a shorter installation root. The installer does not enable short names or
change the host's long-path settings. These source changes do not update an
older pinned setup Action automatically.

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
