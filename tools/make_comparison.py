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


def main(src_dir: str) -> None:
    src = Path(src_dir)
    out_root = Path(__file__).resolve().parent.parent / 'assets' / 'comp'
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
