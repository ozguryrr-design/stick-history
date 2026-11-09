"""Sound: read the voice, find its timing, synthesise effects and a music bed, mix and master.

Nothing here calls a service. The voice is the user's file; effects and music are generated from code (numpy), so
every channel's sound is its own (seeded) and free of licences. A user's own music file in the episode's music/ folder
replaces the generated bed.
"""
import json
import math
import pathlib
import subprocess
import wave

import numpy as np

SR = 44100


def ffmpeg():
    from .render import ffmpeg_exe
    return ffmpeg_exe()


def read_audio(path, sr=SR):
    raw = subprocess.run([ffmpeg(), '-v', 'error', '-i', str(path), '-f', 'f32le', '-ac', '1', '-ar', str(sr), '-'],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32).copy()


def write_wav(path, x, sr=SR):
    x = np.asarray(x, dtype=np.float32)
    if x.ndim == 1:
        x = x[:, None]
    pcm = (np.clip(x, -1, 1) * 32767).astype('<i2')
    with wave.open(str(path), 'wb') as w:
        w.setnchannels(pcm.shape[1])
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm.tobytes())


def find_voice(ep_dir):
    d = pathlib.Path(ep_dir) / 'voice'
    if not d.exists():
        return None
    for ext in ('wav', 'mp3', 'm4a', 'flac', 'ogg', 'aac', 'opus', 'webm'):
        files = sorted(d.glob(f'*.{ext}'))
        if files:
            return files[0]
    return None


# ---------------------------------------------------------------- alignment
def envelope(x, sr=SR, rate=100):
    hop = sr // rate
    k = len(x) // hop
    e = np.sqrt(np.mean(x[:k * hop].reshape(k, hop) ** 2, axis=1) + 1e-12)
    peak = np.percentile(e, 98) or 1
    return np.clip(e / peak, 0, 1)


def segments(env, rate=100, min_sil=0.22, min_seg=0.25):
    """Speech segments split at pauses (relative threshold, so any language, any level)."""
    floor = np.percentile(env, 15)
    thr = floor + (np.percentile(env, 70) - floor) * 0.18
    speech = env > thr
    segs, start, sil = [], None, 0
    for i, s in enumerate(speech):
        if s:
            if start is None:
                start = i
            sil = 0
        elif start is not None:
            sil += 1
            if sil >= min_sil * rate:
                end = i - sil + 1
                if (end - start) / rate >= min_seg:
                    segs.append([start / rate, end / rate])
                start, sil = None, 0
    if start is not None:
        segs.append([start / rate, len(env) / rate])
    return segs


def accents(env, rate=100, n=12):
    """Loudest onsets: good places for cuts and hits."""
    d = np.diff(env, prepend=env[0])
    sm = np.convolve(d, np.ones(5) / 5, mode='same')
    idx = []
    order = np.argsort(-sm)
    for i in order:
        if sm[i] <= 0:
            break
        if all(abs(i - j) > rate * 0.4 for j in idx):
            idx.append(int(i))
        if len(idx) >= n:
            break
    return sorted(round(i / rate, 2) for i in idx)


def transcribe(path, model_size='small', language=None):
    """Word timings with faster-whisper (optional dependency). Returns (language, words) or (None, None)."""
    if not model_size or model_size == 'none':
        return None, None
    try:
        from faster_whisper import WhisperModel
        model = WhisperModel(model_size, device='auto', compute_type='int8')
        segs, info = model.transcribe(str(path), word_timestamps=True, language=language, vad_filter=True)
        words = []
        for s in segs:
            for w in s.words or []:
                words.append({'word': w.word.strip(), 'start': round(w.start, 3), 'end': round(w.end, 3)})
        return info.language, words
    except Exception as e:
        print(f'  Note: Whisper transcription skipped ({e}); using pause/script alignment.')
        return None, None


