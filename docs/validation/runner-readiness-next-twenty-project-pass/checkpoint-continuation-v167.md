# Runner readiness continuation checkpoint v167

## Cumulative status

The campaign remains **17/30 admitted**. Fzy's final ordinary matrix has
independent evidence for 480/480 cases on Linux and macOS. Its three-fault
matrix is now independently audited. Fzy itself remains unadmitted.

## Fzy fault calibration closed

Workflow `43363053728` passed on Linux amd64 and macOS arm64. Each host ran
three declared faults in baseline, corrupted and restored phases: nine phases
per host, 18 total. Each phase acquired the exact pinned source, passed all 32
upstream tests on pristine source, ran the exact frozen rc.8 candidate against
one committed scenario, and passed cleanup. The corrupted phases were detected
at the expected categories and steps:

* F01, missing output newline: N01, `state_assertion_failure`, step 4.
* F02, no-op down navigation: N05, `state_assertion_failure`, step 6.
* F03, empty initial search query: N02, `state_assertion_failure`, step 4.

The host packets passed an independent bounded ZIP audit. It verified provider
byte counts and digests, each source archive and mutated source hash, pristine
and mutated binaries and build logs, the candidate install hashes, all 18
reports and event chains, nested identity manifests, the exact fault
classifications, per-phase source removal, and no remaining matching live
processes. The run receipt is `fzy/fault-calibration-run43363053728-v1.json`;
the readback is `fzy/fault-calibration-artifact-audit-v1.json`. Fzy receives no
admission credit from this one gate by itself.

## Next fzy gates

Complete the public authoring route, maintenance route, model controls, and
independent project/ledger admission review. Then continue the remaining
distinct project candidates and reconcile the original-ten work until 30
fully supported admissions are recorded.
