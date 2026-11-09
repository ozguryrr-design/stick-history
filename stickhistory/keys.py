"""Keyframe interpolation for any value: numbers, lists of numbers, dicts of those. Strings and bools step.

A track is a list of keys: [{"t": 0, ...values}, {"t": 1.2, "ease": "out_back", ...values}].
The ease on a key shapes the segment that ARRIVES at that key. Missing values carry over from the previous key.
"""
from . import ease as E


def lerp(a, b, u):
    if isinstance(a, bool) or isinstance(b, bool):
        return b if u >= 1 else a
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return a + (b - a) * u
    if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)) and len(a) == len(b):
        return [lerp(x, y, u) for x, y in zip(a, b)]
    if isinstance(a, dict) and isinstance(b, dict):
        out = dict(a)
        for k, v in b.items():
            out[k] = lerp(a[k], v, u) if k in a else v
        return out
    return b if u >= 1 else a


def fill(keys, skip=('t', 'ease')):
    """Carry values forward so every key has every field the track ever sets."""
    state, out = {}, []
    for k in sorted(keys, key=lambda k: k.get('t', 0)):
        for f, v in k.items():
            if f in skip:
                continue
            if isinstance(v, dict) and isinstance(state.get(f), dict):
                merged = dict(state[f])
                merged.update(v)
                state[f] = merged
            else:
                state[f] = v
        row = dict(state)
        row['t'] = k.get('t', 0)
        if 'ease' in k:
            row['ease'] = k['ease']
        out.append(row)
    return out


def sample(keys, t, default_ease='in_out_cubic'):
    """Value of a filled track at time t (dict without t/ease)."""
    if not keys:
        return {}
    if t <= keys[0]['t']:
        return _strip(keys[0])
    for a, b in zip(keys, keys[1:]):
        if t < b['t']:
            span = b['t'] - a['t']
            u = 0 if span <= 0 else (t - a['t']) / span
            u = E.get(b.get('ease', default_ease))(u)
            return lerp(_strip(a), _strip(b), u)
    return _strip(keys[-1])


def _strip(k):
    return {f: v for f, v in k.items() if f not in ('t', 'ease')}
