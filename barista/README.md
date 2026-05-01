# Barista

Frontend for the Milkshake Mafia "Taste Engine" — renders the `Ingredients` JSON
from Sommelier as a real-time stylized milkshake.

## Run

```bash
cd barista
npm install
npm run dev
```

Open the URL printed by Vite. Use the bottom-left preset buttons to switch
between mock `Ingredients` (gold/gunk × smooth/chunky). The Leva panel
(top-right) lets you live-tweak scalar fields the shader reads.

## Stack

- **Vite + React + TypeScript** — fast HMR, typed contracts
- **react-three-fiber + drei + postprocessing** — 3D scene, post chain
- **rapier** — physics (reserved for upcoming "ingredients drop into jar" beat)
- **leva** — runtime parameter tweaking
- **gsap** — choreographed animation timeline (planned)
- **tailwindcss v4** — UI chrome

## Architecture

```
src/
  types/ingredients.ts       Mirrors context/DATA_CONTRACTS.md §5 (source of truth)
  data/mockIngredients.ts    4 presets spanning the visual axes
  scene/
    Scene.tsx                Canvas + lighting + post chain
    Blender.tsx              GLB loader + toon-material override
    Liquid.tsx               Dome geometry + custom shader material
    liquidMaterial.ts        GLSL: FBM vertex displacement, fresnel rim, bubble specks
    IngredientFX.tsx         Particle FX driven by inclusions[]
    Notes.tsx                Billboarded Sommelier notes[]
  ui/PresetPicker.tsx        Demo controls
```

## Asset attributions

- **Blender** by [Poly by Google](https://poly.pizza/m/c55xJEOICb4) — licensed under
  [CC-BY 3.0](https://creativecommons.org/licenses/by/3.0/). No modifications to the
  geometry; materials are overridden at runtime.

## Next on the build

- Replace dome-cap liquid with full jar-volume mesh tied to actual jar interior
- Drop real GLB ingredient assets (strawberry, mint, sprinkles, bugs) from
  poly.pizza, animated falling into jar with `@react-three/rapier`
- GSAP timeline: lid open → ingredient drops → blade spin → liquid swirl → reveal
- Outline post-pass for unified cel-shaded silhouettes
- Real `URL → screenshot → Sommelier → Ingredients` wire-up
