"""Hand props, drawn in the hand's frame: grip at the origin, the prop's main axis along +x.

The rig rotates the frame to the forearm's direction plus the prop's `angle` (default -90: the prop stands up when the
forearm points forward). Everything is in character units (a character is about 300 tall at scale 1), facing right.
Props that should stay upright whatever the arm does (shields, lanterns, books held up) set `upright`.
"""
import math

from .svg import n, line, circle, polygon, path, rect, ellipse, group, smooth_path, noise1, shade


def _c(S, spec, key, default):
    return S.c(spec.get(key, default))


def sword(S, p, t, ink, lw):
    L = p.get('length', 100)
    blade = _c(S, p, 'color', 'steel')
    hilt = _c(S, p, 'hilt', 'gold')
    return (
        line((-16, 0), (6, 0), stroke=ink, stroke_width=lw + 1, stroke_linecap='round') +
        polygon([(8, -3.5), (8 + L, -2), (14 + L, 0), (8 + L, 2), (8, 3.5)], fill=blade, stroke=ink, stroke_width=lw * 0.35) +
        line((6, -13), (6, 13), stroke=hilt, stroke_width=lw * 0.9, stroke_linecap='round') +
        circle((-18, 0), 4.5, fill=hilt, stroke=ink, stroke_width=lw * 0.3)
    )


def saber(S, p, t, ink, lw):
    L = p.get('length', 100)
    blade = _c(S, p, 'color', 'steel')
    hilt = _c(S, p, 'hilt', 'gold')
    cv = p.get('curve', 0.22) * L
    d = (f'M8 -3 Q{n(L * 0.6)} {n(-3 - cv * 0.2)} {n(L + 8)} {n(-cv)} '
         f'Q{n(L * 0.62)} {n(5 - cv * 0.1)} 8 4 Z')
    return (
        line((-16, 0), (6, 0), stroke=ink, stroke_width=lw + 1, stroke_linecap='round') +
        path(d, fill=blade, stroke=ink, stroke_width=lw * 0.35) +
        line((6, -9), (6, 9), stroke=hilt, stroke_width=lw * 0.8, stroke_linecap='round')
    )


def dagger(S, p, t, ink, lw):
    q = dict(p)
    q.setdefault('length', 38)
    return sword(S, q, t, ink, lw)


def spear(S, p, t, ink, lw):
    L = p.get('length', 260)
    back = p.get('back', 0.35) * L
    shaft = _c(S, p, 'shaft', 'wood')
    tip = _c(S, p, 'color', 'steel')
    front = L - back
    out = line((-back, 0), (front, 0), stroke=ink, stroke_width=lw * 0.9 + 2, stroke_linecap='round')
    out += line((-back, 0), (front, 0), stroke=shaft, stroke_width=lw * 0.6, stroke_linecap='round')
    out += polygon([(front - 2, -6), (front + 26, 0), (front - 2, 6)], fill=tip, stroke=ink, stroke_width=lw * 0.35)
    if p.get('pennant'):
        pc = S.c(p['pennant'])
        w = noise1(t * 3, 7) * 4
        out += polygon([(front - 30, 0), (front - 6, 0), (front - 18, 26 + w)], fill=pc, stroke=ink, stroke_width=lw * 0.3)
    return out


def pike(S, p, t, ink, lw):
    q = dict(p)
    q.setdefault('length', 420)
    q.setdefault('back', 0.3)
    return spear(S, q, t, ink, lw)


def staff(S, p, t, ink, lw):
    L = p.get('length', 230)
    back = p.get('back', 0.55) * L
    col = _c(S, p, 'color', 'wood')
    out = line((-back, 0), (L - back, 0), stroke=ink, stroke_width=lw * 0.9 + 2, stroke_linecap='round')
    out += line((-back, 0), (L - back, 0), stroke=col, stroke_width=lw * 0.65, stroke_linecap='round')
    top = p.get('top')
    if top == 'crook':
        out += path(f'M{n(L - back)} 0 q 22 0 22 -16 q 0 -14 -14 -12', fill='none', stroke=col, stroke_width=lw * 0.65,
                    stroke_linecap='round')
    elif top == 'orb':
        out += circle((L - back + 8, 0), 9, fill=S.c(p.get('top_color', 'gold')), stroke=ink, stroke_width=lw * 0.3)
    return out


