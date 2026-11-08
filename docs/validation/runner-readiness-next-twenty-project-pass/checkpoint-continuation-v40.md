# Continuation checkpoint v40: 8 November 2026

Branch `work/p0-p2-implementation` is at pushed commit `81847b67`; scoped Taskell corrections are local and not yet committed. Explicit commit/push and hosted workflow authorization remains active. The active native exact-candidate attempt 42494654068 completed on both hosts with zero scenario credit. Campaign progress remains four new admissions (14/30 cumulative); Taskell remains unadmitted.

## Taskell exact candidate status

The exact v0.4.0-rc.6 Darwin arm64 archive remains frozen at 1,855,437 bytes and SHA-256 `132152710ade2c01cac7558f75212121f01af8ab02c5735dc9c7de1c33dbe625`. The earlier exploratory run 42489015452 passed the pinned source suite, first-use smoke, 20 authored scenarios, and public recorder route on Linux amd64 and Intel macOS. It remains one-shot source-build evidence and does not count toward exact-candidate repetitions.

Run 42494654068 verified the acquired Taskell pin and exact source tree on Linux and Apple Silicon without GitHub API calls. Linux passed `stack test --test` and built Taskell 1.11.4 (`6099f625fc30ee1fefcef87c3aa40e34915b4b254b52f4276d940e976225dfd8`), but all twelve harness batches stopped before target launch because the *pushed* journal version still looked only under raw staging for `host-contracts`. macOS arm64 acquired and verified source, then Stack could not provision frozen GHC 9.0.1 for `macosx-aarch64`; tests/build/scenarios did not run. Full outcome record: `taskell/build-attempt-v33.json`.

Local corrections now add the docs-root fallback to the shared journal, an owned Stack configuration that keeps the frozen nightly resolver, dependency lock, and source while selecting supported GHC 9.0.2 on Apple Silicon, and a three-fault baseline/mutated/restored calibration (nine phases per host). The override YAML and fault hashes/count, Python syntax, and `git diff --check` were checked locally. Hosted qualification of these changes has not started. The exact fault workflow is prepared separately, in the same concurrency group as the ordinary series.

The contracts and fixture manifest retain 21 invocation contracts across eight normal workflows and twelve edge families (malformed E11 and recovery are distinct). The closing declaration still requires 504 ordinary exact-candidate invocations and 18 fault-control executions across Linux/macOS. No run has yet earned those credits.

Storage v38 observed `2,147,359,477` combined retained bytes, leaving `124,171` bytes below the declared cap. Receipt `artifacts/runner-readiness-next-twenty-project-pass/storage/53da7380309d4695984d8baff822e482/observed.json`, SHA-256 `8acb795bf56cfd1a57580a40279a9ca0b99688da44b2a974e2710e0256cf4848`. Keep new documentation and harness changes small; do not add raw hosted packets to Git.

## Next actions

1. Validate scoped changes, commit/push them under existing authorization, and inspect that the corrected exact-candidate workflow starts on both standard hosts.
2. Retrieve and audit complete artifacts. Require all 21 contracts x12 batches x2 hosts, target/report/fixture/runtime hashes, cleanup, and the declared fault outcomes before any Taskell admission.
3. Run the Taskell baseline/mutated/restored calibration on both hosts. Preserve build failures and source restoration receipts; no partial credit.
4. Continue the remaining new projects and finish the original-ten carry-forward under the campaign's exact final-candidate matrix.

No PR, issue, discussion, release, or outreach mutation has been made. Do not claim 30/30 until every project, current-candidate cell, fault, audit, cleanup, and carry-forward gate is evidenced.
