# milkshake-mafia

<p align="center">
  <img src="gemini_milkshake_mafia.png" alt="Milkshake Mafia" width="800" />
</p>

The Taste Engine: a 3-tier pipeline that turns a URL into a virtual milkshake.

```
URL → Photographer → screenshot + embedding → Sommelier → Ingredients → Barista → 🥤
```

This branch (`sommelier`) carries:

- **Sommelier** (`sommelier/`): pure-stdlib Python. PCA on the curated cellar, closed-vocab axis discovery, `Ingredients` JSON per `context/DATA_CONTRACTS.md §5`. See [`sommelier/README.md`](sommelier/README.md).
- **Barista** (`barista/`): React-Three-Fiber milkshake renderer. Consumes `Ingredients`. See [`barista/README.md`](barista/README.md).
- **Cellar** (`baselines/cellar_urls_v0.json`): 12 curated reference URLs (Gold / Gunk / Wasabi).
- **Bake bridge** (`scripts/bake_barista_presets.py`): runs Sommelier on every cellar URL and writes typed presets to `barista/src/data/sommelierPresets.ts` so the Barista preset picker shows real Sommelier output alongside its mocks.

## Run end-to-end (offline, dummy embeddings)

```bash
# 1) Bake real Sommelier output for the cellar URLs
python3 scripts/bake_barista_presets.py

# 2) Start Barista
cd barista
npm install
npm run dev          # http://localhost:5173
```

The bottom-left preset picker now lists the 4 hand-crafted mocks + 12 baked Sommelier presets (e.g. `gold-stripe-com`, `gunk-arngren-net`, `wasabi-yahoo-co-jp`). Each is the actual `Ingredients` shape Sommelier would emit; switching presets renders a different milkshake.

`npm run bake` is wired in `barista/package.json` as a shortcut to step 1.

## When Photographer ships

The `bake` step takes a deterministic dummy embedding for each URL (`hashlib.sha256` → random vector). Once Photographer ships real Pix2Struct/CLIP embeddings, swap `dummy_embedding_for_key` in the bake script for the real embedder and re-run — the rest of the pipeline (axis discovery → Ingredients → Barista) is already wired.

For the live "type a URL → see a shake" flow, point Barista at a small HTTP service that wraps `sommelier.taste.ingredients_from_taste_request`. The `<Scene ingredients={...} state={...}>` interface is the integration boundary; nothing in `barista/src/scene/` needs to change.

## Other branches

- `photographer` — capture + embedding tier (Playwright + DINOv2/CLIP backend)
- `barista/scaffold` — original Barista scaffold (merged here)
- `main` — context docs only
