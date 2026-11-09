"""Self-check for an episode: does it render, does every shot frame its people in both formats, does it read."""
import json
import math
import pathlib

import numpy as np

from .episode import Episode
from .scene import FORMATS, CHAR_H
from .rig import HEAD_R


def check(ep_dir, project=None):
    ep_dir = pathlib.Path(ep_dir)
    P = []
    sp = ep_dir / 'scenes.json'
    if not sp.exists():
        return [f'ERROR no scenes.json in {ep_dir}']
    try:
        raw = json.loads(sp.read_text(encoding='utf-8'))
    except json.JSONDecodeError as e:
        return [f'ERROR scenes.json is not valid JSON: {e}']
    if not (ep_dir / 'words.json').exists():
        P.append('WARN no words.json: run `align` so shots can follow the voice (and talking mouths work)')
    brief = {}
    if (ep_dir / 'brief.json').exists():
        brief = json.loads((ep_dir / 'brief.json').read_text(encoding='utf-8'))
        if not brief.get('sources'):
            P.append('WARN brief.json has no sources: every date, number and name must be sourced')
        txt = json.dumps(raw).lower()
        for term in brief.get('avoid', []):
            if f'"{str(term).lower()}"' in txt:
                P.append(f'WARN "{term}" appears in scenes.json but brief.json lists it under avoid (anachronism?)')
    try:
        ep = Episode(ep_dir, project)
    except Exception as e:
        return P + [f'ERROR episode does not load: {e}']
    for a_id in {a['id'] for s in raw.get('shots', []) for a in s.get('actors', [])}:
        pass
    fmts = raw.get('formats', ['16:9', '9:16'])
    from .render import svg_to_rgb
    moves = []
    trans = []
    for s in ep.shots:
        if s.dur < 0.5:
            P.append(f'WARN {s.id}: only {s.dur:.2f}s long; a shot under half a second rarely reads')
        if s.dur > 7:
            P.append(f'WARN {s.id}: {s.dur:.1f}s is long for this genre; split it or give the camera more to do')
        cam = s.spec.get('camera', {})
        if isinstance(cam, dict):
            moves.append(cam.get('move', 'drift'))
            if cam.get('move') == 'static' and s.dur > 2.5:
                P.append(f'WARN {s.id}: static camera for {s.dur:.1f}s; add a move (push_in, drift, orbit...)')
        elif isinstance(cam, list) and len(cam) == 1 and s.dur > 2.5:
            P.append(f'WARN {s.id}: one camera key for {s.dur:.1f}s means no camera motion')
        tr = s.spec.get('transition', 'cut')
        trans.append(tr if isinstance(tr, str) else tr.get('kind'))
        for fmt in fmts:
            Wpx, Hpx = FORMATS[fmt]
            for u in (0.08, 0.5, 0.92):
                t = s.dur * u
                try:
                    svg = ep.frame_svg(s.start + t, fmt)
                except Exception as e:
                    P.append(f'ERROR {s.id} {fmt} at {t:.2f}s: {e}')
                    break
                cam_ = s.camera(t, fmt)
                for a in s.actors:
                    st = a.state(t)
                    if st.get('opacity', 1) == 0:
                        continue
                    ax, feet_y, h, _ = a.box(t)
                    hx, hy, kl = s.to_screen(a.depth, (ax, feet_y - h * 0.89), cam_, fmt)
                    fx, fy, _ = s.to_screen(a.depth, (ax, s['y'] if False else st['y']), cam_, fmt)
                    r = HEAD_R * st['scale'] * kl
                    inside = -r < hx < Wpx + r and -r < hy < Hpx + r
                    if not inside and -0.5 * Wpx < fx < 1.5 * Wpx:
                        if is_target(s, a.id, t):
                            P.append(f'WARN {s.id} {fmt} t={t:.1f}s: the camera frames "{a.id}" but the head is out of frame ({hx:.0f},{hy:.0f})')
                    elif inside and is_target(s, a.id, t):
                        if hx < 0.04 * Wpx or hx > 0.96 * Wpx or hy < 0.03 * Hpx:
                            P.append(f'WARN {s.id} {fmt} t={t:.1f}s: "{a.id}" head touches the frame edge')
                        if fmt == '9:16' and hy > 0.78 * Hpx:
                            P.append(f'WARN {s.id} 9:16 t={t:.1f}s: "{a.id}" head in the bottom 22% (covered by app captions/buttons)')
                if u == 0.5 and s.actors:
                    img = svg_to_rgb(svg, 0.25)
                    for a in s.actors:
                        st = a.state(t)
                        ax, feet_y, h, _ = a.box(t)
                        hx, hy, kl = s.to_screen(a.depth, (ax, feet_y - h * 0.89), cam_, fmt)
                        r = HEAD_R * st['scale'] * kl
                        c = contrast(img, hx * 0.25, hy * 0.25, r * 0.25)
                        if c is not None and c < 0.07:
                            P.append(f'WARN {s.id} {fmt}: "{a.id}" head barely stands out from the background (contrast {c:.2f}); '
                                     f'darken/lighten the set behind it or add a light')
    for i in range(len(moves) - 2):
        if moves[i] == moves[i + 1] == moves[i + 2]:
            P.append(f'NOTE camera move "{moves[i]}" three shots in a row ({ep.shots[i].id}-{ep.shots[i + 2].id}); vary the moves')
            break
    if len(trans) > 3 and all(t == 'cut' for t in trans[1:]):
        P.append('NOTE every transition is a cut; a whip or zoom on a key beat adds energy')
    if ep.words.get('duration') and ep.shots[-1].end < ep.words['duration']:
        P.append(f'ERROR shots end at {ep.shots[-1].end:.2f}s but the voice runs to {ep.words["duration"]:.2f}s')
    cpm = len(ep.shots) / ep.duration * 60
    P.append(f'INFO {len(ep.shots)} shots over {ep.duration:.1f}s ({cpm:.0f} cuts/min), formats {", ".join(fmts)}')
    return P


def is_target(s, aid, t=None):
    from .scene import parse_t
    cam = s.spec.get('camera', {})
    if isinstance(cam, dict):
        on = cam.get('on')
        return on == aid or (isinstance(on, list) and aid in on)
    if not cam:
        return False
    if t is None:
        return any(k.get('on') == aid or (isinstance(k.get('on'), list) and aid in k.get('on')) for k in cam)
    nearest = min(cam, key=lambda k: abs(parse_t(k.get('t', 0), s.dur) - t))
    on = nearest.get('on')
    return on == aid or (isinstance(on, list) and aid in on)


def contrast(img, x, y, r):
    h, w = img.shape[:2]
    if not (r > 2 and 2 * r < x < w - 2 * r and 2 * r < y < h - 2 * r):
        return None
    yy, xx = np.mgrid[0:h, 0:w]
    d = np.sqrt((xx - x) ** 2 + (yy - y) ** 2)
    lum = (img[..., 0] * 0.2126 + img[..., 1] * 0.7152 + img[..., 2] * 0.0722) / 255
    inner = lum[d < r * 0.7]
    ring = lum[(d > r * 1.25) & (d < r * 2.0)]
    if not len(inner) or not len(ring):
        return None
    return max(abs(float(inner.mean()) - float(np.median(ring))), float(np.std(lum[d < r * 1.35])))
