import { t as tr } from '../../i18n'
import { useState } from 'react'
import { Area, AreaChart, ResponsiveContainer, Tooltip, YAxis } from 'recharts'
import { TYPE, XP } from '../../game'
import { Bar, SdgChip, Sheet } from '../ui'
import CharacterCard from './CharacterCard'

const OFFSETS = [0, 55, 85, 55, 0, -55, -85, -55]

export default function QuestMap(ctx) {
  const { s, meta, plan, goal, toggleQuest } = ctx
  const [open, setOpen] = useState(null)

  if (!plan || !goal) return <p className="text-muted">{tr("Drawing your quest map\u2026")}</p>
  const steps = plan.steps
  const doneIdx = steps.map((q) => s.completed.includes(q.id))
  const current = doneIdx.findIndex((d) => !d)
  const doneCount = doneIdx.filter(Boolean).length
  const state = (i) => (doneIdx[i] ? 'done' : i === current ? 'current' : 'locked')
  const year3 = new Date().getFullYear() + 3

  return (
    <div className="grid gap-6 lg:grid-cols-[1fr_340px]">
      <section>
        <div className="panel">
          <h1 className="text-2xl font-bold">{tr('Your quests to {role}', { role: plan.role_title })}</h1>
          <p className="mt-1 text-sm text-muted">Courses teach you, projects prove it, experiences build what AI can't copy. Each quest raises your {year3} Edge Score.</p>
          <div className="mt-4 flex items-center gap-3">
            <Bar value={steps.length ? doneCount / steps.length : 0} color="bg-sprout-500" h="h-4" />
            <span className="shrink-0 text-sm font-bold">{doneCount}/{steps.length}</span>
          </div>
          <p className="mt-2 text-xs text-muted">About {plan.total_hours} hours in total, or {plan.total_weeks} weeks at {plan.hours_per_week} hours a week.</p>
        </div>

        <ol className="relative mx-auto mt-10 flex max-w-sm flex-col items-center gap-10" aria-label="Quest map">
          {steps.map((q, i) => {
            const st = state(i)
            const t = TYPE[q.type]
            return (
              <li key={q.id} className="flex flex-col items-center" style={{ transform: `translateX(${OFFSETS[i % OFFSETS.length]}px)` }}>
                {i === 0 && <span className="mb-2 chip bg-violet-500 text-white">🎯 One Move</span>}
                {st === 'current' && <span className="animate-bob mb-2 rounded-xl border-2 border-line bg-white px-3 py-1 font-display font-semibold text-violet-700">{tr("Start here")}</span>}
                <button onClick={() => setOpen(q)} aria-label={`${t.label}: ${q.title} (${st})`}
                  className={`grid h-20 w-20 place-items-center rounded-full border-b-[6px] text-3xl transition-transform active:translate-y-1 ${
                    st === 'done' ? 'border-sprout-700 bg-sprout-500 text-white'
                      : st === 'current' ? 'border-violet-700 bg-violet-500 ring-8 ring-violet-100'
                        : 'border-[#C9CEDB] bg-line grayscale'}`}>
                  {st === 'done' ? '✓' : st === 'locked' ? '🔒' : t.icon}
                </button>
                <div className="mt-2 max-w-[11rem] text-center text-sm font-bold leading-tight">{q.title.length > 48 ? `${q.title.slice(0, 46)}…` : q.title}</div>
                <div className="text-xs text-muted">{t.label}, +{XP[q.type]} XP</div>
              </li>
            )
          })}
          <li className="flex flex-col items-center">
            <div className={`grid h-24 w-24 place-items-center rounded-3xl border-b-[6px] text-5xl ${doneCount === steps.length ? 'border-sun-600 bg-sun-400' : 'border-[#C9CEDB] bg-line'}`} aria-hidden>🏆</div>
            <div className="mt-2 font-display font-semibold">{plan.role_title}</div>
          </li>
        </ol>
      </section>

      <aside className="space-y-6">
        <CharacterCard {...ctx} compact />
        <div className="panel">
          <h2 className="text-lg font-bold">Your {year3} Edge Score</h2>
          <div className="flex items-baseline gap-2">
            <span className="font-display text-4xl font-bold">{Math.round(goal.edge_y3)}</span>
            {s.history[0] && <span className={`font-bold ${goal.edge_y3 >= s.history[0].edge ? 'text-sprout-600' : 'text-coral-600'}`}>
              {goal.edge_y3 - s.history[0].edge >= 0 ? '+' : ''}{(goal.edge_y3 - s.history[0].edge).toFixed(1)} since you started</span>}
          </div>
          <div className="mt-3 h-28">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={s.history.map((h, i) => ({ ...h, i }))} margin={{ left: -30, right: 4, top: 4 }}>
                <YAxis domain={[0, 100]} fontSize={10} />
                <Tooltip formatter={(v) => [Math.round(v), 'Edge']} labelFormatter={(i) => s.history[i]?.label} />
                <Area type="monotone" dataKey="edge" stroke="#1F9A5E" strokeWidth={3} fill="#CDEFDC" isAnimationActive={false} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      </aside>

      <Sheet open={!!open} onClose={() => setOpen(null)} label="Quest details">
        {open && (() => {
          const i = steps.findIndex((x) => x.id === open.id)
          const st = state(i)
          const t = TYPE[open.type]
          return (
            <>
              <div className="flex items-center gap-2">
                <span className="text-3xl" aria-hidden>{t.icon}</span>
                <span className="chip bg-canvas text-muted">{t.label}: {t.why}</span>
                {i === 0 && <span className="chip bg-violet-500 text-white">One Move</span>}
              </div>
              <h2 className="mt-3 text-2xl font-bold">{open.title}</h2>
              <p className="mt-2 text-muted">Builds <b className="text-ink">{open.target_skill_name}</b>, which adds about <b className="text-ink">{open.edge_gain} points</b> to your {year3} Edge Score.</p>
              <ul className="mt-4 grid grid-cols-3 gap-2 text-center">
                <li className="rounded-2xl bg-canvas p-2"><div className="font-display text-xl font-bold">{open.hours}h</div><div className="text-xs text-muted">time</div></li>
                <li className="rounded-2xl bg-canvas p-2"><div className="font-display text-xl font-bold capitalize">{open.cost.split(' ')[0]}</div><div className="text-xs text-muted">cost</div></li>
                <li className="rounded-2xl bg-canvas p-2"><div className="font-display text-xl font-bold">+{XP[open.type]}</div><div className="text-xs text-muted">XP</div></li>
              </ul>
              <p className="mt-4 text-sm">Source: {open.url ? <a className="font-bold text-violet-600 underline" href={open.url} target="_blank" rel="noreferrer">{open.provider}</a> : open.provider}
                {!open.verified && <span className="text-sun-600"> (link not checked by our team yet)</span>}</p>
              <div className="mt-3 flex flex-wrap gap-1">{open.sdgs.map((g) => <SdgChip key={g} target={g} sdgs={meta.sdgs} />)}</div>
              <div className="mt-6 flex flex-wrap gap-3">
                {st === 'done' && <button className="btn-white" onClick={() => { toggleQuest(open); setOpen(null) }}>{tr("Mark as not done")}</button>}
                {st === 'current' && <button className="btn-green flex-1" onClick={() => { toggleQuest(open); setOpen(null) }}>{tr("I finished this quest")}</button>}
                {st === 'locked' && <p className="text-sm font-bold text-muted">{tr("\ud83d\udd12 Finish the quest before this one to unlock it.")}</p>}
                {open.url && st !== 'done' && <a className="btn-white" href={open.url} target="_blank" rel="noreferrer">Open {t.label.toLowerCase()}</a>}
              </div>
            </>
          )
        })()}
      </Sheet>
    </div>
  )
}
