import React, { useEffect, useState } from 'react'
import { ScaleIcon, ArrowRightIcon } from '@heroicons/react/24/outline'
import useStore from '../store/useStore.js'
import DataTable from '../components/DataTable.jsx'
import StatusBadge from '../components/StatusBadge.jsx'

// ── Helpers ───────────────────────────────────────────────────────────────

function fmt(n) {
  return n !== undefined ? `$${Number(n).toLocaleString('en-US', { minimumFractionDigits: 2 })}` : '••••'
}

function TypeBadge({ type }) {
  const cls = type === 'BASE'
    ? 'bg-emerald-100 text-emerald-700'
    : 'bg-violet-100 text-violet-700'
  return <span className={`text-xs font-bold px-1.5 py-0.5 rounded ${cls}`}>{type}</span>
}

// ── Flow Visualizer ───────────────────────────────────────────────────────

function FlowNode({ node }) {
  const hasAmount = node.amount !== undefined
  return (
    <div className="flex flex-col items-center bg-white border border-slate-200 rounded-xl px-3 py-2.5 min-w-[130px] shadow-sm">
      <div className="text-xs font-semibold text-slate-700 text-center leading-tight">{node.agent_name}</div>
      <div className={`text-[10px] font-medium mt-0.5 ${node.earning_type === 'BASE' ? 'text-emerald-600' : 'text-violet-600'}`}>
        {node.earning_type}
      </div>
      <div className="text-xs font-mono mt-1">
        {hasAmount
          ? <span className="text-slate-800 font-semibold">{fmt(node.amount)}</span>
          : <span className="text-slate-300 tracking-widest">••••</span>
        }
      </div>
      <div className="text-[10px] text-slate-400 mt-0.5">{node.percentage}%</div>
    </div>
  )
}

function CommissionFlow({ flow }) {
  if (!flow.length) return (
    <div className="flex items-center justify-center h-24 text-slate-400 text-sm">
      No flow data for this policy.
    </div>
  )
  return (
    <div className="flex items-center gap-2 overflow-x-auto py-2 px-1">
      {flow.map((node, i) => (
        <React.Fragment key={node.ledger_id}>
          <FlowNode node={node} />
          {i < flow.length - 1 && (
            <ArrowRightIcon className="w-4 h-4 text-slate-300 shrink-0" />
          )}
        </React.Fragment>
      ))}
    </div>
  )
}

// ── KPI Card ──────────────────────────────────────────────────────────────

function KpiCard({ label, value, color }) {
  return (
    <div className="bg-white border border-slate-200 rounded-xl px-5 py-4 flex flex-col gap-0.5">
      <span className="text-xs text-slate-500 font-medium">{label}</span>
      <span className={`text-2xl font-bold ${color}`}>{value}</span>
    </div>
  )
}

// ── Columns ───────────────────────────────────────────────────────────────

const COLUMNS = [
  { key: 'agent_name',        label: 'Agent' },
  { key: 'earning_type',      label: 'Type',    render: v => <TypeBadge type={v} /> },
  { key: 'hierarchy_level',   label: 'Level' },
  { key: 'percentage',        label: '%',       render: v => `${v}%` },
  { key: 'amount',            label: 'Amount',  render: v => fmt(v) },
  { key: 'client_name',       label: 'Client' },
  { key: 'policy_id',         label: 'Policy',  render: v => <span className="font-mono text-xs text-slate-500">{v?.slice(-8)}</span> },
  { key: 'created_at',        label: 'Date',    render: v => v ? new Date(v).toLocaleDateString('en-US') : '—' },
]

// ── Main page ─────────────────────────────────────────────────────────────

export default function CommissionLedger() {
  const {
    ledger, ledgerSummary, ledgerFlow, ledgerLoading,
    fetchLedger, fetchLedgerSummary, fetchLedgerFlow,
    policies, fetchPolicies,
  } = useStore()

  const [selectedPolicy, setSelectedPolicy] = useState('')

  useEffect(() => {
    fetchLedger()
    fetchLedgerSummary()
    fetchPolicies({ status: 'Issued' })
  }, [])

  useEffect(() => {
    if (selectedPolicy) fetchLedgerFlow(selectedPolicy)
    else useStore.getState().fetchLedgerFlow && null
  }, [selectedPolicy])

  const issuedPolicies = policies.filter(p => p.status === 'Issued')

  return (
    <div className="flex flex-col h-full overflow-hidden">
      {/* Header */}
      <div className="px-6 py-4 border-b border-slate-200 bg-white flex items-center gap-2.5 shrink-0">
        <ScaleIcon className="w-5 h-5 text-brand-600" />
        <div>
          <h1 className="text-xl font-semibold text-slate-900">Commission Ledger</h1>
          <p className="text-sm text-slate-500">Immutable earnings trail — BASE + OVERRIDE per policy</p>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto">
        {/* KPI row */}
        <div className="px-6 py-4 grid grid-cols-3 gap-4">
          <KpiCard
            label="Base Earnings (direct sales)"
            value={fmt(ledgerSummary.base_total)}
            color="text-emerald-600"
          />
          <KpiCard
            label="Override Earnings (upline)"
            value={fmt(ledgerSummary.override_total)}
            color="text-violet-600"
          />
          <KpiCard
            label="Grand Total"
            value={fmt(ledgerSummary.grand_total)}
            color="text-brand-600"
          />
        </div>

        {/* Policy Flow Visualizer */}
        <div className="px-6 pb-4">
          <div className="bg-white border border-slate-200 rounded-xl p-4">
            <div className="flex items-center gap-3 mb-3">
              <span className="text-sm font-semibold text-slate-700">Commission Flow by Policy</span>
              <select
                value={selectedPolicy}
                onChange={e => setSelectedPolicy(e.target.value)}
                className="px-2.5 py-1.5 text-sm bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-500"
              >
                <option value="">Select a policy…</option>
                {issuedPolicies.map(p => (
                  <option key={p.policy_id} value={p.policy_id}>
                    {p.client_name} — {p.product_name} ({p.policy_id.slice(-8)})
                  </option>
                ))}
              </select>
            </div>
            {selectedPolicy ? (
              <CommissionFlow flow={ledgerFlow} />
            ) : (
              <div className="flex items-center justify-center h-20 text-slate-400 text-sm">
                Select a policy to visualize commission flow
              </div>
            )}
          </div>
        </div>

        {/* Ledger table */}
        <div className="px-6 pb-6">
          <div className="bg-white border border-slate-200 rounded-xl overflow-hidden">
            <div className="px-4 py-3 border-b border-slate-100">
              <span className="text-sm font-semibold text-slate-700">All Ledger Entries</span>
              <span className="ml-2 text-xs text-slate-400">{ledger.length} rows</span>
            </div>
            <DataTable
              columns={COLUMNS}
              data={ledger}
              loading={ledgerLoading}
              rowKey="ledger_id"
              searchKeys={['agent_name', 'client_name', 'earning_type']}
              emptyText="No ledger entries yet. Issue a policy to generate entries."
            />
          </div>
        </div>
      </div>
    </div>
  )
}
