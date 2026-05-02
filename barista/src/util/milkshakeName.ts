// Deterministic short name for a given Ingredients object — same ingredients
// always produce the same name, so the header stays stable across re-renders
// and only changes when /taste, /remix, or a preset-switch actually mutates
// the milkshake.

import type { Ingredients } from '../types/ingredients'

const BASE_VIBE: Record<string, string> = {
  strawberry: 'Pink',
  vanilla: 'Cream',
  chocolate: 'Cocoa',
  banana: 'Sun',
  matcha: 'Verdant',
  fish: 'Briny',
  expired_milk: 'Curdled',
  burnt_rubber: 'Charcoal',
}

const SUFFIXES = [
  'Riot', 'Drift', 'Royale', 'Storm', 'Special',
  'Crash', 'Heist', 'Rush', 'Heat', 'Wave',
  'Whirl', 'Caper', 'Affair', 'Job', 'Number',
]

function titleCase(token: string): string {
  return token
    .split(/[_\s-]+/)
    .filter(Boolean)
    .map((p) => p.charAt(0).toUpperCase() + p.slice(1))
    .join(' ')
}

function hash(s: string): number {
  let h = 0
  for (let i = 0; i < s.length; i += 1) {
    h = (h * 31 + s.charCodeAt(i)) | 0
  }
  return Math.abs(h)
}

export function nameFor(ingredients: Ingredients | null | undefined): string {
  if (!ingredients) return 'House Blend'

  const baseKey = (ingredients.base || '').toLowerCase()
  const vibe = BASE_VIBE[baseKey] ?? titleCase(baseKey || 'mystery')
  const topInclusion = ingredients.inclusions?.[0]?.kind
  const topTopping = ingredients.toppings?.[0]?.kind
  const feature = topInclusion || topTopping

  const seedSource = [
    baseKey,
    topInclusion ?? '',
    topTopping ?? '',
    ingredients.texture ?? '',
  ].join('|')
  const suffix = SUFFIXES[hash(seedSource) % SUFFIXES.length]

  if (feature) {
    return `${vibe} ${titleCase(feature)} ${suffix}`
  }
  return `${vibe} ${suffix}`
}
