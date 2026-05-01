import { useGLTF } from '@react-three/drei'

// One entry per GLB. nativeMin/nativeMax come from raw bbox inspection
// (scripts/inspect-ingredients.mjs). targetHeight is how tall (in world units)
// we want the asset to render — keeps disparate native scales visually
// proportionate. Centering math in <Ingredient> assumes these bbox values.

export type AssetKey =
  | 'strawberry' | 'banana' | 'cherry' | 'beetle' | 'fish' | 'whipped_cream'

export interface AssetSpec {
  url: string
  nativeMin: [number, number, number]
  nativeMax: [number, number, number]
  /** Desired world-space height. Real-world ratios are tuned for visibility,
      not realism (a real strawberry next to a blender is too small to read). */
  targetHeight: number
  /** Optional spin axis for idle rotation. */
  spinAxis?: 'x' | 'y' | 'z'
  /** Representative color used when computing the blended liquid color
      after the mix animation. */
  averageColor: string
}

export const ASSETS: Record<AssetKey, AssetSpec> = {
  strawberry: {
    url: '/models/ingredients/strawberry.glb',
    nativeMin: [-13.214, -18.704, -10.381],
    nativeMax: [13.214, 18.704, 10.381],
    targetHeight: 0.34,
    spinAxis: 'y',
    averageColor: '#e74c3c',
  },
  banana: {
    url: '/models/ingredients/banana.glb',
    nativeMin: [-10.378, -42.244, -7.809],
    nativeMax: [10.378, 55.707, 35.363],
    targetHeight: 0.55,
    spinAxis: 'y',
    averageColor: '#ffd84d',
  },
  cherry: {
    url: '/models/ingredients/cherry.glb',
    nativeMin: [-1.007, -1.000, -0.955],
    nativeMax: [3.170, 4.131, 0.980],
    targetHeight: 0.22,
    spinAxis: 'y',
    averageColor: '#c0392b',
  },
  beetle: {
    url: '/models/ingredients/beetle.glb',
    nativeMin: [-43.710, -9.224, -53.768],
    nativeMax: [43.710, 7.825, 53.879],
    targetHeight: 0.18,
    spinAxis: 'y',
    averageColor: '#2c2417',
  },
  fish: {
    url: '/models/ingredients/fish.glb',
    nativeMin: [-7.772, -12.270, -40.679],
    nativeMax: [10.404, 15.191, 40.679],
    targetHeight: 0.5,
    spinAxis: 'y',
    averageColor: '#7d8f7c',
  },
  whipped_cream: {
    url: '/models/ingredients/whipped_cream.glb',
    nativeMin: [-0.068, 0.0, -0.079],
    nativeMax: [0.068, 0.097, 0.079],
    targetHeight: 0.18,
    averageColor: '#fff8e8',
  },
}

// Preload at module-evaluate so first preset switch doesn't suspend.
;(Object.values(ASSETS) as AssetSpec[]).forEach((spec) => {
  useGLTF.preload(spec.url)
})

/** Returns scale + position offset that centers the asset on origin and
    fits the desired height — call once per cloned scene graph. */
export function fitTransform(spec: AssetSpec) {
  const sizeY = spec.nativeMax[1] - spec.nativeMin[1]
  const scale = spec.targetHeight / Math.max(sizeY, 0.0001)
  const cx = (spec.nativeMin[0] + spec.nativeMax[0]) / 2
  const cy = (spec.nativeMin[1] + spec.nativeMax[1]) / 2
  const cz = (spec.nativeMin[2] + spec.nativeMax[2]) / 2
  return {
    scale,
    offset: [-cx * scale, -cy * scale, -cz * scale] as [number, number, number],
  }
}
