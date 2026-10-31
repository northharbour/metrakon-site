"""Web figures for the RGB vs white article, from the exports and the noise run.
Run from negacon-converter/:  python build_figures.py <exports root> <noise dir> <assets out dir>

  chart_<arm>.jpg            0 EV chart, same look, cropped to the chart (each arm located itself)
  <scene>_<arm>.jpg          same-look scenes for the wipes, 1600 px long edge
  sky_<arm>.png, patch_<patch>_<arm>.png   matched-colour close-ups (open sky; chart patches) —
                             NOT used by the article (the differences don't show at web sizes),
                             written to results/figures_extra/ for the record and the Reels
"""
import json, os, sys
import numpy as np
sys.path.insert(0, '.')
from PIL import Image
import chartfit as CF

EXP, NOISE, OUT = sys.argv[1:4]
os.makedirs(OUT, exist_ok=True)
EXTRA = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'results', 'figures_extra')
os.makedirs(EXTRA, exist_ok=True)
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(f'{HERE}/match_chroma.py').read()
exec(src[src.index('M_XYZ'):src.index('def chart_ab')])          # sRGB ↔ Lab helpers
FACTORS = json.load(open(f'{EXP}/3 Matched colour/factors.json'))['factors']

ARMS = {  # slug: (export folder, numbering of scene index k)
    'white': ('White CS-Lite', lambda k: f'{6968 + k:05d}'),
    'rgb-camera': ('RGB Camera-balanced', lambda k: f'{6939 + k:05d}'),
    'rgb-sensor': ('RGB Sensor-balanced', lambda k: f'{6913 + k:05d}'),
    'rgb-unmixed': ('RGB Unmixed', lambda k: f'{6913 + k:05d}_unmixed'),
    'trichrome': ('RGB Trichrome', lambda k: f'{6994 + 3 * k:05d}_trichrome'),
}
CHART_K = 4
WIPES = {'street': (15, ['rgb-sensor', 'trichrome']), 'trees': (20, ['white', 'rgb-sensor']),
         'portrait': (12, ['white', 'trichrome'])}
SKY = (21, (0.70, 0.07, 0.90, 0.20))      # scene index, crop box as fractions (x0, y0, x1, y1)


def path(arm, k, sett='1 Same look'):
    folder, num = ARMS[arm]
    return f'{EXP}/{sett}/{folder}/Light Comparison{num(k)}.jpg'


def load(p):
    return np.asarray(Image.open(p).convert('RGB'), np.float64) / 255


# 1. charts: locate on a 4x reduction, crop the full image around the chart corners
#    (the leak-removal arm was measured but is not in the article)
for arm in [a for a in ARMS if a != 'rgb-unmixed']:
    rgb = load(path(arm, CHART_K))
    lin = to_lin(rgb); k = 4; h, w = lin.shape[0] // k, lin.shape[1] // k
    small = lin[:h * k, :w * k].reshape(h, k, w, k, 3).mean(axis=(1, 3))
    best = None
    for seed in ([(0.25, 0.25), (0.75, 0.25), (0.75, 0.75), (0.25, 0.75)], [(0.3, 0.3), (0.7, 0.3), (0.7, 0.7), (0.3, 0.7)]):
        c = CF.locate_chart(small, seed, refine=True, search=True)
        if c and (best is None or c['score'] > best['score']):
            best = c
    pts = (best['corners_px'] + 0.5) * k
    x0, y0 = pts.min(axis=0); x1, y1 = pts.max(axis=0)
    mx, my = 0.06 * (x1 - x0), 0.06 * (y1 - y0)
    im = Image.open(path(arm, CHART_K)).convert('RGB').crop((int(x0 - mx), int(y0 - my), int(x1 + mx), int(y1 + my)))
    if im.height > im.width:
        im = im.rotate(90, expand=True)
    im.thumbnail((720, 720), Image.LANCZOS)
    im.save(f'{OUT}/chart_{arm}.jpg', quality=88)
    print('chart', arm, im.size)

# 2. wipes: same look, 1600 px long edge; the film was repositioned between arms, so the
#    pair is registered (integer shift by phase correlation) and both cropped to the overlap
def shift(a, b):
    a = np.asarray(a.convert('L'), np.float64); b = np.asarray(b.convert('L'), np.float64)
    h, w = min(a.shape[0], b.shape[0]), min(a.shape[1], b.shape[1])
    a, b = (x[:h, :w] - x[:h, :w].mean() for x in (a, b))
    R = np.fft.fft2(a) * np.conj(np.fft.fft2(b)); cc = np.fft.ifft2(R / (np.abs(R) + 1e-9)).real
    y, x = np.unravel_index(np.argmax(cc), cc.shape)
    return int(y if y < h / 2 else y - h), int(x if x < w / 2 else x - w)


