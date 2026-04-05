/**
 * useStore.js
 * -----------
 * Zustand global store — single store with domain slices.
 * Derived state (applications, renewals) is computed in page components with useMemo.
 */

import { create } from 'zustand'
import * as api from '../api.js'

const useStore = create((set, get) => ({

  // ── Clients ──────────────────────────────────────────────────────────────
  clients: [],
  selectedClient: null,
  clientsLoading: false,

  fetchClients: async (params) => {
    set({ clientsLoading: true })
    try {
      const clients = await api.getClients(params)
      set({ clients })
    } catch (e) {
      get().pushToast(e.message, 'error')
    } finally {
      set({ clientsLoading: false })
    }
  },

  fetchClient: async (id) => {
    try {
      const client = await api.getClient(id)
      set({ selectedClient: client })
      return client
    } catch (e) {
      get().pushToast(e.message, 'error')
    }
  },

  createClient: async (body) => {
    try {
      const client = await api.createClient(body)
      set(s => ({ clients: [client, ...s.clients] }))
      get().pushToast('Client added successfully', 'success')
      return client
    } catch (e) {
      get().pushToast(e.message, 'error')
      throw e
    }
  },

  updateClient: async (id, body) => {
    try {
      const updated = await api.updateClient(id, body)
      set(s => ({
        clients: s.clients.map(c => c.client_id === id ? updated : c),
        selectedClient: s.selectedClient?.client_id === id ? updated : s.selectedClient,
      }))
      return updated
    } catch (e) {
      get().pushToast(e.message, 'error')
      throw e
    }
  },

  setSelectedClient: (client) => set({ selectedClient: client }),

  // ── Products ─────────────────────────────────────────────────────────────
  products: [],
  selectedProduct: null,
  productsLoading: false,

  fetchProducts: async (params) => {
    set({ productsLoading: true })
    try {
      const products = await api.getProducts(params)
      set({ products })
    } catch (e) {
      get().pushToast(e.message, 'error')
    } finally {
      set({ productsLoading: false })
    }
  },

  updateProduct: async (id, body) => {
    try {
      const updated = await api.updateProduct(id, body)
      set(s => ({
        products: s.products.map(p => p.product_id === id ? updated : p),
        selectedProduct: s.selectedProduct?.product_id === id ? updated : s.selectedProduct,
      }))
      get().pushToast('Product updated', 'success')
      return updated
    } catch (e) {
      get().pushToast(e.message, 'error')
      throw e
    }
  },

  setSelectedProduct: (product) => set({ selectedProduct: product }),

  // ── Policies ─────────────────────────────────────────────────────────────
  policies: [],
  selectedPolicy: null,
  policiesLoading: false,

  fetchPolicies: async (params) => {
    set({ policiesLoading: true })
    try {
      const policies = await api.getPolicies(params)
      set({ policies })
    } catch (e) {
      get().pushToast(e.message, 'error')
    } finally {
      set({ policiesLoading: false })
    }
  },

  fetchPolicy: async (id) => {
    try {
      const policy = await api.getPolicy(id)
      set({ selectedPolicy: policy })
      return policy
    } catch (e) {
      get().pushToast(e.message, 'error')
    }
  },

  createPolicy: async (body) => {
    try {
      const policy = await api.createPolicy(body)
      set(s => ({ policies: [policy, ...s.policies] }))
      get().pushToast('Policy created', 'success')
      return policy
    } catch (e) {
      get().pushToast(e.message, 'error')
      throw e
    }
  },

  transitionPolicy: async (id, newStatus, agentId = 'AGENT-001') => {
    try {
      const result = await api.transitionPolicy(id, { new_status: newStatus, agent_id: agentId })
      // Refresh the policy in the list
      const updated = await api.getPolicy(id)
      set(s => ({
        policies: s.policies.map(p => p.policy_id === id ? updated : p),
        selectedPolicy: s.selectedPolicy?.policy_id === id ? updated : s.selectedPolicy,
      }))
      get().pushToast(`Status updated to ${newStatus}`, 'success')
      return result
    } catch (e) {
      get().pushToast(e.message, 'error')
      throw e
    }
  },

  setSelectedPolicy: (policy) => set({ selectedPolicy: policy }),

  // ── Commissions ──────────────────────────────────────────────────────────
  commissions: [],
  commissionSummary: { total: 0, sale_total: 0, renewal_total: 0, count: 0 },
  commissionsLoading: false,

  fetchCommissions: async (params) => {
    set({ commissionsLoading: true })
    try {
      const commissions = await api.getCommissions(params)
      set({ commissions })
    } catch (e) {
      get().pushToast(e.message, 'error')
    } finally {
      set({ commissionsLoading: false })
    }
  },

  fetchCommissionSummary: async () => {
    try {
      const summary = await api.getCommissionSummary()
      set({ commissionSummary: summary })
    } catch (e) {
      get().pushToast(e.message, 'error')
    }
  },

  // ── Activities ───────────────────────────────────────────────────────────
  activities: [],
  activitiesLoading: false,

  fetchActivities: async (params) => {
    set({ activitiesLoading: true })
    try {
      const activities = await api.getActivities(params)
      set({ activities })
    } catch (e) {
      get().pushToast(e.message, 'error')
    } finally {
      set({ activitiesLoading: false })
    }
  },

  createActivity: async (body) => {
    try {
      const activity = await api.createActivity(body)
      set(s => ({ activities: [activity, ...s.activities] }))
      get().pushToast('Note logged', 'success')
      return activity
    } catch (e) {
      get().pushToast(e.message, 'error')
      throw e
    }
  },

  // ── Toast notifications ──────────────────────────────────────────────────
  toasts: [],

  pushToast: (msg, type = 'info') =>
    set(s => ({ toasts: [...s.toasts, { id: Date.now() + Math.random(), msg, type }] })),

  removeToast: (id) =>
    set(s => ({ toasts: s.toasts.filter(t => t.id !== id) })),

}))

export default useStore
