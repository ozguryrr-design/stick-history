---
name: stick-history
description: Create original, historically accurate stick-figure animated episodes in both horizontal (16:9) and vertical (9:16) formats from a historical topic and a user-supplied voice-over file (in any language). No Remotion, no Node, no ElevenLabs. On first run, interviews the user to build a persistent channel style profile (palette, line, face, texture, camera energy, typography, ending) and learns from feedback after every episode. Researches any historical era or region without period restrictions, dresses characters and builds sets from parametric parts, directs dynamic camera moves and transitions synced to the voice, synthesises procedural sound effects and music, self-checks framing and contrast, and masters to -14 LUFS.
---

# Stick History Animation Skill

Turn a real historical event and a voice-over file (in any language) into a finished animated episode in **16:9 (YouTube/landscape)** and **9:16 (Shorts/Reels/TikTok)**. Every frame is rendered in pure Python (`resvg-py` + `numpy` + `Pillow` + `ffmpeg`) from a compact JSON scene description (`scenes.json`). No Node, no browser, no paid TTS/SFX APIs.

| Reference | What to read it for |
|---|---|
| `references/style-quiz.md` | First-run style questionnaire, palettes, channel seed, `profile.json`, `learned.md`, `history.json` |
| `references/era-research.md` | Researching any historical period & translating clothing, headgear, weapons, mounts, and architecture into parts |
| `references/dsl.md` | Complete `scenes.json` specification: cast, rig, garments, headwear, props, mounts, world items, maps, timelines, documents |
| `references/camera.md` | Dynamic camera moves, multi-keyframe choreography, rack focus, transitions, and dual 16:9 / 9:16 framing |
| `references/sound.md` | Voice alignment (`w:N`, `s:N`), procedural SFX, ambiences, music moods, ducking, and -14 LUFS mastering |
| `references/traps.md` | Common visual, framing, historical, and audio mistakes to avoid |

## Core Rules

1. **Real history only — every fact is sourced.** Every date, number, name, and historical claim must be verified and written with its source in `episodes/<slug>/brief.json` before `scenes.json` is written. Mark disputed numbers as disputed.
2. **Zero period restrictions — build the era accurately.** Never restrict the user to pre-made eras and never use generic modern figures for historical events. Research the exact century, place, and social roles; list period clothing, headgear, weapons, mounts, and architecture (plus an `avoid` list of anachronisms) in `brief.json`; and assemble them from the parametric rig and world primitives (or the `"svg"` escape hatch for one-off artifacts).
3. **Channel originality & persistent memory.** Before starting any episode, check `profile.json`, `learned.md`, and `history.json` in the project directory:
   - If `profile.json` does not exist, **ask the user the style questions** (`references/style-quiz.md`) before designing scenes, then save their answers with `run.py style`.
   - Always read `learned.md` and `history.json` so you honour past feedback and vary camera moves, transitions, and compositions across episodes.
4. **Language-agnostic external voice-over.** Do not generate paid TTS. The user drops their voice recording (`voice.wav`, `.mp3`, `.m4a`, `.flac`, `.ogg`) into `episodes/<slug>/voice/`, optionally with `script.txt`. If `script.txt` is not provided, `run.py align` transcribes the audio automatically (via `faster-whisper`) or segments it by speech pauses and energy accents.
5. **Storyboard & self-check gate before final render.** Never run a full render until `run.py check <slug>` passes without errors and you have inspected both `storyboard-16x9.jpg` and `storyboard-9x16.jpg`.

---

## Setup (once per machine)

Requires Python 3.10+. Install dependencies:

```bash
pip install -r <skill>/requirements.txt
# Recommended for automatic transcription when script.txt is omitted:
pip install faster-whisper
```

Initialize a project workspace where episodes and channel memory live:

```bash
python <skill>/run.py init
```

All commands below run from that project folder; `<skill>` is the path to this skill directory.

---

## The Pipeline

Work through these steps in order.

### 1. Channel Style Profile & Memory

Check if `profile.json` exists in the project folder:
- **First run (`profile.json` missing):** Read `references/style-quiz.md`. Ask the user to choose their channel's look (Colour mood, Line style, Character face, Texture, Camera energy, Typography, Ending style — or *"Surprise me"* for a seeded signature). Save with:
  ```bash
  python <skill>/run.py style --set palette=parchment line=clean face=expressive texture=paper camera=dynamic font=serif ending=fact --preview
  ```
  Show `style-preview.png` if the user wants to preview the look.
- **Every run:** Read `learned.md` (user rules from previous episodes) and `history.json` (past episodes and camera patterns).

### 2. Create Episode & Historical Research Brief

Create the episode folder:

```bash
python <skill>/run.py new <slug> --topic "<topic>"
```

Read `references/era-research.md`. Research the historical event and write `episodes/<slug>/brief.json`:
- `event`, `date`, `place`, `formats` (`["16:9", "9:16"]`)
- `people`: key historical figures or roles (`id`, `name`, `role`)
- `clothing`: period-accurate headgear, garments, colours, and materials per role
- `objects`: weapons, tools, vessels, mounts, banners, documents
- `architecture` and `landscape`: walls, roofs, columns, domes, terrain, trees, climate
- `avoid`: anachronisms that must not appear in `scenes.json` (checked automatically by `run.py check`)
- `facts` and `sources`: every date and number used, with primary/secondary citations

