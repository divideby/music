#!/usr/bin/env python3
"""lofi_intro — a relaxed lo-fi hip-hop beat, the studio's first track.

Run from the repo root:  ./render.sh lofi_intro
Builds out/lofi_intro.mid, renders out/lofi_intro.ogg.

~72 BPM in C major / A minor. I-vi-ii-V (Cmaj7 Am7 Dm7 G7) on a Rhodes, finger
bass on the roots, a swung lo-fi kit, and a sparse vibes motif. The groove comes
from light swing + humanize baked into the MIDI.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from studio import Song, render            # noqa: E402
from studio.notes import chord             # noqa: E402

STEPS = 16            # per bar
CYCLES = 3            # 4-bar progression x3 -> 12 bars, ~40s at 72 BPM
SWING = 0.54

# (chord root+quality for the Rhodes, bass root) per bar of the progression.
PROG = [
    ("C4", "maj7", "C2"),
    ("A3", "min7", "A1"),
    ("D4", "min7", "D2"),
    ("G3", "dom7", "G1"),
]

# Sparse vibes motif (A minor pentatonic), placed at (bar_in_cycle, step).
MOTIF = [
    (1, 0, "E4", 6), (1, 10, "G4", 6),
    (2, 4, "A4", 8), (2, 12, "G4", 6),
    (3, 0, "E4", 6), (3, 6, "D4", 6), (3, 12, "C4", 8),
]


def build():
    song = Song(tempo=72, steps_per_bar=STEPS)

    chord_notes, stab_notes, bass_notes, vibes_notes = [], [], [], []
    for c in range(CYCLES):
        for b, (root, qual, bass_root) in enumerate(PROG):
            bar = c * len(PROG) + b
            base = bar * STEPS
            ch = chord(root, qual)
            # Rhodes: full chord on the downbeat, soft stab on the "and of 3".
            chord_notes.append((base + 0, ch, 15, 60))
            stab_notes.append((base + 10, ch, 4, 44))
            # Bass: root on 1 (held), fifth on beat 3.
            from studio.notes import note_to_midi
            r = note_to_midi(bass_root)
            bass_notes.append((base + 0, r, 7, 84))
            bass_notes.append((base + 8, r + 7, 5, 72))
            # Vibes motif.
            for mb, ms, pitch, vel in MOTIF:
                if mb == b:
                    vibes_notes.append((base + ms, pitch, 2, vel))

    song.add_part("rhodes", "rhodes", chord_notes, swing=SWING, seed=11)
    song.add_part("rhodes-stab", "rhodes", stab_notes, swing=SWING, seed=12)
    song.add_part("bass", "finger_bass", bass_notes, swing=SWING, seed=21)
    song.add_part("vibes", "vibes", vibes_notes, swing=SWING, seed=31)

    bars = CYCLES * len(PROG)
    # Opening crash on bar 0 only.
    song.add_drums({"crash": "X"}, bars=1, vel=58, seed=2)
    # Main kit, repeated each bar.
    song.add_drums(
        {
            "kick":     "X . . . . o . . x . . . . o . .",
            "snare":    ". . . . X . . . . . o . X . . .",
            "hat":      "x . o . x . o . x . o . x . o o",
            "open_hat": ". . . . . . . . . . . . . . X .",
            "shaker":   "o . o . o . o . o . o . o . o .",
        },
        bars=bars, swing=SWING, vel=96, seed=7,
    )
    return song


def main():
    out = ROOT / "out" / "lofi_intro"
    song = build()
    mid = song.save(out.with_suffix(".mid"))
    ogg = render(mid, out.with_suffix(".ogg"))
    print(f"rendered {ogg}")


if __name__ == "__main__":
    main()
