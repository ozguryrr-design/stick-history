"""The character rig: one stick figure, dressed by parametric parts, posed by angles.

Local frame: feet on y=0, facing right (+x), about 300 units tall at scale 1. The scene mirrors the whole group for
characters facing left. `yaw` 1 is profile, 0 is facing the camera; in between the far limbs foreshorten.

Angles (degrees). Limbs: 0 hangs straight down, 90 points forward, 180 points up, negative goes backward.
  lean        torso, + forward          head        head tilt, + forward (nod)
  arm_n/arm_f upper arm vs torso        elbow_n/f   forearm bend, + bends forward/up
  leg_n/leg_f thigh vs vertical         knee_n/f    shin bend, usually negative (shin goes back)
  lift        raise the whole body (jumps)          hip_h       sitting: hip height above the ground
Near (n) limbs are drawn in front of the body, far (f) behind it.
"""
import math

from . import props as P
from .svg import n, line, circle, polygon, path, polyline, group, ellipse, shade, mix, noise1, smooth_path

HEAD_R = 34
NECK = 6
TORSO = 92
UPPER_ARM = 48
FOREARM = 46
THIGH = 60
SHIN = 60
FOOT = 15
SHOULDER_DROP = 12

BUILD = {'slim': 13, 'average': 17, 'broad': 22, 'heavy': 28, 'child': 13}

POSES = {
    'stand': {'lean': 0, 'head': 0, 'arm_n': 6, 'elbow_n': 6, 'arm_f': -4, 'elbow_f': 6,
              'leg_n': 4, 'knee_n': -2, 'leg_f': -4, 'knee_f': -2},
    'stand_proud': {'lean': -4, 'head': -6, 'arm_n': -20, 'elbow_n': 40, 'arm_f': -24, 'elbow_f': 40,
                    'leg_n': 8, 'knee_n': 0, 'leg_f': -8, 'knee_f': 0},
    'hands_behind': {'lean': -2, 'head': 0, 'arm_n': -25, 'elbow_n': 30, 'arm_f': -28, 'elbow_f': 30,
                     'leg_n': 5, 'knee_n': 0, 'leg_f': -5, 'knee_f': 0},
    'point': {'lean': 4, 'head': -4, 'arm_n': 88, 'elbow_n': 4, 'arm_f': -6, 'elbow_f': 10,
              'leg_n': 10, 'knee_n': -2, 'leg_f': -8, 'knee_f': -2},
    'point_up': {'lean': -4, 'head': -14, 'arm_n': 150, 'elbow_n': 4, 'arm_f': -6, 'elbow_f': 10,
                 'leg_n': 6, 'knee_n': 0, 'leg_f': -6, 'knee_f': 0},
    'raise_fist': {'lean': -2, 'head': -10, 'arm_n': 165, 'elbow_n': 10, 'arm_f': -10, 'elbow_f': 20,
                   'leg_n': 10, 'knee_n': 0, 'leg_f': -10, 'knee_f': 0},
    'cheer': {'lean': -4, 'head': -12, 'arm_n': 160, 'elbow_n': 10, 'arm_f': 150, 'elbow_f': 10,
              'leg_n': 10, 'knee_n': 0, 'leg_f': -10, 'knee_f': 0},
    'wave': {'lean': 0, 'head': -4, 'arm_n': 130, 'elbow_n': 40, 'arm_f': -4, 'elbow_f': 6,
             'leg_n': 4, 'knee_n': 0, 'leg_f': -4, 'knee_f': 0},
    'think': {'lean': 3, 'head': 6, 'arm_n': 40, 'elbow_n': 125, 'arm_f': 30, 'elbow_f': 80,
              'leg_n': 4, 'knee_n': 0, 'leg_f': -4, 'knee_f': 0},
    'shrug': {'lean': 0, 'head': 6, 'arm_n': 40, 'elbow_n': 70, 'arm_f': 35, 'elbow_f': 70,
              'leg_n': 4, 'knee_n': 0, 'leg_f': -4, 'knee_f': 0},
    'hold_out': {'lean': 4, 'head': 4, 'arm_n': 70, 'elbow_n': 25, 'arm_f': 60, 'elbow_f': 30,
                 'leg_n': 6, 'knee_n': 0, 'leg_f': -6, 'knee_f': 0},
    'read': {'lean': 4, 'head': 18, 'arm_n': 45, 'elbow_n': 55, 'arm_f': 40, 'elbow_f': 55,
             'leg_n': 4, 'knee_n': 0, 'leg_f': -4, 'knee_f': 0},
    'present': {'lean': 2, 'head': -2, 'arm_n': 70, 'elbow_n': -5, 'arm_f': 50, 'elbow_f': 5,
                'leg_n': 6, 'knee_n': 0, 'leg_f': -6, 'knee_f': 0},
    'salute': {'lean': -2, 'head': -2, 'arm_n': 100, 'elbow_n': 120, 'arm_f': -2, 'elbow_f': 4,
               'leg_n': 2, 'knee_n': 0, 'leg_f': -2, 'knee_f': 0},
    'bow': {'lean': 55, 'head': 10, 'arm_n': -10, 'elbow_n': 10, 'arm_f': -14, 'elbow_f': 10,
            'leg_n': -6, 'knee_n': -4, 'leg_f': -10, 'knee_f': -4},
    'kneel': {'lean': 6, 'head': 10, 'arm_n': 20, 'elbow_n': 30, 'arm_f': 10, 'elbow_f': 20,
              'leg_n': 90, 'knee_n': -90, 'leg_f': 0, 'knee_f': -95},
    'sit': {'lean': -4, 'head': 0, 'arm_n': 30, 'elbow_n': 40, 'arm_f': 25, 'elbow_f': 40,
            'leg_n': 85, 'knee_n': -85, 'leg_f': 80, 'knee_f': -80, 'hip_h': 92},
    'sit_ground': {'lean': -6, 'head': 0, 'arm_n': 40, 'elbow_n': 30, 'arm_f': -30, 'elbow_f': 10,
                   'leg_n': 80, 'knee_n': -120, 'leg_f': 90, 'knee_f': -10, 'hip_h': 4},
    'throne': {'lean': -6, 'head': -4, 'arm_n': 55, 'elbow_n': 30, 'arm_f': 50, 'elbow_f': 35,
               'leg_n': 88, 'knee_n': -88, 'leg_f': 82, 'knee_f': -82, 'hip_h': 104},
    'crouch': {'lean': 30, 'head': -20, 'arm_n': 40, 'elbow_n': 30, 'arm_f': 20, 'elbow_f': 40,
               'leg_n': 70, 'knee_n': -110, 'leg_f': 30, 'knee_f': -100},
    'cower': {'lean': 25, 'head': 20, 'arm_n': 120, 'elbow_n': 110, 'arm_f': 110, 'elbow_f': 120,
              'leg_n': 40, 'knee_n': -70, 'leg_f': 20, 'knee_f': -60},
    'surprised': {'lean': -10, 'head': -10, 'arm_n': 60, 'elbow_n': 90, 'arm_f': 50, 'elbow_f': 90,
                  'leg_n': 8, 'knee_n': 0, 'leg_f': -14, 'knee_f': 0},
    'charge': {'lean': 22, 'head': -16, 'arm_n': 120, 'elbow_n': 20, 'arm_f': -40, 'elbow_f': 30,
               'leg_n': 40, 'knee_n': -20, 'leg_f': -35, 'knee_f': -40},
    'strike': {'lean': 18, 'head': -6, 'arm_n': 70, 'elbow_n': 10, 'arm_f': -30, 'elbow_f': 20,
               'leg_n': 35, 'knee_n': -20, 'leg_f': -25, 'knee_f': -10},
    'guard': {'lean': 8, 'head': -6, 'arm_n': 50, 'elbow_n': 70, 'arm_f': 60, 'elbow_f': 50,
              'leg_n': 25, 'knee_n': -20, 'leg_f': -20, 'knee_f': -15},
    'aim': {'lean': 6, 'head': 6, 'arm_n': 85, 'elbow_n': 5, 'arm_f': 70, 'elbow_f': 60,
            'leg_n': 20, 'knee_n': -6, 'leg_f': -16, 'knee_f': -4},
    'carry': {'lean': 8, 'head': 0, 'arm_n': 60, 'elbow_n': 60, 'arm_f': 55, 'elbow_f': 60,
              'leg_n': 6, 'knee_n': -4, 'leg_f': -6, 'knee_f': -4},
    'pray': {'lean': 4, 'head': 18, 'arm_n': 50, 'elbow_n': 100, 'arm_f': 48, 'elbow_f': 100,
             'leg_n': 4, 'knee_n': 0, 'leg_f': -4, 'knee_f': 0},
    'fall': {'lean': -60, 'head': -20, 'arm_n': 150, 'elbow_n': 20, 'arm_f': 120, 'elbow_f': 30,
             'leg_n': 50, 'knee_n': -30, 'leg_f': 20, 'knee_f': -40},
    'lie': {'lean': -90, 'head': 0, 'arm_n': 10, 'elbow_n': 0, 'arm_f': 5, 'elbow_f': 0,
            'leg_n': 90, 'knee_n': 0, 'leg_f': 88, 'knee_f': 0, 'hip_h': 10},
    'ride': {'lean': 4, 'head': 0, 'arm_n': 60, 'elbow_n': 40, 'arm_f': 55, 'elbow_f': 40,
             'leg_n': 60, 'knee_n': -70, 'leg_f': 55, 'knee_f': -70, 'hip_h': 0},
    'talk': {'lean': 2, 'head': -2, 'arm_n': 45, 'elbow_n': 60, 'arm_f': 10, 'elbow_f': 20,
             'leg_n': 5, 'knee_n': 0, 'leg_f': -5, 'knee_f': 0},
    'despair': {'lean': 30, 'head': 30, 'arm_n': 90, 'elbow_n': 130, 'arm_f': 80, 'elbow_f': 130,
                'leg_n': 4, 'knee_n': -6, 'leg_f': -4, 'knee_f': -6},
}

