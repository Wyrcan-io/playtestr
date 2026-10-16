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
hosted Go/Python/compilers and checkout-owned dependency/build/temp paths. Only
this campaign's compact events/identities/results are uploaded, excluding caches.
This is a core-only declaration, not a project-host qualification or dispatch.

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
