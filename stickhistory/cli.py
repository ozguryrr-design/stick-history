"""Command line: python <skill>/run.py <command> ...  (run from the project folder)."""
import argparse
import datetime
import json
import math
import pathlib
import shutil
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
SKILL = HERE.parent


def project_dir():
    return pathlib.Path.cwd()


def ep_dir(slug):
    d = project_dir() / 'episodes' / slug
    if not d.exists():
        raise SystemExit(f'No episode "{slug}" at {d}. Create it with: run.py new {slug}')
    return d


# ---------------------------------------------------------------- setup
def cmd_init(a):
    p = project_dir()
    (p / 'episodes').mkdir(exist_ok=True)
    if not (p / 'learned.md').exists():
        (p / 'learned.md').write_text('# What this channel has learned\n\nNotes from the person after each episode. Read before every episode; '
                                      'they override the defaults.\n', encoding='utf-8')
    if not (p / 'history.json').exists():
        (p / 'history.json').write_text('[]\n', encoding='utf-8')
    prof = p / 'profile.json'
    print(f'Project ready at {p}')
    if prof.exists():
        print(f'Style profile found: {json.loads(prof.read_text(encoding="utf-8"))}')
    else:
        print('No style profile yet: ask the style questions (run.py quiz) and save the answers with run.py style ...')


def cmd_quiz(a):
    from .style import quiz
    print(json.dumps(quiz(), indent=2, ensure_ascii=False))


