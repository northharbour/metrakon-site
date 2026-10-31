# Light comparison (RGB vs white article)

Analysis for `src/pages/guides/rgb-vs-white-light.astro`. Data: `~/Pictures/Light Comparison`
(Kodak Gold 200, A7R IV; arms CS-Lite white / RGB camera-balanced / RGB sensor-balanced /
RGB trichrome). Chart brackets and the single-LED triplets now live in `~/Pictures/Light Comparison Source/`
(`Charts/`, `RGB Trichrome/`); the export rolls stay in `Light Comparison`. Triplets merged with
`negacon-converter/tools/trichrome_merge.py`. Profiles in the installed app: COMP CSLite (99),
COMP Cam Balanced (105), COMP Sensor Balanced (102), COMP RGB Trichrome (108).

Run from `negacon-converter/` with its venv, on a COPY of the app database:

| Script | What |
|---|---|
| `rawstats.py <folders…>` | raw channel level at the film base per frame |
| `score_arms.py <db> <out.json>` | rebuild each profile from its stored chart samples (Obelisk's own calibrate + chartfit), saturation needed, colour error (in-sample + leave-one-frame-out), bracket spread |
| `sep_identity.py <db>` | separation with no matrix vs with the fitted matrix |
| `noise_arms.py <db> <Charts dir> <scores.json> <out dir> [identity]` | per-patch colour/L noise at matched colour from the pixels (half-size quads, no demosaic), crops + Lab arrays |
| `noise_summary.py`, `noise_common.py <noise dirs…>` | tables (all clean frames / exposures clean in every arm) |
| `noise_by_exposure.py <db> <Charts dir> <scores.json> <out.json>` + `noise_by_exposure_table.py <out.json>` | every bracket frame (−3…+3), six greys + R/G/B, colour and lightness noise at matched colour; failed chart locations retried from a neighbour frame's corners |
| `make_patch_grid.py <noise dir> <out.png> [ev0\|ev-2]` | close-up grid, every crop shifted to the chart's reference colour so only noise differs |

Fifth arm: `RGB Sensor Unmixed` — the sensor-balanced frames with the LED leak removed by
`negacon-converter/tools/leak_unmix.py` (matrix in `results/leak_matrix.json`), profile COMP RGB Unmixed (111).

Results of the 2026-10-31 run are in `results/`.
