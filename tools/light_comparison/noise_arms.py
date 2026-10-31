"""Colour noise at matched colour, per arm and chart patch, from the actual pixels.

Decode: half size (one Bayer quad per pixel: no demosaic, no white balance) — identical
for every arm. Inversion: pipeline.invert_negative against the profile's picked base.
Chart: chartfit.locate_chart; the patch medians must match the profile's stored samples.
Render: fingerprint → the profile's matrix → that frame's stored tone map → the neutral
reference look → Lab, then a*b* scaled by the arm's saturation-to-chart factor
(sat_suggest), i.e. every arm at the same colour. Noise = within-patch spread.
Run from negacon-converter/: python noise_arms.py <db copy> <charts dir> <scores.json> <out dir>"""
import json, os, sqlite3, sys
import numpy as np
from PIL import Image

sys.path.insert(0, '.')
import pipeline as P
import chartfit as CF

DB, CHARTS, SCORES, OUT = sys.argv[1:5]
IDENTITY = len(sys.argv) > 5 and sys.argv[5] == 'identity'
S_IDENTITY = {'White (CS-Lite)': 2.45, 'RGB, camera-balanced': 2.20, 'RGB, sensor-balanced': 2.07, 'RGB, trichrome': 1.48, 'RGB, unmixed': 1.37}
ARMS = [(99, 'White (CS-Lite)', 'CS-Lite White'), (105, 'RGB, camera-balanced', 'RGB Camera-balanced'),
        (102, 'RGB, sensor-balanced', 'RGB Sensor-balanced'), (108, 'RGB, trichrome', 'RGB Trichrome'),
        (111, 'RGB, unmixed', 'RGB Sensor Unmixed')]
SHOW = {'red': 14, 'blue': 12, 'green': 13, 'neutral 5': 21}
CROP = 96
scores = json.load(open(SCORES))
db = sqlite3.connect(DB); db.row_factory = sqlite3.Row
os.makedirs(OUT, exist_ok=True)

import ast
node = next(n for n in ast.parse(open('main.py').read()).body
            if isinstance(n, ast.FunctionDef) and n.name == '_resolve_profile')
ns = {'json': json}; exec(compile(ast.Module([node], []), 'main.py', 'exec'), ns)
resolve = ns['_resolve_profile']


def patch_boxes(inv, H, inner=0.45):
    boxes = []
    for cx, cy in CF._grid_centers():
        pts = np.array([[cx, cy], [cx + 0.5 / 6, cy], [cx, cy + 0.5 / 4]])
        ph = np.concatenate([pts, np.ones((3, 1))], axis=1) @ H.T
        p, px_, py_ = ph[:, :2] / ph[:, 2:3]
        rad = inner * min(np.hypot(*(px_ - p)), np.hypot(*(py_ - p)))
        boxes.append((int(p[1] - rad), int(p[1] + rad) + 1, int(p[0] - rad), int(p[0] + rad) + 1))
    return boxes


def lab_pixels(bal_px, M, fr, look):
    b = np.clip(bal_px @ M.T, 0.0, None)
    x = np.interp(b, fr['xs'], fr['ys']).astype(np.float32)
    rgb = P.apply_look(x.reshape(1, -1, 3), look, float(fr['ts'])).reshape(-1, 3).astype(np.float64)
    return CF.display_rgb_to_lab(rgb, float(look.get('gamma') or 2.2))


def lab_to_display(lab, gamma=2.2):
    """Inverse of display_rgb_to_lab for the crop images (D65 sRGB primaries, display gamma)."""
    fy = (lab[..., 0] + 16) / 116; fx = fy + lab[..., 1] / 500; fz = fy - lab[..., 2] / 200
    finv = lambda t: np.where(t > 6 / 29, t ** 3, 3 * (6 / 29) ** 2 * (t - 4 / 29))
    xyz = np.stack([0.95047 * finv(fx), finv(fy), 1.08883 * finv(fz)], axis=-1)
    m = np.array([[3.2406, -1.5372, -0.4986], [-0.9689, 1.8758, 0.0415], [0.0557, -0.2040, 1.0570]])
    lin = np.clip(xyz @ m.T, 0, 1)
    return np.clip(lin ** (1 / gamma), 0, 1)


