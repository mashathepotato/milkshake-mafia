from __future__ import annotations

import base64
import io
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from PIL import Image

from .contracts import CaptureRequest, EmbeddingArtifact, EmbeddingInput, ErrorInfo, ScreenshotArtifact
from .capture import capture
from .embed import Embedder, embed_image, load_embedder


def process(
    req: CaptureRequest,
    embedder: Optional[Embedder] = None,
    out_dir: Optional[Path] = None,
) -> tuple[ScreenshotArtifact, EmbeddingArtifact]:
    """
    Core seam: capture + embed → (ScreenshotArtifact, EmbeddingArtifact).
    Future FastAPI wrapper is a thin shim around this function.
    """
    extra_warnings: list[str] = []
    if embedder is None:
        embedder, extra_warnings = load_embedder()

    screenshot = capture(req, out_dir=out_dir)

    # Resolve image for embedding
    if screenshot.png_base64:
        img_bytes = base64.b64decode(screenshot.png_base64)
        image = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        source = "png_base64"
    elif screenshot.png_path:
        image = Image.open(screenshot.png_path).convert("RGB")
        source = "png_path"
    else:
        # Capture failed — return a zero-vector embedding with error
        embedding_artifact = EmbeddingArtifact(
            request_id=req.request_id,
            url=req.url,
            model_id=embedder.model_id,
            embedding_dim=embedder.embedding_dim,
            embedding=[0.0] * embedder.embedding_dim,
            normalized=True,
            computed_at=datetime.now(timezone.utc).isoformat(),
            input=EmbeddingInput(source="none", image_width=0, image_height=0),
            warnings=extra_warnings,
            error=ErrorInfo(
                type="no_image",
                message="Capture produced no image; embedding is a zero vector",
            ),
        )
        return screenshot, embedding_artifact

    embedding_artifact = embed_image(
        image=image,
        embedder=embedder,
        request_id=req.request_id,
        url=req.url,
        source=source,
        extra_warnings=extra_warnings,
    )

    # Write embedding JSON alongside PNG if out_dir given
    if out_dir is not None:
        import json
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / f"{req.request_id}.embedding.json").write_text(
            json.dumps(embedding_artifact.model_dump(), indent=2)
        )

    return screenshot, embedding_artifact
