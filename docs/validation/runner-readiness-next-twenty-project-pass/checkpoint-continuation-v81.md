# Runner readiness continuation checkpoint v81

Campaign status remains **15/30 project admissions**. The five new project admissions recorded on rc.6 and 10 original projects pending requalification are unchanged. mg has zero admission credit.

## mg N05 native attempts

Exact target pin `2209e2087eab34ffceb6bfaa0d62f9e4c36e3c66`, frozen candidate `v0.4.0-rc.6`. N01 first-use and N02/N03/N04 pass on Linux/macOS as development probes only. N02-N05 counters through the latest run: 40 host attempts, 30 passed and 10 failed (the failures are preserved; N05 has no passing host yet).

N05 attempt 1 (`42722834841`) tried undoing an insertion. The first undo passed; the second reported ?No further undo information? on Linux and macOS. See `mg/n05-first-attempt-readback-v1.json`.

N05 attempt 2 (`42774674956`, commit `3d4fc164d1a2b84d1880d6bcf1e652611d389fba`) changed to deletion. Both hosts deleted the suffix and the first undo restored it. A second undo cleared the modified state without changing text; step 20 expecting redo timed out on both hosts. Targets were force-stopped and confirmed exited, workflow inputs removed, and both 41-member retained ZIPs pass CRC. See `mg/n05-second-attempt-readback-v1.json`.

The exact pinned implementation records a MODIFIED marker and undo clears `BFCHG` while consuming it. The third N05 revision now expects: initial `seed changed`, delete suffix -> `seed`, first undo -> `seed changed`, next undo -> still `seed changed` (modified marker), third undo -> `seed` (redo). This public contract and local contract test have not yet been committed or run natively.

Next: validate corrected contract locally, commit/push with preserved attempt-2 evidence/accounting, run the native Linux/macOS workflow, inspect both screens and exact state outcomes, retain and CRC-check provider artifacts, update all counters and checkpoint. Do not claim N05 pass or mg admission before evidence.
