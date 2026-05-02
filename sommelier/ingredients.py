"""Build the canonical ``Ingredients`` JSON described in context/DATA_CONTRACTS.md.

Inputs are PC scores (already normalized to [-1, 1]), discovered axis names,
and the nearest baseline anchor. Output strictly uses VOCAB enums.
"""
from __future__ import annotations

from .linalg import clamp, clamp01

# VOCAB enums (kept here for offline use; mirrors context/VOCAB.md).
GOOD_BASES = ("strawberry", "vanilla", "chocolate", "banana", "matcha")
BAD_BASES = ("fish", "expired_milk", "burnt_rubber")

BASE_COLORS = {
    "strawberry":   ("#ff4da6", "#ffd1e8"),
    "vanilla":      ("#f3e5ab", "#fff8d6"),
    "chocolate":    ("#6b3f1d", "#a87148"),
    "banana":       ("#f7d36c", "#fff1b3"),
    "matcha":       ("#8fbf6a", "#cfe6b8"),
    "fish":         ("#4f7c8c", "#9bbac3"),
    "expired_milk": ("#d6d8c2", "#eef0e3"),
    "burnt_rubber": ("#2b2b2b", "#5e5e5e"),
}

# Snap a curated ``flavor_profile`` string to the closest VOCAB base.
# Order matters: more specific keywords come first.
PROFILE_TO_BASE = (
    ("matcha", "matcha"),
    ("mint", "matcha"),
    ("vanilla", "vanilla"),
    ("milk", "vanilla"),
    ("espresso", "chocolate"),
    ("chocolate", "chocolate"),
    ("caramel", "vanilla"),
    ("strawberry", "strawberry"),
    ("candy", "strawberry"),
    ("banana", "banana"),
    ("fish", "fish"),
    ("deep sea", "fish"),
    ("expired", "expired_milk"),
    ("curdled", "expired_milk"),
    ("rusty", "burnt_rubber"),
    ("burnt", "burnt_rubber"),
    ("iron", "burnt_rubber"),
    ("water", "expired_milk"),
)

# Discovered axis pole → (taste field it drives, on-pole value).
# When the target lands on this pole, apply that value (lerped from neutral by magnitude).
# Both poles of each axis appear here so we pick the right side directly.
AXIS_EFFECTS = {
    "ordered":  ("viscosity", 0.75),  # ordered  = thick, structured
    "chaotic":  ("viscosity", 0.30),
    "airy":     ("texture",   "airy"),
    "dense":    ("texture",   "chunky"),
    "modern":   ("freshness", 0.85),
    "dated":    ("freshness", 0.20),
    "polished": ("freshness", 0.75),
    "raw":      ("freshness", 0.30),
    "playful":  ("sweetness", 0.85),
    "serious":  ("sweetness", 0.30),
    "bright":   ("brightness", 1.0),
    "dark":     ("brightness", 0.0),
}


def _snap_base_from_profile(profile: str, *, good_side: bool) -> str:
    p = (profile or "").lower()
    for needle, base in PROFILE_TO_BASE:
        if needle in p:
            if good_side and base in GOOD_BASES:
                return base
            if not good_side and base in BAD_BASES:
                return base
    return "vanilla" if good_side else "expired_milk"


def _texture_from_quality(pc1: float) -> str:
    if pc1 >= 0.5:
        return "smooth"
    if pc1 >= 0.0:
        return "airy"
    if pc1 >= -0.5:
        return "watery"
    return "sludge"


def _direction_label(axis: dict, pc_value: float) -> str:
    return axis["positive"] if pc_value >= 0.0 else axis["negative"]


def _apply_axis_effect(axis: dict, pc_value: float, fields: dict) -> None:
    """Mutate `fields` by applying the discovered axis's on-pole effect.

    Looks up the pole the target landed on (positive if pc>=0, negative otherwise)
    and pulls the target field toward that pole's value, scaled by |pc|.
    """
    pole = axis["positive"] if pc_value >= 0.0 else axis["negative"]
    eff = AXIS_EFFECTS.get(pole)
    if not eff:
        return
    target, on_value = eff
    if isinstance(on_value, str):
        fields[target] = on_value
        return
    t = clamp01(abs(pc_value))  # 0 = neutral, 1 = fully on the pole
    fields[target] = clamp01(0.5 + (on_value - 0.5) * t)


