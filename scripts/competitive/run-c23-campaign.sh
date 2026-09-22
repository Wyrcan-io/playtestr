#!/usr/bin/env bash
set -euo pipefail

root=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
artifact_root="$root/artifacts/competitive"
bin_dir="$artifact_root/bin"
log_dir="$artifact_root/logs"
oracle_dir="$artifact_root/oracles"
ledger="$artifact_root/c23-attempts.jsonl"
control_ledger="$artifact_root/c23-controls.jsonl"
runner="$root/scripts/competitive/run-c23-tool.sh"
tools=(playtestr atago tui-test termlens)
orders=(
  "playtestr atago tui-test termlens"
  "termlens tui-test atago playtestr"
  "atago playtestr termlens tui-test"
  "tui-test termlens playtestr atago"
  "playtestr termlens atago tui-test"
  "tui-test atago termlens playtestr"
)
mkdir -p "$log_dir" "$oracle_dir"
: >"$ledger"
: >"$control_ledger"

run_control() {
  local task=$1 tool=$2 phase=$3 binary=$4 expected_status_class=$5 expected_oracle=$6
  local canonical result identity log status oracle outcome
  identity="control-${task,,}-${phase}-${tool}"
  result="$oracle_dir/$identity.txt"
  log="$log_dir/$identity.log"
  [[ "$task" == C2 ]] && canonical="$bin_dir/stateful" || canonical="$bin_dir/resize"
  cp "$binary" "$canonical"
  set +e
  bash "$runner" "$task" "$tool" "$identity" "$result" >"$log" 2>&1
  status=$?
  set -e
  oracle=not-applicable
  [[ -f "$result" && "$task" == C2 ]] && oracle=$(tr -d '\r\n' <"$result")
  outcome=passed
  [[ "$expected_status_class" == zero && $status -ne 0 ]] && outcome=failed
  [[ "$expected_status_class" == nonzero && $status -eq 0 ]] && outcome=failed
  [[ "$oracle" != "$expected_oracle" ]] && outcome=failed
  printf '{"task":"%s","tool":"%s","phase":"%s","expected_status_class":"%s","observed_status":%d,"expected_oracle":"%s","observed_oracle":"%s","outcome":"%s","log":"%s"}\n' \
    "$task" "$tool" "$phase" "$expected_status_class" "$status" "$expected_oracle" "$oracle" "$outcome" "${log#$root/}" >>"$control_ledger"
  [[ "$outcome" == passed ]]
}

for task in C2 C3; do
  if [[ "$task" == C2 ]]; then
    good="$bin_dir/stateful-good"; bad="$bin_dir/stateful-bad"; expected_good='port=4242'; expected_bad='port=8080'
  else
    good="$bin_dir/resize-good"; bad="$bin_dir/resize-bad"; expected_good=not-applicable; expected_bad=not-applicable
  fi
  for tool in "${tools[@]}"; do
    run_control "$task" "$tool" good "$good" zero "$expected_good"
    run_control "$task" "$tool" known-bad "$bad" nonzero "$expected_bad"
    run_control "$task" "$tool" recovery "$good" zero "$expected_good"
  done
  [[ "$task" == C2 ]] && cp "$good" "$bin_dir/stateful" || cp "$good" "$bin_dir/resize"
done

campaign_failed=0
for task in C2 C3; do
  for round in $(seq 1 30); do
    read -r -a round_tools <<<"${orders[$(((round-1)%${#orders[@]}))]}"
    position=0
    for tool in "${round_tools[@]}"; do
      position=$((position+1))
      identity=$(printf '%s-repeat-%02d-%d-%s' "${task,,}" "$round" "$position" "$tool")
      result="$oracle_dir/$identity.txt"
      log="$log_dir/$identity.log"
      time_log="$log_dir/$identity.time"
      started=$(date +%s%N)
      set +e
      /usr/bin/time -v -o "$time_log" bash "$runner" "$task" "$tool" "$identity" "$result" >"$log" 2>&1
      status=$?
      set -e
      ended=$(date +%s%N)
      elapsed_ms=$(((ended-started)/1000000))
      max_rss_kb=$(awk -F: '/Maximum resident set size/{gsub(/^[[:space:]]+/, "", $2); print $2}' "$time_log")
      oracle=not-applicable
      [[ -f "$result" && "$task" == C2 ]] && oracle=$(tr -d '\r\n' <"$result")
      evidence_bytes=$(wc -c <"$log")
      outcome=passed
      expected_oracle=not-applicable
      [[ "$task" == C2 ]] && expected_oracle='port=4242'
      if [[ $status -ne 0 || "$oracle" != "$expected_oracle" ]]; then outcome=failed; campaign_failed=1; fi
      printf '{"task":"%s","round":%d,"position":%d,"tool":"%s","exit_status":%d,"oracle":"%s","elapsed_ms":%d,"max_rss_kb":%s,"log_bytes":%d,"outcome":"%s","log":"%s"}\n' \
        "$task" "$round" "$position" "$tool" "$status" "$oracle" "$elapsed_ms" "${max_rss_kb:-null}" "$evidence_bytes" "$outcome" "${log#$root/}" >>"$ledger"
    done
  done
done
exit "$campaign_failed"
