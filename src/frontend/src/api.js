// Thin wrapper around the FastAPI backend.
async function call(path, body) {
  const res = await fetch(`/api${path}`, body === undefined ? {} : {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body),
  })
  if (!res.ok) throw new Error(`${path}: ${res.status} ${await res.text()}`)
  return res.json()
}

export const api = {
  meta: () => call('/meta'),
  parse: (text) => call('/profile/parse', { text }),
  assessment: () => call('/assessment'),
  scoreAssessment: (answers) => call('/assessment', { answers }),
  forecast: (body) => call('/forecast', body),
  pathway: (body) => call('/pathway', body),
  trends: () => call('/trends'),
  refreshTrends: () => call('/trends/refresh', {}),
}
