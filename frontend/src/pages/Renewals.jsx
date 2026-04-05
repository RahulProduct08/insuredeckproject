import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import useStore from '../store/useStore.js'
import DataTable from '../components/DataTable.jsx'
import StatusBadge from '../components/StatusBadge.jsx'

const WINDOW_OPTIONS = [
  { label: '30 days', value: 30 },
  { label: '60 days', value: 60 },
  { label: '90 days', value: 90 },
  { label: '180 days', value: 180 },
]

function daysUntil(dateStr) {
  if (!dateStr) return null
  const diff = new Date(dateStr) - new Date()
  return Math.ceil(diff / (1000 * 60 * 60 * 24))
}

const COLUMNS = [
  { key: 'client_name', label: 'Client' },
  { key: 'product_name', label: 'Product' },
  { key: 'status', label: 'Status', render: (v) => <StatusBadge status={v} /> },
  { key: 'premium', label: 'Premium', render: (v) => `$${Number(v).toLocaleString('en-US')}` },
  {
    key: 'renewal_due_at', label: 'Renewal Due',
    render: (v) => {
      if (!v) return '—'
      const days = daysUntil(v)
      const label = new Date(v).toLocaleDateString('en-US')
      const color = days < 0 ? 'text-red-600 font-semibold' : days < 30 ? 'text-amber-600 font-medium' : 'text-gray-700'
      return (
        <span className={color}>
          {label}
          {days !== null && (
            <span className="ml-1 text-xs">
              ({days < 0 ? `${Math.abs(days)}d overdue` : `${days}d left`})
            </span>
          )}
        </span>
      )
    },
  },
]

export default function Renewals() {
  const navigate = useNavigate()
  const { policies, fetchPolicies, policiesLoading } = useStore()
  const [window, setWindow] = useState(90)

  useEffect(() => {
    fetchPolicies({ renewal_window: window })
  }, [window])

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200 bg-white flex items-center justify-between shrink-0">
        <div>
          <h1 className="text-xl font-semibold text-slate-900">Renewals</h1>
          <p className="text-sm text-slate-500">{policies.length} policies in renewal window</p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-500">Window:</span>
          <div className="flex rounded-lg overflow-hidden border border-gray-200">
            {WINDOW_OPTIONS.map(opt => (
              <button
                key={opt.value}
                onClick={() => setWindow(opt.value)}
                className={`px-3 py-1.5 text-xs font-medium transition-colors
                  ${window === opt.value
                    ? 'bg-blue-600 text-white'
                    : 'bg-white text-gray-600 hover:bg-gray-50'}`}
              >
                {opt.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Alert banner */}
      {policies.some(p => daysUntil(p.renewal_due_at) < 0) && (
        <div className="bg-red-50 border-b border-red-200 px-6 py-2 text-sm text-red-700">
          ⚠️ {policies.filter(p => daysUntil(p.renewal_due_at) < 0).length} policies are past renewal due date.
        </div>
      )}

      <div className="flex-1 overflow-hidden">
        <DataTable
          columns={COLUMNS}
          data={policies}
          loading={policiesLoading}
          rowKey="policy_id"
          searchKeys={['client_name', 'product_name', 'status']}
          onRowClick={(row) => navigate(`/clients/${row.client_id}`)}
          emptyText="No policies due for renewal in this window."
        />
      </div>
    </div>
  )
}
