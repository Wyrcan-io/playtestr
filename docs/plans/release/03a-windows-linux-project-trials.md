# R3 technical trial plan: Lazygit, Lazydocker, and K9s

Status: executed across all six matrix cells with open findings. See the [reviewed technical result](../../trials/technical-trial-2026-09.md). Target applications are identified for reproducibility; their inclusion does not imply maintainer participation, endorsement, sponsorship, or permission to publish private correspondence.

## 1. Outcome and boundaries

Answer a practical question for each application: can the published Playtestr candidate drive a useful interaction, detect an incorrect result, preserve useful evidence, and leave the environment clean on both operating systems?

Start with one complete vertical slice per application. Expand to the bounded scenarios below after that slice works. Maximize distinct failure modes and useful workflows, rather than adding many nearly identical snapshots. Do not promise exhaustive application coverage.

The operator chooses workflows from documented application behavior. Record them as operator-designed and operator-reviewed. Maintainer review, voluntary reuse, quotes, and purchasing intent must not be inferred from permission to test.

All three selected applications are implemented in Go. They broaden application and infrastructure coverage, but this cohort alone does not establish cross-language coverage. The parent [R3 plan](03-real-project-trials.md) still requires independent participant evidence and multiple stacks; keep those gates open. A later Rust or Python application can fill the language gap without expanding this campaign now.

This is planning only. Installation, running applications, creating infrastructure, modifying runner code, publishing workflows, and sending messages are execution-phase work. Revisit the parked R2 workflow only after this campaign's execution and assessment, following the user's requested order; do not label all of R3 complete if its human gates remain outstanding.

## 2. Privacy and authorization records

- Keep the root approval list ignored. It is currently untracked; ignoring it does not remove any historical copies if that changes later.
- Store private consent references, contact details, private observations, kubeconfigs, and unreviewed evidence under ignored `.trial-private/` or outside the repository. Do not read or print the approval list merely to prove that it is ignored.
- Use opaque participant identifiers. Public technical reports can identify the software/version being exercised, but must not connect it to private approvals or identify the people involved.
- Do not publish correspondence, quotes, claims of endorsement, willingness to pay, or private maintainer identities. Test permission is not attribution permission.
- Review screens, target logs, reports, paths, Git configuration, and infrastructure metadata before sharing. Ignored files are still readable locally and can still be uploaded accidentally by broad CI artifact rules.
- Public CI is suitable only for sanitized technical tests. Its job names and artifacts must contain no private participation claims. Publish only explicitly selected artifacts, never the entire working directory.

## 3. Freeze versions once, then repeat

Interpret "latest" as the latest official non-prerelease release available when execution begins. Query the official release pages at that time; record the lookup timestamp. Do not bake a potentially stale version into this plan or install a moving `latest` on every repetition.

For each app record repository URL, release tag, resolved source commit, Windows/Linux archive names, download URLs, published checksums or provenance when available, locally observed SHA-256, and version output. A local hash identifies bytes but is not publisher authentication when no upstream checksum exists.

Use the same release on both hosts. If the latest release has no suitable native asset, record the packaging gap; use a documented pinned-source build only as a separately labeled result. Do not silently substitute an older release. Default-branch HEAD testing is optional follow-up, pinned to a separate commit and evidence set.

Use published Playtestr v0.1.0-rc.1 assets as the initial baseline. Record its exact version and asset hash independently of target versions. If a runner fix is needed, preserve the original failure and label all checkout-built or new-candidate reruns separately. Compatibility evidence for a patched checkout does not prove the existing downloadable candidate works.

Also pin Git, Docker client/server and Compose where used, kubectl, kind, Kubernetes node image, workload image digests, and fixture revision. Dependency downloads occur during preparation; ready fixtures should not depend on an uncontrolled public service during assertions.

## 4. Host and infrastructure matrix

| Application | Windows execution | Linux execution | Fixture dependency |
| --- | --- | --- | --- |
| Lazygit | Windows runner and target through ConPTY | Linux runner and target through a real PTY | Disposable local Git repository |
| Lazydocker | Windows runner and target, talking to a verified Docker endpoint | Linux runner and target with Docker Engine | Dedicated test daemon/VM preferred; owned containers |
| K9s | Windows runner and target, with explicit test kubeconfig | Linux runner and target with explicit test kubeconfig | Disposable Kubernetes cluster |

