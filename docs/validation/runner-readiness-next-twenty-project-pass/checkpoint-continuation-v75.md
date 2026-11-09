# Continuation checkpoint v75

## Campaign count

Still **15/30**: five new projects credited; zero original-ten current-candidate requalifications. mg remains at zero project admission credit.

## mg evidence

The exact rc.6 N01 first-use pilot passed once on Linux x86_64 and macOS arm64 in run 42712723851; see `mg/pilot-n01-native-readback-v1.json`.

N02 edit-and-save had a preserved failed oracle attempt in run 42716663487: mg saved successfully but included the absolute file path in its confirmation, while the initial expectation required a basename. The corrected stable-prefix contract passed on both hosts in run 42717420876. Both retained ZIPs match provider digests, pass CRC, and their inner report and runner-log hashes match receipts. Each report has 12/12 steps passing, same-invocation state outcome `matched`, graceful target exit, and confirmed runner process-group cleanup. Hosted cleanup receipts report all owned workflow inputs absent.

The state report does not preserve saved file bytes/hash. Therefore N02 is development evidence only and does not qualify as an independently re-read exact-byte state oracle. Aggregate development attempts now retain the failure and retry in `mg/scenario-development-accounting-v2.json`; full artifacts/readback are in `mg/scenario-development-readback-v1.json`.

## Next work

Review the pinned mg source for N03 query-replace, create a distinct synthetic fixture and exact-byte oracle, update tests/workflow inputs, and run native Linux/macOS probes. Keep all failed attempts. Continue through eight normal and twelve edge workflows; then freeze only after independent saved-byte evidence, authoring, repetitions, fault calibration, host coverage and cleanup gates pass.