def spread_script(text, segs):
    """No ASR: spread the script's words over the speech segments, matching script lines to pause segments when possible."""
    import re
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    if not lines:
        return []
    if not segs:
        segs = [[0.0, max(3.0, len(text.split()) * 0.4)]]
    words = []
    if len(lines) == len(segs):
        pairs = list(zip(lines, segs))
    else:
        # group segments across lines proportionally by character length
        total_c = sum(len(l) for l in lines) or 1
        t0, t1 = segs[0][0], segs[-1][1]
        span = t1 - t0
        pairs, cur = [], t0
        for l in lines:
            d = span * (len(l) / total_c)
            pairs.append((l, [cur, cur + d - 0.15]))
            cur += d
    for line_text, (s, e) in pairs:
        toks = line_text.split()
        if not toks:
            continue
        tc = sum(len(t) + 1 for t in toks) or 1
        dur_seg = max(0.2, e - s)
        cur_t = s
        for j, tok in enumerate(toks):
            w_dur = (len(tok) + 1) / tc * dur_seg
            words.append({
                'word': tok,
                'start': round(cur_t, 3),
                'end': round(cur_t + w_dur, 3),
                '_line_end': (j == len(toks) - 1),
            })
            cur_t += w_dur
    return words


def match_script(script, asr_words):
    """Replace ASR spellings with the script's words where they line up (keeps ASR timing)."""
    import difflib
    import re
    def norm(w):
        return re.sub(r'[^\w]', '', w.lower())
    sw = script.split()
    a = [norm(w['word']) for w in asr_words]
    b = [norm(w) for w in sw]
    sm = difflib.SequenceMatcher(a=a, b=b, autojunk=False)
    out = [dict(w) for w in asr_words]
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag in ('equal', 'replace') and (i2 - i1) == (j2 - j1):
            for k in range(i2 - i1):
                out[i1 + k]['word'] = sw[j1 + k]
    return out


def align(ep_dir, model_size='small', language=None):
    ep_dir = pathlib.Path(ep_dir)
    vp = find_voice(ep_dir)
    if not vp:
        raise SystemExit(f'No voice file in {ep_dir / "voice"}/ (wav, mp3, m4a, flac, ogg).')
    x = read_audio(vp)
    dur = len(x) / SR
    env = envelope(x)
    segs = segments(env)
    script_p = ep_dir / 'script.txt'
    script = script_p.read_text(encoding='utf-8').strip() if script_p.exists() else ''
    lang, words = transcribe(vp, model_size, language)
    source = 'asr'
    if words and script:
        words = match_script(script, words)
        source = 'asr+script'
    elif not words and script:
        words = spread_script(script, segs)
        source = 'script-estimate'
    elif not words:
        words = []
        source = 'none'
    # sentence segments: from script line breaks if present, else punctuation/pauses
    sentences = []
    if words:
        has_line_end = any(w.get('_line_end') for w in words)
        cur = None
        for i, w in enumerate(words):
            if cur is None:
                cur = {'start': w['start'], 'first': i, 'text': ''}
            cur['text'] += (' ' if cur['text'] else '') + w['word']
            gap = words[i + 1]['start'] - w['end'] if i + 1 < len(words) else 9
            end_here = w.get('_line_end', False) if has_line_end else (w['word'][-1:] in '.!?…' or gap > 0.45)
            if end_here:
                cur.update({'end': w['end'], 'last': i})
                sentences.append(cur)
                cur = None
        if cur:
            cur.update({'end': words[-1]['end'], 'last': len(words) - 1})
            sentences.append(cur)
        for w in words:
            w.pop('_line_end', None)
    else:
        sentences = [{'start': s, 'end': e, 'text': ''} for s, e in segs]
    data = {
        'voice': vp.name, 'duration': round(dur, 3), 'language': lang, 'source': source,
        'words': [dict(w, i=i) for i, w in enumerate(words)],
        'segments': [dict(s, i=i) for i, s in enumerate(sentences)],
        'pauses': [[round(a, 2), round(b, 2)] for (_, a), (b, _) in zip(segs, segs[1:])],
        'accents': accents(env),
        'envelope_rate': 100, 'envelope': [round(float(v), 3) for v in env],
    }
    (ep_dir / 'words.json').write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
    return data


# ---------------------------------------------------------------- synthesis helpers
def _t(d):
    return np.arange(int(d * SR)) / SR


