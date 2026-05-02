import { useState } from 'react'

// Inline explainer for first-time viewers — collapsible so it gets out of the
// way once the concept lands. Values match context/VOCAB.md so what's described
// here stays in lockstep with what Sommelier emits.
export function ConceptNote() {
  const [open, setOpen] = useState(true)

  if (!open) {
    return (
      <button
        onClick={() => setOpen(true)}
        className="absolute left-6 top-24 z-10 h-8 w-8 rounded-full bg-white/10 text-white/70 ring-1 ring-white/20 backdrop-blur-md hover:bg-white/15"
        aria-label="How it works"
      >
        ?
      </button>
    )
  }

  return (
    <div className="absolute left-6 top-24 z-10 max-w-sm rounded-2xl bg-black/45 p-5 text-sm leading-relaxed text-white/85 backdrop-blur-md ring-1 ring-white/10">
      <div className="flex items-start justify-between gap-4">
        <div className="text-xs uppercase tracking-[0.25em] text-white/50">How it works</div>
        <button
          onClick={() => setOpen(false)}
          className="-mr-1 -mt-1 text-white/40 hover:text-white/80"
          aria-label="Hide"
        >
          ×
        </button>
      </div>
      <p className="mt-3 text-white/75">
        Sommelier analyzes a website's visual DNA and translates it into{' '}
        <span className="text-white">ingredients</span>. Barista renders them
        as a milkshake.
      </p>
      <ul className="mt-3 space-y-1.5 text-[13px] text-white/70">
        <li>
          <span className="text-rose-300">Clean spacing & typography</span> →
          strawberry base, sprinkles
        </li>
        <li>
          <span className="text-amber-200">Modern polish, restraint</span> →
          vanilla base, mint, sparkles
        </li>
        <li>
          <span className="text-emerald-200">Premium finish</span> →
          whipped cream topping
        </li>
        <li>
          <span className="text-stone-400">Inconsistent palette / spacing</span>
          {' '}→ sludge texture, tech-debt chunks
        </li>
        <li>
          <span className="text-red-400">Broken layout, unreadable text</span> →
          fish or burnt-rubber base, bugs
        </li>
      </ul>
      <p className="mt-3 text-[12px] text-white/40">
        Mapping table lives in{' '}
        <code className="rounded bg-white/10 px-1 py-px text-white/70">
          context/VOCAB.md
        </code>
        .
      </p>
    </div>
  )
}
