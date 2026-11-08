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
