"""An episode: scenes.json + the voice timing + the channel style -> a full SVG frame at any time, in any format."""
import json
import math
import pathlib

from . import ease as E
from .scene import Shot, FORMATS, parse_t
from .style import Style, load_profile
from .svg import rect, n, circle

TRANSITIONS = ('cut', 'whip', 'zoom', 'dissolve', 'dip', 'flash', 'iris', 'push')


class Episode:
    def __init__(self, ep_dir, project_dir=None, profile=None):
        self.dir = pathlib.Path(ep_dir)
        self.project = pathlib.Path(project_dir) if project_dir else self.dir.parent.parent
        self.spec = json.loads((self.dir / 'scenes.json').read_text(encoding='utf-8'))
        prof = profile or load_profile(self.project) or {}
        self.style = Style(prof)
        self.seed = self.style.seed
        self.fps = self.spec.get('fps', 30)
        self.cast = self.spec.get('cast', {})
        wp = self.dir / 'words.json'
        self.words = json.loads(wp.read_text(encoding='utf-8')) if wp.exists() else {}
        self.env = self.words.get('envelope', [])
        self.env_rate = self.words.get('envelope_rate', 100)
        self.duration = self._duration()
        self._resolve_times()
        self.shots = [Shot(s, self) for s in self.spec['shots']]

    # ------------------------------------------------------------ timing
    def _duration(self):
        if self.spec.get('duration'):
            return float(self.spec['duration'])
        if self.words.get('duration'):
            return float(self.words['duration']) + self.spec.get('tail', 0.8)
        last = self.spec['shots'][-1]
        if 'end' in last:
            return self.anchor(last['end'])
        raise ValueError('No duration: add words.json (run align) or "duration" in scenes.json')

    def anchor(self, v):
        """Absolute time: seconds, "w:12" (start of word 12), "w:12e" (its end), "s:3" (start of sentence 3)."""
        if isinstance(v, (int, float)):
            return float(v)
        s = str(v)
        if s.startswith('w:'):
            words = self.words.get('words', [])
            end = s.endswith('e')
            i = int(s[2:].rstrip('e'))
            if not words:
                raise ValueError(f'Anchor {s} needs words.json with words (run align)')
            i = max(0, min(len(words) - 1, i))
            return float(words[i]['end' if end else 'start'])
        if s.startswith('s:'):
            segs = self.words.get('segments', [])
            end = s.endswith('e')
            i = int(s[2:].rstrip('e'))
            if not segs:
                raise ValueError(f'Anchor {s} needs words.json with segments (run align)')
            i = max(0, min(len(segs) - 1, i))
            return float(segs[i]['end' if end else 'start'])
        return float(s.rstrip('s'))

    def _resolve_times(self):
        shots = self.spec['shots']
        t = 0.0
        for i, s in enumerate(shots):
            s.setdefault('id', f'S{i + 1}')
            s['start'] = self.anchor(s['start']) if 'start' in s else t
            if i == 0:
                s['start'] = 0.0
            t = s['start']
        for i, s in enumerate(shots):
            if 'end' in s and i == len(shots) - 1:
                s['end'] = max(self.anchor(s['end']), self.duration)
            elif i + 1 < len(shots):
                s['end'] = shots[i + 1]['start']
            else:
                s['end'] = self.duration
            if s['end'] <= s['start']:
                raise ValueError(f'Shot {s["id"]} has no length ({s["start"]:.2f}s to {s["end"]:.2f}s); check its anchors')

    def voice_level(self, T):
        if not self.env:
            return 0.0
        i = int(T * self.env_rate)
        if 0 <= i < len(self.env):
            return min(1.0, self.env[i] * 1.6)
        return 0.0

    def shot_at(self, T):
        for i, s in enumerate(self.shots):
            if s.start <= T < s.end:
                return i
        return len(self.shots) - 1

    def frame_count(self):
        return int(math.ceil(self.duration * self.fps))

    # ------------------------------------------------------------ frames
    def frame_svg(self, T, fmt):
        Wpx, Hpx = FORMATS[fmt]
        body = self._compose(T, fmt)
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{Wpx}" height="{Hpx}" viewBox="0 0 {Wpx} {Hpx}">'
                f'<rect width="{Wpx}" height="{Hpx}" fill="{self.style.ink}"/>{body}</svg>')

    def _tr(self, shot):
        tr = shot.spec.get('transition', 'cut')
        if isinstance(tr, str):
            tr = {'kind': tr}
        tr = dict(tr)
        tr.setdefault('len', {'whip': 0.34, 'zoom': 0.4, 'dissolve': 0.6, 'dip': 0.6, 'flash': 0.3, 'iris': 0.7, 'push': 0.45}.get(tr['kind'], 0))
        tr.setdefault('dir', 1)
        if tr['kind'] not in TRANSITIONS:
            raise ValueError(f'Shot {shot.id}: unknown transition "{tr["kind"]}". Known: {", ".join(TRANSITIONS)}')
        return tr

    def _extra(self, T, i):
        """Camera offsets for whip/zoom transitions at absolute time T in shot i."""
        cur = self.shots[i]
        ex = {'dx': 0.0, 'zoom': 1.0}
        if i + 1 < len(self.shots):
            tr = self._tr(self.shots[i + 1])
            b, L = cur.end, tr['len']
            if L and T > b - L / 2:
                u = min(1.0, (T - (b - L / 2)) / (L / 2))
                if tr['kind'] == 'whip':
                    ex['dx'] += tr['dir'] * 2.2 * E.in_cubic(u)
                elif tr['kind'] == 'zoom':
                    ex['zoom'] *= 1 + 2.5 * E.in_cubic(u)
        tr = self._tr(cur)
        L = tr['len']
        if L and i > 0 and T < cur.start + L / 2:
            u = max(0.0, (T - cur.start) / (L / 2))
            if tr['kind'] == 'whip':
                ex['dx'] += -tr['dir'] * 2.2 * (1 - E.out_cubic(u))
            elif tr['kind'] == 'zoom':
                ex['zoom'] *= 1 + 1.2 * (1 - E.out_cubic(u))
        return ex

    def _shot_body(self, i, T, fmt, tag=''):
        s = self.shots[i]
        ex = self._extra(T, i)
        exp = self._extra(T - 1 / self.fps, i)
        ex['dx_prev'], ex['zoom_prev'] = exp['dx'], exp['zoom']
        return s.svg(T - s.start, fmt, f'{s.id}{tag}', ex)

    def _compose(self, T, fmt):
        Wpx, Hpx = FORMATS[fmt]
        i = self.shot_at(T)
        cur = self.shots[i]
        body = self._shot_body(i, T, fmt)
        over = ''
        # transition out of this shot into the next (two-shot blends render both)
        if i + 1 < len(self.shots):
            nx = self.shots[i + 1]
            tr = self._tr(nx)
            b, L = cur.end, tr['len']
            if L and T > b - L / 2:
                u = (T - (b - L)) / L if tr['kind'] in ('dissolve',) else (T - (b - L / 2)) / (L / 2)
                u = max(0.0, min(1.0, u))
                if tr['kind'] == 'dissolve':
                    u2 = (T - (b - L / 2)) / L
                    other = self._shot_body(i + 1, T, fmt, 'n')
                    body = body + f'<g opacity="{n(E.smooth(max(0, min(1, u2))))}">{other}</g>'
                elif tr['kind'] == 'push':
                    u2 = E.in_out_cubic((T - (b - L / 2)) / L)
                    other = self._shot_body(i + 1, T, fmt, 'n')
                    d = tr['dir']
                    body = (f'<g transform="translate({n(-d * Wpx * u2)} 0)">{body}</g>'
                            f'<g transform="translate({n(d * Wpx * (1 - u2))} 0)">{other}</g>')
                elif tr['kind'] == 'dip':
                    over += rect(0, 0, Wpx, Hpx, fill=tr.get('color', '#000000'), fill_opacity=E.in_cubic(u))
                elif tr['kind'] == 'iris':
                    body = self._iris(body, 1 - E.in_cubic(u), Wpx, Hpx, cur.id)
                elif tr['kind'] in ('whip', 'zoom'):
                    over += rect(0, 0, Wpx, Hpx, fill='#ffffff', fill_opacity=0.12 * u)
        tr = self._tr(cur)
        L = tr['len']
        if L and i > 0 and T < cur.start + L / 2:
            u = max(0.0, min(1.0, (T - cur.start) / (L / 2)))
            if tr['kind'] == 'dissolve':
                pv = self.shots[i - 1]
                u2 = (T - (cur.start - L / 2)) / L
                other = self._shot_body(i - 1, T, fmt, 'p')
                body = other + f'<g opacity="{n(E.smooth(max(0, min(1, u2))))}">{body}</g>'
            elif tr['kind'] == 'push':
                u2 = E.in_out_cubic((T - (cur.start - L / 2)) / L)
                other = self._shot_body(i - 1, T, fmt, 'p')
                d = tr['dir']
                body = (f'<g transform="translate({n(-d * Wpx * u2)} 0)">{other}</g>'
                        f'<g transform="translate({n(d * Wpx * (1 - u2))} 0)">{body}</g>')
            elif tr['kind'] == 'dip':
                over += rect(0, 0, Wpx, Hpx, fill=tr.get('color', '#000000'), fill_opacity=1 - E.out_cubic(u))
            elif tr['kind'] == 'flash':
                over += rect(0, 0, Wpx, Hpx, fill=tr.get('color', '#ffffff'), fill_opacity=0.9 * (1 - u))
            elif tr['kind'] == 'iris':
                body = self._iris(body, E.out_cubic(u), Wpx, Hpx, cur.id + 'i')
        # fade in at the very start and out at the very end
        if T < 0.25:
            over += rect(0, 0, Wpx, Hpx, fill='#000', fill_opacity=1 - T / 0.25)
        if T > self.duration - 0.35:
            over += rect(0, 0, Wpx, Hpx, fill='#000', fill_opacity=min(1, (T - (self.duration - 0.35)) / 0.35))
        return body + over

    def _iris(self, body, u, Wpx, Hpx, uid):
        r = max(1, u * math.hypot(Wpx, Hpx) / 2)
        mid = f'{uid}iris'
        return (f'<defs><mask id="{mid}"><rect width="{Wpx}" height="{Hpx}" fill="#000"/>{circle((Wpx / 2, Hpx / 2), r, fill="#fff")}</mask></defs>'
                f'<g mask="url(#{mid})">{body}</g>')
