# Headless DAW: студия для написания треков кодом

**Дата:** 2026-06-18
**Статус:** дизайн утверждён, готов к плану реализации
**Репозиторий:** `~/projects/music` (новый, → `divideby/music`)

## Контекст

Самостоятельная музыкальная студия на этом сервере — пишем треки **кодом**, рендерим headless (без GUI/GPU), публикуем так, чтобы их можно было **послушать и скачать** по ссылке. Проект не привязан к Kolyan, но идейно продолжает его аудио-спеку (`kolyan/docs/superpowers/specs/2026-06-18-audio-realism-smplr-design.md`), где «headless-рендер на сервере (FluidSynth/Csound)» был помечен как путь к «студийному потолку» звука. Берём именно сэмпловый путь (FluidSynth), а не синтез, ради живого тембра.

## Цель и критерии успеха

- Из Python-скрипта получить связный музыкальный трек в виде аудиофайла.
- Тембр — сэмплированные инструменты (GM-саундфонт), а не осцилляторы.
- Весь пайплайн воспроизводим одной командой и детерминирован (один и тот же код → один и тот же `.mid`).
- Результат опубликован на GitHub Pages: `https://divideby.github.io/music/` — слушать в браузере и качать.
- **Definition of done:** на Pages играет первый трек — lo-fi бит ~30–60 c (`out/lofi_intro.ogg`).

## Стек

| Слой | Инструмент | Установка | Роль |
|---|---|---|---|
| Запись MIDI | `mido` | pip | строим `.mid` из Python |
| Рендер | `fluidsynth` | apt | `.mid` + `.sf2` → `.wav` (сэмплы) |
| Саундфонт | `FluidR3_GM.sf2` | скрипт-загрузчик | GM-набор инструментов (свободный) |
| Мастеринг/кодек | `sox` + `ffmpeg` | apt | нормализация, реверб, EQ, `.wav`→`.ogg` |
| Публикация | GitHub Pages + `gh` | есть (`gh` залогинен как `divideby`) | хостинг плеера и файлов |

Все компоненты — CLI, без GUI, без GPU, без лицензионных вопросов (саундфонт свободный, тянется скриптом, в git не коммитится).

## Структура проекта

```
~/projects/music/
  studio/                # переиспользуемая библиотека («движок студии»)
    notes.py             #  'A4'→midi, гаммы, аккорды           (чистый, тестируемый)
    pattern.py           #  степ-секвенсор: бары, свинг, humanize (чистый, тестируемый)
    instruments.py       #  имя голоса → GM-программа (piano/rhodes/bass/drums…)
    song.py              #  Song/Track → строит mido.MidiFile
    render.py            #  .mid → fluidsynth → .wav → мастеринг → .ogg
    __init__.py
  soundfonts/            #  FluidR3_GM.sf2  (gitignored, тянется fetch-soundfont.sh)
  tracks/
    lofi_intro/
      track.py           #  ОДИН трек = один скрипт: собирает Song и зовёт render
  out/                   #  .wav (gitignored) + .ogg (коммитим — нужно для Pages)
  tests/                 #  юнит-тесты чистых модулей + smoke-рендер
  index.html             #  плеер: список треков (<audio> + кнопка скачать)
  render.sh              #  ./render.sh lofi_intro
  fetch-soundfont.sh     #  загрузка FluidR3_GM.sf2
  publish.sh             #  рендер + git add out + commit + push (Pages пересоберётся)
  .gitignore
  README.md
```

**Принцип разделения (как в Kolyan):** чистые хелперы (`notes`, `pattern`, `instruments`) не трогают файловую систему и внешние бинарники — они тестируются юнит-тестами. Сайд-эффекты (вызов fluidsynth/sox/ffmpeg) изолированы в `render.py`. Трек — маленький декларативный скрипт поверх `studio`, не содержит логики рендера кроме одного вызова.

## Компоненты и интерфейсы

### `studio/notes.py` (чистый)
- `note_to_midi(name) -> int` — `'A4'` → 69; мусор → исключение (никогда не молчит).
- `scale(root, mode) -> list[int]` — мажор/минор/дориан и т.п.
- `chord(root, quality) -> list[int]` — триады/септаккорды как список MIDI-нот.

