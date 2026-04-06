/**
 * useStore.js — Zustand global store for InsureDesk.
 */

import { create } from 'zustand'
import * as api from '../api.js'

const useStore = create((set, get) => ({

  // ── Auth ──────────────────────────────────────────────────────────────────
  agent: JSON.parse(localStorage.getItem('insuredesk_agent') || 'null'),
  authLoading: false,

  login: async (email, password) => {
    set({ authLoading: true })
    try {
      const { token, agent } = await api.login({ email, password })
      localStorage.setItem('insuredesk_token', token)
      localStorage.setItem('insuredesk_agent', JSON.stringify(agent))
      set({ agent })
      return agent
    } catch (e) {
      get().pushToast(e.message, 'error')
      throw e
    } finally {
      set({ authLoading: false })
    }
  },

  logout: () => {
    localStorage.removeItem('insuredesk_token')
    localStorage.removeItem('insuredesk_agent')
    set({ agent: null })
  },

  // ── Clients ───────────────────────────────────────────────────────────────
  clients: [],
  selectedClient: null,
  clientsLoading: false,

  fetchClients: async (params) => {
    set({ clientsLoading: true })
    try { set({ clients: await api.getClients(params) }) }
    catch (e) { get().pushToast(e.message, 'error') }
    finally { set({ clientsLoading: false }) }
  },

  fetchClient: async (id) => {
    try {
      const client = await api.getClient(id)
      set({ selectedClient: client })
      return client
    } catch (e) { get().pushToast(e.message, 'error') }
  },

  createClient: async (body) => {
    try {
      const client = await api.createClient(body)
      set(s => ({ clients: [client, ...s.clients] }))
      get().pushToast('Client added', 'success')
      return client
    } catch (e) { get().pushToast(e.message, 'error'); throw e }
  },

  updateClient: async (id, body) => {
    try {
      const updated = await api.updateClient(id, body)
      set(s => ({
        clients: s.clients.map(c => c.client_id === id ? updated : c),
        selectedClient: s.selectedClient?.client_id === id ? updated : s.selectedClient,
      }))
      return updated
    } catch (e) { get().pushToast(e.message, 'error'); throw e }
  },

  setSelectedClient: (client) => set({ selectedClient: client }),

  // ── Products ──────────────────────────────────────────────────────────────
  products: [],
  selectedProduct: null,
  productsLoading: false,

  fetchProducts: async (params) => {
    set({ productsLoading: true })
    try { set({ products: await api.getProducts(params) }) }
    catch (e) { get().pushToast(e.message, 'error') }
    finally { set({ productsLoading: false }) }
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
    } catch (e) { get().pushToast(e.message, 'error'); throw e }
  },

  setSelectedProduct: (product) => set({ selectedProduct: product }),

  // ── Policies ──────────────────────────────────────────────────────────────
  policies: [],
  selectedPolicy: null,
  policiesLoading: false,

  fetchPolicies: async (params) => {
    set({ policiesLoading: true })
    try { set({ policies: await api.getPolicies(params) }) }
    catch (e) { get().pushToast(e.message, 'error') }
    finally { set({ policiesLoading: false }) }
  },

  fetchPolicy: async (id) => {
    try {
      const policy = await api.getPolicy(id)
      set({ selectedPolicy: policy })
      return policy
    } catch (e) { get().pushToast(e.message, 'error') }
  },

  createPolicy: async (body) => {
    try {
      const policy = await api.createPolicy(body)
      set(s => ({ policies: [policy, ...s.policies] }))
      get().pushToast('Policy created', 'success')
      return policy
    } catch (e) { get().pushToast(e.message, 'error'); throw e }
  },

  transitionPolicy: async (id, newStatus) => {
    const agent = get().agent
    try {
      await api.transitionPolicy(id, { new_status: newStatus, agent_id: agent?.agent_id })
      const updated = await api.getPolicy(id)
      set(s => ({
        policies: s.policies.map(p => p.policy_id === id ? updated : p),
        selectedPolicy: s.selectedPolicy?.policy_id === id ? updated : s.selectedPolicy,
      }))
      get().pushToast(`Status → ${newStatus}`, 'success')
    } catch (e) { get().pushToast(e.message, 'error'); throw e }
  },

  setSelectedPolicy: (policy) => set({ selectedPolicy: policy }),

  // ── Commissions ───────────────────────────────────────────────────────────
  commissions: [],
  commissionSummary: { total: 0, sale_total: 0, renewal_total: 0, count: 0 },
  commissionForecast: null,
  commissionsLoading: false,

  fetchCommissions: async (params) => {
    set({ commissionsLoading: true })
    try { set({ commissions: await api.getCommissions(params) }) }
    catch (e) { get().pushToast(e.message, 'error') }
    finally { set({ commissionsLoading: false }) }
  },

  fetchCommissionSummary: async () => {
    try { set({ commissionSummary: await api.getCommissionSummary() }) }
    catch (e) { get().pushToast(e.message, 'error') }
  },

  fetchCommissionForecast: async () => {
    try { set({ commissionForecast: await api.getCommissionForecast() }) }
    catch (e) { get().pushToast(e.message, 'error') }
  },

  // ── Activities ────────────────────────────────────────────────────────────
  activities: [],
  activitiesLoading: false,

  fetchActivities: async (params) => {
    set({ activitiesLoading: true })
    try { set({ activities: await api.getActivities(params) }) }
    catch (e) { get().pushToast(e.message, 'error') }
    finally { set({ activitiesLoading: false }) }
  },

  createActivity: async (body) => {
    try {
      const activity = await api.createActivity(body)
      set(s => ({ activities: [activity, ...s.activities] }))
      get().pushToast('Note logged', 'success')
      return activity
    } catch (e) { get().pushToast(e.message, 'error'); throw e }
  },

  // ── Tasks ─────────────────────────────────────────────────────────────────
  tasks: [],
  tasksLoading: false,

  fetchTasks: async (params) => {
    set({ tasksLoading: true })
    try { set({ tasks: await api.getTasks(params) }) }
    catch (e) { get().pushToast(e.message, 'error') }
    finally { set({ tasksLoading: false }) }
  },

  createTask: async (body) => {
    try {
      const task = await api.createTask(body)
      set(s => ({ tasks: [task, ...s.tasks] }))
      get().pushToast('Task created', 'success')
      return task
    } catch (e) { get().pushToast(e.message, 'error'); throw e }
  },

  updateTask: async (id, body) => {
    try {
      const updated = await api.updateTask(id, body)
      set(s => ({ tasks: s.tasks.map(t => t.task_id === id ? updated : t) }))
      if (body.status === 'completed') get().pushToast('Task completed!', 'success')
      return updated
    } catch (e) { get().pushToast(e.message, 'error'); throw e }
  },

  deleteTask: async (id) => {
    try {
      await api.deleteTask(id)
      set(s => ({ tasks: s.tasks.filter(t => t.task_id !== id) }))
    } catch (e) { get().pushToast(e.message, 'error') }
  },

  // ── Analytics ─────────────────────────────────────────────────────────────
  analytics: null,
  analyticsLoading: false,

  fetchAnalytics: async (params) => {
    set({ analyticsLoading: true })
    try { set({ analytics: await api.getAnalyticsSummary(params) }) }
    catch (e) { get().pushToast(e.message, 'error') }
    finally { set({ analyticsLoading: false }) }
  },

  // ── Hierarchy Graph ───────────────────────────────────────────────────────
  hierarchyGraph: { nodes: [], edges: [] },
  hierarchyLoading: false,

  fetchHierarchyGraph: async () => {
    set({ hierarchyLoading: true })
    try { set({ hierarchyGraph: await api.getHierarchyGraph() }) }
    catch (e) { get().pushToast(e.message, 'error') }
    finally { set({ hierarchyLoading: false }) }
  },

  createHierarchyLink: async (body) => {
    try {
      await api.createHierarchyLink(body)
      get().pushToast('Hierarchy link created', 'success')
      await get().fetchHierarchyGraph()
    } catch (e) { get().pushToast(e.message, 'error'); throw e }
  },

  deleteHierarchyLink: async (id) => {
    try {
      await api.deleteHierarchyLink(id)
      get().pushToast('Link removed', 'success')
      await get().fetchHierarchyGraph()
    } catch (e) { get().pushToast(e.message, 'error') }
  },

  // ── Commission Ledger ─────────────────────────────────────────────────────
  ledger: [],
  ledgerSummary: { base_total: 0, override_total: 0, grand_total: 0 },
  ledgerFlow: [],
  ledgerLoading: false,

  fetchLedger: async (params) => {
    set({ ledgerLoading: true })
    try { set({ ledger: await api.getLedger(params) }) }
    catch (e) { get().pushToast(e.message, 'error') }
    finally { set({ ledgerLoading: false }) }
  },

  fetchLedgerSummary: async () => {
    try { set({ ledgerSummary: await api.getLedgerSummary() }) }
    catch (e) { get().pushToast(e.message, 'error') }
  },

  fetchLedgerFlow: async (policyId) => {
    try { set({ ledgerFlow: await api.getLedgerFlow(policyId) }) }
    catch (e) { get().pushToast(e.message, 'error') }
  },

  // ── Toast ─────────────────────────────────────────────────────────────────
  toasts: [],
  pushToast: (msg, type = 'info') =>
    set(s => ({ toasts: [...s.toasts, { id: Date.now() + Math.random(), msg, type }] })),
  removeToast: (id) =>
    set(s => ({ toasts: s.toasts.filter(t => t.id !== id) })),

}))

export default useStore
