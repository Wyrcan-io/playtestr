# Proof-to-alpha implementation plan

Status: implementation plan for the Playtestr `0.2` milestone.

Date: 2026-08-19

Implementation checkpoint: Slices A and the locally safe portion of Slice B are implemented.
The full twelve-scenario gauntlet passed across fixed seeds with zero cleanup failures;
intelligent autonomy is currently competitive with, but does not yet dominate, the strongest
coverage-guided baseline. Docker execution remains gated on Replay V2, and the browser runtime
remains gated on terminal benchmark improvement and explicit browser installation. Remote CI,
license-owner acceptance, npm trusted-publisher configuration, tagging, and publication remain
release gates.

## 1. Outcome

Turn Playtestr from a promising autonomous terminal explorer into an evidence-backed
playtesting product that can:

- compare its intelligent strategy fairly with simple baselines;
- run a diverse, repeatable terminal-game gauntlet;
- retain knowledge across bounded sessions;
- verify and deduplicate executable findings;
- produce useful machine-readable and human-readable reports;
- optionally execute prebuilt targets through a restricted Docker profile;
- accept bounded suggestions from an optional model provider without trusting it as an oracle;
- expose backend-neutral contracts for later graphical testing;
- meet explicit release gates before an alpha is tagged or published.

Gamr and Playtestr remain separate repositories and products. Gamr owns its game-specific
adapter. Playtestr never imports Gamr.

This milestone does not claim human equivalence, internal code coverage, complete mechanic
coverage, containment against a hostile kernel or Docker daemon, or general graphical-game
support.

## 2. Decision principles

### 2.1 Evidence before sophistication

The intelligent strategy must win, tie, or lose under the same seeds and executable action
budgets as deterministic baselines. Wall-clock time is reported but is not the fairness unit,
because machine and PTY timing vary by platform.

### 2.2 Durable facts, not durable processes

Long campaigns are a sequence of fresh-process episodes. Playtestr persists the world model,
action corpus, verified finding registry, counters, and compatibility metadata. It does not
keep a game process alive indefinitely or serialize opaque provider state.

### 2.3 Reports derive from authoritative artifacts

HTML is a presentation of the same versioned JSON report. It never invents mechanics,
findings, or completion claims. Every executable finding links to its signature, replay, and
reproduction result.

### 2.4 Optional providers propose; core validates

A model provider may suggest an objective and bounded action sequence. Core rejects unknown
actions, over-budget sequences, target mismatches, duplicate proposals, malformed output, and
provider timeouts. Terminal observations and executable oracles remain authoritative.

### 2.5 Isolation is capability-reported

The existing local PTY backend remains explicitly trusted and reports `isolation: none`.
Docker execution reports `isolation: container`, its selected restrictions, and daemon
availability. Containers reduce exposure but are not described as a perfect sandbox.

### 2.6 Graphics reuse product contracts, not terminal assumptions

Campaigns, objectives, proposals, findings, replay identity, and reports are shared concepts.
Terminal screens/actions and graphical frames/pointer actions remain backend-specific.

## 3. Milestone sequence and dependency rationale

1. Benchmark contracts come first so success criteria cannot be changed after seeing results.
2. A gauntlet follows so benchmarks cannot overfit a single hidden-route fixture or Gamr.
3. Campaign persistence follows stable evidence schemas and enables long exploration.
4. Finding verification and reporting consume campaign evidence; they do not create it.
5. Docker wraps the proven runner contract after lifecycle behavior is measurable.
6. Provider supervision enters only after deterministic baselines remain available offline.
7. Release preparation follows local and remote gates.
8. Graphical execution begins with deterministic browser/canvas targets after terminal metrics
   establish that the shared orchestration adds value.

## 4. Fair benchmark system

### 4.1 Strategies

The benchmark matrix contains:

- `intelligent-autonomy`: semantic six-agent orchestration;
- `coverage-guided`: corpus-guided deterministic exploration;
- `round-robin`: fixed action order;
- `seeded-random`: reproducible random action choice;
- `scripted-reference`: optional scenario-specific reference, excluded from competitive ranking.

### 4.2 Fairness rules

