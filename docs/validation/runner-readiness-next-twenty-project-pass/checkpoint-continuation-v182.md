# Runner readiness continuation checkpoint v182

## Campaign status

The campaign remains at **18/30 cumulative admissions**, with **2/20 new
packages** admitted (JOE and fzy). Percol remains at zero admission credit. The
exact candidate remains `v0.4.0-rc.8` (`native-exit-v3`).

## Percol development suite v9

Run `43388079374` completed successfully on Linux amd64 and macOS arm64. Each
host ran all 20 scenarios (eight normal, twelve edge) once against the exact
candidate. All target exits matched; every process group exited and every
managed workspace was cleaned. Source/runtime cleanup and storage checks passed.
macOS detached the temporary case-sensitive build volume. Both downloaded ZIPs
match the GitHub provider digest. Receipts: `percol/development-attempt-v9.json`.

E07 is explicitly a characterization of the pinned target limitation: a typed
lowercase query produces one visible lowercase row, but selecting it emits the
first source row `Blue`. This is recorded as unsupported output selection in
`percol/unsupported-controls-v3.json`; the test does not claim otherwise.

## Admission work still required

The 20-case development run alone earns zero credit. Percol still needs its
ordinary public authoring route and measurements, independently checked output
oracle, three distinct genuine faults with baseline/corrupted/restored evidence,
maintenance and relocation checks, exact-candidate repetitions/variations,
reacquisition proof and final independent audit. Complete these gates before
selecting the next project.
