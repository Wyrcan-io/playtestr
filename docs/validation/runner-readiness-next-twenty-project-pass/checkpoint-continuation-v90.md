# Runner readiness continuation checkpoint v90

Campaign remains **15/30 admissions**. mg has zero admission credit.

## E01 native result

The catalog?s first edge case passed on Linux and macOS in workflow `42779879155`, commit `80b41d7c94ebde304cbc481ebcf47556f30f3f29`. Both reports show 8/8 steps passed, including `(No changes need to be saved)`, exit 0 and the exact zero-byte state matched in the same invocation. Target cleanup was graceful and confirmed; provider digests match metadata; both 73-member archives pass CRC; workflow cleanup confirms owned inputs absent. Evidence: `mg/e01-native-readback-v1.json`.

N01 first-use plus N02-N08 and E01 development probes now pass on both native hosts. N02-N08/E01 totals: 100 host attempts, 90 pass, 10 failed, eight distinct selected scenarios with native passes. All failures are preserved. Local storage receipt `artifacts/runner-readiness-next-twenty-project-pass/storage/bab10bebeffe4aa2ab94440b2b546466/observed.json` reports combined retained 2,132,779,493 / 2,147,483,648 bytes, combined raw 3,974,380,236 / 6,442,450,944 bytes, and combined curated 35,229,545 / 52,428,800 bytes; no caps failed. Hosted storage validation passed as well. No formal qualification or admission gate is complete.

The mg catalog defines eight normal cases N01-N08 and twelve edge cases E01-E12. Next: E02, review exact pinned movement behavior at BOF/EOF, observe bounded refusal/beep and unchanged file bytes, then continue through E12.
