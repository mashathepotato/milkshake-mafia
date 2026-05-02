import type { Ingredients } from '../types/ingredients'

export interface Chip {
  color: string
  label: string
}

// Pick black or white text for a chip based on the chip background's
// perceived luminance (Rec. 709 weights). Cheap and good enough.
export function readableTextColor(hex: string): string {
  const m = /^#?([0-9a-f]{6})$/i.exec(hex)
  if (!m) return '#000'
  const n = parseInt(m[1], 16)
  const r = (n >> 16) & 0xff
  const g = (n >> 8) & 0xff
  const b = n & 0xff
  const lum = (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255
  return lum > 0.55 ? '#000' : '#fff'
}

// Base + first inclusions + first toppings, capped so the row stays compact.
export function chipsFor(ingredients: Ingredients, max = 6): Chip[] {
  return [
    { color: ingredients.color.hex, label: ingredients.base },
    ...ingredients.inclusions.map((i) => ({
      color: ingredients.color.accent_hex,
      label: i.kind,
    })),
    ...ingredients.toppings.map((t) => ({
      color: ingredients.color.accent_hex,
      label: t.kind,
    })),
  ].slice(0, max)
}
