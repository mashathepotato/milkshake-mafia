import { useEffect, useMemo, useRef } from 'react'
import gsap from 'gsap'
import * as THREE from 'three'
import { Sparkles } from '@react-three/drei'
import type { Ingredients } from '../types/ingredients'
import type { BlendState } from '../types/state'
import type { AssetKey } from './assetRegistry'
import { Ingredient } from './Ingredient'
import { GenericIngredient, type Slot } from './GenericIngredient'
import { colorForKind } from './ingredientPalette'

// Canonical-vocab → asset registry. Anything outside this map falls through
// to GenericIngredient (a colored sphere) instead of rendering nothing —
// see ingredientPalette.ts for the per-kind colors.
const KIND_TO_ASSET: Record<string, AssetKey> = {
  // Original GLB set.
  strawberry: 'strawberry',
  banana: 'banana',
  fish: 'fish',
  sprinkles: 'cherry',
  bugs: 'beetle',
  whipped_cream: 'whipped_cream',

  // Poly.pizza-sourced GLBs for the new fruit/gunk vocab. Some kinds reuse
  // the closest-fitting fruit (mango_cube → papaya, raspberry → its own GLB
  // which is also visually right for cherry/strawberry_chunk; pick whichever
  // shape sells best for kinds that don't have a perfect match).
  kiwi_slice: 'kiwi',
  blueberry: 'blueberries',
  raspberry: 'raspberry',
  cherry: 'raspberry',
  strawberry_chunk: 'raspberry',
  mango_cube: 'papaya',
  passionfruit: 'papaya',
  peach_slice: 'papaya',
  soggy_crouton: 'bread_loaf',
  stale_chip: 'bread_loaf',
  wilted_lettuce: 'broccoli',
  cold_pea: 'broccoli',
  mold: 'broccoli',

  // Bases — most-emitted gold/gunk choices.
  vanilla: 'marshmallows',          // soft/cream, reads as vanilla scoop
  chocolate: 'chocolate',
  matcha: 'avocado',                 // closest green object in the catalog
  // Premium kickers + toppings.
  mint: 'peppermint',
  honey_glaze: 'donut',              // glazed donut reads as the topping
  fresh_cream_dollop: 'cupcake',
  caramel_drizzle: 'cookie',
  coconut_flake: 'coconut',
  // Gunk toppings.
  mystery_sauce: 'flan',             // wobbly mystery dessert as the gunk garnish
}

type Spawn = {
  key: string
  position: [number, number, number]
  seed: number
  /** Slot in the jar to drop into — randomized but deterministic per spawn. */
  drop: [number, number, number]
} & (
  | { type: 'glb'; asset: AssetKey }
  | { type: 'generic'; slot: Slot; color: string }
)

function ringPositions(count: number, radius: number, height: number, phase: number) {
  return Array.from({ length: count }, (_, i) => {
    const t = (i + phase) / Math.max(count, 1)
    const angle = t * Math.PI * 2
    const wobble = ((i * 13.37) % 1) * 0.4
    const r = radius + (wobble - 0.2) * 0.3
    const y = height + ((i * 7.91) % 1) * 0.4
    return [Math.cos(angle) * r, y, Math.sin(angle) * r] as [number, number, number]
  })
}

function jarSlot(seed: number): [number, number, number] {
  // Bowl interior is ~0.93 wide, ~0.56 deep. Stay well inside.
  const a = seed * Math.PI * 2
  const r = 0.12 + ((seed * 31) % 1) * 0.1
  return [Math.cos(a) * r, 1.45, Math.sin(a) * r * 0.6]
}

interface Props {
  ingredients: Ingredients
  state: BlendState
}

