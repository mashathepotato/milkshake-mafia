from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from PIL import Image

from .embed import Embedder, load_embedder

BASELINE_DIR = Path(__file__).parent.parent.parent / "baseline"


def build(
    baseline_id: str = "gold-gunk-v0",
    embedder: Optional[Embedder] = None,
    baseline_dir: Optional[Path] = None,
) -> dict:
    """
    Embed all PNGs in baseline/gold/ and baseline/gunk/, write:
      baseline/baseline_embeddings.jsonl  — one item per line, slots into TasteRequest.baseline.items
      baseline/baseline_meta.json         — baseline_id, model_id, dim, normalized, created_at

    Re-run whenever the embedder changes (model_id will differ → Sommelier rejects mismatches).
    """
    if baseline_dir is None:
        baseline_dir = BASELINE_DIR

    extra_warnings: list[str] = []
    if embedder is None:
        embedder, extra_warnings = load_embedder()

    items: list[dict] = []
    for label in ("gold", "gunk"):
        folder = baseline_dir / label
        if not folder.exists():
            print(f"Warning: {folder} not found — skipping label '{label}'")
            continue
        for png_path in sorted(folder.glob("*.png")):
            image = Image.open(png_path).convert("RGB")
            vec = embedder.embed(image)
            items.append(
                {
                    "label": label,
                    "url": f"file://{png_path.resolve()}",
                    "embedding": vec.tolist(),
                }
            )
            print(f"  embedded {label}/{png_path.name}")

    jsonl_path = baseline_dir / "baseline_embeddings.jsonl"
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
        "warnings": extra_warnings,
    }
    meta_path = baseline_dir / "baseline_meta.json"
    meta_path.write_text(json.dumps(meta, indent=2))

    print(
        f"\nBaseline '{baseline_id}': {len(items)} items | model={embedder.model_id} | dim={embedder.embedding_dim}"
    )
    print(f"  -> {jsonl_path}")
    print(f"  -> {meta_path}")
    return meta


def load_baseline(baseline_dir: Optional[Path] = None) -> tuple[dict, list[dict]]:
    """Load baseline_meta.json and baseline_embeddings.jsonl. Returns (meta, items)."""
    if baseline_dir is None:
        baseline_dir = BASELINE_DIR
    meta = json.loads((baseline_dir / "baseline_meta.json").read_text())
    items = [
        json.loads(line)
        for line in (baseline_dir / "baseline_embeddings.jsonl").read_text().splitlines()
        if line.strip()
    ]
    return meta, items
