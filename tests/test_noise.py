import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np  # noqa: E402

from studio.noise import droplet_field, white_samples  # noqa: E402


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

    def test_droplets_deterministic(self):
        a = droplet_field(44100, 44100, 400, seed=5)
        b = droplet_field(44100, 44100, 400, seed=5)
        self.assertTrue(np.array_equal(a, b))

    def test_droplets_seed_differs(self):
        a = droplet_field(44100, 44100, 400, seed=5)
        c = droplet_field(44100, 44100, 400, seed=6)
        self.assertFalse(np.array_equal(a, c))

    def test_droplets_are_transient_not_flat(self):
        # Rain != steady noise: a droplet field must be peaky (high crest
        # factor), unlike flat white noise (crest ~ a few).
        f = droplet_field(44100, 44100, 300, seed=1)
        rms = float(np.sqrt(np.mean(f ** 2)))
        crest = float(np.max(np.abs(f))) / (rms or 1e-9)
        self.assertGreater(crest, 8.0)


if __name__ == "__main__":
    unittest.main()