EXPRESSIONS = {
    #             brow tilt, brow raise, mouth curve, mouth open, eye scale
    'neutral': (0, 0, 0.0, 0.0, 1.0),
    'happy': (0, 0.05, 0.6, 0.0, 1.0),
    'joy': (0, 0.1, 0.7, 0.5, 1.0),
    'angry': (0.55, -0.05, -0.4, 0.0, 1.0),
    'shout': (0.5, 0, -0.1, 0.9, 1.0),
    'sad': (-0.5, 0.02, -0.5, 0.0, 0.9),
    'surprised': (0, 0.25, 0, 0.7, 1.35),
    'afraid': (-0.45, 0.2, -0.3, 0.45, 1.25),
    'determined': (0.35, -0.04, -0.1, 0.0, 0.95),
    'smug': (0.15, 0.05, 0.35, 0.0, 0.8),
    'worried': (-0.4, 0.12, -0.2, 0.0, 1.05),
    'sleep': (0, 0, 0, 0, 0.0),
}


def resolve_pose(pose):
    """A pose name, a dict, or {"base": name, ...overrides}."""
    if isinstance(pose, str):
        if pose not in POSES:
            raise ValueError(f'Unknown pose "{pose}". Known: {", ".join(sorted(POSES))}, or give angles.')
        return dict(POSES[pose])
    out = dict(POSES['stand'])
    base = pose.get('base')
    if base:
        out.update(resolve_pose(base))
    out.update({k: v for k, v in pose.items() if k != 'base'})
    return out


def _d(deg, k=1.0):
    """Unit vector of a limb at angle deg (0 = down, 90 = forward). k scales the forward (x) part."""
    a = math.radians(deg)
    return (math.sin(a) * k, math.cos(a))


def walk_overlay(pose, phase, amount=1.0, run=False):
    """Add a walk (or run) cycle on top of a pose. phase in radians."""
    s, c = math.sin(phase), math.cos(phase)
    amp = 34 if run else 24
    p = dict(pose)
    p['leg_n'] = p.get('leg_n', 0) * (1 - amount) + amp * s * amount
    p['leg_f'] = p.get('leg_f', 0) * (1 - amount) - amp * s * amount
    kb = 70 if run else 38
    p['knee_n'] = p.get('knee_n', 0) * (1 - amount) - kb * max(0.0, -c) * amount - 4
    p['knee_f'] = p.get('knee_f', 0) * (1 - amount) - kb * max(0.0, c) * amount - 4
    aamp = 40 if run else 20
    if not pose.get('_hold_n'):
        p['arm_n'] = p.get('arm_n', 0) * (1 - amount) - aamp * s * amount
        p['elbow_n'] = p.get('elbow_n', 0) * (1 - amount) + (60 if run else 18) * amount
    if not pose.get('_hold_f'):
        p['arm_f'] = p.get('arm_f', 0) * (1 - amount) + aamp * s * amount
        p['elbow_f'] = p.get('elbow_f', 0) * (1 - amount) + (60 if run else 18) * amount
    p['lean'] = p.get('lean', 0) + (14 if run else 3) * amount
    p['lift'] = p.get('lift', 0) + (abs(c) * (10 if run else 3)) * amount
    return p


