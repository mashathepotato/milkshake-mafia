<INSTRUCTIONS>
## Project: The Taste Engine (Hackathon 2026)
Build an autonomous “Taste Engine” that ranks the subjective quality of web UIs and visualizes it as a **Virtual Milkshake**.

### Core idea
- Convert a website screenshot (“vibe”) → embedding vector → PCA-derived axes → “ingredients” JSON → animated milkshake visualization.
- Ratings are **relative**, anchored by baseline examples of “Good (Senior)” vs “Bad (Gunk)”.

## 3-tier pipeline
### 1) Photographer (Visual Encoder)
- Input: target URL(s)
- Output: screenshot + high-dimensional embedding (e.g., CLIP / DINOv2)

### 2) Sommelier (Logic & Mapping)
- Runs PCA vs. baseline dataset
- Maps principal components:
  - `PC1` (Order/Complexity) → texture/viscosity
  - `PC2` (Harmony/Vibrancy) → flavor profile
  - `PC3` (Modernity/Debt) → freshness/aftertaste
- Output: Ingredients JSON, e.g.
  - `{ "base": "strawberry", "texture": "smooth", "inclusions": ["mint","sparkles"], "viscosity": 0.8 }`

### 3) Barista (Visualizer)
- Consumes Ingredients JSON (no scoring logic)
- Renders high-fidelity milkshake with shaders/assets/physics (pouring/blending, toppings, flow)

## KPIs
- Tangibility: make “design quality” feel testable/usable
- Relativity: always relative to the “Gold/Gunk” spectrum
- Presentation hook: real-time transformation from screenshot → visceral liquid representation

## Repo conventions (for now)
- Keep project/product context in `context/`
- Prefer small, composable modules per tier (Photographer/Sommelier/Barista)
- Default to simple, demo-first implementations; optimize later
</INSTRUCTIONS>
