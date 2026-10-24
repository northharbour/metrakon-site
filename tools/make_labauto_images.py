"""Render the Lab auto comparison: the same negatives through a calibrated profile and Lab auto.

    ../negacon-converter/.venv/bin/python tools/make_labauto_images.py [--force] [--all]

Run it with the APP's venv: rendering imports the app (negacon-converter) and calls the same
functions its single-frame export runs (_build_pipeline_args + _render_export), like
make_roll_images.py.

Source: the frames in PAIRS, in the roll folders under SOURCE, which must be in the app's
session (open the folders in Obelisk first). Each frame renders twice, both with NO
adjustments (Density, Temp, Tint and Contrast at 0; crop, rotation and dust as the frame has
them):
  cal  the stock's own calibrated profile (CALIBRATED below)
  lab  Lab auto with the Generic film of the roll's scanning light — no profile involved.
       Each roll is switched to Lab auto on the DB copy the way the roll header does it,
       then analysed by the app's own roll analysis (every frame of the roll, in order).

The app DB is never written: it is copied (sqlite backup, read-only open) to a temp dir and
the app's data dir is pointed there. Sidecar writes are blocked. Full renders are cached in
tools/.renders/labauto/ (gitignored); --force redoes them. --all renders every frame of every
roll (to choose PAIRS) and writes nothing to the site.

Writes:
    public/assets/labauto/<n>_cal.jpg, <n>_lab.jpg   1600 px long edge
    public/assets/labauto/<n>_t.jpg                  picker thumb (Lab auto side)
    src/data/labauto.json                            pairs, sizes, stock names
"""
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
if sys.platform == 'darwin':
    SOURCE = Path.home() / 'Pictures' / 'Obelisk Feature'
    APP_DB = Path.home() / 'Library' / 'Application Support' / 'Obelisk' / 'negacon.db'
else:
    SOURCE = Path(r'C:\Users\Benjamin Hurren\Pictures\Obelisk Feature')
    APP_DB = Path(os.environ.get('LOCALAPPDATA', '')) / 'Programs' / 'Obelisk' / 'data' / 'negacon.db'
CACHE = HERE / 'tools' / '.renders' / 'labauto'
RES = '3200'
LIGHT = 'RGB'           # the Obelisk Feature rolls were scanned under the lab's RGB light

# roll folder -> the stock's calibrated profile (RGB light) for the 'cal' side
CALIBRATED = {
    'Gold': 'Kodak Gold 200', '250D': 'Vision 250D', 'P160': 'Portra 160',
    'Portra400': 'Portra 400', 'Umax': 'Ultramax 400', '800T': 'Cinestill 800T',
    '500T': 'Vision 500T',
}
# (roll folder, RAW name) in display order. Chosen from an --all run to show both sides of
# Lab auto: frames it prints well, including stocks the Generic is not made from (250D,
# 800T, 500T), and a night frame it lifts to grey where the calibrated profile holds black.
PAIRS = [
    ('P160', 'Egypt Portra 16000250.ARW'),
    ('250D', 'April26 250D06727.ARW'),
    ('Portra400', 'Egypt Portra 40000176.ARW'),
    ('Gold', 'China 2603799.ARW'),
    ('800T', 'China 2602608.ARW'),
    ('500T', 'Wiesn 640T09560.ARW'),
]
LONG, THUMB_H, Q = 1600, 104, 84