class Skeleton:
    def __init__(self, pose, yaw=1.0, build='average'):
        self.p = pose
        ay = min(1.0, abs(yaw))
        self.fr = 1 - ay           # how frontal
        k = ay                      # forward foreshortening
        lean = pose.get('lean', 0)
        tw = BUILD.get(build, 17)
        self.tw = tw
        hip = (0.0, 0.0)
        up = (math.sin(math.radians(lean)) * k, -math.cos(math.radians(lean)))
        perp = (-up[1], up[0])  # points "right" of the spine in screen terms when upright
        self.up, self.perp = up, perp
        neck = (hip[0] + up[0] * TORSO, hip[1] + up[1] * TORSO)
        sb = (hip[0] + up[0] * (TORSO - SHOULDER_DROP), hip[1] + up[1] * (TORSO - SHOULDER_DROP))
        hl = math.radians(lean + pose.get('head', 0))
        hup = (math.sin(hl) * k, -math.cos(hl))
        head = (neck[0] + hup[0] * (NECK + HEAD_R), neck[1] + hup[1] * (NECK + HEAD_R))
        sw = tw * 0.9 * self.fr + 2
        hw = tw * 0.5 * self.fr + 1
        side = {'n': 1, 'f': -1}
        J = {'hip': hip, 'neck': neck, 'sb': sb, 'head': head}
        for s in ('n', 'f'):
            sd = side[s]
            sh = (sb[0] + perp[0] * sw * sd, sb[1] + perp[1] * sw * sd)
            kx = k + sd * self.fr
            a1 = lean * k + pose.get('arm_' + s, 0)
            a2 = a1 + pose.get('elbow_' + s, 0)
            v1, v2 = _d(a1, kx), _d(a2, kx)
            el = (sh[0] + v1[0] * UPPER_ARM, sh[1] + v1[1] * UPPER_ARM)
            ha = (el[0] + v2[0] * FOREARM, el[1] + v2[1] * FOREARM)
            hp = (hip[0] + hw * sd, hip[1])
            l1 = pose.get('leg_' + s, 0)
            l2 = l1 + pose.get('knee_' + s, 0)
            u1, u2 = _d(l1, kx), _d(l2, kx)
            kn = (hp[0] + u1[0] * THIGH, hp[1] + u1[1] * THIGH)
            an = (kn[0] + u2[0] * SHIN, kn[1] + u2[1] * SHIN)
            ft = (an[0] + FOOT * (k + 0.5 * sd * self.fr), an[1])
            J.update({'sh_' + s: sh, 'el_' + s: el, 'hand_' + s: ha, 'hp_' + s: hp, 'kn_' + s: kn, 'an_' + s: an,
                      'ft_' + s: ft, 'fa_' + s: math.degrees(math.atan2(v2[1], v2[0]))})
        # ground: lowest ankle on y=0, or hips at hip_h for sitting
        if 'hip_h' in pose:
            dy = -pose['hip_h']
        else:
            dy = -max(J['an_n'][1], J['an_f'][1])
        dy -= pose.get('lift', 0)
        self.j = {k2: (v[0], v[1] + dy) if isinstance(v, tuple) else v for k2, v in J.items()}

    def __getitem__(self, k):
        return self.j[k]


# ---------------------------------------------------------------- drawing
class Ctx:
    def __init__(self, S, t, ink, lw, outline, boil_seed):
        self.S, self.t, self.ink, self.lw, self.ol, self.boil_seed = S, t, ink, lw, outline, boil_seed

    def wob(self, p, i):
        """Boiling-line wobble for the sketch styles (changes a few times a second)."""
        b = self.S.line['boil']
        if not b:
            return p
        f = math.floor(self.t * 8)
        return (p[0] + noise1(i * 3.1 + f * 7.7, self.boil_seed) * b, p[1] + noise1(i * 5.3 + f * 3.3, self.boil_seed + 1) * b)


def limb(c, a, b, d, color, width, idx=0):
    pts_ = [c.wob(a, idx), c.wob(b, idx + 1), c.wob(d, idx + 2)]
    out = ''
    if c.ol or color != c.ink:
        out += polyline(pts_, fill='none', stroke=c.ink, stroke_width=width + max(c.ol, 2.2) * 2,
                        stroke_linecap='round', stroke_linejoin='round')
    out += polyline(pts_, fill='none', stroke=color, stroke_width=width, stroke_linecap='round', stroke_linejoin='round')
    return out


def draw_character(S, spec, pose, t, yaw=1.0, expr='neutral', talk=0.0, blink_seed=0, look=None):
    """SVG for one character in its local frame (feet at origin, facing right). Returns (svg, skeleton)."""
    build = spec.get('build', 'average')
    yaw_abs = abs(yaw)
    sk = Skeleton(pose, yaw_abs, build)
    lw = S.line['limb'] * spec.get('line', 1.0)
    ink = S.ink
    c = Ctx(S, t, ink, lw, S.line['outline'], blink_seed)
    skin = S.c(spec.get('skin', 'skin2'), 0.1)
    head_fill = S.c(spec.get('head_color'), 0.1) if spec.get('head_color') else skin
    sleeves = S.c(spec['sleeves']) if spec.get('sleeves') else ink
    legwear = S.c(spec['legwear']) if spec.get('legwear') else ink
    shoes = S.c(spec['shoes']) if spec.get('shoes') else ink
    outfit = spec.get('outfit', [])
    hold = dict(spec.get('hold', {}))
    if isinstance(pose.get('_hold'), dict):
        hold.update(pose['_hold'])
    J = sk.j
    out = []

    # 1. capes behind everything
    for g in outfit:
        if g.get('kind') == 'cape':
            out.append(_cape(c, sk, g, t))

    # 2. far arm and its prop
    far_col = shade(sleeves, -0.18) if sleeves != ink else ink
    if hold.get('far'):
        out.append(P.draw(S, hold['far'], J['hand_f'], J['fa_f'], t, ink, lw))
    out.append(limb(c, J['sh_f'], J['el_f'], J['hand_f'], far_col, lw, 10))
    out.append(_hand(c, J['hand_f'], skin, lw, spec))

    # 3. legs
    for s in ('f', 'n'):
        col = shade(legwear, -0.18) if (s == 'f' and legwear != ink) else legwear
        out.append(limb(c, J['hp_' + s], J['kn_' + s], J['an_' + s], col, lw * spec.get('leg_width', 1.0), 20 + (s == 'n') * 5))
        out.append(line(J['an_' + s], J['ft_' + s], stroke=shoes, stroke_width=lw * 1.05, stroke_linecap='round'))

    # 4. torso (the stick) unless a garment covers it
    covered = any(g.get('kind') in TORSO_GARMENTS for g in outfit)
    if not covered:
        out.append(limb(c, J['hip'], ((J['hip'][0] + J['neck'][0]) / 2, (J['hip'][1] + J['neck'][1]) / 2), J['neck'],
                        S.c(spec['body']) if spec.get('body') else ink, lw * spec.get('torso_width', 1.0), 30))

    # 5. garments
    for g in outfit:
        k = g.get('kind')
        if k == 'cape':
            continue
        out.append(_garment(c, sk, g, t))

    # 6. neck, head, hair, face, headwear
    hb = (J['head'][0] - sk.up[0] * HEAD_R * 0.8, J['head'][1] - sk.up[1] * HEAD_R * 0.8)
    out.append(line(J['neck'], hb, stroke=ink, stroke_width=lw * 1.5 + 3, stroke_linecap='round'))
    out.append(line(J['neck'], hb, stroke=skin, stroke_width=lw * 1.5, stroke_linecap='round'))
    out.append(_head(c, sk, spec, head_fill, yaw_abs, expr, talk, blink_seed, look))

    # 7. near arm and its prop
    out.append(limb(c, J['sh_n'], J['el_n'], J['hand_n'], sleeves, lw, 40))
    out.append(_hand(c, J['hand_n'], skin, lw, spec))
    if hold.get('near'):
        out.append(P.draw(S, hold['near'], J['hand_n'], J['fa_n'], t, ink, lw))
    return ''.join(out), sk


