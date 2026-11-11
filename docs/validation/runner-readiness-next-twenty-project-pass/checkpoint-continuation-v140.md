# Runner readiness continuation checkpoint v140

Campaign remains **16/30 cumulative admissions** and **6/20 new-project admissions**. No candidate, project or fault admission credit changed.

## rc.7 first native attempt and correction

Workflow run `43055248167` failed on all three hosts before SDK acquisition or any production-source test/build. The wrapper rejected the checkout because `SOURCE_REVISION` was set to `df7fd54375e411542ce899c0e05b19db643ba64b` while the second checkout step still used ref `24029291cd0221d7611f07d27b464ec0936a815f`. This is a prelaunch harness configuration failure.

The exact provider artifacts were retrieved, their local ZIP byte counts/SHA-256 values matched GitHub metadata, and all three extracts contain the failed command identity, started/identified/launched/finished events, console log and harness error. The helper process was reaped and no target/source/SDK tree was acquired. Readback and provider IDs/digests are in `replacement-candidate-attempt-v1-readback.json`; immutable raw ZIPs and bounded extracts remain under ignored campaign `artifacts/.../tmp/rc7-attempt-v1/`.

The declaration now binds the second checkout's `ref: ${{ env.SOURCE_REVISION }}` to the same full intended source SHA. New candidate workflow run required; the failed run remains zero-launch/zero-credit.

## Other hosted work on df7fd543

JOE v2 run `43054584381` uses existing rc.6 candidate archives, not rc.7. Three Linux fault jobs and two Darwin jobs were successful at last read; the remaining Darwin forward-delete job was queued. These are provisional calibration outcomes only, not rc.7 exact-candidate or admission evidence. Retrieve and audit all artifacts before assigning any calibration credit, then repeat JOE against the exact rc.7 archives. Git Town run `43054584184` failed (still pending classification), while Skim development/final series and JOE final qualification were in progress.

## Next

Commit/push the corrected workflow ref, updated predeclaration hash, and immutable v1 artifact readback. Monitor the corrected native candidate run through completion; retrieve, provider-digest verify, extract and independently audit each host packet. Only then create an exact native-exit-v2 candidate freeze. Continue exact-candidate JOE scenarios/faults, affected project admissions, original ten, migrations, controls, delivered CI, fresh checkout, storage/cleanup and final audit.
