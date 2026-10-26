#!/usr/bin/env python3
"""Crop question statements and official solutions out of the exam PDFs.

Author tool only (the site itself has no build step).
Usage: python3 tools/extract.py <exam> <q> [<exam> <q> ...]   (e.g. 26spA 3)
       python3 tools/extract.py --chapter N    (all questions of data/selection.json chapter N)
Writes img/q/<exam>-qNN.png and img/sol/<exam>-qNN.png.
"""
import json, os, re, subprocess, sys, tempfile
import pdfplumber
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXAM = os.path.join(ROOT, 'exam')
DPI = 200

# exam key -> (pdf with statements, pdf with solutions)
def _f(n): return os.path.join(EXAM, n)
FILES = {
    '21spA': ('114075-2021spA+sol.pdf',) * 2,
    '21spB': ('114075-2021spB+sol.pdf',) * 2,
    '22spA': ('114075-2022spAsol.pdf',) * 2,
    '22spB': ('114075-2022spB+sol.pdf',) * 2,
    '22wnA': ('114075-2022wnA+sol.pdf',) * 2,
    '22wnB': ('114075-2022wnB+sol.pdf',) * 2,
    '22wnC': ('114075-2022wnC+sol.pdf',) * 2,
    '23spA': ('114075-2023spAsol.pdf',) * 2,
    '23spB': ('114075-2023spBsol.pdf',) * 2,
    '23wnA': ('114075-2023wnA.pdf', '114075-2023wnAsol.pdf'),
    '23wnB': ('114075-2023wnB+sol.pdf',) * 2,
    '24spA': ('114075-2024spA+sol.pdf',) * 2,
    '24spB': ('114075-2024spB+sol.pdf',) * 2,
    '24spC': ('114075-2024spC+sol.pdf',) * 2,
    '24wnA': ('114075-2024wnA+sol.pdf',) * 2,
    '24wnB': ('114075-2024wnBsol.pdf',) * 2,
    '25spA': ('114075-2025spAsol.pdf',) * 2,
    '25spB': ('114075-2025spBsol.pdf',) * 2,
    '25wnA': ('114075-2025wnA+sol.pdf',) * 2,
    '25wnB': ('114075-2025wnB+sol.pdf',) * 2,
    '26wnA': ('114075-2026wnA+sol.pdf',) * 2,
    '26wnB': ('114075-2026wnB+sol.pdf',) * 2,
    '26wnC': ('114075-2026wnC+sol.pdf',) * 2,
    '26spA': ('פתרון- פיסיקה 2ממ- מועד א- אביב תשפו- להעלאה למודל.pdf',) * 2,
    '26spB': ('פתרון- פיסיקה 2ממ- מועד ב- אביב תשפו- להעלאה למודל.pdf',) * 2,
    '26spM': ('מועד מילואים- 2ממ- אביב תשפו- פתרון- להעלות למודל.pdf',) * 2,
}

HDR = re.compile(r'(?:^|\s)[:\-]?(\d{1,2})\s*[:\-]?\s*הלאש|שאלה\s*[:\-]?\s*(\d{1,2})(?!\d)')
SOL = re.compile(r'ןורתפ|פתרון')
TITLE = re.compile(r'דעומ|מועד|הקיזיפ|הקיסיפ|פיזיקה|פיסיקה|114075|1140075')


def clean(t):
    return re.sub(r'[‎‏‪-‮]', '', t).strip()


def page_lines(pdf):
    """Per page: list of (top, bottom, text) for content lines (title/footer removed),
    plus the vertical extent of the page content (text + graphics)."""
    out = []
    for p in pdf.pages:
        raw = p.extract_text_lines()
        lines = [(l['top'], l['bottom'], clean(l['text'])) for l in raw]
        pagenos = [(l['x0'], l['top'], l['x1'], l['bottom']) for l in raw
                   if (l['top'] > p.height - 95 or l['top'] < 75) and re.fullmatch(r'[\d\s]{1,4}', clean(l['text']))]
        body = []
        for i, (t, b, s) in enumerate(lines):
            if t < 75 and TITLE.search(s):
                continue  # running title
            if (t > p.height - 95 or t < 75) and re.fullmatch(r'[\d\s]{1,4}', s):
                continue  # page number (bottom or top of page)
            body.append((t, b, s))
        tops = [t for t, b, s in body]
        bots = [b for t, b, s in body]
        hi = min(tops) if tops else p.height
        lo = max(bots) if bots else 0
        pageno_top = min([t for t, b, s in lines if t > p.height - 95 and re.fullmatch(r'[\d\s]{1,4}', s)] or [p.height])
        title_bot = max([b for t, b, s in lines if t < 75 and TITLE.search(s)] or [0])
        for o in p.images + p.rects + p.curves + p.lines:
            if o['height'] > p.height * 0.9:
                continue
            if o['top'] > title_bot and o['bottom'] < pageno_top:
                hi, lo = min(hi, o['top']), max(lo, o['bottom'])
        out.append(dict(lines=body, lo=lo, hi=hi, w=p.width, h=p.height, pageno_top=pageno_top, pagenos=pagenos))
    return out


