import { useEffect, useState } from 'react'
import type { Ingredients } from '../types/ingredients'
import type { TasteState } from '../types/state'
import { chipStyle, chipsFor, readableTextColor } from './chipUtils'

interface Props {
  state: TasteState
  screenshot: string | null
  ingredients: Ingredients | null
}

const TASTING_TICKER = [
  'Capturing screenshot…',
  'Embedding through DINOv2…',
  'Projecting through Sommelier cellar…',
  'Composing ingredients…',
]

// Ingredient swatches that float behind the scan shimmer while we wait for
// the API. Mix of good bases, fruits, gunk garnish, and toppings — visualizes
// the menu sommelier is sifting through. Coordinates are deterministic so
// the swirl looks the same every render (no React-induced layout reshuffles).
const CANDIDATE_VOCAB: ReadonlyArray<{ label: string; color: string; x: number; y: number }> = [
  { label: 'strawberry',     color: '#ff4da6', x:  8, y: 10 },
  { label: 'vanilla',        color: '#f3e5ab', x: 78, y:  8 },
  { label: 'matcha',         color: '#8fbf6a', x: 38, y: 16 },
  { label: 'chocolate',      color: '#6b3f1d', x: 60, y: 24 },
  { label: 'banana',         color: '#f7d36c', x: 16, y: 36 },
  { label: 'mango_cube',     color: '#ffb347', x: 70, y: 44 },
  { label: 'kiwi_slice',     color: '#88c45a', x: 42, y: 52 },
  { label: 'raspberry',      color: '#e74c3c', x: 14, y: 62 },
  { label: 'blueberry',      color: '#4f7cb0', x: 80, y: 64 },
  { label: 'cherry',         color: '#c0392b', x: 58, y: 72 },
  { label: 'passionfruit',   color: '#ffaa3b', x: 30, y: 80 },
  { label: 'fish',           color: '#4f7c8c', x: 88, y: 32 },
  { label: 'mold',           color: '#5a6647', x: 22, y: 88 },
  { label: 'eggshell',       color: '#e8dfc8', x: 66, y: 90 },
  { label: 'mystery_sauce',  color: '#7c4a4a', x:  6, y: 80 },
  { label: 'whipped_cream',  color: '#fff8e8', x: 50, y:  4 },
  { label: 'honey_glaze',    color: '#f3c87a', x: 92, y: 78 },
  { label: 'burnt_marshmallow', color: '#3a2a22', x: 24, y: 24 },
]

// Visual transition that sits between the user submitting a URL and the 3D
// blend animation kicking off. While 'tasting', shows a centered scanning
// card with cycling status text (we have nothing else until the API responds).
// On 'revealing', the screenshot fades in inside the same card; a horizontal
// beam sweeps across it once; ingredient swatches puff out as colored chips
// that drift toward the blender; finally the card scales down + dims.
export function TastingFlow({ state, screenshot, ingredients }: Props) {
  const [tickerIndex, setTickerIndex] = useState(0)

  useEffect(() => {
    if (state !== 'tasting') return
    const id = setInterval(
      () => setTickerIndex((i) => (i + 1) % TASTING_TICKER.length),
      1600,
    )
    return () => clearInterval(id)
  }, [state])

  if (state === 'idle') return null

  const baseColor = ingredients?.color.hex ?? '#9ad7ff'
  const accent = ingredients?.color.accent_hex ?? '#ffffff'

  const chips = ingredients ? chipsFor(ingredients) : []

  return (
    <div className="pointer-events-none absolute inset-0 z-20 flex items-center justify-center">
      {/* Backdrop dimmer fades in/out with state */}
      <div
        className={`absolute inset-0 bg-black/50 backdrop-blur-sm transition-opacity duration-500 ${
          state === 'tasting' || state === 'revealing' ? 'opacity-100' : 'opacity-0'
        }`}
      />

      <div
        className={`relative flex flex-col items-center gap-4 transition-all duration-700 ease-in-out ${
          state === 'revealing'
            ? 'scale-95 opacity-95 translate-y-0'
            : 'scale-100 opacity-100'
        }`}
      >
        <div
          className="relative w-[480px] max-w-[90vw] overflow-hidden rounded-2xl ring-1 ring-white/15 shadow-2xl"
          style={{ aspectRatio: '4 / 3' }}
        >
          {/* Placeholder background while no screenshot yet */}
          <div className="absolute inset-0 bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900" />

          {/* Floating candidate ingredient chips while tasting — swirling
              menu of possibilities sommelier is sifting through. Each chip
              has a different float duration + delay so the cloud pulses
              and breathes asymmetrically. */}
          <div
            className={`absolute inset-0 transition-opacity duration-500 ${
              state === 'tasting' ? 'opacity-90' : 'opacity-0'
            }`}
          >
            {CANDIDATE_VOCAB.map((c, i) => (
              <span
                key={c.label}
                className="absolute rounded-full px-2 py-0.5 text-[10px] font-medium tasting-candidate"
                style={{
                  left: `${c.x}%`,
                  top: `${c.y}%`,
                  backgroundColor: c.color,
                  color: readableTextColor(c.color),
                  boxShadow: `0 0 12px ${c.color}99`,
                  // Stagger so the cloud looks alive: each chip has its own
                  // breath cycle (3.6–6.4s) and starts mid-cycle.
                  animationDuration: `${3.6 + (i % 5) * 0.7}s`,
                  animationDelay: `${(i * 0.31) % 4}s`,
                  willChange: 'transform, opacity',
                }}
              >
                {c.label}
              </span>
            ))}
          </div>

          {/* Screenshot fades in once available */}
          {screenshot && (
            <img
              src={screenshot}
              alt="Captured screenshot"
              className={`absolute inset-0 h-full w-full object-cover object-top transition-opacity duration-500 ${
                state === 'revealing' ? 'opacity-100' : 'opacity-0'
              }`}
            />
          )}

          {/* Scan-line shimmer (continuous) */}
          <div className="absolute inset-0 tasting-scan opacity-60" />

          {/* Sweep beam during reveal */}
          {state === 'revealing' && (
            <div
              className="absolute left-0 right-0 h-12 reveal-sweep"
              style={{
                background: `linear-gradient(180deg, transparent, ${accent}55, ${baseColor}99, ${accent}55, transparent)`,
                mixBlendMode: 'screen',
              }}
            />
          )}

          {/* Soft vignette + frame glow */}
          <div className="absolute inset-0 pointer-events-none ring-1 ring-inset ring-white/10 rounded-2xl" />
        </div>

        {/* Status text (tasting) or ingredient breakdown (revealing) */}
        <div className="h-12 flex items-center justify-center text-sm text-white/80 font-mono tracking-wide">
          {state === 'tasting' ? (
            <span className="inline-flex items-center gap-2">
              <span className="inline-block size-2 rounded-full bg-white/70 animate-pulse" />
              {TASTING_TICKER[tickerIndex]}
            </span>
          ) : (
            <div className="flex gap-2 chips-fade-in flex-wrap justify-center">
              {chips.map((c, i) => (
                <span
                  key={i}
                  className="rounded-full px-3 py-1 text-xs font-medium inline-flex items-center gap-1.5"
                  style={{ ...chipStyle(c), animationDelay: `${i * 80}ms` }}
                  title={`freshness ${c.freshness.toFixed(2)}`}
                >
                  {c.label}
                  <span className="text-[10px] opacity-70 font-mono">
                    ♥{Math.round(c.freshness * 100)}
                  </span>
                </span>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
