# Runner readiness campaign

Invoked 16 October 2026. Status: **in progress; Plop development admitted on Linux/macOS**.

Base: `deed954a9ed1c05db73ee93cb2fbb84d9271d1e1`, branch
`work/p0-p2-implementation`. Pre-existing edits: planning index and execution
prompt; preserve both. Source commands exceed published archive capabilities.
Local host: Windows amd64, Go 1.27.0. Other native paths require actual Actions
results; cross-compilation and WSL cannot supply those results.

The controlling [execution prompt](../../plans/runner-readiness-ten-project-execution-prompt.md)
defines acceptance. [Checkpoint](checkpoint.md), [requirements](requirements.md),
[resource and measurement declarations](declarations.md), and
[saved-state decision](../../decisions/runner-saved-state.md) track execution.

Counters: 30 new pinned upstream metadata records reviewed; ten provisional
selections and five provisional reserves in [the candidate ledger](candidates.json).
Plop's owned local tree is removed after archive/restore and cleanup checks.
Poetry is the sole active target. Attempted 2; development admitted 1; archive qualified 0;
old projects migrated 0; final runner admissions 0/100; paid-product admissions 0/100;
final-qualified scenarios, faults, repetitions and native project/host cells all 0.
Development evidence includes nineteen passing Windows Plop scenarios and three
detected real source faults with exact restoration. The repeated-resize case
remains red, and startup failures remain unresolved. Local-only raw fault packet:
`artifacts/runner-readiness-ten-project-pass/plop/faults/a20ca9bc42554dac87dabffed6a78c2d/`.
All twenty scenarios also passed on native Linux amd64 and macOS arm64 using
runner source `93bd63d`, with three real fault replicas, public maintenance,
and verified source archive/restore/removal. Run `38950615245` additionally
records complete immutable ordinary-suite attempts. Development cells: 2;
archive cells: 0. The original Windows F03 alone supplies the project holdout;
native copies are replicas. This admits the development package on those two
hosts, with Windows excluded and first-use/usability limitations retained.
Declared work is never execution evidence. Human usability is unmeasured;
publication is not authorized.

Raw attempts/caches/packages belong only under ignored
`artifacts/runner-readiness-ten-project-pass/`. Earlier evidence is preserved.
