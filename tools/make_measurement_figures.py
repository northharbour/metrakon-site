"""Generate the 'Built as an instrument' measurement figures as dark-theme SVGs.

    python tools/make_measurement_figures.py [path\to\negacon.db]

Reads a REAL calibrated profile (Vision3 250D, id 30) from the app database and writes:
    assets/fp_fingerprint.svg   the per-channel density fingerprint (curve + points)
    assets/fp_matrix.svg        the fitted colour matrix acting on the 24 chart patches

DELIBERATE: no numeric axis labels — the plots show real measured shapes, but the
calibration values themselves (the product's IP) are not reconstructable from them.
"""
import json
import sqlite3
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
DB = Path(sys.argv[1]) if len(sys.argv) > 1 else \
    HERE.parent / 'negacon-converter' / 'data' / 'negacon.db'
PROFILE_ID = 30           # Vision3 250D (RGB) — fingerprint + matrix + stored chart samples

BG, GRID, TEXT = '#0e0e0e', '#242424', '#8a8a8a'
CH_COL = {'r': '#d4574a', 'g': '#9f9fa2', 'b': '#4fc8dd'}
# classic ColorChecker 24 sRGB swatches, row-major (patch sampling order)
CC = ['#735244', '#c29682', '#627a9d', '#576c43', '#8580b1', '#67bdaa',
      '#d67e2c', '#505ba6', '#c15a63', '#5e3c6c', '#9dbc40', '#e0a32e',
      '#383d96', '#469449', '#af363c', '#e7c71f', '#bb5695', '#0885a1',
      '#f3f3f2', '#c8c8c8', '#a0a0a0', '#7a7a79', '#555555', '#343434']
W, H = 720, 480


def interp(x, xs, ys):
    if x <= xs[0]: return ys[0]
    if x >= xs[-1]: return ys[-1]
    for i in range(1, len(xs)):
        if x <= xs[i]:
            f = (x - xs[i - 1]) / max(xs[i] - xs[i - 1], 1e-9)
            return ys[i - 1] + f * (ys[i] - ys[i - 1])
    return ys[-1]


def svg_head():
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
            f'font-family="ui-monospace,Menlo,Consolas,monospace" font-size="13">\n'
            f'<rect width="{W}" height="{H}" fill="{BG}"/>\n')


def fingerprint_svg(cb):
    out = cb['out']
    xmax = max(max(cb[c]) for c in 'rgb') * 1.06
    ymax = max(out) * 1.08
    L, R_, T, B_ = 56, 24, 26, 52          # margins
    pw, ph = W - L - R_, H - T - B_
    X = lambda v: L + v / xmax * pw
    Y = lambda v: T + ph - v / ymax * ph
    s = svg_head()
    for f in (0.25, 0.5, 0.75, 1.0):       # quiet quarter grid, unlabelled
        s += f'<line x1="{L}" y1="{Y(ymax*f/1.08):.1f}" x2="{L+pw}" y2="{Y(ymax*f/1.08):.1f}" stroke="{GRID}"/>\n'
        s += f'<line x1="{X(xmax*f/1.06):.1f}" y1="{T}" x2="{X(xmax*f/1.06):.1f}" y2="{T+ph}" stroke="{GRID}"/>\n'
    s += f'<line x1="{L}" y1="{T+ph}" x2="{L+pw}" y2="{T+ph}" stroke="{TEXT}" stroke-width="1.2"/>\n'
    s += f'<line x1="{L}" y1="{T}" x2="{L}" y2="{T+ph}" stroke="{TEXT}" stroke-width="1.2"/>\n'
    for c in 'rgb':
        pts = sorted(zip(cb[c], out))
        path = ' '.join(f'{X(x):.1f},{Y(y):.1f}' for x, y in pts)
        s += f'<polyline points="{path}" fill="none" stroke="{CH_COL[c]}" stroke-width="2.2"/>\n'
        for x, y in pts:
            s += f'<circle cx="{X(x):.1f}" cy="{Y(y):.1f}" r="4" fill="{CH_COL[c]}" stroke="{BG}" stroke-width="1.2"/>\n'
    s += (f'<text x="{L+pw/2:.0f}" y="{H-16}" fill="{TEXT}" text-anchor="middle">'
          f'measured channel density above film base &#8594;</text>\n')
    s += (f'<text x="18" y="{T+ph/2:.0f}" fill="{TEXT}" text-anchor="middle" '
          f'transform="rotate(-90 18 {T+ph/2:.0f})">reference density &#8594;</text>\n')
    lx = L + 18
    for c, name in (('r', 'red'), ('g', 'green'), ('b', 'blue')):
        s += f'<circle cx="{lx}" cy="{T+14}" r="5" fill="{CH_COL[c]}"/>\n'
        s += f'<text x="{lx+11}" y="{T+18}" fill="{TEXT}">{name}</text>\n'
        lx += 72
    return s + '</svg>\n'