### 3. Voice-Over & Alignment

Ask the user to place their voice-over file in `episodes/<slug>/voice/` (and optionally `episodes/<slug>/script.txt` with one sentence/beat per line). If the user asks you to draft the narration text for them to record first, write `episodes/<slug>/script.txt` in their language: concise, vivid, one visual beat per line, grounded in `brief.json`.

Once the audio file is in `episodes/<slug>/voice/`, align it:

```bash
python <skill>/run.py align <slug> --words
```

This writes `episodes/<slug>/words.json` containing:
- `words` (`w:0`, `w:1`, … and `w:0e` for word ends)
- `segments` (`s:0`, `s:1`, … and `s:0e` for sentence/beat ends)
- `pauses` and `accents` (loudest vocal onsets — ideal for camera cuts and impact hits)
- `envelope` (100 Hz amplitude envelope used for automatic lip-sync when an actor has `"talk": true` and for music ducking)

### 4. Scene Plan (`scenes.json`)

Read `references/dsl.md` and `references/camera.md`. You can also inspect all available building blocks at any time with:

```bash
python <skill>/run.py catalog
```

Write `episodes/<slug>/scenes.json`:
- **Cast (`cast`):** Define each character's `skin`, `build`, `hair`, `beard`, `mustache`, layered `head` (headwear primitives), layered `outfit` (garments, armor, robes, sashes, capes), `sleeves`, `legwear`, `shoes`, `mount` (`horse`, `camel`, `elephant`, `chariot`, …), and `hold` (`near`/`far` props).
- **Shots (`shots`):** Pace cuts to the voice (`s:0`, `s:1`, `w:12`, or seconds), aiming for a new shot or distinct camera beat every 2–4 seconds.
  - Use depth layers (`depth: 6` far background, `depth: 2..3` midground architecture, `depth: 1` actors and main set, `depth: 0.6` blurred foreground silhouette) for rich parallax.
  - Give every shot purposeful camera motion (`push_in`, `pull_out`, `pan_right`, `crane_down`, `orbit`, `snap_in`, `reveal`, or multi-keyframe `[{"t": 0, "frame": "full", "on": ["a", "b"]}, {"t": "80%", "frame": "mcu", "on": "a"}]`).
  - Use historical scene types where they clarify the story: animated `map` (with `lands`, `territories`, marching `routes`, `pins`), `timeline`, `document` (scroll/decree/tablet with animated wax seal), `army`/`crowd`, `ship`, `cannon`.
  - Match the ending shot to `profile.json`'s `ending` preference (`fact` card with source, open `question`, or `next` hook).

### 5. Storyboard & Self-Check Gate

Run the automated verifier and render the storyboards:

```bash
python <skill>/run.py check <slug>
python <skill>/run.py board <slug>
```

1. Read the output of `check`. Fix any `ERROR` or `WARN` (out-of-frame heads in `16:9` or `9:16`, low head-to-background contrast, anachronisms from `brief.json`, static cameras, or shot timing gaps).
2. View **both** `episodes/<slug>/out/storyboard-16x9.jpg` and `episodes/<slug>/out/storyboard-9x16.jpg` against the checklist in `references/traps.md`.
3. Re-run `check` and `board` until both formats read cleanly. If the user is in the loop, show them the storyboards before final rendering.

### 6. Motion Check

For shots with complex action, walks, or multi-keyframe camera moves, render a flipbook grid:

```bash
python <skill>/run.py grid <slug> S2 S3
```

Inspect `episodes/<slug>/out/grid-S2-16x9.jpg` to verify poses, walk cycles, prop angles, and camera easing.

### 7. Sound & Mix Check

Read `references/sound.md`. Build the procedural SFX, ambience beds, and modal music stems:

```bash
python <skill>/run.py sound <slug>
```

The engine automatically cues sounds for visual events (`cannon`, `whip`/`zoom` transitions, `hits`, `year` ticks, `title` booms, `card` paper, `water`/`fire`/`crowd`/`march` ambiences) and merges any custom events/ambience/music in `scenes.json -> sound`.

### 8. Master & Learn

Render and master both formats (`16:9` and `9:16`) to **-14 LUFS / -1 dBTP**:

```bash
python <skill>/run.py master <slug> --quality final
```

(Use `--quality draft` or `--quality preview` for fast iteration.)

Check `episodes/<slug>/out/report.json` and any `voice_masked` warnings. Hand over:
- `episodes/<slug>/out/<slug>-16x9.mp4`
- `episodes/<slug>/out/<slug>-9x16.mp4`
- `episodes/<slug>/out/storyboard-16x9.jpg` and `storyboard-9x16.jpg`

Finally, ask the user what they liked and what they want adjusted next time, and persist their feedback:

```bash
python <skill>/run.py learn <slug> --like "..." --change "..." --rule "..."
```
