"""Close-up grid of chart patches per arm, every crop shifted to the chart's reference colour
so only the noise differs (crops + Lab arrays come from noise_arms.py).
Run from negacon-converter/: python make_patch_grid.py <noise dir> <out.png> [ev0|ev-2]"""
import sys, numpy as np
sys.path.insert(0, '.')
from PIL import Image, ImageDraw
import chartfit as CF
src = open(__file__.replace('make_patch_grid.py', 'noise_arms.py')).read()
exec(src[src.index('def lab_to_display'):src.index('results = {}')])
NOISE, OUT = sys.argv[1:3]
EI = 1 if len(sys.argv) > 3 and sys.argv[3] == 'ev-2' else 0
REF = {'red': 14, 'blue': 12, 'green': 13, 'neutral 5': 21}
ARMS = [('CS-Lite White', ['06972', '06974'], 'White'), ('RGB Camera-balanced', ['06943', '06945'], 'RGB camera-bal.'),
        ('RGB Sensor-balanced', ['06917', '06919'], 'RGB sensor-bal.'), ('RGB Sensor Unmixed', ['06917_unmixed', '06919_unmixed'], 'RGB unmixed'),
        ('RGB Trichrome', ['07006_trichrome', '07012_trichrome'], 'Trichrome')]
k, c, pad = 3, 96, 8
sheet = Image.new('RGB', (110 + len(ARMS) * (c * k + pad), 30 + len(REF) * (c * k + pad)), (14, 16, 22))
d = ImageDraw.Draw(sheet)
for i, (sub, ns, lab) in enumerate(ARMS):
    d.text((110 + i * (c * k + pad) + 4, 8), lab, fill=(230, 230, 230))
    for j, p in enumerate(REF):
        L = np.load(f'{NOISE}/{sub}__Light Comparison{ns[EI]}__{p}.npy')
        L = L - np.median(L.reshape(-1, 3), axis=0) + CF.CC24_LAB[REF[p]]
        im = Image.fromarray((lab_to_display(L) * 255 + 0.5).astype(np.uint8)).resize((c * k, c * k), Image.NEAREST)
        sheet.paste(im, (110 + i * (c * k + pad), 30 + j * (c * k + pad)))
        if i == 0:
            d.text((8, 30 + j * (c * k + pad) + c * k // 2), p, fill=(230, 230, 230))
sheet.save(OUT)
print(OUT, sheet.size)
