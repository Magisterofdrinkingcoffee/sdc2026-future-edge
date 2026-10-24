import { useRef, useState } from 'react'
import { api } from '../../api'
import { XP } from '../../game'
import { WizardFrame } from '../ui'

const LEVELS = [[0.3, 'Basic'], [0.5, 'Some'], [0.7, 'Good'], [0.9, 'Strong']]
const nearest = (v) => LEVELS.reduce((a, b) => (Math.abs(b[0] - v) < Math.abs(a[0] - v) ? b : a))[0]

export default function CvStep({ s, set, meta, award }) {
  const [phase, setPhase] = useState(Object.keys(s.profile.skills).length ? 'review' : 'choose')
  const [reading, setReading] = useState('')
  const [err, setErr] = useState(null)
  const [paste, setPaste] = useState(false)
  const [text, setText] = useState('')
  const [drag, setDrag] = useState(false)
  const [addId, setAddId] = useState('')
  const fileRef = useRef()

  const apply = (res, extra) => {
    const skills = Object.fromEntries(Object.entries(res.skills).map(([k, v]) => [k, nearest(v.level)]))
    set((p) => ({
      profile: { ...p.profile, ...extra, skills, evidence: res.skills, source: res.source, reader: res.reader || null, fairness: res.fairness || null },
      completed: [], history: [],
    }))
    award('cv', XP.cv, 'CV added')
    setPhase('review')
  }

  const run = async (label, fn, extra = {}) => {
    setErr(null); setReading(label); setPhase('reading')
    try {
      const [res] = await Promise.all([fn(), new Promise((r) => setTimeout(r, 900))])
      if (!Object.keys(res.skills).length) throw new Error("We couldn't find any skills we know in this CV. Try pasting the text, or add skills by hand.")
      apply(res, extra)
    } catch (e) { setErr(e.message); setPhase('choose') }
  }

  const onFile = (f) => {
    if (!f) return
    if (!/\.(pdf|docx|txt|png|jpe?g|webp|heic)$/i.test(f.name)) { setErr('Please choose a PDF, Word (.docx), photo or .txt file.'); return }
    run(`Reading ${f.name}`, () => api.uploadCv(f), { name: s.profile.name, avatar: '🙂', goal_role: '', sampleId: null })
  }

  const skillMeta = Object.fromEntries(meta.skills.map((m) => [m.id, m]))
  const setLevel = (id, v) => set((p) => ({ profile: { ...p.profile, skills: { ...p.profile.skills, [id]: v } } }))
  const remove = (id) => set((p) => { const sk = { ...p.profile.skills }; delete sk[id]; return { profile: { ...p.profile, skills: sk } } })

  return (
    <WizardFrame step={1} total={4} onBack={() => set({ stage: 'welcome' })}>
      {phase === 'reading' && (
        <div className="grid place-items-center py-24 text-center">
          <div className="animate-bob text-6xl" aria-hidden>📄</div>
          <h2 className="mt-6 text-2xl font-bold">{reading}…</h2>
          <p className="mt-2 text-muted">Looking for skills and the sentences that prove them.</p>
        </div>
      )}

      {phase === 'choose' && (
        <>
          <h1 className="text-3xl font-bold">Start with your CV</h1>
          <p className="mt-2 text-muted">We read it once to find your skills, then throw it away. Your name, email, phone, IC number, age and gender are removed before matching.</p>

          {err && <div role="alert" className="mt-4 rounded-2xl border-2 border-coral-500 bg-coral-50 p-3 text-sm text-coral-600">{err}</div>}

          {!paste ? (
            <button
              onClick={() => fileRef.current.click()}
              onDragOver={(e) => { e.preventDefault(); setDrag(true) }} onDragLeave={() => setDrag(false)}
              onDrop={(e) => { e.preventDefault(); setDrag(false); onFile(e.dataTransfer.files[0]) }}
              className={`mt-6 grid w-full place-items-center rounded-3xl border-2 border-dashed px-6 py-10 text-center transition-colors ${drag ? 'border-violet-500 bg-violet-50' : 'border-line bg-white hover:border-violet-300'}`}>
              <span className="text-5xl" aria-hidden>📤</span>
              <span className="mt-3 font-display text-xl font-semibold">Drop your CV here</span>
              <span className="text-sm text-muted">PDF, Word, photo or .txt, max 5 MB. Click to choose a file.</span>
            </button>
          ) : (
            <div className="mt-6">
              <textarea value={text} onChange={(e) => setText(e.target.value)} rows={7}
                className="w-full rounded-2xl border-2 border-line p-4 focus:border-violet-500 focus:outline-none"
                placeholder="Paste your CV text, or describe your studies, work and projects…" />
              <button className="btn-violet mt-3" disabled={text.trim().length < 20}
                onClick={() => run('Reading your text', () => api.parseText(text), { goal_role: '', sampleId: null })}>Find my skills</button>
            </div>
          )}
          <input ref={fileRef} type="file" accept=".pdf,.docx,.txt,.png,.jpg,.jpeg,.webp,.heic,application/pdf,image/*" className="hidden" onChange={(e) => onFile(e.target.files[0])} />
          <button className="mt-3 text-sm font-bold text-violet-600 underline" onClick={() => setPaste(!paste)}>
            {paste ? 'Upload a file instead' : 'Prefer to paste text instead?'}
          </button>

          <h2 className="mt-10 text-xl font-bold">Or try a sample person</h2>
          <p className="text-sm text-muted">Made-up people with made-up CVs. Their PDF goes through the same reader as yours.</p>
          <div className="mt-4 grid gap-3 sm:grid-cols-3">
            {meta.profiles.map((p) => (
              <div key={p.id} className="flex flex-col rounded-3xl border-2 border-line bg-white p-4">
                <div className="text-4xl" aria-hidden>{p.avatar}</div>
                <div className="mt-2 font-display text-lg font-semibold">{p.name}</div>
                <div className="flex-1 text-sm text-muted">{p.headline}</div>
                <button className="btn-violet mt-3 py-2 text-sm"
                  onClick={() => run(`Reading ${p.name.split(' ')[0]}'s CV`, () => api.uploadSample(p.id), { name: p.name, avatar: p.avatar, goal_role: p.goal_role, sampleId: p.id })}>
                  Use this CV
                </button>
                <a className="mt-2 text-center text-sm font-bold text-violet-600 underline" href={api.sampleCvUrl(p.id)} target="_blank" rel="noreferrer">View PDF</a>
              </div>
            ))}
          </div>
        </>
      )}

      {phase === 'review' && (
        <>
          <h1 className="text-3xl font-bold">We found {Object.keys(s.profile.skills).length} skills</h1>
          <p className="mt-2 text-muted">From <b>{s.profile.source || 'your profile'}</b>. Check each level. We guessed it from how you described it.</p>
          {s.profile.reader && (
            <div className="mt-3 rounded-2xl bg-sprout-50 p-3 text-sm text-sprout-700">
              🔒 {s.profile.reader.removed_personal_data.length
                ? `Removed before matching: ${s.profile.reader.removed_personal_data.map((x) => ({ name: 'name', email: 'email', phone: 'phone', ic_number: 'IC number', age_dob: 'age / date of birth', gender: 'gender', marital: 'marital status', race_religion: 'race / religion' }[x] || x)).join(', ')}.`
                : 'No personal data found to remove.'}
              {' '}Read with {s.profile.reader.method.startsWith('gemini') ? 'Gemini, and every phrase was checked against your CV' : 'our offline reader'}.
              {s.profile.reader.rejected_phrases > 0 && ` ${s.profile.reader.rejected_phrases} phrase(s) the AI suggested were not in your CV and were dropped.`}
              {s.profile.reader.warnings.map((w, i) => <div key={i} className="mt-1 text-sun-600">{w}</div>)}
            </div>
          )}
          {s.profile.fairness && (
            <div className={`mt-2 rounded-2xl p-3 text-sm ${s.profile.fairness.passed ? 'bg-violet-50 text-violet-700' : 'bg-coral-50 text-coral-600'}`}>
              ⚖️ <b>Fairness check {s.profile.fairness.passed ? 'passed' : 'failed'}:</b> {s.profile.fairness.note}
              {' '}Tested: {s.profile.fairness.attributes.join(', ')}.
            </div>
          )}

          <label className="mt-6 block">
            <span className="text-sm font-bold">What should we call you?</span>
            <input value={s.profile.name} onChange={(e) => set((p) => ({ profile: { ...p.profile, name: e.target.value } }))}
              className="mt-1 w-full rounded-2xl border-2 border-line px-4 py-3 focus:border-violet-500 focus:outline-none" placeholder="Name or nickname" />
          </label>

          <ul className="mt-6 space-y-3">
            {Object.entries(s.profile.skills).sort((a, b) => b[1] - a[1]).map(([id, v]) => {
              const ev = s.profile.evidence?.[id]
              return (
                <li key={id} className="rounded-3xl border-2 border-line bg-white p-4">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <div className="font-display text-lg font-semibold">{skillMeta[id]?.name}</div>
                      {ev ? <q className="text-sm italic text-muted">{ev.evidence}</q> : <span className="text-sm text-muted">Added by you</span>}
                    </div>
                    <button onClick={() => remove(id)} aria-label={`Remove ${skillMeta[id]?.name}`} className="text-xl text-muted hover:text-coral-600">×</button>
                  </div>
                  <div className="mt-3 grid grid-cols-4 gap-2" role="radiogroup" aria-label="Level">
                    {LEVELS.map(([lv, name]) => (
                      <button key={lv} role="radio" aria-checked={v === lv} onClick={() => setLevel(id, lv)}
                        className={`rounded-xl border-2 border-b-4 py-1.5 text-sm font-bold ${v === lv ? 'border-violet-500 bg-violet-50 text-violet-700' : 'border-line text-muted hover:bg-canvas'}`}>{name}</button>
                    ))}
                  </div>
                </li>
              )
            })}
          </ul>

          <div className="mt-4 flex gap-2">
            <select value={addId} onChange={(e) => setAddId(e.target.value)} className="min-w-0 flex-1 rounded-2xl border-2 border-line bg-white px-3 py-2">
              <option value="">Missing a skill? Add it…</option>
              {meta.skills.filter((m) => !(m.id in s.profile.skills)).map((m) => <option key={m.id} value={m.id}>{m.name}</option>)}
            </select>
            <button className="btn-white py-2" disabled={!addId} onClick={() => { setLevel(addId, 0.5); setAddId('') }}>Add</button>
          </div>

          <div className="mt-8 flex flex-wrap justify-between gap-3">
            <button className="btn-white" onClick={() => setPhase('choose')}>Use a different CV</button>
            <button className="btn-green px-8" disabled={!Object.keys(s.profile.skills).length} onClick={() => set({ stage: 'goal' })}>Looks right</button>
          </div>
        </>
      )}
    </WizardFrame>
  )
}
