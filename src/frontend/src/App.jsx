import { useEffect, useState } from 'react'
import { api } from './api'
import ProfileStep from './components/ProfileStep'
import AssessmentStep from './components/AssessmentStep'
import ForecastStep from './components/ForecastStep'
import PathwayStep from './components/PathwayStep'
import { TrendSource } from './components/ui'

const STEPS = [
  { id: 'profile', label: '1. Your profile' },
  { id: 'assessment', label: '2. Edge Assessment' },
  { id: 'forecast', label: '3. Career forecast' },
  { id: 'pathway', label: '4. Pathway & progress' },
]

const EMPTY = { name: '', skills: {}, goal_role: '', cv_text: '' }
const STORE_KEY = 'future-edge-state-v1'

function loadSaved() {
  try { return JSON.parse(localStorage.getItem(STORE_KEY)) || {} } catch { return {} }
}

export default function App() {
  const saved = loadSaved()
  const [meta, setMeta] = useState(null)
  const [error, setError] = useState(null)
  const [step, setStep] = useState(saved.step || 'profile')
  const [profile, setProfile] = useState(saved.profile || EMPTY)
  const [assessment, setAssessment] = useState(saved.assessment || null)
  const [scenario, setScenario] = useState(saved.scenario || 'moderate')
  const [completed, setCompleted] = useState(saved.completed || [])
  const [history, setHistory] = useState(saved.history || [])
  const [overrides, setOverrides] = useState({})
  const [trends, setTrends] = useState(null)

  useEffect(() => {
    api.meta().then(setMeta).catch((e) => setError(e.message))
    api.trends().then(setTrends).catch(() => {})
  }, [])

  useEffect(() => {
    try {
      localStorage.setItem(STORE_KEY, JSON.stringify({ step, profile, assessment, scenario, completed, history }))
    } catch { /* storage unavailable – app still works */ }
  }, [step, profile, assessment, scenario, completed, history])

  const shared = {
    meta, profile, setProfile, assessment, setAssessment, scenario, setScenario,
    completed, setCompleted, history, setHistory, overrides, setOverrides, trends, setTrends, setStep,
    body: {
      skills: profile.skills, scenario, goal_role: profile.goal_role || null,
      assessment: assessment ? { judgment: assessment.judgment, responsibility: assessment.responsibility } : null,
      completed, signal_overrides: overrides,
    },
  }

  const reset = () => {
    setProfile(EMPTY); setAssessment(null); setCompleted([]); setHistory([]); setOverrides({}); setStep('profile')
  }

  return (
    <div className="min-h-screen">
      <header className="bg-ink text-white">
        <div className="mx-auto max-w-6xl px-4 py-5 flex flex-wrap items-center justify-between gap-3">
          <div>
            <div className="text-2xl font-bold tracking-tight">Future <span className="text-sky-400">Edge</span></div>
            <div className="text-sm text-slate-300">Forecast how AI changes your career value – and the one move that keeps you ahead.</div>
          </div>
          <TrendSource trends={trends} dark />
        </div>
        <nav className="mx-auto max-w-6xl px-4 flex gap-1 overflow-x-auto">
          {STEPS.map((s) => (
            <button key={s.id} onClick={() => setStep(s.id)}
              className={`whitespace-nowrap rounded-t-lg px-4 py-2 text-sm font-medium ${step === s.id ? 'bg-slate-50 text-ink' : 'text-slate-300 hover:text-white'}`}>
              {s.label}
            </button>
          ))}
        </nav>
      </header>

      <main className="mx-auto max-w-6xl px-4 py-6">
        {error && <div className="card border-red-300 bg-red-50 text-red-800 mb-4">Cannot reach the backend: {error}</div>}
        {!meta ? <div className="text-slate-500">Loading…</div> : (
          <>
            {step === 'profile' && <ProfileStep {...shared} />}
            {step === 'assessment' && <AssessmentStep {...shared} />}
            {step === 'forecast' && <ForecastStep {...shared} />}
            {step === 'pathway' && <PathwayStep {...shared} />}
          </>
        )}
      </main>

      <footer className="mx-auto max-w-6xl px-4 pb-10 text-xs text-slate-500 space-y-1">
        <p>All scores are <b>estimates</b> to support your own decisions – never a hiring decision. Demo uses synthetic profiles only.</p>
        <p>Every trend, course and SDG link shows its source. SDG targets: United Nations (sdgs.un.org). <button className="underline" onClick={reset}>Reset demo</button></p>
      </footer>
    </div>
  )
}
