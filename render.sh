#!/usr/bin/env bash
# Render one track: ./render.sh <track-name>  (e.g. ./render.sh lofi_intro)
set -euo pipefail
cd "$(dirname "$0")"
name="${1:?usage: ./render.sh <track-name>}"
script="tracks/${name}/track.py"
[ -f "$script" ] || { echo "no such track: $script" >&2; exit 1; }
python3 "$script"
