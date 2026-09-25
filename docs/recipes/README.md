# Three complete authoring recipes

These recipes are the Sprint 12-A copy-and-adapt starting point. Each tests one
meaningful user result, has a deliberate negative and recovery, and keeps target
setup outside Playtestr. Targets run with your permissions; use only reviewed
binaries and owned fixtures.

| Recipe | User result | Independent evidence | Recorded host boundary |
| --- | --- | --- | --- |
| [Selector](selector.md) | Choose exactly `Beta` | Exact accepted output snapshot and exit 0 | Current Windows; historical WSL pilot only |
| [Stateful wizard](stateful-wizard.md) | Create a Vanilla JavaScript scaffold without installing it | Parsed `package.json`, required files, no project `node_modules` | Current Windows; historical WSL pilot only |
| [Full-screen modal and resize](full-screen.md) | Filter a controlled process, close help and survive two resizes | Exact helper PID/executable remains alive | Current Windows; historical WSL pilot only |

Minimum runner: Playtestr v0.1.0 for these spec-v1 actions. The Sprint 12
verification also ran the current source checkout. This is not evidence for
macOS application compatibility or newer target versions.

Readiness is positive evidence after each input. `expect_not` is used only after
the text was observed and an input could remove it. A continuously repainting
screen uses `resize`, immediately followed by `wait_for_redraw`, then a fresh
positive assertion. Snapshots follow readiness or a successful exit assertion;
update one reviewed baseline with `--update --snapshot <name>`, inspect it, then
rerun without `--update`.

The recipes intentionally keep bounded reference details here and the short JSON
under [`examples/recipes`](../../examples/recipes). See [Writing tests](../writing-tests.md),
[Snapshots](../snapshots.md), and [Troubleshooting](../troubleshooting.md) for the
complete contract.

The `v0.4.0-rc.1` release kit also preserves three frozen-byte narratives:
[wrong selection](release-hero.md), [persisted state](release-stateful.md), and
[resize/redraw](release-compatibility.md). Each runs pass, a genuine target
defect, and recovery with the same reviewed spec, plus an independent
postcondition and exact hashes.
