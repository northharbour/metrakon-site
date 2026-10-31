import json, sys, numpy as np
exec(open(sys.argv[0].replace('noise_common.py', 'noise_summary.py')).read().split('for d in sys.argv')[0])
COMMON = [-2, 0, 3]
for d in sys.argv[1:]:
    R = json.load(open(f'{d}/noise.json'))
    print(f'\n== {d.split("/")[-1]} — common exposures {COMMON}: colour noise C per patch (mean over the three), and per exposure (mean of patches)')
    print(f'{"":24s}' + ''.join(f'{p:>10s}' for p in ('red', 'blue', 'green', 'grey')) + '   | ' + ''.join(f'{("EV%+d" % e):>8s}' for e in COMMON) + '   | L')
    for arm, nums in STOPS.items():
        rows = {ev: next(r for r in R[arm] if n in r['frame']) for n, ev in zip(nums, EV)}
        pp = {p: np.mean([rows[e]['noise'][p]['chroma'] for e in COMMON if rows[e]['noise'][p]['valid']]) for p in ('red', 'blue', 'green', 'neutral 5')}
        pe = [np.mean([v['chroma'] for v in rows[e]['noise'].values() if v['valid']]) for e in COMMON]
        L = np.mean([v['L'] for e in COMMON for v in rows[e]['noise'].values() if v['valid']])
        print(f'{arm:24s}' + ''.join(f'{pp[p]:10.2f}' for p in pp) + '   | ' + ''.join(f'{x:8.2f}' for x in pe) + f'   | {L:.2f}')
