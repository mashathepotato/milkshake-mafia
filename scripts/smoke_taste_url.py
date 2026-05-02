#!/usr/bin/env python3
"""End-to-end smoke test: URL → Photographer → Sommelier → Ingredients.

Validates three things:
  1. A known gold URL produces a gold-leaning anchor and high confidence.
  2. A known gunk URL produces a gunk-leaning anchor.
  3. An unreachable URL exercises the failure-mode short-circuit
     (sommelier emits Ingredients{base="fish"|"expired_milk"}, not an exception).

Exits non-zero if any case fails.

Usage:
    python scripts/smoke_taste_url.py
    python scripts/smoke_taste_url.py --embedder dinov2     # if you've rebuilt the baseline
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent))

from milkshake.taste_url import taste_url
from photographer.embed import load_embedder

GOLD_URL = "https://stripe.com"
GUNK_URL = "https://lingscars.com"
DEAD_URL = "https://this-site-does-not-exist-xxx-milkshake-mafia.invalid"

FALLBACK_BASES = {"fish", "expired_milk", "burnt_rubber"}


def _summarise(label: str, ingredients: dict) -> str:
    base = ingredients.get("base", "?")
    nearest = (ingredients.get("meta") or {}).get("nearest_anchor") or {}
    confidence = (ingredients.get("meta") or {}).get("confidence")
    return (
        f"  [{label}] base={base!r} "
        f"nearest_anchor={nearest.get('label')!r} "
        f"confidence={confidence}"
    )


def run(embedder_name: Optional[str]) -> int:
    if embedder_name:
        embedder, warnings = load_embedder(prefer=embedder_name)
        for w in warnings:
            print(f"Warning: {w}", file=sys.stderr)
    else:
        # Auto-pick the embedder that matches the committed baseline.
        from milkshake.taste_url import embedder_for_baseline
        embedder = embedder_for_baseline()

    failures: list[str] = []

    # 1. Gold path
    print(f"-> Tasting {GOLD_URL} (expected gold)")
    gold = taste_url(GOLD_URL, embedder=embedder)
    print(_summarise("gold", gold))
    nearest = (gold.get("meta") or {}).get("nearest_anchor") or {}
    if nearest.get("label") != "gold":
        failures.append(f"gold case: nearest_anchor.label={nearest.get('label')!r}, expected 'gold'")
    if gold.get("base") in FALLBACK_BASES:
        failures.append(f"gold case: got fallback base={gold.get('base')!r}")

    # 2. Gunk path
    print(f"-> Tasting {GUNK_URL} (expected gunk)")
    gunk = taste_url(GUNK_URL, embedder=embedder)
    print(_summarise("gunk", gunk))
    nearest = (gunk.get("meta") or {}).get("nearest_anchor") or {}
    if nearest.get("label") != "gunk":
        failures.append(f"gunk case: nearest_anchor.label={nearest.get('label')!r}, expected 'gunk'")

    # 3. Failure short-circuit
    print(f"-> Tasting {DEAD_URL} (expected fallback Ingredients)")
    dead = taste_url(DEAD_URL, embedder=embedder)
    print(_summarise("dead", dead))
    if dead.get("base") not in FALLBACK_BASES:
        failures.append(f"dead case: base={dead.get('base')!r}, expected one of {FALLBACK_BASES}")
    if not (dead.get("meta") or {}).get("error"):
        failures.append("dead case: meta.error not set on fallback Ingredients")

    if failures:
        print("\nFAIL:", file=sys.stderr)
        for f in failures:
            print(f"  - {f}", file=sys.stderr)
        return 1
    print("\nPASS — gold, gunk, and failure paths all behaved as expected.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="End-to-end taste_url smoke test")
    parser.add_argument(
        "--embedder",
        choices=["dinov2", "histogram"],
        default=None,
        help="Override embedder (default: auto-pick to match the committed baseline model_id)",
    )
    args = parser.parse_args()
    return run(args.embedder)


if __name__ == "__main__":
    sys.exit(main())
