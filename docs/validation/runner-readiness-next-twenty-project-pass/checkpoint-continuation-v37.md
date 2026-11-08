# Continuation checkpoint v37: 8 November 2026

Branch `work/p0-p2-implementation` was at pushed commit `29dee9e9b458393fb10b0defe445b353e624d431` for run `42489015452`. Four of the twenty new applications are admitted (14/30 cumulative). Taskell?s first-use route now passes on both native hosts, but Taskell remains unadmitted.

## Run 42489015452

Ubuntu job `128749633533` and Intel Mac job `128749633785` both passed all 250 pinned upstream tests, built Taskell 1.11.4 and Playtestr, passed the existing-task smoke, and passed all 20 candidate invocations. E12 expected Taskell?s observed exit 1 after a denied save, then verified the original Markdown bytes were unchanged; process-group and workspace cleanup succeeded. Both hosts also passed the no-JSON recorder route through `/review`, fresh `/replay`, `/save`, and ordinary execution (one report, six steps, exit 0, exact board bytes and cleanup).

The compact same-run packets are `taskell/first-use-attempts/42489015452-linux.tar.gz` and `...-macos.tar.gz`; each contains the host/runner identity, smoke, all 20 candidate reports, recorder spec, review/replay/export transcript, ordinary report, input controls, fixture, and workflow-start receipt. v32 binds all per-report/member hashes, binary identities, provider artifact IDs/digests, and recorder outcomes. Each archive was verified against the downloaded provider packet before extraction cleanup.

This is first-use exploratory evidence only. The 20-scenario catalog remains a draft pending final review/freeze. No repeat series, source faults, calibration, maintenance/relocation, compatibility distribution closure, independent audit, or Taskell admission credit exists.

Storage checkpoint v35 passed at 2026-11-08T14:42:00.541660+00:00 with combined retained 2,147,353,465 bytes and 130,183 bytes observed headroom. Receipt SHA-256: ed752a0642f5be11e55a6284197e4f2cf61625fc84b38b83b27031093516ea7b.

Next: finish the cross-host catalog review and freeze exact candidate identities/oracles. Build the bounded native 20 x 12 ordinary series with three real source-fault calibrations per host, preserve every attempt, audit the result, then complete Taskell?s remaining public maintenance, compatibility, exact-candidate, retention and admission gates. Continue the other selected applications; no project count is rounded up. No issue, PR, discussion, release, or outreach mutation was performed.