def matrix_svg(cb, M, meds):
    out = cb['out']
    bal = []
    for m in meds:
        bal.append([interp(m[i], cb[c], out) for i, c in enumerate('rgb')])
    post = [[sum(M[r][c] * v[c] for c in range(3)) for r in range(3)] for v in bal]
    chroma = lambda v: (v[0] - v[1], v[2] - v[1])          # (R−G, B−G) in density
    pre_c, post_c = [chroma(v) for v in bal], [chroma(v) for v in post]
    rng = max(abs(x) for p in pre_c + post_c for x in p) * 1.15
    # square plot area centred horizontally, vertical margins 20/56
    T, ph = 20, H - 76
    Xp = lambda v: (W - ph) / 2 + (v + rng) / (2 * rng) * ph
    Yp = lambda v: T + ph - (v + rng) / (2 * rng) * ph
    s = svg_head()
    x0, y0 = Xp(0), Yp(0)
    s += f'<line x1="{Xp(-rng):.1f}" y1="{y0:.1f}" x2="{Xp(rng):.1f}" y2="{y0:.1f}" stroke="{GRID}" stroke-width="1.4"/>\n'
    s += f'<line x1="{x0:.1f}" y1="{Yp(-rng):.1f}" x2="{x0:.1f}" y2="{Yp(rng):.1f}" stroke="{GRID}" stroke-width="1.4"/>\n'
    for f in (0.5, 1.0):                    # neutral rings, unlabelled
        r = f * rng / (2 * rng) * ph
        s += (f'<circle cx="{x0:.1f}" cy="{y0:.1f}" r="{r:.1f}" fill="none" '
              f'stroke="{GRID}" stroke-dasharray="3 5"/>\n')
    order = sorted(range(24), key=lambda i: i < 18)   # greys first, colours on top
    for i in order:
        grey = i >= 18
        col = CC[i]
        (x1, y1), (x2, y2) = pre_c[i], post_c[i]
        r = 4 if grey else 6
        if not grey:
            s += (f'<line x1="{Xp(x1):.1f}" y1="{Yp(y1):.1f}" x2="{Xp(x2):.1f}" y2="{Yp(y2):.1f}" '
                  f'stroke="{col}" stroke-width="2" opacity="0.75"/>\n')
        s += (f'<circle cx="{Xp(x1):.1f}" cy="{Yp(y1):.1f}" r="{r}" fill="none" '
              f'stroke="{col}" stroke-width="2" opacity="0.85"/>\n')
        s += (f'<circle cx="{Xp(x2):.1f}" cy="{Yp(y2):.1f}" r="{r}" fill="{col}" '
              f'stroke="{BG}" stroke-width="1.4"/>\n')
    s += (f'<text x="{W/2:.0f}" y="{H-34}" fill="{TEXT}" text-anchor="middle">'
          f'red &#8596; green</text>\n')
    s += (f'<text x="{W/2:.0f}" y="{H-14}" fill="{TEXT}" text-anchor="middle" font-size="12">'
          f'24 chart patches &#183; open = measured, filled = corrected &#183; greys stay centred</text>\n')
    s += (f'<text x="{(W-ph)/2-10:.0f}" y="{T+ph/2:.0f}" fill="{TEXT}" text-anchor="middle" '
          f'transform="rotate(-90 {(W-ph)/2-10:.0f} {T+ph/2:.0f})">blue &#8596; green</text>\n')
    return s + '</svg>\n'


def main():
    conn = sqlite3.connect(f'file:{DB}?mode=ro', uri=True)
    row = conn.execute(
        'SELECT channel_balance, density_matrix, calib_samples FROM profiles WHERE id=?',
        (PROFILE_ID,)).fetchone()
    conn.close()
    cb = json.loads(row[0])
    M = json.loads(row[1])
    frames = json.loads(row[2])['chart']['frames']
    meds = frames[len(frames) // 2]['meds']         # mid-bracket frame
    (HERE / 'assets' / 'fp_fingerprint.svg').write_text(fingerprint_svg(cb), encoding='utf-8')
    (HERE / 'assets' / 'fp_matrix.svg').write_text(matrix_svg(cb, M, meds), encoding='utf-8')
    print('wrote assets/fp_fingerprint.svg, assets/fp_matrix.svg')


if __name__ == '__main__':
    main()
