"""Shots and cameras: turns an episode (scenes.json) into one SVG per frame, for 16:9 and 9:16 alike.

World: the stage is authored in world units around (960, 540); a person is about 300 tall; `ground` is the y of the
ground line (default 860). The camera looks at world point (x, y) with `zoom` (1 shows 1080 world units of height).
Both formats share the camera's vertical coverage; the portrait frame is narrower and follows the subject.
"""
import math

from . import keys as K
from . import ease as E
from . import world as W
from .rig import draw_character, resolve_pose, walk_overlay, HEAD_R
from .svg import n, esc, rect, circle, group, line, shade, mix, noise1, rng, path, polygon

FORMATS = {'16:9': (1920, 1080), '9:16': (1080, 1920), '1:1': (1080, 1080), '4:5': (1080, 1350)}
CHAR_H = 300
STAGE = (960, 540)
GROUND = 860

FRAMES = {
    # frame: (visible height in character heights, centre height above the feet in character heights)
    'extreme_wide': (4.2, 0.9), 'wide': (2.6, 0.75), 'full': (1.45, 0.5), 'medium': (0.95, 0.64),
    'mcu': (0.62, 0.76), 'cu': (0.4, 0.86), 'ecu': (0.22, 0.89),
}


def parse_t(v, dur, ep=None, start=0.0):
    """Seconds, "40%" of the shot, or a word anchor "w:12" (absolute, resolved by the episode)."""
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip()
    if s.startswith(('w:', 's:')) and ep is not None:
        return max(0.0, ep.anchor(s) - start)
    if s.endswith('%'):
        return dur * float(s[:-1]) / 100
    if s.endswith('s'):
        return float(s[:-1])
    return float(s)


class Actor:
    def __init__(self, spec, cast, dur, ep=None, start=0.0):
        self.id = spec['id']
        self.char = cast[spec.get('char', spec.get('cast', spec.get('ref', spec['id'])))]
        self.depth = spec.get('depth', 1)
        base = {k: v for k, v in spec.items() if k not in ('keys', 'id', 'char', 'cast', 'ref', 'depth')}
        if 'pose' not in base and (base.get('mount') or self.char.get('mount')):
            base['pose'] = 'ride'
        base.setdefault('pose', 'stand')
        base['t'] = 0
        rows = [base] + [dict(k) for k in spec.get('keys', [])]
        for r in rows:
            r['t'] = parse_t(r.get('t', 0), dur, ep, start)
            if 'pose' in r:
                r['pose'] = resolve_pose(r['pose'])
        self.keys = K.fill(rows)
        self.auto_walk = spec.get('auto_walk', True)

    def state(self, t):
        s = K.sample(self.keys, t)
        s.setdefault('x', STAGE[0])
        s.setdefault('y', GROUND)
        s.setdefault('scale', 1.0)
        s.setdefault('face', 1)
        return s

    def mount_spec(self, s):
        m = s.get('mount', self.char.get('mount'))
        if not m:
            return None
        return {'type': m} if isinstance(m, str) else dict(m)

    def box(self, t):
        s = self.state(t)
        m = self.mount_spec(s)
        mh = W.MOUNT_HEIGHT.get(m.get('type', 'horse'), 135) if m else 120
        return s['x'], s['y'] - (mh - 120) * s['scale'], CHAR_H * s['scale'], (1 if s.get('face', 1) >= 0 else -1)


