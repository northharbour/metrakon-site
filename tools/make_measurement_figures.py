"""Generate the 'Built as an instrument' measurement figures as dark-theme SVGs.

    python tools/make_measurement_figures.py [path\to\negacon.db]

Faithful ports of the APP'S OWN fingerprint-viewer plots (the ones Ben approved),
computed from a real production calibration (Kodak Gold 200, profile 19) through the
app's pipeline itself:

    assets/fp_fingerprint.svg   neutral-cast view: R−G / B−G deviation vs input density —
                                smoothed use-time curves (pipeline._fp_channel_pairs),
                                measured points as dots, the AGED calibration dashed
    assets/fp_matrix.svg        colour view: hue ring with arrows showing how the fitted
                                density matrix moves each hue, plus the summary stats

The cast plot shows channel DIFFERENCES and the ring shows relative moves — neither
exposes the absolute per-channel calibration maps (the product's IP).
"""
import json
import math
import sqlite3
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
DB = Path(sys.argv[1]) if len(sys.argv) > 1 else \
    HERE.parent / 'negacon-converter' / 'data' / 'negacon.db'
APP = HERE.parent / 'negacon-converter'
PROFILE = 19              # Kodak Gold 200 (RGB): fingerprint + aged fingerprint + matrix

BG, GRID, TEXT, ZERO = '#0e0e0e', '#242424', '#8a8a8a', '#4a4a4a'
RG_COL, BG_COL = '#c5852d', '#4fc8dd'      # the app viewer's R−G / B−G colours
W, H = 720, 480

sys.path.insert(0, str(APP))
import numpy as np           # noqa: E402  (the app venv provides it)
import pipeline as apppipe   # noqa: E402


def svg_head():
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
            f'font-family="ui-monospace,Menlo,Consolas,monospace" font-size="12.5">\n'
            f'<rect width="{W}" height="{H}" fill="{BG}"/>\n')


def _maps(cb):
    """Per-channel smoothed use-time maps (dense x, y arrays) via the app pipeline."""
    return {c: [np.asarray(a, float) for a in apppipe._fp_channel_pairs(cb, c)] for c in 'rgb'}


