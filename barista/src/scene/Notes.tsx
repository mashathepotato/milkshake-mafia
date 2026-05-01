import { Billboard, Text } from '@react-three/drei'
import type { Ingredients } from '../types/ingredients'

// Floating Sommelier notes. Billboard so the 3D label always faces the camera —
// readable as the user orbits without needing 2D HTML overlay (which would
// fight the post-processing pipeline).
export function Notes({ ingredients }: { ingredients: Ingredients }) {
  const visible = ingredients.notes.slice(0, 4)
  return (
    <>
      {visible.map((note, i) => {
        const angle = (i / Math.max(visible.length, 1)) * Math.PI * 2
        const r = 2.6
        const y = 1.4 + (i % 2) * 0.4
        return (
          <Billboard
            key={`${note}-${i}`}
            position={[Math.cos(angle) * r, y, Math.sin(angle) * r]}
          >
            <Text
              fontSize={0.22}
              color="#ffffff"
              anchorX="center"
              anchorY="middle"
              outlineWidth={0.012}
              outlineColor="#000000"
            >
              {note}
            </Text>
          </Billboard>
        )
      })}
    </>
  )
}
