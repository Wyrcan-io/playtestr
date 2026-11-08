#!/bin/sh
set -eu
chmod 444 board.md
chmod 555 .
trap 'chmod 755 . 2>/dev/null || true' EXIT HUP INT TERM
taskell board.md
