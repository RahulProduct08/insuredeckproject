/**
 * api.js
 * ------
 * Thin fetch wrapper for all backend endpoints.
 * All functions return parsed JSON or throw an Error with the server message.
 */

const BASE = '/api'

async function request(method, path, body) {
  const res = await fetch(`${BASE}${path}`, {
    method,
    headers: { 'Content-Type': 'application/json' },
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

// ---------------------------------------------------------------------------
// Clients
// ---------------------------------------------------------------------------
export const getClients = (params) => request('GET', `/clients${qs(params)}`)
export const getClient = (id) => request('GET', `/clients/${id}`)
export const createClient = (body) => request('POST', '/clients', body)
export const updateClient = (id, body) => request('PUT', `/clients/${id}`, body)
export const getClientPolicies = (id) => request('GET', `/clients/${id}/policies`)
export const getClientActivities = (id, params) => request('GET', `/clients/${id}/activities${qs(params)}`)

// ---------------------------------------------------------------------------
// Products
// ---------------------------------------------------------------------------
export const getProducts = (params) => request('GET', `/products${qs(params)}`)
export const getProduct = (id) => request('GET', `/products/${id}`)
export const createProduct = (body) => request('POST', '/products', body)
export const updateProduct = (id, body) => request('PUT', `/products/${id}`, body)

// ---------------------------------------------------------------------------
// Policies
// ---------------------------------------------------------------------------
export const getPolicies = (params) => request('GET', `/policies${qs(params)}`)
export const getPolicy = (id) => request('GET', `/policies/${id}`)
export const createPolicy = (body) => request('POST', '/policies', body)
export const updatePolicy = (id, body) => request('PUT', `/policies/${id}`, body)
export const transitionPolicy = (id, body) => request('POST', `/policies/${id}/transition`, body)

// ---------------------------------------------------------------------------
// Commissions
// ---------------------------------------------------------------------------
export const getCommissions = (params) => request('GET', `/commissions${qs(params)}`)
export const getCommissionSummary = () => request('GET', '/commissions/summary')
export const getCommission = (id) => request('GET', `/commissions/${id}`)

// ---------------------------------------------------------------------------
// Activities
// ---------------------------------------------------------------------------
export const getActivities = (params) => request('GET', `/activities${qs(params)}`)
export const createActivity = (body) => request('POST', '/activities', body)
