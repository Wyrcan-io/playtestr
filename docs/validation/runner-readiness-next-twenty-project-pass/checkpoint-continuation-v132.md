# Runner readiness continuation checkpoint v132

Campaign remains **15/30 recorded admissions**. Exact rc.6 remains **5/20 new projects**, 100 scenarios, 10 native cells, 2,400 ordinary executions, 90 calibration executions and 15 real target faults. `mg` remains unadmitted. Current branch `work/p0-p2-implementation` is pushed through `a9d001db`.

## New audited mg evidence

- Hosted route run `42995560305` passed, artifact `13843836840` (900,794 bytes; SHA-256 `038ee1284eff95069d1b2a957cae36fb8bde971a917e2b079d6d3bd5dbab38be`), ZIP CRC passed. Independent audit is `mg/public-route-audit-run-42995560305-v1.json`.
- The audit verifies nine first-use route commands, six saved-state oracle cases, and seven separate technical operations: suite selection; manual spec/environment edit; JSON and offline HTML reports; passing v2 and v3 specs with a documented manual migration; selected suffix rerecord; and rerecorded ordinary pass. The target copy was hash-checked and removed. Each category is distinct in the audit; no project admission credit was created.
- Local focused route tests: 8 passed, one Unix-only permission test skipped on Windows. Python syntax and previous route-audit compatibility checks passed.
- Failed technical attempt `42995255664` reached the v2 ordinary pass, then stopped because the harness incorrectly required a v3-only invocation ID from a valid spec-v2 report. Its evidence remains retained. A fresh full attempt passed with the report-version-aware fix.
- Storage observation `93b1f066e146425cbed34e1cfbb4d719` passes all caps; combined retained 2,071,515,296 bytes, with 75,968,352 bytes of headroom. New curated bytes have 1,128,140 bytes of headroom. See `storage-checkpoint-v47.json`.

## Next work

Keep admission at 15/30. `mg` still lacks independent tampered-model controls matching the other current-candidate project packages; implement and audit these before considering its admission. Then continue remaining project packages sequentially. Campaign gates remain open for fifteen more new project packages, original-ten rc.6 requalification, control/archive refresh, two delivered-CI triplets, fresh-checkout and all-attempt audits, and final retention/cleanup/reporting. Human usability remains unmeasured.

Preserve unrelated untracked `.codex-go-cache/`, `.codex-test-tmp/`, `.runner-readiness-compaction-tmp/`, continuation v117/v46, and existing skim readbacks/model-control files. Preserve failed runs `42990561239` and `42995255664` with their artifacts. Do not run blanket cleanup.
