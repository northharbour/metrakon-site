"""Render the home-page roll demo and the Density sweep through Obelisk's own export path.

    ..\\negacon-converter\\.venv-build\\Scripts\\python tools/make_roll_images.py [--force]

Run it with the APP's venv: rendering imports the app (negacon-converter) and calls the
same two functions its single-frame export runs (_build_pipeline_args + _render_export).

Source: one folder per roll under SOURCE, named the way the lab names roll folders (the
film stock map turns "Gold" into Kodak Gold 200). Every RAW in a roll folder that has an
Obelisk sidecar is used, graded exactly as its sidecar says — open the folder in Obelisk
first, so its frames are in the app's session (the render reads them from the app DB).

The app DB is never written: it is copied (sqlite backup, read-only open) to a temp dir
and the app's data dir is pointed there, so previews/caches/logs land in temp too.
Sidecar writes are blocked. Full renders are cached in tools/.renders/ (gitignored) and
redone only when a frame's grade changes, or with --force.

Writes:
    public/assets/roll/<id>.jpg        hero stage   (1600 px long edge)
    public/assets/roll/<id>_t.jpg      filmstrip    (104 px high)
    public/assets/density/<id>_<i>.jpg Density sweep steps (1600 px long edge)
    public/assets/density/<id>_<i>_t.jpg               (96 px high)
    src/data/rolls.json                rolls, frames, grade values and sweeps for the pages
"""
import hashlib
import json
import os
import shutil
import sqlite3
import sys
import tempfile
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent.parent
APP = HERE.parent / 'negacon-converter'
SOURCE = Path(r'C:\Users\Benjamin Hurren\Pictures\Obelisk Feature')
APP_DB = Path(os.environ.get('LOCALAPPDATA', '')) / 'Programs' / 'Obelisk' / 'data' / 'negacon.db'
CACHE = HERE / 'tools' / '.renders'
RES = '3200'            # export tier: full demosaic binned 2x2, ~3200 px — plenty for 1600

# Roll folders in display order (any other roll folder is appended alphabetically).
ROLL_ORDER = ['Gold', '250D', 'P160', 'Portra400', 'Umax', '800T', '500T']
START = 'ItalyGold204561.ARW'          # the hero opens on this frame

# Density sweeps: the frame's own Density ± SPAN in STEP increments, nothing else changed.
SWEEPS = ['ItalyGold204561.ARW', 'Egypt Portra 16000250.ARW']
SPAN, STEP = 1.0, 0.25

LARGE, THUMB_H, SWEEP_THUMB_H, Q = 1600, 104, 96, 82
GRADE_KEYS = ('wb_temp', 'wb_tint', 'job_exposure', 'job_contrast', 'job_aging')


def sidecar(raw: Path) -> dict | None:
    p = raw.parent / 'Obelisk' / f'{raw.name}.json'
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding='utf-8'))['frames'][0]


def collect() -> list:
    folders = [d for d in SOURCE.iterdir() if d.is_dir() and (d / 'Obelisk' / 'roll.json').exists()]
    order = {n: i for i, n in enumerate(ROLL_ORDER)}
    folders.sort(key=lambda d: (order.get(d.name, len(order)), d.name.lower()))
    rolls = []
    for d in folders:
        frames = []
        for raw in sorted(d.glob('*.ARW')):
            sc = sidecar(raw)
            if sc is None:
                print(f'skip {raw.name}: no sidecar')
                continue
            frames.append({'raw': raw, 'sc': sc})
        if frames:
            roll = json.loads((d / 'Obelisk' / 'roll.json').read_text(encoding='utf-8'))
            rolls.append({'folder': d.name, 'profile': roll['profile']['name'], 'frames': frames})
    return rolls


def signature(sc: dict, density: float | None) -> str:
    """Everything in the sidecar that can change the render (not measurements/previews)."""
    keep = {k: v for k, v in sc.items() if k not in ('measured', 'working_preview')}
    keep['_density'] = density
    return hashlib.sha1(json.dumps(keep, sort_keys=True).encode()).hexdigest()[:16]


class Renderer:
    """The app, imported once against a temp copy of its DB."""

    def __init__(self):
        self.tmp = Path(tempfile.mkdtemp(prefix='obelisk-site-'))
        src = sqlite3.connect(f'file:{APP_DB.as_posix()}?mode=ro', uri=True)
        dst = sqlite3.connect(self.tmp / 'negacon.db')
        src.backup(dst)
        dst.close(); src.close()

        sys.path.insert(0, str(APP))
        import paths
        paths.data_dir = lambda: self.tmp        # DB, previews, caches, logs → temp
        import catalog

        def blocked(*a, **k):
            raise RuntimeError('sidecar write blocked (make_roll_images)')
        for fn in ('_write', 'sync', '_atomic_copy', 'forget', 'forget_roll',
                   '_persist_working_preview', 'restore_working_preview'):
            setattr(catalog, fn, blocked)
        catalog.enabled = lambda: False
        import main
        assert main.PREVIEWS_DIR.parent == self.tmp
        self.main = main

    def render(self, raw: Path, out: Path, density: float | None = None) -> None:
        m = self.main
        with m.get_db() as conn:
            settings = m._load_settings(conn)
            job = conn.execute('SELECT * FROM jobs WHERE file_path=?', (str(raw),)).fetchone()
            if job is None:
                sys.exit(f'{raw} is not in the Obelisk session — open its folder in Obelisk first')
            prof = conn.execute('SELECT * FROM profiles WHERE id=?', (job['profile_id'],)).fetchone()
        render_crop, stats_crop, film_border = m._export_expand_crop(job, 0.0)
        args = m._build_pipeline_args(
            job['id'], job['file_path'], prof, settings,
            json.loads(job['confirmed_strips']) if job['confirmed_strips'] else None,
            write_tiff=False, rotation_override=job['job_rotation'],
            wb_temp=int(job['wb_temp'] or 0), wb_tint=int(job['wb_tint'] or 0),
            job_exposure=float(job['job_exposure'] or 0.0) if density is None else density,
            job_contrast=float(job['job_contrast'] or 0.0),
            lift_blacks=bool(job['lift_blacks']), job_aging=float(job['job_aging'] or 0.0),
            crop_override=render_crop, write_jpeg_out=True, jpeg_quality=95, export_res=RES,
            look_overrides=m._job_look_override(job), dust_patches=m._dust_for(job),
            sub_frame=job['sub_frame'], virtual_copy=int(job['virtual_copy'] or 0),
            stats_crop=stats_crop, write_preview=False,
            sharpen=m._export_sharpen(settings), despeckle=m._export_despeckle(settings),
            film_border=film_border)
        args['jpeg_out_path'] = str(out)
        m._render_export(args, RES)


