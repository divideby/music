#!/usr/bin/env python3
"""synthwave — driving 80s retrowave in A minor.

Run from the repo root:  ./render.sh synthwave

100 BPM, A minor, the classic moody loop Am–F–C–G (i–VI–III–VII) coloured with
add9/maj7 voicings. A lush saw-pad chord bed and a synth-strings wash; a steady
16th-note saw arpeggio (the synthwave "motor") running the whole way through; a
punchy synth-bass octave pulse; a soaring square-lead topline that enters in the
chorus; gated-style backbeat snare/clap and a driving four-on-the-floor kick.

All-synth GM: the FluidR3 saw/square/pad patches sell the retrowave sound far
better than anything that wants distortion.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from studio import Song, render                      # noqa: E402
from studio.notes import chord, note_to_midi         # noqa: E402

STEPS = 16

# i–VI–III–VII in A minor, with lush 80s color (add9 / maj7).
# (chord_root_octave, quality, bass_note, pad_triad_root)
PROG = [
    ("A3", "min", "A1", "A3"),    # i  — Am(add9 via arp)
    ("F3", "maj7", "F1", "F3"),   # VI — Fmaj7
    ("C3", "maj7", "C2", "C3"),   # III— Cmaj7
    ("G3", "maj7", "G1", "G3"),   # VII— Gmaj7
]

# Section layout (bars). The progression loops underneath the whole thing.
SECTIONS = (["intro"] * 4 + ["verse"] * 4 + ["build"] * 4 + ["chorus"] * 8
            + ["chorus"] * 4 + ["outro"] * 2)   # 26 bars ~ 64s

ARP_VEL = {"intro": 70, "verse": 82, "build": 90, "chorus": 100, "outro": 72}

# Chorus topline (square lead): a soaring 4-bar hook over Am–F–C–G.
# (bar_in_4, step, note, dur_steps)
HOOK = [
    (0, 0, "E5", 4), (0, 6, "A5", 2), (0, 8, "G5", 4), (0, 12, "E5", 4),
    (1, 0, "F5", 4), (1, 6, "A5", 2), (1, 8, "C6", 4), (1, 12, "A5", 4),
    (2, 0, "G5", 4), (2, 6, "E5", 2), (2, 8, "G5", 2), (2, 10, "C6", 2), (2, 12, "B5", 4),
    (3, 0, "D5", 4), (3, 6, "G5", 2), (3, 8, "B5", 2), (3, 10, "D6", 2), (3, 12, "G5", 4),
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
    song = Song(tempo=100, steps_per_bar=STEPS)

    arp, pad, strings, bass = [], [], [], []
    for bar, sec in enumerate(SECTIONS):
        base = bar * STEPS
        root, qual, bnote, padroot = PROG[bar % 4]
        ct = chord(root, qual)                        # chord tones (triad or 7th)

        # Saw arpeggio: steady 16ths up the chord, octave up — the motor.
        seq = [ct[0], ct[1], ct[2], (ct[3] if len(ct) > 3 else ct[0] + 12)]
        for s in range(16):
            n = seq[s % 4] + 12 * (1 + (s // 8 % 2))   # alternate octave each half-bar
            arp.append((base + s, n, 1, ARP_VEL[sec]))

        # Lush saw-pad chord bed sustaining the whole bar.
        pad.append((base, chord(padroot, "add9"), 16, 62 if sec in ("intro", "outro") else 74))

        # Synth-strings wash on the bigger sections.
        if sec in ("build", "chorus"):
            strings.append((base, chord(padroot, "maj" if qual.startswith("maj") else "min"),
                            16, 58))

        # Synth bass: punchy octave/root pulse (drops in after the intro).
        if sec != "intro":
            r = note_to_midi(bnote)
            for s, d, off in [(0, 2, 0), (4, 2, 12), (8, 2, 0), (10, 1, 12),
                              (12, 2, 0), (14, 2, 12)]:
                bass.append((base + s, r + off, d, 110 if s == 0 else 96))

    # Square-lead topline: the chorus spans bars 12..23, hook repeats every 4 bars.
    lead = []
    for cs in (12, 16, 20):
        for b4, s, n, d in HOOK:
            lead.append(((cs + b4) * STEPS + s, n, d, 100))

    song.add_part("arp", "saw_lead", arp, seed=61, humanize_time=2, humanize_vel=5)
    song.add_part("pad", "saw_pad", pad, seed=62, humanize_time=2, humanize_vel=3)
    song.add_part("strings", "synth_strings", strings, seed=63, humanize_time=2, humanize_vel=3)
    song.add_part("bass", "synth_bass", bass, seed=64, humanize_time=3, humanize_vel=5)
    song.add_part("lead", "square_lead", lead, seed=65, humanize_time=4, humanize_vel=5)

    _drums(song)
    return song


def _drums(song):
    KICK = "X . . . X . . . X . . . X . . ."          # four on the floor
    SNARE = ". . . . X . . . . . . . X . . ."          # gated-style backbeat 2 & 4
    HAT = ". . x . . . x . . . x . . . x ."            # driving offbeat-ish 16ths
    OPEN = ". . . . . . X . . . . . . . X ."           # offbeat open hats
    BUILD = {"snare": "x x x x x x x x X X X X X X X X",
             "kick": "X . . . X . . . X . . . X . . ."}

    for name, start, length in _blocks(SECTIONS):
        if name == "intro":
            song.add_drums({"kick": KICK, "hat": HAT}, bars=2, start_bar=start + 2,
                           vel=70, seed=7)
        elif name == "verse":
            song.add_drums({"kick": KICK, "snare": SNARE, "hat": HAT},
                           bars=length, start_bar=start, vel=82, seed=7)
        elif name == "build":
            song.add_drums({"kick": KICK, "snare": SNARE, "hat": HAT},
                           bars=length - 1, start_bar=start, vel=84, seed=7)
            song.add_drums(BUILD, bars=1, start_bar=start + length - 1, vel=82, seed=8)
        elif name == "chorus":
            song.add_drums({"kick": KICK, "snare": SNARE, "hat": HAT, "open_hat": OPEN},
                           bars=length, start_bar=start, vel=88, seed=7)
        elif name == "outro":
            song.add_drums({"kick": KICK, "hat": HAT}, bars=length, start_bar=start,
                           vel=68, seed=7)

    for b in (12, 24):                                 # crash on chorus/outro downbeats
        song.add_drums({"crash": "X"}, bars=1, start_bar=b, vel=60, seed=2)


def main():
    out = ROOT / "out" / "synthwave"
    mid = build().save(out.with_suffix(".mid"))
    ogg = render(mid, out.with_suffix(".ogg"),
                 synth_gain=0.72, reverb=22, lowpass=18000, bass_gain=3, treble_gain=3)
    print(f"rendered {ogg}")


if __name__ == "__main__":
    main()
