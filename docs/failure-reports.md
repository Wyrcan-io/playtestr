# Offline failure reports

`playtestr report` turns an existing machine report and its screen/diff files
into one self-contained HTML file. It does not start the target, read test
specifications, update snapshots, or compare against a newer baseline.

The command is available in the checksum-verified
[`v0.3.0-rc.1`](https://github.com/Wyrcan-io/playtestr/releases/tag/v0.3.0-rc.1)
prerelease and later builds. It is not present in `v0.1.0` or `v0.2.0-rc.1`.
Check `playtestr report --help` when using another packaged version.

## Capture and export

Run the test from a directory that can contain a single explicit artifact root:

```text
playtestr test --artifacts-dir artifacts --report artifacts/results.json tests
playtestr report --input artifacts/results.json --evidence-root artifacts --output artifacts/report.html
```

Open `artifacts/report.html` directly in a browser. It needs no server, account,
network connection, JavaScript, target application, spec files, or separate
screen/diff files after generation. Moving that HTML file by itself preserves
the report.

Keep the JSON report and evidence tree together until the HTML is generated.
Relative evidence references are resolved from the directory where the report
command runs, then admitted only when their resolved files remain under
`--evidence-root`. Run the export from the same relative layout used for the
test command. Evidence references containing traversal, absolute paths, URIs,
or network paths are rejected. Symlinks and junctions cannot be used to escape
the root. A screen and diff for one result must share the runner's report-v1
artifact prefix, and one evidence file cannot be assigned to two spec results.

`--output` must not alias the input JSON or an admitted evidence file. The HTML
is written atomically; a validation, read, size, or write error leaves an
existing output unchanged. A rendering error does not modify any captured test
status.

## What the first view answers

The report shows:

- pass, fail, cancelled, and not-run totals;
- failures first in a compact navigation list, distinguished by `spec_path`
  even when display names are duplicated;
- the first recorded failing step, action, category, viewport, final captured
  screen, and existing unified diff;
- target exit, cleanup, and evidence-write outcomes as separate facts; and
- every passing result and all recorded steps behind ordinary document flow and
  native disclosure controls.

Missing screen or diff evidence is labeled where it would appear. For an
assertion timeout, report v1 does not contain the expected expression, so the
HTML says it is unavailable. The renderer does not recover it from a spec or
guess a history or root cause. A readable artifact is embedded captured data,
not proof of cryptographic integrity.

The page is usable with JavaScript disabled. Links, a skip link, native
disclosures, scrollable terminal panes, responsive one-column layout, visible
focus, and high-contrast diff rows support keyboard and narrow-screen use.
There are no scripts, external styles, fonts, images, telemetry, or remote
requests.

## Limits and errors

The renderer enforces these limits before replacing the requested output:

| Input or output | Limit |
| --- | ---: |
| JSON report | 8 MiB |
| Results | 1,000 |
| Aggregate recorded steps | 10,000 |
| Each screen or diff file | 256 KiB |
| Aggregate embedded evidence | 24 MiB |
| Generated HTML | 32 MiB |

Missing referenced evidence is an incomplete-but-readable report and is shown
as missing. An unsupported version, malformed/truncated JSON, inconsistent
summary or identity, unsafe reference, unreadable or oversized evidence, output
alias, or failed requested write is a rendering error and exits nonzero.

## Privacy

The HTML embeds admitted screen and diff text verbatim as escaped literal
content. ANSI and OSC bytes are never interpreted as HTML or links. Report-v1
metadata still excludes command arguments, environment values, typed text, and
expected strings, but a target can print secrets or personal data to its screen.

Inspect `report.html` before sharing it. Use synthetic examples for demos.
Automatic sanitization and secret detection are not promised.

## Two diagnosis checks

Build the repository fixtures, then capture the two Sprint 7 cases:

```text
go build -o bin/demo.exe ./cmd/demo
go build -o bin/fixture.exe ./cmd/fixture
go build -o bin/playtestr.exe ./cmd/playtestr

bin/playtestr.exe test --artifacts-dir artifacts --report artifacts/snapshot-results.json examples/snapshot-mismatch.json
bin/playtestr.exe report --input artifacts/snapshot-results.json --evidence-root artifacts --output artifacts/snapshot-report.html

bin/playtestr.exe test --artifacts-dir artifacts --report artifacts/timeout-results.json examples/assertion-timeout.json
bin/playtestr.exe report --input artifacts/timeout-results.json --evidence-root artifacts --output artifacts/timeout-report.html
```

Both test commands intentionally exit 1. The first HTML includes the captured
screen and unified diff at snapshot step 4. The second includes the screen and
assertion-timeout category at step 2, while explicitly labeling the unavailable
expected expression and diff.

For the pass/failure/recovery demo, use the same `examples/menu.json` spec and
reviewed baseline throughout. Build and run the normal demo, build the demo's
explicit synthetic regression, inspect its generated report, then restore the
normal build and rerun green:

```powershell
go build -o bin/demo.exe ./cmd/demo
bin/playtestr.exe test --artifacts-dir artifacts/sprint7-demo --report artifacts/good.json examples/menu.json

go build -ldflags '-X=main.diagnosticsSuffix=_REGRESSION' -o bin/demo.exe ./cmd/demo
bin/playtestr.exe test --artifacts-dir artifacts/sprint7-demo --report artifacts/bad.json examples/menu.json
bin/playtestr.exe report --input artifacts/bad.json --evidence-root artifacts --output artifacts/bad.html

go build -o bin/demo.exe ./cmd/demo
bin/playtestr.exe test --artifacts-dir artifacts/sprint7-demo --report artifacts/recovered.json examples/menu.json
```

The middle test intentionally exits 1 at snapshot step 6 and its focused diff
shows `_REGRESSION` added to the target's diagnostic result. No spec or baseline
changes between the three runs. Preserve the bad run directory until its
evidence has been reviewed for sensitive content.
