import React, { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import useStore from '../store/useStore.js'
import StatusBadge from '../components/StatusBadge.jsx'
import ActivityFeed from '../components/ActivityFeed.jsx'
import DataTable from '../components/DataTable.jsx'
import { getClientPolicies, getClientActivities, createActivity } from '../api.js'
import { ArrowLeftIcon } from '@heroicons/react/20/solid'

const POLICY_COLUMNS = [
  { key: 'product_name', label: 'Product' },
  { key: 'status',       label: 'Status',  render: (v) => <StatusBadge status={v} /> },
  { key: 'premium',      label: 'Premium', render: (v) => `$${Number(v).toLocaleString('en-US')}` },
  { key: 'created_at',   label: 'Created', render: (v) => v ? new Date(v).toLocaleDateString('en-US') : '—' },
]

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

export default function ClientDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { fetchClient, selectedClient } = useStore()
  const [tab, setTab] = useState('policies')
  const [policies, setPolicies] = useState([])
  const [activities, setActivities] = useState([])
  const [loading, setLoading] = useState(true)
  const [noteText, setNoteText] = useState('')
  const [addingNote, setAddingNote] = useState(false)

  useEffect(() => {
    const load = async () => {
      setLoading(true)
      await fetchClient(id)
      const [pols, acts] = await Promise.all([
        getClientPolicies(id),
        getClientActivities(id, { limit: 50 }),
      ])
      setPolicies(pols)
      setActivities(acts)
      setLoading(false)
    }
    load()
  }, [id])

  const refreshActivities = async () => {
    const acts = await getClientActivities(id, { limit: 50 })
    setActivities(acts)
  }

  const handleLogNote = async (e) => {
    e.preventDefault()
    if (!noteText.trim()) return
    setAddingNote(true)
    try {
      await createActivity({ client_id: id, description: noteText, activity_type: 'note' })
      setNoteText('')
      await refreshActivities()
    } finally {
      setAddingNote(false)
    }
  }

  const client = selectedClient?.client_id === id ? selectedClient : null

  if (loading) {
    return (
      <div className="flex flex-col h-full">
        <div className="h-44 skeleton" />
        <div className="p-6 space-y-4">
          {[1,2,3].map(i => <div key={i} className="skeleton h-12 rounded-xl" />)}
        </div>
      </div>
    )
  }

  if (!client) {
    return <div className="flex items-center justify-center h-full text-slate-400 text-sm">Client not found.</div>
  }

  const issuedPolicies = policies.filter(p => p.status === 'Issued').length
  const inProgressPolicies = policies.filter(p => ['Draft','Submitted','Underwriting','Approved'].includes(p.status)).length

  return (
    <div className="flex flex-col h-full">
      {/* Hero header */}
      <div className={`shrink-0 bg-gradient-to-br from-brand-600 to-brand-800 px-6 pt-4 pb-6`}>
        <button
          onClick={() => navigate('/clients')}
          className="flex items-center gap-1.5 text-xs text-brand-200 hover:text-white mb-4 transition-colors"
        >
          <ArrowLeftIcon className="w-3.5 h-3.5" />
          Back to Clients
        </button>
        <div className="flex items-center gap-4">
          <div className={`w-14 h-14 rounded-2xl bg-white/20 border-2 border-white/30 flex items-center justify-center shrink-0`}>
            <span className="text-xl font-bold text-white">{initials(client.name)}</span>
          </div>
          <div className="flex-1 min-w-0">
            <h1 className="text-2xl font-bold text-white truncate">{client.name}</h1>
            <div className="flex items-center gap-2 mt-1 text-sm text-brand-200 flex-wrap">
              <span>{client.phone}</span>
              <span className="opacity-40">·</span>
              <span>{client.email}</span>
              {client.age && <><span className="opacity-40">·</span><span>{client.age} yrs</span></>}
            </div>
          </div>
          <StatusBadge status={client.stage} size="lg" />
        </div>

        {/* Stats chips */}
        <div className="flex gap-3 mt-5 flex-wrap">
          {[
            { label: 'Policies',    value: policies.length },
            { label: 'Active',      value: issuedPolicies },
            { label: 'In Progress', value: inProgressPolicies },
            { label: 'Dependents',  value: client.dependents ?? '—' },
            { label: 'Risk',        value: client.risk_appetite ?? '—', capitalize: true },
            ...(client.income ? [{ label: 'Income', value: `$${Number(client.income).toLocaleString('en-US')}` }] : []),
          ].map(stat => (
            <div key={stat.label} className="bg-white/10 rounded-lg px-3 py-1.5 text-center">
              <div className="text-xs text-brand-200">{stat.label}</div>
              <div className={`text-sm font-semibold text-white ${stat.capitalize ? 'capitalize' : ''}`}>
                {stat.value}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-slate-200 bg-white px-6 shrink-0">
        <div className="flex gap-6">
          {['policies', 'activity'].map(t => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`py-3 text-sm font-medium border-b-2 transition-colors capitalize
                ${tab === t
                  ? 'border-brand-600 text-brand-600'
                  : 'border-transparent text-slate-500 hover:text-slate-700'}`}
            >
              {t === 'policies' ? `Policies (${policies.length})` : 'Activity Timeline'}
            </button>
          ))}
        </div>
      </div>

      {/* Tab content */}
      <div className="flex-1 overflow-hidden">
        {tab === 'policies' && (
          <DataTable
            columns={POLICY_COLUMNS}
            data={policies}
            rowKey="policy_id"
            searchKeys={['product_name', 'status']}
            emptyText="No policies yet."
          />
        )}

        {tab === 'activity' && (
          <div className="h-full overflow-y-auto p-6">
            <form onSubmit={handleLogNote} className="flex gap-2 mb-6">
              <input
                type="text"
                placeholder="Log a note or call…"
                value={noteText}
                onChange={e => setNoteText(e.target.value)}
                className="flex-1 px-3 py-2 text-sm bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent transition-shadow"
              />
              <button
                type="submit"
                disabled={addingNote || !noteText.trim()}
                className="px-4 py-2 text-sm bg-brand-600 text-white rounded-lg hover:bg-brand-700 disabled:opacity-50 font-medium transition-colors"
              >
                {addingNote ? '…' : 'Log'}
              </button>
            </form>
            <ActivityFeed activities={activities} />
          </div>
        )}
      </div>
    </div>
  )
}
