import hashlib
import json
import math
import random
from pathlib import Path


def _l2_normalize(vec):
    norm = math.sqrt(sum(x * x for x in vec))
    if norm == 0:
        return vec[:]
    return [x / norm for x in vec]


def dummy_embedding_for_key(key: str, embedding_dim: int) -> list:
    """
    Deterministic, L2-normalized dummy embedding for offline demos.

    This is intentionally "fake", but stable across runs. It lets the Sommelier
    tier be developed before the Photographer tier is integrated.
    """
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
    seed = int(digest[:16], 16)
    rng = random.Random(seed)
    vec = [rng.uniform(-1.0, 1.0) for _ in range(int(embedding_dim))]
    return _l2_normalize(vec)


def load_cellar_urls(path: Path):
    payload = json.loads(path.read_text(encoding="utf-8"))
    items = payload.get("items", [])
    out = []
    for item in items:
        label = str(item.get("label", "")).strip().lower()
        url = str(item.get("url", "")).strip()
        if not label or not url:
            continue
        out.append({"label": label, "url": url})
    return out
