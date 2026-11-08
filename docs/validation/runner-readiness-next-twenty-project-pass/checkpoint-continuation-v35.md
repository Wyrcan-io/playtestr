# Continuation checkpoint v35: 8 November 2026

Branch `work/p0-p2-implementation` was at pushed commit `807e038c654c93db651038404cb69cdea6b87ad8` for run `42483792833`. Four of the twenty new applications are admitted (14/30 cumulative). Taskell remains active and unadmitted.

## Run 42483792833

Ubuntu job `128741165456` and Intel Mac job `128741165191` both acquired the pinned Taskell source, passed all 250 upstream tests, built Taskell 1.11.4 and Playtestr, and passed the existing-task smoke. Both attempted all 20 candidate invocations: 19 passed and E12 failed on each host. The full reports, host/runner identities, and failure screens are curated under `taskell/first-use-attempts/42483792833-{linux,macos}/`; v30 binds all 40 report hashes and provider artifact IDs/digests. Every report hash was checked against its curated file.

E12 exited 0 and both process and workspace cleanup succeeded. Its exact board-byte assertion failed on both hosts: the directory was read-only, but `board.md` remained writable. The local fixture now applies mode 0444 to `board.md` before making the directory read-only; this correction has not yet run on either host. The next push is intended to trigger the paired native jobs.

The candidate batch failure skipped the recorder route. No candidate set freeze, native 20 x 2 x 12 series, fault/mutant/restored phases, calibration, maintenance/relocation, full audit, or Taskell admission credit exists. Other successful first routes remain exploratory observations only.

Storage checkpoint v33 passed at 2026-11-08T13:45:14.942446+00:00 with combined retained 2,147,351,121 bytes and 132,527 bytes observed headroom. Receipt SHA-256: d46073a047851de2211a8043ebee51e9dc7747c99ca7bf3602a34418ae26b1b6.

Next: commit and push v30, v33, v35, and the 0444 fixture correction; verify both hosted jobs and artifacts. If E12 passes with unchanged bytes and complete graceful cleanup, continue the recorder route and Taskell?s remaining qualification gates. Then continue the remaining 19 new project admissions. No issue, PR, discussion, release, or outreach mutation was performed.
