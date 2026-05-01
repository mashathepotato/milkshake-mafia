import argparse
import json
import sys
from pathlib import Path

from .dummy import dummy_embedding_for_key, load_cellar_urls
from .taste import taste_from_embeddings, taste_from_taste_request


def _read_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, sort_keys=True)
        f.write("\n")


def _cmd_demo(args: argparse.Namespace) -> int:
    baseline_items = []
    for item in load_cellar_urls(Path(args.baseline_urls_file)):
        if item["label"] == "wasabi" and not args.include_wasabi:
            continue
        baseline_items.append(
            {
                "label": item["label"],
                "url": item["url"],
                "embedding": dummy_embedding_for_key(item["url"], embedding_dim=args.embedding_dim),
            }
        )

    target_embedding = dummy_embedding_for_key(args.url, embedding_dim=args.embedding_dim)
    recipe = taste_from_embeddings(
        target_embedding=target_embedding,
        baseline_items=baseline_items,
        normalized=True,
        pca_components=3,
    )
    json.dump(recipe, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


def _cmd_taste(args: argparse.Namespace) -> int:
    payload = _read_json(Path(args.input))
    recipe = taste_from_taste_request(payload)
    if args.output:
        _write_json(Path(args.output), recipe)
    else:
        json.dump(recipe, sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="sommelier", description="Embedding -> Taste Space -> Barista recipe JSON")
    sub = parser.add_subparsers(dest="cmd", required=True)

    demo = sub.add_parser("demo", help="Run with deterministic dummy embeddings (no Photographer required).")
    demo.add_argument("--url", required=True, help="Target URL (used as dummy embedding key).")
    demo.add_argument(
        "--baseline-urls-file",
        default="baselines/cellar_urls_v0.json",
        help="JSON file with labeled baseline URLs (gold/gunk/wasabi).",
    )
    demo.add_argument("--embedding-dim", type=int, default=768, help="Dummy embedding dimensionality.")
    demo.add_argument("--include-wasabi", action="store_true", help="Include wasabi items in PCA baseline.")
    demo.set_defaults(func=_cmd_demo)

    taste = sub.add_parser("taste", help="Run on a TasteRequest JSON (embedding + baseline embeddings).")
    taste.add_argument("--in", dest="input", required=True, help="Path to TasteRequest JSON.")
    taste.add_argument("--out", dest="output", default=None, help="Write output JSON to a file (default: stdout).")
    taste.set_defaults(func=_cmd_taste)

    args = parser.parse_args(argv)
    return int(args.func(args))
