# Scene DSL Reference (`scenes.json`)

Every episode is defined in `episodes/<slug>/scenes.json`. Run `python <skill>/run.py catalog` at any time to list all available poses, expressions, headwear, garments, props, items, camera moves, transitions, and sound effects.

## Top-Level Structure

```json
{
  "title": "Episode Title",
  "fps": 30,
  "tail": 0.8,
  "time": "dawn",
  "formats": ["16:9", "9:16"],
  "cast": { ... },
  "shots": [ ... ],
  "sound": { ... }
}
```

- `duration`: Optional explicit duration in seconds. By default, duration is `words.json["duration"] + tail`.
- `time`: Default time of day (`"day"`, `"dawn"`, `"dusk"`, `"night"`, `"interior"`, `"storm"`). Each shot can override `time`.

---

## Cast (`cast`)

Each key in `cast` defines a reusable character look:

```json
"mehmed": {
  "skin": "skin2",
  "build": "broad",
  "hair": {"style": "short", "color": "brown"},
  "beard": {"style": "short", "color": "brown"},
  "mustache": true,
  "head": [
    {"shape": "dome", "color": "white", "h": 1.15, "w": 1.25, "wrap": 3},
    {"shape": "plume", "color": "white", "px": 0.25, "py": -1.35, "h": 0.8}
  ],
  "outfit": [
    {"kind": "cape", "color": "crimson", "wind": 0.35},
    {"kind": "kaftan", "color": "#2f6242", "trim": "gold", "pattern": "center", "pattern_color": "gold"},
    {"kind": "sash", "color": "gold"}
  ],
  "sleeves": "#2f6242",
  "legwear": "navy",
  "shoes": "leather",
  "mount": {"type": "horse", "color": "chestnut", "tack": "gold"},
  "hold": {
    "near": {"kind": "saber", "color": "steel", "hilt": "gold"},
    "far": {"kind": "shield", "kind": "round", "color": "crimson", "emblem": "crescent"}
  }
}
```

- **`skin`**: `"skin1"`..`"skin5"` or any colour.
- **`build`**: `"slim"`, `"average"`, `"broad"`, `"heavy"`, `"child"`.
- **`hair`**: `"short"`, `"long"`, `"bun"`, `"curly"`, `"topknot"`, `"ponytail"`, `"queue"`, `"wavy"`, `"bald"`, `"none"`.
- **`beard`**: `"short"`, `"full"`, `"long"`, `"pointed"`, `"goatee"`, `"stubble"`.
- **`head`** (layered headwear): `cap`, `dome`, `cone`, `cylinder`, `brim`, `band`, `points`, `crest`, `plume`, `wrap`, `hood`, `veil`, `flap`, `nasal`, `cheek`, `horns`, `wreath`, `tassel`, `feathers`, `svg`.
- **`outfit`** (layered garments): `robe`, `kaftan`, `dress`, `toga`, `tunic`, `coat`, `uniform`, `shirt`, `vest`, `jacket`, `armor`, `mail`, `skirt`, `apron`, `cape`, `sash`, `belt`, `collar`, `epaulettes`, `medal`, `svg`.
  - Patterns: `"stripes"`, `"center"`, `"dots"`, `"scales"`.
- **`hold`** (`near` and `far` hands): `sword`, `saber`, `scimitar`, `dagger`, `spear`, `pike`, `lance`, `staff`, `scepter`, `axe`, `hammer`, `bow`, `flag`, `banner`, `scroll`, `book`, `letter`, `torch`, `lantern`, `shield`, `musket`, `rifle`, `pistol`, `cup`, `goblet`, `key`, `sack`, `quill`, `telescope`, `crown`, `coin`, `map`, `svg`.

---

## Shots (`shots`)

Each shot runs from `start` to the next shot's `start` (or `end` on the final shot):

```json
{
  "id": "S2",
  "start": "s:1",
  "transition": "whip",
  "time": "interior",
  "ground": true,
  "ground_y": 860,
  "camera": [ ... ],
  "hits": ["40%"],
  "layers": [ ... ],
  "actors": [ ... ],
  "veil": 0.35,
  "lights": [ ... ],
  "fx": ["dust"],
  "text": [ ... ]
}
```

### Time Anchors (`start`, `end`, `t`)
- Shot `start` / `end` (absolute episode time):
  - Seconds: `3.2` or `"3.2s"`
  - Word start/end from `words.json`: `"w:14"` or `"w:14e"`
  - Sentence/beat start/end from `words.json`: `"s:2"` or `"s:2e"`
- Keyframe `t` inside a shot (relative to shot start):
  - Seconds: `0.6` or `"0.6s"`
  - Percentage of shot duration: `"45%"`

### Actors (`actors`)
 World coordinates: stage centre is `(960, 540)`, ground is `y = 860`, a standing character is `300` units tall at `scale: 1.0`.

```json
{
  "id": "mehmed",
  "char": "mehmed",
  "depth": 1.0,
  "x": 780,
  "y": 860,
  "scale": 1.0,
  "face": 1,
  "yaw": 1.0,
  "pose": "stand_proud",
  "expr": "determined",
  "talk": true,
  "keys": [
    {"t": "40%", "x": 860, "pose": "point", "expr": "shout", "ease": "out_back"}
  ]
}
```

