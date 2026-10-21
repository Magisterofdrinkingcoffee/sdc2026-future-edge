// Gamification rules: XP, levels, streaks and badges. Pure functions, easy to test and tweak.

export const XP = {
  cv: 50,          // uploaded / chose a CV
  goal: 20,        // picked a goal role
  quiz: 100,       // finished the Edge Check
  course: 60,
  project: 120,
  experience: 100,
}

// Level n starts at LEVELS[n-1].xp
export const LEVELS = [
  { xp: 0, name: 'Starter' },
  { xp: 100, name: 'Explorer' },
  { xp: 250, name: 'Apprentice' },
  { xp: 450, name: 'Builder' },
  { xp: 700, name: 'Specialist' },
  { xp: 1000, name: 'Pathfinder' },
  { xp: 1400, name: 'Future-proof' },
  { xp: 1900, name: 'Edge master' },
]

export function totalXp(xpLog) {
  return Object.values(xpLog).reduce((s, e) => s + e.amount, 0)
}

export function levelInfo(xp) {
  let i = 0
  while (i + 1 < LEVELS.length && xp >= LEVELS[i + 1].xp) i++
  const cur = LEVELS[i]
  const next = LEVELS[i + 1]
  return {
    level: i + 1,
    name: cur.name,
    into: xp - cur.xp,
    needed: next ? next.xp - cur.xp : 0,
    progress: next ? (xp - cur.xp) / (next.xp - cur.xp) : 1,
    nextName: next?.name,
  }
}

export const today = () => new Date().toISOString().slice(0, 10)

// Consecutive days with activity, ending today (or yesterday, so it isn't lost before you act today).
export function streak(days) {
  const set = new Set(days)
  const d = new Date()
  if (!set.has(today())) d.setDate(d.getDate() - 1)
  let n = 0
  while (set.has(d.toISOString().slice(0, 10))) { n++; d.setDate(d.getDate() - 1) }
  return n
}

export const BADGES = [
  { id: 'first_steps', icon: '🧭', name: 'First steps', how: 'Add your CV' },
  { id: 'know_yourself', icon: '🪞', name: 'Know yourself', how: 'Finish the Edge Check' },
  { id: 'forecaster', icon: '🔭', name: 'Forecaster', how: 'Compare both AI scenarios' },
  { id: 'first_quest', icon: '✅', name: 'First quest', how: 'Finish any quest' },
  { id: 'builder', icon: '🛠️', name: 'Builder', how: 'Finish a project quest' },
  { id: 'people_person', icon: '🤝', name: 'People person', how: 'Finish an experience quest' },
  { id: 'sharp_mind', icon: '🧠', name: 'Sharp mind', how: 'Score 80%+ judgment in the Edge Check' },
  { id: 'rare_mix', icon: '💎', name: 'Rare mix', how: 'Have skills in all 4 skill types' },
  { id: 'edge_up', icon: '📈', name: 'Edge +10', how: 'Raise your future Edge by 10 points' },
  { id: 'halfway', icon: '🏔️', name: 'Halfway there', how: 'Finish half of your quests' },
  { id: 'trend_watcher', icon: '📡', name: 'Trend watcher', how: 'Refresh or play with the trend data' },
]

export function earnedBadges(s) {
  const done = s.questsDone || []
  const types = new Set(done.map((q) => q.type))
  const e = []
  if (Object.keys(s.skills || {}).length) e.push('first_steps')
  if (s.assessment) e.push('know_yourself')
  if (s.flags?.bothScenarios) e.push('forecaster')
  if (done.length >= 1) e.push('first_quest')
  if (types.has('project')) e.push('builder')
  if (types.has('experience')) e.push('people_person')
  if ((s.assessment?.judgment ?? 0) >= 0.8) e.push('sharp_mind')
  if (s.categories >= 4) e.push('rare_mix')
  if (s.edgeGain >= 10) e.push('edge_up')
  if (s.questTotal && done.length >= s.questTotal / 2) e.push('halfway')
  if (s.flags?.trends) e.push('trend_watcher')
  return e
}

// Career "weather" for a score – the forecast metaphor used across the app.
export function weather(score) {
  if (score >= 60) return { icon: '☀️', label: 'Clear skies', tone: 'text-sprout-600' }
  if (score >= 45) return { icon: '🌤️', label: 'Mostly sunny', tone: 'text-sprout-600' }
  if (score >= 30) return { icon: '⛅', label: 'Some clouds', tone: 'text-sun-600' }
  if (score >= 15) return { icon: '🌧️', label: 'Rain likely', tone: 'text-coral-600' }
  return { icon: '⛈️', label: 'Storm warning', tone: 'text-coral-600' }
}

export const TYPE = {
  course: { icon: '📘', label: 'Course', why: 'Learn it', color: 'sky' },
  project: { icon: '🛠️', label: 'Project', why: 'Prove it', color: 'violet' },
  experience: { icon: '🤝', label: 'Experience', why: 'Live it', color: 'sun' },
}

export const FIELD_ICON = {
  'Digital & ICT': '💻', 'Energy & Sustainability': '⚡', Manufacturing: '🏭', Finance: '💰',
  Services: '🧾', 'Science, Health & Agriculture': '🔬', 'Engineering & Construction': '🏗️',
}

// "+82%" / "−26%" / "growing" label for a role's WEF job outlook
export function growthLabel(outlook) {
  if (!outlook) return null
  const g = outlook.malaysia_net_growth_2030 ?? outlook.net_growth_2030
  if (g != null) return { text: `${g > 0 ? '+' : g < 0 ? '−' : ''}${Math.abs(g)}% jobs by 2030`, up: g > 0, down: g < 0, my: outlook.malaysia_net_growth_2030 != null }
  if (outlook.direction) return { text: outlook.direction === 'growing' ? 'Fast-growing job' : 'Fast-declining job', up: outlook.direction === 'growing', down: outlook.direction === 'declining' }
  return null
}
