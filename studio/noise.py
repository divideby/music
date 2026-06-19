"""Procedural ambience: seeded noise shaped into rain / wind / water beds.

Determinism (project rule: same code -> same audio): sox's own `synth
whitenoise` is NOT reproducible between runs, so the noise SOURCE is generated
here with a seeded Python PRNG and written to a WAV; sox is used only to COLOUR
it (filters, tremolo, mix) — which is deterministic. Same seed -> same bed.

Split mirrors the rest of the studio: `white_samples` is pure and unit-tested;
the WAV writer and the sox shaping shell out and live alongside it.
"""

import array
import random
import subprocess
import wave
from pathlib import Path

RATE = 44100


# ── pure ────────────────────────────────────────────────────────────────────
def white_samples(n, seed=0):
    """n deterministic white-noise samples in [-1.0, 1.0] for a given seed."""
    rng = random.Random(seed)
    return [rng.uniform(-1.0, 1.0) for _ in range(n)]


# ── side-effecting (write + sox) ─────────────────────────────────────────────
def _write_wav(path, channels, rate=RATE):
    """Write float channels (list of equal-length lists) as 16-bit PCM WAV."""
    n, nch = len(channels[0]), len(channels)
    interleaved = array.array("h", bytes(2 * n * nch))
    for c, ch in enumerate(channels):
        for i, x in enumerate(ch):
            v = -1.0 if x < -1.0 else 1.0 if x > 1.0 else x
            interleaved[i * nch + c] = int(v * 32767)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(nch)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(interleaved.tobytes())
    return path


def _sox(args):
    subprocess.run(["sox", *args], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def _stereo_base(seconds, seed, rate=RATE):
    """A stereo white-noise base with decorrelated L/R (immersive, not mono)."""
    n = int(seconds * rate)
    left = white_samples(n, seed)
    right = white_samples(n, seed + 9973)        # different seed = stereo width
    return left, right


def rain(out_wav, seconds, seed=1, rate=RATE):
    """Render a rain bed: HF sizzle + mid body (gently pulsing) + low rumble.

    Three frequency bands of the same seeded base, summed — broadband hiss
    weighted toward the highs, with a slow tremolo for 'patter' irregularity.
    """
    out_wav = Path(out_wav)
    base = out_wav.with_suffix(".base.wav")
    sizzle = out_wav.with_suffix(".sz.wav")
    body = out_wav.with_suffix(".bd.wav")
    low = out_wav.with_suffix(".lo.wav")
    _write_wav(base, list(_stereo_base(seconds, seed, rate)), rate)
    _sox([str(base), str(sizzle), "highpass", "2200", "lowpass", "9000", "vol", "0.8"])
    _sox([str(base), str(body), "highpass", "700", "lowpass", "6500",
          "tremolo", "0.3", "12", "vol", "1.0"])
    _sox([str(base), str(low), "lowpass", "450", "vol", "0.5"])
    _sox(["-m", str(sizzle), str(body), str(low), str(out_wav), "gain", "-n", "-3"])
    for p in (base, sizzle, body, low):
        p.unlink(missing_ok=True)
    return out_wav
