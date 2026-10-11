"""Stellt KI-Bilder auf Magenta frei, zerlegt Sprite-Sheets in Einzelbilder und schreibt assets/sprites.js.
Aufruf: python sprites.py <rohordner> <spielordner>
Erwartet im Rohordner: hero.png, enemies.png, boss.png, far.png, mid.png (fehlende werden übersprungen)."""
import sys, os, json
import numpy as np
from PIL import Image

RAW, GAME = sys.argv[1], sys.argv[2]
OUT = os.path.join(GAME, 'assets')
os.makedirs(OUT, exist_ok=True)


def key_magenta(img):
    a = np.asarray(img.convert('RGB')).astype(np.float32)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    d = np.sqrt((255 - r) ** 2 + g ** 2 + (255 - b) ** 2)
    alpha = np.clip((d - 70) / 80, 0, 1)
    # Magenta-Schimmer an den Kanten entfernen
    ex = np.clip(np.minimum(r, b) - g, 0, None) * (1 - alpha * .6)
    r, b = r - ex, b - ex
    out = np.dstack([r, g, b, alpha * 255]).clip(0, 255).astype(np.uint8)
    return out


def runs(mask1d, gap, minlen):
    res, start, last = [], None, None
    for i, v in enumerate(mask1d):
        if v:
            if start is None:
                start = i
            elif i - last > gap:
                res.append([start, last + 1]); start = i
            last = i
    if start is not None:
        res.append([start, last + 1])
    return [r for r in res if r[1] - r[0] >= minlen]


def merge_small(spans, minw):
    spans = [s[:] for s in spans]
    changed = True
    while changed and len(spans) > 1:
        changed = False
        for i, s in enumerate(spans):
            if s[1] - s[0] < minw:
                j = i - 1 if i > 0 and (i == len(spans) - 1 or s[0] - spans[i - 1][1] < spans[i + 1][0] - s[1]) else i + 1
                lo, hi = min(i, j), max(i, j)
                spans[lo] = [min(spans[lo][0], spans[hi][0]), max(spans[lo][1], spans[hi][1])]
                del spans[hi]; changed = True
                break
    return spans


def sheet(name, rows_expected, scale=.55):
    path = os.path.join(RAW, name + '.png')
    if not os.path.exists(path):
        return None
    src = Image.open(path)
    src = src.resize((round(src.width * scale), round(src.height * scale)), Image.LANCZOS)
    rgba = key_magenta(src)
    alpha = rgba[..., 3] > 40
    h, w = alpha.shape
    rows = merge_small(runs(alpha.sum(1) > 2, 6, 10), int(h * .12))
    frames = []
    allcols = [merge_small(runs(alpha[y0:y1].sum(0) > 1, 5, 3), int(w * .045)) for (y0, y1) in rows]
    widths = sorted(c[1] - c[0] for cs in allcols for c in cs)
    med = widths[len(widths) // 2] if widths else 0
    for (y0, y1), cols in zip(rows, allcols):
        band = alpha[y0:y1]
        # Zusammengewachsene Posen (z. B. Klinge berührt Nachbarpose) an der dünnsten Stelle trennen
        split = []
        for (x0, x1) in cols:
            if med and x1 - x0 > 1.7 * med:
                dens = band[:, x0:x1].sum(0)
                a, b = int((x1 - x0) * .3), int((x1 - x0) * .7)
                cut = x0 + a + int(np.argmin(dens[a:b]))
                split += [[x0, cut], [cut, x1]]
            else:
                split.append([x0, x1])
        cols = split
        for (x0, x1) in cols:
            m = alpha[y0:y1, x0:x1]
            ys, xs = np.nonzero(m)
            if len(ys) < 60:
                continue
            by0, by1, bx0, bx1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
            fh = by1 - by0
            band_t = (ys >= by0 + fh * .25) & (ys <= by0 + fh * .6)
            ax = float(xs[band_t].mean() - bx0) if band_t.any() else (bx1 - bx0) / 2
            crop = rgba[y0 + by0:y0 + by1, x0 + bx0:x0 + bx1]
            frames.append((crop, ax, float(fh)))
    print(name, 'Zeilen:', len(rows), 'Bilder:', len(frames), '(erwartet', rows_expected, ')')
    meta = []
    for i, (crop, ax, fh) in enumerate(frames):
        fn = f'{name}_{i}.png'
        Image.fromarray(crop).save(os.path.join(OUT, fn), optimize=True)
        meta.append({'src': 'assets/' + fn, 'w': crop.shape[1], 'h': crop.shape[0], 'ax': round(ax, 1), 'ay': crop.shape[0]})
    return meta


data = {}
old = os.path.join(OUT, 'sprites.js')
if os.path.exists(old):
    txt = open(old, encoding='utf-8').read()
    data = json.loads(txt[txt.index('{'):txt.rindex('}') + 1])
for n, exp in [('hero', 8), ('enemies', 12), ('boss', 5)]:
    m = sheet(n, exp)
    if m is not None:
        data[n] = m

far = os.path.join(RAW, 'far.png')
if os.path.exists(far):
    im = Image.open(far).convert('RGB')
    im = im.resize((round(im.width * 540 / im.height), 540), Image.LANCZOS)
    im.save(os.path.join(OUT, 'far.jpg'), quality=88)
    data['far'] = {'src': 'assets/far.jpg', 'w': im.width, 'h': im.height}
    print('far', im.size)

mid = os.path.join(RAW, 'mid.png')
if os.path.exists(mid):
    src = Image.open(mid)
    src = src.resize((round(src.width * 540 / src.height), 540), Image.LANCZOS)
    rgba = key_magenta(src)
    alpha = rgba[..., 3] > 128
    full = alpha.mean(1)
    h = alpha.shape[0]
    road = next((y for y in range(int(h * .55), h) if full[y] > .97), int(h * .82))
    Image.fromarray(rgba).save(os.path.join(OUT, 'mid.png'), optimize=True)
    data['mid'] = {'src': 'assets/mid.png', 'w': rgba.shape[1], 'h': h, 'road': road}
    print('mid', rgba.shape[1], h, 'Straße ab Zeile', road)

with open(os.path.join(OUT, 'sprites.js'), 'w', encoding='utf-8') as f:
    f.write('window.SPRITES = ' + json.dumps(data) + ';\n')
print('sprites.js geschrieben')