def _env(n, a=0.005, d=0.3, curve=4.0):
    t = np.arange(n) / SR
    att = np.clip(t / max(a, 1e-4), 0, 1)
    dec = np.exp(-np.maximum(t - a, 0) * curve / max(d, 1e-3))
    return att * dec


def _noise(n, rng):
    return rng.standard_normal(n).astype(np.float32)


def _lp(x, cutoff):
    """One-pole low-pass (cutoff Hz or an array of Hz)."""
    c = np.broadcast_to(np.asarray(cutoff, dtype=np.float64), x.shape)
    a = np.exp(-2 * np.pi * c / SR)
    y = np.empty_like(x)
    acc = 0.0
    for i in range(len(x)):
        acc = (1 - a[i]) * x[i] + a[i] * acc
        y[i] = acc
    return y


def _lp_fast(x, cutoff):
    """Fixed-cutoff low-pass via FFT (fast)."""
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    H = 1 / np.sqrt(1 + (f / cutoff) ** 4)
    return np.fft.irfft(X * H, len(x)).astype(np.float32)


def _bp_fast(x, lo, hi):
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    H = (1 / np.sqrt(1 + (f / hi) ** 4)) * (1 / np.sqrt(1 + (lo / np.maximum(f, 1)) ** 4))
    return np.fft.irfft(X * H, len(x)).astype(np.float32)


def _sweep_filter(x, f0, f1):
    """Time-varying low-pass by blocks (cheap)."""
    out = np.zeros_like(x)
    blocks = 24
    L = len(x) // blocks + 1
    for b in range(blocks):
        s, e = b * L, min(len(x), (b + 1) * L + 512)
        if s >= len(x):
            break
        fc = f0 + (f1 - f0) * (b / (blocks - 1))
        seg = _lp_fast(x[s:e], max(60, fc))
        w = np.ones(e - s)
        if b > 0:
            w[:512] = np.linspace(0, 1, min(512, e - s))
        out[s:e] = out[s:e] * (1 - w) + seg * w
    return out


def _norm(x, peak=0.9):
    m = np.max(np.abs(x)) or 1
    return (x / m * peak).astype(np.float32)


def _ks(freq, dur, rng, bright=0.5, decay=0.996):
    """Karplus-Strong plucked string (computed a period at a time)."""
    n = int(dur * SR)
    p = max(2, int(SR / freq))
    buf = rng.uniform(-1, 1, p).astype(np.float32)
    buf = _lp_fast(np.tile(buf, 4), 2000 + bright * 6000)[:p]
    blocks = [buf]
    total = p
    while total < n:
        prev = blocks[-1]
        nxt = decay * 0.5 * (prev + np.roll(prev, -1))
        blocks.append(nxt.astype(np.float32))
        total += p
    return np.concatenate(blocks)[:n]


