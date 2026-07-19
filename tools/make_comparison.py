"""Build web-sized comparison assets from the conversion test set.

Usage:
    python tools/make_comparison.py "C:/Users/Blix/Pictures/Private/Ben/Conversion Comp"

Reads the four tools' full-resolution exports of the same 7-frame bracket and writes:
    assets/comp/thumb/{tool}_{frame}.jpg   grid tiles   (520 px wide, q80)
    assets/comp/large/{tool}_{frame}.jpg   viewer size  (1500 px wide, q82)

Tool keys here must match the TOOLS config in index.html's comparison script.
Re-run after changing the source exports; output filenames are stable.
"""
import sys
from pathlib import Path
from PIL import Image

FRAMES = ['09519', '09520', '09521', '09522', '09523', '09524', '09525']

# key → (display folder pattern relative to the source dir)
TOOLS = {
    'metrakon':     'Metrakon White/Gold_0003_Easy35 Gold Ref{f}.jpg',
    'filmlab':      'Filmlab/Easy35 Gold Ref{f}.ARW.jpg',
    'nlp':          'NegativeLabPro/Untitled Export/Easy35 Gold Ref{f}.jpg',
    'smartconvert': 'SmartConvert/JPG/Easy35 Gold Ref{f}.jpg',
}

SIZES = {'thumb': (520, 80), 'large': (1500, 82)}   # name → (width, jpeg quality)


# Scan-light pair (RGB daylight-balanced vs RGB sensor-balanced), shown as a wipe
# slider. Rendered at the same width and cropped to a common aspect; the sensor
# image is shifted by the measured 2px@900 vertical offset so the wipe seam aligns.
LIGHT_PAIR = {
    'light_daylight': 'RGB Native WB/RGB Daylight.jpg',
    'light_sensor':   'RGB Native WB/RGB SensorNative.jpg',
}
LIGHT_WIDTH, LIGHT_Q = 1500, 82


def build_light_pair(src: Path, out_root: Path) -> None:
    imgs = {}
    for key, rel in LIGHT_PAIR.items():
        p = src / rel
        if not p.exists():
            print(f'MISSING {p} — light pair skipped')
            return
        im = Image.open(p)
        im.thumbnail((LIGHT_WIDTH, LIGHT_WIDTH * 10), Image.LANCZOS)
        imgs[key] = im
    # common canvas: centre-crop both to the smaller height, nudging the sensor
    # image by the measured alignment offset (scaled to output width)
    h = min(i.height for i in imgs.values())
    w = min(i.width for i in imgs.values())
    dy = round(2 * LIGHT_WIDTH / 900)          # measured: sensor sits 2px low at 900px
    for key, im in imgs.items():
        oy = (im.height - h) // 2 + (dy if key == 'light_sensor' else 0)
        oy = max(0, min(im.height - h, oy))
        box = ((im.width - w) // 2, oy, (im.width - w) // 2 + w, oy + h)
        im.crop(box).convert('RGB').save(out_root / f'{key}.jpg',
                                         quality=LIGHT_Q, optimize=True)
    print(f'light pair: done ({w}x{h})')


def main(src_dir: str) -> None:
    src = Path(src_dir)
    out_root = Path(__file__).resolve().parent.parent / 'assets' / 'comp'
    out_root.mkdir(parents=True, exist_ok=True)
    build_light_pair(src, out_root)
    total = 0
    for size_name, (width, quality) in SIZES.items():
        out = out_root / size_name
        out.mkdir(parents=True, exist_ok=True)
        for tool, pattern in TOOLS.items():
            for f in FRAMES:
                p = src / pattern.format(f=f)
                if not p.exists():
                    print(f'MISSING {p}')
                    continue
                im = Image.open(p)
                im.thumbnail((width, width * 10), Image.LANCZOS)
                dest = out / f'{tool}_{f}.jpg'
                im.convert('RGB').save(dest, quality=quality, optimize=True)
                total += 1
        print(f'{size_name}: done')
    n_bytes = sum(p.stat().st_size for p in out_root.rglob('*.jpg'))
    print(f'{total} images written, {n_bytes/1e6:.1f} MB total')


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
