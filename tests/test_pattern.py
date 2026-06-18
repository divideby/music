import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from studio import pattern  # noqa: E402


class TestPattern(unittest.TestCase):
    def test_steps_parse(self):
        self.assertEqual(pattern.steps("x . X o"), [1.0, 0.0, 1.25, 0.5])

    def test_steps_length(self):
        self.assertEqual(len(pattern.steps("x . " * 8)), 16)

    def test_steps_bad_token(self):
        with self.assertRaises(ValueError):
            pattern.steps("x . z")

    def test_swing_only_offbeats(self):
        st = 120
        self.assertEqual(pattern.swing_offset(0, st, 0.5), 0)    # downbeat unmoved
        self.assertEqual(pattern.swing_offset(1, st, 0.5), 60)   # offbeat delayed
        self.assertEqual(pattern.swing_offset(1, st, 0.0), 0)    # no swing

    def test_humanize_deterministic(self):
        events = [[0, 120, 60, 90], [120, 120, 64, 90]]
        a = pattern.humanize(events, seed=42)
        b = pattern.humanize(events, seed=42)
        self.assertEqual(a, b)
        self.assertNotEqual(a, pattern.humanize(events, seed=43))

    def test_humanize_velocity_in_range(self):
        events = [[0, 120, 60, 1], [0, 120, 60, 127]]
        for _, _, _, v in pattern.humanize(events, seed=1, vel=30):
            self.assertTrue(1 <= v <= 127)

    def test_humanize_no_negative_start(self):
        events = [[2, 120, 60, 90]]
        for s, _, _, _ in pattern.humanize(events, seed=5, time_ticks=50):
            self.assertGreaterEqual(s, 0)


if __name__ == "__main__":
    unittest.main()
