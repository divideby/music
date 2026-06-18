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


def amp(in_wav, out_wav, model, norm_db=-6.0, sample_rate=48000):
    """Process in_wav through the NAM `model`, writing out_wav. norm_db is the
    DI peak fed into the amp (hotter = more saturation)."""
    base = str(out_wav)
    raw16, nam_in = base + ".raw16", base + ".namin.wav"
    subprocess.run(["sox", str(in_wav), "-c", "1", "-r", str(sample_rate),
                    "-b", "16", "-e", "signed-integer", "-t", "raw", raw16,
                    "gain", "-n", str(norm_db)],
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
                    "-output", str(out_wav), "-model", str(model)],
                   check=True, stdout=_DEVNULL, stderr=_DEVNULL)
    Path(raw16).unlink(missing_ok=True)
    Path(nam_in).unlink(missing_ok=True)
    return out_wav