def cmd_style(a):
    from .style import DEFAULT_PROFILE, PALETTES, LINES, FACES, TEXTURES, CAMERA, FONTS, ENDINGS
    p = project_dir() / 'profile.json'
    prof = json.loads(p.read_text(encoding='utf-8')) if p.exists() else dict(DEFAULT_PROFILE)
    valid = {'palette': list(PALETTES) + ['surprise'], 'line': list(LINES), 'face': list(FACES), 'texture': list(TEXTURES),
             'camera': list(CAMERA), 'font': list(FONTS), 'ending': list(ENDINGS)}
    for kv in a.set or []:
        k, _, v = kv.partition('=')
        if k == 'seed':
            prof['seed'] = int(v)
            continue
        if k == 'channel':
            prof['channel'] = v
            continue
        if k.startswith('overrides.'):
            prof.setdefault('overrides', {})[k.split('.', 1)[1]] = v
            continue
        if k not in valid:
            raise SystemExit(f'Unknown setting "{k}". Settings: {", ".join(valid)}, seed, channel, overrides.<key>')
        if v not in valid[k]:
            raise SystemExit(f'"{v}" is not a {k}. Choose: {", ".join(valid[k])}')
        prof[k] = v
    if 'seed' not in prof or prof.get('seed') == 1 and not any(s.startswith('seed=') for s in (a.set or [])):
        from .svg import hash_seed
        prof['seed'] = hash_seed(prof.get('channel', ''), time.time()) % 100000
    p.write_text(json.dumps(prof, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f'Saved {p}: {json.dumps(prof, ensure_ascii=False)}')
    if a.preview:
        cmd_preview_style(a)


def cmd_preview_style(a):
    """A style sample: the same small scene in the current profile."""
    from .style import Style, load_profile
    from .render import svg_to_rgb
    from .episode import Episode
    sample = SKILL / 'examples' / 'style-sample'
    out = project_dir() / 'style-preview.png'
    ep = Episode(sample, project_dir())
    from PIL import Image
    Image.fromarray(svg_to_rgb(ep.frame_svg(1.2, '16:9'), 0.5)).save(out)
    print(f'Style preview: {out}')


def cmd_new(a):
    d = project_dir() / 'episodes' / a.slug
    (d / 'voice').mkdir(parents=True, exist_ok=True)
    (d / 'music').mkdir(exist_ok=True)
    (d / 'out').mkdir(exist_ok=True)
    if not (d / 'brief.json').exists():
        (d / 'brief.json').write_text(json.dumps({
            'topic': a.topic or '', 'event': '', 'date': '', 'place': '', 'formats': ['16:9', '9:16'], 'target_seconds': None,
            'people': [], 'clothing': {}, 'objects': [], 'architecture': [], 'landscape': '', 'avoid': [], 'facts': [], 'sources': []
        }, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f'Episode folder: {d}\n  Put the voice-over in {d / "voice"}/ (wav, mp3, m4a...), optionally the text in {d / "script.txt"}.\n'
          f'  Optional: your own music in {d / "music"}/.')


# ---------------------------------------------------------------- sound timing
def cmd_align(a):
    from .audio import align
    d = ep_dir(a.slug)
    data = align(d, a.model, a.language)
    print(f'Voice: {data["voice"]}, {data["duration"]:.2f}s, language: {data["language"] or "unknown"}, words from: {data["source"]}')
    if data['source'] == 'none':
        print('  No transcript: install faster-whisper (pip install faster-whisper) or add script.txt, then re-run align.')
    for s in data['segments']:
        span = f'w:{s["first"]}..w:{s["last"]}' if 'first' in s else ''
        print(f'  s:{s["i"]:<2} {s["start"]:6.2f}-{s["end"]:6.2f}s {span:14} {s.get("text", "")}')
    print(f'  accents (good cut/hit points): {data["accents"]}')
    if a.words:
        print('  ' + ' '.join(f'[{w["i"]}]{w["word"]}@{w["start"]:.2f}' for w in data['words']))
    print(f'Wrote {d / "words.json"}')


# ---------------------------------------------------------------- review
def _sheet(images, labels, cols, out, cell_w):
    from PIL import Image, ImageDraw, ImageFont
    if not images:
        return
    w0, h0 = images[0].size
    cw = cell_w
    ch = int(h0 * cw / w0)
    rows = math.ceil(len(images) / cols)
    pad, lab = 10, 34
    sheet = Image.new('RGB', (cols * (cw + pad) + pad, rows * (ch + lab + pad) + pad), (24, 24, 28))
    dr = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.truetype('DejaVuSans.ttf', 20)
    except Exception:
        font = ImageFont.load_default()
    for i, (im, lb) in enumerate(zip(images, labels)):
        r, c = divmod(i, cols)
        x, y = pad + c * (cw + pad), pad + r * (ch + lab + pad)
        sheet.paste(im.resize((cw, ch)), (x, y + lab))
        dr.text((x + 2, y + 6), lb, fill=(235, 235, 235), font=font)
    sheet.save(out, quality=90)
    return out


def cmd_board(a):
    from .episode import Episode
    from .render import svg_to_rgb, Post
    from PIL import Image
    d = ep_dir(a.slug)
    ep = Episode(d, project_dir())
    only = set(a.shots or [])
    outd = d / 'out' / 'board'
    outd.mkdir(parents=True, exist_ok=True)
    for fmt in _formats(a, ep):
        ims, labels = [], []
        for s in ep.shots:
            if only and s.id not in only:
                continue
            bt = s.spec.get('board_t')
            T = s.start + (float(bt) if bt is not None else s.dur * 0.6)
            img = svg_to_rgb(ep.frame_svg(T, fmt), 0.5)
            img = Post(ep.style.texture, img.shape[1], img.shape[0], ep.seed)(img, 0)
            im = Image.fromarray(img)
            im.save(outd / f'{s.id}-{fmt.replace(":", "x")}.png')
            ims.append(im)
            cam = s.spec.get('camera', {})
            camd = cam.get('move', '') + ' ' + str(cam.get('frame', '')) if isinstance(cam, dict) else f'{len(cam)} keys'
            labels.append(f'{s.id} {s.start:.1f}-{s.end:.1f}s {camd}')
        cols = 4 if fmt != '9:16' else 6
        out = d / 'out' / f'storyboard-{fmt.replace(":", "x")}.jpg'
        _sheet(ims, labels, cols, out, 460 if fmt != '9:16' else 260)
        print(f'Storyboard {fmt}: {out}')


def cmd_grid(a):
    from .episode import Episode
    from .render import svg_to_rgb
    from PIL import Image
    d = ep_dir(a.slug)
    ep = Episode(d, project_dir())
    for fmt in _formats(a, ep):
        for s in ep.shots:
            if a.shots and s.id not in a.shots:
                continue
            k = a.frames
            ims, labels = [], []
            for i in range(k):
                T = s.start + s.dur * (i + 0.5) / k
                ims.append(Image.fromarray(svg_to_rgb(ep.frame_svg(T, fmt), 0.35)))
                labels.append(f'{s.id} t={T - s.start:.2f}s')
            out = d / 'out' / f'grid-{s.id}-{fmt.replace(":", "x")}.jpg'
            _sheet(ims, labels, 4 if fmt != '9:16' else 8, out, 420 if fmt != '9:16' else 200)
            print(f'Motion grid {s.id} {fmt}: {out}')


def _formats(a, ep):
    f = getattr(a, 'format', None) or 'both'
    if f == 'both':
        return ep.spec.get('formats', ['16:9', '9:16'])
    return [f]


def cmd_check(a):
    from .check import check
    d = ep_dir(a.slug)
    problems = check(d, project_dir())
    if not problems:
        print('Check passed: no problems found.')
    for p in problems:
        print(p)
    if any(p.startswith('ERROR') for p in problems):
        sys.exit(1)


# ---------------------------------------------------------------- render, sound, master
def cmd_render(a):
    from .render import render
    from .episode import Episode
    d = ep_dir(a.slug)
    ep = Episode(d, project_dir())
    for fmt in _formats(a, ep):
        render(d, fmt, a.quality, project=project_dir(), workers=a.workers)


def cmd_sound(a):
    from .sound import build
    d = ep_dir(a.slug)
    build(d, project_dir())


def cmd_master(a):
    from .sound import master
    d = ep_dir(a.slug)
    master(d, project_dir(), a.quality, _formats(a, None) if a.format != 'both' else None)


def cmd_learn(a):
    p = project_dir()
    lp = p / 'learned.md'
    if not lp.exists():
        cmd_init(a)
    day = datetime.date.today().isoformat()
    lines = [f'\n## {day} - {a.slug}']
    for x in a.like or []:
        lines.append(f'- Keep: {x}')
    for x in a.change or []:
        lines.append(f'- Change: {x}')
    for x in a.rule or []:
        lines.append(f'- Rule: {x}')
    with lp.open('a', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')
    hp = p / 'history.json'
    hist = json.loads(hp.read_text(encoding='utf-8')) if hp.exists() else []
    d = p / 'episodes' / a.slug
    entry = {'slug': a.slug, 'date': day}
    try:
        brief = json.loads((d / 'brief.json').read_text(encoding='utf-8'))
        entry.update({k: brief.get(k) for k in ('topic', 'event', 'date', 'place')})
        entry['episode_date'] = entry.pop('date')
        entry['date'] = day
        sc = json.loads((d / 'scenes.json').read_text(encoding='utf-8'))
        moves, kinds, trans = set(), set(), set()
        for s in sc.get('shots', []):
            cam = s.get('camera', {})
            if isinstance(cam, dict):
                moves.add(cam.get('move', 'drift'))
            trans.add(s.get('transition', 'cut') if isinstance(s.get('transition', 'cut'), str) else s['transition'].get('kind'))
            for L in s.get('layers', []):
                for it in L.get('items', []):
                    kinds.add(it.get('kind'))
        entry.update({'camera_moves': sorted(moves), 'transitions': sorted(trans), 'items': sorted(k for k in kinds if k)})
    except Exception:
        pass
    hist = [h for h in hist if h.get('slug') != a.slug] + [entry]
    hp.write_text(json.dumps(hist, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f'Noted in {lp} and {hp}.')


def cmd_catalog(a):
    from .catalog import catalog
    data = catalog()
    if a.section:
        data = {a.section: data[a.section]}
    print(json.dumps(data, indent=1, ensure_ascii=False))


def main(argv=None):
    ap = argparse.ArgumentParser(prog='run.py', description='History stick-figure animation: one event, one voice-over, two formats.')
    sub = ap.add_subparsers(dest='cmd', required=True)
    sub.add_parser('init', help='Set up the project folder here').set_defaults(f=cmd_init)
    sub.add_parser('quiz', help='Print the first-run style questions').set_defaults(f=cmd_quiz)
    s = sub.add_parser('style', help='Save style answers: style --set palette=midnight line=bold ...')
    s.add_argument('--set', nargs='*')
    s.add_argument('--preview', action='store_true')
    s.set_defaults(f=cmd_style)
    s = sub.add_parser('new', help='Create an episode folder')
    s.add_argument('slug')
    s.add_argument('--topic')
    s.set_defaults(f=cmd_new)
    s = sub.add_parser('align', help='Time the voice-over (words, sentences, pauses, accents)')
    s.add_argument('slug')
    s.add_argument('--model', default='small')
    s.add_argument('--language')
    s.add_argument('--words', action='store_true', help='Print every word with its index')
    s.set_defaults(f=cmd_align)
    s = sub.add_parser('check', help='Validate scenes.json and the framing')
    s.add_argument('slug')
    s.set_defaults(f=cmd_check)
    s = sub.add_parser('board', help='Storyboard: one still per shot, both formats')
    s.add_argument('slug')
    s.add_argument('shots', nargs='*')
    s.add_argument('--format', default='both')
    s.set_defaults(f=cmd_board)
    s = sub.add_parser('grid', help='Motion grid: frames across a shot')
    s.add_argument('slug')
    s.add_argument('shots', nargs='*')
    s.add_argument('--frames', type=int, default=8)
    s.add_argument('--format', default='16:9')
    s.set_defaults(f=cmd_grid)
    s = sub.add_parser('render', help='Render video (silent)')
    s.add_argument('slug')
    s.add_argument('--quality', default='draft', choices=['preview', 'draft', 'final'])
    s.add_argument('--format', default='both')
    s.add_argument('--workers', type=int)
    s.set_defaults(f=cmd_render)
    s = sub.add_parser('sound', help='Build effects and music stems from scenes.json')
    s.add_argument('slug')
    s.set_defaults(f=cmd_sound)
    s = sub.add_parser('master', help='Mix voice, effects and music, normalise, mux into the videos')
    s.add_argument('slug')
    s.add_argument('--quality', default='final', choices=['preview', 'draft', 'final'])
    s.add_argument('--format', default='both')
    s.set_defaults(f=cmd_master)
    s = sub.add_parser('learn', help='Record the person\'s feedback for next time')
    s.add_argument('slug')
    s.add_argument('--like', nargs='*')
    s.add_argument('--change', nargs='*')
    s.add_argument('--rule', nargs='*')
    s.set_defaults(f=cmd_learn)
    s = sub.add_parser('catalog', help='Everything you can use in scenes.json')
    s.add_argument('section', nargs='?')
    s.set_defaults(f=cmd_catalog)
    a = ap.parse_args(argv)
    a.f(a)


if __name__ == '__main__':
    main()
