"""Places: architecture, nature, objects and crowds, built from parameters so any period and place can be drawn.

Every item is a dict with a `kind` and world coordinates: `x` (centre unless noted) and `y` (the ground line it
stands on; defaults to the scene's ground). Sizes are world units (a person is about 300 tall).
Colours are real-world colours (names or hex); the style pulls them into the palette.
Unknown shapes: use {"kind": "svg", "svg": "<path .../>", "x":..., "y":...} drawn with its origin at (x, y).
"""
import math

from .svg import n, line, circle, polygon, path, rect, ellipse, group, smooth_path, noise1, shade, mix, rng, polyline


class Painter:
    """Colour helper for one layer: real colour -> palette -> atmospheric depth."""

    def __init__(self, S, depth, tod, t, ground_y, seed):
        self.S, self.depth, self.tod, self.t, self.gy, self.seed = S, depth, tod, t, ground_y, seed
        self.ink = S.depth_tint(S.ink, depth, tod)
        self.lw = max(1.5, S.line['limb'] * 0.42)

    def c(self, color, default='stone'):
        return self.S.depth_tint(self.S.c(color or default), self.depth, self.tod)

    def st(self, color, default='stone', w=None):
        return dict(fill=self.c(color, default), stroke=self.ink, stroke_width=w or self.lw, stroke_linejoin='round')


def _y(P, it):
    return it.get('y', P.gy)


# ---------------------------------------------------------------- nature
def hills(P, it):
    x0, x1 = it.get('x0', -1500), it.get('x1', 3500)
    h = it.get('h', 160)
    y = _y(P, it)
    r = rng('hills', it.get('seed', 0), P.seed)
    k = it.get('bumps', 6)
    ptsl = [(x0, y + 400)]
    for i in range(k * 4 + 1):
        x = x0 + (x1 - x0) * i / (k * 4)
        yy = y - h * (0.55 + 0.45 * math.sin(i / 4 * math.pi + r.random() * 0.6) * (0.6 + r.random() * 0.4))
        ptsl.append((x, yy))
    ptsl.append((x1, y + 400))
    return path(smooth_path(ptsl[1:-1]) + f' L{n(x1)} {n(y + 400)} L{n(x0)} {n(y + 400)} Z', fill=P.c(it.get('color'), 'grass'),
                stroke=P.ink if it.get('outline') else 'none', stroke_width=P.lw)


def mountains(P, it):
    x0, x1 = it.get('x0', -1500), it.get('x1', 3500)
    h = it.get('h', 380)
    y = _y(P, it)
    r = rng('mtn', it.get('seed', 0), P.seed)
    ptsl = [(x0, y)]
    x = x0
    while x < x1:
        w = r.uniform(140, 320)
        ptsl.append((x + w * 0.5, y - h * r.uniform(0.5, 1.0)))
        ptsl.append((x + w, y - h * r.uniform(0.15, 0.4)))
        x += w
    ptsl += [(x1, y), (x1, y + 400), (x0, y + 400)]
    col = P.c(it.get('color'), 'stone')
    out = polygon(ptsl, fill=col)
    if it.get('snow'):
        for i in range(1, len(ptsl) - 3, 2):
            px, py = ptsl[i]
            if py < y - h * 0.7:
                out += polygon([(px, py), (px - 26, py + 34), (px - 8, py + 28), (px + 6, py + 38), (px + 24, py + 30)], fill=P.c('snow'))
    return out


def tree(P, it):
    x, y = it.get('x', 0), _y(P, it)
    h = it.get('h', 320)
    kind = it.get('type', 'round')
    leaf = P.c(it.get('color'), 'forest')
    trunk = P.c(it.get('trunk'), 'wood')
    sw = noise1(P.t * 0.8 + x * 0.01, 2) * 3 * it.get('wind', 1)
    if kind == 'palm':
        top = (x + h * 0.12 + sw, y - h)
        out = path(f'M{n(x - 8)} {n(y)} Q{n(x + h * 0.1)} {n(y - h * 0.5)} {n(top[0])} {n(top[1])} L{n(top[0] + 6)} {n(top[1] + 4)} '
                   f'Q{n(x + h * 0.12)} {n(y - h * 0.5)} {n(x + 8)} {n(y)} Z', fill=trunk, stroke=P.ink, stroke_width=P.lw)
        for a in (-160, -120, -60, -20, 20, -90):
            ra = math.radians(a + sw * 2)
            ex, ey = top[0] + math.cos(ra) * h * 0.38, top[1] + math.sin(ra) * h * 0.38 + h * 0.12
            out += path(f'M{n(top[0])} {n(top[1])} Q{n((top[0] + ex) / 2)} {n(min(top[1], ey) - h * 0.12)} {n(ex)} {n(ey)} '
                        f'Q{n((top[0] + ex) / 2)} {n(min(top[1], ey) - h * 0.04)} {n(top[0])} {n(top[1])} Z', fill=leaf, stroke=P.ink,
                        stroke_width=P.lw)
        return out
    if kind == 'cypress':
        w = h * 0.14
        return rect(x - 5, y - h * 0.12, 10, h * 0.12, fill=trunk) + path(
            f'M{n(x)} {n(y - h)} C{n(x + w * 1.4 + sw)} {n(y - h * 0.6)} {n(x + w)} {n(y - h * 0.1)} {n(x)} {n(y - h * 0.08)} '
            f'C{n(x - w)} {n(y - h * 0.1)} {n(x - w * 1.4 + sw)} {n(y - h * 0.6)} {n(x)} {n(y - h)} Z', fill=leaf, stroke=P.ink, stroke_width=P.lw)
    if kind == 'pine':
        out = rect(x - 7, y - h * 0.2, 14, h * 0.2, fill=trunk, stroke=P.ink, stroke_width=P.lw)
        for i in range(3):
            yy = y - h * (0.15 + i * 0.27)
            w = h * (0.32 - i * 0.07)
            out += polygon([(x - w, yy), (x + sw, yy - h * 0.42), (x + w, yy)], fill=leaf, stroke=P.ink, stroke_width=P.lw)
        return out
    if kind == 'bare':
        out = line((x, y), (x, y - h * 0.6), stroke=trunk, stroke_width=12, stroke_linecap='round')
        r = rng('bare', x)
        for i in range(5):
            a = math.radians(-90 + r.uniform(-60, 60))
            sy = y - h * r.uniform(0.35, 0.6)
            out += line((x, sy), (x + math.cos(a) * h * 0.35, sy + math.sin(a) * h * 0.35), stroke=trunk, stroke_width=5, stroke_linecap='round')
        return out
    # round / oak / olive
    out = path(f'M{n(x - 10)} {n(y)} L{n(x - 6)} {n(y - h * 0.5)} L{n(x + 6)} {n(y - h * 0.5)} L{n(x + 10)} {n(y)} Z', fill=trunk,
               stroke=P.ink, stroke_width=P.lw)
    r = rng('tree', x, it.get('seed', 0))
    blobs = []
    for i in range(7):
        a = i / 7 * math.pi * 2
        blobs.append((x + math.cos(a) * h * 0.26 + sw, y - h * 0.68 + math.sin(a) * h * 0.2 * (0.8 + r.random() * 0.4)))
    out += path(smooth_path(blobs, closed=True), fill=leaf, stroke=P.ink, stroke_width=P.lw)
    if kind == 'olive':
        out += path(smooth_path(blobs, closed=True), fill=P.c('#9aa070'), fill_opacity=0.35)
    return out


def bush(P, it):
    x, y = it.get('x', 0), _y(P, it)
    w = it.get('w', 90)
    return path(f'M{n(x - w / 2)} {n(y)} C{n(x - w / 2)} {n(y - w * 0.6)} {n(x)} {n(y - w * 0.75)} {n(x + w * 0.1)} {n(y - w * 0.4)} '
                f'C{n(x + w * 0.3)} {n(y - w * 0.7)} {n(x + w / 2)} {n(y - w * 0.4)} {n(x + w / 2)} {n(y)} Z', **P.st(it.get('color'), 'forest'))


def rock(P, it):
    x, y = it.get('x', 0), _y(P, it)
    w = it.get('w', 80)
    return path(f'M{n(x - w / 2)} {n(y)} L{n(x - w * 0.38)} {n(y - w * 0.4)} L{n(x - w * 0.05)} {n(y - w * 0.55)} L{n(x + w * 0.35)} '
                f'{n(y - w * 0.35)} L{n(x + w / 2)} {n(y)} Z', **P.st(it.get('color'), 'stone'))


def grass(P, it):
    x0, x1 = it.get('x0', -1000), it.get('x1', 3000)
    y = _y(P, it)
    r = rng('grass', x0, P.seed)
    col = P.c(it.get('color'), 'grass')
    out = ''
    x = x0
    while x < x1:
        h = r.uniform(10, 24)
        sw = noise1(P.t * 1.5 + x * 0.02, 3) * 4
        out += polyline([(x - 5, y), (x + sw, y - h), (x + 5, y)], fill='none', stroke=col, stroke_width=2.5, stroke_linecap='round')
        x += r.uniform(30, 90) / it.get('density', 1)
    return out


def water(P, it):
    x0, x1 = it.get('x0', -1500), it.get('x1', 3500)
    y = _y(P, it)
    col = P.c(it.get('color'), 'water')
    deep = it.get('deep', 600)
    amp = it.get('waves', 8)
    k = 60
    ptsl = []
    for i in range(k + 1):
        x = x0 + (x1 - x0) * i / k
        ptsl.append((x, y + math.sin(x * 0.012 + P.t * 2) * amp))
    out = path(smooth_path(ptsl) + f' L{n(x1)} {n(y + deep)} L{n(x0)} {n(y + deep)} Z', fill=col)
    for j in range(3):
        yy = y + 30 + j * 45
        seg = []
        for i in range(k + 1):
            x = x0 + (x1 - x0) * i / k
            seg.append((x, yy + math.sin(x * 0.02 + P.t * 2.5 + j) * amp * 0.5))
        out += path(smooth_path(seg), fill='none', stroke=shade(col, 0.25), stroke_width=2.5, stroke_opacity=0.6,
                    stroke_dasharray='40 60')
    return out


def sun(P, it):
    x, y = it.get('x', 1500), it.get('y', 200)
    r = it.get('r', 70)
    col = P.c(it.get('color'), '#ffd27a')
    return circle((x, y), r * 2.2, fill=col, fill_opacity=0.18) + circle((x, y), r, fill=col)


def moon(P, it):
    x, y = it.get('x', 1500), it.get('y', 200)
    r = it.get('r', 50)
    col = P.c(it.get('color'), '#f4ecd0')
    out = circle((x, y), r * 2.4, fill=col, fill_opacity=0.12) + circle((x, y), r, fill=col)
    if it.get('crescent'):
        tx, ty = x + r * 0.5, r * 0.866
        return circle((x, y), r * 2.4, fill=col, fill_opacity=0.12) + path(
            f'M{n(tx)} {n(y - ty)} A{n(r)} {n(r)} 0 1 0 {n(tx)} {n(y + ty)} A{n(r * 0.95)} {n(r * 0.95)} 0 0 1 {n(tx)} {n(y - ty)} Z', fill=col)
    return out


def stars(P, it):
    r = rng('stars', P.seed)
    out = ''
    for i in range(it.get('count', 80)):
        x, y = r.uniform(-1500, 3500), r.uniform(-300, it.get('y', 500))
        tw = 0.6 + 0.4 * math.sin(P.t * 3 + i)
        out += circle((x, y), r.uniform(1.2, 3), fill='#fffbe8', fill_opacity=0.8 * tw)
    return out


