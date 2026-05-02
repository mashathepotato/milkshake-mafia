#!/usr/bin/env python3
"""
Smoke test — runs process() on 5 preset URLs and validates both artifacts.

Usage:
    python scripts/smoke_test.py
    python scripts/smoke_test.py --embedder histogram
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

# Allow running from repo root without installing the package
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from photographer.contracts import CaptureRequest, EmbeddingArtifact, ScreenshotArtifact
from photographer.embed import load_embedder
from photographer.pipeline import process

URLS = [
    "https://stripe.com",
    "https://linear.app",
    "https://vercel.com",
    "https://news.ycombinator.com",
    "http://motherfuckingwebsite.com",
]


def validate(screenshot: ScreenshotArtifact, embedding: EmbeddingArtifact) -> list[str]:
    issues = []
    ScreenshotArtifact.model_validate(screenshot.model_dump())
    EmbeddingArtifact.model_validate(embedding.model_dump())
    if embedding.embedding_dim != len(embedding.embedding):
        issues.append(f"dim mismatch: {embedding.embedding_dim} vs {len(embedding.embedding)}")
    if not embedding.embedding:
        issues.append("empty embedding")
    return issues


def main() -> None:
    parser = argparse.ArgumentParser(description="Photographer smoke test")
    parser.add_argument("--embedder", choices=["dinov2", "histogram"], default="dinov2")
    parser.add_argument("--out", default="artifacts/smoke", help="Output directory for artifacts")
    args = parser.parse_args()

    prefer = "histogram" if args.embedder == "histogram" else "dinov2"
    embedder, embedder_warnings = load_embedder(prefer=prefer)
    print(f"Embedder: {embedder.model_id}  dim={embedder.embedding_dim}")
    for w in embedder_warnings:
        print(f"  Warning: {w}")
    print()

    results: list[tuple[str, str, float, list[str], list[str]]] = []

    for i, url in enumerate(URLS):
        req = CaptureRequest(request_id=f"smoke{i:03d}", url=url)
        t0 = time.time()
        try:
            screenshot, embedding = process(req, embedder=embedder, out_dir=Path(args.out))
            elapsed = time.time() - t0

            errors: list[str] = []
            if screenshot.error and screenshot.error.type:
                errors.append(f"capture error: {screenshot.error.type}")
            if embedding.error and embedding.error.type:
                errors.append(f"embed error: {embedding.error.type}")
            errors.extend(validate(screenshot, embedding))

            status = "PASS" if not errors else "WARN"
            notes = screenshot.warnings + embedding.warnings
            results.append((url, status, elapsed, errors, notes))
        except Exception as exc:
            elapsed = time.time() - t0
            results.append((url, "FAIL", elapsed, [str(exc)], []))

    # Print results table
    print(f"{'URL':<48} {'STATUS':<6} {'TIME':>6}  NOTES")
    print("-" * 82)
    passed = 0
    for url, status, elapsed, errors, warnings in results:
        short_url = url[:46] + ".." if len(url) > 48 else url
        notes = "; ".join(errors + [f"warn: {w}" for w in warnings])[:52]
        print(f"{short_url:<48} {status:<6} {elapsed:>5.1f}s  {notes}")
        if status == "PASS":
            passed += 1

    print()
    print(f"Result: {passed}/{len(results)} passed")
    sys.exit(0 if passed == len(results) else 1)


if __name__ == "__main__":
    main()
