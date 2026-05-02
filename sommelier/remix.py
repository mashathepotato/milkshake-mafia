"""Remix: blend an ingredient anchor into the current embedding.

Pipeline per /remix call:
    parse_remix_instruction("a splash of mint")  -> {kind: "mint", amount: 0.2}
    blend_embedding(current, anchors["mint"], 0.2) -> new_embedding
    sommelier.taste.ingredients_from_embeddings(new_embedding, ...) -> Ingredients

Anchors are computed once at startup from the cellar's flavor_profile keywords
(matched the same way as sommelier.ingredients.PROFILE_TO_BASE) so the remix
direction is grounded in the same baseline embeddings the Sommelier already uses.
"""
from __future__ import annotations

import re

from .linalg import l2_norm, mean

# VOCAB ingredients we accept (mirrors context/VOCAB.md).
# Legacy strings (tech_debt_chunks, bugs, sparkles, etc.) are kept here as
# acceptable INPUT vocabulary even though build_ingredients no longer emits
# them — users typing "add some sparkles" should still get a sensible blend.
GOOD_BASES = ("strawberry", "vanilla", "chocolate", "banana", "matcha")
BAD_BASES = ("fish", "expired_milk", "burnt_rubber")

POSITIVE_INCLUSIONS = (
    # Current fruit pool (build_ingredients emits these).
    "mango_cube", "raspberry", "kiwi_slice", "passionfruit",
    "strawberry_chunk", "blueberry", "cherry", "peach_slice",
    # Secondary kickers.
    "coconut_flake", "caramel_drizzle", "honey_drop",
    # Legacy positive inclusions (still accepted as input).
    "mint", "sparkles", "sprinkles",
)
NEGATIVE_INCLUSIONS = (
    # Current gunk pool.
    "mold", "fish_bone", "rotten_banana", "soggy_crouton",
    "eggshell", "stale_chip", "cold_pea", "wilted_lettuce",
    # Legacy negative inclusions (still accepted).
    "tech_debt_chunks", "bugs",
)
POSITIVE_TOPPINGS = ("whipped_cream", "honey_glaze", "fresh_cream_dollop")
NEGATIVE_TOPPINGS = ("lint_dust", "burnt_marshmallow", "mystery_sauce", "cigarette_ash")

ALL_INGREDIENTS = (
    GOOD_BASES + BAD_BASES
    + POSITIVE_INCLUSIONS + NEGATIVE_INCLUSIONS
    + POSITIVE_TOPPINGS + NEGATIVE_TOPPINGS
)

POSITIVE_INGREDIENTS = set(GOOD_BASES + POSITIVE_INCLUSIONS + POSITIVE_TOPPINGS)
NEGATIVE_INGREDIENTS = set(BAD_BASES + NEGATIVE_INCLUSIONS + NEGATIVE_TOPPINGS)

# flavor_profile keyword -> ingredient. Order matters: more specific first.
# Used to pull anchor URLs out of the cellar for each ingredient.
PROFILE_KEYWORDS = {
    "vanilla":           ("vanilla", "milk", "caramel"),
    "strawberry":        ("strawberry", "candy"),
    "chocolate":         ("chocolate", "espresso"),
    "matcha":            ("matcha", "mint"),
    "banana":            ("banana",),
    "fish":              ("fish", "deep sea"),
    "expired_milk":      ("expired", "curdled", "water"),
    "burnt_rubber":      ("burnt", "rusty", "iron"),
    # Inclusions / toppings reuse base-flavored anchors when their semantics overlap.
    # Most new vocab has no direct cellar keyword match; falls back to the
    # gold-mean (positive) or gunk-mean (negative) anchor automatically.
    "mint":              ("mint", "matcha"),
    "sparkles":          ("modern", "polish"),
    "sprinkles":         ("candy",),
    "whipped_cream":     ("vanilla", "milk", "caramel"),
    "honey_glaze":       ("vanilla", "caramel"),
    "fresh_cream_dollop":("vanilla", "milk"),
    # New fruit pool — anchors via the only fruit-adjacent keyword the cellar
    # has ('candy' for strawberry/sweet) or fall back to the gold mean.
    "strawberry_chunk":  ("strawberry", "candy"),
    "raspberry":         ("strawberry", "candy"),
    "blueberry":         ("strawberry", "candy"),
    "cherry":            ("strawberry", "candy"),
    "peach_slice":       ("vanilla", "candy"),
    "mango_cube":        ("candy", "modern"),
    "kiwi_slice":        ("matcha", "mint"),
    "passionfruit":      ("modern", "candy"),
    "coconut_flake":     ("vanilla", "milk"),
    "caramel_drizzle":   ("caramel", "vanilla"),
    "honey_drop":        ("vanilla",),
    # New gunk pool.
    "tech_debt_chunks":  ("legacy", "rusty", "iron"),
    "bugs":              ("chaos", "broken"),
    "mold":              ("expired", "curdled"),
    "fish_bone":         ("fish", "deep sea"),
    "rotten_banana":     ("expired", "curdled"),
    "soggy_crouton":     ("expired", "water"),
    "eggshell":          ("rusty", "iron"),
    "stale_chip":        ("expired", "curdled"),
    "cold_pea":          ("water", "deep sea"),
    "wilted_lettuce":    ("expired", "curdled"),
    "lint_dust":         ("expired", "rusty", "iron"),
    "burnt_marshmallow": ("burnt", "rusty"),
    "mystery_sauce":     ("curdled", "expired"),
    "cigarette_ash":     ("burnt", "rusty"),
}

