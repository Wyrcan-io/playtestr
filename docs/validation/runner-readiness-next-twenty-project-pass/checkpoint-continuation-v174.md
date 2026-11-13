# Runner readiness continuation checkpoint v174

## Cumulative status

The cumulative ledger remains at **18/30 admissions** and **2/20 new projects**.
Percol has **0 admission credit**. JOE (rc.7) and fzy (rc.8) remain the only
admitted packages in this batch. The exact final candidate and original-ten
convergence gates remain open.

## Percol development attempt v1

Commit `080972d48821db9756d3134cf839492b95308afe` launched native development
run `43378432162` on Linux amd64 and macOS arm64 using exact `v0.4.0-rc.8`.
Both hosts built CPython 2.7.18, imported pinned Percol and six, and passed the
first two scenarios. Both then failed frozen N03 after its 20-second positive
screen wait: Percol's default string finder does substring matching, so the
invalid subsequence query `ct` displayed zero rows for `cart`. Both reports
confirm process-group exit and workspace cleanup. The first failure is retained
in `percol/development-attempt-v1.json`; provider digests and downloaded ZIP
hashes match. The partial outcomes remain in the attempt denominator and earn
no final-series or admission credit.

The attempt also exposed two cleanup misses. Python 2 wrote sixteen `.pyc` files
into the Percol source tree because the scenario environment omitted
`PYTHONDONTWRITEBYTECODE`; and CPython installed a `bin/python2-config` symlink
not yet in the verified alias inventory. The workflows preserved full evidence
artifacts and bounded campaign storage. The case-sensitive macOS build volume
detached successfully. No target source/runtime is present in the local active
tree; no process is owned or running locally.

## Frozen correction and next action

Scenario contract v1 remains unchanged after launch. Contract v2 uses the
substring query `art`, sets `PYTHONDONTWRITEBYTECODE=1` inside each target
specification, and removes the additional `python2-config` alias only after
resolving it inside the owned runtime tree. Its 20 specs, fixtures, declaration,
focused unit tests and verifier pass locally; no v2 Percol scenario has launched.

The checked-in local source-only acquisition is under
`artifacts/runner-readiness-next-twenty-project-pass/active/percol` and matches
the reviewed pin. The two first-run ZIPs are retained locally under the ignored
campaign `retained/` directory; they are not public documentation links. No PID
or temporary volume remains owned locally. Current native runner is
`v0.4.0-rc.8`; next action is commit and push the v2 correction, then inspect
both host attempts before changing any further contract or awarding credit.
