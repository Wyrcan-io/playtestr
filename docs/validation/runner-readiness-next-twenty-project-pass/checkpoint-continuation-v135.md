# Runner readiness continuation checkpoint v135

Campaign: **16/30 cumulative admitted**, **6/20 new projects on v0.4.0-rc.6**. Candidate new-project totals remain 120 scenarios, 12 native cells, 2,880 ordinary executions, 114 calibration phases and 19 distinct real faults. JOE has zero scenario and admission credit.

## JOE native build gate

- Exact source: `joe-editor/joe@3874898078005d1f5e519235401fab4fd428dd9b`, GPL-2.0. Source archive SHA-256 `5e00e2621225a304061c70903ef6490a700a4bbf1fa600c096b5bbb6746f2312`; all 388 archive entries and source-map records were bound to the hosted acquisition.
- Final native matrix run `43007089541` passed on `ubuntu-24.04` x86_64 and `macos-15` arm64. Both exact provider packet IDs, byte counts and GitHub SHA-256 digests are in `joe/native-build-readback-v1.json`; independent per-member readback is in the ignored raw receipt it references.
- Both hosts completed all seven bounded build/install commands, verified all logged-output hashes and reported no remaining owned process group. Linux tree: 1,037 files, 70,293,223 bytes. macOS tree: 1,037 files, 60,484,450 bytes. Both stayed below the 256 MiB temporary build-tree bound; hosted storage checks passed.
- Two earlier build workflow failures are retained. Run `43004813995` had prepared v1 records and exposed a verifier `NameError` plus missing macOS Autoconf. Run `43005769503` passed on macOS and built/installed Linux, then the initial 64 MiB verifier cap rejected Linux. That second workflow lacked immutable prelaunch records; the accounting omission is explicitly preserved in `joe/native-build-attempt-crosswalk-v1.json`, not backfilled. No run receives scenario or admission credit.
- JOE source remains active locally pending checked cleanup. Public authoring, first-use, scenario contract, saved-state oracle, faults, calibrations and model controls remain unstarted. No candidate total changes.

## Continue

Audit campaign storage, remove only the exact owned source tree after preserving its verified archive evidence, then prepare and freeze JOE's public route and scenarios. Keep every failure and the attempt-record gap visible. Final campaign gates, 30 total admissions, original-ten rc.6 requalification, delivered CI, final audits and complete cleanup remain open.
