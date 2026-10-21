import { useEffect, useState } from 'react'
import { api } from '../../api'
import { XP } from '../../game'
import { WizardFrame } from '../ui'

export default function QuizStep({ set, award }) {
  const [qs, setQs] = useState(null)
  const [i, setI] = useState(0)
  const [answers, setAnswers] = useState({})
  const [intro, setIntro] = useState(true)

  useEffect(() => { api.assessment().then((r) => setQs(r.questions)) }, [])
  if (!qs) return <WizardFrame step={3} total={4}><p className="text-muted">Loading…</p></WizardFrame>

  const q = qs[i]
  const chosen = answers[q.id]
  const next = async () => {
    if (i + 1 < qs.length) { setI(i + 1); return }
    const result = await api.scoreAssessment(answers)
    set({ assessment: result })
    award('quiz', XP.quiz, 'Edge Check finished')
    set({ stage: 'reveal' })
  }

  if (intro) {
    return (
      <WizardFrame step={3} total={4} onBack={() => set({ stage: 'goal' })}>
        <div className="py-10 text-center">
          <div className="text-6xl" aria-hidden>🧠</div>
          <h1 className="mt-4 text-3xl font-bold">The Edge Check</h1>
          <p className="mx-auto mt-3 max-w-md text-muted">
            AI is getting good at technical work. What it can't copy easily is your <b>judgment</b> and how <b>responsible</b> you are.
            Five short work situations. There are no trick questions, just answer how you'd really act.
          </p>
          <button className="btn-violet mt-8 px-10" onClick={() => setIntro(false)}>Start the Edge Check</button>
          <div><button className="mt-4 text-sm font-bold text-muted underline" onClick={() => set({ stage: 'reveal' })}>Skip for now</button></div>
        </div>
      </WizardFrame>
    )
  }

  return (
    <WizardFrame step={3} total={4} onBack={() => (i ? setI(i - 1) : setIntro(true))}>
      <div className="text-sm font-bold text-violet-600">Situation {i + 1} of {qs.length}</div>
      <h1 className="mt-2 text-2xl font-bold leading-snug">{q.text}</h1>
      <div className="mt-6 grid gap-3" role="radiogroup">
        {q.options.map((o, k) => (
          <button key={k} role="radio" aria-checked={chosen === k}
            onClick={() => setAnswers({ ...answers, [q.id]: k })}
            className={`option flex items-center gap-3 ${chosen === k ? 'option-on' : ''}`}>
            <span className={`grid h-8 w-8 shrink-0 place-items-center rounded-lg border-2 text-sm ${chosen === k ? 'border-violet-500' : 'border-line text-muted'}`}>{k + 1}</span>
            {o}
          </button>
        ))}
      </div>
      <div className="mt-8 flex justify-end">
        <button className="btn-green px-10" disabled={chosen === undefined} onClick={next}>{i + 1 < qs.length ? 'Next' : 'See my forecast'}</button>
      </div>
    </WizardFrame>
  )
}
