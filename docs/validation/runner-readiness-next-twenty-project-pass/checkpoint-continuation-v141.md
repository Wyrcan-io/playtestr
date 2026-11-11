# Runner readiness continuation checkpoint v141

## Project count

The last campaign checkpoint remains **16/30 cumulative admissions** and **6/20 next-project admissions**; this continuation adds **zero** project or fault credit. The latest `projects.json` snapshot is not synchronized with that checkpoint: its admission-subject and candidate counters still reflect rc.5/rc.6 records, including restoration-rebuild gates that were resolved later. Reconcile those records against immutable admission and gate-resolution receipts before the next campaign-wide count update; do not infer admission totals from ordinary-execution counters.

## rc.7 exact-candidate preparation

Candidate `v0.4.0-rc.7` (`native-exit-v2`) is frozen from successful, independently audited Linux amd64, macOS arm64, and Windows amd64 workflow run `43056391377`, source revision `df7fd54375e411542ce899c0e05b19db643ba64b`. The earlier run `43055248167` remains preserved as a zero-launch checkout-pin failure. No project/scenario/fault admission transfers from rc.6.

JOE v2's rc.6 source-fault run `43054584381` completed and its six provider artifacts were independently audited: three detected faults across two hosts, 18/18 phases, six baseline passes, six expected contract rejections, six restored recovery passes, and confirmed target/process cleanup. This is historical rc.6 evidence only and earns no rc.7 calibration or project admission credit.

JOE is now predeclared against the exact rc.7 archives. New scenario declaration v4 and attempt v7 bind the 20 scenarios x 12 repetitions on Linux/macOS; development attempt v8 binds 20 x 1. Fault declaration v3 preserves the same three source mutations and binds scenario declaration v4. Public-route declaration v5 binds the rc.7 host archive/binary hashes. The scenario, fault, public-route, and final-qualification helpers/auditors support explicit `native-exit-v2` selection while retaining rc.6 defaults for historical readback. Thirteen focused JOE tests, Python compilation, YAML parsing for all six JOE workflows, rc.7 scenario/fault declaration preflights, and `git diff --check` pass.

The four native JOE workflows have not yet run against rc.7. Next: commit/push this scoped preparation, audit the resulting native artifacts, finish JOE oracle/model/admission gates, reconcile the ledger from receipts, then continue the remaining selected projects and original-ten/global candidate closure. JOE remains unadmitted.
