# Guitar tone: the ladder, the gotchas, and how to verify without ears

This is the consolidated record of getting a believable distorted-guitar tone out
of a headless, sample-based studio. Three rungs, each a real step up, plus the
debugging notes so nobody re-derives them.

## The core problem

GM soundfont guitar samples — especially "distortion guitar" — sound *synthetic*
("midi"). No EQ rescues a fake source. Real tone is made by **amping a clean DI**:
a clean/raw guitar signal → amp (gain/distortion) → **speaker cabinet** → mic. The
cabinet is the single biggest "is this a real guitar?" cue. So the whole strategy
is: render a CLEAN GM guitar as a DI, then build the tone in processing.

## The ladder (all three live on the site for A/B)

| Track | Source | Amp (gain) | Cabinet | Engine |
|---|---|---|---|---|
| `modern_rock` (v1) | GM **distortion** guitar, doubled | sox `overdrive` ×2 + EQ | — | sox |
| `modern_rock_amp` (v2) | GM **clean** guitar (DI), doubled | pedalboard `Distortion` ×2 + EQ | **IR convolution** | pedalboard |
| `modern_rock_nam` (v3) | GM **clean** guitar (DI) | **Neural Amp Modeler** (real-amp neural net) | IR convolution | waveny + pedalboard |

v1→v2 was the big audible jump (user: "уже гораздо лучше") — almost entirely the
**cabinet IR**. v3 swaps the algorithmic distortion for a neural capture of a real
amp; subtler, and it exposed a gain-staging bug (below).

### v1 — sox, GM distortion sample
`tracks/modern_rock/track.py`. Double-track the riff (two GM guitar programs, diff
humanize seeds = width), render as one stem, drive through cascading `sox overdrive`
+ low-mid/presence `equalizer` + `compand`. Cheap, but the source is the ceiling.

### v2 — pedalboard, clean DI → distortion → cabinet IR  ← the winning idea
`tracks/modern_rock_amp/track.py`, `studio/amp.py:guitar_board`. Render a CLEAN GM
guitar (program `clean_guitar`) as the DI, then in pedalboard:
`HighpassFilter → Distortion ×2 (cascade) → PeakFilter (body ~800Hz, presence ~3.5k)
→ Convolution(cab IR) → LowpassFilter → Compressor`. The IR is `irs/cab_*.wav`
(royalty-free synthetic guitar cabs from ValdemarOrn/IRWorkshop). `render_layered`
runs the chain per-stem so the cab/distortion never touches the drums.

### v3 — Neural Amp Modeler (the real-amp rung)
`tracks/modern_rock_nam/track.py`, `studio/nam.py`. Clean DI → **waveny** (a Go CLI
that runs a `.nam` WaveNet model of a real amp) → `amp.cab_board` (cab IR + tone +
comp, *no* distortion — the amp model already provides gain). Pro chain. Models live
in `nam_models/` (gitignored, `./fetch-nam.sh`); the `waveny` CLI is built from
github.com/nlpodyssey/waveny.

## Gotchas that cost time

### waveny WAV format
`waveny process-rt` requires **mono, 24-bit, WAVE format tag 1** (plain PCM). sox and
ffmpeg emit 24-bit as WAVE_FORMAT_EXTENSIBLE (tag 65534) → waveny errors
("unsupported format tag 65534"). Python's `wave` module writes tag 1. Widen 16→24
bit fast without numpy by byte-interleaving (`v<<8` in 24-bit LE is just `[0,lo,hi]`):
```python
buf = bytearray(n*3); buf[1::3] = raw16[0::2]; buf[2::3] = raw16[1::2]
```
All handled in `studio/nam.py`.

### NAM gain staging — the "no overdrive" bug
Symptom: v3 sounded clean, "овердрайва будто нет". It was NOT that NAM failed to
distort. Two real causes, found by measurement:
1. **Buried in the mix.** `.nam` models bake a tiny `config.head_scale` (~0.02), so
   waveny output is ~−27 dB. With no makeup gain the (genuinely distorted) guitar sat
   ~15 dB under bass/drums → inaudible → "clean". Fix: peak-normalize the NAM output
   (`nam.amp(out_norm_db=-1)`).
