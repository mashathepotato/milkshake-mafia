import { useMemo, useState } from 'react'
import { useControls } from 'leva'
import { Scene } from './scene/Scene'
import { PRESET_KEYS, PRESETS } from './data/mockIngredients'
import { PresetPicker } from './ui/PresetPicker'
import type { Ingredients } from './types/ingredients'

export default function App() {
  const [presetKey, setPresetKey] = useState<string>(PRESET_KEYS[0])
  const preset = PRESETS[presetKey]

  // Leva exposes every scalar field the shader reacts to so we can validate
  // the visual mapping (viscosity → swell amplitude, freshness → shine, etc.)
  // without redeploying mock data.
  const overrides = useControls(
    'Ingredients (override)',
    {
      colorHex: { value: preset.color.hex, label: 'color' },
      accentHex: { value: preset.color.accent_hex, label: 'accent' },
      viscosity: { value: preset.viscosity, min: 0, max: 1, step: 0.01 },
      freshness: { value: preset.freshness, min: 0, max: 1, step: 0.01 },
      sweetness: { value: preset.sweetness, min: 0, max: 1, step: 0.01 },
      tartness: { value: preset.tartness, min: 0, max: 1, step: 0.01 },
    },
    [presetKey],
  )

  const ingredients: Ingredients = useMemo(
    () => ({
      ...preset,
      color: { hex: overrides.colorHex, accent_hex: overrides.accentHex },
      viscosity: overrides.viscosity,
      freshness: overrides.freshness,
      sweetness: overrides.sweetness,
      tartness: overrides.tartness,
    }),
    [preset, overrides],
  )

  return (
    <div className="fixed inset-0">
      <Scene ingredients={ingredients} />
      <header className="absolute left-6 top-6 z-10 text-white/80">
        <div className="text-xs uppercase tracking-[0.3em] text-white/40">Milkshake Mafia</div>
        <h1 className="text-2xl font-medium">Barista</h1>
      </header>
      <PresetPicker value={presetKey} onChange={setPresetKey} url={preset.url} />
    </div>
  )
}
