#!/usr/bin/env python3
"""modern_rock_nam — the modern_rock song through a real neural amp model (NAM).

Run from the repo root:  ./render.sh modern_rock_nam

The pro chain: a CLEAN GM guitar DI -> waveny (Neural Amp Modeler, a WaveNet
capture of a boosted Peavey 5150) -> our cabinet IR convolution -> compression.
NAM supplies the actual amp distortion/character (modeled from a real amp), so
pedalboard only does the cabinet + tone. Composition reused from modern_rock.

Requires: waveny on PATH (built from github.com/nlpodyssey/waveny) and the model
at nam_models/5150_boosted.nam. NAM models are mono and trained at 48 kHz, so the
whole render runs at 48k and the guitar DI is summed to mono before waveny.
"""

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from studio import render_layered                  # noqa: E402
from studio.amp import cab_board                    # noqa: E402
from studio import nam                              # noqa: E402

MODEL = ROOT / "nam_models" / "ubermetal.nam"

_spec = importlib.util.spec_from_file_location(
    "modern_rock_track", ROOT / "tracks" / "modern_rock" / "track.py")
mr = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mr)


def nam_pre(norm_db, boost=None):
    """Build a pre-processor: stereo DI -> mono 24-bit -> (boost) -> NAM amp."""
    return lambda in_wav, out_wav: nam.amp(
        in_wav, out_wav, MODEL, norm_db=norm_db, boost=boost, sample_rate=48000)


# Rhythm gets the full Tube-Screamer boost into the amp; lead a lighter push.
RHYTHM_BOOST = nam.TS_BOOST
LEAD_BOOST = ["highpass", "200", "overdrive", "7", "30", "equalizer", "900", "1.4q", "3"]


def main():
    if not MODEL.exists():
        sys.exit(f"missing NAM model: {MODEL}")
    out = ROOT / "out" / "modern_rock_nam"
    guitar, leadsong, band = mr.build(
        rhythm_voices=("clean_guitar", "clean_guitar"), lead_voice="clean_guitar")
    g_mid = guitar.save(out.with_suffix(".gtr.mid"))
    l_mid = leadsong.save(out.with_suffix(".lead.mid"))
    b_mid = band.save(out.with_suffix(".band.mid"))
    ogg = render_layered(
        [
            {"mid": g_mid, "pre": nam_pre(-3, RHYTHM_BOOST), "board": cab_board(ir="cab_modern.wav")},
            {"mid": l_mid, "pre": nam_pre(-6, LEAD_BOOST), "board": cab_board(ir="cab_vintage_bright.wav",
                                                                              presence=3.0, rolloff_hz=12000)},
            {"mid": b_mid, "fx": mr.BAND_FX},
        ],
        out.with_suffix(".ogg"),
        synth_gain=0.7, reverb=12, lowpass=20000, bass_gain=2, treble_gain=1,
        sample_rate=48000,
    )
    for m in (g_mid, l_mid, b_mid):
        Path(m).unlink(missing_ok=True)
    print(f"rendered {ogg}")


if __name__ == "__main__":
    main()
