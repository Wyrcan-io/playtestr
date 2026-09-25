#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 2 ]]; then
  echo 'usage: run.sh FROZEN_RUNNER OUTPUT_DIRECTORY' >&2
  exit 2
fi

runner="$1"
out="$2"
suffix=''
if [[ "$(go env GOOS)" == windows ]]; then suffix='.exe'; fi
mkdir -p "$out" artifacts/release-stories/bin
runner_hash="$(sha256sum "$runner" | awk '{print $1}')"

run_pass() {
  local name="$1" spec="$2"
  "$runner" test --report "$out/$name.json" --artifacts-dir "$out/$name-artifacts" "$spec" >"$out/$name.log" 2>&1
}
run_failure() {
  local name="$1" spec="$2"
  set +e
  "$runner" test --report "$out/$name.json" --artifacts-dir "$out/$name-artifacts" "$spec" >"$out/$name.log" 2>&1
  local status=$?
  set -e
  test "$status" -eq 1
}

# Hero: one unchanged spec detects the reviewed wrong-selection source defect.
go build -o "artifacts/release-stories/bin/selector-good$suffix" ./benchmarks/competitive/c1/selector
go build -tags competitive_bad -o "artifacts/release-stories/bin/selector-bad$suffix" ./benchmarks/competitive/c1/selector
cp "artifacts/release-stories/bin/selector-good$suffix" "artifacts/release-stories/bin/selector$suffix"
export C1_RESULT_PATH="$PWD/$out/hero-result.txt"
run_pass hero-pass release/stories/hero.json
test "$(tr -d '\r\n' < "$C1_RESULT_PATH")" = Beta
cp "artifacts/release-stories/bin/selector-bad$suffix" "artifacts/release-stories/bin/selector$suffix"
run_failure hero-defect release/stories/hero.json
test "$(tr -d '\r\n' < "$C1_RESULT_PATH")" = Alpha
cp "artifacts/release-stories/bin/selector-good$suffix" "artifacts/release-stories/bin/selector$suffix"
run_pass hero-recovery release/stories/hero.json
test "$(tr -d '\r\n' < "$C1_RESULT_PATH")" = Beta

# Stateful: an adapter makes the file oracle part of the target result.
go build -o "artifacts/release-stories/bin/stateful-good$suffix" ./benchmarks/competitive/c2/stateful
go build -tags competitive_bad -o "artifacts/release-stories/bin/stateful-bad$suffix" ./benchmarks/competitive/c2/stateful
go build -o "artifacts/release-stories/bin/stateful-oracle$suffix" ./release/stories/stateful-oracle
export C2_CONFIG_PATH="$PWD/$out/stateful.conf"
cp "artifacts/release-stories/bin/stateful-good$suffix" "artifacts/release-stories/bin/stateful$suffix"
run_pass stateful-pass release/stories/stateful.json
test "$(tr -d '\r\n' < "$C2_CONFIG_PATH")" = port=4242
rm -f "$C2_CONFIG_PATH"
run_pass stateful-cancel release/stories/stateful-cancel.json
test ! -e "$C2_CONFIG_PATH"
cp "artifacts/release-stories/bin/stateful-bad$suffix" "artifacts/release-stories/bin/stateful$suffix"
run_failure stateful-defect release/stories/stateful.json
test "$(tr -d '\r\n' < "$C2_CONFIG_PATH")" = port=8080
cp "artifacts/release-stories/bin/stateful-good$suffix" "artifacts/release-stories/bin/stateful$suffix"
run_pass stateful-recovery release/stories/stateful.json
test "$(tr -d '\r\n' < "$C2_CONFIG_PATH")" = port=4242

