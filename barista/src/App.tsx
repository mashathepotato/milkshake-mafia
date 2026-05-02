import { useEffect, useMemo, useState } from 'react'
import { useControls } from 'leva'
import { Scene } from './scene/Scene'
import { PRESET_KEYS, PRESETS } from './data/mockIngredients'
import { PresetPicker } from './ui/PresetPicker'
import { BlendButton } from './ui/BlendButton'
import { ConceptNote } from './ui/ConceptNote'
import type { Ingredients } from './types/ingredients'
import type { BlendState } from './types/state'

// Total blend timeline (must stay in sync with Blender.tsx + JarLiquid.tsx + IngredientFX.tsx):
//  0.0  lid lifts
//  0.35 ingredients start arcing into jar (staggered)
//  1.6  lid closes
//  1.95 liquid fill begins
//  2.2  color lerp from blended → Sommelier
//  3.4  liquid + color settled → 'done'
const BLEND_DURATION_MS = 3400

export default function App() {
  const [presetKey, setPresetKey] = useState<string>(PRESET_KEYS[0])
  const [state, setState] = useState<BlendState>('idle')
  const preset = PRESETS[presetKey]

  // Switching presets resets everything to idle. Saves users from manually
  // re-running between previews.
  useEffect(() => {
    setState('idle')
  }, [presetKey])

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

  function runBlend() {
    if (state === 'blending') return
    // From 'done', briefly go through 'idle' so child components reset cleanly.
    if (state === 'done') {
      setState('idle')
      requestAnimationFrame(() => requestAnimationFrame(() => setState('blending')))
    } else {
      setState('blending')
    }
    setTimeout(() => setState('done'), BLEND_DURATION_MS)
  }

  return (
    <div className="fixed inset-0">
      <Scene ingredients={ingredients} state={state} />
      <header className="absolute left-6 top-6 z-10 text-white/80">
        <div className="text-xs uppercase tracking-[0.3em] text-white/40">Milkshake Mafia</div>
        <h1 className="text-2xl font-medium">Barista</h1>
      </header>
      <ConceptNote />
      <PresetPicker value={presetKey} onChange={setPresetKey} url={preset.url} />
      <BlendButton state={state} onRun={runBlend} />
    </div>
  )
}