### `studio/pattern.py` (чистый)
- Парсинг бара из строки шагов: `"x . . x . . x ."` (16 шагов), `'x'`=удар, `'.'`=пауза.
- `swing(steps, amount)` — сдвиг чётных шагов (lo-fi грув).
- `humanize(events, time_jitter, vel_jitter, seed)` — детерминированный (фиксированный seed → одинаковый результат; **без `random` без seed** — иначе недетерминизм).

### `studio/instruments.py` (чистый)
- `PROGRAMS: dict[str, int]` — `'piano'→0, 'rhodes'→4, 'bass'→33, …`; ударные — канал 10 (GM perc).
- `program_for(voice) -> int`.

### `studio/song.py`
- `Song(tempo, key)` с методами добавления партий (`add_chords`, `add_bass`, `add_drums`, `add_melody`), каждая на своём MIDI-канале с заданным голосом/велосити.
- `Song.save(path)` → пишет `.mid` через `mido` (применяя свинг/humanize из pattern).

### `studio/render.py` (сайд-эффекты)
- `render(mid_path, out_ogg, soundfont=...) -> Path`:
  1. `fluidsynth -ni -F raw.wav -r 44100 soundfont.sf2 song.mid`
  2. мастеринг через sox: нормализация (`gain -n -1`), лёгкий реверб, мягкий ВЧ/НЧ EQ.
  3. `ffmpeg` → `.ogg` (и опц. `.mp3`).
- Проверяет наличие бинарников и саундфонта, понятная ошибка если нет.

### `tracks/<name>/track.py`
- Импортирует `studio`, строит `Song`, зовёт `render(...)` → `out/<name>.ogg`. Запускается `./render.sh <name>`.

## Поток данных

```
track.py ──build──► out/<name>.mid
out/<name>.mid + soundfonts/FluidR3_GM.sf2 ──fluidsynth──► out/<name>.raw.wav
out/<name>.raw.wav ──sox (norm+reverb+EQ)──► out/<name>.master.wav ──ffmpeg──► out/<name>.ogg
out/<name>.ogg + index.html ──git push──► GitHub Pages ──► divideby.github.io/music
```

Промежуточные `.mid`/`.raw.wav`/`.master.wav` — в `out/` и gitignored, кроме финального `.ogg`.

## Публикация (GitHub Pages)

- `git init` (готово) → `gh repo create divideby/music --public --source=. --remote=origin`.
- Pages включается из ветки `main`, корень (`gh api` или Settings). `index.html` в корне — плеер.
- `index.html`: статический список треков с `<audio controls>` и ссылкой «скачать» на `out/<name>.ogg`. Обновляется вручную при добавлении трека (треков мало; генератор — позже, если понадобится, YAGNI).
- `publish.sh`: рендер всех/указанного трека → `git add index.html out/*.ogg` → commit → push.

## Обработка ошибок

- `render.py` падает с понятным сообщением, если нет `fluidsynth`/`sox`/`ffmpeg` или саундфонта (с подсказкой запустить `fetch-soundfont.sh` / `apt-get install`).
- `notes`/`pattern` бросают на некорректном вводе (нота вне диапазона, кривой бар), а не возвращают тихий мусор.
- `fetch-soundfont.sh` проверяет контрольный размер/наличие после загрузки.

## Тестирование

- **Юнит (pytest или `python -m unittest`)** на чистые модули:
  - `notes`: парсинг нот, граничные октавы, гаммы/аккорды, исключение на мусоре.
  - `pattern`: длина бара, свинг-сдвиг, детерминизм humanize при фиксированном seed.
  - `instruments`: маппинг голосов в программы.
- **Smoke-рендер**: построить 2 бара → `render` → проверить, что `.ogg` существует и длительность/размер ненулевые. Помечается как требующий бинарников (skip, если fluidsynth не установлен).

## Объём (YAGNI / не делаем сейчас)

- Не пишем свой синтезатор и не тащим Csound на старте (опциональное дополнение позже, отдельной спекой).
- Не делаем автогенератор `index.html` — правим руками, пока треков мало.
- Не делаем веб-редактор/реалтайм — только офлайн-рендер.
- Не делаем многотрековый микшер с автоматизацией — мастеринг фиксированной цепочкой sox; точечные правки в `render.py`.

## Первый результат

`tracks/lofi_intro/track.py` — lo-fi бит ~30–60 c: rhodes-аккорды + бас + барабаны со свингом и humanize, лёгкий винил/реверб в мастеринге. Цель — пройти весь путь до играющего файла на `divideby.github.io/music`.
