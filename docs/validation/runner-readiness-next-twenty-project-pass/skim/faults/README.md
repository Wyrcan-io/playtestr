# Skim source-fault attempts

The source-fault matrix is not qualified yet. `next20_skim_faults.py` declares
three bounded, local source mutations against the pinned Skim tree and requires
a corresponding frozen public case to fail after launching the target.
Successful detection will receive credit only from
`fault-matrix-v1.json`, emitted after all three cases, exact source restoration
and post-run provenance verification complete.

The v4-v6 spec variants preserve local harness attempts. The first variant had
an invalid relative mutant-binary path. The later variants fixed that path but
failed in Windows workspace setup with `expand native workspace path: Access is
denied`; all spec steps remained `not_run` and no target launched, so these
attempts count as neither target failures nor detected source faults. Raw
started/build/case reports are retained in the ignored campaign artifact tree.
The hosted Windows workflow runs v7 against GitHub's native temporary workspace
and uploads its complete per-fault evidence, including failures.