def cached(renderer_box: list, raw: Path, sc: dict, density: float | None,
           manifest: dict, force: bool) -> Path:
    tag = '' if density is None else f'_d{density:+.2f}'
    out = CACHE / f'{raw.stem}{tag}.jpg'
    sig = signature(sc, density)
    if force or not out.exists() or manifest.get(out.name) != sig:
        if not renderer_box:
            renderer_box.append(Renderer())
        print(f'render {out.name}', flush=True)
        renderer_box[0].render(raw, out, density)
        manifest[out.name] = sig
    return out


def save_web(src: Path, large: Path, thumb: Path, thumb_h: int) -> tuple[int, int]:
    im = Image.open(src).convert('RGB')
    big = im.copy()
    big.thumbnail((LARGE, LARGE), Image.LANCZOS)
    big.save(large, quality=Q, optimize=True, progressive=True)
    t = im.copy()
    t.thumbnail((thumb_h * 4, thumb_h), Image.LANCZOS)
    t.save(thumb, quality=78, optimize=True)
    return big.size


def main() -> None:
    force = '--force' in sys.argv
    CACHE.mkdir(parents=True, exist_ok=True)
    mpath = CACHE / 'manifest.json'
    manifest = json.loads(mpath.read_text()) if mpath.exists() else {}
    renderer: list = []

    roll_dir = HERE / 'public' / 'assets' / 'roll'
    dens_dir = HERE / 'public' / 'assets' / 'density'
    for d in (roll_dir, dens_dir):
        d.mkdir(parents=True, exist_ok=True)
        for old in d.glob('*.jpg'):
            old.unlink()

    rolls = collect()
    by_raw, out_rolls = {}, []
    for r in rolls:
        key = r['folder'].lower().replace(' ', '')
        frames = []
        for n, f in enumerate(r['frames'], 1):
            sc, fid = f['sc'], f'{key}-{n}'
            src = cached(renderer, f['raw'], sc, None, manifest, force)
            w, h = save_web(src, roll_dir / f'{fid}.jpg', roll_dir / f'{fid}_t.jpg', THUMB_H)
            frame = {'id': fid, 'w': w, 'h': h,
                     'temp': int(sc.get('wb_temp') or 0), 'tint': int(sc.get('wb_tint') or 0),
                     'density': round(float(sc.get('job_exposure') or 0.0), 2),
                     'contrast': round(float(sc.get('job_contrast') or 0.0), 2),
                     'aging': round(float(sc.get('job_aging') or 0.0), 2)}
            frames.append(frame)
            by_raw[f['raw'].name] = (f, frame, r['profile'])
        out_rolls.append({'key': key, 'folder': r['folder'], 'profile': r['profile'], 'frames': frames})

    sweeps = []
    for name in SWEEPS:
        f, frame, profile = by_raw[name]
        base = frame['density']
        n = int(round(SPAN / STEP))
        values = [round(base + k * STEP, 2) for k in range(-n, n + 1)]
        for i, v in enumerate(values):
            src = cached(renderer, f['raw'], f['sc'], v, manifest, force)
            w, h = save_web(src, dens_dir / f"{frame['id']}_{i}.jpg",
                            dens_dir / f"{frame['id']}_{i}_t.jpg", SWEEP_THUMB_H)
        sweeps.append({'id': frame['id'], 'profile': profile, 'values': values,
                       'start': n, 'w': w, 'h': h})

    mpath.write_text(json.dumps(manifest, indent=1))
    if renderer:                    # the DB copy, previews and logs; open log handles may
        shutil.rmtree(renderer[0].tmp, ignore_errors=True)    # keep a file or two
    start = by_raw[START][1]['id'] if START in by_raw else out_rolls[0]['frames'][0]['id']
    data = {'start': start, 'rolls': out_rolls, 'sweeps': sweeps}
    (HERE / 'src' / 'data' / 'rolls.json').write_text(json.dumps(data, indent=1) + '\n')

    n_frames = sum(len(r['frames']) for r in out_rolls)
    size = sum(p.stat().st_size for d in (roll_dir, dens_dir) for p in d.glob('*.jpg'))
    print(f'{len(out_rolls)} rolls, {n_frames} frames, {len(sweeps)} sweeps; '
          f'{size / 1e6:.1f} MB of web images')


if __name__ == '__main__':
    main()
