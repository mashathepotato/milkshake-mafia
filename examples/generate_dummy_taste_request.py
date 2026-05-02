import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sommelier.dummy import dummy_embedding_for_key, load_cellar_urls


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a dummy TasteRequest JSON for local testing.")
    parser.add_argument("--url", required=True, help="Target URL (used as dummy embedding key).")
    parser.add_argument("--out", required=True, help="Output path for TasteRequest JSON.")
    parser.add_argument(
        "--baseline-urls-file",
        default="baselines/cellar_urls_v0.json",
        help="Baseline URL list (gold/gunk/wasabi).",
    )
    parser.add_argument("--embedding-dim", type=int, default=64, help="Dummy embedding dimensionality.")
    parser.add_argument("--include-wasabi", action="store_true", help="Include wasabi in baseline items[].")
    args = parser.parse_args()

    cellar = load_cellar_urls(Path(args.baseline_urls_file))
    items = []
    for it in cellar:
        if it["label"] == "wasabi" and not args.include_wasabi:
            continue
        items.append(
            {
                "label": it["label"],
                "url": it["url"],
                "flavor_profile": it.get("flavor_profile", ""),
                "why": it.get("why", ""),
                "embedding": dummy_embedding_for_key(it["url"], embedding_dim=args.embedding_dim),
            }
        )

    request_id = "dummy-request"
    payload = {
        "request_id": request_id,
        "target_embedding": {
            "request_id": request_id,
            "url": args.url,
            "model_id": "dummy",
            "embedding_dim": args.embedding_dim,
            "embedding": dummy_embedding_for_key(args.url, embedding_dim=args.embedding_dim),
            "normalized": True,
            "computed_at": "2026-05-01T00:00:00Z",
        },
        "baseline": {
            "baseline_id": "dummy-baseline",
            "model_id": "dummy",
            "embedding_dim": args.embedding_dim,
            "normalized": True,
            "items": items,
        },
        "pca": {"n_components": 3},
    }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
