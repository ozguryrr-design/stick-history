"""The episode's sound: effects (automatic + written), ambience, music bed, ducking, master and mux."""
import json
import math
import pathlib
import subprocess

import numpy as np

from . import audio as A
from .episode import Episode
from .scene import FORMATS

DEFAULTS = {'auto': True, 'music': {'mood': 'epic', 'gain': -24}, 'sfx_gain': -9, 'ambience_gain': -28}


def _rms_db(x):
    return 20 * math.log10(float(np.sqrt(np.mean(x ** 2))) + 1e-9)


def _time(ep, v):
    """Absolute seconds from: 2.4, "w:12", "s:3", "S2+0.5", {"shot": "S2", "t": 0.5}."""
    if isinstance(v, dict):
        s = next(s for s in ep.shots if s.id == v['shot'])
        return s.start + float(v.get('t', 0))
    if isinstance(v, str) and v[:1] == 'S' and '+' in v:
        sid, off = v.split('+', 1)
        s = next(s for s in ep.shots if s.id == sid)
        return s.start + float(off)
    if isinstance(v, str) and v[:1] == 'S' and v[1:].isdigit():
        return next(s for s in ep.shots if s.id == v).start
    return ep.anchor(v)


def auto_events(ep):
    """Sound for what the picture already does: impacts, cannons, whips, titles, counters, crowds, water, fire."""
    ev, amb = [], []
    from .scene import parse_t
    for i, s in enumerate(ep.shots):
        sp = s.spec
        for h in sp.get('hits', []):
            ht = parse_t(h if not isinstance(h, dict) else h['t'], s.dur, ep, s.start)
            ev.append({'t': s.start + ht, 'kind': 'impact', 'gain': -4, '_auto': 'hit'})
        tr = sp.get('transition', 'cut')
        tk = tr if isinstance(tr, str) else tr.get('kind')
        if i > 0 and tk in ('whip', 'zoom', 'push'):
            ev.append({'t': s.start - 0.22, 'kind': 'whoosh', 'dur': 0.45, 'pitch': 0.7 if tk == 'zoom' else 1.0, 'gain': -6, '_auto': tk})
        if i > 0 and tk == 'flash':
            ev.append({'t': s.start, 'kind': 'impact', 'gain': -8, '_auto': 'flash'})
        kinds = set()
        for L in sp.get('layers', []):
            for it in L.get('items', []):
                k = it.get('kind')
                kinds.add(k)
                if k == 'cannon' and it.get('fire') is not None:
                    ev.append({'t': s.start + parse_t(it['fire'], s.dur, ep, s.start), 'kind': 'cannon', 'gain': -2, '_auto': 'cannon'})
                if k in ('crowd', 'army'):
                    kinds.add('cheer' if it.get('cheer') else ('march' if it.get('march') else 'crowd'))
        for tx in sp.get('text', []):
            t0 = s.start + parse_t(tx.get('t', 0), s.dur, ep, s.start)
            k = tx.get('kind', 'title')
            if k == 'title':
                ev.append({'t': t0, 'kind': 'boom', 'gain': -6, 'pitch': 0.8, '_auto': 'title'})
            elif k == 'year':
                cnt = tx.get('count', 1.2)
                for j in range(10):
                    u = j / 10
                    ev.append({'t': t0 + cnt * (1 - (1 - u) ** 3), 'kind': 'tick', 'gain': -16, '_auto': 'year'})
                ev.append({'t': t0 + cnt, 'kind': 'impact', 'gain': -6, '_auto': 'year'})
            elif k == 'label':
                ev.append({'t': t0, 'kind': 'pop', 'gain': -18, '_auto': 'label'})
            elif k == 'card':
                ev.append({'t': t0, 'kind': 'paper', 'gain': -12, '_auto': 'card'})
        for f in sp.get('fx', []):
            fk = f if isinstance(f, str) else f.get('kind')
            if fk == 'rain':
                kinds.add('rain')
            if fk == 'flash' and isinstance(f, dict):
                ev.append({'t': s.start + parse_t(f.get('t', 0), s.dur), 'kind': 'thunder', 'gain': -8, '_auto': 'flash'})
        for k, a in (('water', 'waves'), ('fire', 'fire'), ('cheer', 'cheer'), ('crowd', 'crowd'), ('march', 'march'), ('rain', 'rain')):
            if k in kinds:
                amb.append({'kind': a, 'from': s.start, 'to': s.end, 'gain': -2 if a in ('cheer', 'march') else 0, '_auto': True})
        if not any(a['from'] == s.start for a in amb):
            amb.append({'kind': 'wind', 'from': s.start, 'to': s.end, 'gain': -6 if s.tod != 'interior' else -14, '_auto': True})
    return ev, amb


