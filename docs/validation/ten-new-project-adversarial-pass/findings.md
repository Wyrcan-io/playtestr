# Findings: late native fixture repair and renewed qualification in progress

The historical frozen campaign at `e8682f866622442c421005c7f477cd45fcc66fc5` / `38802794545` passed the strict retained-evidence audit: 130 scenarios, 21 native project/host pairs, 2,740 ordinary final repetitions and 2,740 separate state probes, with source-fault restoration and owned removal verified. [Final report](final-report.md). The first failed frozen campaign remains rejected. Usability measurement limits and the unresolved historical macOS readiness failure remain explicit; full-product launch credit is zero. Entries below retain discovery-time status.

Latest general product repairs:

- P10: hide only the internal Windows workspace ownership marker through the native hidden attribute, preserving fixture visibility, ownership validation and cleanup. [Evidence](core/workspace-marker-visibility-repair.json).
- P11: readiness and unique recorder assertions use one synchronized rendered-screen observation. A real redraw could erase the anchor between two reads; the actual reduced failure and post-fix repetitions are retained. [Evidence](core/recorder-redraw-readiness-repair.json).
- P12: allow transient duplicate recorder anchors to resolve within the existing deadline; persistent ambiguity still fails. [Evidence](core/recorder-transient-duplicate-repair.json).
- P13: check the output cap again after the final drain before reporting an early exit, preserving the correct failure category. [Evidence](core/final-drain-output-limit-repair.json).
- P14: add ordinary Home, End, PageUp and PageDown throughout recording and replay, including native Windows key mapping; reject unsupported modified navigation visibly. [Evidence](core/standard-navigation-input-repair.json).

Latest validation findings:

- Closing CI 38831100429 caught helper exit8 in the repeated macOS stubborn-descendant control. The runner accurately reported unexpected exit and confirmed cleanup. A deterministic reader checkpoint exposes a real test-fixture bug: truncating a published heartbeat briefly yields an empty value. Atomic staging/rename fixes that reduced case and ten WSL race repetitions; contextual helper diagnostics now identify future setup errors. Exact original hosted branch and the earlier exit0 failure remain unproven. Native requalification and a new all-ten frozen matrix are required. [Preserved late failure and before/after](core/macos-stubborn-late-failure/manifest.json).

- Publishing the retained deep evidence paths exposed a real Windows source-checkout failure before test execution in runs 38830301887 and 38830302005. All 18 applicable native workflow files now supply Git core.longpaths through workflow-scoped environment configuration before checkout. The source-development guide documents the clone prerequisite. A local Windows sparse clone did not reproduce the hosted failure, so it supplies no before-fail claim; The exact failing checkout step passed in both corrected native Windows jobs, runs 38830901944 and 38830901998; the machine receipt retains their actual step metadata. [Actual errors and scope](core/windows-evidence-checkout-repair.json).

- Final publication check: generic generated-screen ignore rules excluded 209 native manifest-declared screens/diffs from Git. Narrow retained-native-evidence exceptions fixed publication; all 3,241 declared files across completed native collections now match their recorded hashes and index bytes. General generated-artifact exclusions remain active. [Before/after check](core/evidence-publication-check.json).

- Require ten state probes inside each actual completed final repetition group. Initial or recovery probes cannot replace a missing final probe. Bind final events to the current workflow run and attempt, runner, public contract and exact upstream pin. Actual Ranger and nnn group calibrations and negative checks are retained. [Audit repair](core/final-state-group-audit-repair.json).
- Ranger long native hostnames obscured meaningful path evidence; its ordinary supported title option removes that incidental header. An intermittent first-key loss was traced to startup mouse-event/input flushing; positive completed preview/counter readiness replaced header-only readiness. Original failures, source traces and corrected repetitions remain in [Ranger evidence](ranger/README.md).
- nnn corrections preserve meaningful assertions: capture the actual first list row, snapshot a genuine empty-directory counter, model rejected unmatched filter characters accurately, share operational UTF-8 inheritance, and declare a wider macOS viewport for its long native path. Four compiled C faults, including terminal-green second-line corruption, were detected with exact source/binary restoration. [nnn evidence](nnn/README.md).
- A separate macOS race-instrumented stubborn-descendant test failed its readiness step once, despite confirmed cleanup. The cause remains unconfirmed. Fifty subsequent native repetitions and the later full native suites passed; the final freeze also passed fifty repetitions. Serialized failure/screen diagnostics are now available and missing/failed repetitions block final audit. [Investigation and limits](core/macos-stubborn-investigation.json). This is not a claimed production repair.

