# Continuation checkpoint v76

## Campaign count

Still **15/30**: five new projects are credited; zero original-ten projects are requalified on the current candidate. mg has zero admission credit.

## mg status

N01 first-use passed once on Linux x86_64 and macOS arm64 (run 42712723851). N02 edit-and-save passed once per native host in run 42717420876 after preserving the first two-host prompt-oracle failure; see `mg/scenario-development-readback-v1.json`. The state assertion is recorded as matched but the output bytes are not retained.

N03 query-replace was reviewed against exact pinned `src/keymap.c` and `src/search.c`. Run 42719240888 failed on both hosts at step 4 before any replacement: the screen renders `Query replace:` without a stable trailing blank, while the initial contract expected it. Both target process groups were force-stopped and confirmed exited. Provider artifact SHA-256 values and retained local archive identities, reports, screens and cleanup facts are in `mg/n03-first-attempt-readback-v1.json`; do not overwrite these attempts.

The N03 prompt contract now omits invisible trailing spaces. Next commit and push that contract/test repair, rerun the native Linux/macOS workflow, and inspect its saved-state evidence. Then proceed through N04?N20. Development evidence remains separate from the 20-scenario qualification, repetitions, authoring, three faults, native cells, and admission gates.
