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
  // Left empty on purpose: a third-party form service is a data processor that would need
  // its own section in the privacy policy (see formProvider below). With no endpoint the
  // form opens the visitor's email app addressed to contactEmail — no third party involved.
  formEndpoint: '',
  formProvider: { name: '', privacyUrl: '' }, // e.g. { name: 'Formspree, Inc. (USA)', privacyUrl: 'https://formspree.io/legal/privacy-policy' }
  contactEmail: '', // empty = LEGAL.email
};

// Impressum (§ 5 DDG) + privacy-policy controller. Must be REAL details — a production
// build refuses to run while a required field is empty (see Base.astro).
export const LEGAL = {
  name: 'Benjamin Hurren', // owner (Inhaber) — details from northharbourinstruments.com/policies/legal-notice
  trading: 'North Harbour Instruments', // trading name, shown under the name
  street: 'c/o Blix GbR, Pappenheimstr. 3',
  city: '80335 München',          // postcode + city
  country: 'Germany',
  email: 'info@northharbourinstruments.com', // must be reachable; defaults the site contact email too
  phone: '',         // optional but recommended (§ 5 DDG wants a second fast channel)
  vatId: 'DE453709438',         // USt-IdNr., only if you have one (Kleinunternehmer: leave empty)
  register: '',      // only for a registered company, e.g. 'Amtsgericht München, HRB 12345'
  updated: '2026-10-17',
};

export const legalMissing = () =>
  (['name', 'street', 'city', 'email'] as const).filter((k) => !LEGAL[k].trim());

export const NAV = [
  { href: '/how-it-works/', label: 'How it works' },
  { href: '/compare/', label: 'Compare' },
  { href: '/pricing/', label: 'Pricing' },
];

/** The address visitors write to: SITE.contactEmail, else the Impressum email. */
export const contactEmail = () => SITE.contactEmail || LEGAL.email;
