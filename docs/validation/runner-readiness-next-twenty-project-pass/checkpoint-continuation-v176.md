# Runner readiness continuation checkpoint v176

## Cumulative status

The ledger remains **18/30 admissions**, with **2/20 new packages** admitted
(JOE and fzy). Percol remains at zero. Current candidate is exact
`v0.4.0-rc.8` (`native-exit-v3`).

## Percol development attempt v3

Run `43381175066` exercised v3 once on Linux amd64 and macOS arm64. Both passed
N01 through N06, then N07 timed out after Backspace was sent before a positive
prompt readiness check; retained screens still showed query `apx`. Both hosts
confirmed target process-group exit and scenario workspace cleanup. Their exact
source/runtime cleanup then passed: all eight known CPython links were validated
before removal, and source/runtime payloads were removed after evidence retention.
Storage checks passed. The downloaded ZIPs match provider digests. Full details
are recorded in `percol/development-attempt-v3.json`; project and final-matrix
credit remain zero.

## Current uncommitted correction

Scenario v3 remains preserved. V4 starts N07 with an explicit `expect: apx`
screen checkpoint, sends Backspace only after that positive readiness evidence,
then requires the refreshed inverted result `banana`. V4 is materialized and the
local contract verifier passes; no v4 case has launched. Focused harness tests
were last passed before the v4 action-order edit and need one rerun before commit.

Current job `43381175066` is complete on both hosts. Exact failed and successful
historical ZIPs remain under the ignored campaign `retained/` directory; these
are local-only packets. No local target runtime, owned PID or mounted volume
remains. Next action is rerun the focused tests and workflow syntax checks, commit
the v3 failure receipt/checkpoint with v4, push, then inspect the next native
result before any further contract change.
