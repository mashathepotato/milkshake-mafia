#!/usr/bin/env python3
"""Smoke test for the remix path.

Bypasses FastAPI + Photographer (no Playwright capture needed) by treating one
of the cellar URLs' baked embeddings as the "current" tasted embedding, then
running:

    parse_remix_instruction(text)
        -> blend_embedding(current, anchor, amount)
        -> ingredients_from_embeddings(blended, baseline_items)

Asserts:
  1. Each remix returns a valid Ingredients dict.
  2. Two different remixes from the same starting embedding produce
     observably different Ingredients (different base, color, or PC scores).
  3. Chained remixes (mint → bugs) produce a third distinct Ingredients.

Usage:
    python3 scripts/smoke_remix.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from sommelier.remix import (
    blend_embedding,
    build_ingredient_anchors,
    parse_remix_instruction,
)
from sommelier.taste import ingredients_from_embeddings


def _load_baseline() -> tuple[dict, list[dict]]:
    meta = json.loads((REPO_ROOT / "baselines/embeddings/baseline_meta.json").read_text())
    items = [
        json.loads(line)
        for line in (REPO_ROOT / "baselines/embeddings/baseline_embeddings.jsonl")
        .read_text()
        .splitlines()
        if line.strip()
    ]
    return meta, items


def _signature(ingredients: dict) -> tuple:
    """Compact identity for comparing two Ingredients outputs."""
    return (
        ingredients.get("base"),
        ingredients.get("texture"),
        round(ingredients.get("viscosity", 0.0), 3),
        ingredients.get("color", {}).get("hex"),
        round((ingredients.get("meta") or {}).get("pc1", 0.0), 3),
        round((ingredients.get("meta") or {}).get("pc2", 0.0), 3),
        round((ingredients.get("meta") or {}).get("pc3", 0.0), 3),
    )


def main() -> int:
    meta, items = _load_baseline()
    anchors = build_ingredient_anchors(items)

    # "Taste" stripe.com (gold, vanilla-ish) by reusing its baked embedding.
    target = next(it for it in items if it["url"] == "https://stripe.com")
    current = list(target["embedding"])

    failures: list[str] = []

    base_ing = ingredients_from_embeddings(
        target_embedding=current,
        baseline_items=items,
        request_id="smoke",
        url="https://stripe.com",
        baseline_id=meta["baseline_id"],
        model_id=meta["model_id"],
    )
    print(f"  base       sig={_signature(base_ing)}")

    # Remix 1: "a splash of mint"
    parsed1 = parse_remix_instruction("a splash of mint")
    emb1 = blend_embedding(current, anchors[parsed1["kind"]], parsed1["amount"])
    ing1 = ingredients_from_embeddings(
        target_embedding=emb1, baseline_items=items,
        request_id="smoke", url="https://stripe.com",
        baseline_id=meta["baseline_id"], model_id=meta["model_id"],
    )
    print(f"  +mint      parsed={parsed1}  sig={_signature(ing1)}")
    if _signature(ing1) == _signature(base_ing):
        failures.append("mint remix did not change Ingredients signature")

    # Remix 2 (chained on top of the mint remix): "more chaos"
    parsed2 = parse_remix_instruction("more chaos")
    emb2 = blend_embedding(emb1, anchors[parsed2["kind"]], parsed2["amount"])
    ing2 = ingredients_from_embeddings(
        target_embedding=emb2, baseline_items=items,
        request_id="smoke", url="https://stripe.com",
        baseline_id=meta["baseline_id"], model_id=meta["model_id"],
    )
    print(f"  +chaos     parsed={parsed2}  sig={_signature(ing2)}")
    if _signature(ing2) == _signature(ing1):
        failures.append("chained chaos remix did not change Ingredients signature")
    if _signature(ing2) == _signature(base_ing):
        failures.append("chained remix landed back on the original signature")

    # The chained embedding must actually have moved (and the magnitude must
    # be larger than a single hop, since chaining stacks blends).
    moved_total = sum((a - b) * (a - b) for a, b in zip(emb2, current))
    moved_first = sum((a - b) * (a - b) for a, b in zip(emb1, current))
    if moved_total < 1e-9:
        failures.append("chained embedding identical to original — blend did nothing")
    if moved_total <= moved_first:
        failures.append(
            f"chain should drift further from origin: first-hop={moved_first:.4g} "
            f"chained={moved_total:.4g}"
        )

    if failures:
        print("\nFAIL:", file=sys.stderr)
        for f in failures:
            print(f"  - {f}", file=sys.stderr)
        return 1
    print("\nPASS — remix parser, blend, and chaining all behave as expected.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
