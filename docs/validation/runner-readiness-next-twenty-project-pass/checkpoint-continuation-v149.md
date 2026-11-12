# Runner readiness continuation checkpoint v149

## Campaign count

The audited total remains **17/30**. Pick is still unadmitted; its v9 native run failed E11 on both hosts. The exact failed-run artifacts, per-case report hashes, cleanup results and retained screens are recorded in the two v9 host receipts.

## Runner fix and private candidate

Commit `78252c770635ec429e63e4b618e9c319af89c343` is pushed to `work/p0-p2-implementation`. It adds mode-aware arrow-key encoding, a real-PTY regression, the Pick v10 long-list navigation contract and an rc.8 private-candidate pipeline. Local `go test ./...`, `go vet ./...`, the project-local Windows race script, focused PTY regression, Windows demo examples and 19 Python acceptance contract tests passed.

GitHub native candidate workflow run `43330369205` is pinned to that commit. The Linux job is running its source test/vet/race stage; macOS and Windows are queued. The v3 candidate declaration and packet finalizer are stored separately from the runner source commit so they cannot change the candidate bytes. The declaration records that the push-triggered job began before the declaration file was added. No external project scenario has run on rc.8.

The next gate is to verify all three native jobs, retrieve and hash each provider artifact, independently audit the source/test command identities and exact private archive bytes, then freeze rc.8 without transferring historical admissions. Only after that freeze should Pick v10 be materialized and the manual two-host workflow dispatched. Preserve each failed attempt; keep **17/30** until the full new-project and inherited gates close.
