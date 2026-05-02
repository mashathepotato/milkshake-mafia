from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional, Protocol

import numpy as np
from PIL import Image

from .contracts import EmbeddingArtifact, EmbeddingInput, ErrorInfo


class Embedder(Protocol):
    model_id: str
    embedding_dim: int

    def embed(self, image: Image.Image) -> np.ndarray: ...


# ---------------------------------------------------------------------------
# Histogram fallback — no torch required
# ---------------------------------------------------------------------------

class HistogramEmbedder:
    model_id = "histogram-v0"
    embedding_dim = 66

    def embed(self, image: Image.Image) -> np.ndarray:
        img = image.convert("RGB").resize((64, 64))
        arr = np.array(img, dtype=np.float32)

        # 3 channels × 16 bins = 48
        hists: list[np.ndarray] = []
        for c in range(3):
            hist, _ = np.histogram(arr[:, :, c], bins=16, range=(0, 256))
            hists.append(hist.astype(np.float32))
        hist_feat = np.concatenate(hists)

        # Sobel edge density on 4×4 grid of 16×16 blocks = 16
        gray = np.mean(arr, axis=2)
        gx = np.gradient(gray, axis=1)
        gy = np.gradient(gray, axis=0)
        mag = np.sqrt(gx**2 + gy**2)
        edge_feat = np.array(
            [mag[r * 16:(r + 1) * 16, c * 16:(c + 1) * 16].mean()
             for r in range(4) for c in range(4)],
            dtype=np.float32,
        )

        # Mean luminance + std = 2
        lum_feat = np.array([gray.mean(), gray.std()], dtype=np.float32)

        vec = np.concatenate([hist_feat, edge_feat, lum_feat])
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec.astype(np.float32)


# ---------------------------------------------------------------------------
# DINOv2 primary embedder — requires torch + transformers
# ---------------------------------------------------------------------------

class DinoV2Embedder:
    model_id = "dinov2-base"
    embedding_dim = 768
    _HF_MODEL = "facebook/dinov2-base"

    def __init__(self) -> None:
        from transformers import AutoImageProcessor, AutoModel
        import torch

        self._processor = AutoImageProcessor.from_pretrained(self._HF_MODEL)
        self._model = AutoModel.from_pretrained(self._HF_MODEL)
        self._model.eval()

        if torch.cuda.is_available():
            self._device = "cuda"
        elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            self._device = "mps"
        else:
            self._device = "cpu"
        self._model = self._model.to(self._device)

    def embed(self, image: Image.Image) -> np.ndarray:
        import torch

        inputs = self._processor(images=image, return_tensors="pt")
        inputs = {k: v.to(self._device) for k, v in inputs.items()}

        with torch.no_grad():
            outputs = self._model(**inputs)

        # CLS token from last hidden state
        cls = outputs.last_hidden_state[:, 0].squeeze(0).cpu().numpy().astype(np.float32)
        norm = np.linalg.norm(cls)
        if norm > 0:
            cls = cls / norm
        return cls


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def load_embedder(prefer: str = "dinov2") -> tuple[Embedder, list[str]]:
    """Return (embedder, warnings). Falls back to histogram if torch/transformers unavailable."""
    warnings: list[str] = []
    if prefer == "dinov2":
        try:
            embedder = DinoV2Embedder()
            return embedder, warnings
        except Exception as exc:
            warnings.append(
                f"DINOv2 unavailable ({type(exc).__name__}: {exc}); falling back to histogram-v0"
            )
    return HistogramEmbedder(), warnings


# ---------------------------------------------------------------------------
# Embed a PIL image → EmbeddingArtifact
# ---------------------------------------------------------------------------

def embed_image(
    image: Image.Image,
    embedder: Embedder,
    request_id: str,
    url: str,
    source: str = "png_base64",
    extra_warnings: Optional[list[str]] = None,
) -> EmbeddingArtifact:
    warnings = list(extra_warnings or [])
    error: Optional[ErrorInfo] = None
    embedding: list[float] = []
    embedding_dim = embedder.embedding_dim

    try:
        vec = embedder.embed(image)
        embedding = vec.tolist()
        embedding_dim = len(embedding)
    except Exception as exc:
        error = ErrorInfo(type=type(exc).__name__, message=str(exc))
        embedding = [0.0] * embedding_dim

    return EmbeddingArtifact(
        request_id=request_id,
        url=url,
        model_id=embedder.model_id,
        embedding_dim=embedding_dim,
        embedding=embedding,
        normalized=True,
        computed_at=datetime.now(timezone.utc).isoformat(),
        input=EmbeddingInput(
            source=source,
            image_width=image.width,
            image_height=image.height,
        ),
        warnings=warnings,
        error=error,
    )
