#!/usr/bin/env bash
set -u

tool=${1:?tool is required}
attempt=${2:?attempt identity is required}
result_path=${3:?oracle result path is required}
root=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
bin_dir="$root/artifacts/competitive/bin"
tool_dir="$root/artifacts/competitive/tools"
evidence_dir="$root/artifacts/competitive/evidence/$tool/$attempt"
selector="$bin_dir/selector"

mkdir -p "$evidence_dir" "$(dirname "$result_path")"
rm -f "$result_path"
export C1_RESULT_PATH="$result_path"
export C1_SELECTOR_BIN="$selector"

case "$tool" in
  playtestr)
    "$bin_dir/playtestr" test \
      --artifacts-dir "$evidence_dir" \
      --report "$evidence_dir/report.json" \
      "$root/benchmarks/competitive/c1/playtestr.json"
    ;;
  atago)
    "$tool_dir/atago" run --ci --parallel 1 \
      --artifacts-dir "$evidence_dir" \
      "$root/benchmarks/competitive/c1/atago.atago.yaml"
    ;;
  tui-test)
    session="c1-${attempt//[^a-zA-Z0-9_-]/-}"
    common=(--session "$session" --failure-artifacts "$evidence_dir")
    status=0
    "$tool_dir/tui-test" "${common[@]}" run --restart --cols 60 --rows 12 \
      --env "C1_RESULT_PATH=$result_path" "$selector" || status=$?
    if [[ $status -eq 0 ]]; then
      "$tool_dir/tui-test" "${common[@]}" expect text "Select record" --timeout 5000 || status=$?
    fi
    if [[ $status -eq 0 ]]; then
      "$tool_dir/tui-test" "${common[@]}" key press Down || status=$?
    fi
    if [[ $status -eq 0 ]]; then
      "$tool_dir/tui-test" "${common[@]}" expect text "> Beta" --timeout 5000 || status=$?
    fi
    if [[ $status -eq 0 ]]; then
      "$tool_dir/tui-test" "${common[@]}" key press Enter || status=$?
    fi
    if [[ $status -eq 0 ]]; then
      "$tool_dir/tui-test" "${common[@]}" expect text "Selected: Beta" --timeout 5000 || status=$?
    fi
    if [[ $status -eq 0 ]]; then
      "$tool_dir/tui-test" "${common[@]}" wait exit --timeout 5000 || status=$?
    fi
    if [[ $status -eq 0 ]]; then
      "$tool_dir/tui-test" "${common[@]}" expect exit-code 0 --timeout 5000 || status=$?
    fi
    "$tool_dir/tui-test" --session "$session" close >/dev/null 2>&1 || true
    exit "$status"
    ;;
  termlens)
    CARGO_TARGET_DIR="$root/artifacts/competitive/cargo-target" \
      cargo +1.85.0 test --offline --locked \
      --manifest-path "$root/benchmarks/competitive/c1/termlens/Cargo.toml" \
      --test c1 -- c1_selection --exact --nocapture
    ;;
  *)
    echo "unsupported tool: $tool" >&2
    exit 2
    ;;
esac
