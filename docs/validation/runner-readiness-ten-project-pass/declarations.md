# Execution declarations

Only one active external application per host. New local storage cap 6 GiB:
4 GiB active target maximum, 2 GiB retained evidence/packages maximum; curated
Git additions at most 25 MiB. Per new project evidence 64 MiB, old migration
32 MiB. No historical tree expansion. Inventory before acquisition/build and
during growth; stop owned work before exceeding the cap. Never delete shared
tools/caches or earlier campaigns.

Scenario ceiling 120 seconds; step ceiling 30 seconds unless predeclared with
measurement. Intentional hangs use 1–5 second product deadlines and a 30 second
harness ceiling. Command output cap 4 MiB. Builds have a 20 minute ceiling.
Fresh workspace cap 64 MiB. Default one scenario per host; hosted job budget and
minute forecast must be declared before dispatch. No dispatch has occurred.

Prepared core workflow: three native jobs, at most two concurrent, 25 minutes
each (75 hosted job-minute ceiling; forecast 30–45 job-minutes). It uses existing
Python/C compilers, an official checksum-verified Go 1.25.0 SDK extracted only
below its campaign root, and checkout-owned dependency/build/temp paths. Only
this campaign's compact events/identities/results are uploaded, excluding caches.
This is a core-only declaration, not a project-host qualification or dispatch.

Initial manual dispatch of new workflow at `81589cd` returned HTTP 404 because
GitHub had not registered it on the default branch. No run was created. Add a
narrow working-branch push trigger for changes to this workflow itself, allowing
registration/execution without changing the default branch or opening a PR.

Actual initial core run `38916191429` failed setup on all hosts: Ubuntu's default
Go was 1.24.13 (below go.mod), macOS had no `go` on PATH, and the Windows failure
packet remains retained for inspection. No platform credit. The replacement
bootstrap records its attempt before launch, verifies official release-index
hash/size, bounds extraction and avoids global SDK installation. Product deadlines
are unchanged. The pre-existing Terminal/adversarial workflows also trigger on
source pushes; their jobs are separate evidence. The superseded Terminal run
`38916048350` was explicitly cancelled to reduce duplicate hosted work. The
initial aggregate job forecast omitted those automatic workflows; retain this
planning deviation and account for them before subsequent pushes.

Before the bootstrap correction push: expect three dedicated core jobs plus
three automatic Terminal jobs, at most five newly concurrent jobs, 150 total
job-minute ceiling and a 45–60 job-minute forecast. Existing earlier runs retain
their own recorded outcomes; no paid runner or account/budget setting changes.

First use begins after target availability and ends at the first reviewed
ordinary passing test: at most five Playtestr shell invocations and twenty
recorder controls. Count failed attempts too. Diagnosis allows three documented
shell commands. Prepared operator time is not human authoring time.

Final series requires twelve fresh runs per scenario/cell: four ordinary,
two viewport/path, two input/readiness, two bounded contention/output timing,
two highest-risk applicable boundary variations. Contracts/variants must freeze
before launch; retries do not erase failures. Minimum forecast 4,800 ordinary
runs, including 2,400 native Linux, before faults/restorations/old migration.

Compatibility starts unqualified on Linux amd64, macOS arm64 and Windows amd64
for all newly changed public state paths. Declare project/host applicability
after upstream screening. No declared test counts as passed.

Next hosted batch: three corrected core jobs (max two concurrent, 25 minutes
each) and two explicitly dispatched Plop POSIX jobs (max two concurrent,
25 minutes each). Combined ceiling 125 job-minutes, forecast 30-45 minutes,
at most four newly concurrent jobs. The narrow Plop registration push runs no
target jobs. Its generated source runner remains pinned to `e5571bd`; this is
development qualification, not final candidate freeze. Its native profiles are
reviewed before dispatch, with POSIX path/exit and application-redraw differences
recorded explicitly. Windows E05 remains red and is not eligible for credit.

The pre-existing automatic Terminal workflow installs prerequisites outside
checkout-owned roots and duplicates the dedicated core jobs. Further pushes
on this campaign branch now use the dedicated owned-root core pipeline instead;
other branches and pull-request merge refs retain the ordinary workflow.
Earlier automatic runs keep their actual results but do not establish strict
workspace-only compliance. No past outside write is deleted or reclassified.

