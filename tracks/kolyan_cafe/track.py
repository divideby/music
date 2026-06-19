#!/usr/bin/env python3
"""kolyan_cafe — warm lo-fi jazz lounge for the game "Колян".

Run from the repo root:  ./render.sh kolyan_cafe
Builds out/kolyan_cafe.mid, renders out/kolyan_cafe.ogg.

Café scene — the gang relaxes getting their money back (VA-11 Hall-A / Persona
lounge vibe). ~82 BPM, C major with jazz changes. Lush Rhodes comping on 7th/9th
voicings, a walking finger bass with chromatic approach notes, a relaxed vibes
head, a behind-the-beat sax "solo" variation, and a soft brushed kit + shaker.
Swing (~0.14 -> 0.57 ratio) gives the lo-fi/jazz lilt; resolves on a held Cmaj9.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from studio import Song, render            # noqa: E402
from studio.notes import chord, note_to_midi  # noqa: E402

STEPS = 16
SWING = 0.57           # ~0.14 lilt expressed as the swing ratio used by parts

# ── Harmony ──────────────────────────────────────────────────────────────
# A 4-bar turnaround in C, plus a ii-V-I-with-secondary variant. Each entry:
#   (rhodes chord root, quality, bass root, [walking approach notes per bar]).
# Walking notes are placed on beats 2/3/4 (steps 4/8/12), leading to the next
# bar's root.
TURN_A = [
    ("C4",  "maj7", "C2", ["E2", "G2", "B2"]),   # Cmaj7  -> A
    ("A3",  "min7", "A1", ["C2", "E2", "F2"]),   # Am7    -> D
    ("D4",  "min7", "D2", ["F2", "A2", "B2"]),   # Dm7    -> G
    ("G3",  "dom7", "G1", ["B1", "D2", "F2"]),   # G7     -> C
]
# Variation cycle: Em7 - A7 - Dm7 - G7 (a stronger ii-V chain back home).
TURN_B = [
    ("E4",  "min7", "E2", ["G2", "B2", "D2"]),   # Em7    -> A
    ("A3",  "dom7", "A1", ["C#2", "E2", "G2"]),  # A7     -> D
    ("D4",  "min7", "D2", ["F2", "A2", "C2"]),   # Dm7    -> G
    ("G3",  "dom7", "G1", ["B1", "D2", "F2"]),   # G7     -> C
]

# ── Vibes head (relaxed, sits behind the beat) — per (bar_in_cycle, step). ──
# C major / lydian-ish noodling that outlines the changes.
HEAD = [
    (0, 2, "G4", 6, 60), (0, 10, "E4", 4, 52),
    (1, 0, "C5", 4, 58), (1, 8, "A4", 6, 54),
    (2, 2, "F4", 5, 56), (2, 10, "A4", 4, 52), (2, 14, "D5", 3, 50),
    (3, 0, "B4", 4, 56), (3, 6, "G4", 4, 50), (3, 12, "D4", 6, 52),
]

# ── Sax solo phrasing for the variation section (more linear, syncopated). ──
SAX = [
    (0, 4, "E4", 6, 64), (0, 11, "G4", 5, 58), (0, 14, "A4", 3, 54),
    (1, 2, "C5", 6, 66), (1, 9, "B4", 4, 56), (1, 13, "A4", 3, 52),
    (2, 1, "F4", 6, 62), (2, 8, "G4", 4, 56), (2, 12, "A4", 5, 58),
    (3, 3, "D5", 7, 64), (3, 10, "B4", 4, 56), (3, 14, "G4", 3, 52),
]


def build():
    song = Song(tempo=82, steps_per_bar=STEPS)

    chord_notes, stab_notes, bass_notes = [], [], []
    vibes_notes, sax_notes = [], []

    # Section plan (each entry: progression, do_head_vibes, do_sax).
    #   intro      : 4 bars, rhodes + bass only
    #   head x2    : 8 bars (TURN_A) with vibes melody
    #   variation  : 8 bars (TURN_B) with sax solo, sparser vibes
    #   restate    : 8 bars (TURN_A) head + light sax counter
    #   outro      : 4 bars (TURN_A) winding down -> held Cmaj9
    sections = [
        ("intro",     TURN_A, False, False),
        ("head1",     TURN_A, True,  False),
        ("solo1",     TURN_B, False, True),
        ("restate",   TURN_A, True,  False),
        ("outro",     TURN_A, False, False),
    ]

    bar = 0
    for name, prog, do_vibes, do_sax in sections:
        for b, (root, qual, bass_root, walk) in enumerate(prog):
            base = bar * STEPS
            ch = chord(root, qual)
            # Rhodes: lush full chord on the downbeat, soft upbeat stab.
            chord_notes.append((base + 0, ch, 14, 58))
            stab_notes.append((base + 10, ch, 4, 40))
            # On the variation, add a 9th colour stab mid-bar for movement.
            if prog is TURN_B:
                ninth = chord(root, "maj9" if qual == "maj7" else "min9"
                              if qual == "min7" else "dom7")
                stab_notes.append((base + 6, ninth, 3, 36))
            # Walking bass: root on 1, approach notes on 2/3/4.
            r = note_to_midi(bass_root)
            bass_notes.append((base + 0, r, 7, 78))
            for k, wstep in enumerate((4, 8, 12)):
                bass_notes.append((base + wstep, note_to_midi(walk[k]), 3, 68))
            # Melodies.
            if do_vibes:
                for mb, ms, pitch, dur, vel in HEAD:
                    if mb == b:
                        vibes_notes.append((base + ms, pitch, dur, vel))
            if do_sax:
                for mb, ms, pitch, dur, vel in SAX:
                    if mb == b:
                        sax_notes.append((base + ms, pitch, dur, vel))
            bar += 1

    total_bars = bar  # 20

    # Final held Cmaj9 in the last bar (replace the rhodes downbeat there).
    last_base = (total_bars - 1) * STEPS
    chord_notes = [c for c in chord_notes if c[0] != last_base]
    stab_notes = [s for s in stab_notes if s[0] != last_base + 10]
    chord_notes.append((last_base, chord("C4", "maj9"), 16, 56))
    # And a soft vibes tonic to ring out over it.
    vibes_notes.append((last_base + 0, "E5", 12, 46))

    song.add_part("rhodes", "rhodes", chord_notes, swing=SWING,
                  humanize_time=8, humanize_vel=7, seed=11)
    song.add_part("rhodes-stab", "rhodes", stab_notes, swing=SWING,
                  humanize_time=8, humanize_vel=8, seed=12)
    song.add_part("bass", "finger_bass", bass_notes, swing=SWING,
                  humanize_time=6, humanize_vel=6, seed=21)
    song.add_part("vibes", "vibes", vibes_notes, swing=SWING,
                  humanize_time=10, humanize_vel=8, seed=31)
    song.add_part("sax", "sax", sax_notes, swing=SWING,
                  humanize_time=12, humanize_vel=9, seed=41)

    # Soft brushed kit: gentle kick + rim, light ride/hat, steady shaker.
    song.add_drums(
        {
            "kick":   "X . . . . . . . x . . . . . . .",
            "rim":    ". . . . o . . . . . . . o . . .",
            "ride":   "x . . x . . x . x . . x . . x .",
            "hat":    ". . o . . . o . . . o . . . o .",
            "shaker": "o . o o . o o . o . o o . o o .",
        },
        bars=total_bars, swing=SWING, vel=66,
        humanize_time=9, humanize_vel=12, seed=7,
    )
    return song


def main():
    out = ROOT / "out" / "kolyan_cafe"
    song = build()
    mid = song.save(out.with_suffix(".mid"))
    # Dusty, warm master.
    ogg = render(mid, out.with_suffix(".ogg"),
                 reverb=30, lowpass=13500, bass_gain=3, treble_gain=-2)
    print(f"rendered {ogg}")


if __name__ == "__main__":
    main()
