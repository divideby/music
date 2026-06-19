"""Procedural ambience: seeded noise synthesised into a rain bed.

Determinism (project rule: same code -> same audio): sox's own `synth
whitenoise` is NOT reproducible between runs, so every random source here comes
from a SEEDED PRNG (numpy's default_rng, or stdlib random for the pure helper);
sox is used only to COLOUR/mix the result, which is deterministic.

Why granular, not just filtered noise: steady band-limited noise sounds like
hiss/static, not rain. Rain is thousands of individual droplet impacts —
short noise grains with an instant attack and fast decay, at random times. We
synthesise that explicitly: a few loud sharp "taps" + dense soft patter + a
quiet dark "rush" underneath. That transient texture is what the ear hears as
rain.

Split mirrors the studio: `white_samples` is pure and unit-tested; the numpy
grain synthesis is deterministic (also tested) and the WAV writer + sox shaping
shell out.
"""

import subprocess
import wave
from pathlib import Path

import numpy as np

RATE = 44100


# ── pure (stdlib) ────────────────────────────────────────────────────────────
def white_samples(n, seed=0):
    """n deterministic white-noise samples in [-1.0, 1.0] for a given seed.

    The simple reproducible-source primitive; see module docstring.
    """
    import random
    rng = random.Random(seed)
    return [rng.uniform(-1.0, 1.0) for _ in range(n)]


# ── deterministic numpy grain synthesis ─────────────────────────────────────
def droplet_field(n, rate, density, seed, decay_ms=12.0):
    """A mono buffer of `density` drops/sec: enveloped white-noise grains
    (instant attack, exponential decay) placed at seeded-random times.

    Deterministic for a given (n, rate, density, seed, decay_ms).
    """
    rng = np.random.default_rng(seed)
    buf = np.zeros(n, dtype=np.float64)
    noise = rng.standard_normal(n)
    n_drops = int(density * n / rate)
    if n_drops <= 0:
        return buf.astype(np.float32)
    pos = rng.integers(0, n, n_drops)
    amp = rng.random(n_drops) ** 2            # skew: mostly soft drops, few loud
    L = max(2, int(rate * decay_ms / 1000.0))
    env = np.exp(-np.linspace(0.0, 7.0, L))   # sharp attack at 1.0, fast decay
    off = np.arange(L)
    for s in range(0, n_drops, 40000):        # batch to bound memory
        p = pos[s:s + 40000]
        a = amp[s:s + 40000]
        idx = np.clip(p[:, None] + off[None, :], 0, n - 1)
        contrib = (a[:, None] * env[None, :] * noise[idx]).ravel()
        buf += np.bincount(idx.ravel(), weights=contrib, minlength=n)[:n]
    return buf.astype(np.float32)


# ── side-effecting (write + sox) ─────────────────────────────────────────────
def _write_wav(path, channels, rate=RATE):
    """Write float numpy channels (list of equal-length arrays) as 16-bit PCM,
    peak-normalised so nothing clips."""
    a = np.stack(channels, axis=1)            # (n, nch), interleaved by row
    peak = float(np.max(np.abs(a))) or 1.0
    pcm = (a / peak * 0.97 * 32767.0).astype("<i2")
    with wave.open(str(path), "wb") as w:
        w.setnchannels(len(channels))
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(pcm.tobytes())
    return path


def _sox(args):
    subprocess.run(["sox", *args], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def rain(out_wav, seconds, seed=1, rate=RATE):
    """Render a stereo rain bed and return its path.

    Three layers, each its own seeded droplet field, L/R decorrelated for width:
      * sharp  — sparse, loud, short-decay drops: the audible "tap … tap".
      * patter — dense, soft, mid-decay drops: the busy continuous texture.
      * rush   — very dense, quiet, dark, long-decay grains: the background sheet.
    sox then darkens each (rain is not bright), adds a little space, and mixes.
    """
    out_wav = Path(out_wav)
    n = int(seconds * rate)

    def field(density, decay, base_seed):
        return [droplet_field(n, rate, density, base_seed, decay),
                droplet_field(n, rate, density, base_seed + 101, decay)]

    raw = {
        "sharp":  (out_wav.with_suffix(".sharp.wav"),  field(220, 7.0, seed),
                   ["highpass", "300", "lowpass", "7500", "gain", "-n", "-4"]),
        "patter": (out_wav.with_suffix(".patter.wav"), field(2800, 15.0, seed + 11),
                   ["highpass", "250", "lowpass", "5500", "gain", "-n", "-7"]),
        "rush":   (out_wav.with_suffix(".rush.wav"),   field(9000, 26.0, seed + 23),
                   ["highpass", "150", "lowpass", "2600", "tremolo", "0.2", "30",
                    "gain", "-n", "-15"]),
    }
    shaped = []
    tmp = []
    for name, (path, chans, fx) in raw.items():
        _write_wav(path, chans, rate)
        out = out_wav.with_suffix(f".{name}.s.wav")
        _sox([str(path), str(out), *fx])
        shaped.append(str(out))
        tmp += [path, out]
    # mix, gentle space (short room so drops read as drops, not a cathedral)
    _sox(["-m", *shaped, str(out_wav), "gain", "-n", "-3",
          "reverb", "16", "12", "45", "100", "0", "gain", "-n", "-3"])
    for p in tmp:
        Path(p).unlink(missing_ok=True)
    return out_wav
