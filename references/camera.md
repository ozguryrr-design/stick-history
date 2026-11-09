# Dynamic Camera Direction & Dual-Format Framing

Every episode renders in **16:9** (`1920x1080`) and **9:16** (`1080x1920`) from the same `scenes.json`. The camera works in world space and automatically reframes for vertical video so subjects are tracked, never blindly cropped.

## 1. Camera Framing (`frame` and `on`)

Instead of hardcoding pixel coordinates, aim the camera at actors (`"on": "mehmed"`, `"on": ["mehmed", "pasha"]`, or `"on": [x, y]`) with a cinematic shot size:

| `frame` | What it shows | When to use it |
|---|---|---|
| `extreme_wide` | 4.2 character heights | Massive battlefields, fleets, mountain passes, city sieges |
| `wide` | 2.6 character heights | Establishing a set with architecture and actors |
| `full` | 1.45 character heights | Head-to-toe action, walking, riding, two-shots |
| `medium` | 0.95 character heights | Waist-up acting, gesturing, holding props |
| `mcu` | 0.62 character heights | Chest-and-head close acting, speaking key lines |
| `cu` | 0.40 character heights | Face reaction, intense emotion, turning point |
| `ecu` | 0.22 character heights | Eyes, seal stamp, hand on hilt |
| `stage` | Full 1080p stage | Maps, timelines, wide panoramas without a single target actor |

The camera automatically adds **look-room (`lead`)** in the direction the target actor is facing.

---

## 2. Shorthand Camera Moves (`camera` as a dict)

Every shot should move. For a single continuous move across a shot, pass a dict:

```json
"camera": {"frame": "wide", "on": "mehmed", "move": "push_in", "amount": 0.22, "ease": "in_out_cubic"}
```

Available `move` values:
- `push_in` / `pull_out` — Smooth log-space dolly in or out.
- `pan_right` / `pan_left` — Horizontal tracking sweep (automatically scaled for 9:16 so subjects stay inside the narrower vertical frame).
- `tilt_up` / `tilt_down` — Vertical sweep.
- `crane_up` / `crane_down` — Vertical sweep combined with a zoom pull/push (great for revealing towers, walls, or armies).
- `drift` — Subtle cinematic floating movement.
- `orbit` — Parallax horizontal glide with a gentle camera roll (`rot`).
- `snap_in` — Fast `out_expo` punch-in during the first 0.35s, then slow creep (high-energy beat).
- `reveal` — Starts tight and pulls back to reveal the full scene.

---

## 3. Multi-Keyframe Camera Choreography (`camera` as a list)

For dynamic storytelling within a single shot (e.g., starting on a two-shot and pushing into a close-up, or whipping from one character to another), pass a list of camera keys:

```json
"camera": [
  {"t": 0, "frame": "full", "on": ["mehmed", "pasha"]},
  {"t": "45%", "frame": "full", "on": ["mehmed", "pasha"]},
  {"t": "85%", "frame": "mcu", "on": "mehmed", "ease": "in_out_cubic"}
]
```

- Add `"portrait": {"offset": [dx, dy], "push": 0.9}` on any key if a shot needs a custom adjustment specifically for `9:16`.
- Add `"hits": [1.2]` on the shot to trigger a decaying Perlin camera shake + impact sound on a strike, cannon shot, or dramatic beat.

---

## 4. Rack Focus & Foreground Depth

Place a foreground silhouette at `depth: 0.6` (a rock, column, arch, or tree at the edge of the stage) and animate its blur:

```json
{"depth": 0.6, "blur": [0, 10], "items": [{"kind": "column", "x": 320, "h": 600}]},
{"depth": 1.0, "blur": [8, 0], "items": [ ... ]}
```

This smoothly shifts focus from the foreground element to the main subject across the shot.

---

## 5. Transitions Between Shots (`transition`)

Set `"transition"` on the incoming shot:
- `"cut"` — Clean instant cut (use on vocal accents).
- `"whip"` — Fast horizontal whip pan with directional motion blur and automatic whoosh SFX.
- `"zoom"` — Fast zoom-through transition with radial blur and deep whoosh SFX.
- `"dissolve"` — Cross-dissolve between outgoing and incoming shots (great for time passing).
- `"push"` — Slide transition pushing one scene off-screen.
- `"iris"` — Circular iris close/open around the centre of the frame.
- `"dip"` — Dip to black (or `{"kind": "dip", "color": "#ffffff"}`).
- `"flash"` — Bright flash cut with impact SFX.
