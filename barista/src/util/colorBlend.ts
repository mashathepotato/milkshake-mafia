// Weighted RGB average — close enough for a stylized demo. Subtractive
// (paint-style) mixing would be more "realistic" but requires a per-pigment
// model the assets don't carry, and the difference is barely visible at the
// final liquid's roughness/freshness setting.

export function blendColors(items: { hex: string; weight: number }[]): string {
  if (items.length === 0) return '#888888'
  let r = 0, g = 0, b = 0, total = 0
  for (const it of items) {
    const h = it.hex.replace('#', '')
    if (h.length !== 6) continue
    r += parseInt(h.slice(0, 2), 16) * it.weight
    g += parseInt(h.slice(2, 4), 16) * it.weight
    b += parseInt(h.slice(4, 6), 16) * it.weight
    total += it.weight
  }
  if (total === 0) return '#888888'
  const hex = (v: number) => Math.round(v / total).toString(16).padStart(2, '0')
  return '#' + hex(r) + hex(g) + hex(b)
}

/** Linear-interpolate between two hex colors. t in [0,1]. */
export function lerpColor(a: string, b: string, t: number): string {
  const ah = a.replace('#', '')
  const bh = b.replace('#', '')
  const lerp = (av: number, bv: number) => Math.round(av + (bv - av) * t)
  const out = (i: number) =>
    lerp(parseInt(ah.slice(i, i + 2), 16), parseInt(bh.slice(i, i + 2), 16))
      .toString(16).padStart(2, '0')
  return '#' + out(0) + out(2) + out(4)
}
