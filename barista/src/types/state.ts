// 'idle'      → ingredients hover above the blender, lid closed, no liquid
// 'blending'  → lid lifts, ingredients arc into the jar, fade, lid closes,
//               liquid materializes and rises with computed color
// 'done'      → liquid stays at full level, ingredients hidden, lid closed
export type BlendState = 'idle' | 'blending' | 'done'

// Phases of the URL/upload → milkshake flow (orthogonal to the 3D blend
// animation). 'idle' = no taste in flight; 'tasting' = waiting on the API;
// 'revealing' = response in hand, running the screenshot → ingredients
// transition before handing off to BlendState='blending'.
export type TasteState = 'idle' | 'tasting' | 'revealing'
