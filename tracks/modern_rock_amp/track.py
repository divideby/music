#!/usr/bin/env python3
"""modern_rock_amp — the same song as modern_rock, but with a real amp/cab chain.

Run from the repo root:  ./render.sh modern_rock_amp

A/B experiment vs modern_rock. Instead of playing GM's pre-distorted "distortion
guitar" sample and EQ-ing it, this renders a CLEAN GM guitar as a DI signal and
runs it through studio/amp.py (pedalboard): cascading distortion -> tone EQ ->
cabinet impulse-response convolution -> compression. The cab IR is the part that
de-"midis" the tone. Composition is reused verbatim from tracks/modern_rock.
"""

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from studio import render_layered                  # noqa: E402
from studio.amp import guitar_board, lead_board     # noqa: E402

# Reuse the composition from the sibling track.
_spec = importlib.util.spec_from_file_location(
    "modern_rock_track", ROOT / "tracks" / "modern_rock" / "track.py")
mr = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mr)


def main():
    out = ROOT / "out" / "modern_rock_amp"
    # Clean guitar = the DI; the amp board supplies all the gain + cabinet.
    guitar, leadsong, band = mr.build(
        rhythm_voices=("clean_guitar", "clean_guitar"), lead_voice="clean_guitar")
    g_mid = guitar.save(out.with_suffix(".gtr.mid"))
    l_mid = leadsong.save(out.with_suffix(".lead.mid"))
    b_mid = band.save(out.with_suffix(".band.mid"))
    ogg = render_layered(
        [
            {"mid": g_mid, "board": guitar_board(ir="cab_modern.wav", drive=26.0, cascade=10.0)},
            {"mid": l_mid, "board": lead_board(ir="cab_vintage_bright.wav", drive=18.0)},
            {"mid": b_mid, "fx": mr.BAND_FX},
        ],
        out.with_suffix(".ogg"),
        synth_gain=0.7, reverb=12, lowpass=20000, bass_gain=2, treble_gain=1,
    )
    for m in (g_mid, l_mid, b_mid):
        Path(m).unlink(missing_ok=True)
    print(f"rendered {ogg}")


if __name__ == "__main__":
    main()
