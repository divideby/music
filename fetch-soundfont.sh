#!/usr/bin/env bash
# Make soundfonts/FluidR3_GM.sf2 available (symlink the system copy, else install).
set -euo pipefail
cd "$(dirname "$0")"
dest="soundfonts/FluidR3_GM.sf2"
sys="/usr/share/sounds/sf2/FluidR3_GM.sf2"
mkdir -p soundfonts
if [ -e "$dest" ]; then echo "soundfont already present: $dest"; exit 0; fi
if [ ! -f "$sys" ]; then
  echo "installing fluid-soundfont-gm (needs apt/root)..."
  DEBIAN_FRONTEND=noninteractive apt-get install -y fluid-soundfont-gm
fi
ln -sf "$sys" "$dest"
echo "linked $dest -> $sys"
