"""Run a clean DI through a Neural Amp Modeler (.nam) model via the waveny CLI.

waveny is picky about its input WAV: mono, 24-bit, and WAVE format tag 1 (plain
PCM, not the "extensible" tag that sox/ffmpeg emit for 24-bit). So we sox the DI
to mono 16-bit raw, widen to 24-bit PCM by byte-interleaving (v<<8 in 24-bit LE
is just [0x00, lo, hi] of the 16-bit sample — done with fast C-level slice
assignment, no numpy), write it with Python's `wave` (which uses tag 1), then run
waveny. The model supplies the amp distortion; pair its output with a cabinet IR.
"""

import subprocess
import wave
from pathlib import Path

_DEVNULL = subprocess.DEVNULL


# A Tube-Screamer-style boost in FRONT of the amp: high-pass to tighten the lows
# so palm mutes stay defined, a soft-clip overdrive that adds its own harmonics,
# and a mid hump that pushes the amp's gain band. Driving the amp's *level* hotter
# barely adds grit (the model compresses), but a real boost does — its harmonics
# get fed in and re-saturated. This is the authentic "TS into a 5150" trick.
TS_BOOST = ["highpass", "170", "overdrive", "12", "30", "equalizer", "760", "1.3q", "5"]


def amp(in_wav, out_wav, model, norm_db=-6.0, out_norm_db=-1.0, boost=None,
        sample_rate=48000):
    """Process in_wav through the NAM `model`, writing out_wav.

    norm_db: DI peak fed into the amp (hotter = more saturation).
    out_norm_db: peak-normalize the amp output to this level. NAM models bake a
    tiny head_scale (e.g. 0.02), so raw output is ~-27 dB and would be buried in
    a mix — normalizing makes the (already distorted) guitar sit up front.
    boost: sox effect args applied to the DI BEFORE the amp (a pre-amp boost,
    e.g. TS_BOOST). Adds drive that level alone can't. Normalize runs after it.
    """
    base = str(out_wav)
    raw16, nam_in, nam_raw = base + ".raw16", base + ".namin.wav", base + ".namraw.wav"
    pre_fx = list(boost or []) + ["gain", "-n", str(norm_db)]
    subprocess.run(["sox", str(in_wav), "-c", "1", "-r", str(sample_rate),
                    "-b", "16", "-e", "signed-integer", "-t", "raw", raw16,
                    *pre_fx],
                   check=True, stdout=_DEVNULL, stderr=_DEVNULL)

    raw = open(raw16, "rb").read()                 # 16-bit LE: lo,hi,lo,hi,...
    n = len(raw) // 2
    buf = bytearray(n * 3)                          # 24-bit LE: 0,lo,hi,0,lo,hi,...
    buf[1::3] = raw[0::2]
    buf[2::3] = raw[1::2]
    w = wave.open(nam_in, "wb")
    w.setnchannels(1)
    w.setsampwidth(3)
    w.setframerate(sample_rate)
    w.writeframes(bytes(buf))
    w.close()

    subprocess.run(["waveny", "process-rt", "-input", nam_in,
                    "-output", nam_raw, "-model", str(model)],
                   check=True, stdout=_DEVNULL, stderr=_DEVNULL)
    # makeup: NAM output is very quiet (head_scale) -> normalize so it sits in the mix
    subprocess.run(["sox", nam_raw, str(out_wav), "gain", "-n", str(out_norm_db)],
                   check=True, stdout=_DEVNULL, stderr=_DEVNULL)
    for p in (raw16, nam_in, nam_raw):
        Path(p).unlink(missing_ok=True)
    return out_wav