def markers(pages):
    """Ordered list of (page, top, kind, q). kind = 'Q' (question header) or 'S' (solution)."""
    ms = []
    for pi, pg in enumerate(pages):
        for t, b, s in pg['lines']:
            m = HDR.search(s)
            if m and len(s) < 40:
                ms.append((pi, t, 'Q', int(m.group(1) or m.group(2))))
            elif SOL.search(s) and len(s) < 45 and not re.search(r'\d{1,2}\s*הלאש', s):
                ms.append((pi, t, 'S', None))
    return ms


def region(pages, start, end):
    """Segments [(page, y0, y1)] from marker start (page, top) up to marker end (or end of doc)."""
    (p0, y0), (p1, y1) = start, end
    segs = []
    for p in range(p0, p1 + 1):
        top = y0 - 4 if p == p0 else pages[p]['hi'] - 4
        bot = y1 - 3 if p == p1 else pages[p]['lo'] + 4
        if bot - top > 12:
            segs.append((p, top, bot))
    return segs


def blank_pagenos(a, page, x_org, y_org):
    s = DPI / 72
    for x0, t, x1, b in page['pagenos']:
        a[max(0, int((t - 1 - y_org) * s)):max(0, int((b + 1 - y_org) * s)),
          max(0, int((x0 - 1 - x_org) * s)):max(0, int((x1 + 1 - x_org) * s))] = 255
    return a


def unhighlight(im):
    """Solution PDFs highlight the correct option with a yellow marker: turn it back into
    black-on-white (a black/yellow blend has R = G, B ~ 0, so gray = min(R, G))."""
    import numpy as np
    a = np.asarray(im).astype(int)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    m = np.minimum(r, g)
    yellow = (abs(r - g) < 60) & (b < m - 40)
    for c in range(3):
        a[..., c][yellow] = m[yellow]
    return Image.fromarray(a.astype('uint8'))


def render(pdf_path, segs, out_png, pages, clean=False):
    imgs = []
    with tempfile.TemporaryDirectory() as td:
        for i, (p, y0, y1) in enumerate(segs):
            s = DPI / 72
            x = int(25 * s); w = int((pages[p]['w'] - 50) * s)
            base = os.path.join(td, f's{i}')
            subprocess.run(['pdftoppm', '-r', str(DPI), '-f', str(p + 1), '-l', str(p + 1), '-png', '-singlefile',
                            '-x', str(x), '-y', str(int(y0 * s)), '-W', str(w), '-H', str(int((y1 - y0) * s)),
                            pdf_path, base], check=True)
            import numpy as np
            a = np.asarray(Image.open(base + '.png').convert('RGB')).copy()
            imgs.append(trim(Image.fromarray(blank_pagenos(a, pages[p], 25.0, y0))))
    W = max(i.width for i in imgs)
    H = sum(i.height for i in imgs) + 20 * (len(imgs) - 1)
    canvas = Image.new('RGB', (W, H), 'white')
    y = 0
    for im in imgs:
        canvas.paste(im, (W - im.width, y))  # right-align (Hebrew)
        y += im.height + 20
    canvas = pad(canvas)
    if clean:
        canvas = unhighlight(canvas)
    canvas.save(out_png, optimize=True)


def trim(im):
    g = im.convert('L').point(lambda v: 255 if v < 245 else 0)
    bb = g.getbbox()
    return im.crop(bb) if bb else im


def pad(im, m=24):
    c = Image.new('RGB', (im.width + 2 * m, im.height + 2 * m), 'white')
    c.paste(im, (m, m))
    return c


_cache = {}
def load(path):
    if path not in _cache:
        pdf = pdfplumber.open(path)
        pages = page_lines(pdf)
        _cache[path] = (pages, markers(pages))
    return _cache[path]


def end_of(pages):
    return (len(pages) - 1, pages[-1]['lo'] + 6)


