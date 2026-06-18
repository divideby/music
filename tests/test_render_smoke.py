"""Smoke test: a tiny song renders to a non-empty ogg.

Skips if the audio binaries / soundfont aren't installed, so the pure-Python
tests still run anywhere.
"""

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from studio import Song, render                       # noqa: E402
from studio.render import _find_soundfont             # noqa: E402

HAVE_BINS = all(shutil.which(b) for b in ("fluidsynth", "sox", "ffmpeg"))
try:
    _find_soundfont()
    HAVE_SF = True
except RuntimeError:
    HAVE_SF = False


@unittest.skipUnless(HAVE_BINS and HAVE_SF, "audio toolchain not installed")
class TestRenderSmoke(unittest.TestCase):
    def test_two_bars_render(self):
        song = Song(tempo=90, steps_per_bar=16)
        song.add_part("p", "piano",
                      [(0, ["C4", "E4", "G4"], 8, 80), (16, "C5", 8, 80)])
        song.add_drums({"kick": "x . . . x . . ."}, bars=2)
        with tempfile.TemporaryDirectory() as d:
            mid = song.save(Path(d) / "t.mid")
            ogg = render(mid, Path(d) / "t.ogg")
            self.assertTrue(ogg.exists())
            self.assertGreater(ogg.stat().st_size, 1000)


if __name__ == "__main__":
    unittest.main()
