import math

from .linalg import clamp, clamp01, dot, l2_normalize, mean, scale, sub
from .pca import PCAFit, fit_pca, max_abs_sign_fix, project


def _hex_to_rgb(hex_str: str):
    s = hex_str.strip().lstrip("#")
    if len(s) != 6:
        raise ValueError(f"Invalid hex color: {hex_str!r}")
    return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16))


def _rgb_to_hex(rgb):
    r, g, b = rgb
    r = int(clamp(r, 0, 255))
    g = int(clamp(g, 0, 255))
    b = int(clamp(b, 0, 255))
    return f"#{r:02x}{g:02x}{b:02x}"


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def _lerp_hex(a_hex: str, b_hex: str, t: float) -> str:
    t = clamp01(t)
    ar, ag, ab = _hex_to_rgb(a_hex)
    br, bg, bb = _hex_to_rgb(b_hex)
    return _rgb_to_hex(
        (
            round(_lerp(ar, br, t)),
            round(_lerp(ag, bg, t)),
            round(_lerp(ab, bb, t)),
        )
    )


def _safe_std(values, *, eps: float = 1e-12) -> float:
    if not values:
        return 1.0
    m = sum(values) / float(len(values))
    v = sum((x - m) * (x - m) for x in values) / float(len(values))
    s = math.sqrt(v)
    return s if s > eps else 1.0


def _normalize_pc(score: float, baseline_scores) -> float:
    m = sum(baseline_scores) / float(len(baseline_scores)) if baseline_scores else 0.0
    s = _safe_std(baseline_scores)
    z = (float(score) - m) / s
    z_clip = 3.0
    return clamp(z / z_clip, -1.0, 1.0)


def _pick_quality_order(pcs, eigenvalues, d_gold_gunk):
    """
    Reorder components so PC1 best aligns with gold-gunk separation.
    Remaining components keep descending eigenvalue order.
    """
    if not pcs:
        return pcs, eigenvalues

    d_unit = l2_normalize(d_gold_gunk)
    align = [abs(dot(pc, d_unit)) for pc in pcs]
    pc1_idx = max(range(len(pcs)), key=lambda i: align[i])

    remaining = [i for i in range(len(pcs)) if i != pc1_idx]
    remaining.sort(key=lambda i: eigenvalues[i] if i < len(eigenvalues) else 0.0, reverse=True)

    order = [pc1_idx] + remaining
    pcs2 = [pcs[i] for i in order]
    eig2 = [eigenvalues[i] for i in order] if eigenvalues else []
    return pcs2, eig2


def _orient_pc1(pcs, centered_baseline, labels):
    if not pcs:
        return pcs
    pc1 = pcs[0]
    gold_scores = []
    gunk_scores = []
    for x, label in zip(centered_baseline, labels):
        s = dot(x, pc1)
        if label == "gold":
            gold_scores.append(s)
        elif label == "gunk":
            gunk_scores.append(s)
    if gold_scores and gunk_scores:
        if (sum(gold_scores) / len(gold_scores)) < (sum(gunk_scores) / len(gunk_scores)):
            pcs = [scale(pc1, -1.0)] + pcs[1:]
    return pcs


def _cosine_sim(a, b) -> float:
    a = l2_normalize(a)
    b = l2_normalize(b)
    return clamp(dot(a, b), -1.0, 1.0)


def _recipe_from_scores(pc1: float, pc2: float, pc3: float, *, seniority: float, expiration: float):
    # Base flavor (quality axis, with small style-driven variation).
    if pc1 >= 0.0:
        base = "vanilla" if pc2 >= 0.0 else "strawberry"
    else:
        base = "fish" if pc2 < 0.0 else "vinegar"

    base_color = {
        "vanilla": "#f3e5ab",
        "strawberry": "#ff4da6",
        "fish": "#4fc3f7",
        "vinegar": "#c8e6c9",
    }[base]

    # Style axis controls thickness: minimalist -> thinner, dense -> more viscous.
    viscosity = 0.2 + 0.7 * ((1.0 - pc2) / 2.0)
    viscosity = clamp01(viscosity)

    # Age axis dulls the color; modern stays vibrant.
    stale = (1.0 - pc3) / 2.0  # 0 modern -> 1 legacy
    color_hex = _lerp_hex(base_color, "#7b7b7b", stale * 0.55)

    # Toppings & aftertaste bias by quality and age.
    if pc1 >= 0.0:
        toppings = ["whipped_cream", "sparkles" if pc3 >= 0.0 else "sprinkles"]
    else:
        toppings = ["lint_dust", "bugs" if pc3 >= 0.0 else "burnt_marshmallow"]

    if expiration >= 0.75 and "lint_dust" not in toppings:
        toppings[-1] = "lint_dust"

    if pc3 >= 0.5:
        aftertaste = "minty_sparkling"
    elif pc3 >= 0.0:
        aftertaste = "clean_finish"
    elif pc3 >= -0.5:
        aftertaste = "bitter_finish"
    else:
        aftertaste = "curdled_finish"

    primary_flavor = base

    return {
        "analysis": {
            "primary_flavor": primary_flavor,
            "seniority_score": round(float(seniority), 4),
            "expiration_risk": round(float(expiration), 4),
        },
        "milkshake_spec": {
            "base": base,
            "viscosity": round(float(viscosity), 4),
            "color_hex": color_hex,
            "toppings": toppings,
            "aftertaste": aftertaste,
        },
    }


