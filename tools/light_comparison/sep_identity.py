# Saturation each arm needs with NO colour matrix (identity) vs with its fitted matrix:
# the first is the light's own separation, the gap is what the matrix bought.
import json, sys, numpy as np
sys.argv = [sys.argv[0], sys.argv[1], '/dev/null']
exec(open(sys.argv[0].replace('sep_identity.py', 'score_arms.py')).read().split('out = {}')[0])
def sat_for(frames, M, look, masks):
    labs = labs_of(frames, M, look)
    mm = np.stack(masks); cnt = np.maximum(mm.sum(0), 1)
    imp = np.ones(24); imp[:2] = 2.0
    w2 = np.broadcast_to(imp / cnt, mm.shape)[mm]
    ab_r = labs[:, :, 1:][mm]; ab_t = np.broadcast_to(CF.CC24_LAB[:, 1:], labs[:, :, 1:].shape)[mm]
    return float((w2[:, None] * ab_r * ab_t).sum() / (w2[:, None] * ab_r ** 2).sum())
base = None
for pid, label in ARMS:
    row = db.execute('SELECT * FROM profiles WHERE id=?', (pid,)).fetchone()
    chart = json.loads(row['calib_samples'])['chart']
    fp = json.loads(row['channel_balance']); prof = dict(resolve(row), density_matrix=None)
    out_max = float(fp['out'][-1]); frames = frames_for(chart, fp); look = CF.reference_look(prof)
    masks = [CF.valid_mask(f, out_max) for f in frames]
    for m in masks: m[18:] = False
    M = np.asarray(json.loads(row['density_matrix']))
    s0, s1 = sat_for(frames, np.eye(3), look, masks), sat_for(frames, M, look, masks)
    base = base or s0
    print(f'{label:24s} no matrix: needs x{s0:.2f} (separation {base/s0:4.2f}x white) | with matrix: x{s1:.2f} (separation {base/s1:4.2f}x white)')
