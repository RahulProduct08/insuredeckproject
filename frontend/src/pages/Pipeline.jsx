import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import useStore from '../store/useStore.js'

const STAGES = ['Lead', 'Qualified', 'Proposal', 'Closed']

const STAGE_STYLE = {
  Lead:      { border: 'border-slate-300',  badge: 'bg-slate-100 text-slate-600',   left: 'border-l-slate-300'  },
  Qualified: { border: 'border-blue-300',   badge: 'bg-blue-100 text-blue-700',     left: 'border-l-blue-400'   },
  Proposal:  { border: 'border-violet-300', badge: 'bg-violet-100 text-violet-700', left: 'border-l-violet-400' },
  Closed:    { border: 'border-green-300',  badge: 'bg-green-100 text-green-700',   left: 'border-l-green-400'  },
}

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

function ClientCard({ client, onDragStart }) {
  const navigate = useNavigate()
  const style = STAGE_STYLE[client.stage] || STAGE_STYLE.Lead

  return (
    <div
      draggable
      onDragStart={onDragStart}
      onClick={() => navigate(`/clients/${client.client_id}`)}
      className={`bg-white rounded-xl border border-slate-200 border-l-4 ${style.left} p-3 cursor-pointer
        hover:-translate-y-0.5 hover:shadow-md transition-all duration-150 mb-2 select-none`}
    >
      <div className="flex items-center gap-2.5">
        <div className={`w-8 h-8 rounded-full ${avatarColor(client.name)} flex items-center justify-center shrink-0`}>
          <span className="text-xs font-bold text-white">{initials(client.name)}</span>
        </div>
        <div className="flex-1 min-w-0">
          <div className="font-semibold text-sm text-slate-900 truncate">{client.name}</div>
          {client.income && (
            <div className="text-xs text-slate-500">
              ₹{Number(client.income).toLocaleString('en-IN')} / yr
            </div>
          )}
        </div>
      </div>
      {client.phone && (
        <div className="text-xs text-slate-400 mt-2 truncate">{client.phone}</div>
      )}
    </div>
  )
}

function KanbanColumn({ stage, clients, onDrop, onDragOver, onDragLeave, isDragOver }) {
  const style = STAGE_STYLE[stage] || STAGE_STYLE.Lead

  return (
    <div
      className={`flex flex-col flex-1 min-w-56 max-w-72 bg-slate-50 rounded-2xl border ${style.border}
        ${isDragOver ? 'ring-2 ring-brand-300 bg-brand-50' : ''} transition-all duration-150`}
      onDragOver={onDragOver}
      onDragLeave={onDragLeave}
      onDrop={onDrop}
    >
      {/* Column header */}
      <div className="px-4 py-3 flex items-center justify-between">
        <span className="text-sm font-semibold text-slate-700">{stage}</span>
        <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${style.badge}`}>
          {clients.length}
        </span>
      </div>

      {/* Cards */}
      <div className="flex-1 overflow-y-auto px-3 pb-3 min-h-32">
        {clients.map(c => (
          <ClientCard
            key={c.client_id}
            client={c}
            onDragStart={(e) => {
              e.dataTransfer.setData('client_id', c.client_id)
              e.dataTransfer.setData('from_stage', c.stage)
            }}
          />
        ))}
        {clients.length === 0 && (
          <div className="text-center text-xs text-slate-400 py-10 border-2 border-dashed border-slate-200 rounded-xl">
            Drop clients here
          </div>
        )}
      </div>
    </div>
  )
}

export default function Pipeline() {
  const { clients, fetchClients, updateClient, clientsLoading } = useStore()
  const [dragOver, setDragOver] = useState(null)

  useEffect(() => { fetchClients() }, [])

  const clientsByStage = STAGES.reduce((acc, stage) => {
    acc[stage] = clients.filter(c => c.stage === stage)
    return acc
  }, {})

  const handleDrop = async (e, targetStage) => {
    e.preventDefault()
    setDragOver(null)
    const clientId = e.dataTransfer.getData('client_id')
    const fromStage = e.dataTransfer.getData('from_stage')
    if (!clientId || fromStage === targetStage) return
    await updateClient(clientId, { stage: targetStage })
    fetchClients()
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="px-6 py-4 border-b border-slate-200 bg-white shrink-0 flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-slate-900">Pipeline</h1>
          <p className="text-sm text-slate-500">Drag clients between stages to advance the pipeline.</p>
        </div>
        <div className="text-sm text-slate-400 font-medium">{clients.length} clients</div>
      </div>

      {/* Kanban board */}
      <div className="flex-1 overflow-auto p-5">
        {clientsLoading ? (
          <div className="flex items-center justify-center h-64 text-slate-400">
            <div className="skeleton w-48 h-6 rounded-lg" />
          </div>
        ) : (
          <div className="flex gap-4 h-full pb-4">
            {STAGES.map(stage => (
              <KanbanColumn
                key={stage}
                stage={stage}
                clients={clientsByStage[stage] || []}
                isDragOver={dragOver === stage}
                onDragOver={(e) => { e.preventDefault(); setDragOver(stage) }}
                onDragLeave={() => setDragOver(null)}
                onDrop={(e) => handleDrop(e, stage)}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
