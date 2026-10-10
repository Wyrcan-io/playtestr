# Ten-project reliability pass — completed 10 October 2026

All ten distinct real applications completed reviewed public-recorder user journeys, meaningful target-regression detection and unchanged-contract restoration. Final qualification on Playtestr **`53561e6cbef4c80a25893c2f25be5a0979442103`**: **33 scenarios, 330 fresh passing repetitions, 10 detected target regressions, 33 restored scenario passes, 17 independently checked stateful scenarios**. Initial accepted journeys also supplied 330 fresh repetitions on the then-current source; superseded tests and rejected attempts are excluded.

| Project | Exact upstream revision | Language / terminal stack | License | Scenarios / final passes |
| --- | --- | --- | --- | --- |
| [gum](gum/README.md) | [879f048103adf0214b85943b52d8d65b08d772c5](https://github.com/charmbracelet/gum/tree/879f048103adf0214b85943b52d8d65b08d772c5) | Go / Bubble Tea v2 | MIT | 5 / 50 |
| [fzf](fzf/README.md) | [b1be3a8be1b833ce5b92fbbac11637643d60a046](https://github.com/junegunn/fzf/tree/b1be3a8be1b833ce5b92fbbac11637643d60a046) | Go / custom VT renderer | MIT | 3 / 30 |
| [micro](micro/README.md) | [02164788bd29c90456e39f976a566899d39579e4](https://github.com/micro-editor/micro/tree/02164788bd29c90456e39f976a566899d39579e4) | Go / tcell | MIT | 3 / 30 |
| [lazygit](lazygit/README.md) | [c5f7158154602d23b0750d4304c73e2aead8df5b](https://github.com/jesseduffield/lazygit/tree/c5f7158154602d23b0750d4304c73e2aead8df5b) | Go / gocui | MIT | 3 / 30 |
| [gdu](gdu/README.md) | [387cf50377e53bad628603658cfb76fd4a54d718](https://github.com/dundee/gdu/tree/387cf50377e53bad628603658cfb76fd4a54d718) | Go / tview/tcell | MIT | 3 / 30 |
| [visidata](visidata/README.md) | [dd1a9f0a53fe4bf030db939b06c73cb665406d4a](https://github.com/saulpw/visidata/tree/dd1a9f0a53fe4bf030db939b06c73cb665406d4a) | Python / curses | GPL-3.0 | 3 / 30 |
| [litecli](litecli/README.md) | [aa53bb0c1530cd1dfb30534babb0bf47df33c60a](https://github.com/dbcli/litecli/tree/aa53bb0c1530cd1dfb30534babb0bf47df33c60a) | Python / prompt-toolkit | BSD-3-Clause | 3 / 30 |
| [harlequin](harlequin/README.md) | [2c6e7b21d42e10b08730ca89b0cce2f40c42dab3](https://github.com/tconbeer/harlequin/tree/2c6e7b21d42e10b08730ca89b0cce2f40c42dab3) | Python / Textual | MIT | 4 / 40 |
| [npkill](npkill/README.md) | [620f011bf79ebf345d76d916448b37840b30e2a3](https://github.com/voidcosmos/npkill/tree/620f011bf79ebf345d76d916448b37840b30e2a3) | TypeScript / custom terminal renderer | MIT | 3 / 30 |
| [create-vite](create-vite/README.md) | [8a4c19cfc035f2dd203f2fa6d00ab9256a5e77c9](https://github.com/vitejs/vite/tree/8a4c19cfc035f2dd203f2fa6d00ab9256a5e77c9) | TypeScript / @clack/prompts | MIT | 3 / 30 |

## General fixes delivered

- `06af0c0`: recorder rerecord reports the actual newly created working directory, allowing inspection of the correct saved state.
- `c8274d5`: explicit versioned physical-row snapshots, strict validation, recorder support and transactional selected updates. Reviewers choose meaningful rows; failure evidence preserves the full viewport.
- `4a1f41d`: preserve legitimate empty argv values; add CtrlA/CtrlK and reconcile named-key schema validation. Empty executable/NUL remain rejected.
- `53561e6`: CtrlJ emits LF independently of Enter's CR, enabling documented terminal shortcuts with actual PTY coverage.

Reduced regressions exercised failing behavior before fixes. No application-name branches, framework dependencies, AI inference or automatic baseline acceptance were added.

## What actually ran

All ten applications ran in real Linux PTYs on Ubuntu WSL2 amd64, using exact upstream source and synthetic state. Five Go targets were built on Windows for Linux and executed on Linux; cross-compilation itself supplies no native-host compatibility claim. Python applications used isolated native Python 3.12 environments; Node applications used verified portable Node 24.7.0 and explicit pinned build prerequisites. Actual target/binary/module/tree hashes live in each result. Source/dependency pins and [toolchain integrity](toolchains.json) are retained.

Each final scenario ran ten times from freshly copied fixture/HOME/temp/process state: five normal and five with a bounded external CPU worker. This supplies load variation, not an invented application startup-delay mechanism. An additional real target mutation per project produced a red result; restored original bytes passed the same contracts. Independent bounded file/Git/SQLite/manifest checks inspect persisted state before teardown. Six additional saved-state negative controls rejected real corruption despite success-looking UI. The public runner does not yet provide these independent file/database assertions; they are explicit campaign-harness checks, bounded to 10 seconds and 4 MiB. [Real-process harness controls](state-probe-controls.json) cover success, nonzero exit, flood, timeout and reaping.

The runner's **actual native Linux, macOS and Windows** full tests/vet/race/public recorder acceptance passed on exact final source: [run 37654006327](https://github.com/Wyrcan-io/playtestr/actions/runs/37654006327). [Successful job identities](native-final-source.json), [prior fix runs](native-validation.json), and [local final tests/vet/race/examples](local-core-checks.json) are separate evidence. This does not imply all ten upstream applications ran on all three hosts.

Generated per-project workflows were inspected and their equivalent public commands executed locally. They target Linux and explicitly acquire/build prerequisites; they are reproducible setup recipes, **not ten executed hosted PR journeys**. No new PRs, issues, releases, deployments or outreach were performed for this pass.

## Failed attempts and limitations

Per-project reports retain failure categories/steps/cleanup, hashes, rejected recorder captures, actual regression patches, state-corruption evidence and scope exclusions. Retained-artifact counts include retries and intentional negatives; they are not independent adoption, total-ever execution counts or a zero-flakiness claim. Early passing retries overwritten before history preservation cannot be recovered. Original runner identities remain historical; final source/hash associations are explicitly separate.

Notable findings include random-workspace and timing-row snapshot instability; stale/ambiguous readiness; mounted Python startup cost; an upstream Windows-invalid path; WSL `/tmp` removal; explicit prompt-toolkit CPR opt-out; save-path/UTF-8 operator mistakes; synthetic Git fixture mode/line-ending portability; and a Harlequin recovery test that mechanically passed without actual query results. That weak test was rejected and replaced with positive result-grid proof. App-supported configuration, meaningful anchors and reviewed physical rows resolve setup/authoring issues without silent normalization.

Candidate accounting: ten selected/executed/completed, zero substituted or excluded journeys. Three additional [reserves](reserve-screening.json) were screened from primary GitHub metadata at final review, not before the original selection; they receive no execution credit. This sequencing deviation is explicit. Rejected recorder attempts and blocked build/setup attempts belong to the selected journeys and do not create additional projects.

The historical Windows wizard timeout in [run 37538837223](https://github.com/Wyrcan-io/playtestr/actions/runs/37538837223) remains unexplained. Forty bounded local repetitions of its retained sequence passed; [report hashes and denominator](windows-wizard-reproduction.json). Original failed evidence is preserved. Later green runs do not establish a causal fix; broadened Windows reliability remains a measured risk.

Only trusted synthetic targets were executed. PTYs and subprocesses are not isolation. Mouse/style/grapheme completeness, terminal-query replies, secret handling for arbitrary apps, network/credential integrations and whole-application coverage are outside these scenario claims. See each scope table. New source features are not a claim about older published archives; no release was made.

## Reproduction, retention and next gate

[Machine ledger](ledger.json), [frozen source/binary hashes](final-runner.json), [findings and dispositions](findings.md), per-project specs/baselines/fixtures, exact licensed patches, locks, recipes, workflow templates and compact reports remain. Raw bounded evidence is ignored under `artifacts/ten-project-user-pass`; hosted artifacts have their original retention and are not promised after expiry. Patch/license attribution identifies every pinned upstream; fixture data is synthetic. Operator elapsed measurements use warm caches, not independent-user research; interrupted historical repeats are not assigned invented elapsed figures.

Every temporary application checkout, binary, native environment and task-specific dependency cache was removed after evidence/process checks. [Final cleanup verification](cleanup.json) and [package checks](package-checks.json) are recorded separately; shared pre-existing Go caches/compiler and Playtestr itself are preserved.

This completes the **early reliability portion of P5**. P3 paid review, P4 commerce, remaining whole-product P5 and the full campaign remain unqualified. **Complete-product credit: 0/100.** It is evidence for tested terminal workflows, not readiness for commercial launch or proof of demand.
