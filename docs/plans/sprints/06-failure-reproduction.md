# Sprint 6 — Reproduce a CI failure locally

Status: proposed. Depends on Sprint 5's stable suite/artifact identities. Primary outcome: a developer can inspect a failed run's required inputs and rerun its reviewed test against a local trusted application without reconstructing CI context by hand.

## User problem and value

A test fails in CI but passes on a laptop. The author does not know whether the viewport, application version, spec revision, baseline, or test selection differed. Saving every raw terminal byte would not recreate the filesystem, backend state, or process scheduler, and copying complete launch environments could expose secrets.

This sprint delivers a bounded reproduction manifest with local input resolution and explicit execution. It does not promise deterministic replay of arbitrary applications. A rerun that passes is useful evidence of non-reproduction; it must never be labeled a successful reproduction of the original failure.

## Entry gate

Use at least one real CI-to-local reproduction case from the adopter cohort. Collect the current manual steps and missing facts. Require stable Sprint 5 output paths and a named test/application revision. If the only difficulty is missing documentation, fix that first and reevaluate the need for a manifest command.

## Proposed workflow

```text
playtestr test --repro artifacts/repro.json --report artifacts/results.json tests/terminal/menu.json
playtestr reproduce --inspect artifacts/repro.json
playtestr reproduce --execute --spec tests/terminal/menu.json artifacts/repro.json
```

Names are proposals. Inspection is the default and never starts a process, fetches a repository, installs a dependency, or applies environment variables. Execution requires an explicit flag and an explicitly chosen local spec. The local spec remains the authoritative trusted launch definition. This separation lets a user inspect an externally supplied manifest without executing embedded commands.

## Reproduction contract

Define `repro_version: 1` as a separate format, with its own schema and resource limits. Do not overload report v1 or quietly embed commands/arguments into it. Proposed fields include runner version, host OS/architecture, selected relative spec identity, initial viewport, successful resize sequence, action kinds and indexes, timeout/output limits, original failure identity, and references to local evidence.

Keep the initial export and rerun contract to one explicitly selected spec. Reject a multi-spec `--repro` request with guidance to select the failing spec, rather than silently choosing the first failure. Suite-wide reproduction bundles require a separate demonstrated need and format decision.

Record a fingerprint of a canonical redacted spec structure and baseline content hashes where suitable. Exclude command arguments, environment values, typed input, expected strings, and full source files from exported manifests. Do not compute/persist hashes of secret values as an attempted privacy shortcut. A structural fingerprint cannot prove two local inputs are identical; label sensitive launch/input values as externally supplied and unverified.

Target identity may use a user-supplied revision label and an optional executable hash when explicitly configured. Do not run an arbitrary target `--version` command automatically or infer a package version from a filename. Record which properties are observed, supplied, missing, or unverifiable.

## Baselines, paths, and portability

The manifest references reviewed local baselines and relative spec locations. It does not rewrite them. Compare available fingerprints before a rerun, and show mismatches clearly. Never apply `--update` during reproduction. A missing baseline is a prerequisite failure, not permission to create one.

Resolve manifest references under an explicitly selected root. Reject traversal, absolute references where disallowed, path aliases that overwrite inputs, and symlinks escaping the root. A move from Windows to Linux may not be portable; fail with the concrete incompatibility rather than claiming fidelity.

Allow an explicit exploratory override for a known version/fingerprint mismatch only if its output is labeled as a divergent run. Original run evidence stays immutable, and each attempt receives a fresh directory.

## Failure identity and rerun outcomes

Identify the original failure using structured category, selected spec identity, step index/action, and snapshot reference if applicable. Include primary failure separately from cleanup/evidence failures. Do not parse console prose or count an unrelated timeout as reproducing a snapshot mismatch.

The result of a reproduction attempt is one of: reproduced within the recorded observable identity; not reproduced; different failure; prerequisite mismatch; or cancelled. Document the CLI status mapping at checkpoint 1. A proposed mapping is 0 for the same observed failure, 1 for not reproduced/different failure, 2 for invalid inputs/prerequisites, and 130 for cancellation; explain that this command's success means successful reproduction, unlike `test` where success means the target test passed.

Missing application state remains a stated limitation. The reproduction manifest does not capture databases, network services, the process scheduler, or secret inputs. Sprint 9 will later make repository-local workspace state more repeatable.

## Scope exclusions and resource budgets

