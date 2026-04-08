import React, { useEffect, useState, useCallback } from 'react'
import {
  PlusIcon, PlayIcon, ChevronRightIcon, XMarkIcon,
  ClockIcon, ShieldExclamationIcon, CheckCircleIcon,
  ExclamationTriangleIcon, DocumentMagnifyingGlassIcon,
  ArrowPathIcon, InformationCircleIcon,
} from '@heroicons/react/24/outline'
import StatusBadge from '../components/StatusBadge.jsx'
import * as api from '../api.js'
import useStore from '../store/useStore.js'

// ─── helpers ────────────────────────────────────────────────────────────────

function fmt(v) {
  if (v == null) return '—'
  if (typeof v === 'number') return v.toLocaleString('en-US', { maximumFractionDigits: 1 })
  return v
}
function fmtUSD(v) {
  if (v == null) return '—'
  return `$${Number(v).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
}
function fmtDate(s) {
  if (!s) return '—'
  return new Date(s).toLocaleString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}
function shortId(id) {
  return id ? id.slice(0, 8) + '…' : '—'
}

const DECISION_COLORS = {
  APPROVED:                 'bg-emerald-100 text-emerald-700 border-emerald-200',
  APPROVED_WITH_CONDITIONS: 'bg-teal-100    text-teal-700    border-teal-200',
  REJECTED:                 'bg-red-100     text-red-700     border-red-200',
  PENDED:                   'bg-amber-100   text-amber-700   border-amber-200',
}

const SEVERITY_COLORS = {
  LOW:      'bg-slate-100  text-slate-600',
  MEDIUM:   'bg-amber-100  text-amber-700',
  HIGH:     'bg-orange-100 text-orange-700',
  CRITICAL: 'bg-red-100    text-red-700',
}

// ─── KPI card ───────────────────────────────────────────────────────────────

function KpiCard({ label, value, icon: Icon, color }) {
  return (
    <div className="bg-white rounded-xl shadow-card p-4 flex items-center gap-4">
      <div className={`w-10 h-10 rounded-lg flex items-center justify-center shrink-0 ${color}`}>
        <Icon className="w-5 h-5" />
      </div>
      <div>
        <div className="text-xl font-bold text-slate-900">{value}</div>
        <div className="text-xs text-slate-500 mt-0.5">{label}</div>
      </div>
    </div>
  )
}

// ─── Create application modal ────────────────────────────────────────────────

function CreateModal({ clients, products, onClose, onCreated }) {
  const pushToast = useStore(s => s.pushToast)
  const [form, setForm] = useState({ client_id: '', product_id: '', raw_input: {} })
  const [saving, setSaving] = useState(false)
  const [age, setAge] = useState('')
  const [income, setIncome] = useState('')
  const [sumAssured, setSumAssured] = useState('')
  const [smoker, setSmoker] = useState(false)
  const [bmi, setBmi] = useState('')

  const handle = async (e) => {
    e.preventDefault()
    if (!form.client_id || !form.product_id) return
    setSaving(true)
    try {
      const raw_input = {
        forms: {
          age: age ? Number(age) : undefined,
          annual_income: income ? Number(income) : undefined,
          sum_assured: sumAssured ? Number(sumAssured) : undefined,
          smoker,
          bmi: bmi ? Number(bmi) : undefined,
        },
      }
      const app = await api.createUWApplication({ ...form, raw_input })
      pushToast('Application created', 'success')
      onCreated(app)
    } catch (e) {
      pushToast(e.message, 'error')
    } finally {
      setSaving(false)
    }
  }

  const inp = 'w-full px-3 py-2 text-sm bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent transition-shadow'

  return (
    <div className="fixed inset-0 bg-black/40 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-panel p-6 w-full max-w-md animate-slide-up">
        <div className="flex items-center justify-between mb-5">
          <h2 className="text-base font-semibold text-slate-900">New Underwriting Application</h2>
          <button onClick={onClose} className="p-1 rounded-lg hover:bg-slate-100 transition-colors">
            <XMarkIcon className="w-5 h-5 text-slate-400" />
          </button>
        </div>
        <form onSubmit={handle} className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-slate-600 mb-1">Client *</label>
              <select className={inp} value={form.client_id} onChange={e => setForm(f => ({ ...f, client_id: e.target.value }))} required>
                <option value="">Select client…</option>
                {clients.map(c => <option key={c.client_id} value={c.client_id}>{c.name}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-600 mb-1">Product *</label>
              <select className={inp} value={form.product_id} onChange={e => setForm(f => ({ ...f, product_id: e.target.value }))} required>
                <option value="">Select product…</option>
                {products.map(p => <option key={p.product_id} value={p.product_id}>{p.name}</option>)}
              </select>
            </div>
          </div>

          <div className="border-t border-slate-100 pt-4">
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-3">Applicant Data</p>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium text-slate-600 mb-1">Age</label>
                <input type="number" className={inp} placeholder="e.g. 35" value={age} onChange={e => setAge(e.target.value)} min="1" max="100" />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-600 mb-1">Annual Income ($)</label>
                <input type="number" className={inp} placeholder="e.g. 90000" value={income} onChange={e => setIncome(e.target.value)} min="0" />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-600 mb-1">Sum Assured ($)</label>
                <input type="number" className={inp} placeholder="e.g. 500000" value={sumAssured} onChange={e => setSumAssured(e.target.value)} min="0" />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-600 mb-1">BMI</label>
                <input type="number" className={inp} placeholder="e.g. 24.5" value={bmi} onChange={e => setBmi(e.target.value)} min="0" step="0.1" />
              </div>
            </div>
            <div className="flex items-center gap-2 mt-3">
              <input type="checkbox" id="smoker" checked={smoker} onChange={e => setSmoker(e.target.checked)} className="rounded" />
              <label htmlFor="smoker" className="text-sm text-slate-700">Smoker</label>
            </div>
          </div>

          <div className="flex gap-2 pt-2">
            <button type="button" onClick={onClose} className="flex-1 py-2.5 bg-slate-100 text-slate-700 text-sm rounded-lg hover:bg-slate-200 font-medium transition-colors">
              Cancel
            </button>
            <button type="submit" disabled={saving} className="flex-1 py-2.5 bg-brand-600 text-white text-sm rounded-lg hover:bg-brand-700 disabled:opacity-50 font-medium transition-colors">
              {saving ? 'Creating…' : 'Create Application'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

// ─── Detail panel ────────────────────────────────────────────────────────────

function DetailPanel({ appId, onClose, onRefresh }) {
  const pushToast = useStore(s => s.pushToast)
  const [summary, setSummary] = useState(null)
  const [risk, setRisk]       = useState(null)
  const [decision, setDecision] = useState(null)
  const [reqs, setReqs]       = useState([])
  const [audit, setAudit]     = useState([])
  const [tab, setTab]         = useState('overview')
  const [running, setRunning] = useState(false)
  const [issuing, setIssuing] = useState(false)

  const load = useCallback(async () => {
    try {
      const [s, r, d, rq, a] = await Promise.allSettled([
        api.getUWApplication(appId),
        api.getUWRisk(appId),
        api.getUWDecision(appId),
        api.getUWRequirements(appId),
        api.getUWAudit(appId),
      ])
      if (s.status === 'fulfilled') setSummary(s.value)
      if (r.status === 'fulfilled') setRisk(r.value)
      if (d.status === 'fulfilled') setDecision(d.value)
      if (rq.status === 'fulfilled') setReqs(rq.value)
      if (a.status === 'fulfilled') setAudit(a.value)
    } catch (e) { pushToast(e.message, 'error') }
  }, [appId, pushToast])

  useEffect(() => { load() }, [load])

  const runPipeline = async () => {
    setRunning(true)
    try {
      await api.runUnderwriting(appId, {})
      pushToast('Underwriting pipeline completed', 'success')
      await load()
      onRefresh()
    } catch (e) { pushToast(e.message, 'error') }
    finally { setRunning(false) }
  }

  const issuePolicy = async () => {
    setIssuing(true)
    try {
      await api.issueUWPolicy(appId)
      pushToast('Policy issued successfully', 'success')
      await load()
      onRefresh()
    } catch (e) { pushToast(e.message, 'error') }
    finally { setIssuing(false) }
  }

  const canRun   = summary && ['CREATED', 'IN_PROGRESS', 'DATA_ENRICHED'].includes(summary.state)
  const canIssue = summary && summary.state === 'APPROVED'

  const tabs = ['overview', 'risk', 'decision', 'requirements', 'audit']

  return (
    <div className="w-[440px] shrink-0 border-l border-slate-200 bg-white flex flex-col h-full animate-fade-in">
      {/* Header */}
      <div className="px-5 py-4 border-b border-slate-200 flex items-start justify-between shrink-0">
        <div>
          <div className="text-xs text-slate-400 font-mono mb-1">{shortId(appId)}</div>
          <div className="flex items-center gap-2">
            {summary && <StatusBadge status={summary.state} size="lg" />}
          </div>
        </div>
        <button onClick={onClose} className="p-1 rounded-lg hover:bg-slate-100 transition-colors mt-0.5">
          <XMarkIcon className="w-5 h-5 text-slate-400" />
        </button>
      </div>

      {/* Actions */}
      <div className="px-5 py-3 border-b border-slate-100 flex gap-2 shrink-0">
        {canRun && (
          <button onClick={runPipeline} disabled={running}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-brand-600 text-white text-xs rounded-lg hover:bg-brand-700 disabled:opacity-50 font-medium transition-colors">
            {running ? <ArrowPathIcon className="w-3.5 h-3.5 animate-spin" /> : <PlayIcon className="w-3.5 h-3.5" />}
            {running ? 'Running…' : 'Run Pipeline'}
          </button>
        )}
        {canIssue && (
          <button onClick={issuePolicy} disabled={issuing}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-emerald-600 text-white text-xs rounded-lg hover:bg-emerald-700 disabled:opacity-50 font-medium transition-colors">
            <CheckCircleIcon className="w-3.5 h-3.5" />
            {issuing ? 'Issuing…' : 'Issue Policy'}
          </button>
        )}
        {summary?.state === 'PENDED' && (
          <span className="flex items-center gap-1.5 text-xs text-amber-600 font-medium">
            <ExclamationTriangleIcon className="w-4 h-4" />
            Pending requirements
          </span>
        )}
      </div>

      {/* Tabs */}
      <div className="flex border-b border-slate-200 shrink-0 px-5">
        {tabs.map(t => (
          <button key={t} onClick={() => setTab(t)}
            className={`py-2.5 mr-4 text-xs font-medium border-b-2 transition-colors capitalize ${
              tab === t ? 'border-brand-600 text-brand-600' : 'border-transparent text-slate-500 hover:text-slate-700'
            }`}>
            {t}
          </button>
        ))}
      </div>

      {/* Tab content */}
      <div className="flex-1 overflow-y-auto p-5 space-y-4">

        {/* ── Overview tab ── */}
        {tab === 'overview' && summary && (
          <>
            <Section title="Application">
              <Row label="State" value={<StatusBadge status={summary.state} />} />
              <Row label="Decision" value={summary.decision
                ? <span className={`text-xs font-semibold px-2 py-0.5 rounded border ${DECISION_COLORS[summary.decision] || ''}`}>{summary.decision}</span>
                : '—'} />
              <Row label="Risk Score" value={summary.risk_score != null ? `${summary.risk_score} / 100` : '—'} />
              <Row label="Risk Class" value={summary.risk_class ? <StatusBadge status={summary.risk_class} /> : '—'} />
              <Row label="Manual Review" value={summary.manual_review_required ? 'Yes' : 'No'} />
              <Row label="Pending Reqs" value={summary.pending_requirements_count ?? '—'} />
              <Row label="Created" value={fmtDate(summary.created_at)} />
            </Section>
            <Section title="Next Steps">
              {summary.allowed_transitions?.length > 0 ? (
                <div className="flex flex-wrap gap-1.5">
                  {summary.allowed_transitions.map(t => (
                    <span key={t} className="text-xs bg-slate-100 text-slate-600 px-2 py-0.5 rounded-full">{t}</span>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-slate-400">No further transitions — terminal state.</p>
              )}
            </Section>
          </>
        )}

        {/* ── Risk tab ── */}
        {tab === 'risk' && (
          risk ? (
            <>
              <Section title="Risk Score">
                <div className="flex items-end gap-3 mb-3">
                  <span className="text-3xl font-bold text-slate-900">{risk.risk_score}</span>
                  <span className="text-sm text-slate-400 mb-1">/ 100</span>
                  <StatusBadge status={risk.risk_class} size="lg" />
                </div>
                {risk.premium_loading_percent > 0 && (
                  <div className="text-xs text-amber-600 font-medium">+{risk.premium_loading_percent}% premium loading</div>
                )}
              </Section>
              {risk.risk_flags?.length > 0 && (
                <Section title={`Risk Flags (${risk.risk_flags.length})`}>
                  <div className="space-y-2">
                    {risk.risk_flags.map((f, i) => (
                      <div key={i} className="flex items-start gap-2.5 p-2.5 rounded-lg bg-slate-50">
                        <span className={`text-xs font-bold px-1.5 py-0.5 rounded shrink-0 ${SEVERITY_COLORS[f.severity] || ''}`}>
                          {f.severity}
                        </span>
                        <div>
                          <div className="text-xs font-medium text-slate-700">{f.flag_code}</div>
                          <div className="text-xs text-slate-500 mt-0.5">{f.description}</div>
                        </div>
                      </div>
                    ))}
                  </div>
                </Section>
              )}
              {risk.manual_review_required && (
                <div className="flex items-start gap-2 p-3 bg-amber-50 border border-amber-200 rounded-lg">
                  <ShieldExclamationIcon className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
                  <p className="text-xs text-amber-700">{risk.review_reason || 'Manual underwriter review required.'}</p>
                </div>
              )}
            </>
          ) : <Empty text="Risk classification not yet run." />
        )}

        {/* ── Decision tab ── */}
        {tab === 'decision' && (
          decision ? (
            <>
              <Section title="Decision">
                <div className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-lg border text-sm font-semibold mb-3 ${DECISION_COLORS[decision.decision] || ''}`}>
                  {decision.decision}
                </div>
                <Row label="Decided by" value={decision.decided_by} />
                <Row label="Decided at" value={fmtDate(decision.decided_at)} />
              </Section>
              {decision.premium_adjustment?.final_premium && (
                <Section title="Premium">
                  <Row label="Base Premium" value={fmtUSD(decision.premium_adjustment.base_premium)} />
                  <Row label="Loading" value={`${decision.premium_adjustment.loading_percent ?? 0}%`} />
                  <Row label="Final Premium" value={<span className="font-semibold text-brand-700">{fmtUSD(decision.premium_adjustment.final_premium)}</span>} />
                </Section>
              )}
              {decision.conditions?.length > 0 && (
                <Section title="Conditions">
                  {decision.conditions.map((c, i) => (
                    <div key={i} className="p-2.5 bg-teal-50 border border-teal-200 rounded-lg mb-2">
                      <div className="text-xs font-semibold text-teal-700">{c.condition_code}</div>
                      <div className="text-xs text-teal-600 mt-0.5">{c.description}</div>
                    </div>
                  ))}
                </Section>
              )}
              {decision.rejection_reasons?.length > 0 && (
                <Section title="Rejection Reasons">
                  {decision.rejection_reasons.map((r, i) => (
                    <div key={i} className="p-2.5 bg-red-50 border border-red-200 rounded-lg mb-2">
                      <div className="text-xs font-semibold text-red-700">{r.reason_code}</div>
                      <div className="text-xs text-red-600 mt-0.5">{r.description}</div>
                    </div>
                  ))}
                </Section>
              )}
              {decision.audit_trail?.summary && (
                <Section title="Audit Summary">
                  <p className="text-xs text-slate-600 leading-relaxed">{decision.audit_trail.summary}</p>
                </Section>
              )}
            </>
          ) : <Empty text="Decision not yet made." />
        )}

        {/* ── Requirements tab ── */}
        {tab === 'requirements' && (
          reqs.length > 0 ? (
            <Section title={`Requirements (${reqs.length})`}>
              <div className="space-y-2">
                {reqs.map(r => (
                  <div key={r.requirement_id} className="p-3 rounded-lg bg-slate-50 border border-slate-200">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs font-medium text-slate-700">{r.field_name}</span>
                      <span className={`text-xs font-semibold px-1.5 py-0.5 rounded ${
                        r.status === 'FULFILLED' ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-100 text-amber-700'
                      }`}>{r.status}</span>
                    </div>
                    <p className="text-xs text-slate-500">{r.description}</p>
                    {r.document_type && (
                      <p className="text-xs text-slate-400 mt-1">Doc: {r.document_type}</p>
                    )}
                  </div>
                ))}
              </div>
            </Section>
          ) : <Empty text="No requirements identified yet." />
        )}

        {/* ── Audit tab ── */}
        {tab === 'audit' && (
          audit.length > 0 ? (
            <div className="space-y-3">
              {audit.map(entry => (
                <div key={entry.log_id} className="p-3 bg-slate-50 rounded-lg border border-slate-200">
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-xs font-semibold text-slate-700">{entry.tool_called}</span>
                    <span className={`text-xs px-1.5 py-0.5 rounded font-medium ${
                      entry.validation_status === 'VALID' ? 'bg-emerald-100 text-emerald-700' : 'bg-red-100 text-red-700'
                    }`}>{entry.validation_status}</span>
                  </div>
                  {entry.prompt_version && (
                    <div className="text-xs text-slate-400 mb-1">Prompt: {entry.prompt_version}</div>
                  )}
                  <div className="text-xs text-slate-400">{fmtDate(entry.timestamp)}</div>
                </div>
              ))}
            </div>
          ) : <Empty text="No audit entries yet." />
        )}
      </div>
    </div>
  )
}

