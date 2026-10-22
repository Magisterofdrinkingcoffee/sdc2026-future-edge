import { BADGES, levelInfo, LEVELS, streak } from '../../game'
import { Bar } from '../ui'
import CharacterCard from './CharacterCard'

export default function MeView(ctx) {
  const { s, set, xp, earned, reset } = ctx
  const lv = levelInfo(xp)
  const days = streak(s.days)
  return (
    <div className="grid gap-6 lg:grid-cols-[340px_1fr]">
      <div className="space-y-6">
        <CharacterCard {...ctx} />
        <div className="panel space-y-3">
          <button className="btn-white w-full" onClick={() => set({ stage: 'cv' })}>Update my CV</button>
          <button className="btn-white w-full" onClick={() => set({ stage: 'quiz' })}>Play Catch the AI again</button>
          <button className="w-full text-sm font-bold text-coral-600 underline" onClick={() => window.confirm('Delete your progress on this device and start again?') && reset()}>Start over</button>
        </div>
      </div>
      <div className="space-y-6">
        <section className="panel">
          <div className="flex flex-wrap items-center gap-6">
            <div>
              <div className="font-display text-4xl font-bold">Level {lv.level}</div>
              <div className="text-muted">{lv.name}</div>
            </div>
            <div className="min-w-[12rem] flex-1">
              <Bar value={lv.progress} color="bg-sun-500" h="h-4" />
              <div className="mt-1 text-sm text-muted">{lv.nextName ? `${lv.needed - lv.into} XP to ${lv.nextName}` : 'Top level reached'}</div>
            </div>
            <div className="text-center">
              <div className="font-display text-4xl font-bold text-sun-600">🔥 {days}</div>
              <div className="text-sm text-muted">day streak</div>
            </div>
          </div>
          <ol className="mt-5 flex flex-wrap gap-2" aria-label="Levels">
            {LEVELS.map((l, i) => <li key={l.name} className={`chip ${i < lv.level ? 'bg-sun-100 text-sun-600' : 'bg-canvas text-muted'}`}>{i + 1}. {l.name}</li>)}
          </ol>
        </section>

        <section className="panel">
          <h2 className="text-xl font-bold">Badges <span className="text-muted">{earned.length}/{BADGES.length}</span></h2>
          <ul className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-3 xl:grid-cols-4">
            {BADGES.map((b) => {
              const got = earned.includes(b.id)
              return (
                <li key={b.id} className={`rounded-3xl border-2 p-4 text-center ${got ? 'border-sun-400 bg-sun-50' : 'border-line bg-white'}`}>
                  <div className={`text-4xl ${got ? '' : 'opacity-30 grayscale'}`} aria-hidden>{b.icon}</div>
                  <div className="mt-2 font-display font-semibold">{b.name}</div>
                  <div className="text-xs text-muted">{got ? 'Unlocked' : b.how}</div>
                </li>
              )
            })}
          </ul>
        </section>

        <section className="panel">
          <h2 className="text-xl font-bold">XP history</h2>
          <ul className="mt-3 divide-y-2 divide-line">
            {Object.entries(s.xpLog).reverse().map(([k, e]) => (
              <li key={k} className="flex justify-between py-2 text-sm"><span>{e.reason}</span><b className="text-sun-600">+{e.amount}</b></li>
            ))}
          </ul>
        </section>
      </div>
    </div>
  )
}