def axe(S, p, t, ink, lw):
    L = p.get('length', 90)
    head = _c(S, p, 'color', 'iron')
    out = line((-18, 0), (L, 0), stroke=ink, stroke_width=lw * 0.9 + 2, stroke_linecap='round')
    out += line((-18, 0), (L, 0), stroke=_c(S, p, 'shaft', 'wood'), stroke_width=lw * 0.6, stroke_linecap='round')
    out += path(f'M{n(L - 18)} -2 L{n(L - 22)} -26 Q{n(L + 6)} -22 {n(L + 4)} -2 Z', fill=head, stroke=ink, stroke_width=lw * 0.35)
    return out


def hammer(S, p, t, ink, lw):
    L = p.get('length', 70)
    out = line((-14, 0), (L, 0), stroke=_c(S, p, 'shaft', 'wood'), stroke_width=lw * 0.7, stroke_linecap='round')
    out += rect(L - 6, -16, 16, 32, rx=3, fill=_c(S, p, 'color', 'iron'), stroke=ink, stroke_width=lw * 0.35)
    return out


def bow(S, p, t, ink, lw):
    h = p.get('length', 140) / 2
    draw = p.get('draw', 0.0)  # 0 relaxed .. 1 fully drawn
    col = _c(S, p, 'color', 'wood')
    out = path(f'M0 {n(-h)} Q{n(h * 0.75)} 0 0 {n(h)}', fill='none', stroke=ink, stroke_width=lw * 0.9 + 2, stroke_linecap='round')
    out += path(f'M0 {n(-h)} Q{n(h * 0.75)} 0 0 {n(h)}', fill='none', stroke=col, stroke_width=lw * 0.6, stroke_linecap='round')
    sx = -draw * 45
    out += path(f'M0 {n(-h)} L{n(sx)} 0 L0 {n(h)}', fill='none', stroke=shade(S.ink, 0.35), stroke_width=1.5)
    if p.get('arrow', True) and draw > 0.05:
        out += line((sx, 0), (sx + 110, 0), stroke=S.ink, stroke_width=2.5)
        out += polygon([(sx + 110, -4), (sx + 122, 0), (sx + 110, 4)], fill=S.ink)
    return group(out, transform='rotate(90)')


def flag(S, p, t, ink, lw):
    L = p.get('length', 260)
    back = p.get('back', 0.35) * L
    front = L - back
    colors = [S.c(c) for c in p.get('colors', ['red'])]
    W, H = p.get('w', 110), p.get('h', 72)
    out = line((-back, 0), (front, 0), stroke=ink, stroke_width=lw * 0.8 + 2, stroke_linecap='round')
    out += line((-back, 0), (front, 0), stroke=_c(S, p, 'pole', 'wood'), stroke_width=lw * 0.55, stroke_linecap='round')
    if p.get('finial', True):
        out += circle((front + 6, 0), 6, fill=S.c(p.get('finial_color', 'gold')), stroke=ink, stroke_width=1.5)
    # cloth hangs off the pole's top, perpendicular, waving
    cloth = _wave_cloth(front - H, W, H, t, p.get('wind', 1.0))
    stripes = p.get('stripes', 'vertical')
    k = len(colors)
    body = ''
    for i, c in enumerate(colors):
        a, b = i / k, (i + 1) / k
        if stripes == 'horizontal':
            quad = [cloth(0, a), cloth(1, a), cloth(1, b), cloth(0, b)]
            quad = _refine(cloth, (0, a), (1, b), horizontal=True)
        else:
            quad = _refine(cloth, (a, 0), (b, 1), horizontal=False)
        body += polygon(quad, fill=c)
    outline = _refine(cloth, (0, 0), (1, 1), horizontal=False)
    body += polygon(outline, fill='none', stroke=ink, stroke_width=lw * 0.3)
    em = p.get('emblem')
    if em:
        cx, cy = cloth(0.45, 0.5)
        body += emblem(S, em, (cx, cy), H * 0.28, p.get('emblem_color', 'white'), ink)
    return out + body