- Same manifest compatibility key.
- Same seed list.
- Same maximum total executable actions.
- Same maximum actions per fresh-process episode.
- Same target adapter and expected evidence for strategies capable of consuming semantics.
- Fresh corpus and world for every strategy/seed pair.
- Startup/bootstrap actions count against the budget.
- Cancellation, cleanup failure, runner error, or budget overrun is recorded, never silently
  discarded.
- Strategy order is rotated by seed to reduce thermal/order bias; result sorting is stable.

### 4.3 Metrics

Per strategy and aggregate:

- actions and episodes consumed;
- observed unique states and transitions;
- expected mechanic, milestone, and semantic-tag recall;
- completion and hidden-route discovery;
- first discovery action and episode;
- executable finding signatures;
- cleanup failures and failed runs;
- median and worst elapsed time as diagnostics;
- contributing agent roles for autonomy;
- deterministic result signature.

No metric is called source-code coverage.

### 4.4 Comparison rules

The report states whether autonomy is `dominant`, `competitive`, or `behind`:

- dominant: no lower evidence score, no more cleanup failures, and a strictly higher evidence
  score than every non-reference baseline in at least one scenario/seed;
- competitive: within the declared tolerance and without lifecycle regression;
- behind: lower evidence score outside tolerance or a lifecycle regression.

A single fixture cannot satisfy the release gate. The aggregate must include multiple action,
timing, text-entry, resource, recovery, and failure shapes.

## 5. Terminal-game gauntlet

### 5.1 V1 fixture matrix

The committed gauntlet references at least ten deterministic scenarios:

1. hidden multi-step route;
2. resource acquisition and locked purchase;
3. text-command inventory quest;
4. timing window;
5. turn/counter progression;
6. clean no-output startup failure;
7. deterministic crash sequence;
8. output flood/limit;
9. hanging process and forced cleanup;
10. Unicode/VT rendering stability;
11. resize-sensitive screen;
12. child process-tree cleanup.

Scenarios are classified as `discovery`, `robustness`, or `lifecycle`. Competitive recall is
computed only where expected evidence is meaningful. Robustness/lifecycle scenarios gate
oracle and cleanup correctness.

### 5.2 Suite file

`gauntlet.v1.json` contains only relative manifest paths, scenario IDs, classification,
expected evidence, an explicit per-scenario minimum evidence score, budgets, and seeds. Paths are resolved relative to the suite file and are
required to remain inside its directory unless the caller explicitly allows external paths.

### 5.3 External-game admission

An external terminal game joins the release gauntlet only when:

- its version or immutable revision is recorded;
- installation is not performed implicitly by a benchmark;
- the manifest uses a deterministic seed where supported;
- expected evidence is reviewed rather than inferred from the benchmark output;
- license and redistribution constraints allow the selected integration.

## 6. Persistent campaigns

### 6.1 State schema

Campaign V1 stores:

- schema version, campaign ID, target ID, target compatibility key;
- monotonically increasing revision;
- created/updated timestamps;
- total sessions, episodes, actions, and elapsed time;
- serializable world-model snapshot;
- serialized action corpus;
- deduplicated finding records and reproduction summaries;
- bounded session summaries and deterministic signatures;
- configuration necessary to interpret budgets, never ambient environment values.

### 6.2 Resume safety

- Loading rejects unknown schemas, malformed state, target mismatch, or compatibility mismatch.
- World snapshots are hydrated through a validating constructor.
- Writes use a temporary file and atomic rename with backup restoration.
- Optional expected revision supplies compare-and-swap protection against stale writers.
- Session history is capped; aggregate counters remain monotonic.
- Cancellation saves completed episode evidence and marks the session cancelled.
- A crash during replacement leaves either the previous valid state or the complete new state.

### 6.3 CLI

```text
playtestr campaign --manifest game.json --state artifacts/game.campaign.json
                    [--episodes 30] [--total-actions 360]
                    [--verify-findings] [--report artifacts/game-report]
                    --trust-target
```

Repeated invocation resumes compatible evidence. `--fresh` refuses to overwrite an existing
campaign unless an explicit replacement flag is later introduced.

## 7. Verified finding registry

### 7.1 Identity and deduplication

Finding signature V1 remains the primary identity. A registry record contains:

