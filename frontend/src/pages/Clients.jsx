import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import useStore from '../store/useStore.js'
import DataTable from '../components/DataTable.jsx'
import DetailPanel from '../components/DetailPanel.jsx'
import StatusBadge from '../components/StatusBadge.jsx'
import { PlusIcon } from '@heroicons/react/20/solid'

function initials(name = '') {
  return name.split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase()
}

const AVATAR_COLORS = [
  'bg-brand-600', 'bg-violet-600', 'bg-teal-600',
  'bg-amber-600', 'bg-rose-600',   'bg-indigo-600',
]
function avatarColor(name = '') {
  let hash = 0
  for (const c of name) hash = (hash * 31 + c.charCodeAt(0)) & 0xffff
  return AVATAR_COLORS[hash % AVATAR_COLORS.length]
}

function AvatarCell({ name }) {
  return (
    <div className="flex items-center gap-2.5">
      <div className={`w-7 h-7 rounded-full ${avatarColor(name)} flex items-center justify-center shrink-0`}>
        <span className="text-xs font-bold text-white">{initials(name)}</span>
      </div>
      <span className="font-medium text-slate-800">{name}</span>
    </div>
  )
}

const COLUMNS = [
  { key: 'name', label: 'Name', render: (v) => <AvatarCell name={v} /> },
  { key: 'stage', label: 'Stage', render: (v) => <StatusBadge status={v} /> },
  { key: 'phone', label: 'Phone' },
  { key: 'income', label: 'Income', render: (v) => v ? `$${Number(v).toLocaleString('en-US')}` : '—' },
  { key: 'age', label: 'Age' },
]

const DETAIL_FIELDS = [
  { key: 'name',          label: 'Full Name',         editable: true },
  { key: 'phone',         label: 'Phone',              editable: true },
  { key: 'email',         label: 'Email',              editable: true },
  { key: 'age',           label: 'Age',                editable: true, type: 'number' },
  { key: 'income',        label: 'Annual Income ($)',  editable: true, type: 'number', currency: true },
  { key: 'dependents',    label: 'Dependents',         editable: true, type: 'number' },
  {
    key: 'risk_appetite', label: 'Risk Appetite',      editable: true, type: 'select',
    options: ['low', 'moderate', 'high'],
  },
  {
    key: 'stage',         label: 'Pipeline Stage',     editable: true, type: 'select',
    options: ['Lead', 'Qualified', 'Proposal', 'Negotiation', 'Closed'],
  },
]

const FIELD_LABELS = {
  name: 'Full Name', phone: 'Phone', email: 'Email',
  age: 'Age', income: 'Annual Income ($)',
}

export default function Clients() {
  const navigate = useNavigate()
  const { clients, fetchClients, clientsLoading, selectedClient, setSelectedClient, createClient, updateClient } = useStore()
  const [showCreate, setShowCreate] = useState(false)
  const [form, setForm] = useState({ name: '', phone: '', email: '', age: '', income: '' })
  const [creating, setCreating] = useState(false)

  useEffect(() => { fetchClients() }, [])

  const handleSave = async (patch) => {
    await updateClient(selectedClient.client_id, patch)
    await fetchClients()
  }

  const handleCreate = async (e) => {
    e.preventDefault()
    setCreating(true)
    try {
      await createClient({
        ...form,
        age: form.age ? Number(form.age) : undefined,
        income: form.income ? Number(form.income) : undefined,
      })
      setShowCreate(false)
      setForm({ name: '', phone: '', email: '', age: '', income: '' })
      fetchClients()
    } finally {
      setCreating(false)
    }
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="px-6 py-4 border-b border-slate-200 bg-white flex items-center justify-between shrink-0">
        <div>
          <h1 className="text-xl font-semibold text-slate-900">Leads / Clients</h1>
          <p className="text-sm text-slate-500">{clients.length} total clients</p>
        </div>
        <button
          onClick={() => setShowCreate(true)}
          className="flex items-center gap-1.5 px-3 py-2 text-sm bg-brand-600 text-white rounded-lg hover:bg-brand-700 font-medium transition-colors"
        >
          <PlusIcon className="w-4 h-4" />
          Add Client
        </button>
      </div>

      {/* Create Modal */}
      {showCreate && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-sm flex items-center justify-center z-50 animate-fade-in">
          <form onSubmit={handleCreate} className="bg-white rounded-2xl shadow-2xl p-6 w-full max-w-sm space-y-4 animate-slide-up">
            <h2 className="text-base font-semibold text-slate-900">New Client</h2>
            {['name', 'phone', 'email', 'age', 'income'].map(field => (
              <div key={field}>
                <label className="block text-xs font-medium text-slate-500 mb-1">
                  {FIELD_LABELS[field]}
                  {['name', 'phone', 'email'].includes(field) && (
                    <span className="text-red-400 ml-0.5">*</span>
                  )}
                </label>
                <input
                  type={['age', 'income'].includes(field) ? 'number' : 'text'}
                  required={['name', 'phone', 'email'].includes(field)}
                  value={form[field]}
                  onChange={e => setForm(f => ({ ...f, [field]: e.target.value }))}
                  className="w-full px-3 py-2 text-sm bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent transition-shadow"
                />
              </div>
            ))}
            <div className="flex gap-2 pt-2">
              <button
                type="submit"
                disabled={creating}
                className="flex-1 py-2.5 bg-brand-600 text-white text-sm rounded-lg hover:bg-brand-700 disabled:opacity-50 font-medium transition-colors"
              >
                {creating ? 'Adding…' : 'Add Client'}
              </button>
              <button
                type="button"
                onClick={() => setShowCreate(false)}
                className="flex-1 py-2.5 bg-slate-100 text-slate-700 text-sm rounded-lg hover:bg-slate-200 font-medium transition-colors"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Main content */}
      <div className="flex-1 flex overflow-hidden">
        <div className={`flex flex-col overflow-hidden ${selectedClient ? 'w-3/5' : 'w-full'}`}>
          <DataTable
            columns={COLUMNS}
            data={clients}
            loading={clientsLoading}
            rowKey="client_id"
            searchKeys={['name', 'phone', 'email']}
            onRowClick={(row) => setSelectedClient(row)}
            selected={selectedClient}
            emptyText="No clients yet. Add one to get started."
          />
        </div>

        {selectedClient && (
          <div className="w-2/5 flex flex-col overflow-hidden">
            <DetailPanel
              title={selectedClient.name}
              item={selectedClient}
              fields={DETAIL_FIELDS}
              onSave={handleSave}
              onClose={() => setSelectedClient(null)}
            >
              <button
                onClick={() => navigate(`/clients/${selectedClient.client_id}`)}
                className="w-full py-2.5 text-sm text-brand-600 border border-brand-200 rounded-lg hover:bg-brand-50 font-medium transition-colors"
              >
                Open Client 360 →
              </button>
            </DetailPanel>
          </div>
        )}
      </div>
    </div>
  )
}
