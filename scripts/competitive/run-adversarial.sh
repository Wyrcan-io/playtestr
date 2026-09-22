#!/usr/bin/env bash
set -euo pipefail

root=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
artifact_root="$root/artifacts/competitive"
bin_dir="$artifact_root/bin"
tool_dir="$artifact_root/tools"
fixture="$bin_dir/adversarial"
log_dir="$artifact_root/logs"
pid_dir="$artifact_root/adversarial-pids"
ledger="$artifact_root/adversarial.jsonl"
mkdir -p "$log_dir" "$pid_dir"
: >"$ledger"
export ADVERSARIAL_BIN="$fixture"

wait_for_pid_file() {
  local path=$1
  for _ in $(seq 1 100); do
    [[ -s "$path" ]] && return 0
    sleep 0.05
  done
  return 1
}

process_gone() {
  local path=$1 pid
  [[ -s "$path" ]] || return 1
  pid=$(tr -d '\r\n' <"$path")
  for _ in $(seq 1 40); do
    if ! kill -0 "$pid" 2>/dev/null; then return 0; fi
    sleep 0.05
  done
  kill -KILL "$pid" 2>/dev/null || true
  return 1
}

record_case() {
  local tool=$1 case_name=$2 capability=$3 expected_class=$4
  local identity="$tool-$case_name" pid_path="$pid_dir/$tool-$case_name.pid"
  local log="$log_dir/adversarial-$tool-$case_name.log" status=0 survivor=false outcome=passed
  rm -f "$pid_path"
  export ADVERSARIAL_PID_PATH="$pid_path"
  local started ended elapsed_ms
  started=$(date +%s%N)
  set +e
  case "$tool:$case_name" in
    playtestr:hang)
      "$bin_dir/playtestr" test --report "$artifact_root/playtestr-hang.json" \
        --artifacts-dir "$artifact_root/evidence/adversarial/playtestr-hang" \
        "$root/benchmarks/competitive/adversarial/playtestr-hang.json" >"$log" 2>&1
      status=$?
      [[ $status -eq 1 ]] && jq -e '.results[0].failure.category == "run_timeout"' "$artifact_root/playtestr-hang.json" >/dev/null || status=99
      ;;
    playtestr:cancel)
      "$bin_dir/playtestr" test --report "$artifact_root/playtestr-cancel.json" \
        --artifacts-dir "$artifact_root/evidence/adversarial/playtestr-cancel" \
        "$root/benchmarks/competitive/adversarial/playtestr-cancel.json" >"$log" 2>&1 &
      runner_pid=$!
      if wait_for_pid_file "$pid_path"; then kill -INT "$runner_pid" 2>/dev/null; fi
      wait "$runner_pid"; status=$?
      if [[ $status -eq 130 ]] && jq -e '.results[0].failure.category == "cancelled"' "$artifact_root/playtestr-cancel.json" >/dev/null; then
        status=0
      else
        status=99
      fi
      ;;
    playtestr:flood)
      "$bin_dir/playtestr" test --report "$artifact_root/playtestr-flood.json" \
        --artifacts-dir "$artifact_root/evidence/adversarial/playtestr-flood" \
        "$root/benchmarks/competitive/adversarial/playtestr-flood.json" >"$log" 2>&1
      status=$?
      [[ $status -eq 1 ]] && jq -e '.results[0].failure.category == "output_limit"' "$artifact_root/playtestr-flood.json" >/dev/null || status=99
      ;;
    atago:hang)
      "$tool_dir/atago" run --ci --parallel 1 "$root/benchmarks/competitive/adversarial/atago-hang.atago.yaml" >"$log" 2>&1
      status=$?
      [[ $status -ne 0 ]] || status=99
      ;;
    atago:cancel)
      "$tool_dir/atago" run --ci --parallel 1 "$root/benchmarks/competitive/adversarial/atago-cancel.atago.yaml" >"$log" 2>&1
      status=$?
      ;;
    atago:flood)
      "$tool_dir/atago" run --ci --parallel 1 "$root/benchmarks/competitive/adversarial/atago-flood.atago.yaml" >"$log" 2>&1
      status=$?
      ;;
    tui-test:hang)
      session=adversarial-hang
      "$tool_dir/tui-test" --session "$session" run --restart --cols 60 --rows 12 --env "ADVERSARIAL_PID_PATH=$pid_path" "$fixture" hang >"$log" 2>&1 || status=$?
      [[ $status -ne 0 ]] || "$tool_dir/tui-test" --session "$session" expect text "adversarial ready" --timeout 5000 >>"$log" 2>&1 || status=$?
      if [[ $status -eq 0 ]]; then
        "$tool_dir/tui-test" --session "$session" wait exit --timeout 500 >>"$log" 2>&1
        wait_status=$?
        [[ $wait_status -ne 0 ]] || status=99
      fi
      "$tool_dir/tui-test" --session "$session" kill >>"$log" 2>&1 || status=$?
      "$tool_dir/tui-test" --session "$session" close >>"$log" 2>&1 || true
      ;;
    tui-test:cancel)
      session=adversarial-cancel
      "$tool_dir/tui-test" --session "$session" run --restart --cols 60 --rows 12 --env "ADVERSARIAL_PID_PATH=$pid_path" "$fixture" hang >"$log" 2>&1 || status=$?
      [[ $status -ne 0 ]] || "$tool_dir/tui-test" --session "$session" expect text "adversarial ready" --timeout 5000 >>"$log" 2>&1 || status=$?
      [[ $status -ne 0 ]] || "$tool_dir/tui-test" --session "$session" signal INT >>"$log" 2>&1 || status=$?
      [[ $status -ne 0 ]] || "$tool_dir/tui-test" --session "$session" expect text "cancelled by signal" --timeout 5000 >>"$log" 2>&1 || status=$?
      [[ $status -ne 0 ]] || "$tool_dir/tui-test" --session "$session" wait exit --timeout 5000 >>"$log" 2>&1 || status=$?
      "$tool_dir/tui-test" --session "$session" close >>"$log" 2>&1 || true
      ;;
    tui-test:flood)
      session=adversarial-flood
      "$tool_dir/tui-test" --session "$session" run --restart --cols 60 --rows 12 --env "ADVERSARIAL_PID_PATH=$pid_path" "$fixture" flood >"$log" 2>&1 || status=$?
      [[ $status -ne 0 ]] || "$tool_dir/tui-test" --session "$session" expect text "flood complete" --timeout 10000 >>"$log" 2>&1 || status=$?
      [[ $status -ne 0 ]] || "$tool_dir/tui-test" --session "$session" wait exit --timeout 5000 >>"$log" 2>&1 || status=$?
      "$tool_dir/tui-test" --session "$session" close >>"$log" 2>&1 || true
      ;;
    termlens:*)
      rust_test="adversarial_$case_name"
      [[ "$case_name" == flood ]] && rust_test=adversarial_finite_flood
      CARGO_TARGET_DIR="$artifact_root/cargo-target" cargo +1.85.0 test --offline --locked \
        --manifest-path "$root/benchmarks/competitive/c1/termlens/Cargo.toml" \
        --test c1 -- "$rust_test" --exact --nocapture >"$log" 2>&1
      status=$?
      ;;
  esac
  set -e
  ended=$(date +%s%N); elapsed_ms=$(((ended-started)/1000000))
  if ! process_gone "$pid_path"; then survivor=true; outcome=failed; fi
  if [[ $status -eq 99 ]]; then outcome=failed; fi
  if [[ "$expected_class" == success && $status -ne 0 ]]; then outcome=failed; fi
  if [[ "$expected_class" == bounded-failure && $status -eq 0 ]]; then outcome=failed; fi
  printf '{"tool":"%s","case":"%s","capability":"%s","expected":"%s","observed_status":%d,"survivor":%s,"elapsed_ms":%d,"outcome":"%s","log":"%s"}\n' \
    "$tool" "$case_name" "$capability" "$expected_class" "$status" "$survivor" "$elapsed_ms" "$outcome" "${log#$root/}" >>"$ledger"
  [[ "$outcome" == passed ]]
}

record_case playtestr hang bounded-timeout bounded-failure
record_case atago hang bounded-timeout bounded-failure
record_case tui-test hang timeout-then-explicit-kill success
record_case termlens hang bounded-wait-and-drop success
record_case playtestr cancel runner-cancellation success
record_case atago cancel target-signal success
record_case tui-test cancel target-signal success
record_case termlens cancel target-signal success
record_case playtestr flood raw-output-limit bounded-failure
record_case atago flood finite-drain-no-documented-limit success
record_case tui-test flood finite-drain-no-documented-limit success
record_case termlens flood finite-drain-no-documented-limit success
