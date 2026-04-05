import React, { useState, useEffect } from 'react'
import { XMarkIcon, PencilIcon, CheckIcon } from '@heroicons/react/20/solid'

export default function DetailPanel({ title, item, fields = [], onSave, onClose, children }) {
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState({})
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    setEditing(false)
    setDraft({})
  }, [item])

  if (!item) {
    return (
      <div className="flex items-center justify-center h-full text-sm text-slate-400 border-l border-slate-100">
        Select a row to view details
      </div>
    )
  }

  const startEdit = () => {
    const initial = {}
    fields.filter(f => f.editable).forEach(f => { initial[f.key] = item[f.key] ?? '' })
    setDraft(initial)
    setEditing(true)
  }

  const handleSave = async () => {
    setSaving(true)
    try {
      await onSave?.(draft)
      setEditing(false)
    } finally {
      setSaving(false)
    }
  }

  const renderValue = (field) => {
    const val = item[field.key]
    if (val === null || val === undefined || val === '') return <span className="text-slate-400">—</span>
    if (typeof val === 'number' && field.currency) return `₹${val.toLocaleString('en-IN')}`
    return String(val)
  }

  const inputCls = "w-full px-3 py-2 text-sm bg-white border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent transition-shadow"

  const renderEditField = (field) => {
    const val = draft[field.key] ?? ''
    if (field.type === 'select' && field.options) {
      return (
        <select value={val} onChange={e => setDraft(d => ({ ...d, [field.key]: e.target.value }))} className={inputCls}>
          {field.options.map(o => (
            <option key={o.value ?? o} value={o.value ?? o}>{o.label ?? o}</option>
          ))}
        </select>
      )
    }
    if (field.type === 'textarea') {
      return (
        <textarea
          value={val}
          onChange={e => setDraft(d => ({ ...d, [field.key]: e.target.value }))}
          rows={3}
          className={inputCls}
        />
      )
    }
    return (
      <input
        type={field.type === 'number' ? 'number' : 'text'}
        value={val}
        onChange={e => setDraft(d => ({ ...d, [field.key]: e.target.value }))}
        className={inputCls}
      />
    )
  }

  return (
    <div className="flex flex-col h-full bg-white shadow-panel border-l border-slate-100">
      {/* Header */}
      <div className="flex items-center justify-between px-5 py-4 border-b border-slate-100">
        <h3 className="text-base font-semibold text-slate-800 truncate mr-3">{title}</h3>
        <div className="flex items-center gap-1.5 shrink-0">
          {onSave && !editing && (
            <button
              onClick={startEdit}
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium bg-brand-50 text-brand-700 rounded-lg hover:bg-brand-100 transition-colors"
            >
              <PencilIcon className="w-3 h-3" />
              Edit
            </button>
          )}
          {editing && (
            <>
              <button
                onClick={handleSave}
                disabled={saving}
                className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium bg-brand-600 text-white rounded-lg hover:bg-brand-700 disabled:opacity-50 transition-colors"
              >
                <CheckIcon className="w-3 h-3" />
                {saving ? 'Saving…' : 'Save'}
              </button>
              <button
                onClick={() => setEditing(false)}
                className="px-3 py-1.5 text-xs font-medium bg-slate-100 text-slate-600 rounded-lg hover:bg-slate-200 transition-colors"
              >
                Cancel
              </button>
            </>
          )}
          {onClose && (
            <button
              onClick={onClose}
              className="p-1.5 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg transition-colors"
            >
              <XMarkIcon className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>

      {/* Fields */}
      <div className="flex-1 overflow-y-auto p-5 space-y-5">
        {fields.map(field => (
          <div key={field.key}>
            <div className="text-xs font-medium text-slate-500 mb-1">{field.label}</div>
            {editing && field.editable
              ? renderEditField(field)
              : <div className="text-sm text-slate-800">{renderValue(field)}</div>
            }
          </div>
        ))}

        {children && (
          <div className="pt-4 border-t border-slate-100">
            {children}
          </div>
        )}
      </div>
    </div>
  )
}
