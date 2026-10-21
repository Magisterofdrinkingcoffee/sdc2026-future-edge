import { useEffect, useState } from 'react'
import { api } from '../../api'
import { FIELD_ICON, weather } from '../../game'
import { Bar, ForecastStrip, SdgChip } from '../ui'

const GROUPS = [
  { id: 'rising', icon: '🌱', title: 'Growing in value', text: 'Hard for AI and in demand. Lean into these.', bar: 'bg-sprout-500' },
  { id: 'holding', icon: '⚖️', title: 'Holding steady', text: 'AI helps here, but still needs you.', bar: 'bg-sun-500' },
  { id: 'fading', icon: '🍂', title: 'At risk from AI', text: 'AI is quickly getting good at these.', bar: 'bg-coral-500' },
]

export default function ForecastView(ctx) {
  const { s, set, meta, forecast, goal } = ctx
  const year3 = new Date().getFullYear() + 3

  useEffect(() => {
    const seen = { ...(s.flags.seen || {}), [s.scenario]: true }
    set((p) => ({ flags: { ...p.flags, seen, bothScenarios: !!(seen.fast && seen.moderate) } }))
  }, [s.scenario]) // eslint-disable-line react-hooks/exhaustive-deps

  if (!forecast || !goal) return <p className="text-muted">Loading forecast…</p>
  const cur = forecast[s.scenario]
  const otherSc = s.scenario === 'fast' ? 'moderate' : 'fast'
  const other = forecast[otherSc].roles.find((r) => r.role_id === goal.role_id)
  const ranked = [...cur.roles].sort((a, b) => b.edge_y3 - a.edge_y3)

  return (
    <div className="space-y-6">
      <section className="panel">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold">Career forecast: {goal.title}</h1>
            <p className="text-sm text-muted">How hard you'll be to replace by AI, from 0 to 100. Estimates, not a verdict.</p>
          </div>
          <div className="flex rounded-2xl border-2 border-line p-1" role="radiogroup" aria-label="AI scenario">
            {Object.entries(meta.scenarios).map(([id, sc]) => (
              <button key={id} role="radio" aria-checked={s.scenario === id} onClick={() => set({ scenario: id })}
                className={`rounded-xl px-3 py-1.5 text-sm font-bold ${s.scenario === id ? 'bg-violet-500 text-white' : 'text-muted'}`}>
                {id === 'fast' ? '🚀' : '🐢'} {sc.label}
              </button>
            ))}
          </div>
        </div>
        <div className="mt-5"><ForecastStrip timeline={goal.timeline} compare={other.timeline} /></div>
        <p className="mt-2 text-xs text-muted">"vs" is the {meta.scenarios[otherSc].label} scenario.</p>

        <details className="mt-4 rounded-2xl bg-canvas p-4">
          <summary className="cursor-pointer font-display font-semibold">How we worked this out</summary>
          <ul className="mt-2 space-y-1 text-sm">{Object.values(goal.explain).map((e, i) => <li key={i}>{e}</li>)}</ul>
          {goal.gap.length > 0 && <p className="mt-2 text-sm"><b>Skills gap:</b> {goal.gap.map((g) => g.name).join(', ')}.</p>}
        </details>
        <div className="mt-4 flex flex-wrap gap-2">{Object.entries(goal.sdgs).map(([t, why]) => <SdgChip key={t} target={t} reason={why} sdgs={meta.sdgs} />)}</div>
      </section>

      <div className="grid gap-6 lg:grid-cols-[1fr_340px]">
        <section className="panel">
          <h2 className="text-xl font-bold">Your skills over the next 3 years</h2>
          <p className="text-sm text-muted">The bar shows how much of each skill AI can do: now (solid) and in {year3} (faded).</p>
          <div className="mt-4 space-y-6">
            {GROUPS.map((g) => {
              const list = cur.skills.filter((k) => k.status === g.id)
              if (!list.length) return null
              return (
                <div key={g.id}>
                  <h3 className="font-display text-lg font-semibold">{g.icon} {g.title}</h3>
                  <p className="text-sm text-muted">{g.text}</p>
                  <ul className="mt-2 space-y-3">
                    {list.map((k) => (
                      <li key={k.skill}>
                        <div className="flex justify-between gap-2 text-sm"><b>{k.name}</b>
                          <span className="shrink-0 text-muted">AI can do {Math.round(k.exposure_now * 100)}% now, {Math.round(k.exposure_y3 * 100)}% in {year3}</span></div>
                        <div className="relative mt-1 h-3 overflow-hidden rounded-full bg-line">
                          <div className={`absolute h-3 rounded-full opacity-35 ${g.bar}`} style={{ width: `${k.exposure_y3 * 100}%` }} />
                          <div className={`absolute h-3 rounded-full ${g.bar}`} style={{ width: `${k.exposure_now * 100}%` }} />
                        </div>
                        <div className="mt-0.5 text-xs text-muted">Trend: {k.signal.label}, research {k.signal.growth >= 0 ? 'up' : 'down'} {Math.abs(Math.round((k.signal.growth || 0) * 100))}% in a year</div>
                      </li>
                    ))}
                  </ul>
                </div>
              )
            })}
          </div>
          <p className="mt-6 text-xs text-muted">Trend source: {cur.trend_source.source}{cur.trend_source.fetched_at ? `, updated ${new Date(cur.trend_source.fetched_at).toLocaleDateString()}` : ''}. Today's AI levels per skill: {cur.exposure_source}.</p>
        </section>

        <aside className="space-y-6">
          <section className="panel">
            <h2 className="text-lg font-bold">Other roles for you</h2>
            <p className="text-sm text-muted">Ranked by your {year3} Edge Score.</p>
            <ul className="mt-3 space-y-1">
              {ranked.map((r) => {
                const w = weather(r.edge_y3)
                const isGoal = r.role_id === goal.role_id
                return (
                  <li key={r.role_id}>
                    <button onClick={() => !isGoal && window.confirm(`Make ${r.title} your new goal? Your quest map will change.`) && set((p) => ({ profile: { ...p.profile, goal_role: r.role_id }, completed: [], history: [] }))}
                      className={`flex w-full items-center gap-3 rounded-2xl px-3 py-2 text-left ${isGoal ? 'bg-violet-50' : 'hover:bg-canvas'}`}>
                      <span className="text-xl" aria-hidden>{w.icon}</span>
                      <span className="min-w-0 flex-1"><span className="block truncate text-sm font-bold">{FIELD_ICON[meta.roles.find((x) => x.id === r.role_id)?.field]} {r.title}</span>
                        <span className="text-xs text-muted">{isGoal ? 'Your goal' : `${Math.round(r.match * 100)}% skill match`}</span>
                        {r.at_risk && <span className="chip ml-1 bg-coral-50 text-coral-600" title={`AI could do about ${Math.round(r.role_ai_exposure_y3 * 100)}% of this role's work by ${year3}`}>at risk</span>}</span>
                      <span className="font-display text-lg font-bold">{Math.round(r.edge_y3)}</span>
                    </button>
                  </li>
                )
              })}
            </ul>
          </section>
          <TrendPanel {...ctx} />
        </aside>
      </div>
    </div>
  )
}