- signature, kind, severity, first/last session and occurrence count;
- highest evidence level;
- representative shortest replay;
- reproduction classification, attempt counts, matches, and quorum;
- observed statuses and affected seeds;
- message variants without changing identity.

The registry never merges distinct signatures merely because their messages look similar.

### 7.2 Verification policy

- New error findings are eligible for automatic verification.
- Warning findings may be verified when budget remains.
- Default quorum is three of three; configurable lower quorum is explicitly labeled.
- Stable reproduction promotes evidence to `reproduced`.
- Mixed evidence is `flaky`; zero matches remains `observed`.
- Verification uses a fresh process for every attempt and exact signature equality.
- Verification has separate attempt and elapsed-time budgets.

### 7.3 Evidence levels

`confirmed` remains the established level for an executable crash, process, resource-limit, or
invariant oracle that directly proves its condition. Reproduction stability is recorded
separately as a quorum and classification; it does not demote a confirmed oracle to
`reproduced`. Only `reviewed` is reserved for an explicit human/product review workflow.

## 8. Professional report bundle

Every campaign/report export writes atomically within the target artifact quota:

- `report.json`: canonical Report V1;
- `report.html`: standalone, escaped, no external assets or script;
- `summary.md`: concise review handoff;
- `replays.json`: representative replay map keyed by finding/path ID.

Sections:

- target/runtime/campaign identity;
- executive summary and limitations;
- benchmark comparison when available;
- mechanics and evidence confidence;
- milestones, completion, hidden, and shortest observed routes;
- findings grouped by severity and evidence;
- reproduction and cleanup health;
- agent contribution and budget accounting;
- exact replay/API commands;
- machine/version provenance.

HTML uses a restrictive content-security-policy meta tag, escapes all target-controlled text,
and embeds no secrets or environment values.

## 9. Docker execution backend

### 9.1 V1 scope

Docker V1 runs an already-built, explicitly named image. It does not build images, pull by
default, mount the Docker socket, pass host credentials, or infer host paths.

Default run profile:

- `--pull never` and `--rm`;
- `--network none`;
- `--read-only`;
- `--cap-drop ALL`;
- `--security-opt no-new-privileges`;
- non-root numeric user;
- CPU, memory, PID, and temporary-filesystem limits;
- no host bind mounts;
- isolated temporary `/tmp`;
- explicit environment allowlist;
- deterministic container name and forced removal fallback;
- existing runner output, action, artifact, and wall-clock limits.

Docker documents that containers have no CPU or memory limits by default, so Playtestr must
always supply them. Docker also documents `--read-only`, PID limits, capability dropping,
`no-new-privileges`, and the `none` network driver:

- https://docs.docker.com/engine/containers/resource_constraints/
- https://docs.docker.com/reference/cli/docker/container/run
- https://docs.docker.com/engine/network/drivers/none/

### 9.2 Capability and acknowledgement

`probeDocker()` reports CLI presence, daemon reachability, server OS, and warnings. CLI use
requires `--container-target`; enabling network or pull uses separate acknowledgements.

V1 cannot claim VM-grade isolation. Docker daemon compromise, kernel vulnerabilities, unsafe
images, and explicitly relaxed flags remain outside the guarantee.

## 10. Optional supervisor provider

### 10.1 Contract

The provider receives a bounded, redacted context:

- target ID and declared action vocabulary;
- semantic screen summary and bounded recent text;
- known mechanics/objectives and shortest prefixes;
- remaining action/time budget;
- deterministic request ID.

It returns proposal objects, not executable code, shell commands, manifests, environment
changes, oracle results, or findings.

### 10.2 Validation and resilience

- timeout and abort support;
- response byte and proposal count limits;
- exact schema validation;
- allowed-action and per-proposal budget checks;
- stable deduplication and scoring;
- provider ID/model/version recorded in reports;
- provider errors degrade to deterministic agents;
- no provider is required by build, tests, benchmarks, or basic CLI use.

The first implementation is provider-neutral with a deterministic test provider. Hosted model
adapters are separate optional packages or future entry points.

## 11. License and alpha release

