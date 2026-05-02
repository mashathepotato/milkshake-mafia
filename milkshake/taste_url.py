"""URL → Ingredients in one call. Photographer + Sommelier glue."""
from __future__ import annotations

import sys
import uuid
from pathlib import Path
from typing import Optional

# Allow running from a checkout without `pip install -e .`
_REPO_ROOT = Path(__file__).resolve().parent.parent
_SRC = _REPO_ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from photographer.baseline import EMBEDDINGS_DIR, load_baseline
from photographer.contracts import CaptureRequest, Viewport
from photographer.embed import Embedder, load_embedder
from photographer.pipeline import process
from sommelier.taste import ingredients_from_taste_request


class ModelMismatchError(RuntimeError):
    """Target embedding's model_id != baseline's model_id."""


def taste_url(
    url: str,
    *,
    embedder: Optional[Embedder] = None,
    embeddings_dir: Optional[Path] = None,
    pca_components: int = 3,
    request_id: Optional[str] = None,
    viewport: Optional[Viewport] = None,
) -> dict:
    """Capture URL, embed, and project into the cellar's PCA space.

    Returns canonical Ingredients JSON per context/DATA_CONTRACTS.md §5.
    On capture/embed failure, sommelier's short-circuit emits a fallback
    Ingredients (base="fish" or "expired_milk") rather than raising.
    """
    embeddings_dir = embeddings_dir or EMBEDDINGS_DIR
    request_id = request_id or str(uuid.uuid4())[:8]
    viewport = viewport or Viewport()

    baseline_meta, baseline_items = load_baseline(embeddings_dir)

    if embedder is None:
        embedder, _ = load_embedder(prefer="histogram")

    if embedder.model_id != baseline_meta["model_id"]:
        raise ModelMismatchError(
            f"target embedder model_id={embedder.model_id!r} but "
            f"baseline model_id={baseline_meta['model_id']!r}; rebuild baseline "
            f"or pass a matching embedder"
        )

    req = CaptureRequest(request_id=request_id, url=url, viewport=viewport)
    _, embedding = process(req, embedder=embedder)

    payload = {
        "request_id": request_id,
        "target_embedding": embedding.model_dump(),
        "baseline": {
            "baseline_id": baseline_meta["baseline_id"],
            "model_id": baseline_meta["model_id"],
            "embedding_dim": baseline_meta["embedding_dim"],
            "normalized": baseline_meta.get("normalized", True),
            "items": baseline_items,
        },
        "pca": {"n_components": pca_components},
    }
    return ingredients_from_taste_request(payload)
