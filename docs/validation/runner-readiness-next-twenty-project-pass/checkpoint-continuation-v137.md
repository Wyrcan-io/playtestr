# Runner readiness continuation checkpoint v137

Campaign remains **16/30 cumulative admitted** and **6/20 new-project admissions on v0.4.0-rc.6**. JOE has **20 final-qualified scenarios across two native cells and 480/480 audited ordinary passes**, but **0 source faults and 0 project admission credit**. Original-ten current-candidate requalification and campaign closure remain open.

## JOE final qualification audited

- Fresh attempt v6, workflow run `43036633466`, exact head `6d08e40a98c3f23dc99f841bb83fd99a99317255`. Linux amd64 and macOS arm64 each passed all 240 scenario repetitions, owned source cleanup, and storage checks.
- Independently downloaded Linux artifact `13864020534` (10,078,654 bytes, SHA-256 `b2cb870eb557897336a565f437132ce7e286c1889967b99ec9e5bb5894a868d4`) and macOS artifact `13864470241` (9,266,215 bytes, SHA-256 `ca43bbbcc6291e308033c53cff35174322321b0d902f254d67ecffda85f5c293`); local download hashes matched provider metadata.
- Full provider ZIP audit: `joe/final-qualification-artifact-audit-run43036633466-v1.json`; 480 receipts, reports, exact runner/target/source/build identities, workspaces, process cleanup, source restoration/removal and storage audited.
- v5 remains a preserved zero-launch preflight failure: `joe/scenario-attempt-v5-finished.json`. v6 is the passing attempt. The final auditor's repetition path bug and three rejected audit commands are retained in `joe/final-qualification-audit-invocations-v1.json`; 6 relevant auditor/source-map tests pass.

## Next: source fault calibration

- Three mutations are frozen in `joe/fault-declaration-v1.json` and individually hashed patch/source manifests in `joe/faults/`. A static readback against the pinned `5e00e262...` tarball verifies unique anchors and all before/after/patch hashes: `joe/fault-declaration-source-readback-v1.json`.
- Native Linux/macOS baseline, corrupted-source, and freshly reacquired/rebuilt recovery jobs are prepared in `.github/workflows/runner-readiness-next20-joe-fault-calibration.yml`; **18 required phase executions remain pending**. No JOE fault target has launched.
- Local validation: fault declaration preflight passed; 18 Python unit tests passed with 3 host-specific skips; workflow YAML parsed; `git diff --check` passed.
- Current local changes are scoped to JOE fault/builder/auditor tooling, declarations and ledger. Commit/push to `work/p0-p2-implementation` is already authorized. Preserve unrelated untracked files.
- After push, monitor all triggered workflows; independently retrieve and audit each host/fault artifact before credit. Then complete JOE oracle calibration/model controls and continue remaining new-project packages, first-ten current-candidate gates, public controls, installs/delivered-CI, fresh checkout, storage and final audit.
