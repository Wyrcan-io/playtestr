# R3c cross-stack validation record

Status: complete on `v0.1.0-rc.2`, 12 September 2026. This is operator-run technical evidence, not independent adoption. Raw reports, screens, hashes, manifests, setup logs, exploratory failures, and mutation artifacts remain in ignored storage under `.trial-private/r3c/`.

## Result

Nine distinct released applications ran on Windows amd64/ConPTY and WSL Linux amd64/Unix PTY. A real-terminal manual baseline established the keys, focus, result, and exit behavior for each of the 18 cells before its final automation. All cells then passed their frozen three-attempt primary sample: **54/54** without automatic retries. Every cell also has a controlled fixture failure, restored pass, application cancel or invalid-input path, runner cancellation after positive readiness, confirmed target cleanup, and a fresh second session. Full-screen flows exercised `120x40 -> 80x24 -> 120x40`; prompt flows exercised editing or validation and Unicode where supported.

The runner was the extracted public `v0.1.0-rc.2` asset. Windows `playtestr.exe` SHA-256 was `2747C0AEEDF02B128A196E2F589417824603AAB89A43120F7270ECF7EAA3C1B0`; the Linux binary SHA-256 was `5DD68B06509611E2574E28C4D44D9049338815B655319778A8104BBF0D2706E8`. Both reported `v0.1.0-rc.2`. “Linux” below means Ubuntu 24.04.3 under WSL2, kernel 6.18; it is not a claim for every Linux distribution. No macOS real-application claim is added.

