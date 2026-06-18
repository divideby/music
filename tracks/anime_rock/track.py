#!/usr/bin/env python3
"""anime_rock — driving J-rock in the spirit of an anime opening.

Run from the repo root:  ./render.sh anime_rock

~172 BPM, E minor. Distortion power-chord rhythm, an overdriven lead (intro riff
+ soaring chorus melody), pick bass on straight 8ths, a string pad under the
chorus for the anime-epic lift, plus crashes on section downbeats and tom fills
into each chorus. Progression is the anthemic i–VI–III–VII (Em–C–G–D).
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from studio import Song, render                      # noqa: E402
from studio.notes import chord, note_to_midi         # noqa: E402

STEPS = 16
PROG = ["E2", "C2", "G2", "D2"]          # Em - C - G - D (octave-2 roots)

# Section map: each bar -> (power-chord root, rhythm style).
SPEC = []
SPEC += [("E2", "chug")] * 4                                   # intro  (bars 0-3)
SPEC += [(PROG[i % 4], "chug") for i in range(8)]              # verse1 (4-11)
SPEC += [(PROG[i % 4], "ring") for i in range(8)]              # chorus1(12-19)
SPEC += [(PROG[i % 4], "chug") for i in range(8)]              # verse2 (20-27)
SPEC += [(PROG[i % 4], "ring") for i in range(8)]              # chorus2(28-35)
SPEC += [("C2", "ring"), ("D2", "ring"), ("E2", "ring"), ("E2", "ring")]  # outro (36-39)

CHORUS_BARS = {b for b, (_, st) in enumerate(SPEC) if st == "ring"} - {36, 37, 38, 39}

# Intro lead riff (E minor pentatonic), one bar, repeated through the intro.
INTRO_RIFF = [(0, "E4", 2), (2, "G4", 2), (4, "E4", 1), (6, "A4", 2),
              (8, "B4", 2), (10, "G4", 2), (12, "E4", 2), (14, "D4", 2)]

# Soaring chorus melody, a 4-bar phrase aligned to Em-C-G-D. (bar_in_4, step, note, dur)
CHORUS_MEL = [
    (0, 0, "B4", 4), (0, 4, "D5", 4), (0, 8, "E5", 6), (0, 14, "B4", 2),
    (1, 0, "C5", 4), (1, 4, "E5", 4), (1, 8, "G5", 8),
    (2, 0, "D5", 4), (2, 4, "G5", 4), (2, 8, "B5", 6), (2, 14, "A5", 2),
    (3, 0, "A4", 4), (3, 4, "D5", 4), (3, 8, "F#5", 8),
]
CHORUS_STARTS = [12, 16, 28, 32]         # two choruses, the phrase twice each

# Triad voicings for the string pad, by power-chord root.
PAD = {"E2": ("E4", "min"), "C2": ("C4", "maj"), "G2": ("G3", "maj"), "D2": ("D4", "maj")}


def build():
    song = Song(tempo=172, steps_per_bar=STEPS)

    rhythm, bass, lead, strings = [], [], [], []
    for bar, (root, style) in enumerate(SPEC):
        base = bar * STEPS
        power = chord(root, "5")
        root_midi = note_to_midi(root)
        if style == "chug":                      # palm-muted straight 8ths
            for s in range(0, 16, 2):
                rhythm.append((base + s, power, 1, 106 if s % 4 == 0 else 92))
        else:                                    # let the chords ring
            rhythm.append((base + 0, power, 8, 102))
            rhythm.append((base + 8, power, 8, 96))
        for s in range(0, 16, 2):                # bass drives 8ths on the root
            bass.append((base + s, root_midi, 1, 98 if s % 4 == 0 else 84))
        if bar in CHORUS_BARS:                   # string pad holds the triad
            rn, q = PAD[root]
            strings.append((base + 0, chord(rn, q), 16, 44))

    for bar in range(4):                         # intro riff
        base = bar * STEPS
        for s, n, d in INTRO_RIFF:
            lead.append((base + s, n, d, 96))
    for cs in CHORUS_STARTS:                     # chorus melody
        for b4, s, n, d in CHORUS_MEL:
            lead.append(((cs + b4) * STEPS + s, n, d, 100))

    song.add_part("rhythm", "distortion", rhythm, seed=41, humanize_time=4, humanize_vel=5)
    song.add_part("bass", "pick_bass", bass, seed=42, humanize_time=4, humanize_vel=5)
    song.add_part("lead", "overdrive", lead, seed=43, humanize_time=5, humanize_vel=6)
    song.add_part("strings", "strings", strings, seed=44, humanize_time=3, humanize_vel=4)

    # Drums: solid rock backbeat for all 40 bars.
    song.add_drums(
        {
            "kick":  "X . . . x . . . X . . . x . . .",
            "snare": ". . . . X . . o . . . . X . . o",
            "hat":   "X . x . X . x . X . x . X . x .",
        },
        bars=len(SPEC), vel=104, seed=7, humanize_time=5, humanize_vel=10,
    )
    # Crash on each section downbeat.
    for b in (0, 4, 12, 20, 28, 36):
        song.add_drums({"crash": "X"}, bars=1, start_bar=b, vel=80, seed=2)
    # Tom fill into each chorus (over the last verse bar).
    fill = {
        "tom_hi":  ". . . . . . . . X X . . . . . .",
        "tom_mid": ". . . . . . . . . . X X . . . .",
        "tom_lo":  ". . . . . . . . . . . . X X . .",
        "snare":   ". . . . . . . . . . . . . . X X",
    }
    for b in (11, 27):
        song.add_drums(fill, bars=1, start_bar=b, vel=102, seed=9, humanize_time=3)
    return song


def main():
    out = ROOT / "out" / "anime_rock"
    mid = build().save(out.with_suffix(".mid"))
    ogg = render(mid, out.with_suffix(".ogg"),
                 synth_gain=0.5, reverb=14, lowpass=16500, bass_gain=2, treble_gain=2)
    print(f"rendered {ogg}")


if __name__ == "__main__":
    main()
