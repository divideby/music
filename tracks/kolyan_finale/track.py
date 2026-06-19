#!/usr/bin/env python3
"""kolyan_finale — circus "oom-pah" apotheosis of stupidity.

Grand finale for the absurdist crime-comedy VN "Колян": triumphant, silly,
victory-of-the-idiots energy. 128 BPM, C major, 16 steps/bar.

The defining groove is the oom-pah: a tuba-ish bass thumps the chord ROOT on
the strong beats (steps 0,4,8,12) while an organ stabs the off-beats
(steps 2,6,10,14) — the classic carousel/march bounce. A goofy trumpet fanfare
states a big dumb hook, doubled an octave up by square-lead and sparkled with
glockenspiel/music-box; marimba runs add the clown-shuffle. Marching circus kit
with snare rolls, tom fills, tambourine and crashes; a drum-roll + cymbal build
slams into the final restatement and a button C-major hit.

Run from the repo root:  ./render.sh kolyan_finale
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from studio import Song, render                      # noqa: E402
from studio.notes import chord, note_to_midi         # noqa: E402

STEPS = 16

# I–vi–IV–V in C major (C–Am–F–G): the bright, triumphant circus turnaround.
# (root-for-bass, triad-root-for-stab, quality)
PROG = [("C2", "C4", "maj"), ("A1", "A3", "min"),
        ("F2", "F3", "maj"), ("G2", "G3", "maj")]

# Section layout (bars). PROG loops underneath the whole thing. ~31 bars ≈ 64s.
SECTIONS = (["intro"] * 2          # fanfare: crash + roll, no full band yet
            + ["verse"] * 8        # goofy theme stated
            + ["build"] * 4        # bigger restatement, countermelody
            + ["chorus"] * 8       # triumphant hook, octave-up double
            + ["bridge"] * 4       # carousel breakdown, drum-roll build
            + ["final"] * 4        # final hook restatement
            + ["button"] * 1)      # big C-major button hit

# The big dumb hook, a 4-bar fanfare over C–Am–F–G. (bar_in_4, step, note, dur)
# Lots of arpeggio runs and a triumphant repeated motif.
HOOK = [
    # bar 0 — C: triumphant rising arpeggio to the high G, the "victory" motif
    (0, 0, "G4", 2), (0, 2, "G4", 2), (0, 4, "C5", 2), (0, 6, "E5", 2),
    (0, 8, "G5", 4), (0, 12, "E5", 2), (0, 14, "C5", 2),
    # bar 1 — Am: cheeky little turn
    (1, 0, "A4", 2), (1, 2, "A4", 2), (1, 4, "C5", 2), (1, 6, "E5", 2),
    (1, 8, "A5", 4), (1, 12, "G5", 2), (1, 14, "E5", 2),
    # bar 2 — F: galloping run up
    (2, 0, "F4", 2), (2, 2, "A4", 2), (2, 4, "C5", 2), (2, 6, "F5", 2),
    (2, 8, "A5", 2), (2, 10, "F5", 2), (2, 12, "C5", 2), (2, 14, "A4", 2),
    # bar 3 — G: build the tension then resolve home next loop
    (3, 0, "G4", 2), (3, 2, "B4", 2), (3, 4, "D5", 2), (3, 6, "G5", 2),
    (3, 8, "B5", 2), (3, 10, "D6", 2), (3, 12, "B5", 2), (3, 14, "G5", 2),
]

# A second-voice countermelody for the build/final (a sixth/third below-ish).
COUNTER = [
    (0, 0, "E4", 4), (0, 8, "C4", 4),
    (1, 0, "C4", 4), (1, 8, "A3", 4),
    (2, 0, "A3", 4), (2, 8, "C4", 4),
    (3, 0, "D4", 4), (3, 8, "B3", 4),
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
    song = Song(tempo=128, steps_per_bar=STEPS)

    oom, pah, organ, glock, mbox, marimba = [], [], [], [], [], []
    for bar, sec in enumerate(SECTIONS):
        base = bar * STEPS
        broot, troot, qual = PROG[bar % 4]
        triad = chord(troot, qual)

        if sec == "intro":
            # Fanfare intro: only a sustained organ pedal + sparkle, band waits.
            organ.append((base + 0, chord("C3", "maj"), 16, 52))
            glock.append((base + 0, note_to_midi("G5"), 4, 56))
            continue
        if sec == "button":
            # Big final C-major hit — everything slams the chord and holds.
            oom.append((base + 0, note_to_midi("C2"), 16, 118))
            organ.append((base + 0, chord("C3", "maj") + chord("C4", "maj"), 16, 100))
            glock.append((base + 0, note_to_midi("C6"), 16, 80))
            continue

        loud = sec in ("chorus", "final")
        bvel = 112 if loud else 100
        pvel = 92 if loud else 80

        # ── OOM: tuba-ish bass thumps the ROOT on the strong beats (0,4,8,12).
        r = note_to_midi(broot)
        for s in (0, 4, 8, 12):
            # alternate root / fifth-up for the classic oom bounce
            off = 0 if s in (0, 8) else 7
            oom.append((base + s, r + off, 4, bvel if s == 0 else bvel - 8))

        # ── PAH: organ chord stabs on the OFF-beats (2,6,10,14).
        for s in (2, 6, 10, 14):
            pah.append((base + s, triad, 2, pvel))

        # ── Carousel organ pad sustains under the band (fills the gaps -> fuller mix).
        if sec in ("verse", "build", "chorus", "final"):
            organ.append((base + 0, triad, 16, 42 if sec == "verse" else 48))

        # ── Marimba clown-shuffle run (offbeat 8ths) keeps it busy & silly.
        if sec in ("verse", "build", "chorus", "final"):
            seq = [triad[0], triad[1], triad[2], triad[1]]
            for k, s in enumerate((1, 5, 9, 13)):
                marimba.append((base + s, seq[k % 4] + 12, 2, 60 if loud else 54))

        # ── Glock sparkle on chord downbeats in the big sections.
        if sec in ("chorus", "final"):
            glock.append((base + 0, triad[-1] + 12, 2, 58))
            glock.append((base + 8, triad[1] + 12, 2, 50))

        # ── Music-box top sparkle in the final restatement.
        if sec == "final":
            mbox.append((base + 4, triad[-1] + 24, 2, 46))
            mbox.append((base + 12, triad[0] + 24, 2, 42))

    # ── Trumpet fanfare hook + square-lead octave double + countermelody.
    trumpet, lead, counter = [], [], []
    HOOK_STARTS = [(2, 104), (6, 108)]      # verse: two statements (bars 2,6)
    HOOK_STARTS += [(10, 110)]              # build: one statement (+counter)
    HOOK_STARTS += [(14, 118), (18, 120)]   # chorus: two statements (+oct double)
    HOOK_STARTS += [(26, 126)]              # final: one statement (full)
    OCT_DOUBLE = {14, 18, 26}
    COUNTER_AT = {10, 14, 18, 26}

    for start, vel in HOOK_STARTS:
        for b4, s, n, d in HOOK:
            at = (start + b4) * STEPS + s
            trumpet.append((at, n, d, vel))
            if start in OCT_DOUBLE:
                lead.append((at, note_to_midi(n) + 12, d, vel - 26))
        if start in COUNTER_AT:
            for b4, s, n, d in COUNTER:
                at = (start + b4) * STEPS + s
                counter.append((at, n, d, vel - 30))

    song.add_part("oom", "synth_bass", oom, seed=11, humanize_time=4, humanize_vel=6)
    song.add_part("pah", "organ", pah, seed=12, humanize_time=3, humanize_vel=8)
    song.add_part("organ_pad", "rock_organ", organ, seed=13, humanize_time=2, humanize_vel=4)
    song.add_part("marimba", "marimba", marimba, seed=14, humanize_time=4, humanize_vel=7)
    song.add_part("glock", "glock", glock, seed=15, humanize_time=3, humanize_vel=5)
    song.add_part("music_box", "music_box", mbox, seed=16, humanize_time=4, humanize_vel=5)
    song.add_part("trumpet", "trumpet", trumpet, seed=17, humanize_time=5, humanize_vel=7)
    song.add_part("lead", "square_lead", lead, seed=18, humanize_time=5, humanize_vel=6)
    song.add_part("counter", "trumpet", counter, seed=19, humanize_time=5, humanize_vel=6)

    _drums(song)
    return song


def _drums(song):
    # Marching/circus kit. Kick on the beat, snare backbeat with circus flams.
    KICK = "X . . . x . . . X . . . x . . ."
    SNARE = ". . x . X . . x . . x . X . x ."     # marching snare chatter
    SNARE_BIG = "x . x . X . x . x . x . X . x x"  # busier for the big sections
    HAT = "x . x . x . x . x . x . x . x ."
    TAMB = ". . X . . . X . . . X . . . X ."      # circus tambourine on offs
    ROLL = "x x x x x x x x X X X X X X X X"       # drum-roll build

    for name, start, length in _blocks(SECTIONS):
        if name == "intro":
            # opening crash, then a snare roll swelling across the 2 fanfare bars
            song.add_drums({"crash": "X"}, bars=1, start_bar=start, vel=92, seed=2)
            song.add_drums({"snare": "x . . . x . . . x . x . x x x x"},
                           bars=1, start_bar=start, vel=66, seed=3)
            song.add_drums({"snare": "x x x x x x x x X X X X X X X X"},
                           bars=1, start_bar=start + 1, vel=78, seed=3)
        elif name == "verse":
            song.add_drums({"kick": KICK, "snare": SNARE, "hat": HAT, "tambourine": TAMB},
                           bars=length, start_bar=start, vel=98, seed=4)
        elif name == "build":
            song.add_drums({"kick": KICK, "snare": SNARE_BIG, "hat": HAT,
                            "tambourine": TAMB}, bars=length, start_bar=start,
                           vel=104, seed=4)
        elif name == "chorus":
            song.add_drums({"kick": KICK, "snare": SNARE_BIG, "hat": HAT,
                            "tambourine": TAMB}, bars=length, start_bar=start,
                           vel=110, seed=5)
        elif name == "bridge":
            # carousel breakdown then a big drum-roll + tom fill build
            song.add_drums({"kick": KICK, "tambourine": TAMB},
                           bars=length - 1, start_bar=start, vel=92, seed=4)
            song.add_drums({"snare": ROLL,
                            "tom_lo": ". . . . . . . . X . X . X . X .",
                            "tom_mid": ". . . . . . . . . X . X . X . X"},
                           bars=1, start_bar=start + length - 1, vel=106, seed=6)
        elif name == "final":
            song.add_drums({"kick": KICK, "snare": SNARE_BIG, "hat": HAT,
                            "tambourine": TAMB}, bars=length, start_bar=start,
                           vel=112, seed=5)
        elif name == "button":
            # one decisive crash + kick on the final hit
            song.add_drums({"crash": "X", "kick": "X", "snare": "X"},
                           bars=1, start_bar=start, vel=118, seed=2)

    # Crash accents on every big section downbeat.
    for b in (2, 10, 14, 18, 26):
        song.add_drums({"crash": "X"}, bars=1, start_bar=b, vel=84, seed=2)


def main():
    out = ROOT / "out" / "kolyan_finale"
    mid = build().save(out.with_suffix(".mid"))
    ogg = render(mid, out.with_suffix(".ogg"),
                 synth_gain=0.62, reverb=20, lowpass=17000, bass_gain=3, treble_gain=3)
    print(f"rendered {ogg}")


if __name__ == "__main__":
    main()
