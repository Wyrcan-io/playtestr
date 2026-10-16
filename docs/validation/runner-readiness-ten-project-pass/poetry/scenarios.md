# Declared Poetry scenarios

Declared before authoring tests. Pin `38a86661d2ae58694c76d0bb4e628e1400d6dc6f`,
MIT, Python/Cleo. Source metadata, init/new/version/config/source/check commands
and Poetry-core build backend reviewed. Wheel-only dependencies and a local venv
are owned by the active tree. Windows amd64, Linux amd64 and macOS arm64 are
proposed development cells, not current coverage. All rows initially unexecuted.

Common budget: fresh managed fixture, 100x28 viewport, 10-second steps,
120-second scenario, 2 MiB terminal output, 64 files/1 MiB fixture. Temporary
home/temp, synthetic explicit author/Python constraint, disabled plugins/keyring,
no user Git identity, no package-index search or publish. Repository configuration
uses `https://packages.example.invalid/simple/` without contacting it. Offline
builds use already installed reviewed Poetry-core. No shell-generated fake UI.
Check exact exit before final public saved-state assertions; interactive actions
also need specific prompt/transition evidence. Expected text/TOML comes from
reviewed fixture edits. Archive capture requires independent member/payload
review and deterministic timestamp, rather than trusting a success banner.

| ID | User workflow / risk | Positive outcome and same-run state |
| --- | --- | --- |
| N01 | Interactive init in an existing directory | Confirm reviewed metadata; exact pyproject, existing sentinel unchanged |
| N02 | Interactive new nested namespaced source project | Specific creation result; namespace/src/tests/readme entry sets and exact pyproject |
| N03 | Bump existing project minor version | Specific old/new version, exit 0, exact changed TOML and unrelated comments preserved |
| N04 | Set local virtualenv policy | Exit 0; exact poetry.toml, pyproject unchanged; no global config |
| N05 | Add an explicit package repository configuration | Specific source-added result; exact named URL/priority and unchanged project metadata |
| N06 | Remove obsolete repository configuration | Specific removed-source result; exact remaining configuration |
| N07 | Validate a complete local package | All-checks-passed, exit 0; exact fixture bytes unchanged |
| N08 | Build a local source distribution offline | Specific artifact result; exact dist entries and reviewed deterministic archive bytes |
| E01 | Invalid author then correction in interactive init | Visible validation/re-prompt; only corrected author saved |
| E02 | Decline final generation with dirty existing files | Command-aborted exit; pyproject absent, sentinel bytes unchanged |
| E03 | Ctrl-C after editing wizard fields | Exact native cancellation status; no saved project, sentinel unchanged |
| E04 | Existing nonempty nested new destination | Specific destination error; original content/entries unchanged, no partial scaffold |
| E05 | Repeated resize during init with long description | Semantic prompt progression after two resizes; exact complete long value saved |
| E06 | Unicode/spaced path plus namespace scaffold | Exact portable paths and source/test entries; no sibling writes |
| E07 | Invalid version bump on a dirty commented TOML | Specific parser error and nonzero exit; exact original file unchanged |
| E08 | Version dry run with pre-existing build artifact | Correct proposed version; project and existing artifact unchanged |
| E09 | Wrong-type destination pyproject.toml directory | Accurate bounded refusal; directory/sentinel unchanged and no replaced file |
| E10 | Case-insensitive existing source name update | Explicit updating result; one source with reviewed new priority, no duplicate |
| E11 | Remove missing source with other source preserved | Specific missing-source error, exit 1; complete TOML unchanged |
| E12 | Missing README during strict check with dirty source | Specific missing-readme diagnostic, nonzero; source/TOML unchanged, no invented success |

Combined risks: E02 dirty-state cancellation; E04 nested collision and partial
creation; E05 resize plus long input and save; E06 Unicode relocation plus
namespace layout; E08 dry-run plus existing artifacts; E12 missing resource plus
dirty-state preservation. These combine independent expectations in single runs.

Exclusions: remote resolution/search, credentials/keyring, publishing, arbitrary
third-party plugins and user package installation. No network-isolation claim.
N08 is conditional on a reproducible exact archive across declared host profiles;
if unavailable, keep that cell open and declare a replacement meaningful task
before authoring it. Three real source faults and a post-contract holdout remain
undeclared/unexecuted; they cannot supply scenario quota.
