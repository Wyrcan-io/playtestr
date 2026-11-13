# Runner readiness continuation checkpoint v177

## Cumulative status

The ledger remains **18/30 admissions**, with **2/20 new packages** admitted
(JOE and fzy). Percol remains at zero admission credit. Exact runner candidate:
`v0.4.0-rc.8` (`native-exit-v3`).

## Percol attempt v4

Run `43382154788` reached scenario E06 on both native Linux amd64 and macOS
arm64. N01 through N08 and E01 through E05 passed (13 cases per host). E06
reproduced a pinned upstream bug: the documented `--auto-match` path calls
`finish_with_exit_code()` without its required argument and exits 1 with
`TypeError`. The runner captured this as `unexpected_exit`; target process groups
and scenario workspaces cleaned correctly. The first failure and matching
artifact digests are in `percol/development-attempt-v4.json`; the control is
explicitly recorded in `percol/unsupported-controls-v1.json`.

V4's complete source/runtime cleanup passed on both hosts: acquisition source
hashes restored, exact eight CPython symlinks validated before mutation,
runtime archives preserved, links removed, source/runtime payloads removed, and
storage limits passed. Local verified provider-matching artifacts remain under
the ignored campaign `retained/` directory.

## Current correction

V4 remains preserved. V5 replaces unsupported `--auto-match` with eager query
matching: after a positive initial screen, it types `a`, expects the complete
`1/2` result count, selects `apple`, and checks exact output. V5 is materialized
but has not been launched. Next, rerun focused unit/contract/workflow checks,
commit the v4 failure evidence with v5, push, and inspect both native cells.

No local target runtime, owned PID or mounted volume remains.