# Compatibility: the same resize spec rejects a stale-viewport redraw.
go build -o "artifacts/release-stories/bin/compatibility-good$suffix" ./release/stories/compatibility-target
go build -tags release_story_bad -o "artifacts/release-stories/bin/compatibility-bad$suffix" ./release/stories/compatibility-target
export COMPAT_RESULT_PATH="$PWD/$out/compatibility-result.txt"
cp "artifacts/release-stories/bin/compatibility-good$suffix" "artifacts/release-stories/bin/compatibility$suffix"
run_pass compatibility-pass release/stories/compatibility.json
test "$(tr -d '\r\n' < "$COMPAT_RESULT_PATH")" = 'size=80x20 modal=false'
rm -f "$COMPAT_RESULT_PATH"
cp "artifacts/release-stories/bin/compatibility-bad$suffix" "artifacts/release-stories/bin/compatibility$suffix"
run_failure compatibility-defect release/stories/compatibility.json
test ! -e "$COMPAT_RESULT_PATH"
cp "artifacts/release-stories/bin/compatibility-good$suffix" "artifacts/release-stories/bin/compatibility$suffix"
run_pass compatibility-recovery release/stories/compatibility.json
test "$(tr -d '\r\n' < "$COMPAT_RESULT_PATH")" = 'size=80x20 modal=false'

{
  echo "runner_sha256=$runner_hash"
  echo "selector_good_sha256=$(sha256sum "artifacts/release-stories/bin/selector-good$suffix" | awk '{print $1}')"
  echo "selector_bad_sha256=$(sha256sum "artifacts/release-stories/bin/selector-bad$suffix" | awk '{print $1}')"
  echo "stateful_good_sha256=$(sha256sum "artifacts/release-stories/bin/stateful-good$suffix" | awk '{print $1}')"
  echo "stateful_bad_sha256=$(sha256sum "artifacts/release-stories/bin/stateful-bad$suffix" | awk '{print $1}')"
  echo "compatibility_good_sha256=$(sha256sum "artifacts/release-stories/bin/compatibility-good$suffix" | awk '{print $1}')"
  echo "compatibility_bad_sha256=$(sha256sum "artifacts/release-stories/bin/compatibility-bad$suffix" | awk '{print $1}')"
  echo "hero_spec_sha256=$(sha256sum release/stories/hero.json | awk '{print $1}')"
  echo "stateful_spec_sha256=$(sha256sum release/stories/stateful.json | awk '{print $1}')"
  echo "stateful_cancel_spec_sha256=$(sha256sum release/stories/stateful-cancel.json | awk '{print $1}')"
  echo "compatibility_spec_sha256=$(sha256sum release/stories/compatibility.json | awk '{print $1}')"
} > "$out/hashes.txt"

python - "$out" <<'PY'
import json, pathlib, sys
root = pathlib.Path(sys.argv[1])
expected = {
    'hero-pass': 'passed', 'hero-defect': 'failed', 'hero-recovery': 'passed',
    'stateful-pass': 'passed', 'stateful-cancel': 'passed',
    'stateful-defect': 'failed', 'stateful-recovery': 'passed',
    'compatibility-pass': 'passed', 'compatibility-defect': 'failed',
    'compatibility-recovery': 'passed',
}
expected_failures = {
    'hero-defect': 'unexpected_exit',
    'stateful-defect': 'unexpected_exit',
    'compatibility-defect': 'assertion_timeout',
}
for name, status in expected.items():
    record = json.loads((root / f'{name}.json').read_text(encoding='utf-8'))
    assert record['results'][0]['status'] == status, (name, record)
    assert record['results'][0]['cleanup']['confirmed_exited'], (name, record)
    if name in expected_failures:
        assert record['results'][0]['failure']['category'] == expected_failures[name], (name, record)
(root / 'summary.json').write_text(json.dumps({
    'schema_version': 1,
    'status': 'passed',
    'runner_sha256': dict(line.split('=', 1) for line in (root / 'hashes.txt').read_text().splitlines())['runner_sha256'],
    'story_outcomes': expected,
    'editing': 'none; full command logs retained',
    'accelerated_waits': 'none',
    'capture_tooling': 'GitHub Actions log and Playtestr JSON/text artifacts',
}, indent=2) + '\n', encoding='utf-8')
PY