def _wave_cloth(x0, W, H, t, wind):
    """Cloth point at (u along fly, v along hoist); the hoist runs along the pole (x), the fly hangs out in +y."""
    def at(u, v):
        wave = math.sin(u * 5.0 - t * 7.0 * wind) * 7 * u * wind
        sag = u * u * 10 * (1.2 - wind * 0.6)
        return (x0 + v * H + sag * 0.4 + wave * 0.3, u * W + wave * 0.15 + sag * 0.1 + math.cos(u * 4 - t * 6) * 3 * u)
    return at


def _refine(cloth, a, b, horizontal, steps=8):
    (u0, v0), (u1, v1) = a, b
    top = [cloth(u0 + (u1 - u0) * i / steps, v0) for i in range(steps + 1)]
    bot = [cloth(u0 + (u1 - u0) * i / steps, v1) for i in range(steps, -1, -1)]
    return top + bot


def emblem(S, kind, c, r, color, ink):
    col = S.c(color)
    x, y = c
    if kind == 'crescent':
        tx, ty = x + r * 0.5, r * 0.866
        return path(f'M{n(tx)} {n(y - ty)} A{n(r)} {n(r)} 0 1 0 {n(tx)} {n(y + ty)} '
                    f'A{n(r * 0.95)} {n(r * 0.95)} 0 0 1 {n(tx)} {n(y - ty)} Z', fill=col)
    if kind == 'crescent_star':
        return emblem(S, 'crescent', (x - r * 0.2, y), r, color, ink) + emblem(S, 'star', (x + r * 0.75, y), r * 0.45, color, ink)
    if kind == 'star':
        ptsl = []
        for i in range(10):
            a = -math.pi / 2 + i * math.pi / 5
            rr = r if i % 2 == 0 else r * 0.42
            ptsl.append((x + rr * math.cos(a), y + rr * math.sin(a)))
        return polygon(ptsl, fill=col)
    if kind == 'cross':
        w = r * 0.32
        return rect(x - w / 2, y - r, w, 2 * r, fill=col) + rect(x - r, y - w / 2, 2 * r, w, fill=col)
    if kind == 'circle':
        return circle((x, y), r, fill=col)
    if kind == 'eagle':
        d = (f'M{n(x)} {n(y - r * 0.6)} l{n(r * 0.25)} {n(r * 0.3)} l{n(r * 0.75)} {n(-r * 0.45)} l{n(-r * 0.3)} {n(r * 0.75)} '
             f'l{n(-r * 0.35)} {n(r * 0.1)} l{n(-r * 0.05)} {n(r * 0.6)} l{n(-r * 0.25)} {n(-r * 0.4)} l{n(-r * 0.25)} {n(r * 0.4)} '
             f'l{n(-r * 0.05)} {n(-r * 0.6)} l{n(-r * 0.35)} {n(-r * 0.1)} l{n(-r * 0.3)} {n(-r * 0.75)} l{n(r * 0.75)} {n(r * 0.45)} Z')
        return path(d, fill=col)
    if kind == 'sun':
        out = circle((x, y), r * 0.5, fill=col)
        for i in range(12):
            a = i * math.pi / 6
            out += line((x + r * 0.62 * math.cos(a), y + r * 0.62 * math.sin(a)), (x + r * math.cos(a), y + r * math.sin(a)),
                        stroke=col, stroke_width=r * 0.12, stroke_linecap='round')
        return out
    if kind == 'lion':
        return circle((x, y), r * 0.75, fill=col) + circle((x + r * 0.2, y - r * 0.1), r * 0.35, fill=ink, fill_opacity=0.25)
    return ''


