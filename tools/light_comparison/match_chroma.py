"""Matched-colour set for the article: every arm's same-look exports with their colourfulness
scaled to the reference arm's (trichrome), so a comparison shows noise, not saturation.

The factor per arm is the least-squares scale that maps the a*b* of the 18 colour patches of
its exported 0 EV chart onto the reference arm's (export_chroma.py measures the same). Only
a*/b* are scaled — L* is untouched — in CIE Lab (D65) from proper sRGB; colours pushed past
sRGB are clipped and counted. Run from negacon-converter/:
  python match_chroma.py <same-look exports dir> <out dir> [reference arm]"""
import glob, json, os, sys
import numpy as np
sys.path.insert(0, '.')
from PIL import Image
import chartfit as CF

SRC, OUT = sys.argv[1:3]
REF = sys.argv[3] if len(sys.argv) > 3 else 'RGB Trichrome'
CHARTS = {'White CS-Lite': '06972', 'RGB Camera-balanced': '06943', 'RGB Sensor-balanced': '06917',
          'RGB Unmixed': '06917_unmixed', 'RGB Trichrome': '07006_trichrome'}
M_XYZ = np.array([[0.4124564, 0.3575761, 0.1804375], [0.2126729, 0.7151522, 0.0721750], [0.0193339, 0.1191920, 0.9503041]])
M_RGB = np.linalg.inv(M_XYZ)
WP = np.array([0.95047, 1.0, 1.08883])


def to_lin(v): return np.where(v <= 0.04045, v / 12.92, ((v + 0.055) / 1.055) ** 2.4)
def to_srgb(v): return np.where(v <= 0.0031308, v * 12.92, 1.055 * np.power(np.maximum(v, 0), 1 / 2.4) - 0.055)
def f(t): return np.where(t > (6 / 29) ** 3, np.cbrt(t), t / (3 * (6 / 29) ** 2) + 4 / 29)
def finv(t): return np.where(t > 6 / 29, t ** 3, 3 * (6 / 29) ** 2 * (t - 4 / 29))


def rgb_to_lab(rgb):
    xyz = to_lin(rgb) @ M_XYZ.T / WP
    fx, fy, fz = f(xyz[..., 0]), f(xyz[..., 1]), f(xyz[..., 2])
    return np.stack([116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz)], axis=-1)


def lab_to_rgb(lab):
    fy = (lab[..., 0] + 16) / 116
    xyz = np.stack([finv(fy + lab[..., 1] / 500), finv(fy), finv(fy - lab[..., 2] / 200)], axis=-1) * WP
    lin = xyz @ M_RGB.T
    out = np.clip(lin, 0, 1)
    return to_srgb(out), (np.abs(lin - out) > 1e-4).any(axis=-1)


def chart_ab(path):
    rgb = np.asarray(Image.open(path).convert('RGB'), np.float64) / 255
    lin = to_lin(rgb); k = 4; h, w = lin.shape[0] // k, lin.shape[1] // k
    small = lin[:h * k, :w * k].reshape(h, k, w, k, 3).mean(axis=(1, 3))
    best = None
    for seed in ([(0.25, 0.25), (0.75, 0.25), (0.75, 0.75), (0.25, 0.75)], [(0.3, 0.3), (0.7, 0.3), (0.7, 0.7), (0.3, 0.7)]):
        c = CF.locate_chart(small, seed, refine=True, search=True)
        if c and (best is None or c['score'] > best['score']):
            best = c
    meds, _, _ = CF._sample_via_h(small, CF._homography(np.array(best['unit']), best['corners_px']), inner=0.35)
    return CF.linear_rgb_to_lab(meds)[:18, 1:]


ref_ab = chart_ab(f'{SRC}/{REF}/Light Comparison{CHARTS[REF]}.jpg')
factors = {}
for arm, n in CHARTS.items():
    ab = chart_ab(f'{SRC}/{arm}/Light Comparison{n}.jpg')
    factors[arm] = round(float((ab * ref_ab).sum() / (ab * ab).sum()), 4)
print('factors (a*b* scale to match', REF + '):', factors, flush=True)
os.makedirs(OUT, exist_ok=True)
json.dump(dict(reference=REF, factors=factors, source=SRC), open(f'{OUT}/factors.json', 'w'), indent=1)

for arm, s in factors.items():
    os.makedirs(f'{OUT}/{arm}', exist_ok=True)
    clipped = total = 0
    for p in sorted(glob.glob(f'{SRC}/{arm}/*.jpg')):
        im = Image.open(p)
        rgb = np.asarray(im.convert('RGB'), np.float32) / 255
        out = np.empty_like(rgb)
        for y0 in range(0, rgb.shape[0], 512):
            lab = rgb_to_lab(rgb[y0:y0 + 512].astype(np.float64))
            lab[..., 1:] *= s
            o, c = lab_to_rgb(lab)
            out[y0:y0 + 512] = o; clipped += int(c.sum())
        total += rgb.shape[0] * rgb.shape[1]
        Image.fromarray((out * 255 + 0.5).astype(np.uint8)).save(
            f'{OUT}/{arm}/{os.path.basename(p)}', quality=97, subsampling=0, icc_profile=im.info.get('icc_profile'))
    print(f'{arm:22s} ×{s:.3f}  {len(glob.glob(f"{SRC}/{arm}/*.jpg"))} images, '
          f'{100 * clipped / max(total, 1):.3f}% of pixels clipped to sRGB', flush=True)

print('\nverify — chart a*b* of the matched set vs the reference:')
for arm, n in CHARTS.items():
    ab = chart_ab(f'{OUT}/{arm}/Light Comparison{n}.jpg')
    print(f'  {arm:22s} remaining factor ×{float((ab * ref_ab).sum() / (ab * ab).sum()):.3f}')