def taste_from_embeddings(*, target_embedding, baseline_items, normalized: bool, pca_components: int = 3):
    if not baseline_items:
        raise ValueError("baseline_items is required")

    labels = []
    baseline_vectors = []
    for item in baseline_items:
        emb = item.get("embedding")
        if not isinstance(emb, list) or not emb:
            raise ValueError("Each baseline item must include a non-empty embedding[]")
        labels.append(str(item.get("label", "")).strip().lower())
        baseline_vectors.append([float(x) for x in emb])

    d = len(baseline_vectors[0])
    if len(target_embedding) != d:
        raise ValueError(f"Target embedding_dim={len(target_embedding)} does not match baseline embedding_dim={d}")

    gold_vecs = [v for v, lab in zip(baseline_vectors, labels) if lab == "gold"]
    gunk_vecs = [v for v, lab in zip(baseline_vectors, labels) if lab == "gunk"]
    if not gold_vecs or not gunk_vecs:
        raise ValueError("Baseline must include at least 1 gold and 1 gunk item")

    mu_gold = mean(gold_vecs)
    mu_gunk = mean(gunk_vecs)
    d_gold_gunk = sub(mu_gold, mu_gunk)

    pca = fit_pca(baseline_vectors, n_components=int(pca_components))
    pcs = [max_abs_sign_fix(pc) for pc in pca.components]
    pcs, eigenvalues = _pick_quality_order(pcs, pca.eigenvalues, d_gold_gunk)

    centered_baseline = [sub(v, pca.mean) for v in baseline_vectors]
    pcs = _orient_pc1(pcs, centered_baseline, labels)

    # Rebuild PCA fit with reordered/oriented components.
    pca = PCAFit(mean=pca.mean, components=pcs, eigenvalues=eigenvalues or pca.eigenvalues)

    baseline_scores = []
    for pc in pca.components:
        baseline_scores.append([dot(x, pc) for x in centered_baseline])

    raw_scores = project(pca, target_embedding)
    norm_scores = [
        _normalize_pc(s, baseline_scores[i]) if i < len(baseline_scores) else 0.0
        for i, s in enumerate(raw_scores)
    ]
    pc1 = norm_scores[0] if len(norm_scores) > 0 else 0.0
    pc2 = norm_scores[1] if len(norm_scores) > 1 else 0.0
    pc3 = norm_scores[2] if len(norm_scores) > 2 else 0.0

    # Pole distances expressed as [0,1] "closeness" scores for interpretability.
    if normalized:
        v = target_embedding
    else:
        v = l2_normalize(target_embedding)

    gold_sim = _cosine_sim(v, mu_gold)
    gunk_sim = _cosine_sim(v, mu_gunk)
    seniority = (1.0 + gold_sim) / 2.0
    expiration = (1.0 + gunk_sim) / 2.0

    return _recipe_from_scores(pc1, pc2, pc3, seniority=seniority, expiration=expiration)


def taste_from_taste_request(payload: dict):
    target = payload.get("target_embedding") or {}
    baseline = (payload.get("baseline") or {})

    target_embedding = target.get("embedding")
    if not isinstance(target_embedding, list) or not target_embedding:
        raise ValueError("TasteRequest.target_embedding.embedding[] is required")

    baseline_items = baseline.get("items")
    if not isinstance(baseline_items, list) or not baseline_items:
        raise ValueError("TasteRequest.baseline.items[] is required")

    normalized = bool(baseline.get("normalized", True) and target.get("normalized", True))
    return taste_from_embeddings(
        target_embedding=[float(x) for x in target_embedding],
        baseline_items=baseline_items,
        normalized=normalized,
        pca_components=int((payload.get("pca") or {}).get("n_components", 3)),
    )
