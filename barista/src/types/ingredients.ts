// Mirrors context/DATA_CONTRACTS.md §5 Ingredients (Sommelier output, Barista input).
// Treat upstream contract as source of truth — keep in sync.

export type Base =
  | 'strawberry' | 'vanilla' | 'chocolate' | 'banana' | 'matcha'
  | 'fish' | 'expired_milk' | 'burnt_rubber'
  | (string & {}) // permit unknown values; Barista must degrade gracefully

export type Texture =
  | 'smooth' | 'airy' | 'chunky' | 'watery' | 'sludge'
  | (string & {})

export type InclusionKind =
  | 'sprinkles' | 'mint' | 'sparkles'
  | 'tech_debt_chunks' | 'bugs'
  | (string & {})

export type ToppingKind =
  | 'whipped_cream'
  | 'lint_dust' | 'burnt_marshmallow'
  | (string & {})

export interface Inclusion {
  kind: InclusionKind
  amount: number // [0,1]
}

export interface Topping {
  kind: ToppingKind
  amount: number // [0,1]
}

export interface Ingredients {
  request_id: string
  url: string
  version: 'ingredients-v0'
  base: Base
  color: { hex: string; accent_hex: string }
  texture: Texture
  viscosity: number   // [0,1]
  tartness: number    // [0,1]
  sweetness: number   // [0,1]
  freshness: number   // [0,1]
  inclusions: Inclusion[]
  toppings: Topping[]
  notes: string[]
  meta?: {
    pc1?: number
    pc2?: number
    pc3?: number
    confidence?: number
    baseline_id?: string
    model_id?: string
  }
}
