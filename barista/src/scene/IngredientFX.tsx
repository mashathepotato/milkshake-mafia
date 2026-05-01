import { Sparkles } from '@react-three/drei'
import type { Ingredients } from '../types/ingredients'

// Lightweight first-pass mapping: inclusions/toppings → particle FX.
// Real GLB assets (sprinkles, mint, bugs) drop in next iteration; this gets
// the demo "alive" so timing/composition can be evaluated.
export function IngredientFX({ ingredients }: { ingredients: Ingredients }) {
  const totalSparklesAmount = ingredients.inclusions
    .filter((i) => i.kind === 'sparkles' || i.kind === 'sprinkles')
    .reduce((sum, i) => sum + i.amount, 0)

  const bugAmount = ingredients.inclusions
    .filter((i) => i.kind === 'bugs' || i.kind === 'tech_debt_chunks')
    .reduce((sum, i) => sum + i.amount, 0)

  return (
    <>
      {totalSparklesAmount > 0 && (
        <Sparkles
          count={Math.floor(40 * Math.min(1, totalSparklesAmount))}
          scale={[1.6, 1.4, 1.6]}
          position={[0, 1.0, 0]}
          size={4}
          speed={0.5}
          color={ingredients.color.accent_hex}
        />
      )}
      {bugAmount > 0 && (
        <Sparkles
          count={Math.floor(30 * Math.min(1, bugAmount))}
          scale={[1.4, 1.2, 1.4]}
          position={[0, 0.85, 0]}
          size={3}
          speed={1.2}
          color="#1a1a1a"
        />
      )}
    </>
  )
}