Recommended license: AGPL-3.0, matching Gamr and protecting a future hosted Playtestr service.
The owner must accept the network-source obligations before publication. GNU explains that a
modified network-served version must offer corresponding source to remote users:
https://www.gnu.org/licenses/agpl-3.0.html

Release candidate version: `0.2.0-alpha.1`.

Tag/publication gates:

1. local typecheck, tests, build, lifecycle soak, package dry-run, and vulnerability audit;
2. benchmark report committed or attached with fixed seeds and budgets;
3. Node 22 CI on Windows, Linux, macOS and Node 24 on Linux;
4. Windows lifecycle soak;
5. license owner approval and complete license text;
6. public package contents reviewed;
7. npm trusted publisher configured with provenance and no long-lived publish token;
8. release notes disclose terminal-only scope and Docker limitations;
9. signed or GitHub-created tag from the verified commit;
10. installed-tarball smoke after publication.

npm recommends trusted publishing with short-lived OIDC credentials and automatically created
provenance for eligible public packages:
https://docs.npmjs.com/trusted-publishers/

No automated implementation step publishes or tags merely because local tests pass.

## 12. Graphical backend roadmap and contract

### 12.1 Shared contracts

- objective and proposal identity;
- campaign session and budget accounting;
- finding signatures and reproduction quorum;
- artifact quotas and reports;
- backend capability reporting.

### 12.2 Browser V1 target

Start with deterministic local HTML/canvas games:

- fresh non-persistent browser context per episode;
- fixed viewport, locale, timezone, color scheme, reduced motion, and device scale factor;
- no network except the explicitly allowed local origin;
- keyboard, pointer, and bounded wait actions;
- accessibility/DOM observations where available;
- screenshot buffer for canvas-only evidence;
- bounded screenshots and optional video artifacts;
- seeded initialization script only when declared by the target;
- context/browser cleanup confirmation.

Playwright documents clean-slate browser contexts and warns that screenshot output varies with
OS, browser, hardware, and settings. Therefore visual baselines are platform/browser-specific:

- https://playwright.dev/docs/browser-contexts
- https://playwright.dev/docs/test-snapshots

### 12.3 Admission gate

The browser runtime is added only after:

- terminal benchmarks meet the evidence gate;
- the graphical contract passes with an in-memory deterministic backend;
- browser binaries are installed explicitly rather than during ordinary package installation;
- local-origin and artifact threat models are reviewed;
- CI has a pinned browser version and platform-specific visual baselines.

Native desktop games, anti-cheat protected games, arbitrary remote websites, and computer-
vision-only navigation are later milestones.

## 13. Implementation slices

### Slice A: proof and persistence

- benchmark autonomy against equal-budget baselines;
- add suite/gauntlet schema and runner;
- hydrate WorldModel snapshots;
- add Campaign V1 atomic load/save/resume;
- add finding registry;
- add JSON/HTML/Markdown report bundle;
- expose CLI and public API;
- test malformed, incompatible, stale-revision, escaping, and cancellation paths.

### Slice B: controlled extensibility

- Docker command/profile builder and daemon probe;
- Docker PTY backend with forced-removal fallback;
- optional supervisor contracts and validating agent wrapper;
- graphical contracts and deterministic in-memory conformance tests.

### Slice C: release evidence

- run gauntlet and fixed-seed comparison;
- run full checks and 100-run lifecycle soak;
- package dry-run and audit;
- confirm remote CI;
- obtain license approval;
- prepare changelog/release notes;
- only then tag and publish.

## 14. Definition of done

This implementation milestone is complete when:

- benchmarks include intelligent autonomy and equal executable budgets;
- at least ten classified scenarios are represented in the gauntlet;
- campaigns resume compatible world/corpus/finding evidence with atomic revisioned writes;
- executable findings are exact-signature deduplicated and optionally quorum-verified;
- JSON and escaped standalone HTML reports derive from the same canonical model;
- Docker configuration is restrictive by default and capability-reported;
- provider output cannot bypass action/schema/budget validation;
- graphical contracts are backend-neutral and tested without claiming a browser product;
- Playtestr remains independent from Gamr;
- local checks, lifecycle soak, package smoke, and cross-repository adapter smoke pass;
- remote CI, license acceptance, tagging, publication, hosted providers, and browser runtime are
  reported accurately as complete or still gated.
