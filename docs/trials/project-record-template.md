# R3 project trial record

Copy this file once per project. Use an opaque local identifier when the participant or repository is private. Do not commit credentials, environment values, typed secrets, personal paths, or unsanitized screens.

## Consent and identity

- Trial ID:
- Date opened:
- Participant alias:
- Participant relationship to project:
- Consent to retain this trial record: yes/no
- Project name may be published: yes/no
- Participant name may be published: yes/no
- Sanitized quotes may be published: yes/no
- Sanitized specs/evidence may be published: yes/no
- Permission confirmed on/date/reference:

## Project and environment

- Repository or private project reference:
- Application version/commit:
- Current development version/commit, if tested separately:
- Implementation language/runtime/framework:
- Operating system/version/architecture:
- Shell/terminal:
- Playtestr archive:
- Observed archive SHA-256:
- `playtestr --version` output:
- Target prerequisites and versions:
- Go present on execution PATH: yes/no/unknown

## Chosen user workflow

- User goal:
- Why this flow is regression-prone or costly:
- Current protection: manual/existing automation/none
- Manual keyboard steps:
- Expected visible states:
- Expected exit status or long-running behavior:
- Initial filesystem/application state:
- State changed by the flow:
- Synthetic data used:
- Data or evidence that must remain private:
- Network/external services involved:
- Concrete regression to detect:

## First session

- Prerequisites-ready time:
- First passing-test time:
- Assistance given before first pass:
- Spec path/reference:
- Readiness assertions chosen and why:
- Snapshot names and review decision:
- Good application result and report reference:
- Bad application revision/change:
- Bad result exit code/category/step:
- Evidence the participant inspected:
- Could the participant explain the failure unaided: yes/no
- Restored-good result:
- Historical artifact behavior understood: yes/no/not encountered

### Ten-run observation

| Attempt | Good app version | Host/state reset | Result | Duration | Failure/evidence |
| --- | --- | --- | --- | --- | --- |
| 1 | | | | | |
| 2 | | | | | |
| 3 | | | | | |
| 4 | | | | | |
| 5 | | | | | |
| 6 | | | | | |
| 7 | | | | | |
| 8 | | | | | |
| 9 | | | | | |
| 10 | | | | | |

- Passed/attempted:
- Any retries omitted or performed:
- State/timing/rendering variation observed:
- Reproduction reference for each unexpected result:

## Later use and CI

- Date of second session:
- Application change or reason for rerun:
- Participant chose to keep/modify/remove test:
- Reason:
- Assistance given:
- CI attempted: yes/no/not suitable
- CI host and workflow reference:
- CI pass result:
- Controlled CI failure result/category:
- Evidence retention and privacy review:

## Findings

For every finding, add an entry to `observations.md` and reference its ID here.

- Observation IDs:
- Release blocker present: yes/no
- Adoption blocker present: yes/no
- Workaround:
- Smallest useful change:
- Maintainer's final assessment in their own words:
- Remaining unknowns:
- Trial status: selected/in progress/initial complete/repeated use complete/withdrawn
- Reason if withdrawn:
