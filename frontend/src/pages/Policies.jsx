import React, { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import useStore from '../store/useStore.js'
import DataTable from '../components/DataTable.jsx'
import StatusBadge from '../components/StatusBadge.jsx'

const COLUMNS = [
  { key: 'client_name', label: 'Client' },
  { key: 'product_name', label: 'Product' },
  { key: 'status', label: 'Status', render: (v) => <StatusBadge status={v} /> },
  { key: 'premium', label: 'Premium', render: (v) => `₹${Number(v).toLocaleString('en-IN')}` },
  { key: 'issued_at', label: 'Issued', render: (v) => v ? new Date(v).toLocaleDateString('en-IN') : '—' },
  { key: 'renewal_due_at', label: 'Renewal Due', render: (v) => v ? new Date(v).toLocaleDateString('en-IN') : '—' },
]

export default function Policies() {
  const navigate = useNavigate()
  const { policies, fetchPolicies, policiesLoading, selectedPolicy, setSelectedPolicy } = useStore()

  useEffect(() => {
    fetchPolicies({ status: 'Issued' })
  }, [])

  const issued = policies.filter(p => p.status === 'Issued')

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="px-6 py-4 border-b border-slate-200 bg-white shrink-0">
        <h1 className="text-xl font-semibold text-slate-900">Active Policies</h1>
        <p className="text-sm text-slate-500">{issued.length} issued policies</p>
      </div>

      {/* Main */}
      <div className="flex-1 flex overflow-hidden">
        <div className={`flex flex-col overflow-hidden ${selectedPolicy ? 'w-3/5' : 'w-full'}`}>
          <DataTable
            columns={COLUMNS}
            data={issued}
            loading={policiesLoading}
            rowKey="policy_id"
            searchKeys={['client_name', 'product_name']}
            onRowClick={setSelectedPolicy}
            selected={selectedPolicy}
            emptyText="No issued policies."
          />
        </div>

        {selectedPolicy && (
          <div className="w-2/5 flex flex-col border-l border-gray-200 bg-white overflow-y-auto">
            <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100">
              <h3 className="text-sm font-semibold text-gray-800">{selectedPolicy.client_name}</h3>
              <button onClick={() => setSelectedPolicy(null)} className="text-gray-400 hover:text-gray-600 text-lg">×</button>
            </div>

            <div className="p-4 space-y-4">
              <div className="flex items-center gap-3">
                <StatusBadge status={selectedPolicy.status} size="lg" />
                <span className="text-sm text-gray-600">{selectedPolicy.product_name}</span>
              </div>

              {[
                ['Premium', `₹${Number(selectedPolicy.premium).toLocaleString('en-IN')}`],
                ['Issued Date', selectedPolicy.issued_at ? new Date(selectedPolicy.issued_at).toLocaleDateString('en-IN') : '—'],
                ['Renewal Due', selectedPolicy.renewal_due_at ? new Date(selectedPolicy.renewal_due_at).toLocaleDateString('en-IN') : '—'],
                ['Commission Rate', selectedPolicy.commission_rate_percent ? `${selectedPolicy.commission_rate_percent}%` : '—'],
              ].map(([label, value]) => (
                <div key={label}>
                  <div className="text-xs font-medium text-gray-500">{label}</div>
                  <div className="text-sm text-gray-800 mt-0.5">{value}</div>
                </div>
              ))}

              <button
                onClick={() => navigate(`/clients/${selectedPolicy.client_id}`)}
                className="w-full py-2 text-sm text-blue-600 border border-blue-200 rounded-lg hover:bg-blue-50 font-medium"
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
