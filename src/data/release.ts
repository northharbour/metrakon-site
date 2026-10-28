// The public releases of the app, read from GitHub when the site BUILDS (the site is
// static), so a visitor's browser never contacts GitHub until they click a download.
// Each platform's download is the newest published release that HAS that platform's file,
// so a platform built later (or not rebuilt for a Mac-only fix) keeps its download: the
// two may be different versions. A new release shows up on the next deploy: the workflow
// runs daily, or run it by hand (Actions → Deploy site → Run workflow) right after publishing.
import { SITE } from '../site';

export type Asset = { name: string; url: string; mb: number; version: string; date: string };
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
    const r = await fetch(`https://api.github.com/repos/${SITE.releasesRepo}/releases?per_page=30`, { headers });
    if (r.status === 404) return { state: 'none' };
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    // Newest first, as GitHub lists them; drafts and pre-releases are not public downloads
    // (the same releases /releases/latest would skip).
    const list = ((await r.json()) as any[]).filter((j) => !j.draft && !j.prerelease);
    if (!list.length) return { state: 'none' };
    const version = (j: any) => String(j.tag_name ?? '').replace(/^v/, '');
    const date = (j: any) => String(j.published_at ?? '').slice(0, 10);
    const pick = (re: RegExp): Asset | undefined => {
      for (const j of list) {
        const a = (j.assets ?? []).find((x: { name: string }) => re.test(x.name));
        if (a) return { name: a.name, url: a.browser_download_url, mb: Math.round(a.size / 1e6),
                        version: version(j), date: date(j) };
      }
    };
    const newest = list[0];
    return {
      state: 'ready',
      release: {
        version: version(newest),
        url: newest.html_url,
        date: date(newest),
        mac: pick(/\.dmg$/i),
        win: pick(/\.exe$/i),
      },
    };
  } catch (e) {
    console.warn(`[release] could not read the releases of ${SITE.releasesRepo}: ${e}`);
    return { state: 'unknown' };
  }
}

export const RELEASE: ReleaseState = await load();

/** The trial buttons show: switched on, and a release exists (or GitHub was unreachable). */
export const trialAvailable = SITE.trial && RELEASE.state !== 'none';

/** Where a platform's download button points: the file itself, else the release page. */
export const downloadHref = (a?: Asset) => a?.url ?? (RELEASE.state === 'ready' ? RELEASE.release.url : RELEASES_PAGE);
export const releasesPage = `https://github.com/${SITE.releasesRepo}/releases`;
