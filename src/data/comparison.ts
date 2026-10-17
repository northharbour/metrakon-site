// Comparison data. Tool keys match the filenames tools/make_comparison.py writes
// (public/assets/comp/{thumb,large}/<key>_<frame>.jpg). NOTE: 'metrakon' is the app's
// historical filename id for Obelisk's renders — only the LABEL renames.

export const TOOLS = [
  { key: 'metrakon', label: 'Obelisk' },
  { key: 'filmlab', label: 'FilmLab' },
  { key: 'nlp', label: 'Negative Lab Pro' },
  { key: 'smartconvert', label: 'SmartConvert' },
] as const;

export type StockKey = '250d' | 'gold';

export const SETS: Record<StockKey, {
  label: string;
  frames: string[];
  samples: string[] | null;
  stats: [string, string][];
}> = {
  '250d': {
    label: 'Vision3 250D',
    frames: ['06570', '06571', '06572', '06573', '06574', '06575', '06576'],
    samples: ['06553', '06555', '06556', '06559', '06563', '06577', '06582', '06583', '06585', '06587'],
    stats: [
      ['1', 'Obelisk median brightness spread (8-bit levels) over the normal and over-exposed frames of this bracket. The levelling is automatic.'],
      ['8–29', 'The same spread in the other tools — even with density matched by hand where the tool allows it.'],
      ['+8 → −14', 'Negative Lab Pro’s mean R−G balance swings from warm on under-exposed frames to cool on over-exposed ones. Obelisk holds within 8 levels of neutral across the bracket.'],
    ],
  },
  gold: {
    label: 'Kodak Gold 200',
    frames: ['09519', '09520', '09521', '09522', '09523', '09524', '09525'],
    samples: null,
    stats: [
      ['13', 'Obelisk median brightness spread (8-bit levels) over the normal and over-exposed frames. The levelling is automatic.'],
      ['42–56', 'The same spread in the other tools — even with density matched by hand where the tool allows it.'],
      ['warm → cool', 'Per-image estimation drifts colour with exposure: Negative Lab Pro’s balance swings from warm (mean R−G +15) to cool (−4) along the bracket. Obelisk’s holds one direction.'],
    ],
  },
};

export const STOCK_ORDER: StockKey[] = ['250d', 'gold'];

export const thumb = (t: string, f: string) => `/assets/comp/thumb/${t}_${f}.jpg`;
export const large = (t: string, f: string) => `/assets/comp/large/${t}_${f}.jpg`;
