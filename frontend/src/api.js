const BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'
async function request(path, options) {
  const response = await fetch(`${BASE}${path}`, options)
  if (!response.ok) { const body = await response.json().catch(() => ({})); throw new Error(body.detail || 'Request failed') }
  return response.json()
}
export const getSKUs = () => request('/api/skus')
export const getRegions = () => request('/api/regions')
export const getOverview = () => request('/api/overview')
export const runForecast = (payload) => request('/api/forecast', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify(payload) })

