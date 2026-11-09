# Channel Style Quiz & Persistent Memory

Every channel using `stick-history` gets its own visual and musical identity so episodes made by different creators do not look or sound identical.

## First-Run Style Questionnaire

When `profile.json` does not exist in the project directory (or when the user asks to restyle their channel), ask the user these 7 questions in their own language. Keep the prompt conversational; they can answer each one or pick **"Surprise me"** (`palette=surprise`) to generate a seeded look.

| Key | Question | Options |
|---|---|---|
| `palette` | **Colour mood** (Renk havası) | `parchment` (Warm paper & sepia ink, old-book calm)<br>`midnight` (Dark cinematic blue, lamplight & moonlight)<br>`pastel` (Soft, airy, gentle)<br>`engraving` (Black-and-white print with one crimson accent)<br>`golden` (Warm sunset light, long shadows, epic)<br>`fresco` (Terracotta, ochre & olive, ancient murals)<br>`miniature` (Flat lapis, vermilion & gold, illuminated manuscript)<br>`surprise` (Seed-generated custom palette) |
| `line` | **Line character** (Çizgi karakteri) | `clean` (Thin and crisp)<br>`bold` (Thick and chunky with outline)<br>`sketch` (Hand-drawn boiling/wobbling line)<br>`brush` (Tapered brush stroke) |
| `face` | **Character faces** (Karakter yüzü) | `none` (Faceless silhouette — body posture carries the acting)<br>`dots` (Minimal dot eyes)<br>`expressive` (Eyes, eyebrows, and animated talking mouths) |
| `texture` | **Surface texture** (Doku) | `flat` (Clean digital flat)<br>`paper` (Subtle paper grain & soft vignette)<br>`film` (Old film grain, vignette, and gentle projector flicker) |
| `camera` | **Camera energy** (Kamera enerjisi) | `calm` (Slow documentary drifts and dissolves)<br>`dynamic` (Balanced push-ins, pans, and whip transitions on beats)<br>`energetic` (Fast moves, snap zooms, stronger impact shakes) |
| `font` | **Typography** (Yazı stili) | `serif` (Classic literary serif)<br>`sans` (Modern clean sans-serif)<br>`hand` (Handwritten chronicle)<br>`inscription` (Carved monumental capitals) |
| `ending` | **Episode ending** (Bölüm sonu) | `fact` (Ends on a sourced historical fact card)<br>`question` (Ends on a thought-provoking question for comments)<br>`next` (Ends on a cliffhanger / what happened next) |

Save the answers with:

```bash
python <skill>/run.py style --set palette=midnight line=clean face=expressive texture=paper camera=dynamic font=serif ending=fact --preview
```

### Custom Colour Overrides

If the user wants a specific accent or paper colour on top of a palette, pass `overrides.<key>=#hex`:

```bash
python <skill>/run.py style --set palette=parchment overrides.accent=#1f5a7a
```

---

## How Persistent Learning Works

Three files in the project folder carry memory across episodes and across different AI agents:

1. **`profile.json`** — The channel's chosen visual & camera signature plus its integer `seed` (which varies procedural crowds, trees, clouds, SFX timbre, and musical root notes).
2. **`learned.md`** — Human feedback rules logged after each episode via `run.py learn <slug> --like ... --change ... --rule ...`. Always read `learned.md` before planning a new episode; any rule written there overrides the defaults.
3. **`history.json`** — Automatic log of completed episodes, historical periods, camera moves, transitions, and world items used. Check `history.json` so you don't repeat the exact same opening move or visual layout in consecutive episodes.
