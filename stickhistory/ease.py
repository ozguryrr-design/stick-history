"""Easing curves. Every function maps 0..1 to 0..1 (back/elastic may overshoot)."""
import math


def linear(t):
    return t


def smooth(t):
    return t * t * (3 - 2 * t)


def in_quad(t):
    return t * t


def out_quad(t):
    return 1 - (1 - t) ** 2


def in_out_quad(t):
    return 2 * t * t if t < 0.5 else 1 - (-2 * t + 2) ** 2 / 2


def in_cubic(t):
    return t ** 3


def out_cubic(t):
    return 1 - (1 - t) ** 3


def in_out_cubic(t):
    return 4 * t ** 3 if t < 0.5 else 1 - (-2 * t + 2) ** 3 / 2


def in_expo(t):
    return 0 if t <= 0 else 2 ** (10 * t - 10)


def out_expo(t):
    return 1 if t >= 1 else 1 - 2 ** (-10 * t)


def in_out_expo(t):
    if t <= 0:
        return 0
    if t >= 1:
        return 1
    return 2 ** (20 * t - 10) / 2 if t < 0.5 else (2 - 2 ** (-20 * t + 10)) / 2


def out_back(t, s=1.70158):
    t -= 1
    return 1 + (s + 1) * t ** 3 + s * t ** 2


def in_back(t, s=1.70158):
    return (s + 1) * t ** 3 - s * t ** 2


def in_out_back(t, s=1.70158 * 1.525):
    if t < 0.5:
        return ((2 * t) ** 2 * ((s + 1) * 2 * t - s)) / 2
    return ((2 * t - 2) ** 2 * ((s + 1) * (t * 2 - 2) + s) + 2) / 2


def out_elastic(t):
    if t <= 0 or t >= 1:
        return t
    return 2 ** (-10 * t) * math.sin((t * 10 - 0.75) * (2 * math.pi / 3)) + 1


def step(t):
    return 0 if t < 1 else 1


EASES = {
    'linear': linear, 'smooth': smooth, 'in_quad': in_quad, 'out_quad': out_quad, 'in_out_quad': in_out_quad,
    'in': in_cubic, 'out': out_cubic, 'in_out': in_out_cubic,
    'in_cubic': in_cubic, 'out_cubic': out_cubic, 'in_out_cubic': in_out_cubic,
    'in_expo': in_expo, 'out_expo': out_expo, 'in_out_expo': in_out_expo,
    'out_back': out_back, 'in_back': in_back, 'in_out_back': in_out_back,
    'out_elastic': out_elastic, 'step': step, 'hold': step,
    # camera-flavoured aliases
    'whip': in_out_expo, 'snap': out_expo, 'settle': out_back, 'drift': in_out_quad,
}


def get(name):
    if callable(name):
        return name
    if name is None:
        return in_out_cubic
    if name not in EASES:
        raise ValueError(f'Unknown ease "{name}". Use one of: {", ".join(sorted(EASES))}')
    return EASES[name]
