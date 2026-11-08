# Taskell progress checkpoint v1

Original checkpoint observed at `50bdca22990180da5da2fc1bfba305e3d99f65de`;
continued on branch `work/p0-p2-implementation` through `e3bdaa0dfdddc964c4af729768728e1f077320e0`.

## Campaign position

- New project admissions: **4/20**. Taskell is the next active target and has **no admission credit** yet.
- One local target tree is active under `artifacts/runner-readiness-next-twenty-project-pass/active/taskell`; do not acquire another application until Taskell retention and checked cleanup close.
- Taskell pin: `smallhadroncollider/taskell@a2df95f26762fc3e78d6f131cea7fc1f3b13bd47`; 151 primary source blobs verified. License is BSD-3-Clause; `.bin/build` and `.bin/analytics` remain excluded.
- Hosted native dependency resolution passed on Ubuntu 24.04 x86-64 and macOS 15 arm64 (run `42448195583`); both packets list 158 dependencies and compare equal except for the host-local source URI. Exact packets and artifact digests are retained under `dependency-resolution-v1/`.
- Superseded Linux resolution packet (161 packages) is retained separately under `dependency-resolution-attempt-v1/`.
- Run `42448622006`: Ubuntu built Taskell and all 250 upstream tests passed, then an unsupported `--version` invocation was interpreted as a board path; macOS Intel stopped before tests because the workflow queried standalone `ghc` although it was intentionally absent. Preserved in `build-attempt-v1.json`.

## Active hosted work

All jobs use standard GitHub-hosted runners. Do not count an in-progress job as evidence.

| Run | Commit | State / current step |
| --- | --- | --- |
| `42448762334` | `2e099a291f008a64ad25ced9149bfa29d16a5bfe` | Ubuntu failed after tests at `--version`; macOS Intel still in Stack build/test |
| `42448946195` | `9290862f73512c518b0596a75b5cd0be5d511313` | Both hosts still in Stack build/test; includes the authored smoke case, but its earlier `--version` check is still wrong |
| `42449293721` | `92447ca687e17f9e7f286402495795324f0fa826` | Both hosts still in Stack build/test; uses documented `-v` and the authored smoke case |
| `42449665350` | `50bdca22990180da5da2fc1bfba305e3d99f65de` | Both hosts still in Stack build/test; includes the no-JSON recorder first-use attempt and retains its review transcript |

Final run `42449665350` job IDs: macOS Intel `128635972163`, Ubuntu `128635972428`.
Its recorder transcript is not yet available. The current route must first
complete and preserve `/review` output; inspect it before producing a reviewed
export/replay attempt. The authored JSON smoke is separate and is not no-JSON
first-route evidence.

## Storage and next work

Fresh `next20_storage.py taskell` observation passed: raw 1,997,864,068 bytes;
combined raw 3,906,572,640; combined retained 2,147,480,504 of 2,147,483,648
(3,144 bytes observed headroom before this storage receipt); new curated
11,680,390; combined curated 23,336,634. Downloaded dependency extraction
directories were removed from campaign `tmp` after complete packets were
retained under docs. Avoid adding raw evidence until storage is measured again.

Next: poll the four runs; preserve every host's actual result; retrieve the
successful build packets and compare binary/report hashes; inspect the
authored smoke report; read the recorder review transcript; only then freeze
the first useful scenario and rerun the public recorder route through
`/review`, fresh `/replay`, `/save`, and ordinary `playtestr test`. Continue
Taskell's 8-normal/12-edge declaration, three real source faults, full native
cells/calibration, final candidate qualification, cleanup and admission audit.

## 2026-11-08 continuation

The four-run table above is historical and superseded by these receipts. Run
`42449961171` passed the Linux upstream suite (250 tests) and built Taskell and
Playtestr, but the authored smoke was rejected prelaunch for named key `q`;
artifact `13604999973` and digest are in `build-attempt-v5.json`. Its macOS
Intel job was still running when that immutable receipt was recorded. The case now
uses text input for `q`. Commit `e3bdaa0dfdddc964c4af729768728e1f077320e0`
was pushed, triggering corrected Linux/macOS Intel run `42450896413`. At the
latest poll, Linux was in upstream tests and macOS in toolchain setup. Continue
monitoring, retain and inspect both native artifacts, then complete the no-JSON
recorder route before designing/freezing the 20+12 scenarios. Taskell has zero
admission credit; overall new admissions remain 4/20.

Run `42450896413` subsequently failed Ubuntu before target launch because the
smoke fixture path named a missing directory; its immutable failure is
`build-attempt-v7.json`. The next workflow run `42451645308` began with pinned
Go setup on macOS and upstream tests on Linux, but used the pre-correction
fixture. The smoke now uses the actual `first-use-v1/fixtures/board-basic.md`
path/name, and the workflow watches these inputs. This corrected declaration
is pushed in the next commit; monitor its successor run before proceeding.

