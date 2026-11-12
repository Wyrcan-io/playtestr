# Runner readiness continuation checkpoint v143

## Admission count and candidate scope

The last closed candidate checkpoint remains 16/30 (ten first-batch admissions plus six exact-rc.6 new-project admissions). JOE is now independently admitted on exact rc.7, so the cumulative campaign stands at **17/30** and the next-twenty rc.7 projection stands at **1/20**. This does not transfer any rc.5/rc.6 project to rc.7. The original ten still have zero rc.7 qualification; the other nine next-twenty projects still require exact-current-candidate evidence. Paid admissions remain zero.

`projects.json` now names rc.7 as the qualification candidate and records only JOE in its current-candidate projection: 20 canonical scenarios, two native cells, 480 ordinary executions, 18 required calibration phases and three distinct source faults. The ten historical next-twenty admissions remain separately itemized across rc.5/rc.6. The updated JOE `admission.json` hash is in the project row and admission-subject list.

## JOE rc.7 closure

The exact candidate remains `v0.4.0-rc.7` / `native-exit-v2`, frozen from candidate workflow run `43056391377`. Campaign implementation commit `439db6ea5ec014cc15b2de92d7b94dc9dc26e58f` was pushed to `work/p0-p2-implementation` under the existing authorization.

- Scenario-development run `43063382292`: independent artifact audit verifies 20/20 launched scenarios per Linux and macOS host.
- Final qualification run `43063382262`: independent artifact audit verifies 240/240 outcomes per host (12 repetitions x 20 scenarios), exact candidate archive, target build identities, source restoration and cleanup.
- Source-fault run `43063382475`: independent audit verifies three distinct detected faults, 18/18 baseline/fault/recovery phases, source restoration and owned process/tree cleanup.
- Public authoring route run `43063382264`: exact-candidate route readback verifies first-use, seeded diagnosis, selected state maintenance, Unicode relocation and workflow preview on Linux/macOS.
- Oracle route run `43069489959`: both hosted jobs succeeded. Independent provider artifact audit verifies 22 cases: one positive per host and ten negative state assertions per host; all negatives failed at the intended state checkpoint after terminal/exit evidence. Exact LF, CRLF, empty, NUL, no-final-newline and Unicode byte families matched. Each report binds the state assertion to its own invocation/workspace and confirms cleanup.
- Positive/tampered model run: `next20_joe_model_controls.py` reconstructs both host models from the independent audit receipts; all 12 deliberately altered evidence models were rejected, then the unchanged model revalidated.
- Admission audit verifies the frozen 8-normal/12-edge set, both exact rc.7 archives, all three real faults, required calibrations, public route, model controls and cleanup before writing `joe/admission.json`.

The first JOE scenario revision's six failures per host and earlier public-route/maintenance failures remain retained; successful revisions do not erase them. Human usability remains unmeasured; no participant was contacted. The new calibration and model controls add no project/scenario/fault credit beyond JOE's complete admission.

## Next action

Continue the 30-project execution. Requalify each remaining credited project and the original ten against rc.7, preserving first failures and exact native evidence; select the next project using the canonical ledger and do not reuse active source trees. Current count is 17/30, not campaign completion.
