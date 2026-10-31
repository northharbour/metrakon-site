// The plans on /pricing. Plans differ ONLY in how many frames they export a month and the
// support around that, never in features (negacon-converter NEXT_BUILD_TODO §4). They are
// shown before release without prices; `price` appears once SITE.stage === 'released'.
// Allowances are working figures, NOT final.
// `checkout` is the payment provider's hosted-checkout URL for that plan.

export type Plan = {
  name: string;
  for: string;
  allowance: number | null;  // exported frames per calendar month; null = unlimited
  scope: string;             // who or what one licence covers
  price: string | null;      // e.g. '€99'; null = "Contact us" once released
  priceNote?: string;        // e.g. 'once, with a year of updates', '/ month'
  extras: string[];          // support and service only: every plan has every feature
  checkout: string;
};

export const PLANS: Plan[] = [
  {
    name: 'Personal',
    for: 'Photographers scanning their own film',
    allowance: 1000,
    scope: 'One person',
    price: null,
    extras: ['Email support'],
    checkout: '',
  },
  {
    name: 'Small lab',
    for: 'Small labs and scanning services',
    allowance: 4000,
    scope: 'One scanning station',
    price: null,
    extras: ['Email support'],
    checkout: '',
  },
  {
    name: 'Lab',
    for: 'Labs scanning customer film every day',
    allowance: null,
    scope: 'Per scanning station',
    price: null,
    extras: ['Onboarding call and help calibrating your rig', 'Priority support'],
    checkout: '',
  },
];

// True of every licence, whatever the tier. Shown before release too.
export const INCLUDED = [
  'Calibrated conversion for colour negative (C-41, ECN-2) and black & white',
  'Calibration tools — build profiles for your own stocks and light',
  'Lab auto — lab-printer conversion for colour film without a profile',
  'Overnight conversion, film stock map and automatic roll base',
  'Scan quality control and exposure contact sheets',
  'Local automatic orientation',
  'Live GPU grading with background export',
];
