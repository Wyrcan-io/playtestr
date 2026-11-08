# Continuation checkpoint v45: 8 November 2026

Branch `work/p0-p2-implementation` is pushed at `9967b0d6`. The exact rc.6
campaign ledger remains four of twenty new admissions (14/30 cumulative);
original-ten current-candidate requalification remains zero. Do not claim 30/30.

## Skim exact-candidate series audit

Run `42506300345` on commit `7d66abef35d9a1e8bae63cd2a5bb20e54755ebe9`
completed on standard hosted Linux and Windows. Both provider artifact digests
were independently matched after in-memory retrieval. All 12 batches per host
were rehashed and checked for 20/20 cases, all 240 per-host outcome records link
to matching report and finished-receipt SHA-256 values, runner exits are zero,
and per-outcome workspace cleanup receipts are true. Each host has three distinct
source mutations detected, three passing baselines, three restored recoveries,
and verified source/target restoration. Full details are recorded in
`skim/artifact-retrieval-readback-v8.json`.

This completes only the exact-candidate native series and fault packet audit.
Skim has not been admitted. Its public first-use/authoring, maintenance,
relocation, delivered-CI, whole-control applicability, current storage, complete
cleanup, and final campaign closure gates remain outstanding. Keep all known
Windows directional-navigation and raw NUL-framing boundaries explicit.

## Taskell native dependency correction

Taskell run `42509718525` on `dd0c41a4` failed on macOS while extracting the
signed MacPorts libedit package: its inert man-page symlink
`opt/local/share/man/man3/el_tok_end.3.gz` was rejected. Linux was still running;
the paired macOS fault job had the same extraction failure. The scoped fix in
`9967b0d6` validates and skips relative documentation links without
materializing them and refuses escaping links. Local helper tests pass 10 tests
with two expected Windows native-symlink skips; Python compilation and diff
checks pass. Exact-candidate and fault workflows were dispatched by the push;
run IDs `42510913121` and `42510913142` were pending/in progress at checkpoint.
No Taskell credit is claimed.

The Windows staged-native harness run at `9967b0d6`, `42510913429`, passed.
Untracked `.codex-go-cache/` and `.codex-test-tmp/` remain protected and are
untouched. Continue monitoring Taskell, independently audit its real native
artifacts on success, finish Skim's remaining public-route gates, then proceed
sequentially through the remaining selected projects, original-ten transfer,
old migrations, controls, storage, retention and final audits.