function Section({ title, children }) {
  return (
    <div>
      <div className="text-xs font-semibold uppercase tracking-wide text-slate-400 mb-2">{title}</div>
      <div className="space-y-1.5">{children}</div>
    </div>
  )
}

function Row({ label, value }) {
  return (
    <div className="flex items-center justify-between py-1 border-b border-slate-50">
      <span className="text-xs text-slate-500">{label}</span>
      <span className="text-xs text-slate-900 font-medium text-right">{value ?? '—'}</span>
    </div>
  )
}

function Empty({ text }) {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-slate-400">
      <InformationCircleIcon className="w-8 h-8 mb-2 opacity-50" />
      <p className="text-sm">{text}</p>
    </div>
  )
}

// ─── Main page ───────────────────────────────────────────────────────────────

export default function Underwriting() {
  const pushToast = useStore(s => s.pushToast)
  const clients   = useStore(s => s.clients)
  const products  = useStore(s => s.products)
  const fetchClients  = useStore(s => s.fetchClients)
  const fetchProducts = useStore(s => s.fetchProducts)

  const [queue, setQueue]     = useState({ pended: [], manual_review: [] })
  const [allApps, setAllApps] = useState([])
  const [loading, setLoading] = useState(true)
  const [selected, setSelected] = useState(null)
  const [showCreate, setShowCreate] = useState(false)
  const [filter, setFilter]   = useState('ALL')   // ALL | PENDED | APPROVED | REJECTED

  const loadData = useCallback(async () => {
    setLoading(true)
    try {
      const [q, apps] = await Promise.all([
        api.getUWQueue(),
        api.getUWApplications(),
      ])
      setQueue(q)
      setAllApps(apps)
    } catch (e) {
      pushToast(e.message, 'error')
    } finally {
      setLoading(false)
    }
  }, [pushToast])

  useEffect(() => {
    loadData()
    if (!clients.length) fetchClients()
    if (!products.length) fetchProducts()
  }, [loadData, clients.length, products.length, fetchClients, fetchProducts])

  // Derived
  const allDecisioned = allApps.filter(a => a.decision)
  const approved  = allApps.filter(a => a.state === 'APPROVED' || (a.decision && a.decision.startsWith('APPROVED')))
  const rejected  = allApps.filter(a => a.state === 'REJECTED')
  const pended    = queue.pended || []
  const manualRev = queue.manual_review || []

  const displayed = filter === 'ALL'      ? allApps
                  : filter === 'PENDED'   ? pended
                  : filter === 'APPROVED' ? approved
                  : filter === 'REJECTED' ? rejected
                  : allApps

  const kpis = [
    { label: 'Total Applications', value: allApps.length,  icon: DocumentMagnifyingGlassIcon, color: 'bg-brand-100 text-brand-600' },
    { label: 'Approved',           value: approved.length,  icon: CheckCircleIcon,              color: 'bg-emerald-100 text-emerald-600' },
    { label: 'Pending Review',     value: pended.length + manualRev.length, icon: ClockIcon, color: 'bg-amber-100 text-amber-600' },
    { label: 'Rejected',           value: rejected.length,  icon: ShieldExclamationIcon,        color: 'bg-red-100 text-red-600' },
  ]

  const FILTERS = ['ALL', 'PENDED', 'APPROVED', 'REJECTED']

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="px-6 py-4 border-b border-slate-200 bg-white shrink-0 flex items-center justify-between">
        <div>
          <h1 className="text-lg font-bold text-slate-900">Underwriting</h1>
          <p className="text-xs text-slate-400 mt-0.5">WAT Framework v3 · decision-driven lifecycle</p>
        </div>
        <button
          onClick={() => setShowCreate(true)}
          className="flex items-center gap-2 px-3 py-2 bg-brand-600 text-white text-sm rounded-lg hover:bg-brand-700 font-medium transition-colors"
        >
          <PlusIcon className="w-4 h-4" />
          New Application
        </button>
      </div>

      {/* KPIs */}
      <div className="px-6 py-4 grid grid-cols-2 lg:grid-cols-4 gap-3 bg-slate-50 border-b border-slate-200 shrink-0">
        {kpis.map(k => <KpiCard key={k.label} {...k} />)}
      </div>

      {/* Filter bar */}
      <div className="px-6 py-3 bg-white border-b border-slate-200 shrink-0 flex items-center gap-2">
        {FILTERS.map(f => (
          <button key={f} onClick={() => setFilter(f)}
            className={`px-3 py-1 text-xs font-medium rounded-full transition-colors ${
              filter === f
                ? 'bg-brand-600 text-white'
                : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
            }`}>
            {f}
          </button>
        ))}
        <button onClick={loadData} className="ml-auto p-1.5 rounded-lg hover:bg-slate-100 transition-colors text-slate-400 hover:text-slate-700">
          <ArrowPathIcon className="w-4 h-4" />
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Table */}
        <div className={`flex-1 overflow-auto ${selected ? 'hidden lg:block' : ''}`}>
          {loading ? (
            <div className="p-6 space-y-2">
              {[...Array(5)].map((_, i) => (
                <div key={i} className="h-12 bg-slate-100 rounded-lg animate-pulse" />
              ))}
            </div>
          ) : displayed.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-64 text-slate-400">
              <DocumentMagnifyingGlassIcon className="w-12 h-12 mb-3 opacity-30" />
              <p className="text-sm font-medium">No applications found</p>
              <p className="text-xs mt-1">Create one using the button above</p>
            </div>
          ) : (
            <table className="w-full text-sm">
              <thead className="bg-slate-50 border-b border-slate-200 sticky top-0">
                <tr>
                  {['Application', 'Client', 'State', 'Risk', 'Decision', 'Updated'].map(h => (
                    <th key={h} className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wide">{h}</th>
                  ))}
                  <th />
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {displayed.map(app => (
                  <tr
                    key={app.application_id}
                    onClick={() => setSelected(app.application_id === selected ? null : app.application_id)}
                    className={`cursor-pointer transition-colors ${
                      app.application_id === selected ? 'bg-brand-50' : 'hover:bg-slate-50'
                    }`}
                  >
                    <td className="px-4 py-3 font-mono text-xs text-slate-500">{shortId(app.application_id)}</td>
                    <td className="px-4 py-3 text-slate-700 text-xs">{app.client_id ? shortId(app.client_id) : '—'}</td>
                    <td className="px-4 py-3"><StatusBadge status={app.state} /></td>
                    <td className="px-4 py-3">
                      {app.risk_score != null ? (
                        <span className="flex items-center gap-1.5">
                          <span className="text-xs font-semibold text-slate-700">{app.risk_score}</span>
                          {app.risk_class && <StatusBadge status={app.risk_class} />}
                        </span>
                      ) : '—'}
                    </td>
                    <td className="px-4 py-3">
                      {app.decision ? (
                        <span className={`text-xs font-semibold px-2 py-0.5 rounded border ${DECISION_COLORS[app.decision] || 'bg-slate-100 text-slate-600 border-slate-200'}`}>
                          {app.decision}
                        </span>
                      ) : '—'}
                    </td>
                    <td className="px-4 py-3 text-xs text-slate-400">{fmtDate(app.updated_at || app.created_at)}</td>
                    <td className="px-4 py-3">
                      <ChevronRightIcon className={`w-4 h-4 text-slate-300 transition-transform ${app.application_id === selected ? 'rotate-90' : ''}`} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        {/* Detail panel */}
        {selected && (
          <DetailPanel
            appId={selected}
            onClose={() => setSelected(null)}
            onRefresh={loadData}
          />
        )}
      </div>

      {/* Modals */}
      {showCreate && (
        <CreateModal
          clients={clients}
          products={products}
          onClose={() => setShowCreate(false)}
          onCreated={(app) => {
            setShowCreate(false)
            setSelected(app.application_id)
            loadData()
          }}
        />
      )}
    </div>
  )
}