Record actual OS build/distribution, CPU architecture, PTY backend, shell, locale, dimensions, dependency versions, and endpoint topology. A Linux VM, WSL2 distro, or Linux CI runner can provide Linux evidence, labeled accurately. Running Linux Playtestr inside WSL does not provide Windows ConPTY evidence.

A Windows Docker client may manage Linux containers in Docker Desktop or another explicitly configured test engine. Windows K9s may manage Linux Kubernetes nodes. These are Windows client/terminal tests, not Windows container or Windows node compatibility claims.

Do not assume a hosted Windows CI runner has a usable Linux container engine or supports the required virtualization. Preflight locally first; use a dedicated Windows machine if necessary. A pre-existing remote cluster or Docker endpoint must never be selected from ambient defaults.

### Preflight acceptance

- Identify available native execution hosts without installing or enabling machine-wide virtualization implicitly.
- Verify candidate and target executables, versions, and dependency access.
- Prove the Docker endpoint and Kubernetes context belong to this test campaign before any mutation.
- Create target-specific empty configuration homes; explicitly route Git config, Docker config/context, kubeconfig, and application state there using supported settings for the pinned release.
- Verify the application honors these settings. Avoid inheriting the user's plugins, Git hooks, credential helpers, cloud authentication, or custom key bindings.
- Document disk/memory requirements and bounded setup deadlines after checking the chosen infrastructure versions.
- If a prerequisite is missing, mark the affected matrix cells blocked and continue independent cells. Missing infrastructure is not a Playtestr defect or a pass.

## 5. Shared execution contract

Use current [spec v1](../../spec-v1.md) and [report v1](../../report-v1.md). Inputs are keyboard/text/resize actions; assertions inspect rendered text, snapshots, and exit status. Filesystem and service-state checks belong to the trial harness, not invented spec actions.

Each scenario has four explicit phases: prepare starting state, drive the real TUI, verify independent postconditions, and clean up. A harness result passes only if all required phases pass. Keep harness failures separate from Playtestr's structured failure category. Do not edit a passing report to disguise a failed external postcondition.

| Phase | Positive evidence |
| --- | --- |
| Setup | Required repository/container/resource exists with exact intended state |
| Ready | A distinctive visible label for the intended screen, not merely silence |
| Action | Input causes a new relevant visible state, not text that was already present |
| Result | Rendered expectation plus independent Git/Docker/Kubernetes state where applicable |
| Exit | Exact observed expected exit code for the tested quit path |
| Cleanup | Runner process cleanup and separately verified fixture cleanup |

Discover keys and configuration from the pinned application's help/docs; do not guess shortcuts from another version. Establish a manual baseline using the same config, viewport, fixture, and host. Record assistance and any behavior that cannot yet be confirmed manually.

Start at 120x40, then exercise 80x24 and restore 120x40. A smaller stress size is an optional diagnostic, not automatically a supported target size. Use ASCII synthetic identifiers first, then one filename/value with spaces and one Unicode case where the app supports it. Colors, pixel appearance, mouse behavior, and terminal font glyph coverage are not part of Playtestr's text contract.

Use bounded readiness polling for fixture setup and visible `expect` actions for TUI transitions. Separate setup deadlines from target startup, step, total run, output, and cleanup limits. Record actual chosen limits before the sample; never enlarge product limits merely to make a failing sample pass.

Dynamic dashboards contain ages, IDs, uptime, CPU, memory, rates, and generated names. Assert stable labels and meaningful state transitions. Take whole-screen snapshots only of genuinely stable views, such as suitable help/dialog screens. Do not add undocumented masking or crop actions to spec v1. If no stable snapshot exists, record that limitation and use other assertions; do not normalize away the behavior being tested.

## 6. Lazygit scenarios

Prepare a temporary repository with synthetic Git author/committer identity, fixed timestamps, explicit default branch, LF fixture content, deterministic commits, no remote, and isolated configuration. Disable signing, hooks, credential helpers, external pagers/diff tools, and automatic network actions for the fixture using supported configuration. Verify actual Git settings rather than changing global user configuration.