Prepared command/control/elapsed UX assessments use synthetic fixtures, warm caches and an experienced operator. They are not independent novice studies. Configured jobs, later retries and passing terminal output alone do not establish qualification; actual reports, separately checked saved state and confirmed removal remain required.

Audit consistency: the original driver selects a reviewed Unix cancellation variant, but the first strict auditor and corpus guard looked for its base filename. A shared host-case resolver now preserves all 390 original scenario/platform selections and binds the actual variant. The real Cookiecutter Linux archive validates ten groups, 100 ordinary runs, 100 separate state probes and removal. All 30 harness checks passed on Windows (five platform skips) and Linux/WSL (two skips). No public spec, snapshot or frozen Go input changed. [Actual calibration](core/final-host-case-selection-repair.json).

Copier Windows Git-update budget calibration: the original final-series recorder timed out before its Support level prompt at 10 seconds, with the update preparation screen retained. Twenty native traced probes measured 8.14 to 9.67 seconds to that prompt and passed unchanged screen/exact-state checks. Its Windows-only budget is declared as 20 seconds before corrected requalification; Unix remains 10 seconds and all assertions/snapshots remain unchanged. This is a test-authoring budget correction, with no precise host-scheduling or production-fix claim. [Evidence](copier/git-update-budget-calibration.json).

Corrected Copier requalification passed at `087ec53d86f167dbbade3ffaa82614409da3675f` / `38799866153`: all five native jobs succeeded, with 120 ordinary and 120 separate final-group state probes on each application host, three restored source controls and owned removal. The calibration is explicit; the first failed frozen attempt remains rejected. A new all-ten freeze remains required. [Actual Linux groups](copier/corrected-native-group-check-Linux.json), [actual Windows groups](copier/corrected-native-group-check-Windows.json).

## Historical investigations

H23 — owned Rust setup: Rustup installed the requested private compiler but
then failed attempting self-update in a private Cargo home without the global
bootstrap. `--no-self-update` keeps the existing bootstrap untouched. WSL Cargo
then chose system Rust 1.75 although direct Rustup execution reported 1.97.1.
The recipe resolves and validates the canonical owned compiler and sets Cargo's
explicit RUSTC/RUSTDOC paths. Actual Windows and WSL builds passed with exact
1.97.1. MSVC's ordinary binary included a wall-clock PE timestamp; `/Brepro`
enabled exact Windows executable restoration, proved by the first actual
source mutation/restoration control. [Retained prerequisite failures](helix/setup-first-failures.json).

H24 — terminal authoring semantics: Helix retained one final newline when
changing a whole-buffer selection; the first pasted body added an unwanted
blank line detected by the independent file probe. Its Windows input path
ignored literal LF as logical Enter. Explicit named Enter between lines
preserves the unchanged intended file bytes. On Unix, Escape followed directly
by a command could parse as a combined sequence. INS/NOR checkpoints and a
previously observed error's disappearance express actual readiness without
sleeps. Historical contracts and first failures remain retained. These are
target-input/authoring findings, not a raw-byte transport or automatic-paste
normalization claim. One nested-path case preserves genuine host slash spelling
through an explicit Unix baseline; it is still one scenario.

