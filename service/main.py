"""FastAPI bridge for the Barista UI.

Endpoints:
    POST /taste         {url}             → {ingredients, screenshot}
    POST /taste/upload  multipart file    → {ingredients, screenshot}
    GET  /health                          → {status: "ok"}

Loads embedder + baseline once at startup so each request only pays the
capture/embed cost (~5–30s with histogram-v0 + Playwright; ~1s for upload).

Run:
    .venv/bin/uvicorn service.main:app --reload --port 8000
"""
from __future__ import annotations

import base64
import io
import sys
import traceback
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
from pydantic import BaseModel, Field

_REPO_ROOT = Path(__file__).resolve().parent.parent
for p in (_REPO_ROOT, _REPO_ROOT / "src"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from milkshake.taste_url import (  # noqa: E402
    ModelMismatchError,
    embedder_for_baseline,
    taste_image,
    taste_url,
)
from photographer.embed import Embedder, load_embedder  # noqa: E402

# Trim sommelier's richer meta down to what Barista's TS Ingredients type
# currently declares — same set the bake script uses.
META_KEEP = {"pc1", "pc2", "pc3", "confidence", "baseline_id", "model_id"}

# Thumbnail config — full-page screenshots can be 5000+ px tall; even at JPEG
# quality 75 the base64 stays under ~150 KB at this size.
THUMB_WIDTH = 480
THUMB_QUALITY = 75


class TasteRequest(BaseModel):
    url: str = Field(..., min_length=1, description="URL to taste")
    embedder: Optional[str] = Field(
        None,
        description="Override embedder choice ('histogram' or 'dinov2'); "
                    "defaults to whatever the service was started with.",
    )


_default_embedder: Embedder | None = None


def _get_embedder(name: Optional[str]) -> Embedder:
    global _default_embedder
    if name is None:
        if _default_embedder is None:
            _default_embedder = embedder_for_baseline()
        return _default_embedder
    embedder, _warnings = load_embedder(prefer=name)
    return embedder


def _trim_meta(ingredients: dict) -> dict:
    meta = ingredients.get("meta") or {}
    ingredients["meta"] = {k: v for k, v in meta.items() if k in META_KEEP}
    return ingredients


def _thumbnail_data_url(image: Optional[Image.Image]) -> Optional[str]:
    """Encode a PIL image as a base64 JPEG data URL (or return None)."""
    if image is None:
        return None
    img = image.convert("RGB")
    if img.width > THUMB_WIDTH:
        ratio = THUMB_WIDTH / img.width
        img = img.resize((THUMB_WIDTH, int(img.height * ratio)), Image.Resampling.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=THUMB_QUALITY, optimize=True)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


app = FastAPI(title="Milkshake Mafia — Taste Bridge", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    # Vite picks the next free port if 5173 is taken, so allow any localhost port.
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+",
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


@app.on_event("startup")
def _warm_embedder() -> None:
    _get_embedder(None)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/taste")
def taste(req: TasteRequest) -> dict:
    try:
        embedder = _get_embedder(req.embedder)
        ingredients, screenshot = taste_url(req.url, embedder=embedder, return_screenshot=True)
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "Baseline embeddings not found. Run "
                "`python -m photographer baseline build` first."
            ),
        ) from exc
    except ModelMismatchError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except Exception as exc:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"taste failed: {exc!r}") from exc

    return {
        "ingredients": _trim_meta(ingredients),
        "screenshot": _thumbnail_data_url(screenshot),
    }


@app.post("/taste/upload")
async def taste_upload(
    file: UploadFile = File(...),
    embedder: Optional[str] = Form(None),
) -> dict:
    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="empty upload")
    try:
        image = Image.open(io.BytesIO(contents))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"unreadable image: {exc!r}") from exc

    try:
        emb = _get_embedder(embedder)
        ingredients = taste_image(image, embedder=emb, url=f"upload://{file.filename or 'image'}")
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ModelMismatchError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except Exception as exc:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"taste failed: {exc!r}") from exc

    return {
        "ingredients": _trim_meta(ingredients),
        "screenshot": _thumbnail_data_url(image),
    }
