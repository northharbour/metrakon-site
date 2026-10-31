"""Lab question (Ben, 2026-10-31): is upgrading from one combined-RGB exposure (the lab's
camera-balanced set-up) to separate R, G, B exposures worth it? Builds registered wipe pairs
for the local page src/pages/lab-compare.astro (not part of the site; git-excluded):
same settings, and matched colour (camera-balanced a*b* scaled up to the separate-exposure
scan's colourfulness: on the face for the portrait, on the chart for the other scenes).
Run from negacon-converter/:  python lab_compare.py <exports root> <out dir>"""
import json, os, sys
import numpy as np
from PIL import Image

EXP, OUT = sys.argv[1:3]
os.makedirs(OUT, exist_ok=True)
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(f'{HERE}/match_chroma.py').read(); exec(src[src.index('M_XYZ'):src.index('def chart_ab')])
bf = open(f'{HERE}/build_figures.py').read(); exec(bf[bf.index('def shift'):bf.index('# the portrait again')])
FACTORS = json.load(open(f'{EXP}/3 Matched colour/factors.json'))['factors']
SAME = f'{EXP}/1 Same look'
CAM = lambda k: f'{SAME}/RGB Camera-balanced/Light Comparison{6939 + k:05d}.jpg'
TRI = lambda k: f'{SAME}/RGB Trichrome/Light Comparison{6994 + 3 * k:05d}_trichrome.jpg'
SCENES = {'portrait': 12, 'street': 15, 'trees': 20}
FACE = (0.36, 0.22, 0.64, 0.50)


def face_chroma(im):
    rgb = np.asarray(im, np.float64) / 255; H, W = rgb.shape[:2]; x0, y0, x1, y1 = FACE
    lab = rgb_to_lab(rgb[int(y0 * H):int(y1 * H):2, int(x0 * W):int(x1 * W):2])
    skin = (lab[..., 0] > 45) & (lab[..., 0] < 90)
    return float(np.hypot(lab[..., 1], lab[..., 2])[skin].mean())


def boost(im, f):
    lab = rgb_to_lab(np.asarray(im, np.float64) / 255); lab[..., 1:] *= f
    out, clip = lab_to_rgb(lab)
    return Image.fromarray((out * 255 + 0.5).astype(np.uint8)), float(clip.mean())


for name, k in SCENES.items():
    a, b = Image.open(CAM(k)).convert('RGB'), Image.open(TRI(k)).convert('RGB')
    for im in (a, b):
        im.thumbnail((1600, 1600), Image.LANCZOS)
    dy, dx = shift(a, b)
    h, w = min(a.height, b.height) - abs(dy), min(a.width, b.width) - abs(dx)
    a = a.crop((max(dx, 0), max(dy, 0), max(dx, 0) + w, max(dy, 0) + h))
    b = b.crop((max(-dx, 0), max(-dy, 0), max(-dx, 0) + w, max(-dy, 0) + h))
    fac = face_chroma(b) / face_chroma(a) if name == 'portrait' else FACTORS['RGB Camera-balanced']
    am, clip = boost(a, fac)
    a.save(f'{OUT}/{name}_camera.jpg', quality=88); b.save(f'{OUT}/{name}_trichrome.jpg', quality=88)
    am.save(f'{OUT}/{name}_camera-matched.jpg', quality=88)
    print(f'{name}: registered {(dy, dx)}, camera-balanced colour x{fac:.2f} for the matched pair, {100 * clip:.2f}% clipped')
