# Native Bundler reductions

Development evidence only; this is not final archive qualification.

Windows run 39008017809 passed 16/20. After the general interrupt repair, run
39010635498 passes the original E03 and both independent Ruby input probes on
source `f470cd99aef89e080cc8455e4f8ad4715ecd12c2`. A controlled ignoring ancestor
also reproduced the old runner failure locally. See the
[interrupt decision](../../../decisions/windows-inherited-interrupt.md).

The exact ordinary Windows environment retained invocation
`c143b20e3dc3f9aa3c3533b1acd3e49e` with an unexpected literal `%SystemDrive%`
directory alongside the three reviewed root entries. Independent local routes
had a different PATH order and did not expose it. The diagnostic records root
names and the original report hash, verifies the marker, removes that exact owned
workspace, and preserves a separate removal receipt. The native profile now
explicitly inherits `SystemDrive` for the owned Ruby runtime's Windows system
directory expansion. It changes no expected files or entry sets. Actual new
native ordinary verification remains required.

Linux run 39010635498 passes 18/20. Run 39010958048 independently records native
Ruby 3.2.3 and `EditLine wrapper`. A five-second real PTY prints direct ANSI with
its ESC bytes intact; Readline's colored prompt emits literal `[32m` and `[0m`
without ESC. The product rendered those emitted bytes accurately. The target's
supported `NO_COLOR=1` profile avoids this unsupported colored EditLine prompt;
there is no core ANSI stripping or snapshot update.

The same run's unsaved selected-file review observes two `ruby` lines in the
otherwise exact N06 lockfile. The saved-state assertion correctly rejected that
output in the original invocation. The portable native profile uses the target's
documented `BUNDLE_FORCE_RUBY_PLATFORM=true` and omits native-platform removal,
requesting the same intended single-Ruby-platform lock directly. Every expected
byte remains unchanged. This is an explicit target workflow profile, not an
upstream repair or acceptance of duplicate lines. The original failed command,
report and unsaved review remain retained.

Local-only packets: `artifacts/runner-readiness-ten-project-pass/native/` runs
39010635498 and 39010958048. Raw synthetic Readline bytes, library identities,
selected lock review, original failed reports and removal receipts are retained
there. No diagnostic job earns a project admission. Re-run all twenty ordinary
cases, source-fault replicas and maintenance on both declared native hosts before
admission.
