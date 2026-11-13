# Runner readiness continuation checkpoint v153

## Cumulative status

The audited count is **17/30**. Pick remains project 18, with exact rc.8
ordinary/fault evidence, public and technical routes, and 17 passing model
tamper controls; its admission and the campaign ledger have not been reconciled.
The next selected project is fzy.

## fzy source and behavior

- Selected pin: `jhawthorn/fzy` at
  `34b88869d022e861da4846c4463aea3ddfb3ff30`; MIT license verified.
- The target is a non-stateful C99 fuzzy selector. Its observable contract is
  candidate/query bytes written to stdout and exact exit status. Keyboard UI is
  driven through the controlling PTY; stdout is captured into a same-run
  harness file solely for byte-exact assertions.
- Source review is `fzy/source-review-v1.md`; source archive/tree identity and
  storage scope are bound in `fzy/source-provenance.json`.
- A twenty-case v1 matrix is prepared: eight normal, twelve edge, with explicit
  rendered selection evidence, output bytes, cancellation statuses, NUL input,
  UTF-8 candidate output, viewport paging, filter mode and option bounds.

## First native attempt and retained failure

Run `43354015363` (head `25bf5f58c4ec64a8497c2bc94ff3cdbef0916f6c`) acquired the
same 49,100-byte source archive on Linux and macOS. Both hosts built and
installed fzy and passed all 32 upstream tests. The attempt then stopped before
candidate installation or Playtestr scenarios: upstream `make veryclean` leaves
five compiler-generated `.d` files and, on macOS, a `test/fzytest.dSYM` bundle;
the exact-source check refused those extra build outputs. The no-case target
cleanup invocation was missing its explicit `--no-case-reports` flag, and the
storage check preceded creation of the required `fzy/source-provenance.json`.
The provider identities, actual target binaries, and zero scenario credit are
retained in `fzy/development-attempt-run43354015363-v1.json`.

Corrections are bounded: compare the isolated build copy to the pristine source,
remove only inventoried regular `.d` outputs and the bounded compiler dSYM tree,
verify the copy byte-exact, use no-case cleanup when scenarios were skipped,
and declare/bind project provenance before storage measurement. No target code
or test expectation was altered. Retry the full Linux/macOS workflow and audit
provider packets before crediting any scenario.

## Next work

1. Complete and independently audit fzy development and exact-candidate native
   qualification, retain every failure, then execute and audit its real faults,
   public authoring route, maintenance and model controls.
2. Review Pick's project package and reconcile its selected-project/candidate
   history before admission; do not change the count for a route or model
   milestone.
3. Continue all remaining selected packages and inherited campaign gates.
