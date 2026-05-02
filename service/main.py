"""FastAPI bridge: POST /taste {url} → Ingredients JSON.

Loads embedder + baseline once at startup so each request only pays the
capture + embed cost (~5–30s with histogram-v0 + Playwright). The Barista
Vite dev server (default http://localhost:5173) is allowed via CORS.

Run:
    .venv/bin/uvicorn service.main:app --reload --port 8000
"""
from __future__ import annotations

import sys
import traceback
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

_REPO_ROOT = Path(__file__).resolve().parent.parent
for p in (_REPO_ROOT, _REPO_ROOT / "src"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from milkshake.taste_url import ModelMismatchError, taste_url  # noqa: E402
from photographer.embed import Embedder, load_embedder  # noqa: E402

# Trim sommelier's richer meta down to what Barista's TS Ingredients type
# currently declares — same set the bake script uses.
META_KEEP = {"pc1", "pc2", "pc3", "confidence", "baseline_id", "model_id"}


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
            _default_embedder, _ = load_embedder(prefer="histogram")
        return _default_embedder
    embedder, _warnings = load_embedder(prefer=name)
    return embedder


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
        ingredients = taste_url(req.url, embedder=embedder)
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

    meta = ingredients.get("meta") or {}
    ingredients["meta"] = {k: v for k, v in meta.items() if k in META_KEEP}
    return ingredients