LETTERS = 'אבגדהו'
HEB = re.compile(r'[א-ת]')
OVR_PATH = os.path.join(ROOT, 'tools/overrides.json')
META_PATH = os.path.join(ROOT, 'tools/meta.json')


def find_labels(pdf, segs):
    """Option labels 'א.' 'ב.' ... (in PDF points). The dot sits left of the letter (RTL)."""
    cands = []
    for si, (p, y0, y1) in enumerate(segs):
        chars = [c for c in pdf.pages[p].chars if y0 <= c['top'] <= y1]
        for c in chars:
            if c['text'] not in LETTERS:
                continue
            near = [d for d in chars if abs(d['top'] - c['top']) < 4]
            dot = [d for d in near if d['text'] in '.)' and -1.5 <= c['x0'] - d['x1'] <= 4]
            if not dot:
                continue
            d = dot[0]
            if any(HEB.match(h['text']) and -1 <= h['x0'] - c['x1'] <= 2.5 for h in near):
                continue  # letter is the end of a word
            if any(HEB.match(h['text']) and -1 <= d['x0'] - h['x1'] <= 1.2 for h in near):
                continue
            cands.append(dict(seg=si, letter=c['text'], x0=min(d['x0'], c['x0']), x1=c['x1'],
                              top=min(c['top'], d['top']), bottom=max(c['bottom'], d['bottom'])))
    labels = []
    for L in LETTERS:
        cs = [c for c in cands if c['letter'] == L]
        if not cs:
            break
        labels.append(max(cs, key=lambda c: (c['seg'], c['top'])))
    return labels


def render_segments(pdf_path, segs, pages):
    """Full-width renders of each segment, no trimming. Returns list of (array, x_origin_pt, y_origin_pt)."""
    import numpy as np
    out = []
    s = DPI / 72
    with tempfile.TemporaryDirectory() as td:
        for i, (p, y0, y1) in enumerate(segs):
            base = os.path.join(td, f's{i}')
            subprocess.run(['pdftoppm', '-r', str(DPI), '-f', str(p + 1), '-l', str(p + 1), '-png', '-singlefile',
                            '-x', str(int(25 * s)), '-y', str(int(y0 * s)), '-W', str(int((pages[p]['w'] - 50) * s)),
                            '-H', str(int((y1 - y0) * s)), pdf_path, base], check=True)
            a = np.asarray(Image.open(base + '.png').convert('RGB')).copy()
            out.append((blank_pagenos(a, pages[p], 25.0, y0), 25.0, y0))
    return out


def _ink(a):
    return (a.min(-1) < 200)


