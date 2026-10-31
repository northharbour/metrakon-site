import sys, io, glob, os, rawpy
from PIL import Image, ImageDraw
folder, out = sys.argv[1], sys.argv[2]
files = sorted(glob.glob(os.path.join(folder, '*.ARW')))
tw, cols = 360, 6
tiles = []
for f in files:
    with rawpy.imread(f) as r:
        t = r.extract_thumb()
    im = Image.open(io.BytesIO(t.data)).convert('RGB')
    im.thumbnail((tw, tw))
    tiles.append((os.path.basename(f)[-9:-4], im))
th = max(im.height for _, im in tiles)
rows = (len(tiles) + cols - 1) // cols
sheet = Image.new('RGB', (cols * (tw + 8), rows * (th + 26)), (20, 20, 20))
d = ImageDraw.Draw(sheet)
for i, (n, im) in enumerate(tiles):
    x, y = (i % cols) * (tw + 8), (i // cols) * (th + 26)
    sheet.paste(im, (x, y + 20)); d.text((x + 4, y + 4), n, fill=(255, 200, 80))
sheet.save(out, quality=85)
print(len(tiles), sheet.size)
