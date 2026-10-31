"""Chroma of the 18 colour patches in each arm's EXPORTED 0 EV chart (same look for every
arm) → the saturation each arm needs to match a reference arm. Run from negacon-converter/:
python export_chroma.py <exports dir> [reference arm folder name]"""
import os, sys, numpy as np
sys.path.insert(0, '.')
from PIL import Image
import chartfit as CF
EXP = sys.argv[1]; REFARM = sys.argv[2] if len(sys.argv) > 2 else 'RGB Trichrome'
CHARTS = {'White CS-Lite': '06972', 'RGB Camera-balanced': '06943', 'RGB Sensor-balanced': '06917',
          'RGB Unmixed': '06917_unmixed', 'RGB Trichrome': '07006_trichrome'}
labs = {}
for arm, n in CHARTS.items():
    rgb = np.asarray(Image.open(f'{EXP}/{arm}/Light Comparison{n}.jpg').convert('RGB'), np.float64) / 255
    lin = np.where(rgb <= 0.04045, rgb / 12.92, ((rgb + 0.055) / 1.055) ** 2.4)
    k = 4; h, w = lin.shape[0] // k, lin.shape[1] // k
    small = lin[:h * k, :w * k].reshape(h, k, w, k, 3).mean(axis=(1, 3))
    best = None
    for seed in ([(0.25, 0.25), (0.75, 0.25), (0.75, 0.75), (0.25, 0.75)], [(0.3, 0.3), (0.7, 0.3), (0.7, 0.7), (0.3, 0.7)]):
        c = CF.locate_chart(small, seed, refine=True, search=True)
        if c and (best is None or c['score'] > best['score']): best = c
    meds, _, ok = CF._sample_via_h(small, CF._homography(np.array(best['unit']), best['corners_px']), inner=0.35)
    lab = CF.linear_rgb_to_lab(meds)
    labs[arm] = lab
    C = np.hypot(lab[:18, 1], lab[:18, 2])
    print(f'{arm:22s} locate score {best["score"]:.2f}  grey L* {lab[18,0]:.0f}→{lab[23,0]:.0f}  mean chroma C* {C.mean():5.1f}  '
          f'red C* {np.hypot(*lab[14,1:]):5.1f}  blue C* {np.hypot(*lab[12,1:]):5.1f}')
ref = labs[REFARM][:18, 1:]
print(f'\nsaturation to match {REFARM} at 1.40 (least squares over the 18 colour patches):')
for arm, lab in labs.items():
    ab = lab[:18, 1:]
    s = float((ab * ref).sum() / (ab * ab).sum())
    print(f'  {arm:22s} ×{s:4.2f}  →  saturation {1.4 * s:4.2f}')
