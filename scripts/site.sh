#!/bin/sh
set -eu

command_name=${1:-build}
repo_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)

case "$(hugo version)" in
  *"hugo v0.164.0"*) ;;
  *) echo "Website requires Hugo v0.164.0." >&2; exit 1 ;;
esac

if [ "$command_name" = "serve" ]; then
  exec hugo server --source "$repo_root" --config site/hugo.toml --buildDrafts --disableFastRender
fi
if [ "$command_name" != "build" ]; then
  echo "Usage: sh scripts/site.sh [build|serve]" >&2
  exit 2
fi

hugo --source "$repo_root" --config site/hugo.toml --cleanDestinationDir --minify
mkdir -p "$repo_root/public/schema"
cp "$repo_root/schema/playtestr-spec-v1.schema.json" "$repo_root/public/schema/"
cp "$repo_root/schema/playtestr-report-v1.schema.json" "$repo_root/public/schema/"
node "$repo_root/scripts/check-site.mjs" "$repo_root/public"