# User-typed phrases that map to ingredients (looser than PROFILE_KEYWORDS,
# which is for cellar flavor_profile strings).
ALIAS_TO_INGREDIENT = {
    "creamy": "vanilla",
    "milky": "vanilla",
    "minty": "mint",
    "sparkly": "sparkles",
    "shiny": "sparkles",
    "candy": "strawberry",
    "berry": "strawberry",
    "fruity": "strawberry",
    "chocolatey": "chocolate",
    "cocoa": "chocolate",
    "espresso": "chocolate",
    "coffee": "chocolate",
    "green tea": "matcha",
    "matcha": "matcha",
    "fishy": "fish",
    "rotten": "expired_milk",
    "stale": "expired_milk",
    "expired": "expired_milk",
    "rubbery": "burnt_rubber",
    "burnt": "burnt_rubber",
    "rusty": "burnt_rubber",
    "chaos": "bugs",
    "chaotic": "bugs",
    "buggy": "bugs",
    "broken": "bugs",
    "messy": "bugs",
    "old": "tech_debt_chunks",
    "legacy": "tech_debt_chunks",
    "outdated": "tech_debt_chunks",
    "dated": "tech_debt_chunks",
    "premium": "whipped_cream",
    "fancy": "whipped_cream",
    "luxe": "whipped_cream",
    "honey": "honey_glaze",
    "dusty": "lint_dust",
    "grimy": "lint_dust",
    "harsh": "burnt_marshmallow",
    "overcooked": "burnt_marshmallow",
    # New fruit/gunk vocab aliases.
    "mango": "mango_cube",
    "raspberries": "raspberry",
    "kiwi": "kiwi_slice",
    "blueberries": "blueberry",
    "blueberry": "blueberry",
    "cherries": "cherry",
    "peach": "peach_slice",
    "peaches": "peach_slice",
    "passion": "passionfruit",
    "coconut": "coconut_flake",
    "caramel": "caramel_drizzle",
    "moldy": "mold",
    "moldy bread": "mold",
    "bone": "fish_bone",
    "bones": "fish_bone",
    "rotten banana": "rotten_banana",
    "soggy": "soggy_crouton",
    "crouton": "soggy_crouton",
    "eggshells": "eggshell",
    "shells": "eggshell",
    "chip": "stale_chip",
    "chips": "stale_chip",
    "pea": "cold_pea",
    "peas": "cold_pea",
    "lettuce": "wilted_lettuce",
    "wilted": "wilted_lettuce",
    "cigarette": "cigarette_ash",
    "ash": "cigarette_ash",
    "mystery": "mystery_sauce",
}

# Amount keyword -> blend factor (passed as the `amount` arg to blend_embedding).
AMOUNT_KEYWORDS = {
    "splash":   0.2,
    "touch":    0.2,
    "drop":     0.2,
    "tiny":     0.2,
    "little":   0.2,
    "hint":     0.2,
    "dash":     0.2,
    "some":     0.35,
    "bit":      0.35,
    "more":     0.55,
    "lot":      0.55,
    "extra":    0.55,
    "heavy":    0.55,
    "tons":     0.55,
}
DEFAULT_AMOUNT = 0.3


