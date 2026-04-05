import React, { useEffect, useState } from 'react'
import useStore from '../store/useStore.js'
import * as api from '../api.js'

const QUESTIONS = [
  { key: 'coverage_gaps', label: 'Current coverage gaps', type: 'select',
    options: ['No current coverage', 'Health only', 'Life only', 'Auto only', 'Multiple gaps'] },
  { key: 'family_situation', label: 'Family situation', type: 'select',
    options: ['Single, no dependents', 'Married, no children', 'Married with children', 'Single parent'] },
  { key: 'financial_goals', label: 'Primary financial goal', type: 'select',
    options: ['Income replacement', 'Debt protection', 'Retirement savings', 'Estate planning', 'Business continuity'] },
  { key: 'risk_tolerance', label: 'Risk tolerance', type: 'select',
    options: ['Conservative', 'Moderate', 'Aggressive'] },
  { key: 'health_concern', label: 'Has health concerns?', type: 'boolean' },
  { key: 'has_vehicle', label: 'Has vehicle to insure?', type: 'boolean' },
  { key: 'has_dependents', label: 'Has dependents?', type: 'boolean' },
  { key: 'age', label: 'Client age', type: 'number', placeholder: 'e.g. 35' },
  { key: 'annual_income', label: 'Annual income ($)', type: 'number', placeholder: 'e.g. 75000' },
]

