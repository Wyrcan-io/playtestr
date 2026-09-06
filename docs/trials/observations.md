# R3 observations and backlog

Status: awaiting participant evidence. Add an item only when it has a user task and reproducible observation.

## Known pre-trial questions

These are prompts to observe, not cohort findings:

| ID | Question | Existing evidence | Trial decision needed |
| --- | --- | --- | --- |
| PRE-001 | Does retained adjacent failure evidence confuse a later passing run? | Report v1 correctly removes evidence references, while old `.actual.txt` files remain. | Ask participants whether the latest report/status is clear and whether manual removal is acceptable. |
| PRE-002 | Does direct release installation create too much CI plumbing? | R2 uses explicit asset download and checksum verification. | Record actual adopter setup before scheduling reusable CI work. |
| PRE-003 | Does mutable application state prevent repeated runs? | No qualifying project evidence yet. | Record exact files/resources rather than assuming a workspace feature solves it. |

Pre-trial questions do not count toward frequency or roadmap priority until a participant encounters them.

## Accepted observations

| ID | Trial(s) | User task | Category | Impact | Reproduction/evidence | Workaround | Frequency | Smallest useful response | Destination | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

## Priority rules

| Priority | Qualifying impact | Required response |
| --- | --- | --- |
| Release blocker | False pass, surviving managed process, data loss, unintended sensitive-data persistence, or broken advertised installation. | Hold stable promotion, preserve a sanitized reproduction, fix, and verify new candidate bytes where needed. |
| Adoption blocker | The agreed real workflow cannot be tested without disproportionate custom setup or incorrect supported rendering. | Decide on a narrow candidate fix or evidence-backed sprint before expanding the trial. |
| Repeated friction | Two or more participants struggle with the same authoring, discovery, evidence, or CI task. | Rank by time/impact and feed the smallest relevant sprint. |
| Project-specific issue | One target/environment needs a workaround that is safe and documented. | Record the workaround and avoid a general compatibility claim. |
| Preference or speculation | No blocked task or reproduction. | Keep as context; do not schedule automatically. |

## Triage checklist

For each accepted item, verify:

- The target version, host, starting state, spec, expected result, and actual result are known.
- The failure layer is identified without relying only on console prose.
- Shared evidence is sanitized and publication permission is recorded.
- Impact and cohort frequency are stated separately.
- The workaround does not hide a false pass, leak a process, update a baseline blindly, or weaken production time/output limits.
- The proposed response is the smallest user-visible improvement that solves the observed task.

Close an item only with recorded evidence or an explicit decision that the behavior remains a documented limitation. Do not claim a participant accepted a workaround unless they actually did.
