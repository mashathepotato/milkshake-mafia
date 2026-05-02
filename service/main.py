"""FastAPI bridge for the Barista UI.

Endpoints:
    POST /taste         {url}             → {ingredients, screenshot}
    POST /taste/upload  multipart file    → {ingredients, screenshot}
    POST /remix         {request_id, instruction} → {ingredients, screenshot, parsed}
    GET  /health                          → {status: "ok"}

Loads embedder + baseline once at startup so each request only pays the
capture/embed cost (~5–30s with histogram-v0 + Playwright; ~1s for upload).
The /remix endpoint blends an ingredient anchor into a session's stored
embedding (no recapture) and re-projects through the same PCA, so chained
remixes drift the milkshake while preserving the original site's grounding.

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
from PIL import Image, ImageChops
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
from photographer.baseline import EMBEDDINGS_DIR, load_baseline  # noqa: E402
from photographer.embed import Embedder, load_embedder  # noqa: E402
from sommelier.ingredients import BASE_COLORS  # noqa: E402
from sommelier.remix import (  # noqa: E402
    RemixParseError,
    blend_embedding,
    build_ingredient_anchors,
    parse_remix_instruction,
)
from sommelier.taste import ingredients_from_embeddings  # noqa: E402

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


class RemixRequest(BaseModel):
    request_id: str = Field(..., min_length=1, description="ID from a prior /taste response")
    instruction: str = Field(..., min_length=1, description="e.g. 'add a splash of mint'")


_default_embedder: Embedder | None = None

# Cached at startup; reused by /taste, /taste/upload, and /remix.
_BASELINE_META: dict | None = None
_BASELINE_ITEMS: list[dict] | None = None
_ANCHORS: dict[str, list[float]] | None = None

# In-memory session store keyed by request_id. Each entry holds the *current*
# (possibly chained-remix) embedding for that session so the next /remix can
# build on it. TODO: evict — single-user demo for now.
_SESSIONS: dict[str, dict] = {}


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


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    h = hex_color.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def _tint_image(image: Image.Image, hex_color: str, strength: float = 0.45) -> Image.Image:
    """Multiply-blend a flat color over the image so the remix base is visible.

    Strength is the alpha applied to the tint layer; 0.45 is enough to read
    "mango" or "burnt rubber" at a glance without obliterating the source.
    """
    base = image.convert("RGB")
    tint = Image.new("RGB", base.size, _hex_to_rgb(hex_color))
    multiplied = ImageChops.multiply(base, tint)
    return Image.blend(base, multiplied, max(0.0, min(1.0, strength)))


def _store_session(
    request_id: str,
    embedding: list[float],
    *,
    url: str,
    screenshot: Optional[Image.Image] = None,
) -> None:
    """Persist a tasted embedding (and source screenshot) so /remix can build on it.

    No-op on empty embeddings. The screenshot is kept as a PIL image so /remix
    can re-emit a tinted thumbnail without recapturing the page.
    """
    if not embedding:
        return
    _SESSIONS[request_id] = {
        "embedding": embedding,
        "url": url,
        "request_id": request_id,
        "screenshot": screenshot.copy() if screenshot is not None else None,
    }


app = FastAPI(title="Milkshake Mafia — Taste Bridge", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    # Vite picks the next free port if 5173 is taken, so allow any localhost port.
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+",
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


@app.on_event("startup")
def _warm_caches() -> None:
    """Load embedder + baseline + ingredient anchor table once."""
    global _BASELINE_META, _BASELINE_ITEMS, _ANCHORS
    _get_embedder(None)
    _BASELINE_META, _BASELINE_ITEMS = load_baseline(EMBEDDINGS_DIR)
    _ANCHORS = build_ingredient_anchors(_BASELINE_ITEMS)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/taste")
def taste(req: TasteRequest) -> dict:
    try:
        embedder = _get_embedder(req.embedder)
        ingredients, screenshot, embedding = taste_url(
            req.url,
            embedder=embedder,
            return_screenshot=True,
            return_embedding=True,
        )
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

    _store_session(ingredients["request_id"], embedding, url=req.url, screenshot=screenshot)

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

    upload_url = f"upload://{file.filename or 'image'}"
    try:
        emb = _get_embedder(embedder)
        ingredients, embedding = taste_image(
            image, embedder=emb, url=upload_url, return_embedding=True
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ModelMismatchError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except Exception as exc:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"taste failed: {exc!r}") from exc

    _store_session(ingredients["request_id"], embedding, url=upload_url, screenshot=image)

    return {
        "ingredients": _trim_meta(ingredients),
        "screenshot": _thumbnail_data_url(image),
    }


@app.post("/remix")
def remix(req: RemixRequest) -> dict:
    if _BASELINE_ITEMS is None or _BASELINE_META is None or _ANCHORS is None:
        raise HTTPException(status_code=503, detail="service still warming up; retry shortly")

    session = _SESSIONS.get(req.request_id)
    if session is None:
        raise HTTPException(
            status_code=404,
            detail="session expired or unknown — taste a URL first",
        )

    try:
        parsed = parse_remix_instruction(req.instruction)
    except RemixParseError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    anchor = _ANCHORS.get(parsed["kind"])
    if anchor is None:
        # Parser only emits known VOCAB names; guard anyway in case the anchor
        # table got out of sync with the vocab.
        raise HTTPException(status_code=500, detail=f"no anchor for {parsed['kind']!r}")

    new_embedding = blend_embedding(session["embedding"], anchor, parsed["amount"])

    try:
        ingredients = ingredients_from_embeddings(
            target_embedding=new_embedding,
            baseline_items=_BASELINE_ITEMS,
            request_id=session["request_id"],
            url=session["url"],
            baseline_id=_BASELINE_META["baseline_id"],
            model_id=_BASELINE_META["model_id"],
        )
    except Exception as exc:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"remix failed: {exc!r}") from exc

    # Chain forward: next /remix call builds on this blended embedding.
    session["embedding"] = new_embedding

    # Re-emit the cached screenshot tinted by the new base color so the
    # reference panel updates in lockstep with the milkshake. Falls back to
    # the untinted source (or None) if the session predates screenshot caching.
    tinted: Optional[Image.Image] = None
    cached = session.get("screenshot")
    if cached is not None:
        base_hex, _accent = BASE_COLORS.get(ingredients.get("base", ""), ("#cccccc", "#ffffff"))
        tinted = _tint_image(cached, base_hex)

    return {
        "ingredients": _trim_meta(ingredients),
        "screenshot": _thumbnail_data_url(tinted) if tinted is not None else None,
        "parsed": parsed,
    }
