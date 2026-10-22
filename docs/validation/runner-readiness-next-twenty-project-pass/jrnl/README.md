# jrnl: first development target

Status: first Windows public authoring route passed; no project admission yet.

The [first public route](first-use.json) used the exact rc.5 Windows archive:
three Playtestr invocations, eleven recorder controls, no handwritten Playtestr
JSON. It selected the alpha entry for deletion, retained beta's independently
reviewed exact bytes, checked the resulting entry set in the same invocation,
replayed fresh and passed an ordinary test with confirmed target/workspace
cleanup. The [exported editable spec](normal-delete.json) and its snapshot are
preserved. This is one prepared engineering flow, not the twenty-scenario package
or a human study.

Canonical primary source: [jrnl-org/jrnl](https://github.com/jrnl-org/jrnl), pin
`90de4948d79a4fca8c7238dd2487b599f458c903`. The pinned README describes plain-text
journals and interactive entry composition. Pinned command documentation also
provides per-entry deletion and time-change confirmation. The upstream testing
matrix names Linux, macOS and Windows with Python 3.11–3.14. This campaign plans
native Linux amd64 and Windows amd64; upstream CI is feasibility evidence, not
Playtestr compatibility proof.

Reviewed primary metadata: GPL-3.0-only license, Python >=3.11,<3.15, ordinary
`poetry.core.masonry.api` backend, `jrnl.main:run` entry point and declared runtime
dependencies. npm accessibility-check dependencies and developer tasks are not
needed and will not run. Installed source remains editable for actual faults.
Dependencies will be downloaded as wheels, hashed/reviewed before installation,
and installed offline into an owned copied venv. No global install, keyring,
encryption, real journal, production credentials or live service is used.

Planned useful outcomes: selectively remove or preserve a dated synthetic entry,
change a selected entry's timestamp, compose text, filter a meaningful subset,
and independently inspect exact reviewed journal bytes. Configure explicit
relative journal paths, no external editor and deterministic supplied dates.
Target configuration and seed data may be prepared; no Playtestr JSON may be
handwritten for the first record/review/replay/export route.

Predeclared authoring window: after target setup, count every Playtestr invocation
and recorder control until the first reviewed ordinary pass (targets <=5 and
<=20). Record failed initial windows separately from repaired measured routes.
Diagnosis target <=3 ordinary documented commands. Agent measurements establish
no beginner/human duration. Maintenance must update one intended file-state
expectation while preserving unrelated approvals. Relocate to a spaced/Unicode
path, then generate the delivered workflow.

Before final admission declare eight normal and twelve edge tasks, including
four meaningful combined-risk cases. Freeze their exact source/fixture/contracts
and two-host twelve-repeat variations. Select three genuine source/configuration
faults and restoration controls; at least one mutation is selected after test
freeze, with its actual prior exposure disclosed. No fault credit exists yet.

Resource forecast: 2 MiB upstream source, under 256 MiB runtime/wheels and 64 MiB
scenario workspace; 20-minute bounded setup, 120-second ordinary scenario,
30-second step, 4 MiB command output. Retained evidence target <=40 MiB, cap
64 MiB all generations. Exact storage will be sampled before/after setup and
qualification. Runtime, source and copied data remain in this campaign's owned
paths; target processes must terminate before checked inventory-based removal.
