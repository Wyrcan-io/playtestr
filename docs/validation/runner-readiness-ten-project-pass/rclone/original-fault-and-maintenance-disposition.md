# Original Linux faults and maintenance disposition

Run 39328483971 at e9b90a1 executed the committed native twenty-case profile
and all three actual compiled source faults. `original-source-faults.json`
independently verifies the changed source catalogs, actual compiler and runner
hashes, changed executable hashes, unchanged public contracts, intended failure
categories, same-execution file/entry rejection and exact original executable
restoration. Source/runtime cleanup passed. F03 is consumed as the original
held-out Linux fault; later executions are replicas.

The workflow failed afterward in maintenance, while rendering the deliberate
file-change report. The helper supplied an absolute artifact directory, so the
machine report contained absolute evidence references. The offline renderer
correctly rejected those references under its confinement policy. That failure
does not invalidate the preceding compiled fault observations or establish a
production fix.

The native contract, fault and maintenance helpers now pass workspace-relative
report and artifact paths, following the previously verified public route.
The renderer policy and production Go remain unchanged. The corrected
maintenance flow must still execute successfully. Further Linux fault runs
are replicas; Windows replicas follow the committed original evidence. No
Rclone development or final-archive admission is granted by this disposition.
