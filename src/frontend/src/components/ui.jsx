export function SdgBadge({ target, sdgs, reason }) {
  const goal = target.split('.')[0]
  const text = sdgs?.targets?.[target]
  return (
    <span title={`SDG ${target}: ${text || ''}${reason ? `\nWhy: ${reason}` : ''}`}
      className="chip bg-emerald-50 text-emerald-700 border border-emerald-200 cursor-help">
      SDG {target}{sdgs?.goals?.[goal] ? ` · ${sdgs.goals[goal]}` : ''}
    </span>
  )
}

const STATUS = {
  rising: 'bg-emerald-100 text-emerald-800',
  holding: 'bg-amber-100 text-amber-800',
  fading: 'bg-rose-100 text-rose-800',
}
const ARROW = { rising: '▲', holding: '■', fading: '▼' }

export function StatusChip({ status }) {
  return <span className={`chip ${STATUS[status]}`}>{ARROW[status]} {status}</span>
}

const TYPE = {
  course: ['Course', 'bg-sky-100 text-sky-800', 'knowledge'],
  project: ['Project', 'bg-violet-100 text-violet-800', 'proof'],
  experience: ['Experience', 'bg-orange-100 text-orange-800', 'personal skills'],
}
export function TypeChip({ type }) {
  const [label, cls, why] = TYPE[type]
  return <span className={`chip ${cls}`} title={why}>{label} · {why}</span>
}

export function EstimateNote({ children }) {
  return <span className="chip bg-slate-100 text-slate-600 border border-slate-200">Estimate{children ? ` · ${children}` : ''}</span>
}

export function TrendSource({ trends, dark }) {
  if (!trends) return null
  const date = trends.fetched_at ? new Date(trends.fetched_at).toLocaleString() : 'not fetched yet'
  return (
    <div className={`text-xs rounded-lg px-3 py-2 max-w-md ${dark ? 'bg-white/10 text-slate-200' : 'bg-slate-100 text-slate-600'}`}>
      <div className="font-semibold">{trends.is_sample ? '⚠ Sample trend data' : 'Live trend data'}</div>
      <div>Source: {trends.is_sample ? 'placeholder values – press “Refresh trend data”' : trends.source}</div>
      <div>Updated: {date}</div>
    </div>
  )
}

export function Pct({ v }) {
  return <>{Math.round(v * 100)}%</>
}
