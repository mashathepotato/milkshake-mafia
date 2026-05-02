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

Pools are picked from deterministically by PC2/PC3 quadrants — same URL
always gets the same garnish. Barista should fall back gracefully on any
unknown value (`(string & {})` in the TS type).

**Positive — primary fruit (modern: bright, dated: classic)**
- bright (`pc3 ≥ 0`): `mango_cube` `raspberry` `kiwi_slice` `passionfruit`
- classic (`pc3 < 0`): `strawberry_chunk` `blueberry` `cherry` `peach_slice`

**Positive — secondary kicker (only when `pc1 ≥ 0.5`)**
- premium (`pc3 ≥ 0`): `coconut_flake` `caramel_drizzle` `mint`
- soft (`pc3 < 0`): `sprinkles` `honey_drop` `sparkles`

**Negative — gunk garnish (visceral when `pc1 < −0.5`, else stale)**
- visceral: `mold` `fish_bone` `rotten_banana` `soggy_crouton`
- stale: `eggshell` `stale_chip` `cold_pea` `wilted_lettuce`

## `Ingredients.toppings[].kind`

**Positive**
- `whipped_cream` `honey_glaze` `fresh_cream_dollop`

**Negative**
- `lint_dust` `burnt_marshmallow` `mystery_sauce` `cigarette_ash`

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

