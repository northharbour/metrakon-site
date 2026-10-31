# Per frame: each CFA channel's level at the clear film base (99.5th pct of the 2x2-binned
# plane = the brightest film, i.e. the rebate), as % of the sensor's range above black.
import sys, glob, os, json, numpy as np, rawpy
from multiprocessing import Pool
def planes(path):
    with rawpy.imread(path) as r:
        im = r.raw_image_visible.astype(np.float32)
        cols = r.raw_colors_visible; desc = r.color_desc.decode()
        black = np.array(r.black_level_per_channel, np.float32); white = float(r.white_level)
        wb = list(r.camera_whitebalance)
    out = {}
    for c in range(4):
        ys, xs = np.nonzero(cols[:2, :2] == c)
        p = im[ys[0]::2, xs[0]::2] - black[c]
        out.setdefault(desc[c], []).append(p / (white - black[c]))
    return {k: np.mean(v, axis=0) for k, v in out.items()}, wb
def stats(path):
    P, wb = planes(path)
    lv = {k: float(np.percentile(v[::2, ::2], 99.5)) * 100 for k, v in P.items()}
    return os.path.basename(path)[-9:-4], lv, wb
if __name__ == '__main__':
    files = []
    for d in sys.argv[1:]: files += sorted(glob.glob(os.path.join(d, '*.ARW')))
    with Pool(8) as pool: res = pool.map(stats, files)
    for (n, lv, wb), f in zip(res, files):
        print(f"{os.path.basename(os.path.dirname(f)):15s} {n}  R {lv['R']:5.1f}  G {lv['G']:5.1f}  B {lv['B']:5.1f}   camWB {wb[0]:.3f} {wb[1]:.3f} {wb[2]:.3f}")
