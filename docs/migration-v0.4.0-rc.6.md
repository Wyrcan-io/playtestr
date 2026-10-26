# Native exit-status migration (private candidate in development)

No rc.6 release or qualified replacement archive exists yet. Current source
repairs a defect found while validating cargo-generate: Windows native control-C
returned `3221225786`, which rc.5 reported but could neither assert nor render in
HTML. The original application failures and before-fix regressions are retained.

Spec v3 now permits exact unsigned 32-bit `exit` values, from `0` through
`4294967295`. Spec v1/v2 expectations remain `0` through `255`. All report schemas
and the HTML reader accept the full captured native range, including unexpected
wide exits from older specs. No field, report-version number, baseline or fixture
is rewritten. Unix signals retain the existing `128 + signal` convention; Windows
statuses remain native values. No truncation or cross-platform remapping occurs.

For a Windows interruption test, use its observed native value, for example
`{"exit":3221225786}` in a v3 managed-fixture test. A target that handles an
interrupt can return another status. Current 64-bit source builds represent the
full range; this change supplies no additional platform qualification claim.

Keep the earlier executable beside a replacement, verify its exact archive and
version, then change PATH. Older readers cannot run wider expectations and may
reject reports containing them. Rollback restores the earlier executable and
compatible expectations; keep the original reports for a current reader.

The twenty-project campaign must build a distinct private candidate and
requalify the original ten and the four rc.5 admissions on its exact archives.
Those historical rc.5 receipts remain valid for their recorded bytes and are
not replacement-candidate evidence. Native regression, distribution, migration
and campaign closure gates remain open. No release/tag/publication is authorized.

Windows returns application or exception termination values through its native
DWORD status API. See Microsoft's [GetExitCodeProcess contract](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-getexitcodeprocess).
