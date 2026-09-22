#!/usr/bin/env bash
set -euo pipefail

root=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
artifact_root="$root/artifacts/competitive"
bin_dir="$artifact_root/bin"
log_dir="$artifact_root/logs"
oracle_dir="$artifact_root/oracles"
ledger="$artifact_root/c1-attempts.jsonl"
control_ledger="$artifact_root/c1-controls.jsonl"
runner="$root/scripts/competitive/run-c1-tool.sh"
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
  local tool=$1 phase=$2 binary=$3 expected_status=$4 expected_oracle=$5
  local identity="control-${phase}-${tool}"
  local result="$oracle_dir/$identity.txt"
  local log="$log_dir/$identity.log"
  cp "$binary" "$bin_dir/selector"
  set +e
  bash "$runner" "$tool" "$identity" "$result" >"$log" 2>&1
  local status=$?
  set -e
  local oracle="missing"
  [[ -f "$result" ]] && oracle=$(tr -d '\r\n' <"$result")
  local outcome=passed
  if [[ "$status" -ne "$expected_status" || "$oracle" != "$expected_oracle" ]]; then
    outcome=failed
  fi
  printf '{"tool":"%s","phase":"%s","expected_status":%d,"observed_status":%d,"expected_oracle":"%s","observed_oracle":"%s","outcome":"%s","log":"%s"}\n' \
    "$tool" "$phase" "$expected_status" "$status" "$expected_oracle" "$oracle" "$outcome" "${log#$root/}" >>"$control_ledger"
  [[ "$outcome" == passed ]]
}

for tool in "${tools[@]}"; do
  run_control "$tool" good "$bin_dir/selector-good" 0 Beta
  run_control "$tool" known-bad "$bin_dir/selector-bad" 1 Alpha
  run_control "$tool" recovery "$bin_dir/selector-good" 0 Beta
done

cp "$bin_dir/selector-good" "$bin_dir/selector"
campaign_failed=0
for round in $(seq 1 30); do
  read -r -a round_tools <<<"${orders[$(((round-1)%${#orders[@]}))]}"
  position=0
  for tool in "${round_tools[@]}"; do
    position=$((position+1))
    identity=$(printf 'repeat-%02d-%d-%s' "$round" "$position" "$tool")
    result="$oracle_dir/$identity.txt"
    log="$log_dir/$identity.log"
    time_log="$log_dir/$identity.time"
    started=$(date +%s%N)
    set +e
    /usr/bin/time -v -o "$time_log" bash "$runner" "$tool" "$identity" "$result" >"$log" 2>&1
    status=$?
    set -e
    ended=$(date +%s%N)
    elapsed_ms=$(((ended-started)/1000000))
    max_rss_kb=$(awk -F: '/Maximum resident set size/{gsub(/^[[:space:]]+/, "", $2); print $2}' "$time_log")
    oracle=missing
    [[ -f "$result" ]] && oracle=$(tr -d '\r\n' <"$result")
    evidence_bytes=$(wc -c <"$log")
    outcome=passed
    if [[ $status -ne 0 || "$oracle" != Beta ]]; then
      outcome=failed
      campaign_failed=1
    fi
    printf '{"task":"C1","round":%d,"position":%d,"tool":"%s","exit_status":%d,"oracle":"%s","elapsed_ms":%d,"max_rss_kb":%s,"log_bytes":%d,"outcome":"%s","log":"%s"}\n' \
      "$round" "$position" "$tool" "$status" "$oracle" "$elapsed_ms" "${max_rss_kb:-null}" "$evidence_bytes" "$outcome" "${log#$root/}" >>"$ledger"
  done
done

exit "$campaign_failed"
