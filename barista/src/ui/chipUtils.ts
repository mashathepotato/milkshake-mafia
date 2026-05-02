import type React from 'react'
import type { Ingredients } from '../types/ingredients'

export interface Chip {
  color: string
  label: string
  freshness: number // [0,1] — used for opacity/saturation on render
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
// The base chip uses the global freshness; per-item chips use their own
// freshness if Sommelier emitted one (falls back to global, then 1.0).
export function chipsFor(ingredients: Ingredients, max = 6): Chip[] {
  const globalFresh = ingredients.freshness ?? 1.0
  return [
    {
      color: ingredients.color.hex,
      label: ingredients.base,
      freshness: globalFresh,
    },
    ...ingredients.inclusions.map((i) => ({
      color: ingredients.color.accent_hex,
      label: i.kind,
      freshness: i.freshness ?? globalFresh,
    })),
    ...ingredients.toppings.map((t) => ({
      color: ingredients.color.accent_hex,
      label: t.kind,
      freshness: t.freshness ?? globalFresh,
    })),
  ].slice(0, max)
}

// Visual treatment for a chip given its freshness — fresher = vivid,
// stale = washed out and slightly transparent. Cheap inline styles so
// either render site (TastingFlow, ScreenshotPreview) gets the same look.
export function chipStyle(chip: Chip): React.CSSProperties {
  const f = Math.max(0, Math.min(1, chip.freshness))
  const opacity = 0.45 + 0.55 * f
  const saturate = 0.4 + 0.6 * f
  return {
    backgroundColor: chip.color,
    color: readableTextColor(chip.color),
    boxShadow: `0 0 ${10 + 6 * f}px ${chip.color}${Math.round(0x44 + 0x44 * f)
      .toString(16)
      .padStart(2, '0')}`,
    opacity,
    filter: `saturate(${saturate.toFixed(2)})`,
  }
}
