# R1 — Publish the first release candidate

Status: completed on 2026-09-07. Product outcome: a developer can download a known Playtestr build without installing Go or cloning the runner source.

Completion evidence: [v0.1.0-rc.1](https://github.com/Wyrcan-io/playtestr/releases/tag/v0.1.0-rc.1) was published from commit `1dde372282a574025957c4bf1b603287cbef93e4` after [native release run 34052977944](https://github.com/Wyrcan-io/playtestr/actions/runs/34052977944) passed on Linux amd64, macOS arm64, and Windows amd64. The six public assets were downloaded and matched against the staged workflow artifacts byte-for-byte.

## Why this matters

Workflow artifacts prove a build ran, but they are a poor permanent installation interface. The first prerelease creates a discoverable version, installation instructions, and a support target for the installation walkthrough and external trials. Success is a usable download with provenance, not a release page alone.

## Starting evidence and gaps

The repository records successful Sprint 4 terminal tests and release-candidate run `34048585717`, built from `bcd1b6e`. Subsequent documentation and CI commits do not change those archive bytes. At execution time, inspect current tags, releases, asset expiration, and commit history before selecting a version; do not assume these historical assets still exist or that `v0.1.0-rc.1` is unused.

The current release workflow executes `bin/playtestr` before packaging. It does not extract its own ZIP/tar.gz and execute that copy. Correct that verification gap for the candidate being published. The archive currently contains only the runner, README, and LICENSE; the demo and external Gum executable are separate prerequisites.

## Scope

Publish one GitHub prerelease for Linux amd64, macOS arm64, and Windows amd64, provided each has native evidence for the selected candidate. Include three archives, their checksum files, human-readable release notes, and explicit links to version-matched instructions. Keep the runner standalone. Package-manager distribution and stable-release promotion belong to later plans.

## Checkpoint 1 — Freeze candidate identity

1. Inspect the current repository state and available version names. Choose the exact source commit and candidate version together.
2. If using the historical candidate unchanged, tag its producing commit. If anything in the binary, archive contents, or versioned docs must change, create and verify a new candidate build; do not label old bytes as the new build.
3. Record candidate commit, version, target triplets, build command/toolchain, CI run IDs, and asset names in a release preparation note.
4. Freeze fixes to release blockers only. Carry convenience requests into the trial backlog.

Acceptance: every proposed asset has one source commit and one version, with no ambiguous use of moving `main` or `latest`.

## Checkpoint 2 — Close distribution correctness gaps

For each native host, build, archive, extract into a fresh directory, and invoke the extracted binary. Verify `--version`, `--help`, a successful test, expected failure status, and a writable report destination. Confirm Unix executable permissions survive extraction and Windows paths with spaces work.

Inventory linked dependency licenses and attribution requirements, including the Go distribution notices relevant to bundled runtime code. Record what is required for binary redistribution and include the necessary third-party notices in the archive. The project's Apache license alone is not proof that all bundled dependency notices are covered.

Inspect archive member paths, file types, permissions, names, and size. Reject absolute paths, traversal entries, unexpected symlinks, build caches, fixture secrets, or unrelated files. Validate the checksum against the archive and verify the binary inside belongs to the candidate.

Acceptance: the same bytes intended for upload have passed extraction and execution on each claimed native target. Retain evidence from the extracted location, not the build directory.

## Checkpoint 3 — Prepare an honest first-user path

Prepare release notes covering the supported workflow: launch a trusted target, drive keys, assert visible text and exit status, compare reviewed snapshots, and save JSON/failure evidence. Include known terminal and process-management limitations, spec/report versions, and a link to reporting problems.

Provide a binary-only quickstart using an explicitly named trusted target already present on the test host, with platform-specific variants where needed. Also offer the demo quickstart with its Go build requirement clearly labeled. Do not advertise a no-Go demo if the user still needs to build `cmd/demo`.

Separate Playtestr requirements from application requirements. Downloading Playtestr does not install Gum, Python, Node, the target's dependencies, or the user's project.

Acceptance: a reader can identify the correct asset, its prerequisites, a verification command, and a first test before leaving the release page.

## Checkpoint 4 — Stage and verify publication

Stage a draft prerelease with explicit source commit/tag identity, notes, and the complete asset set. Verify all three archives and checksums are present and correctly named before exposing the release. If permissions or account configuration prevent drafts, prepare the equivalent exact asset/notes manifest locally first.

Publishing/tagging is an external action. Use the session's explicit release authorization if present; otherwise request it only after the candidate is concrete and reviewable. Earlier permission to push implementation commits or run CI is not itself a request to publish a release. Do not add unrelated permission steps.

Once published, download the release assets through their public links, recompute checksums, and compare with the staged manifest. Preserve the source/run provenance in notes; a checksum verifies byte integrity, not independent publisher authenticity.

Acceptance: the release is marked prerelease, every public link works, and public downloads match the approved bytes.

## Failure handling

| Problem | Response |
| --- | --- |
| Historical artifacts expired | Rebuild the selected commit with recorded inputs and rerun all candidate checks. |
| Version or tag already exists | Inspect it; never overwrite it silently. Select the next candidate version if bytes must change. |
| One native host fails | Fix the candidate or explicitly narrow supported assets and update claims; do not publish an unverified target. |
| Upload incomplete | Keep the release in draft until the manifest is complete. |
| Published asset is defective | Mark the candidate as superseded with a clear explanation and issue a new candidate; do not silently swap bytes. |
| Setup requires unsafe credential workarounds | Resolve the actual setup cause; do not teach users to disable verification globally. |

## Definition of done

- [x] Exact commit/version and target manifest recorded.
- [x] Extracted archives, required notices, executable modes, and checksums verified natively.
- [x] Release notes and separate binary/demo prerequisites reviewed.
- [x] Prerelease published under explicit authorization, with matching public downloads.
- [x] R2 has the immutable URLs, candidate identity, and walkthrough instructions it needs.

Stop after publication and verification. Stable promotion, outreach, package managers, and new runner behavior are outside R1.
