import { useEffect, useState } from 'react'
import { api } from '../../api'
import { Logo } from '../ui'

const cellColor = (v) => v >= 0.7 ? 'bg-sprout-500 text-white' : v >= 0.5 ? 'bg-sprout-100 text-sprout-700' : v >= 0.3 ? 'bg-sun-100 text-sun-600' : 'bg-coral-50 text-coral-600'
const LEVEL = (v) => v >= 0.7 ? 'Strong' : v >= 0.5 ? 'Good' : v >= 0.3 ? 'Some' : 'Gap'

export default function TeamView({ set, meta }) {
  const [members, setMembers] = useState([])
  const [role, setRole] = useState('data_analyst')
  const [scenario, setScenario] = useState('fast')
  const [rep, setRep] = useState(null)
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState(null)

  const toSkills = (res) => Object.fromEntries(Object.entries(res.skills).map(([k, v]) => [k, v.level]))
  const loadSample = async () => {
    setBusy(true); setErr(null)
    try {
      const out = []
      for (const p of meta.profiles) out.push({ name: `${p.name} (${p.headline})`, skills: toSkills(await api.uploadSample(p.id)) })
      setMembers(out)
    } catch (e) { setErr(e.message) } finally { setBusy(false) }
  }
  const addCvs = async (files) => {
    setBusy(true); setErr(null)
    try {
      const out = [...members]
      for (const f of files) out.push({ name: `Employee ${out.length + 1}`, skills: toSkills(await api.uploadCv(f)) })
      setMembers(out)
    } catch (e) { setErr(e.message) } finally { setBusy(false) }
  }

  useEffect(() => {
    if (!members.length) { setRep(null); return }
    api.team({ members, role_id: role, scenario }).then(setRep).catch((e) => setErr(e.message))
  }, [JSON.stringify(members), role, scenario]) // eslint-disable-line react-hooks/exhaustive-deps

  const roleTitle = (id) => meta.roles.find((r) => r.id === id)?.title
  return (
    <div className="min-h-screen">
      <header className="mx-auto flex max-w-6xl items-center justify-between px-4 py-6">
        <Logo />
        <button className="btn-white py-2 text-sm" onClick={() => set({ stage: 'welcome' })}>‹ Back</button>
      </header>
      <main className="mx-auto max-w-6xl space-y-6 px-4 pb-16">
        <section className="panel">
          <h1 className="text-3xl font-bold">🏢 Team view for HR &amp; L&amp;D</h1>
          <p className="mt-1 text-muted">See your team's skills against a future role, find the shared gaps, and get one reskilling plan for everyone. CVs are read once and not stored; names you upload are replaced with "Employee 1, 2…".</p>
          <div className="mt-4 flex flex-wrap items-center gap-3">
            <button className="btn-violet px-5 py-2" disabled={busy} onClick={loadSample}>{busy ? 'Reading CVs…' : `Load the sample team (${meta.profiles.length} made-up people)`}</button>
            <label className="btn-white cursor-pointer px-5 py-2">
              + Add CVs
              <input type="file" multiple accept=".pdf,.docx,.txt,.png,.jpg,.jpeg" className="hidden" onChange={(e) => addCvs([...e.target.files])} />
            </label>
            {members.length > 0 && <button className="text-sm font-bold text-muted underline" onClick={() => setMembers([])}>Clear team</button>}
          </div>
          {err && <p className="mt-2 text-sm text-coral-600">{err}</p>}
          <div className="mt-4 flex flex-wrap items-center gap-3">
            <label className="text-sm font-bold">Future role to train for:
              <select value={role} onChange={(e) => setRole(e.target.value)} className="ml-2 rounded-xl border-2 border-line px-3 py-1.5">
                {[...meta.roles].sort((a, b) => a.title.localeCompare(b.title)).map((r) => <option key={r.id} value={r.id}>{r.title}</option>)}
              </select>
            </label>
            <div className="flex rounded-2xl border-2 border-line p-1">
              {Object.entries(meta.scenarios).map(([id, sc]) => (
                <button key={id} onClick={() => setScenario(id)} className={`rounded-xl px-3 py-1 text-sm font-bold ${scenario === id ? 'bg-violet-500 text-white' : 'text-muted'}`}>{id === 'fast' ? '🚀' : '🐢'} {sc.label}</button>
              ))}
            </div>
          </div>
        </section>

        {rep && (
          <>
            <section className="grid gap-3 sm:grid-cols-3">
              <div className="panel"><div className="text-sm font-bold text-muted">Team average Edge Score (2029)</div><div className="font-display text-4xl font-bold">{Math.round(rep.team_edge_y3)}</div><div className="text-xs text-muted">as {rep.role_title}, {meta.scenarios[rep.scenario].label}</div></div>
              <div className="panel"><div className="text-sm font-bold text-muted">Ready now (≥60% skill match)</div><div className="font-display text-4xl font-bold">{rep.ready} / {rep.members.length}</div></div>
              <div className="panel"><div className="text-sm font-bold text-muted">Team training plan</div><div className="font-display text-4xl font-bold">{rep.plan_hours} h</div><div className="text-xs text-muted">{rep.gaps.length} shared skill gaps, free or low-cost courses</div></div>
            </section>

            <section className="panel overflow-x-auto">
              <h2 className="text-xl font-bold">Skills heatmap: team vs {rep.role_title}</h2>
              <p className="text-sm text-muted">Columns are the role's skills, most important first (★ = importance). Colour = each person's level.</p>
              <table className="mt-3 w-full min-w-[720px] border-separate border-spacing-1 text-sm">
                <thead>
                  <tr>
                    <th className="text-left">Person</th>
                    {rep.columns.map((c) => <th key={c.skill} className="px-1 align-bottom text-xs font-bold"><div>{c.name}</div><div className="text-sun-500">{'★'.repeat(c.weight)}</div></th>)}
                    <th className="text-xs">Edge 2029</th>
                    <th className="text-left text-xs">Best future role for them</th>
                  </tr>
                </thead>
                <tbody>
                  {rep.members.map((m) => (
                    <tr key={m.name}>
                      <td className="max-w-[220px] pr-2 text-xs font-bold">{m.name}</td>
                      {rep.columns.map((c) => (
                        <td key={c.skill} title={`${m.levels[c.skill]}`} className={`rounded-lg text-center text-xs font-bold ${cellColor(m.levels[c.skill])}`}>{LEVEL(m.levels[c.skill])}</td>
                      ))}
                      <td className="text-center font-display font-bold">{Math.round(m.edge_y3)}</td>
                      <td className="text-xs">{m.best_role.title} ({Math.round(m.best_role.edge_y3)})</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </section>

            <div className="grid gap-6 lg:grid-cols-[1fr_360px]">
              <section className="panel">
                <h2 className="text-xl font-bold">One reskilling plan for the team</h2>
                <p className="text-sm text-muted">Gaps sorted by how important the skill is for {rep.role_title}. One course covers everyone who needs it.</p>
                <ol className="mt-3 space-y-3">
                  {rep.gaps.map((g, i) => (
                    <li key={g.skill} className="rounded-2xl border-2 border-line p-3 text-sm">
                      <div className="flex justify-between gap-2"><b>{i + 1}. {g.name} <span className="text-sun-500">{'★'.repeat(g.weight)}</span></b><span className="text-muted">team avg {Math.round(g.team_avg * 100)}%</span></div>
                      <div className="text-xs text-muted">Needed by: {g.people.join(', ')}</div>
                      {g.course && <div className="mt-1">📘 {g.course.url ? <a className="underline" href={g.course.url} target="_blank" rel="noreferrer">{g.course.title}</a> : g.course.title} – {g.course.provider}, {g.course.hours} h each, {g.course.cost}. <b>{g.team_hours} h</b> for the team.</div>}
                    </li>
                  ))}
                </ol>
              </section>
              <aside className="space-y-6">
                <section className="panel">
                  <h2 className="text-lg font-bold">🌍 Team SDG contribution</h2>
                  <p className="text-sm text-muted">SDG targets your team would serve in {rep.role_title} and in each person's best future role (number = people).</p>
                  <ul className="mt-2 space-y-2">
                    {rep.sdg_contribution.slice(0, 8).map((e) => (
                      <li key={e.target} className="flex gap-2 text-sm"><span className="chip bg-sprout-50 text-sprout-700">SDG {e.target}</span><span className="flex-1 text-xs text-muted">{e.text}</span><b>{e.count}</b></li>
                    ))}
                  </ul>
                </section>
                <section className="panel text-sm text-muted">⚖️ {rep.note} The same fairness check as the personal view applies: names, gender, age, race and religion are removed before matching.</section>
              </aside>
            </div>
          </>
        )}
        {!rep && <p className="text-center text-muted">Load the sample team or add CVs to see the heatmap. Target role: {roleTitle(role)}.</p>}
      </main>
    </div>
  )
}
