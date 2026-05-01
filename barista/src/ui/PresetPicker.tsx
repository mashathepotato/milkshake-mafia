import { PRESET_KEYS } from '../data/mockIngredients'

interface Props {
  value: string
  onChange: (key: string) => void
  url: string
}

// Demo control surface. Real "Run" flow (URL → screenshot → Sommelier) lives
// behind this same `value`/`onChange` shape, so swapping data sources later
// won't touch the scene.
export function PresetPicker({ value, onChange, url }: Props) {
  return (
    <div className="absolute left-6 bottom-6 z-10 flex flex-col gap-3 rounded-2xl bg-black/40 p-4 backdrop-blur-md ring-1 ring-white/10">
      <div className="text-xs uppercase tracking-widest text-white/60">Preset</div>
      <div className="flex gap-2 flex-wrap max-w-md">
        {PRESET_KEYS.map((k) => (
          <button
            key={k}
            onClick={() => onChange(k)}
            className={`px-3 py-1.5 rounded-full text-sm transition ${
              value === k
                ? 'bg-white text-black'
                : 'bg-white/10 text-white hover:bg-white/20'
            }`}
          >
            {k}
          </button>
        ))}
      </div>
      <div className="text-xs text-white/40 font-mono truncate max-w-md">{url}</div>
    </div>
  )
}
