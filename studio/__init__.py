"""Headless code-first music studio.

Pure helpers (notes, pattern, instruments) carry no side effects and are unit
tested. song builds a standard MIDI file; render turns it into audio via
fluidsynth + sox + ffmpeg. A "track" is a small declarative script that builds a
Song and calls render() — see tracks/<name>/track.py.
"""

from .song import Song
from .render import render, render_layered

__all__ = ["Song", "render", "render_layered"]
