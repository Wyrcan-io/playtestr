# Continuation checkpoint v34: 8 November 2026

Branch `work/p0-p2-implementation` was at pushed commit `581aa12423bf2d01da612808e2f99f3c80de6f06` for run `42481721587`. Four of the twenty new applications are admitted (14/30 cumulative). Taskell remains active and unadmitted.

## Run 42481721587

Ubuntu job `128734901147` and Intel Mac job `128734901336` both acquired the pinned Taskell source, passed all 250 upstream tests, built Taskell 1.11.4 and Playtestr, and passed the existing-task smoke. Both attempted all 20 candidate invocations: 19 passed and E12 failed on each host. E10 now passes on both after sending Enter to the `(Y/n)` prompt. All same-run reports, host/runner identities, and failure screens are curated under `taskell/first-use-attempts/42481721587-{linux,macos}/`; v29 binds the report hashes and provider artifact IDs/digests.

E12's directory-level write denial worked, but the candidate did not send `q`, leaving Taskell open until forced process-group cleanup (exit 137). The shell trap therefore did not restore permissions; workspace cleanup correctly reported permission denied and retained that isolated workspace on each ephemeral host. This is a candidate interaction and cleanup miss. The local correction now sends `q`, expects a clean exit 0, and checks that `board.md` bytes remain unchanged; it has not been run yet.

The candidate batch failure skipped the public recorder route. No candidate set freeze, native 20 x 2 x 12 series, fault/mutant/restored phases, calibration, maintenance/relocation, full audit, or Taskell admission credit exists. Other successful first routes are exploratory observations only.

Storage checkpoint v32 passed at 2026-11-08T13:09:59.358174Z with combined retained 2,147,349,949 bytes and 133,699 bytes observed headroom. Receipt SHA-256: `eb08f01b6afc101d1e65b006bcd4163a81611fb02a5df82d0d35499b41f05bee`.

Next: validate the E12 correction, commit/push v29, v32, and v34 with the spec change, and execute both hosted native jobs again. Inspect the exact same-run screen, state bytes, process exit, and cleanup before freezing. Continue the full Taskell gates and then the remaining 19 project admissions. No issue, PR, discussion, release, or outreach mutation was performed.
