"""Summary of noise_by_exposure.json: per exposure, mean colour (a*b*) and lightness noise over
the in-range patches (greys neutral 8 → 3.5 and red/green/blue; black excluded: near L*=0 its
a*b* spread means nothing; white excluded: on dense frames it is compressed to paper white)."""
import json, sys
import numpy as np
R = json.load(open(sys.argv[1]))
USE = ['neutral 8', 'neutral 6.5', 'neutral 5', 'neutral 3.5', 'red', 'green', 'blue']
arms = list(R)
for metric, lab in (('chroma', 'COLOUR noise (a*b*, matched colour)'), ('L', 'LIGHTNESS noise (L*)')):
    print(f'\n{lab}: mean over in-range patches; (n) = patches used')
    print(f'{"EV":>4s}' + ''.join(f'{a:>24s}' for a in arms))
    for ev in (-3, -2, -1, 0, 1, 2, 3):
        cells = []
        for a in arms:
            f = next(x for x in R[a] if x['ev'] == ev)
            v = [f['noise'][p][metric] for p in USE if f['noise'][p]['valid']]
            cells.append(f'{np.mean(v):6.2f} ({len(v)})' if v else '      –')
        print(f'{ev:+4d}' + ''.join(f'{c:>24s}' for c in cells))
print('\nsame patch set at every exposure where all arms have it in range (fair cross-arm comparison):')
for ev in (-3, -2, -1, 0, 1, 2, 3):
    fs = {a: next(x for x in R[a] if x['ev'] == ev) for a in arms}
    common = [p for p in USE if all(fs[a]['noise'][p]['valid'] for a in arms)]
    if not common:
        continue
    vals = {a: np.mean([fs[a]['noise'][p]['chroma'] for p in common]) for a in arms}
    w = vals['White (CS-Lite)']
    print(f'{ev:+4d}  ' + '   '.join(f'{a.split(",")[-1].strip()[:14]:>14s} {v:5.2f} ({100 * (v / w - 1):+4.0f}%)' for a, v in vals.items()) + f'   [{len(common)} patches]')
