import { useEffect, useMemo, useRef } from 'react'
import { useFrame } from '@react-three/fiber'
import gsap from 'gsap'
import * as THREE from 'three'
import { ASSETS } from './assetRegistry'
import type { Ingredients } from '../types/ingredients'
import type { BlendState } from '../types/state'

// Vortex particles spinning inside the jar during the mix window.
// Coloured by the actual ingredient palette so they read as the dropped
// fruits being thrown around the blade. Timed to fade in just after
// ingredients have entered, peak during the lid-close, and fade out as the
// liquid rises past them.

const JAR_BOTTOM_Y = 0.78
const JAR_HEIGHT = 0.74          // matches FILLED_HEIGHT in JarLiquid
const MIN_RADIUS = 0.06
const MAX_RADIUS = 0.26
const PARTICLE_COUNT = 60

interface ParticleData {
  baseRadius: number
  heightFrac: number
  angularSpeed: number  // rad/s at peak intensity
  phase: number
  size: number
  color: string
  yWobbleAmp: number
  yWobbleFreq: number
}

function colorsFromIngredients(ing: Ingredients): string[] {
  const out: string[] = []
  const baseSpec = ASSETS[ing.base as keyof typeof ASSETS]
  if (baseSpec) {
    // Multiple entries weight base higher in the random pick.
    out.push(baseSpec.averageColor, baseSpec.averageColor, baseSpec.averageColor)
  }
  for (const inc of ing.inclusions) {
    const k = inc.kind === 'sprinkles' ? 'cherry' : inc.kind === 'bugs' ? 'beetle' : null
    if (k && ASSETS[k as keyof typeof ASSETS]) {
      const c = ASSETS[k as keyof typeof ASSETS].averageColor
      const reps = Math.max(1, Math.round(inc.amount * 3))
      for (let i = 0; i < reps; i++) out.push(c)
    }
  }
  for (const t of ing.toppings) {
    if (t.kind === 'whipped_cream') {
      const reps = Math.max(1, Math.round(t.amount * 2))
      for (let i = 0; i < reps; i++) out.push(ASSETS.whipped_cream.averageColor)
    }
  }
  out.push(ing.color.accent_hex)
  return out.length ? out : [ing.color.hex]
}

interface Props {
  ingredients: Ingredients
  state: BlendState
}

export function SwirlVortex({ ingredients, state }: Props) {
  const colors = useMemo(() => colorsFromIngredients(ingredients), [ingredients])

  const particles = useMemo<ParticleData[]>(() => {
    return Array.from({ length: PARTICLE_COUNT }, (_, i) => {
      const s = (n: number) => ((i * (1 + n * 1.731) + n * 0.917) % 1)
      return {
        baseRadius: MIN_RADIUS + (MAX_RADIUS - MIN_RADIUS) * s(1),
        heightFrac: s(2),
        angularSpeed: 5 + s(3) * 5,         // 5–10 rad/s
        phase: s(4) * Math.PI * 2,
        size: 0.018 + s(5) * 0.022,
        color: colors[Math.floor(s(6) * colors.length)],
        yWobbleAmp: 0.04 + s(7) * 0.06,
        yWobbleFreq: 1.5 + s(8) * 2.5,
      }
    })
  }, [colors])

  const meshRefs = useRef<(THREE.Mesh | null)[]>([])
  if (meshRefs.current.length !== particles.length) {
    meshRefs.current = new Array(particles.length).fill(null)
  }

  // Intensity envelope: ramps up while ingredients still arriving + lid closes,
  // peaks before liquid fill takes over, fades as liquid rises.
  const intensityRef = useRef({ value: 0 })
  const timeRef = useRef(0)

  useEffect(() => {
    if (state === 'blending') {
      intensityRef.current.value = 0
      timeRef.current = 0
      const tl = gsap.timeline()
      tl.to(intensityRef.current, { value: 1, duration: 0.4, ease: 'power2.out' }, 1.4)
        .to(intensityRef.current, { value: 1, duration: 0.6 }, 1.8)
        .to(intensityRef.current, { value: 0, duration: 0.5, ease: 'power2.in' }, 2.6)
      return () => { tl.kill() }
    }
    intensityRef.current.value = 0
  }, [state])

  useFrame((_, dt) => {
    timeRef.current += dt
    const t = timeRef.current
    const I = intensityRef.current.value
    if (I < 0.001) {
      // Cheap path: hide everything when intensity is effectively zero.
      for (const m of meshRefs.current) if (m) m.visible = false
      return
    }
    particles.forEach((p, i) => {
      const m = meshRefs.current[i]
      if (!m) return
      m.visible = true
      const ang = t * p.angularSpeed * I + p.phase
      const r = p.baseRadius * (0.85 + 0.25 * Math.sin(t * 1.3 + p.phase))
      m.position.x = Math.cos(ang) * r
      m.position.z = Math.sin(ang) * r
      m.position.y =
        JAR_BOTTOM_Y +
        p.heightFrac * JAR_HEIGHT +
        Math.sin(t * p.yWobbleFreq + p.phase) * p.yWobbleAmp * I
      m.scale.setScalar(p.size * I)
    })
  })

  if (state !== 'blending') return null

  return (
    <>
      {particles.map((p, i) => (
        <mesh key={i} ref={(r) => { meshRefs.current[i] = r }}>
          <sphereGeometry args={[1, 10, 10]} />
          {/* toneMapped=false keeps the raw colour saturated — reads as
              "glowing pulp" rather than a dim sphere under tone mapping. */}
          <meshBasicMaterial color={p.color} toneMapped={false} />
        </mesh>
      ))}
    </>
  )
}
