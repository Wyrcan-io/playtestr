# Runner readiness continuation checkpoint v159

## Cumulative status

The audited admission total remains **17/30**. Fzy's first 40 development
outcomes passed independent readback. Its exact-candidate final matrix has not
started; Pick remains pending its independent package and ledger review.

## Preserved prelaunch run 43358141466

Both hosts acquired and built the pinned fzy source, passed all 32 upstream
tests and installed the frozen rc.8 runner. Before any Playtestr invocation, the
scenario helper attempted phase `qualification`; the campaign event recorder
rejected it because that label was not declared. There were zero scenario
launches. The workflow's report-required cleanup correctly refused to report
target cleanup without a target report, leaving the owned source/runtime tree
in the hosted job workspace until that ephemeral job ended. Storage was
measured and both provider packets were retained in
`fzy/final-archive-attempt-run43358141466-v1.json`. No scenario or cleanup credit
is assigned to this attempt.

The workflow now records the repeated exact-candidate phase as the declared
`final-archive` phase. It will run all 20 frozen scenarios twelve times on each
host, then use the same explicit cleanup and storage checks.

## Next work

1. Rerun the exact 12 × 20 Linux/macOS matrix on rc.8, retrieve both ZIPs and
   independently audit all 480 outcomes and cleanup evidence.
2. Complete fzy source-fault calibration, public authoring and maintenance,
   model/oracle controls and admission review.
3. Reconcile Pick and continue the remaining projects and inherited gates to 30
   complete admissions.