def clouds(P, it):
    r = rng('clouds', it.get('seed', 0), P.seed)
    col = P.c(it.get('color'), 'white')
    out = ''
    for i in range(it.get('count', 5)):
        x = r.uniform(-1200, 3200) + P.t * it.get('speed', 12)
        y = r.uniform(it.get('y0', 60), it.get('y1', 320))
        w = r.uniform(160, 340)
        out += path(f'M{n(x - w / 2)} {n(y)} C{n(x - w / 2)} {n(y - w * 0.25)} {n(x - w * 0.15)} {n(y - w * 0.3)} {n(x)} {n(y - w * 0.18)} '
                    f'C{n(x + w * 0.15)} {n(y - w * 0.35)} {n(x + w / 2)} {n(y - w * 0.2)} {n(x + w / 2)} {n(y)} Z', fill=col,
                    fill_opacity=it.get('opacity', 0.85))
    return out


def smoke(P, it):
    x, y = it.get('x', 0), _y(P, it)
    h = it.get('h', 400)
    col = P.c(it.get('color'), '#5a5a5a')
    out = ''
    for i in range(9):
        u = ((i / 9) + P.t * 0.15) % 1
        r = 20 + u * 70
        dx = noise1(u * 3 + i, 8) * 40 + u * it.get('drift', 80)
        out += circle((x + dx, y - u * h), r, fill=col, fill_opacity=0.5 * (1 - u))
    return out


def fire(P, it):
    x, y = it.get('x', 0), _y(P, it)
    s = it.get('size', 1.0)
    out = ''
    for i, (col, k) in enumerate((('#e8552a', 1.0), ('#ffa63a', 0.7), ('#fff0a0', 0.4))):
        f = 1 + noise1(P.t * 8 + i * 3 + x, 5) * 0.2
        w, h = 40 * s * k, 110 * s * k * f
        out += path(f'M{n(x - w)} {n(y)} C{n(x - w)} {n(y - h * 0.5)} {n(x - w * 0.2)} {n(y - h * 0.6)} {n(x + noise1(P.t * 5, 6) * w * 0.4)} {n(y - h)} '
                    f'C{n(x + w * 0.3)} {n(y - h * 0.6)} {n(x + w)} {n(y - h * 0.5)} {n(x + w)} {n(y)} Z', fill=col)
    return out


# ---------------------------------------------------------------- architecture
def _blocks(P, x, y, w, h, col, kind):
    """Masonry lines inside a rect (x, y top-left)."""
    out = ''
    lc = shade(col, -0.22)
    if kind in ('blocks', 'bricks'):
        bh = 26 if kind == 'bricks' else 46
        bw = 54 if kind == 'bricks' else 90
        row = 0
        yy = y + bh
        while yy < y + h:
            out += line((x, yy), (x + w, yy), stroke=lc, stroke_width=1.6)
            off = (bw / 2) * (row % 2)
            xx = x + off
            while xx < x + w:
                out += line((xx, yy - bh), (xx, yy), stroke=lc, stroke_width=1.6)
                xx += bw
            yy += bh
            row += 1
    return out


