# Runner readiness campaign

Invoked 16 October 2026. Status: **in progress; three development admissions across six native cells**.

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
Poetry's owned local tree is also removed after verified retention and cleanup.
RubyGems/Bundler is admitted on Linux/Windows and its owned local tree is removed.
Microsoft Edit is the sole active target. Attempted 4; development admitted 3; archive qualified 0;
old projects migrated 0; final runner admissions 0/100; paid-product admissions 0/100;
final-qualified scenarios, faults, repetitions and native project/host cells all 0.
Development evidence includes nineteen passing Windows Plop scenarios and three
detected real source faults with exact restoration. The repeated-resize case
remains red, and startup failures remain unresolved. Local-only raw fault packet:
`artifacts/runner-readiness-ten-project-pass/plop/faults/a20ca9bc42554dac87dabffed6a78c2d/`.
All twenty scenarios also passed on native Linux amd64 and macOS arm64 using
runner source `93bd63d`, with three real fault replicas, public maintenance,
and verified source archive/restore/removal. Run `38950615245` additionally
records complete immutable ordinary-suite attempts. Poetry run `38957159731`
passed all twenty scenarios on both hosts, with fault replicas, maintenance and
verified source removal; [admission receipt](poetry/development-admission.json).
Bundler run `39011298428` passes twenty cases, three source-fault replicas,
public maintenance and verified source removal on native Linux amd64 and Windows
amd64; [admission receipt](rubygems/development-admission.json). Its original
failures and explicit runtime profiles remain in [native findings](rubygems/native-findings.md).
All 1,986 native packet payloads have a verified local-only compressed archive
and eight selected restoration checks. Expanded evidence briefly exceeded the
project cap; the breach remains recorded, and retained Bundler evidence is now
37,003,254 bytes after verified compaction. Whole campaign storage observation
is 1,199,571,043 bytes, excluding subsequent small records, with no active targets.
Development cells: 6;
archive cells: 0. The original Windows F03 alone supplies the project holdout;
native copies are replicas. This admits the development package on those two
hosts, with Windows excluded and first-use/usability limitations retained.
Declared work is never execution evidence. Human usability is unmeasured;
publication is not authorized.

Bundler's first public route passed in three invocations and twenty recorder
controls, without handwritten JSON. Its remaining scenarios and qualification
are in progress. The [historical investigation disposition](historical-disposition-development.json)
records 150 Windows wizard attempts and 150 repetitions of each separate macOS
control. Green current repetitions leave original causal branches unresolved.
The [88-control mapping correction](old-control-matrix-revision-2.json) adds an
actual local Windows short-path alias pass; the hosted filesystem skip remains.

Raw attempts/caches/packages belong only under ignored
`artifacts/runner-readiness-ten-project-pass/`. Earlier evidence is preserved.
