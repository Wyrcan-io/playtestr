# Runner readiness continuation checkpoint v180

## Campaign status

The campaign remains at **18/30 cumulative admissions**, with **2/20 new
packages** admitted (JOE and fzy). Percol remains in progress with zero admission
credit. The exact candidate is `v0.4.0-rc.8` (`native-exit-v3`).

## Percol development attempt v7

Run `43385198838` reached E07 on Linux amd64 and macOS arm64 after N01–N08 and
E01–E06 passed on each host. E07 started with both `Blue` and `blue`, typed the
lowercase query after case-sensitive mode setup, required a visible `1/1` result,
and selected it. Both reports show one lowercase result on screen and target exit
0, but the exact `result.txt` assertion for `blue\n` failed on both hosts. The
report omits the observed bytes, so the mismatch is not yet diagnosed. The exact
provider artifact digests were verified after download. Both hosts passed
process-group cleanup, workspace cleanup, source restoration, runtime cleanup,
source/runtime removal and storage checks. The immutable failure receipt is
`percol/development-attempt-v7.json`; no admission credit is earned.

## Next action

Preserve v7. Prepare v8 to retain its rendered interaction and exact saved-output
check, while writing a harness-owned hexadecimal diagnostic of `result.txt` to
the PTY after Percol exits. Run v8 on both standard GitHub hosted native runners,
inspect exact bytes and every cleanup path, then decide whether the mismatch is
in Percol behavior or the reviewed expectation before any admission accounting.
