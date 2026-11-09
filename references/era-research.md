# Researching & Building Any Historical Era

**Never restrict the user to pre-packaged eras.** The stick-figure aesthetic is intentionally simple so that any century, culture, and geography can be built accurately from parametric parts in minutes.

## 1. Write `brief.json` Before `scenes.json`

Every episode starts with historical research saved in `episodes/<slug>/brief.json`:

```json
{
  "topic": "User's topic",
  "event": "Specific historical event",
  "date": "Exact date or year range",
  "place": "Geography & setting",
  "formats": ["16:9", "9:16"],
  "people": [
    {"id": "hannibal", "name": "Hannibal Barca", "role": "Carthaginian general"}
  ],
  "clothing": {
    "general": "Bronze crested helmet, linen cuirass (linothorax) over red tunic, wool cloak",
    "soldier": "Conical/round bronze helmet, tunic, round/oval shield, spear"
  },
  "objects": ["spear", "round shield", "war elephant"],
  "architecture": ["punic stone walls", "mountain pass", "army camp tents"],
  "landscape": "Snowy Alpine mountain pass, pine and bare trees, rocks",
  "avoid": ["stirrups", "plate armor", "gunpowder", "medieval castle"],
  "facts": [
    {
      "claim": "Hannibal crossed the Alps in autumn 218 BCE with 37 war elephants.",
      "source": "Polybius, Histories, Book III"
    }
  ],
  "sources": ["Polybius, Histories III", "Livy, Ab Urbe Condita XXI"]
}
```

`run.py check <slug>` inspects `brief.json`:
- Warns if `sources` is empty.
- Scans `scenes.json` for any term listed in `avoid` to catch accidental anachronisms.

---

## 2. How to Dress Any Period on the Rig

Characters are dressed by combining `head` (a list of headwear shapes) and `outfit` (a list of garments), plus `hair`, `beard`, `mustache`, `sleeves`, `legwear`, `shoes`, `mount`, and `hold`.

### Headwear Recipes Across Eras

| Era / Role | `head` list recipe |
|---|---|
| **Ancient Egyptian Pharaoh** | `[{"shape": "hood", "color": "lapis", "h": 1.55}, {"shape": "band", "color": "gold"}]` |
| **Mesopotamian / Persian King** | `[{"shape": "cylinder", "color": "gold", "h": 1.15, "w": 0.95, "taper": 0.9, "band": true}]` (+ `"beard": {"style": "long"}`) |
| **Greek Hoplite / Roman Legionary** | `[{"shape": "cap", "color": "bronze", "h": 1.15}, {"shape": "crest", "color": "crimson"}, {"shape": "cheek", "color": "bronze"}]` |
| **Roman Senator / Emperor** | `[{"shape": "wreath", "color": "gold"}]` |
| **Viking / Early Medieval Warrior** | `[{"shape": "cap", "color": "iron", "h": 1.05}, {"shape": "nasal", "color": "iron"}]` (*Never put horns on historical Vikings unless depicting ritual Bronze Age helmets!*) |
| **Medieval European King / Queen** | `[{"shape": "band", "color": "gold"}, {"shape": "points", "color": "gold", "count": 5, "gem": "crimson"}]` |
| **Medieval Monk / Scholar** | `[{"shape": "hood", "color": "brown"}]` |
| **Steppe / Mongol / Turkic Rider** | `[{"shape": "cone", "color": "brown", "h": 1.1, "band": true, "accent": "leather"}, {"shape": "flap", "color": "leather", "h": 1.1}]` |
| **Ottoman / Abbasid / Mughal Ruler** | `[{"shape": "dome", "color": "white", "h": 1.15, "w": 1.25, "wrap": 3}, {"shape": "plume", "color": "white", "px": 0.25, "py": -1.35, "h": 0.8}]` |
| **Ottoman Janissary (Börk)** | `[{"shape": "cylinder", "color": "white", "h": 1.4, "w": 0.9, "round_top": true, "band": true}, {"shape": "flap", "color": "white", "h": 1.6}]` |
| **19th c. Ottoman / Reform Official (Fez)** | `[{"shape": "cylinder", "color": "crimson", "h": 0.95, "w": 0.88, "taper": 0.86, "tassel": "black"}]` |
| **Chinese Imperial Scholar / Tang Official** | `[{"shape": "cylinder", "color": "black", "h": 0.85, "w": 0.9, "round_top": true}, {"shape": "band", "color": "black", "w": 1.6, "h": 0.12}]` |
| **Edo Samurai / Ashigaru** | `[{"shape": "cone", "color": "iron", "h": 0.65, "w": 1.55}, {"shape": "flap", "color": "iron", "h": 0.9}]` |
| **Mesoamerican / Indigenous Noble** | `[{"shape": "band", "color": "gold"}, {"shape": "feathers", "color": "emerald", "count": 7}]` |
| **18th–19th c. Officer / Explorer** | `[{"shape": "cap", "color": "navy", "h": 0.95}, {"shape": "brim", "color": "navy", "w": 1.6, "h": 0.14}]` |
| **WWI / WWII Soldier** | `[{"shape": "cap", "color": "field_grey", "h": 0.92}, {"shape": "brim", "color": "field_grey", "w": 1.35, "h": 0.1}]` |

