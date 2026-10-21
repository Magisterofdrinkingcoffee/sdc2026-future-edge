import { useEffect, useState } from 'react'
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { api } from '../api'
import { EstimateNote, SdgBadge, TypeChip } from './ui'

export default function PathwayStep({ meta, profile, body, completed, setCompleted, history, setHistory, setStep }) {
  const [plan, setPlan] = useState(null)
  const [edgeNow, setEdgeNow] = useState(null)
  const [hours, setHours] = useState(6)
  const roleId = profile.goal_role

  const key = JSON.stringify({ body, hours })
  useEffect(() => {
    if (!roleId || !Object.keys(profile.skills).length) return
    // the plan is computed from the ORIGINAL profile so finished steps stay visible as ticked
    api.pathway({ ...body, completed: [], role_id: roleId, hours_per_week: hours }).then(setPlan)
    api.forecast(body).then((f) => {
      const r = f.roles.find((x) => x.role_id === roleId)
      setEdgeNow(r)
      if (!history.length) setHistory([{ step: 'Start', edge: r.edge_y3 }])
    })
  }, [key]) // eslint-disable-line react-hooks/exhaustive-deps

  if (!roleId) return <div className="card">Pick a goal role on the forecast page first. <button className="underline" onClick={() => setStep('forecast')}>Go to forecast</button></div>
  if (!plan || !edgeNow) return <div className="text-slate-500">Building your pathway…</div>

  const toggle = async (item) => {
    const next = completed.includes(item.id) ? completed.filter((c) => c !== item.id) : [...completed, item.id]
    setCompleted(next)
    const f = await api.forecast({ ...body, completed: next })
    const r = f.roles.find((x) => x.role_id === roleId)
    setHistory([...history, { step: completed.includes(item.id) ? `Undo: ${item.title.slice(0, 18)}` : item.title.slice(0, 22), edge: r.edge_y3 }])
  }

  const doneCount = plan.steps.filter((s) => completed.includes(s.id)).length

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold">Your pathway to {plan.role_title}</h2>
          <p className="text-sm text-slate-600">Courses give knowledge, projects give proof, experiences build the personal skills AI can't copy.</p>
        </div>
        <label className="text-sm">Hours per week:{' '}
          <select value={hours} onChange={(e) => setHours(+e.target.value)} className="rounded border border-slate-300 p-1">
            {[3, 6, 10, 15].map((h) => <option key={h}>{h}</option>)}
          </select>
        </label>
      </div>

      {plan.one_move && (
        <section className="card border-2 border-edge-500 bg-edge-50">
          <div className="label text-edge-700">Your One Move</div>
          <div className="text-xl font-bold mt-1">Improve {plan.one_move.name}</div>
          <p className="text-sm text-slate-700 mt-1">{plan.one_move.explain}</p>
          <div className="mt-2"><EstimateNote>{plan.scenario === 'fast' ? 'fast AI disruption' : 'moderate AI disruption'}</EstimateNote></div>
        </section>
      )}

      <div className="grid gap-5 lg:grid-cols-3">
        <section className="card lg:col-span-2">
          <div className="flex justify-between items-center mb-3">
            <div className="label">Steps ({doneCount}/{plan.steps.length} done)</div>
            <div className="text-xs text-slate-500">≈ {plan.total_hours} h · {plan.total_weeks} weeks at {plan.hours_per_week} h/week</div>
          </div>
          <ol className="space-y-3">
            {plan.steps.map((s, i) => {
              const done = completed.includes(s.id)
              return (
                <li key={s.id} className={`rounded-xl border p-3 ${done ? 'bg-emerald-50 border-emerald-200' : 'border-slate-200'}`}>
                  <div className="flex gap-3">
                    <input type="checkbox" checked={done} onChange={() => toggle(s)} className="mt-1 h-5 w-5 accent-emerald-600" aria-label="mark done" />
                    <div className="flex-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="text-slate-400 text-sm">{i + 1}.</span>
                        <TypeChip type={s.type} />
                        <span className="text-xs text-slate-500">≈ {s.hours} h · {s.weeks} wk · {s.cost}</span>
                      </div>
                      <div className={`font-medium mt-1 ${done ? 'line-through text-slate-500' : ''}`}>{s.title}</div>
                      <div className="text-xs text-slate-600">Builds <b>{s.target_skill_name}</b> (+{s.edge_gain} Edge) · Source: {s.url ? <a className="underline text-edge-700" href={s.url} target="_blank" rel="noreferrer">{s.provider}</a> : s.provider}{!s.verified && <span className="text-amber-600"> · link not yet verified</span>}</div>
                      <div className="flex flex-wrap gap-1 mt-2">{s.sdgs.map((t) => <SdgBadge key={t} target={t} sdgs={meta.sdgs} />)}</div>
                    </div>
                  </div>
                </li>
              )
            })}
          </ol>
        </section>

        <section className="card h-fit">
          <div className="label">Progress · your {new Date().getFullYear() + 3} Edge Score</div>
          <div className="text-4xl font-bold mt-1">{Math.round(history.at(-1)?.edge ?? edgeNow.edge_y3)}</div>
          <div className="text-sm text-slate-500">started at {Math.round(history[0]?.edge ?? edgeNow.edge_y3)}</div>
          <div className="h-44 mt-3">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={history.map((h, i) => ({ ...h, n: i }))} margin={{ left: -25, right: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="n" fontSize={11} tickFormatter={(n) => (n === 0 ? 'start' : `#${n}`)} />
                <YAxis domain={[0, 100]} fontSize={11} />
                <Tooltip formatter={(v) => [Math.round(v), 'Edge']} labelFormatter={(n) => history[n]?.step} />
                <Area type="monotone" dataKey="edge" stroke="#059669" fill="#a7f3d0" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
          <p className="text-xs text-slate-500 mt-2">Tick a step when you finish it – your forecast updates. Your progress is saved in this browser.</p>
        </section>
      </div>
    </div>
  )
}