| ID | Workflow | Acceptance and oracle | Priority |
| --- | --- | --- | --- |
| LG-01 | Select and stage one changed file, then unstage it | Correct file visibly changes state; `git diff --cached` confirms exact staged content and later empty index | Required first slice |
| LG-02 | Commit a staged synthetic change through the TUI | Expected commit appears; Git verifies message, tree, and clean intended state | Required |
| LG-03 | Switch between two local branches | Selected branch changes; `git symbolic-ref` and fixture file content agree | Required |
| LG-04 | Filter/navigate files, open/close help, resize and recover | Selected fixture remains identifiable; no lost input or unusable redraw; clean quit | Required |
| LG-05 | Stage one of two separated hunks | Index contains only the chosen hunk | Follow-up after required slices |
| LG-06 | Attempt branch switch with a conflicting local edit; cancel | Useful conflict/refusal state; original branch and edit preserved | Follow-up |

Cover empty/no-change state, a spaced filename, CRLF-related host differences, first-run dialogs, and stale Git locks as bounded diagnostic cases. Do not assert platform-dependent absolute paths or incidental commit abbreviations without deliberately controlling them. Git-repository discovery must never escape into the Playtestr source repository.

Defer interactive rebase, remote pushes, credential prompts, submodule networks, and custom external commands. They increase state and subprocess complexity without being needed to prove the first useful regression test.

## 7. Lazydocker scenarios

Use a minimal fixture image pinned by digest with deterministic bounded log messages and an observable start/stop lifecycle. Preload it before testing. Give resources unique campaign ownership labels and deterministic display names within a dedicated daemon. Avoid host-directory mounts, privileged containers, real credentials, and exposed public ports.

| ID | Workflow | Acceptance and oracle | Priority |
| --- | --- | --- | --- |
| LD-01 | Select the fixture container and inspect its logs | Correct selection and unique log marker are visible; Docker confirms matching container identity | Required first slice |
| LD-02 | Stop and start the selected fixture | TUI shows each state; Docker inspect independently confirms state changes | Required |
| LD-03 | Restart the fixture | Docker start timestamp or fixture start generation changes; running state alone is insufficient proof | Required |
| LD-04 | Navigate views/help, resize, return to container and quit | Expected labels and selection recover without relying on live metric snapshots | Required |
| LD-05 | Empty container list and unavailable test endpoint | Bounded, interpretable behavior with no unintended endpoint fallback | Required negative cases |
| LD-06 | Compose service navigation | Fixed Compose project and services selected correctly | Follow-up if Compose integration is useful |

Inventory endpoint containers before and after a run. A global container list can expose unrelated workloads; use a dedicated engine for mutation scenarios. A container name alone is not a sufficient deletion guard: require the recorded ID and ownership labels.

Stopping the Lazydocker process does not stop its managed containers. The harness owns container cleanup separately. Do not use global prune, remove-all, or shutdown of a shared Docker daemon. Test unavailability with a dedicated invalid endpoint or dedicated engine, never by disrupting a user's engine.

## 8. K9s scenarios

Provision an explicitly named disposable kind cluster where the chosen host supports it, or a dedicated equivalent. Pin the Kubernetes node image. Use a dedicated kubeconfig and namespace with small synthetic resources: a one-replica Deployment, stable labels, deterministic log marker, and a ConfigMap. Avoid external services, secrets, cluster plugins, cloud credentials, and production contexts.

Use a test-scoped identity with only required resource permissions where practical. Preflight required discovery and namespace permissions separately from application behavior. Record any broader privileges used for cluster setup; do not expose setup credentials in artifacts.

| ID | Workflow | Acceptance and oracle | Priority |
| --- | --- | --- | --- |
| K9-01 | Enter fixture namespace, find a pod, open logs | Namespace/resource identity and fixed log marker visible; API verifies labels and resource identity | Required first slice |
| K9-02 | Filter resources and inspect description/YAML | Selected fixture's stable field is visible; return navigation works | Required |
| K9-03 | Delete one fixture pod through the confirmation dialog | API observes original UID gone and Deployment replacement Ready; do not rely on generated pod name staying fixed | Required controlled mutation |
| K9-04 | Cancel a resource deletion | Original UID remains; no deletion timestamp or unintended mutation | Required |
| K9-05 | Resize/help/navigation and clean quit | Readable expected state after resize and exact normal exit | Required |
| K9-06 | Empty namespace, permission denial, unreachable test API | Each produces bounded accurate behavior; record which layer fails | Required negative cases |

Exclude dynamic ages, pod suffixes, metrics, and resource versions from exact snapshots. Wait on readiness conditions, not elapsed sleeps. Missing metrics-server is an environment fact, not automatically a rendering bug. Keep a separate broad selector test if filtering by a generated pod name would otherwise hide selection errors.

