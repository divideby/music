# CLAUDE.md — music studio

Headless, code-first music studio. Tracks are written as Python, rendered to
audio on the server (no GUI/GPU), published online to listen/download.

**Live:** https://music-psi-lovat.vercel.app  ·  **Repo:** `divideby/music`

## Quickstart

```bash
./fetch-soundfont.sh          # one-time: link FluidR3_GM.sf2 (gitignored)
./fetch-nam.sh                # one-time: NAM amp models (gitignored, for *_nam tracks)
./render.sh <track>           # build out/<track>.ogg  (e.g. lofi_intro)
python3 -m unittest discover -s tests   # 15 tests, all pure-module + a render smoke
./publish.sh "msg"            # commit + push + deploy to Vercel
```

Listen locally: `python3 -m http.server` → http://localhost:8000/

## Layout

```
studio/        engine. PURE + unit-tested: notes, pattern, instruments.
               SIDE-EFFECTS (shell out): song (MIDI), render, amp (pedalboard), nam (waveny).
tracks/<name>/track.py   one declarative track = build a Song, call render*. The examples.
irs/           cabinet impulse responses (committed, tiny)
nam_models/    NAM amp captures (GITIGNORED — ./fetch-nam.sh)
soundfonts/    FluidR3_GM.sf2 (GITIGNORED — ./fetch-soundfont.sh)
out/           *.ogg committed (Pages needs them); *.wav/*.mid ignored
docs/guitar-tone.md   the guitar-tone ladder, gotchas, and how to verify by ear-less
docs/superpowers/specs/   original design spec
```

## Conventions

- **Pure vs side-effecting split** (mirrors the Kolyan project): `notes`/`pattern`/
  `instruments` never touch the filesystem or binaries and are unit-tested; anything
  that shells out (fluidsynth/sox/ffmpeg/pedalboard/waveny) lives in `song`/`render`/
  `amp`/`nam`. Keep it that way — tests stay fast and runnable anywhere.
- **A track is declarative.** It composes a `Song` from helpers and calls a render
  function. No render logic in the track beyond the one call. Copy an existing track.
- **Determinism.** No unseeded randomness. `humanize`/`add_part`/`add_drums` take a
  `seed`; same code → same `.mid` → same audio. Tests rely on this.
- **Commit the `.ogg`** (Pages/Vercel serve it); never commit `.wav`/`.mid`/soundfonts/
  NAM models.
- **pip** needs `--break-system-packages` here (PEP 668; venv ensurepip is broken).

## Critical gotchas (read before re-discovering them)

- **Deploy is Vercel, NOT GitHub Pages.** The `divideby.github.io` account has the
  custom domain `divideby.ru`, so GitHub 301-redirects every `divideby.github.io/*`
  project page to `divideby.ru/*` (Cloudflare, doesn't serve this repo). `./publish.sh`
  deploys to Vercel (`music-psi-lovat.vercel.app`). jsDelivr can hotlink a raw `.ogg`.
- **There is no audio playback on this server.** You cannot judge tone by ear — verify
  *objectively* (levels, dynamics, distortion proxies — see docs/guitar-tone.md) and
  tell the user the final aesthetic call is theirs. Don't claim "sounds great."
- **NAM via `waveny` is picky:** mono, 24-bit, WAVE **format tag 1** (plain PCM). sox/
  ffmpeg write 24-bit as "extensible" (tag 65534) which waveny rejects — `studio/nam.py`
  builds the WAV with Python `wave` + a byte-interleave trick. NAM output is very quiet
  (`head_scale`); you MUST make up gain or the guitar buries in the mix. Details &
  the "no overdrive" debugging story: docs/guitar-tone.md.
- **GM distortion guitar sounds "midi".** The fix that worked: render a CLEAN GM guitar
  as a DI and amp it (pedalboard cab IR, then real NAM amp). See the tone ladder.

## Studio API (see tracks/ for usage)

- `Song(tempo, steps_per_bar=16)` — 16-step/bar grid. `.add_part(name, voice, notes,
  swing=, seed=)` where notes are `(abs_step, pitch_or_chord, dur_steps, vel)`;
  `.add_drums({drum: "x . o X .."}, bars, start_bar=, swing=)`; `.save(path)`.
- `notes`: `note_to_midi`, `scale(root,mode)`, `chord(root,quality)` (incl. `'5'` power).
- `instruments`: `PROGRAMS` (voice→GM), `DRUMS` (name→key).
- `render(mid, ogg, reverb=, lowpass=, bass_gain=, treble_gain=)` — simple sox master.
- `render_layered(stems, ogg, sample_rate=)` — per-stem chains; each stem dict takes
  `mid` + one of `fx` (sox args) / `board` (pedalboard) / `pre` (callable, e.g. NAM).
- `amp.guitar_board / cab_board / lead_board` (pedalboard amp+cab); `nam.amp(di, out, model)`.

## Dependencies

apt: `fluidsynth sox ffmpeg fluid-soundfont-gm` (+ `golang-go portaudio19-dev` to build
waveny). pip: `mido pedalboard` (`--break-system-packages`). `waveny` CLI built from
github.com/nlpodyssey/waveny → `/usr/local/bin` (see fetch-nam.sh header).
