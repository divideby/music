"""Pitch helpers: note names <-> MIDI numbers, scales, chords.

Pure module — no I/O, no external binaries. Scientific pitch notation, where
A4 = MIDI 69 = 440 Hz. Bad input raises (never returns silent garbage).
"""

SEMITONE = {
    "C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3, "E": 4, "F": 5,
    "F#": 6, "Gb": 6, "G": 7, "G#": 8, "Ab": 8, "A": 9, "A#": 10, "Bb": 10, "B": 11,
}


def note_to_midi(name):
    """'A4' -> 69. Accepts an int as-is (already a MIDI number)."""
    if isinstance(name, int):
        return name
    s = name.strip()
    # split trailing octave (optionally negative), rest is letter + accidental
    i = len(s)
    while i > 0 and (s[i - 1].isdigit() or s[i - 1] == "-"):
        i -= 1
    letter, octave = s[:i], s[i:]
    if letter not in SEMITONE or octave == "":
        raise ValueError(f"bad note: {name!r}")
    midi = (int(octave) + 1) * 12 + SEMITONE[letter]
    if not 0 <= midi <= 127:
        raise ValueError(f"note out of MIDI range: {name!r} -> {midi}")
    return midi


# Scale formulas as semitone offsets from the root.
SCALES = {
    "major": [0, 2, 4, 5, 7, 9, 11],
    "minor": [0, 2, 3, 5, 7, 8, 10],          # natural minor
    "harmonic_minor": [0, 2, 3, 5, 7, 8, 11],
    "dorian": [0, 2, 3, 5, 7, 9, 10],
    "phrygian": [0, 1, 3, 5, 7, 8, 10],
    "mixolydian": [0, 2, 4, 5, 7, 9, 10],
    "minor_pentatonic": [0, 3, 5, 7, 10],
    "major_pentatonic": [0, 2, 4, 7, 9],
}


def scale(root, mode="major", octaves=1):
    """Return MIDI notes of a scale starting at root, spanning `octaves`."""
    base = note_to_midi(root)
    steps = SCALES[mode]
    out = []
    for o in range(octaves):
        for s in steps:
            out.append(base + 12 * o + s)
    out.append(base + 12 * octaves)  # close on the octave
    return out


# Chord formulas as semitone offsets from the root.
CHORDS = {
    "maj": [0, 4, 7],
    "min": [0, 3, 7],
    "dim": [0, 3, 6],
    "aug": [0, 4, 8],
    "sus2": [0, 2, 7],
    "sus4": [0, 5, 7],
    "5": [0, 7, 12],        # power chord: root + fifth + octave
    "maj7": [0, 4, 7, 11],
    "min7": [0, 3, 7, 10],
    "dom7": [0, 4, 7, 10],
    "min7b5": [0, 3, 6, 10],
    "maj9": [0, 4, 7, 11, 14],
    "min9": [0, 3, 7, 10, 14],
    "add9": [0, 4, 7, 14],
}


def chord(root, quality="maj"):
    """Return MIDI notes for a chord, e.g. chord('C4','maj7') -> [60,64,67,71]."""
    base = note_to_midi(root)
    if quality not in CHORDS:
        raise ValueError(f"unknown chord quality: {quality!r}")
    return [base + s for s in CHORDS[quality]]