### Garment Recipes Across Eras

- **Ancient tunics & kilts:** `[{"kind": "skirt", "color": "linen", "length": 0.4}, {"kind": "collar", "color": "gold"}, {"kind": "sash", "color": "gold", "tails": true}]`
- **Toga / draped robe:** `[{"kind": "toga", "color": "ivory", "trim": "crimson"}]`
- **Scale or chain armor over tunic:** `[{"kind": "tunic", "color": "crimson"}, {"kind": "armor", "color": "steel", "pattern": "scales"}, {"kind": "belt", "color": "leather"}]`
- **Kaftan / long court robe:** `[{"kind": "kaftan", "color": "crimson", "trim": "gold", "pattern": "center", "pattern_color": "gold"}, {"kind": "sash", "color": "gold"}]`
- **Military coat / modern uniform:** `[{"kind": "uniform", "color": "khaki", "open": true, "buttons": "bronze"}, {"kind": "belt", "color": "leather"}, {"kind": "epaulettes", "color": "gold"}]`

---

## 3. Building Period Architecture & Sets

Combine world items across depth layers (`depth: 6` far, `depth: 2..3` mid, `depth: 1` near):
- **Antiquity:** `pyramid` (`stepped: true` for Mesopotamia/Mesoamerica, smooth for Egypt), `obelisk`, `colonnade` (`style: "lotus"`, `"doric"`, or `"ionic"`), `ruins`, `statue`, `chariot`.
- **Classical & Medieval:** `wall` (`crenel: true`, `texture: "blocks"`), `tower` (`roof: "crenel"` or `"cone"`), `arch` (`style: "round"`, `"pointed"`, or `"horseshoe"`), `bridge`, `barricade` (`type: "palisade"`).
- **Islamic / Ottoman / Persian / South Asian:** `dome` (`drum: 60`, `finial: "crescent"`, or `onion: true`), `minaret`, `arch` (`style: "pointed"` or `"horseshoe"`), `room` (`pattern: "tiles"`), `tent` (`type: "pavilion"`).
- **Steppe / Nomadic:** `hills`, `mountains`, `tent` (`type: "yurt"`), `mount` (`type: "horse"` or `"camel"`), `fire`.
- **East Asian:** `building` (`roof: "pagoda"`, `tiers: 3`), `ship` (`type: "junk"`), `bridge`.
- **Maritime / Age of Sail:** `water`, `ship` (`type: "galley"`, `"longship"`, `"dhow"`, `"cog"`, `"galleon"`, `"junk"`, `"steamship"`), `cannon`.
- **Industrial / Modern:** `skyline` (`flavor: ["block", "smokestack", "gable"]`), `barricade` (`type: "trench"`, `wire: true`), `mount` (`type: "train"`, `"tank"`, `"car"`, `"biplane"`).

---

## 4. The `"svg"` Escape Hatch

Whenever a historical story hinges on a specific artifact that isn't a standard primitive (e.g., the Rosetta Stone, Sputnik, a printing press, the Wright Flyer, a Trojan Horse), draw it with `"kind": "svg"` (in world items, props, headwear, or garments):

```json
{
  "kind": "svg",
  "x": 960,
  "y": 860,
  "scale": 1.2,
  "svg": "<rect x='-60' y='-180' width='120' height='180' rx='12' fill='#3a3a40' stroke='#111' stroke-width='4'/>"
}
```