def build(ep_dir, project=None):
    ep_dir = pathlib.Path(ep_dir)
    ep = Episode(ep_dir, project)
    cfg = dict(DEFAULTS)
    cfg.update(ep.spec.get('sound', {}))
    dur = ep.duration
    n = int(dur * A.SR) + 1
    rng = np.random.default_rng(ep.seed)
    events, amb = ([], [])
    if cfg.get('auto', True):
        events, amb = auto_events(ep)
    for e in cfg.get('events', []):
        e = dict(e)
        e['t'] = _time(ep, e['t'])
        events.append(e)
    for x in cfg.get('ambience', []):
        x = dict(x)
        if 'shots' in x:
            ss = [s for s in ep.shots if s.id in x['shots']]
            x['from'], x['to'] = min(s.start for s in ss), max(s.end for s in ss)
        x['from'] = _time(ep, x.get('from', 0))
        x['to'] = _time(ep, x.get('to', dur))
        # a written ambience replaces automatic ones that overlap it
        amb = [a for a in amb if not (a.get('_auto') and a['from'] < x['to'] and a['to'] > x['from'])]
        amb.append(x)
    for rm in cfg.get('mute_auto', []):
        events = [e for e in events if e.get('_auto') != rm]
        amb = [a for a in amb if not (a.get('_auto') and a['kind'] == rm)]
    # effects stem
    fx = np.zeros(n, dtype=np.float32)
    cache = {}
    for i, e in enumerate(sorted(events, key=lambda e: e['t'])):
        key = (e['kind'], e.get('dur'), e.get('pitch', 1.0), i % 3)
        if key not in cache:
            cache[key] = A.sfx(e['kind'], np.random.default_rng(ep.seed + i % 3 + hash(e['kind']) % 1000), e.get('dur'), e.get('pitch', 1.0))
        x = cache[key] * A.db(e.get('gain', 0) + cfg['sfx_gain'])
        s = int(max(0, e['t']) * A.SR)
        L = min(len(x), n - s)
        if L > 0:
            fx[s:s + L] += x[:L]
    # ambience stem (merge consecutive same-kind ranges so beds don't restart every cut)
    ab = np.zeros(n, dtype=np.float32)
    merged = []
    for a in sorted(amb, key=lambda a: (a['kind'], a['from'])):
        if merged and merged[-1]['kind'] == a['kind'] and a['from'] <= merged[-1]['to'] + 0.05:
            merged[-1]['to'] = max(merged[-1]['to'], a['to'])
        else:
            merged.append(dict(a))
    for a in merged:
        L = a['to'] - a['from']
        if L <= 0.1:
            continue
        x = A.sfx(a['kind'], np.random.default_rng(ep.seed + 7), L + 0.6)
        x = x / (np.sqrt(np.mean(x ** 2)) + 1e-9) * A.db(-20) * A.db(a.get('gain', 0) + cfg['ambience_gain'] + 20)
        s = int(a['from'] * A.SR)
        k = min(len(x), n - s)
        if k > 0:
            fx_fade = A._fade(k, 0.3)
            ab[s:s + k] += x[:k] * fx_fade
    # music
    mu = np.zeros(n, dtype=np.float32)
    mcfg = cfg.get('music')
    mfile = None
    md = ep_dir / 'music'
    if md.exists():
        for ext in ('wav', 'mp3', 'm4a', 'flac', 'ogg'):
            fl = sorted(md.glob(f'*.{ext}'))
            if fl:
                mfile = fl[0]
                break
    if mcfg is not False and mcfg is not None:
        mcfg = mcfg if isinstance(mcfg, dict) else {'mood': str(mcfg)}
        if mfile:
            x = A.read_audio(mfile)
            if len(x) < n:
                x = np.tile(x, n // len(x) + 1)
            x = x[:n] * A._fade(n, 1.0)
        else:
            x = A.music(dur, mcfg.get('mood', 'epic'), ep.seed, mcfg.get('root'), mcfg.get('instrument'))
        x = x / (np.sqrt(np.mean(x ** 2)) + 1e-9) * A.db(mcfg.get('gain', -24))
        mu[:min(n, len(x))] = x[:n]
    # duck music and ambience under the voice
    if ep.env:
        env = np.array(ep.env, dtype=np.float32)
        env = np.convolve(env, np.ones(25) / 25, mode='same')
        t = np.arange(n) / A.SR
        e = np.interp(t * ep.env_rate, np.arange(len(env)), env, right=0)
        duck = 1 - np.clip(e * 1.4, 0, 1) * cfg.get('duck', 0.55)
        mu *= duck
        ab *= 1 - (1 - duck) * 0.7
    out = ep_dir / 'out'
    out.mkdir(exist_ok=True)
    A.write_wav(out / 'sfx.wav', fx)
    A.write_wav(out / 'ambience.wav', ab)
    A.write_wav(out / 'music.wav', mu)
    print(f'Sound: {len(events)} effects, {len(merged)} ambience beds, music: {"file " + mfile.name if mfile else (mcfg or {}).get("mood", "off") if mcfg else "off"}')
    for e in sorted(events, key=lambda e: e['t'])[:60]:
        print(f'  {e["t"]:6.2f}s {e["kind"]:<10} {e.get("gain", 0):+.0f} dB {("(auto: " + e["_auto"] + ")") if e.get("_auto") else ""}')
    for a in merged:
        print(f'  bed {a["kind"]:<8} {a["from"]:.2f}-{a["to"]:.2f}s')
    print(f'Wrote {out / "sfx.wav"}, ambience.wav, music.wav')


def mixcheck(voice, other, env_rate=100, sr=A.SR):
    """Moments where effects/music come within 3 dB of the voice while it speaks."""
    hop = sr // env_rate
    k = min(len(voice), len(other)) // hop
    v = np.sqrt(np.mean(voice[:k * hop].reshape(k, hop) ** 2, axis=1) + 1e-12)
    o = np.sqrt(np.mean(other[:k * hop].reshape(k, hop) ** 2, axis=1) + 1e-12)
    speaking = v > np.percentile(v, 60) * 0.5
    bad = speaking & (20 * np.log10(o / v) > -3)
    spans, start = [], None
    for i, b in enumerate(bad):
        if b and start is None:
            start = i
        if not b and start is not None:
            if i - start > 8:
                spans.append((start / env_rate, i / env_rate))
            start = None
    return spans


def master(ep_dir, project=None, quality='final', formats=None):
    ep_dir = pathlib.Path(ep_dir)
    ep = Episode(ep_dir, project)
    out = ep_dir / 'out'
    if not (out / 'sfx.wav').exists():
        build(ep_dir, project)
    n = int(ep.duration * A.SR) + 1
    stems = {}
    for name in ('sfx', 'ambience', 'music'):
        p = out / f'{name}.wav'
        x = A.read_audio(p) if p.exists() else np.zeros(n, np.float32)
        stems[name] = np.pad(x, (0, max(0, n - len(x))))[:n]
    vp = A.find_voice(ep_dir)
    voice = np.zeros(n, np.float32)
    if vp:
        v = A.read_audio(vp)
        v = v / (np.sqrt(np.mean(v[np.abs(v) > 0.01] ** 2)) + 1e-9) * A.db(-18) if np.any(np.abs(v) > 0.01) else v
        voice[:min(n, len(v))] = v[:n]
    bed = stems['sfx'] + stems['ambience'] + stems['music']
    mix = voice + bed
    spans = mixcheck(voice, bed) if vp else []
    peak = np.max(np.abs(mix)) or 1
    if peak > 0.98:
        mix = mix / peak * 0.98
    A.write_wav(out / 'mix.wav', np.stack([mix, mix], axis=1))
    # two-pass loudness normalisation to -14 LUFS, -1 dBTP
    ff = A.ffmpeg()
    r = subprocess.run([ff, '-hide_banner', '-nostats', '-i', str(out / 'mix.wav'), '-af', 'loudnorm=I=-14:TP=-1:LRA=11:print_format=json',
                        '-f', 'null', '-'], capture_output=True, text=True, encoding='utf-8', errors='ignore')
    js = r.stderr[r.stderr.rfind('{'): r.stderr.rfind('}') + 1]
    m = json.loads(js)
    filt = (f'loudnorm=I=-14:TP=-1:LRA=11:measured_I={m["input_i"]}:measured_TP={m["input_tp"]}:measured_LRA={m["input_lra"]}:'
            f'measured_thresh={m["input_thresh"]}:offset={m["target_offset"]}:linear=true')
    subprocess.run([ff, '-y', '-v', 'error', '-i', str(out / 'mix.wav'), '-af', filt, '-ar', '48000', str(out / 'master.wav')], check=True)
    loud, pk = A.lufs(out / 'master.wav')
    fmts = formats or ep.spec.get('formats', ['16:9', '9:16'])
    files = []
    from .render import render
    for fmt in fmts:
        vid = out / f'{fmt.replace(":", "x")}-{quality}.mp4'
        if not vid.exists():
            render(ep_dir, fmt, quality, project=project)
        final = out / f'{ep_dir.name}-{fmt.replace(":", "x")}.mp4'
        subprocess.run([ff, '-y', '-v', 'error', '-i', str(vid), '-i', str(out / 'master.wav'), '-c:v', 'copy', '-c:a', 'aac', '-b:a', '256k',
                        '-shortest', '-movflags', '+faststart', str(final)], check=True)
        files.append(str(final))
    report = {'duration': round(ep.duration, 2), 'loudness_lufs': loud, 'true_peak_db': pk, 'formats': fmts, 'files': files,
              'shots': len(ep.shots), 'cuts_per_minute': round(len(ep.shots) / ep.duration * 60, 1),
              'voice_masked': [[round(a, 2), round(b, 2)] for a, b in spans]}
    (out / 'report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))
    if spans:
        print('Warning: effects/music crowd the voice at ' + ', '.join(f'{a:.2f}-{b:.2f}s' for a, b in spans) +
              ' (lower those events, move hits into pauses, or lower "sfx_gain").')
