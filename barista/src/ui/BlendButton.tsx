import type { BlendState } from '../types/state'

interface Props {
  state: BlendState
  onRun: () => void
}

const LABEL: Record<BlendState, string> = {
  idle: 'Run blend',
  blending: 'Blending…',
  done: 'Run again',
}

export function BlendButton({ state, onRun }: Props) {
  const disabled = state === 'blending'
  return (
    <div className="absolute right-6 bottom-6 z-10">
      <button
        onClick={onRun}
        disabled={disabled}
        className={`px-6 py-3 rounded-full text-sm font-medium tracking-wide transition shadow-lg ring-1 ${
          disabled
            ? 'bg-white/10 text-white/40 ring-white/10 cursor-not-allowed'
            : 'bg-white text-black ring-white/20 hover:bg-white/90 active:scale-95'
        }`}
      >
        {LABEL[state]}
      </button>
    </div>
  )
}
