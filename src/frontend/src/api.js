// Thin wrapper around the FastAPI backend.
async function call(path, body) {
  const res = await fetch(`/api${path}`, body === undefined ? {} : {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body),
  })
  if (!res.ok) {
    let msg = `${res.status}`
    try { msg = (await res.json()).detail || msg } catch { /* not JSON */ }
    throw new Error(msg)
  }
  return res.json()
}

async function upload(file) {
  const form = new FormData()
  form.append('file', file)
  const res = await fetch('/api/profile/upload', { method: 'POST', body: form })
  if (!res.ok) {
    let msg = `Upload failed (${res.status})`
    try { msg = (await res.json()).detail || msg } catch { /* not JSON */ }
    throw new Error(msg)
  }
  return res.json()
}

export const api = {
  meta: () => call('/meta'),
  parseText: (text) => call('/profile/parse', { text }),
  uploadCv: upload,
  // Sample people go through exactly the same upload + parsing as a real PDF.
  uploadSample: async (id) => {
    const blob = await (await fetch(`/api/sample-cvs/${id}.pdf`)).blob()
    return upload(new File([blob], `${id}.pdf`, { type: 'application/pdf' }))
  },
  sampleCvUrl: (id) => `/api/sample-cvs/${id}.pdf`,
  assessment: () => call('/assessment'),
  scoreAssessment: (answers) => call('/assessment', { answers }),
  forecast: (body) => call('/forecast', body),
  pathway: (body) => call('/pathway', body),
  trends: () => call('/trends'),
  modelExposure: (text) => call('/model/exposure', { text }),
  catchPack: (params) => call(`/catch?${new URLSearchParams(params)}`),
  scoreCatch: (body) => call('/catch', body),
  refreshTrends: () => call('/trends/refresh', {}),
  team: (body) => call('/team', body),
}