def option_cells(labels, rends, gap_pt=32, vgap_pt=22):
    """Pixel boxes (seg, x0, y0, x1, y1, label) of each option, in original order."""
    import numpy as np
    s = DPI / 72
    cen = lambda l: (l['top'] + l['bottom']) / 2
    rows = []
    for l in labels:
        for r in rows:
            if r[0]['seg'] == l['seg'] and abs(cen(r[0]) - cen(l)) < 6:
                r.append(l); break
        else:
            rows.append([l])
    rows.sort(key=lambda r: (r[0]['seg'], cen(r[0])))
    px = lambda l, seg: (int((l['x0'] - rends[seg][1]) * s), int((l['top'] - rends[seg][2]) * s),
                         int((l['x1'] - rends[seg][1]) * s), int((l['bottom'] - rends[seg][2]) * s))
    # 1. horizontal extent of every cell, measured on the label's own line
    xr_of, xl_of = {}, {}
    for row in rows:
        seg = row[0]['seg']; ink = _ink(rends[seg][0]); H, W = ink.shape
        row.sort(key=lambda l: -l['x1'])
        for k, l in enumerate(row):
            lx0, ly0, lx1, ly1 = px(l, seg)
            xr = min(W, lx1 + int(3 * s))
            if k + 1 < len(row):
                xl = px(row[k + 1], seg)[2] + int(5 * s)
            else:
                band = ink[max(0, ly0 - int(4 * s)):ly1 + int(4 * s), :xr].any(0)
                xl, run = xr, 0
                for x in range(xr - 1, -1, -1):
                    if band[x]:
                        xl, run = x, 0
                    else:
                        run += 1
                        if run > gap_pt * s:
                            break
            xr_of[l['letter']], xl_of[l['letter']] = xr, xl
    single = all(len(r) == 1 for r in rows)
    if single:  # vertical list: one common column
        xl_c = min(xl_of.values()); xr_c = max(xr_of.values())
        for k in xl_of:
            xl_of[k], xr_of[k] = xl_c, xr_c

    def row_x(row):
        return min(xl_of[l['letter']] for l in row), max(xr_of[l['letter']] for l in row)

    def white_above(seg, row, lo):
        """Boundary above a row of labels: among the white bands between `lo` and the label top,
        take the longest one, favouring bands close to the label (exponents may sit above it)."""
        ink = _ink(rends[seg][0]); x0, x1 = row_x(row)
        top = min(px(l, seg)[1] for l in row)
        rowink = ink[:, x0:x1].any(1)
        lo = max(lo, 0)
        runs, start = [], None
        for y in range(lo, top + 1):
            if not rowink[y]:
                start = y if start is None else start
            elif start is not None:
                runs.append((start, y - 1)); start = None
        if start is not None:
            runs.append((start, top))
        if not runs:
            return lo
        best = max(runs, key=lambda r: (r[1] - r[0]) - 0.3 * (top - r[1]))
        return (best[0] + best[1]) // 2

    cells = {}
    for ri, row in enumerate(rows):
        seg = row[0]['seg']; a = rends[seg][0]; ink = _ink(a); H = ink.shape[0]
        prev = rows[ri - 1] if ri > 0 and rows[ri - 1][0]['seg'] == seg else None
        nxt = rows[ri + 1] if ri + 1 < len(rows) and rows[ri + 1][0]['seg'] == seg else None
        lo = max(px(l, seg)[3] for l in prev) if prev else max(0, px(row[0], seg)[1] - int(30 * s))
        y0 = white_above(seg, row, lo)
        if nxt:
            y1 = white_above(seg, nxt, max(px(l, seg)[3] for l in row))
        else:
            x0, x1 = row_x(row)
            col = ink[:, x0:x1].any(1)
            y1, run = max(px(l, seg)[3] for l in row), 0
            for y in range(y1, H):
                if col[y]:
                    y1, run = y + 1, 0
                else:
                    run += 1
                    if run > vgap_pt * s:
                        break
        for l in row:
            cells[l['letter']] = (seg, xl_of[l['letter']], y0, xr_of[l['letter']], y1, l)
    return [cells[L] for L in LETTERS[:len(labels)]]


def drop_bottom_specks(a, gap=40, max_ink=300):
    """Remove tiny ink blocks at the bottom, separated from the content above by a white gap."""
    import numpy as np
    a = a.copy()
    while True:
        rows = np.where(_ink(a).any(1))[0]
        if len(rows) < 2:
            return a
        breaks = np.where(np.diff(rows) > gap)[0]
        if not len(breaks):
            return a
        start = rows[breaks[-1] + 1]
        if _ink(a[start:]).sum() > max_ink:
            return a
        a[start:] = 255


def save_trim(a, path):
    im = trim(Image.fromarray(a))
    im = pad(im, 16)
    im.save(path, optimize=True)
    return im


def overrides():
    return json.load(open(OVR_PATH)) if os.path.exists(OVR_PATH) else {}


