interface Props {
  src: string | null
  url?: string
}

// Renders the screenshot Photographer captured (or the user uploaded), so
// the user sees what Sommelier actually tasted. Sits below the TasteBar.
export function ScreenshotPreview({ src, url }: Props) {
  if (!src) return null
  return (
    <div className="absolute right-6 top-[260px] z-10 flex w-[360px] flex-col gap-2 rounded-2xl bg-black/40 p-3 backdrop-blur-md ring-1 ring-white/10">
      <div className="flex items-baseline justify-between">
        <div className="text-xs uppercase tracking-widest text-white/60">What we tasted</div>
        {url && <div className="truncate font-mono text-[10px] text-white/40 ml-2">{url}</div>}
      </div>
      <div className="overflow-hidden rounded-lg ring-1 ring-white/10 max-h-[280px]">
        <img src={src} alt="Captured screenshot" className="w-full h-auto block" />
      </div>
    </div>
  )
}
