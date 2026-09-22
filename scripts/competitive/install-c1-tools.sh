#!/usr/bin/env bash
set -euo pipefail

root=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
artifact_root="$root/artifacts/competitive"
bin_dir="$artifact_root/bin"
tool_dir="$artifact_root/tools"
download_dir="$artifact_root/downloads"
install_ledger="$artifact_root/install.jsonl"
mkdir -p "$bin_dir" "$tool_dir" "$download_dir"
: >"$install_ledger"

measure_install() {
  local name=$1
  shift
  local started ended status
  started=$(date +%s%N)
  set +e
  "$@"
  status=$?
  set -e
  ended=$(date +%s%N)
  printf '{"tool":"%s","elapsed_ms":%d,"exit_status":%d}\n' \
    "$name" "$(((ended-started)/1000000))" "$status" >>"$install_ledger"
  return "$status"
}

install_playtestr() {
  go build -trimpath -o "$bin_dir/playtestr" ./cmd/playtestr
}

install_atago() {
  local archive="$download_dir/atago_0.23.0_linux_amd64.tar.gz"
  curl --fail --location --silent --show-error \
    --output "$archive" \
    https://github.com/nao1215/atago/releases/download/v0.23.0/atago_0.23.0_linux_amd64.tar.gz
  echo "7e1582bb40ac0b437f3fffb54a4b26b8d1c00ee27654322fcd003c59d85b325d  $archive" | sha256sum --check --status
  tar -xzf "$archive" -C "$download_dir"
  install -m 0755 "$(find "$download_dir" -type f -name atago -print -quit)" "$tool_dir/atago"
}

install_tui_test() {
  local archive="$download_dir/tui-test-x86_64-unknown-linux-gnu.tar.gz"
  curl --fail --location --silent --show-error \
    --output "$archive" \
    https://github.com/microsoft/tui-test/releases/download/0.1.0-beta.5/tui-test-x86_64-unknown-linux-gnu.tar.gz
  echo "4788539cf313fe6d30b321de5bbe7ac8b5830c84b2aa6f6815335686da19dc83  $archive" | sha256sum --check --status
  tar -xzf "$archive" -C "$download_dir"
  install -m 0755 "$(find "$download_dir" -type f -name tui-test -print -quit)" "$tool_dir/tui-test"
}

install_termlens() {
  CARGO_TARGET_DIR="$artifact_root/cargo-target" \
    cargo +1.85.0 test --locked --no-run \
    --manifest-path "$root/benchmarks/competitive/c1/termlens/Cargo.toml"
}

measure_install playtestr install_playtestr
measure_install atago install_atago
measure_install tui-test install_tui_test
measure_install termlens install_termlens

go build -trimpath -o "$bin_dir/selector-good" ./benchmarks/competitive/c1/selector
go build -trimpath -tags=competitive_bad \
  -o "$bin_dir/selector-bad" ./benchmarks/competitive/c1/selector
cp "$bin_dir/selector-good" "$bin_dir/selector"
go build -trimpath -o "$bin_dir/stateful-good" ./benchmarks/competitive/c2/stateful
go build -trimpath -tags=competitive_bad -o "$bin_dir/stateful-bad" ./benchmarks/competitive/c2/stateful
cp "$bin_dir/stateful-good" "$bin_dir/stateful"
go build -trimpath -o "$bin_dir/resize-good" ./benchmarks/competitive/c3/resize
go build -trimpath -tags=competitive_bad -o "$bin_dir/resize-bad" ./benchmarks/competitive/c3/resize
cp "$bin_dir/resize-good" "$bin_dir/resize"

{
  echo "commit=$(git rev-parse HEAD)"
  echo "host=$(uname -srvmo)"
  echo "go=$(go version)"
  echo "rust=$(rustc +1.85.0 --version)"
  "$tool_dir/atago" --version 2>&1 || "$tool_dir/atago" version 2>&1
  "$tool_dir/tui-test" --version 2>&1
  cargo +1.85.0 tree --locked --manifest-path "$root/benchmarks/competitive/c1/termlens/Cargo.toml" -e normal
  sha256sum "$bin_dir/playtestr" "$bin_dir/selector-good" "$bin_dir/selector-bad" \
    "$bin_dir/stateful-good" "$bin_dir/stateful-bad" "$bin_dir/resize-good" \
    "$bin_dir/resize-bad" "$tool_dir/atago" "$tool_dir/tui-test"
} >"$artifact_root/versions.txt"
