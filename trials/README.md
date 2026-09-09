# Real-application technical trials

This directory records reproducible, operator-run compatibility trials. The target names identify tested software and versions; they do not imply maintainer participation, endorsement, or adoption.

The pinned release inputs are in [`manifest.json`](manifest.json). The reviewed September 2026 results are in [`docs/trials/technical-trial-2026-09.md`](../docs/trials/technical-trial-2026-09.md). Raw terminal screens, kubeconfigs, local paths, contact records, target logs, and attempt reports stay under ignored `.trial-private/` because a global Docker or Kubernetes view can reveal unrelated local resource names.

Every scenario follows four phases:

1. Create a synthetic, campaign-owned fixture.
2. Drive the real TUI through a native Playtestr process.
3. Check the resulting Git, Docker, or Kubernetes state independently.
4. Remove only resources whose recorded identity and ownership match the fixture.

Rendered text alone is insufficient for a mutating workflow. A static panel title, retained log line, annotation, or generated resource name can survive after the intended action fails. The external oracle is part of the result, and an oracle failure makes the overall scenario fail even when Playtestr reports that its screen assertions passed.

Reusable workflow boundaries and target-specific oracle requirements are documented in [`recipes.md`](recipes.md). The Windows harness at [`scripts/trials/run-trial.ps1`](../scripts/trials/run-trial.ps1) preserves the runner and oracle outcomes separately and fails overall when either fails. Resource setup remains operator-controlled because Docker endpoints and Kubernetes contexts must be supplied explicitly.
