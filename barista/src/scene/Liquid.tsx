import { useRef } from 'react'
import { useFrame } from '@react-three/fiber'
import * as THREE from 'three'
import { LiquidMaterial } from './liquidMaterial'
import type { Ingredients } from '../types/ingredients'

// Placeholder for the actual liquid volume inside the blender jar.
// Position/scale will be retuned once the real blender model's interior cavity
// is measured in-scene (drei <Bounds> + a temp helper cube).
export function Liquid({ ingredients }: { ingredients: Ingredients }) {
  const matRef = useRef<InstanceType<typeof LiquidMaterial>>(null!)
  const meshRef = useRef<THREE.Mesh>(null!)

  useFrame((_, dt) => {
    if (!matRef.current) return
    matRef.current.uTime += dt
    matRef.current.uColor.set(ingredients.color.hex)
    matRef.current.uAccent.set(ingredients.color.accent_hex)
    matRef.current.uViscosity = ingredients.viscosity
    matRef.current.uFreshness = ingredients.freshness
  })

  return (
    <mesh ref={meshRef} position={[0, 0.6, 0]}>
      {/* Dome cap (top half of a sphere, scaled flatter) — reads as the
          meniscus surface of a thick shake. */}
      <sphereGeometry args={[0.7, 96, 64, 0, Math.PI * 2, 0, Math.PI / 2]} />
      <liquidMaterial ref={matRef} />
    </mesh>
  )
}
