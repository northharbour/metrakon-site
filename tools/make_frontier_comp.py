"""Build the home page's Frontier comparison: the same negatives, Obelisk next to a Frontier.

    python tools/make_frontier_comp.py

Source (SOURCE below): the Frontier JPEGs (Fujifilm Frontier) in the folder root and
Obelisk's exports of the same negatives in Export/<roll>/; PAIRS matches them up. Shown
side by side, so neither image is aligned or retouched — both are only resized (the
Frontier's EXIF orientation applied).

Ben's exports as graded: white balance and density matched to the Frontier. The exports
also carry per-frame contrast, and on three frames a small tone-curve/saturation change,
so the page says WB and density were matched — never "nothing else was changed".

Writes:
    public/assets/frontier/<n>_ob.jpg, <n>_fr.jpg   1600 px long edge
    public/assets/frontier/<n>_t.jpg                picker thumb (Obelisk side)
    src/data/frontier.json                          pair sizes
"""
import json
from pathlib import Path

from PIL import Image, ImageOps

HERE = Path(__file__).resolve().parent.parent
SOURCE = Path(r'C:\Users\Benjamin Hurren\Pictures\Obelisk Feature\Frontier Comp')
ROLL = '01 Gold'
# (RAW name, Frontier JPEG) — the Obelisk export is Export/<ROLL>/Frontier Comp_01_<stem>.jpg
PAIRS = [
    ('Rome 2501097.ARW', 'R1-09940-001A.JPG'),
    ('Rome 2501105.ARW', 'R1-09940-008A.JPG'),
    ('Rome 2501118.ARW', 'R1-09940-022A.JPG'),
    ('Rome 2501130.ARW', 'R1-09940-034A.JPG'),
]
LONG, THUMB_H, Q = 1600, 104, 84


def save(src: Path, dst: Path) -> Image.Image:
    im = ImageOps.exif_transpose(Image.open(src)).convert('RGB')
    im.thumbnail((LONG, LONG), Image.LANCZOS)
    im.save(dst, quality=Q, optimize=True, progressive=True)
    return im


def main() -> None:
    out = HERE / 'public' / 'assets' / 'frontier'
    out.mkdir(parents=True, exist_ok=True)
    for old in out.glob('*.jpg'):
        old.unlink()
    pairs = []
    for n, (raw, fr_name) in enumerate(PAIRS, 1):
        ob = save(SOURCE / 'Export' / ROLL / f'Frontier Comp_01_{Path(raw).stem}.jpg', out / f'{n}_ob.jpg')
        fr = save(SOURCE / fr_name, out / f'{n}_fr.jpg')
        t = ob.copy(); t.thumbnail((THUMB_H * 4, THUMB_H), Image.LANCZOS)
        t.save(out / f'{n}_t.jpg', quality=78, optimize=True)
        pairs.append({'n': n, 'ob': list(ob.size), 'fr': list(fr.size)})
        print(f'{n}: {raw} -> {ob.size}   {fr_name} -> {fr.size}')
    (HERE / 'src' / 'data' / 'frontier.json').write_text(json.dumps({'pairs': pairs}, indent=1) + '\n')
    size = sum(p.stat().st_size for p in out.glob('*.jpg'))
    print(f'{len(pairs)} pairs, {size / 1e6:.1f} MB')


if __name__ == '__main__':
    main()
