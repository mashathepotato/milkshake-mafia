"""URL/image → Ingredients in one call. Photographer + Sommelier glue."""
from __future__ import annotations

import base64
import io
import sys
import uuid
from pathlib import Path
from typing import Optional

from PIL import Image

# Allow running from a checkout without `pip install -e .`
_REPO_ROOT = Path(__file__).resolve().parent.parent
_SRC = _REPO_ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from photographer.baseline import EMBEDDINGS_DIR, load_baseline
from photographer.contracts import CaptureRequest, ScreenshotArtifact, Viewport
from photographer.embed import Embedder, embed_image, load_embedder
from photographer.pipeline import process
from sommelier.taste import ingredients_from_taste_request


class ModelMismatchError(RuntimeError):
    """Target embedding's model_id != baseline's model_id."""


# Map a baseline's recorded model_id to the load_embedder() preference key
# that produces the matching backend. Keep in sync with photographer.embed.
_MODEL_TO_PREFER = {
    "dinov2-base": "dinov2",
    "histogram-v0": "histogram",
}


def embedder_for_baseline(embeddings_dir: Optional[Path] = None) -> Embedder:
    """Load the embedder whose model_id matches the committed baseline.

    The baseline is the source of truth — once it's built, the only embedder
    that produces compatible target vectors is the one that built it. Callers
    should prefer this over choosing an embedder by hand.
    """
    embeddings_dir = embeddings_dir or EMBEDDINGS_DIR
    meta, _ = load_baseline(embeddings_dir)
    model_id = meta["model_id"]
    prefer = _MODEL_TO_PREFER.get(model_id)
    if prefer is None:
        raise ModelMismatchError(
            f"baseline model_id={model_id!r} has no known embedder mapping; "
            f"add it to milkshake.taste_url._MODEL_TO_PREFER"
        )
    embedder, warnings = load_embedder(prefer=prefer)
    if embedder.model_id != model_id:
        # load_embedder fell back (e.g., dinov2 unavailable → histogram). The
        # fallback is incompatible with the baseline; surface it loudly.
        raise ModelMismatchError(
            f"baseline expects model_id={model_id!r} but loaded embedder is "
            f"{embedder.model_id!r}; warnings: {warnings}"
        )
    return embedder


def _resolve_screenshot_image(screenshot: ScreenshotArtifact) -> Optional[Image.Image]:
    """Pull a PIL image out of a ScreenshotArtifact (base64 or path)."""
    if screenshot.png_base64:
        return Image.open(io.BytesIO(base64.b64decode(screenshot.png_base64))).convert("RGB")
    if screenshot.png_path:
        return Image.open(screenshot.png_path).convert("RGB")
    return None


def _embedding_vector(embedding) -> list[float]:
    """Extract the float list from an EmbeddingArtifact (empty on capture/embed error)."""
    return [float(x) for x in (embedding.embedding or [])]


def _project(
    *,
    embedding,
    request_id: str,
    embeddings_dir: Optional[Path],
    pca_components: int,
) -> dict:
    embeddings_dir = embeddings_dir or EMBEDDINGS_DIR
    baseline_meta, baseline_items = load_baseline(embeddings_dir)
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


def _check_model(embedder: Embedder, embeddings_dir: Optional[Path]) -> None:
    embeddings_dir = embeddings_dir or EMBEDDINGS_DIR
    baseline_meta, _ = load_baseline(embeddings_dir)
    if embedder.model_id != baseline_meta["model_id"]:
        raise ModelMismatchError(
            f"target embedder model_id={embedder.model_id!r} but "
            f"baseline model_id={baseline_meta['model_id']!r}; rebuild baseline "
            f"or pass a matching embedder"
        )


def taste_url(
    url: str,
    *,
    embedder: Optional[Embedder] = None,
    embeddings_dir: Optional[Path] = None,
    pca_components: int = 3,
    request_id: Optional[str] = None,
    viewport: Optional[Viewport] = None,
    return_screenshot: bool = False,
    return_embedding: bool = False,
):
    """Capture URL, embed, project into the cellar's PCA space.

    Returns canonical Ingredients dict per context/DATA_CONTRACTS.md §5.
    If ``return_screenshot=True``, the result includes a PIL.Image of the
    captured screenshot (or None on capture failure). If ``return_embedding``
    is true, it also includes the raw target embedding vector — useful for
    /remix-style downstream blending without recapturing the URL.

    The result is a tuple in the order ``(ingredients, image, embedding)``,
    omitting whichever optional pieces weren't requested. With both flags
    false, just the dict is returned.

    On capture/embed failure, sommelier's short-circuit emits a fallback
    Ingredients (base="fish" or "expired_milk") rather than raising.
    """
    request_id = request_id or str(uuid.uuid4())[:8]
    viewport = viewport or Viewport()

    if embedder is None:
        embedder = embedder_for_baseline(embeddings_dir)
    else:
        _check_model(embedder, embeddings_dir)

    req = CaptureRequest(request_id=request_id, url=url, viewport=viewport)
    screenshot, embedding = process(req, embedder=embedder)

    ingredients = _project(
        embedding=embedding,
        request_id=request_id,
        embeddings_dir=embeddings_dir,
        pca_components=pca_components,
    )
    extras: list = []
    if return_screenshot:
        extras.append(_resolve_screenshot_image(screenshot))
    if return_embedding:
        extras.append(_embedding_vector(embedding))
    if not extras:
        return ingredients
    return (ingredients, *extras)


def taste_image(
    image: Image.Image,
    *,
    embedder: Optional[Embedder] = None,
    embeddings_dir: Optional[Path] = None,
    pca_components: int = 3,
    request_id: Optional[str] = None,
    url: str = "",
    return_embedding: bool = False,
):
    """Embed a pre-existing image (skips capture) and project via sommelier.

    Use for direct screenshot uploads — same downstream path as taste_url
    but without Playwright. Returns the Ingredients dict by default, or
    ``(ingredients, embedding)`` when ``return_embedding=True`` so callers
    can chain a /remix without re-uploading.
    """
    request_id = request_id or str(uuid.uuid4())[:8]

    if embedder is None:
        embedder = embedder_for_baseline(embeddings_dir)
    else:
        _check_model(embedder, embeddings_dir)

    pil_image = image.convert("RGB")
    embedding = embed_image(
        image=pil_image,
        embedder=embedder,
        request_id=request_id,
        url=url or f"upload://{request_id}",
        source="upload",
    )

    ingredients = _project(
        embedding=embedding,
        request_id=request_id,
        embeddings_dir=embeddings_dir,
        pca_components=pca_components,
    )
    if return_embedding:
        return ingredients, _embedding_vector(embedding)
    return ingredients
