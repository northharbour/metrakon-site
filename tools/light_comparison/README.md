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

## Decode fix (2026-10-31, after publishing)

Every result above was measured before Obelisk's full-scale decode fix (negacon-converter
CLAUDE.md decision log 2026-10-31: LibRaw's `adjust_maximum` rescaled frames whose brightest
pixel was above 75% of full scale, so a base picked on one frame was off for others). The
COMP calibrations carried that: camera-balanced 6 of 7 bracket frames +0.37, white and
trichrome the strip-end frames +0.30 / +0.23, sensor-balanced ≤ 0.12.

`results/scores_fullscale.json` = `score_arms.py` on a DB copy after "Rebuild calibration"
corrected the stored samples (no rescans). Against `scores.json`:

| | separation vs white | held-out ΔE | hue | drift |
|---|---|---|---|---|
| White (CS-Lite) | 1.00× | 12.9 → 13.2 | 9.3° → 9.4° | 7.9 → 7.4 |
| RGB camera-balanced | 1.12× → 1.15× | 12.1 → 12.4 | 8.7° → 8.6° | 6.6 → 7.4 |
| RGB sensor-balanced | 1.25× → 1.26× | 11.9 → 12.4 | 7.7° → 7.8° | 7.1 → 7.5 |
| RGB trichrome | 1.65× → 1.64× | 11.5 → 11.7 | 8.0° → 7.8° | 6.0 → 6.1 |

Separation and hue error hold. Drift no longer favours single-exposure RGB over white light
(only trichrome is steadier), so the article's drift row needs updating. Still to do: rebuild
the COMP profiles in the app (their chart raws moved to `Light Comparison Source/Charts/`, so
repoint the profiles or move the raws back first), rerun the noise scripts, update the article.
