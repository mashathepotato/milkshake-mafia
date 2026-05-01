import { useGLTF, Float } from '@react-three/drei'
import { useFrame } from '@react-three/fiber'
import { useMemo, useRef } from 'react'
import * as THREE from 'three'
import { ASSETS, fitTransform, type AssetKey } from './assetRegistry'

interface Props {
  kind: AssetKey
  position: [number, number, number]
  /** Random seed (0..1) for variety in idle motion / rotation phase. */
  seed?: number
  /** If false, no Float bobbing wrapper. */
  float?: boolean
  scale?: number
}

// Generic GLB renderer. Centers + size-fits the loaded scene synchronously
// inside useMemo (same pattern as Blender) so every asset reads as a coherent
// part of the scene regardless of native units.
export function Ingredient({ kind, position, seed = 0, float = true, scale = 1 }: Props) {
  const spec = ASSETS[kind]
  const { scene } = useGLTF(spec.url)

  const cloned = useMemo(() => {
    const c = scene.clone(true)
    const { scale: fit, offset } = fitTransform(spec)
    c.scale.setScalar(fit)
    c.position.set(...offset)
    return c
  }, [scene, spec])

  const rotRef = useRef<THREE.Group>(null!)
  useFrame((_, dt) => {
    if (!rotRef.current || !spec.spinAxis) return
    rotRef.current.rotation[spec.spinAxis] += dt * (0.4 + seed * 0.6)
  })

  // Float adds gentle hover/wobble — desyncing each instance via seed-derived
  // speed/intensity stops them looking robotic.
  const inner = (
    <group ref={rotRef} scale={scale}>
      <primitive object={cloned} />
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
