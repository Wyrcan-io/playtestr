# Runner readiness continuation checkpoint v158

## Cumulative status

The campaign remains **17/30 admitted**. fzy is not yet admitted. Its full
first native matrix now has independent artifact readback; Pick remains pending
separate package and ledger review.

## fzy development matrix audit

Run `43356291927` passed all 20 cases on Linux amd64 and macOS arm64 (40/40).
The exact provider ZIPs were retrieved into workspace scratch and independently
checked against their provider byte counts and SHA-256 digests. The new auditor
validated ZIP CRCs, unique safe paths and expansion bounds; pinned source and
build/runtime identities; upstream test receipts; exact rc.8 installation;
each scenario spec digest in the attempt identity; all four positive attempt
events; report hashes, exact exit codes and all steps; source restoration; and
target/descendant cleanup. It reconstructed all 40 unique passed invocations.
The audit is `fzy/development-artifact-audit-v2.json`; the exact contract is
`fzy/scenario-declaration-v1.json`. No project admission credit is assigned.

The artifact audit identified and corrected a receipt-label mix-up: the
candidate provider ZIP digest and the nested frozen runner archive digest are
now recorded as separate fields. The receipt retains the provider ZIP, while
the installed archive hash matches the candidate freeze.

## Remaining

1. Run the exact frozen 20-case contract twelve times on each supported native
   host, then independently audit the complete 480-outcome matrix.
2. Calibrate real source faults, public authoring/update workflows, maintenance,
   oracle/model controls and every admission requirement for fzy.
3. Review Pick, continue the remaining new projects, and close original-project
   candidate qualification and global campaign gates before claiming 30.
