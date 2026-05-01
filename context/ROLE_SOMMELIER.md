# Role: Sommelier (Logic & Mapping)

## Mission
Translate an embedding vector (“vibe”) into a concrete **Ingredients** object that the Barista can render.

Sommelier owns:
- relative scoring (Gold ↔ Gunk spectrum)
- PCA projection + normalization
- mapping PC axes into taste dimensions and discrete assets

Sommelier does **not**:
- capture screenshots
- compute embeddings (unless you explicitly build a combined service)
- render visuals

## Owned outputs
- `Ingredients`
- optional `SommelierDebug`

See `context/DATA_CONTRACTS.md`.

## Core algorithm (v0)
1) Validate input: target `EmbeddingArtifact` + baseline items all share:
   - same `model_id`
   - same `embedding_dim`
2) Build matrix `X` from baseline embeddings (+ optionally include target for centering stability).
3) Fit PCA with `n_components=3`.
4) Project target embedding → `pc1/pc2/pc3`.
5) Normalize PCs:
   - scale by baseline distribution (e.g., z-score) or min/max
   - clip to `[-1, 1]` for stability
6) Map PCs to taste attributes:
   - `PC1 (Order/Complexity)` → `viscosity` + `texture`
   - `PC2 (Harmony/Vibrancy)` → `base` + `color` + `sweetness/tartness`
   - `PC3 (Modernity/Debt)` → `freshness` + “aftertaste” notes/toppings

## Mapping spec (recommended, tweakable)
### PC1 → texture/viscosity (structure)
- High PC1 (order) → `texture="smooth"`, higher `viscosity`
- Low PC1 (chaos) → `texture="chunky"` or `"sludge"`, lower freshness, more “debt” inclusions

### PC2 → flavor profile + palette (harmony)
- High PC2 (pleasant harmony) → `base` in “good” set (strawberry/vanilla/matcha/banana)
- Low PC2 (discordant) → “bad” bases (fish/expired_milk/burnt_rubber)
- Use PC2 to drive main liquid `color.hex` and `accent_hex`

### PC3 → freshness/aftertaste (modernity/debt)
- High PC3 (modern) → higher `freshness`, sparkles/mint, cleaner toppings
- Low PC3 (debt) → “lint dust”, “tech_debt_chunks”, burnt toppings

## Definition of Done (DoD)
- Given `TasteRequest`, returns `Ingredients` that:
  - respects `[0,1]` bounds for scalar taste fields
  - includes `meta.pc1/pc2/pc3` in `[-1,1]`
  - includes `meta.confidence` and `baseline_id`
- Produces at least one **debug explanation** (notes or SommelierDebug) suitable for demo narration.
- Uses canonical enum strings from `context/VOCAB.md` (or updates it in coordination with Barista).

## Confidence (how to compute, simple v0)
Pick a simple confidence that helps demo credibility:
- inverse distance to nearest baseline neighbor
- or consistency of projection vs. baseline variance
- return as `meta.confidence` in `[0,1]`

## Integration points
- Photographer supplies embeddings + baseline embeddings (or baseline is a shared asset).
- Barista consumes Ingredients; coordinate with Barista on:
  - list of `base`, `texture`, `inclusions.kind`, `toppings.kind` (see `context/VOCAB.md`)
  - color expectations (hex) and animation triggers

## What to communicate to the team
- baseline format (where it lives; how to label gold vs gunk)
- mapping table for discrete assets (so Barista can render them)
- what “v0 is good enough” for demo stability
