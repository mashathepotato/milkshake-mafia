from __future__ import annotations

import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .contracts import CaptureRequest, Viewport
from .embed import Embedder, load_embedder
from .pipeline import process

REPO_ROOT = Path(__file__).parent.parent.parent
CELLAR_PATH = REPO_ROOT / "baselines" / "cellar_urls_v0.json"
EMBEDDINGS_DIR = REPO_ROOT / "baselines" / "embeddings"


def build(
    baseline_id: Optional[str] = None,
    embedder: Optional[Embedder] = None,
    cellar_path: Optional[Path] = None,
    out_dir: Optional[Path] = None,
    viewport: Optional[Viewport] = None,
) -> dict:
    """
    Capture + embed every URL in the cellar; write to baselines/embeddings/.

    Output:
      <out_dir>/baseline_embeddings.jsonl  — one {label,url,flavor_profile,why,embedding} per line,
                                             drops into TasteRequest.baseline.items
      <out_dir>/baseline_meta.json         — baseline_id, model_id, dim, normalized, created_at,
                                             item_count, warnings, skipped

    The text fields (flavor_profile, why) come straight from the cellar JSON and
    are required by sommelier/axes.discover_axes() to name the discovered PCA axes.

    Items whose capture errors are skipped (logged in meta.skipped); they would
    otherwise inject zero-vectors into the PCA matrix and skew the poles.
    """
    cellar_path = cellar_path or CELLAR_PATH
    out_dir = out_dir or EMBEDDINGS_DIR
    viewport = viewport or Viewport()

    cellar = json.loads(cellar_path.read_text())
    baseline_id = baseline_id or cellar.get("baseline_id", "cellar-urls-v0")
    cellar_items: list[dict] = cellar.get("items", [])

    extra_warnings: list[str] = []
    if embedder is None:
        embedder, extra_warnings = load_embedder()

    out_dir.mkdir(parents=True, exist_ok=True)

    items: list[dict] = []
    skipped: list[dict] = []
    for entry in cellar_items:
        url = entry["url"]
        label = entry["label"]
        req = CaptureRequest(request_id=str(uuid.uuid4())[:8], url=url, viewport=viewport)
        print(f"  capturing {label:<7s} {url}", file=sys.stderr)
        try:
            _, embedding = process(req, embedder=embedder)
        except Exception as exc:
            skipped.append({"url": url, "label": label, "reason": f"exception: {exc!r}"})
            print(f"    SKIP — exception: {exc!r}", file=sys.stderr)
            continue
        if embedding.error and embedding.error.type:
            skipped.append({"url": url, "label": label, "reason": embedding.error.message or embedding.error.type})
            print(f"    SKIP — {embedding.error.type}: {embedding.error.message}", file=sys.stderr)
            continue
        items.append(
            {
                "label": label,
                "url": url,
                "flavor_profile": entry.get("flavor_profile", ""),
                "why": entry.get("why", ""),
                "embedding": embedding.embedding,
            }
        )

    jsonl_path = out_dir / "baseline_embeddings.jsonl"
    with open(jsonl_path, "w") as fh:
        for item in items:
            fh.write(json.dumps(item) + "\n")

    meta = {
        "baseline_id": baseline_id,
        "model_id": embedder.model_id,
        "embedding_dim": embedder.embedding_dim,
        "normalized": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "item_count": len(items),
        "skipped": skipped,
        "warnings": extra_warnings,
        "cellar_source": str(cellar_path.relative_to(REPO_ROOT)),
    }
    meta_path = out_dir / "baseline_meta.json"
    meta_path.write_text(json.dumps(meta, indent=2))

    print(
        f"\nBaseline '{baseline_id}': {len(items)} items "
        f"(skipped {len(skipped)}) | model={embedder.model_id} | dim={embedder.embedding_dim}",
        file=sys.stderr,
    )
    print(f"  -> {jsonl_path}", file=sys.stderr)
    print(f"  -> {meta_path}", file=sys.stderr)
    return meta


def load_baseline(out_dir: Optional[Path] = None) -> tuple[dict, list[dict]]:
    """Load baseline_meta.json and baseline_embeddings.jsonl. Returns (meta, items)."""
    out_dir = out_dir or EMBEDDINGS_DIR
    meta = json.loads((out_dir / "baseline_meta.json").read_text())
    items = [
        json.loads(line)
        for line in (out_dir / "baseline_embeddings.jsonl").read_text().splitlines()
        if line.strip()
    ]
    return meta, items
