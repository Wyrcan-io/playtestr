# Continuation checkpoint v66: native mg preflight failure preserved and repaired

Date: 10 November 2026 (Asia/Calcutta). Current-candidate admissions remain
**5/20 new projects** (15/30 cumulative). The original ten remain **0/10
requalified** on rc.6. Taskell remains a zero-credit rejection. mg remains
acquired but unbuilt, untested and unadmitted.

## First native dispatch

The user-authorized commit e268a1718834bc70104c62893dd3ebe125bf2d9a was pushed
to work/p0-p2-implementation. GitHub Actions run 42696468759 failed on both
standard hosts before acquisition or target launch. Linux job 129429517167
reported the descendant-cleanup test treating terminated zombie entries as
live; macOS job 129429517511 reported PermissionError from using killpg(..., 0)
as the process liveness probe. Both final storage steps then failed because a
fresh checkout did not yet contain the ignored active/ directory. The immutable
run summary and direct provider links are in mg/native-build-preflight-v1.json;
the original run logs remain available from the linked provider run.

## Repairs and local verification

The build helper now enumerates exact process-group members through bounded
ps output, checks that group members belong to the current UID, and
distinguishes non-running zombie records from live descendants. The storage
observer accepts an absent fresh active/ directory and rejects linked roots.
No native source was acquired or executed by the failed run.

The focused Windows suite passes its portable cases; its three POSIX-specific
tests are skipped locally and must pass on the next Linux/macOS run. The next
dispatch must prove those cleanup tests, exact-pin acquisition, both native
source builds and storage closure before any mg scenario pilot. Admission
counters remain unchanged.

Prior committed checkpoints v64 and v65 and all first-batch evidence are
unchanged. Unrelated working-tree caches and Skim drafts remain untracked and
untouched. No PR, issue, discussion, release, tag, outreach or paid action.
