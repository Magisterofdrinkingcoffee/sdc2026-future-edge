import { useEffect, useState } from 'react'
import { api } from '../api'
import { EstimateNote, Pct } from './ui'

export default function AssessmentStep({ assessment, setAssessment, setStep }) {
  const [qs, setQs] = useState(null)
  const [answers, setAnswers] = useState({})

  useEffect(() => { api.assessment().then(setQs) }, [])

  const submit = async () => setAssessment(await api.scoreAssessment(answers))

  if (!qs) return <div className="text-slate-500">Loading…</div>
  const done = Object.keys(answers).length === qs.questions.length

  return (
    <div className="grid gap-5 lg:grid-cols-3">
      <section className="card lg:col-span-2 space-y-5">
        <div>
          <h2 className="text-lg font-semibold">Edge Assessment</h2>
          <p className="text-sm text-slate-600">AI is getting good at many technical tasks. What it can't replace easily is <b>judgment</b> and <b>responsibility</b>. Answer honestly – there's no hiring decision here. {qs.note}</p>
        </div>
        {qs.questions.map((q, qi) => (
          <div key={q.id}>
            <div className="font-medium mb-2">{qi + 1}. {q.text}</div>
            <div className="grid gap-2">
              {q.options.map((o, i) => (
                <label key={i} className={`flex gap-2 items-start rounded-lg border p-2 text-sm cursor-pointer ${answers[q.id] === i ? 'border-edge-500 bg-edge-50' : 'border-slate-200 hover:bg-slate-50'}`}>
                  <input type="radio" name={q.id} checked={answers[q.id] === i} onChange={() => setAnswers({ ...answers, [q.id]: i })} className="mt-0.5 accent-edge-600" />
                  {o}
                </label>
              ))}
            </div>
          </div>
        ))}
        <button className="btn-primary" disabled={!done} onClick={submit}>See my result</button>
      </section>

      <aside className="card h-fit space-y-3">
        <div className="label">Your human-skill estimate</div>
        {assessment ? (
          <>
            <Bar label="Judgment & critical thinking" v={assessment.judgment} />
            <Bar label="Responsibility & ownership" v={assessment.responsibility} />
            <EstimateNote>based on {assessment.answered} scenarios</EstimateNote>
            <p className="text-sm text-slate-600">These feed your Edge Score as the "uniqueness" multiplier – the part of you AI can't copy.</p>
            <button className="btn-primary w-full justify-center" onClick={() => setStep('forecast')}>See my career forecast →</button>
          </>
        ) : <p className="text-sm text-slate-500">Answer all 5 scenarios to see your result.</p>}
      </aside>
    </div>
  )
}

function Bar({ label, v }) {
  return (
    <div>
      <div className="flex justify-between text-sm"><span>{label}</span><b><Pct v={v} /></b></div>
      <div className="h-2 rounded bg-slate-200"><div className="h-2 rounded bg-edge-600" style={{ width: `${v * 100}%` }} /></div>
    </div>
  )
}
