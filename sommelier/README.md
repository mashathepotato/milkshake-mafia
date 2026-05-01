# Sommelier (Python CLI)

Sommelier maps a screenshot **embedding vector** into a 3-axis "Taste Space" (via PCA on a reference baseline) and emits a compact Barista-facing recipe JSON.

This package is **standard-library only** (no numpy/sklearn), so it can run in constrained hackathon environments.

## Quick demo (no Photographer required)
Runs PCA on the curated URL "cellar" and uses **deterministic dummy embeddings** derived from URL strings:

```bash
python3 -m sommelier demo --url https://example.com
```

Baseline URL list lives at `baselines/cellar_urls_v0.json`.

## Real input (Photographer integration)
When Photographer is wired up, pass a `TasteRequest` JSON that includes:
- `target_embedding.embedding[]`
- `baseline.items[].embedding[]` with `label` (`gold`/`gunk`)

```bash
python3 -m sommelier taste --in /path/to/taste_request.json
```

## Output format (current)
Sommelier currently outputs the simplified Barista recipe schema discussed in the Sommelier brief:

```json
{
  "analysis": {
    "primary_flavor": "string",
    "seniority_score": 0.0,
    "expiration_risk": 0.0
  },
  "milkshake_spec": {
    "base": "string",
    "viscosity": 0.0,
    "color_hex": "string",
    "toppings": ["string"],
    "aftertaste": "string"
  }
}
```

When we merge with Barista + align contracts, we can additionally emit `context/DATA_CONTRACTS.md` `Ingredients` without changing the projection core.
