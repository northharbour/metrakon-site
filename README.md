# Obelisk website

Marketing site for Obelisk, built with [Astro](https://astro.build) and deployed to GitHub Pages
at `image.northharbourinstruments.com` (see `public/CNAME`).

```bash
npm install
npm run dev       # http://localhost:4321
npm run build     # static output in dist/
```

## Layout

| Path | What |
|---|---|
| `src/site.ts` | Name, release stage, form endpoint, contact email, nav — the launch switches |
| `src/data/comparison.ts` | Comparison tools, bracket frames, stats (used by home + /compare) |
| `src/data/labauto.json` | Calibrated vs Lab auto pairs on the home page (`tools/make_labauto_images.py`) |
| `src/data/plans.ts` | Subscription plans (rendered only when `stage = 'released'`) |
| `src/pages/` | `/`, `/how-it-works/`, `/compare/`, `/pricing/`, 404 |
| `src/components/` | App-window hero demo, bracket demo, wipe slider, early-access form |
| `public/assets/` | Images, icons, social card (`og.jpg`) |
| `tools/` | Python generators for the comparison images and measurement figures |

## Before merging to main

1. **Impressum details** in `LEGAL` in `src/site.ts` (name, street, city, email; phone/VAT ID
   if you have them). A production build refuses to run while any required field is empty.
2. **Pages source**: repo Settings → Pages → Source: **GitHub Actions** (the workflow in
   `.github/workflows/deploy.yml` builds and publishes on every push to `main`).
3. **Form**: left without a service on purpose — it opens the visitor's email app addressed to
   the Impressum email, so no third party processes data. If you add Formspree/Tally later, also
   set `formProvider` so the privacy policy names it.
4. Trademark clearance for OBELISK is still open.

## Launch

Set `stage: 'released'` in `src/site.ts`, fill prices and checkout links in `src/data/plans.ts`.
The header CTA, hero button and pricing page switch over automatically.

## Notes

- Palette is taken from the app icon (amber = negative/action, cyan = measured data). Dark only.
- Fonts are self-hosted (`@fontsource`), so no requests go to Google — matters for EU visitors.
- Comparison image filenames keep the historical `metrakon_` prefix; only labels say Obelisk.
- Copy register: plain and specific, claims backed by measurements. Don't add numbers that
  aren't measured.
