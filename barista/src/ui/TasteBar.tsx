import { useRef, useState } from 'react'

export type TasteSubmission =
  | { mode: 'url'; url: string }
  | { mode: 'upload'; file: File }

interface Props {
  busy: boolean
  errorMessage: string | null
  onSubmit: (s: TasteSubmission) => void
}

type Mode = 'url' | 'upload'

export function TasteBar({ busy, errorMessage, onSubmit }: Props) {
  const [mode, setMode] = useState<Mode>('url')
  const [url, setUrl] = useState('https://stripe.com')
  const [file, setFile] = useState<File | null>(null)
  const fileRef = useRef<HTMLInputElement>(null)

  function submit(e: React.FormEvent) {
    e.preventDefault()
    if (busy) return
    if (mode === 'url') {
      if (!url.trim()) return
      onSubmit({ mode: 'url', url: url.trim() })
    } else {
      if (!file) return
      onSubmit({ mode: 'upload', file })
    }
  }

  function pickMode(next: Mode) {
    if (busy) return
    setMode(next)
  }

  return (
    <form
      onSubmit={submit}
      className="absolute right-6 top-6 z-30 flex flex-col gap-3 rounded-2xl bg-black/40 p-4 backdrop-blur-md ring-1 ring-white/10 w-[360px]"
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
            disabled={busy}
            className="flex-1 rounded-lg bg-white/10 px-3 py-2 text-sm text-white placeholder:text-white/30 outline-none ring-1 ring-white/10 focus:ring-white/40 disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={busy || !url.trim()}
            className="rounded-lg bg-white px-3 py-2 text-sm font-medium text-black transition hover:bg-white/80 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {busy ? 'Tasting…' : 'Taste'}
          </button>
        </div>
      ) : (
        <div className="flex flex-col gap-2">
          <input
            ref={fileRef}
            type="file"
            accept="image/png,image/jpeg,image/webp"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            disabled={busy}
            className="text-xs text-white/70 file:mr-3 file:rounded-md file:border-0 file:bg-white/10 file:px-3 file:py-1.5 file:text-white file:cursor-pointer hover:file:bg-white/20 disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={busy || !file}
            className="rounded-lg bg-white px-3 py-2 text-sm font-medium text-black transition hover:bg-white/80 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {busy ? 'Tasting…' : file ? `Taste ${file.name}` : 'Pick an image'}
          </button>
        </div>
      )}

      {errorMessage && (
        <div className="text-xs text-red-300 break-words">{errorMessage}</div>
      )}
    </form>
  )
}