def _hand(c, p, skin, lw, spec):
    col = c.S.c(spec['gloves']) if spec.get('gloves') else (skin if spec.get('skin_hands', True) else c.ink)
    return circle(p, lw * 0.85, fill=col, stroke=c.ink, stroke_width=max(1.6, lw * 0.3))


TORSO_GARMENTS = {'robe', 'tunic', 'coat', 'dress', 'shirt', 'vest', 'jacket', 'armor', 'mail', 'kaftan', 'toga', 'uniform'}
GARMENT_DEFAULTS = {
    #          length (of the leg), flare, torso cover
    'robe': (0.95, 1.7), 'kaftan': (0.9, 1.6), 'dress': (1.0, 2.1), 'toga': (0.8, 1.6), 'tunic': (0.45, 1.25),
    'coat': (0.7, 1.4), 'uniform': (0.35, 1.05), 'shirt': (0.12, 1.0), 'vest': (0.1, 1.0), 'jacket': (0.25, 1.05),
    'armor': (0.12, 1.0), 'mail': (0.4, 1.2), 'skirt': (0.42, 1.5), 'apron': (0.6, 1.1),
}


def _body_rows(sk, length, flare, width=1.0):
    """Left/right outline points of a garment: shoulders, chest, waist, hem."""
    J = sk.j
    tw = sk.tw * width * 1.15
    up, perp = sk.up, sk.perp
    sb = J['sb']
    hip = J['hip']
    neck = J['neck']
    shw = tw * 0.95
    rows = []
    top = (neck[0] - up[0] * 4, neck[1] - up[1] * 4)
    rows.append([(top[0] - perp[0] * tw * 0.45, top[1] - perp[1] * tw * 0.45), (top[0] + perp[0] * tw * 0.45, top[1] + perp[1] * tw * 0.45)])
    rows.append([(sb[0] - perp[0] * shw, sb[1] - perp[1] * shw), (sb[0] + perp[0] * shw, sb[1] + perp[1] * shw)])
    ww = tw * 0.8
    rows.append([(hip[0] - perp[0] * ww, hip[1] - perp[1] * ww), (hip[0] + perp[0] * ww, hip[1] + perp[1] * ww)])
    if length > 0.05:
        L = (THIGH + SHIN) * length
        # the hem hangs from the hips, centred between the legs at that height
        u = min(1.0, length)
        kn = [(J['kn_n'], J['an_n']), (J['kn_f'], J['an_f'])]
        def leg_at(s):
            hp, k2, a2 = J['hp_' + s], J['kn_' + s], J['an_' + s]
            if u <= 0.5:
                w = u / 0.5
                return (hp[0] + (k2[0] - hp[0]) * w, hp[1] + (k2[1] - hp[1]) * w)
            w = (u - 0.5) / 0.5
            return (k2[0] + (a2[0] - k2[0]) * w, k2[1] + (a2[1] - k2[1]) * w)
        pn, pf = leg_at('n'), leg_at('f')
        cx = (pn[0] + pf[0]) / 2
        cy = max(hip[1] + L * 0.85, min(pn[1], pf[1]))
        cy = min(cy, 52 if sk.p.get('_mounted') else -3)
        spread = abs(pn[0] - pf[0]) / 2
        hw = max(tw * flare * 0.85, spread + lw_pad(sk))
        rows.append([(cx - hw, cy), (cx + hw, cy)])
    return rows


def lw_pad(sk):
    return 6


def _garment_path(rows):
    return _poly_smooth([r[0] for r in rows], [r[1] for r in rows][::-1])


def _poly_smooth(left, right):
    """Down the left side (smooth), straight across the hem, up the right side (smooth), round over the shoulders."""
    def seg(points):
        p = [points[0]] + points + [points[-1]]
        out = ''
        for i in range(1, len(p) - 2):
            p0, p1, p2, p3 = p[i - 1], p[i], p[i + 1], p[i + 2]
            c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
            c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
            out += f' C{n(c1[0])} {n(c1[1])} {n(c2[0])} {n(c2[1])} {n(p2[0])} {n(p2[1])}'
        return out
    d = f'M{n(left[0][0])} {n(left[0][1])}' + seg(left)
    d += f' L{n(right[0][0])} {n(right[0][1])}' + seg(right)
    return d + ' Z'


def _strip(rows, u0, u1):
    left = [(r[0][0] + (r[1][0] - r[0][0]) * u0, r[0][1] + (r[1][1] - r[0][1]) * u0) for r in rows]
    right = [(r[0][0] + (r[1][0] - r[0][0]) * u1, r[0][1] + (r[1][1] - r[0][1]) * u1) for r in rows]
    return left + right[::-1]


def _band(rows, i, v0, v1):
    """A horizontal band between row i and i+1, from v0 to v1 (0..1)."""
    a, b = rows[i], rows[i + 1]
    def at(v, side):
        return (a[side][0] + (b[side][0] - a[side][0]) * v, a[side][1] + (b[side][1] - a[side][1]) * v)
    return [at(v0, 0), at(v0, 1), at(v1, 1), at(v1, 0)]


