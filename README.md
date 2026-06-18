# music — headless code-first studio

Tracks are written as Python, rendered to audio on the server with no GUI/GPU,
and published to GitHub Pages so you can listen and download in the browser.

**Listen:** https://divideby.github.io/music/

## Stack

- **mido** — build the MIDI from code
- **FluidSynth** + **FluidR3_GM.sf2** — sampled GM instruments (live timbre, not oscillators)
- **sox** + **ffmpeg** — mastering (normalize, warm tone, light reverb) and `.ogg` encode

## Layout

```
studio/        engine — notes, pattern, instruments (pure, tested) + song, render
tracks/<name>/track.py   one declarative script per track
out/           rendered audio (.ogg committed; .wav/.mid ignored)
tests/         unittest for the pure modules + a render smoke test
index.html     the player page served by Pages
```

## Use

```bash
./fetch-soundfont.sh          # one-time: link FluidR3_GM.sf2
./render.sh lofi_intro        # build out/lofi_intro.ogg
python3 -m unittest discover -s tests   # run tests
./publish.sh "add a track"    # commit + push -> Pages rebuilds
```

Listen locally without Pages: `python3 -m http.server` then open
`http://localhost:8000/`.

## Write a new track

Copy `tracks/lofi_intro/track.py`, change the chords / patterns, run
`./render.sh <name>`, add an `<article class="track">` block to `index.html`,
then `./publish.sh`. The studio API:

- `Song(tempo, steps_per_bar)` — 16-step-per-bar grid
- `song.add_part(name, voice, notes, swing=...)` — `notes` are
  `(abs_step, pitch_or_chord, dur_steps, velocity)`
- `song.add_drums({drum: "x . o . X ..."}, bars, swing=...)`
- `render(mid, "out/<name>.ogg")`

Voices and drum names live in `studio/instruments.py`; chords/scales in
`studio/notes.py`.
