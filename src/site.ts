// One place for the values every page shares. A rename or a launch is an edit here.

export const SITE = {
  name: 'Obelisk',
  publisher: 'North Harbour Instruments',
  url: 'https://image.northharbourinstruments.com',
  description:
    'Obelisk converts camera-scanned colour negatives through a measured calibration of ' +
    'your film stock and scanning rig, so a whole roll lands at one density and one colour.',

  // Release state drives the CTAs and the pricing page. 'early-access' until the first
  // paid release; then 'released' (shows prices + the Download link).
  stage: 'early-access' as 'early-access' | 'released',

  // Early-access form. GitHub Pages cannot receive a POST, so this must be a form
  // service endpoint (Formspree, Buttondown, Tally…). Empty = the form falls back to
  // opening an email to CONTACT_EMAIL.
  formEndpoint: '',
  contactEmail: '', // TODO: set before merging — e.g. hello@northharbourinstruments.com
};

export const NAV = [
  { href: '/how-it-works/', label: 'How it works' },
  { href: '/compare/', label: 'Compare' },
  { href: '/pricing/', label: 'Pricing' },
];
