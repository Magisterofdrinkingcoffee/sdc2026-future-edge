import { useEffect, useState } from 'react'
import confetti from 'canvas-confetti'
import { weather } from '../game'

const reducedMotion = () => window.matchMedia?.('(prefers-reduced-motion: reduce)').matches

export function celebrate() {
  if (reducedMotion()) return
  confetti({ particleCount: 90, spread: 70, origin: { y: 0.7 }, colors: ['#6C4CF1', '#2BB673', '#FFB020', '#3D9BFF'] })
}

export function Logo({ small }) {
  return (
    <div className={`flex items-center gap-2 font-display font-bold ${small ? 'text-xl' : 'text-2xl'}`}>
      <span aria-hidden className="grid h-9 w-9 place-items-center rounded-xl bg-violet-500 text-white shadow-[0_3px_0_#4529B8]">⌁</span>
      <span>Future Edge</span>
    </div>
  )
}

export function Toasts({ toasts }) {
  return (
    <div aria-live="polite" className="pointer-events-none fixed bottom-4 inset-x-0 z-50 flex flex-col items-center gap-2 px-4">
      {toasts.map((t) => (
        <div key={t.id} className="animate-pop flex items-center gap-3 rounded-2xl border-2 border-line bg-white px-4 py-3 shadow-[0_4px_0_#E3E6EF]">
          <span className="text-2xl" aria-hidden>{t.icon}</span>
          <div><div className="font-display font-semibold">{t.title}</div>{t.text && <div className="text-sm text-muted">{t.text}</div>}</div>
        </div>
      ))}
    </div>
  )
}

export function Bar({ value, color = 'bg-violet-500', track = 'bg-line', h = 'h-3' }) {
  return (
    <div className={`${h} w-full overflow-hidden rounded-full ${track}`}>
      <div className={`${h} rounded-full ${color} transition-all duration-500`} style={{ width: `${Math.max(0, Math.min(1, value)) * 100}%` }} />
    </div>
  )
}

export function useCountUp(target, ms = 900) {
  const [v, setV] = useState(reducedMotion() ? target : 0)
  useEffect(() => {
    if (reducedMotion()) { setV(target); return }
    let raf; const t0 = performance.now(); const from = 0
    const tick = (t) => { const k = Math.min(1, (t - t0) / ms); setV(from + (target - from) * (1 - (1 - k) ** 3)); if (k < 1) raf = requestAnimationFrame(tick) }
    raf = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(raf)
  }, [target, ms])
  return v
}

// The signature element: your career as a 4-year weather forecast.
export function ForecastStrip({ timeline, animate, compare }) {
  const year0 = new Date().getFullYear()
  return (
    <ol className="grid grid-cols-4 gap-2 sm:gap-3">
      {timeline.map((t, i) => <ForecastDay key={t.year} t={t} i={i} year={year0 + t.year} animate={animate} other={compare?.[i]} />)}
    </ol>
  )
}

function ForecastDay({ t, i, year, animate, other }) {
  const n = useCountUp(t.edge, animate ? 700 + i * 250 : 0)
  const w = weather(t.edge)
  return (
    <li className={`rounded-2xl border-2 px-2 py-3 text-center ${i === 0 ? 'border-violet-300 bg-violet-50' : 'border-line bg-white'}`}>
      <div className="text-xs font-bold text-muted">{i === 0 ? 'Now' : year}</div>
      <div className="my-1 text-3xl sm:text-4xl" aria-hidden>{w.icon}</div>
      <div className="font-display text-2xl font-bold sm:text-3xl">{Math.round(animate ? n : t.edge)}</div>
      <div className={`text-[11px] font-bold leading-tight ${w.tone}`}>{w.label}</div>
      {other && <div className="mt-1 text-[11px] text-muted" title="Other scenario">vs {Math.round(other.edge)}</div>}
    </li>
  )
}

export function SdgChip({ target, sdgs, reason }) {
  const goal = target.split('.')[0]
  return (
    <span title={`SDG ${target}: ${sdgs?.targets?.[target] || ''}${reason ? `\nWhy: ${reason}` : ''}`}
      className="chip cursor-help bg-sprout-50 text-sprout-700">
      🌍 SDG {target}{sdgs?.goals?.[goal] ? ` ${sdgs.goals[goal]}` : ''}
    </span>
  )
}

export function Sheet({ open, onClose, children, label }) {
  useEffect(() => {
    if (!open) return
    const k = (e) => e.key === 'Escape' && onClose()
    window.addEventListener('keydown', k)
    return () => window.removeEventListener('keydown', k)
  }, [open, onClose])
  if (!open) return null
  return (
    <div className="fixed inset-0 z-40 flex items-end justify-center bg-ink/40 sm:items-center" onClick={onClose} role="dialog" aria-modal="true" aria-label={label}>
      <div className="animate-pop max-h-[90vh] w-full max-w-lg overflow-y-auto rounded-t-3xl bg-white p-6 sm:rounded-3xl" onClick={(e) => e.stopPropagation()}>
        {children}
      </div>
    </div>
  )
}

// Wizard frame: logo, progress bar, centred single column.
export function WizardFrame({ step, total, onBack, children }) {
  return (
    <div className="min-h-screen">
      <header className="mx-auto flex max-w-2xl items-center gap-4 px-4 pt-6">
        {onBack ? <button onClick={onBack} aria-label="Back" className="grid h-10 w-10 place-items-center rounded-xl text-2xl text-muted hover:bg-white">‹</button> : <span className="w-10" />}
        <div className="flex-1"><Bar value={step / total} color="bg-sprout-500" h="h-4" /></div>
        <span className="text-sm font-bold text-muted">{step}/{total}</span>
      </header>
      <main className="mx-auto max-w-2xl px-4 pb-16 pt-8">{children}</main>
    </div>
  )
}
