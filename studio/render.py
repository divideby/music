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


def _fluidsynth(mid, wav, sf, gain, sample_rate=44100):
    _run(["fluidsynth", "-ni", "-g", str(gain), "-r", str(sample_rate),
          "-F", str(wav), str(sf), str(mid)])


def render_layered(stems, out_ogg, soundfont=None, synth_gain=0.5,
                   reverb=12, lowpass=18000, bass_gain=2, treble_gain=2,
                   sample_rate=44100, master_fx=None, keep_wav=False):
    """Render several MIDI stems, process each with its own chain, mix, master.

    stems: list of dicts, each with "mid" and optionally:
      "pre"   — callable(in_wav, out_wav) run right after synth (e.g. an external
                amp-sim CLI like waveny; note it may require mono input).
      "board" — a pedalboard.Pedalboard run on the (pre-processed) stem.
      "fx"    — a sox effect-arg list (used when there's no board).
    Each stem is synth'd separately, then conformed to stereo @ sample_rate so
    mono amp-sim output mixes cleanly. The mix is summed as 32-bit float (no
    clipping), then the shared master chain + ogg encode run. Returns Path.

    master_fx: optional sox effect-arg list that REPLACES the default 2-bus
    chain (normalize + tone + lowpass + reverb + normalize). Pass this to add
    real bus glue/limiting (e.g. `compand`) for a denser, louder master; when
    None the default chain runs (so existing tracks are unaffected).
    """
    _require("fluidsynth", "apt-get install fluidsynth")
    _require("sox", "apt-get install sox")
    _require("ffmpeg", "apt-get install ffmpeg")
    sf = _find_soundfont(soundfont)

    out_ogg = Path(out_ogg)
    out_ogg.parent.mkdir(parents=True, exist_ok=True)
    tmp, processed = [], []
    for i, st in enumerate(stems):
        raw = out_ogg.with_suffix(f".s{i}.raw.wav")
        _fluidsynth(st["mid"], raw, sf, synth_gain, sample_rate)
        tmp.append(raw)
        src = raw
        if st.get("pre") is not None:                        # external pre-processor
            pre = out_ogg.with_suffix(f".s{i}.pre.wav")
            st["pre"](str(src), str(pre))
            tmp.append(pre)
            src = pre
        proc = out_ogg.with_suffix(f".s{i}.proc.wav")
        if st.get("board") is not None:                      # pedalboard amp/cab chain
            from .amp import apply_board
            apply_board(st["board"], src, proc)
        else:                                                # sox effect chain
            _run(["sox", str(src), str(proc), *(st.get("fx") or ["gain", "0"])])
        conf = out_ogg.with_suffix(f".s{i}.wav")             # conform for the mix
        _run(["sox", str(proc), "-c", "2", "-r", str(sample_rate), str(conf)])
        tmp += [proc, conf]
        processed.append(conf)

    mix = out_ogg.with_suffix(".mix.wav")
    master = out_ogg.with_suffix(".master.wav")
    tmp += [mix, master]
    # sum as float to avoid inter-stem clipping, then master.
    _run(["sox", "-m", *[str(p) for p in processed], "-b", "32",
          "-e", "floating-point", str(mix)])
    if master_fx is None:
        master_fx = ["gain", "-n", "-3", "bass", str(bass_gain),
                     "treble", str(treble_gain), "lowpass", str(lowpass),
                     "reverb", str(reverb), "gain", "-n", "-1"]
    _run(["sox", str(mix), str(master), *master_fx])
    _run(["ffmpeg", "-y", "-i", str(master), "-q:a", "5", str(out_ogg)])

    if not keep_wav:
        for p in tmp:
            Path(p).unlink(missing_ok=True)
    return out_ogg


def render(mid_path, out_ogg, soundfont=None, synth_gain=0.6,
           reverb=35, lowpass=14000, bass_gain=3, treble_gain=-2, keep_wav=False):
    """mid_path -> out_ogg. Returns Path(out_ogg).

    Mastering chain (sox): peak-normalize, tone shaping, low-pass, a touch of
    reverb, then ffmpeg encodes to Ogg Vorbis. Defaults lean warm/lofi; pass
    e.g. reverb=12, lowpass=16000, treble_gain=2 for a brighter, drier rock mix.
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
    sox_fx = ["gain", "-n", "-1.5", "bass", str(bass_gain), "treble", str(treble_gain),
              "lowpass", str(lowpass), "reverb", str(reverb), "gain", "-n", "-1"]
    _run(["sox", str(raw), str(master), *sox_fx])

    # 3) encode to ogg (q5 ~ 160kbps VBR)
    _run(["ffmpeg", "-y", "-i", str(master), "-q:a", "5", str(out_ogg)])

    if not keep_wav:
        raw.unlink(missing_ok=True)
        master.unlink(missing_ok=True)
    return out_ogg
