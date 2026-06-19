#!/usr/bin/env python3
"""trap — dark half-time trap / hip-hop.

Run from the repo root:  ./render.sh trap

140 BPM, half-time feel (snare/clap on beat 3 = step 8), C minor with a
phrygian-flavoured i–VI–VII loop (Cm–Ab–Bb). The defining elements:

  * 808 sub bass (synth_bass2) — long sustained low roots that ARE the bassline,
    pitched to each chord and ringing out, doubling the booming kick.
  * Booming kick locked to the 808.
  * Snare + clap on the backbeat (step 8 — the half-time snare).
  * Busy 16th hi-hats with bursts of rolls (doubled / 32nd-feel stutters) and a
    few open-hat accents — the trap signature.
  * A dark, eerie music-box loop as the topline, with a synth-strings pad for
    atmosphere.

Structure (~60s @ 140): intro (808 + melody) / main (full beat, rolls) /
breakdown (drop hats, just 808 + melody) / main / outro.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from studio import Song, render                      # noqa: E402
from studio.notes import note_to_midi                # noqa: E402

STEPS = 16

# i–VI–VII in C minor: Cm – Ab – Bb. One chord per bar, looping.
# (sub-bass root, pad chord tones)
LOOP = [
    ("C1",  ["C3", "Eb3", "G3"]),    # Cm  (i)
    ("C1",  ["C3", "Eb3", "G3"]),
    ("Ab0", ["Ab2", "C3", "Eb3"]),   # Ab  (VI)
    ("Bb0", ["Bb2", "D3", "F3"]),    # Bb  (VII)
]

# Section layout (bars). The Cm loop runs underneath the whole thing. 40 bars.
SECTIONS = (["intro"] * 4 + ["main"] * 12 + ["break"] * 4
            + ["main"] * 12 + ["outro"] * 4)          # 36 bars ~ 62s @ 140

# Dark eerie music-box motif — a short looping phrase over the 4-bar loop.
# (bar_in_4, step, note, dur)  — C minor / phrygian colour.
MOTIF = [
    (0, 0, "G4", 4),  (0, 6, "Eb4", 2), (0, 10, "C4", 4),
    (1, 0, "D4", 2),  (1, 4, "Eb4", 4), (1, 12, "G4", 2),
    (2, 0, "Ab4", 4), (2, 8, "G4", 2),  (2, 12, "Eb4", 4),
    (3, 0, "F4", 2),  (3, 4, "D4", 2),  (3, 8, "Bb4", 4), (3, 14, "G4", 2),
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
    song = Song(tempo=140, steps_per_bar=STEPS)

    sub, pad, glock = [], [], []
    for bar, sec in enumerate(SECTIONS):
        base = bar * STEPS
        root, padtones = LOOP[bar % 4]

        # 808 sub bass: long sustained root that rings out, plus a couple of
        # rhythmic re-hits with a slide-feel octave pop. This is the bassline.
        r = note_to_midi(root)
        sub.append((base + 0, r, 12, 118))            # the long boom on the 1
        sub.append((base + 8, r, 6, 104))             # re-hit under the snare
        if sec in ("main", "outro"):
            sub.append((base + 14, r + 12, 1, 90))    # little octave grace pop

        # Pad: low, airy strings for atmosphere (not in the sparse intro head).
        if sec in ("main", "break", "outro"):
            v = 34 if sec == "break" else 30
            pad.append((base + 0, [note_to_midi(p) for p in padtones], 16, v))

        # Music-box motif loops everywhere except the very first intro bar.
        if bar >= 1:
            for b4, s, n, d in MOTIF:
                if b4 == bar % 4:
                    vel = 58 if sec == "break" else 50
                    glock.append((base + s, note_to_midi(n), d, vel))

    song.add_part("sub808", "synth_bass2", sub, seed=41,
                  humanize_time=2, humanize_vel=4)
    song.add_part("pad", "synth_strings", pad, seed=42,
                  humanize_time=2, humanize_vel=3)
    song.add_part("motif", "music_box", glock, seed=43,
                  humanize_time=4, humanize_vel=6)

    _drums(song)
    return song


def _drums(song):
    # Half-time: kick on 1 (+ syncopated ghosts), snare/clap on step 8 (beat 3).
    KICK   = "X . . . . . X . X . . . . . X ."
    SNARE  = ". . . . . . . . X . . . . . . ."   # the big half-time backbeat
    CLAP   = ". . . . . . . . X . . . . . . ."   # layered with the snare

    # Busy 16th hats with roll bursts. Doubled/tripled chars on one lane read as
    # the same 16th step velocity-scaled; for true rolls we pack a 32nd-feel by
    # adding extra hat lanes is overkill — instead vary intensity across the bar
    # with x/X and a stutter cluster near the end.
    HAT_A  = "x . x x x . x . x x x . x x x x"   # steady with end-of-bar roll
    HAT_B  = "x x x . x . x x x . x x x x x x"   # busier, leading roll
    OPEN   = ". . . . . . . . . . . . . . X ."   # open-hat accent before bar end

    # A faster 32nd-style roll lane is faked with a second hat pattern that the
    # render layers (same key); using add_drums twice on the hat lane stacks hits.
    ROLL   = ". . . . . . . . . . . . x x x x"   # extra stutter under HAT roll

    for name, start, length in _blocks(SECTIONS):
        if name == "intro":
            # Last 2 intro bars: just hats easing in (build feel), no snare yet.
            song.add_drums({"hat": "x . x . x . x . x . x . x x x x"},
                           bars=2, start_bar=start + 2, vel=70, seed=11)
        elif name in ("main", "outro"):
            v = 100 if name == "main" else 88
            for b in range(length):
                hat = HAT_B if b % 4 == 3 else HAT_A     # busier into the turnaround
                lanes = {"kick": KICK, "snare": SNARE, "clap": CLAP,
                         "hat": hat, "open_hat": OPEN}
                song.add_drums(lanes, bars=1, start_bar=start + b, vel=v, seed=7)
                # Extra roll stutter on the last bar of each 4-bar group.
                if b % 4 == 3:
                    song.add_drums({"hat": ROLL}, bars=1, start_bar=start + b,
                                   vel=v + 6, seed=8)
        elif name == "break":
            # Breakdown: drop the hats/kick, leave 808 + melody breathing, with a
            # rising hi-hat roll on the last bar building back into the drop.
            song.add_drums({"snare": SNARE, "clap": CLAP},
                           bars=length - 1, start_bar=start, vel=86, seed=7)
            BUILD = "x x x x x x x x x x x x x x x x"     # 16th roll
            song.add_drums({"hat": BUILD}, bars=1, start_bar=start + length - 1,
                           vel=78, seed=9)
            song.add_drums({"hat": BUILD}, bars=1, start_bar=start + length - 1,
                           vel=96, seed=10)               # double up = denser roll

    # Crash on the drop downbeats (back into main after intro / break).
    for b in (4, 20):
        song.add_drums({"crash": "X"}, bars=1, start_bar=b, vel=72, seed=2)


def main():
    out = ROOT / "out" / "trap"
    mid = build().save(out.with_suffix(".mid"))
    ogg = render(mid, out.with_suffix(".ogg"),
                 synth_gain=0.6, reverb=12, lowpass=17000,
                 bass_gain=6, treble_gain=3)
    print(f"rendered {ogg}")


if __name__ == "__main__":
    main()