def extract(exam, q, debug_dir=None):
    import numpy as np
    qid = f'{exam}-q{q:02d}'
    ovr = overrides().get(qid, {})
    st_pdf, so_pdf = (_f(n) for n in FILES[exam])
    pages, ms = load(st_pdf)
    idx = [i for i, m in enumerate(ms) if m[2] == 'Q' and m[3] == q]
    if not idx:
        raise SystemExit(f'{exam} Q{q}: header not found')
    i = idx[0]
    nxt = next((m for m in ms[i + 1:]), None)
    stop = (nxt[0], nxt[1]) if nxt else end_of(pages)
    if 'stop' in ovr:
        stop = tuple(ovr['stop'])
    if st_pdf == so_pdf and (not nxt or nxt[2] != 'S'):
        print(f'  ! {qid}: no solution marker right after statement')
    os.makedirs(os.path.join(ROOT, 'img/q'), exist_ok=True)
    os.makedirs(os.path.join(ROOT, 'img/sol'), exist_ok=True)
    segs = region(pages, ms[i][:2], stop)
    rends = render_segments(st_pdf, segs, pages)
    for a, _, _ in rends:
        a[:] = np.asarray(unhighlight(Image.fromarray(a)))
    with pdfplumber.open(st_pdf) as pdf:
        labels = find_labels(pdf, segs)
    meta = dict(n=len(labels), split=not ovr.get('noSplit', False))
    s = DPI / 72
    for f in os.listdir(os.path.join(ROOT, 'img/q')):
        if f.startswith(qid):
            os.remove(os.path.join(ROOT, 'img/q', f))
    if 'n' in ovr:
        meta['n'] = ovr['n']
    if meta['split'] and len(labels) >= 2:
        cells = option_cells(labels, rends, ovr.get('gap', 32), ovr.get('vgap', 22))
        for k, (seg, x0, y0, x1, y1, l) in enumerate(cells):
            a = rends[seg][0][y0:y1, x0:x1].copy()
            # mask the original letter + dot
            lx0 = int((l['x0'] - 1.5 - rends[seg][1]) * s) - x0
            lx1 = int((l['x1'] + 1.5 - rends[seg][1]) * s) - x0
            ly0 = int((l['top'] - 1.5 - rends[seg][2]) * s) - y0
            ly1 = int((l['bottom'] + 1.5 - rends[seg][2]) * s) - y0
            a[max(0, ly0):max(0, ly1), max(0, lx0):max(0, lx1)] = 255
            save_trim(a, os.path.join(ROOT, f'img/q/{qid}-o{k}.png'))
        if debug_dir:
            dbg = [r[0].copy() for r in rends]
        for seg, x0, y0, x1, y1, l in cells:
            if debug_dir:
                d = dbg[seg]
                d[y0:y0 + 3, x0:x1] = d[y1 - 3:y1, x0:x1] = (255, 0, 0)
                d[y0:y1, x0:x0 + 3] = d[y0:y1, x1 - 3:x1] = (255, 0, 0)
            rends[seg][0][y0:y1, x0:x1] = 255  # remove options from the stem
        # drop specks left below the options block (stray dots), so the stem ends above it
        for seg in {c[0] for c in cells}:
            a = rends[seg][0]
            top = min(c[2] for c in cells if c[0] == seg)
            if _ink(a[top:]).sum() < 400:
                a[top:] = 255
    else:
        meta['split'] = False
        if debug_dir:
            dbg = [r[0].copy() for r in rends]
    stem = [trim(Image.fromarray(drop_bottom_specks(r[0]))) for r in rends]
    stem = [im for im in stem if im.height > 8]
    W = max(im.width for im in stem); H = sum(im.height for im in stem) + 20 * (len(stem) - 1)
    canvas = Image.new('RGB', (W, H), 'white'); y = 0
    for im in stem:
        canvas.paste(im, (W - im.width, y)); y += im.height + 20
    pad(canvas).save(os.path.join(ROOT, f'img/q/{qid}.png'), optimize=True)
    if debug_dir:
        os.makedirs(debug_dir, exist_ok=True)
        ims = [Image.fromarray(d) for d in dbg]
        W = max(im.width for im in ims); H = sum(im.height for im in ims)
        c = Image.new('RGB', (W, H), 'white'); y = 0
        for im in ims:
            c.paste(im, (0, y)); y += im.height
        c.thumbnail((1100, 3000)); c.save(os.path.join(debug_dir, qid + '.png'))
    # solution
    spages, sms = load(so_pdf)
    if so_pdf == st_pdf:
        j = ms.index(nxt) if nxt and nxt[2] == 'S' else None
    else:
        js = [k for k, m in enumerate(sms) if m[2] == 'Q' and m[3] == q]
        j = js[0] if js else None
    meta['sol'] = j is not None
    if j is None:
        print(f'  ! {qid}: no official solution found')
    else:
        nq = next((m for m in sms[j + 1:] if m[2] == 'Q'), None)
        stop = (nq[0], nq[1]) if nq else end_of(spages)
        if 'solStop' in ovr:
            stop = tuple(ovr['solStop'])
        render(so_pdf, region(spages, sms[j][:2], stop), os.path.join(ROOT, f'img/sol/{qid}.png'), spages)
    allmeta = json.load(open(META_PATH)) if os.path.exists(META_PATH) else {}
    allmeta[qid] = meta
    json.dump(allmeta, open(META_PATH, 'w'), indent=1, sort_keys=True)
    return meta


if __name__ == '__main__':
    args = sys.argv[1:]
    dbg = None
    if '--debug' in args:
        k = args.index('--debug'); dbg = args[k + 1]; del args[k:k + 2]
    todo = []
    if args and args[0] == '--chapter':
        sel = json.load(open(os.path.join(ROOT, 'data/selection.json')))
        for it in sel[str(int(args[1]))]:
            todo.append((it['exam'], it['q']))
    else:
        todo = [(args[i], int(args[i + 1])) for i in range(0, len(args), 2)]
    for e, q in todo:
        print(e, q, extract(e, q, dbg))
