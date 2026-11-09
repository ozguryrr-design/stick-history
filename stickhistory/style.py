"""The channel's look: palettes, line, faces, texture, camera energy, type. Built from profile.json.

Every colour that comes from an episode (a kaftan's red, a wall's ochre) goes through Style.c(), which pulls it toward
the palette's tint, so any period's real colours sit inside the channel's mood.
"""
import json
import pathlib

from .svg import mix, shade, rng

# Sky and ground per time of day: (sky top, sky bottom, ground near, ground far, ambient light colour)
PALETTES = {
    'parchment': {
        'label': 'Parchment & sepia: warm paper, brown ink, old-book calm',
        'tint': '#b08850', 'tint_amount': 0.35, 'ink': '#3a2a1c', 'paper': '#efe1c3', 'accent': '#a8432a',
        'head': '#f6ead2', 'skins': ['#f1d9b5', '#d9b48a', '#b88a5e', '#8a6040', '#5e3f2a'],
        'times': {
            'day': ('#e9d6ac', '#f4e8cc', '#cdb284', '#ddc79d', '#fff4dc'),
            'dawn': ('#d9b893', '#f2dcb8', '#bfa077', '#d3b78d', '#ffe6c4'),
            'dusk': ('#a87b55', '#e7c08c', '#9c7a52', '#b8946a', '#ffd29a'),
            'night': ('#4d3d2e', '#7a6249', '#5a4834', '#6b5640', '#e8c88f'),
            'interior': ('#c9ab7f', '#dcc39a', '#a98a62', '#bb9c72', '#ffe2b0'),
            'storm': ('#7d6c58', '#a8957a', '#86735a', '#978268', '#f0e0c0'),
        },
    },
    'midnight': {
        'label': 'Midnight blue: dark and cinematic, lamplight and moonlight',
        'tint': '#24345c', 'tint_amount': 0.32, 'ink': '#0d1220', 'paper': '#151d33', 'accent': '#ffb347',
        'head': '#f3ead8', 'skins': ['#f0d6b8', '#d6ae86', '#b0825a', '#7f5a3c', '#553a28'],
        'times': {
            'day': ('#5f7fb0', '#a9bfd8', '#4a5a6e', '#62738a', '#fff2d6'),
            'dawn': ('#2e3f6e', '#d89a7a', '#3a4258', '#4c5470', '#ffcf9e'),
            'dusk': ('#1b2447', '#c46a4f', '#2a2f45', '#3a3f5c', '#ffb070'),
            'night': ('#070b1a', '#1c2a4f', '#141a2c', '#1d2540', '#ffcc80'),
            'interior': ('#1a2238', '#2c3654', '#232a40', '#2d3550', '#ffc27a'),
            'storm': ('#1a2030', '#3d4a60', '#20283a', '#2c3548', '#cfe0ff'),
        },
    },
    'pastel': {
        'label': 'Soft pastel: gentle, airy, friendly',
        'tint': '#e7c9d6', 'tint_amount': 0.3, 'ink': '#4a4458', 'paper': '#fbf3ee', 'accent': '#ef8a7a',
        'head': '#fff8f0', 'skins': ['#fde3cf', '#f0c7a5', '#d7a17c', '#b07a58', '#8a5c42'],
        'times': {
            'day': ('#bfe0f2', '#fdf0e6', '#cfe5c4', '#dcebd2', '#fffaf0'),
            'dawn': ('#f6d5e1', '#fff0dc', '#e3dcc6', '#ece6d3', '#fff0e0'),
            'dusk': ('#c7b6e0', '#f7cdb8', '#c9c0cf', '#d6cdd9', '#ffe0cc'),
            'night': ('#5c5f8f', '#9b93c0', '#7a7b9e', '#8a89ab', '#fff0d0'),
            'interior': ('#f2e3dc', '#f8ece6', '#e3d0c6', '#ead9d0', '#fff3e6'),
            'storm': ('#a9b4c4', '#d6dbe2', '#b4bcc4', '#c3c9d0', '#f6f8ff'),
        },
    },
    'engraving': {
        'label': 'Engraving: black and white like an old print, one red accent',
        'tint': '#808080', 'tint_amount': 0.85, 'ink': '#111111', 'paper': '#f2efe8', 'accent': '#c0262d',
        'head': '#fbfaf6', 'skins': ['#e8e6e0', '#d2cfc8', '#b9b5ad', '#9c978e', '#7d7870'],
        'times': {
            'day': ('#e6e3dc', '#f6f4ef', '#cfccc4', '#dcd9d2', '#ffffff'),
            'dawn': ('#d6d2ca', '#efece6', '#c4c0b8', '#d2cec6', '#ffffff'),
            'dusk': ('#9c9890', '#dcd8d0', '#aaa69e', '#bab6ae', '#ffffff'),
            'night': ('#2a2a2a', '#5a5a58', '#3a3a38', '#4a4a48', '#f0f0f0'),
            'interior': ('#c8c5be', '#dcd9d2', '#b4b1aa', '#c2bfb8', '#ffffff'),
            'storm': ('#6e6c68', '#a09e98', '#7c7a76', '#8c8a86', '#ffffff'),
        },
    },
    'golden': {
        'label': 'Golden hour: warm sunset light, long shadows, epic',
        'tint': '#e09a4a', 'tint_amount': 0.28, 'ink': '#2a1810', 'paper': '#3a2418', 'accent': '#ffd27a',
        'head': '#fff1dc', 'skins': ['#f6d6b0', '#e0b083', '#bf8a5a', '#8e5e3a', '#603e26'],
        'times': {
            'day': ('#f0b46a', '#ffe2a8', '#a8774a', '#c49262', '#fff0c8'),
            'dawn': ('#e48a6a', '#ffd3a0', '#9a6a4a', '#b6845e', '#ffe0b0'),
            'dusk': ('#7a3a4a', '#ffae5a', '#6a4430', '#8a5c40', '#ffc070'),
            'night': ('#2a1a2e', '#6a3a40', '#2e2020', '#3e2c2a', '#ffb060'),
            'interior': ('#7a4a30', '#b8784a', '#5e3a26', '#704832', '#ffc078'),
            'storm': ('#5a4038', '#9a7458', '#5a463a', '#6a5444', '#ffd8a0'),
        },
    },
    'fresco': {
        'label': 'Fresco & earth: terracotta, ochre and olive, ancient walls',
        'tint': '#b0704a', 'tint_amount': 0.3, 'ink': '#3b2418', 'paper': '#e8d2b0', 'accent': '#2f6f73',
        'head': '#f7e6cc', 'skins': ['#f0d0a8', '#d8a878', '#b47c50', '#8a5a36', '#5e3c24'],
        'times': {
            'day': ('#d9b98e', '#efdcbc', '#b98c5c', '#c9a072', '#fff0d4'),
            'dawn': ('#d1a080', '#ecd0aa', '#ad8058', '#bf946a', '#ffe2bc'),
            'dusk': ('#9a5a44', '#dca070', '#8c5e3e', '#a07050', '#ffcc90'),
            'night': ('#3e2a26', '#6e4a3a', '#4a3428', '#5a4032', '#f0c080'),
            'interior': ('#c08a60', '#d8aa7c', '#9a6c46', '#ad7c54', '#ffd6a0'),
            'storm': ('#7a6250', '#a68a70', '#806a54', '#907a62', '#f0dcc0'),
        },
    },
    'miniature': {
        'label': 'Miniature: flat lapis, vermilion and gold, like an illuminated manuscript',
        'tint': '#c8a04a', 'tint_amount': 0.18, 'ink': '#1a1a3a', 'paper': '#f3e6c4', 'accent': '#c8302a',
        'head': '#fbf0dc', 'skins': ['#f6dcc0', '#e4bc94', '#c4946a', '#946644', '#68462e'],
        'times': {
            'day': ('#2f5aa8', '#7fa6d8', '#c9a85a', '#d8bc72', '#fff4d8'),
            'dawn': ('#3a4f98', '#e8b07a', '#b89650', '#ccaa66', '#ffe6c0'),
            'dusk': ('#1f2c6a', '#d88a5a', '#9c7c40', '#b09054', '#ffd090'),
            'night': ('#0f1640', '#2a3a7a', '#5a4c2a', '#6a5a34', '#ffe0a0'),
            'interior': ('#a8343a', '#c8584a', '#c8a050', '#d4b064', '#ffe8c0'),
            'storm': ('#3a4a6a', '#7888a8', '#8a7a50', '#9a8a60', '#f0f0ff'),
        },
    },
}

