# Agent prompts (copy/paste)

These are starter prompts teammates can use to configure their coding agents for a single tier. They assume the agent will read:
- `context/ARCHITECTURE.md`
- `context/DATA_CONTRACTS.md`
- the relevant `context/ROLE_*.md`

## Photographer agent prompt
You are implementing the **Photographer** tier for “The Taste Engine”.

Goal: for any URL, output a `ScreenshotArtifact` and `EmbeddingArtifact` that conform exactly to `context/DATA_CONTRACTS.md`.

Constraints:
- Do ingestion + vectorization only. Do not implement PCA mapping or visuals.
- Make capture deterministic (fixed viewport, stable wait strategy, clear timeouts).
- Choose one embedding backend (DINOv2/CLIP preferred) and one fallback backend; set `model_id` accordingly.
- L2-normalize embeddings and set `normalized=true`.

Deliverables:
- A runnable entrypoint (CLI or minimal service) that accepts `CaptureRequest` and prints/writes the two artifacts as JSON.
- A small baseline helper that can generate embeddings for a labeled Gold/Gunk set (keep it small and demo-friendly).
- Clear errors in `error.type`/`error.message` instead of crashing.

Definition of done:
- Works on 5+ URLs reliably.
- Produces stable `embedding_dim` and consistent `model_id`.

## Sommelier agent prompt
You are implementing the **Sommelier** tier for “The Taste Engine”.

Goal: take a `TasteRequest` (target embedding + baseline) and produce `Ingredients` (and optional `SommelierDebug`) per `context/DATA_CONTRACTS.md`.

Constraints:
- Do math + mapping only. Do not capture screenshots or render visuals.
- Use PCA with 3 components and normalize/clamp PC values to `[-1, 1]`.
- Map PCs to taste dimensions:
  - PC1 → `viscosity` + `texture`
  - PC2 → `base` + `color` + `sweetness/tartness`
  - PC3 → `freshness` + inclusions/toppings/notes
- Keep all scalar taste fields in `[0, 1]`.

Deliverables:
- A runnable entrypoint (CLI or minimal service) that consumes a `TasteRequest` JSON and outputs `Ingredients` JSON.
- A simple, demo-friendly `confidence` signal in `[0,1]` plus helpful `notes[]`.

Definition of done:
- Produces meaningfully different Ingredients for obvious Gold vs Gunk examples.
- Never emits invalid enums/strings outside `context/VOCAB.md` (or clearly documents additions).

## Barista agent prompt
You are implementing the **Barista** tier for “The Taste Engine”.

Goal: render the `Ingredients` JSON as a compelling “Virtual Milkshake” visualization in real time.

Constraints:
- Visuals only. No PCA/embedding logic.
- Must render something attractive even with minimal Ingredients (graceful fallback).
- Use Ingredients fields to drive:
  - liquid `color`
  - `viscosity` flow speed/thickness
  - `texture` material/noise
  - `inclusions` and `toppings` as visible assets/particles
  - `freshness` as shine/bubbles/afterglow

Deliverables:
- A runnable frontend that can accept Ingredients (mock JSON first, then wired to real pipeline later).
- A “new result” animation (pour/blend morph) when Ingredients updates.
- A small set of supported asset keywords documented (should match `context/VOCAB.md`).

Definition of done:
- Viewers can immediately tell “good shake” vs “bad shake”.
- Animation feels responsive during the demo.

