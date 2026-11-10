# Runner readiness continuation checkpoint v126

Campaign remains **15/30 admitted projects**. The 26 pilot/final-matrix jobs on commit `d1d77d8f5de53ab2276abc4a0078b6488c0bfcea` passed; the dependent public recorder route failed and gives `mg` no admission credit.

## Preserved first public-route attempt

- Hosted run `42830712855`, route job `129886045505`, artifact `next20-mg-public-route-42830712855` (`13772396692`), provider size 178,750 bytes, SHA-256 `b12c3e3bc060f023bd5a7fca2bdf85f085a68fc7fa8073eb664d07106333ffba`; local ZIP CRC check passed.
- The exact candidate version command passed. The first `record` invocation (attempt `3d45e356f36946f9b0f5bfb4db14fd54`) exited 1 after 0.0867 seconds. Its immutable `finished` event reports `exit_mismatch`, console SHA-256 `5af3ba0fb0116108c279cf94342a7c2e83026a05c8fcb7dfe6847b2563616558`, and no harness cleanup errors.
- The uploaded artifact omitted the attempt `console.log` and identity manifest. The output hash is preserved, but its bytes are unavailable from that job artifact; this retention miss remains explicit and cannot be retroactively repaired. The first route remains a failed initial observation.
- Updated the registered workflow to preserve attempt directories and identity catalogs on subsequent runs, and added a manual `route_only` input so a fresh bounded route attempt can run against the already audited native matrix without dispatching another 26-cell matrix.

## Next action

Commit/push the capture correction and manually dispatch `route_only=true`. Diagnose from the fresh retained `console.log`; keep this first failure separate. Do not admit `mg` unless the new public route, remaining admission requirements, retained evidence, cleanup and independent audit all pass.
