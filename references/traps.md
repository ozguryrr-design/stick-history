# Visual, Historical & Audio Traps Checklist

Check every storyboard (`storyboard-16x9.jpg` and `storyboard-9x16.jpg`) against this list before running a final render.

## 1. Dual-Format Framing Traps (16:9 & 9:16)

- **Two-shots too wide for 9:16:** In `16:9`, two characters at `x: 650` and `x: 1270` (`620` units apart) fit easily; in `9:16`, they get pushed to the left and right edges. Place conversing characters `260–340` world units apart (e.g., `x: 800` and `x: 1120`) so they read well in both formats.
- **Bottom 22% of 9:16 is covered by platform UI:** TikTok, Reels, and Shorts cover the bottom fifth of the vertical screen with captions and buttons. Keep character heads and text cards above `y = 0.78` in `9:16` (`run.py check` warns when a head drops into this zone).
- **Map labels clipped in 9:16:** Keep key map pins, routes, and labels between `x = 600` and `x = 1320` so a `"frame": "stage"` map shot shows all critical geography in vertical format too.
- **Text overlapping map labels or heads:** Put `year` counters or `card`s in clear sky/sea areas (`y: 0.16..0.24` or `y: 0.80`) away from character heads and map city names.

## 2. Character & Contrast Traps

- **Dark headgear on a dark night background:** A brown or black cap/hood against a night hill or dark interior wall disappears. In night shots (`time: "night"` or `veil > 0`), either give the character lighter headwear (`white`, `cream`, `gold`, `steel`), place a torch/lamp `light` behind them, or use a lighter mid-ground element behind their head (`run.py check` measures head-to-background contrast automatically).
- **Frozen characters:** A shot where characters don't move at all feels dead. Give the speaking character `"talk": true` and at least one keyframe pose change (`"t": "40%", "pose": "point"`), or have characters walk into position.
- **Mounted characters:** Always attach `"mount": {"type": "horse", ...}` on the character or actor rather than placing a standalone horse item at the same `x, y` — the actor `mount` property automatically seats the rider in the saddle, adjusts garment drape, bobs with the gait, and raises the camera's target box to the rider's head.

## 3. Historical Traps

- **Anachronisms across eras of the same culture:** For example, the Ottoman *fez* belongs to the 19th century (post-1829 Mahmud II reforms), never 1453 or 16th-century scenes (which use the wrapped *destar/kavuk* or Janissary *börk*). Always populate `brief.json -> avoid` before writing `scenes.json`.
- **Generic silhouettes:** Never leave historical figures as bare default stick figures. Even a peasant or sailor needs a period tunic, belt, and cap/head-wrap so the era reads in a single still frame.
- **Unsourced numbers:** Never put a number in a script or `card` without recording its primary/secondary source in `brief.json`.

## 4. Sound Traps

- **Loud SFX landing directly on a spoken keyword:** If `master` reports `voice_masked` spans in `report.json`, shift heavy hits (`cannon`, `impact`, `bell`) into the pause just before or after the word, or lower that event's `gain` by 4–6 dB.