Commit `2144fd69` pushed the corrected fixture path/name, expanded workflow
path filters to include first-use inputs, and retained `build-attempt-v7.json`.
Run `42451800719` is the first run with both this fixture correction and pinned
Go setup; its Linux and Intel macOS jobs were in upstream tests at last poll.
The intermediate Go-enabled run `42451645308` failed before target launch on
the old fixture path; Linux artifact receipt is `build-attempt-v8.json`. Keep
this attempt separate and continue monitoring the two-host run.

Run `42450896413` has now completed on both hosts. Its macOS Intel lane passed
all 250 upstream tests and built Taskell, but lacked Go before Playtestr build;
the Linux lane failed on fixture setup. Both exact outcomes and artifact
digests are in `build-attempt-v9.json`. Run `42451800719` is still the first
workflow carrying both corrections; at the latest poll its two jobs are in
the pinned Stack test stage.

The Linux leg of run `42451800719` completed with 250 upstream tests and both
binary builds successful, but failed workspace setup: `workspace.fixture` is
spec-relative, so the repository-prefixed path was incorrect. Its receipt is
`build-attempt-v10.json`. The case now uses `fixtures`, relative to its
owning spec directory. The run's macOS result remains open; a new push will
exercise the corrected path and setup on both hosts.

Run `42451645308` later completed on both hosts. Linux and Intel macOS each
passed all 250 upstream tests, built the target and Playtestr, and configured
Go 1.25.0, then both failed before target launch on the old fixture path.
Full receipt `build-attempt-v11.json` records both artifact digests. Corrected
spec-relative fixture run `42452701639` is the active qualification attempt;
its jobs remain in pinned upstream tests at latest observation.

Run `42451800719` subsequently completed with both native builds, 250-test
upstream suites and Go setup successful, but both smoke cases still failed
before target launch because the fixture path included a repository prefix.
Receipt `build-attempt-v12.json` records each artifact. The corrected path is
in source `6a18fb07`, run `42452701639`; continue to inspect that run before
freezing any Taskell application scenarios.

The Linux leg of `42452701639` has now launched Taskell. The upstream suite
passed; initial screen and text input passed; the state checkpoint failed
before exit because its `Review sample` expectation matched stale initial text
in 0 ms. Same-run report and screen are retained under
`taskell/first-use-attempts/first-use-attempts-v1.tar.gz` under
`42452701639-linux/`; process-group cleanup and
workspace removal were confirmed. The case now sends quit, asserts exact exit
0, then checks final saved bytes. No target-defect or admission credit from the
premature state check. MacOS is still in upstream tests; the corrected case
will run under the next workflow push.

Ubuntu on run `42453888286` completed one passing authored case on the exact
runner and Taskell binaries. All six steps passed, including exit 0, exact
saved board bytes, confirmed process-group termination and workspace removal.
The readback report/host/runner/recorder console are retained under
`taskell/first-use-attempts/first-use-attempts-v1.tar.gz` under
`42453888286-linux/`, and toolchain/binary hashes
are bound in `build-attempt-v14.json`. The subsequent no-JSON recorder failed
before target launch because its independent workflow step omitted the target
directory from PATH. That environment is corrected for the next run. MacOS
for `42453888286` was still in upstream tests; no native-cell or admission
credit is claimed.

Run `42452701639` is now complete on both native hosts. Linux and Intel macOS
each passed 250 upstream tests and built Taskell/Playtestr, but both ran the
old premature state checkpoint and failed before q/exit. Linux evidence is in
`first-use-attempts/first-use-attempts-v1.tar.gz` under `42452701639-linux/`
with receipt `build-attempt-v13.json`; MacOS evidence is in that archive under
`42452701639-macos/` with receipt
`build-attempt-v15.json`. The corrected post-exit case passed on Linux in
`42453888286`; the same run's independent recorder environment failed because
PATH omitted Taskell, now fixed in the next pushed workflow. Continue watching
`42455018922` for both-host smoke and public recorder results. Taskell remains
unadmitted.

## Latest continuation (2026-11-08)

Linux on run `42455018922` repeated the six-step authored smoke successfully.
Its recorder launched Taskell and reached review, but unquoted `/text q` was
invalid JSON; the preview retained only the successful prefix and had no exit
or state checkpoint. Receipt `build-attempt-v16.json` preserves this separate
control-input failure.

