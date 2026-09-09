# Reproducible real-application recipes

These recipes describe the repeatable boundary proven during the September 2026 technical campaign. They use pinned inputs from [`manifest.json`](manifest.json), isolated target configuration, one synthetic resource, a Playtestr report, and an independent read-only oracle. Target names identify compatibility samples and do not imply endorsement.

Use [`scripts/trials/run-trial.ps1`](../scripts/trials/run-trial.ps1) on Windows to combine a spec result with an external oracle. It creates a new attempt directory for every run and exits nonzero if either component fails. Oracle execution defaults to a 30-second deadline and 1 MiB combined output limit. Its oracle is an executable plus arguments; put compound checks in a small repository-local script. Do not put credentials or ambient dashboard captures in an attempt intended for publication.

## Lazygit

1. Create a new repository with a synthetic author, `alpha.txt`, a filename containing spaces, and a Unicode filename. Record `HEAD`, branch, and `git write-tree` before the action.
2. Launch pinned Lazygit with an isolated `HOME` and config directory. Assert a filename identifying the selected row before sending Space.
3. For staging, the oracle checks `git diff --cached --name-only` equals exactly `alpha.txt` and checks the cached blob. For commit, check the exact new commit message, parent, and tree. For branch selection, check `git symbolic-ref --short HEAD`.
4. Exercise failure by creating `.git/index.lock`. A screen pass with an unchanged index must fail overall. Remove only that lock, restore the starting index, and rerun to green.
5. Before deleting the fixture, confirm its resolved path is beneath the operator-provided attempt root.

## Lazydocker

1. Require an explicit Docker endpoint preflight. Create one digest-pinned synthetic container with a unique name and both an owner label and trial label. Record its ID and initial `StartedAt`.
2. Use isolated Lazydocker config and filter to the unique name. Screen assertions must establish the selected row or a unique fixture marker before input.
3. The oracle inspects only the recorded ID. Stop expects `exited` and the expected code. Start/restart polls with a deadline for `running` and a changed `StartedAt`; retained logs are never accepted as state proof.
4. Exercise failure with an incorrect expected generation or timestamp. Restore the fixture directly for the next attempt, label that restoration as setup, then rerun the TUI path to green.
5. Before stop, start, or removal, recheck exact ID, name, owner label, and trial label. Never enumerate evidence from, mutate, or remove unrelated containers. An unavailable endpoint is a setup failure and must not trigger a daemon restart or fallback.

## K9s

1. Use a disposable cluster or an explicitly supplied dedicated context and kubeconfig. Create a namespace plus uniquely labeled Pod and ConfigMap; record UIDs and live fields through the API.
2. Assert the selected resource identity before mutation. Logs require the unique pod marker. YAML assertions use the live field and remove historical last-applied annotations that could contain stale values.
3. Delete expects the original pod UID to disappear and a new Ready UID to appear. Cancel expects the original UID to remain without a deletion timestamp. Readiness polling is bounded.
4. Exercise failure by changing the live ConfigMap value while retaining the same fixture identity; the overall attempt must fail. Restore the live field and rerun to green.
5. Cleanup uses the recorded context, namespace, name, and UID. Never change the operator's active context and never issue cluster-wide deletion.

For all targets, keep exploratory, setup, primary, negative, and recovery attempts distinct. Preserve `runner-report.json`, `harness-result.json`, oracle output, target/version hashes, and cleanup outcome. A target assertion can pass while the user task fails; only the combined status is the trial result.
