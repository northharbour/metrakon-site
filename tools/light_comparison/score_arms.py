"""Score the four light-comparison profiles from their stored chart samples, using
Obelisk's own calibration code (calibrate.build_fingerprint + chartfit.fit_matrix).
Read-only: works on a copy of the app database. Run from negacon-converter/."""
import ast, json, sqlite3, sys
import numpy as np

sys.path.insert(0, '.')
import calibrate as C
import chartfit as CF

DB = sys.argv[1]
ARMS = [(99, 'White (CS-Lite)'), (105, 'RGB, camera-balanced'),
        (102, 'RGB, sensor-balanced'), (108, 'RGB, trichrome'), (111, 'RGB, unmixed')]
GREYS = list(range(18, 24))

# _resolve_profile lifted out of main.py (importing main creates a database)
src = open('main.py').read()
node = next(n for n in ast.parse(src).body if isinstance(n, ast.FunctionDef) and n.name == '_resolve_profile')
ns = {'json': json}
exec(compile(ast.Module([node], []), 'main.py', 'exec'), ns)
resolve = ns['_resolve_profile']

db = sqlite3.connect(DB); db.row_factory = sqlite3.Row


def frames_for(chart, fp):
    return [dict(name=fr['name'], bal=CF.balance_vec(np.asarray(fr['meds'], float), fp),
                 stds=np.asarray(fr['stds']), xs=np.asarray(fr['xs']), ys=np.asarray(fr['ys']),
                 tone_strength=float(fr['ts']))
            for fr in chart['frames'] if 'xs' in fr]


def labs_of(frames, M, look):
    g = float(look.get('gamma') or 2.2)
    return np.stack([CF.display_rgb_to_lab(CF.render_patches(f, M, look), g) for f in frames])


def hue_err(lab):
    th = np.degrees(np.arctan2(CF.CC24_LAB[:, 2], CF.CC24_LAB[:, 1]))
    h = np.degrees(np.arctan2(lab[:, 2], lab[:, 1]))
    return np.abs((h - th + 180) % 360 - 180)


out = {}
for pid, label in ARMS:
    row = db.execute('SELECT * FROM profiles WHERE id=?', (pid,)).fetchone()
    chart = json.loads(row['calib_samples'])['chart']
    pts = [(f'{fr["name"]}#g{g}', np.asarray(fr['meds'][g], float), float(fr['stds'][g]))
           for fr in chart['frames'] for g in GREYS if fr['stds'][g] < 0.6]
    fp, _ = C.build_fingerprint(pts)
    same_fp = json.dumps(fp, sort_keys=True) == json.dumps(json.loads(row['channel_balance']), sort_keys=True)
    prof = dict(resolve(row), channel_balance=fp, density_matrix=None)
    out_max = float(fp['out'][-1])
    frames = frames_for(chart, fp)
    M, rep = CF.fit_matrix(frames, prof, out_max, M0=np.eye(3))
    same_M = np.allclose(M, np.asarray(json.loads(row['density_matrix'])), atol=1e-6)
    look = CF.reference_look(prof)
    masks = [CF.valid_mask(f, out_max) for f in frames]
    for m in masks: m[18:] = False

    # bracket consistency at the fit's chroma scale: each patch's ab spread across frames
    labs = labs_of(frames, M, look); s = rep['sat_suggest']
    spreads = []
    for j in range(18):
        use = [k for k, m in enumerate(masks) if m[j]]
        if len(use) >= 3:
            ab = s * labs[use, j, 1:]
            spreads.append(float(np.sqrt(((ab - ab.mean(axis=0)) ** 2).sum(axis=1).mean())))

    # leave-one-frame-out: refit the matrix on the other six, score the held-out frame
    lofo = []
    for k in range(len(frames)):
        train = frames[:k] + frames[k + 1:]
        Mk, rk = CF.fit_matrix(train, prof, out_max, M0=np.eye(3))
        lab = labs_of([frames[k]], Mk, look)[0]
        m = masks[k]
        if not m.any():
            continue
        sk = rk['sat_suggest']
        d_struct = np.hypot(sk * lab[:, 1] - CF.CC24_LAB[:, 1], sk * lab[:, 2] - CF.CC24_LAB[:, 2])
        lofo.append(dict(frame=frames[k]['name'], n=int(m.sum()),
                         dE_struct=float(d_struct[m].mean()), hue=float(hue_err(lab)[m].mean()),
                         per_patch={CF.CC24_NAMES[j]: round(float(d_struct[j]), 2) for j in range(18) if m[j]}))
    w = np.array([r['n'] for r in lofo], float)
    out[label] = dict(
        pid=pid, rebuild_matches_stored=bool(same_fp and same_M),
        matrix=rep['matrix'], row_norms=[round(float(np.linalg.norm(r)), 3) for r in M],
        sat_suggest=rep['sat_suggest'], n_samples=rep['n_samples'],
        insample=dict(dE_struct=rep['dE_struct_after'], dE00=rep['dE00_after'], hue=rep['hue_degrees_after'],
                      dE_struct_identity=rep['dE_struct_before'], hue_identity=rep['hue_degrees_before']),
        bracket_spread=round(float(np.mean(spreads)), 2),
        holdout=dict(dE_struct=round(float((w * [r['dE_struct'] for r in lofo]).sum() / w.sum()), 2),
                     hue=round(float((w * [r['hue'] for r in lofo]).sum() / w.sum()), 2),
                     frames=[(r['frame'][-25:], r['n'], round(r['dE_struct'], 2)) for r in lofo]),
        per_patch_insample=rep['per_patch_after'],
    )
    print(f"{label:24s} rebuild={out[label]['rebuild_matches_stored']} sat={rep['sat_suggest']} "
          f"rows={out[label]['row_norms']} | in-sample ΔEstruct {rep['dE_struct_after']} hue {rep['hue_degrees_after']}° "
          f"| held-out ΔEstruct {out[label]['holdout']['dE_struct']} hue {out[label]['holdout']['hue']}° "
          f"| bracket spread {out[label]['bracket_spread']}", flush=True)

json.dump(out, open(sys.argv[2], 'w'), indent=1)