def neutral_cast_svg(cb, cb_aged):
    m = _maps(cb)
    hi = min(float(m[c][0][-1]) for c in 'rgb')          # common calibrated range
    d = np.linspace(0.0, hi, 240)
    ev = lambda mm, x: np.interp(x, mm[0], mm[1])
    rg = ev(m['r'], d) - ev(m['g'], d)
    bgc = ev(m['b'], d) - ev(m['g'], d)
    curves = [(rg, RG_COL, False), (bgc, BG_COL, False)]
    if cb_aged:
        ma = _maps(cb_aged)
        hia = min(float(ma[c][0][-1]) for c in 'rgb')
        da = np.linspace(0.0, min(hi, hia), 240)
        curves.append(((ev(ma['r'], da) - ev(ma['g'], da), da), RG_COL, True))
        curves.append(((ev(ma['b'], da) - ev(ma['g'], da), da), BG_COL, True))
    ymax = max(float(np.max(np.abs(c[0][0] if isinstance(c[0], tuple) else c[0])))
               for c in curves) * 1.3
    ymax = max(ymax, 0.2)
    L, R_, T, B_ = 64, 22, 22, 66
    pw, ph = W - L - R_, H - T - B_
    X = lambda v: L + v / hi * pw
    Y = lambda v: T + ph / 2 - v / ymax * ph / 2
    s = svg_head()
    for f in (0.25, 0.5, 0.75, 1.0):
        s += f'<line x1="{X(hi*f):.1f}" y1="{T}" x2="{X(hi*f):.1f}" y2="{T+ph}" stroke="{GRID}"/>\n'
    for yv in (-ymax / 1.3, -ymax / 2.6, ymax / 2.6, ymax / 1.3):
        s += f'<line x1="{L}" y1="{Y(yv):.1f}" x2="{L+pw}" y2="{Y(yv):.1f}" stroke="{GRID}"/>\n'
    s += f'<line x1="{L}" y1="{Y(0):.1f}" x2="{L+pw}" y2="{Y(0):.1f}" stroke="{ZERO}" stroke-width="1.4"/>\n'
    s += f'<line x1="{L}" y1="{T}" x2="{L}" y2="{T+ph}" stroke="{TEXT}"/>\n'
    # ticks
    for f in (0.0, 0.25, 0.5, 0.75, 1.0):
        s += (f'<text x="{X(hi*f):.0f}" y="{T+ph+18}" fill="{TEXT}" text-anchor="middle">'
              f'{hi*f:.1f}</text>\n')
    for yv in (-ymax / 1.3, 0.0, ymax / 1.3):
        s += (f'<text x="{L-8}" y="{Y(yv)+4:.1f}" fill="{TEXT}" text-anchor="end">'
              f'{yv:+.2f}'.replace('+0.00', '0.00') + '</text>\n')
    # curves (solid fresh, dashed aged)
    for data, col, dashed in curves:
        ys, xs = (data[0], data[1]) if isinstance(data, tuple) else (data, d)
        path = ' '.join(f'{X(float(x)):.1f},{Y(float(y)):.1f}' for x, y in zip(xs, ys))
        dash = ' stroke-dasharray="6 5"' if dashed else ''
        s += f'<polyline points="{path}" fill="none" stroke="{col}" stroke-width="2.4"{dash}/>\n'
    # measured points: raw control points of the FRESH fp, cast vs the green map
    out = np.asarray(cb['out'], float)
    for ch, col in (('r', RG_COL), ('b', BG_COL)):
        xs = np.asarray(cb[ch], float)
        keep = xs <= hi
        ys = out[keep] - np.interp(xs[keep], m['g'][0], m['g'][1])
        for x, y in zip(xs[keep], ys):
            s += (f'<circle cx="{X(float(x)):.1f}" cy="{Y(float(y)):.1f}" r="4" '
                  f'fill="{col}" stroke="{BG}" stroke-width="1.2"/>\n')
    s += (f'<text x="{L+pw/2:.0f}" y="{H-26}" fill="{TEXT}" text-anchor="middle">'
          f'input density</text>\n')
    s += (f'<text x="20" y="{T+ph/2:.0f}" fill="{TEXT}" text-anchor="middle" '
          f'transform="rotate(-90 20 {T+ph/2:.0f})">neutral cast (channel &#8722; green)</text>\n')
    s += (f'<text x="{L}" y="{H-8}" fill="{TEXT}">'
          f'<tspan fill="{RG_COL}">&#9644;</tspan> R&#8722;G  '
          f'<tspan fill="{BG_COL}">&#9644;</tspan> B&#8722;G &#183; dots = measured points'
          + (' &#183; &#8211;&#8211; aged' if cb_aged else '') + '</text>\n')
    return s + '</svg>\n'