No node drains, cluster-wide deletes, real secret views, remote production exec, or production context switching. Cluster deletion must target the exact recorded campaign-owned cluster. Verify namespace/resources and local helper processes independently of the K9s process exiting.

## 9. Prove failures and recovery

For every application and host, preserve good -> intended bad -> restored good evidence using the same test contract.

Distinguish three experiments:

1. Assertion self-check: deliberately wrong expected text/snapshot proves Playtestr reports a mismatch. Useful runner evidence, but not proof of detecting an application regression.
2. Controlled behavioral fault: change a fixture's result (wrong content, log marker, or missing expected resource) while keeping launch and readiness valid. Label this fixture-fault detection, not an upstream application bug.
3. Application regression: use a documented known-bad upstream revision, or a small reversible source mutation at the pinned source commit affecting the chosen behavior. Run an unmodified build from the same source/toolchain as a control; preserve patch and hashes. Label locally mutated builds explicitly.

Prefer a real reproducible application regression when available. Do not search indefinitely for one or manufacture an upstream bug claim. If only fixture faults are practical, record the limitation and leave the parent R3 application-regression gate unresolved.

For expected failures assert nonzero runner status, correct structured category where Playtestr owns the failure, relevant failing step, useful evidence, and cleanup. A malformed spec or absent executable does not count as detecting the intended behavioral defect. Harness-only oracle failures must also make the overall command fail.

Exercise cancellation while waiting for readiness and while observing logs, total timeout, and one bounded output-flood case with synthetic fixture output where feasible. Keep unrelated runner lifecycle coverage in existing tests; do not build dozens of redundant real-app stress cases. Verify that process cleanup does not accidentally remove external fixtures before evidence capture.

## 10. Repetition and matrix accounting

The core matrix has six cells: three applications times two native client operating systems. Run every required scenario once successfully in each cell, including its relevant failure and recovery cases. Then repeat the primary slice ten consecutive times per cell from reset state: 60 primary-slice attempts total.

Record attempts individually, including setup, target, oracle, and cleanup outcomes. No concealed automatic retries. A failed attempt stays in the denominator even if a subsequent rerun passes. After a fix, start a separately labeled sample and retain the original one. Report both scenario breadth and repetition counts; ten passes do not establish general reliability.

Run one second-session sample on each host to expose persisted config/cache/state. Label this operator repeatability; it is not voluntary maintainer retention. Establish a reviewed normal viewport baseline before resize/Unicode variants so failures can be attributed.

## 11. Harness and artifact design for implementation

Keep orchestration outside runner core. Prefer PowerShell for Windows and a small shell script for Linux; use a Go helper only when meaningful shared verification would otherwise be duplicated. No new production dependency is required just to launch trials.

Proposed layout, to create incrementally during implementation:

- `trials/<application>/`: small specs, synthetic fixtures, setup/reset instructions, narrowly useful checks.
- `trials/manifest.json`: pinned versions, asset references/hashes, fixture revision; no private identities or credentials.
- `scripts/trials/`: bounded platform setup/run/cleanup entry points.
- `.trial-private/runs/<run-id>/`: raw reports, screens, target logs, environment fingerprints with sensitive fields excluded, and private notes.
- `docs/trials/`: reviewed technical summaries and backlog findings only.

Each attempt gets a unique directory. Playtestr report paths must resolve to that attempt's evidence; old adjacent `.actual.txt`/`.diff.txt` files cannot be mistaken for current results. Preserve the existing historical-artifact caveat. Keep metadata bounded and explicit; never dump full ambient environment or kubeconfig for debugging.

A harness status vocabulary should distinguish passed, behavioral failure, setup failure, cleanup failure, blocked, and not run. Keep the original Playtestr report untouched. Preserve primary failure plus cleanup/evidence errors even when several occur together.

Resource operations and polling have deadlines and finalizers. On interruption, capture useful evidence before cleanup where possible. Persist exact resource ownership before mutation so interrupted cleanup can be resumed safely. Clean only paths whose resolved absolute location is within the declared trial workspace, and services whose IDs/labels match the manifest. No broad filesystem resets or infrastructure prune commands.

## 12. CI, defects, and scope control

First run locally on both platforms; then automate the exact proven recipes. A Linux CI job can provision its own disposable engine/cluster if supported. Windows jobs require confirmed infrastructure capability; do not silently skip service-dependent cases and report the matrix green.

