# Runner readiness continuation checkpoint v165

## Cumulative status

The campaign remains **17/30 admitted**. Fzy's final ordinary matrix is
independently audited at 480/480 on Linux and macOS. Its fault calibration is
still open and earns zero credit until complete independent readback.

## Latest fault-run finding

Run `43362139656` passed earlier baseline/corrupted/restored phases far enough
to reach the F03 mutated-source build. The declared F03 mutated file digest was
wrong: it did not match the exact byte replacement applied by the runner. The
pinned source file's baseline hash and one-region replacement were reproduced
locally; the correct mutated digest is now frozen as
`2de42f4ffd879c93208bd630341d2a111582bc66657808d34ca7df2f2a729123`.

The run and both artifact digests are appended to
`fzy/fault-calibration-attempt-run43360846815-v1.json`. No phase or fault
credit is claimed from this incomplete matrix. Earlier preserved findings
include the F02 report boundary correction to exact output failure at step 6.

## Next action

Re-run the complete Linux/macOS matrix against the corrected fault declaration.
The next artifact audit will verify source archive and file bytes, pristine and
mutated build logs/binaries, all 18 reports and event chains, candidate hashes,
source removal, and process cleanup. Then complete fzy's public authoring,
maintenance, model controls and admission review before moving on to further
project slots.
