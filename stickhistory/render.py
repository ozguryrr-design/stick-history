"""Frames -> video. SVG per frame, rendered by resvg in parallel, graded in numpy, piped to ffmpeg."""
import io
import math
import multiprocessing as mp
import os
import pathlib
import shutil
import subprocess
import sys
import time

import numpy as np
from PIL import Image
import resvg_py

from .episode import Episode
from .scene import FORMATS

_EP = None
_POST = None
_FONT_DIRS = []


def ffmpeg_exe():
    exe = shutil.which('ffmpeg')
    if exe:
        return exe
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        raise SystemExit('ffmpeg not found: install it, or `pip install imageio-ffmpeg`.')


def font_dirs():
    here = pathlib.Path(__file__).resolve().parent.parent / 'fonts'
    return [str(here)] if here.exists() else []


def svg_to_rgb(svg, zoom=1.0):
    png = resvg_py.svg_to_bytes(svg_string=svg, zoom=zoom if zoom != 1.0 else None, font_dirs=font_dirs() or None)
    im = Image.open(io.BytesIO(bytes(png))).convert('RGB')
    return np.asarray(im)


class Post:
    """Texture: grain, vignette, flicker, per the profile's texture."""

    def __init__(self, texture, w, h, seed=1):
        self.texture = texture
        self.w, self.h = w, h
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        d = np.sqrt(((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2)
        strength = {'flat': 0.0, 'paper': 0.22, 'film': 0.32}.get(texture, 0)
        self.vig = (1 - strength * np.clip(d - 0.35, 0, None) ** 1.6)[..., None].astype(np.float32)
        r = np.random.default_rng(seed)
        amt = {'flat': 0, 'paper': 4.5, 'film': 7.5}.get(texture, 0)
        self.grains = [(r.normal(0, amt, (h, w, 1))).astype(np.float32) for _ in range(4 if texture == 'film' else 1)] if amt else []

    def __call__(self, img, i):
        if self.texture == 'flat':
            return img
        f = img.astype(np.float32) * self.vig
        if self.grains:
            f += self.grains[i % len(self.grains)]
        if self.texture == 'film':
            f *= 1 + 0.025 * math.sin(i * 1.7) * math.sin(i * 0.37)
        return np.clip(f, 0, 255).astype(np.uint8)


def _init(ep_dir, project, scale):
    global _EP, _POST
    _EP = Episode(ep_dir, project)
    _EP._scale = scale


def _frame(args):
    i, fmt, fps = args
    T = i / fps
    svg = _EP.frame_svg(T, fmt)
    img = svg_to_rgb(svg, _EP._scale)
    global _POST
    if _POST is None or _POST.w != img.shape[1] or _POST.h != img.shape[0]:
        _POST = Post(_EP.style.texture, img.shape[1], img.shape[0], _EP.seed)
    return _POST(img, i).tobytes(), img.shape[1], img.shape[0]


def render(ep_dir, fmt='16:9', quality='final', out=None, project=None, frames=None, workers=None):
    ep = Episode(ep_dir, project)
    q = {'preview': (0.5, 15), 'draft': (0.5, 30), 'final': (1.0, None)}[quality]
    scale, fps = q[0], q[1] or ep.fps
    total = int(math.ceil(ep.duration * fps))
    idx = list(range(total)) if frames is None else frames
    Wpx, Hpx = FORMATS[fmt]
    W2, H2 = int(round(Wpx * scale)), int(round(Hpx * scale))
    W2 -= W2 % 2
    H2 -= H2 % 2
    out = pathlib.Path(out) if out else ep.dir / 'out' / f'{fmt.replace(":", "x")}-{quality}.mp4'
    out.parent.mkdir(parents=True, exist_ok=True)
    cmd = [ffmpeg_exe(), '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W2}x{H2}', '-r', str(fps), '-i', '-',
           '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '18' if quality == 'final' else '24', '-preset',
           'medium' if quality == 'final' else 'veryfast', '-movflags', '+faststart', str(out)]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    workers = workers or max(1, (os.cpu_count() or 2) - 1)
    t0 = time.time()
    ctx = mp.get_context('fork' if sys.platform != 'win32' else 'spawn')
    with ctx.Pool(workers, initializer=_init, initargs=(str(ep.dir), str(ep.project), scale)) as pool:
        done = 0
        for buf, w, h in pool.imap(_frame, [(i, fmt, fps) for i in idx], chunksize=2):
            if (w, h) != (W2, H2):
                im = Image.frombytes('RGB', (w, h), buf).resize((W2, H2))
                buf = im.tobytes()
            proc.stdin.write(buf)
            done += 1
            if done % max(1, total // 10) == 0:
                print(f'  {fmt} {done}/{len(idx)} frames ({time.time() - t0:.0f}s)', flush=True)
    proc.stdin.close()
    proc.wait()
    print(f'Rendered {out} ({len(idx)} frames, {time.time() - t0:.1f}s)')
    return out


def still(ep_dir, T, fmt='16:9', scale=0.5, project=None):
    ep = Episode(ep_dir, project)
    img = svg_to_rgb(ep.frame_svg(T, fmt), scale)
    post = Post(ep.style.texture, img.shape[1], img.shape[0], ep.seed)
    return Image.fromarray(post(img, int(T * ep.fps)))
