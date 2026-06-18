#!/usr/bin/env bash
# Fetch the NAM amp model used by tracks/modern_rock_nam (community capture).
# Also needs the `waveny` CLI on PATH — build from github.com/nlpodyssey/waveny:
#   apt-get install golang-go portaudio19-dev
#   git clone https://github.com/nlpodyssey/waveny && cd waveny
#   go build -o /usr/local/bin/waveny ./cmd/waveny
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p nam_models
url="https://raw.githubusercontent.com/pelennor2170/NAM_models/main/Helga%20B%205150%20BlockLetter%20-%20Boosted.nam"
curl -sL -o nam_models/5150_boosted.nam "$url"
echo "fetched nam_models/5150_boosted.nam ($(du -h nam_models/5150_boosted.nam | cut -f1))"