Linux on run `42455300421` passed all 250 pinned upstream tests, built Taskell
and Playtestr, passed all six smoke steps including exact exit and Markdown
state, and confirmed process/workspace cleanup. The public recorder route
reached review with quoted inputs, recorded the intended actions and selected
saved state, then cancelled explicitly (130). It did not replay or export.
Receipt `build-attempt-v17.json` records the preview-only result and hosted
artifact digest. The Mac Intel job remains in the pinned upstream tests at the
latest status check.

Next inspect the recorded candidate and exercise fresh `/replay`, `/save`, and
ordinary `playtestr test` on the exact exported files. Then define and challenge
the full Taskell case catalog and execute native repetitions and fault
calibrations. Taskell still has zero scenario, native-cell, fault or admission
credit; campaign remains 4/20 new admissions (14/30 cumulative).

Linux on run `42456298245` now completed the public first-use route: reviewed
candidate, successful fresh recorder replay, export, and ordinary runner test.
The authored smoke and ordinary test reports both show 6/6 steps, exact exit,
saved state, process-group cleanup and workspace deletion. Its curated eight-
member packet and binary/artifact identities are recorded in
`build-attempt-v18.json`.

MacOS Intel on the same run then passed the identical 250-test, build, smoke,
recorder replay/export and ordinary-test path. Its reports likewise show 6/6
steps and confirmed state, process and workspace cleanup. Receipt
`build-attempt-v19.json` and its independently hashed packet preserve the Mac
binary and run identities. The cross-host first-use path is now observed on
Linux and Intel Mac, but this adds no frozen scenario-series, native-cell,
fault calibration or admission credit. Storage checkpoint v18 passed after
lossless receipt compaction, with 152,451 bytes retained headroom at its
observation. Continue measuring before adding larger evidence packets.

## Scenario-candidate continuation (2026-11-08)

Run `42458747709` tested the new-task candidate on Ubuntu after the prior
first-use route. The existing-task case passed, then the create-task case
timed out on its first screen assertion (`assertion_timeout`, step 1); its
later input, exit and state assertions did not run. The failure was caused by
the candidate invoking `taskell board.md` while its fixture actually provides
`board-basic.md`. This is a campaign-spec path error, not evidence of a
Taskell defect. The Mac Intel leg subsequently passed its pinned 250-test
suite, built both binaries, and passed the six-step existing-task smoke before
reproducing the same step-1 prompt. Run `42458747709`'s exact per-host artifact,
binary, report and final-screen hashes are in `build-attempt-v20.json`; the
selected reports and screens are retained in its Linux and macOS evidence
directories. Both runner reports confirm process-group termination and
workspace cleanup. The create-task spec is locally corrected to the fixture's
actual filename. The prepared duplicate candidate remains uncredited and must
not be advanced until the corrected create-task case has been observed on
both native hosts. Taskell remains at zero scenario-series, native-cell,
fault-calibration or admission credit.

Run `42460993289` passed the pinned 250-test suite and existing-task smoke on
both hosts, then the corrected create-task case passed steps 1-7 but timed out
at exit on both. The captured final screen shows `q` inserted as a task while
Taskell remains in INSERT mode. Both reports show forced process-group cleanup
and workspace removal; the exit and exact saved-state assertions did not pass.
The duplicate case did not run. `build-attempt-v21.json` and its paired
report/screen/identity directories preserve the results. Source inspection
confirms Enter stores a task and creates a new blank insert row; Escape calls
`finishTask`, removes the blank row and enters normal mode. The create spec is
locally updated to send Escape, verify INSERT is absent, then send `q`. It is
not credited until a fresh Linux/macOS run passes saved-state and cleanup
assertions.

Run `42462915946` passed the existing-task smoke on both hosts but rejected
the create-task spec before target launch: `expect_not "INSERT"` lacked an
earlier positive expectation for the same text. The runner report is
`invalid_spec`; cleanup was not attempted because no target started. The
duplicate case was not reached. Paired artifacts and hashes are in
`build-attempt-v22.json`. The local candidate now positively expects INSERT
before Escape and negatively expects it afterward. This validation correction
has not yet been exercised on either host.

Run `42464484824` had a Linux setup failure (Stack 3.11.1 download returned
HTTP 504 twice before any build or test). Intel macOS passed all 250 upstream
tests and the existing-task smoke. The create-task candidate passed all 11
interaction/exit steps, including Escape to normal mode and natural exit 0, and
confirmed process and workspace cleanup. Its step-12 state assertion looked
for `board.md`, while the command and fixture use `board-basic.md`; it failed
because that selected path was missing. Exact Mac report, screen, runner and
host data are in `build-attempt-v23.json`; Linux's exact setup excerpt is
retained separately. No saved bytes were asserted, the duplicate case did not
run, and the scenario has no credit. The local state assertion now names
`board-basic.md`; the next hosted run must pass the entire case on both hosts.
