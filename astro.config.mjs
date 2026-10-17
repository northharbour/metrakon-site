import { defineConfig } from 'astro/config';

// Served from the custom domain in public/CNAME, so the site lives at the root.
export default defineConfig({
  site: 'https://image.northharbourinstruments.com',
  trailingSlash: 'ignore',
  build: { format: 'directory' },
});