results = {}
for pid, label, sub in ARMS:
    row = db.execute('SELECT * FROM profiles WHERE id=?', (pid,)).fetchone()
    chart = json.loads(row['calib_samples'])['chart']
    fp = json.loads(row['channel_balance'])
    M = np.asarray(json.loads(row['density_matrix']))
    prof = dict(resolve(row), density_matrix=None)
    look = CF.reference_look(prof)
    s = S_IDENTITY[label] if IDENTITY else scores[label]['sat_suggest']
    if IDENTITY: M = np.eye(3)
    base = np.asarray(chart['base_pick']['base'] if chart.get('base_pick') else chart['frames'][0]['base'])
    out_max = float(fp['out'][-1])
    per_frame = []
    for fr in chart['frames']:
        path = os.path.join(CHARTS, sub, fr['name'])
        lin = P.load_raw(path, half_size=True, wb_mode='unity')
        inv = P.invert_negative(lin, base)
        stored = np.asarray(fr['meds'])
        # locate on a 4x box-averaged copy, then pick the orientation and refine the
        # corners by matching the profile's stored patch medians (same image, same base)
        k = 4
        h4, w4 = inv.shape[0] // k, inv.shape[1] // k
        small = inv[:h4 * k, :w4 * k].reshape(h4, k, w4, k, 3).mean(axis=(1, 3))
        best = None
        for seed in ([(0.33, 0.27), (0.70, 0.27), (0.70, 0.75), (0.33, 0.75)],
                     [(0.30, 0.22), (0.73, 0.22), (0.73, 0.80), (0.30, 0.80)]):
            c = CF.locate_chart(small, seed, refine=False, search=True)
            if c and (best is None or c['score'] > best['score']):
                best = c
        def diff(unit, pts):
            meds_s, _, ok = CF._sample_via_h(small, CF._homography(np.array(unit), pts))
            return float(np.abs(meds_s - stored).mean()) if ok else 9.0
        cur = best['corners_px'].copy()
        unit = min(CF._corner_assignments(), key=lambda u: diff(u, cur))
        cur_d = diff(unit, cur)
        size = max(np.ptp(cur[:, 0]), np.ptp(cur[:, 1]))
        def rough(unit, pts):   # patch-box uniformity: boxes clear of every patch edge
            _, sd, ok = CF._sample_via_h(small, CF._homography(np.array(unit), pts), inner=0.35)
            return float(sd.mean()) if ok else 9.0
        for step in (0.03, 0.01, 0.004, 0.0015):
            improved = True
            while improved:
                improved = False
                for ci in range(4):
                    for ax in range(2):
                        for sg in (1.0, -1.0):
                            t = cur.copy(); t[ci, ax] += sg * step * size
                            d = diff(unit, t)
                            if d < cur_d - 1e-6:
                                cur, cur_d, improved = t, d, True
        cur_r = rough(unit, cur)
        for step in (0.004, 0.0015, 0.0006):
            improved = True
            while improved:
                improved = False
                for ci in range(4):
                    for ax in range(2):
                        for sg in (1.0, -1.0):
                            t = cur.copy(); t[ci, ax] += sg * step * size
                            r = rough(unit, t)
                            if r < cur_r - 1e-6:
                                cur, cur_r, improved = t, r, True
        best = dict(score=cur_d, unit=unit, corners_px=(cur + 0.5) * k - 0.5)
        H = CF._homography(np.array(best['unit']), best['corners_px'])
        boxes = patch_boxes(inv, H, inner=0.35)
        meds = np.array([np.median(inv[y0:y1, x0:x1].reshape(-1, 3), axis=0) for y0, y1, x0, x1 in boxes])
        dd = np.abs(meds - stored).max(axis=1); match = float(np.median(dd)); worst = float(dd.max())
        bal_meds = CF.balance_vec(meds, fp)
        valid = (np.all(bal_meds > CF._VALID_LO, axis=1) & np.all(bal_meds < out_max - CF._VALID_MARG, axis=1))
        noise = {}
        for name, j in SHOW.items():
            y0, y1, x0, x1 = boxes[j]
            px = inv[y0:y1, x0:x1].reshape(-1, 3).astype(np.float64)
            lab = lab_pixels(CF.balance_vec(px, fp), M, fr, look)
            lab[:, 1:] *= s
            ab = lab[:, 1:] - np.median(lab[:, 1:], axis=0)
            noise[name] = dict(chroma=float(np.sqrt((ab ** 2).sum(axis=1).mean())),
                               L=float(lab[:, 0].std()), valid=bool(valid[j]))
            cy, cx = (y0 + y1) // 2, (x0 + x1) // 2
            crop = inv[cy - CROP // 2:cy + CROP // 2, cx - CROP // 2:cx + CROP // 2].reshape(-1, 3).astype(np.float64)
            clab = lab_pixels(CF.balance_vec(crop, fp), M, fr, look); clab[:, 1:] *= s
            np.save(os.path.join(OUT, f'{sub}__{fr["name"][:-4]}__{name}.npy'), clab.reshape(CROP, CROP, 3))
            img = (lab_to_display(clab.reshape(CROP, CROP, 3)) * 255 + 0.5).astype(np.uint8)
            Image.fromarray(img).save(os.path.join(OUT, f'{sub}__{fr["name"][:-4]}__{name}.png'))
        grey_d = float(meds[21].mean())   # neutral 5 density → bracket order
        per_frame.append(dict(frame=fr['name'], grey_density=round(grey_d, 3), small_mean_diff=round(best['score'], 4),
                              median_patch_diff=round(match, 4), worst_patch_diff=round(worst, 3), noise=noise))
        print(f"{label:22s} {fr['name'][-24:]:24s} N5 dens {grey_d:5.2f} Δsmall {best['score']:.3f} "
              f"Δmed {match:.3f}/{worst:.2f} | " + '  '.join(f"{k} C{v['chroma']:.2f}/L{v['L']:.2f}{'' if v['valid'] else '*'}"
                                                  for k, v in noise.items()), flush=True)
    results[label] = per_frame
json.dump(results, open(os.path.join(OUT, 'noise.json'), 'w'), indent=1)