# the portrait again with the white-light scan exported from Obelisk at saturation 2.54
# instead of 1.4 (Ben, 2026-10-31): its face comes out as colourful as the separate-exposure
# scan's (face C* 17.2 vs 17.6), so this is a real Obelisk setting, not a post-process
FACE = (0.36, 0.22, 0.64, 0.50)                    # x0, y0, x1, y1 as fractions of the frame
MATCHED = {'portrait-matched': (12, ['white', 'trichrome'], '4 Portrait saturation 2.54')}


def face_chroma(rgb):
    H, W = rgb.shape[:2]; x0, y0, x1, y1 = FACE
    lab = rgb_to_lab(rgb[int(y0 * H):int(y1 * H):4, int(x0 * W):int(x1 * W):4])
    skin = (lab[..., 0] > 45) & (lab[..., 0] < 90)
    return float(np.hypot(lab[..., 1], lab[..., 2])[skin].mean())


for name, (k, arms, sett) in MATCHED.items():
    print(f'{name}: face C* {arms[0]} ({sett}) {face_chroma(load(path(arms[0], k, sett))):.1f}, '
          f'{arms[1]} {face_chroma(load(path(arms[1], k))):.1f}')

for name, spec in list(WIPES.items()) + list(MATCHED.items()):
    k, arms = spec[0], spec[1]
    first = path(arms[0], k, spec[2]) if name in MATCHED else path(arms[0], k)
    a, b = Image.open(first).convert('RGB'), Image.open(path(arms[1], k)).convert('RGB')
    for im in (a, b):
        im.thumbnail((1600, 1600), Image.LANCZOS)
    dy, dx = shift(a, b)                      # b's content sits at a's position + (dy, dx)
    h, w = min(a.height, b.height) - abs(dy), min(a.width, b.width) - abs(dx)
    a = a.crop((max(dx, 0), max(dy, 0), max(dx, 0) + w, max(dy, 0) + h))
    b = b.crop((max(-dx, 0), max(-dy, 0), max(-dx, 0) + w, max(-dy, 0) + h))
    for arm, im in zip(arms, (a, b)):
        im.save(f'{OUT}/{name}_{arm}.jpg', quality=85)
    print('wipe', name, arms, 'registered by', (dy, dx), '→', a.size)

