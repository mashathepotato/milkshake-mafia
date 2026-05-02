"""Unit tests for sommelier.remix — parser, blend, and anchor builder.

Pure stdlib; no pytest. Run as:

    python tests/test_remix.py
"""
from __future__ import annotations

import sys
from pathlib import Path

# Allow running from repo root without installing the package.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sommelier.linalg import l2_norm
from sommelier.remix import (
    ALL_INGREDIENTS,
    DEFAULT_AMOUNT,
    RemixParseError,
    blend_embedding,
    build_ingredient_anchors,
    parse_remix_instruction,
)


# ---- parser ----------------------------------------------------------------

def test_parser_literal_vocab():
    out = parse_remix_instruction("vanilla")
    assert out == {"kind": "vanilla", "amount": DEFAULT_AMOUNT}, out


def test_parser_amount_splash():
    out = parse_remix_instruction("a splash of mint")
    assert out == {"kind": "mint", "amount": 0.2}, out


def test_parser_amount_more():
    out = parse_remix_instruction("more chaos")
    assert out == {"kind": "bugs", "amount": 0.55}, out


def test_parser_amount_some():
    out = parse_remix_instruction("add some sparkles")
    assert out == {"kind": "sparkles", "amount": 0.35}, out


def test_parser_alias_creamy():
    out = parse_remix_instruction("make it creamy")
    assert out == {"kind": "vanilla", "amount": DEFAULT_AMOUNT}, out


def test_parser_alias_buggy():
    out = parse_remix_instruction("a touch of buggy")
    assert out == {"kind": "bugs", "amount": 0.2}, out


def test_parser_underscored_vocab():
    # tech_debt_chunks is the literal vocab name; ensure underscored matches work.
    out = parse_remix_instruction("more tech_debt_chunks")
    assert out == {"kind": "tech_debt_chunks", "amount": 0.55}, out


def test_parser_rejects_gibberish():
    try:
        parse_remix_instruction("xyzzy")
    except RemixParseError:
        return
    raise AssertionError("expected RemixParseError for 'xyzzy'")


def test_parser_rejects_empty():
    try:
        parse_remix_instruction("")
    except RemixParseError:
        return
    raise AssertionError("expected RemixParseError for empty string")


# ---- blend -----------------------------------------------------------------

def test_blend_zero_amount_unchanged():
    cur = [1.0, 2.0, 3.0]
    out = blend_embedding(cur, [9.0, 9.0, 9.0], 0.0)
    assert out == cur, out


def test_blend_full_amount_is_50_percent():
    cur = [0.0, 0.0, 0.0]
    anchor = [10.0, 10.0, 10.0]
    out = blend_embedding(cur, anchor, 1.0)
    # cap is 0.5, so out = 5.0 each.
    assert all(abs(x - 5.0) < 1e-9 for x in out), out


def test_blend_preserves_shape():
    cur = [1.0] * 66
    anchor = [2.0] * 66
    out = blend_embedding(cur, anchor, 0.5)
    assert len(out) == 66
    # amount=0.5 -> t=0.25 -> 1*0.75 + 2*0.25 = 1.25
    assert all(abs(x - 1.25) < 1e-9 for x in out), out[:3]


def test_blend_dim_mismatch_raises():
    try:
        blend_embedding([1.0, 2.0], [1.0, 2.0, 3.0], 0.5)
    except ValueError:
        return
    raise AssertionError("expected ValueError for dim mismatch")


def test_blend_zero_anchor_is_noop():
    cur = [1.0, 2.0, 3.0]
    out = blend_embedding(cur, [0.0, 0.0, 0.0], 0.5)
    assert out == cur, out


# ---- anchors ---------------------------------------------------------------

