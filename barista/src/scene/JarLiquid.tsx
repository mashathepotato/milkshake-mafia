import { useEffect, useMemo, useRef } from 'react'
import { useFrame } from '@react-three/fiber'
import gsap from 'gsap'
import * as THREE from 'three'
import { LiquidMaterial } from './liquidMaterial'
import { ASSETS } from './assetRegistry'
import { blendColors, lerpColor } from '../util/colorBlend'
import type { Ingredients } from '../types/ingredients'
import type { BlendState } from '../types/state'

// Bowl interior estimates for the fused-mesh blender. Tune by eye.
const JAR_BOTTOM_Y = 0.78
const JAR_FILL_HEIGHT = 0.95
const FILL_RATIO = 0.78
const FILLED_HEIGHT = JAR_FILL_HEIGHT * FILL_RATIO

// Curved silhouette: narrow base flaring to a wider rim. Profile is built
// at full size; fill animation is shader-clipped, not scaled, so the wide
// top never appears squished into the narrow base.
const RADIUS_BOTTOM = 0.16
const RADIUS_TOP = 0.31
const CURVE_POWER = 2.4
const PROFILE_SEGMENTS = 24

interface Props {
  ingredients: Ingredients
  state: BlendState
}

function radiusAt(t: number) {
  const eased = 1 - Math.pow(1 - t, CURVE_POWER)
  return RADIUS_BOTTOM + (RADIUS_TOP - RADIUS_BOTTOM) * eased
}

function computeBlendedColor(ingredients: Ingredients): string {
  const samples: { hex: string; weight: number }[] = []
  const baseSpec = ASSETS[ingredients.base as keyof typeof ASSETS]
  if (baseSpec) samples.push({ hex: baseSpec.averageColor, weight: 3 })
  for (const inc of ingredients.inclusions) {
    const k = inc.kind === 'sprinkles' ? 'cherry' : inc.kind === 'bugs' ? 'beetle' : null
    if (k && ASSETS[k as keyof typeof ASSETS]) {
      samples.push({ hex: ASSETS[k as keyof typeof ASSETS].averageColor, weight: inc.amount * 2 })
    }
  }
  for (const t of ingredients.toppings) {
    if (t.kind === 'whipped_cream') {
      samples.push({ hex: ASSETS.whipped_cream.averageColor, weight: t.amount })
    }
  }
  return samples.length ? blendColors(samples) : ingredients.color.hex
}

export function JarLiquid({ ingredients, state }: Props) {
  const matRefBody = useRef<InstanceType<typeof LiquidMaterial>>(null!)
  const matRefDome = useRef<InstanceType<typeof LiquidMaterial>>(null!)
  const domeRef = useRef<THREE.Mesh>(null!)

  // Lathe profile: 2D points (radius, y) revolved around Y.
  const profile = useMemo(() => {
    const pts: THREE.Vector2[] = []
    for (let i = 0; i <= PROFILE_SEGMENTS; i++) {
      const t = i / PROFILE_SEGMENTS
      pts.push(new THREE.Vector2(radiusAt(t), t * FILLED_HEIGHT))
    }
    return pts
  }, [])

  const blendedHex = useMemo(() => computeBlendedColor(ingredients), [ingredients])

  // Animated state read from inside useFrame.
  const fillRef = useRef({ level: 0 }) // 0..1 — fraction of the FILLED_HEIGHT
  const colorMixRef = useRef({ t: 0 }) // 0..1 — blended → final lerp

  useEffect(() => {
    if (state === 'blending') {
      fillRef.current.level = 0
      colorMixRef.current.t = 0
      const tlFill = gsap.to(fillRef.current, {
        level: 1,
        duration: 1.4,
        ease: 'power2.out',
        delay: 1.95,
      })
      const tlColor = gsap.to(colorMixRef.current, {
        t: 1,
        duration: 1.2,
        ease: 'power1.inOut',
        delay: 2.2,
      })
      return () => { tlFill.kill(); tlColor.kill() }
    }
    if (state === 'idle') {
      fillRef.current.level = 0
      colorMixRef.current.t = 0
    }
    if (state === 'done') {
      fillRef.current.level = 1
      colorMixRef.current.t = 1
    }
  }, [state, blendedHex, ingredients.color.hex])

  useFrame((_, dt) => {
    const fill = fillRef.current.level
    const fillWorldY = JAR_BOTTOM_Y + fill * FILLED_HEIGHT
    const cur = lerpColor(blendedHex, ingredients.color.hex, colorMixRef.current.t)

    if (matRefBody.current) {
      matRefBody.current.uTime += dt
      matRefBody.current.uColor.set(cur)
      matRefBody.current.uAccent.set(ingredients.color.accent_hex)
      matRefBody.current.uViscosity = ingredients.viscosity
      matRefBody.current.uFreshness = ingredients.freshness
      matRefBody.current.uFillLevel = fillWorldY
    }
    if (matRefDome.current) {
      matRefDome.current.uTime += dt
      matRefDome.current.uColor.set(cur)
      matRefDome.current.uAccent.set(ingredients.color.accent_hex)
      matRefDome.current.uViscosity = ingredients.viscosity
      matRefDome.current.uFreshness = ingredients.freshness
      // Dome doesn't need clipping — only show it when the fill is complete.
      matRefDome.current.uFillLevel = 1e6
    }
    if (domeRef.current) {
      // Position dome at the rising fill line; scale matches the lathe radius
      // at this fraction so the meniscus snaps to the wall, no gap.
      const r = radiusAt(fill)
      domeRef.current.position.y = fill * FILLED_HEIGHT
      const s = r / RADIUS_TOP
      domeRef.current.scale.set(s, s, s)
      // Hide entirely until we have a real surface to show — under ~5% looks
      // like a floating bubble.
      domeRef.current.visible = fill > 0.05
    }
  })

  if (state === 'idle') return null

  return (
    <group position={[0, JAR_BOTTOM_Y, 0]}>
      {/* Curved liquid body — full geometry, fragments above fill line discarded. */}
      <mesh>
        <latheGeometry args={[profile, 64]} />
        <liquidMaterial ref={matRefBody} side={THREE.DoubleSide} />
      </mesh>
      {/* Surface meniscus that follows the fill line. */}
      <mesh ref={domeRef} position={[0, 0, 0]}>
        <sphereGeometry args={[RADIUS_TOP, 48, 24, 0, Math.PI * 2, 0, Math.PI / 2]} />
        <liquidMaterial ref={matRefDome} side={THREE.DoubleSide} />
      </mesh>
    </group>
  )
}