# ---------------------------------------------------------------- effects
def sfx(kind, rng, dur=None, pitch=1.0):
    """One effect as a mono float array."""
    k = kind
    if k == 'whoosh':
        d = dur or 0.45
        x = _noise(int(d * SR), rng)
        x = _sweep_filter(x, 300 * pitch, 3500 * pitch) * np.sin(np.linspace(0, np.pi, len(x))) ** 2
        return _norm(x, 0.7)
    if k in ('boom', 'impact'):
        d = dur or 1.6
        t = _t(d)
        f = 55 * pitch * np.exp(-t * 3) + 30
        body = np.sin(2 * np.pi * np.cumsum(f) / SR) * _env(len(t), 0.002, d * 0.5, 3)
        crack = _lp_fast(_noise(len(t), rng), 1800) * _env(len(t), 0.001, 0.25, 6)
        return _norm(body * 1.0 + crack * 0.5, 0.95)
    if k == 'cannon':
        d = dur or 2.4
        t = _t(d)
        crack = _noise(len(t), rng) * _env(len(t), 0.0005, 0.08, 6)
        body = np.sin(2 * np.pi * np.cumsum(48 * pitch * np.exp(-t * 2) + 25) / SR) * _env(len(t), 0.002, 1.2, 3)
        rumble = _lp_fast(_noise(len(t), rng), 200) * _env(len(t), 0.02, d, 2.5)
        return _norm(crack * 0.6 + body + rumble * 1.5, 0.95)
    if k in ('gunshot', 'musket'):
        d = dur or 0.9
        t = _t(d)
        crack = _noise(len(t), rng) * _env(len(t), 0.0003, 0.05, 7)
        tail = _lp_fast(_noise(len(t), rng), 900) * _env(len(t), 0.003, d * 0.6, 4)
        return _norm(crack + tail * 0.8, 0.9)
    if k in ('hit', 'thud', 'punch'):
        d = dur or 0.35
        t = _t(d)
        body = np.sin(2 * np.pi * 90 * pitch * t * np.exp(-t * 8)) * _env(len(t), 0.001, 0.15, 5)
        return _norm(body + _lp_fast(_noise(len(t), rng), 1200) * _env(len(t), 0.001, 0.05, 6) * 0.6, 0.85)
    if k in ('clang', 'sword'):
        d = dur or 1.2
        t = _t(d)
        x = np.zeros(len(t))
        for f, a in ((1830, 1), (2710, 0.6), (4150, 0.4), (5530, 0.25), (930, 0.3)):
            x += a * np.sin(2 * np.pi * f * pitch * t + rng.random() * 6) * np.exp(-t * (3 + f / 1200))
        x += _noise(len(t), rng) * _env(len(t), 0.0005, 0.03, 6) * 0.5
        if k == 'sword':
            sw = sfx('whoosh', rng, 0.25, 1.6)
            x = np.concatenate([sw * 0.6, x[: max(0, len(x) - len(sw))]]) if len(x) > len(sw) else x
        return _norm(x, 0.7)
    if k == 'bell':
        d = dur or 3.5
        t = _t(d)
        x = np.zeros(len(t))
        base = 220 * pitch
        for r, a in ((0.5, 0.6), (1, 1), (1.19, 0.5), (1.5, 0.4), (2, 0.35), (2.74, 0.2), (3.0, 0.15)):
            x += a * np.sin(2 * np.pi * base * r * t) * np.exp(-t * (0.6 + r * 0.5))
        return _norm(x * _env(len(t), 0.002, d, 1.5), 0.7)
    if k in ('drum', 'war_drum'):
        d = dur or 0.9
        t = _t(d)
        f = 70 * pitch * (1 + 0.6 * np.exp(-t * 30))
        x = np.sin(2 * np.pi * np.cumsum(f) / SR) * _env(len(t), 0.002, 0.45, 4)
        x += _lp_fast(_noise(len(t), rng), 500) * _env(len(t), 0.001, 0.08, 5) * 0.4
        return _norm(x, 0.9)
    if k == 'horn':
        d = dur or 2.2
        t = _t(d)
        f = 110 * pitch * (1 + 0.004 * np.sin(2 * np.pi * 5 * t))
        ph = 2 * np.pi * np.cumsum(f) / SR
        saw = sum(np.sin(ph * h) / h for h in range(1, 12))
        a = np.clip(t / 0.25, 0, 1) * np.clip((d - t) / 0.4, 0, 1)
        return _norm(_lp_fast(saw * a, 1200), 0.6)
    if k == 'tick':
        d = dur or 0.08
        t = _t(d)
        return _norm(np.sin(2 * np.pi * 2500 * pitch * t) * _env(len(t), 0.0005, 0.02, 6), 0.5)
    if k == 'pop':
        d = dur or 0.15
        t = _t(d)
        return _norm(np.sin(2 * np.pi * (400 + 900 * np.exp(-t * 40)) * pitch * t) * _env(len(t), 0.001, 0.06, 5), 0.6)
    if k in ('paper', 'scroll'):
        d = dur or 0.8
        n = int(d * SR)
        x = _bp_fast(_noise(n, rng), 1500, 7000)
        am = np.abs(_lp_fast(_noise(n, rng), 18))
        return _norm(x * am / (am.max() or 1) * np.sin(np.linspace(0, np.pi, n)), 0.45)
    if k == 'riser':
        d = dur or 1.6
        t = _t(d)
        x = _sweep_filter(_noise(len(t), rng), 200, 6000) * (t / d) ** 2
        x += np.sin(2 * np.pi * np.cumsum(200 + 600 * (t / d) ** 2) / SR) * (t / d) ** 2 * 0.3
        return _norm(x, 0.6)
    if k in ('crowd', 'murmur', 'cheer', 'battle'):
        d = dur or 4.0
        n = int(d * SR)
        x = _bp_fast(_noise(n, rng), 250, 2200)
        am = 0.6 + 0.4 * _lp_fast(_noise(n, rng), 3) / 0.05
        y = x * np.clip(am, 0.2, 1.4)
        if k == 'cheer':
            y *= np.clip(np.linspace(0.3, 1.4, n), 0, 1.4)
            y += _bp_fast(_noise(n, rng), 800, 3500) * 0.5 * np.linspace(0, 1, n)
        if k == 'battle':
            for _ in range(int(d * 3)):
                s = rng.integers(0, max(1, n - SR))
                c = sfx('clang', rng, 0.6, rng.uniform(0.8, 1.3)) * rng.uniform(0.1, 0.35)
                y[s:s + len(c)] += c[: n - s]
        return _norm(y * _fade(n), 0.6)
    if k == 'wind':
        d = dur or 6.0
        n = int(d * SR)
        x = _lp_fast(_noise(n, rng), 500)
        am = 0.6 + 0.4 * np.sin(2 * np.pi * np.cumsum(0.12 + 0.1 * np.abs(_lp_fast(_noise(n, rng), 1))) / SR)
        return _norm(x * am * _fade(n), 0.5)
    if k in ('fire', 'crackle'):
        d = dur or 5.0
        n = int(d * SR)
        x = _lp_fast(_noise(n, rng), 700) * 0.4
        for _ in range(int(d * 18)):
            s = rng.integers(0, n - 2000)
            L = rng.integers(200, 1500)
            x[s:s + L] += _noise(L, rng) * np.exp(-np.arange(L) / (L / 5)) * rng.uniform(0.3, 1)
        return _norm(x * _fade(n), 0.5)
    if k in ('waves', 'sea'):
        d = dur or 8.0
        t = _t(d)
        x = _lp_fast(_noise(len(t), rng), 900)
        am = 0.35 + 0.65 * (0.5 + 0.5 * np.sin(2 * np.pi * t / 4.2)) ** 2
        return _norm(x * am * _fade(len(t)), 0.5)
    if k == 'rain':
        d = dur or 6.0
        n = int(d * SR)
        return _norm(_bp_fast(_noise(n, rng), 800, 9000) * _fade(n), 0.4)
    if k == 'thunder':
        d = dur or 4.0
        t = _t(d)
        x = _lp_fast(_noise(len(t), rng), 300) * _env(len(t), 0.05, d, 2)
        x += _noise(len(t), rng) * _env(len(t), 0.001, 0.15, 5) * 0.3
        return _norm(x, 0.9)
    if k in ('gallop', 'horses'):
        d = dur or 3.0
        n = int(d * SR)
        x = np.zeros(n)
        step = 0.36 / pitch
        tt = 0.0
        while tt < d - 0.2:
            for off in (0, 0.07, 0.14):
                s = int((tt + off) * SR)
                h = sfx('hit', rng, 0.12, 1.4) * 0.6
                x[s:s + len(h)] += h[: n - s]
            tt += step
        return _norm(x * _fade(n), 0.7)
    if k in ('steps', 'march'):
        d = dur or 3.0
        n = int(d * SR)
        x = np.zeros(n)
        step = 0.5 / pitch
        tt = 0.0
        while tt < d - 0.1:
            s = int(tt * SR)
            h = _lp_fast(sfx('hit', rng, 0.1, 1.8), 2500) * (0.9 if k == 'march' else 0.4)
            x[s:s + len(h)] += h[: n - s]
            tt += step
        return _norm(x * _fade(n), 0.7)
    if k == 'splash':
        d = dur or 1.0
        n = int(d * SR)
        return _norm(_bp_fast(_noise(n, rng), 400, 6000) * _env(n, 0.005, 0.5, 4), 0.6)
    if k == 'explosion':
        b = sfx('boom', rng, dur or 2.5, 0.7)
        return _norm(b + sfx('crackle', rng, len(b) / SR)[: len(b)] * 0.3, 0.95)
    if k == 'coins':
        d = dur or 0.8
        n = int(d * SR)
        x = np.zeros(n)
        for _ in range(8):
            s = rng.integers(0, n // 2)
            c = sfx('clang', rng, 0.3, rng.uniform(2, 3)) * 0.3
            x[s:s + len(c)] += c[: n - s]
        return _norm(x, 0.5)
    if k == 'door':
        d = dur or 1.2
        t = _t(d)
        creak = np.sin(2 * np.pi * np.cumsum(180 + 60 * np.sin(2 * np.pi * 3 * t)) / SR) * _lp_fast(np.abs(_noise(len(t), rng)), 40) * 3
        return _norm(creak * np.clip(t / 0.1, 0, 1) + sfx('thud', rng, d)[: len(t)] * (t > d * 0.8), 0.5)
    if k == 'quill':
        d = dur or 1.0
        n = int(d * SR)
        x = _bp_fast(_noise(n, rng), 3000, 9000) * (0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 6 * np.arange(n) / SR)))
        return _norm(x * _fade(n), 0.25)
    if k == 'typewriter':
        d = dur or 1.5
        n = int(d * SR)
        x = np.zeros(n)
        tt = 0.0
        while tt < d - 0.05:
            s = int(tt * SR)
            c = sfx('tick', rng, 0.04, rng.uniform(0.4, 0.6))
            x[s:s + len(c)] += c[: n - s]
            tt += rng.uniform(0.07, 0.16)
        return _norm(x, 0.5)
    if k == 'engine':
        d = dur or 4.0
        t = _t(d)
        f = 40 * pitch
        x = sum(np.sin(2 * np.pi * f * h * t) / h for h in range(1, 8)) * (1 + 0.3 * np.sin(2 * np.pi * 9 * t))
        return _norm(_lp_fast(x, 600) * _fade(len(t)), 0.5)
    if k == 'heartbeat':
        d = dur or 2.0
        n = int(d * SR)
        x = np.zeros(n)
        for s0 in np.arange(0, d - 0.3, 0.85):
            for off, a in ((0, 1), (0.22, 0.7)):
                h = sfx('drum', rng, 0.3, 0.6) * a
                s = int((s0 + off) * SR)
                x[s:s + len(h)] += h[: n - s]
        return _norm(x, 0.8)
    raise ValueError(f'Unknown sound "{kind}". Known: {", ".join(SFX_KINDS)}')


