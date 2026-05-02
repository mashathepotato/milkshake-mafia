# Vocabulary (canonical strings)

This file is the shared “language” between Sommelier and Barista.

Sommelier should only emit values from here (unless you coordinate an update).
Barista should render *at least* the values from here (unknown values should fall back gracefully).

## `Ingredients.base`
**Good / neutral**
- `strawberry`
- `vanilla`
- `chocolate`
- `banana`
- `matcha`

**Bad / failure**
- `fish`
- `expired_milk`
- `burnt_rubber`

## `Ingredients.texture`
- `smooth` (clean, coherent UI)
- `airy` (minimal, spacious, light)
- `chunky` (inconsistent spacing/components)
- `watery` (thin, unfinished, low-structure)
- `sludge` (overwhelming, broken, “gunk”)

## `Ingredients.inclusions[].kind`
**Positive**
- `sprinkles` (clean details, polish)
- `mint` (restraint, clarity)
- `sparkles` (delight, modern flair)

**Negative**
- `tech_debt_chunks` (visual debt, inconsistency)
- `bugs` (broken elements, obvious failures)

## `Ingredients.toppings[].kind`
**Positive**
- `whipped_cream` (premium finish)

**Negative**
- `lint_dust` (grime, outdated)
- `burnt_marshmallow` (overcooked styling, harsh contrast)

## Notes on extensibility
- Additions are allowed, but should be coordinated:
  1) update this file
  2) Sommelier emits new values
  3) Barista adds rendering support (or a clear fallback)

## Available 3D models (poly.pizza catalog)

A 100-entry catalog of poly.pizza ingredient models lives at
[`context/poly_pizza_ingredients.json`](./poly_pizza_ingredients.json) — 20
each across `fruit`, `food`, `vegetable`, `dessert`, `candy`. Each entry has
`slug`, `name`, `author`, `category`, and a canonical `url`. Sommelier and
Barista should both treat this file as the shared menu of available GLBs:

- **Sommelier** may emit any `slug` from this catalog as an `ingredients[].kind`
  in addition to (or instead of) the canonical names listed above.
- **Barista** can resolve each `slug` to `https://poly.pizza/m/{slug}` to
  download the GLB and register it in `barista/src/scene/assetRegistry.ts`.

Keep `version: poly-pizza-catalog-v1` bumped if the schema changes.

