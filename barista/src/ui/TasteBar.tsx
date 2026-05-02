import { useRef, useState } from 'react'
import type { Ingredients } from '../types/ingredients'

interface Props {
  onTasted: (ingredients: Ingredients, screenshot: string | null) => void
  endpoint?: string
}

type Mode = 'url' | 'upload'
type Status = 'idle' | 'tasting' | 'error'

interface TasteResponse {
  ingredients: Ingredients
  screenshot: string | null
}

export function TasteBar({ onTasted, endpoint = 'http://localhost:8000' }: Props) {
  const [mode, setMode] = useState<Mode>('url')
  const [url, setUrl] = useState('https://stripe.com')
  const [file, setFile] = useState<File | null>(null)
  const [status, setStatus] = useState<Status>('idle')
  const [error, setError] = useState<string | null>(null)
  const fileRef = useRef<HTMLInputElement>(null)

  async function submit(e: React.FormEvent) {
    e.preventDefault()
    if (status === 'tasting') return
    setStatus('tasting')
    setError(null)
    try {
      let res: Response
      if (mode === 'url') {
        if (!url.trim()) return
        res = await fetch(`${endpoint}/taste`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ url: url.trim() }),
        })
      } else {
        if (!file) {
          setError('Pick an image first.')
          setStatus('error')
          return
        }
        const form = new FormData()
        form.append('file', file)
        res = await fetch(`${endpoint}/taste/upload`, { method: 'POST', body: form })
      }
      if (!res.ok) {
        const detail = await res.json().catch(() => ({ detail: res.statusText }))
        throw new Error(detail.detail || `HTTP ${res.status}`)
      }
      const data = (await res.json()) as TasteResponse
      onTasted(data.ingredients, data.screenshot)
      setStatus('idle')
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err))
      setStatus('error')
    }
  }

  function pickMode(next: Mode) {
    if (status === 'tasting') return
    setMode(next)
    setError(null)
  }

  return (
    <form
      onSubmit={submit}
      className="absolute right-6 top-6 z-10 flex flex-col gap-3 rounded-2xl bg-black/40 p-4 backdrop-blur-md ring-1 ring-white/10 w-[360px]"
    >
      <div className="flex items-center justify-between">
        <div className="text-xs uppercase tracking-widest text-white/60">Taste</div>
        <div className="flex gap-1 text-xs">
          <button
            type="button"
            onClick={() => pickMode('url')}
            className={`rounded-md px-2 py-1 ${mode === 'url' ? 'bg-white text-black' : 'bg-white/10 text-white/70 hover:bg-white/20'}`}
          >
            URL
          </button>
          <button
            type="button"
            onClick={() => pickMode('upload')}
            className={`rounded-md px-2 py-1 ${mode === 'upload' ? 'bg-white text-black' : 'bg-white/10 text-white/70 hover:bg-white/20'}`}
          >
            Upload
          </button>
        </div>
      </div>

      {mode === 'url' ? (
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
      ) : (
        <div className="flex flex-col gap-2">
          <input
            ref={fileRef}
            type="file"
            accept="image/png,image/jpeg,image/webp"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            disabled={status === 'tasting'}
            className="text-xs text-white/70 file:mr-3 file:rounded-md file:border-0 file:bg-white/10 file:px-3 file:py-1.5 file:text-white file:cursor-pointer hover:file:bg-white/20 disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={status === 'tasting' || !file}
            className="rounded-lg bg-white px-3 py-2 text-sm font-medium text-black transition hover:bg-white/80 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {status === 'tasting' ? 'Tasting…' : file ? `Taste ${file.name}` : 'Pick an image'}
          </button>
        </div>
      )}

      {status === 'tasting' && (
        <div className="text-xs text-white/50">
          {mode === 'url'
            ? 'Capturing screenshot and projecting through Sommelier (5–30s)…'
            : 'Embedding image and projecting through Sommelier…'}
        </div>
      )}
      {status === 'error' && error && (
        <div className="text-xs text-red-300 break-words">{error}</div>
      )}
    </form>
  )
}
