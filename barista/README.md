# Barista

Frontend tier of the Milkshake Mafia "Taste Engine." Consumes the
`Ingredients` JSON from Sommelier (or 4 built-in mocks) and renders it as a
real-time stylized milkshake: ingredients hover above a 3D blender, drop into
the jar on a "Run blend" click, swirl in a coloured vortex while the shake
fills the jar, and settle at the Sommelier's final colour.

```
┌───────────────┐  CaptureRequest  ┌──────────────┐  TasteRequest  ┌──────────────┐  Ingredients  ┌──────────────┐
│  User / Demo  │ ───────────────► │ Photographer │ ─────────────► │  Sommelier   │ ────────────► │   BARISTA    │
│    Runner     │ ◄─────────────── │   (URL→png   │ ◄──────────────│  (PCA →      │               │  (this app)  │
└───────────────┘  Ingredients     │   →embed)    │                │  ingredients)│               └──────────────┘
                                   └──────────────┘                └──────────────┘
```

## Run

```bash
cd barista
npm install
npm run dev
```

Bottom-left preset buttons switch between 4 mock `Ingredients` (gold/gunk ×
smooth/chunky). Leva panel (top-right) live-tweaks scalar fields. Bottom-right
**Run blend** triggers the full mix animation.

---

## How this connects to the rest of the hackathon

### Input contract (what Barista expects)

The only thing this app reads from upstream is an `Ingredients` object
matching `context/DATA_CONTRACTS.md §5`. The TypeScript mirror lives at
`src/types/ingredients.ts` — keep both in lockstep when the contract evolves.

```ts
{
  base: 'strawberry' | 'vanilla' | 'fish' | ...,
  color: { hex: '#ff5b8a', accent_hex: '#ffd2dd' },
  texture: 'smooth' | 'chunky' | 'sludge' | ...,
  viscosity: 0.0–1.0,
  freshness: 0.0–1.0,
  // ...tartness, sweetness
  inclusions: [{ kind: 'sprinkles' | 'bugs' | ..., amount: 0–1 }],
  toppings:   [{ kind: 'whipped_cream' | ..., amount: 0–1 }],
  notes: ['Premium spacing', ...],
  meta: { /* PCA debug, model id, baseline id */ },
}
```

### Visual mapping (Sommelier vocab → Barista renders)

This is the table Sommelier should target. Anything outside this list
falls through silently (no error, just no visual). Add new vocab by:
1. Updating `context/VOCAB.md`
2. Sourcing a GLB / extending the shader
3. Adding the entry to `src/scene/assetRegistry.ts`
4. Mapping it in `src/scene/IngredientFX.tsx#KIND_TO_ASSET`

| Sommelier emits | What Barista renders | Asset / mechanic |
|---|---|---|
| `base: 'strawberry'` | 3 strawberry GLBs hovering, red liquid blend | `ingredients/strawberry.glb` (Poly by Google, CC-BY) |
| `base: 'banana'` | 3 banana GLBs, yellow blend | `ingredients/banana.glb` |
| `base: 'vanilla' / 'matcha' / 'chocolate'` | (no GLB yet — falls back to `color.hex`) | extend registry |
| `base: 'fish' / 'expired_milk' / 'burnt_rubber'` | 3 fish GLBs (or beetles fallback) | `ingredients/fish.glb`, `ingredients/beetle.glb` |
| `inclusion: 'sprinkles'` | Cherry GLBs as sprinkle stand-in | `ingredients/cherry.glb` |
| `inclusion: 'sparkles'` | drei `<Sparkles>` particles in accent colour | particle FX |
| `inclusion: 'mint'` | (no GLB yet) | extend registry |
| `inclusion: 'bugs' / 'tech_debt_chunks'` | Beetle GLBs swarming | `ingredients/beetle.glb` |
| `topping: 'whipped_cream'` | Whipped-cream dollop on top of the lid | `ingredients/whipped_cream.glb` (Kenney, CC0) |
| `topping: 'lint_dust' / 'burnt_marshmallow'` | (no GLB yet) | extend registry |
| `color.hex` | Final liquid colour after the blend animation lerps from the computed average → this value | `JarLiquid.tsx` |
| `color.accent_hex` | Liquid surface highlight, sparkle particles | `liquidMaterial.ts`, `IngredientFX.tsx` |
| `viscosity` | Liquid surface ripple speed + amplitude (low = quick ripples, high = slow swells) | `liquidMaterial.ts` |
| `freshness` | Liquid sheen, bubble spec density, fresnel rim brightness | `liquidMaterial.ts` |
| `texture` | (planned: smooth/chunky surface noise variation) | extend shader |
| `notes` | (currently UI overlay text — re-add as billboarded 3D labels later if desired) | — |

### Wiring up real Sommelier output (replacing the mocks)

Today: `App.tsx` reads from `data/mockIngredients.ts` and passes through Leva
overrides to `<Scene>`. Single source: the `ingredients: Ingredients` prop.

