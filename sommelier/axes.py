"""Discover axis names from baseline extremes using a closed vocabulary.

The "axes" of the Sommelier's taste space are PCA components ordered/oriented so
PC1 aligns with the gold-vs-gunk discriminant. The Plan calls for the *meaning*
of each axis to be discovered from the data rather than asserted by spec — a
constrained vocabulary keeps that discovery stable and demo-friendly.

For v0 (no Photographer / no real screenshots), we let the human-written
``flavor_profile`` and ``why`` strings on each baseline item act as the textual
proxy for what a vision model would have said. When real embeddings ship, the
function signature stays — the implementation can be swapped to call a VLM on
screenshots without touching callers.
"""
from __future__ import annotations

import re

# Closed vocabulary: each entry is (positive_pole, negative_pole, keywords_pos, keywords_neg).
# Axis names appear verbatim in `notes[]`, so keep them short and human-readable.
AXIS_VOCAB = [
    (
        "ordered", "chaotic",
        {"clean", "coherent", "coherence", "polish", "polished", "structured",
         "hierarchy", "precise", "layout", "harmony", "breathable", "premium",
         "consistent", "minimal", "modern"},
        {"chaos", "chaotic", "overwhelming", "clashing", "broken", "weak",
         "assault", "cluttered", "clutter", "density", "dense", "wiki"},
    ),
    (
        "airy", "dense",
        {"whitespace", "breathability", "breathable", "minimal", "airy",
         "spacious", "light", "extreme whitespace"},
        {"density", "dense", "packed", "overwhelming", "information"},
    ),
    (
        "modern", "dated",
        {"modern", "current", "fresh", "contemporary", "premium",
         "micro-interactions", "micro", "interactions"},
        {"legacy", "obsolete", "90s", "old", "outdated", "expired", "rusty",
         "iron", "shavings"},
    ),
    (
        "polished", "raw",
        {"polish", "polished", "premium", "refined", "exceptional", "finish",
         "artisanal", "harmony"},
        {"raw", "weak", "bare", "simple", "functional", "no visual sugar"},
    ),
    (
        "playful", "serious",
        {"playful", "candy", "fun", "vibrant", "delight", "sparkles"},
        {"serious", "professional", "technical", "utility", "precise"},
    ),
    (
        "bright", "dark",
        {"bright", "light", "white", "vanilla", "milk", "whitespace"},
        {"dark", "dark-mode", "contrast", "espresso", "cold"},
    ),
]


_TOKEN_RE = re.compile(r"[a-z][a-z\-]+")


def _tokens(text: str) -> set:
    return set(_TOKEN_RE.findall(text.lower()))


def _score(tokens_pos: set, tokens_neg: set, kw_pos: set, kw_neg: set) -> float:
    """Score an axis pair: how well does (pos text → pos kw) and (neg text → neg kw) match?"""
    return float(
        len(tokens_pos & kw_pos) + len(tokens_neg & kw_neg)
        - 0.5 * (len(tokens_pos & kw_neg) + len(tokens_neg & kw_pos))
    )


def _join_text(items) -> str:
    parts = []
    for it in items or ():
        parts.append(str(it.get("flavor_profile", "")))
        parts.append(str(it.get("why", "")))
        parts.append(str(it.get("url", "")))
    return " ".join(parts)


def discover_axis(pos_extremes, neg_extremes, *, used: set | None = None) -> dict:
    """Pick the best closed-vocab axis name for one PC.

    Parameters
    ----------
    pos_extremes, neg_extremes : list of baseline items (with ``flavor_profile``/``why``)
        Items closest to the +1 and -1 ends of this axis.
    used : set, optional
        Axis-pair labels already assigned to earlier PCs; avoid reusing.

    Returns
    -------
    dict with keys: ``positive``, ``negative``, ``score``.
    """
    used = used or set()
    pos_text = _tokens(_join_text(pos_extremes))
    neg_text = _tokens(_join_text(neg_extremes))

    best = None
    for positive, negative, kw_pos, kw_neg in AXIS_VOCAB:
        if positive in used or negative in used:
            continue
        forward = _score(pos_text, neg_text, kw_pos, kw_neg)
        reverse = _score(neg_text, pos_text, kw_pos, kw_neg)
        if forward >= reverse:
            score = forward
            p, n = positive, negative
        else:
            score = reverse
            p, n = negative, positive
        if best is None or score > best["score"]:
            best = {"positive": p, "negative": n, "score": score}

    if best is None:
        # Vocabulary exhausted; fall back to a generic label.
        return {"positive": "high", "negative": "low", "score": 0.0}
    return best


def extremes_per_axis(baseline_items, baseline_scores, *, k: int = 3):
    """For each axis (list of per-baseline scores), return (top_k_pos, top_k_neg) item indices."""
    out = []
    n = len(baseline_items)
    for scores in baseline_scores:
        idx = list(range(n))
        idx.sort(key=lambda i: scores[i])
        bottom = idx[: min(k, n)]
        top = list(reversed(idx[-min(k, n):]))
        out.append((top, bottom))
    return out


def discover_axes(baseline_items, baseline_scores, *, k: int = 3):
    """Discover an axis label for each PC, avoiding duplicates."""
    extremes = extremes_per_axis(baseline_items, baseline_scores, k=k)
    used = set()
    axes = []
    for top, bottom in extremes:
        pos_items = [baseline_items[i] for i in top]
        neg_items = [baseline_items[i] for i in bottom]
        axis = discover_axis(pos_items, neg_items, used=used)
        used.add(axis["positive"])
        used.add(axis["negative"])
        axes.append(axis)
    return axes