class Shot:
    def __init__(self, spec, ep):
        self.spec = spec
        self.ep = ep
        self.id = spec.get('id', 'S')
        self.start = spec['start']
        self.end = spec['end']
        self.dur = self.end - self.start
        self.tod = spec.get('time', ep.spec.get('time', 'day'))
        self.ground = spec.get('ground_y', GROUND)
        cast = ep.cast
        self.actors = [Actor(a, cast, self.dur, ep, self.start) for a in spec.get('actors', [])]
        self.by_id = {a.id: a for a in self.actors}
        self._cam = {}

    # ------------------------------------------------------------ camera
    def target(self, on, t):
        """(x, feet_y, height, face) of what the camera frames."""
        if isinstance(on, str):
            if on not in self.by_id:
                raise ValueError(f'Shot {self.id}: camera "on" names unknown actor "{on}"')
            return self.by_id[on].box(t)
        if isinstance(on, (list, tuple)) and on and isinstance(on[0], str):
            boxes = [self.target(o, t) for o in on]
            xs = [b[0] for b in boxes]
            h = max(b[2] for b in boxes)
            return (min(xs) + max(xs)) / 2, max(b[1] for b in boxes), h, boxes[0][3], max(xs) - min(xs)
        if isinstance(on, (list, tuple)):
            return on[0], on[1] + CHAR_H * 0.5, CHAR_H, 1
        return STAGE[0], GROUND, CHAR_H, 1

    def resolve_cam_key(self, k, fmt):
        out = dict(k)
        if 'frame' in k:
            fr = k['frame']
            on = k.get('on')
            if fr == 'stage' or (fr in ('wide', 'extreme_wide') and on is None):
                vh = 1080 * (1.0 if fr != 'extreme_wide' else 1.35) * (1.35 if fmt == '9:16' else 1.0)
                cx, cy = k.get('at', STAGE)
                face = 1
            else:
                tg = self.target(on, k['t'])
                x, feet, h, face = tg[:4]
                spread = tg[4] if len(tg) > 4 else 0
                rel, up = FRAMES[fr]
                vh = h * rel
                cx, cy = x, feet - h * up
                if spread:
                    if fmt == '9:16':
                        vh = max(vh, min(spread * 16 / 9 * 1.1, h * 2.6))
                    else:
                        vh = max(vh, (spread + h * 0.7) * 9 / 16 * 1.15)
                        cy = feet - vh * 0.5 + h * 0.1
                else:
                    lead = k.get('lead', 0.11 if fr in ('medium', 'mcu', 'cu', 'full') else 0.0)
                    wide = vh * (16 / 9 if fmt != '9:16' else 9 / 16)
                    cx += face * wide * (lead if fmt != '9:16' else lead * 0.25)
            off = k.get('offset', (0, 0))
            ox_scale = (0.42 if (fmt == '9:16' and on is not None) else 1.0)
            cx += off[0] * ox_scale * vh / 1080
            cy += off[1] * vh / 1080
            out['x'], out['y'], out['zoom'] = cx, cy, 1080 / vh * k.get('push', 1.0)
        pk = k.get('portrait') if fmt == '9:16' else None
        if pk:
            out.update(pk)
        out.setdefault('rot', 0)
        for f in ('frame', 'on', 'offset', 'portrait', 'lead', 'push', 'at'):
            out.pop(f, None)
        return out

    def cam_keys(self, fmt):
        if fmt in self._cam:
            return self._cam[fmt]
        spec = self.spec.get('camera', {'frame': 'stage'})
        if isinstance(spec, dict):
            spec = expand_move(spec, self.dur, self.ep.style.camera['speed'])
        rows = []
        for k in spec:
            k = dict(k)
            k['t'] = parse_t(k.get('t', 0), self.dur, self.ep, self.start)
            rows.append(k)
        rows = K.fill(rows)
        resolved = [self.resolve_cam_key(k, fmt) for k in rows]
        for r, k in zip(resolved, rows):
            r['lz'] = math.log(max(0.05, r.pop('zoom', 1.0)))
            r['t'] = k['t']
            if 'ease' in k:
                r['ease'] = k['ease']
        self._cam[fmt] = resolved
        return resolved

    def camera(self, t, fmt):
        c = K.sample(self.cam_keys(fmt), t)
        c.setdefault('x', STAGE[0])
        c.setdefault('y', STAGE[1])
        c['zoom'] = math.exp(c.pop('lz', 0.0))
        c.setdefault('rot', 0)
        # handheld drift and impact shakes
        energy = self.ep.style.camera
        vh = 1080 / c['zoom']
        hh = self.spec.get('handheld', c.get('handheld', 0.35 if energy['speed'] >= 1 else 0.15))
        sx = noise1(t * 0.7, 101) * hh * vh * 0.006
        sy = noise1(t * 0.6, 202) * hh * vh * 0.005
        shake = 0
        for hit in self.spec.get('hits', []):
            ht = parse_t(hit if not isinstance(hit, dict) else hit['t'], self.dur, self.ep, self.start)
            amp = 1.0 if not isinstance(hit, dict) else hit.get('amp', 1.0)
            if t >= ht:
                u = t - ht
                shake += amp * math.exp(-u * 7) * (u < 1.2)
        shake *= energy['shake']
        sx += noise1(t * 28, 303) * shake * vh * 0.025
        sy += noise1(t * 31, 404) * shake * vh * 0.025
        c['x'] += sx
        c['y'] += sy
        c['rot'] += noise1(t * 25, 505) * shake * 1.2
        return c

    # ------------------------------------------------------------ drawing
    def svg(self, t, fmt, uid, extra=None):
        """The shot's frame body at local time t."""
        Wpx, Hpx = FORMATS[fmt]
        S = self.ep.style
        extra = extra or {}
        cam = self.camera(t, fmt)
        cam['x'] += extra.get('dx', 0) * 1080 / cam['zoom']
        cam['zoom'] *= extra.get('zoom', 1.0)
        dt = 1 / self.ep.fps
        prev = self.camera(t - dt, fmt)
        prev['x'] += extra.get('dx_prev', extra.get('dx', 0)) * 1080 / prev['zoom']
        prev['zoom'] *= extra.get('zoom_prev', extra.get('zoom', 1.0))
        k = Hpx / (1080 / cam['zoom'])
        # motion blur only for fast moves (whips, snaps, zoom-throughs), in output pixels per frame
        bk = S.camera['blur'] * (Hpx / 1080)
        blur_x = max(0.0, abs(cam['x'] - prev['x']) * k - 34 * (Hpx / 1080)) * 0.22 * bk
        blur_y = max(0.0, abs(cam['y'] - prev['y']) * k - 34 * (Hpx / 1080)) * 0.22 * bk
        zb = max(0.0, abs(math.log(cam['zoom'] / prev['zoom'])) - 0.05) * 90 * bk
        blur_x, blur_y = blur_x + zb, blur_y + zb
        env = S.times(self.tod)
        env.update({k2: S.c(v) for k2, v in self.spec.get('env', {}).items() if k2 in ('sky_top', 'sky_bottom', 'ground', 'ground_far')})
        defs = []
        body = []
        sky_id = f'{uid}sky'
        defs.append(f'<linearGradient id="{sky_id}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{env["sky_top"]}"/>'
                    f'<stop offset="1" stop-color="{env["sky_bottom"]}"/></linearGradient>')
        body.append(rect(0, 0, Wpx, Hpx, fill=f'url(#{sky_id})'))
        layers = self.layers(env)
        world = []
        for depth, items, opts in layers:
            world.append(self.layer_svg(depth, items, opts, t, cam, fmt, env, uid))
        wbody = ''.join(world)
        if blur_x > 1.0 or blur_y > 1.0:
            fid = f'{uid}mb'
            defs.append(f'<filter id="{fid}" x="0" y="0" width="{Wpx}" height="{Hpx}" filterUnits="userSpaceOnUse">'
                        f'<feGaussianBlur stdDeviation="{n(min(blur_x, 60))} {n(min(blur_y, 60))}"/></filter>')
            wbody = f'<g filter="url(#{fid})">{wbody}</g>'
        body.append(wbody)
        body.append(self.veil_svg(t, cam, fmt, env, uid))
        body.append(self.fx_svg(t, fmt, env, uid, defs))
        body.append(self.text_svg(t, fmt))
        return f'<defs>{"".join(defs)}</defs>' + ''.join(body)

    def layers(self, env):
        """[(depth, items, opts)] far to near, with the actors placed in their depth's layer."""
        spec = self.spec
        out = {}
        g = self.ground
        # automatic ground: far band and near ground, unless the shot says ground: false
        if spec.get('ground', True) is not False:
            out.setdefault(4.0, ([], {}))[0].append({'kind': 'ground', 'y': g - spec.get('horizon', 170), 'color': env['ground_far'], '_raw': True})
            out.setdefault(1.0, ([], {}))[0].append({'kind': 'ground', 'y': g, 'color': env['ground'], '_raw': True})
        for L in spec.get('layers', []):
            d = float(L.get('depth', 1))
            bucket = out.setdefault(d, ([], {}))
            bucket[0].extend(L.get('items', []))
            bucket[1].update({k: v for k, v in L.items() if k not in ('items', 'depth')})
        for a in self.actors:
            out.setdefault(float(a.depth), ([], {}))[0].append({'kind': '_actor', 'actor': a})
        return [(d, items, opts) for d, (items, opts) in sorted(out.items(), key=lambda kv: -kv[0])]

    def layer_svg(self, depth, items, opts, t, cam, fmt, env, uid):
        Wpx, Hpx = FORMATS[fmt]
        S = self.ep.style
        z = max(0.2, depth)
        k0 = Hpx / 1080
        kl = k0 * cam['zoom'] ** (1 / z)
        cx = STAGE[0] + (cam['x'] - STAGE[0]) / z
        cy = STAGE[1] + (cam['y'] - STAGE[1]) / z
        P = W.Painter(S, depth, self.tod, t, self.ground, self.ep.seed)
        parts = []
        actors = []
        front = []
        for it in items:
            if it.get('kind') == '_actor':
                actors.append(it['actor'])
                continue
            if it.get('_raw'):
                parts.append(rect(-6000, it['y'], 16000, 6000, fill=S.depth_tint(it['color'], depth, self.tod) if depth > 1 else it['color']))
                continue
            (front if it.get('front') else parts).append(W.draw_item(P, it))
        actors.sort(key=lambda a: a.state(t)['y'])
        for a in actors:
            parts.append(self.actor_svg(a, t, depth))
        parts.extend(front)
        parts.append(self.lights_svg(t, depth, env, uid))
        body = ''.join(parts)
        tr = f'translate({n(Wpx / 2)} {n(Hpx / 2)}) rotate({n(cam["rot"])}) scale({n(kl)}) translate({n(-cx)} {n(-cy)})'
        g = f'<g transform="{tr}">{body}</g>'
        blur = opts.get('blur')
        if isinstance(blur, (list, tuple)) and len(blur) == 2:
            u_b = E.in_out_cubic(min(1.0, max(0.0, t / max(0.01, self.dur))))
            blur = blur[0] + (blur[1] - blur[0]) * u_b
        if blur and blur > 0.3:
            fid = f'{uid}b{str(depth).replace(".", "_")}'
            g = (f'<defs><filter id="{fid}" x="0" y="0" width="{Wpx}" height="{Hpx}" filterUnits="userSpaceOnUse"><feGaussianBlur stdDeviation="{n(blur)}"/></filter></defs>'
                 f'<g filter="url(#{fid})">{g}</g>')
        if opts.get('opacity') is not None:
            g = f'<g opacity="{n(opts["opacity"])}">{g}</g>'
        return g

    def actor_svg(self, a, t, depth):
        S = self.ep.style
        s = a.state(t)
        pose = dict(s.get('pose', {}))
        mspec = a.mount_spec(s)
        walk = s.get('walk')
        run = s.get('run', False)
        if walk is None and a.auto_walk:
            x0 = a.state(t - 0.05)['x']
            x1 = a.state(t + 0.05)['x']
            v = abs(x1 - x0) / 0.1 / max(0.2, s['scale'])
            walk = v / (95 if not run else 160) if v > 8 else 0
            run = run or v > 330
        if walk and not mspec:
            amount = min(1.0, walk / 0.6)
            pose = walk_overlay(pose, t * walk * 2 * math.pi + hash(a.id) % 7, amount, run)
        if mspec and mspec.get('type', 'horse') in ('horse', 'camel', 'elephant'):
            pose.update({'leg_n': 62, 'knee_n': -75, 'leg_f': 55, 'knee_f': -70, 'hip_h': -15, '_mounted': True})
        if s.get('lift'):
            pose['lift'] = pose.get('lift', 0) + s['lift']
        # breathing so nobody is ever frozen
        pose['lean'] = pose.get('lean', 0) + math.sin(t * 2.1 + len(a.id)) * 0.8
        talk = 0.0
        if s.get('talk'):
            talk = self.ep.voice_level(self.start + t) * float(s['talk'] if not isinstance(s['talk'], bool) else 1.0)
        yaw = s.get('yaw', 1.0)
        svg, sk = draw_character(S, a.char, pose, t, yaw=yaw, expr=s.get('expr', 'neutral'), talk=talk,
                                 blink_seed=sum(map(ord, a.id)), look=s.get('look'))
        face = 1 if s.get('face', 1) >= 0 else -1
        sc = s['scale']
        mount_svg = ''
        ry = s['y']
        if mspec:
            gait = mspec.get('gait', walk or 0.0)
            P = W.Painter(S, depth, self.tod, t, self.ground, self.ep.seed)
            m_it = dict(mspec, x=s['x'], y=s['y'], scale=sc, face=face, gait=gait)
            mount_svg = W.mount(P, m_it)
            mh = W.MOUNT_HEIGHT.get(mspec.get('type', 'horse'), 135)
            ph = t * gait * math.pi * 2 + (s['x'] * 0.01)
            bob = abs(math.sin(ph)) * (7 if gait > 1.2 else 3) if gait else 0
            ry = s['y'] - (mh + bob) * sc
        shadow = ''
        if not mspec and ('hip_h' not in pose or pose.get('hip_h', 0) < 20):
            shadow = f'<ellipse cx="{n(s["x"])}" cy="{n(s["y"])}" rx="{n(48 * sc)}" ry="{n(9 * sc)}" fill="#000" fill-opacity="0.18"/>'
        elif mspec:
            shadow = f'<ellipse cx="{n(s["x"])}" cy="{n(s["y"])}" rx="{n(95 * sc)}" ry="{n(12 * sc)}" fill="#000" fill-opacity="0.2"/>'
        rotate = f' rotate({n(s["tilt"])})' if s.get('tilt') else ''
        op = s.get('opacity')
        g = f'<g transform="translate({n(s["x"])} {n(ry)}){rotate} scale({n(sc * face)} {n(sc)})"' + (f' opacity="{n(op)}"' if op is not None else '') + f'>{svg}</g>'
        return shadow + mount_svg + g

    def to_screen(self, depth, p, cam, fmt):
        Wpx, Hpx = FORMATS[fmt]
        z = max(0.2, depth)
        kl = Hpx / 1080 * cam['zoom'] ** (1 / z)
        cx = STAGE[0] + (cam['x'] - STAGE[0]) / z
        cy = STAGE[1] + (cam['y'] - STAGE[1]) / z
        x, y = (p[0] - cx) * kl, (p[1] - cy) * kl
        a = math.radians(cam['rot'])
        return Wpx / 2 + x * math.cos(a) - y * math.sin(a), Hpx / 2 + x * math.sin(a) + y * math.cos(a), kl

    def veil_svg(self, t, cam, fmt, env, uid):
        """Darkness over the frame with soft holes where the lights are (screen space, so it stays cheap)."""
        veil = self.spec.get('veil', 0)
        if not veil:
            return ''
        Wpx, Hpx = FORMATS[fmt]
        defs, holes = '', ''
        for i, L in enumerate(self.spec.get('lights', [])):
            if L.get('hole', True) is False:
                continue
            sx, sy, kl = self.to_screen(float(L.get('depth', 1)), (L['x'], L['y']), cam, fmt)
            gid = f'{uid}h{i}'
            defs += (f'<radialGradient id="{gid}"><stop offset="0" stop-color="#000"/><stop offset="0.5" stop-color="#000" stop-opacity="0.75"/>'
                     f'<stop offset="1" stop-color="#000" stop-opacity="0"/></radialGradient>')
            fl = 1 + noise1(t * L.get('flicker', 0) * 6, i) * 0.06 if L.get('flicker') else 1
            holes += circle((sx, sy), L.get('r', 300) * kl * fl, fill=f'url(#{gid})')
        mid = f'{uid}veil'
        defs += f'<mask id="{mid}" maskUnits="userSpaceOnUse" x="0" y="0" width="{Wpx}" height="{Hpx}"><rect width="{Wpx}" height="{Hpx}" fill="#fff"/>{holes}</mask>'
        return (f'<defs>{defs}</defs><rect width="{Wpx}" height="{Hpx}" fill="{shade(env["sky_top"], -0.55)}" fill-opacity="{n(veil)}" '
                f'mask="url(#{mid})"/>')

    def lights_svg(self, t, depth, env, uid):
        lights = [L for L in self.spec.get('lights', []) if float(L.get('depth', 1)) == depth]
        if not lights:
            return ''
        S = self.ep.style
        out = ''
        defs = ''
        for i, L in enumerate(lights):
            gid = f'{uid}g{i}'
            col = S.c(L.get('color'), 0.1) if L.get('color') else env['light']
            defs += (f'<radialGradient id="{gid}"><stop offset="0" stop-color="{col}" stop-opacity="{n(L.get("strength", 0.35))}"/>'
                     f'<stop offset="1" stop-color="{col}" stop-opacity="0"/></radialGradient>')
            fl = 1 + noise1(t * L.get('flicker', 0) * 6, i + 9) * 0.08 if L.get('flicker') else 1
            out += circle((L['x'], L['y']), L.get('r', 300) * 0.8 * fl, fill=f'url(#{gid})')
        return f'<defs>{defs}</defs>{out}'

    # ------------------------------------------------------------ screen-space effects and text
    def fx_svg(self, t, fmt, env, uid, defs):
        Wpx, Hpx = FORMATS[fmt]
        out = ''
        for f in self.spec.get('fx', []):
            if isinstance(f, str):
                f = {'kind': f}
            kind = f['kind']
            r = rng('fx', kind, self.id)
            if kind in ('dust', 'embers', 'snow', 'rain', 'ash'):
                cnt = f.get('count', {'rain': 140, 'snow': 90}.get(kind, 45))
                for i in range(cnt):
                    x0, y0 = r.random() * Wpx, r.random() * Hpx
                    sp = r.uniform(0.5, 1.5)
                    if kind == 'rain':
                        y = (y0 + t * 1400 * sp) % (Hpx + 100) - 50
                        x = (x0 - t * 200 * sp) % Wpx
                        out += line((x, y), (x - 8, y + 34), stroke='#c8d4e0', stroke_width=2, stroke_opacity=0.5)
                    elif kind == 'snow':
                        y = (y0 + t * 90 * sp) % (Hpx + 40) - 20
                        x = (x0 + math.sin(t + i) * 30) % Wpx
                        out += circle((x, y), 2 + sp * 2.5, fill='#ffffff', fill_opacity=0.85)
                    elif kind == 'embers':
                        y = (y0 - t * 120 * sp) % (Hpx + 40) - 20
                        x = (x0 + math.sin(t * 2 + i) * 40) % Wpx
                        out += circle((x, y), 1.5 + sp * 2, fill='#ffb347', fill_opacity=0.5 + 0.4 * math.sin(t * 6 + i))
                    else:
                        y = (y0 - t * 18 * sp) % Hpx
                        x = (x0 + t * 25 * sp + math.sin(t + i) * 20) % Wpx
                        out += circle((x, y), 1.2 + sp * 1.5, fill=env['light'], fill_opacity=0.25 + 0.2 * math.sin(t * 2 + i))
            elif kind == 'fog':
                out += rect(0, Hpx * f.get('y', 0.6), Wpx, Hpx, fill=f'url(#{uid}fog)')
                defs.append(f'<linearGradient id="{uid}fog" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{env["sky_bottom"]}" stop-opacity="0"/>'
                            f'<stop offset="1" stop-color="{env["sky_bottom"]}" stop-opacity="{n(f.get("amount", 0.6))}"/></linearGradient>')
            elif kind == 'flash':
                ft = parse_t(f.get('t', 0), self.dur)
                if t >= ft:
                    a = max(0, 1 - (t - ft) / f.get('len', 0.35))
                    if a > 0:
                        out += rect(0, 0, Wpx, Hpx, fill=f.get('color', '#ffffff'), fill_opacity=a * f.get('amount', 0.85))
            elif kind == 'rays':
                cx = Wpx * f.get('x', 0.75)
                for i in range(6):
                    a = math.radians(100 + i * 9 + math.sin(t * 0.5 + i) * 2)
                    L = Hpx * 1.6
                    out += polygon([(cx, -20), (cx + math.cos(a - 0.03) * L, math.sin(a - 0.03) * L), (cx + math.cos(a + 0.03) * L, math.sin(a + 0.03) * L)],
                                   fill=env['light'], fill_opacity=0.06)
            elif kind == 'tint':
                out += rect(0, 0, Wpx, Hpx, fill=self.ep.style.c(f.get('color', '#000000'), 0), fill_opacity=f.get('amount', 0.2))
        return out

    def text_svg(self, t, fmt):
        out = ''
        for tx in self.spec.get('text', []):
            out += text_block(self.ep.style, tx, t, self.dur, fmt)
        return out