| ID | Pinned application | Useful task and independent oracle | Windows | WSL Linux |
| --- | --- | --- | --- | --- |
| PY-01 | [Posting 2.10.0](https://github.com/darrenburns/posting) | Send an HTTP GET to a private fixture server and inspect its Unicode response; access log plus fixture marker | 3/3 pass | 3/3 pass |
| PY-02 | [litecli 1.17.1](https://github.com/dbcli/litecli) | Insert/read a Unicode SQLite row and use history/cancel; SQLite query plus unchanged neighbor row | 3/3 pass | 3/3 pass |
| PY-03 | [mitmproxy 12.2.3](https://github.com/mitmproxy/mitmproxy) | Inspect request headers and Unicode response in an offline flow; parse the flow independently | 3/3 pass | 3/3 pass |
| RS-01 | [bottom 0.14.9](https://github.com/ClementTsang/bottom) | Search a known live process, open help, resize, and quit; exact external process identity and fixture hash | 3/3 pass | 3/3 pass |
| RS-02 | [GitUI 0.28.1](https://github.com/extrawurst/gitui) | Stage one Unicode file in a repository whose path contains spaces; Git index bytes/path plus unchanged neighbor | 3/3 pass | 3/3 pass |
| RS-03 | [television 0.15.9](https://github.com/alexpasmantier/television) | Filter and select one Unicode line; exact selected stdout and unchanged candidates file | 3/3 pass | 3/3 pass |
| JS-01 | [npkill 0.12.2](https://github.com/zaldih/npkill) | Navigate to a known dependency tree in dry-run mode; exact marker and neighbor hashes | 3/3 pass | 3/3 pass |
| JS-02 | [create-vite 9.2.1](https://github.com/vitejs/vite) | Scaffold a Vanilla JavaScript project; exact file manifest and package fields | 3/3 pass | 3/3 pass |
| JS-03 | [ipm-cli 1.3.3](https://github.com/inkdropapp/ipm-cli) | Reject an invalid type, then scaffold a dark Inkdrop theme; exact package fields and CSS manifest | 3/3 pass | 3/3 pass |

## Frozen provenance

Windows used Python 3.12.7, Node.js 24.7.0, npm 11.5.1, Git 2.45.1, and the pinned standalone Rust binaries. WSL Linux used Python 3.12.3, Git 2.43.0, checksum-verified Node.js 24.7.0, and isolated native virtual environments. Python wheels, npm tarballs, Rust archives, package metadata, locks where supplied, and inspected npm lifecycle scripts are retained privately. Target archive/package SHA-256 values are:

| Target | SHA-256 identity |
| --- | --- |
| Posting wheel | `C0FD982A22DDEB9FB01F85F89045600F440452DDA7B47D69EB0944264A3B88DC` |
| litecli wheel | `4D1743DFA086B178DE6543B36F1780203E8A9BC99643AF4B721F6C880C5AA7A9` |
| mitmproxy wheel | `DF75CCD15CCB39AB55CE9DD4130312270E8BA208EB927A7CBE50CB52678EC722` |
| bottom Windows / Linux | `01660721B0FDC72B191F2B27B78DC9A3087AEB7B3FAD4A890C53870089D6B500` / `E0C325829E8BDCEA25A8A7651DA05DBB6F1FC109AC5D2F0187867D3D5D9C0DF8` |
| GitUI Windows / Linux | `FAB116CCDF9AE4E17378DB912D76CC26E60AEFD2226F44E665120DEA166867E4` / `F6149B9AE203397158B0C89C13CFDE718E7121D3D3CD2EBC597F93D6628D9B5B` |
| television Windows / Linux | `ABFBB2A9989CC633F4467DD9026EF84E63969ACAA87C69541073226533236ECB` / `87D47D071F3C3BAC939B1E9B2C63E45C299C9AD31CF8711F63DEDE614D0C6608` (matched upstream checksum files) |
| npkill npm tarball | `039D6C3118667D1AE53751E45E8BD6B97C32CBBE7F7416CA4B7C9FC4C272C399` |
| create-vite npm tarball | `4DD92D0E734E96E88EC8AFD8C0153F6A9446156205460A995B978B63B49B4EB8` |
| ipm-cli npm tarball | `E7A33CE7CF997A24E6C27D81219D0C6B6497E2F254AF6D2D41D33A5C529006DD` |

The applications' package metadata recorded their licenses (Apache-2.0 for Posting, BSD for litecli, MIT for the other selected packages/repositories) and the retrieval date. No global package installation or personal application configuration was used.

## Nine technical records

Each row above corresponds to one record whose two host cells share the task but retain separate installations, configuration, reports, postcondition output, and reset evidence.

- **PY-01:** a loopback-only HTTP server served a unique JSON fixture. The spec opened the request, asserted the actual body after submission, resized twice, and exited by application cancel. A missing marker failed at content readiness and restoration passed. The independent access-log check is implemented by [check-http-get.ps1](../../scripts/trials/oracles/check-http-get.ps1).
- **PY-02:** isolated SQLite databases started from a byte-stable baseline. The primary inserted `PLAYTESTR-PY02` with a lambda-valued field, queried it, recalled history with ArrowUp, cancelled the edit, and quit. A database without the expected table failed and restoration passed; invalid SQL left the result table unchanged.
- **PY-03:** mitmproxy ran with its network listener disabled and loaded one synthetic HTTP flow. Request and response tabs exposed the known header/body; the external oracle parsed URL, header, and body from the flow file and checked its hash was unchanged. A flow containing only `BROKEN-FLOW` failed, and rejecting then accepting the quit prompt covered application cancellation.
- **RS-01:** a dedicated helper process with an exact executable path supplied the selectable row. The target searched it, closed help, redrew at both sizes, and quit. Absence of the helper caused the intended assertion failure; Playtestr cleanup did not kill the external oracle process.
- **RS-02:** a disposable Git repository contained one selected Unicode change and one neighbor. The flow staged only the selected path, while `git diff --cached` proved the exact staged bytes and the neighbor hash remained stable. Cancel left the index unchanged. Configuration and `safe.directory` were isolated to the trial.
- **RS-03:** television read three local candidate lines and returned the exact Unicode selection. A marker-free candidates file failed, restoration passed, and Escape produced no selected output. Config/data directories were isolated on both hosts.
- **JS-01:** npkill scanned two tiny local fixture trees in `--dry-run` mode. The selected marker and adjacent tree remained byte-identical. Renaming the selected `node_modules` directory produced the intended miss, and invalid navigation/cancel did not delete anything.
- **JS-02:** create-vite selected Vanilla then JavaScript and produced a fixed local project. The oracle checked the package name/scripts and a known file manifest. A renamed template failed, restoration passed, and an edited prompt followed by Ctrl+C produced no project.
- **JS-03:** ipm-cli rejected choice `9`, accepted a theme/dark selection, and generated the expected package plus three layered CSS files. Renaming the theme template caused failure; a collision experiment was retained but not counted because this target merges/overwrites the controlled directory. Ctrl+C produced no package.

## Application regression experiments

These are separate from fixture faults and are explicitly synthetic; they are not upstream defects.

| Ecosystem | Reversible change | Bad result | Restored result |
| --- | --- | --- | --- |
| Python | litecli's visible one-row status was changed from `Query OK` to `Query MUTATED` in the isolated 1.17.1 install | Target launched and wrote the exact Unicode row, while the unchanged spec failed at the status assertion | Original source hash restored; same primary behavior and SQLite oracle passed |
| Rust | bottom source tag `0.14.9` (`e22236a928eeb876b2ccaad2f3d1ce5f6450281a`) changed the rendered process title to `BROCESSES`; a locked release binary was built | Mutated binary launched and failed at the `Processes` assertion; the external marker process survived | Checkout restored clean, official binary restored into the same test path, and the same spec passed |
| Node.js | ipm-cli's visible completion text changed from `Created theme` to `Mutated theme` in the isolated 1.3.3 install | Target launched and generated the correct theme, while the unchanged spec failed at the completion assertion | Original source hash restored; same flow and package/CSS oracle passed |

The first Rust experiment changed a layout-type label that was not rendered by this flow; its passing result is retained as a useful demonstration that a mutation is not evidence unless it affects the observed behavior. A corrected rendered-title mutation is the counted experiment.

## Findings and disposition

No Playtestr correctness, lifecycle, packaging, or security blocker was found. Every runner cancellation returned 130, reported `cancelled`, and confirmed target process-tree exit. Expected target/assertion failures returned 1 and retained a final screen; application exits and external fixtures were kept distinct.

| Finding | Classification and disposition |
| --- | --- |
| Windows npkill and ipm-cli each produced an intermittent empty initial screen during pre-sample/cancellation or mutation setup; immediate diagnostic reruns launched normally, and the frozen 3/3 samples were already complete | Target/runtime/PTY startup observation. The ipm-cli pre-sample artifact is retained. The npkill pre-sample artifact was accidentally overwritten by its diagnostic rerun; that evidence-retention error is recorded here instead of presenting the rerun as the original. Neither event is counted as a primary pass, and neither reproduced deterministically; track if Node startup recurs. |
| Posting initially raced while opening a collection, so a screen match could be followed by a target `NoMatches` crash | Spec synchronization/target behavior. The final useful flow waits on the submitted response and passed both hosts; the failed exploratory attempt remains retained. |
| Posting's WSL virtual environment on the mounted filesystem imported too slowly | Setup environment. Moving only the isolated environment to native `/tmp` resolved it; candidate binary and fixtures remained the pinned ones. |
| GitUI/libgit2 could not canonicalize the sandbox-owned Windows repository | Test infrastructure. The final Windows runs used an explicitly isolated Git config under command-specific elevation; no personal config changed. |
| Windows PowerShell 5 reads BOM-less UTF-8 scripts as the active ANSI code page | Harness/documentation friction. Campaign launchers explicitly read UTF-8; target specs remained UTF-8 JSON. |
| ipm-cli's collision state did not produce the proposed fault | Oracle/fixture design. Preserved as non-sensitive exploratory evidence; the counted fault removed the selected template. |
| Per-application active authoring minutes were not independently instrumented; filesystem timestamps span setup breaks and cannot measure hands-on time | Measurement gap. Qualitative setup/custom-script friction is recorded here; no fabricated duration is reported. Add an explicit time log to later participant trials. |

## R4 handoff

R3c's technical entry gate was accepted for the exact `v0.1.0-rc.2` bytes and tested host labels above. R4 subsequently completed the public-contract audit, maintenance/release documentation, stable-version native builds, stable archive checksums, public installation verification, and the nine-workflow refresh against the actual stable bytes. Stable v0.1.0 was published from commit `4ed8884e674f6a2625034850073b648d7a7b2aa2` on 12 September 2026. Independent review, voluntary reuse, and participant-owned CI remain open under R3 after publication.

Final reconciliation re-read all 126 primary/fault/recovery/second-session/runner-cancel reports used by the compact audit: every primary set was 3/3, every controlled fault was `failed`, every recovery and second session was `passed`, and every runner cancellation was `cancelled` with confirmed cleanup. `go test ./...`, `go vet ./...`, the project-local Windows race script, the demo build, and both menu example specs passed. The final `go run` emitted a non-fatal module stat-cache access warning from the sandboxed user profile while both examples passed; no repository or product result depended on that cache write.
