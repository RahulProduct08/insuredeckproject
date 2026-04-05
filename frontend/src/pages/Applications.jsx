import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import useStore from '../store/useStore.js'
import DataTable from '../components/DataTable.jsx'
import StatusBadge from '../components/StatusBadge.jsx'
import { getProducts, getClients } from '../api.js'
import { PlusIcon, CheckIcon } from '@heroicons/react/20/solid'

const IN_PROGRESS_STATUSES = ['Draft', 'Submitted', 'Underwriting', 'Approved']

const NEXT_STEPS = {
  Draft:       ['Submitted'],
  Submitted:   ['Underwriting', 'Rejected'],
  Underwriting:['Approved', 'Rejected'],
  Approved:    ['Issued', 'Rejected'],
}

const FSM_STAGES = ['Draft', 'Submitted', 'Underwriting', 'Approved', 'Issued']

const COLUMNS = [
  { key: 'client_name',  label: 'Client' },
  { key: 'product_name', label: 'Product' },
  { key: 'status',       label: 'Status',  render: (v) => <StatusBadge status={v} /> },
  { key: 'premium',      label: 'Premium', render: (v) => `$${Number(v).toLocaleString('en-US')}` },
  { key: 'updated_at',   label: 'Updated', render: (v) => v ? new Date(v).toLocaleDateString('en-US') : '—' },
]