def _garment(c, sk, g, t):
    S, ink = c.S, c.ink
    kind = g.get('kind')
    col = S.c(g.get('color', 'linen'))
    J = sk.j
    ow = max(1.6, c.lw * 0.32)
    if kind == 'svg':
        hip = J['hip']
        return group(g.get('svg', ''), transform=f'translate({n(hip[0])} {n(hip[1])}) rotate({n(math.degrees(math.atan2(sk.up[0], -sk.up[1])))})')
    if kind in ('sash', 'belt'):
        rows = _body_rows(sk, 0, 1)
        if g.get('diagonal'):
            a, b = rows[1][1], rows[2][0]
            return line(a, b, stroke=col, stroke_width=g.get('width', 8), stroke_linecap='round')
        quad = _band(rows, 1, 0.82, 1.0)
        out = polygon(quad, fill=col, stroke=ink, stroke_width=ow)
        if g.get('tails'):
            hp = J['hip']
            out += path(f'M{n(hp[0] - 4)} {n(hp[1])} q -10 30 -4 48', fill='none', stroke=col, stroke_width=7, stroke_linecap='round')
        return out
    if kind == 'collar':
        nk = J['neck']
        r = g.get('size', 14)
        return ellipse((nk[0], nk[1] + 4), r * 1.3, r * 0.55, fill=col, stroke=ink, stroke_width=ow)
    if kind == 'epaulettes':
        out = ''
        for s in ('n', 'f'):
            out += ellipse(J['sh_' + s], 10, 5, fill=col, stroke=ink, stroke_width=ow)
        return out
    if kind == 'medal':
        sb = J['sb']
        return circle((sb[0] + sk.perp[0] * 6 + 4, sb[1] + 14), 4.5, fill=col, stroke=ink, stroke_width=1.2)
    if kind == 'trousers':
        return ''  # handled by `legwear`
    length, flare = GARMENT_DEFAULTS.get(kind, (0.4, 1.2))
    length = g.get('length', length)
    flare = g.get('flare', flare)
    width = g.get('width', 1.0)
    rows = _body_rows(sk, length, flare, width)
    if kind == 'skirt' or kind == 'apron':
        rows = rows[2:]
        if len(rows) < 2:
            return ''
    out = ''
    out += path(_garment_path(rows), fill=col, stroke=ink, stroke_width=ow, stroke_linejoin='round')
    pat = g.get('pattern')
    pc = S.c(g.get('pattern_color', 'gold'))
    if pat == 'stripes':
        k = g.get('count', 5)
        for i in range(k):
            if i % 2:
                out += polygon(_strip(rows, i / k, (i + 1) / k), fill=pc, fill_opacity=0.9)
    elif pat == 'center':
        out += polygon(_strip(rows, 0.42, 0.58), fill=pc)
    elif pat == 'scales' or kind in ('mail',):
        for ri in range(len(rows) - 1):
            for v in (0.33, 0.66):
                q = _band(rows, ri, v, v + 0.01)
                out += line(q[0], q[1], stroke=shade(col, -0.35), stroke_width=1.6)
    elif pat == 'dots':
        for ri in range(len(rows) - 1):
            for v in (0.3, 0.7):
                q = _band(rows, ri, v, v)
                for u in (0.25, 0.5, 0.75):
                    x = q[0][0] + (q[1][0] - q[0][0]) * u
                    y = q[0][1] + (q[1][1] - q[0][1]) * u
                    out += circle((x, y), 2.4, fill=pc)
    if kind == 'armor':
        sb = J['sb']
        out += path(f'M{n(sb[0] - 6)} {n(sb[1] + 6)} q 8 10 14 2', fill='none', stroke=shade(col, 0.45), stroke_width=3, stroke_linecap='round')
    if kind == 'toga':
        a, b = rows[1][1], rows[-1][0]
        out += line(a, b, stroke=shade(col, -0.2), stroke_width=4)
    if g.get('open') or kind == 'coat':
        top = ((rows[0][0][0] + rows[0][1][0]) / 2, (rows[0][0][1] + rows[0][1][1]) / 2)
        bot = ((rows[-1][0][0] + rows[-1][1][0]) / 2 + 4, rows[-1][0][1])
        out += line(top, bot, stroke=shade(col, -0.35), stroke_width=2)
        if g.get('buttons'):
            for i in range(1, 5):
                u = i / 6
                out += circle((top[0] + (bot[0] - top[0]) * u + 3, top[1] + (bot[1] - top[1]) * u), 2.2, fill=S.c(g['buttons']))
    trim = g.get('trim')
    if trim:
        tc = S.c(trim)
        last = rows[-1]
        out += line(last[0], last[1], stroke=tc, stroke_width=4.5, stroke_linecap='round')
        out += line(rows[0][0], rows[0][1], stroke=tc, stroke_width=3.5, stroke_linecap='round')
    return out


def _cape(c, sk, g, t):
    S = c.S
    J = sk.j
    col = S.c(g.get('color', 'red'))
    sb = J['sb']
    L = g.get('length', 0.85) * (TORSO + THIGH + SHIN) * 0.75
    sway = noise1(t * 1.3, 11) * 10 + g.get('wind', 0) * 30
    top_b = (sb[0] - sk.perp[0] * sk.tw - 4, sb[1] - 6)
    top_f = (sb[0] + sk.perp[0] * sk.tw * 0.4, sb[1] - 8)
    bot_b = (top_b[0] - 22 - sway, sb[1] + L)
    bot_f = (top_f[0] - 2 - sway * 0.4, sb[1] + L - 4)
    d = smooth_path([top_f, top_b, (top_b[0] - 14 - sway * 0.5, sb[1] + L * 0.5), bot_b,
                     ((bot_b[0] + bot_f[0]) / 2, sb[1] + L + 6), bot_f], closed=True)
    return path(d, fill=shade(col, -0.1), stroke=c.ink, stroke_width=max(1.6, c.lw * 0.32))


