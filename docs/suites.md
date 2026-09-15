# Test suites and CI evidence

Pass one or more spec files or directories to `playtestr test`. A directory is searched recursively for files whose names end in lowercase `.json`:

```text
playtestr test --list tests/terminal
playtestr test --artifacts-dir artifacts/playtestr --report artifacts/results.json tests/terminal
```

Flags must precede paths. `--list` prints the exact resolved selection and never launches a target. It cannot be combined with execution or output flags. An empty selection, missing or unreadable root, or exceeded discovery limit exits 2 with a selection error.

## Selection contract

- Explicit files keep argument order. Each directory expands in its argument position.
- Matches within a directory are sorted by normalized relative path. `/` is used when paths are printed. Path comparison follows the host filesystem's case behavior.
- The same filesystem file is run once, even when selected through duplicate arguments or hard links.
- Directory symlinks are not followed. An explicitly supplied symlink root is rejected; pass its resolved target deliberately instead.
- `.git`, `.cache`, `.playtestr`, `artifacts`, and `node_modules` directories are skipped. The configured artifact destination is also excluded from traversal, so a prior evidence run cannot become test input. Put the report outside the selected tree (normally under `artifacts/`); a report path that is itself selected is rejected as an input/output collision.
- Discovery is limited to 10,000 visited entries and 1,000 selected specs. Valid selected specs may declare at most 10,000 steps in aggregate; existing per-spec limits still apply.
- Custom glob and filter syntax is not implemented. A shell-expanded explicit file list remains supported.

All selection and destination checks finish before a target launches. `--snapshot` still requires `--update` and exactly one resolved spec. Update mode rejects two specs that resolve to the same snapshot baseline.

## Serial results and status

Specs run serially. An ordinary failure does not stop later specs. Ctrl+C cleans the active process, marks it `cancelled`, marks remaining selections `not_run`, writes requested partial output, and exits 130.

Every execution ends with a stable summary containing total, passed, failed, cancelled, and not-run counts. Each failure line includes its normalized spec path, category, first failed step when available, and written screen/diff paths.

Exit status remains:

- `0`: every selected spec passed and requested outputs were written;
- `1`: a test, cleanup, evidence, or report write failed;
- `2`: command usage, selection, a resource cap, or a prelaunch collision is invalid;
- `130`: cancellation.

## Artifact layout

Without `--artifacts-dir`, failures retain the compatible adjacent `<spec>.actual.txt` and `<spec>.diff.txt` paths. With the option, Playtestr creates a new UTC-timestamped, randomly suffixed directory for every invocation:

```text
artifacts/playtestr/
  20260915T120000Z-123456789/
    tests-terminal-menu.json-a1b2c3d4e5f6.actual.txt
    tests-terminal-menu.json-a1b2c3d4e5f6.diff.txt
```

The readable portion derives from the normalized selected path; the suffix derives from its resolved canonical path. Specs with the same basename in different folders therefore cannot overwrite each other. Previous run directories are preserved, while a new report references only evidence actually written by its own results.

Report and artifact destinations may not alias a selected spec or snapshot baseline, and an artifact root may not contain selected specs. Output creation and write errors remain failures distinct from the primary test failure. Report v1 path fields retain their existing meaning: they contain the path used for the file written by the runner, relative to the invocation directory when the supplied destination was relative and absolute when it was absolute.

Evidence can contain target-rendered data. Review it before sharing, upload only the explicit artifact root, and configure finite CI retention.

## Deliberately omitted

The acceptance evidence did not identify a CI test-results viewer requiring JUnit, so Sprint 5 keeps the existing JSON report rather than adding an unvalidated format. It also found no selection task requiring custom globs or filters. Workers, retries, tags, hooks, setup actions, hosted upload, and a configuration framework remain out of scope.
