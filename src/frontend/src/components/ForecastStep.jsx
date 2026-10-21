import { useEffect, useState } from 'react'
import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { api } from '../api'
import { EstimateNote, Pct, SdgBadge, StatusChip, TrendSource } from './ui'

const YEAR0 = new Date().getFullYear()

export default function ForecastStep(props) {
  const { meta, profile, body, scenario, setScenario, overrides, setOverrides, trends, setTrends, setStep, setProfile } = props
  const [both, setBoth] = useState(null)
  const [roleId, setRoleId] = useState(profile.goal_role || null)
  const [err, setErr] = useState(null)

  const bodyKey = JSON.stringify({ ...body, scenario: undefined })
  useEffect(() => {
    if (!Object.keys(profile.skills).length) return
    Promise.all(['moderate', 'fast'].map((s) => api.forecast({ ...body, scenario: s })))
      .then(([m, f]) => { setBoth({ moderate: m, fast: f }); setErr(null) })
      .catch((e) => setErr(e.message))
  }, [bodyKey]) // eslint-disable-line react-hooks/exhaustive-deps

  if (!Object.keys(profile.skills).length) return <div className="card">Add your skills first. <button className="underline" onClick={() => setStep('profile')}>Go to profile</button></div>
  if (err) return <div className="card text-rose-700">{err}</div>
  if (!both) return <div className="text-slate-500">Calculating forecast…</div>

  const cur = both[scenario]
  const ranked = [...cur.roles].sort((a, b) => b.edge_y3 - a.edge_y3)
  const selId = roleId || ranked[0].role_id
  const role = cur.roles.find((r) => r.role_id === selId)
  const other = both[scenario === 'fast' ? 'moderate' : 'fast'].roles.find((r) => r.role_id === selId)
  const chart = role.timeline.map((t, i) => ({
    year: `${YEAR0 + t.year}`,
    [cur.scenario_label]: t.edge,
    [both[scenario === 'fast' ? 'moderate' : 'fast'].scenario_label]: other.timeline[i].edge,
  }))
  const change = role.edge_y3 - role.edge_now

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold">{profile.name ? `${profile.name}'s` : 'Your'} career forecast</h2>
          <p className="text-sm text-slate-600">How much of your value AI can't replace – now and over the next 3 years.</p>
        </div>
        <div className="flex rounded-lg border border-slate-300 bg-white p-1">
          {Object.entries(meta.scenarios).map(([id, s]) => (
            <button key={id} onClick={() => setScenario(id)} className={`rounded-md px-3 py-1.5 text-sm font-medium ${scenario === id ? 'bg-ink text-white' : 'text-slate-600'}`}>{s.label}</button>
          ))}
        </div>
      </div>

      <div className="grid gap-5 lg:grid-cols-3">
        <section className="card min-w-0 lg:col-span-2">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <div className="label">Future Edge Score · {role.title}</div>
              <div className="flex items-baseline gap-3 mt-1">
                <span className="text-4xl font-bold">{Math.round(role.edge_now)}</span>
                <span className="text-slate-400">→</span>
                <span className={`text-4xl font-bold ${change < -2 ? 'text-rose-600' : 'text-slate-700'}`}>{Math.round(role.edge_y3)}</span>
                <span className="text-sm text-slate-500">in {YEAR0 + 3}</span>
              </div>
            </div>
            <EstimateNote>{cur.scenario_label}</EstimateNote>
          </div>
          <div className="h-56 mt-3">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chart} margin={{ left: -20, right: 10 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="year" fontSize={12} />
                <YAxis domain={[0, 100]} fontSize={12} />
                <Tooltip />
                <Legend wrapperStyle={{ fontSize: 12 }} />
                <Line type="monotone" dataKey={cur.scenario_label} stroke="#1d4ed8" strokeWidth={3} dot isAnimationActive={false} />
                <Line type="monotone" dataKey={both[scenario === 'fast' ? 'moderate' : 'fast'].scenario_label} stroke="#94a3b8" strokeDasharray="5 5" dot={false} isAnimationActive={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
          <ul className="mt-3 space-y-1 text-sm text-slate-700">
            {Object.values(role.explain).map((e, i) => <li key={i}>• {e}</li>)}
          </ul>
          <div className="flex flex-wrap gap-2 mt-3">
            {Object.entries(role.sdgs).map(([t, why]) => <SdgBadge key={t} target={t} reason={why} sdgs={meta.sdgs} />)}
          </div>
          <div className="mt-4 flex flex-wrap items-center gap-3">
            <button className="btn-primary" onClick={() => { setProfile({ ...profile, goal_role: role.role_id }); setStep('pathway') }}>Build my pathway for {role.title} →</button>
            {role.gap.length > 0 && <span className="text-sm text-slate-600">Skills gap: {role.gap.slice(0, 4).map((g) => g.name).join(', ')}{role.gap.length > 4 ? '…' : ''}</span>}
          </div>
        </section>

        <section className="card">
          <div className="label mb-2">Future roles for you (ranked by {YEAR0 + 3} Edge)</div>
          <div className="space-y-1">
            {ranked.map((r) => (
              <button key={r.role_id} onClick={() => setRoleId(r.role_id)}
                className={`w-full flex items-center justify-between rounded-lg px-3 py-2 text-sm text-left ${r.role_id === selId ? 'bg-edge-50 border border-edge-500' : 'hover:bg-slate-50 border border-transparent'}`}>
                <span>
                  <span className="font-medium">{r.title}</span>
                  {r.role_id === profile.goal_role && <span className="chip bg-ink text-white ml-2">goal</span>}
                  <span className="block text-xs text-slate-500">match <Pct v={r.match} /> · gap {r.gap.length} skills</span>
                </span>
                <span className="text-right"><b>{Math.round(r.edge_y3)}</b><span className={`block text-xs ${r.edge_y3 < r.edge_now - 2 ? 'text-rose-600' : 'text-slate-500'}`}>{r.edge_y3 - r.edge_now >= 0 ? '+' : ''}{(r.edge_y3 - r.edge_now).toFixed(1)}</span></span>
              </button>
            ))}
          </div>
        </section>
      </div>

      <div className="grid gap-5 lg:grid-cols-3">
        <section className="card lg:col-span-2 overflow-x-auto">
          <div className="label mb-2">Skill forecast · which of your skills fade or hold up</div>
          <table className="w-full text-sm">
            <thead className="text-left text-xs text-slate-500">
              <tr><th className="py-1">Skill</th><th>Outlook</th><th>AI can do today → {YEAR0 + 3}</th><th>Trend signal (12-month research growth)</th></tr>
            </thead>
            <tbody>
              {cur.skills.map((s) => (
                <tr key={s.skill} className="border-t border-slate-100">
                  <td className="py-2 pr-2">{s.name}<span className="block text-xs text-slate-400">{s.category}</span></td>
                  <td><StatusChip status={s.status} /></td>
                  <td><Pct v={s.exposure_now} /> → <b><Pct v={s.exposure_y3} /></b></td>
                  <td className="text-xs">{s.signal.label}: {s.signal.growth == null ? 'n/a' : `${s.signal.growth >= 0 ? '+' : ''}${Math.round(s.signal.growth * 100)}%`}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="text-xs text-slate-500 mt-3">Trend source: {cur.trend_source.source} {cur.trend_source.fetched_at ? `(updated ${new Date(cur.trend_source.fetched_at).toLocaleDateString()})` : ''}. Today's AI-exposure levels: {cur.exposure_source}.</p>
        </section>

        <TrendPanel {...{ meta, trends, setTrends, overrides, setOverrides }} />
      </div>
    </div>
  )
}

function TrendPanel({ meta, trends, setTrends, overrides, setOverrides }) {
  const [polling, setPolling] = useState(false)
  const refresh = async () => {
    await api.refreshTrends(); setPolling(true)
    const id = setInterval(async () => {
      const t = await api.trends(); setTrends(t)
      if (!t.refresh.running) { clearInterval(id); setPolling(false) }
    }, 3000)
  }
  const growth = (sid) => overrides[sid] ?? trends?.signals?.[sid]?.growth ?? 0

  return (
    <section className="card space-y-3">
      <div className="label">AI-trend signal layer</div>
      <TrendSource trends={trends} />
      <button className="btn-ghost w-full justify-center" disabled={polling} onClick={refresh}>{polling ? 'Fetching from arXiv…' : 'Refresh trend data (arXiv)'}</button>
      {trends?.refresh?.error && <p className="text-xs text-rose-600">{trends.refresh.error}</p>}
      {polling && <p className="text-xs text-slate-500">{trends?.refresh?.log?.slice(-1)[0]}</p>}
      <div className="border-t pt-3">
        <div className="label mb-1">What-if: simulate new trend data</div>
        <p className="text-xs text-slate-500 mb-2">Drag to see how faster AI progress in one area changes your forecast.</p>
        {meta.signals.map((s) => (
          <div key={s.id} className="text-xs mb-2">
            <div className="flex justify-between"><span>{s.label}</span><b>{growth(s.id) >= 0 ? '+' : ''}{Math.round(growth(s.id) * 100)}%</b></div>
            <input type="range" min="-0.5" max="3" step="0.1" value={growth(s.id)} className="w-full accent-edge-600"
              onChange={(e) => setOverrides({ ...overrides, [s.id]: +e.target.value })} />
          </div>
        ))}
        {Object.keys(overrides).length > 0 && <button className="text-xs underline" onClick={() => setOverrides({})}>Back to real trend data</button>}
      </div>
    </section>
  )
}
