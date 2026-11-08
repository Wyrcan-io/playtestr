# Taskell progress checkpoint v2 ? 8 November 2026

**Campaign count:** 4/20 newly admitted; 14/30 cumulative. **Taskell:** active, zero admission credit.

- Pinned target: `smallhadroncollider/taskell@a2df95f26762fc3e78d6f131cea7fc1f3b13bd47`, 151 source files, BSD-3-Clause.
- Exploratory first-use run `42489015452`: Linux amd64 and Intel macOS x86-64 each passed upstream 250 tests, source/runner builds, N01 smoke, all 20 first-use candidate contracts, and reviewed recorder `/review` ? fresh `/replay` ? `/save` ? ordinary test. Exact reports, screens, recorder transcript, binary IDs and artifact digests are retained in build attempt v32 and paired compact packets. These do not qualify the frozen rc.6 candidate or repeated series.
- Frozen catalog: 8 normal workflows, 12 edge families, 21 invocation contracts (E11 malformed and recovery split); case hashes and 21 fixture-file hashes are bound in `host-contracts/`. The source-built first-use specs match the corresponding run-v32 spec hashes on both exploratory hosts.
- Exact candidate: private Playtestr v0.4.0-rc.6; Darwin arm64 archive SHA-256 `132152710ade2c01cac7558f75212121f01af8ab02c5735dc9c7de1c33dbe625` (verified in the active input area). Frozen final declaration requires 504 ordinary invocations (21 ? 12 ? 2 hosts) and 18 source-fault calibration invocations.
- Prepared native workflow uses standard GitHub-hosted Ubuntu 24.04 amd64 and macOS 15 arm64, obtains exact private archives from audited run artifacts, rebuilds and tests pinned Taskell, and records batch reports. It has not yet been pushed or run.
- Updated `next20_jrnl_final.py` verifies candidate, scenario, fixture and runtime lock hashes; supports PATH-launched native commands; does not retry cases; records all results and stops further launches if cleanup cannot be confirmed.
- Local checks passed: all 20 exploratory spec hashes matched both hosts, 21 frozen spec/fixture structure checks, exact arm64 archive digest, Python compile, workflow YAML parse and `git diff --check`. Native exact-candidate runs, source fault phases, cleanup audit, compatibility/maintenance, independent audit and admission remain outstanding.

Next: commit/push the scoped work under existing authorization, inspect native workflow execution, then perform all source fault, audit and cleanup gates. Continue the remaining sixteen new projects and candidate-current review of the original ten. Do not claim 30/30 until every gate is evidenced.
