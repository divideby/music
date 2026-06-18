#!/usr/bin/env bash
# Commit rendered tracks + the player and push (GitHub Pages rebuilds on push).
# Usage: ./publish.sh ["commit message"]
set -euo pipefail
cd "$(dirname "$0")"
msg="${1:-publish: update tracks}"
git add -A
if git diff --cached --quiet; then
  echo "nothing to publish"; exit 0
fi
git commit -m "$msg"
git push
echo "pushed — Pages will rebuild at the repo's Pages URL"
