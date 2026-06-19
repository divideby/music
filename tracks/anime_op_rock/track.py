#!/usr/bin/env python3
"""anime_op_rock — a J-pop anime-opening with a REAL distorted guitar.

Run from the repo root:  ./render.sh anime_op_rock

The brief (the one required track): a shounen-anime OP in the YOASOBI/LiSA vein —
174 BPM, E major, the "Royal Road" progression Amaj7-B7-G#m7-C#m7 — but driven by
an actual distorted rhythm guitar instead of a fake GM distortion sample. The
guitar follows the proven tone ladder (docs/guitar-tone.md): a CLEAN GM guitar DI
-> Tube-Screamer-style boost -> waveny (Neural Amp Modeler, a WaveNet capture of a
high-gain amp) -> cabinet IR. Around it: a sawtooth 16th arp (the OP motor), bright
piano stabs, a soaring square-lead "vocal" hook in the chorus, syncopated synth
bass, a synth-string pad that lifts the chorus, glockenspiel sparkle, and a driving
rock kit with a snare build into each chorus.

Three render stems so the cab/distortion never touches the synths:
  * guitar  — clean GM DI -> NAM amp + cab IR (the distortion)
  * lead    — the square-lead vocal hook, its own presence EQ
  * band    — arp, piano, bass, strings, glock, drums

Requires waveny on PATH and nam_models/ubermetal.nam (./fetch-nam.sh). NAM models
are mono @ 48 kHz, so the whole render runs at 48k and the DI is summed to mono.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from studio import Song, render_layered             # noqa: E402
from studio.amp import cab_board                     # noqa: E402
from studio import nam                               # noqa: E402
from studio.notes import chord, note_to_midi         # noqa: E402

MODEL = ROOT / "nam_models" / "ubermetal.nam"
STEPS = 16
TEMPO = 174

# Royal Road in E major: IVmaj7 - V7 - iiim7 - vim7. Four bars, loops underneath.
ROYAL = [("A3", "maj7"), ("B3", "dom7"), ("G#3", "min7"), ("C#4", "min7")]
# Power-chord root for the guitar per bar (kept in a tight low register).
GROOT = ["A2", "B2", "G#2", "C#3"]
# Bass root per bar.
BROOT = ["A1", "B1", "G#1", "C#2"]
# Triad for the string pad.
TRIAD = {"A3": ("A4", "maj"), "B3": ("B4", "maj"), "G#3": ("G#4", "min"), "C#4": ("C#4", "min")}

# 40 bars ~ 55s at 174 BPM. Royal Road loops; sections drive the arrangement.
SECTIONS = (["intro"] * 4 + ["verse"] * 8 + ["pre"] * 4 + ["chorus"] * 8
            + ["verse"] * 4 + ["chorus"] * 8 + ["outro"] * 4)

# Chorus "vocal" hook (square lead), a 4-bar phrase over A-B-G#m-C#m, E major.
# (bar_in_4, step, note, dur)
HOOK = [
    (0, 0, "E5", 2), (0, 2, "F#5", 2), (0, 4, "G#5", 4), (0, 8, "E5", 2), (0, 10, "C#5", 2), (0, 12, "E5", 4),
    (1, 0, "F#5", 2), (1, 2, "G#5", 2), (1, 4, "B5", 4), (1, 8, "F#5", 2), (1, 10, "D#5", 2), (1, 12, "F#5", 4),
    (2, 0, "G#5", 2), (2, 2, "F#5", 2), (2, 4, "D#5", 4), (2, 8, "B4", 2), (2, 10, "D#5", 2), (2, 12, "F#5", 2), (2, 14, "G#5", 2),
    (3, 0, "E5", 2), (3, 2, "D#5", 2), (3, 4, "C#5", 4), (3, 8, "G#4", 2), (3, 10, "B4", 2), (3, 12, "C#5", 4),
]
HOOK_STARTS = [16, 20, 28, 32]                       # the two choruses, hook twice each
ARP_VEL = {"intro": 60, "verse": 56, "pre": 70, "chorus": 78, "outro": 64}


def _blocks(sections):
    out, i = [], 0
    while i < len(sections):
        j = i
        while j < len(sections) and sections[j] == sections[i]:
            j += 1
        out.append((sections[i], i, j - i))
        i = j
    return out


# Guitar riffs per section. kind: 'm' muted single-note chug, 'p' power stab,
# 'pr' ringing power chord.
def _riff_for(name):
    if name == "intro":
        return [(0, "pr", 8), (8, "p", 2), (10, "m", 1), (12, "p", 2), (14, "m", 1)]
    if name == "verse":                              # galloping drive
        return [(0, "p", 2), (2, "m", 1), (3, "m", 1), (4, "p", 2), (6, "m", 1), (7, "m", 1),
                (8, "p", 2), (10, "m", 1), (11, "m", 1), (12, "p", 2), (14, "m", 1), (15, "m", 1)]
    if name == "pre":                                # straight 16th chug build
        return [(s, "m", 1) for s in range(16)]
    if name == "chorus":                             # anthemic ringing power chords
        return [(0, "pr", 6), (6, "p", 2), (8, "pr", 4), (12, "p", 2), (14, "m", 1), (15, "m", 1)]
    return [(0, "pr", 16)]                            # outro: let it ring


def build():
    guitar = Song(tempo=TEMPO, steps_per_bar=STEPS)
    leadsong = Song(tempo=TEMPO, steps_per_bar=STEPS)
    band = Song(tempo=TEMPO, steps_per_bar=STEPS)

    gtr, arp, piano, bass, strings, glock = [], [], [], [], [], []
    for bar, sec in enumerate(SECTIONS):
        base = bar * STEPS
        root, qual = ROYAL[bar % 4]
        ct = chord(root, qual)                       # four 7th-chord tones
        groot = GROOT[bar % 4]
        broot = note_to_midi(BROOT[bar % 4])

        # --- distorted rhythm guitar (clean DI; NAM adds the gain) ---
        if sec != "intro" or bar >= 2:               # guitar enters bar 2 (build)
            for step, kind, dur in _riff_for(sec):
                if kind.startswith("p"):             # power chord
                    notes, gv = chord(groot, "5"), (116 if sec == "chorus" else 108)
                    gd = dur
                else:                                # palm-muted chug
                    notes, gv, gd = [note_to_midi(groot)], 96, 1
                gtr.append((base + step, notes, gd, gv))

        # --- sawtooth arp: the OP motor, straight 8ths an octave up ---
        seq = [ct[0], ct[1], ct[2], ct[3], ct[1], ct[2], ct[3], ct[0] + 12]
        for k, s in enumerate(range(0, 16, 2)):
            arp.append((base + s, seq[k] + 12, 2, ARP_VEL[sec]))

        # --- piano chord stabs ---
        if sec in ("verse", "pre", "chorus", "outro"):
            for s in (0, 6, 8, 14):
                piano.append((base + s, ct, 2, 82 if s in (0, 8) else 68))

        # --- synth bass: syncopated, with octave pops, locked to the kick ---
        if bar >= 2:
            for s, d, off in [(0, 3, 0), (6, 2, 0), (8, 2, 12), (11, 1, 0), (14, 2, 0)]:
                bass.append((base + s, broot + off, d, 100 if s == 0 else 84))

        # --- string pad lifts the chorus/outro ---
        if sec in ("chorus", "outro"):
            tr, tq = TRIAD[root]
            strings.append((base + 0, chord(tr, tq), 16, 44))

        # --- glock sparkle on intro + chorus downbeats ---
        if sec in ("intro", "chorus"):
            glock.append((base + 0, ct[-1] + 12, 2, 54))
            glock.append((base + 8, ct[1] + 12, 2, 46))

    # Guitar is mono into NAM; one stem (centered "wall").
    guitar.add_part("gtr", "clean_guitar", gtr, seed=71, humanize_time=3, humanize_vel=6)

    lead = []
    for cs in HOOK_STARTS:
        for b4, s, n, d in HOOK:
            lead.append(((cs + b4) * STEPS + s, n, d, 108))
    leadsong.add_part("lead", "square_lead", lead, seed=72, humanize_time=4, humanize_vel=5)

    band.add_part("arp", "saw_lead", arp, seed=73, humanize_time=3, humanize_vel=5)
    band.add_part("piano", "piano", piano, seed=74, humanize_time=4, humanize_vel=6)
    band.add_part("bass", "synth_bass", bass, seed=75, humanize_time=3, humanize_vel=5)
    band.add_part("strings", "synth_strings", strings, seed=76, humanize_time=2, humanize_vel=3)
    band.add_part("glock", "glock", glock, seed=77, humanize_time=3, humanize_vel=4)
    _drums(band)

    return guitar, leadsong, band


def _drums(song):
    KICK = "X . . x X . . . X . . x X . . ."          # driving rock kick
    SNARE = ". . . . X . . . . . . . X . . ."          # backbeat 2 & 4
    HAT = "x x x x x x x x x x x x x x x x"             # busy 16th hats
    OPEN = ". . X . . . X . . . X . . . X ."           # offbeat open hats
    RIDE = "X . x . X . x . X . x . X . x ."
    BUILD = {"snare": "x x x x x x x x X X X X X X X X",
             "kick": "X . . . X . . . X . . . X . . ."}

    for name, start, length in _blocks(SECTIONS):
        if name == "intro":
            song.add_drums({"kick": KICK, "hat": HAT}, bars=2, start_bar=start + 2,
                           vel=92, seed=7)
        elif name == "verse":
            song.add_drums({"kick": KICK, "snare": SNARE, "hat": HAT},
                           bars=length, start_bar=start, vel=104, seed=7)
        elif name == "pre":
            song.add_drums({"kick": KICK, "snare": SNARE, "hat": HAT},
                           bars=length - 1, start_bar=start, vel=104, seed=7)
            song.add_drums(BUILD, bars=1, start_bar=start + length - 1, vel=104, seed=8)
        elif name == "chorus":
            song.add_drums({"kick": KICK, "snare": SNARE, "hat": HAT,
                            "open_hat": OPEN, "ride": RIDE},
                           bars=length, start_bar=start, vel=110, seed=7)
        elif name == "outro":
            song.add_drums({"kick": KICK, "snare": SNARE, "hat": HAT},
                           bars=length, start_bar=start, vel=96, seed=7)

    for b in (16, 28, 36):                            # crash on chorus/outro downbeats
        song.add_drums({"crash": "X"}, bars=1, start_bar=b, vel=82, seed=2)


def nam_pre(norm_db, boost=None):
    """stereo DI -> mono 24-bit -> (boost) -> NAM amp."""
    return lambda in_wav, out_wav: nam.amp(
        in_wav, out_wav, MODEL, norm_db=norm_db, boost=boost, sample_rate=48000)


# Light presence + air on the square-lead "vocal".
LEAD_FX = ["equalizer", "3200", "1.6q", "3", "highpass", "180", "gain", "-n", "-5"]
BAND_FX = ["equalizer", "80", "1q", "2", "gain", "-n", "-2"]


def main():
    if not MODEL.exists():
        sys.exit(f"missing NAM model: {MODEL} — run ./fetch-nam.sh")
    out = ROOT / "out" / "anime_op_rock"
    guitar, leadsong, band = build()
    g_mid = guitar.save(out.with_suffix(".gtr.mid"))
    l_mid = leadsong.save(out.with_suffix(".lead.mid"))
    b_mid = band.save(out.with_suffix(".band.mid"))
    ogg = render_layered(
        [
            {"mid": g_mid, "pre": nam_pre(-4, nam.TS_BOOST),
             "board": cab_board(ir="cab_modern.wav", out_db=-7.0)},
            {"mid": l_mid, "fx": LEAD_FX},
            {"mid": b_mid, "fx": BAND_FX},
        ],
        out.with_suffix(".ogg"),
        synth_gain=0.7, reverb=14, lowpass=19000, bass_gain=2, treble_gain=2,
        sample_rate=48000,
    )
    for m in (g_mid, l_mid, b_mid):
        Path(m).unlink(missing_ok=True)
    print(f"rendered {ogg}")


if __name__ == "__main__":
    main()
