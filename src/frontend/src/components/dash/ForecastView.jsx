import { t } from '../../i18n'
import { useEffect, useState } from 'react'
import { api } from '../../api'
import { FIELD_ICON, weather } from '../../game'
import { Bar, CriticalChip, ForecastStrip, GrowthChip, SdgChip } from '../ui'

const GROUPS = [
  { id: 'rising', icon: '🌱', title: 'Growing in value', text: 'Hard for AI and in demand. Lean into these.', bar: 'bg-sprout-500' },
  { id: 'holding', icon: '⚖️', title: 'Holding steady', text: 'AI helps here, but still needs you.', bar: 'bg-sun-500' },
  { id: 'fading', icon: '🍂', title: 'At risk from AI', text: 'AI will be able to do much more of this work by year 3.', bar: 'bg-coral-500' },
]

export default function ForecastView(ctx) {
  const { s, set, meta, forecast, goal } = ctx
  const year3 = new Date().getFullYear() + 3
  const [showAll, setShowAll] = useState(false)

  useEffect(() => {
    const seen = { ...(s.flags.seen || {}), [s.scenario]: true }
    set((p) => ({ flags: { ...p.flags, seen, bothScenarios: !!(seen.fast && seen.moderate) } }))
  }, [s.scenario]) // eslint-disable-line react-hooks/exhaustive-deps

  if (!forecast || !goal) return <p className="text-muted">Loading forecast…</p>
  const cur = forecast[s.scenario]
  const otherSc = s.scenario === 'fast' ? 'moderate' : 'fast'
  const other = forecast[otherSc].roles.find((r) => r.role_id === goal.role_id)
  const rankedAll = [...cur.roles].sort((a, b) => (b.rank_score ?? b.edge_y3) - (a.rank_score ?? a.edge_y3))
  const ranked = showAll ? rankedAll : rankedAll.filter((r, i) => i < 8 || r.role_id === goal.role_id)

  return (
    <div className="space-y-6">
      <section className="panel">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold">{t('Career forecast: {role}', { role: goal.title })}</h1>
            <p className="text-sm text-muted">{t("How hard you'll be to replace by AI, from 0 to 100. Estimates, not a verdict.")}</p>
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

        <RoleFacts role={goal} />

        <details className="mt-4 rounded-2xl bg-canvas p-4">
          <summary className="cursor-pointer font-display font-semibold">{t("How we worked this out")}</summary>
          <ul className="mt-2 space-y-1 text-sm">{Object.values(goal.explain).map((e, i) => <li key={i}>{e}</li>)}</ul>
          {goal.gap.length > 0 && <p className="mt-2 text-sm"><b>Skills gap:</b> {goal.gap.map((g) => g.name).join(', ')}.</p>}
        </details>
      </section>

      <SdgPanel {...ctx} cur={cur} />

      <div className="grid gap-6 lg:grid-cols-[1fr_340px]">
        <section className="panel">
          <h2 className="text-xl font-bold">{t("Your skills over the next 3 years")}</h2>
          <p className="text-sm text-muted">The bar shows how much of each skill AI can do: now (solid) and in {year3} (faded).</p>
          <div className="mt-4 space-y-6">
            {GROUPS.map((g) => {
              const list = cur.skills.filter((k) => k.status === g.id)
              if (!list.length) return null
              return (
                <div key={g.id}>
                  <h3 className="font-display text-lg font-semibold">{g.icon} {t(g.title)}</h3>
                  <p className="text-sm text-muted">{g.text}</p>
                  <ul className="mt-2 space-y-3">
                    {list.map((k) => (
                      <li key={k.skill}>
                        <div className="flex justify-between gap-2 text-sm"><b>{k.name}</b>
                          <span className="shrink-0 text-muted">AI can do {Math.round(k.exposure_now * 100)}% now, {Math.round(k.exposure_y3 * 100)}% in {year3}{k.exposure_y3_range && Math.round(k.exposure_y3_range[1] * 100) > Math.round(k.exposure_y3_range[0] * 100) && <> (range {Math.round(k.exposure_y3_range[0] * 100)}–{Math.round(k.exposure_y3_range[1] * 100)}%)</>}</span></div>
                        <div className="relative mt-1 h-3 overflow-hidden rounded-full bg-line">
                          <div className={`absolute h-3 rounded-full opacity-35 ${g.bar}`} style={{ width: `${k.exposure_y3 * 100}%` }} />
                          <div className={`absolute h-3 rounded-full ${g.bar}`} style={{ width: `${k.exposure_now * 100}%` }} />
                        </div>
                        <div className="mt-0.5 text-xs text-muted">📈 Model 2: {k.signal.label} research {k.signal.growth >= 0 ? '+' : ''}{Math.round((k.signal.growth || 0) * 100)}% expected next year{k.signal.growth_low != null && ` (80% range ${Math.round(k.signal.growth_low * 100)}% to ${Math.round(k.signal.growth_high * 100)}%)`}{k.signal.past_growth != null && `, grew ${Math.round(k.signal.past_growth * 100)}% a year since 2023`}</div>
                        <ModelReading m={k.model} />
                      </li>
                    ))}
                  </ul>
                </div>
              )
            })}
          </div>
          <p className="mt-6 text-xs text-muted">Trend source: {cur.trend_source.source}{cur.trend_source.fetched_at ? `, updated ${new Date(cur.trend_source.fetched_at).toLocaleDateString()}` : ''}. How much AI can do each skill: {cur.exposure_source}.</p>
        </section>

        <aside className="space-y-6">
          <section className="panel">
            <h2 className="text-lg font-bold">{t("Other roles for you")}</h2>
            <p className="text-sm text-muted">Ranked by your {year3} Edge Score{(s.sdgFocus || []).length ? ', with a lift for roles that serve your SDG focus' : ''}.</p>
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
                        <span className="ml-1"><GrowthChip outlook={r.outlook} /></span>
                        {r.sdg_focus_match?.length > 0 && <span className="chip ml-1 bg-sprout-50 text-sprout-700" title={r.explain?.sdg}>🌍 your SDG focus</span>}
                        {r.at_risk && <span className="chip ml-1 bg-coral-50 text-coral-600" title={`AI could do about ${Math.round(r.role_ai_exposure_y3 * 100)}% of this role's work by ${year3}`}>at risk</span>}</span>
                      <span className="font-display text-lg font-bold">{Math.round(r.edge_y3)}</span>
                    </button>
                  </li>
                )
              })}
            </ul>
            {rankedAll.length > ranked.length || showAll ? (
              <button className="mt-3 w-full text-sm font-bold text-violet-600 underline" onClick={() => setShowAll(!showAll)}>
                {showAll ? 'Show top roles only' : `Show all ${rankedAll.length} roles`}
              </button>
            ) : null}
          </section>
          <ModelCard card={cur.model} />
          <TrendModelCard ts={cur.trend_source} />
          <TrendPanel {...ctx} />
        </aside>
      </div>
    </div>
  )
}

