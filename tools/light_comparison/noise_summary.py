import json, sys, numpy as np
STOPS = {  # shooting order 0, -1, -2, -3, +1, +2, +3 (confirmed by neutral-5 density)
 'White (CS-Lite)': ['06972', '06973', '06974', '06975', '06976', '06977', '06978'],
 'RGB, camera-balanced': ['06943', '06944', '06945', '06946', '06947', '06948', '06949'],
 'RGB, sensor-balanced': ['06917', '06918', '06919', '06920', '06921', '06922', '06923'],
 'RGB, trichrome': ['07006', '07009', '07012', '07015', '07018', '07021', '07024'],
 'RGB, unmixed': ['06917', '06918', '06919', '06920', '06921', '06922', '06923']}
EV = [0, -1, -2, -3, 1, 2, 3]
for d in sys.argv[1:]:
    R = json.load(open(f'{d}/noise.json')); print(f'\n== {d.split("/")[-1]}: colour noise C (ΔE, at matched colour), frames −2…+3, located cleanly, patch in range')
    print(f'{"":24s}' + ''.join(f'{p:>12s}' for p in ('red', 'blue', 'green', 'neutral 5', 'mean')) + '   L-noise mean')
    for arm, nums in STOPS.items():
        rows = {n: r for r in R[arm] for n in nums if n in r['frame']}
        acc = {p: [] for p in ('red', 'blue', 'green', 'neutral 5')}; Ls = []
        for n, ev in zip(nums, EV):
            r = rows[n]
            if ev < -2 or r['median_patch_diff'] > 0.02: continue
            for p, v in r['noise'].items():
                if v['valid']: acc[p].append(v['chroma']); Ls.append(v['L'])
        m = {p: np.mean(v) for p, v in acc.items()}
        print(f'{arm:24s}' + ''.join(f'{m[p]:12.2f}' for p in acc) + f'{np.mean(list(m.values())):12.2f}' + f'   {np.mean(Ls):.2f}   (n={sum(len(v) for v in acc.values())})')