H25 — intended maintenance: a changed document title also needs its explicitly
associated positive checkpoint updated before testing the old snapshot. The
maintenance helper now permits an explicitly selected assertion edit with the
new input, while preserving all primary contracts. The initial early assertion
failure remains in the ledger; meaningful snapshot mismatch/update recovery,
diagnosis and relocation subsequently passed. The prepared Helix operator route
used four commands and twenty recorder controls with no manual JSON edits,
excluding earlier setup/engineering/corrections. No assertion is inferred or
silently changed, and no independent beginner study is claimed.

P08 — recorder input sequence / high: native Linux state probe
`9509488d4ad2435b84f029ee8bfb99bc` rejected a genuinely new search result
because the target rendered it before the following Enter confirmation. The
recorder overwrote its pre-input screen at every key, making authoring depend
on target rendering speed. [Real reduced before/after evidence](core/input-sequence-repair/manifest.json)
reproduces the failure, then passes ten repetitions of every recorder test,
ten Unix reduced controls and ten unchanged Windows superfile state probes.
The general repair retains the first screen in an uncheckpointed input sequence;
prefix reconstruction uses the same rule. Unchanged initial captions and a
later already-satisfied result remain rejected. Contracts were not edited.
Full Go/vet, native Windows race and public examples passed; native
three-OS requalification passed at `4c90d39` / `38319592021`. The same run
qualified superfile's Linux/macOS development journeys and confirmed teardown.

T01 — target dependency / high: hosted Windows copy repetition six failed
with an unrequested help overlay. A separate race-instrumented build of the
unchanged target confirmed concurrent reuse/read of Ultraviolet's Windows input
buffer (`terminal_reader_windows.go:106` versus `terminal_reader.go:201`).
[Actual race stack](superfile/first-failures/confirmed-upstream-input-race.txt)
and diagnostic ID `1397b374ca4c49898b4d3272e99391d2` are retained. It does not
establish the precise cause of that original help event. The Windows target
path is unqualified; no retry success erases the failure and no patched target
is substituted. [Explicit host adjustment](native-host-adjustments.json) assigns
superfile to Linux/macOS and adds Windows to Glow's existing Linux/macOS plan.
The required five Windows project qualifications remain a gate, not a claim.

Later evidence updates below supersede discovery-time pending statuses in the
original table. The first failed attempts and original ledger bytes remain intact.

H18 update: source `425288ae737e6b6e525913e351cae735a2372e00` successfully
compiled the target on native Linux and Windows. All three product-control jobs
and standard smoke passed. The application jobs then failed the first checkpoint
with `LF 02-nested`, rather than the reviewed initial `LF 00-empty`.

H20 — fixture prerequisites: Git omitted the two empty directories from each
fixture tree. A reviewed `fixture-directories.json` now declares them explicitly;
setup reconstructs only bounded paths below the declared fixture roots, rejects
links/nonempty state and validates every entry before creating anything. Directory
names are now included in pre-launch provenance. The real [local regression](lf/fixture-prerequisite-repair.json)
preserves the original failure and passes the same spec/baseline after directory
restoration; traversal/no-partial-creation/nonempty-preservation calibration also
passed. This is a campaign prerequisite repair, not an application-specific core
branch or an accepted snapshot update. Native run `38311988432` at `cb34cc3`
subsequently passed all five jobs, including lf's complete Linux/Windows
development journeys and verified teardown.

P07 — named control input: the real superfile recorder rejected its ordinary
`CtrlR` shortcut (original console in `superfile/first-failures`). Support now
maps all Ctrl+A–Z names to their defined terminal control bytes, preserving
existing aliases and navigation. Schemas, contract documentation and migration
notes are updated. Ten real Windows and ten WSL reduced controls verified all
26 bytes; full Go/vet/native Windows race and public examples passed. Hosted
three-native-OS checks of this later source are pending. This general repair
does not infer application semantics or introduce target/framework branches.