# ---------------------------------------------------------------- head
def _head(c, sk, spec, fill, yaw, expr, talk, blink_seed, look):
    S, ink = c.S, c.ink
    J = sk.j
    hc = J['head']
    r = HEAD_R * spec.get('head_size', 1.0)
    tilt = sk.p.get('lean', 0) * yaw + sk.p.get('head', 0)
    u = 1 / r
    sc = f'translate({n(hc[0])} {n(hc[1])}) rotate({n(tilt)}) scale({n(r)})'
    ow = max(1.8, c.lw * 0.32) * u
    parts_back, parts_front = [], []
    hair = spec.get('hair', {'style': 'short', 'color': 'black'})
    if isinstance(hair, str):
        hair = {'style': hair}
    hcol = S.c(hair.get('color', 'black'))
    hb, hf = HAIR.get(hair.get('style', 'short'), HAIR['short'])(yaw)
    if hb:
        parts_back.append(path(hb, fill=hcol, stroke=ink, stroke_width=ow, stroke_linejoin='round'))
    if hf:
        parts_front.append(path(hf, fill=hcol, stroke=ink, stroke_width=ow, stroke_linejoin='round'))
    out = ''.join(parts_back)
    out += circle((0, 0), 1, fill=fill, stroke=ink, stroke_width=ow * 1.15)
    out += ''.join(parts_front)
    # face
    if S.face != 'none':
        out += _face(c, expr, yaw, talk, blink_seed, ow, look)
    beard = spec.get('beard')
    if beard:
        if isinstance(beard, str):
            beard = {'style': beard}
        bcol = S.c(beard.get('color', hair.get('color', 'black')))
        bd = BEARDS.get(beard.get('style', 'short'))
        if bd:
            out += path(bd(yaw), fill=bcol, stroke=ink, stroke_width=ow, stroke_linejoin='round')
    if spec.get('mustache'):
        mc = S.c(spec.get('mustache_color', hair.get('color', 'black'))) if spec['mustache'] is True else S.c(spec['mustache'])
        mx = 0.55 * yaw
        out += path(f'M{n(mx - 0.32)} 0.42 Q{n(mx)} 0.22 {n(mx + 0.32)} 0.42 Q{n(mx)} 0.34 {n(mx - 0.32)} 0.42 Z', fill=mc,
                    stroke=ink, stroke_width=ow * 0.7)
    for hw in spec.get('head', []):
        out += headwear(S, hw, ink, ow, yaw, c.t)
    return group(out, transform=sc)


def _face(c, expr, yaw, talk, seed, ow, look):
    S, ink = c.S, c.ink
    bt, br, mc, mo, es = EXPRESSIONS.get(expr, EXPRESSIONS['neutral'])
    # blink: a short close every few seconds
    ph = (c.t + (seed % 97) * 0.37) % 3.7
    blink = ph < 0.12
    cx = 0.42 * yaw
    sep = 0.3 * (1 - 0.45 * yaw)
    ex = [cx - sep, cx + sep]
    if yaw > 0.85:
        ex = [cx + 0.05, cx + 0.42]
    ey = -0.08
    lx, ly = (look or (0, 0))
    out = ''
    rr = 0.1 * es
    for i, x in enumerate(ex):
        xx = x + lx * 0.06
        if blink or es == 0:
            out += line((xx - 0.1, ey), (xx + 0.1, ey), stroke=ink, stroke_width=ow * 1.4, stroke_linecap='round')
        else:
            out += ellipse((xx, ey + ly * 0.05), rr, rr * 1.25, fill=ink)
    if S.face == 'expressive':
        for i, x in enumerate(ex):
            sgn = -1 if i == 0 else 1
            y0 = ey - 0.26 - br
            dy = bt * 0.12 * (1 if sgn > 0 else -1) * (1 if yaw < 0.85 else (1 if i == 0 else -1))
            out += line((x - 0.14, y0 - dy), (x + 0.14, y0 + dy), stroke=ink, stroke_width=ow * 1.5, stroke_linecap='round')
        mx = 0.36 * yaw + (0.22 if yaw > 0.85 else 0)
        my = 0.45
        open_ = max(mo, talk)
        w = 0.24
        if open_ > 0.08:
            out += ellipse((mx, my), w * 0.75, 0.05 + open_ * 0.16, fill=shade(ink, 0.15), stroke=ink, stroke_width=ow)
        else:
            out += path(f'M{n(mx - w)} {n(my)} Q{n(mx)} {n(my + mc * 0.22)} {n(mx + w)} {n(my)}', fill='none', stroke=ink,
                        stroke_width=ow * 1.4, stroke_linecap='round')
    elif talk > 0.1:
        mx = 0.4 * yaw + (0.2 if yaw > 0.85 else 0)
        out += ellipse((mx, 0.45), 0.13, 0.04 + talk * 0.12, fill=ink)
    return out


def _hair_short(y):
    return ('M-1.05 0.1 C -1.15 -0.9 -0.3 -1.2 0.35 -1.08 C 0.8 -1.0 1.05 -0.65 1.02 -0.35 C 0.6 -0.62 0 -0.7 -0.35 -0.45 '
            'C -0.6 -0.2 -0.75 0.15 -1.05 0.1 Z', None)


def _hair_long(y):
    return ('M-0.9 -0.7 C -0.4 -1.25 0.6 -1.2 1.0 -0.5 C 0.6 -0.65 0.1 -0.7 -0.25 -0.45 C -0.5 0.2 -0.55 1.1 -0.9 1.7 '
            'C -1.3 1.2 -1.35 0.1 -0.9 -0.7 Z', None)


def _hair_bun(y):
    return ('M-1.0 0.0 C -1.1 -0.9 -0.2 -1.2 0.4 -1.05 C 0.85 -0.95 1.05 -0.6 1.0 -0.35 C 0.5 -0.62 -0.1 -0.68 -0.4 -0.4 '
            'C -0.7 -0.1 -0.8 0.1 -1.0 0.0 Z M-1.05 -0.85 a0.38 0.38 0 1 0 0.01 0 Z', None)


def _hair_curly(y):
    d = 'M-1.0 0.2 '
    for i in range(8):
        a0 = math.pi * (1.05 + i * 0.12)
        a1 = math.pi * (1.05 + (i + 1) * 0.12)
        x1, y1 = math.cos(a1) * 1.1, math.sin(a1) * 1.1
        d += f'A0.22 0.22 0 0 1 {n(x1)} {n(y1)} '
    d += 'C 0.6 -0.6 0 -0.7 -0.4 -0.4 C -0.6 -0.2 -0.75 0.15 -1.0 0.2 Z'
    return (d, None)


def _hair_topknot(y):
    s, _ = _hair_short(y)
    return (s + ' M-0.25 -1.05 L-0.05 -1.45 L0.25 -1.42 L0.15 -1.05 Z', None)


def _hair_ponytail(y):
    s, _ = _hair_short(y)
    return (s + ' M-0.95 -0.35 C -1.5 -0.2 -1.6 0.6 -1.35 1.1 C -1.2 0.6 -1.05 0.2 -0.8 -0.05 Z', None)


