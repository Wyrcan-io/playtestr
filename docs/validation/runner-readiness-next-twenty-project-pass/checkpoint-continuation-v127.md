# Runner readiness continuation checkpoint v127

Campaign remains **15/30 admitted projects**. `mg` still has zero admission credit; the two route attempts below failed during target command resolution before any target process launched.

## Route attempt 2 and diagnosis

- Route-only GitHub run `42840242945`, artifact ID `13775971217`, size 182,083 bytes, SHA-256 `7c06ca4a099ba219f51ad7f87b53f558885b86aaaa4aee59a67beb0193aa5b6b`. Local ZIP CRC passed, and this packet includes the route command's `console.log` plus identity catalog and events.
- Version check passed (`31020ce54cc54a14832e643a84da1b5c`). First recorder invocation `c35184e1727f409db501f79af6351c71` exited 1 after 0.0609 seconds; cleanup had no errors. Its captured console ends with `resolve workspace command "mg" before changing cwd: exec: "mg": executable file not found in $PATH`.
- The retained build artifact's `active/mg/install/bin/mg` mode was `0644` after `actions/download-artifact` and `upload-artifact`, despite exact binary bytes matching. The public route copied that mode unchanged. Existing native pilot code already contains the required scoped execute-bit restoration helper; the route now applies it only to the owned copy and receipts before/after mode without modifying target bytes.
- Attempt 1 (run `42830712855`, artifact ID `13772396692`) is preserved separately. Its artifact omitted the console and identity manifest; its event hash and exit mismatch remain, but the exact console bytes cannot be recovered. This first-retention defect remains open and is not retroactively repaired.
- Updated route helper tests cover execute-bit restoration and byte preservation in addition to report cleanup/positive-evidence checks. The next route-only run will capture all attempt directories, console logs and identities.

## Next action

Commit/push the scoped permission fix and run the standard hosted Linux route-only workflow. Keep both prior failures and their separate evidence limitations. `mg` remains unadmitted until the first-use, diagnosis, maintenance, relocation, workflow-preview, cleanup and independent audit checks all pass.
