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

import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from studio import Song, render_layered    # noqa: E402
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

    # Each instrument becomes its OWN stem (own Song) so render_layered can
    # mix it individually — panned, balanced, EQ'd, with its own reverb send.
    # Long, loose humanize for a dreamy, un-quantized haze. No swing.
    def one(voice, notes, **hz):
        s = Song(tempo=TEMPO, steps_per_bar=STEPS)
        s.add_part(voice, voice, notes, **hz)
        return s

    stems = {
        "pad":     one("pad", pad, humanize_time=12, humanize_vel=8, seed=11),
        "strings": one("synth_strings", strings,
                       humanize_time=14, humanize_vel=6, seed=13),
        "piano":   one("piano", piano, humanize_time=10, humanize_vel=10, seed=21),
        "box":     one("music_box", box, humanize_time=11, humanize_vel=10, seed=31),
        "glock":   one("glock", glock, humanize_time=9, humanize_vel=8, seed=41),
        "bass":    one("finger_bass", bass, humanize_time=8, humanize_vel=7, seed=51),
    }

    # Gentle half-time lo-fi beat under the middle sections only — its own stem.
    if drums_start is not None:
        drm = Song(tempo=TEMPO, steps_per_bar=STEPS)
        drm.add_drums(
            {
                "kick":   "X . . . . . . . . . . . o . . .",
                "rim":    ". . . . . . . . X . . . . . . .",
                "hat":    "x . . . o . . . x . . . o . . .",
                "shaker": "o . o . o . o . o . o . o . o .",
            },
            bars=drums_end - drums_start, start_bar=drums_start,
            swing=0.0, vel=54, humanize_time=10, humanize_vel=12, seed=7,
        )
        stems["drums"] = drm
    return stems


def pan(p):
    """Constant-power pan of a mono-collapsed stem. p in [-1 (L) .. +1 (R)].

    Collapses the stem to mono, then spreads it across L/R with cos/sin gains
    so total power stays constant as it moves across the field.
    """
    a = (p + 1) / 2 * (math.pi / 2)
    return ["channels", "1", "remix", "-m", f"1v{math.cos(a):.3f}", f"1v{math.sin(a):.3f}"]


# ── Per-stem mix chains (sox effect args). This IS the mix: placement (pan),
# balance (gain dB), tone (EQ/filters), and an individual reverb "send" per
# instrument. reverb args = reverberance HF-damp room-scale stereo pre-delay;
# darker/bigger = hall (pads), brighter/smaller = plate (bells/lead). ───────
FX = {
    # Warm bed: kept stereo for width, rolled-off top, low-mid body, big HALL.
    "pad": ["highpass", "50", "lowpass", "8500", "equalizer", "320", "1q", "2",
            "gain", "-3", "reverb", "62", "45", "100", "100", "18"],
    # Airy upper layer: high-passed above the pad, soft top, even bigger hall.
    "strings": ["highpass", "220", "treble", "2", "gain", "-7",
                "reverb", "66", "35", "100", "100", "22"],
    # Arpeggios: panned LEFT, presence around 2.6 kHz, medium plate.
    "piano": pan(-0.45) + ["highpass", "110", "equalizer", "2600", "1.2q", "1.5",
                           "gain", "-4", "reverb", "34", "28", "55", "100", "6"],
    # Music-box lead: near-centre, forward, bright plate + a soft dreamy slap echo.
    "box": pan(0.12) + ["highpass", "250", "equalizer", "3200", "1q", "2.5",
                        "gain", "1", "echo", "0.85", "0.55", "260", "0.3",
                        "reverb", "42", "22", "55", "100", "0"],
    # Glock twinkle: panned RIGHT (mirrors the piano), soft, bright, long plate.
    "glock": pan(0.5) + ["highpass", "500", "gain", "-9",
                         "reverb", "58", "20", "60", "100", "0"],
    # Bass: centred + MONO, tight low-pass, low-mid bump, glue compression,
    # almost dry (keeps the low end solid, not washy).
    "bass": pan(0.0) + ["lowpass", "3500", "equalizer", "110", "1q", "2",
                        "compand", "0.05,0.3", "6:-42,-32,-18,-10,-6,-5", "-2",
                        "gain", "-2", "reverb", "5"],
    # Drums: stereo, glue compression for punch/evenness, short room.
    "drums": ["compand", "0.005,0.12", "6:-48,-40,-24,-14,-8,-6", "-3",
              "equalizer", "95", "1q", "2", "treble", "1", "gain", "-2",
              "reverb", "20", "30", "40", "100", "0"],
}

# Mix order (purely cosmetic for the sum): beds, support, rhythm, then leads.
ORDER = ["pad", "strings", "piano", "bass", "drums", "box", "glock"]


def main():
    out = ROOT / "out" / "endless_summer"
    songs = build()

    mids, stems = [], []
    for name in ORDER:
        if name not in songs:
            continue
        mid = songs[name].save(out.with_suffix(f".{name}.mid"))
        mids.append(mid)
        stems.append({"mid": mid, "fx": FX[name]})

    # Mix + master. Per-stem chains place/balance/EQ each instrument; the 2-bus
    # master then GLUES the result: warm tone, a light shared room, bus
    # compression to pull the body up (the reverb sends dilute RMS otherwise),
    # then a fast soft-knee "limiter" catching the peaks, and peak-normalize.
    # Kept musical, not brickwalled — it's dreamy ambient, dynamics matter.
    master_fx = [
        "gain", "-n", "-6",                                  # headroom for comp
        "bass", "3", "treble", "-2", "lowpass", "13500",     # warm tone
        "reverb", "10",                                      # light glue room
        # bus glue: gentle ~2:1 above ~-26 dB, with makeup gain
        "compand", "0.15,0.6", "6:-50,-48,-26,-18,-10,-7", "4",
        # fast soft-knee limiter on the peaks
        "compand", "0.002,0.08", "3:-12,-9,-2,-2,0,-1.5", "0",
        "gain", "-n", "-1",                                  # final peak ceiling
    ]
    ogg = render_layered(
        stems, out.with_suffix(".ogg"),
        synth_gain=0.5, master_fx=master_fx,
    )
    for m in mids:
        Path(m).unlink(missing_ok=True)
    print(f"rendered {ogg}")


if __name__ == "__main__":
    main()
