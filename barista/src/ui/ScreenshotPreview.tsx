import type { Ingredients } from '../types/ingredients'
import { chipsFor, readableTextColor } from './chipUtils'

// Persistent reference panel for the most-recently tasted URL/upload.
// Renders the ingredient chips above the screenshot so the user can see
// the chosen base/inclusions/toppings while looking at the source image.
export function ScreenshotPreview({ src, ingredients }: Props) {
  if (!src && !ingredients) return null
  const chips = ingredients ? chipsFor(ingredients) : []

  return (
    <div className="absolute right-6 top-[260px] z-10 flex w-[360px] flex-col gap-2 rounded-2xl bg-black/40 p-3 backdrop-blur-md ring-1 ring-white/10">
      <div className="flex items-baseline justify-between">
        <div className="text-xs uppercase tracking-widest text-white/60">What we tasted</div>
        {ingredients?.url && (
          <div className="ml-2 truncate font-mono text-[10px] text-white/40">{ingredients.url}</div>
        )}
      </div>

      {chips.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {chips.map((c, i) => (
            <span
              key={i}
              className="rounded-full px-2.5 py-0.5 text-[11px] font-medium"
              style={{
                backgroundColor: c.color,
                color: readableTextColor(c.color),
                boxShadow: `0 0 10px ${c.color}55`,
              }}
            >
              {c.label}
            </span>
          ))}
        </div>
      )}

      {src && (
        <div className="max-h-[260px] overflow-hidden rounded-lg ring-1 ring-white/10">
          <img src={src} alt="Captured screenshot" className="block h-auto w-full" />
        </div>
      )}
    </div>
  )
}