Next evidence-correction batch: three core jobs plus two manually dispatched
Plop jobs, maximum four concurrent, 125 job-minute ceiling and 30-45 job-minute
forecast. Runner remains pinned to 93bd63d; ordinary suite invocation gains
immutable prelaunch identity. No production runner change or final freeze.

Before Poetry native batch: three core jobs plus two standard native Poetry
jobs, at most four concurrent, 125 job-minute ceiling, 30-45 job-minute forecast.
Runner production source remains 93bd63d. Native project scripts and all runtime
setup are explicitly owned. Windows Poetry E05 remains excluded. No final freeze.

Poetry corrective batch: preceding core 38953916606 finished successfully on all
three hosts. Next push starts three core jobs; manually repeat the two Poetry
jobs with corrected suite selection and copied venv runtime. Same maximum four
concurrent, 125 job-minute ceiling, forecast 30-45. Both first failing project
packets remain in the denominator; no scenario credit from the setup-only run.
Historical investigations are prepared but dispatched only after Poetry jobs
settle, as separately declared in historical-investigations.md.

Next corrective push: preceding core 38955563062 passed all hosts. Core-workflow
change causes one full three-host run (75 job-minute ceiling); a separate
three-host harness run has a 15 job-minute ceiling. Wait for harness jobs to
settle, then two Poetry jobs (50 ceiling), then two historical jobs (50 ceiling).
Maximum four concurrent at every stage, total additional ceiling 190 job-minutes,
forecast 40-50. Future acceptance-only edits run the lightweight harness matrix;
full Go/race/core validation stays on production source/schema/installer changes
and final freeze. No host count or required final gate is reduced.

Bundler/RubyGems acquisition predeclaration: the first download exceeded the
shared 8 MiB source-archive guard and stopped before persistence/extraction.
Retain failed attempt 30bc4e943cc04e4c9aca167f1f74989c and its marker-only tree.
A reviewed retry permits 32 MiB compressed, 192 MiB expanded, 20,000 members,
8 MiB/member. This remains within the original 512 MiB active forecast and
4 GiB hard ceiling; no campaign/evidence cap increase. Resume only that exact
marker-only owned tree. Portable official Ruby 4.0.7-1 x64 archive is 17,742,012
bytes, GitHub-reported SHA256 7a9be96d3448ecbd9a81eccae1f619131dfcc761f2c98dded03ece6c05d0474f.
No installer/global changes; bounded inventory/extraction must precede execution.

Pinned RubyGems archive inspection: 13,869,557 compressed bytes, 37,323,733
expanded bytes, 3,173 members, no links. A recorded public package-index test
fixture is 21,539,733 bytes and exceeded the old per-member 8 MiB guard. Preserve
17e5c3c29cff4dfca7108e9f8db9c6ff and its partial tree. Completion permits
32 MiB/member within the already declared 192 MiB total, performs all member
validation before any new extraction, and verifies the existing archive digest
from a prelaunch proof. No fixture recording or build hook is executed.

Portable Ruby inventory first hit the default 4 MiB harness output cap before
extraction (2c91b4a4c7af44c19b633672d538db9b). Preserve that bounded rejection.
A reviewed retry uses only the already SHA-verified archive, permits 16 MiB for
this technical member listing and at most 40,000 runtime entries; expanded data
remains capped at 256 MiB, 32 MiB/member. Ordinary target output remains at the
original 2 MiB/4 MiB scenario/harness bounds. No installer or global changes.

Complete official Ruby inventory has 20,370 entries, 276,090,150 expanded bytes,
maximum member 5,749,760 bytes and 4,787,785 listing bytes. The 256 MiB expanded
guard stopped before extraction (9bcafca7fb694dc5a01d1bfc75f9016d). Reviewed
completion permits 288 MiB expanded, still inside the 512 MiB active forecast
with the measured source tree. Directory type uses actual 7-Zip Attributes D.
All earlier failures remain; no native Ruby target run has yet earned credit.

Bundler native batch: standard Linux amd64 and Windows amd64, at most two jobs,
25 minutes each (50 job-minute ceiling); expected 10-15 job minutes. Existing
core is complete and harness 39005929747 succeeded, leaving only the one-job
historical Windows batch active. Ruby Linux uses an already installed >=3.2
runtime; Windows repeats the reviewed owned portable runtime. No global install.
Use the public generated workflow with explicit SDK/target preparation and the
reviewed bounded manual campaign steps. All twenty ordinary scenarios, source
fault replicas, maintenance, source restore and checked removal must actually
pass. Original local F03 alone supplies Bundler's held-out fault.

