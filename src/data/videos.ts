// The videos on the site, listed on /guides/ and embedded where they fit. Each plays through
// VideoEmbed (click to load, privacy policy §5); the poster is a self-hosted still in
// public/assets/video/.

export interface Video {
  id: string;             // YouTube video id
  slug: string;           // anchor on /guides/
  title: string;          // the title on YouTube (player + accessible name)
  heading: string;        // the title on the site
  duration: string;
  poster: string;
  summary: string;
  setup?: string;         // the gear in the video
}

export const VIDEOS: Video[] = [
  {
    id: 'qeYuUDmC2Go',
    slug: 'introduction',
    title: 'An Introduction to Obelisk - A Film Conversion Tool For Labs',
    heading: 'Introduction to Obelisk',
    duration: '6:21',
    poster: '/assets/video/intro.jpg',
    summary: 'What Obelisk is for and how it is used, in six minutes.',
  },
  {
    id: 'ebSeDewCUl4',
    slug: 'calibration',
    title: 'Obelisk Intro to Calibration',
    heading: 'Your first calibration',
    duration: '17:52',
    poster: '/assets/video/calibration.jpg',
    summary: 'A Kodak Gold 200 profile made from a colour chart bracket on a fresh install, then a roll of the same film converted with it, from the base pick to the finishing edits.',
    setup: 'Scanned with a Leica SL3-S and an Easy35V2. Chart: Calibrite ColorChecker Classic Mini.',
  },
];

export const video = (slug: string) => VIDEOS.find((v) => v.slug === slug)!;
