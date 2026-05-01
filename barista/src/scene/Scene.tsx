import { Canvas } from '@react-three/fiber'
import {
  ContactShadows,
  Environment,
  Float,
  OrbitControls,
  PerspectiveCamera,
} from '@react-three/drei'
import {
  Bloom,
  ChromaticAberration,
  EffectComposer,
  Noise,
  Vignette,
} from '@react-three/postprocessing'
import { ACESFilmicToneMapping } from 'three'
import { BlendFunction } from 'postprocessing'
import { Suspense } from 'react'
import { Blender } from './Blender'
import { Liquid } from './Liquid'
import { IngredientFX } from './IngredientFX'
import { Notes } from './Notes'
import type { Ingredients } from '../types/ingredients'

export function Scene({ ingredients }: { ingredients: Ingredients }) {
  return (
    <Canvas
      shadows
      dpr={[1, 2]}
      gl={{ antialias: true, toneMapping: ACESFilmicToneMapping, toneMappingExposure: 1.05 }}
    >
      <PerspectiveCamera makeDefault position={[3.5, 2.6, 4.2]} fov={38} />
      <OrbitControls
        target={[0, 0.9, 0]}
        enablePan={false}
        minDistance={3}
        maxDistance={9}
        minPolarAngle={0.2}
        maxPolarAngle={Math.PI / 2.05}
      />

      <color attach="background" args={['#0b0d12']} />

      {/* HDRI does the heavy lifting for material believability. */}
      <Environment preset="studio" environmentIntensity={0.7} />

      {/* Key light to crisp the toon shading bands. */}
      <directionalLight
        position={[4, 6, 3]}
        intensity={1.4}
        castShadow
        shadow-mapSize-width={1024}
        shadow-mapSize-height={1024}
      />
      <ambientLight intensity={0.2} />

      <Suspense fallback={null}>
        <Float floatIntensity={0.15} rotationIntensity={0} speed={0.6}>
          <Blender position={[0, 0, 0]} />
          <Liquid ingredients={ingredients} />
        </Float>

        <IngredientFX ingredients={ingredients} />
        <Notes ingredients={ingredients} />

        <ContactShadows
          position={[0, -0.01, 0]}
          opacity={0.55}
          scale={6}
          blur={2.4}
          far={4}
        />
      </Suspense>

      <EffectComposer>
        <Bloom intensity={0.55} luminanceThreshold={0.6} luminanceSmoothing={0.4} mipmapBlur />
        <ChromaticAberration
          offset={[0.0008, 0.0012]}
          radialModulation={false}
          modulationOffset={0}
          blendFunction={BlendFunction.NORMAL}
        />
        <Noise opacity={0.05} />
        <Vignette eskil={false} offset={0.18} darkness={0.55} />
      </EffectComposer>
    </Canvas>
  )
}