Drop-in replacement when Sommelier is ready (Pattern A — single orchestrator
calling Sommelier over HTTP):

```ts
const [ingredients, setIngredients] = useState<Ingredients | null>(null)
async function runUrl(url: string) {
  setState('idle')
  const res = await fetch('/api/taste', {
    method: 'POST',
    body: JSON.stringify({ url }),
  })
  const ing: Ingredients = await res.json()
  setIngredients(ing)
  setState('blending')
}
```

The `<Scene ingredients={...} state={...}>` interface is unchanged.

If Pattern B (3 services), the Barista calls Sommelier directly with a
`TasteRequest` and receives `Ingredients`. Same prop interface.

### Choreography (the demo beat)

```
0.00s  Run clicked
0.00s  Lid lifts (no-op on current GLB — single mesh, no separable cap)
0.35s  Ingredients arc one-by-one into the jar, shrinking as they pass the rim
1.40s  Swirl vortex spins up — particles colored from the actual ingredient palette
1.60s  Lid closes (no-op)
1.95s  Liquid begins filling the jar (shader-clipped fill line rising)
2.20s  Liquid color lerps from "average of dropped ingredients" → Sommelier's color.hex
2.60s  Swirl fades as fill catches up
3.40s  Done — liquid settled at full level, button shows "Run again"
```

Total `BLEND_DURATION_MS` lives in `App.tsx`.

---

## Stack

| Lib | Why |
|---|---|
| Vite + React + TypeScript | Fast HMR, typed contract |
| react-three-fiber, drei, postprocessing | Declarative 3D, prebuilt helpers, post chain |
| rapier | Reserved for future physics-based ingredient drop |
| leva | Runtime parameter tweaking |
| gsap | Choreographed timeline orchestration |
| tailwindcss v4 | UI chrome (header, preset picker, blend button, concept note) |

## Project structure

```
src/
  types/
    ingredients.ts           Mirror of context/DATA_CONTRACTS.md §5
    state.ts                 'idle' | 'blending' | 'done'
  data/
    mockIngredients.ts       4 presets spanning gold/gunk × smooth/chunky
  scene/
    Scene.tsx                Canvas + camera + lighting + composition root
    Blender.tsx              GLB loader, scale/center fit, lid choreography
    Ingredient.tsx           Generic GLB renderer with idle hover + spin
    IngredientFX.tsx         Spawns ingredients per Ingredients, drop animation
    SwirlVortex.tsx          Particle vortex during the mix moment
    JarLiquid.tsx            Tapered lathe + dome, shader-clipped fill animation
    liquidMaterial.ts        Custom GLSL: FBM displacement, fresnel, fillLevel discard
    assetRegistry.ts         Per-GLB scale/center metadata + averageColor for blend
  ui/
    ConceptNote.tsx          "How it works" overlay (collapsible)
    PresetPicker.tsx         Mock preset selector
    BlendButton.tsx          Run / Blending… / Run again
  util/
    colorBlend.ts            Weighted RGB average + hex lerp
  App.tsx                    State machine, Leva, layout
public/models/
  blender.glb                Hero asset (Poly by Google CC-BY)
  ingredients/*.glb          Per-ingredient assets
scripts/
  inspect-glb.mjs            Bbox dump (for re-fit when swapping models)
  inspect-tree.mjs           Node tree (for finding separable parts e.g. lid)
  inspect-primitives.mjs     Per-primitive bbox (for finding handle-vs-jar axis)
  inspect-ingredients.mjs    Bbox of every ingredient GLB → seed registry values
```

## Asset attributions

- **Blender** by [Poly by Google](https://poly.pizza/m/5on5mJSu0gT) — CC-BY 3.0
- **Strawberry / Banana / Cherry / Beetle / Fish** by [Poly by Google](https://poly.pizza)
  — CC-BY 3.0
- **Whipped Cream** by [Kenney](https://poly.pizza/m/mbMrdSG41d) — CC0

## Open work

- Source GLBs for `vanilla`, `matcha`, `chocolate`, `mint`, `lint_dust`, `burnt_marshmallow`
- Pull from [`context/poly_pizza_ingredients.json`](../context/poly_pizza_ingredients.json) — a
  shared 100-entry catalog of poly.pizza ingredient models (fruit, food, vegetable,
  dessert, candy). Wire by downloading each GLB into `public/models/ingredients/`,
  extending `assetRegistry.ts` with bbox + targetHeight, and adding the kind →
  asset mapping in `IngredientFX.tsx#KIND_TO_ASSET`.
- Texture-driven surface variation for `texture` field (smooth/chunky/sludge)
- Real screenshot preview pane (when Photographer is wired up)
- Blade spin animation (current GLB has no separable blade — workaround:
  motion-blur particles at the bottom of the jar during the swirl window)
- Outline post-pass for cel-shaded silhouettes (Bloom + ChromaticAberration are
  off right now; re-introduce after the rest of the scene is locked)
