# Continuation checkpoint v29 — 8 November 2026

Branch `work/p0-p2-implementation`; latest pushed native candidate source is
`40735055c65cf1e1e49b620b881778078223501b`. Four of twenty new projects are
admitted on rc.6 (14/30 cumulative); the campaign remains incomplete.

## Taskell evidence and next candidate

Pinned Taskell source is
`smallhadroncollider/taskell@a2df95f26762fc3e78d6f131cea7fc1f3b13bd47`
(151 primary blobs verified, BSD-3-Clause). Do not start another target
before Taskell's full test/fault/audit/cleanup requirements close.

Run `42467040351` passed the 250-test upstream suite, existing-task smoke,
creation, duplicate, and public recorder review/fresh replay/export/ordinary
test route on Linux and Intel macOS. Mac's first attempt hit Stack 3.11.1
HTTP 504 and was rerun in isolation; the rerun passed. Creation passed 12/12,
matched exact `board-basic.md` bytes, exited 0 and confirmed process/workspace
cleanup. Duplicate passed 7/7, matched exact `board.md` bytes, exited 0 and
confirmed cleanup. Exact host/artifact/binary/spec/report hashes are in
`taskell/build-attempt-v24.json` and its two curated evidence directories.
These are single observations, not repeated native series or admission.

The candidate set still has only N01-N03 defined. N02's observed route enters
INSERT with `a`, types the task and presses Enter, then uses Escape to finish
Taskell's automatically created blank insert row before `q`. N03's duplicate
case passed on both hosts with unchanged neighboring rows and exact bytes.
The authored catalog remains unfrozen.

N04 (rename one selected task) is now prepared at
`taskell/first-use-v1/taskell-n04-rename-task.json`. The fixture has a uniquely
named `Rename me` row with preserved neighbors; it selects that row, enters
edit, sends nine Backspace keys to clear its end-positioned cursor field,
types `Renamed task`, presses Enter and Escape, quits normally, then checks
exact serialized bytes. The candidate is source-grounded in the pinned
`startEdit`, `textToField`, and Backspace field handler, but it has not yet
run on either native host.

The hosted scenario stage is being changed to enumerate every
`taskell-*.json` candidate except the already separate existing-task smoke,
run each in its own report/artifact directory, continue to later cases after
any one failure, and fail the overall step if any candidate fails. This
preserves multi-case diagnostics in one expensive native build. The updated
workflow and N04 are pending validation/push in the next commit.

## Remaining Taskell gates

Complete N04-N08 and E01-E12 with exact screens/bytes, host limits, timeouts,
and failure handling. Freeze the complete catalog only after all candidate
routes have passed on both native hosts and every declared risk pair is
bounded. Then execute 20 cases x 2 hosts x 12 repetitions with order/leakage
checks, three real source mutations with baseline/mutant/restored phases on
both hosts, calibration, maintenance, relocation, original-ten closure, all
audits, final candidate and checked cleanup. No Taskell native series,
fault-calibration or admission credit exists yet.

Storage checkpoint v20 passed after the v20-v24 Taskell evidence set with
151,107 bytes combined-retained headroom and 14,336,408 bytes new curated
headroom. Measure again before the next substantial retained packet; preserve
all failures and the historical storage archive.

No PR, issue, discussion, release or outreach mutation was performed or is
authorized. Commit/push and standard hosted validation are authorized.
