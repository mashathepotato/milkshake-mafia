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

