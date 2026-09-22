#!/usr/bin/env bash
set -u

task=${1:?task is required}
tool=${2:?tool is required}
attempt=${3:?attempt identity is required}
oracle_path=${4:?oracle path is required}
root=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
bin_dir="$root/artifacts/competitive/bin"
tool_dir="$root/artifacts/competitive/tools"
evidence_dir="$root/artifacts/competitive/evidence/$task/$tool/$attempt"
mkdir -p "$evidence_dir" "$(dirname "$oracle_path")"

case "$task" in
  C2)
    target="$bin_dir/stateful"
    spec_playtestr="$root/benchmarks/competitive/c2/playtestr.json"
    spec_atago="$root/benchmarks/competitive/c2/atago.atago.yaml"
    rust_test=c2_stateful_setup
    printf 'port=8080\n' >"$oracle_path"
    export C2_CONFIG_PATH="$oracle_path"
    export C2_STATEFUL_BIN="$target"
    ;;
  C3)
    target="$bin_dir/resize"
    spec_playtestr="$root/benchmarks/competitive/c3/playtestr.json"
    spec_atago="$root/benchmarks/competitive/c3/atago.atago.yaml"
    rust_test=c3_resize_redraw
    ;;
  *)
    echo "unsupported task: $task" >&2
    exit 2
    ;;
esac

status=0
case "$tool" in
  playtestr)
    "$bin_dir/playtestr" test --artifacts-dir "$evidence_dir" \
      --report "$evidence_dir/report.json" "$spec_playtestr" || status=$?
    ;;
  atago)
    "$tool_dir/atago" run --ci --parallel 1 --artifacts-dir "$evidence_dir" \
      "$spec_atago" || status=$?
    ;;
  tui-test)
    session="${task,,}-${attempt//[^a-zA-Z0-9_-]/-}"
    common=(--session "$session" --failure-artifacts "$evidence_dir")
    run_args=(run --restart --cols 60 --rows 12)
    if [[ "$task" == C2 ]]; then
      run_args+=(--env "C2_CONFIG_PATH=$oracle_path")
    fi
    run_args+=(/bin/sh -c '"$1"; code=$?; printf "\nTARGET_EXIT:%s\n" "$code"; exit "$code"' c-exit-shim "$target")
    "$tool_dir/tui-test" "${common[@]}" "${run_args[@]}" || status=$?
    if [[ $status -eq 0 && "$task" == C2 ]]; then
      "$tool_dir/tui-test" "${common[@]}" expect text "Port (1024-65535):" --timeout 5000 || status=$?
      [[ $status -ne 0 ]] || "$tool_dir/tui-test" "${common[@]}" type invalid || status=$?
      [[ $status -ne 0 ]] || "$tool_dir/tui-test" "${common[@]}" key press Enter || status=$?
      [[ $status -ne 0 ]] || "$tool_dir/tui-test" "${common[@]}" expect text "Invalid port" --timeout 5000 || status=$?
      [[ $status -ne 0 ]] || "$tool_dir/tui-test" "${common[@]}" type 4242 || status=$?
      [[ $status -ne 0 ]] || "$tool_dir/tui-test" "${common[@]}" key press Enter || status=$?
      [[ $status -ne 0 ]] || "$tool_dir/tui-test" "${common[@]}" expect text "Saved port 4242" --timeout 5000 || status=$?
    elif [[ $status -eq 0 ]]; then
      "$tool_dir/tui-test" "${common[@]}" expect text "Main screen" --timeout 5000 || status=$?
      [[ $status -ne 0 ]] || "$tool_dir/tui-test" "${common[@]}" key press '?' || status=$?
      [[ $status -ne 0 ]] || "$tool_dir/tui-test" "${common[@]}" expect text "Help modal" --timeout 5000 || status=$?
      [[ $status -ne 0 ]] || "$tool_dir/tui-test" "${common[@]}" resize 80 20 || status=$?
      [[ $status -ne 0 ]] || "$tool_dir/tui-test" "${common[@]}" expect text "Size: 80x20" --timeout 5000 || status=$?
      [[ $status -ne 0 ]] || "$tool_dir/tui-test" "${common[@]}" key press Escape || status=$?
      [[ $status -ne 0 ]] || "$tool_dir/tui-test" "${common[@]}" expect text "Help modal" --not --timeout 5000 || status=$?
      [[ $status -ne 0 ]] || "$tool_dir/tui-test" "${common[@]}" expect text "Press ? for help" --timeout 5000 || status=$?
      [[ $status -ne 0 ]] || "$tool_dir/tui-test" "${common[@]}" key press q || status=$?
    fi
    if [[ $status -eq 0 ]]; then
      "$tool_dir/tui-test" "${common[@]}" expect text "TARGET_EXIT:0" --timeout 5000 || status=$?
    fi
    if [[ $status -eq 0 ]]; then
      "$tool_dir/tui-test" "${common[@]}" wait exit --timeout 5000 || status=$?
    fi
    "$tool_dir/tui-test" --session "$session" close >/dev/null 2>&1 || true
    ;;
  termlens)
    if [[ "$task" == C3 ]]; then
      export C3_RESIZE_BIN="$target"
    fi
    CARGO_TARGET_DIR="$root/artifacts/competitive/cargo-target" \
      cargo +1.85.0 test --offline --locked \
      --manifest-path "$root/benchmarks/competitive/c1/termlens/Cargo.toml" \
      --test c1 -- "$rust_test" --exact --nocapture || status=$?
    ;;
  *)
    echo "unsupported tool: $tool" >&2
    exit 2
    ;;
esac

if [[ $status -eq 0 && "$task" == C2 ]]; then
  [[ $(cat "$oracle_path") == 'port=4242' ]] || status=1
fi
exit "$status"
