import { Float } from '@react-three/drei'
import { useFrame } from '@react-three/fiber'
import { useRef } from 'react'
import * as THREE from 'three'

export type Slot = 'base' | 'inclusion' | 'topping'

interface Props {
  color: string
  slot: Slot
  position: [number, number, number]
  /** Random seed (0..1) for variety in idle motion / rotation phase. */
  seed?: number
  float?: boolean
}

// Sized to roughly match the GLB ingredients in assetRegistry.ts:
// base ~ strawberry/banana, inclusion ~ cherry/sprinkles, topping ~ dollop.
const RADIUS: Record<Slot, number> = {
  base: 0.16,
  inclusion: 0.09,
  topping: 0.07,
}

// Colored-sphere stand-in for any ingredient kind without a registered GLB.
// Reads as "a blob of this flavor" — good enough for the blend animation
// to show *something* representative of every Sommelier-emitted kind without
// requiring 30+ GLB downloads. Wire poly.pizza GLBs into assetRegistry.ts
// later to upgrade specific kinds (e.g. mango_cube → an actual mango mesh)
// and the dispatch in IngredientFX will pick them up automatically.
export function GenericIngredient({ color, slot, position, seed = 0, float = true }: Props) {
  const rotRef = useRef<THREE.Group>(null!)
  useFrame((_, dt) => {
    if (!rotRef.current) return
    rotRef.current.rotation.y += dt * (0.4 + seed * 0.6)
  })

  const radius = RADIUS[slot]
  const inner = (
    <group ref={rotRef}>
      <mesh castShadow>
        <sphereGeometry args={[radius, 24, 18]} />
        <meshStandardMaterial color={color} roughness={0.45} metalness={0.05} />
      </mesh>
    </group>
  )

  return (
    <group position={position}>
      {float ? (
        <Float
          speed={1.0 + seed * 0.6}
          rotationIntensity={0.2}
          floatIntensity={0.4 + seed * 0.3}
          floatingRange={[-0.08, 0.08]}
        >
          {inner}
        </Float>
      ) : (
        inner
      )}
    </group>
  )
}
