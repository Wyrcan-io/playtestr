# Continuation checkpoint v58: Taskell native rerun after route and macOS preflight failures

Date: 9 November 2026. The campaign remains **5/20 new-project admissions on
rc.6, 15/30 cumulative**. Taskell is project six and remains unadmitted. The
original ten remain 0/10 requalified on rc.6.

## Exact candidate attempt

Commit `d7ffbd2c8f96a96a12001bae965ff52729c04ba2` is pushed on
`work/p0-p2-implementation`. Hosted run `42546285446` built Taskell after
restoring its frozen GHC 9.0.2 toolchain on both native hosts. Both jobs then
failed the new public authoring route at the helper's incorrect hard-coded
saved-board byte expectation, before any of the twelve candidate batches.
The Linux artifact is 11,751,051 bytes with provider SHA-256
`3505a09d05f79aa1b2342f1d365345f119bdfe0b82b1f02445206b0e40a814f8`; the
macOS ARM64 artifact is 305,309,481 bytes with provider SHA-256
`9694f60956eac77dfbf7a8552b4ca9e2689175f0d1705b22366b48015b5a94f0`. Provider
metadata is recorded in [attempt v40](taskell/final-series-attempts-v40.json).
The local helper now derives its expected board bytes from the frozen public
Taskell scenario and constrains selected maintenance to the intended text,
screen expectation and saved-state bytes. No candidate batch or admission
credit is claimed from run `42546285446`.

## Source-fault attempt

Hosted run `42546285402` passed all nine declared Linux source-fault phases,
checked target cleanup and uploaded artifact `13644149101` (11,771,188 bytes,
provider SHA-256
`462fb98939ca74459bd2b890fb1ac53e169a53bfafba4c48c63c1b60f53e7b3e`). The
macOS ARM64 preflight unit test failed because the test expected `/tmp/...`
while `Path.resolve()` correctly returned `/private/tmp/...`; no macOS target
was acquired or launched. Its cleanup and artifact-preservation steps also
failed because preflight had not created the target/evidence tree. The test now
compares against the resolved temporary path. [Fault attempt v7](taskell/fault-attempt-v7.json)
preserves this result with zero admission credit. Neither large workflow ZIP
was retained locally; provider metadata is evidence only, not independent
archive-member readback.

## Local successor state and next actions

The focused Taskell suite passed 25 tests with three expected Windows symlink
capability skips. Python compilation, `git diff --check`, JSON validation and
both Taskell workflow YAML parses passed. Pending tracked changes are the
frozen-case route oracle/maintenance assertions and the resolved-path macOS
test expectation, plus the two zero-credit receipts and this checkpoint.
Unrelated local cache and Skim draft files remain untouched and unstaged.

Next, commit and push only the reviewed Taskell source, receipts, checkpoint
and accidental Git Town cancellation receipt. Monitor the new exact and
source-fault native workflows serially. Require the public route and all twelve
candidate batches on both Linux and macOS, all nine fault phases on both hosts,
and checked cleanup. Retrieve and independently audit bounded artifact members
without retaining the large provider ZIPs locally. Taskell admission remains
open until those checks and the complete per-project packet audit pass. Do not
acquire project seven (`mg`) before Taskell is closed and cleaned.

The accidental Git Town workflow triggered by a broad path filter was canceled
before its scenario suite and has a separate zero-credit cancellation receipt.
Do not rerun Git Town as part of this Taskell transition. There is no release,
tag, PR, issue, discussion, outreach, or paid infrastructure action authorized.

No 30/30 completion claim is made. Human usability remains unmeasured, and paid
admissions remain zero.