function FsmStepper({ currentStatus }) {
  const currentIdx = FSM_STAGES.indexOf(currentStatus)
  return (
    <div className="flex items-center gap-0 mb-4">
      {FSM_STAGES.map((stage, i) => {
        const done    = i < currentIdx
        const active  = i === currentIdx
        const future  = i > currentIdx
        return (
          <React.Fragment key={stage}>
            <div className="flex flex-col items-center">
              <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold transition-colors
                ${done   ? 'bg-brand-600 text-white'
                : active ? 'bg-brand-600 text-white ring-4 ring-brand-100'
                :          'bg-slate-200 text-slate-400'}`}
              >
                {done ? <CheckIcon className="w-3.5 h-3.5" /> : i + 1}
              </div>
              <span className={`text-xs mt-1 font-medium whitespace-nowrap
                ${active ? 'text-brand-600' : done ? 'text-slate-500' : 'text-slate-300'}`}>
                {stage}
              </span>
            </div>
            {i < FSM_STAGES.length - 1 && (
              <div className={`flex-1 h-0.5 mx-1 mb-4 transition-colors
                ${i < currentIdx ? 'bg-brand-600' : 'bg-slate-200'}`} />
            )}
          </React.Fragment>
        )
      })}
    </div>
  )
}

export default function Applications() {
  const navigate = useNavigate()
  const { policies, fetchPolicies, policiesLoading, selectedPolicy, setSelectedPolicy, transitionPolicy, createPolicy } = useStore()
  const [showCreate, setShowCreate] = useState(false)
  const [products, setProductsList] = useState([])
  const [clients, setClientsList] = useState([])
  const [form, setForm] = useState({ client_id: '', product_id: '', premium: '' })
  const [creating, setCreating] = useState(false)
  const [transitioning, setTransitioning] = useState(false)

  useEffect(() => {
    fetchPolicies({ status: IN_PROGRESS_STATUSES.join(',') })
    getProducts().then(setProductsList)
    getClients().then(setClientsList)
  }, [])

  const inProgress = policies.filter(p => IN_PROGRESS_STATUSES.includes(p.status))

  const handleTransition = async (newStatus) => {
    if (!selectedPolicy) return
    setTransitioning(true)
    try {
      await transitionPolicy(selectedPolicy.policy_id, newStatus)
      await fetchPolicies({ status: IN_PROGRESS_STATUSES.join(',') })
      if (['Issued', 'Rejected'].includes(newStatus)) setSelectedPolicy(null)
    } finally {
      setTransitioning(false)
    }
  }

  const handleCreate = async (e) => {
    e.preventDefault()
    setCreating(true)
    try {
      await createPolicy({
        client_id: form.client_id,
        product_id: form.product_id,
        premium: Number(form.premium),
      })
      setShowCreate(false)
      setForm({ client_id: '', product_id: '', premium: '' })
      fetchPolicies({ status: IN_PROGRESS_STATUSES.join(',') })
    } finally {
      setCreating(false)
    }
  }

  const nextSteps = selectedPolicy ? (NEXT_STEPS[selectedPolicy.status] || []) : []
  const selectCls = "w-full px-3 py-2 text-sm bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent"

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="px-6 py-4 border-b border-slate-200 bg-white flex items-center justify-between shrink-0">
        <div>
          <h1 className="text-xl font-semibold text-slate-900">Applications</h1>
          <p className="text-sm text-slate-500">{inProgress.length} in-progress policies</p>
        </div>
        <button
          onClick={() => setShowCreate(true)}
          className="flex items-center gap-1.5 px-3 py-2 text-sm bg-brand-600 text-white rounded-lg hover:bg-brand-700 font-medium transition-colors"
        >
          <PlusIcon className="w-4 h-4" />
          New Application
        </button>
      </div>

      {/* Create Modal */}
      {showCreate && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-sm flex items-center justify-center z-50 animate-fade-in">
          <form onSubmit={handleCreate} className="bg-white rounded-2xl shadow-2xl p-6 w-full max-w-sm space-y-4 animate-slide-up">
            <h2 className="text-base font-semibold text-slate-900">New Application</h2>
            <div>
              <label className="block text-xs font-medium text-slate-500 mb-1">Client</label>
              <select required value={form.client_id} onChange={e => setForm(f => ({ ...f, client_id: e.target.value }))} className={selectCls}>
                <option value="">Select client…</option>
                {clients.map(c => <option key={c.client_id} value={c.client_id}>{c.name}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-500 mb-1">Product</label>
              <select required value={form.product_id} onChange={e => setForm(f => ({ ...f, product_id: e.target.value }))} className={selectCls}>
                <option value="">Select product…</option>
                {products.map(p => <option key={p.product_id} value={p.product_id}>{p.name}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-500 mb-1">Annual Premium ($)</label>
              <input
                type="number" required min="0"
                value={form.premium}
                onChange={e => setForm(f => ({ ...f, premium: e.target.value }))}
                className={selectCls}
              />
            </div>
            <div className="flex gap-2 pt-2">
              <button type="submit" disabled={creating}
                className="flex-1 py-2.5 bg-brand-600 text-white text-sm rounded-lg hover:bg-brand-700 disabled:opacity-50 font-medium transition-colors">
                {creating ? 'Creating…' : 'Create'}
              </button>
              <button type="button" onClick={() => setShowCreate(false)}
                className="flex-1 py-2.5 bg-slate-100 text-slate-700 text-sm rounded-lg hover:bg-slate-200 font-medium transition-colors">
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Main */}
      <div className="flex-1 flex overflow-hidden">
        <div className={`flex flex-col overflow-hidden ${selectedPolicy ? 'w-3/5' : 'w-full'}`}>
          <DataTable
            columns={COLUMNS}
            data={inProgress}
            loading={policiesLoading}
            rowKey="policy_id"
            searchKeys={['client_name', 'product_name', 'status']}
            onRowClick={setSelectedPolicy}
            selected={selectedPolicy}
            emptyText="No in-progress applications."
          />
        </div>

        {selectedPolicy && (
          <div className="w-2/5 flex flex-col border-l border-slate-100 bg-white overflow-y-auto shadow-panel">
            <div className="flex items-center justify-between px-5 py-4 border-b border-slate-100">
              <h3 className="text-base font-semibold text-slate-800">{selectedPolicy.client_name}</h3>
              <button
                onClick={() => setSelectedPolicy(null)}
                className="p-1.5 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg transition-colors"
              >
                ✕
              </button>
            </div>

            <div className="p-5 space-y-5">
              {/* FSM Stepper */}
              <FsmStepper currentStatus={selectedPolicy.status} />

              {/* Status & product */}
              <div className="flex items-center gap-3">
                <StatusBadge status={selectedPolicy.status} size="lg" />
                <span className="text-sm text-slate-600">{selectedPolicy.product_name}</span>
              </div>

              {/* Fields */}
              {[
                ['Premium', `$${Number(selectedPolicy.premium).toLocaleString('en-US')}`],
                ['Created', selectedPolicy.created_at ? new Date(selectedPolicy.created_at).toLocaleDateString('en-US') : '—'],
                ['Updated', selectedPolicy.updated_at ? new Date(selectedPolicy.updated_at).toLocaleDateString('en-US') : '—'],
              ].map(([label, value]) => (
                <div key={label}>
                  <div className="text-xs font-medium text-slate-500">{label}</div>
                  <div className="text-sm text-slate-800 mt-0.5">{value}</div>
                </div>
              ))}

              {/* Status history */}
              {selectedPolicy.status_history?.length > 0 && (
                <div>
                  <div className="text-xs font-medium text-slate-500 mb-2">History</div>
                  <div className="space-y-1">
                    {selectedPolicy.status_history.map((h, i) => (
                      <div key={i} className="text-xs text-slate-600 flex items-center gap-1">
                        <span className="text-slate-400">{h.from_status || 'Created'}</span>
                        <span className="text-slate-300">→</span>
                        <StatusBadge status={h.to_status} />
                        <span className="text-slate-400 ml-auto">{h.changed_at ? new Date(h.changed_at).toLocaleDateString('en-US') : ''}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Advance status */}
              {nextSteps.length > 0 && (
                <div>
                  <div className="text-xs font-medium text-slate-500 mb-2">Advance Status</div>
                  <div className="flex flex-wrap gap-2">
                    {nextSteps.map(status => (
                      <button
                        key={status}
                        disabled={transitioning}
                        onClick={() => handleTransition(status)}
                        className={`px-3 py-1.5 text-xs rounded-lg font-medium transition-colors disabled:opacity-50
                          ${status === 'Rejected'
                            ? 'bg-red-50 text-red-700 hover:bg-red-100 border border-red-200'
                            : 'bg-brand-50 text-brand-700 hover:bg-brand-100 border border-brand-200'}`}
                      >
                        {transitioning ? '…' : `→ ${status}`}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              <button
                onClick={() => navigate(`/clients/${selectedPolicy.client_id}`)}
                className="w-full py-2.5 text-sm text-brand-600 border border-brand-200 rounded-lg hover:bg-brand-50 font-medium transition-colors"
              >
                View Client 360 →
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
