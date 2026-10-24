import { t } from '../../i18n'
import { FIELD_ICON, XP } from '../../game'
import { CriticalChip, GrowthChip, WizardFrame } from '../ui'

export default function GoalStep({ s, set, meta, award }) {
  const fields = [...new Set(meta.roles.map((r) => r.field))]
  const pick = (id) => {
    set((p) => ({ profile: { ...p.profile, goal_role: id }, completed: [], history: [] }))
    award('goal', XP.goal, 'Goal chosen')
    set({ stage: 'quiz' })
  }
  return (
    <WizardFrame step={2} total={4} onBack={() => set({ stage: 'cv' })}>
      <h1 className="text-3xl font-bold">{t("Where do you want to be?")}</h1>
      <p className="mt-2 text-muted">Pick the role you're aiming for. You can change it later. Job growth is from the WEF Future of Jobs Report 2025; 🇲🇾 marks jobs on Malaysia's Critical Occupations List (MyCOL 2024/25).</p>

      <button onClick={() => pick('')} className="option mt-6 flex items-center gap-3">
        <span className="text-3xl" aria-hidden>🧭</span>
        <span><span className="block font-display text-lg">{t("Not sure yet, suggest one for me")}</span>
          <span className="text-sm font-normal text-muted">{t("We'll pick the role where you'll have the strongest edge in 3 years, skipping roles AI is taking over.")}</span></span>
      </button>

      {fields.map((f) => (
        <section key={f} className="mt-8">
          <h2 className="mb-3 text-lg font-bold">{FIELD_ICON[f]} {f}</h2>
          <div className="grid gap-3 sm:grid-cols-2">
            {meta.roles.filter((r) => r.field === f).map((r) => (
              <button key={r.id} onClick={() => pick(r.id)} className={`option ${s.profile.goal_role === r.id ? 'option-on' : ''}`}>
                <span className="block">{r.title}</span>
                <span className="mt-1 flex flex-wrap gap-1"><GrowthChip outlook={r.outlook} /><CriticalChip mycol={r.mycol} /></span>
              </button>
            ))}
          </div>
        </section>
      ))}
    </WizardFrame>
  )
}
