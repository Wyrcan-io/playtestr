# R2 — Verify the installation experience

Status: planned. Depends on R1. Product outcome: a new user downloads Playtestr and gets a useful result using only the published instructions.

## User and task

A CLI author has an existing application, wants a smoke test, and should not need Go, knowledge of Playtestr internals, or access to the maintainer's checkout. The task ends when the author can run a passing test, recognize an intentional failure, and find its evidence.

Internal release extraction is a prerequisite. This milestone tests the actual download links, documentation, permissions, PATH setup, and missing-prerequisite messages after publication.

## Test environments

Use Linux amd64, macOS arm64, and Windows amd64 as separate rows. Record OS version, architecture, shell, archive, checksum, runner version, target version, and whether any tool was already installed. Use a fresh directory and PATH that cannot accidentally select `bin/playtestr` from the source checkout. A native CI VM helps automate checks; it does not replace the human walkthrough.

Test with Go absent from the execution path for the binary-only route. An existing target may need its own runtime; record that separately. Exercise the optional source/demo route independently, with its documented Go prerequisite.

## Checkpoint 1 — Write the walkthrough protocol

Before observing participants, write the exact instructions and expected checkpoints:

1. Choose the matching archive from the prerelease.
2. Download archive and checksum, verify locally, and extract.
3. Invoke the extracted binary by its explicit path and check its version.
4. Optionally add its directory to PATH using shell-appropriate instructions.
5. Create one small spec for a known trusted installed command and run it.
6. Change an assertion deliberately, rerun, and find the JSON report/final screen.
7. Restore the assertion and rerun successfully.
8. Remove the installation directory and any explicitly created test data.

Acceptance: the protocol needs no repository-internal scripts or unmentioned dependencies. Choose harmless target commands per host; do not assume identical shell built-ins are directly executable on every platform.

## Checkpoint 2 — Automate the public-asset smoke test

Implement a bounded native check of the published archive URL, integrity, extraction, permissions, version, and successful/failed execution. Place target fixtures outside the Playtestr build directory and identify them explicitly. Run in a temporary directory with spaces to catch path quoting problems.

Assert exact runner exit status from the downloaded executable, not from `go run`. Check that report entries identify the requested spec, failure category, and correct evidence paths. Verify a second successful invocation cannot be confused with stale evidence from the earlier failing run; document current behavior or fix release-blocking ambiguity.

Acceptance: all three advertised targets pass using downloaded bytes. Unsupported targets receive a clear explanation rather than an accidental fallback binary.

## Checkpoint 3 — Observe an unassisted walkthrough

Ask at least two consenting people unfamiliar with the implementation to attempt the instructions. Prefer different operating systems. Record assistance, failed steps, error messages, and elapsed time to first pass. Do not send invitations on the user's behalf without outreach authorization.

Use a target of roughly ten minutes to first pass once prerequisites are present as an onboarding goal, not a performance claim. If a participant takes longer, identify the obstacle rather than blaming the participant or excluding the result. Separate download time, prerequisite installation, and test-authoring time.

Acceptance: at least two fresh-user attempts are recorded; any maintainer assistance is visible. Each can intentionally cause a failure and locate evidence without hidden instructions.

## Checkpoint 4 — Repair and retest the failed step

Classify each issue as documentation, packaging, platform behavior, target prerequisite, or runner behavior. Fix the smallest source of friction. If only a live web instruction changes, retest that route. If archive contents or binaries change, generate a new candidate version and repeat integrity and runtime checks for those bytes.

Do not overwrite a published candidate in place to make walkthrough notes appear cleaner. Track the version tested by each person.

Acceptance: critical installation paths have no unresolved blocker. Nonblocking usability issues have a reproduction and a clear follow-up owner.

## Required acceptance cases

| Case | Evidence required |
| --- | --- |
| Correct host archive | Explicit-path invocation prints the expected candidate version. |
| Integrity mismatch | Instructions stop before execution; a damaged archive is not treated as installed. |
| Missing Go | Binary-only first test still works. |
| Missing target | Actionable launch failure; no misleading passing result. |
| Space-containing path | Runner and spec paths are handled correctly in the documented shell. |
| Valid JSON, unsupported spec version | Target never starts and migration guidance is visible. |
| Expected failure | Exact exit code 1; useful screen and machine report can be located. |
| Ctrl+C | Cancellation code and cleanup behavior match the documented contract. |
| No write permission for report | Nonzero result identifies the write problem without claiming a saved file. |
| Uninstall | Removal affects only the explicitly installed files and walkthrough data. |

## Evidence template

Record participant alias/consent, host, shell, immutable download URL, archive hash, runner version, target/runtime version, start/end times, failed step, assistance given, and links to sanitized evidence. Exclude credentials and personal paths where they are unnecessary. No usage analytics service is needed.

## Definition of done

- [ ] All three native public-download checks pass for the candidate under consideration.
- [ ] At least two independent walkthroughs completed, including intentional failure diagnosis.
- [ ] No unresolved installation blocker remains on an advertised target.
- [ ] Documentation distinguishes binary installation from building a demo/target.
- [ ] R3 receives the exact instructions and known friction; R4 receives candidate-specific evidence.

A green build pipeline alone cannot close this milestone. If participants are unavailable, record the outstanding human check and continue only independent preparation work.
