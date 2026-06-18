#!/usr/bin/env bash
# Commit rendered tracks + the player, push to git, and deploy to Vercel.
# (GitHub Pages is hijacked by the account's custom domain — see README.)
# Usage: ./publish.sh ["commit message"]
set -euo pipefail
cd "$(dirname "$0")"
msg="${1:-publish: update tracks}"
git add -A
if git diff --cached --quiet; then
  echo "nothing new to commit"
else
  git commit -m "$msg"
  git push
fi
echo "deploying to Vercel..."
vercel deploy --prod --yes
echo "live: https://music-psi-lovat.vercel.app"
