# Voice Alignment, Procedural Sound & Mastering

No external audio APIs are required. Voice-over comes from the user's file in `episodes/<slug>/voice/`; sound effects and music are synthesised procedurally in numpy using the channel's `seed`.

## 1. Voice Alignment (`run.py align <slug>`)

Place any audio file (`voice.wav`, `.mp3`, `.m4a`, `.flac`, `.ogg`, `.opus`) in `episodes/<slug>/voice/`.
Optionally place the transcript in `episodes/<slug>/script.txt` (one sentence or visual beat per line).

- If `faster-whisper` is installed, `align` transcribes the audio in its native language with word-level timestamps and reconciles spellings with `script.txt` if present.
- If `faster-whisper` is not installed (or `--model none` is passed), `align` detects speech segments and pauses from the energy envelope and distributes `script.txt` lines across the speech segments.
- `align` also extracts:
  - `accents`: timestamps of the sharpest vocal onsets — use these for cuts and camera hits.
  - `envelope`: 100 Hz amplitude contour — drives automatic mouth animation on any actor with `"talk": true` and ducks music/ambience under speech.

---

## 2. Automatic & Custom Sound (`scenes.json -> sound`)

When you run `python <skill>/run.py sound <slug>`, the engine automatically cues sounds from the visual elements in `scenes.json`:
- `cannon` with `fire` -> `cannon` blast
- `hits` -> `impact`
- `whip` / `zoom` / `push` transitions -> `whoosh`
- `year` counter -> accelerating `tick`s + `impact`
- `title` -> `boom`, `label` -> `pop`, `card` -> `paper`
- `water`, `fire`, `crowd`, `army`, `rain` -> matching continuous ambience beds (cross-faded across cuts)

You can customize or add events in `scenes.json`:

```json
"sound": {
  "auto": true,
  "sfx_gain": -9,
  "ambience_gain": -28,
  "music": {"mood": "eastern", "gain": -23, "instrument": "oud"},
  "mute_auto": ["year"],
  "events": [
    {"t": "S2+0.4", "kind": "paper", "gain": -8},
    {"t": "w:15", "kind": "sword", "gain": -5},
    {"t": 6.5, "kind": "horn", "gain": -7, "pitch": 0.85}
  ],
  "ambience": [
    {"kind": "battle", "shots": ["S3", "S4"], "gain": -2}
  ]
}
```

### Available Procedural Sound Effects (`kind`)
- **Impacts & Weapons:** `whoosh`, `boom`, `impact`, `cannon`, `gunshot`, `musket`, `hit`, `thud`, `punch`, `clang`, `sword`, `explosion`
- **Signals & Musical Hits:** `bell`, `drum`, `war_drum`, `horn`, `riser`, `heartbeat`, `tick`, `pop`
- **Foley:** `paper`, `scroll`, `quill`, `typewriter`, `coins`, `door`, `splash`, `steps`, `march`, `gallop`, `horses`, `engine`
- **Ambiences:** `wind`, `fire`, `crackle`, `waves`, `sea`, `rain`, `thunder`, `crowd`, `murmur`, `cheer`, `battle`

### Available Music Moods (`music.mood`)
- `epic` (Minor, 92 BPM, drums + plucked harp/strings + warm pad)
- `tense` (Phrygian, 100 BPM, driving pulse)
- `eastern` (Hijaz maqam, 88 BPM, oud-style pluck + frame drum)
- `march` (Minor, 112 BPM, martial cadence)
- `calm` (Major, 72 BPM, gentle arpeggios, no drums)
- `sad` (Minor, 64 BPM, sparse & warm)
- `mystery` (Harmonic minor, 70 BPM)
- `triumph` (Major, 104 BPM, bright & uplifting)
- Or place any `.mp3`/`.wav` file in `episodes/<slug>/music/` to use a custom track instead.

---

## 3. Mix Check & Mastering (`run.py master <slug>`)

`master` mixes `voice` + `sfx` + `ambience` + `music`, checks for moments where effects crowd within 3 dB of the speaking voice (`voice_masked` in `report.json`), runs two-pass EBU R128 loudness normalization to **-14.0 LUFS / -1.0 dBTP**, and muxes the master audio into both `16:9` and `9:16` MP4 files.