def _hair_queue(y):
    return ('M-1.0 -0.2 C -1.0 -0.7 -0.6 -0.95 -0.2 -1.0 C -0.5 -0.6 -0.7 -0.2 -0.85 0.2 Z '
            'M-0.95 0.0 C -1.25 0.6 -1.3 1.4 -1.2 2.2 L-1.05 2.2 C -1.05 1.4 -1.0 0.7 -0.8 0.2 Z', None)


def _hair_none(y):
    return (None, None)


def _hair_wavy(y):
    return ('M-1.05 0.35 C -1.25 -0.9 -0.3 -1.25 0.4 -1.1 C 0.9 -1.0 1.1 -0.65 1.02 -0.3 C 0.7 -0.5 0.4 -0.55 0.2 -0.52 '
            'C 0 -0.65 -0.3 -0.6 -0.45 -0.4 C -0.55 -0.05 -0.7 0.45 -1.05 0.35 Z', None)


HAIR = {'short': _hair_short, 'long': _hair_long, 'bun': _hair_bun, 'curly': _hair_curly, 'topknot': _hair_topknot,
        'ponytail': _hair_ponytail, 'queue': _hair_queue, 'bald': _hair_none, 'none': _hair_none, 'wavy': _hair_wavy}


def _beard_short(y):
    return 'M-0.05 0.55 C 0.1 0.95 0.75 0.95 0.95 0.4 C 0.75 0.62 0.3 0.7 -0.05 0.55 Z'


def _beard_full(y):
    return 'M-0.55 0.2 C -0.5 1.05 0.6 1.25 0.98 0.35 C 0.85 0.45 0.65 0.55 0.5 0.55 C 0.2 0.62 -0.2 0.55 -0.55 0.2 Z'


def _beard_long(y):
    return 'M-0.55 0.2 C -0.55 1.3 0.1 2.0 0.35 2.1 C 0.6 1.6 1.0 1.0 0.98 0.35 C 0.6 0.6 -0.1 0.62 -0.55 0.2 Z'


def _beard_pointed(y):
    return 'M-0.3 0.4 C -0.1 0.9 0.4 1.5 0.62 1.55 C 0.7 1.1 0.95 0.75 0.98 0.35 C 0.6 0.6 0.1 0.62 -0.3 0.4 Z'


def _beard_goatee(y):
    return 'M0.4 0.62 C 0.42 0.95 0.6 1.1 0.72 1.12 C 0.78 0.9 0.82 0.75 0.8 0.6 C 0.66 0.66 0.52 0.66 0.4 0.62 Z'


def _beard_stubble(y):
    return 'M-0.05 0.55 C 0.1 0.85 0.7 0.85 0.92 0.42 C 0.7 0.6 0.3 0.66 -0.05 0.55 Z'


BEARDS = {'short': _beard_short, 'full': _beard_full, 'long': _beard_long, 'pointed': _beard_pointed,
          'goatee': _beard_goatee, 'stubble': _beard_stubble}


