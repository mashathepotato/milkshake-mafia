import { useState } from 'react'
import type { Ingredients } from '../types/ingredients'

interface Props {
  onTasted: (ingredients: Ingredients) => void
  endpoint?: string
}

type Status = 'idle' | 'tasting' | 'error'

export function UrlBar({ onTasted, endpoint = 'http://localhost:8000/taste' }: Props) {
  const [url, setUrl] = useState('https://stripe.com')
  const [status, setStatus] = useState<Status>('idle')
  const [error, setError] = useState<string | null>(null)

  async function submit(e: React.FormEvent) {
    e.preventDefault()
    if (!url.trim() || status === 'tasting') return
    setStatus('tasting')
    setError(null)
    try {
      const res = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: url.trim() }),
      })
      if (!res.ok) {
        const detail = await res.json().catch(() => ({ detail: res.statusText }))
        throw new Error(detail.detail || `HTTP ${res.status}`)
      }
      const ingredients = (await res.json()) as Ingredients
      onTasted(ingredients)
      setStatus('idle')
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err))
      setStatus('error')
    }
  }

  return (
    <form
      onSubmit={submit}
      className="absolute right-6 top-6 z-10 flex flex-col gap-2 rounded-2xl bg-black/40 p-4 backdrop-blur-md ring-1 ring-white/10 w-[360px]"
    >
      <div className="text-xs uppercase tracking-widest text-white/60">Taste a URL</div>
      <div className="flex gap-2">
        <input
          type="url"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="https://example.com"
          disabled={status === 'tasting'}
          className="flex-1 rounded-lg bg-white/10 px-3 py-2 text-sm text-white placeholder:text-white/30 outline-none ring-1 ring-white/10 focus:ring-white/40 disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={status === 'tasting' || !url.trim()}
          className="rounded-lg bg-white px-3 py-2 text-sm font-medium text-black transition hover:bg-white/80 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {status === 'tasting' ? 'Tasting…' : 'Taste'}
        </button>
      </div>
      {status === 'tasting' && (
        <div className="text-xs text-white/50">
          Capturing screenshot and projecting through Sommelier (5–30s)…
        </div>
      )}
      {status === 'error' && error && (
        <div className="text-xs text-red-300 break-words">{error}</div>
      )}
    </form>
  )
}