function ModelReading({ m }) {
  if (!m) return null
  const words = (m.top_words || []).map((w) => `"${w.term}" (${w.towards === 'AI' ? 'AI' : 'human'})`).join(', ')
  return (
    <details className="mt-1 text-xs text-muted">
      <summary className="cursor-pointer">🧠 Model 1 {m.personal ? 'read your CV sentence' : 'read this skill'}</summary>
      <div className="mt-1 rounded-xl bg-canvas p-2">
        {m.personal && <div>Your sentence: <q className="italic">{m.sentence}</q></div>}
        {!m.personal && <div>Task: <q className="italic">{m.task}</q></div>}
        <div className="mt-1">AI can't speed it up: <b>{Math.round(m.E0 * 100)}%</b> · chatbot alone: <b>{Math.round(m.E1 * 100)}%</b> · AI with tools: <b>{Math.round(m.E2 * 100)}%</b>{m.personal && ' (blended 50/50 with the general skill reading)'}</div>
        {words && <div className="mt-1">Words that mattered most: {words}</div>}
      </div>
    </details>
  )
}

function TrendModelCard({ ts }) {
  const b = ts?.backtest
  if (!b) return null
  return (
    <section className="panel">
      <h2 className="text-lg font-bold">📈 Model 2: AI-trend forecaster</h2>
      <p className="mt-1 text-sm text-muted">Fits a growth trend to 36 months of new arXiv papers (Oct 2023 – Sep 2026) per AI area and projects it ahead with an 80% range. The trend fades over time (a damped trend), because AI research boomed in 2023–24 and is now slowing. That range is part of your Edge Score range.</p>
      <div className="mt-3 grid grid-cols-2 gap-2 text-center">
        <div className="rounded-2xl bg-violet-50 p-2"><div className="font-display text-2xl font-bold text-violet-700">{Math.round(b.model_mean_error * 100)}%</div><div className="text-xs text-muted">average error</div></div>
        <div className="rounded-2xl bg-canvas p-2"><div className="font-display text-2xl font-bold">{Math.round(b.naive_mean_error * 100)}%</div><div className="text-xs text-muted">"same as last year"</div></div>
      </div>
      <p className="mt-2 text-xs text-muted">Backtest: trained on the first 24 months, predicted the last 12. Better than the simple guess on {b.model_better_on} of {b.signals} AI areas; the real result fell inside the 80% range for {b.inside_80pct_band} of {b.signals}.</p>
    </section>
  )
}