def text_block(S, tx, t, dur, fmt):
    Wpx, Hpx = FORMATS[fmt]
    portrait = fmt == '9:16'
    kind = tx.get('kind', 'title')
    t0 = parse_t(tx.get('t', 0), dur)
    t1 = parse_t(tx.get('until', dur), dur)
    if t < t0 or t > t1 + 0.4:
        return ''
    u_in = min(1.0, (t - t0) / tx.get('in', 0.45))
    u_out = max(0.0, (t - t1) / 0.35)
    a = E.out_cubic(u_in) * (1 - u_out)
    ink = S.c(tx['color'], 0) if tx.get('color') else S.pal['paper'] if kind in ('title', 'year') and False else None
    fam = S.font
    light = tx.get('light', True)
    col = '#fbf6ea' if light else S.ink
    shadow_col = '#000000' if light else '#ffffff'
    if kind == 'title':
        size = tx.get('size', 120 if not portrait else 104)
        y = Hpx * tx.get('y', 0.42 if not portrait else 0.36)
        sc = 1.12 - 0.12 * E.out_expo(u_in)
        sp = (1 - E.out_cubic(u_in)) * 18
        lines_ = str(tx['text']).split('\n')
        body = ''
        for i, L in enumerate(lines_):
            yy = y + i * size * 1.05
            body += (f'<text x="{n(Wpx / 2)}" y="{n(yy)}" font-family="{fam}" font-size="{n(size)}" font-weight="700" text-anchor="middle" '
                     f'letter-spacing="{n(sp)}" fill="{shadow_col}" fill-opacity="0.35" transform="translate(4 5)">{esc(L)}</text>'
                     f'<text x="{n(Wpx / 2)}" y="{n(yy)}" font-family="{fam}" font-size="{n(size)}" font-weight="700" text-anchor="middle" '
                     f'letter-spacing="{n(sp)}" fill="{col}">{esc(L)}</text>')
        if tx.get('sub'):
            yy = y + len(lines_) * size * 1.05 + size * 0.05
            body += line((Wpx / 2 - 160 * a, yy - size * 0.55), (Wpx / 2 + 160 * a, yy - size * 0.55), stroke=S.accent, stroke_width=4)
            body += (f'<text x="{n(Wpx / 2)}" y="{n(yy)}" font-family="{fam}" font-size="{n(size * 0.38)}" text-anchor="middle" '
                     f'letter-spacing="6" fill="{col}">{esc(tx["sub"])}</text>')
        cx, cy = Wpx / 2, y
        return f'<g opacity="{n(a)}" transform="translate({n(cx)} {n(cy)}) scale({n(sc)}) translate({n(-cx)} {n(-cy)})">{body}</g>'
    if kind == 'year':
        a0, a1 = tx.get('from', tx.get('to', 0)), tx.get('to', 0)
        cu = min(1.0, max(0.0, (t - t0) / tx.get('count', 1.2)))
        v = round(a0 + (a1 - a0) * E.out_cubic(cu))
        label = f'{tx.get("prefix", "")}{v}{tx.get("suffix", "")}'
        size = tx.get('size', 190 if not portrait else 170)
        y = Hpx * tx.get('y', 0.5 if not portrait else 0.42)
        body = (f'<text x="{n(Wpx / 2 + 5)}" y="{n(y + 6)}" font-family="{fam}" font-size="{n(size)}" font-weight="700" text-anchor="middle" fill="{shadow_col}" fill-opacity="0.35">{esc(label)}</text>'
                f'<text x="{n(Wpx / 2)}" y="{n(y)}" font-family="{fam}" font-size="{n(size)}" font-weight="700" text-anchor="middle" fill="{col}">{esc(label)}</text>')
        if tx.get('sub'):
            body += (f'<text x="{n(Wpx / 2)}" y="{n(y + size * 0.42)}" font-family="{fam}" font-size="{n(size * 0.24)}" text-anchor="middle" '
                     f'letter-spacing="5" fill="{col}">{esc(tx["sub"])}</text>')
        return f'<g opacity="{n(a)}">{body}</g>'
    if kind == 'label':
        size = tx.get('size', 46 if not portrait else 50)
        x = Wpx * (0.06 if not portrait else 0.08)
        y = Hpx * tx.get('y', 0.86 if not portrait else 0.74)
        wline = 220 * E.out_expo(u_in)
        body = rect(x, y - size * 1.05, 6, size * (1.6 if tx.get('sub') else 1.15), fill=S.accent)
        body += (f'<text x="{n(x + 24)}" y="{n(y)}" font-family="{fam}" font-size="{n(size)}" font-weight="700" fill="{col}" '
                 f'stroke="{shadow_col}" stroke-opacity="0.25" stroke-width="6" paint-order="stroke">{esc(tx["text"])}</text>')
        if tx.get('sub'):
            body += (f'<text x="{n(x + 24)}" y="{n(y + size * 0.62)}" font-family="{fam}" font-size="{n(size * 0.5)}" letter-spacing="3" fill="{col}" '
                     f'stroke="{shadow_col}" stroke-opacity="0.25" stroke-width="4" paint-order="stroke">{esc(tx["sub"])}</text>')
        dx = (1 - E.out_cubic(u_in)) * -40
        return f'<g opacity="{n(a)}" transform="translate({n(dx)} 0)">{body}</g>'
    if kind == 'caption':
        size = tx.get('size', 52 if not portrait else 58)
        y = Hpx * tx.get('y', 0.9 if not portrait else 0.8)
        return (f'<g opacity="{n(a)}"><text x="{n(Wpx / 2)}" y="{n(y)}" font-family="{fam}" font-size="{n(size)}" font-weight="700" text-anchor="middle" '
                f'fill="{col}" stroke="{shadow_col}" stroke-opacity="0.45" stroke-width="8" paint-order="stroke">{esc(tx["text"])}</text></g>')
    if kind == 'card':
        lines_ = str(tx['text']).split('\n')
        max_ch = max([len(L) for L in lines_] + [len(tx.get('source', '')) * 0.65, 1])
        max_bw = Wpx * (0.76 if not portrait else 0.90)
        size = tx.get('size', 40 if not portrait else 34)
        size = min(size, (max_bw - 80) / max(1, max_ch * 0.54))
        bw = min(max_bw, max(Wpx * (0.56 if not portrait else 0.82), max_ch * size * 0.55 + 84))
        bh = size * (1.48 * len(lines_) + (1.55 if tx.get('source') else 0.8))
        x0, y0 = (Wpx - bw) / 2, Hpx * tx.get('y', 0.5) - bh / 2
        from .svg import luma
        dark_card = luma(S.pal['paper']) < 0.35
        fg = '#f6efe2' if dark_card else S.ink
        border = S.accent if dark_card else S.ink
        body = rect(x0, y0, bw, bh, rx=18, fill=S.pal['paper'], fill_opacity=0.94, stroke=border, stroke_width=3)
        body += rect(x0, y0, 10, bh, fill=S.accent)
        for i, L in enumerate(lines_):
            body += (f'<text x="{n(x0 + 38)}" y="{n(y0 + size * 1.42 * (i + 1))}" font-family="{fam}" font-size="{n(size)}" font-weight="600" fill="{fg}">{esc(L)}</text>')
        if tx.get('source'):
            body += (f'<text x="{n(x0 + 38)}" y="{n(y0 + bh - size * 0.55)}" font-family="{fam}" font-size="{n(size * 0.56)}" fill="{fg}" '
                     f'fill-opacity="0.78">{esc(tx["source"])}</text>')
        dy = (1 - E.out_back(u_in)) * 30
        return f'<g opacity="{n(a)}" transform="translate(0 {n(dy)})">{body}</g>'
    raise ValueError(f'Unknown text kind "{kind}". Known: title, year, label, caption, card')


