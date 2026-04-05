/**
 * api.js — fetch wrapper for InsureDesk backend.
 */

const BASE = '/api'

function getToken() {
  return localStorage.getItem('insuredesk_token') || ''
}

async function request(method, path, body) {
  const headers = { 'Content-Type': 'application/json' }
  const token = getToken()
  if (token) headers['Authorization'] = `Bearer ${token}`

  const res = await fetch(`${BASE}${path}`, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  })
  const json = await res.json()
  if (!res.ok) throw new Error(json.error || `HTTP ${res.status}`)
  return json
}

function qs(params = {}) {
  const filtered = Object.fromEntries(
    Object.entries(params).filter(([, v]) => v !== undefined && v !== null && v !== '')
  )
  const s = new URLSearchParams(filtered).toString()
  return s ? `?${s}` : ''
}

// Auth
export const login = (body) => fetch(`${BASE}/auth/login`, {
  method: 'POST', headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(body),
}).then(async r => { const j = await r.json(); if (!r.ok) throw new Error(j.error); return j })
export const register = (body) => fetch(`${BASE}/auth/register`, {
  method: 'POST', headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(body),
}).then(async r => { const j = await r.json(); if (!r.ok) throw new Error(j.error); return j })
export const getMe = () => request('GET', '/auth/me')

// Agents
export const getAgents = () => request('GET', '/api/agents')
export const updateAgent = (id, body) => request('PATCH', `/api/agents/${id}`, body)

// Clients
export const getClients = (params) => request('GET', `/clients${qs(params)}`)
export const getClient = (id) => request('GET', `/clients/${id}`)
export const createClient = (body) => request('POST', '/clients', body)
export const updateClient = (id, body) => request('PUT', `/clients/${id}`, body)
export const getClientPolicies = (id) => request('GET', `/clients/${id}/policies`)
export const getClientActivities = (id, params) => request('GET', `/clients/${id}/activities${qs(params)}`)

// Products
export const getProducts = (params) => request('GET', `/products${qs(params)}`)
export const getProduct = (id) => request('GET', `/products/${id}`)
export const createProduct = (body) => request('POST', '/products', body)
export const updateProduct = (id, body) => request('PUT', `/products/${id}`, body)

// Policies
export const getPolicies = (params) => request('GET', `/policies${qs(params)}`)
export const getPolicy = (id) => request('GET', `/policies/${id}`)
export const createPolicy = (body) => request('POST', '/policies', body)
export const updatePolicy = (id, body) => request('PUT', `/policies/${id}`, body)
export const transitionPolicy = (id, body) => request('POST', `/policies/${id}/transition`, body)

// Commissions
export const getCommissions = (params) => request('GET', `/commissions${qs(params)}`)
export const getCommissionSummary = () => request('GET', '/commissions/summary')
export const getCommissionForecast = () => request('GET', '/commissions/forecast')
export const getCommission = (id) => request('GET', `/commissions/${id}`)

// Activities
export const getActivities = (params) => request('GET', `/activities${qs(params)}`)
export const createActivity = (body) => request('POST', '/activities', body)

// Tasks
export const getTasks = (params) => request('GET', `/tasks${qs(params)}`)
export const createTask = (body) => request('POST', '/tasks', body)
export const updateTask = (id, body) => request('PATCH', `/tasks/${id}`, body)
export const deleteTask = (id) => request('DELETE', `/tasks/${id}`)

// Analytics
export const getAnalyticsSummary = (params) => request('GET', `/analytics/summary${qs(params)}`)

// Needs Analysis
export const getNeedsAnalyses = (clientId) => request('GET', `/needs-analysis/client/${clientId}`)
export const createNeedsAnalysis = (body) => request('POST', '/needs-analysis', body)
