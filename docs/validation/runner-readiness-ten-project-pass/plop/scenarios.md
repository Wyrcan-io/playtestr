# Declared Plop scenarios

Declared before authoring tests. All rows are **not run / not admitted**.
Linux amd64 and Windows amd64 are proposed cells; upstream's pinned test workflow
names Ubuntu/Windows on Node 18/20. Local Node 24.7.0 is a separately recorded
runtime variation, not proof those upstream CI jobs passed here.

Common contract: fresh synthetic managed fixture, selected temporary home/temp,
80x24 initial viewport unless explicitly varied, 10-second steps, 120-second
whole-run ceiling, 2 MiB terminal cap, 1 MiB/64-file scenario fixture ceiling.
No shell generator actions, plugins, external services or real personal state.
Prompt text is positive readiness; after confirmation, assert the specific
action result, observe the exact exit, then inspect saved state before cleanup.
No fault or repetition counts as one of these scenarios.

| ID | User risk, preconditions and actions | Positive completion and exact saved outcome |
| --- | --- | --- |
| N01 | Generate a named source artifact from a reviewed template | Artifact-name prompt, create `alpha`, successful add result, exit 0, `out/alpha.txt` exact `name=alpha\n` |
| N02 | Scaffold a nested module with addMany | Module-name prompt, choose module, successful multi-file result, exit 0, complete exact entry set and reviewed text files |
| N03 | Register a new route without damaging existing registry | Existing registry with explicit insertion marker; enter route | Successful append result, exit 0, exact preserved prefix/marker plus one inserted route |
| N04 | Change a version marker in existing source | Reviewed version file; enter replacement | Successful modify result, exit 0, exact replacement and untouched surrounding bytes |
| N05 | Decline optional generation safely | Name plus explicit optional-file confirmation; decline | Visible confirmation result, exit 0, required file exact and optional path absent |
| N06 | Preserve a pre-existing user file with skipIfExists | Existing reviewed artifact; confirm generator | Visible skipped result, exit 0, pre-existing bytes unchanged |
| N07 | Explicitly replace a reviewed generated file | Existing generated file, explicit overwrite confirmation | Successful overwrite, exit 0, new exact bytes; unrelated file unchanged |
| N08 | Apply filename/content case helpers in a nested generator | Enter a multiword module identifier | Reviewed nested kebab-case path and PascalCase content, exit 0; exact directories/files |
| E01 | Empty name validation and correction without restart | Submit empty name, observe validation, correct | Visible rejection then success for corrected name; only corrected output exists |
| E02 | Existing-file collision must not destroy reviewed work | Existing destination; attempt ordinary add | Visible collision, exit 1, original bytes unchanged, no extra entries |
| E03 | Destination ancestor is a file | Fixture `out` is a regular file; attempt nested output | Visible action error, exit 1; ancestor bytes unchanged and intended child absent |
| E04 | Cancel before optional confirmation with dirty pre-existing state | Name entered; cancel at confirmation | Exact native cancellation exit must be established from pinned reader before spec authoring; no outputs and old bytes unchanged |
| E05 | Resize while selecting a nondefault generator | 80x12, select menu, resize to 100x16 and back; checkpoint redraw before navigation | Specific nondefault-generator prompt and intended output; other generator's output absent |
| E06 | Off-screen choice in a long selector | More choices than supported viewport height; navigate to a named late item | Specific generation result and exact selected item in saved output, not merely menu text |
| E07 | Unicode/spaced nested path alongside existing dirty files | Explicit supported UTF-8 name and spaced path; preserve unrelated file | Exact encoded bytes/path set, successful save and unchanged unrelated data |
| E08 | Multi-file generation preserves CRLF and binary NUL bytes | Reviewed raw binary and CRLF template fixtures | Successful addMany result, exit 0, byte-exact binary/text files and directory entries |
| E09 | Append uniqueness with pre-existing matching content | Dirty registry already contains reviewed route; confirm append | No duplicate insertion, exact unrelated text preserved; exit 0 |
| E10 | Missing selected template | Prompt succeeds; declared template path absent | Specific missing-template action failure, exit 1, intended output absent |
| E11 | Partial multi-action generation then collision | First destination absent, second exists, third would be created | First file exact, second unchanged, third absent; visible abort and exit 1 |
| E12 | Continue after a declared nonfatal action failure | First action collides with abortOnFail false; second valid | First bytes unchanged, second exact, visible error plus later success; overall exit 1 |

Combined-risk table: E05 resize + menu transition; E07 Unicode/spaced paths +
pre-existing state; E08 multiple writes + binary/newline distinctions; E11 partial
save + collision + failure exit. These combinations are declared applicability,
not an exhaustive Cartesian product.

Fault plan: after reviewed tests freeze, mutate a real prompt/action transition,
mutate abort/continuation behavior, and mutate the upstream file-write payload
while retaining success output. One fault is selected only after contract freeze.
Store real patches, source identities, original misses and exact restorations;
none has executed yet. Independent fixture/template bytes calibrate the oracle.