- **Auto walk cycle:** Whenever `x` changes across keys, the rig automatically computes velocity and overlays a natural walk or run cycle! Set `"walk": 0` if you want a character to slide without stepping.
- **Named poses (`pose`):** `stand`, `stand_proud`, `hands_behind`, `point`, `point_up`, `raise_fist`, `cheer`, `wave`, `think`, `shrug`, `hold_out`, `read`, `present`, `salute`, `bow`, `kneel`, `sit`, `sit_ground`, `throne`, `crouch`, `cower`, `surprised`, `charge`, `strike`, `guard`, `aim`, `carry`, `pray`, `fall`, `lie`, `ride`, `talk`, `despair` — or override individual joint angles `{"base": "point", "arm_n": 110, "head": -12}`.
- **Expressions (`expr`):** `neutral`, `happy`, `joy`, `angry`, `shout`, `sad`, `surprised`, `afraid`, `determined`, `smug`, `worried`, `sleep`.
- **Mounts (`mount`):** `"horse"`, `"camel"`, `"elephant"`, `"chariot"`, `"cart"`, `"carriage"`, `"tank"`, `"train"`, `"car"`, `"biplane"` (or a dict `{"type": "horse", "color": "chestnut", "tack": "gold"}`).

### World Layers & Items (`layers`)

Layers are sorted far-to-near by `depth` (`depth: 6` moves slowly in parallax and fades into atmospheric perspective; `depth: 1` is the main stage; `depth: 0.6` moves faster in the foreground and can have `"blur": 6` or `"blur": [8, 0]` for rack focus).

- **Nature:** `mountains`, `hills`, `tree` (`round`, `oak`, `olive`, `palm`, `pine`, `cypress`, `bare`), `bush`, `rock`, `grass`, `water`, `sun`, `moon` (`crescent: true`), `stars`, `clouds`, `smoke`, `fire`.
- **Architecture:** `wall` (`crenel: true`), `tower` (`crenel`, `cone`, `dome`, `onion`, `pyramid`), `building` (`gable`, `hip`, `flat`, `dome`, `pagoda`, `thatch`), `arch`/`gate` (`round`, `pointed`, `horseshoe`, `flat`), `column`/`colonnade` (`doric`, `ionic`, `lotus`, `plain`), `dome`, `minaret`, `tent` (`cone`, `yurt`, `pavilion`), `pyramid` (`stepped`), `obelisk`, `skyline`/`city`, `room` (1-point perspective interior), `bridge`, `ruins`, `barricade`/`trench`, `statue`, `banner`, `furniture` (`table`, `map_table`, `chair`, `throne`, `bench`, `chest`, `barrel`, `crate`, `bed`, `carpet`, `candle`, `bookshelf`, `globe`, `fireplace`).
- **Vehicles & Weapons:** `ship` (`galley`, `longship`, `cog`, `galleon`, `dhow`, `junk`, `steamship`), `cannon` (`fire: 1.2` triggers recoil + smoke flash + auto cannon boom), `mount`/`vehicle`.
- **Crowds & Armies:** `crowd`/`army` (`x0`, `x1`, `rows`, `count`, `colors`, `head`, `carry: "spear"|"pike"|"flag"|"shield"`, `march`, `advance`, `cheer`).
- **Historical Graphics:**
  - `map`: `lands`, `territories` (with `grow: [t0, t1]`), `routes` (animated arrows `from`..`to`), `pins` (`city`, `star`, `battle` with `pulse: true`), `compass`.
  - `timeline`: `start_year`, `end_year`, `events`, sliding `marker: [from_year, to_year]`.
  - `document`: `scroll`, `decree`, `tablet` with animated wax `seal` at `seal_t`.

### Lighting & Screen FX (`veil`, `lights`, `fx`, `text`)
- `veil`: `0..0.6` darkens the frame except where `lights` punch soft holes.
- `lights`: `[{"x": 960, "y": 650, "r": 500, "color": "#ffa84a", "strength": 0.4, "flicker": 1}]`.
- `fx`: `"dust"`, `"embers"`, `"snow"`, `"rain"`, `"ash"`, `"fog"`, `"rays"`, `{"kind": "flash", "t": 1.0}`, `{"kind": "tint", "color": "#000", "amount": 0.2}`.
- `text`:
  - `{"kind": "title", "text": "LINE 1\nLINE 2", "sub": "SUBTITLE", "t": 0.2}`
  - `{"kind": "year", "from": 1400, "to": 1453, "sub": "CONSTANTINOPLE", "t": 0.1}`
  - `{"kind": "label", "text": "Sultan Mehmed II", "sub": "21 APRIL 1453", "t": 0.3}`
  - `{"kind": "caption", "text": "Short emphasis text", "t": 0.2}`
  - `{"kind": "card", "text": "Sourced historical fact...", "source": "Source: ...", "t": "40%"}`