def wall(P, it):
    x, y = it.get('x', 0), _y(P, it)
    w, h = it.get('w', 600), it.get('h', 300)
    col = P.c(it.get('color'), 'stone')
    x0 = x - w / 2
    out = rect(x0, y - h, w, h, fill=col, stroke=P.ink, stroke_width=P.lw)
    out += _blocks(P, x0, y - h, w, h, col, it.get('texture', 'blocks'))
    if it.get('crenel'):
        cw = it.get('crenel_w', 40)
        k = int(w // (cw * 2))
        for i in range(k):
            out += rect(x0 + i * cw * 2 + cw / 2, y - h - cw * 0.8, cw, cw * 0.8, fill=col, stroke=P.ink, stroke_width=P.lw)
    for win in it.get('windows', []):
        out += window(P, dict(win, x=x0 + win.get('x', 0.5) * w, y=y - h + win.get('y', 0.4) * h, base=False))
    if it.get('door'):
        d = it['door'] if isinstance(it['door'], dict) else {}
        out += arch(P, dict(d, x=x0 + d.get('x', 0.5) * w, y=y, w=d.get('w', 110), h=d.get('h', 200), fill_dark=True,
                            style=d.get('style', 'round')))
    return out


def tower(P, it):
    x, y = it.get('x', 0), _y(P, it)
    w, h = it.get('w', 160), it.get('h', 520)
    col = P.c(it.get('color'), 'stone')
    rc = P.c(it.get('roof_color'), 'brick')
    out = rect(x - w / 2, y - h, w, h, fill=col, stroke=P.ink, stroke_width=P.lw)
    out += _blocks(P, x - w / 2, y - h, w, h, col, it.get('texture', 'blocks'))
    roof = it.get('roof', 'crenel')
    top = y - h
    if roof == 'crenel':
        cw = w / 5
        for i in range(3):
            out += rect(x - w / 2 + i * cw * 2, top - cw * 0.8, cw, cw * 0.8, fill=col, stroke=P.ink, stroke_width=P.lw)
    elif roof == 'cone':
        out += polygon([(x - w * 0.62, top), (x, top - w * it.get('roof_h', 1.3)), (x + w * 0.62, top)], fill=rc, stroke=P.ink, stroke_width=P.lw)
    elif roof == 'dome':
        out += dome(P, {'x': x, 'y': top, 'w': w * 1.0, 'h': w * 0.55, 'color': it.get('roof_color', 'lead'), 'finial': it.get('finial')})
    elif roof == 'onion':
        out += dome(P, {'x': x, 'y': top, 'w': w * 1.05, 'h': w * 0.9, 'onion': True, 'color': it.get('roof_color', 'gold'),
                        'finial': it.get('finial', 'cross')})
    elif roof == 'pyramid':
        out += polygon([(x - w * 0.55, top), (x, top - w * 0.6), (x + w * 0.55, top)], fill=rc, stroke=P.ink, stroke_width=P.lw)
    for i in range(it.get('windows', 2)):
        out += window(P, {'x': x, 'y': y - h * (0.35 + 0.25 * i), 'w': w * 0.22, 'h': w * 0.42, 'style': it.get('window_style', 'round'),
                          'lit': it.get('lit', False)})
    return out


def window(P, it):
    x, y = it.get('x', 0), it.get('y', 0)
    w, h = it.get('w', 50), it.get('h', 80)
    lit = it.get('lit', False)
    fill = P.c('#ffd27a', 0) if lit else shade(P.c(it.get('color'), 'stone'), -0.55)
    style = it.get('style', 'round')
    if style == 'rect':
        d = f'M{n(x - w / 2)} {n(y + h / 2)} L{n(x - w / 2)} {n(y - h / 2)} L{n(x + w / 2)} {n(y - h / 2)} L{n(x + w / 2)} {n(y + h / 2)} Z'
    elif style == 'pointed':
        d = (f'M{n(x - w / 2)} {n(y + h / 2)} L{n(x - w / 2)} {n(y - h / 2 + w * 0.4)} Q{n(x - w / 2)} {n(y - h / 2)} {n(x)} {n(y - h / 2 - w * 0.2)} '
             f'Q{n(x + w / 2)} {n(y - h / 2)} {n(x + w / 2)} {n(y - h / 2 + w * 0.4)} L{n(x + w / 2)} {n(y + h / 2)} Z')
    else:
        d = (f'M{n(x - w / 2)} {n(y + h / 2)} L{n(x - w / 2)} {n(y - h / 2 + w / 2)} A{n(w / 2)} {n(w / 2)} 0 0 1 {n(x + w / 2)} '
             f'{n(y - h / 2 + w / 2)} L{n(x + w / 2)} {n(y + h / 2)} Z')
    out = path(d, fill=fill, stroke=P.ink, stroke_width=P.lw)
    if lit:
        out = circle((x, y), max(w, h) * 1.1, fill='#ffd27a', fill_opacity=0.12) + out
    if it.get('bars'):
        out += line((x, y - h / 2), (x, y + h / 2), stroke=P.ink, stroke_width=P.lw)
    return out


def arch(P, it):
    """A doorway/gate/arcade arch. style: round, pointed, horseshoe, flat."""
    x, y = it.get('x', 0), _y(P, it)
    w, h = it.get('w', 160), it.get('h', 260)
    style = it.get('style', 'round')
    col = P.c(it.get('color'), 'stone')
    dark = shade(col, -0.6)
    hw = w / 2
    spring = y - h + hw
    if style == 'pointed':
        top = f'Q{n(x - hw)} {n(y - h + hw * 0.2)} {n(x)} {n(y - h)} Q{n(x + hw)} {n(y - h + hw * 0.2)} {n(x + hw)} {n(spring)}'
    elif style == 'horseshoe':
        top = f'C{n(x - hw * 1.25)} {n(spring - hw * 0.7)} {n(x - hw * 0.5)} {n(y - h)} {n(x)} {n(y - h)} C{n(x + hw * 0.5)} {n(y - h)} {n(x + hw * 1.25)} {n(spring - hw * 0.7)} {n(x + hw)} {n(spring)}'
    elif style == 'flat':
        top = f'L{n(x - hw)} {n(y - h)} L{n(x + hw)} {n(y - h)} L{n(x + hw)} {n(spring)}'
    else:
        top = f'A{n(hw)} {n(hw)} 0 0 1 {n(x + hw)} {n(spring)}'
    d = f'M{n(x - hw)} {n(y)} L{n(x - hw)} {n(spring)} {top} L{n(x + hw)} {n(y)} Z'
    out = ''
    if it.get('frame', True):
        fw = it.get('frame_w', 22)
        out += path(f'M{n(x - hw - fw)} {n(y)} L{n(x - hw - fw)} {n(spring)} ' + (
            f'A{n(hw + fw)} {n(hw + fw)} 0 0 1 {n(x + hw + fw)} {n(spring)}' if style == 'round' else
            f'L{n(x)} {n(y - h - fw)} L{n(x + hw + fw)} {n(spring)}') + f' L{n(x + hw + fw)} {n(y)} Z',
            fill=shade(col, 0.08), stroke=P.ink, stroke_width=P.lw)
    out += path(d, fill=dark if it.get('fill_dark', True) else 'none', stroke=P.ink, stroke_width=P.lw)
    if it.get('doors'):
        out += path(d, fill=P.c(it['doors'], 'wood'), stroke=P.ink, stroke_width=P.lw)
        out += line((x, y), (x, y - h + 10), stroke=P.ink, stroke_width=P.lw)
    return out


def column(P, it):
    x, y = it.get('x', 0), _y(P, it)
    h, w = it.get('h', 420), it.get('w', 46)
    col = P.c(it.get('color'), 'marble')
    style = it.get('style', 'doric')
    out = rect(x - w / 2, y - h, w, h, fill=col, stroke=P.ink, stroke_width=P.lw)
    for i in (1, 2):
        xx = x - w / 2 + w * i / 3
        out += line((xx, y - h + 20), (xx, y - 12), stroke=shade(col, -0.18), stroke_width=1.6)
    out += rect(x - w * 0.75, y - 14, w * 1.5, 14, fill=col, stroke=P.ink, stroke_width=P.lw)
    if style == 'ionic':
        out += rect(x - w * 0.8, y - h - 12, w * 1.6, 14, fill=col, stroke=P.ink, stroke_width=P.lw)
        out += circle((x - w * 0.8, y - h - 2), 9, fill=col, stroke=P.ink, stroke_width=P.lw) + circle((x + w * 0.8, y - h - 2), 9, fill=col, stroke=P.ink, stroke_width=P.lw)
    elif style == 'lotus':
        out += path(f'M{n(x - w / 2)} {n(y - h)} C{n(x - w)} {n(y - h - 30)} {n(x - w * 0.6)} {n(y - h - 50)} {n(x)} {n(y - h - 40)} '
                    f'C{n(x + w * 0.6)} {n(y - h - 50)} {n(x + w)} {n(y - h - 30)} {n(x + w / 2)} {n(y - h)} Z', fill=col, stroke=P.ink, stroke_width=P.lw)
    elif style == 'plain':
        pass
    else:
        out += rect(x - w * 0.7, y - h - 14, w * 1.4, 14, fill=col, stroke=P.ink, stroke_width=P.lw)
    return out


def colonnade(P, it):
    x0, x1 = it.get('x0', 0), it.get('x1', 1200)
    k = it.get('count', 6)
    h = it.get('h', 420)
    y = _y(P, it)
    col = it.get('color', 'marble')
    out = ''
    for i in range(k):
        out += column(P, {'x': x0 + (x1 - x0) * i / max(1, k - 1), 'y': y, 'h': h, 'style': it.get('style', 'doric'), 'color': col})
    if it.get('roof', True):
        c = P.c(col, 'marble')
        out += rect(x0 - 60, y - h - 60, x1 - x0 + 120, 46, fill=c, stroke=P.ink, stroke_width=P.lw)
        if it.get('pediment', True):
            out += polygon([(x0 - 70, y - h - 60), ((x0 + x1) / 2, y - h - 60 - (x1 - x0) * 0.16), (x1 + 70, y - h - 60)], fill=c,
                           stroke=P.ink, stroke_width=P.lw)
    return out


def dome(P, it):
    x, y = it.get('x', 0), _y(P, it)
    w, h = it.get('w', 300), it.get('h', 160)
    col = P.c(it.get('color'), 'lead')
    hw = w / 2
    if it.get('onion'):
        d = (f'M{n(x - hw * 0.8)} {n(y)} C{n(x - hw * 1.3)} {n(y - h * 0.45)} {n(x - hw * 0.2)} {n(y - h * 0.7)} {n(x)} {n(y - h)} '
             f'C{n(x + hw * 0.2)} {n(y - h * 0.7)} {n(x + hw * 1.3)} {n(y - h * 0.45)} {n(x + hw * 0.8)} {n(y)} Z')
    else:
        d = f'M{n(x - hw)} {n(y)} C{n(x - hw)} {n(y - h * 1.33)} {n(x + hw)} {n(y - h * 1.33)} {n(x + hw)} {n(y)} Z'
    out = ''
    if it.get('drum', 0):
        dh = it['drum']
        out += rect(x - hw * 0.92, y - 0, w * 0.92, 0, fill=col)
        out += rect(x - hw * 0.95, y - dh, w * 0.95, dh, fill=P.c(it.get('drum_color'), 'stone'), stroke=P.ink, stroke_width=P.lw)
        for i in range(5):
            out += window(P, {'x': x - hw * 0.7 + i * hw * 0.35, 'y': y - dh / 2, 'w': 12, 'h': dh * 0.55, 'color': it.get('drum_color', 'stone')})
        y -= dh
        d = d.replace(n(y + dh), n(y))
        if it.get('onion'):
            d = (f'M{n(x - hw * 0.8)} {n(y)} C{n(x - hw * 1.3)} {n(y - h * 0.45)} {n(x - hw * 0.2)} {n(y - h * 0.7)} {n(x)} {n(y - h)} '
                 f'C{n(x + hw * 0.2)} {n(y - h * 0.7)} {n(x + hw * 1.3)} {n(y - h * 0.45)} {n(x + hw * 0.8)} {n(y)} Z')
        else:
            d = f'M{n(x - hw)} {n(y)} C{n(x - hw)} {n(y - h * 1.33)} {n(x + hw)} {n(y - h * 1.33)} {n(x + hw)} {n(y)} Z'
    out += path(d, fill=col, stroke=P.ink, stroke_width=P.lw)
    out += path(f'M{n(x - hw * 0.45)} {n(y - h * 0.25)} Q{n(x - hw * 0.4)} {n(y - h * 0.75)} {n(x - hw * 0.05)} {n(y - h * 0.9)}', fill='none',
                stroke=shade(col, 0.35), stroke_width=4, stroke_linecap='round')
    fin = it.get('finial')
    if fin:
        out += finial(P, x, y - h, fin)
    return out


def finial(P, x, y, kind):
    g = P.c('gold')
    out = line((x, y), (x, y - 40), stroke=g, stroke_width=4)
    if kind == 'crescent':
        out += path(f'M{n(x + 4)} {n(y - 70)} A16 16 0 1 0 {n(x + 4)} {n(y - 40)} A13 13 0 1 1 {n(x + 4)} {n(y - 70)} Z', fill=g)
    elif kind == 'cross':
        out += line((x, y - 40), (x, y - 72), stroke=g, stroke_width=4) + line((x - 12, y - 60), (x + 12, y - 60), stroke=g, stroke_width=4)
    elif kind == 'ball':
        out += circle((x, y - 46), 9, fill=g)
    elif kind == 'spike':
        out += polygon([(x - 5, y - 40), (x, y - 70), (x + 5, y - 40)], fill=g)
    return out


def minaret(P, it):
    x, y = it.get('x', 0), _y(P, it)
    h, w = it.get('h', 700), it.get('w', 46)
    col = P.c(it.get('color'), 'marble')
    out = rect(x - w / 2, y - h, w, h, fill=col, stroke=P.ink, stroke_width=P.lw)
    for i in range(it.get('balconies', 2)):
        by = y - h * (0.55 + i * 0.25)
        out += rect(x - w * 0.8, by, w * 1.6, 12, fill=col, stroke=P.ink, stroke_width=P.lw)
    out += polygon([(x - w * 0.6, y - h), (x, y - h - w * 2.6), (x + w * 0.6, y - h)], fill=P.c(it.get('cap_color'), 'lead'), stroke=P.ink, stroke_width=P.lw)
    out += finial(P, x, y - h - w * 2.6, it.get('finial', 'crescent')) if it.get('finial', 'crescent') else ''
    return out


def building(P, it):
    """A generic house/hall. roof: gable, hip, flat, dome, pagoda, thatch, none."""
    x, y = it.get('x', 0), _y(P, it)
    w, h = it.get('w', 380), it.get('h', 260)
    col = P.c(it.get('color'), 'sandstone')
    rc = P.c(it.get('roof_color'), 'terracotta')
    x0 = x - w / 2
    out = rect(x0, y - h, w, h, fill=col, stroke=P.ink, stroke_width=P.lw)
    out += _blocks(P, x0, y - h, w, h, col, it.get('texture', 'plain'))
    roof = it.get('roof', 'gable')
    top = y - h
    rh = it.get('roof_h', w * 0.35)
    if roof == 'gable':
        out += polygon([(x0 - 20, top), (x, top - rh), (x0 + w + 20, top)], fill=rc, stroke=P.ink, stroke_width=P.lw)
    elif roof == 'hip':
        out += polygon([(x0 - 20, top), (x0 + w * 0.25, top - rh), (x0 + w * 0.75, top - rh), (x0 + w + 20, top)], fill=rc, stroke=P.ink, stroke_width=P.lw)
    elif roof == 'thatch':
        out += path(f'M{n(x0 - 30)} {n(top + 10)} Q{n(x)} {n(top - rh * 1.4)} {n(x0 + w + 30)} {n(top + 10)} Z', fill=P.c(it.get('roof_color'), 'straw'), stroke=P.ink, stroke_width=P.lw)
    elif roof == 'pagoda':
        for i in range(it.get('tiers', 2)):
            ty = top - i * rh * 0.8
            tw = w * (1 - i * 0.22)
            out += path(f'M{n(x - tw / 2 - 50)} {n(ty)} Q{n(x - tw / 2)} {n(ty - 10)} {n(x - tw * 0.3)} {n(ty - rh * 0.6)} L{n(x + tw * 0.3)} {n(ty - rh * 0.6)} '
                        f'Q{n(x + tw / 2)} {n(ty - 10)} {n(x + tw / 2 + 50)} {n(ty)} Z', fill=rc, stroke=P.ink, stroke_width=P.lw)
            if i < it.get('tiers', 2) - 1:
                out += rect(x - tw * 0.3, ty - rh * 0.8 - 4, tw * 0.6, rh * 0.25, fill=col, stroke=P.ink, stroke_width=P.lw)
    elif roof == 'dome':
        out += dome(P, {'x': x, 'y': top, 'w': w * 0.6, 'h': w * 0.32, 'color': it.get('roof_color', 'lead'), 'finial': it.get('finial')})
    elif roof == 'flat':
        out += rect(x0 - 10, top - 14, w + 20, 14, fill=shade(col, -0.1), stroke=P.ink, stroke_width=P.lw)
    for i in range(it.get('windows', 2)):
        k = it.get('windows', 2)
        out += window(P, {'x': x0 + w * (i + 1) / (k + 1), 'y': y - h * 0.62, 'w': it.get('window_w', 44), 'h': it.get('window_h', 70),
                          'style': it.get('window_style', 'rect'), 'lit': it.get('lit', False), 'color': it.get('color', 'sandstone')})
    if it.get('door', True):
        out += arch(P, {'x': x + w * it.get('door_x', 0), 'y': y, 'w': 70, 'h': min(150, h * 0.6), 'style': it.get('door_style', 'flat'),
                        'frame': False, 'doors': it.get('door_color', 'wood'), 'color': it.get('color', 'sandstone')})
    return out


def tent(P, it):
    x, y = it.get('x', 0), _y(P, it)
    w, h = it.get('w', 260), it.get('h', 200)
    col = P.c(it.get('color'), 'linen')
    kind = it.get('type', 'cone')
    if kind == 'yurt':
        out = rect(x - w / 2, y - h * 0.5, w, h * 0.5, fill=col, stroke=P.ink, stroke_width=P.lw)
        out += path(f'M{n(x - w / 2 - 6)} {n(y - h * 0.5)} Q{n(x)} {n(y - h * 1.15)} {n(x + w / 2 + 6)} {n(y - h * 0.5)} Z', fill=shade(col, -0.08), stroke=P.ink, stroke_width=P.lw)
        out += rect(x - 26, y - h * 0.42, 52, h * 0.42, fill=P.c(it.get('door_color'), 'red'), stroke=P.ink, stroke_width=P.lw)
        return out
    if kind == 'pavilion':
        out = rect(x - w / 2, y - h * 0.55, w, h * 0.55, fill=col, stroke=P.ink, stroke_width=P.lw)
        out += polygon([(x - w / 2 - 20, y - h * 0.55), (x, y - h), (x + w / 2 + 20, y - h * 0.55)], fill=P.c(it.get('roof_color'), 'red'), stroke=P.ink, stroke_width=P.lw)
        out += polygon([(x - 30, y), (x, y - h * 0.5), (x + 30, y)], fill=shade(col, -0.5))
        if it.get('stripes'):
            for i in range(1, 6):
                xx = x - w / 2 + w * i / 6
                out += line((xx, y - h * 0.55), (xx, y), stroke=P.c(it['stripes']), stroke_width=8)
        return out
    out = polygon([(x - w / 2, y), (x, y - h), (x + w / 2, y)], fill=col, stroke=P.ink, stroke_width=P.lw)
    out += polygon([(x - w * 0.12, y), (x, y - h * 0.55), (x + w * 0.12, y)], fill=shade(col, -0.5))
    out += line((x, y - h), (x, y - h - 30), stroke=P.ink, stroke_width=P.lw)
    if it.get('pennant'):
        out += polygon([(x, y - h - 30), (x + 34, y - h - 22), (x, y - h - 14)], fill=P.c(it['pennant']))
    return out


def pyramid(P, it):
    x, y = it.get('x', 0), _y(P, it)
    w, h = it.get('w', 900), it.get('h', 560)
    col = P.c(it.get('color'), 'sandstone')
    if it.get('stepped'):
        k = it.get('steps', 6)
        out = ''
        for i in range(k):
            ww = w * (1 - i / k)
            out += rect(x - ww / 2, y - h * (i + 1) / k, ww, h / k, fill=shade(col, -0.04 * (i % 2)), stroke=P.ink, stroke_width=P.lw)
        if it.get('temple'):
            out += rect(x - w * 0.08, y - h - h * 0.15, w * 0.16, h * 0.15, fill=col, stroke=P.ink, stroke_width=P.lw)
        return out
    out = polygon([(x - w / 2, y), (x, y - h), (x + w / 2, y)], fill=col, stroke=P.ink, stroke_width=P.lw)
    out += polygon([(x, y - h), (x + w / 2, y), (x + w * 0.12, y)], fill=shade(col, -0.18))
    return out


def obelisk(P, it):
    x, y = it.get('x', 0), _y(P, it)
    h, w = it.get('h', 500), it.get('w', 60)
    col = P.c(it.get('color'), 'sandstone')
    return polygon([(x - w / 2, y), (x - w * 0.35, y - h), (x, y - h - w * 0.6), (x + w * 0.35, y - h), (x + w / 2, y)], fill=col, stroke=P.ink, stroke_width=P.lw)


def skyline(P, it):
    """A distant city silhouette. flavor: a list of shapes to mix: block, tower, dome, minaret, spire, pagoda, gable, smokestack."""
    x0, x1 = it.get('x0', -1200), it.get('x1', 3200)
    y = _y(P, it)
    h = it.get('h', 220)
    r = rng('sky', it.get('seed', 0), P.seed)
    flavor = it.get('flavor', ['block', 'gable', 'tower'])
    col = P.c(it.get('color'), 'stone')
    out = ''
    x = x0
    lit = it.get('lit', 0)
    while x < x1:
        kind = r.choice(flavor)
        w = r.uniform(60, 160)
        hh = h * r.uniform(0.35, 0.8)
        if kind == 'block':
            out += rect(x, y - hh, w, hh, fill=col)
        elif kind == 'gable':
            out += polygon([(x, y), (x, y - hh), (x + w / 2, y - hh - w * 0.4), (x + w, y - hh), (x + w, y)], fill=col)
        elif kind == 'tower':
            out += rect(x + w * 0.3, y - hh * 1.5, w * 0.4, hh * 1.5, fill=col) + polygon([(x + w * 0.25, y - hh * 1.5), (x + w / 2, y - hh * 1.9), (x + w * 0.75, y - hh * 1.5)], fill=col)
        elif kind == 'dome':
            out += rect(x, y - hh * 0.6, w, hh * 0.6, fill=col) + path(f'M{n(x)} {n(y - hh * 0.6)} C{n(x)} {n(y - hh * 1.3)} {n(x + w)} {n(y - hh * 1.3)} {n(x + w)} {n(y - hh * 0.6)} Z', fill=col)
        elif kind == 'minaret':
            out += rect(x + w * 0.45, y - hh * 2, 12, hh * 2, fill=col) + polygon([(x + w * 0.45 - 4, y - hh * 2), (x + w * 0.45 + 6, y - hh * 2.3), (x + w * 0.45 + 16, y - hh * 2)], fill=col)
            w = w * 0.6
        elif kind == 'spire':
            out += rect(x + w * 0.35, y - hh * 1.3, w * 0.3, hh * 1.3, fill=col) + polygon([(x + w * 0.35, y - hh * 1.3), (x + w / 2, y - hh * 2.2), (x + w * 0.65, y - hh * 1.3)], fill=col)
        elif kind == 'pagoda':
            for i in range(3):
                ww = w * (1 - i * 0.25)
                out += polygon([(x + (w - ww) / 2 - 10, y - hh * (0.4 + i * 0.3)), (x + w / 2, y - hh * (0.55 + i * 0.3)), (x + (w + ww) / 2 + 10, y - hh * (0.4 + i * 0.3))], fill=col)
            out += rect(x + w * 0.3, y - hh * 0.45, w * 0.4, hh * 0.45, fill=col)
        elif kind == 'smokestack':
            out += rect(x + w * 0.4, y - hh * 1.6, 18, hh * 1.6, fill=col) + rect(x, y - hh * 0.5, w, hh * 0.5, fill=col)
        if lit:
            for j in range(int(lit * r.uniform(0, 3))):
                out += rect(x + r.uniform(0.15, 0.75) * w, y - r.uniform(0.15, 0.5) * hh, 8, 11, fill='#ffd27a', fill_opacity=0.9)
        x += w + r.uniform(-10, 30)
    return out


def ship(P, it):
    """kind: galley, longship, cog, galleon, dhow, junk, steamship. y is the waterline."""
    x, y = it.get('x', 0), _y(P, it)
    s = it.get('scale', 1.0)
    kind = it.get('type', 'galleon')
    hull = P.c(it.get('color'), 'wood')
    sail = P.c(it.get('sail'), 'linen')
    rock_ = math.sin(P.t * 1.4 + x * 0.01) * it.get('rock', 2.5)
    bob = math.sin(P.t * 1.8 + x * 0.01) * 4
    L = 420
    out = ''
    if kind in ('galley', 'longship'):
        out += path(f'M{-L / 2} -40 Q 0 30 {L / 2} -40 L{L / 2 + 30} -90 Q{L / 2 - 10} -50 {L / 2 - 40} -40 L{-L / 2 + 40} -40 Q{-L / 2 + 10} -50 {-L / 2 - 30} -90 Z',
                    fill=hull, stroke=P.ink, stroke_width=P.lw)
        for i in range(9):
            ox = -L / 2 + 60 + i * 38
            a = math.sin(P.t * 3 + i * 0.3) * 12
            out += line((ox, -20), (ox - 30 + a, 40), stroke=P.ink, stroke_width=3)
        if kind == 'longship':
            for i in range(7):
                out += circle((-L / 2 + 70 + i * 45, -46), 16, fill=P.c(it.get('shields', 'red') if i % 2 else 'gold'), stroke=P.ink, stroke_width=2)
        out += line((0, -40), (0, -300), stroke=P.ink, stroke_width=6)
        out += rect(-110, -290, 220, 170, fill=sail, stroke=P.ink, stroke_width=P.lw)
        if it.get('stripes'):
            for i in range(0, 4, 2):
                out += rect(-110 + i * 55, -290, 55, 170, fill=P.c(it['stripes']))
    elif kind in ('cog', 'galleon', 'dhow', 'junk'):
        out += path(f'M{-L / 2 - 20} -110 L{L / 2 + 30} -90 Q{L / 2} 10 {L / 2 - 60} 20 L{-L / 2 + 30} 20 Q{-L / 2} -20 {-L / 2 - 20} -110 Z',
                    fill=hull, stroke=P.ink, stroke_width=P.lw)
        out += line((-L / 2, -60), (L / 2, -50), stroke=shade(hull, 0.25), stroke_width=4)
        if kind == 'galleon':
            out += rect(-L / 2 - 20, -170, 120, 60, fill=hull, stroke=P.ink, stroke_width=P.lw)
            for i in range(6):
                out += rect(-L / 2 + 40 + i * 55, -45, 16, 14, fill=P.ink)
        masts = {'cog': [0], 'galleon': [-110, 20, 140], 'dhow': [20], 'junk': [-80, 40]}[kind]
        for mi, mx in enumerate(masts):
            mh = 380 if mi != 0 or kind != 'galleon' else 300
            out += line((mx, -90), (mx, -90 - mh), stroke=P.ink, stroke_width=6)
            if kind == 'dhow':
                out += path(f'M{mx - 160} -140 L{mx + 30} {-90 - mh} Q{mx + 120} -200 {mx + 60} -110 Z', fill=sail, stroke=P.ink, stroke_width=P.lw)
            elif kind == 'junk':
                out += path(f'M{mx - 70} -110 L{mx - 50} {-90 - mh} L{mx + 70} {-90 - mh + 20} L{mx + 80} -110 Z', fill=P.c(it.get('sail'), 'terracotta'), stroke=P.ink, stroke_width=P.lw)
                for j in range(5):
                    yy = -110 - (mh - 20) * j / 5
                    out += line((mx - 65, yy), (mx + 78, yy), stroke=P.ink, stroke_width=2)
            else:
                for j in range(2 if kind == 'galleon' else 1):
                    top = -90 - mh + 20 + j * mh * 0.48
                    hh = mh * 0.4
                    bulge = 18 + it.get('wind', 1) * 12
                    out += path(f'M{mx - 80} {top} Q{mx + bulge} {top + hh / 2} {mx - 80} {top + hh} L{mx + 80} {top + hh} Q{mx + 80 + bulge} {top + hh / 2} {mx + 80} {top} Z',
                                fill=sail, stroke=P.ink, stroke_width=P.lw)
                    if it.get('emblem') and j == 0:
                        from .props import emblem as _em
                        out += _em(P.S, it['emblem'], (mx, top + hh / 2), hh * 0.22, it.get('emblem_color', 'red'), P.ink)
            if it.get('flag'):
                fc = [P.c(c) for c in it['flag']]
                for k, c in enumerate(fc):
                    out += rect(mx, -90 - mh - 40 + k * 40 / len(fc), 60, 40 / len(fc), fill=c)
    elif kind == 'steamship':
        out += path(f'M{-L / 2 - 20} -80 L{L / 2 + 40} -80 L{L / 2} 20 L{-L / 2 + 10} 20 Z', fill=P.c(it.get('color'), 'black'), stroke=P.ink, stroke_width=P.lw)
        out += rect(-L / 2 + 40, -150, L * 0.6, 70, fill=P.c('white'), stroke=P.ink, stroke_width=P.lw)
        for i in range(2):
            out += rect(-60 + i * 110, -260, 44, 110, fill=P.c(it.get('funnel'), 'red'), stroke=P.ink, stroke_width=P.lw)
            out += smoke(P, {'x': -38 + i * 110, 'y': -260, 'h': 300, 'color': '#4a4a4a'})
    return group(out, transform=f'translate({n(x)} {n(y + bob)}) rotate({n(rock_)}) scale({n(s * it.get("face", 1))} {n(s)})')


def cannon(P, it):
    x, y = it.get('x', 0), _y(P, it)
    s = it.get('scale', 1)
    face = it.get('face', 1)
    ang = it.get('angle', -10)
    fire_t = it.get('fire')  # time (shot seconds) the cannon fires
    recoil = 0
    out_fx = ''
    if fire_t is not None and P.t >= fire_t:
        u = P.t - fire_t
        recoil = -30 * math.exp(-u * 6) * (u < 1.5)
        if u < 1.2:
            a = 1 - u / 1.2
            out_fx = circle((200, 0), 40 + u * 160, fill='#f0ece2', fill_opacity=0.75 * a) + circle((190, 0), 30 * a, fill='#ffd27a', fill_opacity=a)
    body = (polygon([(0, -22), (180, -14), (180, 14), (0, 22)], fill=P.c(it.get('color'), 'bronze'), stroke=P.ink, stroke_width=P.lw) +
            rect(176, -18, 14, 36, fill=P.c(it.get('color'), 'bronze'), stroke=P.ink, stroke_width=P.lw) + out_fx)
    barrel = group(body, transform=f'translate({n(recoil)} -60) rotate({n(ang)})')
    carriage = polygon([(-30, 0), (-10, -70), (60, -70), (110, 0)], fill=P.c('wood'), stroke=P.ink, stroke_width=P.lw)
    wheel = circle((40, -30), 34, fill=P.c('wood'), stroke=P.ink, stroke_width=P.lw * 1.4) + circle((40, -30), 6, fill=P.ink)
    return group(carriage + barrel + wheel, transform=f'translate({n(x)} {n(y)}) scale({n(s * face)} {n(s)})')


def furniture(P, it):
    """table, chair, throne, bench, desk, chest, barrel, crate, bed, carpet, candle, bookshelf, globe, fireplace, map_table."""
    x, y = it.get('x', 0), _y(P, it)
    kind = it.get('type', 'table')
    col = P.c(it.get('color'), 'wood')
    s = it.get('scale', 1)
    st = dict(fill=col, stroke=P.ink, stroke_width=P.lw)
    if kind in ('table', 'desk', 'map_table'):
        w, h = it.get('w', 260), it.get('h', 100)
        out = rect(-w / 2, -h, w, 14, **st) + rect(-w / 2 + 12, -h + 14, 12, h - 14, **st) + rect(w / 2 - 24, -h + 14, 12, h - 14, **st)
        out = ellipse((0, 0), w * 0.5, 8, fill='#000', fill_opacity=0.18) + out
        if kind == 'map_table':
            out += polygon([(-w * 0.4, -h - 2), (w * 0.4, -h - 2), (w * 0.36, -h - 10), (-w * 0.36, -h - 10)], fill=P.c('cream'), stroke=P.ink, stroke_width=1.5)
    elif kind == 'chair':
        out = rect(-30, -92, 60, 10, **st) + rect(-30, -82, 8, 82, **st) + rect(22, -82, 8, 82, **st) + rect(-30, -190, 8, 100, **st)
    elif kind == 'throne':
        g = P.c(it.get('trim'), 'gold')
        out = rect(-60, -260, 120, 170, rx=20, fill=P.c(it.get('back'), 'crimson'), stroke=P.ink, stroke_width=P.lw)
        out += rect(-70, -110, 140, 24, fill=g, stroke=P.ink, stroke_width=P.lw)
        out += rect(-70, -86, 18, 86, fill=g, stroke=P.ink, stroke_width=P.lw) + rect(52, -86, 18, 86, fill=g, stroke=P.ink, stroke_width=P.lw)
        out += circle((0, -275), 14, fill=g, stroke=P.ink, stroke_width=P.lw)
        out = ellipse((0, 0), 90, 10, fill='#000', fill_opacity=0.2) + out
    elif kind == 'bench':
        out = rect(-120, -60, 240, 12, **st) + rect(-110, -48, 10, 48, **st) + rect(100, -48, 10, 48, **st)
    elif kind == 'chest':
        out = rect(-60, -70, 120, 70, rx=6, **st) + line((-60, -46), (60, -46), stroke=P.ink, stroke_width=P.lw) + rect(-8, -52, 16, 14, fill=P.c('gold'))
    elif kind == 'barrel':
        out = path('M-36 0 Q-46 -50 -36 -100 L36 -100 Q46 -50 36 0 Z', **st) + line((-42, -30), (42, -30), stroke=P.ink, stroke_width=3) + line((-42, -70), (42, -70), stroke=P.ink, stroke_width=3)
    elif kind == 'crate':
        out = rect(-50, -100, 100, 100, **st) + line((-50, -100), (50, 0), stroke=P.ink, stroke_width=3)
    elif kind == 'bed':
        out = rect(-150, -60, 300, 30, **st) + rect(-150, -30, 14, 30, **st) + rect(136, -30, 14, 30, **st) + rect(-150, -130, 18, 100, **st) + rect(-120, -76, 240, 18, rx=8, fill=P.c(it.get('sheet'), 'white'))
    elif kind == 'carpet':
        w = it.get('w', 420)
        cc = P.c(it.get('color'), 'crimson')
        out = polygon([(-w / 2, 0), (w / 2, 0), (w / 2 - 60, -40), (-w / 2 + 60, -40)], fill=cc, stroke=P.ink, stroke_width=P.lw)
        out += polygon([(-w / 2 + 30, -6), (w / 2 - 30, -6), (w / 2 - 70, -34), (-w / 2 + 70, -34)], fill='none', stroke=P.c(it.get('trim'), 'gold'), stroke_width=4)
    elif kind == 'candle':
        f = 1 + noise1(P.t * 9 + x, 2) * 0.15
        out = rect(-6, -40, 12, 40, fill=P.c('ivory'), stroke=P.ink, stroke_width=1.5)
        out += ellipse((0, -50 * f), 5, 10 * f, fill='#ffcf5a') + circle((0, -48), 40, fill='#ffd27a', fill_opacity=0.12)
    elif kind == 'bookshelf':
        out = rect(-90, -320, 180, 320, **st)
        r = rng('books', x)
        for row in range(4):
            yy = -320 + 20 + row * 76
            xx = -80
            while xx < 70:
                bw = r.uniform(10, 22)
                out += rect(xx, yy + r.uniform(0, 14), bw, 56, fill=P.c(r.choice(['crimson', 'navy', 'green', 'ochre', 'brown'])))
                xx += bw + 2
            out += line((-90, yy + 70), (90, yy + 70), stroke=P.ink, stroke_width=P.lw)
    elif kind == 'globe':
        out = line((0, 0), (0, -80), stroke=P.ink, stroke_width=5) + circle((0, -120), 44, fill=P.c('sky'), stroke=P.ink, stroke_width=P.lw)
        out += path('M-30 -140 Q-10 -130 -18 -110 Q0 -100 10 -125 Q25 -140 30 -110', fill='none', stroke=P.c('green'), stroke_width=8, stroke_linecap='round')
    elif kind == 'fireplace':
        out = rect(-140, -260, 280, 260, fill=P.c(it.get('color'), 'stone'), stroke=P.ink, stroke_width=P.lw)
        out += path('M-90 0 L-90 -120 Q0 -190 90 -120 L90 0 Z', fill=P.ink)
        out += fire(P, {'x': 0, 'y': -6, 'size': 0.8})
    else:
        out = ''
    return group(out, transform=f'translate({n(x)} {n(y)}) scale({n(s * it.get("face", 1))} {n(s)})')


def banner(P, it):
    """A cloth banner hanging from a wall or pole (vertical)."""
    x, y = it.get('x', 0), it.get('y', 0)
    w, h = it.get('w', 90), it.get('h', 220)
    colors = [P.c(c) for c in it.get('colors', ['crimson'])]
    sw = math.sin(P.t * 1.5 + x) * 4
    out = line((x - w / 2 - 10, y), (x + w / 2 + 10, y), stroke=P.ink, stroke_width=6, stroke_linecap='round')
    k = len(colors)
    for i, c in enumerate(colors):
        x0 = x - w / 2 + w * i / k
        x1 = x - w / 2 + w * (i + 1) / k
        out += polygon([(x0, y), (x1, y), (x1 + sw, y + h - (20 if i == k - 1 else 0)), (x0 + sw, y + h - (20 if i == 0 else 0))], fill=c)
    out += polygon([(x - w / 2, y), (x + w / 2, y), (x + w / 2 + sw, y + h - 20), (x + sw, y + h), (x - w / 2 + sw, y + h - 20)], fill='none', stroke=P.ink, stroke_width=P.lw)
    if it.get('emblem'):
        from .props import emblem as _em
        out += _em(P.S, it['emblem'], (x + sw * 0.5, y + h * 0.42), w * 0.3, it.get('emblem_color', 'gold'), P.ink)
    return out


def room(P, it):
    """An interior in one-point perspective: back wall, floor, side walls. x0..x1 is the back wall's span."""
    x0, x1 = it.get('x0', 160), it.get('x1', 1760)
    y = _y(P, it)
    h = it.get('h', 700)
    wall_c = P.c(it.get('wall'), 'sandstone')
    floor_c = P.c(it.get('floor'), 'wood')
    side = it.get('side', 600)
    out = ''
    out += polygon([(x0 - side * 3, y + 900), (x1 + side * 3, y + 900), (x1, y), (x0, y)], fill=floor_c)
    for i in range(-8, 9):
        bx = (x0 + x1) / 2 + i * (x1 - x0) / 12
        out += line((bx, y), ((x0 + x1) / 2 + i * (x1 - x0) / 12 * 4, y + 900), stroke=shade(floor_c, -0.15), stroke_width=2)
    out += rect(x0, y - h, x1 - x0, h, fill=wall_c)
    out += _blocks(P, x0, y - h, x1 - x0, h, wall_c, it.get('texture', 'plain'))
    out += polygon([(x0 - side * 3, y - h - side * 2), (x0, y - h), (x0, y), (x0 - side * 3, y + 900)], fill=shade(wall_c, -0.15))
    out += polygon([(x1 + side * 3, y - h - side * 2), (x1, y - h), (x1, y), (x1 + side * 3, y + 900)], fill=shade(wall_c, -0.15))
    out += line((x0, y), (x1, y), stroke=P.ink, stroke_width=P.lw)
    out += line((x0, y), (x0, y - h), stroke=P.ink, stroke_width=P.lw) + line((x1, y), (x1, y - h), stroke=P.ink, stroke_width=P.lw)
    if it.get('trim'):
        out += rect(x0, y - 40, x1 - x0, 40, fill=P.c(it['trim']))
        out += rect(x0, y - h, x1 - x0, 30, fill=P.c(it['trim']))
    if it.get('pattern') == 'tiles':
        tc = P.c(it.get('pattern_color'), 'turquoise')
        for i in range(int((x1 - x0) // 60)):
            for j in range(4):
                out += rect(x0 + i * 60 + 18, y - 280 + j * 60 + 18, 24, 24, fill=tc, transform=f'rotate(45 {n(x0 + i * 60 + 30)} {n(y - 280 + j * 60 + 30)})')
    return out


def ground_strip(P, it):
    x0, x1 = it.get('x0', -2000), it.get('x1', 4000)
    y = _y(P, it)
    return rect(x0, y, x1 - x0, it.get('h', 900), fill=P.c(it.get('color'), 'earth'))


def road(P, it):
    x0, x1 = it.get('x0', -2000), it.get('x1', 4000)
    y = _y(P, it)
    return rect(x0, y, x1 - x0, it.get('h', 60), fill=P.c(it.get('color'), 'sand'), fill_opacity=0.8)


def crowd(P, it):
    """Many small simple figures: an army, a crowd, a court. Cheap to draw, varied by seed.

    x0..x1, rows, count; head: helmet|cone|turban|hat|hood|bare|tall; colors: [...]; carry: spear|pike|flag|none;
    march: steps per second (0 = stand); cheer: arms up amount 0..1; face: 1 or -1; size: figure height.
    """
    x0, x1 = it.get('x0', 0), it.get('x1', 1200)
    y = _y(P, it)
    rows = it.get('rows', 3)
    count = it.get('count', 30)
    size = it.get('size', 140)
    face = it.get('face', 1)
    colors = [P.c(c) for c in it.get('colors', ['red'])]
    head = it.get('head', 'helmet')
    hc = P.c(it.get('head_color'), 'iron')
    carry = it.get('carry', 'spear')
    march = it.get('march', 0)
    cheer = it.get('cheer', 0)
    r = rng('crowd', it.get('seed', 0), x0, P.seed)
    per = max(1, count // rows)
    out = ''
    for row in range(rows):
        yy = y - row * size * 0.22
        sc = 1 - row * 0.06
        shade_u = -0.12 * row
        figs = []
        for i in range(per):
            fx = x0 + (x1 - x0) * (i + r.uniform(0.2, 0.8)) / per + row * 23
            figs.append((fx, r.random()))
        for fx, rv in figs:
            ph = P.t * march * math.pi * 2 + rv * 6
            bob = abs(math.sin(ph)) * 4 if march else 0
            out += _crowd_fig(P, fx + (P.t * march * 30 * face if it.get('advance') else 0), yy - bob, size * sc * (0.92 + rv * 0.16),
                              shade(colors[int(rv * 97) % len(colors)], shade_u), hc, head, carry, face, ph if march else None,
                              cheer * (0.5 + 0.5 * math.sin(P.t * 5 + rv * 9)) if cheer else 0, it, rv)
    return out


def _crowd_fig(P, x, y, s, col, hc, head, carry, face, ph, cheer, it, rv):
    u = s / 140
    ink = P.ink
    lw = max(2.0, 5 * u)
    hr = 15 * u
    hip = (x, y - 52 * u)
    neck = (x + 3 * face * u, y - 98 * u)
    hd = (x + 5 * face * u, y - 98 * u - hr - 2 * u)
    swing = math.sin(ph) * 14 * u if ph is not None else 0
    out = polyline([(x - 12 * u + swing, y), hip, (x + 12 * u - swing, y)], fill='none', stroke=ink, stroke_width=lw, stroke_linecap='round')
    out += path(f'M{n(neck[0] - 13 * u)} {n(neck[1])} L{n(neck[0] + 13 * u)} {n(neck[1])} L{n(hip[0] + 15 * u)} {n(hip[1] + 14 * u)} L{n(hip[0] - 15 * u)} {n(hip[1] + 14 * u)} Z',
                fill=col, stroke=ink, stroke_width=lw * 0.5)
    hand = (x + 22 * face * u, y - 62 * u - cheer * 60 * u)
    out += line((neck[0], neck[1] + 6 * u), hand, stroke=ink, stroke_width=lw, stroke_linecap='round')
    if carry in ('spear', 'pike'):
        L = (230 if carry == 'spear' else 360) * u
        tilt = it.get('tilt', 0)
        top = (hand[0] + math.sin(math.radians(tilt)) * L * 0.8 * face, hand[1] - math.cos(math.radians(tilt)) * L * 0.8)
        bot = (hand[0] - math.sin(math.radians(tilt)) * L * 0.2 * face, hand[1] + math.cos(math.radians(tilt)) * L * 0.2)
        out += line(bot, top, stroke=ink, stroke_width=lw * 0.6)
        out += polygon([(top[0] - 4 * u, top[1] + 4 * u), (top[0], top[1] - 14 * u), (top[0] + 4 * u, top[1] + 4 * u)], fill=P.c('steel'))
    elif carry == 'flag' and rv > 0.8:
        top = (hand[0], hand[1] - 200 * u)
        out += line(hand, top, stroke=ink, stroke_width=lw * 0.6)
        fc = P.c(it.get('flag_color', 'red'))
        w = math.sin(P.t * 6 + rv * 9) * 6 * u
        out += polygon([top, (top[0] + 60 * u * face, top[1] + 8 * u + w), (top[0], top[1] + 34 * u)], fill=fc, stroke=ink, stroke_width=lw * 0.4)
    elif carry == 'shield':
        out += circle((x + 14 * face * u, y - 70 * u), 22 * u, fill=P.c(it.get('shield_color', 'red')), stroke=ink, stroke_width=lw * 0.5)
    out += circle(hd, hr, fill=P.S.depth_tint(P.S.pal['head'], P.depth, P.tod), stroke=ink, stroke_width=lw * 0.5)
    if head == 'helmet':
        out += path(f'M{n(hd[0] - hr * 1.05)} {n(hd[1])} A{n(hr * 1.05)} {n(hr * 1.05)} 0 0 1 {n(hd[0] + hr * 1.05)} {n(hd[1])} Z', fill=hc, stroke=ink, stroke_width=lw * 0.4)
    elif head == 'cone':
        out += polygon([(hd[0] - hr * 1.05, hd[1] - hr * 0.2), (hd[0], hd[1] - hr * 2.2), (hd[0] + hr * 1.05, hd[1] - hr * 0.2)], fill=hc, stroke=ink, stroke_width=lw * 0.4)
    elif head == 'turban':
        out += ellipse((hd[0], hd[1] - hr * 0.6), hr * 1.15, hr * 0.85, fill=hc, stroke=ink, stroke_width=lw * 0.4)
    elif head == 'tall':
        out += polygon([(hd[0] - hr * 0.9, hd[1] - hr * 0.4), (hd[0] - hr * 0.8, hd[1] - hr * 2.6), (hd[0] + hr * 0.8, hd[1] - hr * 2.6), (hd[0] + hr * 0.9, hd[1] - hr * 0.4)], fill=hc, stroke=ink, stroke_width=lw * 0.4)
    elif head == 'hat':
        out += ellipse((hd[0], hd[1] - hr * 0.5), hr * 1.7, hr * 0.3, fill=hc, stroke=ink, stroke_width=lw * 0.4)
        out += rect(hd[0] - hr * 0.8, hd[1] - hr * 1.5, hr * 1.6, hr * 1.0, fill=hc, stroke=ink, stroke_width=lw * 0.4)
    elif head == 'hood':
        out += path(f'M{n(hd[0] + hr * 0.6 * face)} {n(hd[1] - hr)} A{n(hr * 1.2)} {n(hr * 1.2)} 0 1 {0 if face > 0 else 1} {n(hd[0] - hr * 0.2 * face)} {n(hd[1] + hr * 1.3)} Z',
                    fill=hc, stroke=ink, stroke_width=lw * 0.4)
    return out


def mount(P, it):
    """Mounts and vehicles: horse, camel, elephant, chariot, cart, carriage, tank, car, train, biplane."""
    x, y = it.get('x', 0), _y(P, it)
    kind = it.get('type', 'horse')
    s = it.get('scale', 1.0)
    face = 1 if it.get('face', 1) >= 0 else -1
    gait = it.get('gait', 0.0)
    ph = P.t * gait * math.pi * 2 + (x * 0.01)
    bob = abs(math.sin(ph)) * (7 if gait > 1.2 else 3) if gait else 0
    col = P.c(it.get('color'), 'chestnut' if kind == 'horse' else ('sand' if kind == 'camel' else 'grey'))
    dark = shade(col, -0.22)
    tack = P.c(it.get('tack'), 'crimson')
    lw = P.lw
    out = ''
    if kind in ('horse', 'camel'):
        camel = kind == 'camel'
        bh = 152 if not camel else 190
        bl = 170 if not camel else 180
        sw1 = math.sin(ph) * (32 if gait else 5)
        sw2 = math.cos(ph) * (32 if gait else 5)
        # far legs
        for lx, sw in ((-bl * 0.36, -sw1), (bl * 0.36, -sw2)):
            out += polyline([(lx, -bh + 25), (lx + sw * 0.45, -bh * 0.48), (lx + sw, 0)],
                            fill='none', stroke=dark, stroke_width=lw * 2.3, stroke_linecap='round', stroke_linejoin='round')
        # body
        if camel:
            d = (f'M{n(-bl * 0.5)} {n(-bh + 24)} C{n(-bl * 0.56)} {n(-bh - 30)} {n(-bl * 0.15)} {n(-bh - 82)} 0 {n(-bh - 76)} '
                 f'C{n(bl * 0.18)} {n(-bh - 82)} {n(bl * 0.5)} {n(-bh - 20)} {n(bl * 0.52)} {n(-bh + 24)} '
                 f'Q0 {n(-bh + 48)} {n(-bl * 0.5)} {n(-bh + 24)} Z')
        else:
            d = (f'M{n(-bl * 0.52)} {n(-bh + 22)} C{n(-bl * 0.56)} {n(-bh - 34)} {n(bl * 0.56)} {n(-bh - 34)} {n(bl * 0.52)} {n(-bh + 22)} '
                 f'Q0 {n(-bh + 46)} {n(-bl * 0.52)} {n(-bh + 22)} Z')
        out += path(d, fill=col, stroke=P.ink, stroke_width=lw)
        # tail
        tsw = math.sin(P.t * 3 + x) * 10 + (18 if gait else 0)
        out += path(f'M{n(-bl * 0.5)} {n(-bh - 10)} Q{n(-bl * 0.72 - tsw)} {n(-bh + 10)} {n(-bl * 0.65 - tsw)} {n(-bh + 75)}',
                    fill='none', stroke=P.ink, stroke_width=lw * 2.4, stroke_linecap='round')
        # saddle cloth
        if it.get('saddle', True):
            sy = -bh - (52 if camel else 24)
            out += polygon([(-34, sy), (34, sy), (40, sy + 38), (-40, sy + 38)], fill=tack, stroke=P.ink, stroke_width=lw * 0.8)
        # neck and head
        nod = math.sin(ph) * (6 if gait else 1)
        if camel:
            neck_d = f'M{n(bl * 0.35)} {n(-bh + 5)} Q{n(bl * 0.68)} {n(-bh + 10)} {n(bl * 0.72)} {n(-bh - 85 + nod)}'
            out += path(neck_d, fill='none', stroke=col, stroke_width=28, stroke_linecap='round')
            out += path(neck_d, fill='none', stroke=P.ink, stroke_width=lw)
            hx, hy = bl * 0.75, -bh - 92 + nod
            out += ellipse((hx + 18, hy), 26, 14, fill=col, stroke=P.ink, stroke_width=lw)
        else:
            nx0, ny0 = bl * 0.34, -bh - 10
            nx1, ny1 = bl * 0.68, -bh - 92 + nod
            out += polygon([(nx0 - 16, ny0 + 22), (nx0 + 22, ny0 + 26), (nx1 + 16, ny1 + 12), (nx1 - 14, ny1 - 10)],
                           fill=col, stroke=P.ink, stroke_width=lw)
            out += polygon([(nx1 - 10, ny1 - 14), (nx1 + 48, ny1 + 10), (nx1 + 40, ny1 + 28), (nx1 - 4, ny1 + 18)],
                           fill=col, stroke=P.ink, stroke_width=lw)
            out += polygon([(nx1 - 6, ny1 - 14), (nx1 + 2, ny1 - 32), (nx1 + 12, ny1 - 12)], fill=col, stroke=P.ink, stroke_width=lw * 0.8)
            out += circle((nx1 + 16, ny1 + 2), 3.5, fill=P.ink)
            if it.get('reins', True):
                out += path(f'M{n(nx1 + 32)} {n(ny1 + 20)} Q{n(bl * 0.25)} {n(-bh - 15)} -8 {n(-bh - 32)}',
                            fill='none', stroke=P.ink, stroke_width=2)
        # near legs
        for lx, sw in ((-bl * 0.3, sw1), (bl * 0.42, sw2)):
            out += polyline([(lx, -bh + 25), (lx + sw * 0.45, -bh * 0.48), (lx + sw, 0)],
                            fill='none', stroke=col, stroke_width=lw * 2.3, stroke_linecap='round', stroke_linejoin='round')
            out += polyline([(lx, -bh + 25), (lx + sw * 0.45, -bh * 0.48), (lx + sw, 0)],
                            fill='none', stroke=P.ink, stroke_width=lw * 0.9, stroke_linecap='round', stroke_linejoin='round')
    elif kind == 'elephant':
        bh, bl = 230, 210
        sw = math.sin(ph) * (18 if gait else 2)
        for lx, sgn in ((-bl * 0.32, -1), (bl * 0.32, 1)):
            out += line((lx, -bh + 40), (lx + sw * sgn, 0), stroke=dark, stroke_width=34, stroke_linecap='round')
        out += ellipse((0, -bh), bl * 0.58, 95, fill=col, stroke=P.ink, stroke_width=lw)
        out += circle((bl * 0.52, -bh - 25), 58, fill=col, stroke=P.ink, stroke_width=lw)
        out += ellipse((bl * 0.32, -bh - 20), 34, 48, fill=dark, stroke=P.ink, stroke_width=lw)
        out += path(f'M{n(bl * 0.92)} {n(-bh - 20)} Q{n(bl * 1.15)} {n(-bh + 60)} {n(bl * 0.95)} {n(-bh + 110)}',
                    fill='none', stroke=col, stroke_width=24, stroke_linecap='round')
        out += path(f'M{n(bl * 0.82)} {n(-bh + 5)} Q{n(bl * 1.25)} {n(-bh + 25)} {n(bl * 1.35)} {n(-bh - 20)}',
                    fill='none', stroke=P.c('ivory'), stroke_width=10, stroke_linecap='round')
        for lx, sgn in ((-bl * 0.26, 1), (bl * 0.38, -1)):
            out += line((lx, -bh + 40), (lx + sw * sgn, 0), stroke=col, stroke_width=34, stroke_linecap='round')
        if it.get('howdah', True):
            out += rect(-48, -bh - 135, 96, 45, rx=6, fill=tack, stroke=P.ink, stroke_width=lw)
    elif kind in ('chariot', 'cart', 'carriage'):
        out += mount(P, {'type': 'horse', 'x': 150, 'y': 0, 'gait': gait, 'color': it.get('horse_color', 'chestnut'), 'saddle': False})
        out += line((-20, -95), (140, -115), stroke=P.ink, stroke_width=6)
        wcol = P.c(it.get('color'), 'wood')
        if kind == 'chariot':
            out += path('M-85 -35 L-85 -125 Q-20 -135 10 -80 L10 -35 Z', fill=tack, stroke=P.ink, stroke_width=lw)
            r = 42
        elif kind == 'carriage':
            out += rect(-150, -210, 160, 145, rx=16, fill=wcol, stroke=P.ink, stroke_width=lw)
            out += rect(-115, -185, 50, 48, rx=4, fill=P.c('sky'), stroke=P.ink, stroke_width=lw * 0.8)
            out += circle((-120, -45), 42, fill='none', stroke=P.ink, stroke_width=lw * 1.6)
            r = 48
        else:
            out += rect(-130, -115, 140, 55, fill=wcol, stroke=P.ink, stroke_width=lw)
            r = 42
        out += circle((-35, -r), r, fill='none', stroke=P.ink, stroke_width=lw * 1.8)
        for i in range(6):
            a = P.t * (gait or 1) * 4 + i * math.pi / 3
            out += line((-35, -r), (-35 + math.cos(a) * r, -r + math.sin(a) * r), stroke=P.ink, stroke_width=3)
    elif kind == 'tank':
        tcol = P.c(it.get('color'), 'field_grey')
        out += rect(-140, -52, 280, 48, rx=22, fill=shade(tcol, -0.25), stroke=P.ink, stroke_width=lw * 1.4)
        for i in range(6):
            out += circle((-110 + i * 44, -28), 18, fill=P.c('iron'), stroke=P.ink, stroke_width=lw)
        out += polygon([(-150, -50), (-110, -105), (105, -105), (145, -50)], fill=tcol, stroke=P.ink, stroke_width=lw)
        out += path('M-55 -105 L-40 -150 L55 -150 L70 -105 Z', fill=tcol, stroke=P.ink, stroke_width=lw)
        out += line((60, -130), (195, -136), stroke=P.ink, stroke_width=14, stroke_linecap='round')
        out += line((60, -130), (195, -136), stroke=tcol, stroke_width=9, stroke_linecap='round')
    elif kind == 'train':
        bcol = P.c(it.get('color'), 'black')
        out += rect(-220, -165, 290, 110, rx=10, fill=bcol, stroke=P.ink, stroke_width=lw)
        out += rect(-220, -230, 95, 175, fill=P.c('crimson'), stroke=P.ink, stroke_width=lw)
        out += rect(-195, -205, 45, 42, fill=P.c('sky'), stroke=P.ink, stroke_width=lw * 0.8)
        out += rect(20, -235, 32, 70, fill=bcol, stroke=P.ink, stroke_width=lw)
        out += smoke(P, {'x': 36, 'y': -235, 'h': 220, 'drift': -120})
        for wx in (-170, -85, 0, 60):
            out += circle((wx, -28), 28, fill=P.c('iron'), stroke=P.ink, stroke_width=lw * 1.3)
        out += polygon([(70, -55), (115, -8), (70, -8)], fill=P.c('iron'), stroke=P.ink, stroke_width=lw)
    elif kind == 'car':
        ccol = P.c(it.get('color'), 'navy')
        out += path('M-130 -35 L-130 -85 L-70 -90 L-45 -140 L55 -140 L85 -90 L135 -82 L135 -35 Z', fill=ccol, stroke=P.ink, stroke_width=lw)
        out += polygon([(-38, -132), (48, -132), (72, -92), (-60, -92)], fill=P.c('sky'), stroke=P.ink, stroke_width=lw * 0.8)
        for wx in (-82, 82):
            out += circle((wx, -34), 32, fill=P.c('black'), stroke=P.ink, stroke_width=lw) + circle((wx, -34), 14, fill=P.c('silver'))
    elif kind == 'biplane':
        pcol = P.c(it.get('color'), 'crimson')
        out += path('M-140 -10 L80 -22 L100 10 L-140 12 Z', fill=pcol, stroke=P.ink, stroke_width=lw)
        out += polygon([(-140, -10), (-165, -45), (-125, -10)], fill=pcol, stroke=P.ink, stroke_width=lw)
        out += rect(-40, -65, 110, 12, rx=4, fill=pcol, stroke=P.ink, stroke_width=lw)
        out += rect(-40, 12, 110, 12, rx=4, fill=pcol, stroke=P.ink, stroke_width=lw)
        out += line((-20, -53), (-20, 12), stroke=P.ink, stroke_width=3) + line((45, -53), (45, 12), stroke=P.ink, stroke_width=3)
        out += ellipse((104, -6), 6, 42 * (0.4 + 0.6 * abs(math.sin(P.t * 25))), fill=P.c('silver'), fill_opacity=0.6)
    return group(out, transform=f'translate({n(x)} {n(y - bob)}) scale({n(s * face)} {n(s)})')


MOUNT_HEIGHT = {'horse': 168, 'camel': 230, 'elephant': 320, 'chariot': 42, 'cart': 65, 'carriage': 95}


def bridge(P, it):
    x0, x1 = it.get('x0', 100), it.get('x1', 1820)
    y = _y(P, it)
    h = it.get('h', 190)
    arches = it.get('arches', 4)
    col = P.c(it.get('color'), 'stone')
    w = x1 - x0
    aw = w / arches
    d = f'M{n(x0)} {n(y - h)} L{n(x1)} {n(y - h)} L{n(x1)} {n(y)} '
    for i in range(arches - 1, -1, -1):
        ax1 = x0 + (i + 0.88) * aw
        ax0 = x0 + (i + 0.12) * aw
        r = (ax1 - ax0) / 2
        d += f'L{n(ax1)} {n(y)} A{n(r)} {n(r * 0.9)} 0 0 0 {n(ax0)} {n(y)} '
    d += f'L{n(x0)} {n(y)} Z'
    out = path(d, fill=col, stroke=P.ink, stroke_width=P.lw)
    out += rect(x0, y - h - 18, w, 18, fill=shade(col, 0.08), stroke=P.ink, stroke_width=P.lw)
    return out


def ruins(P, it):
    x, y = it.get('x', 960), _y(P, it)
    w = it.get('w', 700)
    col = P.c(it.get('color'), 'marble')
    r = rng('ruins', x, P.seed)
    out = ''
    for i in range(it.get('columns', 4)):
        cx = x - w / 2 + w * i / max(1, it.get('columns', 4) - 1)
        ch = r.uniform(110, 340)
        out += polygon([(cx - 22, y), (cx - 22, y - ch), (cx - 4, y - ch - 18), (cx + 12, y - ch + 8), (cx + 22, y - ch + 2), (cx + 22, y)],
                       fill=col, stroke=P.ink, stroke_width=P.lw)
        out += rect(cx - 32, y - 16, 64, 16, fill=col, stroke=P.ink, stroke_width=P.lw)
    for i in range(5):
        bx = x + r.uniform(-w * 0.45, w * 0.45)
        out += rect(bx, y - 28, r.uniform(36, 72), 28, fill=shade(col, -0.08), stroke=P.ink, stroke_width=P.lw)
    return out


def barricade(P, it):
    x0, x1 = it.get('x0', 300), it.get('x1', 1600)
    y = _y(P, it)
    kind = it.get('type', 'palisade')
    out = ''
    if kind == 'palisade':
        col = P.c(it.get('color'), 'wood')
        x = x0
        while x < x1:
            out += polygon([(x, y), (x, y - 140), (x + 11, y - 168), (x + 22, y - 140), (x + 22, y)], fill=col, stroke=P.ink, stroke_width=P.lw)
            x += 20
    elif kind == 'trench':
        col = P.c(it.get('color'), 'sand')
        x = x0
        while x < x1:
            for row in range(3):
                out += ellipse((x + (row % 2) * 22, y - 14 - row * 22), 32, 13, fill=shade(col, -0.05 * row), stroke=P.ink, stroke_width=P.lw)
            x += 58
        if it.get('wire', True):
            pts_ = [(x0 + (x1 - x0) * i / 28, y - 85 - (i % 2) * 26) for i in range(29)]
            out += polyline(pts_, fill='none', stroke=P.ink, stroke_width=2.5)
    return out


def statue(P, it):
    x, y = it.get('x', 960), _y(P, it)
    h = it.get('h', 360)
    col = P.c(it.get('color'), 'marble')
    ph = h * 0.42
    out = rect(x - 56, y - ph, 112, ph, fill=col, stroke=P.ink, stroke_width=P.lw)
    out += rect(x - 68, y - 22, 136, 22, fill=col, stroke=P.ink, stroke_width=P.lw)
    out += rect(x - 64, y - ph - 14, 128, 14, fill=col, stroke=P.ink, stroke_width=P.lw)
    fh = h - ph - 14
    top = y - ph - 14
    out += polygon([(x - 26, top), (x - 32, top - fh * 0.72), (x + 32, top - fh * 0.72), (x + 26, top)], fill=col, stroke=P.ink, stroke_width=P.lw)
    out += circle((x, top - fh * 0.86), fh * 0.13, fill=col, stroke=P.ink, stroke_width=P.lw)
    return out


def map_view(P, it):
    """Animated historical map in world space (x0..x1, y0..y1).
    lands: [{"points": [[x,y],...], "color": "sandstone", "name": "ANATOLIA"}]
    territories: [{"points": [[x,y],...], "color": "crimson", "grow": [t0, t1]}]
    routes: [{"points": [[x,y],...], "color": "crimson", "from": 0.2, "to": 2.0, "dashed": true, "label": "..."}]
    pins: [{"x": 960, "y": 540, "label": "Constantinople", "icon": "star|city|battle|port", "t": 0.2}]
    """
    from .svg import esc
    x0, y0 = it.get('x0', -400), it.get('y0', -200)
    w, h = it.get('w', 2720), it.get('h', 1500)
    sea = P.c(it.get('sea_color'), 'water')
    land_default = P.c(it.get('land_color'), 'sandstone')
    fam = P.S.font
    out = rect(x0, y0, w, h, fill=sea)
    # latitude/longitude grid
    gcol = shade(sea, 0.16)
    for gx in range(int(x0), int(x0 + w), 240):
        out += line((gx, y0), (gx, y0 + h), stroke=gcol, stroke_width=1.4, stroke_opacity=0.45, stroke_dasharray='8 10')
    for gy in range(int(y0), int(y0 + h), 240):
        out += line((x0, gy), (x0 + w, gy), stroke=gcol, stroke_width=1.4, stroke_opacity=0.45, stroke_dasharray='8 10')
    # landmasses
    for ld in it.get('lands', []):
        pts_ = [tuple(p) for p in ld['points']]
        d = smooth_path(pts_, closed=True) if ld.get('smooth', True) else 'M' + ' L'.join(f'{n(px)} {n(py)}' for px, py in pts_) + ' Z'
        lcol = P.c(ld.get('color'), 'sandstone') if ld.get('color') else land_default
        out += path(d, fill=shade(sea, -0.25), transform='translate(6 8)', fill_opacity=0.35)
        out += path(d, fill=lcol, stroke=P.ink, stroke_width=P.lw * 1.1)
        if ld.get('name'):
            cx = ld.get('lx', sum(p[0] for p in pts_) / len(pts_))
            cy = ld.get('ly', sum(p[1] for p in pts_) / len(pts_))
            out += (f'<text x="{n(cx)}" y="{n(cy)}" font-family="{fam}" font-size="{n(ld.get("size", 38))}" font-weight="700" '
                    f'letter-spacing="6" text-anchor="middle" fill="{P.ink}" fill-opacity="0.55">{esc(ld["name"])}</text>')
    # territories (shaded regions, optionally growing over [t0, t1])
    for tr in it.get('territories', []):
        pts_ = [tuple(p) for p in tr['points']]
        u = 1.0
        if tr.get('grow'):
            t0, t1 = tr['grow']
            u = max(0.0, min(1.0, (P.t - t0) / max(0.01, t1 - t0)))
        if u <= 0:
            continue
        cx = sum(p[0] for p in pts_) / len(pts_)
        cy = sum(p[1] for p in pts_) / len(pts_)
        scaled = [(cx + (px - cx) * u, cy + (py - cy) * u) for px, py in pts_]
        d = smooth_path(scaled, closed=True) if tr.get('smooth', True) else 'M' + ' L'.join(f'{n(px)} {n(py)}' for px, py in scaled) + ' Z'
        tcol = P.c(tr.get('color'), 'crimson')
        out += path(d, fill=tcol, fill_opacity=tr.get('opacity', 0.38), stroke=tcol, stroke_width=3, stroke_dasharray='10 6')
    # routes (animated arrows)
    for rt in it.get('routes', []):
        pts_ = [tuple(p) for p in rt['points']]
        t0, t1 = rt.get('from', 0.0), rt.get('to', 1.5)
        u = max(0.0, min(1.0, (P.t - t0) / max(0.01, t1 - t0)))
        if u <= 0 or len(pts_) < 2:
            continue
        sub, tip, ang = _trim_polyline(pts_, u)
        rcol = P.c(rt.get('color'), 'crimson')
        rw = rt.get('width', 8)
        d = smooth_path(sub) if len(sub) > 2 and rt.get('smooth', True) else 'M' + ' L'.join(f'{n(px)} {n(py)}' for px, py in sub)
        dash = '16 12' if rt.get('dashed') else None
        out += path(d, fill='none', stroke=P.ink, stroke_width=rw + 4, stroke_linecap='round', stroke_dasharray=dash)
        out += path(d, fill='none', stroke=rcol, stroke_width=rw, stroke_linecap='round', stroke_dasharray=dash)
        if rt.get('arrow', True):
            ah = rw * 2.4
            out += group(polygon([(0, 0), (-ah, -ah * 0.55), (-ah * 0.75, 0), (-ah, ah * 0.55)], fill=rcol, stroke=P.ink, stroke_width=2),
                         transform=f'translate({n(tip[0])} {n(tip[1])}) rotate({n(ang)})')
    # pins
    for pin in it.get('pins', []):
        pt = pin.get('t', 0.0)
        if P.t < pt:
            continue
        u = min(1.0, (P.t - pt) / 0.35)
        px, py = pin['x'], pin['y']
        pcol = P.c(pin.get('color'), 'accent')
        icon = pin.get('icon', 'city')
        if pin.get('pulse', icon in ('battle', 'star')):
            pr = 16 + ((P.t * 1.4) % 1.0) * 38
            pa = 1.0 - ((P.t * 1.4) % 1.0)
            out += circle((px, py), pr, fill='none', stroke=pcol, stroke_width=3, stroke_opacity=pa * 0.7)
        if icon == 'battle':
            out += group(line((-14, -14), (14, 14), stroke=pcol, stroke_width=5, stroke_linecap='round') +
                         line((-14, 14), (14, -14), stroke=pcol, stroke_width=5, stroke_linecap='round'),
                         transform=f'translate({n(px)} {n(py)}) scale({n(u)})')
        elif icon == 'star':
            from .props import emblem as _em
            out += group(_em(P.S, 'star', (0, 0), 16, pin.get('color', 'accent'), P.ink),
                         transform=f'translate({n(px)} {n(py)}) scale({n(u)})')
        else:
            out += circle((px, py), 10 * u, fill=pcol, stroke=P.ink, stroke_width=3)
        if pin.get('label'):
            ly = py - 20 if pin.get('above', True) else py + 34
            out += (f'<text x="{n(px)}" y="{n(ly)}" font-family="{fam}" font-size="{n(pin.get("size", 32))}" font-weight="700" '
                    f'text-anchor="middle" fill="{P.ink}" stroke="#fbf6ea" stroke-width="6" stroke-opacity="0.75" paint-order="stroke">{esc(pin["label"])}</text>')
    # compass rose
    if it.get('compass', True):
        cx, cy = it.get('compass_at', (x0 + w - 220, y0 + 220))
        out += circle((cx, cy), 48, fill='none', stroke=P.ink, stroke_width=2, stroke_opacity=0.55)
        out += polygon([(cx, cy - 58), (cx - 10, cy), (cx, cy - 12), (cx + 10, cy)], fill=P.ink, fill_opacity=0.65)
        out += polygon([(cx, cy + 58), (cx - 8, cy), (cx + 8, cy)], fill=P.ink, fill_opacity=0.3)
    return out


def _trim_polyline(pts_, u):
    segs = [math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts_, pts_[1:])]
    total = sum(segs) or 1
    target = total * u
    out = [pts_[0]]
    acc = 0.0
    ang = 0.0
    for a, b, L in zip(pts_, pts_[1:], segs):
        ang = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))
        if acc + L >= target:
            w = (target - acc) / max(1e-6, L)
            tip = (a[0] + (b[0] - a[0]) * w, a[1] + (b[1] - a[1]) * w)
            out.append(tip)
            return out, tip, ang
        out.append(b)
        acc += L
    return out, pts_[-1], ang


def timeline_view(P, it):
    """A historical timeline bar in world space: ticks, events, and a sliding marker."""
    from .svg import esc
    x0, x1 = it.get('x0', 300), it.get('x1', 1620)
    y = it.get('y', 540)
    y_start, y_end = it.get('start_year', 1400), it.get('end_year', 1500)
    fam = P.S.font
    out = line((x0, y), (x1, y), stroke=P.ink, stroke_width=6, stroke_linecap='round')
    step = it.get('step', max(1, (y_end - y_start) // 5))
    yr = y_start
    while yr <= y_end:
        u = (yr - y_start) / max(1, y_end - y_start)
        xx = x0 + (x1 - x0) * u
        out += line((xx, y - 16), (xx, y + 16), stroke=P.ink, stroke_width=4)
        out += f'<text x="{n(xx)}" y="{n(y + 52)}" font-family="{fam}" font-size="30" text-anchor="middle" fill="{P.ink}">{yr}</text>'
        yr += step
    for ev in it.get('events', []):
        u = (ev['year'] - y_start) / max(1, y_end - y_start)
        xx = x0 + (x1 - x0) * u
        ecol = P.c(ev.get('color'), 'accent')
        out += circle((xx, y), 12, fill=ecol, stroke=P.ink, stroke_width=3)
        if ev.get('label'):
            out += (f'<text x="{n(xx)}" y="{n(y - 30)}" font-family="{fam}" font-size="32" font-weight="700" text-anchor="middle" '
                    f'fill="{P.ink}">{esc(ev["label"])}</text>')
    if it.get('marker') is not None:
        m = it['marker']
        if isinstance(m, (list, tuple)):
            t_dur = it.get('dur', 2.0)
            u_t = min(1.0, P.t / max(0.01, t_dur))
            cur = m[0] + (m[1] - m[0]) * (1 - (1 - u_t) ** 3)
        else:
            cur = float(m)
        u = (cur - y_start) / max(1, y_end - y_start)
        xx = x0 + (x1 - x0) * u
        out += polygon([(xx, y - 18), (xx - 16, y - 46), (xx + 16, y - 46)], fill=P.S.accent, stroke=P.ink, stroke_width=3)
    return out


def document_view(P, it):
    """A large historical document/scroll/decree/tablet/newspaper at (x, y)."""
    from .svg import esc
    x, y = it.get('x', 960), it.get('y', 500)
    w, h = it.get('w', 520), it.get('h', 640)
    kind = it.get('type', 'scroll')
    col = P.c(it.get('color'), 'stone' if kind == 'tablet' else 'cream')
    fam = P.S.font
    out = ''
    if kind == 'tablet':
        out += path(f'M{n(x - w / 2)} {n(y + h / 2)} L{n(x - w / 2)} {n(y - h / 2 + 80)} A{n(w / 2)} 80 0 0 1 {n(x + w / 2)} {n(y - h / 2 + 80)} L{n(x + w / 2)} {n(y + h / 2)} Z',
                    fill=col, stroke=P.ink, stroke_width=P.lw * 1.3)
    else:
        out += rect(x - w / 2, y - h / 2, w, h, rx=8, fill=col, stroke=P.ink, stroke_width=P.lw * 1.2)
        if kind == 'scroll':
            rh = 28
            out += rect(x - w / 2 - 24, y - h / 2 - rh / 2, w + 48, rh, rx=12, fill=shade(col, -0.15), stroke=P.ink, stroke_width=P.lw)
            out += rect(x - w / 2 - 24, y + h / 2 - rh / 2, w + 48, rh, rx=12, fill=shade(col, -0.15), stroke=P.ink, stroke_width=P.lw)
    if it.get('title'):
        out += (f'<text x="{n(x)}" y="{n(y - h / 2 + 88)}" font-family="{fam}" font-size="{n(it.get("title_size", 42))}" font-weight="700" '
                f'text-anchor="middle" fill="{P.ink}">{esc(it["title"])}</text>')
    lines_n = it.get('lines', 7)
    r = rng('doc', x, y)
    for i in range(lines_n):
        ly = y - h / 2 + 145 + i * ((h - 240) / max(1, lines_n))
        lw_ = w * (0.72 if i < lines_n - 1 else 0.45) * r.uniform(0.88, 1.0)
        out += line((x - w * 0.36, ly), (x - w * 0.36 + lw_, ly), stroke=P.ink, stroke_width=4, stroke_opacity=0.55, stroke_linecap='round')
    if it.get('seal', True) and kind != 'tablet':
        st = it.get('seal_t', 0.4)
        if P.t >= st:
            u = min(1.0, (P.t - st) / 0.22)
            sc = 1.6 - 0.6 * u
            sx, sy = x + w * 0.22, y + h * 0.3
            scol = P.c(it.get('seal_color'), 'crimson')
            out += group(polygon([(-12, 0), (-22, 55), (-4, 42), (6, 58), (18, 0)], fill=scol, stroke=P.ink, stroke_width=2) +
                         circle((0, 0), 32, fill=scol, stroke=P.ink, stroke_width=3) +
                         circle((0, 0), 22, fill='none', stroke=shade(scol, 0.25), stroke_width=2),
                         transform=f'translate({n(sx)} {n(sy)}) scale({n(sc)})')
    return out


def raw(P, it):
    x, y = it.get('x', 0), it.get('y', 0)
    return group(it.get('svg', ''), transform=f'translate({n(x)} {n(y)}) scale({n(it.get("scale", 1))})')


ITEMS = {
    'hills': hills, 'mountains': mountains, 'tree': tree, 'bush': bush, 'rock': rock, 'grass': grass, 'water': water,
    'sun': sun, 'moon': moon, 'stars': stars, 'clouds': clouds, 'smoke': smoke, 'fire': fire,
    'wall': wall, 'tower': tower, 'window': window, 'arch': arch, 'gate': arch, 'column': column, 'colonnade': colonnade,
    'dome': dome, 'minaret': minaret, 'building': building, 'house': building, 'tent': tent, 'pyramid': pyramid,
    'obelisk': obelisk, 'skyline': skyline, 'city': skyline, 'ship': ship, 'cannon': cannon, 'furniture': furniture,
    'banner': banner, 'room': room, 'ground': ground_strip, 'road': road, 'crowd': crowd, 'army': crowd,
    'mount': mount, 'vehicle': mount, 'bridge': bridge, 'ruins': ruins, 'barricade': barricade, 'trench': barricade,
    'statue': statue, 'map': map_view, 'timeline': timeline_view, 'document': document_view, 'svg': raw,
}


def draw_item(P, it):
    kind = it.get('kind')
    if kind not in ITEMS:
        raise ValueError(f'Unknown item kind "{kind}". Known: {", ".join(sorted(ITEMS))}. For anything else use "svg".')
    out = ITEMS[kind](P, it)
    if it.get('opacity') is not None and kind not in ('clouds',):
        out = group(out, opacity=it['opacity'])
    return out
