import type { Ingredients } from '../types/ingredients'

// Four presets span the visual axes Barista has to render distinctly:
// gold (strawberry/vanilla) vs gunk (sludge/fish) AND smooth vs chunky.
// Useful as a lever for demoing without Sommelier wired up.

export const PRESETS: Record<string, Ingredients> = {
  'gold-strawberry': {
    request_id: 'demo-1',
    url: 'https://stripe.com',
    version: 'ingredients-v0',
    base: 'strawberry',
    color: { hex: '#ff5b8a', accent_hex: '#ffd2dd' },
    texture: 'smooth',
    viscosity: 0.75,
    tartness: 0.4,
    sweetness: 0.8,
    freshness: 0.95,
    inclusions: [
      { kind: 'sprinkles', amount: 0.6 },
      { kind: 'sparkles', amount: 0.4 },
    ],
    toppings: [{ kind: 'whipped_cream', amount: 0.7 }],
    notes: ['Premium spacing', 'Coherent typography', 'Modern polish'],
    meta: { pc1: 0.6, pc2: 0.2, pc3: -0.1, confidence: 0.84, baseline_id: 'gold-gunk-v0', model_id: 'mock' },
  },

  'gold-vanilla': {
    request_id: 'demo-2',
    url: 'https://linear.app',
    version: 'ingredients-v0',
    base: 'vanilla',
    color: { hex: '#fff1c2', accent_hex: '#ffffff' },
    texture: 'airy',
    viscosity: 0.45,
    tartness: 0.1,
    sweetness: 0.6,
    freshness: 0.9,
    inclusions: [{ kind: 'mint', amount: 0.5 }],
    toppings: [{ kind: 'whipped_cream', amount: 0.5 }],
    notes: ['Restrained palette', 'Confident whitespace'],
    meta: { pc1: 0.4, pc2: -0.3, pc3: 0.0, confidence: 0.78, baseline_id: 'gold-gunk-v0', model_id: 'mock' },
  },

  'gunk-sludge': {
    request_id: 'demo-3',
    url: 'https://example-bad-site.test',
    version: 'ingredients-v0',
    base: 'burnt_rubber',
    color: { hex: '#5a4730', accent_hex: '#7a6a3f' },
    texture: 'sludge',
    viscosity: 0.95,
    tartness: 0.7,
    sweetness: 0.1,
    freshness: 0.15,
    inclusions: [
      { kind: 'tech_debt_chunks', amount: 0.8 },
      { kind: 'bugs', amount: 0.5 },
    ],
    toppings: [{ kind: 'lint_dust', amount: 0.6 }],
    notes: ['Inconsistent spacing', 'Clashing palette', 'Visual debt'],
    meta: { pc1: -0.7, pc2: 0.6, pc3: 0.2, confidence: 0.71, baseline_id: 'gold-gunk-v0', model_id: 'mock' },
  },

  'gunk-fish': {
    request_id: 'demo-4',
    url: 'https://broken-layout.test',
    version: 'ingredients-v0',
    base: 'fish',
    color: { hex: '#4a6a55', accent_hex: '#7d8f7c' },
    texture: 'chunky',
    viscosity: 0.55,
    tartness: 0.9,
    sweetness: 0.05,
    freshness: 0.05,
    inclusions: [
      { kind: 'bugs', amount: 0.9 },
      { kind: 'tech_debt_chunks', amount: 0.4 },
    ],
    toppings: [{ kind: 'burnt_marshmallow', amount: 0.7 }],
    notes: ['Broken layout', 'Unreadable text', 'Avoid'],
    meta: { pc1: -0.9, pc2: 0.8, pc3: -0.4, confidence: 0.66, baseline_id: 'gold-gunk-v0', model_id: 'mock' },
  },
}

export const PRESET_KEYS = Object.keys(PRESETS) as Array<keyof typeof PRESETS>