2. **Moderate-gain model.** A given capture via `waveny process-rt` tops out at
   moderate crunch, and **driving the DI hotter barely adds harmonics** (tested
   −18/−9/−1 dB in → 3rd harmonic moved <2 dB). To get more grit, **swap to a
   higher-gain capture**, don't just push level. Model comparison below.

### Sample rate / channels
NAM models are 48 kHz; the `*_nam` track renders the whole mix at 48k
(`render_layered(sample_rate=48000)`). NAM is mono → `render_layered` conforms every
processed stem to stereo before the float mix, so a mono amp stem mixes cleanly.

## Verifying tone with no audio playback

The server can't play sound. Judge *objectively*; the final aesthetic call is the
user's. Recipes used here (all ffmpeg):

- **Level / clipping:** `-af volumedetect` → `mean_volume`, `max_volume`. Heavy mix
  sits ~−15 dB mean; keep `max_volume` ≤ −0.5 dB. `astats` `Flat factor: 0` = no clip.
- **Section dynamics:** `astats=metadata=1:reset=<sr*secs>` + `ametadata=print:key=
  lavfi.astats.Overall.RMS_level` → RMS per window; confirms intro→verse→chorus build.
- **Distortion proof (the decisive one):** feed a **pure sine** through the chain and
  measure harmonic bands — `bandpass=f=<freq>:width_type=h:w=30` then `volumedetect`.
  A clean sine has only the fundamental; distortion adds **3rd/5th harmonics**. Report
  harmonic level *relative to the fundamental* (e.g. 3rd at −12 dB = driven; −30 dB =
  clean). This is how the NAM gain bug and model gain were diagnosed.
- **Cabinet check:** compare energy `>6 kHz` (`highpass=f=6000,volumedetect`) vs full
  level — a real cab rolls off fizz, so an IR'd tone has ~5 dB less relative HF than the
  raw sox tone.
- **Caveat:** crest factor on a *gappy* guitar stem (palm-mute chugs with silence) is
  misleading — silence inflates it. Use the sine-harmonic test instead.

## NAM model gain comparison (sine 220 Hz, harmonics relative to fundamental)

Higher = more gain/saturation. Measured via the sine recipe above.

| Model (in `pelennor2170/NAM_models`) | 3rd harmonic | 5th harmonic | verdict |
|---|---|---|---|
| Helga B 5150 BlockLetter Boosted | −15.7 dB | −19.6 dB | moderate crunch |
| **Jason Z Line 6 UBERMETAL** ← used | −12.0 dB | −15.4 dB | solid high-gain |
| Tudor N Mesa 2x12 Gain@10 | −13.2 dB | −14.1 dB | high-gain |
| Tom C Engl Savage | **+13.2 dB** | −2.5 dB | extreme (risk: fizzy) |

## Add a new amped track (recipe)

1. Copy `tracks/modern_rock_amp/` (pedalboard) or `tracks/modern_rock_nam/` (NAM).
2. Compose: reuse a sibling's `build(...)` via `importlib`, or write a fresh `Song`.
   For amped guitar, use a **clean** source voice (`clean_guitar`), not `distortion`.
3. Choose the chain per stem in `render_layered`:
   - pedalboard: `{"board": amp.guitar_board(ir=..., drive=...)}`
   - NAM: `{"pre": lambda i,o: nam.amp(i,o, MODEL, norm_db=-3), "board": amp.cab_board(ir=...)}`
   - drums/bass: `{"fx": [sox args]}`
4. `./render.sh <name>`, verify objectively (above), add an `<article>` to `index.html`,
   `./publish.sh`.

## Ceiling & next rungs

Even v3 is "a good MIDI guitar through a real amp model", not a played guitar — we
have no real DI. Further options if asked: a higher-gain NAM model (Engl Savage), a
boost/overdrive *in front of* the amp ("TS into a 5150"), stacking NAM + a touch of
pedalboard distortion, or hosting a real amp-sim VST3 via pedalboard (JUCE headless
may need xvfb).
