#!/usr/bin/env python3
"""kolyan_jojo — the menacing "JoJo intrusion" / villain-standoff theme.

For the absurdist crime-comedy anime visual novel "Колян". Slow, ominous,
dramatic dread — a JoJo's-Bizarre-Adventure standoff with the "ゴゴゴ" rumble.

Run from the repo root:  ./render.sh kolyan_jojo

76 BPM, C harmonic minor. The villain color is the leading-tone B-natural over
Cm. Built from: a slow detuned organ/strings/choir/pad swell holding Cm / Ab /
G(maj, the dominant); a deep synth-bass pedal thudding the root C; heartbeat
tom_lo/kick on beats 1 & 3; a climbing trumpet/square-lead motif outlining
C-Eb-G-Ab-B; crash/ride swells on section changes. Slow and spacious — held
notes and silence, an anime stare-down rather than a beat.

Structure (18 bars ~ 60s incl. reverb tail at 76 BPM): a quiet ominous intro
(pad + pedal), a rising tension section (motif climbs, toms enter), a big
menacing peak (full chord swell + crash), and a tail resolving on a held Cm.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from studio import Song, render                      # noqa: E402
from studio.notes import chord                       # noqa: E402

STEPS = 16
TEMPO = 76

# Harmonic progression per bar: (root, quality) for the held pad/strings.
# Cm (i) - Ab (VI) - G major (V, harmonic-minor dominant) - back, ending on Cm.
# Voiced in low-mid register for menace.
PROG = {
    "Cm":  ("C3",  "min"),
    "Ab":  ("Ab2", "maj"),
    "G":   ("G2",  "maj"),
    "Cm5": ("C3",  "5"),     # bare power-chord-ish hit for stings
}

# Bass pedal root per bar (deep, on the downbeats).
BASS = {"Cm": "C1", "Ab": "Ab1", "G": "G1", "Cm5": "C1"}

# Section layout (per bar). Each entry is (section, chord_key).
SECTIONS = (
    [("intro", "Cm")] * 2 + [("intro", "Ab")] * 1 + [("intro", "Cm")] * 1        # 4: quiet ominous
    + [("rise", "Cm")] * 2 + [("rise", "Ab")] * 1 + [("rise", "G")] * 1          # 4: tension builds
    + [("peak", "Cm")] * 1 + [("peak", "Ab")] * 1 + [("peak", "G")] * 1          # 4: menacing peak
    + [("peak", "Cm5")] * 1
    + [("tail", "Cm")] * 4                                                       # 4: resolve on Cm
)   # 16 bars + reverb tail

# The climbing villain motif: C-Eb-G-Ab-B (harmonic minor), rising and stinging.
# (step, note, dur) within a single bar; played sparse, register climbs over time.
MOTIF = [
    (0, "C4", 4), (4, "Eb4", 4), (8, "G4", 4), (12, "Ab4", 3),
]
MOTIF_STING = [(0, "B4", 6), (8, "C5", 8)]   # the leading-tone sting -> tonic


def _blocks(sections):
    out, i = [], 0
    while i < len(sections):
        j = i
        while j < len(sections) and sections[j][0] == sections[i][0]:
            j += 1
        out.append((sections[i][0], i, j - i))
        i = j
    return out


def build():
    song = Song(tempo=TEMPO, steps_per_bar=STEPS)

    pad, strings, choir, organ, bass = [], [], [], [], []
    lead, sting = [], []

    for bar, (sec, ck) in enumerate(SECTIONS):
        base = bar * STEPS
        root, qual = PROG[ck]
        ch = chord(root, qual)

        # ── Pad: a slow detuned swell holding the chord the whole bar. ──
        pad_vel = {"intro": 44, "rise": 56, "peak": 72, "tail": 50}[sec]
        pad.append((base, ch, 16, pad_vel))

        # ── Strings: enter in rise, swell up, an octave up for air. ──
        if sec in ("rise", "peak", "tail"):
            sv = {"rise": 40, "peak": 60, "tail": 38}[sec]
            strings.append((base, [n + 12 for n in ch], 16, sv))

        # ── Choir "ゴゴゴ" rumble: low held vowel, peak only. ──
        if sec == "peak":
            choir.append((base, ch, 16, 54))

        # ── Organ: dark reedy doubling of the chord, rise + peak. ──
        if sec in ("rise", "peak"):
            ov = 38 if sec == "rise" else 50
            organ.append((base, [n - 12 for n in ch], 16, ov))

        # ── Bass pedal: deep root thud on the downbeats (heartbeat with toms). ──
        r = BASS[ck]
        bv = {"intro": 80, "rise": 92, "peak": 104, "tail": 84}[sec]
        # beat 1 and beat 3 — slow, spacious thuds
        bass.append((base + 0, r, 6, bv))
        if sec in ("rise", "peak"):
            bass.append((base + 8, r, 5, bv - 8))
        if sec == "tail" and bar == len(SECTIONS) - 4:
            # final long held tonic pedal under the resolving Cm tail
            bass.append((base, r, 16 * 4, 78))

    # ── Climbing villain motif (trumpet) — enters in rise, climbs over bars. ──
    rise_bars = [b for b, (s, _) in enumerate(SECTIONS) if s == "rise"]
    for idx, bar in enumerate(rise_bars):
        base = bar * STEPS
        oct_up = 12 * (idx // 4)   # climb a register as the section repeats
        for step, n, dur in MOTIF:
            # only the front of each bar, leave space; velocity grows
            lead.append((base + step, _shift(n, oct_up), dur,
                         60 + idx * 3))

    # ── Square-lead sting on each peak chord-change: the B-natural -> C. ──
    peak_bars = [b for b, (s, _) in enumerate(SECTIONS) if s == "peak"]
    for bar in peak_bars[::2]:        # every other peak bar, leave space
        base = bar * STEPS
        for step, n, dur in MOTIF_STING:
            sting.append((base + step, n, dur, 92))

    song.add_part("pad", "pad", pad, seed=11, humanize_time=2, humanize_vel=3)
    song.add_part("strings", "synth_strings", strings, seed=12,
                  humanize_time=2, humanize_vel=3)
    song.add_part("choir", "choir", choir, seed=13, humanize_time=2, humanize_vel=3)
    song.add_part("organ", "rock_organ", organ, seed=14, humanize_time=2, humanize_vel=3)
    song.add_part("bass", "synth_bass", bass, seed=15, humanize_time=3, humanize_vel=5)
    song.add_part("lead", "trumpet", lead, seed=16, humanize_time=4, humanize_vel=6)
    song.add_part("sting", "square_lead", sting, seed=17, humanize_time=3, humanize_vel=5)

    _drums(song)
    return song


def _shift(name, semis):
    """Shift a note name up by `semis` semitones, returning the MIDI int."""
    from studio.notes import note_to_midi
    return note_to_midi(name) + semis


def _drums(song):
    # Heartbeat: deep tom + kick on beats 1 and 3 (steps 0 and 8). Sparse.
    HEART_KICK = "X . . . . . . . X . . . . . . ."
    HEART_TOM  = "x . . . . . . . o . . . . . . ."

    for name, start, length in _blocks(SECTIONS):
        if name == "intro":
            # very sparse — just a single tom thud per bar, faint
            song.add_drums({"tom_lo": "X . . . . . . . . . . . . . . ."},
                           bars=length, start_bar=start, vel=66, seed=3)
        elif name == "rise":
            song.add_drums({"kick": HEART_KICK, "tom_lo": HEART_TOM},
                           bars=length, start_bar=start, vel=88, seed=3)
            # a building low tom roll on the last bar of each 4-bar rise block
        elif name == "peak":
            song.add_drums({"kick": HEART_KICK, "tom_lo": HEART_TOM},
                           bars=length, start_bar=start, vel=104, seed=3)
        elif name == "tail":
            # one final heartbeat, then let it ring
            song.add_drums({"kick": "X . . . . . . . . . . . . . . ."},
                           bars=2, start_bar=start, vel=80, seed=3)

    # Timpani-like low tom roll as a build into the peak.
    peak_start = next(s for n, s, _ in _blocks(SECTIONS) if n == "peak")
    ROLL = "x x o o x x o o X X X X X X X X"
    song.add_drums({"tom_lo": ROLL}, bars=1, start_bar=peak_start - 1,
                   vel=96, seed=4)

    # Crash / ride swells on section changes (peak downbeats) + the final hit.
    for n, s, _ in _blocks(SECTIONS):
        if n == "peak":
            song.add_drums({"crash": "X"}, bars=1, start_bar=s, vel=84, seed=2)
    # ride shimmer through the peak for dread
    song.add_drums({"ride": "x . . . x . . . x . . . x . . ."},
                   bars=8, start_bar=peak_start, vel=58, seed=5)
    # final crash on the tail downbeat
    tail_start = next(s for n, s, _ in _blocks(SECTIONS) if n == "tail")
    song.add_drums({"crash": "X"}, bars=1, start_bar=tail_start, vel=90, seed=2)


def main():
    out = ROOT / "out" / "kolyan_jojo"
    mid = build().save(out.with_suffix(".mid"))
    # Heavy, wide, dark cinematic master.
    ogg = render(mid, out.with_suffix(".ogg"),
                 synth_gain=0.6, reverb=40, lowpass=15000,
                 bass_gain=4, treble_gain=0)
    print(f"rendered {ogg}")


if __name__ == "__main__":
    main()