H21 — Windows ledger contention: a real four-process calibration failed with
`PermissionError: [WinError 5] Access is denied` during atomic lock-directory
creation. A just-removed Windows directory can remain delete-pending. Acquisition
now retries that native error within the existing ten-second deadline; it never
steals or removes a competing lock. A persistent denial still fails explicitly.
Actual concurrent-writer calibration and deterministic transient/persistent
controls pass; an additional twenty actual four-process series passed, preserving
all 1,600 expected records with no lock left behind. This
is a campaign accounting repair, not a product behavior change.

H22 — superfile authoring/maintenance scope: empty-panel captions were assumed
incorrectly, existing captions were rejected as stale after Tab, and an existing
preview line was rejected as stale after resize. The corrected checkpoints use
fresh metadata or newly exposed preview state, with exact independent file
checks. One maintenance inspection looked for a preview token outside the
declared snapshot rows; the new assessment checks the actual in-range neighbor
name. Original attempts remain in the ledger; no reviewed primary contract was
updated to conceal these mistakes.

| ID | Class / severity | Observation | Current disposition / evidence |
| --- | --- | --- | --- |
| P05 | Windows resize / high | A continuously redrawing target changed dimensions without another CSI 8 reply; the second resize timed out | Bounded current-request post-return output fence, plus explicit semantic readiness. Actual native core checks passed at `ff38039`, `6df8c37` and `5188978`; [investigation](core/continuous-resize-investigation.json). A transport fence does not prove application readiness. |
| P06 | Windows workspace / high | Git returned long paths while a short TEMP alias produced a differently spelled managed root | Expand native created-root and cleanup parent spellings. Actual 8.3 before/after control passed on native Windows; [repair](core/workspace-short-path-repair.json). No isolation claim. |
| H12 | Python process harness / medium | CPython emitted unclosed transport warnings after owned timeout/flood cleanup | Close the verified pinned asyncio process transport after bounded drain/reap; calibration passed without those warnings. |
| H14 | Maintenance harness / medium | A second relocation assessment reused an already existing destination | Unique owned assessment path; actual meaningful manual edit/update/relocation routes passed. |
| H15 | Evidence ledger / high | Cross-OS concurrent append damaged one imported identity record | Original ledger frozen byte-for-byte; serialized v2 epoch and exact quarantine reader; only actual archived identity restored. [Audit](core/ledger-quarantine.json); real concurrent writers and unknown-damage rejection passed natively. |
| H16 | Recorder evidence / high | Buffered later controls could quit after an earlier rejection and erase the useful failure screen | Send one control per new public prompt and drain the requested failure screen before cancellation. Actual lf failed caption/precondition consoles now retain live screens. [Repair](core/recorder-protocol-repair.json). |
| H17 | Semantic accounting / high | A state probe's expected cancellation exit was logged as process passed before the semantic rejection was raised outside the harness | Completion callback validates rejection and positive state evidence before logging pass. Original ID retains its process event plus an appended unqualified semantic audit. Real zero-exit/semantic-rejection calibration passed on all three native hosts at `5188978`. |
| H18 | Target toolchain / high | Native lf compilation required Go 1.26 while Playtestr's workflow supplied Go 1.25 with switching disabled | [Exact first failures](lf/toolchain-first-failures/manifest.json). Target recipe pins Go 1.27.0 with checksum verification and owned module-cache acquisition. Local exact compiler/build passed; native retry pending. This is a target prerequisite repair, not a runner Go-version increase. |
| H19 | Retained metadata / medium | Windows checkout CRLF and Linux checkout LF changed copied license/dependency metadata between setup attempts | Retain immutable pinned Git blob bytes for license/go.mod/go.sum; actual source-file and binary inventories still describe each host's real compiled inputs. |
| C02/C03 | Explicit application scope | Copier file-list order and optional Git fallback warning differed across hosts | Deliberately reviewed semantic answer rows plus independently required exact generated/protected files. Historical full captures remain. Native source `6df8c37` passed twelve workflows, faults, 120 ordinary and 120 state executions per host, and owned deletion. Git merge/conflict correctness remains excluded. |

