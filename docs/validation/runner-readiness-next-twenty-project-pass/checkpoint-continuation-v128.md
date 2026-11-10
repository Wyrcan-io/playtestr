# Runner readiness continuation checkpoint v128

Campaign remains **15/30 admitted projects**. `mg` remains unadmitted.

## Route attempt 3

- Hosted Linux route-only run `42883681805`, artifact `13795680694`, size 182,702 bytes, SHA-256 `55051fc97fbe6b38bbe74ea96cebdc63e1a0d3c6f4a68673ba53ec455430e632`; the local ZIP CRC check passed.
- The scoped execute-bit restoration worked: the recorder resolved the owned `mg` target, launched it, observed the initial fixture and typed marker, saved the note, and captured exact expected bytes (`MG_PUBLIC_ROUTE_START\nMG_PUBLIC_ROUTE_RC6`). The artifact `planned.json` records the copy's mode transition.
- The first-use invocation still failed because the `Wrote public-note.txt` checkpoint hit `context deadline exceeded` at the 5-second step budget. The attempt's complete console is retained at `mg/73a57a28e8af4f7184c1fe2addbd22b6/console.log`; it contains the full generated draft and failed/rejected `/review`, `/replay`, `/save` controls. This remains a route failure, not a pass. Run 42883681805 is preserved as a separate failed attempt.
- The recorder controller trims leading/trailing whitespace from control lines; therefore `/expect Wrote ` silently loses its trailing space. The next attempt now uses the meaningful prefix `/expect Wrote` and a 15-second step budget. The independent `/file public-note.txt` assertion still checks the exact intended bytes.

## Next action

Run the next bounded route-only attempt with the corrected status anchor. Preserve this failed draft and all earlier failures. `mg` remains gated on review, fresh replay/export, ordinary test, diagnosis, selected maintenance, relocation, workflow preview, complete cleanup and independent audit.