Use finite job timeouts and artifact retention, read-only repository permissions, pinned downloads, explicit cleanup/failure paths, and narrow artifact selection. Evidence uploads run after failure without suppressing test status. Operator-owned CI proves CI feasibility, not integration into an upstream maintainer's project.

Classify findings as target behavior, target nondeterminism, fixture/harness defect, environment/setup, spec authoring, terminal rendering/input, runner lifecycle/evidence, or documentation. Capture exact reproductions and smallest useful remedies in the [observations backlog](../../trials/observations.md).

False passes, surviving managed processes, unintended data changes, and sensitive-data persistence are candidate blockers. Keep stable promotion held until relevant fixes are verified. For runner changes, add a regression test that fails before the fix; run appropriate Go tests, vet, race checks for lifecycle/concurrency changes, and affected native trials. Do not rewrite the emulator or add future sprint features without a demonstrated blocking case and a bounded design decision.

## 13. Implementation checkpoints

1. Privacy and inventory: verify ignored files, native hosts, version manifest, isolated config, and available infrastructure. Exit: exact six-cell setup plan and explicit blockers.
2. Lazygit first slice: manual baseline, native execution, independent index oracle, negative and recovery proof, cleanup. Exit: LG-01 works on both hosts.
3. Lazygit breadth: remaining required scenarios and ten-run primary samples. Exit: recorded results and bounded unresolved findings.
4. Lazydocker: endpoint ownership, fixture lifecycle, LD-01 first, then required scenarios and samples. Exit: external container cleanup verified on both hosts.
5. K9s: cluster identity/RBAC/readiness, K9-01 first, then required scenarios and samples. Exit: exact resource mutation/cancellation and cluster cleanup evidence.
6. Cross-host assessment: second-session checks, meaningful resize/Unicode diagnostics, six-cell summary, precise compatibility limitations.
7. CI and handoff: automate feasible cells, record infrastructure gaps, rank findings, identify runner candidate changes and any human adoption gates still missing.
8. Return to the deferred R2 run: inspect its actual current result once this technical campaign is assessed; investigate only if it still fails.

Each checkpoint produces a runnable, reviewable increment. Do not implement all harnesses before proving the first app's first slice. During execution, continue through authorized independent work when one prerequisite is blocked; report concrete infrastructure requirements when the user must supply them.

## 14. Definition of done

- [x] Approval file ignored and untracked; no private maintainer details in staged content.
- [x] Latest official target releases resolved once and pinned with provenance for both hosts.
- [x] Six native client matrix cells executed or explicitly recorded as blocked; blocked cells prevent a full campaign-complete claim.
- [x] Every required scenario has setup, screen evidence, applicable external oracle, and cleanup evidence.
- [x] Per-app/per-host good, intended-bad, and restored-good results distinguish assertion self-checks, fixture faults, and application regressions.
- [x] Sixty primary-slice attempts recorded without hidden retries; original failures retained.
- [x] Second-session, resize, cancellation, and relevant negative-environment cases assessed.
- [x] No unrelated Git files, Docker resources, Kubernetes contexts, or host configuration changed.
- [x] Feasible CI paths executed with evidence; unsupported infrastructure remains explicit.
- [x] Findings ranked; candidate blockers resolved or promotion held with concrete reasons.
- [x] Public summary contains only reviewed technical evidence and no endorsement or participant claims.
- [x] Parent R3's cross-language and human review/reuse gaps remain visible until actually satisfied.

## Sources to consult at version freeze

- [Lazygit repository and documentation](https://github.com/jesseduffield/lazygit): Git operations and configuration; [official releases](https://github.com/jesseduffield/lazygit/releases).
- [Lazydocker repository and documentation](https://github.com/jesseduffield/lazydocker): Docker prerequisites and interaction; [official releases](https://github.com/jesseduffield/lazydocker/releases).
- [K9s repository and documentation](https://github.com/derailed/k9s): Kubernetes interaction and configuration; [official releases](https://github.com/derailed/k9s/releases).
- [kind quick start](https://kind.sigs.k8s.io/docs/user/quick-start/): supported cluster setup and image loading. A kind-capable host is a prerequisite, not an assumption about every Windows machine.

Repository descriptions and setup references were checked when drafting. Workflow choices and priorities above are proposed trial design, not claims that these paths have already passed Playtestr.