def build_ingredients(
    *,
    request_id: str,
    url: str,
    pcs,
    axes,
    nearest_anchor: dict,
    confidence: float,
    baseline_id: str,
    model_id: str,
):
    """Compose the Ingredients dict per DATA_CONTRACTS.md.

    Parameters
    ----------
    pcs : list of float (length 3)
        Normalized PC scores in [-1, 1]. PC1 is the gold-vs-gunk axis.
    axes : list of dict (length 3)
        Discovered axis names per PC, each with ``positive``/``negative`` keys.
    nearest_anchor : dict
        Baseline item closest to the target (with ``url``, ``label``, optional
        ``flavor_profile``).
    """
    pc1 = pcs[0] if len(pcs) > 0 else 0.0
    pc2 = pcs[1] if len(pcs) > 1 else 0.0
    pc3 = pcs[2] if len(pcs) > 2 else 0.0

    # Trust the nearest-anchor label over PC1 sign when the anchor is unambiguously
    # gold or gunk: PC1 can land near the centroid (|pc1| ~ 0) for noisy embedders,
    # which would otherwise flip a clearly-gold target into the bad-base branch.
    nearest_label = (nearest_anchor or {}).get("label", "")
    if nearest_label == "gold":
        good_side = True
    elif nearest_label == "gunk":
        good_side = False
    else:
        good_side = pc1 >= 0.0

    nearest_profile = nearest_anchor.get("flavor_profile", "") if nearest_anchor else ""
    base = _snap_base_from_profile(nearest_profile, good_side=good_side)
    color_hex, accent_hex = BASE_COLORS.get(base, ("#cccccc", "#ffffff"))

    # Defaults — all VOCAB-canonical.
    fields = {
        "viscosity": 0.5,
        "sweetness": 0.6 if good_side else 0.3,
        "tartness":  0.4 if good_side else 0.6,
        "freshness": 0.6 if good_side else 0.3,
        "texture":   _texture_from_quality(pc1),
    }

    # Apply discovered axis effects in order; PC1 sets viscosity baseline, PC2/PC3 layer on top.
    for axis, pc in zip(axes, (pc1, pc2, pc3)):
        _apply_axis_effect(axis, pc, fields)

    # Inclusions/toppings — sign + quality + secondary PCs pick from a
    # food/fruit pool (no more code-puns like tech_debt_chunks). Selection is
    # deterministic in the PC scores so the same URL always gets the same
    # garnish; PC1 magnitude drives `amount`, PC2/PC3 quadrants pick the kind.
    #
    # Good side: PC3 (modern/dated) splits bright vs. classic fruits;
    #            PC2 (airy/dense) picks the second inclusion + topping.
    # Bad side:  PC1 magnitude splits "very gunk" (visceral) vs. mid-gunk
    #            (just stale); PC3 picks the topping flavor of failure.
    GOOD_PRIMARY_BRIGHT = ("mango_cube", "raspberry", "kiwi_slice", "passionfruit")
    GOOD_PRIMARY_CLASSIC = ("strawberry_chunk", "blueberry", "cherry", "peach_slice")
    GOOD_SECONDARY_PREMIUM = ("coconut_flake", "caramel_drizzle", "mint")
    GOOD_SECONDARY_SOFT = ("sprinkles", "honey_drop", "sparkles")
    GOOD_TOPPING = ("whipped_cream", "honey_glaze", "fresh_cream_dollop")
    BAD_PRIMARY_VISCERAL = ("mold", "fish_bone", "rotten_banana", "soggy_crouton")
    BAD_PRIMARY_STALE = ("eggshell", "stale_chip", "cold_pea", "wilted_lettuce")
    BAD_TOPPING = ("lint_dust", "burnt_marshmallow", "mystery_sauce", "cigarette_ash")

    def _pick(pool, key):
        """Deterministic pick from a tuple based on a [-1,1] PC score."""
        idx = int(((key + 1.0) / 2.0) * len(pool)) % len(pool)
        return pool[idx]

    inclusions = []
    toppings = []
    if good_side:
        primary_pool = GOOD_PRIMARY_BRIGHT if pc3 >= 0.0 else GOOD_PRIMARY_CLASSIC
        inclusions.append({
            "kind": _pick(primary_pool, pc2),
            "amount": round(0.3 + 0.5 * clamp01((pc1 + 1) / 2), 3),
        })
        if pc1 >= 0.5:
            secondary_pool = GOOD_SECONDARY_PREMIUM if pc3 >= 0.0 else GOOD_SECONDARY_SOFT
            inclusions.append({"kind": _pick(secondary_pool, pc1), "amount": 0.4})
        toppings.append({
            "kind": _pick(GOOD_TOPPING, pc2),
            "amount": round(0.3 + 0.6 * clamp01((pc1 + 1) / 2), 3),
        })
    else:
        primary_pool = BAD_PRIMARY_VISCERAL if pc1 < -0.5 else BAD_PRIMARY_STALE
        inclusions.append({
            "kind": _pick(primary_pool, pc2),
            "amount": round(0.3 + 0.5 * clamp01((-pc1 + 1) / 2), 3),
        })
        toppings.append({
            "kind": _pick(BAD_TOPPING, pc3),
            "amount": round(0.3 + 0.5 * clamp01((-pc1 + 1) / 2), 3),
        })

    # Notes — the demo line.
    notes = []
    if nearest_anchor:
        anchor_url = nearest_anchor.get("url", "")
        anchor_profile = nearest_anchor.get("flavor_profile", "")
        if anchor_profile:
            notes.append(f"closest to {anchor_url} ({anchor_profile})")
        else:
            notes.append(f"closest to {anchor_url}")
    if axes:
        primary_axis = axes[0]
        direction = _direction_label(primary_axis, pc1)
        notes.append(f"{primary_axis['positive']}/{primary_axis['negative']}: leaning {direction}")

    return {
        "request_id": request_id,
        "url": url,
        "version": "ingredients-v0",
        "base": base,
        "color": {"hex": color_hex, "accent_hex": accent_hex},
        "texture": fields["texture"],
        "viscosity": round(fields["viscosity"], 4),
        "tartness":  round(fields["tartness"],  4),
        "sweetness": round(fields["sweetness"], 4),
        "freshness": round(fields["freshness"], 4),
        "inclusions": inclusions,
        "toppings": toppings,
        "notes": notes,
        "meta": {
            "pc1": round(pc1, 4),
            "pc2": round(pc2, 4),
            "pc3": round(pc3, 4),
            "confidence": round(clamp01(confidence), 4),
            "baseline_id": baseline_id,
            "model_id": model_id,
            "discovered_axes": [
                {"positive": a["positive"], "negative": a["negative"]} for a in axes
            ],
            "nearest_anchor": {
                "url": nearest_anchor.get("url", "") if nearest_anchor else "",
                "label": nearest_anchor.get("label", "") if nearest_anchor else "",
                "flavor_profile": nearest_anchor.get("flavor_profile", "") if nearest_anchor else "",
            } if nearest_anchor else None,
        },
    }


def fallback_ingredients(*, request_id: str, url: str, baseline_id: str,
                         model_id: str, reason: str, kind: str = "expired_milk"):
    """Failure-mode short-circuit when target embedding is missing or zero-norm."""
    color_hex, accent_hex = BASE_COLORS.get(kind, ("#cccccc", "#ffffff"))
    return {
        "request_id": request_id,
        "url": url,
        "version": "ingredients-v0",
        "base": kind,
        "color": {"hex": color_hex, "accent_hex": accent_hex},
        "texture": "watery",
        "viscosity": 0.3,
        "tartness":  0.7,
        "sweetness": 0.1,
        "freshness": 0.0,
        "inclusions": [{"kind": "bugs", "amount": 0.6}],
        "toppings":   [{"kind": "lint_dust", "amount": 0.5}],
        "notes": [f"could not taste this URL ({reason})", "served as fallback fish/expired_milk"],
        "meta": {
            "pc1": 0.0, "pc2": 0.0, "pc3": 0.0,
            "confidence": 0.0,
            "baseline_id": baseline_id,
            "model_id": model_id,
            "discovered_axes": [],
            "nearest_anchor": None,
            "error": reason,
        },
    }
