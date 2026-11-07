# Skim source-fault attempts

The source-development fault matrix completed in hosted run `41827379783` on
Windows. All three bounded mutations were detected by their frozen public cases
after target launch, the case-owned processes and workspaces were cleaned, and
the pinned source was restored and reverified. Its 28-member evidence archive
and every member hash were independently checked; see
[`../source-development-readback-v2.json`](../source-development-readback-v2.json).
These are development faults. They do not count as Skim's final candidate source
faults; the exact current candidate must repeat its own required calibration
series before admission.

The v4-v6 spec variants preserve local harness attempts. The first variant had
an invalid relative mutant-binary path. The later variants fixed that path but
failed in Windows workspace setup with `expand native workspace path: Access is
denied`; all spec steps remained `not_run` and no target launched, so these
attempts count as neither target failures nor detected source faults. Raw
started/build/case reports are retained in the ignored campaign artifact tree.
The hosted Windows workflow runs v7 against GitHub's native temporary workspace
and uploads its complete per-fault evidence, including failures.