SFX_KINDS = ['whoosh', 'boom', 'impact', 'cannon', 'gunshot', 'musket', 'hit', 'thud', 'punch', 'clang', 'sword', 'bell',
             'drum', 'war_drum', 'horn', 'tick', 'pop', 'paper', 'scroll', 'riser', 'crowd', 'murmur', 'cheer', 'battle',
             'wind', 'fire', 'crackle', 'waves', 'sea', 'rain', 'thunder', 'gallop', 'horses', 'steps', 'march', 'splash',
             'explosion', 'coins', 'door', 'quill', 'typewriter', 'engine', 'heartbeat']


def _fade(n, f=0.15):
    k = min(n // 3, int(f * SR))
    w = np.ones(n)
    if k:
        w[:k] = np.linspace(0, 1, k)
        w[-k:] = np.linspace(1, 0, k)
    return w


# ---------------------------------------------------------------- music
MODES = {
    'minor': [0, 2, 3, 5, 7, 8, 10], 'major': [0, 2, 4, 5, 7, 9, 11], 'dorian': [0, 2, 3, 5, 7, 9, 10],
    'phrygian': [0, 1, 3, 5, 7, 8, 10], 'hijaz': [0, 1, 4, 5, 7, 8, 10], 'pentatonic': [0, 2, 4, 7, 9, 12, 14],
    'harmonic_minor': [0, 2, 3, 5, 7, 8, 11],
}
MOODS = {
    #            mode,      bpm, progression (scale degrees), drums, brightness
    'epic': ('minor', 92, [0, 5, 3, 4], True, 0.6),
    'tense': ('phrygian', 100, [0, 1, 0, 6], True, 0.4),
    'calm': ('major', 72, [0, 4, 5, 3], False, 0.5),
    'sad': ('minor', 64, [0, 3, 5, 4], False, 0.35),
    'mystery': ('harmonic_minor', 70, [0, 5, 1, 4], False, 0.3),
    'triumph': ('major', 104, [0, 3, 4, 0], True, 0.7),
    'eastern': ('hijaz', 88, [0, 1, 0, 6], True, 0.5),
    'march': ('minor', 112, [0, 4, 0, 4], True, 0.55),
}


def music(dur, mood='epic', seed=1, root=None, instrument=None):
    rng = np.random.default_rng(seed)
    mode, bpm, prog, drums, bright = MOODS.get(mood, MOODS['epic'])
    scale = MODES[mode]
    root = root or (40 + int(rng.integers(0, 7)))  # MIDI note, E2..A#2
    beat = 60 / bpm
    bar = beat * 4
    n = int((dur + 1) * SR)
    out = np.zeros(n, dtype=np.float32)
    def hz(m):
        return 440 * 2 ** ((m - 69) / 12)
    def deg(d, octave=0):
        return root + scale[d % len(scale)] + 12 * (d // len(scale) + octave)
    bars = int(dur / bar) + 2
    t_bar = np.arange(int(bar * SR)) / SR
    inst = instrument or ('oud' if mode == 'hijaz' else 'harp')
    for b in range(bars):
        d = prog[b % len(prog)]
        s = int(b * bar * SR)
        # pad: three detuned voices, low-passed
        chord = [deg(d), deg(d + 2), deg(d + 4), deg(d, 1)]
        pad = np.zeros(len(t_bar))
        for m in chord:
            for det in (-0.12, 0.12):
                pad += np.sin(2 * np.pi * hz(m + 12 + det) * t_bar) + 0.3 * np.sin(2 * np.pi * hz(m + 24 + det) * t_bar)
        pad *= 0.5 - 0.5 * np.cos(2 * np.pi * np.clip(t_bar / bar, 0, 1))
        seg = out[s:s + len(pad)]
        seg += (pad[:len(seg)] * 0.035).astype(np.float32)
        # bass on beats 1 and 3
        for k in (0, 2):
            bs = s + int(k * beat * SR)
            L = int(beat * 1.8 * SR)
            tt = np.arange(L) / SR
            bass = np.sin(2 * np.pi * hz(deg(d, -1)) * tt) * np.exp(-tt * 2.5)
            out[bs:bs + L] += (bass[: max(0, n - bs)] * 0.22).astype(np.float32)
        # plucked arpeggio
        if b > 0 or True:
            for k in range(8):
                if rng.random() < 0.82:
                    m = chord[int(rng.integers(0, len(chord)))] + 12
                    ps = s + int(k * beat / 2 * SR)
                    note = _ks(hz(m), beat * 1.5, rng, bright, 0.994 if inst == 'harp' else 0.990)
                    if inst == 'oud':
                        note = note * (1 + 0.0 * np.arange(len(note)))
                    out[ps:ps + len(note)] += (note[: max(0, n - ps)] * 0.12).astype(np.float32)
        if drums:
            for k in range(4):
                ds = s + int(k * beat * SR)
                if k in (0, 2) or rng.random() < 0.25:
                    dr = sfx('drum', rng, 0.6, 0.8 if k == 0 else 1.0) * (0.35 if k == 0 else 0.22)
                    out[ds:ds + len(dr)] += dr[: max(0, n - ds)]
    out = out[: int(dur * SR)]
    return _norm(out * _fade(len(out), 1.0), 0.8)


# ---------------------------------------------------------------- mix
def lufs(path):
    r = subprocess.run([ffmpeg(), '-hide_banner', '-nostats', '-i', str(path), '-af', 'ebur128=peak=true', '-f', 'null', '-'],
                       capture_output=True, text=True, encoding='utf-8', errors='ignore')
    import re
    i = re.findall(r'I:\s+(-?[\d.]+) LUFS', r.stderr)
    p = re.findall(r'Peak:\s+(-?[\d.]+) dBFS', r.stderr)
    return (float(i[-1]) if i else None), (float(p[-1]) if p else None)


def db(x):
    return 10 ** (x / 20)
