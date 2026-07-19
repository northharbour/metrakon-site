# Metrakon landing site

A single self-contained static page. No build step, no dependencies — GitHub Pages serves
`index.html` directly.

## Before it goes live

1. **Images.** Drop files into `assets/` and replace the `<div class="ph">…</div>` placeholders
   with `<img src="assets/…" alt="…">`. Three slots are marked in the HTML:
   - `roll-consistency.jpg` — contact sheet or bracket strip (the strongest single proof)
   - `light-before.jpg` / `light-after.jpg` — the scanning light comparison
2. **Favicon.** Add `assets/favicon.ico` (the app's `static/negacon.ico` works), or remove the
   `<link rel="icon">` line.
3. **Numbers.** The three stats in the light section are from the 2026-07-17 measurements. Check
   they still reflect the current rig before publishing.

## Email capture

The signup form is written but **commented out** in `index.html`, under the "Status" section. To
turn it on: remove the comment markers, then set `action=` to a real endpoint — GitHub Pages is
static and cannot process submissions itself. Formspree and Buttondown both have free tiers and
take one line. The comment block lists the exact values and the wording to restore alongside it.

## Deploying

```bash
# in a fresh directory
git init
# copy the contents of this folder in (index.html, assets/, this README)
git add .
git commit -m "Landing page"
git remote add origin git@github.com:<user>/<repo>.git
git push -u origin main
```

Then in the repo: **Settings → Pages → Source: deploy from branch → `main` / root**.

### Custom subdomain

To serve at `image.northharbourinstruments.com`:

1. Add a file named `CNAME` at the repo root containing exactly:
   ```
   image.northharbourinstruments.com
   ```
2. At your DNS provider, add a `CNAME` record: `image` → `<user>.github.io`
3. In Settings → Pages, enter the custom domain and enable **Enforce HTTPS** once the
   certificate provisions (usually a few minutes, occasionally up to an hour).

## Notes

- The palette matches the application UI (`--accent` amber `#c5852d`, `--cyan` `#4fc8dd`,
  neutral greys) so the site and product read as one thing. Keep them in sync if the app theme
  changes.
- Copy follows the project writing-style rule: plain professional documentation register, no
  slogans, minimal emphasis.
- The page names Metrakon throughout. Trademark clearance was still outstanding as of
  2026-07-19 — worth resolving before promoting the page or buying a matching domain.