Source `5188978057d4a31aaf752a1dafb9fbb73488f1ea` passed all three native core
jobs and standard smoke run `38119968121`. The adversarial run `38119968128`
failed both application setup jobs before lf qualification because of H18;
core success does not turn the overall run or project qualification green.

C03 — Host Git fallback output: the next native Linux/Windows attempt reaches
the real Git update and exits 0, but emits an additional generic Git-version
warning. Pinned Copier first requests `--inter-hunk-context=-1`, catches a Git
execution error, retries with zero inter-hunk context, and prints this warning.
Do not infer failed file updates from the warning, or claim correctness from
exit 0. Preserve both native mismatch reports/screens/diffs and both earlier
full-screen contracts. Publicly review explicit update version/answer rows
1–3, exclude this trailer, and independently verify exact v2 files, absence
conditions and preserved committed local customization on every state probe.
Complex merge/conflict correctness remains untested. This is an explicit target
scope/prerequisite choice, not a Playtestr normalization change or an upstream
repair. Native Git versions are separately recorded; full hosted state and
repetition requalification remain pending.

H15 — Shared ledger integrity / high: native-evidence import overlapped a WSL
recorder finish and overwrote part of an imported identity event. Preserve
epoch 1 byte-for-byte, including its exact malformed fragment and recorded
checksum in [the quarantine manifest](core/ledger-quarantine.json). New writes
use `attempts-v2.jsonl` under a bounded atomic-directory lock shared by Windows
and WSL. Readers recognize only the exact quarantined fragment in the exact
frozen file; any unknown damage is an error, never a green record. Restore the
one lost identity event from the actual retained native Ubuntu artifact and
append an explicit restoration audit with its archive-ledger checksum. Four
real concurrent writers preserve all 80 exact synthetic records; an unrelated
malformed ledger is rejected. Thirteen local harness controls pass (two native
symlink prerequisites skipped), without transport warnings. Hosted reruns
remain necessary. No original damaged bytes or failed attempts were rewritten.

P06 — Windows workspace interoperability: native run 38115136553 reached
Copier's Git update, then its actual path containment check rejected the short
`RUNNER~1` temporary path against Git's `runneradmin` long spelling. Expand the
newly created owned workspace and cleanup's temporary-root comparison through
the native long-path API. Preserve ownership-marker and reparse checks. A real
short-alias/ConPTY target fails with the original launch spelling and passes
ten repaired runs with process and workspace cleanup. The first candidate
exposed cleanup's own spelling mismatch and was rejected before correction.
[Before/after evidence](core/workspace-short-path-repair.json). Native
application requalification is pending.

C02 — Target output determinism and explicit assertion scope: Copier's actual
multi-file create/conflict log order differs between fresh filesystems. Native
Linux failed its full-screen baseline while answers and exit matched. Preserve
the old full-screen contracts and failure; publicly record deliberately
selected stable answer rows for four multi-file workflows. Each still executes
all meaningful prompts/actions and exact exit, and independently checks exact
generated/protected files. Excluded listing order is explicitly untested; no
automatic sorting, masking, or inferred filesystem assertion was added to the
runner. Actual fault detection/restoration must rerun against these revised
contracts. Windows and exploratory Linux/WSL reviewed row captures succeeded;
hosted qualification remains pending.

H13 — Instrumented stress-test budget: native macOS ordinary rapid-key control
passed in 0.73 seconds; the race run matched all 320 expected bytes then exceeded
its test-only 15-second whole-run deadline while waiting for exit at step 323.
Retain the failure, use a 60-second test-only whole-run budget for this bounded
stress helper, and keep exact byte assertions and per-step budgets unchanged.
No product default or project deadline changed. Native race requalification is
required; this is not a zero-failure or performance claim.

H14 — Repeated maintenance collision: a second legitimate assessment found the
earlier owned relocation directory. Use a unique campaign assessment ID in the
relocated checkout name. The failed attempt and earlier result remain evidence;
the corrected public edit/diagnosis/update/replay/relocation route passes.

