#!/usr/bin/env python3
"""dnb — liquid drum & bass at the genre-standard 174 BPM.

Run from the repo root:  ./render.sh dnb

F minor, the lush "liquid" flavour: a Fmin9 / Abmaj7 / Dbmaj7 / Ebmaj9 loop on a
Rhodes-style epiano pad, a deep sustained sub bass locked to the roots, and a
vibraphone melodic hook. The defining element is the two-step amen-style break —
fast syncopated kick + snare with the backbeat snare on beat 3 (step 8), ghost
snares, busy 16th hats with open-hat accents.

Structure (40 bars ~ 55s @ 174): intro (pad + sub) / main (full break) /
breakdown (drums drop out, pad + sub only) / main again with a snare-roll build /
outro. Deterministic — every part is seeded.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from studio import Song, render                      # noqa: E402
from studio.notes import chord, note_to_midi         # noqa: E402

STEPS = 16

# Liquid F-minor loop: lush 7th/9th chords, one chord per bar.
PROG = [("F3", "min9"), ("Ab3", "maj7"), ("Db3", "maj7"), ("Eb3", "maj9")]
# Sub-bass root per chord, way down in the floor.
SUB = {"F3": "F1", "Ab3": "Ab1", "Db3": "Db1", "Eb3": "Eb1"}

# Section layout (bars), 40 total.
SECTIONS = (["intro"] * 4 + ["main"] * 12 + ["break"] * 8
            + ["main"] * 12 + ["outro"] * 4)

PAD_VEL = {"intro": 42, "main": 48, "break": 54, "outro": 40}

# 4-bar vibraphone hook over F-Ab-Db-Eb (bar_in_4, step, note, dur).
HOOK = [
    (0, 0, "C5", 4), (0, 6, "Ab4", 2), (0, 10, "C5", 2), (0, 12, "Eb5", 4),
    (1, 0, "Eb5", 4), (1, 6, "C5", 2), (1, 10, "Ab4", 4),
    (2, 0, "F5", 4), (2, 6, "Ab4", 2), (2, 8, "C5", 2), (2, 12, "Db5", 4),
    (3, 0, "Bb4", 4), (3, 6, "G4", 2), (3, 8, "Bb4", 2), (3, 12, "C5", 4),
]


def _blocks(sections):
    out, i = [], 0
    while i < len(sections):
        j = i
        while j < len(sections) and sections[j] == sections[i]:
            j += 1
        out.append((sections[i], i, j - i))
        i = j
    return out


def build():
    song = Song(tempo=174, steps_per_bar=STEPS)

    pad, sub = [], []
    for bar, sec in enumerate(SECTIONS):
        base = bar * STEPS
        root, qual = PROG[bar % 4]
        ct = chord(root, qual)

        # Rhodes/epiano pad: lush chord, but let it breathe (decays before the
        # bar end) so the break transients keep the mix dynamic, not a wall.
        pad.append((base, ct, 8, PAD_VEL[sec]))

        # Sub bass: deep syncopated reese-style root line, sparse with gaps.
        r = note_to_midi(SUB[root])
        sub.append((base + 0, r, 6, 96))     # downbeat root, leaves room
        sub.append((base + 10, r, 3, 84))    # low push, gap after

    # Vibes hook only over the two main sections; loops the 4-bar phrase.
    vibes = []
    for start in (4, 8, 12, 24, 28):                 # main-section 4-bar windows
        for b4, s, n, d in HOOK:
            vibes.append(((start + b4) * STEPS + s, n, d, 70))

    song.add_part("pad", "epiano", pad, seed=41, humanize_time=3, humanize_vel=4)
    song.add_part("sub", "synth_bass2", sub, seed=42, humanize_time=2, humanize_vel=3)
    song.add_part("vibes", "vibes", vibes, seed=43, humanize_time=4, humanize_vel=6)

    _drums(song)
    return song


def _drums(song):
    # Two-step amen-style break: snare backbeat on step 8, ghost snare at 14,
    # syncopated kicks, busy 16th hats with offbeat open-hat accents.
    KICK = "X . . . . . x . . . X . . . . ."
    SNARE = ". . . . . . . . X . . . . . x ."
    GHOST = ". . . . . o . . . . . . o . . ."   # quiet ghost snares between
    HAT = "x . . x . x . . x . . x . x . ."     # syncopated 16th hats, airy
    OPEN = ". . . . o . . . . . . . o . . ."    # offbeat open-hat accents
    RIDE = ". . o . . . o . . . o . . . o ."

    # A 2-bar snare roll that builds into the second drop.
    ROLL = {"snare": "x x x x x x x x x x x x X X X X",
            "kick":  "X . . . X . . . X . . . X . . ."}

    for name, start, length in _blocks(SECTIONS):
        if name == "intro":
            # No break yet — just a soft ride to keep time the last 2 bars.
            song.add_drums({"ride": RIDE}, bars=2, start_bar=start + 2,
                           vel=60, seed=11)
        elif name == "main":
            song.add_drums(
                {"kick": KICK, "snare": SNARE, "hat": HAT, "open_hat": OPEN},
                bars=length, start_bar=start, vel=104, seed=11)
            song.add_drums({"snare": GHOST}, bars=length, start_bar=start,
                           vel=58, seed=12)
        elif name == "break":
            # Drums drop out (pad + sub carry it); soft shaker pulse only.
            song.add_drums({"shaker": "x . x . x . x . x . x . x . x ."},
                           bars=length, start_bar=start, vel=50, seed=13)

    # Crash on each drop into a main section.
    for b in (4, 24):
        song.add_drums({"crash": "X"}, bars=1, start_bar=b, vel=84, seed=2)

    # Snare-roll build in the last 2 bars of the breakdown, into the 2nd drop.
    song.add_drums(ROLL, bars=2, start_bar=22, vel=96, seed=14)


def main():
    out = ROOT / "out" / "dnb"
    mid = build().save(out.with_suffix(".mid"))
    ogg = render(mid, out.with_suffix(".ogg"),
                 synth_gain=0.42, reverb=14, lowpass=18000,
                 bass_gain=5, treble_gain=2)
    print(f"rendered {ogg}")


if __name__ == "__main__":
    main()
