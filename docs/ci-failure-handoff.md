# Reproduce a CI failure locally

Start with ordinary reviewed inputs. A useful handoff names the source and
runner revision, target identity, selected spec and baseline, host and viewport,
safe prerequisites, original report, and isolated evidence directory. It does
not need an environment dump, source bundle, terminal recording, or executable
commands embedded in an artifact.

## Minimal handoff

From a clean checkout of the named revision:

1. Verify the runner source/binary, target, spec, fixture and baseline identities
   supplied by CI. Obtain targets through their documented trusted install path;
   never execute a binary copied from an unreviewed failure artifact.
2. Recreate only the safe synthetic prerequisites named by the test. Do not copy
   secrets or ambient CI environment values.
3. Preview the exact selection, then execute it once into fresh evidence:

   ```powershell
   playtestr test --list path/to/failing.json
   playtestr test --report artifacts/local.json --artifacts-dir artifacts/evidence path/to/failing.json
   ```

4. Compare the structured failure category, failed step/action, target outcome,
   viewport, screen and diff with the CI result. Matching these is a matching
   observable failure, not proof of the same root cause.
5. Optionally render the retained report without rerunning the target:

   ```powershell
   playtestr report --input artifacts/local.json --evidence-root . --output artifacts/local.html
   ```

6. Run the reviewed corrected target/spec once. A pass means the CI failure was
   not reproduced in that corrected context; it must not be labeled a reproduced
   failure. Also verify that an intentionally omitted prerequisite fails with a
   different, actionable category.

Flags precede paths. Never use `--update` during reproduction: a missing or
changed baseline is a prerequisite mismatch to resolve explicitly. Preserve the
original CI evidence and give every local attempt a fresh artifact directory.

## Record the result

Keep the original and local runner/target/spec/baseline identities, OS and
architecture, viewport, safe setup commands, elapsed time, report path, evidence
paths, primary failure category and step, target exit, and cleanup outcome.
Classify the attempt as the same observed failure, not reproduced, a different
failure, a prerequisite mismatch, or cancelled. State unknown application data,
services, scheduling and secret inputs instead of implying they were captured.

The [Sprint 6 experiment](https://github.com/Wyrcan-io/playtestr/blob/main/docs/validation/sprint-6-handoff-2026-09-21.md) demonstrates
this with a pinned Gum selector. Ordinary instructions recovered every necessary
fact, so Playtestr deliberately has no reproduction-manifest command.