export default function NeedsAnalysis() {
  const { clients, fetchClients, agent } = useStore()
  const pushToast = useStore(s => s.pushToast)
  const [selectedClientId, setSelectedClientId] = useState('')
  const [answers, setAnswers] = useState({})
  const [notes, setNotes] = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [history, setHistory] = useState([])

  useEffect(() => { fetchClients() }, [])

  useEffect(() => {
    if (!selectedClientId) { setHistory([]); setResult(null); return }
    api.getNeedsAnalyses(selectedClientId).then(setHistory).catch(() => {})
    // Pre-fill age/income from client
    const client = clients.find(c => c.client_id === selectedClientId)
    if (client) {
      setAnswers(a => ({
        ...a,
        age: client.age || a.age,
        annual_income: client.income || a.annual_income,
        has_dependents: (client.dependents || 0) > 0,
      }))
    }
  }, [selectedClientId])

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!selectedClientId) { pushToast('Select a client first', 'error'); return }
    setLoading(true)
    try {
      const res = await api.createNeedsAnalysis({
        client_id: selectedClientId,
        agent_id: agent?.agent_id,
        answers,
        notes,
      })
      setResult(res)
      pushToast('Needs analysis saved', 'success')
      api.getNeedsAnalyses(selectedClientId).then(setHistory)
    } catch (e) {
      pushToast(e.message, 'error')
    } finally {
      setLoading(false)
    }
  }

  const update = (key, val) => setAnswers(a => ({ ...a, [key]: val }))

  return (
    <div className="flex flex-col h-full overflow-auto">
      <div className="px-6 py-4 border-b border-slate-200 bg-white shrink-0">
        <h1 className="text-xl font-semibold text-slate-900">Needs Analysis</h1>
        <p className="text-sm text-slate-500">Qualify clients and get product recommendations</p>
      </div>

      <div className="flex-1 p-6">
        <div className="max-w-2xl mx-auto space-y-6">
          {/* Client selector */}
          <div className="bg-white rounded-2xl shadow-card p-5">
            <label className="block text-sm font-medium text-slate-700 mb-2">Select Client</label>
            <select
              value={selectedClientId}
              onChange={e => setSelectedClientId(e.target.value)}
              className="w-full px-3 py-2.5 rounded-lg border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
            >
              <option value="">— Choose a client —</option>
              {clients.map(c => (
                <option key={c.client_id} value={c.client_id}>
                  {c.name} ({c.stage})
                </option>
              ))}
            </select>
          </div>

          {selectedClientId && (
            <form onSubmit={handleSubmit} className="bg-white rounded-2xl shadow-card p-5 space-y-4">
              <h2 className="text-sm font-semibold text-slate-800">Qualification Worksheet</h2>

              {QUESTIONS.map(q => (
                <div key={q.key}>
                  <label className="block text-sm font-medium text-slate-700 mb-1">{q.label}</label>
                  {q.type === 'select' && (
                    <select
                      value={answers[q.key] || ''}
                      onChange={e => update(q.key, e.target.value)}
                      className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                    >
                      <option value="">Select…</option>
                      {q.options.map(o => <option key={o} value={o}>{o}</option>)}
                    </select>
                  )}
                  {q.type === 'boolean' && (
                    <div className="flex gap-3">
                      {['Yes', 'No'].map(opt => (
                        <button
                          key={opt} type="button"
                          onClick={() => update(q.key, opt === 'Yes')}
                          className={`px-4 py-2 text-sm rounded-lg border transition-colors ${
                            answers[q.key] === (opt === 'Yes')
                              ? 'bg-brand-600 text-white border-brand-600'
                              : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'
                          }`}
                        >
                          {opt}
                        </button>
                      ))}
                    </div>
                  )}
                  {q.type === 'number' && (
                    <input
                      type="number" placeholder={q.placeholder}
                      value={answers[q.key] || ''}
                      onChange={e => update(q.key, Number(e.target.value))}
                      className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                    />
                  )}
                </div>
              ))}

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Agent Notes</label>
                <textarea
                  rows={3} value={notes}
                  onChange={e => setNotes(e.target.value)}
                  placeholder="Additional observations…"
                  className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 resize-none"
                />
              </div>

              <button
                type="submit" disabled={loading}
                className="w-full py-2.5 bg-brand-600 hover:bg-brand-700 text-white text-sm font-semibold rounded-xl transition-colors disabled:opacity-50"
              >
                {loading ? 'Analyzing…' : 'Run Analysis & Get Recommendations'}
              </button>
            </form>
          )}

          {/* Results */}
          {result?.recommended_products && (
            <div className="bg-white rounded-2xl shadow-card p-5 animate-slide-up">
              <h2 className="text-sm font-semibold text-slate-800 mb-4">Recommended Products</h2>
              <div className="space-y-3">
                {result.recommended_products.map((p, i) => (
                  <div key={p.product_id}
                    className={`p-4 rounded-xl border ${i === 0 ? 'border-brand-200 bg-brand-50' : 'border-slate-100 bg-slate-50'}`}>
                    <div className="flex items-start justify-between">
                      <div>
                        <div className="flex items-center gap-2">
                          {i === 0 && (
                            <span className="text-xs font-semibold text-brand-700 bg-brand-100 px-2 py-0.5 rounded-full">
                              Best Match
                            </span>
                          )}
                          <h3 className="text-sm font-semibold text-slate-800">{p.name}</h3>
                        </div>
                        <p className="text-xs text-slate-500 mt-1">{p.description}</p>
                      </div>
                      <div className="text-right shrink-0 ml-4">
                        <p className="text-xs text-slate-500">Suitability</p>
                        <p className={`text-lg font-bold ${i === 0 ? 'text-brand-700' : 'text-slate-700'}`}>
                          {p.suitability_score}
                        </p>
                      </div>
                    </div>
                    <div className="mt-2 flex gap-4 text-xs text-slate-500">
                      <span>Premium: ${p.min_premium?.toLocaleString('en-US')}–${p.max_premium?.toLocaleString('en-US')}</span>
                      <span>Commission: {p.commission_rate_percent}%</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* History */}
          {history.length > 0 && (
            <div className="bg-white rounded-2xl shadow-card p-5">
              <h2 className="text-sm font-semibold text-slate-800 mb-3">Previous Analyses</h2>
              <div className="space-y-2">
                {history.map(h => (
                  <div key={h.analysis_id} className="flex items-center justify-between p-3 bg-slate-50 rounded-xl text-xs">
                    <span className="text-slate-600">
                      {new Date(h.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
                    </span>
                    <span className="text-slate-500">
                      {h.recommended_products?.length || 0} recommendations
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