Native Bundler packets retain source member indexes, acquisition digests, selected
restores, cleanup receipts and all attempts. Omit repeated native
`retained-source/source.tar.gz` copies from upload: the one canonical local
archive will be retained and its SHA must equal each native acquisition/index.
This avoids counting duplicate immutable upstream tarballs against the 64 MiB
per-project packet cap. A digest mismatch requires preserving the distinct
archive within the existing cap before any admission. Never omit failed logs,
identity records or target-fault patches to manufacture a storage pass.

Bundler native 39008017809: Linux context refused the installed Ruby symlink
before any scenario; Windows passed 16/20, with root entry-set mismatches in
N01/E02/E05 and interrupt exit timeout in E03. Both verified source restore and
checked removal. Small packets are retrieved (271,321/815,538 compressed bytes).
Next bounded diagnostic batch is one standard Windows job, 25-minute ceiling,
forecast 3-5 minutes. It performs only unsaved public root-entry review and a
Ctrl-C/Enter discrimination, records all attempts, exports no baseline and earns
no project admission. Run after harness jobs settle to maintain four-job cap.
Linux's next profile uses the explicitly resolved installed executable, and
native LF only for selected newly generated YAML preferences. No symlink-policy
relaxation, target wrapper or automatic baseline update is introduced.

Diagnostic job 39008375030 hit the existing Go download read timeout before
target acquisition. Its 10,290-byte compact packet is retained; no project case
ran. Separate diagnostic run 39008624569 repeats the same one-job route with
unchanged SDK and product timeouts. This extra dispatch was not included in the
preceding one-job forecast; record a planning deviation and another 25-minute
ceiling (expected 3-5 minutes), rather than erasing the setup failure or calling
it a product retry. Full core 39007726395 and harness 39008324773 have completed
successfully, so this new diagnostic is the sole active hosted job.

Next separate Windows-only diagnostic: one standard job, 25-minute ceiling,
expected 3-5 minutes, unchanged product deadlines. In addition to the unsaved
reviews it uses two explicitly nonqualifying diagnostic contracts: a Ruby exit
hook lists only the synthetic working directory's immediate names before exit;
the interrupt probe waits for the complete framework prompt. All original
contracts remain byte-identical. Twenty-test harness validation may overlap
(maximum two harness jobs plus this one diagnostic, below the four-job cap).

After 39009496800 ruled out complete-prompt readiness as sufficient, one further
Windows diagnostic is declared (25-minute ceiling, expected 3-5 minutes). It
retains the exact original failed ordinary workspace for immediate-name
inspection, then verifies marker identity and removes only that owned temporary
workspace through PowerShell. Its untouched original report remains retained
with a separate removal receipt. Two minimal real Ruby input contracts compare
gets and Readline Ctrl-C handling. No delay padding or qualification credit.

R3-08 repair native series: core source f470cd99aef89e080cc8455e4f8ad4715ecd12c2
has the ordinary/full-local and focused-before/after regression evidence. Core
run 39010459162 uses its existing three-host bounds. After the new lightweight
harness finishes, dispatch one two-host Bundler batch (25 minutes per job,
forecast 5-8 minutes Linux, 3-5 Windows). Linux runs its complete ordinary,
source-fault and maintenance journey; Windows runs reduced diagnosis and exact
original-contract retention with the ordinary workflow's inherited environment.
This separates a measured PATH/environment discrepancy from the inherited
interrupt repair. At most two core plus two project jobs run concurrently.

39010635498 produced Linux 18/20 and positive repaired Windows interrupt evidence.
The exact retained Windows root contained a literal `%SystemDrive%` directory;
the next Windows profile explicitly inherits this runtime prerequisite for all
contracts while preserving every expected state. Linux N01/N06 require reduction.
One Linux-only diagnostic is declared next (standard host, 25-minute ceiling,
expected 3-5 minutes). It uses an unsaved selected lock-file review and one
five-second/64-KiB synthetic Readline PTY capture with owned process-group reap.
No expectation changes, no automatic retry, no qualification credit. Maximum
four aggregate hosted jobs remains in force.
