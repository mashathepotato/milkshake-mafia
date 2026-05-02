Embeddings baseline cache

This folder is reserved for Photographer-produced embedding artifacts keyed by URL.

Expected (v0) format:
- One JSON file per URL with at least:
  - `url`
  - `model_id`
  - `embedding_dim`
  - `embedding` (list[float])
  - `normalized` (bool)

Sommelier can load these to build `TasteRequest.baseline.items[]` without requiring
inline embeddings.

