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
