"""Build web-sized comparison assets from the conversion test sets.

Usage:
    python tools/make_comparison.py ["C:/Users/Blix/Pictures/Private/Ben"]

The source root holds one folder per film-stock comparison set (SETS below). Each
set is the same 7-frame chart bracket converted by the four tools, plus (optionally)
a sample set of varied real scenes converted at the same defaults. Writes:

    assets/comp/thumb/{tool}_{frame}.jpg   grid tiles   (520 px wide, q80)
    assets/comp/large/{tool}_{frame}.jpg   viewer size  (1500 px wide, q82)

Frame numbers are unique across stocks, so all stocks share the two output dirs.
Tool keys and frame lists must match the SETS config in index.html's comparison
script. Re-run after changing the source exports; output filenames are stable.
"""
import sys
from pathlib import Path
from PIL import Image, ImageOps

DEFAULT_SRC = 'C:/Users/Blix/Pictures/Private/Ben'

SETS = {
    'gold': {
        'folder': 'Conversion Comp Gold',
        'frames': ['09519', '09520', '09521', '09522', '09523', '09524', '09525'],
        'tools': {
            'metrakon':     'Metrakon White/Gold_0003_Easy35 Gold Ref{f}.jpg',
            'filmlab':      'Filmlab/Easy35 Gold Ref{f}.ARW.jpg',
            'nlp':          'NegativeLabPro/Untitled Export/Easy35 Gold Ref{f}.jpg',
            'smartconvert': 'SmartConvert/JPG/Easy35 Gold Ref{f}.jpg',
        },
        'samples': [],
        'sample_tools': {},
    },
    '250d': {
        'folder': 'Conversion Comp 250D',
        'frames': ['06570', '06571', '06572', '06573', '06574', '06575', '06576'],
        'tools': {
            'metrakon':     'Metrakon/Easy35Scans{f}.jpg',
            'filmlab':      'Filmlab/Easy35Scans{f}.ARW.jpg',
            'nlp':          'NLP/Untitled Export/Easy35Scans{f}.jpg',
            'smartconvert': 'SMartConvert/JPG/Easy35Scans{f}.jpg',
        },
        # varied real scenes from the same stock, converted at the same defaults
        'samples': ['06553', '06555', '06556', '06559', '06563',
                    '06577', '06582', '06583', '06585', '06587'],
        'sample_tools': {
            'metrakon':     'Metrakon/Sampleset/Easy35Scans{f}.jpg',
            'filmlab':      'Filmlab/Sampleset/Easy35Scans{f}.ARW.jpg',
            'nlp':          'NLP/SampleSet/Easy35Scans{f}.jpg',
            'smartconvert': 'SMartConvert/Sampleset/JPG/Easy35Scans{f}.jpg',
        },
    },
}

SIZES = {'thumb': (520, 80), 'large': (1500, 82)}   # name → (width, jpeg quality)

# Per-file rotation overrides (degrees CCW), for exports whose file is genuinely
# unrotated with no EXIF orientation either (EXIF-tagged files are handled
# generally via exif_transpose on load). FilmLab exported the portrait frame
# 06559 as unrotated landscape; every other tool shows it upright.
ROTATE = {
    ('filmlab', '06559'): 90,
}


# Scan-light pair (RGB daylight-balanced vs RGB sensor-balanced), shown as a wipe
# slider. Rendered at the same width and cropped to a common aspect; the sensor
# image is shifted by the measured 2px@900 vertical offset so the wipe seam aligns.
LIGHT_SET = 'gold'
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


def build_images(src: Path, out_root: Path, tools: dict, frames: list) -> int:
    total = 0
    for size_name, (width, quality) in SIZES.items():
        out = out_root / size_name
        out.mkdir(parents=True, exist_ok=True)
        for tool, pattern in tools.items():
            for f in frames:
                p = src / pattern.format(f=f)
                if not p.exists():
                    print(f'MISSING {p}')
                    continue
                im = ImageOps.exif_transpose(Image.open(p))
                deg = ROTATE.get((tool, f))
                if deg:
                    im = im.rotate(deg, expand=True)
                im.thumbnail((width, width * 10), Image.LANCZOS)
                im.convert('RGB').save(out / f'{tool}_{f}.jpg',
                                       quality=quality, optimize=True)
                total += 1
    return total


def main(src_root: str) -> None:
    root = Path(src_root)
    out_root = Path(__file__).resolve().parent.parent / 'assets' / 'comp'
    out_root.mkdir(parents=True, exist_ok=True)
    build_light_pair(root / SETS[LIGHT_SET]['folder'], out_root)
    total = 0
    for stock, cfg in SETS.items():
        src = root / cfg['folder']
        if not src.is_dir():
            print(f'MISSING set folder {src} — {stock} skipped')
            continue
        n = build_images(src, out_root, cfg['tools'], cfg['frames'])
        n += build_images(src, out_root, cfg['sample_tools'], cfg['samples'])
        total += n
        print(f'{stock}: wrote {n} images')
    n_bytes = sum(p.stat().st_size for p in out_root.rglob('*.jpg'))
    print(f'{total} images written this run, {n_bytes/1e6:.1f} MB total on disk')


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else DEFAULT_SRC)
