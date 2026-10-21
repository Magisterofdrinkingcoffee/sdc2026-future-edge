import { levelInfo, streak } from '../../game'
import { Bar, Logo } from '../ui'
import QuestMap from './QuestMap'
import ForecastView from './ForecastView'
import MeView from './MeView'

const TABS = [
  { id: 'quests', icon: '🗺️', label: 'Quests' },
  { id: 'forecast', icon: '🔭', label: 'Forecast' },
  { id: 'me', icon: '🏅', label: 'Me' },
]

export default function Dashboard(ctx) {
  const { s, set, xp, goal } = ctx
  const lv = levelInfo(xp)
  const days = streak(s.days)
  return (
    <div className="min-h-screen pb-24 sm:pb-10">
      <header className="sticky top-0 z-30 border-b-2 border-line bg-white/95 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center gap-3 px-4 py-3">
          <button onClick={() => set({ stage: 'welcome' })} aria-label="Home"><Logo small /></button>
          <nav className="ml-6 hidden gap-1 sm:flex">
            {TABS.map((t) => (
              <button key={t.id} onClick={() => set({ tab: t.id })} aria-current={s.tab === t.id}
                className={`rounded-xl px-4 py-2 font-display font-semibold ${s.tab === t.id ? 'bg-violet-50 text-violet-700' : 'text-muted hover:bg-canvas'}`}>
                <span aria-hidden>{t.icon}</span> {t.label}
              </button>
            ))}
          </nav>
          <div className="ml-auto flex items-center gap-2 sm:gap-4">
            <Stat icon="🔥" value={days} label={`${days}-day streak`} tone="text-sun-600" />
            {goal && <Stat icon="⚡" value={Math.round(goal.edge_y3)} label={`Edge Score in ${new Date().getFullYear() + 3}`} tone="text-violet-600" />}
            <div className="hidden w-40 md:block" title={`${lv.into} / ${lv.needed} XP to ${lv.nextName}`}>
              <div className="flex justify-between text-xs font-bold"><span>Lv {lv.level} {lv.name}</span><span className="text-muted">{xp} XP</span></div>
              <Bar value={lv.progress} color="bg-sun-500" h="h-2.5" />
            </div>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-4 py-6">
        {s.tab === 'quests' && <QuestMap {...ctx} />}
        {s.tab === 'forecast' && <ForecastView {...ctx} />}
        {s.tab === 'me' && <MeView {...ctx} />}
      </main>

      <nav className="fixed inset-x-0 bottom-0 z-30 grid grid-cols-3 border-t-2 border-line bg-white sm:hidden">
        {TABS.map((t) => (
          <button key={t.id} onClick={() => set({ tab: t.id })} aria-current={s.tab === t.id}
            className={`py-3 text-center text-xs font-bold ${s.tab === t.id ? 'text-violet-600' : 'text-muted'}`}>
            <div className="text-2xl" aria-hidden>{t.icon}</div>{t.label}
          </button>
        ))}
      </nav>
    </div>
  )
}

function Stat({ icon, value, label, tone }) {
  return (
    <div className={`flex items-center gap-1 rounded-xl px-2 py-1 font-display text-lg font-bold ${tone}`} title={label} aria-label={label}>
      <span aria-hidden>{icon}</span>{value}
    </div>
  )
}
