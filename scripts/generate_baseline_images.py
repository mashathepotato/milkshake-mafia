#!/usr/bin/env python3
"""
Generate synthetic Gold/Gunk placeholder PNGs for the baseline.

These are purely synthetic and represent the aesthetic poles:
  Gold = clean, minimal, whitespace-forward (emulates Linear/Stripe/Vercel)
  Gunk = chaotic, clashing, cluttered (emulates broken/ugly sites)

Run once to populate baseline/gold/ and baseline/gunk/ before building baseline embeddings.

Usage:
    python scripts/generate_baseline_images.py
"""
from __future__ import annotations

import random
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

BASELINE = Path(__file__).parent.parent / "baseline"
W, H = 1440, 900
RNG = random.Random(42)
NP_RNG = np.random.default_rng(42)


def gold_image(seed: int) -> Image.Image:
    """Minimal, whitespace-heavy, muted palette."""
    rng = random.Random(seed)
    img = Image.new("RGB", (W, H), (252, 252, 253))
    draw = ImageDraw.Draw(img)

    # Background subtle gradient via bands
    for y in range(H):
        lum = int(252 + (y / H) * 3)
        draw.line([(0, y), (W, y)], fill=(lum, lum, min(255, lum + 2)))

    # Navigation bar
    draw.rectangle([0, 0, W, 64], fill=(255, 255, 255))
    draw.line([0, 64, W, 64], fill=(230, 230, 235), width=1)

    # Logo placeholder
    logo_color = rng.choice([(99, 102, 241), (16, 185, 129), (59, 130, 246), (239, 68, 68)])
    draw.rectangle([40, 20, 140, 44], fill=logo_color)

    # Nav items
    for i in range(5):
        x = 220 + i * 120
        draw.rectangle([x, 26, x + 80, 38], fill=(200, 200, 210))

    # Hero headline block
    draw.rectangle([120, 130, 700, 175], fill=(30, 30, 40))
    draw.rectangle([120, 190, 560, 210], fill=(180, 180, 195))
    draw.rectangle([120, 225, 480, 240], fill=(200, 200, 210))

    # CTA button
    cta_color = rng.choice([(99, 102, 241), (16, 185, 129), (59, 130, 246)])
    draw.rounded_rectangle([120, 270, 280, 310], radius=6, fill=cta_color)
    draw.rounded_rectangle([300, 270, 450, 310], radius=6, outline=(180, 180, 195), width=2)

    # Hero image placeholder
    draw.rounded_rectangle([780, 100, W - 60, H - 80], radius=12, fill=(240, 240, 248))
    draw.rounded_rectangle([820, 140, W - 100, H - 120], radius=8, fill=(220, 220, 235))

    # Feature cards row
    card_y = 520
    for i in range(3):
        x = 120 + i * 420
        draw.rounded_rectangle([x, card_y, x + 380, card_y + 200], radius=10, fill=(255, 255, 255))
        draw.rounded_rectangle([x, card_y, x + 380, card_y + 200], radius=10, outline=(230, 230, 235), width=1)
        icon_color = rng.choice([(99, 102, 241), (16, 185, 129), (59, 130, 246), (251, 191, 36)])
        draw.rounded_rectangle([x + 20, card_y + 20, x + 52, card_y + 52], radius=6, fill=icon_color)
        draw.rectangle([x + 20, card_y + 72, x + 200, card_y + 86], fill=(50, 50, 60))
        draw.rectangle([x + 20, card_y + 96, x + 320, card_y + 108], fill=(180, 180, 195))
        draw.rectangle([x + 20, card_y + 116, x + 280, card_y + 128], fill=(195, 195, 210))

    # Footer
    draw.rectangle([0, H - 80, W, H], fill=(248, 248, 250))
    draw.line([0, H - 80, W, H - 80], fill=(230, 230, 235), width=1)

    return img.filter(ImageFilter.GaussianBlur(0.3))


def gunk_image(seed: int) -> Image.Image:
    """Chaotic, clashing, broken-layout feel."""
    rng = np.random.default_rng(seed)
    random_rng = random.Random(seed)

    # Start with noisy background
    noise = rng.integers(100, 256, (H, W, 3), dtype=np.uint8)
    img = Image.fromarray(noise, "RGB")
    draw = ImageDraw.Draw(img)

    # Tiled rainbow blocks
    for _ in range(40):
        x1 = int(rng.integers(0, W - 100))
        y1 = int(rng.integers(0, H - 80))
        x2 = x1 + int(rng.integers(60, 300))
        y2 = y1 + int(rng.integers(40, 200))
        color = tuple(int(c) for c in rng.integers(0, 256, 3))
        draw.rectangle([x1, y1, min(x2, W), min(y2, H)], fill=color)

    # Randomly placed "text" bars
    for _ in range(60):
        x = int(rng.integers(0, W - 200))
        y = int(rng.integers(0, H - 20))
        w = int(rng.integers(50, 400))
        color = tuple(int(c) for c in rng.integers(0, 256, 3))
        draw.rectangle([x, y, min(x + w, W), min(y + 12, H)], fill=color)

    # Big clashing header
    header_colors = [(255, 0, 0), (0, 0, 255), (255, 255, 0), (0, 255, 0)]
    draw.rectangle([0, 0, W, 80], fill=random_rng.choice(header_colors))
    draw.rectangle([0, 80, W, 100], fill=random_rng.choice(header_colors))

    # Tables / overlapping boxes
    for _ in range(8):
        x1 = int(rng.integers(0, W - 200))
        y1 = int(rng.integers(200, H - 100))
        color = tuple(int(c) for c in rng.integers(128, 256, 3))
        draw.rectangle([x1, y1, x1 + 180, y1 + 80], outline=(0, 0, 0), width=3, fill=color)

    return img


GOLD_NAMES = [
    "stripe_hero",
    "linear_dashboard",
    "vercel_landing",
    "notion_homepage",
    "figma_landing",
    "loom_marketing",
    "github_landing",
]

GUNK_NAMES = [
    "broken_table_site",
    "web1_disaster",
    "neon_nightmare",
    "geocities_revival",
    "ie6_relic",
    "frame_overflow",
    "marquee_madness",
]


def main() -> None:
    gold_dir = BASELINE / "gold"
    gunk_dir = BASELINE / "gunk"
    gold_dir.mkdir(parents=True, exist_ok=True)
    gunk_dir.mkdir(parents=True, exist_ok=True)

    print("Generating Gold images...")
    for i, name in enumerate(GOLD_NAMES):
        path = gold_dir / f"{name}.png"
        img = gold_image(seed=i * 17)
        img.save(path, format="PNG", optimize=True)
        print(f"  {path.name} ({path.stat().st_size // 1024} KB)")

    print("\nGenerating Gunk images...")
    for i, name in enumerate(GUNK_NAMES):
        path = gunk_dir / f"{name}.png"
        img = gunk_image(seed=i * 31 + 100)
        img.save(path, format="PNG", optimize=True)
        print(f"  {path.name} ({path.stat().st_size // 1024} KB)")

    print(f"\nDone: {len(GOLD_NAMES)} gold + {len(GUNK_NAMES)} gunk images in {BASELINE}/")


if __name__ == "__main__":
    main()
