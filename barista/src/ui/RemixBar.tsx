import { useState } from 'react'
import type { Ingredients } from '../types/ingredients'

interface Props {
  requestId: string | null
  onRemixed: (ingredients: Ingredients, screenshot: string | null) => void
  endpoint?: string
}

type Status = 'idle' | 'remixing' | 'error'

interface RemixResponse {
  ingredients: Ingredients
  screenshot: string | null
  parsed?: { kind: string; amount: number }
}

export function RemixBar({ requestId, onRemixed, endpoint = 'http://localhost:8000/remix' }: Props) {
  const [instruction, setInstruction] = useState('')
  const [status, setStatus] = useState<Status>('idle')
  const [error, setError] = useState<string | null>(null)
  const [lastParsed, setLastParsed] = useState<{ kind: string; amount: number } | null>(null)

  if (!requestId) return null

  async function submit(e: React.FormEvent) {
    e.preventDefault()
    if (!instruction.trim() || status === 'remixing') return
    setStatus('remixing')
    setError(null)
    try {
      const res = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ request_id: requestId, instruction: instruction.trim() }),
      })
      if (!res.ok) {
        const detail = await res.json().catch(() => ({ detail: res.statusText }))
        throw new Error(detail.detail || `HTTP ${res.status}`)
      }
      const data = (await res.json()) as RemixResponse
      if (data.parsed) setLastParsed(data.parsed)
      onRemixed(data.ingredients, data.screenshot)
      setInstruction('')
      setStatus('idle')
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err))
      setStatus('error')
    }
  }

  return (
    <form
      onSubmit={submit}
      className="absolute right-6 top-48 z-30 flex flex-col gap-2 rounded-2xl bg-black/40 p-4 backdrop-blur-md ring-1 ring-white/10 w-[360px]"
    >
      <div className="text-xs uppercase tracking-widest text-white/60">Add an ingredient</div>
      <div className="flex gap-2">
        <input
          type="text"
          value={instruction}
          onChange={(e) => setInstruction(e.target.value)}
          placeholder="a splash of mint, more chaos, …"
          disabled={status === 'remixing'}
          className="flex-1 rounded-lg bg-white/10 px-3 py-2 text-sm text-white placeholder:text-white/30 outline-none ring-1 ring-white/10 focus:ring-white/40 disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={status === 'remixing' || !instruction.trim()}
          className="rounded-lg bg-white px-3 py-2 text-sm font-medium text-black transition hover:bg-white/80 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {status === 'remixing' ? 'Mixing…' : 'Add'}
        </button>
      </div>
      {status === 'idle' && lastParsed && (
        <div className="text-xs text-white/50">
          last: {lastParsed.kind} ({lastParsed.amount.toFixed(2)})
        </div>
      )}
      {status === 'remixing' && (
        <div className="text-xs text-white/50">Re-blending with the new ingredient…</div>
      )}
      {status === 'error' && error && (
        <div className="text-xs text-red-300 break-words">{error}</div>
      )}
    </form>
  )
}
