#!/usr/bin/env python3
"""modern_rock — heavy modern rock / metalcore with a fat overloaded guitar.

Run from the repo root:  ./render.sh modern_rock

158 BPM, Drop-D / D minor. The "fat" comes from production, not just notes:
  * the rhythm guitar is DOUBLE-TRACKED (distortion + overdrive in unison),
  * rendered as its own stem and driven through a cascading sox overdrive +
    low-mid/presence EQ + compression chain (see GUITAR_FX),
  * bass locks to the guitar rhythm an octave-ish below for low-end weight.
Riffs are palm-muted Drop-D chugs (short staccato low D) punctuated by power
chords — the metalcore alternating-riff idea. Structure: intro / verse /
pre-chorus build / chorus / verse / chorus / breakdown / outro.

Research notes that shaped this: palm mute = very short low-string notes;
fatness = layering + cascading overdrive + low-mid EQ + compression; Drop-D
chugging on the open root; i-VI-VII-IV (Dm-Bb-C-Gm) anthem progression.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from studio import Song, render_layered             # noqa: E402
from studio.notes import chord, note_to_midi         # noqa: E402

STEPS = 16

# Section layout (bars), 40 bars ~ 60s at 158 BPM.
SECTIONS = (["intro"] * 2 + ["verse"] * 8 + ["prechorus"] * 4 + ["chorus"] * 8
            + ["verse"] * 4 + ["chorus"] * 8 + ["breakdown"] * 4 + ["outro"] * 2)

CHORUS_ROOTS = ["D2", "Bb1", "C2", "G1"]              # Dm - Bb - C - Gm

# Riff specs: (step, kind, root, dur). kind: 'm' muted chug, 'p' power stab,
# 'pr' power chord left ringing.
VERSE_RIFF = [
    (0, "p", "D2", 2), (2, "m", "D2", 1), (3, "m", "D2", 1), (4, "p", "F2", 2),
    (6, "m", "D2", 1), (7, "m", "D2", 1), (8, "p", "D2", 2), (10, "m", "D2", 1),
    (11, "p", "C2", 2), (12, "m", "D2", 1), (13, "m", "D2", 1), (14, "p", "Bb1", 2),
]
BREAKDOWN_RIFF = [
    (0, "pr", "D2", 4), (4, "m", "D2", 1), (6, "p", "D2", 2), (8, "m", "D2", 1),
    (10, "pr", "Bb1", 4), (14, "m", "D2", 1),
]

# Chorus lead hook (D minor pentatonic), 4-bar phrase. (bar_in_4, step, note, dur)
HOOK = [
    (0, 0, "D5", 4), (0, 4, "F5", 4), (0, 8, "A5", 6), (0, 14, "G5", 2),
    (1, 0, "F5", 4), (1, 4, "D5", 4), (1, 8, "C5", 8),
    (2, 0, "C5", 4), (2, 4, "D5", 4), (2, 8, "F5", 6), (2, 14, "A5", 2),
    (3, 0, "G5", 4), (3, 4, "A5", 4), (3, 8, "D5", 8),
]
HOOK_STARTS = [14, 18, 26, 30]


def _blocks(sections):
    out, i = [], 0
    while i < len(sections):
        j = i
        while j < len(sections) and sections[j] == sections[i]:
            j += 1
        out.append((sections[i], i, j - i))
        i = j
    return out


def _riff_for(name, chorus_idx):
    if name in ("intro", "verse"):
        return VERSE_RIFF
    if name == "prechorus":                          # straight 16th chug build
        return [(s, "m", "D2", 1) for s in range(16)]
    if name == "chorus":
        r = CHORUS_ROOTS[chorus_idx % 4]
        return [(0, "pr", r, 12), (8, "m", r, 1), (10, "m", r, 1),
                (12, "m", r, 1), (14, "m", r, 1)]
    if name == "breakdown":
        return BREAKDOWN_RIFF
    return [(0, "pr", "D2", 16)]                      # outro: let it ring


def build(rhythm_voices=("distortion", "overdrive"), lead_voice="overdrive"):
    tempo = 158
    guitar = Song(tempo=tempo, steps_per_bar=STEPS)   # rhythm stem (doubled)
    leadsong = Song(tempo=tempo, steps_per_bar=STEPS)  # lead stem
    band = Song(tempo=tempo, steps_per_bar=STEPS)      # drums + bass stem

    gtr_notes, bass_notes = [], []
    chorus_idx = 0
    for bar, name in enumerate(SECTIONS):
        base = bar * STEPS
        riff = _riff_for(name, chorus_idx)
        if name == "chorus":
            chorus_idx += 1
        for step, kind, root, dur in riff:
            rm = note_to_midi(root)
            if kind.startswith("p"):                 # power chord
                notes, gv, gd = chord(root, "5"), (118 if name == "breakdown" else 112), dur
            else:                                    # palm-muted chug
                notes, gv, gd = [rm], 98, 1
            gtr_notes.append((base + step, notes, gd, gv))
            bass_notes.append((base + step, rm, max(1, gd), 102))

    # Double-track: same notes on distortion + overdrive (different seeds so the
    # humanize jitter differs slightly -> a wider, thicker unison).
    guitar.add_part("gtrL", rhythm_voices[0], gtr_notes, seed=61, humanize_time=3, humanize_vel=5)
    guitar.add_part("gtrR", rhythm_voices[1], gtr_notes, seed=62, humanize_time=4, humanize_vel=6)

    lead = []
    for cs in HOOK_STARTS:
        for b4, s, n, d in HOOK:
            lead.append(((cs + b4) * STEPS + s, n, d, 110))
    leadsong.add_part("lead", lead_voice, lead, seed=63, humanize_time=4, humanize_vel=5)

    band.add_part("bass", "pick_bass", bass_notes, seed=64, humanize_time=3, humanize_vel=5)
    _drums(band)

    return guitar, leadsong, band


def _drums(song):
    KICK = "X . . x X . x . X . . x X . x ."
    SNARE = ". . . . X . . . . . . . X . . ."
    HAT = "X . x . X . x . X . x . X . x ."
    HAT16 = "x x x x x x x x x x x x x x x x"
    OPEN = ". . X . . . X . . . X . . . X ."
    BD_KICK = "X . . . . . . . X . . x . . . ."
    BD_SNARE = ". . . . . . . . X . . . . . . ."
    BUILD = {"snare": "x x x x x x x x X X X X X X X X", "kick": KICK}

    ci = 0
    for name, start, length in _blocks(SECTIONS):
        if name == "intro":
            song.add_drums({"kick": KICK, "hat": HAT}, bars=length, start_bar=start, vel=96, seed=7)
        elif name == "verse":
            song.add_drums({"kick": KICK, "snare": SNARE, "hat": HAT},
                           bars=length, start_bar=start, vel=104, seed=7)
        elif name == "prechorus":
            song.add_drums({"kick": KICK, "snare": SNARE, "hat": HAT16},
                           bars=length - 1, start_bar=start, vel=104, seed=7)
            song.add_drums(BUILD, bars=1, start_bar=start + length - 1, vel=102, seed=8)
        elif name == "chorus":
            song.add_drums({"kick": KICK, "snare": SNARE, "hat": HAT, "open_hat": OPEN},
                           bars=length, start_bar=start, vel=110, seed=7)
        elif name == "breakdown":
            song.add_drums({"kick": BD_KICK, "snare": BD_SNARE, "crash": "X . . . . . . ."},
                           bars=length, start_bar=start, vel=116, seed=7, humanize_time=3)
        elif name == "outro":
            song.add_drums({"kick": "X . . . . . . . . . . . . . . .", "crash": "X . . . . . . ."},
                           bars=length, start_bar=start, vel=100, seed=7)
        ci += 1

    for b in (2, 14, 26, 34):                        # crashes on section downbeats
        song.add_drums({"crash": "X"}, bars=1, start_bar=b, vel=84, seed=2)


# Cascading overdrive + EQ + compression — the fat, overloaded rhythm tone.
GUITAR_FX = [
    "highpass", "55",
    "equalizer", "850", "1.2q", "+3",        # low-mid body / chug weight
    "equalizer", "2600", "2q", "+4",         # presence / bite
    "overdrive", "18", "28",                 # first stage
    "overdrive", "9", "20",                  # cascaded second stage = fatter
    "compand", "0.01,0.2", "6:-58,-48,-28,-18,-10,-8", "-2",  # thicken/sustain
    "highpass", "60",
    "gain", "-n", "-5",
]
LEAD_FX = [
    "highpass", "130",
    "equalizer", "3000", "2q", "+3",
    "overdrive", "12", "22",
    "gain", "-n", "-7",
]
BAND_FX = ["equalizer", "75", "1q", "+3", "gain", "-n", "-2"]


def main():
    out = ROOT / "out" / "modern_rock"
    guitar, leadsong, band = build()
    g_mid = guitar.save(out.with_suffix(".gtr.mid"))
    l_mid = leadsong.save(out.with_suffix(".lead.mid"))
    b_mid = band.save(out.with_suffix(".band.mid"))
    ogg = render_layered(
        [
            {"mid": g_mid, "fx": GUITAR_FX},
            {"mid": l_mid, "fx": LEAD_FX},
            {"mid": b_mid, "fx": BAND_FX},
        ],
        out.with_suffix(".ogg"),
        synth_gain=0.5, reverb=10, lowpass=19000, bass_gain=2, treble_gain=2,
    )
    for m in (g_mid, l_mid, b_mid):
        Path(m).unlink(missing_ok=True)
    print(f"rendered {ogg}")


if __name__ == "__main__":
    main()