P05 — Windows repeated-resize defect: a real continuously redrawing target
reported the second requested dimensions while ConPTY emitted no second CSI 8
resize confirmation. The previous exact-confirmation-only barrier timed out.
The candidate also accepts an output read begun after successful native resize
return, for the current request only. This fences transport progression; queued
output does not prove application readiness, which remains an explicit screen
assertion. A pre-return read and superseded read are rejected. Ten fresh real
12-resize repetitions passed locally. The first combined ten-run command
exceeded its 120-second harness budget and remains incomplete evidence; the
300-second retry kept unchanged product deadlines. Native requalification and
the historical wizard stability check are pending. [Before evidence and design](core/continuous-resize-investigation.json).

H12 — CPython harness cleanup: calibration completed but emitted destructor
warnings for unclosed Proactor subprocess transports after loop shutdown.
Explicitly close the pinned Python 3.12 process transports after bounded
drain/reaping while the loop remains live, including taskkill and load-worker
transports. Eleven controls reran without warnings locally (two symlink tests
skipped for unavailable Windows privilege); native checks remain required.

| ID | Class / severity | Observation | Disposition / evidence |
| --- | --- | --- | --- |
| H01 | Harness / high | Earlier helper used unbounded output capture and checks separate from repeated runner attempts | New async capture has independent output/time bounds and unique append-only launch/finish IDs. State checks use the current recorder workspace and compare the approved screen. They remain separately counted executions, not public filesystem assertions. |
| H02 | Harness / high | Independent oracle failure killed recorder abruptly, retaining one owned workspace | Graceful `/quit` before forceful bounded cleanup; first retained directory removed only after exact attempt log, ownership marker, no live reference and link checks. Subsequent failures report graceful recorder cancellation. |
| H03 | Synthetic fixtures / medium | JSON expectation escaped café whereas reviewed template writes UTF-8; default Windows file writes introduced CRLF | Explicit UTF-8 exact expectations and LF in owned synthetic fixture/hook writers. First mismatches retained; no target or Playtestr fix claimed. |
| H04 | Harness / medium | Review-screen comparator removed meaningful leading spaces | Preserve exact displayed baseline indentation; ignore only the console's extra blank separator. First rejection retained. |
| H05 | Native Python harness / medium | Flood/timeout shutdown left asyncio pipe transports open at loop closure | Close input, await pipe shutdown and boundedly drain stopped output. Real subprocess flood/timeout calibration rerun without transport warnings. First cleanup implementation's small drain bound incorrectly masked the original overflow; bound corrected before credit. |
| P01 | Target/platform behavior | Linux renders Ctrl+C as `^C`; Windows does not | Preserve Windows baseline and explicitly reviewed Unix variant. Both preserve exact nonzero exit, cancellation marker and independent absence/protected-state checks. The Linux mismatch is retained; no stripping or assertion weakening. |
| H06 | Harness / medium | Maintenance invoked `test --artifacts-dir` with an absolute path, producing references the documented offline renderer deliberately refuses | Use the documented relative evidence layout. No renderer security contract weakened. First diagnosis error retained; corrected mismatch → HTML → selected update → ordinary pass succeeded. |
| H07 | Harness / high | First native Linux flood calibration deadlocked while awaiting the killed process before draining its full stdout pipe | Kill the owned process group, close input, drain within independent byte/time bounds, then reap. Actual failure run 38044385441 retained; corrected real flood/timeout controls pass locally on Windows and Linux/WSL. Native requalification required. |
| H08 | Setup harness / medium | Hosted Linux pip installation succeeded, then freeze incorrectly selected the WSL-only uv variable | Select freeze mechanism using the same explicit install route. Original setup traceback/artifact retained from run 38044385441; hosted requalification pending. |
| H09 | Cleanup recipe / medium | Native Windows completed 100 ordinary repetitions and 100 state probes, then refused upstream's tracked documentation symlinks | Retain the failed teardown as an incomplete project gate. Verify canonical owned path and reparse tag, unlink only recognized owned symlinks through nonrecursive native APIs, then remove the ordinary owned tree. Unknown tags/junctions remain rejected; native replay and deletion must actually rerun. |
| C01 | Scope / high validation risk | Real generated-file corruption can retain a passing terminal transcript | Actual Cookiecutter source write is corrupted; ordinary unchanged terminal test stays green, independent exact-file oracle must reject. Recovery restores exact source/spec/baseline hashes. No automatic filesystem correctness claim. |
| H10 | State oracle / high | Resolving an expected path before link inspection concealed an inside-workspace symlink to a correct file | Inspect every lexical path component before resolving. Reduced real-file/link calibration passes on Linux/WSL; local Windows explicitly skips because native link creation is unavailable. Native hosted calibration remains required. No public runner change. |
| P02 | Native Windows / high investigation | Run 38045564219 reproduced historical wizard recovery failure at step 5 after text, resize and Enter; assertion timeout, confirmed process/workspace cleanup | First log and report retained. Smoke recipe omitted the failing screen because its default artifact was beside the generated spec outside uploaded evidence. Recovery now explicitly writes its screen into the retained artifact tree. A bounded identical-action reproduction series is underway; no causal diagnosis yet. |
| P03 | Core input / high | A backend returning a partial write without an error was silently accepted as a complete input action | Reject with `io.ErrShortWrite`. A reduced faulty writer forwards one real byte into a real PTY: removing the guard fails, restoring it passes, with actual target cleanup in both attempts. [Repair evidence](core/short-input-repair.json). This is independent of P02 and does not claim an OS short-write occurred there. |
| P04 | Windows lifecycle / high | Immediate detached child and grandchild survive Job Object cleanup while the runner reports confirmed exit | Create the target suspended, attach its Job Object, then resume its initial thread. The same real ConPTY test removes only the new startup guards: both generations survive and independently verified exact-handle fallback kills them. Ten fresh repaired controls pass; local full Go/vet/race pass. [Evidence](core/startup-repair.json). Native requalification pending. |
| H11 | Harness / high | An exception during final pipe drain/reaping could replace the original failure and omit the finished ledger record | Separate cleanup errors, always retain the completed attempt, preserve the original exception, and reject otherwise green commands with failed cleanup. Two fault-injected cleanup calibrations use real processes. Future attempts also capture current target source-file hashes, including deliberate mutations. Earlier ledgers remain unchanged. |

