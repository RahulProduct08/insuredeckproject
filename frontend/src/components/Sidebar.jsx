import React from 'react'
import { NavLink, useNavigate } from 'react-router-dom'
import {
  UsersIcon, ChartBarIcon, ShieldCheckIcon, DocumentTextIcon,
  CheckBadgeIcon, ArrowPathIcon, BanknotesIcon, HomeIcon,
  PresentationChartLineIcon, ClipboardDocumentListIcon,
  ArrowRightStartOnRectangleIcon, ShareIcon, ScaleIcon,
  MagnifyingGlassCircleIcon, CpuChipIcon,
} from '@heroicons/react/24/outline'
import useStore from '../store/useStore.js'

const NAV_GROUPS = [
  {
    label: 'Overview',
    links: [
      { to: '/dashboard',      label: 'Dashboard',        Icon: HomeIcon },
      { to: '/analytics',      label: 'Analytics',        Icon: PresentationChartLineIcon },
      { to: '/hierarchy',      label: 'Agent Hierarchy',  Icon: ShareIcon },
    ],
  },
  {
    label: 'Pre-Sales',
    links: [
      { to: '/clients',        label: 'Leads / Clients',  Icon: UsersIcon },
      { to: '/pipeline',       label: 'Pipeline',         Icon: ChartBarIcon },
      { to: '/products',       label: 'Products',         Icon: ShieldCheckIcon },
      { to: '/needs-analysis', label: 'Needs Analysis',   Icon: ClipboardDocumentListIcon },
    ],
  },
  {
    label: 'During Sales',
    links: [
      { to: '/applications',   label: 'Applications',     Icon: DocumentTextIcon },
      { to: '/underwriting',   label: 'Underwriting',     Icon: MagnifyingGlassCircleIcon },
    ],
  },
  {
    label: 'Post-Sales',
    links: [
      { to: '/policies',           label: 'Policies',          Icon: CheckBadgeIcon },
      { to: '/renewals',           label: 'Renewals',          Icon: ArrowPathIcon },
      { to: '/commissions',        label: 'Commissions',       Icon: BanknotesIcon },
      { to: '/commission-ledger',  label: 'Ledger',            Icon: ScaleIcon },
    ],
  },
  {
    label: 'Simulation',
    links: [
      { to: '/agent-chat', label: 'SAM Agent', Icon: CpuChipIcon },
    ],
  },
]

function initials(name) {
  if (!name) return '??'
  return name.split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase()
}

export default function Sidebar() {
  const navigate = useNavigate()
  const { agent, logout, tasks } = useStore()
  const overdueTasks = (tasks || []).filter(t =>
    t.status === 'open' && t.due_date && new Date(t.due_date) < new Date()
  )

  const handleLogout = () => {
    logout()
    navigate('/login', { replace: true })
  }

  return (
    <aside className="w-56 bg-slate-900 flex flex-col shrink-0">
      {/* Logo */}
      <div className="px-4 py-5 flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg bg-brand-600 flex items-center justify-center shrink-0">
          <ShieldCheckIcon className="w-5 h-5 text-white" />
        </div>
        <div>
          <div className="text-sm font-bold text-white leading-tight">InsureDesk</div>
          <div className="text-xs text-slate-400">Agent Portal</div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto px-2 pb-4">
        {NAV_GROUPS.map(group => (
          <div key={group.label} className="mb-5">
            <div className="px-3 mb-1 text-xs font-semibold uppercase tracking-widest text-slate-500">
              {group.label}
            </div>
            {group.links.map(({ to, label, Icon }) => (
              <NavLink
                key={to} to={to}
                className={({ isActive }) =>
                  `relative flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors mb-0.5 ${
                    isActive
                      ? 'bg-brand-600 text-white'
                      : 'text-slate-300 hover:text-white hover:bg-slate-800'
                  }`
                }
              >
                <Icon className="w-4 h-4 shrink-0" />
                <span>{label}</span>
                {label === 'Dashboard' && overdueTasks.length > 0 && (
                  <span className="ml-auto min-w-[18px] h-[18px] px-1 text-xs font-bold bg-red-500 text-white rounded-full flex items-center justify-center">
                    {overdueTasks.length}
                  </span>
                )}
              </NavLink>
            ))}
          </div>
        ))}
      </nav>

      {/* Agent footer */}
      <div className="px-4 py-4 border-t border-slate-800">
        <div className="flex items-center gap-2.5 mb-3">
          <div className="w-8 h-8 rounded-full bg-brand-700 flex items-center justify-center shrink-0">
            <span className="text-xs font-bold text-white">{initials(agent?.name)}</span>
          </div>
          <div className="min-w-0 flex-1">
            <div className="text-xs font-medium text-slate-300 truncate">{agent?.name || 'Agent'}</div>
            <div className="text-xs text-slate-500 capitalize truncate">{agent?.role || 'agent'}</div>
          </div>
        </div>
        <button
          onClick={handleLogout}
          className="w-full flex items-center gap-2 px-2 py-1.5 text-xs text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition-colors"
        >
          <ArrowRightStartOnRectangleIcon className="w-4 h-4" />
          Sign Out
        </button>
      </div>
    </aside>
  )
}
