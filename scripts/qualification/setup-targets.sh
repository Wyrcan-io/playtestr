#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
setup_started_utc="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
setup_started_epoch="$(date +%s)"
tools="$root/.trial-private/corpus-tools"
external="$root/.tools/external"
sources="$root/.trial-private/qualification-sources"
mkdir -p "$tools" "$external" "$sources" "$tools/bottom-original" "$tools/lazygit-target"

suffix=""
if [[ "${RUNNER_OS:-}" == "Windows" ]] || [[ "$(go env GOOS)" == "windows" ]]; then
  suffix=".exe"
fi

fetch_commit() {
  local name="$1" url="$2" commit="$3"
  local destination="$sources/$name"
  rm -rf -- "$destination"
  git init -q "$destination"
  git -C "$destination" remote add origin "$url"
  git -C "$destination" fetch -q --depth 1 origin "$commit"
  git -C "$destination" checkout -q --detach FETCH_HEAD
  test "$(git -C "$destination" rev-parse HEAD)" = "$commit"
}

GOBIN="$external" go install github.com/charmbracelet/gum@v0.17.0

fetch_commit lazygit https://github.com/jesseduffield/lazygit.git c07f4d381b90419583b7ce04f87379654d983ebc
(cd "$sources/lazygit" && go build -trimpath -o "$tools/lazygit-target/lazygit$suffix" .)

fetch_commit micro https://github.com/zyedidia/micro.git 04c577049ca898f097cd6a2dae69af0b4d4493e1
(cd "$sources/micro" && go build -trimpath -o "$tools/micro.exe" ./cmd/micro)

fetch_commit bottom https://github.com/ClementTsang/bottom.git e22236a928eeb876b2ccaad2f3d1ce5f6450281a
(cd "$sources/bottom" && cargo build --release --locked)
cp "$sources/bottom/target/release/btm$suffix" "$tools/bottom-original/btm$suffix"

for oracle in lazygit micro create-vite; do
  (cd "$root/corpus/controls/$oracle-oracle" && go build -trimpath -o "$tools/$oracle-oracle$suffix" .)
done

runtime="$tools/create-vite-runtime"
rm -rf -- "$runtime"
mkdir -p "$runtime"
(cd "$runtime" && npm pack --silent create-vite@9.2.1 > tarball-name.txt)
tarball="$(tr -d '\r\n' < "$runtime/tarball-name.txt")"
echo "4dd92d0e734e96e88ec8afd8c0153f6a9446156205460a995b978b63b49b4eb8  $runtime/$tarball" | sha256sum --check
(cd "$runtime" && npm install --ignore-scripts --no-audit --no-fund "./$tarball")

{
  echo "setup_started_utc=$setup_started_utc"
  echo "setup_elapsed_seconds=$(($(date +%s) - setup_started_epoch))"
  echo "go=$(go version)"
  echo "rust=$(rustc --version)"
  echo "cargo=$(cargo --version)"
  echo "node=$(node --version)"
  echo "npm=$(npm --version)"
  echo "gum=$(sha256sum "$external/gum$suffix" | awk '{print $1}')"
  echo "lazygit=$(sha256sum "$tools/lazygit-target/lazygit$suffix" | awk '{print $1}')"
  echo "bottom=$(sha256sum "$tools/bottom-original/btm$suffix" | awk '{print $1}')"
  echo "micro=$(sha256sum "$tools/micro.exe" | awk '{print $1}')"
  echo "create_vite_tarball=$(sha256sum "$runtime/$tarball" | awk '{print $1}')"
} > "$tools/qualification-targets.txt"
