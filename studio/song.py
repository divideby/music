"""Song: assemble parts into a standard MIDI file via mido.

A Song owns a tempo and a 16-step-per-bar grid. Parts are added with high-level
helpers (add_drums / add_part); each gets its own MIDI channel. Drums always go
to channel 9 (GM percussion). save() merges everything into one .mid.

Timing model: one bar = 4 beats. step_ticks = ticks_per_beat * 4 / steps_per_bar.
Swing and humanize are applied as parts are added, so the written MIDI already
grooves — render() just plays it.
"""

from pathlib import Path

from mido import Message, MetaMessage, MidiFile, MidiTrack, bpm2tempo

from . import instruments, pattern
from .notes import note_to_midi


class Song:
    def __init__(self, tempo=72, ticks_per_beat=480, steps_per_bar=16):
        self.tempo = tempo
        self.tpb = ticks_per_beat
        self.spb = steps_per_bar
        self._channels = []   # dicts: name, program, is_drum, chan, events
        self._next_chan = 0

    # ── timing ──────────────────────────────────────────────────────────
    def step_ticks(self):
        return self.tpb * 4 // self.spb

    def _alloc_chan(self):
        c = self._next_chan
        self._next_chan += 1
        if self._next_chan == 9:      # reserve 9 for percussion
            self._next_chan = 10
        return c

    def _add_channel(self, name, program, is_drum, events):
        chan = 9 if is_drum else self._alloc_chan()
        self._channels.append(
            {"name": name, "program": program, "is_drum": is_drum,
             "chan": chan, "events": events}
        )

    # ── parts ───────────────────────────────────────────────────────────
    def add_drums(self, lanes, bars, swing=0.0, vel=100,
                  humanize_time=8, humanize_vel=12, seed=1, start_bar=0):
        """lanes: {drum_name: step_string}. The pattern repeats for `bars` bars,
        starting at `start_bar` (use it to place crashes/fills on a section
        downbeat). Step-string velocity scales (x/X/o) ride on top of `vel`.
        """
        st = self.step_ticks()
        events = []
        for name, patt in lanes.items():
            key = instruments.drum_for(name)
            scales = pattern.steps(patt)
            for b in range(bars):
                for i, scale in enumerate(scales):
                    if scale <= 0:
                        continue
                    bar = start_bar + b
                    start = (bar * self.spb + i) * st + pattern.swing_offset(i, st, swing)
                    v = max(1, min(127, int(vel * scale)))
                    events.append([start, st // 2, key, v])
        events = pattern.humanize(events, seed, humanize_time, humanize_vel)
        self._add_channel("drums", 0, True, events)

    def add_part(self, name, voice, notes, swing=0.0,
                 humanize_time=6, humanize_vel=6, seed=2):
        """Add a melodic/harmonic part.

        notes: list of (abs_step, pitch, dur_steps, velocity) where
          abs_step  — step index from song start (bar*steps_per_bar + step)
          pitch     — a note ('A3'/57) or a list of them for a chord
          dur_steps — length in steps
          velocity  — 1..127
        """
        st = self.step_ticks()
        events = []
        for step, pitch, dur, vel in notes:
            start = step * st + pattern.swing_offset(step, st, swing)
            pitches = pitch if isinstance(pitch, (list, tuple)) else [pitch]
            for p in pitches:
                events.append([start, dur * st, note_to_midi(p), vel])
        events = pattern.humanize(events, seed, humanize_time, humanize_vel)
        self._add_channel(name, instruments.program_for(voice), False, events)

    # ── output ──────────────────────────────────────────────────────────
    def save(self, path):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        mid = MidiFile(ticks_per_beat=self.tpb)

        meta = MidiTrack()
        mid.tracks.append(meta)
        meta.append(MetaMessage("set_tempo", tempo=bpm2tempo(self.tempo)))
        meta.append(MetaMessage("time_signature", numerator=4, denominator=4))

        for ch in self._channels:
            tr = MidiTrack()
            mid.tracks.append(tr)
            tr.append(MetaMessage("track_name", name=ch["name"]))
            if not ch["is_drum"]:
                tr.append(Message("program_change", channel=ch["chan"],
                                  program=ch["program"], time=0))
            msgs = []
            for start, dur, note, vel in ch["events"]:
                msgs.append((start, 1, note, vel, ch["chan"]))       # note_on
                msgs.append((start + dur, 0, note, 0, ch["chan"]))   # note_off
            # sort by time; off (0) before on (1) at the same tick to avoid
            # cutting a re-struck note short
            msgs.sort(key=lambda m: (m[0], m[1]))
            t = 0
            for at, kind, note, vel, chan in msgs:
                delta = at - t
                t = at
                mtype = "note_on" if kind == 1 else "note_off"
                tr.append(Message(mtype, channel=chan, note=note,
                                  velocity=vel, time=delta))
        mid.save(str(path))
        return path