def scroll(S, p, t, ink, lw):
    col = _c(S, p, 'color', 'cream')
    if p.get('open'):
        h = p.get('h', 70)
        out = rect(-4, -6, 52, h, rx=3, fill=col, stroke=ink, stroke_width=lw * 0.35)
        for i in range(4):
            out += line((4, 8 + i * 12), (40 - (i % 2) * 10, 8 + i * 12), stroke=ink, stroke_width=1.6, stroke_opacity=0.6)
        out += rect(-8, -10, 60, 9, rx=4, fill=shade(col, -0.15), stroke=ink, stroke_width=lw * 0.3)
        out += rect(-8, h - 8, 60, 9, rx=4, fill=shade(col, -0.15), stroke=ink, stroke_width=lw * 0.3)
        if p.get('seal'):
            out += circle((22, h - 18), 7, fill=S.c(p['seal']), stroke=ink, stroke_width=1)
        return group(out, transform='rotate(90)')
    out = rect(-6, -26, 12, 52, rx=5, fill=col, stroke=ink, stroke_width=lw * 0.35)
    if p.get('seal'):
        out += circle((0, 0), 6, fill=S.c(p['seal']), stroke=ink, stroke_width=1)
    return out


def book(S, p, t, ink, lw):
    col = _c(S, p, 'color', 'brown')
    return rect(-4, -20, 30, 40, rx=2, fill=col, stroke=ink, stroke_width=lw * 0.35) + \
        rect(22, -18, 4, 36, fill=_c(S, p, 'pages', 'cream'))


def letter(S, p, t, ink, lw):
    col = _c(S, p, 'color', 'cream')
    out = rect(-2, -14, 34, 26, fill=col, stroke=ink, stroke_width=lw * 0.3)
    out += path('M-2 -14 L15 0 L32 -14', fill='none', stroke=ink, stroke_width=1.3)
    if p.get('seal'):
        out += circle((15, 2), 4.5, fill=S.c(p['seal']))
    return out


def torch(S, p, t, ink, lw):
    out = line((-20, 0), (50, 0), stroke=ink, stroke_width=lw * 0.9 + 2, stroke_linecap='round')
    out += line((-20, 0), (50, 0), stroke=_c(S, p, 'color', 'wood'), stroke_width=lw * 0.7, stroke_linecap='round')
    f = 1 + noise1(t * 9, 3) * 0.18
    out += group(
        path('M0 0 C -10 -10 -12 -26 0 -44 C 4 -30 14 -24 10 -10 C 9 -4 5 0 0 0 Z', fill=S.c('#ffae3a', 0.05)) +
        path('M0 0 C -5 -8 -6 -18 0 -28 C 3 -18 8 -14 5 -6 Z', fill='#fff1b0'),
        transform=f'translate(54 0) rotate(90) scale({n(f)} {n(1 / f)})')
    return out


def lantern(S, p, t, ink, lw):
    glow = 0.85 + noise1(t * 6, 5) * 0.1
    out = line((0, 0), (0, 14), stroke=ink, stroke_width=2)
    out += rect(-11, 14, 22, 30, rx=4, fill='#ffd27a', fill_opacity=glow, stroke=ink, stroke_width=lw * 0.4)
    out += path('M-13 14 L0 4 L13 14 Z', fill=ink)
    return out


