#!/usr/bin/env python3
"""kolyan_cringe — dark-but-funny half-time trap / hyperpop for the game "Колян".

Run from the repo root:  ./render.sh kolyan_cringe

Scene: the "cringe-content" night — the gang films embarrassing money-flexing
meme videos at home. Manic, ridiculous swagger; hype but stupid.

140 BPM half-time, F minor (phrygian colour). The defining elements:

  * 808 sub bass (synth_bass2) — long sustained low roots (F1 → Db1 → Eb1) that
    ARE the bassline, ringing out and doubling a booming kick. A quick octave
    glide-pop on the downbeat for swagger.
  * Booming kick locked to the 808.
  * Snare + clap on the backbeat (step 8 — the half-time trap snare).
  * Busy 16th hi-hats with ROLL bursts (packed `x` runs = 32nd stutters) and a
    few open-hat accents.
  * A manic, obnoxious square-lead "flex" hook (F-minor-pentatonic, high and
    catchy) doubled by glockenspiel sparkle — the meme-flex energy.
  * A choir stab for dumb drama on the turnarounds.

Structure (~62s @ 140): intro (808 + hook, hats easing in) / main (full beat,
rolls) / breakdown ("drop the beat" — just 808 + hook) / main with a hat-roll
build / outro.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from studio import Song, render                      # noqa: E402
from studio.notes import note_to_midi                # noqa: E402

STEPS = 16

# i–VI–VII in F minor with a phrygian flavour: Fm – Db – Eb.
# One chord per bar, looping in 4-bar groups. (sub-bass root, choir stab tones)
LOOP = [
    ("F1",  ["F3", "Ab3", "C4"]),    # Fm  (i)
    ("F1",  ["F3", "Ab3", "C4"]),
    ("Db1", ["Db3", "F3", "Ab3"]),   # Db  (VI)
    ("Eb1", ["Eb3", "G3", "Bb3"]),   # Eb  (VII)
]

# Section layout (bars). The Fm loop runs underneath the whole thing.
SECTIONS = (["intro"] * 4 + ["main"] * 12 + ["break"] * 4
            + ["main"] * 12 + ["outro"] * 4)          # 36 bars ~ 62s @ 140

# Manic flex hook — high, obnoxious F-minor-pentatonic (F Ab Bb C Eb).
# A short repeating phrase over the 4-bar loop. (bar_in_4, step, note, dur)
HOOK = [
    (0, 0, "C5", 2),  (0, 2, "C5", 2),  (0, 4, "Ab4", 2), (0, 6, "C5", 2),
    (0, 8, "Eb5", 4), (0, 12, "C5", 2), (0, 14, "Ab4", 2),
    (1, 0, "Bb4", 2), (1, 2, "Bb4", 2), (1, 4, "C5", 2),  (1, 8, "Ab4", 4),
    (1, 12, "F4", 4),
    (2, 0, "Db5", 2), (2, 2, "Db5", 2), (2, 4, "Ab4", 2), (2, 6, "Db5", 2),
    (2, 8, "F5", 4),  (2, 12, "Eb5", 2), (2, 14, "Db5", 2),
    (3, 0, "Eb5", 2), (3, 2, "Eb5", 2), (3, 4, "Bb4", 2), (3, 8, "C5", 4),
    (3, 12, "F5", 2), (3, 14, "Eb5", 2),
]

HOOK_VEL = {"intro": 78, "main": 104, "break": 92, "outro": 70}


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

    bass, choir, lead, glock = [], [], [], []
    for bar, sec in enumerate(SECTIONS):
        base = bar * STEPS
        root, stab = LOOP[bar % 4]
        r = note_to_midi(root)

        # 808 sub: long sustained root that rings the whole bar, doubling the
        # kick. A quick octave-up pop on the "and" gives the trap glide swagger.
        bass.append((base + 0, r, 14, 112))
        if sec in ("main", "break", "outro"):
            bass.append((base + 8, r + 12, 2, 88))     # octave pop on the backbeat

        # Choir stab for dumb drama — only on chord changes in the full sections.
        if sec in ("main",) and bar % 4 in (2, 3):
            choir.append((base + 0, stab, 6, 56))

    # Hook: square lead + glock sparkle. Plays through intro/main/break/outro
    # (skip the very first bar of intro so the 808 lands alone first).
    for bar, sec in enumerate(SECTIONS):
        if sec == "outro" and bar % 4 not in (0, 1):
            continue                                    # thin the hook in the outro
        if bar == 0:
            continue
        b4 = bar % 4
        v = HOOK_VEL[sec]
        for hb, s, n, d in HOOK:
            if hb != b4:
                continue
            lead.append((bar * STEPS + s, n, d, v))
            # glock doubles the longer notes an octave up for that obnoxious ping
            if d >= 4 and sec in ("main", "break"):
                glock.append((bar * STEPS + s, note_to_midi(n) + 12, 2, 50))

    song.add_part("sub808", "synth_bass2", bass, seed=11,
                  humanize_time=2, humanize_vel=3)
    song.add_part("choir", "choir", choir, seed=12,
                  humanize_time=3, humanize_vel=5)
    song.add_part("lead", "square_lead", lead, seed=13,
                  humanize_time=4, humanize_vel=8)
    song.add_part("glock", "glock", glock, seed=14,
                  humanize_time=3, humanize_vel=5)

    _drums(song)
    return song


def _drums(song):
    # Half-time trap: kick anchors the 808, snare/clap on step 8 (beat 3).
    KICK  = "X . . . . . X . . . . . X . . ."
    SNARE = ". . . . . . . . X . . . . . . ."
    CLAP  = ". . . . . . . . X . . . . . . ."
    # Busy 16th hats with roll bursts packed into the back half of the bar.
    HAT      = "x . x . x . x x x . x . x x x x"
    HAT_ROLL = "x . x x x x x . x x x x x x x x"   # heavier stutter for the build
    OPEN     = ". . . . . . x . . . . . . . x ."

    for name, start, length in _blocks(SECTIONS):
        if name == "intro":
            # hats ease in: last 2 bars only, no snare yet.
            song.add_drums({"kick": KICK, "hat": HAT},
                           bars=2, start_bar=start + 2, vel=88, seed=7)
        elif name == "main":
            # first chunk steady, then a hat-roll build into the next section.
            steady = length - 1
            song.add_drums(
                {"kick": KICK, "snare": SNARE, "clap": CLAP,
                 "hat": HAT, "open_hat": OPEN},
                bars=steady, start_bar=start, vel=104, seed=7)
            song.add_drums(
                {"kick": KICK, "snare": SNARE, "clap": CLAP, "hat": HAT_ROLL},
                bars=1, start_bar=start + steady, vel=106, seed=8)
        elif name == "break":
            # "drop the beat": just a soft kick + 808 + hook, no snare/hats.
            song.add_drums({"kick": "X . . . . . . . . . . . X . . ."},
                           bars=length, start_bar=start, vel=80, seed=7)
        elif name == "outro":
            song.add_drums({"kick": KICK, "snare": SNARE, "clap": CLAP, "hat": HAT},
                           bars=length, start_bar=start, vel=84, seed=7)

    # crashes on the section downbeats for drama.
    for b in (4, 20, 24, 32):
        song.add_drums({"crash": "X"}, bars=1, start_bar=b, vel=70, seed=2)


def main():
    out = ROOT / "out" / "kolyan_cringe"
    mid = build().save(out.with_suffix(".mid"))
    ogg = render(mid, out.with_suffix(".ogg"),
                 synth_gain=0.55, reverb=12, lowpass=17000,
                 bass_gain=6, treble_gain=3)
    print(f"rendered {ogg}")


if __name__ == "__main__":
    main()
