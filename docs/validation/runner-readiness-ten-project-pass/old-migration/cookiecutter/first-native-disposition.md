# First native migration disposition

Run 39335671239 at 9d61955 passed the original ten Linux scenarios and the
real corruption/legacy-false-green/public-rejection/restoration control. Its
workflow failed afterward in checked cleanup: the new explicit report selector
accepted only report v3, while the terminal-only v2 calibration correctly
produced report v2. The packet and actual failed cleanup result remain retained.

Cleanup now validates both supported report formats rather than skipping the
legacy report. A regression covers confirmed and unconfirmed v2 cleanup, and
all 52 local helper tests pass. The corrected local Windows retention verified
the original archive, every regular source member, selected restores and fresh
runtime absence before native checked removal. No local active target remains.

This is a harness-format correction; production Go, original case actions,
snapshots, saved-byte expectations and private candidate bytes are unchanged.
A fresh Linux run is required for complete cleanup and migration credit. The
failed workflow is not reported as successful native qualification.
