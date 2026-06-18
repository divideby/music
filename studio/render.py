"""Render a MIDI file to audio: fluidsynth -> sox mastering -> ffmpeg encode.

Side-effecting layer (the only module that shells out). Keeps the pure parts of
the studio testable. Fails loudly with an actionable message if a binary or the
soundfont is missing.
"""

import shutil
import subprocess
from pathlib import Path

# Project copy first (fetch-soundfont.sh symlinks it here), then the system one.
SOUNDFONT_CANDIDATES = [
    Path(__file__).resolve().parent.parent / "soundfonts" / "FluidR3_GM.sf2",
    Path("/usr/share/sounds/sf2/FluidR3_GM.sf2"),
]


def _require(binary, hint):
    if shutil.which(binary) is None:
        raise RuntimeError(f"missing '{binary}' — {hint}")


def _find_soundfont(explicit=None):
    cands = [Path(explicit)] if explicit else SOUNDFONT_CANDIDATES
    for c in cands:
        if c.exists():
            return c
    raise RuntimeError(
        "soundfont not found (FluidR3_GM.sf2). Run ./fetch-soundfont.sh or "
        "apt-get install fluid-soundfont-gm."
    )


def _run(cmd):
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL,
                   stderr=subprocess.DEVNULL)


def render(mid_path, out_ogg, soundfont=None, synth_gain=0.6,
           reverb=35, lowpass=14000, keep_wav=False):
    """mid_path -> out_ogg. Returns Path(out_ogg).

    Mastering chain (sox): peak-normalize, gentle low-pass + tone shaping for a
    warm/lofi feel, a touch of reverb. Then ffmpeg encodes to Ogg Vorbis.
    """
    _require("fluidsynth", "apt-get install fluidsynth")
    _require("sox", "apt-get install sox")
    _require("ffmpeg", "apt-get install ffmpeg")
    sf = _find_soundfont(soundfont)

    mid_path = Path(mid_path)
    out_ogg = Path(out_ogg)
    out_ogg.parent.mkdir(parents=True, exist_ok=True)
    raw = out_ogg.with_suffix(".raw.wav")
    master = out_ogg.with_suffix(".master.wav")

    # 1) synth: MIDI + soundfont -> raw stereo wav
    _run(["fluidsynth", "-ni", "-g", str(synth_gain), "-r", "44100",
          "-F", str(raw), str(sf), str(mid_path)])

    # 2) master: normalize, warm tone, light reverb
    sox_fx = ["gain", "-n", "-1.5", "bass", "+3", "treble", "-2",
              "lowpass", str(lowpass), "reverb", str(reverb), "gain", "-n", "-1"]
    _run(["sox", str(raw), str(master), *sox_fx])

    # 3) encode to ogg (q5 ~ 160kbps VBR)
    _run(["ffmpeg", "-y", "-i", str(master), "-q:a", "5", str(out_ogg)])

    if not keep_wav:
        raw.unlink(missing_ok=True)
        master.unlink(missing_ok=True)
    return out_ogg