LINES = {
    'clean': {'label': 'Thin and clean', 'limb': 7.0, 'outline': 0.0, 'boil': 0.0},
    'bold': {'label': 'Bold and chunky', 'limb': 12.0, 'outline': 2.5, 'boil': 0.0},
    'sketch': {'label': 'Sketchy, the line wobbles a little (boiling)', 'limb': 7.5, 'outline': 0.0, 'boil': 1.6},
    'brush': {'label': 'Brush stroke, thick and tapered', 'limb': 10.0, 'outline': 0.0, 'boil': 0.6},
}

FACES = {
    'none': 'Faceless: the body acts, the head is a plain circle',
    'dots': 'Dot eyes only',
    'expressive': 'Expressive: eyes, brows and mouth',
}

TEXTURES = {
    'flat': 'Flat and clean',
    'paper': 'Paper grain and soft vignette',
    'film': 'Old film: grain, vignette, a slight flicker',
}

CAMERA = {
    'calm': {'label': 'Calm documentary: slow drifts and dissolves', 'speed': 0.7, 'shake': 0.5, 'blur': 0.6},
    'dynamic': {'label': 'Dynamic: push-ins, pans, whip pans on beats', 'speed': 1.0, 'shake': 1.0, 'blur': 1.0},
    'energetic': {'label': 'High energy: fast moves, snaps, shakes, many cuts', 'speed': 1.35, 'shake': 1.5,
                  'blur': 1.3},
}

