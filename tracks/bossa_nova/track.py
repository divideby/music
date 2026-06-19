#!/usr/bin/env python3
"""bossa_nova — warm, intimate bossa nova / Latin jazz.

Run from the repo root:  ./render.sh bossa_nova
Builds out/bossa_nova.mid, renders out/bossa_nova.ogg.

~132 BPM in F major. Nylon-guitar comping the signature syncopated 7th/9th
"chunk" (anticipating the beat), finger bass on the root–fifth bossa pulse
(beats 1 and 3), a soft 3-2 bossa-clave rim + steady shaker, and a gentle
flute/sax/vibes melody over jazzy ii–V–I changes. Structure: intro (guitar +
bass) → head with flute → variation with sax + vibes → outro resolving to Fmaj7.

Determinism: every part takes a seed; same code → same MIDI → same audio.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from studio import Song, render            # noqa: E402
from studio.notes import chord, note_to_midi   # noqa: E402

STEPS = 16
SWING = 0.10          # a light relaxed lilt on the comping parts

# 4-bar ii–V–I cycle in F major, plus a turnaround. (root+qual for the nylon
# guitar voicing, bass root). 9 sections of 4 bars = 36 bars.
#   | Gm9 | C9 | Fmaj9 | Dm9 |  with a ii–V turnaround into the next cycle.
PROG = [
    ("G3", "min9", "G1"),    # Gm9   (ii)
    ("C3", "dom7", "C2"),    # C7    (V)   -> low root for a fat dominant
    ("F3", "maj9", "F1"),    # Fmaj9 (I)
    ("D3", "min9", "D2"),    # Dm9   (vi as ii of the turnaround)
]

NUM_CYCLES = 9                       # 36 bars
BARS = NUM_CYCLES * len(PROG)


def comp_chord(base, ch):
    """Bossa nylon comp for one bar: the classic syncopated 'chunk'.

    The guitar does NOT land on beat 1. It anticipates: a short stab on the
    'and of 1' (step 2), a sustained chunk on the 'and of 2' (step 6), and an
    anticipation of the next bar pushed onto step 14. Soft, fingered velocities.
    """
    return [
        (base + 2, ch, 3, 58),    # and-of-1, short
        (base + 6, ch, 5, 64),    # and-of-2, the main chunk (a touch longer)
        (base + 11, ch, 2, 52),   # late off-beat fill
        (base + 14, ch, 3, 60),   # anticipation, pushes into the next bar
    ]


def bass_line(base, root_name):
    """Bossa bass pulse: root on beat 1, fifth on beat 3 (the two-feel)."""
    r = note_to_midi(root_name)
    return [
        (base + 0, r, 7, 88),     # root, beat 1 (held)
        (base + 8, r + 7, 6, 80),  # fifth, beat 3
    ]


# Flute melody for the head — sparse, lyrical, F major / pentatonic-ish, placed
# at (bar_in_cycle, step, pitch, dur, vel). Sits over the ii–V–I changes.
HEAD = [
    (0, 0, "Bb4", 4, 70), (0, 6, "A4", 3, 66), (0, 12, "G4", 4, 64),
    (1, 2, "G4", 3, 68), (1, 8, "E4", 4, 64), (1, 14, "G4", 2, 60),
    (2, 0, "A4", 6, 72), (2, 8, "C5", 4, 70), (2, 13, "A4", 3, 64),
    (3, 0, "F4", 4, 66), (3, 6, "A4", 3, 64), (3, 12, "D4", 4, 62),
]

# Sax counter-melody for the variation section — a bit lower, breathier phrasing.
VARI = [
    (0, 2, "D4", 4, 66), (0, 10, "F4", 4, 64),
    (1, 0, "G4", 6, 70), (1, 10, "Bb4", 4, 66),
    (2, 0, "C5", 4, 72), (2, 6, "A4", 3, 66), (2, 10, "G4", 5, 64),
    (3, 4, "F4", 4, 64), (3, 12, "C4", 4, 62),
]

# Vibes color accents in the variation (placed sparsely, high register).
VIBES = [
    (0, 8, "F5", 3, 40),
    (1, 6, "D5", 3, 42),
    (2, 12, "E5", 3, 44),
    (3, 0, "C5", 4, 40),
]


def build():
    song = Song(tempo=132, steps_per_bar=STEPS)

    guitar, ride_bass, flute, sax, vibes = [], [], [], [], []

    for c in range(NUM_CYCLES):
        for b, (root, qual, bass_root) in enumerate(PROG):
            bar = c * len(PROG) + b
            base = bar * STEPS

            # Intro (cycles 0): guitar + bass only, no melody.
            in_intro = c == 0
            in_head = 1 <= c <= 3
            in_vari = 4 <= c <= 6
            in_outro = c >= 7

            ch = chord(root, qual)

            # On the very last bar of the whole tune, resolve cleanly to Fmaj9
            # with a single held voicing instead of the syncopated comp.
            if bar == BARS - 1:
                fch = chord("F3", "maj9")
                guitar.append((base + 0, fch, 16, 66))
                ride_bass.append((base + 0, note_to_midi("F1"), 14, 86))
                continue

            guitar += comp_chord(base, ch)
            ride_bass += bass_line(base, bass_root)

            # Melody layers per section.
            if in_head:
                for mb, ms, pitch, dur, vel in HEAD:
                    if mb == b:
                        flute.append((base + ms, pitch, dur, vel))
            if in_vari:
                for mb, ms, pitch, dur, vel in VARI:
                    if mb == b:
                        sax.append((base + ms, pitch, dur, vel))
                for mb, ms, pitch, dur, vel in VIBES:
                    if mb == b:
                        vibes.append((base + ms, pitch, dur, vel))
            if in_outro and not in_vari:
                # Outro reprises the flute head once, more sparsely, fading.
                for mb, ms, pitch, dur, vel in HEAD:
                    if mb == b and ms in (0, 8):
                        flute.append((base + ms, pitch, dur, max(40, vel - 18)))

    song.add_part("nylon", "nylon", guitar, swing=SWING, seed=11)
    song.add_part("bass", "finger_bass", ride_bass, swing=SWING, seed=21)
    song.add_part("flute", "flute", flute, swing=SWING, seed=31)
    song.add_part("sax", "sax", sax, swing=SWING, seed=41)
    song.add_part("vibes", "vibes", vibes, swing=SWING, seed=51)

    # Bossa clave/rim — a 2-bar 3-2 side-stick pattern, soft. Plus a soft kick
    # surdo pulse and a steady shaker driving every 8th. Start after the 1-bar
    # count so the intro breathes; here we run it across the whole tune.
    # 3-2 bossa clave (rim), spread over two bars (32 steps):
    #   bar A: 1 . . & . . 4 . . . & . . . . .   (3-side)
    #   bar B: . . . . & . . . 3 . . . . . . .   (2-side, approx)
    song.add_drums(
        {
            # surdo-ish soft kick: beat 1 and the 'and of 3' two-feel
            "kick": "o . . . . . . . . . o . . . . .",
            "rim":  "X . . X . . X . . . X . X . . .",
        },
        bars=BARS, swing=0.0, vel=70, seed=7,
    )
    # Steady shaker on every 8th note (the bossa engine).
    song.add_drums(
        {"shaker": "o . o . o . o . o . o . o . o ."},
        bars=BARS, swing=SWING, vel=58, seed=9,
    )
    return song


def main():
    out = ROOT / "out" / "bossa_nova"
    song = build()
    mid = song.save(out.with_suffix(".mid"))
    # Warm, intimate acoustic master.
    ogg = render(mid, out.with_suffix(".ogg"),
                 reverb=28, lowpass=15000, bass_gain=3, treble_gain=1)
    print(f"rendered {ogg}")


if __name__ == "__main__":
    main()
