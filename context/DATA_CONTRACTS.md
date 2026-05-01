# Data contracts (source of truth)

These JSON contracts define the integration boundaries between tiers. Implementations can be in any language, but must preserve:
- field names
- types
- semantics

If you need to change a contract, do it here first, then update all tiers.

## 1) CaptureRequest (Photographer input)
```json
{
  "request_id": "uuid-or-shortid",
  "url": "https://example.com",
  "viewport": { "width": 1440, "height": 900 },
  "full_page": true,
  "wait_until": "networkidle",
  "wait_ms": 500,
  "user_agent": "optional-string",
  "headers": { "optional": "http headers" }
}
```

**Notes**
- `wait_until` should be one of: `"load" | "domcontentloaded" | "networkidle"`.
- `wait_ms` is an additional delay after `wait_until`.

## 2) ScreenshotArtifact (Photographer output)
```json
{
  "request_id": "same-as-input",
  "url": "https://example.com",
  "captured_at": "2026-05-01T00:00:00Z",
  "viewport": { "width": 1440, "height": 900 },
  "full_page": true,
  "png_base64": "iVBORw0KGgoAAA... (preferred for small demos)",
  "png_path": "optional/path/on-disk.png",
  "http_status": 200,
  "final_url": "https://example.com",
  "warnings": ["optional strings"],
  "error": {
    "type": "optional error type",
    "message": "optional message"
  }
}
```

## 3) EmbeddingArtifact (Photographer output)
```json
{
  "request_id": "same-as-input",
  "url": "https://example.com",
  "model_id": "dinov2-base",
  "embedding_dim": 3,
  "embedding": [0.0123, -0.0456, 0.0000],
  "normalized": true,
  "computed_at": "2026-05-01T00:00:00Z",
  "input": {
    "source": "png_base64|png_path",
    "image_width": 1440,
    "image_height": 3000
  },
  "warnings": ["optional strings"],
  "error": { "type": "optional", "message": "optional" }
}
```

**Notes**
- `embedding` should be float-ish numbers; JSON means they’ll arrive as numbers.
- `embedding_dim` must equal `len(embedding)`.
- `normalized=true` means L2-normalized (recommended for PCA stability).
- Real embeddings are typically much larger (e.g., 512/768+ dims); examples are shortened for readability.

## 4) TasteRequest (Sommelier input)
```json
{
  "request_id": "same id",
  "target_embedding": {
    "request_id": "same id",
    "url": "https://example.com",
    "model_id": "dinov2-base",
    "embedding_dim": 3,
    "embedding": [0.0123, -0.0456, 0.0000],
    "normalized": true,
    "computed_at": "2026-05-01T00:00:00Z"
  },
  "baseline": {
    "baseline_id": "gold-gunk-v0",
    "model_id": "dinov2-base",
    "embedding_dim": 3,
    "normalized": true,
    "items": [
      { "label": "gold", "url": "https://gold.example", "embedding": [0.11, -0.22, 0.33] },
      { "label": "gunk", "url": "https://gunk.example", "embedding": [-0.44, 0.55, -0.66] }
    ]
  },
  "pca": { "n_components": 3 }
}
```

**Notes**
- `target_embedding.model_id` and `baseline.model_id` must match.
- `target_embedding.embedding_dim` and `baseline.embedding_dim` must match.
- `normalized` should match between target and baseline.

## 5) Ingredients (Sommelier output; Barista input)
```json
{
  "request_id": "same id",
  "url": "https://example.com",
  "version": "ingredients-v0",
  "base": "strawberry|vanilla|chocolate|banana|matcha|fish|expired_milk|...",
  "color": { "hex": "#ff4da6", "accent_hex": "#ffffff" },
  "texture": "smooth|airy|chunky|watery|sludge",
  "viscosity": 0.8,
  "tartness": 0.2,
  "sweetness": 0.7,
  "freshness": 0.9,
  "inclusions": [
    { "kind": "sprinkles|mint|sparkles|tech_debt_chunks|bugs", "amount": 0.3 }
  ],
  "toppings": [
    { "kind": "whipped_cream|lint_dust|burnt_marshmallow", "amount": 0.5 }
  ],
  "notes": ["Short strings usable in the demo UI"],
  "meta": {
    "pc1": 0.12,
    "pc2": -0.44,
    "pc3": 0.78,
    "confidence": 0.62,
    "baseline_id": "gold-gunk-v0",
    "model_id": "dinov2-base"
  }
}
```

**Rules**
- All scalar taste fields (`viscosity`, `tartness`, `sweetness`, `freshness`) are normalized to `[0, 1]`.
- `meta.pc1/pc2/pc3` are normalized to `[-1, 1]` after scaling/clipping.
- Barista must be able to render even if `notes` is empty.

## 6) SommelierDebug (optional)
```json
{
  "request_id": "same id",
  "pca": {
    "explained_variance_ratio": [0.4, 0.2, 0.1],
    "components_preview": [[0.01, -0.02], [0.03, 0.04], [0.05, -0.06]]
  },
  "neighbors": [
    { "url": "https://baseline.example", "label": "gold", "distance": 0.12 }
  ]
}
```
