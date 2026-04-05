import React from 'react'
import {
  PencilSquareIcon,
  PhoneIcon,
  UserGroupIcon,
  ClockIcon,
  DocumentPlusIcon,
  ArrowsRightLeftIcon,
  BanknotesIcon,
  WrenchScrewdriverIcon,
  SparklesIcon,
} from '@heroicons/react/24/outline'

const TYPE_META = {
  note:                { Icon: PencilSquareIcon,    color: 'bg-slate-100 text-slate-600'   },
  call:                { Icon: PhoneIcon,            color: 'bg-blue-100 text-blue-600'     },
  meeting:             { Icon: UserGroupIcon,        color: 'bg-violet-100 text-violet-600' },
  follow_up:           { Icon: ClockIcon,            color: 'bg-amber-100 text-amber-600'   },
  policy_created:      { Icon: DocumentPlusIcon,     color: 'bg-indigo-100 text-indigo-600' },
  status_change:       { Icon: ArrowsRightLeftIcon,  color: 'bg-teal-100 text-teal-600'     },
  commission_recorded: { Icon: BanknotesIcon,        color: 'bg-green-100 text-green-600'   },
  servicing:           { Icon: WrenchScrewdriverIcon,color: 'bg-slate-100 text-slate-600'   },
  upsell_opportunity:  { Icon: SparklesIcon,         color: 'bg-yellow-100 text-yellow-600' },
}

const FALLBACK = { Icon: PencilSquareIcon, color: 'bg-slate-100 text-slate-500' }

function formatTs(ts) {
  if (!ts) return ''
  return new Date(ts).toLocaleString('en-US', {
    day: '2-digit', month: 'short', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

function getDateGroup(ts) {
  if (!ts) return 'Older'
  const d = new Date(ts)
  const now = new Date()
  const diffMs = now - d
  const diffDays = Math.floor(diffMs / 86400000)
  if (diffDays === 0) return 'Today'
  if (diffDays === 1) return 'Yesterday'
  if (diffDays <= 7) return 'This week'
  return 'Older'
}

function SkeletonItem() {
  return (
    <div className="flex gap-3 pb-4">
      <div className="skeleton w-8 h-8 rounded-xl shrink-0" />
      <div className="flex-1 space-y-2 pt-1">
        <div className="skeleton h-3.5 rounded w-3/4" />
        <div className="skeleton h-3 rounded w-1/3" />
      </div>
    </div>
  )
}

export default function ActivityFeed({ activities = [], loading = false }) {
  if (loading) {
    return (
      <div className="space-y-1 px-1">
        <SkeletonItem />
        <SkeletonItem />
        <SkeletonItem />
      </div>
    )
  }

  if (!activities.length) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-slate-400">
        <ClockIcon className="w-8 h-8 mb-2 text-slate-300" />
        <p className="text-sm">No activity recorded yet.</p>
      </div>
    )
  }

  // Group by date label
  const groups = []
  let currentGroup = null
  activities.forEach(act => {
    const label = getDateGroup(act.timestamp)
    if (!currentGroup || currentGroup.label !== label) {
      currentGroup = { label, items: [] }
      groups.push(currentGroup)
    }
    currentGroup.items.push(act)
  })

  return (
    <div className="space-y-4">
      {groups.map(group => (
        <div key={group.label}>
          <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3 px-1">
            {group.label}
          </div>
          <div className="space-y-1">
            {group.items.map(act => {
              const meta = TYPE_META[act.activity_type] || FALLBACK
              const { Icon } = meta
              return (
                <div key={act.activity_id} className="relative flex gap-3 pb-4 timeline-item">
                  <div className={`shrink-0 w-8 h-8 rounded-xl flex items-center justify-center ${meta.color}`}>
                    <Icon className="w-4 h-4" />
                  </div>
                  <div className="flex-1 min-w-0 pt-0.5">
                    <p className="text-sm text-slate-700 leading-snug">{act.description}</p>
                    <p className="text-xs text-slate-400 mt-1">{formatTs(act.timestamp)}</p>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      ))}
    </div>
  )
}
