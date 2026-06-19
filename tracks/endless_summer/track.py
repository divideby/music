#!/usr/bin/env python3
"""endless_summer — nostalgic dreamy ambient for a visual novel.

Run from the repo root:  ./render.sh endless_summer
Builds out/endless_summer.mid, renders out/endless_summer.ogg.

A love letter to Sergey Eybog's «Бесконечное лето» (Everlasting Summer)
soundtrack: warm reverb-drenched synth pad, a simple repetitive music-box
melody, soft piano arpeggios and a sparse glockenspiel twinkle, over a gentle
half-time lo-fi beat. Slow, hazy, melancholic-but-warm — pioneer-camp summer
nostalgia as background music for reading.

Key & changes follow the main theme's world: A-flat major, built on the iconic
nostalgic loop  Ab – Cm – Fm – Eb , with a vi-IV-I-V "lift" section (Fm – Db –
Ab – Eb) and a wistful bridge. ~75 BPM, half-time feel. Mastered very warm and
washed-out (heavy reverb, gentle low-pass) for that tape/lo-fi haze.

Determinism: every part takes a seed; same code -> same MIDI -> same audio.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from studio import Song, render            # noqa: E402
from studio.notes import chord, note_to_midi   # noqa: E402

STEPS = 16
TEMPO = 75

# ── Harmony ────────────────────────────────────────────────────────────────
# Each entry: (pad chord root, quality, bass root). 4-bar cycles in Ab major.
# A — the iconic Everlasting-Summer loop: I – iii – vi – V.
PROG_A = [
    ("Ab3", "maj7", "Ab1"),   # Abmaj7  (I)
    ("C4",  "min7", "C2"),    # Cm7     (iii)
    ("F3",  "min7", "F1"),    # Fm7     (vi)
    ("Eb4", "add9", "Eb2"),   # Eb(add9)(V)
]
# B — the "lift": vi – IV – I – V, the most nostalgic pop turn there is.
PROG_B = [
    ("F3",  "min7", "F1"),    # Fm7     (vi)
    ("Db4", "maj7", "Db2"),   # Dbmaj7  (IV)
    ("Ab3", "maj7", "Ab1"),   # Abmaj7  (I)
    ("Eb4", "add9", "Eb2"),   # Eb(add9)(V)
]
# C — wistful bridge: IV – V – vi – V, hanging on the unresolved dominant.
PROG_C = [
    ("Db4", "maj7", "Db2"),   # Dbmaj7  (IV)
    ("Eb4", "add9", "Eb2"),   # Eb(add9)(V)
    ("F3",  "min7", "F1"),    # Fm7     (vi)
    ("Eb4", "add9", "Eb2"),   # Eb(add9)(V)
]

# ── Music-box melody over PROG_A — simple, singable, Ab major. ──────────────
# (bar_in_cycle, step, note, dur, vel)
MEL_A = [
    (0, 0, "Eb5", 4, 70), (0, 6, "C5", 4, 60), (0, 12, "Ab4", 4, 56),
    (1, 0, "C5", 6, 64),  (1, 8, "Bb4", 4, 58), (1, 14, "Eb5", 2, 52),
    (2, 0, "F5", 4, 68),  (2, 6, "Eb5", 4, 60), (2, 12, "C5", 6, 56),
    (3, 2, "Bb4", 4, 62), (3, 8, "Eb5", 4, 58), (3, 12, "F5", 4, 54),
]

# ── Music-box melody over PROG_B — higher, more longing, sparser. ──────────
MEL_B = [
    (0, 0, "Ab5", 6, 66), (0, 8, "F5", 4, 56),
    (1, 0, "C5", 4, 60),  (1, 6, "F5", 4, 58), (1, 12, "Ab5", 4, 54),
    (2, 0, "Eb5", 6, 66), (2, 8, "C5", 4, 58), (2, 12, "Bb4", 2, 50),
    (3, 0, "Bb4", 4, 60), (3, 8, "Eb5", 6, 56),
]

# ── Glockenspiel twinkle for B / bridge — very high, very soft, sparse. ────
GLOCK = [
    (0, 4, "Ab6", 2, 34), (1, 10, "Eb6", 2, 32),
    (2, 6, "C6", 2, 34),  (3, 2, "Bb5", 2, 30), (3, 12, "Eb6", 2, 30),
]


def whole_bar_pad(base, root, qual, vel=46):
    """One soft, sustained pad chord filling the whole bar."""
    return [(base, chord(root, qual), STEPS, vel)]


def piano_arp(base, root, qual, vel=42):
    """Gentle ascending broken chord — soft eighth-ish sparkle under the pad."""
    tones = chord(root, qual)
    out = []
    for i, step in enumerate((0, 3, 6, 9, 12, 15)):
        n = tones[i % len(tones)] + (12 if i >= len(tones) else 0)
        out.append((base + step, n, 3, vel - (i % 2) * 6))
    return out


def soft_bass(base, root_name, vel=64):
    """Root on beat 1 (held), fifth on beat 3 — a slow two-feel pulse."""
    r = note_to_midi(root_name)
    return [(base + 0, r, 7, vel), (base + 8, r + 7, 5, vel - 6)]


def build():
    song = Song(tempo=TEMPO, steps_per_bar=STEPS)

    pad, strings, box, glock, piano, bass = [], [], [], [], [], []

    # (name, progression, melody, do_box, do_strings, do_glock, do_piano, do_bass)
    sections = [
        ("intro",  PROG_A, MEL_A, True,  False, False, False, False),
        ("A1",     PROG_A, MEL_A, True,  False, False, True,  True),
        ("A1b",    PROG_A, MEL_A, True,  False, False, True,  True),
        ("B1",     PROG_B, MEL_B, True,  True,  True,  True,  True),
        ("B1b",    PROG_B, MEL_B, True,  True,  True,  True,  True),
        ("A2",     PROG_A, MEL_A, True,  True,  False, True,  True),
        ("A2b",    PROG_A, MEL_A, True,  True,  False, True,  True),
        ("bridge", PROG_C, None,  False, True,  True,  True,  True),
        ("bridgeb",PROG_C, None,  False, True,  True,  True,  True),
        ("A3",     PROG_A, MEL_A, True,  True,  False, True,  True),
        ("A3b",    PROG_A, MEL_A, True,  True,  False, True,  True),
        ("outro",  PROG_A, MEL_A, True,  True,  False, False, True),
    ]

    bar = 0
    drums_start = None
    drums_end = None
    for name, prog, mel, do_box, do_strings, do_glock, do_piano, do_bass in sections:
        # Drums run continuously from the first A section through the last.
        if do_bass and name != "outro":
            if drums_start is None:
                drums_start = bar
            drums_end = bar + len(prog)
        for b, (root, qual, bass_root) in enumerate(prog):
            base = bar * STEPS
            pad += whole_bar_pad(base, root, qual)
            if do_strings:
                # A second, airier pad layer an octave-ish up for the swell.
                strings += [(base, chord(root, qual), STEPS, 30)]
            if do_box and mel:
                for mb, ms, pitch, dur, vel in mel:
                    if mb == b:
                        # Intro a touch softer / more distant.
                        v = vel - 10 if name == "intro" else vel
                        box.append((base + ms, pitch, dur, v))
            if do_glock:
                for gb, gs, pitch, dur, vel in GLOCK:
                    if gb == b:
                        glock.append((base + gs, pitch, dur, vel))
            if do_piano:
                piano += piano_arp(base, root, qual)
            if do_bass:
                bass += soft_bass(base, bass_root,
                                  vel=56 if name == "outro" else 64)
            bar += 1

    total_bars = bar  # 48

    # Final bar: let everything ring out on a held Abmaj9, with one last
    # music-box tonic floating on top.
    last_base = (total_bars - 1) * STEPS
    pad = [p for p in pad if p[0] != last_base]
    box = [n for n in box if n[0] < last_base]      # clear the last bar's box
    bass = [n for n in bass if n[0] != last_base and n[0] != last_base + 8]
    pad.append((last_base, chord("Ab3", "maj9"), STEPS, 48))
    strings.append((last_base, chord("Ab3", "maj9"), STEPS, 28))
    bass.append((last_base, note_to_midi("Ab1"), STEPS, 52))
    box.append((last_base, note_to_midi("Ab5"), 12, 44))

    # Long, loose humanize for a dreamy, un-quantized haze. No swing.
    song.add_part("pad", "pad", pad, humanize_time=12, humanize_vel=8, seed=11)
    song.add_part("strings", "synth_strings", strings,
                  humanize_time=14, humanize_vel=6, seed=13)
    song.add_part("piano", "piano", piano,
                  humanize_time=10, humanize_vel=10, seed=21)
    song.add_part("box", "music_box", box,
                  humanize_time=11, humanize_vel=10, seed=31)
    song.add_part("glock", "glock", glock,
                  humanize_time=9, humanize_vel=8, seed=41)
    song.add_part("bass", "finger_bass", bass,
                  humanize_time=8, humanize_vel=7, seed=51)

    # Gentle half-time lo-fi beat under the middle sections only.
    if drums_start is not None:
        song.add_drums(
            {
                "kick":   "X . . . . . . . . . . . o . . .",
                "rim":    ". . . . . . . . X . . . . . . .",
                "hat":    "x . . . o . . . x . . . o . . .",
                "shaker": "o . o . o . o . o . o . o . o .",
            },
            bars=drums_end - drums_start, start_bar=drums_start,
            swing=0.0, vel=54, humanize_time=10, humanize_vel=12, seed=7,
        )
    return song


def main():
    out = ROOT / "out" / "endless_summer"
    song = build()
    mid = song.save(out.with_suffix(".mid"))
    # Very warm, washed-out master: heavy reverb haze + gentle low-pass for
    # that tape/lo-fi nostalgia, soft top end.
    ogg = render(mid, out.with_suffix(".ogg"),
                 reverb=52, lowpass=12500, bass_gain=3, treble_gain=-3)
    print(f"rendered {ogg}")


if __name__ == "__main__":
    main()
