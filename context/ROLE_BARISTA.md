# Role: Barista (Visualizer)

## Mission
Render the **Ingredients** JSON as an immediately understandable “milkshake” experience.

Barista owns:
- visuals, shaders, materials, particle systems
- animation choreography (pouring/blending on data arrival)
- UX that makes the output feel “testable and usable”

Barista does **not**:
- perform PCA
- embed images
- decide the score logic

## Owned input
- `Ingredients` (see `context/DATA_CONTRACTS.md`)

## Visual mapping (requirements)
Your renderer should support at minimum:
- `base` + `color.hex` driving liquid color (gradient encouraged)
- `viscosity` driving liquid thickness / flow speed
- `texture` switching between smooth vs chunky/noisy material
- `inclusions[]` and `toppings[]` spawning visible assets
- `freshness` affecting “shine”, opacity, bubbles, or afterglow

## UX requirements (demo-first)
- A single “Run” flow:
  1) user enters URL (or picks from a preset list)
  2) sees screenshot (optional but compelling)
  3) sees milkshake transform in real time
- Show 2–4 short `notes[]` from Sommelier as on-screen labels (for narration).
- Must degrade gracefully:
  - if inclusions/toppings are empty, still looks good
  - if `base` is unknown, render a neutral fallback

## Definition of Done (DoD)
- Given a valid `Ingredients` object:
  - renders a milkshake scene deterministically
  - animates transition on new data (even if simple)
  - stays performant for demo (no multi-second stalls)
- Can visually distinguish at least:
  - “good” (strawberry/vanilla) vs “bad” (fish/expired milk)
  - smooth vs sludge textures

## Integration points
- Coordinate with Sommelier on enumerations:
  - supported `base` values (see `context/VOCAB.md`)
  - supported `texture` values (see `context/VOCAB.md`)
  - supported `inclusions.kind` / `toppings.kind` (see `context/VOCAB.md`)
- Prefer data-driven assets: a mapping table in code, not hard-coded per URL.

## What to communicate to the team
- list of supported assets/keywords (so Sommelier can target them)
- any strict requirements (e.g., `color.hex` must be present)