class RemixParseError(ValueError):
    """Raised when the user instruction can't be matched to a VOCAB ingredient."""


def build_ingredient_anchors(baseline_items: list[dict]) -> dict[str, list[float]]:
    """Compute one anchor embedding per VOCAB ingredient from the cellar.

    For each ingredient, pick cellar items whose ``flavor_profile`` matches a
    keyword in ``PROFILE_KEYWORDS[ingredient]`` and return their mean embedding.
    If no item matches, fall back to the mean of all gold (positive ingredients)
    or all gunk (negative ingredients) so the anchor still points in a sensible
    direction along the gold-gunk axis.
    """
    if not baseline_items:
        raise ValueError("build_ingredient_anchors() needs at least one baseline item")

    gold_embs = [item["embedding"] for item in baseline_items if item.get("label") == "gold"]
    gunk_embs = [item["embedding"] for item in baseline_items if item.get("label") == "gunk"]
    fallback_pos = mean(gold_embs) if gold_embs else mean([item["embedding"] for item in baseline_items])
    fallback_neg = mean(gunk_embs) if gunk_embs else fallback_pos

    anchors: dict[str, list[float]] = {}
    for ingredient in ALL_INGREDIENTS:
        keywords = PROFILE_KEYWORDS.get(ingredient, ())
        is_positive = ingredient in POSITIVE_INGREDIENTS
        # Only pull anchors from same-polarity (or wildcard wasabi) items so
        # 'milk' matching 'Organic Milk' (gold) doesn't also match 'Curdled
        # Milk' (gunk) and dilute the vanilla anchor toward the centroid.
        allowed_labels = {"gold", "wasabi"} if is_positive else {"gunk", "wasabi"}
        matches: list[list[float]] = []
        for item in baseline_items:
            if item.get("label") not in allowed_labels:
                continue
            profile = (item.get("flavor_profile") or "").lower()
            if any(kw in profile for kw in keywords):
                matches.append(item["embedding"])
        if matches:
            anchors[ingredient] = mean(matches)
        else:
            anchors[ingredient] = fallback_pos if is_positive else fallback_neg
    return anchors


def parse_remix_instruction(text: str) -> dict:
    """Parse free text into ``{kind, amount}``.

    Recognized ingredient names from VOCAB plus a small alias set
    (``ALIAS_TO_INGREDIENT``). Amount comes from keywords like 'splash' or
    'more'; defaults to 0.3 if no amount keyword is present.

    Raises RemixParseError if no ingredient is mentioned.
    """
    if not text or not text.strip():
        raise RemixParseError("instruction is empty")

    s = text.lower().strip()
    tokens = re.findall(r"[a-z_]+", s)
    token_set = set(tokens)

    # Amount: first matching keyword wins.
    amount = DEFAULT_AMOUNT
    for kw, value in AMOUNT_KEYWORDS.items():
        if kw in token_set:
            amount = value
            break

    # Ingredient: prefer literal vocab names (incl. with underscores like
    # 'tech_debt_chunks'), then aliases. Multi-word aliases match against the
    # full lowercased string; single-word against tokens.
    for ingredient in ALL_INGREDIENTS:
        if ingredient in s:
            return {"kind": ingredient, "amount": amount}

    for alias, ingredient in ALIAS_TO_INGREDIENT.items():
        if " " in alias:
            if alias in s:
                return {"kind": ingredient, "amount": amount}
        elif alias in token_set:
            return {"kind": ingredient, "amount": amount}

    raise RemixParseError(
        f"could not interpret {text!r} — try an ingredient like 'mint', 'vanilla', or 'chaos'"
    )


def blend_embedding(current: list[float], anchor: list[float], amount: float) -> list[float]:
    """Linearly interpolate ``current`` toward ``anchor`` by ``amount * 0.5``.

    The 0.5 cap keeps the website's grounding through chained remixes — a single
    remix can shift at most halfway toward the anchor.
    """
    if len(current) != len(anchor):
        raise ValueError(
            f"embedding dim mismatch: current={len(current)} anchor={len(anchor)}"
        )
    if l2_norm(anchor) < 1e-12:
        # Defensive: a zero anchor would just shrink the current vector.
        return list(current)
    t = max(0.0, min(1.0, float(amount))) * 0.5
    return [c * (1.0 - t) + a * t for c, a in zip(current, anchor)]