class Renderer:
    """The app, imported once against a temp copy of its DB."""

    def __init__(self):
        self.tmp = Path(tempfile.mkdtemp(prefix='obelisk-labauto-'))
        src = sqlite3.connect(f'file:{APP_DB.as_posix()}?mode=ro', uri=True)
        dst = sqlite3.connect(self.tmp / 'negacon.db')
        src.backup(dst)
        dst.close(); src.close()

        sys.path.insert(0, str(APP))
        import paths
        paths.data_dir = lambda: self.tmp        # DB, previews, caches, logs → temp
        import catalog

        def blocked(*a, **k):
            raise RuntimeError('sidecar write blocked (make_labauto_images)')
        for fn in ('_write', '_atomic_copy', 'forget', 'forget_roll',
                   '_persist_working_preview', 'restore_working_preview'):
            setattr(catalog, fn, blocked)
        catalog.sync = lambda *a, **k: 0         # the roll analysis syncs when it is done
        catalog.enabled = lambda: False
        import main
        assert main.PREVIEWS_DIR.parent == self.tmp
        self.main = main
        self.analysed: set = set()

    def _profile(self, conn, name: str):
        row = conn.execute("SELECT * FROM profiles WHERE name=? AND light_source=? "
                           "AND film_type='color'", (name, LIGHT)).fetchone()
        if row is None:
            sys.exit(f'no {LIGHT} profile called {name!r} in the app DB')
        return row

    def lab_auto(self, folder: Path) -> None:
        """Switch the roll to Lab auto on the DB copy (as POST /api/rolls/conversion does
        for the Generic of LIGHT) and run the app's roll analysis on this thread."""
        m, key = self.main, str(folder)
        if key in self.analysed:
            return
        with m.get_db() as conn:
            lab = m._lab_profile(conn, LIGHT)
            fid = m.labauto.film_id(m.labauto.film_for(LIGHT))
            conn.execute('''INSERT OR REPLACE INTO roll_conversion
                            (folder, mode, profile_id, profile_signature, base_signature,
                             recipe, wb_mode, rig_id, lab_film, created_at)
                            VALUES (?, 'lab_auto', ?, '', '', NULL, ?, ?, ?, datetime('now'))''',
                         (key, lab['id'], *m._current_base_regime(), fid))
            for r in m._roll_folder_jobs(conn, key):
                conn.execute('UPDATE jobs SET profile_id=?, profile_name=? WHERE id=?',
                             (lab['id'], lab['name'], r['id']))
            conn.commit()
        m._run_roll_conversion_analysis(key, 'lab_auto', int(lab['id']))
        task = m._roll_conversion_tasks.get(key) or {}
        if task.get('status') != 'ready':
            sys.exit(f'Lab auto analysis failed for {folder.name}: {task.get("error")}')
        print(f'{folder.name}: Lab auto analysed ({task["frames_used"]} frames, {fid})', flush=True)
        self.analysed.add(key)

    def render(self, raw: Path, side: str, out: Path) -> None:
        m = self.main
        if side == 'lab':
            self.lab_auto(raw.parent)
        with m.get_db() as conn:
            settings = m._load_settings(conn)
            job = conn.execute('SELECT * FROM jobs WHERE file_path=?', (str(raw),)).fetchone()
            if job is None:
                sys.exit(f'{raw} is not in the Obelisk session — open its folder in Obelisk first')
            prof = (conn.execute('SELECT * FROM profiles WHERE id=?', (job['profile_id'],)).fetchone()
                    if side == 'lab' else self._profile(conn, CALIBRATED[raw.parent.name]))
        assert (side == 'lab') == m._is_lab_profile(prof)
        render_crop, stats_crop, film_border = m._export_expand_crop(job, 0.0)
        args = m._build_pipeline_args(
            job['id'], job['file_path'], prof, settings,
            json.loads(job['confirmed_strips']) if job['confirmed_strips'] else None,
            write_tiff=False, rotation_override=job['job_rotation'],
            wb_temp=0, wb_tint=0, job_exposure=0.0, job_contrast=0.0,
            lift_blacks=False, job_aging=0.0,
            crop_override=render_crop, write_jpeg_out=True, jpeg_quality=95, export_res=RES,
            look_overrides=None, dust_patches=m._dust_for(job),
            sub_frame=job['sub_frame'], virtual_copy=int(job['virtual_copy'] or 0),
            stats_crop=stats_crop, write_preview=False,
            sharpen=m._export_sharpen(settings), despeckle=m._export_despeckle(settings),
            film_border=film_border)
        args['jpeg_out_path'] = str(out)
        m._render_export(args, RES)


def save_web(src: Path, large: Path, thumb: Path | None = None) -> tuple[int, int]:
    im = Image.open(src).convert('RGB')
    big = im.copy()
    big.thumbnail((LONG, LONG), Image.LANCZOS)
    big.save(large, quality=Q, optimize=True, progressive=True)
    if thumb is not None:
        t = im.copy()
        t.thumbnail((THUMB_H * 4, THUMB_H), Image.LANCZOS)
        t.save(thumb, quality=78, optimize=True)
    return big.size


def main() -> None:
    force, every = '--force' in sys.argv, '--all' in sys.argv
    CACHE.mkdir(parents=True, exist_ok=True)
    if every:
        pairs = [(d.name, raw.name) for d in sorted(SOURCE.iterdir()) if d.name in CALIBRATED
                 for raw in sorted(d.glob('*.ARW'))]
    else:
        pairs = PAIRS
    if not pairs:
        sys.exit('PAIRS is empty: run with --all, look at tools/.renders/labauto/, fill PAIRS')

    renderer: list = []
    rendered = []
    # Calibrated first: the Lab auto switch restamps the roll's frames on the DB copy.
    for side in ('cal', 'lab'):
        for roll, name in pairs:
            raw = SOURCE / roll / name
            out = CACHE / f'{raw.stem}_{side}.jpg'
            if force or not out.exists():
                if not renderer:
                    renderer.append(Renderer())
                print(f'render {out.name}', flush=True)
                renderer[0].render(raw, side, out)
            rendered.append(out)
    if renderer:
        shutil.rmtree(renderer[0].tmp, ignore_errors=True)
    if every:
        print(f'{len(rendered)} renders in {CACHE}')
        return

    out_dir = HERE / 'public' / 'assets' / 'labauto'
    out_dir.mkdir(parents=True, exist_ok=True)
    for old in out_dir.glob('*.jpg'):
        old.unlink()
    data = []
    for n, (roll, name) in enumerate(pairs, 1):
        stem = Path(name).stem
        cal = save_web(CACHE / f'{stem}_cal.jpg', out_dir / f'{n}_cal.jpg')
        lab = save_web(CACHE / f'{stem}_lab.jpg', out_dir / f'{n}_lab.jpg', out_dir / f'{n}_t.jpg')
        data.append({'n': n, 'stock': CALIBRATED[roll], 'cal': list(cal), 'lab': list(lab)})
        print(f'{n}: {roll}/{name} -> {lab}')
    (HERE / 'src' / 'data' / 'labauto.json').write_text(
        json.dumps({'light': LIGHT, 'pairs': data}, indent=1) + '\n')
    size = sum(p.stat().st_size for p in out_dir.glob('*.jpg'))
    print(f'{len(data)} pairs, {size / 1e6:.1f} MB')


if __name__ == '__main__':
    main()