Exclude raw ANSI recording, screen video, timing playback, automatic repository checkout, target installation, remote execution, environment capture, source-code bundles, rerun-until-pass loops, and failure minimization. Preserve synthetic/redacted evidence rules from the current product.

Start with a proposed 1 MB manifest, 1,000 steps per referenced spec, the existing spec/session limits, and one rerun per explicit invocation. Reproduction must use the same bounded session/cleanup machinery as `test`. Reject malformed or oversized manifests before reading referenced evidence or launching targets.

## Architecture

Add a narrow internal manifest encoder/validator and local prerequisite resolver. Keep the canonical manifest independent of xpty/vt10x types. Use existing structured run results as the source of captured facts. Reuse runner execution rather than duplicating a replay engine.

Separate inspect, prerequisite evaluation, and execute into testable operations. CLI code owns the explicit execution switch and exit mapping. The manifest writer owns serialization only. Sensitive values stay in the user-selected local spec and target process configuration.

## Checkpoints

### 6.1 — Reproduce one failure manually and freeze semantics

Document the adopter failure, the missing context, and what can actually be captured safely. Define manifest fields, unknown/unverified states, failure identity, and CLI status semantics. Review redacted fingerprints and explicitly list what they do not verify.

Acceptance: the contract supports this real task without claiming a complete execution snapshot.

### 6.2 — Export a minimal failure manifest

Write the bounded manifest from a selected run and existing evidence. Include versions/viewport/step identity and useful limits. Keep report v1 unchanged. Handle invalid spec, prelaunch failure, and cancellation honestly when some metadata was never observed.

Acceptance: a failure creates a parseable manifest; canary values placed in environment, typed input, and command arguments do not appear in it or in derived metadata.

### 6.3 — Inspect safely and resolve prerequisites

Implement inspect-only output and validation of local references. Show missing target/spec/baselines and mismatched known identities without starting anything. A hostile manifest cannot cause a process launch or escape its root through a path reference.

Acceptance: a helper executable placed in a malicious manifest remains unstarted during inspection.

### 6.4 — Execute a reviewed local spec once

Require explicit local spec selection and execution intent. Run through the ordinary runner, save separate attempt evidence, and preserve original files. Enforce cancellation, output limit, cleanup, and total timeout in exactly the same execution path.

Acceptance: the known regression reproduces, a corrected application does not, and an unrelated crash is classified as a different failure.

### 6.5 — Validate portability and incomplete context

Test path relocation, different runner/spec/baseline versions, absent local inputs, and cross-host attempts. Refuse to certify an exact match where redacted input or runtime state cannot be verified. Document how users supply their own known test data.

Acceptance: limitations are visible before execution; no silent auto-download or baseline update occurs.

### 6.6 — Trial the CI-to-local workflow

Have the adopter obtain the CI evidence, inspect it locally, identify prerequisites, and rerun the chosen regression. Measure assistance and time spent locating the correct inputs. Record a non-reproduction case as well as a successful one.

Acceptance: the maintainer can explain whether the observed failure reproduced and which facts remain unverified.

## Acceptance matrix

| Case | Required result |
| --- | --- |
| Known broken target/spec/baseline | Same observed failure identity; new attempt evidence saved. |
| Corrected target | Not reproduced, with the new passing result retained. |
| Unrelated crash instead of mismatch | Different failure, never counted as reproduced. |
| Inspect untrusted manifest | No target, shell, network request, or dependency install starts. |
| Missing/changed baseline | Clear prerequisite mismatch; baseline unchanged. |
| Export with sensitive local inputs | No raw sensitive values or secret-derived hashes exported. |
| Manifest moved to another folder | Explicit root resolution works without using original absolute user paths. |
| Malformed version/path/oversized manifest | Prelaunch failure within resource limits. |
| Cancel/hang/flood | Existing bounded execution and cleanup guarantees hold. |
| Primary failure plus cleanup failure | Both retained; reproduction identity does not conceal cleanup damage. |

## Definition of done and handoff

- [ ] Checkpoints 6.1–6.6 complete with one real reproduction task.
- [ ] Inspect cannot execute and execute cannot rewrite original evidence/baselines.
- [ ] Format, privacy boundary, failure identity, limits, and unknown states documented and tested.
- [ ] Advertised platform paths run natively; no new unsupported compatibility claim.
- [ ] Existing `test` commands and report v1 remain compatible.

Handoff to Sprint 7: a bounded manifest and stable evidence references suitable for local inspection. Automatic minimization remains deferred until repeated runs establish a useful, stable failure predicate.
