# Sommelier (Python CLI)

Sommelier maps a screenshot **embedding vector** into a 3-axis "Taste Space" (PCA on a curated baseline) and emits the canonical `Ingredients` JSON described in [`context/DATA_CONTRACTS.md`](../context/DATA_CONTRACTS.md).

This package is **standard-library only** (no numpy/sklearn) so it can run in constrained hackathon environments.

## What's different from the original spec

The Sommelier originally specified hardcoded PC meanings (`PC1 = Order/Complexity`, etc.). This implementation discovers axis names from the data instead — see [`/Users/masha/.claude-max/plans/look-through-the-database-agile-oasis.md`](../../.claude-max/plans/look-through-the-database-agile-oasis.md) for the strategy memo.

- **Quality axis from labels:** PCA components are reordered so PC1 best aligns with the `gold` − `gunk` mean-difference vector (LDA-style).
- **Closed-vocab axis discovery:** for each PC, the items at the +/− extremes vote (via their `flavor_profile`/`why` text) for the best-matching axis name from a fixed vocabulary (`ordered/chaotic`, `airy/dense`, `modern/dated`, `polished/raw`, `playful/serious`, `bright/dark`). Result is deterministic and stable across runs.
- **Enum mapping by axis semantics:** the discovered axis name (not the PC ordinal) decides which taste field it drives — `ordered/chaotic` → viscosity, `airy/dense` → texture, etc.
- **Failure-mode short-circuit:** missing or zero-norm target embeddings short-circuit to `expired_milk` / `fish` with `confidence=0`.
- **Legacy recipe schema** is still available behind `--schema legacy`.

## Quick demo (no Photographer required)

```bash
# Canonical Ingredients (default)
python3 -m sommelier demo --url https://stripe.com

# Original recipe schema
python3 -m sommelier demo --url https://stripe.com --schema legacy
```

Wasabi anchors are included by default — they enrich the nearest-neighbor pool. Disable with `--no-wasabi`.

## Real input (Photographer integration)

```bash
python3 -m sommelier taste --in /path/to/taste_request.json
```

The `target_embedding.error.type` field is honored — set it to short-circuit to `fish` with `confidence=0`.

## Output (default Ingredients schema)

Strictly conforms to `Ingredients` from `context/DATA_CONTRACTS.md`, plus two `meta` extensions:

- `meta.discovered_axes[]` — closed-vocab axis names per PC, in PC order
- `meta.nearest_anchor` — `{url, label, flavor_profile}` of the closest baseline item

Notes are always two lines, fixed format:
```
"closest to {nearest.url} ({nearest.flavor_profile})"
"{axis_pos}/{axis_neg}: leaning {direction}"
```

## File layout

- `sommelier/pca.py` — PCA via Gram + power iteration (stdlib)
- `sommelier/taste.py` — projection, ordering, normalization, nearest anchor, confidence
- `sommelier/axes.py` — closed-vocab axis-name discovery from extremes
- `sommelier/ingredients.py` — `Ingredients` builder + failure-mode fallback
- `sommelier/dummy.py` — deterministic SHA256 dummy embeddings (offline demo)
- `sommelier/cli.py` — `demo` and `taste` subcommands

## Roadmap (deferred per plan)

- Real screenshot embeddings (Pix2Struct or CLIP ViT-L/14) once Photographer ships
- VLM call replacing the text-matching axis discovery (closed vocab kept; just better evidence)
- CLIP-text-encoder enum mapping for axis-to-VOCAB-string assignment
- Ambient corpus expansion, structural feature concat, three-class wasabi LDA, era axis (Wayback)
