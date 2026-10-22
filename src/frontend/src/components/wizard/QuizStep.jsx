import { useEffect, useState } from 'react'
import { api } from '../../api'
import { XP } from '../../game'
import { Bar, celebrate, WizardFrame } from '../ui'

const IT_SKILLS = ['python', 'basic_coding', 'web_dev', 'sql', 'ml', 'deep_learning', 'llm_apps', 'mlops', 'cloud', 'cybersecurity', 'networking', 'data_engineering']
const ENG_SKILLS = ['power_systems', 'renewable_energy', 'circuit_design', 'electrical_maintenance', 'plc', 'embedded', 'iot', 'mechanical_maintenance', 'cad', 'structural_design', 'ev_battery', 'ohs']

// Model 3: "Catch the AI". The user reviews AI-written work with planted mistakes.
export default function QuizStep({ s, set, meta, award }) {
  const [stage, setStage] = useState('intro') // intro | review | confidence | action | situations | result
  const [pack, setPack] = useState(null)
  const [flagged, setFlagged] = useState([])
  const [confidence, setConfidence] = useState(70)
  const [action, setAction] = useState(null)
  const [answers, setAnswers] = useState({})
  const [result, setResult] = useState(null)
  const [err, setErr] = useState(null)

  useEffect(() => {
    const goal = meta.roles.find((r) => r.id === s.profile.goal_role)
    const sk = Object.keys(s.profile.skills)
    const params = goal ? { sector: goal.field }
      : { pack: sk.some((x) => IT_SKILLS.includes(x)) ? 'it' : sk.some((x) => ENG_SKILLS.includes(x)) ? 'engineering' : 'business' }
    api.catchPack(params).then(setPack).catch((e) => setErr(e.message))
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const toggle = (i) => setFlagged((f) => (f.includes(i) ? f.filter((x) => x !== i) : [...f, i]))
  const submit = async () => {
    const r = await api.scoreCatch({ pack: pack.pack, flagged, confidence, action, answers })
    setResult(r)
    set({ assessment: r })
    award('quiz', XP.quiz, 'Edge Check finished')
    if (r.details.all_found) celebrate()
    setStage('result')
  }

  const back = {
    intro: () => set({ stage: 'goal' }), review: () => setStage('intro'), confidence: () => setStage('review'),
    action: () => setStage('confidence'), situations: () => setStage('action'), result: () => setStage('situations'),
  }[stage]

  if (err) return <WizardFrame step={3} total={4} onBack={() => set({ stage: 'goal' })}><p className="text-coral-600">{err}</p></WizardFrame>
  if (!pack) return <WizardFrame step={3} total={4}><p className="text-muted">Loading…</p></WizardFrame>

  return (
    <WizardFrame step={3} total={4} onBack={back}>
      {stage === 'intro' && (
        <div className="py-8 text-center">
          <div className="text-6xl" aria-hidden>🕵️</div>
          <h1 className="mt-4 text-3xl font-bold">Catch the AI</h1>
          <p className="mx-auto mt-3 max-w-md text-muted">
            In the AI era, your edge is <b>judgment</b>: spotting when AI is wrong, and owning what happens next.
            An AI assistant wrote something for you. Some lines are wrong. Find them.
          </p>
          <p className="mx-auto mt-2 max-w-md text-sm text-muted">About 2 minutes. This is an estimate to guide you, never a hiring decision.</p>
          <button className="btn-violet mt-8 px-10" onClick={() => setStage('review')}>Start</button>
          <div><button className="mt-4 text-sm font-bold text-muted underline" onClick={() => set({ stage: 'reveal' })}>Skip for now</button></div>
        </div>
      )}

      {stage === 'review' && (
        <>
          <div className="text-sm font-bold text-violet-600">🤖 AI draft: {pack.title}</div>
          <p className="mt-1 text-muted">{pack.context}</p>
          <h1 className="mt-4 text-2xl font-bold">Tap every line you wouldn't send as it is.</h1>
          <ol className="mt-5 space-y-2">
            {pack.lines.map((line, i) => {
              const on = flagged.includes(i)
              return (
                <li key={i}>
                  <button onClick={() => toggle(i)} aria-pressed={on}
                    className={`option flex items-start gap-3 font-normal ${on ? 'border-coral-500 bg-coral-50 text-ink hover:bg-coral-50' : ''}`}>
                    <span className={`mt-0.5 grid h-7 w-7 shrink-0 place-items-center rounded-lg border-2 text-sm font-bold ${on ? 'border-coral-500 bg-coral-500 text-white' : 'border-line text-muted'}`}>{on ? '!' : i + 1}</span>
                    <span>{line}</span>
                  </button>
                </li>
              )
            })}
          </ol>
          <div className="mt-6 flex items-center justify-between gap-3">
            <span className="text-sm text-muted">{flagged.length} line(s) flagged</span>
            <button className="btn-green px-8" onClick={() => setStage('confidence')}>Done checking</button>
          </div>
        </>
      )}

      {stage === 'confidence' && (
        <div className="py-6">
          <h1 className="text-2xl font-bold">How sure are you that you found every mistake?</h1>
          <p className="mt-2 text-muted">Good judgment includes knowing what you might have missed.</p>
          <div className="mt-10 text-center font-display text-5xl font-bold text-violet-600">{confidence}%</div>
          <input type="range" min="0" max="100" step="5" value={confidence} onChange={(e) => setConfidence(+e.target.value)}
            className="mt-4 w-full accent-violet-500" aria-label="Confidence" />
          <div className="flex justify-between text-xs text-muted"><span>Just guessing</span><span>Completely sure</span></div>
          <div className="mt-8 flex justify-end"><button className="btn-green px-10" onClick={() => setStage('action')}>Next</button></div>
        </div>
      )}

      {stage === 'action' && (
        <>
          <h1 className="text-2xl font-bold">{pack.actions.question}</h1>
          <div className="mt-6 grid gap-3" role="radiogroup">
            {pack.actions.options.map((o) => (
              <button key={o.id} role="radio" aria-checked={action === o.id} onClick={() => setAction(o.id)}
                className={`option ${action === o.id ? 'option-on' : ''}`}>{o.text}</button>
            ))}
          </div>
          <div className="mt-8 flex justify-end"><button className="btn-green px-10" disabled={!action} onClick={() => setStage('situations')}>Next</button></div>
        </>
      )}

      {stage === 'situations' && (
        <>
          <h1 className="text-2xl font-bold">Two quick situations</h1>
          {pack.situations.map((q) => (
            <div key={q.id} className="mt-6">
              <div className="font-semibold">{q.text}</div>
              <div className="mt-3 grid gap-2" role="radiogroup">
                {q.options.map((o, k) => (
                  <button key={k} role="radio" aria-checked={answers[q.id] === k} onClick={() => setAnswers({ ...answers, [q.id]: k })}
                    className={`option text-sm ${answers[q.id] === k ? 'option-on' : ''}`}>{o}</button>
                ))}
              </div>
            </div>
          ))}
          <div className="mt-8 flex justify-end">
            <button className="btn-green px-10" disabled={pack.situations.some((q) => answers[q.id] === undefined)} onClick={submit}>See my result</button>
          </div>
        </>
      )}

      {stage === 'result' && result && (
        <>
          <div className="text-center">
            <div className="text-6xl" aria-hidden>{result.details.all_found ? '🏆' : result.details.found >= 2 ? '🕵️' : '🔍'}</div>
            <h1 className="mt-3 text-3xl font-bold">You caught {result.details.found} of {result.details.planted} mistakes</h1>
            {result.details.false_alarms > 0 && <p className="mt-1 text-muted">and flagged {result.details.false_alarms} line(s) that were fine.</p>}
          </div>
          <div className="panel mt-6 space-y-4">
            <Score label="🧠 Judgment" v={result.judgment} range={result.judgment_range} />
            <Score label="🛡️ Responsibility" v={result.responsibility} range={result.responsibility_range} />
            <ul className="space-y-1 text-sm text-muted">{result.explain.map((e, i) => <li key={i}>{e}</li>)}</ul>
            <p className="text-xs text-muted">{result.note}</p>
          </div>
          <h2 className="mt-8 text-xl font-bold">What the AI got wrong</h2>
          <ul className="mt-3 space-y-3">
            {result.feedback.mistakes.map((m) => (
              <li key={m.line} className={`rounded-2xl border-2 p-3 ${m.found ? 'border-sprout-500 bg-sprout-50' : 'border-coral-500 bg-coral-50'}`}>
                <div className="text-sm font-bold">{m.found ? '✓ You caught this' : '✗ You missed this'} <span className="chip ml-1 bg-white text-muted">{m.type}</span></div>
                <q className="mt-1 block text-sm italic">{m.text}</q>
                <div className="mt-1 text-sm">{m.why}</div>
              </li>
            ))}
            {result.feedback.false_alarms.map((f) => (
              <li key={f.line} className="rounded-2xl border-2 border-line bg-white p-3 text-sm">
                <b>This line was fine:</b> <q className="italic">{f.text}</q>
              </li>
            ))}
          </ul>
          <div className="mt-8 flex justify-end"><button className="btn-violet px-10" onClick={() => set({ stage: 'reveal' })}>See my forecast</button></div>
        </>
      )}
    </WizardFrame>
  )
}

function Score({ label, v, range }) {
  return (
    <div>
      <div className="flex justify-between text-sm font-bold"><span>{label}</span>
        <span>{Math.round(v * 100)} <span className="font-normal text-muted">(range {Math.round(range[0] * 100)}–{Math.round(range[1] * 100)})</span></span></div>
      <Bar value={v} color="bg-violet-500" h="h-3" />
    </div>
  )
}