def _fake_cellar(dim: int = 8) -> list[dict]:
    """Tiny fake cellar that exercises every PROFILE_KEYWORDS bucket."""
    def vec(seed: float) -> list[float]:
        return [(seed + i) * 0.1 for i in range(dim)]

    return [
        # gold
        {"label": "gold", "url": "u1", "flavor_profile": "Premium Vanilla", "embedding": vec(1)},
        {"label": "gold", "url": "u2", "flavor_profile": "Cold Brew Espresso", "embedding": vec(2)},
        {"label": "gold", "url": "u3", "flavor_profile": "Organic Milk", "embedding": vec(3)},
        {"label": "gold", "url": "u4", "flavor_profile": "Artisanal Mint", "embedding": vec(4)},
        {"label": "gold", "url": "u5", "flavor_profile": "Salted Caramel", "embedding": vec(5)},
        # gunk
        {"label": "gunk", "url": "u6", "flavor_profile": "Deep Sea Shake", "embedding": vec(6)},
        {"label": "gunk", "url": "u7", "flavor_profile": "Sour Candy & Fish", "embedding": vec(7)},
        {"label": "gunk", "url": "u8", "flavor_profile": "Expired Water", "embedding": vec(8)},
        {"label": "gunk", "url": "u9", "flavor_profile": "Curdled Milk", "embedding": vec(9)},
        {"label": "gunk", "url": "u10", "flavor_profile": "Rusty Iron Shavings", "embedding": vec(10)},
        # wasabi
        {"label": "wasabi", "url": "u11", "flavor_profile": "Matcha Ginger", "embedding": vec(11)},
        {"label": "wasabi", "url": "u12", "flavor_profile": "Plain Tap Water", "embedding": vec(12)},
    ]


def test_anchors_cover_every_vocab_ingredient():
    cellar = _fake_cellar()
    anchors = build_ingredient_anchors(cellar)
    missing = [ing for ing in ALL_INGREDIENTS if ing not in anchors]
    assert not missing, f"missing anchors: {missing}"


def test_anchors_have_nonzero_norm():
    cellar = _fake_cellar()
    anchors = build_ingredient_anchors(cellar)
    for ingredient, vec in anchors.items():
        norm = l2_norm(vec)
        assert norm > 1e-9, f"{ingredient!r} anchor has zero norm"


def test_anchors_match_keywords():
    cellar = _fake_cellar()
    anchors = build_ingredient_anchors(cellar)
    # Vanilla should match u1 (Premium Vanilla), u3 (Organic Milk), u5 (Salted Caramel).
    # Mean of vec(1), vec(3), vec(5) = vec(3) componentwise.
    expected = [(3.0 + i) * 0.1 for i in range(8)]
    for got, exp in zip(anchors["vanilla"], expected):
        assert abs(got - exp) < 1e-9, (anchors["vanilla"], expected)


def test_anchors_fallback_for_unmatched():
    # Cellar with no 'sparkles' or 'bugs' matches; both should fall back.
    cellar = [
        {"label": "gold", "url": "g1", "flavor_profile": "vanilla", "embedding": [1.0, 1.0]},
        {"label": "gunk", "url": "k1", "flavor_profile": "fish",    "embedding": [9.0, 9.0]},
    ]
    anchors = build_ingredient_anchors(cellar)
    # 'sparkles' has no profile match -> positive fallback (gold mean).
    assert anchors["sparkles"] == [1.0, 1.0], anchors["sparkles"]
    # 'bugs' has no profile match -> negative fallback (gunk mean).
    assert anchors["bugs"] == [9.0, 9.0], anchors["bugs"]


# ---- runner ----------------------------------------------------------------

def main() -> int:
    tests = [v for k, v in globals().items() if k.startswith("test_") and callable(v)]
    failures: list[tuple[str, BaseException]] = []
    for fn in tests:
        try:
            fn()
            print(f"  PASS  {fn.__name__}")
        except BaseException as exc:
            failures.append((fn.__name__, exc))
            print(f"  FAIL  {fn.__name__}: {exc!r}")
    print()
    print(f"Result: {len(tests) - len(failures)}/{len(tests)} passed")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