P02 update: pristine target public replay failed 3/500; an instrumented target failed 1/500 and confirmed receipt of all five name bytes. A real-session raw-stream probe failed at iteration 249 and retained successful writes of both name and CR; further output arrived after cleanup supplied another input event. Native key-down/up Enter encoding still failed 1/500 public replays and was rejected and removed. A Windows resize barrier observes the exact current ConPTY resize confirmation before advancing input. The bounded acknowledgment probe passed 500 original-backend sessions, then the candidate passed 500 unchanged-action public replays, full local Go/vet and race checks. Native requalification remains required. The precise internal OS wake-up mechanism and earliest historical failure remain unproven.

One discarded probe variant constructed a second unused PTY before replacing the first. Its results are excluded as harness ownership evidence; the corrected constructor acquires exactly one backend and reran 500 sessions. No external-project scenario credit comes from these diagnostic probes.

Attempts created after the provenance repair retain runner bytes and exact spec, fixture and snapshot hashes before execution. Earlier attempts retain their original evidence and separate source/contract inventories; their ledgers are not retroactively rewritten.

Initial direct public smoke commands and the initial startup diagnostic preceded attempt registration and are excluded from append-only campaign counts. Registered startup before/after evidence is retained separately. The initial basic route used an already prepared control sequence; its 3.811-second execution measurement is not total authoring effort. A later bounded public Cookiecutter route measured 65.078 active operator seconds, three shell commands, twelve recorder controls and zero manual JSON edits. Prior project knowledge, prepared fixtures and warm caches remain confounders; this is an operator assessment, not novice usability evidence.

