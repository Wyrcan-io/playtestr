# Public-command usability assessment

All ten development journeys exercised the public recorder and ordinary test
command. These are constrained operator assessments with prepared synthetic
fixtures, warm caches and prior knowledge. They are not independent beginner
studies. The measurements below belong to the runner identities in the linked
records; they are not measurements repeated on the final frozen binary.

| Project | Playtestr shell commands | Recorder controls | Recorded interval | Evidence |
| --- | ---: | ---: | --- | --- |
| Cookiecutter | 3 | 12 | 65.078 seconds active operator time | [Ledger](cookiecutter/ux-bounded-ledger.json) |
| Copier | 3 | 15 | 92.5 seconds active operator time | [Ledger](copier/ux-bounded-ledger.json) |
| lf | 4 | 19 | 3.172 seconds automated prepared walkthrough | [Ledger](lf/ux-prepared-route.json) |
| Superfile | 4 | 17 | 4.094 seconds automated prepared walkthrough | [Ledger](superfile/ux-prepared-route.json) |
| Helix | 4 | 20 | 4.000 seconds automated prepared walkthrough | [Ledger](helix/ux-prepared-route.json) |
| Glow | 4 | 12 | 24.369 seconds automated prepared walkthrough | [Ledger](glow/ux-prepared-route.json) |
| Broot | 4 | 17 | 21.231 seconds automated prepared walkthrough | [Ledger](broot/ux-prepared-route.json) |
| Yazi | 4 | 15 | 43.340 seconds automated prepared walkthrough | [Ledger](yazi/ux-prepared-route.json) |
| Ranger | 4 | 16 | 72.934 seconds automated prepared walkthrough | [Ledger](ranger/ux-prepared-route.json) |
| nnn | 4 | 16 | 57.996 seconds automated prepared walkthrough | [Ledger](nnn/ux-prepared-route.json) |

The prepared walkthroughs automate one response at a time through the public
recorder. Their elapsed time excludes acquisition, fixture engineering,
exploratory authoring and correction. In particular, the three-to-four-second
results do not measure human authoring or review speed. Do not average the two
measurement types or advertise them as onboarding times. The fifteen-minute
active-human-time gate is directly measured only for Cookiecutter and Copier;
the remaining eight records establish bounded prepared execution, with human
authoring time unmeasured.

The recorded routes meet the provisional five-command and twenty-control
ceilings. They use no handwritten JSON for the first simple flow. Target input
and recorder controls have separate roles: successful automation still requires
someone to choose meaningful checkpoints and review expectations. The task does
not establish automatic specification discovery.

Each project's `maintenance-result.json` retains its intentional mismatch,
report diagnosis, selected expectation update, passing rerun, relocation and
generated workflow preview. Project reports also retain suffix rerecord and
manual-spec authoring evidence. Those technical-maintainer exercises are
separate from the simple first-use command counts. Hosted Actions execution is
not a real pull-request integration journey.

The practical result is a short repeatable command route after a trusted target
and fixtures have been prepared. Application installation, suitable terminal
readiness checkpoints, explicit environment policy and expectation review remain
developer work. Further testing with unfamiliar human users is needed before
claiming that these workflows are straightforward for beginners.
