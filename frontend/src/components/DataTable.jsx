import React, { useState, useMemo } from 'react'
import {
  MagnifyingGlassIcon,
  ChevronUpDownIcon,
  ChevronUpIcon,
  ChevronDownIcon,
} from '@heroicons/react/20/solid'
import { InboxIcon } from '@heroicons/react/24/outline'

function SkeletonRow({ cols }) {
  return (
    <tr>
      {Array.from({ length: cols }).map((_, i) => (
        <td key={i} className="px-4 py-3">
          <div className="skeleton h-4 rounded-md" style={{ width: `${60 + (i * 17) % 30}%` }} />
        </td>
      ))}
    </tr>
  )
}

export default function DataTable({
  columns = [],
  data = [],
  onRowClick,
  searchKeys = [],
  rowKey = 'id',
  emptyText = 'No records found.',
  selected = null,
  loading = false,
}) {
  const [search, setSearch] = useState('')
  const [sortCol, setSortCol] = useState(null)
  const [sortDir, setSortDir] = useState('asc')

  const handleSort = (key) => {
    if (sortCol === key) {
      setSortDir(d => d === 'asc' ? 'desc' : 'asc')
    } else {
      setSortCol(key)
      setSortDir('asc')
    }
  }

  const filtered = useMemo(() => {
    let rows = data
    if (search && searchKeys.length) {
      const q = search.toLowerCase()
      rows = rows.filter(row =>
        searchKeys.some(k => String(row[k] ?? '').toLowerCase().includes(q))
      )
    }
    if (sortCol) {
      rows = [...rows].sort((a, b) => {
        const av = a[sortCol] ?? ''
        const bv = b[sortCol] ?? ''
        const cmp = String(av).localeCompare(String(bv), undefined, { numeric: true })
        return sortDir === 'asc' ? cmp : -cmp
      })
    }
    return rows
  }, [data, search, searchKeys, sortCol, sortDir])

  const SortIcon = ({ col }) => {
    if (sortCol !== col) return <ChevronUpDownIcon className="w-3.5 h-3.5 text-slate-300 ml-1 inline" />
    return sortDir === 'asc'
      ? <ChevronUpIcon className="w-3.5 h-3.5 text-brand-500 ml-1 inline" />
      : <ChevronDownIcon className="w-3.5 h-3.5 text-brand-500 ml-1 inline" />
  }

  return (
    <div className="flex flex-col h-full">
      {/* Search bar */}
      <div className="p-3 border-b border-slate-100">
        <div className="relative">
          <MagnifyingGlassIcon className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input
            type="text"
            placeholder="Search…"
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="w-full pl-9 pr-3 py-2 text-sm bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent transition-shadow"
          />
        </div>
      </div>

      {/* Table */}
      <div className="flex-1 overflow-auto">
        <table className="w-full text-sm">
          <thead className="sticky top-0 bg-white border-b border-slate-200 z-10">
            <tr>
              {columns.map(col => (
                <th
                  key={col.key}
                  onClick={col.sortable !== false ? () => handleSort(col.key) : undefined}
                  className={`px-4 py-3 text-left text-xs font-semibold text-slate-500 whitespace-nowrap select-none
                    ${col.sortable !== false ? 'cursor-pointer hover:text-slate-700' : ''}
                    ${col.width ? col.width : ''}`}
                >
                  {col.label}
                  {col.sortable !== false && <SortIcon col={col.key} />}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {loading ? (
              Array.from({ length: 6 }).map((_, i) => <SkeletonRow key={i} cols={columns.length} />)
            ) : filtered.length === 0 ? (
              <tr>
                <td colSpan={columns.length}>
                  <div className="flex flex-col items-center justify-center py-16 text-slate-400">
                    <InboxIcon className="w-10 h-10 mb-3 text-slate-300" />
                    <p className="text-sm font-medium">{emptyText}</p>
                  </div>
                </td>
              </tr>
            ) : (
              filtered.map(row => {
                const id = row[rowKey]
                const isSelected = selected && selected[rowKey] === id
                return (
                  <tr
                    key={id}
                    onClick={() => onRowClick?.(row)}
                    className={`border-b border-slate-100 transition-colors
                      ${onRowClick ? 'cursor-pointer' : ''}
                      ${isSelected
                        ? 'bg-brand-50 border-l-2 border-brand-500'
                        : 'hover:bg-slate-50'}`}
                  >
                    {columns.map(col => (
                      <td key={col.key} className="px-4 py-3 text-slate-700">
                        {col.render ? col.render(row[col.key], row) : (row[col.key] ?? '—')}
                      </td>
                    ))}
                  </tr>
                )
              })
            )}
          </tbody>
        </table>
      </div>

      {/* Footer */}
      <div className="px-4 py-2.5 border-t border-slate-100 text-xs text-slate-400 bg-white">
        {loading ? 'Loading…' : `${filtered.length} of ${data.length} records`}
      </div>
    </div>
  )
}
