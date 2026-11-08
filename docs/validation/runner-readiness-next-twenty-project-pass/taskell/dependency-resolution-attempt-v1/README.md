# Superseded Taskell Linux dependency-resolution attempt

This is the exact bounded packet produced for run `42447675823` on
`ubuntu-24.04` before the workflow was corrected to use Stack's pinned global
package hints. Its 161-package output is preserved as an attempt and is not the
canonical cross-host graph. The later `dependency-resolution-v1` packets use
the corrected resolver command and match across Linux and macOS. Attempt IDs,
provider artifact digest and disposition are in
[`dependency-preflight-attempt-v5.json`](../dependency-preflight-attempt-v5.json).