# 3. sky close-ups at matched colour, 100% pixels; every crop shifted to one average colour so
#    only the noise differs, and refused if any pixel had to be clipped
k, (fx0, fy0, fx1, fy1) = SKY
labs = {}
for arm in ARMS:
    rgb = load(path(arm, k))
    H, W = rgb.shape[:2]
    side = int(min((fx1 - fx0) * W, (fy1 - fy0) * H, 320))
    cx, cy = int((fx0 + fx1) / 2 * W), int((fy0 + fy1) / 2 * H)
    lab = rgb_to_lab(rgb[cy - side // 2:cy + side // 2, cx - side // 2:cx + side // 2])
    lab[..., 1:] *= FACTORS[ARMS[arm][0]]
    labs[arm] = lab
common = np.mean([l.reshape(-1, 3).mean(axis=0) for l in labs.values()], axis=0)
for arm, lab in labs.items():
    out, clip = lab_to_rgb(lab - lab.reshape(-1, 3).mean(axis=0) + common)
    assert not clip.any(), f'sky crop clipped for {arm}'
    Image.fromarray((out * 255 + 0.5).astype(np.uint8)).save(f'{EXTRA}/sky_{arm}.png')
print('sky crops at common colour L*a*b*', common.round(1))

# 4. chart patch tiles (half-size quads, matched colour, mean at the chart's reference colour)
REF = {'red': 14, 'green': 13, 'blue': 12, 'grey': 21}
EV0 = {'white': ('CS-Lite White', '06972'), 'rgb-camera': ('RGB Camera-balanced', '06943'),
       'rgb-sensor': ('RGB Sensor-balanced', '06917'), 'rgb-unmixed': ('RGB Sensor Unmixed', '06917_unmixed'),
       'trichrome': ('RGB Trichrome', '07006_trichrome')}
for arm, (sub, n) in EV0.items():
    for p, j in REF.items():
        L = np.load(f'{NOISE}/{sub}__Light Comparison{n}__{"neutral 5" if p == "grey" else p}.npy')
        L = L - np.median(L.reshape(-1, 3), axis=0) + CF.CC24_LAB[j]
        fy = (L[..., 0] + 16) / 116
        xyz = np.stack([finv(fy + L[..., 1] / 500), finv(fy), finv(fy - L[..., 2] / 200)], axis=-1) * WP
        rgb = to_srgb(np.clip(xyz @ M_RGB.T, 0, 1))
        Image.fromarray((rgb * 255 + 0.5).astype(np.uint8)).save(f'{EXTRA}/patch_{p}_{arm}.png')
print('patch tiles done')

# 5. link-preview images (og:image, 1200×630): one picture split down the middle — white light
#    on the left half, separate R, G, B on the right — like the article's wipe stopped halfway
from PIL import ImageDraw


def chart_bbox(img):
    """(cx, cy, w, h) of the ColorChecker in a full-size export, located as in section 1."""
    lin = to_lin(np.asarray(img, np.float64) / 255); k = 4; h, w = lin.shape[0] // k, lin.shape[1] // k
    small = lin[:h * k, :w * k].reshape(h, k, w, k, 3).mean(axis=(1, 3))
    best = None
    for seed in ([(0.25, 0.25), (0.75, 0.25), (0.75, 0.75), (0.25, 0.75)], [(0.3, 0.3), (0.7, 0.3), (0.7, 0.7), (0.3, 0.7)]):
        c = CF.locate_chart(small, seed, refine=True, search=True)
        if c and (best is None or c['score'] > best['score']):
            best = c
    pts = (best['corners_px'] + 0.5) * k - 0.5
    (x0, y0), (x1, y1) = pts.min(axis=0), pts.max(axis=0)
    return (x0 + x1) / 2, (y0 + y1) / 2, x1 - x0, y1 - y0, CF._homography(np.array(best['unit']), pts)


def _edges(im):
    x = np.asarray(im.convert('L'), np.float64); gy, gx = np.gradient(x); return np.hypot(gx, gy)


def _phase(A, B):
    h, w = min(A.shape[0], B.shape[0]), min(A.shape[1], B.shape[1])
    win = np.outer(np.hanning(h), np.hanning(w))
    A, B = (A[:h, :w] - A[:h, :w].mean()) * win, (B[:h, :w] - B[:h, :w].mean()) * win
    R = np.fft.fft2(A) * np.conj(np.fft.fft2(B)); cc = np.fft.ifft2(R / (np.abs(R) + 1e-9)).real
    y, x = np.unravel_index(np.argmax(cc), cc.shape)
    return cc.max(), int(y if y < h / 2 else y - h), int(x if x < w / 2 else x - w)


def register(a, b, q=4):
    """Scale and shift mapping b onto a: (sc, dy, dx) with b resized by sc, then
    b pixel = a pixel − (dy, dx). The two exports cover slightly different areas of film and
    the white-light scans were made at ~3% higher magnification, so the scale is searched
    (edge maps, Hann window, phase correlation on a q× reduction)."""
    A = _edges(a.reduce(q)); bq = b.reduce(q)
    best = None
    for sc in np.arange(0.95, 1.0501, 0.0025):
        pk, dy, dx = _phase(A, _edges(bq.resize((round(bq.width * sc), round(bq.height * sc)), Image.BILINEAR)))
        if best is None or pk > best[0]:
            best = (pk, sc, dy, dx)
    return best[1], best[2] * q, best[3] * q


def split_preview(k, framing, out, on_chart=False, where=None):
    a = Image.open(path('white', k)).convert('RGB')
    b = Image.open(path('trichrome', k)).convert('RGB')
    sc, dy, dx = register(a, b)
    b = b.resize((round(b.width * sc), round(b.height * sc)), Image.LANCZOS)
    print(f'  {out}: scale x{sc:.4f}')
    # b pixel = a pixel − (dy, dx)
    cx, cy, bw = framing(a)
    inset = max(abs(dx), abs(dy)) + 8
    bw = min(bw, 2 * min(cx, a.width - cx) - 2 * inset)                   # stay inside both images
    bh = bw * 630 / 1200
    cy = min(max(cy, bh / 2 + inset), a.height - bh / 2 - inset)
    box = (round(cx - bw / 2), round(cy - bh / 2), round(cx + bw / 2), round(cy + bh / 2))
    left = a.crop(box).resize((1200, 630), Image.LANCZOS)
    right = b.crop((box[0] - dx, box[1] - dy, box[2] - dx, box[3] - dy)).resize((1200, 630), Image.LANCZOS)
    og = left.copy(); og.paste(right.crop((600, 0, 1200, 630)), (600, 0))
    d = ImageDraw.Draw(og)
    d.rectangle((599, 0, 600, 630), fill=(233, 236, 243))                 # the wipe's divider + handle
    d.ellipse((581, 296, 619, 334), fill=(233, 236, 243))
    d.polygon([(593, 315), (599, 309), (599, 321)], fill=(7, 10, 18))
    d.polygon([(607, 315), (601, 309), (601, 321)], fill=(7, 10, 18))
    og.save(f'{where or OUT}/{out}', quality=86)
    print(out, 'registered by', (dy, dx), 'box', box)


# portrait: the first portrait (further away, more contrast), full frame width, centred 44%
# down the frame so the sweater shows (Ben, 2026-10-31)
split_preview(11, lambda im: (im.width / 2, 0.44 * im.height, im.width), 'og-portrait-split.jpg')
# chart: the chart plus some of the scene around it, filling the frame
split_preview(CHART_K, lambda im: (lambda c: (c[0], c[1], 1.3 * c[3] * 1200 / 630))(chart_bbox(im)),
              'og-chart-split.jpg', on_chart=True, where=EXTRA)        # the alternative, not used
