# Sprint 10 compatibility-family decision

Date: 21 September 2026. Operator: Playtestr maintainer. Review boundary:
operator engineering, not independent adoption.

## Decision

Sprint 10 is **deferred because its evidence gate is not met**. No terminal
compatibility family is selected and no runner, schema, snapshot or terminal
profile behavior changes in this checkpoint.

The entry contract requires a real Sprint 11 application flow that fails with
the current runner for a confirmed renderer, VT-sequence or terminal-query
reason, plus an independently observed expected screen. The five admitted pilot
records contain no such failure:

| Pilot | Relevant observation | Disposition |
| --- | --- | --- |
| `GUM-01` | Current Windows selector passed 3/3; the deliberate wrong-selection snapshot mismatch is a target/input control, not an emulator failure | Not a Sprint 10 trigger |
| `LG-01` | Current evidence staged the intended path; the index-lock false pass was an oracle/spec problem caught by Git | Not a terminal-renderer defect |
| `CV-01` | Prompt/scaffold flow passed; missing-template control failed at the intended readiness assertion | Not a terminal-renderer defect |
| `BT-06` | Help, disappearance and `120x40 -> 80x24 -> 120x40` redraw passed 3/3 on Windows and in historical WSL evidence | Candidate redraw path is not blocked |
| `LG-08` | Current Windows adapter-backed fresh-workspace flow passed 3/3 with pre-deletion oracle and cleanup | Not a terminal-renderer defect |

The documented one-rune-per-cell limitation remains real, but no admitted pilot
currently demonstrates that it blocks the user task. A known limitation alone
does not justify a new terminal profile, broad Unicode claim or emulator
replacement.

## Triage classification

- Current highest pilot risks are native-host breadth, cold setup measurement,
  unexecuted new candidate routes and focused-case gaps.
- The retained Lazygit persisted-draft and index-lock observations are state and
  oracle lifecycle findings.
- The Gum negative is an intentionally wrong selection correctly detected by an
  unchanged baseline.
- The bottom missing-helper negative is a controlled external-process absence,
  not evidence of wrong terminal cells.
- No blank-screen observation is promoted to a renderer diagnosis.

Consequently there is no reduced failing application case, no independently
specified failing cell corpus, and no failing-before/passing-after application
pair on which checkpoints 10.2-10.6 could honestly operate.

## Exclusions and revisit trigger

This decision does not claim general Unicode, grapheme, emoji, ambiguous-width,
mouse, VT-query or framework compatibility. Existing documented limitations and
the current terminal implementation remain unchanged.

Reopen Sprint 10 only when an exact admitted or adopter workflow records all of:

1. target/version, host, dimensions and input sequence;
2. current-runner failure repeated for the intended terminal reason;
3. independently observed expected cells or protocol behavior;
4. a reduced deterministic fixture that retains the failure; and
5. a target regression distinguishable from the runner defect.

At that point select one bounded family and rerun the native, lifecycle,
snapshot and resource checks in the Sprint 10 plan. Until then the maintenance
cost of a speculative profile/schema change is rejected.

## Verification

This documentation/scope decision reuses the validated Sprint 11 records and
does not invalidate runner-byte evidence. Checked locally:

```text
go test ./internal/corpus
go vet ./...
git diff --check
```

The next roadmap checkpoint is Sprint 12-A authoring and diagnostics.
