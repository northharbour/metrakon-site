import { defineConfig } from 'astro/config';
import { readdir, readFile, writeFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { join, sep } from 'node:path';

// Served from the custom domain in public/CNAME, so the site lives at the root.
const SITE = 'https://image.northharbourinstruments.com';

// sitemap.xml from the built pages: every page except the 404 and any page marked noindex
// (drafts), so a new page is listed without touching this. public/robots.txt points here.
const sitemap = {
  name: 'sitemap',
  hooks: {
    'astro:build:done': async ({ dir }) => {
      const root = fileURLToPath(dir);
      const pages = (await readdir(root, { recursive: true })).filter((f) => f.endsWith('.html')).sort();
      const urls = [];
      for (const f of pages) {
        if (f === '404.html') continue;
        if (/<meta name="robots" content="[^"]*noindex/.test(await readFile(join(root, f), 'utf8'))) continue;
        const path = '/' + f.split(sep).join('/').replace(/index\.html$/, '');
        urls.push(`  <url><loc>${new URL(path, SITE).href}</loc></url>`);
      }
      await writeFile(join(root, 'sitemap.xml'),
        `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${urls.join('\n')}\n</urlset>\n`);
    },
  },
};

export default defineConfig({
  site: SITE,
  trailingSlash: 'ignore',
  build: { format: 'directory' },
  integrations: [sitemap],
});