Native source `3154500e1e2a576378a951366cfa8e008f6c3441` passed the wizard reproduction and standard recovery smoke on all three OSes. This supports the measured resize synchronization repair; it does not prove the earliest historical timeout's internal OS mechanism. P04 is a separate subsequent finding requiring its own native requalification.

Native update: run 38051205443 passed all five jobs at `d9c5c46130f67e6e99d76ae289afa6ce439f1154`, including real Windows P04 before/after rejection and ten restored controls, all applicable core checks, Cookiecutter Linux/Windows faults/repetitions/state and owned deletion. H07?H10 native rechecks also passed. Standard smoke run 38051205435 passed all three OSes. Earlier pending-native table text describes discovery-time disposition; these actual subsequent results resolve those development requalification gates. H11 calibration intentionally retains separate synthetic cleanup errors.


P09: Glow exposed a general terminal-environment precedence defect: an explicit or selected inherited TERM was silently replaced by xterm-256color. Six real v1/v2 PTY cases failed before the fix; eighty cases each passed on Windows and WSL after it. Defaults remain stable without ambient inheritance, and literal values win. Full local Go/vet/race and public examples passed. Native three-host validation is still required. Terminal replies remain outside scope. See core/terminal-profile-repair.json and Glow first-failure evidence.

T02: Pristine pinned Glow Windows input has an actual Ultraviolet shared-buffer race, confirmed by the separately instrumented target on its first public workflow with exit66. Ordinary tests passing do not qualify that host. Linux/macOS remain the intended Glow hosts; the fifth Windows gate provisionally moves to Yazi. No upstream source repair or outreach is performed.

H26: A native artifact arrived between listing/downloading artifacts and collection, leaving an incomplete destination. Collection now preflights downloads and explicitly resumes incomplete collections while refusing changed retained bytes or completed-history overwrite. Reduced missing-archive/conflict/completed-history checks and actual resumed collection passed.

H27: Generated setup commands built a target in an owned directory without exporting its PATH for later Actions steps. The setup recipe now explicitly appends the verified owned directory to GITHUB_PATH. A real temporary control-file calibration preserved earlier entries and exported only the target directory; native/generated workflow inspection remains distinct from a real PR journey.

Execution correction: live Windows step metadata in run38469407174 misrepresented an application run as a stuck Go prerequisite. Cancellation interrupted actual repetitions after faults had restored successfully. The real archive is retained, the wrong interpretation is explicitly corrected, and that retry receives no qualification credit. The prior complete Windows run and corrected complete Linux run independently qualify Helix development. Future execution must not cancel a healthy bounded application run based solely on incomplete live step metadata.


H28: The Glow resize recipe sent viewport-dependent G before target redraw; native Linux accurately failed at paragraph74/92%. Add the existing observed wait_for_redraw action immediately after each resize and expose /redraw through the generic campaign control encoder. Original contract/failure retained. Ten fresh ordinary and ten separate state probes passed on WSL; the final baseline is byte-identical. Native requalification remains pending. This fixes authoring synchronization, not the target or product deadline.


H29: Actual WSL lock-directory acquisition returned missing-path while the Windows collector shared the ledger. Retry only when the parent remains an existing directory and within the unchanged ten-second deadline; never recreate a missing parent or remove another writer lock. The new reduced case failed before the repair; all17 calibrations passed on Windows and WSL afterward. Interrupted attempt4f88f8ba2f1e4ce988049aae6238aff1 remains uncredited.

H30: Glow Enter could apply an old multi-result filter before the asynchronous new query completed, leaving the UI in its single-result list. Every affected selection now waits for its fresh selected-result marker before Enter. The original macOS load failure/contracts remain retained; six final baselines are identical. Ten ordinary plus ten state cases and repeated public UX/maintenance/rerecord passed on WSL; native requalification remains required.