function ModelCard({ card }) {
  const [text, setText] = useState('')
  const [res, setRes] = useState(null)
  if (!card) return null
  const ask = async () => setRes(await api.modelExposure(text))
  return (
    <section className="panel">
      <h2 className="text-lg font-bold">🧠 Model 1: AI-exposure model</h2>
      <p className="mt-1 text-sm text-muted">Trained on {card.n_tasks.toLocaleString()} real job tasks that people rated for how much AI can do them. Tested only on {card.n_occupations} occupations it never saw in training.</p>
      <div className="mt-3 grid grid-cols-2 gap-2 text-center">
        <div className="rounded-2xl bg-violet-50 p-2"><div className="font-display text-2xl font-bold text-violet-700">{Math.round(card.accuracy * 100)}%</div><div className="text-xs text-muted">accuracy</div></div>
        <div className="rounded-2xl bg-canvas p-2"><div className="font-display text-2xl font-bold">{Math.round(card.baseline_accuracy * 100)}%</div><div className="text-xs text-muted">simple guess</div></div>
      </div>
      <p className="mt-2 text-xs text-muted">Best at spotting work AI can't do ({Math.round(card.recall_per_class.E0 * 100)}% right), weakest at "chatbot alone" tasks ({Math.round(card.recall_per_class.E1 * 100)}%). Data: {card.data}.</p>
      <details className="mt-3">
        <summary className="cursor-pointer text-sm font-bold">Try the model on any task</summary>
        <textarea rows={2} value={text} onChange={(e) => setText(e.target.value)} placeholder="e.g. Repair hydraulic presses on the factory floor"
          className="mt-2 w-full rounded-xl border-2 border-line p-2 text-sm focus:border-violet-500 focus:outline-none" />
        <button className="btn-white mt-2 w-full py-2 text-sm" disabled={text.trim().length < 5} onClick={ask}>Ask Model 1</button>
        {res && (
          <div className="mt-2 rounded-xl bg-canvas p-2 text-xs">
            AI can't speed it up <b>{Math.round(res.E0 * 100)}%</b> · chatbot alone <b>{Math.round(res.E1 * 100)}%</b> · AI with tools <b>{Math.round(res.E2 * 100)}%</b>
            <div className="mt-1 text-muted">Words that mattered: {res.top_words.map((w) => `"${w.term}" → ${w.towards}`).join(', ') || 'none it knows'}</div>
          </div>
        )}
      </details>
    </section>
  )
}

