import { useGLTF } from '@react-three/drei'
import { useEffect, useMemo } from 'react'
import * as THREE from 'three'

// Loads the Poly by Google blender (CC-BY 3.0). Re-skin every mesh with
// MeshToonMaterial + a 3-step gradient ramp so the imported asset matches the
// stylized look of the rest of the scene rather than its original PBR bake.
useGLTF.preload('/models/blender.glb')

function makeToonGradient(): THREE.DataTexture {
  // 3 brightness bands → cel-shaded. Power-of-two width keeps GPUs happy.
  const data = new Uint8Array([60, 60, 60, 255, 170, 170, 170, 255, 240, 240, 240, 255])
  const tex = new THREE.DataTexture(data, 3, 1, THREE.RGBAFormat)
  tex.minFilter = THREE.NearestFilter
  tex.magFilter = THREE.NearestFilter
  tex.needsUpdate = true
  return tex
}

export function Blender({ position = [0, 0, 0] as [number, number, number] }) {
  const { scene } = useGLTF('/models/blender.glb')
  const gradient = useMemo(makeToonGradient, [])

  // Clone so multiple instances (or HMR swaps) don't share mutated materials.
  const cloned = useMemo(() => scene.clone(true), [scene])

  useEffect(() => {
    cloned.traverse((obj) => {
      if (obj instanceof THREE.Mesh) {
        const original = obj.material as THREE.MeshStandardMaterial | undefined
        const baseColor = original?.color?.clone() ?? new THREE.Color('#cccccc')
        obj.material = new THREE.MeshToonMaterial({
          color: baseColor,
          gradientMap: gradient,
        })
        obj.castShadow = true
        obj.receiveShadow = true
      }
    })
  }, [cloned, gradient])

  return <primitive object={cloned} position={position} scale={1.6} />
}