# ------------------------------------------------------------ camera move shorthands
def expand_move(spec, dur, speed=1.0):
    """{"frame": "medium", "on": "x", "move": "push_in", "amount": 0.2} -> keys. Moves: static, push_in, pull_out,
    pan_left, pan_right, tilt_up, tilt_down, crane_down, crane_up, drift, orbit, dolly_zoom, snap_in, reveal."""
    base = {k: v for k, v in spec.items() if k not in ('move', 'amount', 'ease')}
    base.setdefault('frame', 'stage')
    mv = spec.get('move', 'drift')
    a = spec.get('amount', 0.18) * speed
    ez = spec.get('ease', 'in_out_cubic')
    k0 = dict(base, t=0)
    k1 = dict(base, t=dur)
    k1['ease'] = ez
    off0 = list(base.get('offset', (0, 0)))
    if mv == 'static':
        return [k0]
    if mv == 'push_in':
        k0['push'] = 1 - a * 0.5
        k1['push'] = 1 + a * 0.5
    elif mv == 'pull_out':
        k0['push'] = 1 + a * 0.5
        k1['push'] = 1 - a * 0.5
    elif mv in ('pan_left', 'pan_right'):
        d = 1 if mv == 'pan_right' else -1
        k0['offset'] = (off0[0] - d * a * 1500, off0[1])
        k1['offset'] = (off0[0] + d * a * 1500, off0[1])
    elif mv in ('tilt_up', 'tilt_down', 'crane_down', 'crane_up'):
        d = -1 if mv in ('tilt_up', 'crane_up') else 1
        k0['offset'] = (off0[0], off0[1] - d * a * 1300)
        k1['offset'] = (off0[0], off0[1] + d * a * 1300)
        if mv.startswith('crane'):
            k0['push'] = 1 - a * 0.4
            k1['push'] = 1 + a * 0.2
    elif mv == 'drift':
        k0['offset'] = (off0[0] - a * 300, off0[1])
        k1['offset'] = (off0[0] + a * 300, off0[1])
        k0['push'], k1['push'] = 1.0, 1 + a * 0.25
        k1['ease'] = 'linear'
    elif mv == 'orbit':
        k0['offset'] = (off0[0] - a * 900, off0[1])
        k1['offset'] = (off0[0] + a * 900, off0[1])
        k0['rot'], k1['rot'] = -a * 8, a * 8
        k0['push'], k1['push'] = 1.0, 1 + a * 0.3
    elif mv == 'snap_in':
        km = dict(base, t=min(0.35, dur * 0.3), push=1 + a * 1.5, ease='out_expo')
        k0['push'] = 1.0
        k1 = dict(km, t=dur, push=1 + a * 1.7, ease='linear')
        return [k0, km, k1]
    elif mv == 'reveal':
        k0['push'] = 1 + a * 2.5
        k1['push'] = 1.0
        k1['ease'] = 'out_cubic'
    elif mv == 'dolly_zoom':
        k0['push'], k1['push'] = 1 - a, 1 + a
        k0['rot'], k1['rot'] = 0, 0
    else:
        raise ValueError(f'Unknown camera move "{mv}"')
    return [k0, k1]