# ---------------------------------------------------------------- headwear (head units: radius 1, centre 0,0)
def headwear(S, hw, ink, ow, yaw, t):
    shape = hw.get('shape')
    col = S.c(hw.get('color', 'linen'))
    acc = S.c(hw.get('accent', 'gold'))
    h = hw.get('h')
    w = hw.get('w')
    x0, y0 = hw.get('x', 0), hw.get('y', 0)
    st = dict(fill=col, stroke=ink, stroke_width=ow, stroke_linejoin='round')
    if shape == 'cap':
        hh = h or 1.12
        ww = w or 1.06
        d = f'M{n(-ww)} -0.15 C {n(-ww)} {n(-hh * 1.25)} {n(ww)} {n(-hh * 1.25)} {n(ww)} -0.15 Z'
        body = path(d, **st)
        if hw.get('band', True):
            body += path(f'M{n(-ww)} -0.15 L{n(ww)} -0.15', stroke=acc, stroke_width=0.14, fill='none')
    elif shape == 'dome':
        hh = h or 0.95
        ww = w or 1.15
        body = path(f'M{n(-ww * 0.92)} -0.25 C {n(-ww * 1.25)} {n(-0.3 - hh * 1.1)} {n(-ww * 0.4)} {n(-0.3 - hh * 1.32)} 0 {n(-0.3 - hh * 1.3)} '
                    f'C {n(ww * 0.4)} {n(-0.3 - hh * 1.32)} {n(ww * 1.25)} {n(-0.3 - hh * 1.1)} {n(ww * 0.92)} -0.25 '
                    f'Q 0 -0.05 {n(-ww * 0.92)} -0.25 Z', **st)
        for i in range(hw.get('wrap', 0)):
            yy = -0.4 - (i + 1) * hh / (hw.get('wrap', 0) + 1)
            body += path(f'M{n(-ww * 0.8)} {n(yy + 0.12)} Q 0 {n(yy - 0.18)} {n(ww * 0.8)} {n(yy - 0.05)}', fill='none',
                         stroke=shade(col, -0.25), stroke_width=0.07)
    elif shape == 'cone':
        hh = h or 1.3
        ww = w or 1.05
        curl = hw.get('curl', 0)
        tip = (curl, -0.35 - hh)
        if curl:
            d = f'M{n(-ww)} -0.3 Q {n(-ww * 0.3)} {n(-0.4 - hh * 0.8)} {n(tip[0])} {n(tip[1])} Q {n(ww * 0.5)} {n(-0.35 - hh * 0.5)} {n(ww)} -0.3 Z'
        else:
            d = f'M{n(-ww)} -0.3 L{n(tip[0])} {n(tip[1])} L{n(ww)} -0.3 Z'
        body = path(d, **st)
        if hw.get('band', True):
            body += path(f'M{n(-ww)} -0.3 L{n(ww)} -0.3', stroke=acc, stroke_width=0.16, fill='none')
    elif shape == 'cylinder':
        hh = h or 1.1
        ww = w or 0.95
        tp = hw.get('taper', 1.0)
        top_y = -0.45 - hh
        if hw.get('round_top'):
            d = (f'M{n(-ww)} -0.45 L{n(-ww * tp)} {n(top_y + 0.3)} Q 0 {n(top_y - 0.25)} {n(ww * tp)} {n(top_y + 0.3)} '
                 f'L{n(ww)} -0.45 Z')
        else:
            d = f'M{n(-ww)} -0.45 L{n(-ww * tp)} {n(top_y)} L{n(ww * tp)} {n(top_y)} L{n(ww)} -0.45 Z'
        body = path(d, **st)
        if hw.get('band', False):
            body += path(f'M{n(-ww)} -0.52 L{n(ww)} -0.52', stroke=acc, stroke_width=0.16, fill='none')
        if hw.get('tassel'):
            tx = ww * tp * 0.2
            sw = noise1(t * 2, 4) * 0.08
            body += path(f'M{n(tx)} {n(top_y)} Q {n(-ww * 0.6)} {n(top_y + 0.1)} {n(-ww * 0.9 + sw)} {n(top_y + 0.55)}', fill='none',
                         stroke=S.c(hw['tassel']), stroke_width=0.1, stroke_linecap='round')
    elif shape == 'brim':
        ww = w or 1.7
        th = h or 0.16
        body = ellipse((0, -0.5), ww, th, **st)
    elif shape == 'band':
        ww = w or 1.04
        th = h or 0.22
        body = path(f'M{n(-ww)} {n(-0.5 - th / 2)} L{n(ww)} {n(-0.5 - th / 2)} L{n(ww)} {n(-0.5 + th / 2)} L{n(-ww)} {n(-0.5 + th / 2)} Z', **st)
    elif shape == 'points':
        k = hw.get('count', 5)
        ww = w or 0.95
        hh = h or 0.5
        base = -0.62
        p_ = [(-ww, base)]
        for i in range(k):
            xa = -ww + (2 * ww) * (i + 0.5) / k
            xb = -ww + (2 * ww) * (i + 1) / k
            p_ += [(xa, base - hh), (xb, base - hh * 0.35)]
        p_[-1] = (ww, base - hh * 0.35)
        p_ += [(ww, base)]
        body = polygon(p_, **st)
        if hw.get('gems', True):
            body += circle((0, base - 0.12), 0.09, fill=S.c(hw.get('gem', 'red')))
    elif shape == 'crest':
        hh = h or 0.75
        body = path(f'M-0.95 -0.75 C -0.9 {n(-0.95 - hh * 1.3)} 0.9 {n(-0.95 - hh * 1.3)} 0.95 -0.75 '
                    f'C 0.6 {n(-0.95 - hh * 0.55)} -0.6 {n(-0.95 - hh * 0.55)} -0.95 -0.75 Z', **st)
    elif shape == 'plume':
        hh = h or 1.1
        ang = hw.get('angle', -20)
        sway = noise1(t * 2.2, 9) * 6
        body = group(path(f'M0 0 C -0.28 {n(-hh * 0.4)} -0.22 {n(-hh * 0.85)} 0.05 {n(-hh)} C 0.22 {n(-hh * 0.7)} 0.18 {n(-hh * 0.35)} 0 0 Z', **st),
                     transform=f'translate({n(hw.get("px", 0.1))} {n(hw.get("py", -1.05))}) rotate({n(ang + sway)})')
    elif shape == 'wrap':
        ww = w or 1.12
        body = ''
        for i in range(hw.get('count', 3)):
            yy = -0.35 - i * 0.22
            body += path(f'M{n(-ww)} {n(yy + 0.08)} Q 0 {n(yy - 0.2)} {n(ww)} {n(yy)}', fill='none', stroke=col, stroke_width=0.2,
                         stroke_linecap='round')
    elif shape in ('hood', 'veil'):
        ln = h or (1.9 if shape == 'veil' else 1.5)
        open_x = 0.55 if shape == 'veil' else 0.4
        d = (f'M{n(open_x)} -0.92 C 0.1 -1.35 -1.25 -1.3 -1.22 -0.1 C -1.2 {n(ln * 0.5)} -1.05 {n(ln)} -0.8 {n(ln)} '
             f'L 0.55 {n(ln)} C 0.4 {n(ln * 0.6)} 0.25 0.9 0.15 0.75 C -0.1 0.4 -0.25 -0.4 {n(open_x)} -0.92 Z')
        body = path(d, **st)
    elif shape == 'flap':
        ln = h or 1.0
        body = path(f'M-0.7 -0.6 C -1.15 -0.3 -1.3 {n(ln * 0.5)} -1.25 {n(ln)} L-0.55 {n(ln * 0.8)} L-0.55 -0.2 Z', **st)
    elif shape == 'nasal':
        body = path('M0.88 -0.62 L1.02 -0.6 L1.08 0.25 L0.96 0.27 Z', **st)
    elif shape == 'cheek':
        body = path('M0.2 -0.35 C 0.5 -0.35 0.62 0.1 0.48 0.6 L0.18 0.55 Z', **st)
    elif shape == 'horns':
        body = path('M-0.6 -0.75 C -1.2 -0.9 -1.4 -1.4 -1.2 -1.8 C -1.0 -1.4 -0.7 -1.15 -0.35 -0.95 Z', **st) + \
            path('M0.6 -0.75 C 1.2 -0.9 1.4 -1.4 1.2 -1.8 C 1.0 -1.4 0.7 -1.15 0.35 -0.95 Z', **st)
    elif shape == 'wreath':
        body = ''
        for i in range(7):
            a = math.pi * (1.1 + i * 0.13)
            x, y = math.cos(a) * 1.02, math.sin(a) * 1.02 - 0.05
            body += ellipse((x, y), 0.17, 0.08, fill=col, stroke=ink, stroke_width=ow * 0.6,
                            transform=f'rotate({n(math.degrees(a) + 90)} {n(x)} {n(y)})')
    elif shape == 'tassel':
        sw = noise1(t * 2, 4) * 0.08
        body = path(f'M{n(x0)} {n(y0)} q -0.2 0.3 {n(-0.3 + sw)} 0.6', fill='none', stroke=col, stroke_width=0.12)
    elif shape == 'feathers':
        body = ''
        k = hw.get('count', 7)
        for i in range(k):
            a = -150 + i * (120 / max(1, k - 1))
            body += group(path('M0 0 C -0.12 -0.4 -0.1 -0.8 0 -0.95 C 0.1 -0.8 0.12 -0.4 0 0 Z', **st),
                          transform=f'translate(0 -0.7) rotate({n(a + 90)}) scale(1.2)')
    elif shape == 'svg':
        body = hw.get('svg', '')
    else:
        raise ValueError(f'Unknown headwear shape "{shape}". Known: cap dome cone cylinder brim band points crest plume '
                         f'wrap hood veil flap nasal cheek horns wreath tassel feathers svg')
    tr = []
    if x0 or y0:
        if shape != 'tassel':
            tr.append(f'translate({n(x0)} {n(y0)})')
    if hw.get('tilt'):
        tr.append(f'rotate({n(hw["tilt"])})')
    if hw.get('s'):
        tr.append(f'scale({n(hw["s"])})')
    return group(body, transform=' '.join(tr)) if tr else body
