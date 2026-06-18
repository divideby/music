#!/usr/bin/env python3
"""electropop_op — modern anime-OP electropop in the YOASOBI vein.

Run from the repo root:  ./render.sh electropop_op

160 BPM, C major, the J-pop "Royal Road" progression Fmaj7-G7-Em7-Am7. Bright
acoustic piano stabs, a sawtooth 8th-note arp, a square-lead vocal-ish topline in
the chorus, syncopated synth bass, a synth-string pad, glockenspiel sparkle, and
four-on-the-floor dance drums with a snare build into the chorus.

No distortion guitar — GM renders pianos/synths far more convincingly, which is
what actually sells the modern-OP sound.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from studio import Song, render                      # noqa: E402
from studio.notes import chord, note_to_midi         # noqa: E402

STEPS = 16
ROYAL = [("F3", "maj7"), ("G3", "dom7"), ("E3", "min7"), ("A3", "min7")]
TRIAD = {"F3": ("F4", "maj"), "G3": ("G4", "maj"), "E3": ("E4", "min"), "A3": ("A4", "min")}
BASS = {"F3": "F2", "G3": "G2", "E3": "E2", "A3": "A2"}

# Section layout (bars). Royal Road loops underneath the whole thing.
SECTIONS = (["intro"] * 4 + ["verse"] * 8 + ["pre"] * 4 + ["chorus"] * 8
            + ["verse"] * 4 + ["chorus"] * 8 + ["outro"] * 4)   # 40 bars ~ 60s

# Chorus topline (square lead), a 4-bar hook over F-G-Em-Am. (bar_in_4, step, note, dur)
HOOK = [
    (0, 0, "A4", 2), (0, 2, "C5", 2), (0, 4, "C5", 4), (0, 8, "A4", 2), (0, 10, "G4", 2), (0, 12, "A4", 4),
    (1, 0, "B4", 2), (1, 2, "D5", 2), (1, 4, "D5", 4), (1, 8, "B4", 2), (1, 10, "B4", 2), (1, 12, "D5", 4),
    (2, 0, "E5", 2), (2, 2, "D5", 2), (2, 4, "B4", 4), (2, 8, "G4", 2), (2, 10, "B4", 2), (2, 12, "E5", 2), (2, 14, "D5", 2),
    (3, 0, "C5", 2), (3, 2, "B4", 2), (3, 4, "A4", 4), (3, 8, "E4", 2), (3, 10, "A4", 2), (3, 12, "C5", 4),
]
ARP_VEL = {"intro": 58, "verse": 54, "pre": 66, "chorus": 72, "outro": 62}


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
    song = Song(tempo=160, steps_per_bar=STEPS)

    arp, piano, bass, strings, glock = [], [], [], [], []
    for bar, sec in enumerate(SECTIONS):
        base = bar * STEPS
        root, qual = ROYAL[bar % 4]
        ct = chord(root, qual)                       # four 7th-chord tones

        # Sawtooth arp, an octave up, straight 8ths — the electropop motor.
        seq = [ct[0], ct[1], ct[2], ct[3], ct[1], ct[2], ct[3], ct[0] + 12]
        for k, s in enumerate(range(0, 16, 2)):
            arp.append((base + s, seq[k] + 12, 2, ARP_VEL[sec]))

        # Piano: syncopated chord stabs.
        if sec in ("verse", "pre", "chorus", "outro"):
            for s in (0, 6, 8, 14):
                piano.append((base + s, ct, 2, 84 if s in (0, 8) else 70))

        # Synth bass: bouncy, syncopated, with an octave pop.
        if bar >= 4:
            r = note_to_midi(BASS[root])
            for s, d, off in [(0, 3, 0), (6, 2, 0), (8, 2, 12), (11, 1, 0), (14, 2, 0)]:
                bass.append((base + s, r + off, d, 96 if s == 0 else 82))

        # String pad lifts the chorus/outro.
        if sec in ("chorus", "outro"):
            tr, tq = TRIAD[root]
            strings.append((base + 0, chord(tr, tq), 16, 40))

        # Glock sparkle on intro + chorus.
        if sec in ("intro", "chorus"):
            glock.append((base + 0, ct[-1] + 12, 2, 52))
            glock.append((base + 8, ct[1] + 12, 2, 44))

    lead = []
    for cs in (16, 20, 28, 32):                      # two choruses, hook twice each
        for b4, s, n, d in HOOK:
            lead.append(((cs + b4) * STEPS + s, n, d, 104))

    song.add_part("arp", "saw_lead", arp, seed=51, humanize_time=3, humanize_vel=5)
    song.add_part("piano", "piano", piano, seed=52, humanize_time=4, humanize_vel=6)
    song.add_part("bass", "synth_bass", bass, seed=53, humanize_time=3, humanize_vel=5)
    song.add_part("strings", "synth_strings", strings, seed=54, humanize_time=2, humanize_vel=3)
    song.add_part("glock", "glock", glock, seed=55, humanize_time=3, humanize_vel=4)
    song.add_part("lead", "square_lead", lead, seed=56, humanize_time=4, humanize_vel=5)

    _drums(song)
    return song


def _drums(song):
    KICK = "X . . . X . . . X . . . X . . ."        # four on the floor
    CLAP = ". . . . X . . . . . . . X . . ."        # backbeat 2 & 4
    HAT = "X o x o X o x o X o x o X o x o"          # busy 16th hats
    OPEN = ". . X . . . X . . . X . . . X ."         # offbeat open hats
    BUILD = {"snare": "x x x x x x x x X X X X X X X X",
             "kick": "X . . . X . . . X . . . X . . ."}

    for name, start, length in _blocks(SECTIONS):
        if name == "intro":
            song.add_drums({"kick": KICK, "hat": HAT}, bars=2, start_bar=start + 2,
                           vel=90, seed=7)
        elif name == "verse":
            song.add_drums({"kick": KICK, "clap": CLAP, "hat": HAT},
                           bars=length, start_bar=start, vel=100, seed=7)
        elif name == "pre":
            song.add_drums({"kick": KICK, "clap": CLAP, "hat": HAT},
                           bars=length - 1, start_bar=start, vel=100, seed=7)
            song.add_drums(BUILD, bars=1, start_bar=start + length - 1, vel=98, seed=8)
        elif name == "chorus":
            song.add_drums({"kick": KICK, "clap": CLAP, "hat": HAT, "open_hat": OPEN},
                           bars=length, start_bar=start, vel=106, seed=7)
        elif name == "outro":
            song.add_drums({"kick": KICK, "hat": HAT}, bars=length, start_bar=start,
                           vel=88, seed=7)

    for b in (16, 28, 36):                           # crash on chorus/outro downbeats
        song.add_drums({"crash": "X"}, bars=1, start_bar=b, vel=78, seed=2)


def main():
    out = ROOT / "out" / "electropop_op"
    mid = build().save(out.with_suffix(".mid"))
    ogg = render(mid, out.with_suffix(".ogg"),
                 synth_gain=0.55, reverb=18, lowpass=17500, bass_gain=3, treble_gain=3)
    print(f"rendered {ogg}")


if __name__ == "__main__":
    main()
