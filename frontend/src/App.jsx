import React, { useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import {
  CheckCircleIcon,
  XCircleIcon,
  InformationCircleIcon,
  XMarkIcon,
} from '@heroicons/react/20/solid'
import Sidebar from './components/Sidebar.jsx'
import Pipeline from './pages/Pipeline.jsx'
import Clients from './pages/Clients.jsx'
import ClientDetail from './pages/ClientDetail.jsx'
import Products from './pages/Products.jsx'
import Applications from './pages/Applications.jsx'
import Policies from './pages/Policies.jsx'
import Commissions from './pages/Commissions.jsx'
import Renewals from './pages/Renewals.jsx'
import useStore from './store/useStore.js'

const TOAST_CONFIG = {
  success: { Icon: CheckCircleIcon,     bg: 'bg-emerald-600', bar: 'bg-emerald-400' },
  error:   { Icon: XCircleIcon,         bg: 'bg-red-600',     bar: 'bg-red-400'     },
  info:    { Icon: InformationCircleIcon,bg: 'bg-brand-600',   bar: 'bg-brand-400'   },
}

function Toast({ toast }) {
  const removeToast = useStore(s => s.removeToast)

  useEffect(() => {
    const t = setTimeout(() => removeToast(toast.id), 3500)
    return () => clearTimeout(t)
  }, [toast.id, removeToast])

  const cfg = TOAST_CONFIG[toast.type] || TOAST_CONFIG.info
  const { Icon } = cfg

  return (
    <div className={`${cfg.bg} text-white rounded-xl shadow-lg overflow-hidden animate-slide-up min-w-72 max-w-sm`}>
      <div className="flex items-center gap-3 px-4 py-3">
        <Icon className="w-5 h-5 shrink-0 opacity-90" />
        <span className="text-sm font-medium flex-1">{toast.msg}</span>
        <button
          onClick={() => removeToast(toast.id)}
          className="p-0.5 rounded hover:bg-white/20 transition-colors"
        >
          <XMarkIcon className="w-4 h-4" />
        </button>
      </div>
      {/* Auto-dismiss progress bar */}
      <div className="h-0.5 bg-white/20">
        <div
          className={`h-full ${cfg.bar} opacity-60`}
          style={{ animation: 'shrink-x 3.5s linear forwards' }}
        />
      </div>
    </div>
  )
}

export default function App() {
  const toasts = useStore(s => s.toasts)

  return (
    <BrowserRouter>
      <div className="flex h-screen bg-slate-50 overflow-hidden">
        <Sidebar />
        <main className="flex-1 overflow-auto">
          <Routes>
            <Route path="/" element={<Navigate to="/pipeline" replace />} />
            <Route path="/pipeline"      element={<Pipeline />} />
            <Route path="/clients"       element={<Clients />} />
            <Route path="/clients/:id"   element={<ClientDetail />} />
            <Route path="/products"      element={<Products />} />
            <Route path="/applications"  element={<Applications />} />
            <Route path="/policies"      element={<Policies />} />
            <Route path="/commissions"   element={<Commissions />} />
            <Route path="/renewals"      element={<Renewals />} />
          </Routes>
        </main>

        {/* Toast notifications */}
        <div className="fixed bottom-6 right-6 flex flex-col gap-3 z-50">
          {toasts.map(t => <Toast key={t.id} toast={t} />)}
        </div>
      </div>
    </BrowserRouter>
  )
}
