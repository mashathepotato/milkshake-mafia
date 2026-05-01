import { Canvas } from '@react-three/fiber'
import {
  ContactShadows,
  Environment,
  OrbitControls,
  PerspectiveCamera,
} from '@react-three/drei'
import { ACESFilmicToneMapping } from 'three'
import { Suspense, useRef } from 'react'
import { Blender, type BlenderHandle } from './Blender'
import { IngredientFX } from './IngredientFX'
import { JarLiquid } from './JarLiquid'
import { SwirlVortex } from './SwirlVortex'
import type { Ingredients } from '../types/ingredients'
import type { BlendState } from '../types/state'

interface Props {
  ingredients: Ingredients
  state: BlendState
}

export function Scene({ ingredients, state }: Props) {
  const blenderRef = useRef<BlenderHandle>(null)

  return (
    <Canvas
      dpr={[1, 1.5]}
      gl={{ antialias: true, toneMapping: ACESFilmicToneMapping, toneMappingExposure: 1.0 }}
    >
      <PerspectiveCamera makeDefault position={[4, 2.4, 5]} fov={38} />
      <OrbitControls
        target={[0, 1, 0]}
        enablePan={false}
        minDistance={3}
        maxDistance={12}
        minPolarAngle={0.2}
        maxPolarAngle={Math.PI / 2.05}
      />

      <color attach="background" args={['#0b0d12']} />

      <Environment preset="studio" environmentIntensity={0.6} />

      <directionalLight position={[4, 6, 3]} intensity={1.0} />
      <ambientLight intensity={0.5} />

      <Suspense fallback={null}>
        <Blender ref={blenderRef} position={[0, 0, 0]} state={state} />
        <IngredientFX ingredients={ingredients} state={state} />
        <SwirlVortex ingredients={ingredients} state={state} />
        <JarLiquid ingredients={ingredients} state={state} />

        <ContactShadows
          position={[0, 0.001, 0]}
          opacity={0.45}
          scale={6}
          blur={2.4}
          far={4}
          frames={1}
        />
      </Suspense>
    </Canvas>
  )
}