export function IngredientFX({ ingredients, state }: Props) {
  const spawns = useMemo<Spawn[]>(() => {
    const result: Spawn[] = []

    // Base — 3 instances arranged in a ring above the blender.
    const baseAsset = KIND_TO_ASSET[ingredients.base]
    const basePositions = ringPositions(3, 1.6, 2.9, 0)
    basePositions.forEach((p, i) => {
      const seed = (i * 0.371) % 1
      const common = { key: `base-${i}`, position: p, seed, drop: jarSlot(seed) }
      if (baseAsset) {
        result.push({ ...common, type: 'glb', asset: baseAsset })
      } else {
        result.push({ ...common, type: 'generic', slot: 'base', color: colorForKind(ingredients.base) })
      }
    })

    // Inclusions — count scales with amount; ring above the base ring.
    ingredients.inclusions.forEach((inc, ix) => {
      // `sparkles` has its own Drei <Sparkles> particle overlay below;
      // skip it here so we don't double-render it as colored spheres too.
      if (inc.kind === 'sparkles') return
      const asset = KIND_TO_ASSET[inc.kind]
      const count = Math.max(1, Math.round(inc.amount * 6))
      const positions = ringPositions(count, 1.1, 2.4, ix * 0.15)
      positions.forEach((p, i) => {
        const seed = ((ix * 7 + i) * 0.371) % 1
        const common = { key: `inc-${ix}-${i}`, position: p, seed, drop: jarSlot(seed) }
        if (asset) {
          result.push({ ...common, type: 'glb', asset })
        } else {
          result.push({ ...common, type: 'generic', slot: 'inclusion', color: colorForKind(inc.kind) })
        }
      })
    })

    // Toppings — single instance per kind, perched above the jar.
    ingredients.toppings.forEach((t, ix) => {
      const asset = KIND_TO_ASSET[t.kind]
      const seed = 0.2 + ix * 0.1
      const common = {
        key: `top-${ix}`,
        position: [0, 2.05, 0] as [number, number, number],
        seed,
        drop: jarSlot(seed),
      }
      if (asset) {
        result.push({ ...common, type: 'glb', asset })
      } else {
        result.push({ ...common, type: 'generic', slot: 'topping', color: colorForKind(t.kind) })
      }
    })

    return result
  }, [ingredients])

  const groupRefs = useRef<(THREE.Group | null)[]>([])

  // Reset refs array length when spawn list changes (preset switch).
  if (groupRefs.current.length !== spawns.length) {
    groupRefs.current = new Array(spawns.length).fill(null)
  }

  // Drop animation when state goes to 'blending'. Stagger by index so it reads
  // as an ordered pour rather than a synchronized teleport.
  useEffect(() => {
    if (state !== 'blending') return
    const tl = gsap.timeline()
    spawns.forEach((s, i) => {
      const g = groupRefs.current[i]
      if (!g) return
      const delay = 0.35 + i * 0.04
      tl.to(g.position, {
        x: s.drop[0],
        y: s.drop[1],
        z: s.drop[2],
        duration: 0.6,
        ease: 'power2.in',
      }, delay)
      .to(g.scale, {
        x: 0.001, y: 0.001, z: 0.001,
        duration: 0.35,
        ease: 'power2.in',
      }, delay + 0.35)
    })
    return () => { tl.kill() }
  }, [state, spawns])

  // Returning to idle (preset switch or replay): restore positions + scale.
  useEffect(() => {
    if (state !== 'idle') return
    spawns.forEach((s, i) => {
      const g = groupRefs.current[i]
      if (!g) return
      g.position.set(...s.position)
      g.scale.setScalar(1)
    })
  }, [state, spawns])

  const sparkleAmount = ingredients.inclusions
    .filter((i) => i.kind === 'sparkles')
    .reduce((sum, i) => sum + i.amount, 0)

  if (state === 'done') return null

  return (
    <>
      {spawns.map((s, i) => (
        <group
          key={s.key}
          ref={(r) => { groupRefs.current[i] = r }}
          position={s.position}
        >
          {s.type === 'glb' ? (
            <Ingredient kind={s.asset} position={[0, 0, 0]} seed={s.seed} float={state === 'idle'} />
          ) : (
            <GenericIngredient
              color={s.color}
              slot={s.slot}
              position={[0, 0, 0]}
              seed={s.seed}
              float={state === 'idle'}
            />
          )}
        </group>
      ))}

      {state === 'idle' && sparkleAmount > 0 && (
        <Sparkles
          count={Math.floor(60 * Math.min(1, sparkleAmount))}
          scale={[3, 2, 3]}
          position={[0, 1.6, 0]}
          size={5}
          speed={0.4}
          color={ingredients.color.accent_hex}
        />
      )}
    </>
  )
}
