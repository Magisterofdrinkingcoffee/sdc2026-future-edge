import { useState } from 'react'
import { api } from '../api'

const LEVELS = [
  [0.2, 'Beginner'], [0.5, 'Intermediate'], [0.7, 'Job-ready'], [0.9, 'Expert'],
]
const levelName = (v) => [...LEVELS].reverse().find(([x]) => v >= x - 0.05)?.[1] || 'Beginner'

export default function ProfileStep({ meta, profile, setProfile, setStep, setCompleted, setHistory, setAssessment }) {
  const [busy, setBusy] = useState(false)
  const [note, setNote] = useState(null)
  const [addId, setAddId] = useState('')
  const skillName = Object.fromEntries(meta.skills.map((s) => [s.id, s.name]))

  const pickSample = (p) => {
    setProfile({ name: p.name, skills: p.skills, goal_role: p.goal_role, cv_text: p.cv_text })
    setCompleted([]); setHistory([]); setAssessment(null)
    setNote(`Loaded synthetic profile: ${p.headline}`)
  }

  const extract = async () => {
    setBusy(true)
    try {
      const r = await api.parse(profile.cv_text || '')
      setProfile({ ...profile, skills: { ...r.skills, ...profile.skills } })
      setNote(`Found ${Object.keys(r.skills).length} skills (${r.method}). Adjust each level below.`)
    } catch (e) { setNote(e.message) } finally { setBusy(false) }
  }

  const setLevel = (id, v) => setProfile({ ...profile, skills: { ...profile.skills, [id]: v } })
  const remove = (id) => { const s = { ...profile.skills }; delete s[id]; setProfile({ ...profile, skills: s }) }

  return (
    <div className="grid gap-5 lg:grid-cols-5">
      <section className="card min-w-0 lg:col-span-2 space-y-4">
        <div>
          <div className="label mb-2">Try a sample person (synthetic data)</div>
          <div className="flex flex-col gap-2">
            {meta.profiles.map((p) => (
              <button key={p.id} onClick={() => pickSample(p)} className="btn-ghost justify-start text-left flex-wrap gap-x-1 gap-y-0">
                <span className="font-semibold">{p.name}</span><span className="text-slate-500">– {p.headline}</span>
              </button>
            ))}
          </div>
        </div>
        <div>
          <div className="label mb-2">…or paste a CV / describe yourself</div>
          <textarea className="w-full rounded-lg border border-slate-300 p-3 text-sm h-36"
            placeholder="e.g. Final-year electrical engineering student, power systems coursework, basic Python…"
            value={profile.cv_text} onChange={(e) => setProfile({ ...profile, cv_text: e.target.value })} />
          <p className="text-xs text-slate-500 mt-1">Please don't paste real personal data (name, IC, phone) – this is a demo.</p>
          <button className="btn-primary mt-2" disabled={busy || !profile.cv_text} onClick={extract}>{busy ? 'Reading…' : 'Extract skills'}</button>
        </div>
        {note && <div className="text-sm text-edge-700 bg-edge-50 rounded-lg p-2">{note}</div>}
      </section>

      <section className="card min-w-0 lg:col-span-3 space-y-4">
        <div className="grid sm:grid-cols-2 gap-3">
          <label className="block">
            <span className="label">Name</span>
            <input className="mt-1 w-full rounded-lg border border-slate-300 p-2 text-sm" value={profile.name}
              onChange={(e) => setProfile({ ...profile, name: e.target.value })} placeholder="Your name or a nickname" />
          </label>
          <label className="block">
            <span className="label">Goal role</span>
            <select className="mt-1 w-full rounded-lg border border-slate-300 p-2 text-sm" value={profile.goal_role}
              onChange={(e) => setProfile({ ...profile, goal_role: e.target.value })}>
              <option value="">Let Future Edge suggest</option>
              {meta.roles.map((r) => <option key={r.id} value={r.id}>{r.title} ({r.field})</option>)}
            </select>
          </label>
        </div>

        <div>
          <div className="label mb-2">Your skills ({Object.keys(profile.skills).length})</div>
          {Object.keys(profile.skills).length === 0 && <p className="text-sm text-slate-500">No skills yet – pick a sample, extract from text, or add below.</p>}
          <div className="space-y-2">
            {Object.entries(profile.skills).sort((a, b) => b[1] - a[1]).map(([id, v]) => (
              <div key={id} className="flex items-center gap-3">
                <div className="w-28 sm:w-56 text-sm truncate" title={skillName[id]}>{skillName[id] || id}</div>
                <input type="range" min="0.1" max="1" step="0.1" value={v} onChange={(e) => setLevel(id, +e.target.value)} className="flex-1 accent-edge-600" />
                <div className="w-16 sm:w-24 text-xs text-slate-600">{levelName(v)}</div>
                <button onClick={() => remove(id)} className="text-slate-400 hover:text-rose-600 text-sm" aria-label="remove">✕</button>
              </div>
            ))}
          </div>
          <div className="flex gap-2 mt-3">
            <select className="flex-1 min-w-0 rounded-lg border border-slate-300 p-2 text-sm" value={addId} onChange={(e) => setAddId(e.target.value)}>
              <option value="">Add a skill…</option>
              {meta.skills.filter((s) => !(s.id in profile.skills)).map((s) => <option key={s.id} value={s.id}>{s.name} ({s.category})</option>)}
            </select>
            <button className="btn-ghost" disabled={!addId} onClick={() => { setLevel(addId, 0.5); setAddId('') }}>Add</button>
          </div>
        </div>

        <div className="flex justify-end gap-2 pt-2">
          <button className="btn-ghost" disabled={!Object.keys(profile.skills).length} onClick={() => setStep('forecast')}>Skip to forecast</button>
          <button className="btn-primary" disabled={!Object.keys(profile.skills).length} onClick={() => setStep('assessment')}>Next: Edge Assessment →</button>
        </div>
      </section>
    </div>
  )
}
