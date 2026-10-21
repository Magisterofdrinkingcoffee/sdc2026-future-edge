import { useEffect } from 'react'
import { celebrate, ForecastStrip, WizardFrame } from '../ui'
import CharacterCard from '../dash/CharacterCard'

export default function Reveal(ctx) {
  const { s, set, forecast, plan, goal } = ctx
  useEffect(() => { if (goal) celebrate() }, [!!goal]) // eslint-disable-line react-hooks/exhaustive-deps

  if (!forecast || !goal) {
    return <WizardFrame step={4} total={4}><div className="py-24 text-center"><div className="animate-bob text-6xl">🔭</div><h2 className="mt-4 text-2xl font-bold">Building your forecast…</h2></div></WizardFrame>
  }
  const other = forecast[s.scenario === 'fast' ? 'moderate' : 'fast'].roles.find((r) => r.role_id === goal.role_id)
  const drop = Math.round(goal.edge_now - goal.edge_y3)
  const fading = forecast[s.scenario].skills.filter((k) => k.status === 'fading')

  return (
    <WizardFrame step={4} total={4} onBack={() => set({ stage: 'quiz' })}>
      <h1 className="text-3xl font-bold">{s.profile.name ? `${s.profile.name.split(' ')[0]}, here's` : "Here's"} your forecast as {/^[AEIOU]/.test(goal.title) ? 'an' : 'a'} {goal.title}</h1>
      <p className="mt-2 text-muted">
        In the {forecast[s.scenario].scenario_label} scenario, your Edge Score {drop > 0 ? `drops by ${drop} points` : 'holds steady'} by {new Date().getFullYear() + 3}
        {fading.length ? `, mainly because AI is catching up on ${fading.slice(0, 2).map((f) => f.name.toLowerCase()).join(' and ')}` : ''}.
      </p>

      <div className="mt-6"><ForecastStrip timeline={goal.timeline} compare={other.timeline} animate /></div>
      <p className="mt-2 text-xs text-muted">Estimate. "vs" shows the {forecast[s.scenario === 'fast' ? 'moderate' : 'fast'].scenario_label} scenario. Not a hiring decision.</p>

      <div className="mt-8 grid gap-5 sm:grid-cols-2">
        <CharacterCard {...ctx} compact />
        <div className="panel flex flex-col border-violet-300 bg-violet-50">
          <div className="text-3xl" aria-hidden>🎯</div>
          <h2 className="mt-2 text-xl font-bold">Your One Move</h2>
          {plan?.one_move ? (
            <>
              <p className="mt-1 font-display text-2xl font-semibold text-violet-700">Get better at {plan.one_move.name.toLowerCase()}</p>
              <p className="mt-2 flex-1 text-sm text-muted">This one skill raises your {new Date().getFullYear() + 3} Edge Score by about {plan.one_move.edge_gain} points, more than any other skill.</p>
            </>
          ) : <p className="flex-1 text-muted">Working it out…</p>}
          <button className="btn-violet mt-4" onClick={() => set({ stage: 'app', tab: 'quests' })}>Start my quests</button>
        </div>
      </div>
    </WizardFrame>
  )
}
