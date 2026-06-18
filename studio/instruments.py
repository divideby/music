"""Abstract voice names -> General MIDI program numbers / drum notes.

Pure module. Keeps tracks readable ('rhodes', 'kick') instead of magic GM ints.
Percussion lives on MIDI channel 10 (0-indexed 9); DRUMS maps names to GM keys.
"""

# Voice name -> GM program (0-indexed).
PROGRAMS = {
    "piano": 0,
    "rhodes": 4,        # electric piano 1 — the lofi staple
    "epiano": 5,
    "harpsichord": 6,
    "vibes": 11,
    "organ": 19,
    "nylon": 24,
    "steel": 25,
    "jazz_guitar": 26,
    "clean_guitar": 27,
    "finger_bass": 33,
    "pick_bass": 34,
    "fretless": 35,
    "synth_bass": 38,
    "strings": 48,
    "ensemble": 49,
    "choir": 52,
    "trumpet": 56,
    "sax": 65,
    "flute": 73,
    "pad": 89,           # warm pad
}

# Drum name -> GM percussion key number.
DRUMS = {
    "kick": 36,
    "rim": 37,
    "snare": 38,
    "clap": 39,
    "hat": 42,           # closed hi-hat
    "pedal_hat": 44,
    "open_hat": 46,
    "tom_lo": 45,
    "tom_mid": 47,
    "tom_hi": 50,
    "crash": 49,
    "ride": 51,
    "tambourine": 54,
    "shaker": 70,
}


def program_for(voice):
    if voice not in PROGRAMS:
        raise ValueError(f"unknown voice: {voice!r}")
    return PROGRAMS[voice]


def drum_for(name):
    if name not in DRUMS:
        raise ValueError(f"unknown drum: {name!r}")
    return DRUMS[name]