FONTS = {
    'serif': {'label': 'Classic serif', 'family': 'EB Garamond, Noto Serif, DejaVu Serif, serif'},
    'sans': {'label': 'Modern sans', 'family': 'Outfit, Noto Sans, DejaVu Sans, sans-serif'},
    'hand': {'label': 'Handwritten', 'family': 'Caveat, Comic Neue, cursive'},
    'inscription': {'label': 'Carved inscription (capitals)', 'family': 'Cinzel, Noto Serif, DejaVu Serif, serif'},
}

ENDINGS = {
    'question': 'Ends on a question to the viewer',
    'next': 'Ends on what happened next ("to be continued")',
    'fact': 'Ends on a sourced fact card',
}

DEFAULT_PROFILE = {
    'palette': 'midnight', 'line': 'clean', 'face': 'dots', 'texture': 'paper', 'camera': 'dynamic',
    'font': 'serif', 'ending': 'question', 'seed': 1, 'overrides': {},
}


def quiz():
    """The first-run questions, with their options, as data (the agent asks them in its own words)."""
    return {
        'palette': {k: v['label'] for k, v in PALETTES.items()} | {'surprise': 'Surprise me: a palette made from the channel seed'},
        'line': {k: v['label'] for k, v in LINES.items()},
        'face': FACES,
        'texture': TEXTURES,
        'camera': {k: v['label'] for k, v in CAMERA.items()},
        'font': {k: v['label'] for k, v in FONTS.items()},
        'ending': ENDINGS,
    }


def surprise_palette(seed):
    """A palette of its own, built from a base palette shifted by the seed."""
    r = rng('palette', seed)
    base = PALETTES[r.choice(list(PALETTES))]
    tint = '#%02x%02x%02x' % tuple(r.randint(60, 220) for _ in range(3))
    p = json.loads(json.dumps(base))
    p['label'] = f'Surprise palette (seed {seed})'
    p['tint'] = tint
    p['tint_amount'] = 0.2 + r.random() * 0.2
    p['accent'] = '#%02x%02x%02x' % tuple(r.randint(120, 255) for _ in range(3))
    p['times'] = {k: tuple(mix(c, tint, 0.25) for c in v) for k, v in base['times'].items()}
    return p