def _hue_colour(theta_deg):
    """Plane angle → display colour (+x red, +y blue, −x cyan, −y yellow)."""
    h = (360.0 - theta_deg) % 360.0
    c, x = 0.62, 0.62 * (1 - abs((h / 60.0) % 2 - 1))
    seq = [(c, x, 0), (x, c, 0), (0, c, x), (0, x, c), (x, 0, c), (c, 0, x)]
    r, g, b = seq[int(h // 60) % 6]
    to = lambda v: int((v + 0.28) * 255)
    return f'#{to(r):02x}{to(g):02x}{to(b):02x}'


def matrix_ring_svg(M):
    chroma = lambda v: (v[0] - v[1], v[2] - v[1])
    pre, post, cols = [], [], []
    for k in range(12):
        th = k * 30.0
        a, b = math.cos(math.radians(th)), math.sin(math.radians(th))
        g = -(a + b) / 3.0
        v = [a + g, g, b + g]                    # mean-free density vector with that chroma
        mv = [sum(M[r][c] * v[c] for c in range(3)) for r in range(3)]
        pre.append((a, b)); post.append(chroma(mv)); cols.append(_hue_colour(th))
    sat = sum(math.hypot(*p) for p in post) / 12.0
    hue_shifts = []
    for (a, b), (a2, b2) in zip(pre, post):
        dth = math.degrees(math.atan2(b2, a2) - math.atan2(b, a))
        dth = (dth + 180) % 360 - 180
        hue_shifts.append(dth)
    mx_shift = max(hue_shifts, key=abs)
    names = 'RGB'
    off = [(abs(M[i][j]), f'{names[i]}&#8592;{names[j]}')
           for i in range(3) for j in range(3) if i != j]
    ct_v, ct_n = max(off)
    det = (M[0][0] * (M[1][1] * M[2][2] - M[1][2] * M[2][1])
           - M[0][1] * (M[1][0] * M[2][2] - M[1][2] * M[2][0])
           + M[0][2] * (M[1][0] * M[2][1] - M[1][1] * M[2][0]))
    rng = max(max(math.hypot(*p) for p in post), 1.0) * 1.5
    T, ph = 18, H - 72
    Xp = lambda v: (W - ph) / 2 + (v + rng) / (2 * rng) * ph
    Yp = lambda v: T + ph - (v + rng) / (2 * rng) * ph
    s = svg_head()
    x0, y0 = Xp(0), Yp(0)
    s += f'<line x1="{Xp(-rng):.1f}" y1="{y0:.1f}" x2="{Xp(rng):.1f}" y2="{y0:.1f}" stroke="{ZERO}"/>\n'
    s += f'<line x1="{x0:.1f}" y1="{Yp(-rng):.1f}" x2="{x0:.1f}" y2="{Yp(rng):.1f}" stroke="{ZERO}"/>\n'
    ring_r = 1.0 / (2 * rng) * ph
    s += (f'<circle cx="{x0:.1f}" cy="{y0:.1f}" r="{ring_r:.1f}" fill="none" '
          f'stroke="{TEXT}" stroke-dasharray="4 6" opacity="0.6"/>\n')
    for (a, b), (a2, b2), col in zip(pre, post, cols):
        x1, y1, x2, y2 = Xp(a), Yp(b), Xp(a2), Yp(b2)
        s += f'<circle cx="{x1:.1f}" cy="{y1:.1f}" r="4.5" fill="{col}"/>\n'
        s += (f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
              f'stroke="{col}" stroke-width="2.6"/>\n')
        ang = math.atan2(y2 - y1, x2 - x1)
        for da in (math.radians(155), math.radians(-155)):
            s += (f'<line x1="{x2:.1f}" y1="{y2:.1f}" '
                  f'x2="{x2 + 9*math.cos(ang+da):.1f}" y2="{y2 + 9*math.sin(ang+da):.1f}" '
                  f'stroke="{col}" stroke-width="2.6"/>\n')
    s += f'<text x="{Xp(rng)-6:.0f}" y="{y0-8:.1f}" fill="{TEXT}" text-anchor="end">R&#8722;G &#8594; red</text>\n'
    s += f'<text x="{Xp(-rng)+6:.0f}" y="{y0-8:.1f}" fill="{TEXT}">cyan</text>\n'
    s += f'<text x="{x0+8:.1f}" y="{Yp(rng)+16:.1f}" fill="{TEXT}">B&#8722;G &#8594; blue</text>\n'
    s += f'<text x="{x0+8:.1f}" y="{Yp(-rng)-6:.1f}" fill="{TEXT}">yellow</text>\n'
    s += (f'<text x="{(W-ph)/2:.0f}" y="{H-10}" fill="{TEXT}">'
          f'arrows = how the matrix moves each hue &#183; dashed = input chroma</text>\n')
    s += (f'<text x="{(W+ph)/2:.0f}" y="{H-10}" fill="{TEXT}" text-anchor="end">'
          f'saturation &#215;{sat:.2f} &#183; max hue shift {mx_shift:+.0f}&#176; &#183; '
          f'crosstalk {ct_v:.2f} ({ct_n}) &#183; det {det:.2f}</text>\n')
    return s + '</svg>\n'


def main():
    conn = sqlite3.connect(f'file:{DB}?mode=ro', uri=True)
    row = conn.execute(
        'SELECT channel_balance, channel_balance_aged, density_matrix FROM profiles WHERE id=?',
        (PROFILE,)).fetchone()
    conn.close()
    cb = json.loads(row[0])
    cb_aged = json.loads(row[1]) if row[1] else None
    M = json.loads(row[2])
    (HERE / 'assets' / 'fp_fingerprint.svg').write_text(neutral_cast_svg(cb, cb_aged), encoding='utf-8')
    (HERE / 'assets' / 'fp_matrix.svg').write_text(matrix_ring_svg(M), encoding='utf-8')
    print('wrote assets/fp_fingerprint.svg, assets/fp_matrix.svg  [Kodak Gold 200]')


if __name__ == '__main__':
    main()
