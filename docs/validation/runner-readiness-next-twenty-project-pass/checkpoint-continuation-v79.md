# Continuation checkpoint v79

## Campaign count

**15/30.** Five new-project admissions are credited; zero original-ten projects have current-candidate requalification. mg remains unadmitted.

## mg scenario probes

N01 first-use passed on Linux/macOS. N02 edit/save, N03 query-replace and N04 cut/yank each now have a passing development probe on Linux x86_64 and macOS arm64. N04 corrected run 42721990744 passed all 26 steps on both hosts, including the visible moved text and same-invocation saved-state assertion. Provider digest, local retained ZIP, candidate/target/report/log identities and cleanup are in `mg/n04-native-readback-v1.json`.

First failures remain preserved: N02 confirmation basename mismatch, N03 invisible prompt-space mismatch and N04 missing separator before yank. Their bounded cleanups and artifacts remain linked from `mg/scenario-development-accounting-v6.json`. Reports assert exact expected state but do not preserve actual bytes, so separate exact-byte readback is still open.

Development scenario attempts across N02?N04 total 24 host executions (18 passed, 6 failed); N01 pilot counts are separate. No ordinary qualification executions, scenario matrix, fault calibrations, or mg admission credit have been earned.

## Next work

Review N05 undo/redo against pinned source; create a distinct fixture and screen/state oracle; add it to the same bounded native workflow; preserve and diagnose first attempts. Continue N05?N20 before beginning qualification repetitions and fault runs.
