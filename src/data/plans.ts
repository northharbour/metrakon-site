// Subscription plans. Rendered on /pricing only once SITE.stage === 'released'.
// PLACEHOLDERS — tiers, prices and limits are not decided. See the subscription plan doc.
// `checkout` is the payment provider's hosted-checkout URL for that plan.

export type Plan = {
  name: string;
  for: string;
  monthly: number | null;   // in `currency`; null = "Contact us"
  yearly: number | null;    // per month, billed yearly
  seats: string;
  features: string[];
  checkout: string;
  featured?: boolean;
};

export const CURRENCY = '€';

export const PLANS: Plan[] = [
  {
    name: 'Studio',
    for: 'Photographers and archives scanning their own work',
    monthly: null, yearly: null,
    seats: '1 scanning station',
    features: ['Every conversion feature', 'Unlimited calibrated profiles', 'Updates while subscribed', 'Email support'],
    checkout: '',
  },
  {
    name: 'Lab',
    for: 'Film labs digitising customer rolls',
    monthly: null, yearly: null,
    seats: 'Per scanning station',
    features: ['Everything in Studio', 'Profile sharing across stations', 'Lab onboarding call', 'Priority support'],
    checkout: '',
    featured: true,
  },
  {
    name: 'Multi-site',
    for: 'Lab groups and institutions',
    monthly: null, yearly: null,
    seats: '5+ stations',
    features: ['Everything in Lab', 'Volume pricing', 'Onboarding and rig calibration help', 'Invoice billing'],
    checkout: '',
  },
];

// True of every licence, whatever the tier. Shown before release too.
export const INCLUDED = [
  'Calibrated conversion for colour negative (C-41, ECN-2) and black & white',
  'Calibration tools — build profiles for your own stocks and light',
  'Overnight conversion, film stock map and automatic roll base',
  'Scan quality control and exposure contact sheets',
  'Local automatic orientation',
  'Live GPU grading with background export',
];
