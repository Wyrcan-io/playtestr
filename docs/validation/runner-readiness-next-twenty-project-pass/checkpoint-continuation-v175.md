# Runner readiness continuation checkpoint v175

## Cumulative and active work

The cumulative ledger remains **18/30 admissions**, with **2/20 new packages**
admitted (JOE and fzy). Percol remains at zero admission credit. Current exact
private candidate is `v0.4.0-rc.8` (`native-exit-v3`).

Percol v1 and v2 native attempts are preserved in
`percol/development-attempt-v1.json` and `percol/development-attempt-v2.json`.
Both partial runs reached Linux amd64 and macOS arm64 and their uploaded ZIPs
were downloaded with hashes matching GitHub's provider digests. v1 passed N01
and N02 before an invalid subsequence expectation at N03. v2 passed N01 through
N06 before N07's saved-state check caught Percol returning `apple` while its
initial invert-mode query displayed both `apple` and `banana`. All launched
targets exited, and all associated test workspaces were cleaned. Neither partial
series earns final-matrix or admission credit.

The v1 source-bytecode cleanup defect is corrected in v2: no files were added to
Percol's exact source tree. Both runs exceeded the current cleanup inventory's
approved runtime-symlink set. Runtime bundles were retained before any removal;
storage caps passed. Exact host artifacts, report paths, failure categories,
candidate and hashes are captured in the attempt records. No local target
runtime, owned PID or mounted volume remains. Local source-only acquisition and
artifact ZIPs remain under the ignored campaign tree.

## Frozen v3 corrections

The v2 scenario folder and declaration remain unchanged after launch. V3 changes
N07 to start with `--query=apx`, send Backspace after Percol starts, then assert
and select `banana`; this forces a new finder evaluation after the CLI applies
invert mode. The development workflow now verifies that CPython has exactly the
eight previously observed in-tree symlinks (four executable/config aliases,
two pkg-config aliases and two man-page aliases), confirms every resolution
stays inside the owned runtime, then unlinks them only after validating the
complete set. The Python runtime archive is captured first. V3 specs, fixtures,
declaration and focused tests must pass before launch.

The two tracked fixes remain uncommitted at this checkpoint. Next: validate v3,
write the v2 failure receipts and checkpoint into Git, push to the authorized
branch, and inspect each fresh native result before proceeding.
