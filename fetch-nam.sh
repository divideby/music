#!/usr/bin/env bash
# Fetch the NAM amp model used by tracks/modern_rock_nam (community capture).
# Also needs the `waveny` CLI on PATH — build from github.com/nlpodyssey/waveny:
#   apt-get install golang-go portaudio19-dev
#   git clone https://github.com/nlpodyssey/waveny && cd waveny
#   go build -o /usr/local/bin/waveny ./cmd/waveny
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p nam_models
base="https://raw.githubusercontent.com/pelennor2170/NAM_models/main"
# name -> source file in the NAM_models repo (high-gain captures)
fetch() { curl -sL -o "nam_models/$1" "$base/$2"; echo "fetched nam_models/$1 ($(du -h nam_models/$1 | cut -f1))"; }
fetch "ubermetal.nam"    "Jason%20Z%20Line%206%20UBERMETAL%20INSANE%20droom%20metal%20at%20its%20best.nam"
fetch "5150_boosted.nam" "Helga%20B%205150%20BlockLetter%20-%20Boosted.nam"
