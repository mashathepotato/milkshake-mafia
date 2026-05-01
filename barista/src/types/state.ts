// 'idle'      → ingredients hover above the blender, lid closed, no liquid
// 'blending'  → lid lifts, ingredients arc into the jar, fade, lid closes,
//               liquid materializes and rises with computed color
// 'done'      → liquid stays at full level, ingredients hidden, lid closed
export type BlendState = 'idle' | 'blending' | 'done'
