import React from 'react'

const STATUS_STYLES = {
  // Pipeline stages
  Lead:          { dot: 'bg-slate-400',   text: 'text-slate-600'  },
  Qualified:     { dot: 'bg-blue-500',    text: 'text-blue-700'   },
  Proposal:      { dot: 'bg-violet-500',  text: 'text-violet-700' },
  Negotiation:   { dot: 'bg-amber-500',   text: 'text-amber-700'  },
  Closed:        { dot: 'bg-green-500',   text: 'text-green-700'  },

  // Policy statuses
  Draft:         { dot: 'bg-slate-400',   text: 'text-slate-600'  },
  Submitted:     { dot: 'bg-blue-500',    text: 'text-blue-700'   },
  Underwriting:  { dot: 'bg-amber-500',   text: 'text-amber-700'  },
  Approved:      { dot: 'bg-indigo-500',  text: 'text-indigo-700' },
  Issued:        { dot: 'bg-green-500',   text: 'text-green-700'  },
  Rejected:      { dot: 'bg-red-500',     text: 'text-red-700'    },
  Lapsed:        { dot: 'bg-orange-500',  text: 'text-orange-700' },

  // Underwriting lifecycle states
  CREATED:                  { dot: 'bg-slate-400',   text: 'text-slate-600'  },
  IN_PROGRESS:              { dot: 'bg-blue-500',    text: 'text-blue-700'   },
  DATA_ENRICHED:            { dot: 'bg-violet-500',  text: 'text-violet-700' },
  RISK_CLASSIFIED:          { dot: 'bg-amber-500',   text: 'text-amber-700'  },
  DECISIONED:               { dot: 'bg-indigo-500',  text: 'text-indigo-700' },
  APPROVED:                 { dot: 'bg-emerald-500', text: 'text-emerald-700'},
  APPROVED_WITH_CONDITIONS: { dot: 'bg-teal-500',    text: 'text-teal-700'   },
  REJECTED:                 { dot: 'bg-red-500',     text: 'text-red-700'    },
  PENDED:                   { dot: 'bg-orange-500',  text: 'text-orange-700' },
  ISSUED:                   { dot: 'bg-green-500',   text: 'text-green-700'  },

  // Risk classes
  PREFERRED:    { dot: 'bg-emerald-500', text: 'text-emerald-700' },
  STANDARD:     { dot: 'bg-blue-500',    text: 'text-blue-700'    },
  SUBSTANDARD:  { dot: 'bg-amber-500',   text: 'text-amber-700'   },
  DECLINED:     { dot: 'bg-red-500',     text: 'text-red-700'     },
}

const FALLBACK = { dot: 'bg-slate-400', text: 'text-slate-600' }

export default function StatusBadge({ status, size = 'sm' }) {
  const style = STATUS_STYLES[status] || FALLBACK

  if (size === 'lg') {
    return (
      <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-sm font-medium bg-white border border-slate-200 ${style.text}`}>
        <span className={`w-2 h-2 rounded-full shrink-0 ${style.dot}`} />
        {status}
      </span>
    )
  }

  return (
    <span className={`inline-flex items-center gap-1 text-xs font-medium ${style.text}`}>
      <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${style.dot}`} />
      {status}
    </span>
  )
}
