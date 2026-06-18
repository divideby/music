import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from studio.notes import note_to_midi, scale, chord  # noqa: E402


class TestNotes(unittest.TestCase):
    def test_reference_pitch(self):
        self.assertEqual(note_to_midi("A4"), 69)   # 440 Hz
        self.assertEqual(note_to_midi("C-1"), 0)   # lowest MIDI
        self.assertEqual(note_to_midi("G9"), 127)  # highest MIDI

    def test_accidentals_enharmonic(self):
        self.assertEqual(note_to_midi("C#4"), note_to_midi("Db4"))

    def test_int_passthrough(self):
        self.assertEqual(note_to_midi(60), 60)

    def test_bad_input_raises(self):
        for bad in ["H4", "C", "", "C99"]:
            with self.assertRaises(ValueError):
                note_to_midi(bad)

    def test_scale_major(self):
        self.assertEqual(scale("C4", "major"), [60, 62, 64, 65, 67, 69, 71, 72])

    def test_chord_maj7(self):
        self.assertEqual(chord("C4", "maj7"), [60, 64, 67, 71])

    def test_chord_unknown_raises(self):
        with self.assertRaises(ValueError):
            chord("C4", "nope")


if __name__ == "__main__":
    unittest.main()
