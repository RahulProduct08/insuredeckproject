import React, { useEffect, useState } from 'react'
import useStore from '../store/useStore.js'
import DataTable from '../components/DataTable.jsx'
import { BanknotesIcon, ArrowTrendingUpIcon, ArrowPathIcon } from '@heroicons/react/24/outline'

const COLUMNS = [
  { key: 'client_name', label: 'Client' },
  { key: 'product_name', label: 'Product' },
  {
    key: 'event_type', label: 'Type',
    render: (v) => (
      <span className={`inline-flex items-center gap-1 text-xs font-medium
        ${v === 'sale' ? 'text-blue-700' : 'text-green-700'}`}>
        <span className={`w-1.5 h-1.5 rounded-full ${v === 'sale' ? 'bg-blue-500' : 'bg-green-500'}`} />
        {v === 'sale' ? 'Sale' : 'Renewal'}
      </span>
    ),
  },
  { key: 'premium', label: 'Premium', render: (v) => `$${Number(v).toLocaleString('en-US')}` },
  { key: 'rate_percent', label: 'Rate', render: (v) => `${v}%` },
  { key: 'amount', label: 'Commission', render: (v) => (
    <span className="font-semibold text-slate-800">${Number(v).toLocaleString('en-US')}</span>
  )},
  { key: 'recorded_at', label: 'Date', render: (v) => v ? new Date(v).toLocaleDateString('en-US') : '—' },
]

function KpiCard({ label, value, sub, Icon, iconColor, gradient = false }) {
  return (
    <div className={`rounded-2xl border border-slate-100 shadow-card p-5 flex items-start gap-4 ${gradient ? 'bg-gradient-to-br from-brand-50 to-white' : 'bg-white'}`}>
      <div className={`p-2.5 rounded-xl ${gradient ? 'bg-brand-100' : 'bg-slate-100'}`}>
        <Icon className={`w-5 h-5 ${iconColor}`} />
      </div>
      <div className="min-w-0">
        <div className="text-xs font-semibold text-slate-500 uppercase tracking-wide">{label}</div>
        <div className={`text-3xl font-bold mt-0.5 ${gradient ? 'text-brand-700' : 'text-slate-900'}`}>{value}</div>
        {sub && <div className="text-xs text-slate-400 mt-0.5">{sub}</div>}
      </div>
    </div>
  )
}

export default function Commissions() {
  const { commissions, commissionSummary, commissionForecast, fetchCommissions,
          fetchCommissionSummary, fetchCommissionForecast, commissionsLoading } = useStore()
  const [filter, setFilter] = useState({ event_type: '' })

  useEffect(() => {
    fetchCommissionSummary()
    fetchCommissions(filter)
    fetchCommissionForecast()
  }, [])

  const handleFilter = (key, value) => {
    const newFilter = { ...filter, [key]: value }
    setFilter(newFilter)
    fetchCommissions(newFilter)
  }

  const fmt = (n) => `$${Number(n || 0).toLocaleString('en-US', { maximumFractionDigits: 0 })}`

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="px-6 py-4 border-b border-slate-200 bg-white shrink-0">
        <h1 className="text-xl font-semibold text-slate-900">Commissions</h1>
        <p className="text-sm text-slate-500">Track upfront and renewal earnings</p>
      </div>

      {/* KPI Cards */}
      <div className="px-6 py-5 grid grid-cols-3 lg:grid-cols-5 gap-4 shrink-0 border-b border-slate-100 bg-slate-50">
        <KpiCard
          label="Total Earnings"
          value={fmt(commissionSummary.total)}
          sub={`${commissionSummary.count} commission records`}
          Icon={BanknotesIcon}
          iconColor="text-brand-600"
          gradient
        />
        <KpiCard
          label="Upfront (Sale)"
          value={fmt(commissionSummary.sale_total)}
          sub="On policy issuance"
          Icon={ArrowTrendingUpIcon}
          iconColor="text-blue-600"
        />
        <KpiCard
          label="Renewal"
          value={fmt(commissionSummary.renewal_total)}
          sub="Annual renewals"
          Icon={ArrowPathIcon}
          iconColor="text-green-600"
        />
        {commissionForecast && (
          <>
            <KpiCard
              label="3-Month Forecast"
              value={fmt(commissionForecast.forecast_3_months)}
              sub="Pipeline + renewals"
              Icon={ArrowTrendingUpIcon}
              iconColor="text-amber-600"
            />
            <KpiCard
              label="6-Month Forecast"
              value={fmt(commissionForecast.forecast_6_months)}
              sub="Pipeline + renewals"
              Icon={ArrowTrendingUpIcon}
              iconColor="text-orange-600"
            />
          </>
        )}
      </div>

      {/* Filter bar */}
      <div className="px-6 py-3 border-b border-slate-100 bg-white flex items-center gap-4 shrink-0">
        <span className="text-sm text-slate-500 font-medium">Filter by:</span>
        <select
          value={filter.event_type}
          onChange={e => handleFilter('event_type', e.target.value)}
          className="px-3 py-1.5 text-sm bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent"
        >
          <option value="">All Types</option>
          <option value="sale">Sale (Upfront)</option>
          <option value="renewal">Renewal</option>
        </select>
        {filter.event_type && (
          <button
            onClick={() => handleFilter('event_type', '')}
            className="text-xs text-slate-400 hover:text-slate-600 font-medium"
          >
            Clear filter
          </button>
        )}
      </div>

      {/* Table */}
      <div className="flex-1 overflow-hidden">
        <DataTable
          columns={COLUMNS}
          data={commissions}
          loading={commissionsLoading}
          rowKey="commission_id"
          searchKeys={['client_name', 'product_name', 'event_type']}
          emptyText="No commission records."
        />
      </div>
    </div>
  )
}
