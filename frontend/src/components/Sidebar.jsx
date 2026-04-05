import React from 'react'
import { NavLink } from 'react-router-dom'
import {
  UsersIcon,
  ChartBarIcon,
  ShieldCheckIcon,
  DocumentTextIcon,
  CheckBadgeIcon,
  ArrowPathIcon,
  BanknotesIcon,
} from '@heroicons/react/24/outline'

const NAV_GROUPS = [
  {
    label: 'Pre-Sales',
    links: [
      { to: '/clients',      label: 'Leads / Clients', Icon: UsersIcon },
      { to: '/pipeline',     label: 'Pipeline',         Icon: ChartBarIcon },
      { to: '/products',     label: 'Products',         Icon: ShieldCheckIcon },
    ],
  },
  {
    label: 'During Sales',
    links: [
      { to: '/applications', label: 'Applications',     Icon: DocumentTextIcon },
    ],
  },
  {
    label: 'Post-Sales',
    links: [
      { to: '/policies',     label: 'Policies',         Icon: CheckBadgeIcon },
      { to: '/renewals',     label: 'Renewals',         Icon: ArrowPathIcon },
      { to: '/commissions',  label: 'Commissions',      Icon: BanknotesIcon },
    ],
  },
]

export default function Sidebar() {
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
                key={to}
                to={to}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors mb-0.5 ${
                    isActive
                      ? 'bg-brand-600 text-white'
                      : 'text-slate-300 hover:text-white hover:bg-slate-800'
                  }`
                }
              >
                <Icon className="w-4 h-4 shrink-0" />
                <span>{label}</span>
              </NavLink>
            ))}
          </div>
        ))}
      </nav>

      {/* Footer */}
      <div className="px-4 py-4 border-t border-slate-800 flex items-center gap-3">
        <div className="w-7 h-7 rounded-full bg-brand-700 flex items-center justify-center shrink-0">
          <span className="text-xs font-bold text-white">A1</span>
        </div>
        <div className="min-w-0">
          <div className="text-xs font-medium text-slate-300 truncate">Agent</div>
          <div className="text-xs text-slate-500 truncate">AGENT-001</div>
        </div>
      </div>
    </aside>
  )
}
