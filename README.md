# music — headless code-first studio

> [!NOTE]
> **Archived / read-only.** The reusable studio **skills** now live in
> [`divideby/skills`](https://github.com/divideby/skills) (install with
> `npx skills add divideby/skills`) — the engine and pipeline scripts ship
> bundled inside the `writing-music` skill there. This repo (engine source,
> tracks, renders) is kept for history; the live site keeps serving its last
> deploy. To resume active work, `gh repo unarchive divideby/music`.

Tracks are written as Python, rendered to audio on the server with no GUI/GPU,
and published online (Vercel) so you can listen and download in the browser.

> **For agents / contributors:** read [CLAUDE.md](CLAUDE.md) for conventions and
> gotchas, and [docs/guitar-tone.md](docs/guitar-tone.md) for the guitar-tone
> ladder (sox → pedalboard+cab IR → NAM) and how to verify tone with no playback.

**Listen:** https://music-psi-lovat.vercel.app

Direct file (download / hotlink): `https://cdn.jsdelivr.net/gh/divideby/music@main/out/lofi_intro.ogg`

> Hosted on Vercel, not GitHub Pages: the `divideby.github.io` account has the
> custom domain `divideby.ru`, so GitHub 301-redirects every `divideby.github.io/*`
> project page to `divideby.ru/*` (Cloudflare), which doesn't serve this repo.
> Vercel gives a clean working URL; jsDelivr serves the raw `.ogg` straight from git.

## Stack

- **mido** — build the MIDI from code
- **FluidSynth** + **FluidR3_GM.sf2** — sampled GM instruments (live timbre, not oscillators)
- **sox** + **ffmpeg** — mastering (normalize, warm tone, light reverb) and `.ogg` encode
- **pedalboard** (`pip install pedalboard`) — guitar amp/cab modeling: render a clean
  GM guitar as a DI, then distortion → **cabinet impulse-response convolution** →
  compression (see `studio/amp.py`, IRs in `irs/`). The cab IR is what de-"midis"
  a distorted tone. Used by `tracks/modern_rock_amp` (A/B against `modern_rock`).
- **waveny + NAM** (top rung) — a real **Neural Amp Modeler** capture for the guitar
  amp. Clean DI → `waveny` (a `.nam` WaveNet model of a high-gain amp) → cab IR. See
  `studio/nam.py` and `tracks/modern_rock_nam`. Setup: `./fetch-nam.sh` for the models,
  and build the `waveny` CLI (instructions in that script). NAM is mono / 24-bit /
  48 kHz with a quiet `head_scale` — quirks and the "no overdrive" fix are documented
  in [docs/guitar-tone.md](docs/guitar-tone.md).

## Layout

```
studio/        engine — notes, pattern, instruments (pure, tested) + song, render
tracks/<name>/track.py   one declarative script per track
out/           rendered audio (.ogg committed; .wav/.mid ignored)
tests/         unittest for the pure modules + a render smoke test
index.html     the player page served by Vercel
irs/           cabinet impulse responses · nam_models/ NAM captures (gitignored)
docs/          guitar-tone.md (the tone ladder) + superpowers/specs (design)
```

## Use

```bash
./fetch-soundfont.sh          # one-time: link FluidR3_GM.sf2
./render.sh lofi_intro        # build out/lofi_intro.ogg
python3 -m unittest discover -s tests   # run tests
./publish.sh "add a track"    # commit + push to git AND deploy to Vercel
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
