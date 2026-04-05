import React, { useEffect } from 'react'
import { BanknotesIcon, DocumentTextIcon, UsersIcon, ArrowTrendingUpIcon } from '@heroicons/react/24/outline'
import useStore from '../store/useStore.js'

function Kpi({ label, value, sub, color }) {
  return (
    <div className="bg-white rounded-2xl shadow-card p-5">
      <p className="text-xs font-medium text-slate-500">{label}</p>
      <p className={`text-2xl font-bold mt-1 ${color || 'text-slate-900'}`}>{value ?? '—'}</p>
      {sub && <p className="text-xs text-slate-400 mt-0.5">{sub}</p>}
    </div>
  )
}

function Bar({ label, pct, color, value }) {
  return (
    <div>
      <div className="flex justify-between text-xs mb-1">
        <span className="text-slate-600">{label}</span>
        <span className="font-medium text-slate-800">{value}</span>
      </div>
      <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
        <div className={`h-full ${color} rounded-full transition-all`} style={{ width: `${Math.min(pct, 100)}%` }} />
      </div>
    </div>
  )
}

export default function Analytics() {
  const { analytics, fetchAnalytics, analyticsLoading, commissionForecast, fetchCommissionForecast } = useStore()

  useEffect(() => {
    fetchAnalytics()
    fetchCommissionForecast()
  }, [])

  const a = analytics
  const f = commissionForecast
  const pipeline = a?.pipeline || {}
  const totalClients = Object.values(pipeline).reduce((s, v) => s + v, 0)

  const fmt$ = (n) => n != null ? `$${Number(n).toLocaleString('en-US', { maximumFractionDigits: 0 })}` : '—'
  const fmtPct = (n) => n != null ? `${n}%` : '—'

  return (
    <div className="flex flex-col h-full overflow-auto">
      {/* Header */}
      <div className="px-6 py-4 border-b border-slate-200 bg-white shrink-0">
        <h1 className="text-xl font-semibold text-slate-900">Analytics</h1>
        <p className="text-sm text-slate-500">Production summary and pipeline health</p>
      </div>

      <div className="flex-1 p-6 space-y-6">
        {analyticsLoading && (
          <div className="text-sm text-slate-400 text-center py-8">Loading analytics…</div>
        )}

        {a && (
          <>
            {/* Production KPIs */}
            <div>
              <h2 className="text-sm font-semibold text-slate-700 mb-3">Production Summary</h2>
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                <Kpi label="Policies MTD" value={a.policies_mtd?.count} sub={fmt$(a.policies_mtd?.premium) + ' premium'} color="text-brand-700" />
                <Kpi label="Policies YTD" value={a.policies_ytd?.count} sub={fmt$(a.policies_ytd?.premium) + ' premium'} />
                <Kpi label="Commissions MTD" value={fmt$(a.commissions_mtd)} sub="Month to date" color="text-emerald-700" />
                <Kpi label="Commissions YTD" value={fmt$(a.commissions_ytd)} sub="Year to date" />
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Pipeline */}
              <div className="bg-white rounded-2xl shadow-card p-5">
                <h2 className="text-sm font-semibold text-slate-800 mb-4">Pipeline Breakdown</h2>
                <div className="space-y-3">
                  {[
                    { stage: 'Lead',        color: 'bg-slate-400' },
                    { stage: 'Qualified',   color: 'bg-blue-400'  },
                    { stage: 'Proposal',    color: 'bg-amber-400' },
                    { stage: 'Negotiation', color: 'bg-orange-400'},
                    { stage: 'Closed',      color: 'bg-emerald-500'},
                  ].map(({ stage, color }) => (
                    <Bar
                      key={stage} label={stage} color={color}
                      value={pipeline[stage] || 0}
                      pct={totalClients ? ((pipeline[stage] || 0) / totalClients * 100) : 0}
                    />
                  ))}
                </div>
                <div className="mt-4 pt-3 border-t border-slate-100 grid grid-cols-2 gap-4 text-center">
                  <div>
                    <p className="text-xs text-slate-500">Lead → Proposal</p>
                    <p className="text-lg font-bold text-slate-800 mt-0.5">{fmtPct(a.conversion?.lead_to_proposal)}</p>
                  </div>
                  <div>
                    <p className="text-xs text-slate-500">Proposal → Closed</p>
                    <p className="text-lg font-bold text-slate-800 mt-0.5">{fmtPct(a.conversion?.proposal_to_closed)}</p>
                  </div>
                </div>
              </div>

              {/* Renewals */}
              <div className="bg-white rounded-2xl shadow-card p-5">
                <h2 className="text-sm font-semibold text-slate-800 mb-4">Renewal Forecast</h2>
                <div className="space-y-4">
                  {[
                    { label: '30 Days', key: '30_days', color: 'text-red-600' },
                    { label: '60 Days', key: '60_days', color: 'text-amber-600' },
                    { label: '90 Days', key: '90_days', color: 'text-slate-700' },
                  ].map(({ label, key, color }) => {
                    const r = a.renewals?.[key]
                    return (
                      <div key={key} className="flex items-center justify-between p-3 bg-slate-50 rounded-xl">
                        <div>
                          <p className="text-sm font-medium text-slate-700">Next {label}</p>
                          <p className="text-xs text-slate-500 mt-0.5">{r?.count ?? 0} policies</p>
                        </div>
                        <p className={`text-lg font-bold ${color}`}>{fmt$(r?.premium)}</p>
                      </div>
                    )
                  })}
                </div>
              </div>

              {/* Lead Sources */}
              <div className="bg-white rounded-2xl shadow-card p-5">
                <h2 className="text-sm font-semibold text-slate-800 mb-4">Lead Sources</h2>
                <div className="space-y-3">
                  {(a.lead_sources || []).map(({ lead_source, cnt }) => {
                    const total = (a.lead_sources || []).reduce((s, r) => s + r.cnt, 0)
                    return (
                      <Bar key={lead_source} label={lead_source} value={cnt}
                        pct={total ? cnt / total * 100 : 0} color="bg-brand-500" />
                    )
                  })}
                  {(!a.lead_sources || a.lead_sources.length === 0) && (
                    <p className="text-sm text-slate-400">No lead source data yet.</p>
                  )}
                </div>
              </div>

              {/* Commission Forecast */}
              {f && (
                <div className="bg-white rounded-2xl shadow-card p-5">
                  <h2 className="text-sm font-semibold text-slate-800 mb-4">Commission Forecast</h2>
                  <div className="space-y-3">
                    <div className="flex justify-between items-center p-3 bg-brand-50 rounded-xl">
                      <div>
                        <p className="text-sm font-medium text-brand-800">3-Month Forecast</p>
                        <p className="text-xs text-brand-600 mt-0.5">Pipeline + renewals</p>
                      </div>
                      <p className="text-xl font-bold text-brand-700">{fmt$(f.forecast_3_months)}</p>
                    </div>
                    <div className="flex justify-between items-center p-3 bg-slate-50 rounded-xl">
                      <div>
                        <p className="text-sm font-medium text-slate-700">6-Month Forecast</p>
                        <p className="text-xs text-slate-500 mt-0.5">Pipeline + renewals</p>
                      </div>
                      <p className="text-xl font-bold text-slate-800">{fmt$(f.forecast_6_months)}</p>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-xs text-slate-500">Renewals next 90d</span>
                      <span className="text-sm font-semibold text-emerald-700">{fmt$(f.renewal_90_days)}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-xs text-slate-500">Weighted pipeline</span>
                      <span className="text-sm font-semibold text-slate-700">{fmt$(f.pipeline_weighted)}</span>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Top Clients */}
            {a.top_clients?.length > 0 && (
              <div className="bg-white rounded-2xl shadow-card p-5">
                <h2 className="text-sm font-semibold text-slate-800 mb-4">Top Clients by Premium</h2>
                <div className="space-y-2">
                  {a.top_clients.map((c, i) => (
                    <div key={c.name} className="flex items-center gap-3 py-2">
                      <span className="w-6 text-xs font-bold text-slate-400 text-right">{i + 1}</span>
                      <div className="flex-1">
                        <p className="text-sm font-medium text-slate-800">{c.name}</p>
                        <p className="text-xs text-slate-400">{c.policy_count} polic{c.policy_count === 1 ? 'y' : 'ies'}</p>
                      </div>
                      <p className="text-sm font-semibold text-slate-800">{fmt$(c.total_premium)}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}
