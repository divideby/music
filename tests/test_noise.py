import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from studio.noise import white_samples  # noqa: E402


class TestNoise(unittest.TestCase):
    def test_length(self):
        self.assertEqual(len(white_samples(500, seed=0)), 500)

    def test_deterministic_same_seed(self):
        # The project rule: same code/seed -> same audio. sox noise isn't
        # reproducible, so the source must be.
        self.assertEqual(white_samples(1000, seed=7), white_samples(1000, seed=7))

    def test_different_seed_differs(self):
        self.assertNotEqual(white_samples(1000, seed=1), white_samples(1000, seed=2))

    def test_in_range(self):
        self.assertTrue(all(-1.0 <= x <= 1.0 for x in white_samples(2000, seed=3)))


if __name__ == "__main__":
    unittest.main()
