// The latest public release of the app, read from GitHub when the site BUILDS (the site is
// static), so a visitor's browser never contacts GitHub until they click a download.
// A new release shows up on the next deploy: the workflow runs daily, or run it by hand
// (Actions → Deploy site → Run workflow) right after publishing.
import { SITE } from '../site';

export type Asset = { name: string; url: string; mb: number };
export type Release = { version: string; url: string; date: string; mac?: Asset; win?: Asset };

// 'ready': a published release. 'none': nothing published yet. 'unknown': GitHub could not
// be asked (offline build, rate limit) — the buttons then go to the releases page.
export type ReleaseState =
  | { state: 'ready'; release: Release }
  | { state: 'none' }
  | { state: 'unknown' };

const RELEASES_PAGE = `https://github.com/${SITE.releasesRepo}/releases/latest`;

async function load(): Promise<ReleaseState> {
  const headers: Record<string, string> = {
    Accept: 'application/vnd.github+json',
    'User-Agent': 'obelisk-site',
  };
  if (process.env.GITHUB_TOKEN) headers.Authorization = `Bearer ${process.env.GITHUB_TOKEN}`;
  try {
    const r = await fetch(`https://api.github.com/repos/${SITE.releasesRepo}/releases/latest`, { headers });
    if (r.status === 404) return { state: 'none' };
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    const j = await r.json();
    const pick = (re: RegExp): Asset | undefined => {
      const a = (j.assets ?? []).find((x: { name: string }) => re.test(x.name));
      return a && { name: a.name, url: a.browser_download_url, mb: Math.round(a.size / 1e6) };
    };
    return {
      state: 'ready',
      release: {
        version: String(j.tag_name ?? '').replace(/^v/, ''),
        url: j.html_url,
        date: String(j.published_at ?? '').slice(0, 10),
        mac: pick(/\.dmg$/i),
        win: pick(/\.exe$/i),
      },
    };
  } catch (e) {
    console.warn(`[release] could not read the latest release of ${SITE.releasesRepo}: ${e}`);
    return { state: 'unknown' };
  }
}

export const RELEASE: ReleaseState = await load();

/** The trial buttons show: switched on, and a release exists (or GitHub was unreachable). */
export const trialAvailable = SITE.trial && RELEASE.state !== 'none';

/** Where a platform's download button points: the file itself, else the release page. */
export const downloadHref = (a?: Asset) => a?.url ?? (RELEASE.state === 'ready' ? RELEASE.release.url : RELEASES_PAGE);
export const releasesPage = `https://github.com/${SITE.releasesRepo}/releases`;
