import { useGLTF } from '@react-three/drei'
import { forwardRef, useEffect, useImperativeHandle, useMemo, useRef } from 'react'
import { useFrame } from '@react-three/fiber'
import gsap from 'gsap'
import * as THREE from 'three'
import type { BlendState } from '../types/state'

// Loads the Poly by Google blender (CC-BY 3.0). Native bbox: 344u tall,
// scale = 2/344 = 0.00581.
//
// Tree contains three named meshes — Blender (motor), Bowl (jar), Blender_Cap
// (lid). We grab a ref to Blender_Cap so the blend timeline can animate it.
// All transforms applied inside useMemo (synchronous) to avoid the matrixWorld
// race we saw with runtime Box3 measurement.
// New model (poly.pizza/m/5on5mJSu0gT, Poly by Google CC-BY) ships as one
// fused mesh — no separable Blender_Cap node, so lid animation no-ops below.
//
// Center X/Z derived from the LID primitive (#4) and BASE primitive (#6),
// not the full bbox. Both are symmetric around (~4, ~-3); the full-bbox
// center is pulled to (17, -3) by an asymmetric handle on the +x side.
// Centering on the jar axis keeps the liquid mesh inside the bowl —
// the handle correctly sticks out to one side instead.
const NATIVE_HEIGHT = 269.13
const NATIVE_MIN_Y = 3.79
const NATIVE_CENTER_X = 4.2
const NATIVE_CENTER_Z = -3.2
const TARGET_HEIGHT = 2.0
const FIT_SCALE = TARGET_HEIGHT / NATIVE_HEIGHT

// 0.45 world-space lift in local (cloned-scene) units. Local unit = native unit
// since scale is applied to the cloned root, so cap's own position is in
// native space (~344 tall).
const CAP_LIFT_LOCAL = 0.45 / FIT_SCALE
const CAP_TILT_RAD = 0.35

useGLTF.preload('/models/blender.glb')

export interface BlenderHandle {
  /** Whole blender root (for camera shake etc.) */
  root: THREE.Group | null
}

interface Props {
  position?: [number, number, number]
  state: BlendState
}

export const Blender = forwardRef<BlenderHandle, Props>(function Blender(
  { position = [0, 0, 0], state },
  ref,
) {
  const { scene } = useGLTF('/models/blender.glb')
  const rootRef = useRef<THREE.Group>(null!)

  // Clone + apply scale/lift sync. Also detach the cap so we can animate it
  // freely without nested matrix math from the cloned root's scale.
  const { mainScene, cap } = useMemo(() => {
    const c = scene.clone(true)
    c.scale.setScalar(FIT_SCALE)
    c.position.set(
      -NATIVE_CENTER_X * FIT_SCALE,
      -NATIVE_MIN_Y * FIT_SCALE,
      -NATIVE_CENTER_Z * FIT_SCALE,
    )
    let foundCap: THREE.Object3D | null = null
    c.traverse((obj) => {
      if (obj.name === 'Blender_Cap') foundCap = obj
    })
    return { mainScene: c, cap: foundCap as THREE.Object3D | null }
  }, [scene])

  const capInitialPos = useRef<THREE.Vector3 | null>(null)
  const capInitialRot = useRef<THREE.Euler | null>(null)

  useEffect(() => {
    if (cap && !capInitialPos.current) {
      capInitialPos.current = cap.position.clone()
      capInitialRot.current = cap.rotation.clone()
    }
  }, [cap])

  // Lid choreography keyed off blend state transitions.
  useEffect(() => {
    if (!cap || !capInitialPos.current || !capInitialRot.current) return
    const home = capInitialPos.current
    const homeRot = capInitialRot.current

    if (state === 'blending') {
      const tl = gsap.timeline()
      tl.to(cap.position, {
        y: home.y + CAP_LIFT_LOCAL,
        z: home.z - CAP_LIFT_LOCAL * 0.4,
        duration: 0.4,
        ease: 'power2.out',
      }, 0)
        .to(cap.rotation, { x: homeRot.x - CAP_TILT_RAD, duration: 0.4, ease: 'power2.out' }, 0)
        // close after the drop completes (drop window: 0.3-1.5s)
        .to(cap.position, { y: home.y, z: home.z, duration: 0.35, ease: 'power2.in' }, 1.6)
        .to(cap.rotation, { x: homeRot.x, duration: 0.35, ease: 'power2.in' }, 1.6)
      return () => { tl.kill() }
    } else if (state === 'idle') {
      gsap.to(cap.position, { x: home.x, y: home.y, z: home.z, duration: 0.3 })
      gsap.to(cap.rotation, { x: homeRot.x, y: homeRot.y, z: homeRot.z, duration: 0.3 })
    }
  }, [state, cap])

  // Subtle camera shake during the spin window — sells "the blade is going."
  useFrame((three) => {
    if (state !== 'blending' || !rootRef.current) return
    rootRef.current.rotation.y = (Math.random() - 0.5) * 0.003
    rootRef.current.position.x = (Math.random() - 0.5) * 0.005
    void three
  })

  useImperativeHandle(ref, () => ({ root: rootRef.current }), [])

  return (
    <group ref={rootRef} position={position}>
      <primitive object={mainScene} />
    </group>
  )
})