function TrendPanel({ meta, trends, setTrends, overrides, setOverrides, set }) {
  const [busy, setBusy] = useState(false)
  const mark = () => set((p) => ({ flags: { ...p.flags, trends: true } }))
  const refresh = async () => {
    mark(); await api.refreshTrends(); setBusy(true)
    const id = setInterval(async () => {
      const t = await api.trends(); setTrends(t)
      if (!t.refresh.running) { clearInterval(id); setBusy(false) }
    }, 3000)
  }
  const g = (sid) => overrides[sid] ?? trends?.signals?.[sid]?.growth ?? 0
  return (
    <section className="panel">
      <h2 className="text-lg font-bold">📡 Where the trend data comes from</h2>
      {trends && (
        <p className={`mt-2 rounded-2xl p-3 text-sm ${trends.is_sample ? 'bg-sun-50 text-sun-600' : 'bg-sprout-50 text-sprout-700'}`}>
          {trends.is_sample ? 'Sample values for the demo. Refresh to load real research data from arXiv.'
            : `Real arXiv paper counts, updated ${new Date(trends.fetched_at).toLocaleString()}.`}
        </p>
      )}
      <button className="btn-white mt-3 w-full py-2 text-sm" disabled={busy} onClick={refresh}>{busy ? 'Fetching from arXiv (about 1 min)…' : 'Refresh trend data'}</button>
      {trends?.refresh?.error && <p className="mt-2 text-xs text-coral-600">{trends.refresh.error}</p>}
      <details className="mt-4">
        <summary className="cursor-pointer text-sm font-bold">What if AI moves faster in one area?</summary>
        <p className="mt-1 text-xs text-muted">Drag a slider and watch your forecast change.</p>
        {meta.signals.map((sg) => (
          <label key={sg.id} className="mt-3 block text-xs">
            <span className="flex justify-between font-bold"><span>{sg.label}</span><span>{g(sg.id) >= 0 ? '+' : ''}{Math.round(g(sg.id) * 100)}%</span></span>
            <input type="range" min="-0.5" max="3" step="0.1" value={g(sg.id)} className="w-full accent-violet-500"
              onChange={(e) => { mark(); setOverrides({ ...overrides, [sg.id]: +e.target.value }) }} />
          </label>
        ))}
        {Object.keys(overrides).length > 0 && <button className="mt-2 text-xs font-bold text-violet-600 underline" onClick={() => setOverrides({})}>Back to real data</button>}
      </details>
    </section>
  )
}
