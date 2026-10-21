import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { api } from './api'
import { BADGES, earnedBadges, levelInfo, today, totalXp, XP } from './game'
import { celebrate, Toasts } from './components/ui'
import Welcome from './components/wizard/Welcome'
import CvStep from './components/wizard/CvStep'
import GoalStep from './components/wizard/GoalStep'
import QuizStep from './components/wizard/QuizStep'
import Reveal from './components/wizard/Reveal'
import Dashboard from './components/dash/Dashboard'

const STORE_KEY = 'future-edge-v2'
const FRESH = {
  stage: 'welcome', tab: 'quests',
  profile: { name: '', avatar: '🙂', skills: {}, evidence: {}, source: null, goal_role: '' },
  assessment: null, scenario: 'fast', completed: [], xpLog: {}, days: [], flags: {}, history: [], earned: [],
}

function loadSaved() {
  try { return { ...FRESH, ...(JSON.parse(localStorage.getItem(STORE_KEY)) || {}) } } catch { return FRESH }
}

export default function App() {
  const [s, setS] = useState(loadSaved)
  const set = useCallback((patch) => setS((prev) => ({ ...prev, ...(typeof patch === 'function' ? patch(prev) : patch) })), [])
  const [meta, setMeta] = useState(null)
  const [error, setError] = useState(null)
  const [toasts, setToasts] = useState([])
  const [forecast, setForecast] = useState(null)   // { moderate, fast }
  const [plan, setPlan] = useState(null)
  const [overrides, setOverrides] = useState({})
  const [trends, setTrends] = useState(null)

  useEffect(() => {
    api.meta().then(setMeta).catch((e) => setError(e.message))
    api.trends().then(setTrends).catch(() => {})
  }, [])
  useEffect(() => { try { localStorage.setItem(STORE_KEY, JSON.stringify(s)) } catch { /* private mode */ } }, [s])
  useEffect(() => { window.scrollTo(0, 0) }, [s.stage, s.tab])

  const toast = useCallback((t) => {
    const id = Math.random()
    setToasts((ts) => [...ts, { ...t, id }])
    setTimeout(() => setToasts((ts) => ts.filter((x) => x.id !== id)), 3200)
  }, [])

  // ---- XP --------------------------------------------------------------
  const award = useCallback((key, amount, reason) => {
    setS((prev) => {
      if (prev.xpLog[key]) return prev
      const before = levelInfo(totalXp(prev.xpLog))
      const xpLog = { ...prev.xpLog, [key]: { amount, reason } }
      const after = levelInfo(totalXp(xpLog))
      setTimeout(() => {
        toast({ icon: '⭐', title: `+${amount} XP`, text: reason })
        if (after.level > before.level) {
          toast({ icon: '🎉', title: `Level ${after.level}: ${after.name}`, text: 'You levelled up!' })
          celebrate()
        }
      }, 0)
      return { ...prev, xpLog, days: prev.days.includes(today()) ? prev.days : [...prev.days, today()] }
    })
  }, [toast])
  const unaward = (key) => set((prev) => { const xpLog = { ...prev.xpLog }; delete xpLog[key]; return { xpLog } })

  // ---- request body shared by forecast + pathway -------------------------
  const assessed = s.assessment ? { judgment: s.assessment.judgment, responsibility: s.assessment.responsibility } : null
  const body = useMemo(() => ({
    skills: s.profile.skills, goal_role: s.profile.goal_role || null, assessment: assessed,
    completed: s.completed, signal_overrides: overrides,
  }), [s.profile.skills, s.profile.goal_role, s.assessment, s.completed, overrides]) // eslint-disable-line react-hooks/exhaustive-deps

  const ready = ['reveal', 'app'].includes(s.stage) && Object.keys(s.profile.skills).length > 0
  useEffect(() => {
    if (!ready) return
    Promise.all(['moderate', 'fast'].map((sc) => api.forecast({ ...body, scenario: sc })))
      .then(([moderate, fast]) => {
        setForecast({ moderate, fast })
        if (!s.profile.goal_role) {   // "suggest for me": best future role that isn't shrinking or mostly automatable
          const safe = fast.roles.filter((r) => !r.at_risk)
          const growing = safe.filter((r) => r.edge_y3 >= 0.8 * r.edge_now)
          const pool = growing.length ? growing : safe.length ? safe : fast.roles
          const best = [...pool].sort((a, b) => b.edge_y3 - a.edge_y3)[0]
          set((p) => ({ profile: { ...p.profile, goal_role: best.role_id } }))
        }
      })
      .catch((e) => setError(e.message))
  }, [ready, JSON.stringify(body)]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (!ready || !s.profile.goal_role) return
    // Plan is built from the profile WITHOUT finished quests, so the map stays stable as you complete it.
    api.pathway({ ...body, completed: [], role_id: s.profile.goal_role, scenario: s.scenario, hours_per_week: 6 })
      .then(setPlan).catch((e) => setError(e.message))
  }, [ready, s.profile.goal_role, s.scenario, JSON.stringify(s.profile.skills), JSON.stringify(s.assessment), JSON.stringify(overrides)]) // eslint-disable-line react-hooks/exhaustive-deps

  const goal = forecast?.[s.scenario]?.roles.find((r) => r.role_id === s.profile.goal_role)

  // start the progress history once we know the starting score
  useEffect(() => {
    if (goal && s.history.length === 0) set({ history: [{ label: 'Start', edge: goal.edge_y3 }] })
  }, [goal]) // eslint-disable-line react-hooks/exhaustive-deps

  // ---- badges --------------------------------------------------------------
  const questsDone = (plan?.steps || []).filter((q) => s.completed.includes(q.id))
  const categories = meta ? new Set(Object.entries(s.profile.skills).filter(([, v]) => v >= 0.3)
    .map(([id]) => meta.skills.find((m) => m.id === id)?.category)).size : 0
  const edgeGain = goal && s.history[0] ? goal.edge_y3 - s.history[0].edge : 0
  const earned = earnedBadges({ ...s, skills: s.profile.skills, questsDone, questTotal: plan?.steps.length, categories, edgeGain })
  const firstBadgeCheck = useRef(true)
  useEffect(() => {
    const fresh = earned.filter((b) => !s.earned.includes(b))
    if (!fresh.length) return
    if (!firstBadgeCheck.current) {
      fresh.forEach((id) => { const b = BADGES.find((x) => x.id === id); toast({ icon: b.icon, title: `Badge unlocked: ${b.name}`, text: b.how }) })
    }
    set({ earned: [...s.earned, ...fresh] })
  }, [earned.join()]) // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => { firstBadgeCheck.current = false }, [])

  // ---- quest completion ---------------------------------------------------
  const toggleQuest = async (q) => {
    const done = s.completed.includes(q.id)
    const completed = done ? s.completed.filter((c) => c !== q.id) : [...s.completed, q.id]
    set({ completed })
    if (done) unaward(`quest:${q.id}`)
    else { award(`quest:${q.id}`, XP[q.type] || 50, `Quest done: ${q.title}`); celebrate() }
    const f = await api.forecast({ ...body, completed, scenario: s.scenario })
    const r = f.roles.find((x) => x.role_id === s.profile.goal_role)
    set((p) => ({ history: [...p.history, { label: done ? `Undid: ${q.title}` : q.title, edge: r.edge_y3 }] }))
  }

  const reset = () => { setS(FRESH); setForecast(null); setPlan(null); setOverrides({}) }

  const ctx = {
    s, set, meta, award, toast, forecast, plan, goal, body, overrides, setOverrides, trends, setTrends,
    toggleQuest, reset, earned, xp: totalXp(s.xpLog),
  }

  return (
    <>
      {error && (
        <div role="alert" className="fixed top-3 inset-x-3 z-50 mx-auto max-w-lg rounded-2xl border-2 border-coral-500 bg-coral-50 p-3 text-sm text-coral-600">
          <b>Can't reach the Future Edge server.</b> Start the backend (uvicorn) and reload. <span className="opacity-70">({error})</span>
          <button className="ml-2 underline" onClick={() => setError(null)}>Dismiss</button>
        </div>
      )}
      {!meta ? <div className="grid min-h-screen place-items-center text-muted">Loading…</div> : (
        <>
          {s.stage === 'welcome' && <Welcome {...ctx} />}
          {s.stage === 'cv' && <CvStep {...ctx} />}
          {s.stage === 'goal' && <GoalStep {...ctx} />}
          {s.stage === 'quiz' && <QuizStep {...ctx} />}
          {s.stage === 'reveal' && <Reveal {...ctx} />}
          {s.stage === 'app' && <Dashboard {...ctx} />}
        </>
      )}
      <Toasts toasts={toasts} />
    </>
  )
}