def shield(S, p, t, ink, lw):
    kind = p.get('shape', p.get('variant', 'round'))
    col = _c(S, p, 'color', 'red')
    rim = _c(S, p, 'rim', 'iron')
    r = p.get('size', 40)
    if kind == 'round':
        out = circle((0, 0), r, fill=col, stroke=ink, stroke_width=lw * 0.5)
        out += circle((0, 0), r - 4, fill='none', stroke=rim, stroke_width=3)
        out += circle((0, 0), r * 0.22, fill=rim, stroke=ink, stroke_width=1.2)
    elif kind == 'kite':
        d = f'M{n(-r * 0.75)} {n(-r)} Q0 {n(-r * 1.25)} {n(r * 0.75)} {n(-r)} Q{n(r * 0.8)} {n(r * 0.4)} 0 {n(r * 1.6)} Q{n(-r * 0.8)} {n(r * 0.4)} {n(-r * 0.75)} {n(-r)} Z'
        out = path(d, fill=col, stroke=ink, stroke_width=lw * 0.5)
    elif kind == 'heater':
        d = f'M{n(-r * 0.8)} {n(-r)} L{n(r * 0.8)} {n(-r)} L{n(r * 0.8)} {n(-r * 0.1)} Q{n(r * 0.7)} {n(r * 0.9)} 0 {n(r * 1.2)} Q{n(-r * 0.7)} {n(r * 0.9)} {n(-r * 0.8)} {n(-r * 0.1)} Z'
        out = path(d, fill=col, stroke=ink, stroke_width=lw * 0.5)
    else:  # scutum: tall curved rectangle
        out = rect(-r * 0.62, -r * 1.25, r * 1.24, r * 2.5, rx=r * 0.18, fill=col, stroke=ink, stroke_width=lw * 0.5)
        out += circle((0, 0), r * 0.2, fill=rim, stroke=ink, stroke_width=1.2)
    em = p.get('emblem')
    if em:
        out += emblem(S, em, (0, 0 if kind in ('round', 'scutum') else -r * 0.15), r * 0.42, p.get('emblem_color', 'gold'), ink)
    return out


def musket(S, p, t, ink, lw):
    L = p.get('length', 150)
    wood = _c(S, p, 'stock', 'wood')
    metal = _c(S, p, 'color', 'iron')
    out = polygon([(-50, -4), (-10, -5), (-10, 5), (-42, 14), (-54, 12)], fill=wood, stroke=ink, stroke_width=lw * 0.35)
    out += rect(-12, -4, L - 30, 7, fill=wood, stroke=ink, stroke_width=lw * 0.3)
    out += rect(-12, -6, L - 12, 4, fill=metal, stroke=ink, stroke_width=lw * 0.25)
    if p.get('bayonet'):
        out += polygon([(L - 24, -5), (L + 22, -4), (L - 24, -2)], fill=S.c('steel'), stroke=ink, stroke_width=1)
    if p.get('smoke'):
        a = max(0.0, 1 - p['smoke'])
        out += circle((L + 10, -4), 14 + 30 * p['smoke'], fill='#e8e4dc', fill_opacity=0.7 * a)
    return out


def rifle(S, p, t, ink, lw):
    q = dict(p)
    q.setdefault('length', 135)
    return musket(S, q, t, ink, lw)


def pistol(S, p, t, ink, lw):
    out = polygon([(-4, -4), (34, -4), (34, 2), (6, 2), (2, 14), (-8, 12)], fill=_c(S, p, 'color', 'iron'),
                  stroke=ink, stroke_width=lw * 0.35)
    return out


def cup(S, p, t, ink, lw):
    col = _c(S, p, 'color', 'gold')
    return path('M-10 -18 L10 -18 L6 -2 L2 0 L2 10 L8 14 L-8 14 L-2 10 L-2 0 L-6 -2 Z', fill=col, stroke=ink,
                stroke_width=lw * 0.3)


def key(S, p, t, ink, lw):
    col = _c(S, p, 'color', 'iron')
    return circle((-6, 0), 7, fill='none', stroke=col, stroke_width=3.5) + line((1, 0), (30, 0), stroke=col, stroke_width=3.5) + \
        line((24, 0), (24, 8), stroke=col, stroke_width=3.5) + line((30, 0), (30, 8), stroke=col, stroke_width=3.5)


def sack(S, p, t, ink, lw):
    col = _c(S, p, 'color', 'linen')
    return path('M-4 0 C -24 10 -26 50 0 52 C 26 50 24 10 4 0 Z', fill=col, stroke=ink, stroke_width=lw * 0.4)


def quill(S, p, t, ink, lw):
    return path('M0 0 L40 -4 C 30 -14 14 -10 0 0 Z', fill=_c(S, p, 'color', 'white'), stroke=ink, stroke_width=1.3)


