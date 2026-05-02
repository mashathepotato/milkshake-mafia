// Per-ingredient color lookup used by GenericIngredient when no GLB is
// registered in assetRegistry.ts. Mirrors the vocab in sommelier/ingredients.py
// (BASE_COLORS) and the inclusion/topping pools added in the recent vocab swap.
//
// New vocab strings are picked to read distinctly in 3D: fruit reds/oranges
// for the good pool, muted greens/browns/greys for the gunk pool. Toppings
// use lighter accent shades. Unknown kinds fall back to a neutral grey so
// nothing renders invisible.

export const FALLBACK_COLOR = '#cccccc'

export const KIND_COLOR: Record<string, string> = {
  // Bases (mirror sommelier/ingredients.py BASE_COLORS hex values).
  strawberry: '#ff4da6',
  vanilla: '#f3e5ab',
  chocolate: '#6b3f1d',
  banana: '#f7d36c',
  matcha: '#8fbf6a',
  fish: '#4f7c8c',
  expired_milk: '#d6d8c2',
  burnt_rubber: '#2b2b2b',

  // Good inclusions — fruit pool (bright + classic).
  mango_cube: '#ffb347',
  raspberry: '#e74c3c',
  kiwi_slice: '#88c45a',
  passionfruit: '#ffaa3b',
  strawberry_chunk: '#ff6488',
  blueberry: '#4f7cb0',
  cherry: '#c0392b',
  peach_slice: '#ffb088',

  // Good inclusions — secondary kickers.
  coconut_flake: '#fff5e0',
  caramel_drizzle: '#c47a2c',
  honey_drop: '#f3c87a',
  mint: '#9ad58a',
  sparkles: '#cfeaff',
  sprinkles: '#ff5b8a',

  // Bad inclusions — gunk pool.
  mold: '#5a6647',
  fish_bone: '#dcd6c0',
  rotten_banana: '#7d6233',
  soggy_crouton: '#a08561',
  eggshell: '#e8dfc8',
  stale_chip: '#a87a4f',
  cold_pea: '#7aa05a',
  wilted_lettuce: '#5e7a3c',
  // Legacy negative inclusions (still accepted by remix; kept for any
  // pre-vocab-swap presets in mockIngredients.ts).
  bugs: '#2c2417',
  tech_debt_chunks: '#5a4730',

  // Good toppings.
  whipped_cream: '#fff8e8',
  honey_glaze: '#f3c87a',
  fresh_cream_dollop: '#fff5d4',

  // Bad toppings.
  lint_dust: '#9a9a8c',
  burnt_marshmallow: '#3a2a22',
  mystery_sauce: '#7c4a4a',
  cigarette_ash: '#7a7770',
}

export function colorForKind(kind: string): string {
  return KIND_COLOR[kind] ?? FALLBACK_COLOR
}
