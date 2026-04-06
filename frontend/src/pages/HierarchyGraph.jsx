import '@xyflow/react/dist/style.css'
import React, { useCallback, useEffect, useMemo, useState } from 'react'
import { ReactFlow, Background, Controls, MiniMap, Handle, Position, useNodesState, useEdgesState } from '@xyflow/react'
import { ShareIcon, PlusIcon, XMarkIcon } from '@heroicons/react/24/outline'
import useStore from '../store/useStore.js'

// ── Avatar helpers ─────────────────────────────────────────────────────────

const COLORS = ['bg-brand-600','bg-violet-600','bg-teal-600','bg-amber-600','bg-rose-600','bg-indigo-600']
function avatarColor(name = '') {
  let h = 0
  for (const c of name) h = (h * 31 + c.charCodeAt(0)) & 0xffff
  return COLORS[h % COLORS.length]
}
function initials(name = '') {
  return name.split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase()
}

// ── Custom AgentNode ───────────────────────────────────────────────────────

const ROLE_BADGE = {
  admin: 'bg-violet-100 text-violet-700',
  agent: 'bg-slate-100 text-slate-600',
}

function AgentNode({ data }) {
  const { agent_id, name, role, earnings_visible, total_earnings, isSelf } = data
  return (
    <div className={`bg-white border-2 ${isSelf ? 'border-brand-500' : 'border-slate-200'} rounded-xl shadow-md px-4 py-3 min-w-[160px] max-w-[200px]`}>
      <Handle type="target" position={Position.Top} className="!bg-brand-400 !w-3 !h-3" />
      <div className="flex flex-col items-center gap-1.5">
        <div className={`w-10 h-10 rounded-full ${avatarColor(name)} flex items-center justify-center shrink-0`}>
          <span className="text-sm font-bold text-white">{initials(name)}</span>
        </div>
        <div className="text-center">
          <div className="text-xs font-semibold text-slate-800 leading-tight">{name}</div>
          <span className={`text-[10px] font-medium px-1.5 py-0.5 rounded-full ${ROLE_BADGE[role] || ROLE_BADGE.agent}`}>
            {role}
          </span>
        </div>
        <div className="text-xs font-mono text-slate-500">
          {earnings_visible
            ? <span className="text-emerald-600 font-semibold">${(total_earnings ?? 0).toLocaleString('en-US', { minimumFractionDigits: 2 })}</span>
            : <span className="text-slate-300 tracking-widest">••••</span>
          }
        </div>
      </div>
      <Handle type="source" position={Position.Bottom} className="!bg-brand-400 !w-3 !h-3" />
    </div>
  )
}

const nodeTypes = { agentNode: AgentNode }

// ── BFS Layout ─────────────────────────────────────────────────────────────

function computeLayout(nodes, edges, viewerId) {
  if (!nodes.length) return []

  // Find roots (nodes with no incoming edges)
  const hasIncoming = new Set(edges.map(e => e.downline_agent_id))
  const roots = nodes.filter(n => !hasIncoming.has(n.agent_id)).map(n => n.agent_id)
  if (!roots.length) roots.push(nodes[0].agent_id)

  const levels = {}
  const queue = roots.map(r => ({ id: r, level: 0 }))
  const visited = new Set()
  while (queue.length) {
    const { id, level } = queue.shift()
    if (visited.has(id)) continue
    visited.add(id)
    if (levels[level] === undefined) levels[level] = []
    levels[level].push(id)
    // children (downlines of this upline)
    edges
      .filter(e => e.upline_agent_id === id)
      .forEach(e => queue.push({ id: e.downline_agent_id, level: level + 1 }))
  }

  // Any unvisited nodes go to last level
  nodes.forEach(n => {
    if (!visited.has(n.agent_id)) {
      const last = Math.max(0, ...Object.keys(levels).map(Number)) + 1
      if (!levels[last]) levels[last] = []
      levels[last].push(n.agent_id)
    }
  })

  const flowNodes = []
  for (const [lvl, ids] of Object.entries(levels)) {
    const y = Number(lvl) * 160
    const totalW = ids.length * 220
    ids.forEach((id, i) => {
      const node = nodes.find(n => n.agent_id === id)
      if (!node) return
      flowNodes.push({
        id,
        type: 'agentNode',
        position: { x: i * 220 - totalW / 2 + 110, y },
        data: { ...node, isSelf: id === viewerId },
      })
    })
  }
  return flowNodes
}

function computeEdges(edges) {
  return edges.map(e => ({
    id: String(e.id),
    source: e.upline_agent_id,
    target: e.downline_agent_id,
    type: 'smoothstep',
    animated: false,
    label: `${e.override_percentage}% override`,
    labelStyle: { fill: '#64748b', fontSize: 10 },
    markerEnd: { type: 'arrowclosed', color: '#60a5fa' },
    style: { stroke: '#60a5fa', strokeWidth: 2 },
  }))
}

// ── Main page ─────────────────────────────────────────────────────────────

