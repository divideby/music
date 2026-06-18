"""Guitar amp + cabinet processing via Spotify pedalboard.

Turns a clean DI-ish guitar stem into a heavy amp tone the way real tone is made:
cascading distortion (the gain stage) -> tone EQ -> cabinet impulse-response
convolution -> compression. The cabinet IR convolution is what actually sells
"real guitar" vs a raw GM distortion sample.

Headless, no GUI, no external VST — pedalboard's built-in DSP + Convolution only.
Imported lazily by render.py so the rest of the studio doesn't require pedalboard.
"""

from pathlib import Path

from pedalboard import (Compressor, Convolution, Distortion, Gain,
                        HighpassFilter, LowpassFilter, PeakFilter, Pedalboard)
from pedalboard.io import AudioFile

IR_DIR = Path(__file__).resolve().parent.parent / "irs"


def guitar_board(ir="cab_modern.wav", drive=28.0, cascade=12.0,
                 low_mid=2.5, presence=3.0, body_hz=750, presence_hz=3500,
                 tight_hz=90, rolloff_hz=11000, out_db=-6.0):
    """Heavy rhythm tone: tighten lows -> cascading gain -> tone -> cab -> comp."""
    return Pedalboard([
        HighpassFilter(cutoff_frequency_hz=tight_hz),       # kill flub before gain
        Distortion(drive_db=drive),                          # main gain stage
        Distortion(drive_db=cascade),                        # cascade = fatter
        PeakFilter(cutoff_frequency_hz=body_hz, gain_db=low_mid, q=1.0),
        PeakFilter(cutoff_frequency_hz=presence_hz, gain_db=presence, q=1.4),
        Convolution(str(IR_DIR / ir), mix=1.0),              # the cabinet
        LowpassFilter(cutoff_frequency_hz=rolloff_hz),       # de-fizz
        Compressor(threshold_db=-18, ratio=3.0, attack_ms=5, release_ms=120),
        Gain(gain_db=out_db),
    ])


def lead_board(ir="cab_vintage_bright.wav", drive=20.0, out_db=-8.0):
    """Brighter, less low-mid lead tone."""
    return Pedalboard([
        HighpassFilter(cutoff_frequency_hz=160),
        Distortion(drive_db=drive),
        PeakFilter(cutoff_frequency_hz=2500, gain_db=3.0, q=1.2),
        Convolution(str(IR_DIR / ir), mix=1.0),
        LowpassFilter(cutoff_frequency_hz=12000),
        Gain(gain_db=out_db),
    ])


def apply_board(board, in_wav, out_wav):
    """Run a pedalboard chain over a wav file."""
    with AudioFile(str(in_wav)) as f:
        audio = f.read(f.frames)
        sr = f.samplerate
    out = board(audio, sr)
    with AudioFile(str(out_wav), "w", sr, out.shape[0]) as f:
        f.write(out)
    return out_wav
