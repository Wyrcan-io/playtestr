# Attempts and counters

The command-event adapter uses immutable schema-v1 records in the new campaign's
`events/` root, with `campaign=runner-readiness-next-twenty-project-pass` and an
explicit development/final phase. It preserves the historical helper's event
validation and does not redirect any original campaign caller.

Each ID has separate exclusive `started`, `identified`, `launched`, `finished`
events. Started records precede process launch, identified records reference a
hashed input manifest, launched records identify the actual child, finished
records retain actual exit/category/duration/console hash/output bytes and
harness cleanup separately. Failed setup without launch remains failed setup.
Partial events are not passing executions. Consoles remain local-only synthetic
engineering evidence, not public environment dumps.

Target-level prelaunch declarations must additionally bind the actual archive
and executable, target pin/runtime/build, fixture/contracts/expectations,
OS/architecture, phase/variant/seed, limits and expected outcome. The generic
command wrapper alone does not provide a new application's runtime identity or
same-invocation state evidence and cannot award admission. New project execution
must extend identities before launch; reports and independent audits then prove
positive steps, invocation/workspace IDs and cleanup.

One immutable per-event publisher and checked merge avoid concurrent append
corruption. Identical bytes from distinct real executions remain distinct IDs.
Only identical copies of one event identity may be deduplicated. Never replace
failed repetitions or relabel development/authoring/control commands as final
ordinary runs. Rejected series keep their complete observed denominators.

At closure declare an accounting cutoff; reconcile every started ID at that
cutoff and retain later audit/closure commands as a separate finite delta.
Reported command-seconds are summed command duration, not elapsed campaign time
or human effort. Provider queue/job time, build/setup, authoring, ordinary,
calibration, investigation and controls are separate denominators.