class Style:
    def __init__(self, profile=None):
        prof = dict(DEFAULT_PROFILE)
        prof.update(profile or {})
        self.profile = prof
        self.seed = prof.get('seed', 1)
        if prof['palette'] == 'surprise':
            self.pal = surprise_palette(self.seed)
        else:
            self.pal = json.loads(json.dumps(PALETTES[prof['palette']]))
        self.pal.update(prof.get('overrides', {}))
        self.line = LINES[prof['line']]
        self.face = prof['face']
        self.texture = prof['texture']
        self.camera = CAMERA[prof['camera']]
        self.font = FONTS[prof['font']]['family']
        self.ink = self.pal['ink']
        self.accent = self.pal['accent']

    def c(self, color, amount=None):
        """A real-world colour, pulled toward the palette's tint so it belongs to this look."""
        if not color or color == 'none':
            return 'none'
        if color == 'ink':
            return self.ink
        if color == 'accent':
            return self.accent
        if color == 'head':
            return self.pal['head']
        if color.startswith('skin'):
            i = int(color[4:] or 1) - 1
            return self.pal['skins'][max(0, min(4, i))]
        if not color.startswith('#'):
            color = NAMED.get(color, '#888888')
        a = self.pal['tint_amount'] if amount is None else amount
        return mix(color, self.pal['tint'], a)

    def times(self, tod):
        top, bottom, ground, far, light = self.pal['times'].get(tod, self.pal['times']['day'])
        return {'sky_top': top, 'sky_bottom': bottom, 'ground': ground, 'ground_far': far, 'light': light}

    def depth_tint(self, color, depth, tod):
        """Atmospheric perspective: far things fade toward the horizon colour."""
        if depth <= 1:
            return color
        fade = min(0.85, (depth - 1) * 0.22)
        return mix(color, self.times(tod)['sky_bottom'], fade)

    def shade(self, color, u):
        return shade(color, u)


NAMED = {
    'red': '#b8322a', 'crimson': '#9e1b32', 'scarlet': '#d0312d', 'maroon': '#6b1f24', 'orange': '#d9822b',
    'gold': '#d4a83a', 'yellow': '#e3c547', 'ochre': '#c48a3a', 'olive': '#7a7a3a', 'green': '#3f7a45',
    'emerald': '#2a7a5a', 'teal': '#2f7a7a', 'turquoise': '#3aa6a0', 'blue': '#2f5aa0', 'navy': '#1f2f5a',
    'lapis': '#26478f', 'indigo': '#3a3478', 'purple': '#6a3a7a', 'violet': '#7a4aa0', 'pink': '#d98aa0',
    'white': '#f2efe6', 'ivory': '#efe6cc', 'cream': '#ece0bf', 'beige': '#d6c29a', 'tan': '#c09a6a',
    'brown': '#6e4a2e', 'chestnut': '#7a3f22', 'grey': '#8a8a8a', 'gray': '#8a8a8a', 'steel': '#9aa4ae',
    'iron': '#5a6068', 'silver': '#c4c8cc', 'bronze': '#a8783a', 'copper': '#b8683a', 'black': '#1e1e22',
    'stone': '#a89c88', 'sandstone': '#d2b48a', 'marble': '#e6e2da', 'brick': '#a4523a', 'wood': '#8a5a34',
    'straw': '#d8c07a', 'linen': '#e2d8c0', 'wool': '#cbbfa6', 'leather': '#7a5232', 'khaki': '#a89a6a',
    'field_grey': '#6e7468', 'sky': '#8ab4d8', 'water': '#3a6a8a', 'sand': '#dcc496', 'snow': '#f0f4f8',
    'grass': '#6a9a4a', 'forest': '#2e5a34', 'earth': '#7a5a3a', 'terracotta': '#c0603a',
    'lead': '#7d858e', 'brass': '#c09a48', 'mud': '#6a5638', 'rust': '#8a4a2a', 'plaster': '#e4d6bc',
}


def load_profile(project_dir):
    p = pathlib.Path(project_dir) / 'profile.json'
    if p.exists():
        return json.loads(p.read_text(encoding='utf-8'))
    return None
