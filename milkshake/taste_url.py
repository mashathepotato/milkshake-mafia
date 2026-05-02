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


def _resolve_screenshot_image(screenshot: ScreenshotArtifact) -> Optional[Image.Image]:
    """Pull a PIL image out of a ScreenshotArtifact (base64 or path)."""
    if screenshot.png_base64:
        return Image.open(io.BytesIO(base64.b64decode(screenshot.png_base64))).convert("RGB")
    if screenshot.png_path:
        return Image.open(screenshot.png_path).convert("RGB")
    return None


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
):
    """Capture URL, embed, project into the cellar's PCA space.

    Returns canonical Ingredients dict per context/DATA_CONTRACTS.md §5.
    If ``return_screenshot=True``, returns a tuple ``(ingredients, image)``
    where ``image`` is a PIL.Image of the captured screenshot (or None on
    capture failure).

    On capture/embed failure, sommelier's short-circuit emits a fallback
    Ingredients (base="fish" or "expired_milk") rather than raising.
    """
    request_id = request_id or str(uuid.uuid4())[:8]
    viewport = viewport or Viewport()

    if embedder is None:
        embedder, _ = load_embedder(prefer="histogram")
    _check_model(embedder, embeddings_dir)

    req = CaptureRequest(request_id=request_id, url=url, viewport=viewport)
    screenshot, embedding = process(req, embedder=embedder)

    ingredients = _project(
        embedding=embedding,
        request_id=request_id,
        embeddings_dir=embeddings_dir,
        pca_components=pca_components,
    )
    if return_screenshot:
        return ingredients, _resolve_screenshot_image(screenshot)
    return ingredients


def taste_image(
    image: Image.Image,
    *,
    embedder: Optional[Embedder] = None,
    embeddings_dir: Optional[Path] = None,
    pca_components: int = 3,
    request_id: Optional[str] = None,
    url: str = "",
) -> dict:
    """Embed a pre-existing image (skips capture) and project via sommelier.

    Use for direct screenshot uploads — same downstream path as taste_url
    but without Playwright. Always returns just the Ingredients dict; the
    caller already has the image.
    """
    request_id = request_id or str(uuid.uuid4())[:8]

    if embedder is None:
        embedder, _ = load_embedder(prefer="histogram")
    _check_model(embedder, embeddings_dir)

    pil_image = image.convert("RGB")
    embedding = embed_image(
        image=pil_image,
        embedder=embedder,
        request_id=request_id,
        url=url or f"upload://{request_id}",
        source="upload",
    )

    return _project(
        embedding=embedding,
        request_id=request_id,
        embeddings_dir=embeddings_dir,
        pca_components=pca_components,
    )
