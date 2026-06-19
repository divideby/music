#!/usr/bin/env python3
"""kolyan_title — main title theme for the game «Колян».

Run from the repo root:  ./render.sh kolyan_title

The game is an absurdist crime-comedy anime visual novel, so the title wants
"heist-comedy anime opening": A minor, ~122 BPM, a jaunty spy-ish square-lead
hook with a harmonic-minor leading tone (the criminal wink), off-beat organ +
clean-guitar skank stabs (the bounce), a driving root-fifth-octave bass, glock
sparkle and a punchy kit. Progression Am–F–C–G | Am–F–G–E (the E major V is the
harmonic-minor tension that yanks back to Am). One Song -> render().
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from studio import Song, render                       # noqa: E402
from studio.notes import chord, note_to_midi          # noqa: E402

STEPS = 16
TEMPO = 122

# 8-bar loop. (root, quality, bass_note). E maj at the end = harmonic-minor V.
PROG = [
    ("A3", "min", "A1"), ("F3", "maj", "F1"), ("C4", "maj", "C2"), ("G3", "maj", "G1"),
    ("A3", "min", "A1"), ("F3", "maj", "F1"), ("G3", "maj", "G1"), ("E3", "maj", "E1"),
]

# Spy-jaunty square-lead hook over the 8-bar prog. (bar_in_8, step, note, dur)
HOOK = [
    (0, 0, "A4", 2), (0, 2, "C5", 2), (0, 4, "E5", 2), (0, 6, "C5", 2), (0, 8, "A4", 2), (0, 10, "B4", 2), (0, 12, "C5", 4),
    (1, 0, "A4", 2), (1, 2, "C5", 2), (1, 4, "F5", 2), (1, 6, "C5", 2), (1, 8, "A4", 2), (1, 10, "G4", 2), (1, 12, "F4", 4),
    (2, 0, "E5", 2), (2, 2, "G5", 2), (2, 4, "E5", 2), (2, 6, "C5", 2), (2, 8, "D5", 2), (2, 10, "E5", 2), (2, 12, "G5", 4),
    (3, 0, "D5", 2), (3, 2, "B4", 2), (3, 4, "G4", 2), (3, 6, "B4", 2), (3, 8, "D5", 4), (3, 12, "B4", 4),
    (4, 0, "A4", 2), (4, 2, "E5", 2), (4, 4, "A5", 2), (4, 6, "E5", 2), (4, 8, "C5", 2), (4, 10, "B4", 2), (4, 12, "A4", 4),
    (5, 0, "C5", 2), (5, 2, "A4", 2), (5, 4, "F4", 2), (5, 6, "A4", 2), (5, 8, "C5", 2), (5, 10, "D5", 2), (5, 12, "C5", 4),
    (6, 0, "B4", 2), (6, 2, "D5", 2), (6, 4, "G5", 2), (6, 6, "D5", 2), (6, 8, "B4", 2), (6, 10, "A4", 2), (6, 12, "G4", 4),
    (7, 0, "B4", 2), (7, 2, "G#4", 2), (7, 4, "E4", 2), (7, 6, "G#4", 2), (7, 8, "B4", 4), (7, 12, "E5", 4),   # G# = harmonic-minor V
]

# Section layout (bars). 32 bars ~ 63s at 122 BPM.
SECTIONS = ["intro"] * 4 + ["A"] * 8 + ["B"] * 8 + ["A"] * 8 + ["outro"] * 4
HOOK_STARTS = [4, 12, 20]                              # each A/B start = one full 8-bar hook
BACK_VEL = {"intro": 58, "A": 84, "B": 80, "outro": 64}


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
    song = Song(tempo=TEMPO, steps_per_bar=STEPS)

    piano, guitar, organ, bass, glock = [], [], [], [], []
    for bar, sec in enumerate(SECTIONS):
        base = bar * STEPS
        root, qual, broot = PROG[bar % 8]
        ct = chord(root, qual)                         # triad
        bv = BACK_VEL[sec]
        r = note_to_midi(broot)

        # Driving root–fifth–octave bass (the bounce).
        if bar >= 2:
            for s, off, d in [(0, 0, 2), (3, 0, 1), (6, 7, 2), (8, 12, 2), (11, 0, 1), (14, 7, 2)]:
                bass.append((base + s, r + off, d, 98 if s in (0, 8) else 82))

        # Low sustained organ — carousel/heist warmth under everything.
        if sec in ("A", "B", "outro"):
            organ.append((base + 0, ct, 16, max(30, bv - 44)))

        # Piano: chord stabs on the strong beats.
        if sec in ("A", "B", "outro"):
            for s in (0, 8):
                piano.append((base + s, ct, 2, bv))

        # Clean-guitar off-beat skank stabs (the ska/spy push).
        if sec in ("A", "B"):
            for s in (2, 6, 10, 14):
                guitar.append((base + s, [n + 12 for n in ct], 1, bv - 16))

        # Glock sparkle on section downbeats (anime sweetness).
        if sec in ("A", "B") and bar in HOOK_STARTS:
            glock.append((base + 0, ct[-1] + 12, 2, 60))

    lead = []
    for cs in HOOK_STARTS:
        for b8, s, n, d in HOOK:
            lead.append(((cs + b8) * STEPS + s, n, d, 104))

    song.add_part("lead", "square_lead", lead, seed=81, humanize_time=4, humanize_vel=6)
    song.add_part("piano", "piano", piano, seed=82, humanize_time=4, humanize_vel=6)
    song.add_part("guitar", "clean_guitar", guitar, seed=83, humanize_time=3, humanize_vel=6)
    song.add_part("organ", "rock_organ", organ, seed=84, humanize_time=2, humanize_vel=3)
    song.add_part("bass", "pick_bass", bass, seed=85, humanize_time=3, humanize_vel=5)
    song.add_part("glock", "glock", glock, seed=86, humanize_time=3, humanize_vel=4)
    _drums(song)
    return song


def _drums(song):
    KICK = "X . . x X . . . X . . x X . . ."
    SNARE = ". . . . X . . . . . . . X . . ."
    HAT = "x . x . x . x . x . x . x . x ."
    HAT16 = "x x x x x x x x x x x x x x x x"
    OPEN = ". . X . . . X . . . X . . . X ."
    BUILD = {"snare": "x x x x x x x x X X X X X X X X",
             "kick": "X . . . X . . . X . . . X . . ."}

    for name, start, length in _blocks(SECTIONS):
        if name == "intro":
            song.add_drums({"kick": KICK, "hat": HAT}, bars=2, start_bar=start + 2, vel=86, seed=7)
            song.add_drums(BUILD, bars=1, start_bar=start + length - 1, vel=92, seed=8)
        elif name == "A":
            song.add_drums({"kick": KICK, "snare": SNARE, "hat": HAT}, bars=length,
                           start_bar=start, vel=104, seed=7)
        elif name == "B":
            song.add_drums({"kick": KICK, "snare": SNARE, "hat": HAT16, "open_hat": OPEN},
                           bars=length, start_bar=start, vel=106, seed=7)
        elif name == "outro":
            song.add_drums({"kick": KICK, "snare": SNARE, "hat": HAT}, bars=length - 1,
                           start_bar=start, vel=92, seed=7)
            song.add_drums({"kick": "X . . . . . . . . . . . . . . .", "crash": "X"},
                           bars=1, start_bar=start + length - 1, vel=100, seed=2)

    for b in (4, 12, 20):                              # crash on each section downbeat
        song.add_drums({"crash": "X"}, bars=1, start_bar=b, vel=80, seed=2)


def main():
    out = ROOT / "out" / "kolyan_title"
    mid = build().save(out.with_suffix(".mid"))
    ogg = render(mid, out.with_suffix(".ogg"),
                 synth_gain=0.6, reverb=16, lowpass=16000, bass_gain=3, treble_gain=3)
    Path(mid).unlink(missing_ok=True)
    print(f"rendered {ogg}")


if __name__ == "__main__":
    main()
