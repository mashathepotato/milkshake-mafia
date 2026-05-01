# Role: Photographer (Visual Encoder)

## Mission
Turn a target URL into:
1) a high-fidelity screenshot (stable, comparable)
2) a high-dimensional embedding vector that captures “vibe”

The Photographer owns *ingestion and vectorization*. It does **not** decide “good vs bad”; it only produces artifacts.

## Owned outputs
- `ScreenshotArtifact`
- `EmbeddingArtifact`

See `context/DATA_CONTRACTS.md`.

## Responsibilities (what you implement)
### A) Deterministic capture
- Choose a headless browser runner (Playwright recommended for stability).
- Use a fixed viewport and a repeatable capture recipe:
  - consistent user agent (optional)
  - consistent wait strategy (`wait_until` + `wait_ms`)
  - optional `full_page` screenshots (useful for long pages, but increases variance)
- Record capture metadata (final url, status if available, warnings, errors).

### B) Preprocessing for embeddings
- Decide on a consistent image preprocessing pipeline for the chosen model:
  - resize/crop strategy (e.g., center crop or pad-to-square)
  - color space
  - normalization constants
- Document the model and preprocessing via `model_id`.

### C) Embedding generation
- Provide one embedding backend:
  - preferred: DINOv2 or CLIP via Python/torch
  - fallback: “cheap embedding” (e.g., histogram + layout heuristics) for demo resilience
- Ensure output vector length is consistent and declared as `embedding_dim`.
- Normalize embeddings (L2) unless there is a compelling reason not to (`normalized=true`).

### D) Baseline support
Baseline defines the Gold/Gunk poles.
- Provide a way to embed a small baseline set (e.g., a `baseline/` folder of images or URLs).
- Keep baseline small for hackathon (10–30 samples total is fine).

## Definition of Done (DoD)
- Given a URL, you can produce a `ScreenshotArtifact` and `EmbeddingArtifact` that pass contract validation:
  - has `request_id`, `url`, `model_id`, `embedding_dim`, `embedding[]`
  - `embedding_dim == len(embedding)`
  - outputs include useful metadata and errors are structured (not thrown as raw stack traces)
- Can run on at least 5 URLs reliably without manual intervention.

## Integration points
- Sommelier depends on:
  - embedding dimensionality being stable
  - `model_id` matching baseline items
  - L2 normalization consistency
- Barista does not consume Photographer outputs directly (only Ingredients), but screenshot can optionally be shown in the demo UI.

## Common pitfalls
- Full-page screenshots can introduce large variance (infinite scroll, animations).
- “networkidle” can hang on pages with long-polling; have a timeout and warning.
- Fonts/loading differences can shift embeddings; keep capture settings stable.

## What to communicate to the team
- chosen `model_id` and embedding dimension
- capture recipe defaults (viewport, wait conditions)
- where baseline inputs live and how to generate baseline embeddings

