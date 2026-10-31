"""Noise against exposure: every bracket frame (−3…+3) of each article arm, all six grey patches
plus red, green and blue, colour (a*b*) and lightness (L*) noise at matched colour.

Same measurement as noise_arms.py (half-size decode, profile's picked base, each frame's own
stored tone map — so the stretch Obelisk applies to thin frames is included — the profile's
matrix and look, a*b* scaled by the arm's saturation-to-chart factor). Frames where the chart
isn't found from the default seeds are retried from the corners of a frame of the same arm
that was. A patch outside the calibrated density range is still measured, and flagged.
Run from negacon-converter/:
  python noise_by_exposure.py <db copy> <Charts dir> <scores.json> <out.json>"""
import ast, json, os, sqlite3, sys
import numpy as np
sys.path.insert(0, '.')
import pipeline as P
import chartfit as CF

DB, CHARTS, SCORES, OUT = sys.argv[1:5]
ARMS = [(99, 'White (CS-Lite)', 'CS-Lite White'), (105, 'RGB, camera-balanced', 'RGB Camera-balanced'),
        (102, 'RGB, sensor-balanced', 'RGB Sensor-balanced'), (108, 'RGB, trichrome', 'RGB Trichrome')]
EV = [0, -1, -2, -3, 1, 2, 3]                       # shooting order of every bracket
PATCHES = {'white': 18, 'neutral 8': 19, 'neutral 6.5': 20, 'neutral 5': 21, 'neutral 3.5': 22, 'black': 23,
           'red': 14, 'green': 13, 'blue': 12}
scores = json.load(open(SCORES))
db = sqlite3.connect(DB); db.row_factory = sqlite3.Row
node = next(n for n in ast.parse(open('main.py').read()).body
            if isinstance(n, ast.FunctionDef) and n.name == '_resolve_profile')
ns = {'json': json}; exec(compile(ast.Module([node], []), 'main.py', 'exec'), ns)
resolve = ns['_resolve_profile']
here = os.path.dirname(os.path.abspath(__file__))
src = open(f'{here}/noise_arms.py').read()
exec(src[src.index('def patch_boxes'):src.index('def lab_to_display')])      # patch_boxes, lab_pixels


def refine(small, stored, corners):
    """Orientation by the stored medians, corners by them, then by patch uniformity."""
    def diff(unit, pts):
        m, _, ok = CF._sample_via_h(small, CF._homography(np.array(unit), pts))
        return float(np.abs(m - stored).mean()) if ok else 9.0
    def rough(unit, pts):
        _, sd, ok = CF._sample_via_h(small, CF._homography(np.array(unit), pts), inner=0.35)
        return float(sd.mean()) if ok else 9.0
    cur = corners.copy()
    unit = min(CF._corner_assignments(), key=lambda u: diff(u, cur))
    size = max(np.ptp(cur[:, 0]), np.ptp(cur[:, 1]))
    for fn, steps in ((diff, (0.03, 0.01, 0.004, 0.0015)), (rough, (0.004, 0.0015, 0.0006))):
        val = fn(unit, cur)
        for step in steps:
            improved = True
            while improved:
                improved = False
                for ci in range(4):
                    for ax in range(2):
                        for sg in (1.0, -1.0):
                            t = cur.copy(); t[ci, ax] += sg * step * size
                            v = fn(unit, t)
                            if v < val - 1e-6:
                                cur, val, improved = t, v, True
    return unit, cur, diff(unit, cur)


results = {}
for pid, label, sub in ARMS:
    row = db.execute('SELECT * FROM profiles WHERE id=?', (pid,)).fetchone()
    chart = json.loads(row['calib_samples'])['chart']
    fp = json.loads(row['channel_balance'])
    M = np.asarray(json.loads(row['density_matrix']))
    look = CF.reference_look(dict(resolve(row), density_matrix=None))
    s = scores[label]['sat_suggest']
    base = np.asarray(chart['base_pick']['base'])
    out_max = float(fp['out'][-1])
    frames = []
    for fr in chart['frames']:
        inv = P.invert_negative(P.load_raw(os.path.join(CHARTS, sub, fr['name']), half_size=True, wb_mode='unity'), base)
        k = 4; h4, w4 = inv.shape[0] // k, inv.shape[1] // k
        small = inv[:h4 * k, :w4 * k].reshape(h4, k, w4, k, 3).mean(axis=(1, 3))
        best = None
        for seed in ([(0.33, 0.27), (0.70, 0.27), (0.70, 0.75), (0.33, 0.75)],
                     [(0.30, 0.22), (0.73, 0.22), (0.73, 0.80), (0.30, 0.80)]):
            c = CF.locate_chart(small, seed, refine=False, search=True)
            if c and (best is None or c['score'] > best['score']):
                best = c
        unit, cur, d = refine(small, np.asarray(fr['meds']), best['corners_px'])
        frames.append(dict(fr=fr, inv=inv, small=small, unit=unit, cur=cur, d=d))
    # retry poorly matched frames from the corners of the best-matched frames of this arm
    good = sorted([f for f in frames if f['d'] < 0.02], key=lambda f: f['d'])
    for f in frames:
        if f['d'] >= 0.02:
            for g in good[:3]:
                frac = g['cur'] / np.array([g['small'].shape[1], g['small'].shape[0]])
                c = CF.locate_chart(f['small'], [tuple(p) for p in frac], refine=False, search=True)
                if not c:
                    continue
                unit, cur, d = refine(f['small'], np.asarray(f['fr']['meds']), c['corners_px'])
                if d < f['d']:
                    f.update(unit=unit, cur=cur, d=d)
    per = []
    for f, ev in zip(frames, EV):
        fr, inv = f['fr'], f['inv']
        H = CF._homography(np.array(f['unit']), (f['cur'] + 0.5) * 4 - 0.5)
        boxes = patch_boxes(inv, H, inner=0.35)
        meds = np.array([np.median(inv[y0:y1, x0:x1].reshape(-1, 3), axis=0) for y0, y1, x0, x1 in boxes])
        bal = CF.balance_vec(meds, fp)
        valid = np.all(bal > CF._VALID_LO, axis=1) & np.all(bal < out_max - CF._VALID_MARG, axis=1)
        noise = {}
        for name, j in PATCHES.items():
            y0, y1, x0, x1 = boxes[j]
            lab = lab_pixels(CF.balance_vec(inv[y0:y1, x0:x1].reshape(-1, 3).astype(np.float64), fp), M, fr, look)
            lab[:, 1:] *= s
            ab = lab[:, 1:] - np.median(lab[:, 1:], axis=0)
            noise[name] = dict(chroma=round(float(np.sqrt((ab ** 2).sum(axis=1).mean())), 3),
                               L=round(float(lab[:, 0].std()), 3), Lmean=round(float(lab[:, 0].mean()), 1),
                               valid=bool(valid[j]))
        per.append(dict(frame=fr['name'], ev=ev, located=round(f['d'], 4), noise=noise))
        print(f"{label:22s} EV{ev:+d} {fr['name'][-22:]:22s} match {f['d']:.3f}  " +
              '  '.join(f"{n[:6]} {v['chroma']:5.2f}/{v['L']:4.2f}{'' if v['valid'] else '*'}" for n, v in noise.items()), flush=True)
    results[label] = per
json.dump(results, open(OUT, 'w'), indent=1)