def telescope(S, p, t, ink, lw):
    col = _c(S, p, 'color', 'brass' if False else 'bronze')
    return polygon([(-20, -4), (50, -7), (50, 7), (-20, 4)], fill=col, stroke=ink, stroke_width=lw * 0.35) + \
        rect(46, -9, 10, 18, rx=2, fill=shade(col, -0.2), stroke=ink, stroke_width=1)


def crown(S, p, t, ink, lw):
    col = _c(S, p, 'color', 'gold')
    return polygon([(-16, 8), (-16, -6), (-9, 2), (0, -12), (9, 2), (16, -6), (16, 8)], fill=col, stroke=ink, stroke_width=1.5)


def coin(S, p, t, ink, lw):
    return circle((6, 0), 7, fill=_c(S, p, 'color', 'gold'), stroke=ink, stroke_width=1.2)


def map_sheet(S, p, t, ink, lw):
    col = _c(S, p, 'color', 'cream')
    out = polygon([(0, -24), (22, -20), (44, -24), (44, 24), (22, 28), (0, 24)], fill=col, stroke=ink, stroke_width=lw * 0.35)
    out += path('M6 -8 C 14 -14 24 4 36 -6 M10 10 C 18 4 26 16 38 8', fill='none', stroke=ink, stroke_width=1.3, stroke_opacity=0.6)
    return out


def raw_svg(S, p, t, ink, lw):
    return p.get('svg', '')


PROPS = {
    'sword': sword, 'saber': saber, 'scimitar': saber, 'dagger': dagger, 'spear': spear, 'pike': pike, 'lance': pike,
    'staff': staff, 'scepter': staff, 'axe': axe, 'hammer': hammer, 'bow': bow, 'flag': flag, 'banner': flag,
    'scroll': scroll, 'book': book, 'letter': letter, 'torch': torch, 'lantern': lantern, 'shield': shield,
    'musket': musket, 'rifle': rifle, 'pistol': pistol, 'cup': cup, 'goblet': cup, 'key': key, 'sack': sack,
    'quill': quill, 'telescope': telescope, 'crown': crown, 'coin': coin, 'map': map_sheet, 'svg': raw_svg,
}

# Default angle of the prop relative to the forearm (degrees), and whether it stays upright.
DEFAULTS = {
    'sword': (-90, False), 'saber': (-90, False), 'scimitar': (-90, False), 'dagger': (-90, False),
    'spear': (-90, False), 'pike': (-90, False), 'lance': (-90, False), 'staff': (-90, False), 'scepter': (-90, False),
    'axe': (-90, False), 'hammer': (-90, False), 'bow': (0, True), 'flag': (-90, False), 'banner': (-90, False),
    'scroll': (0, True), 'book': (0, True), 'letter': (0, True), 'torch': (-90, False), 'lantern': (0, True),
    'shield': (0, True), 'musket': (-90, False), 'rifle': (-90, False), 'pistol': (-90, False), 'cup': (0, True),
    'goblet': (0, True), 'key': (-90, False), 'sack': (0, True), 'quill': (-90, False), 'telescope': (-90, False),
    'crown': (0, True), 'coin': (0, True), 'map': (0, True), 'svg': (0, False),
}


def draw(S, spec, hand, forearm_deg, t, ink, lw):
    """spec: a prop name or {"kind": ..., ...}. hand: (x, y). forearm_deg: direction elbow->hand in degrees."""
    if isinstance(spec, str):
        spec = {'kind': spec}
    kind = spec.get('kind', 'svg')
    if kind not in PROPS:
        raise ValueError(f'Unknown prop "{kind}". Known: {", ".join(sorted(PROPS))}, or "svg" with your own markup.')
    da, up = DEFAULTS.get(kind, (0, False))
    up = spec.get('upright', up)
    ang = spec.get('angle', da) + (0 if up else forearm_deg)
    sc = spec.get('scale', 1)
    body = PROPS[kind](S, spec, t, ink, lw)
    return group(body, transform=f'translate({n(hand[0])} {n(hand[1])}) rotate({n(ang)}) scale({n(sc)})')
