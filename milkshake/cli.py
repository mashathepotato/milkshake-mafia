"""`python -m milkshake taste --url <URL>` — end-to-end orchestrator CLI."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .taste_url import ModelMismatchError, taste_url


def _cmd_taste(args: argparse.Namespace) -> int:
    embeddings_dir = Path(args.embeddings_dir) if args.embeddings_dir else None

    embedder = None
    if args.embedder:
        from photographer.embed import load_embedder
        embedder, warnings = load_embedder(prefer=args.embedder)
        for w in warnings:
            print(f"Warning: {w}", file=sys.stderr)

    try:
        ingredients = taste_url(
            args.url,
            embedder=embedder,
            embeddings_dir=embeddings_dir,
            pca_components=args.pca_components,
        )
    except FileNotFoundError as exc:
        print(
            f"Error: baseline embeddings not found ({exc}). "
            f"Run `python -m photographer baseline build` first.",
            file=sys.stderr,
        )
        return 2
    except ModelMismatchError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 3

    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(ingredients, indent=2, sort_keys=True) + "\n")
        print(f"Wrote {out}", file=sys.stderr)
    else:
        json.dump(ingredients, sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="milkshake",
        description="URL → Ingredients (Photographer + Sommelier orchestrator)",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_taste = sub.add_parser(
        "taste",
        help="Capture + embed a URL via Photographer, project via Sommelier, emit Ingredients JSON",
    )
    p_taste.add_argument("--url", required=True, help="Target URL")
    p_taste.add_argument("--out", dest="output", default=None, help="Write Ingredients JSON to file (default: stdout)")
    p_taste.add_argument(
        "--embedder",
        choices=["dinov2", "histogram"],
        default=None,
        help="Override embedder (default: auto-pick to match committed baseline model_id)",
    )
    p_taste.add_argument("--embeddings-dir", default=None, help="Override baselines/embeddings/ path")
    p_taste.add_argument("--pca-components", type=int, default=3)
    p_taste.set_defaults(func=_cmd_taste)

    args = parser.parse_args(argv)
    return int(args.func(args))
