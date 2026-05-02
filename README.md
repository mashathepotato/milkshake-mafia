# milkshake-mafia

<p align="center">
  <img src="gemini_milkshake_mafia.png" alt="Milkshake Mafia" width="800" />
</p>

## Photographer (visual encoder tier)

Turns a URL into a `ScreenshotArtifact` (PNG + metadata) and an `EmbeddingArtifact`
(L2-normalized vector + metadata) per `context/DATA_CONTRACTS.md`. Capture and
vectorization only — no scoring, PCA, or rendering.

### Embedders

| `model_id`       | Dim | Backend                                     | When used                     |
| ---------------- | --- | ------------------------------------------- | ----------------------------- |
| `dinov2-base`    | 768 | `facebook/dinov2-base` via `transformers`   | Default. Needs torch+torchvision+transformers. |
| `histogram-v0`   |  66 | numpy color histogram + Sobel edges + lum.  | Auto-fallback if DINOv2 import fails. |

The fallback is recorded as a warning on the artifact and as a `model_id` change
on the baseline meta — Sommelier rejects mismatches, so always rebuild the
baseline after switching backends.

### Capture defaults

| Setting       | Default                                      |
| ------------- | -------------------------------------------- |
| Viewport      | 1440×900                                     |
| `full_page`   | `true` (clipped to 6000 px tall, warned)     |
| `wait_until`  | `networkidle` (falls back to `domcontentloaded` on timeout, warned) |
| `wait_ms`     | 500                                          |
| User agent    | `Mozilla/5.0 (compatible; PhotographerBot/1.0)` |

### Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e .                 # core: playwright, pillow, numpy, pydantic
pip install -e '.[dinov2]'       # optional: torch, transformers (also needs torchvision)
playwright install chromium
```

### CLI

```bash
python -m photographer capture --url https://stripe.com --out artifacts/
python -m photographer embed   --image artifacts/<id>.png
python -m photographer run     --url https://stripe.com --out artifacts/
python -m photographer baseline build      # → baseline/baseline_embeddings.jsonl + meta
```

`run` writes `<request_id>.png`, `<request_id>.screenshot.json`, and
`<request_id>.embedding.json` to `--out`.

### Baseline (Gold vs Gunk)

PNGs live in `baseline/gold/` and `baseline/gunk/`. `baseline build` embeds them
all with the active embedder and writes:

- `baseline/baseline_embeddings.jsonl` — one `{label,url,embedding}` per line,
  drops straight into `TasteRequest.baseline.items`.
- `baseline/baseline_meta.json` — `baseline_id`, `model_id`, `embedding_dim`,
  `normalized`, `created_at`, item count.

Rebuild whenever the embedder changes; Sommelier compares `model_id` and
`embedding_dim` on both sides.

### Smoke test

```bash
python scripts/smoke_test.py                    # default: dinov2
python scripts/smoke_test.py --embedder histogram
```

Runs `process()` on five preset URLs, validates both artifacts, prints a
PASS/WARN/FAIL table. Exits non-zero if anything below PASS.

### Failure modes (surfaced, not raised)

| Symptom                       | How it shows up                                          |
| ----------------------------- | -------------------------------------------------------- |
| `networkidle` hangs           | Warning + fallback to `domcontentloaded`                 |
| Navigation timeout still      | `error.type="timeout"`, no PNG, embedding zero-vector    |
| DNS / `net::ERR_*`            | `error.type="dns_error"`                                 |
| Page taller than 6000 px      | Image clipped, warning recorded                          |
| DINOv2 weights/torch missing  | Warning + automatic histogram fallback                   |

### Licensing notes

DINOv2 (`facebook/dinov2-base`) is released under Apache-2.0 — fine for
commercial use. The `histogram-v0` fallback is pure numpy, no model license.
The plan originally proposed DINOv3 (non-commercial); we chose DINOv2 to match
`DATA_CONTRACTS.md` and avoid that constraint. Swapping to CLIP or DINOv3 is a
new `Embedder` class in `src/photographer/embed.py` and a `load_embedder` arm.

