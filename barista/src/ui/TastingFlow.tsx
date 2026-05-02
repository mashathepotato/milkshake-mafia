import { useEffect, useState } from 'react'
import type { Ingredients } from '../types/ingredients'
import type { TasteState } from '../types/state'
import { chipStyle, chipsFor } from './chipUtils'

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
