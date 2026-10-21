import { levelInfo } from '../../game'
import { Bar } from '../ui'

// RPG-style card: who you are in stats. Every stat comes from the scoring engine or the Edge Check.
export default function CharacterCard({ s, meta, goal, xp, compact }) {
  const lv = levelInfo(xp)
  const cats = Object.fromEntries(meta.skills.map((m) => [m.id, m.category]))
  const avg = (filter) => {
    const v = Object.entries(s.profile.skills).filter(([id]) => filter(cats[id])).map(([, x]) => x)
    return v.length ? v.reduce((a, b) => a + b, 0) / v.length : 0
  }
  const stats = [
    { icon: '🧠', name: 'Judgment', v: s.assessment?.judgment, color: 'bg-violet-500' },
    { icon: '🛡️', name: 'Responsibility', v: s.assessment?.responsibility, color: 'bg-violet-500' },
    { icon: '🔧', name: 'Tech skills', v: avg((c) => c === 'technical' || c === 'data'), color: 'bg-sky-500' },
    { icon: '💎', name: 'Rare mix', v: goal?.rarity, color: 'bg-sun-500' },
  ]
  return (
    <div className="panel">
      <div className="flex items-center gap-4">
        <div className="grid h-16 w-16 shrink-0 place-items-center rounded-2xl bg-violet-50 text-4xl" aria-hidden>{s.profile.avatar || '🙂'}</div>
        <div className="min-w-0">
          <div className="truncate font-display text-xl font-bold">{s.profile.name || 'You'}</div>
          <div className="text-sm text-muted">Level {lv.level} {lv.name}{goal ? `, aiming for ${goal.title}` : ''}</div>
        </div>
      </div>
      <dl className="mt-5 space-y-3">
        {stats.map((st) => (
          <div key={st.name}>
            <div className="flex justify-between text-sm font-bold">
              <dt>{st.icon} {st.name}</dt>
              <dd>{st.v == null ? <span className="text-muted">take the Edge Check</span> : `${Math.round(st.v * 100)}`}</dd>
            </div>
            <Bar value={st.v ?? 0} color={st.color} h="h-2.5" />
          </div>
        ))}
      </dl>
      {!compact && (
        <p className="mt-4 text-xs text-muted">Judgment and responsibility come from your Edge Check answers. Tech skills are the average level of your technical and data skills. Rare mix is how unusual your combination of skill types is. All are estimates.</p>
      )}
    </div>
  )
}
