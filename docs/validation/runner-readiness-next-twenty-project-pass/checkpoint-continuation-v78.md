# Continuation checkpoint v78

## Campaign count

Still **15/30**: five new project admissions and zero original-ten current-candidate requalifications. mg remains unadmitted.

## Current mg cases

N01 first-use and N02/N03 scenario probes pass on Linux/macOS. N04 is under development. Its first native attempt (run 42721418974) failed at step 18 on both hosts after cut-and-yank: the saved-screen candidate was `alpha  gammabeta`, with no separator between line-end text and the yanked word. Save and state assertions did not run; forced process-group cleanup was confirmed. Retained reports/screens/archive identities are in `mg/n04-first-attempt-readback-v1.json`.

N04 now inserts one explicit space after CtrlE and before CtrlY. The source review and test cover that ordering. Next push and inspect the corrected Linux/macOS run, preserving the original failure. Current development host attempts for N02/N03/N04 include 18 attempts, 12 passes and 6 failures; N01 pilot runs are accounted separately. Qualification remains zero.
