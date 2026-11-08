# Taskell dependency resolution v1

Run `42448195583` resolved the pinned Stack graph on GitHub-hosted
`ubuntu-24.04` x86-64 and `macos-15` arm64. Each native packet contains the
source provenance, project manifest and Stack lock inputs, exact Stackage
snapshot, full JSON dependency list and DOT graph, and a host manifest with
SHA-256 hashes for every packet file.

Both packets list 158 packages. Their package names, versions, licenses,
external source locations and dependency edges match. The only JSON hash
difference is the machine-specific `file://` URI for the checked-out local
Taskell source. ZIP digests and run/job IDs are in
[`dependency-preflight-attempt-v7.json`](../dependency-preflight-attempt-v7.json).

This stage only resolves dependencies. It does not build or launch Taskell and
does not prove a terminal workflow or project admission.
