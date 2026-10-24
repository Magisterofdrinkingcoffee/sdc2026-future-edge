import { FactCard, ForecastStrip, Logo } from '../ui'

const EXAMPLE = [{ year: 0, edge: 64 }, { year: 1, edge: 55 }, { year: 2, edge: 44 }, { year: 3, edge: 33 }]

export default function Welcome({ set, s, meta }) {
  const started = Object.keys(s.profile.skills).length > 0
  return (
    <div className="min-h-screen">
      <header className="mx-auto flex max-w-5xl items-center justify-between px-4 py-6">
        <Logo />
        {started && <button className="btn-white py-2 text-sm" onClick={() => set({ stage: 'app' })}>Continue my quests</button>}
      </header>
      <main className="mx-auto grid max-w-5xl items-center gap-10 px-4 pb-16 pt-6 lg:grid-cols-2">
        <div>
          <h1 className="text-4xl font-bold leading-tight sm:text-5xl">What will AI do to your career in the next 3 years?</h1>
          <p className="mt-4 max-w-md text-lg text-muted">
            Upload your CV and get a career forecast: which of your skills AI will take over, which will keep you valuable,
            and a quest map of small steps to stay ahead.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <button className="btn-violet px-8 text-lg" onClick={() => set({ stage: 'cv' })}>{started ? 'Start over with a new CV' : 'Get my forecast'}</button>
            <button className="btn-white px-6 text-lg" onClick={() => set({ stage: 'team' })}>🏢 For HR &amp; L&amp;D teams</button>
          </div>
          <p className="mt-4 text-sm text-muted">Takes about 3 minutes. Your CV is read once and not stored.</p>
        </div>
        <div className="panel">
          <div className="mb-3 flex items-center justify-between">
            <div className="font-display text-lg font-semibold">Example: data entry clerk</div>
            <span className="chip bg-canvas text-muted">Example</span>
          </div>
          <ForecastStrip timeline={EXAMPLE} animate />
          <p className="mt-4 text-sm text-muted">Your Edge Score shows how hard you'll be to replace by AI, from 0 to 100. Each year gets its own forecast.</p>
        </div>
      </main>
      <section className="mx-auto max-w-5xl px-4 pb-16">
        <h2 className="text-2xl font-bold">Malaysia's job market is already changing</h2>
        <p className="mt-1 text-muted">Real numbers from the World Economic Forum and the Department of Statistics Malaysia.</p>
        <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {meta.facts.filter((f) => ['analytical', 'data_entry', 'ai_jobs', 'human_tasks'].includes(f.id)).map((f) => <FactCard key={f.id} fact={f} />)}
        </div>
      </section>
    </div>
  )
}
