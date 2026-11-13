# Runner readiness continuation checkpoint v183

## Campaign status

The campaign remains at **18/30 cumulative admissions**, with **2/20 new
packages** admitted (JOE and fzy). Percol remains at zero admission credit.

## Percol public-authoring attempt v2

Run `43390505123` executed the complete public route on Linux amd64 and macOS
arm64: candidate version check, record, ten controls, exact file and fixture
review, replay/save, and ordinary test. Both exported v3 specs contain the exact
`apple\n` result, unchanged synthetic inputs and expected directory entries.
Both ordinary reports passed with target exit 0, confirmed process-group cleanup
and cleaned workspaces. The helper itself then failed because the harness read
`exit_code` instead of `returncode` from `adversarial_process.execute`.

The subsequent exact source-manifest cleanup correctly rejected 16 generated
Python 2 `.pyc` files: public spec construction had omitted
`PYTHONDONTWRITEBYTECODE=1`. The complete source/runtime artifacts were retained
as required. Both ZIPs were downloaded and verified against provider digests;
the Linux archive shows the generated `selection.json`, passing ordinary report
and exact bytecode paths. See
`percol/public-first-use-attempt-v2.json`. This is a real route pass with a
harness/cleanup failure, so it earns no admission credit.

## Correction

The harness now checks `returncode` and explicitly stores
`PYTHONDONTWRITEBYTECODE=1` in the generated public spec environment. Rerun the
same route on both hosts; require its durable package receipt and exact source
restoration before advancing.
