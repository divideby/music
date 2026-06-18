"""Step-sequencer helpers: parse step strings, apply swing, humanize.

Pure module. A "step string" is whitespace-separated tokens, one per step:
  '.'  rest
  'x'  hit  (velocity scale 1.0)
  'X'  accent (1.25)
  'o'  ghost  (0.5)
steps() returns a list of velocity scales (0.0 == rest). Length = token count.
"""

import random

_TOKENS = {".": 0.0, "x": 1.0, "X": 1.25, "o": 0.5}


def steps(s):
    """'x . X o' -> [1.0, 0.0, 1.25, 0.5]."""
    out = []
    for tok in s.split():
        if tok not in _TOKENS:
            raise ValueError(f"bad step token: {tok!r} in {s!r}")
        out.append(_TOKENS[tok])
    return out


def swing_offset(step_index, step_ticks, amount):
    """Delay odd (off-beat) steps by `amount` of a step. amount in [0, ~0.6]."""
    if amount and step_index % 2 == 1:
        return int(step_ticks * amount)
    return 0


def humanize(events, seed=0, time_ticks=6, vel=8):
    """Deterministically jitter event timing and velocity.

    events: list of [start, dur, note, velocity]. Returns a new list; the same
    seed always yields the same result (no global RNG, so tests are stable).
    """
    rng = random.Random(seed)
    out = []
    for start, dur, note, velocity in events:
        s = max(0, start + rng.randint(-time_ticks, time_ticks))
        v = min(127, max(1, velocity + rng.randint(-vel, vel)))
        out.append([s, dur, note, v])
    return out