function RoleFacts({ role }) {
  const o = role.outlook || {}
  const g = o.malaysia_net_growth_2030 ?? o.net_growth_2030
  return (
    <div className="mt-5 grid gap-3 sm:grid-cols-3">
      <div className="rounded-2xl border-2 border-line p-4">
        <div className="text-sm font-bold text-muted">{t("Job demand by 2030")}</div>
        <div className={`font-display text-2xl font-bold ${g > 0 || o.direction === 'growing' ? 'text-sprout-600' : g < 0 || o.direction === 'declining' ? 'text-coral-600' : ''}`}>
          {g != null ? `${g > 0 ? '+' : ''}${g}%` : o.direction ? (o.direction === 'growing' ? 'Growing fast' : 'Declining fast') : 'No data'}
        </div>
        <div className="text-xs text-muted">{o.wef_role ? `${o.wef_role}${o.malaysia_net_growth_2030 != null ? ', Malaysia' : ', worldwide'}. ${o.malaysia_source || o.source}` : o.note}</div>
      </div>
      <div className="rounded-2xl border-2 border-line p-4">
        <div className="text-sm font-bold text-muted">{t("Typical pay")}</div>
        <div className="font-display text-2xl font-bold">RM {role.wage?.median_myr.toLocaleString()}</div>
        <div className="text-xs text-muted">Median monthly wage, {role.wage?.group}. {role.wage?.source}</div>
      </div>
      <div className="rounded-2xl border-2 border-line p-4">
        <div className="text-sm font-bold text-muted">{t("Malaysia's critical jobs list")}</div>
        <div className="font-display text-2xl font-bold">{role.mycol?.critical ? '🇲🇾 Yes' : 'Not listed'}</div>
        <div className="text-xs text-muted">{role.mycol?.critical ? `MASCO ${role.mycol.masco}, ${role.mycol.name}. ${role.mycol.source}` : 'TalentCorp MyCOL 2024/2025'}</div>
      </div>
      {role.description && <p className="text-sm text-muted sm:col-span-3">{role.description}{role.ai_tools?.length ? ` AI tools you'll work with: ${role.ai_tools.join(', ')}.` : ''}</p>}
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
      <button className="btn-white mt-3 w-full py-2 text-sm" disabled={busy} onClick={refresh}>{busy ? 'Fetching 36 months from arXiv (about 20 min)…' : 'Refresh trend data'}</button>
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


function SdgPanel({ s, set, meta, plan, goal, cur }) {
  const themes = meta.sdg_themes || {}
  const focus = s.sdgFocus || []
  const toggle = (t) => set((p) => {
    const f = p.sdgFocus || []
    return { sdgFocus: f.includes(t) ? f.filter((x) => x !== t) : [...f, t], flags: { ...p.flags, sdg: true } }
  })
  const sum = plan?.sdg_summary
  const best = focus.length
    ? [...cur.roles].filter((r) => r.sdg_focus_match?.length).sort((a, b) => b.edge_y3 - a.edge_y3).slice(0, 4)
    : []
  return (
    <section className="panel">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-xl font-bold">{t("\ud83c\udf0d Your path and the Sustainable Development Goals")}</h2>
          <p className="text-sm text-muted">What your work as a {goal.title} would help the world with – and roles that serve the goals you care about.</p>
        </div>
      </div>
      {goal.sdg_impact && <p className="mt-3 rounded-2xl bg-sprout-50 p-3 text-sm text-sprout-700"><b>{t("Why it matters:")}</b> {goal.sdg_impact}</p>}

      {sum && sum.targets.length > 0 && (
        <div className="mt-4">
          <h3 className="font-display font-semibold">Your path contributes to {sum.goals.length} SDG{sum.goals.length > 1 ? 's' : ''}</h3>
          <ul className="mt-2 grid gap-2 sm:grid-cols-2">
            {sum.targets.map((t) => (
              <li key={t.target} className="rounded-2xl border-2 border-line p-3 text-sm">
                <div className="font-bold">SDG {t.target} · {sum.goal_names[t.goal]}</div>
                <div className="text-xs text-muted">{t.text}</div>
                <div className="mt-1 text-xs">Because of {t.sources.slice(0, 3).join('; ')}{t.sources.length > 3 ? ` and ${t.sources.length - 3} more` : ''}.</div>
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="mt-5">
        <h3 className="font-display font-semibold">{t("What do you want your work to help with?")}</h3>
        <p className="text-xs text-muted">{t("Pick any. Roles that serve these goals move up your list and are shown below. Your Edge Score itself never changes \u2013 it only measures how hard you are to replace.")}</p>
        <div className="mt-2 flex flex-wrap gap-2" role="group" aria-label="SDG focus">
          {Object.entries(themes).map(([id, th]) => (
            <button key={id} aria-pressed={focus.includes(id)} onClick={() => toggle(id)}
              className={`rounded-full border-2 px-3 py-1.5 text-sm font-bold ${focus.includes(id) ? 'border-sprout-500 bg-sprout-50 text-sprout-700' : 'border-line text-muted'}`}>
              {th.icon} {th.label}
            </button>
          ))}
        </div>
        {focus.length > 0 && (
          <div className="mt-3">
            {best.length ? (
              <ul className="grid gap-2 sm:grid-cols-2">
                {best.map((r) => (
                  <li key={r.role_id} className="rounded-2xl bg-canvas p-3 text-sm">
                    <div className="flex justify-between gap-2"><b>{r.title}</b><span className="font-display font-bold">{Math.round(r.edge_y3)}</span></div>
                    <div className="text-xs text-muted">{Math.round(r.match * 100)}% skill match · {r.sdg_focus_match.map((t) => themes[t]?.icon + ' ' + themes[t]?.label).join(', ')}</div>
                    {r.sdg_impact && <div className="mt-1 text-xs">{r.sdg_impact}</div>}
                    {r.role_id !== goal.role_id && (
                      <button className="mt-2 text-xs font-bold text-violet-600 underline"
                        onClick={() => window.confirm(`Make ${r.title} your new goal? Your quest map will change.`) && set((p) => ({ profile: { ...p.profile, goal_role: r.role_id }, completed: [], history: [] }))}>
                        Make this my goal
                      </button>
                    )}
                  </li>
                ))}
              </ul>
            ) : <p className="text-sm text-muted">No roles in our catalog serve this goal yet.</p>}
          </div>
        )}
      </div>
    </section>
  )
}