export default function HierarchyGraph() {
  const { hierarchyGraph, hierarchyLoading, fetchHierarchyGraph, createHierarchyLink, deleteHierarchyLink, agent } = useStore()
  const [rfNodes, setRfNodes, onNodesChange] = useNodesState([])
  const [rfEdges, setRfEdges, onEdgesChange] = useEdgesState([])
  const [showPanel, setShowPanel] = useState(false)
  const [form, setForm] = useState({ upline_agent_id: '', downline_agent_id: '', override_percentage: 5 })
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => { fetchHierarchyGraph() }, [])

  useEffect(() => {
    const { nodes, edges } = hierarchyGraph
    setRfNodes(computeLayout(nodes, edges, agent?.agent_id))
    setRfEdges(computeEdges(edges))
  }, [hierarchyGraph, agent])

  const handleAddLink = async (e) => {
    e.preventDefault()
    setSubmitting(true)
    try {
      await createHierarchyLink({
        ...form,
        override_percentage: Number(form.override_percentage),
      })
      setShowPanel(false)
      setForm({ upline_agent_id: '', downline_agent_id: '', override_percentage: 5 })
    } finally {
      setSubmitting(false)
    }
  }

  const agentOptions = hierarchyGraph.nodes

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="px-6 py-4 border-b border-slate-200 bg-white flex items-center justify-between shrink-0">
        <div className="flex items-center gap-2.5">
          <ShareIcon className="w-5 h-5 text-brand-600" />
          <div>
            <h1 className="text-xl font-semibold text-slate-900">Agent Hierarchy</h1>
            <p className="text-sm text-slate-500">
              {hierarchyGraph.nodes.length} agents · {hierarchyGraph.edges.length} relationships
            </p>
          </div>
        </div>
        {agent?.role === 'admin' && (
          <button
            onClick={() => setShowPanel(true)}
            className="flex items-center gap-1.5 px-3 py-2 text-sm bg-brand-600 text-white rounded-lg hover:bg-brand-700 font-medium transition-colors"
          >
            <PlusIcon className="w-4 h-4" />
            Add Link
          </button>
        )}
      </div>

      {/* Graph canvas */}
      <div className="flex-1 relative">
        {hierarchyLoading ? (
          <div className="flex items-center justify-center h-full text-slate-400 text-sm">Loading hierarchy…</div>
        ) : (
          <ReactFlow
            nodes={rfNodes}
            edges={rfEdges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            nodeTypes={nodeTypes}
            fitView
            fitViewOptions={{ padding: 0.3 }}
            proOptions={{ hideAttribution: true }}
          >
            <Background gap={24} size={1} color="#e2e8f0" />
            <Controls />
            <MiniMap nodeColor={() => '#60a5fa'} maskColor="rgba(248,250,252,0.8)" />
          </ReactFlow>
        )}

        {/* Admin slide-in panel */}
        {showPanel && (
          <div className="absolute inset-y-0 right-0 w-72 bg-white border-l border-slate-200 shadow-xl flex flex-col z-10">
            <div className="flex items-center justify-between px-4 py-3 border-b border-slate-200">
              <span className="font-semibold text-slate-800 text-sm">Add Hierarchy Link</span>
              <button onClick={() => setShowPanel(false)} className="text-slate-400 hover:text-slate-600">
                <XMarkIcon className="w-4 h-4" />
              </button>
            </div>
            <form onSubmit={handleAddLink} className="flex flex-col gap-4 p-4 flex-1">
              <div>
                <label className="block text-xs font-medium text-slate-500 mb-1">Upline (Manager/MGA)</label>
                <select
                  required
                  value={form.upline_agent_id}
                  onChange={e => setForm(f => ({ ...f, upline_agent_id: e.target.value }))}
                  className="w-full px-3 py-2 text-sm bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-500"
                >
                  <option value="">Select agent…</option>
                  {agentOptions.map(a => (
                    <option key={a.agent_id} value={a.agent_id}>{a.name} ({a.role})</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-500 mb-1">Downline (Agent)</label>
                <select
                  required
                  value={form.downline_agent_id}
                  onChange={e => setForm(f => ({ ...f, downline_agent_id: e.target.value }))}
                  className="w-full px-3 py-2 text-sm bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-500"
                >
                  <option value="">Select agent…</option>
                  {agentOptions.map(a => (
                    <option key={a.agent_id} value={a.agent_id}>{a.name} ({a.role})</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-500 mb-1">Override % (upline earns this % of downline premium)</label>
                <input
                  type="number"
                  min="0"
                  max="100"
                  step="0.1"
                  required
                  value={form.override_percentage}
                  onChange={e => setForm(f => ({ ...f, override_percentage: e.target.value }))}
                  className="w-full px-3 py-2 text-sm bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-500"
                />
              </div>
              <button
                type="submit"
                disabled={submitting}
                className="mt-auto py-2.5 bg-brand-600 text-white text-sm rounded-lg hover:bg-brand-700 disabled:opacity-50 font-medium transition-colors"
              >
                {submitting ? 'Creating…' : 'Create Link'}
              </button>
            </form>
          </div>
        )}
      </div>
    </div>
  )
}
