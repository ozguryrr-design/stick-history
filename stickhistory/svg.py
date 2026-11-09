"""Tiny helpers for writing SVG strings and working with colours."""
import math
import random


def n(v):
    """Compact number formatting."""
    if isinstance(v, int):
        return str(v)
    s = f'{v:.2f}'.rstrip('0').rstrip('.')
    return '0' if s in ('-0', '') else s


def pts(points):
    return ' '.join(f'{n(x)},{n(y)}' for x, y in points)


def attrs(**kw):
    out = []
    for k, v in kw.items():
        if v is None or v is False:
            continue
        k = k.rstrip('_').replace('_', '-')
        if isinstance(v, float):
            v = n(v)
        out.append(f'{k}="{v}"')
    return ' '.join(out)


def esc(text):
    return (str(text).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;'))


def polyline(points, **kw):
    return f'<polyline points="{pts(points)}" {attrs(**kw)}/>'


def polygon(points, **kw):
    return f'<polygon points="{pts(points)}" {attrs(**kw)}/>'


def line(a, b, **kw):
    return f'<line x1="{n(a[0])}" y1="{n(a[1])}" x2="{n(b[0])}" y2="{n(b[1])}" {attrs(**kw)}/>'


def circle(c, r, **kw):
    return f'<circle cx="{n(c[0])}" cy="{n(c[1])}" r="{n(r)}" {attrs(**kw)}/>'


def ellipse(c, rx, ry, **kw):
    return f'<ellipse cx="{n(c[0])}" cy="{n(c[1])}" rx="{n(rx)}" ry="{n(ry)}" {attrs(**kw)}/>'


def rect(x, y, w, h, **kw):
    return f'<rect x="{n(x)}" y="{n(y)}" width="{n(w)}" height="{n(h)}" {attrs(**kw)}/>'


def path(d, **kw):
    return f'<path d="{d}" {attrs(**kw)}/>'


def group(body, **kw):
    a = attrs(**kw)
    return f'<g {a}>{body}</g>' if a else f'<g>{body}</g>'


def smooth_path(points, closed=False):
    """Catmull-Rom through points, as cubic beziers."""
    if len(points) < 3:
        return 'M' + ' L'.join(f'{n(x)} {n(y)}' for x, y in points)
    p = list(points)
    if closed:
        p = [p[-1]] + p + [p[0], p[1]]
    else:
        p = [p[0]] + p + [p[-1]]
    d = f'M{n(p[1][0])} {n(p[1][1])}'
    for i in range(1, len(p) - 2):
        p0, p1, p2, p3 = p[i - 1], p[i], p[i + 1], p[i + 2]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d += f' C{n(c1[0])} {n(c1[1])} {n(c2[0])} {n(c2[1])} {n(p2[0])} {n(p2[1])}'
    return d + (' Z' if closed else '')


# ---------------------------------------------------------------- colour
def hex2rgb(h):
    h = h.lstrip('#')
    if len(h) == 3:
        h = ''.join(c * 2 for c in h)
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def rgb2hex(c):
    return '#%02x%02x%02x' % tuple(max(0, min(255, round(v))) for v in c)


def mix(a, b, u):
    """Blend colour a toward b by u (0..1)."""
    ca, cb = hex2rgb(a), hex2rgb(b)
    return rgb2hex([x + (y - x) * u for x, y in zip(ca, cb)])


def shade(c, u):
    """u < 0 darkens toward black, u > 0 lightens toward white."""
    return mix(c, '#000000', -u) if u < 0 else mix(c, '#ffffff', u)


def luma(c):
    r, g, b = hex2rgb(c)
    return (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255


# ---------------------------------------------------------------- deterministic noise
def rng(*seed):
    return random.Random(hash_seed(*seed))


def hash_seed(*parts):
    h = 2166136261
    for ch in '|'.join(str(p) for p in parts):
        h = ((h ^ ord(ch)) * 16777619) & 0xFFFFFFFF
    return h


def noise1(x, seed=0):
    """Smooth 1D value noise in -1..1."""
    i = math.floor(x)
    f = x - i
    a = _hash01(i, seed) * 2 - 1
    b = _hash01(i + 1, seed) * 2 - 1
    u = f * f * (3 - 2 * f)
    return a + (b - a) * u


def _hash01(i, seed):
    h = hash_seed(i, seed)
    return (h & 0xFFFF) / 0xFFFF


def rot(p, deg, origin=(0, 0)):
    a = math.radians(deg)
    x, y = p[0] - origin[0], p[1] - origin[1]
    return (origin[0] + x * math.cos(a) - y * math.sin(a), origin[1] + x * math.sin(a) + y * math.cos(a))
