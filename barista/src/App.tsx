import { useEffect, useMemo, useRef, useState } from 'react'
import { useControls } from 'leva'
import { Scene } from './scene/Scene'
import { PRESET_KEYS, PRESETS } from './data/mockIngredients'
import { SOMMELIER_PRESET_KEYS, SOMMELIER_PRESETS } from './data/sommelierPresets'
import { PresetPicker } from './ui/PresetPicker'
import { BlendButton } from './ui/BlendButton'
import { ConceptNote } from './ui/ConceptNote'
import { TasteBar, type TasteSubmission } from './ui/TasteBar'
import { ScreenshotPreview } from './ui/ScreenshotPreview'
import { TastingFlow } from './ui/TastingFlow'
import type { Ingredients } from './types/ingredients'
import type { BlendState, TasteState } from './types/state'

const ALL_PRESETS: Record<string, Ingredients> = { ...PRESETS, ...SOMMELIER_PRESETS }
const ALL_KEYS: string[] = [...PRESET_KEYS, ...SOMMELIER_PRESET_KEYS]
const LIVE_KEY = 'live'

// Total blend timeline (must stay in sync with Blender.tsx + JarLiquid.tsx + IngredientFX.tsx):
//  0.0  lid lifts
//  0.35 ingredients start arcing into jar (staggered)
//  1.6  lid closes
//  1.95 liquid fill begins
//  2.2  color lerp from blended → Sommelier
//  3.4  liquid + color settled → 'done'
const BLEND_DURATION_MS = 3400

// Reveal sequence: screenshot fades in → scan beam sweeps → ingredient
// chips pop → card scales down. Must outlast the CSS keyframes (1.4s sweep).
const REVEAL_DURATION_MS = 2400

const TASTE_ENDPOINT = 'http://localhost:8000'

interface TasteResponse {
  ingredients: Ingredients
  screenshot: string | null
}

export default function App() {
  const [presetKey, setPresetKey] = useState<string>(ALL_KEYS[0])
  const [blendState, setBlendState] = useState<BlendState>('idle')
  const [tasteState, setTasteState] = useState<TasteState>('idle')
  const [livePreset, setLivePreset] = useState<Ingredients | null>(null)
  const [liveScreenshot, setLiveScreenshot] = useState<string | null>(null)
  const [tasteError, setTasteError] = useState<string | null>(null)
  const revealTimer = useRef<number | null>(null)
  const blendTimer = useRef<number | null>(null)

  const presetMap: Record<string, Ingredients> = livePreset
    ? { [LIVE_KEY]: livePreset, ...ALL_PRESETS }
    : ALL_PRESETS
  const keyList: string[] = livePreset ? [LIVE_KEY, ...ALL_KEYS] : ALL_KEYS
  const preset = presetMap[presetKey] ?? presetMap[keyList[0]]

  useEffect(() => {
    setBlendState('idle')
  }, [presetKey])

  useEffect(() => {
    return () => {
      if (revealTimer.current) window.clearTimeout(revealTimer.current)
      if (blendTimer.current) window.clearTimeout(blendTimer.current)
    }
  }, [])

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
    if (blendState === 'blending') return
    if (blendState === 'done') {
      setBlendState('idle')
      requestAnimationFrame(() => requestAnimationFrame(() => setBlendState('blending')))
    } else {
      setBlendState('blending')
    }
    if (blendTimer.current) window.clearTimeout(blendTimer.current)
    blendTimer.current = window.setTimeout(() => setBlendState('done'), BLEND_DURATION_MS)
  }

  // Drives the URL/upload → milkshake flow. The TastingFlow overlay observes
  // tasteState + the just-fetched screenshot/ingredients; once the reveal
  // window elapses we drop back to idle and trigger the existing 3D blend.
  async function handleSubmit(submission: TasteSubmission) {
    setTasteError(null)
    setTasteState('tasting')
    setLiveScreenshot(null)
    try {
      let res: Response
      if (submission.mode === 'url') {
        res = await fetch(`${TASTE_ENDPOINT}/taste`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ url: submission.url }),
        })
      } else {
        const form = new FormData()
        form.append('file', submission.file)
        res = await fetch(`${TASTE_ENDPOINT}/taste/upload`, { method: 'POST', body: form })
      }
      if (!res.ok) {
        const detail = await res.json().catch(() => ({ detail: res.statusText }))
        throw new Error(detail.detail || `HTTP ${res.status}`)
      }
      const data = (await res.json()) as TasteResponse
      setLivePreset(data.ingredients)
      setLiveScreenshot(data.screenshot)
      setPresetKey(LIVE_KEY)
      setTasteState('revealing')

      if (revealTimer.current) window.clearTimeout(revealTimer.current)
      revealTimer.current = window.setTimeout(() => {
        setTasteState('idle')
        runBlend()
      }, REVEAL_DURATION_MS)
    } catch (err) {
      setTasteError(err instanceof Error ? err.message : String(err))
      setTasteState('idle')
    }
  }

  return (
    <div className="fixed inset-0">
      <Scene ingredients={ingredients} state={blendState} />
      <header className="absolute left-6 top-6 z-10 text-white/80">
        <div className="text-xs uppercase tracking-[0.3em] text-white/40">Milkshake Mafia</div>
        <h1 className="text-2xl font-medium">Barista</h1>
      </header>
      <ConceptNote />
      <TasteBar
        busy={tasteState !== 'idle'}
        errorMessage={tasteError}
        onSubmit={handleSubmit}
      />
      <ScreenshotPreview src={liveScreenshot} url={livePreset?.url} />
      <PresetPicker value={presetKey} onChange={setPresetKey} url={preset.url} keys={keyList} />
      <BlendButton state={blendState} onRun={runBlend} />
      <TastingFlow
        state={tasteState}
        screenshot={liveScreenshot}
        ingredients={livePreset}
      />
    </div>
  )
}
