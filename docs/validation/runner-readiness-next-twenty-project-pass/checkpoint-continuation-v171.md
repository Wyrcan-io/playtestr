# Runner readiness continuation checkpoint v171

## Campaign status

The cumulative campaign remains **17/30 admitted**. Fzy's technical route is
still open and has zero technical/admission credit.

## First native technical-route attempt

Run `43365829863` rebuilt the exact fzy source and passed its upstream tests on
Linux and macOS. Both hosts passed the exact-candidate version check, two-spec
suite listing, manual v3 execution with exact fixture-byte preservation, and
machine-to-HTML report check. The v2 execution did not launch: its spec sat at
the technical output root while the shared identity recorder requires its
relative fixture directory alongside the spec. This was a harness setup defect,
not an application failure.

The exact provider packets are preserved in
`fzy/technical-route-attempt-run43365829863-v1.json`. Both jobs restored and
removed the owned source, verified no matching target processes remained, and
passed storage bounds. The attempt receives zero technical or admission credit.
The v2 spec and its fixture are now created under the same migration directory,
with a focused placement regression.

## Remaining work

Rerun the corrected Linux/macOS route and independently audit both provider
packets. Continue to preserve partial failures and award no credit until the
complete route passes. Fzy still needs model controls and package/ledger review;
the remaining projects and campaign-wide gates remain open.
