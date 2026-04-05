import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  CheckCircleIcon, ClockIcon, ExclamationTriangleIcon,
  PlusIcon, ChartBarIcon, UsersIcon, DocumentTextIcon, BanknotesIcon,
} from '@heroicons/react/24/outline'
import { CheckCircleIcon as CheckCircleSolid } from '@heroicons/react/20/solid'
import useStore from '../store/useStore.js'

const PRIORITY_COLORS = {
  high:   { bg: 'bg-red-50',    border: 'border-red-200',    text: 'text-red-700',    dot: 'bg-red-500'    },
  medium: { bg: 'bg-amber-50',  border: 'border-amber-200',  text: 'text-amber-700',  dot: 'bg-amber-500'  },
  low:    { bg: 'bg-slate-50',  border: 'border-slate-200',  text: 'text-slate-600',  dot: 'bg-slate-400'  },
}

function isOverdue(due) {
  if (!due) return false
  return new Date(due) < new Date()
}

function TaskCard({ task, onComplete }) {
  const overdue = isOverdue(task.due_date)
  const pc = PRIORITY_COLORS[task.priority] || PRIORITY_COLORS.low
  return (
    <div className={`flex items-start gap-3 p-3 rounded-xl border ${pc.bg} ${pc.border} group`}>
      <button
        onClick={() => onComplete(task.task_id)}
        className="mt-0.5 w-5 h-5 rounded-full border-2 border-current flex-shrink-0 hover:bg-white/60 transition-colors"
        style={{ color: pc.dot.replace('bg-', '') === pc.dot ? '#94a3b8' : undefined }}
      />
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className={`text-sm font-medium ${overdue ? 'text-red-700' : 'text-slate-800'}`}>
            {task.title}
          </span>
          {overdue && <ExclamationTriangleIcon className="w-4 h-4 text-red-500 shrink-0" />}
        </div>
        {task.client_name && (
          <p className="text-xs text-slate-500 mt-0.5">{task.client_name}</p>
        )}
        {task.due_date && (
          <p className={`text-xs mt-0.5 ${overdue ? 'text-red-600 font-medium' : 'text-slate-400'}`}>
            {overdue ? 'Overdue: ' : 'Due: '}
            {new Date(task.due_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
          </p>
        )}
      </div>
      <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${pc.bg} ${pc.text} border ${pc.border} shrink-0`}>
        {task.priority}
      </span>
    </div>
  )
}

function KpiCard({ label, value, sub, Icon, color }) {
  return (
    <div className="bg-white rounded-2xl shadow-card p-5 flex items-start gap-4">
      <div className={`w-11 h-11 rounded-xl flex items-center justify-center shrink-0 ${color}`}>
        <Icon className="w-6 h-6" />
      </div>
      <div>
        <p className="text-xs font-medium text-slate-500">{label}</p>
        <p className="text-2xl font-bold text-slate-900 mt-0.5">{value}</p>
        {sub && <p className="text-xs text-slate-400 mt-0.5">{sub}</p>}
      </div>
    </div>
  )
}

export default function Dashboard() {
  const navigate = useNavigate()
  const { agent, tasks, fetchTasks, tasksLoading, updateTask, analytics, fetchAnalytics } = useStore()
  const [showNewTask, setShowNewTask] = useState(false)
  const [newTask, setNewTask] = useState({ title: '', priority: 'medium', due_date: '' })
  const { createTask } = useStore()

  useEffect(() => {
    fetchTasks({ agent_id: agent?.role === 'admin' ? undefined : agent?.agent_id, status: 'open' })
    fetchAnalytics()
  }, [])

  const overdueTasks = tasks.filter(t => isOverdue(t.due_date) && t.status === 'open')
  const todayTasks = tasks.filter(t => {
    if (!t.due_date || t.status !== 'open') return false
    const due = new Date(t.due_date).toDateString()
    const today = new Date().toDateString()
    return due === today
  })
  const upcomingTasks = tasks.filter(t => {
    if (!t.due_date || t.status !== 'open') return false
    const due = new Date(t.due_date)
    const today = new Date()
    today.setHours(0, 0, 0, 0)
    return due > today
  })

  const handleComplete = async (taskId) => {
    await updateTask(taskId, { status: 'completed' })
    fetchTasks({ agent_id: agent?.role === 'admin' ? undefined : agent?.agent_id, status: 'open' })
  }

  const handleCreateTask = async (e) => {
    e.preventDefault()
    await createTask({ ...newTask, agent_id: agent?.agent_id })
    setNewTask({ title: '', priority: 'medium', due_date: '' })
    setShowNewTask(false)
    fetchTasks({ agent_id: agent?.role === 'admin' ? undefined : agent?.agent_id, status: 'open' })
  }

  const pipeline = analytics?.pipeline || {}
  const totalClients = Object.values(pipeline).reduce((a, b) => a + b, 0)

  return (
    <div className="flex flex-col h-full overflow-auto">
      {/* Header */}
      <div className="px-6 py-4 border-b border-slate-200 bg-white shrink-0">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-semibold text-slate-900">
              Good {new Date().getHours() < 12 ? 'morning' : new Date().getHours() < 17 ? 'afternoon' : 'evening'},{' '}
              {agent?.name?.split(' ')[0]}
            </h1>
            <p className="text-sm text-slate-500">
              {overdueTasks.length > 0
                ? `${overdueTasks.length} overdue task${overdueTasks.length > 1 ? 's' : ''} need your attention`
                : `${tasks.length} open tasks`}
            </p>
          </div>
          <button
            onClick={() => setShowNewTask(true)}
            className="flex items-center gap-2 px-4 py-2 bg-brand-600 text-white text-sm font-medium rounded-xl hover:bg-brand-700 transition-colors"
          >
            <PlusIcon className="w-4 h-4" />
            New Task
          </button>
        </div>
      </div>

      <div className="flex-1 p-6 space-y-6">
        {/* KPI row */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <KpiCard
            label="Total Clients" value={totalClients}
            sub={`${pipeline['Closed'] || 0} closed`}
            Icon={UsersIcon} color="bg-brand-50 text-brand-600"
          />
          <KpiCard
            label="Policies MTD" value={analytics?.policies_mtd?.count ?? '—'}
            sub={analytics?.policies_mtd?.premium ? `$${Number(analytics.policies_mtd.premium).toLocaleString('en-US')} premium` : ''}
            Icon={DocumentTextIcon} color="bg-emerald-50 text-emerald-600"
          />
          <KpiCard
            label="Commissions MTD" value={analytics?.commissions_mtd != null ? `$${Number(analytics.commissions_mtd).toLocaleString('en-US', { maximumFractionDigits: 0 })}` : '—'}
            sub="Month to date"
            Icon={BanknotesIcon} color="bg-amber-50 text-amber-600"
          />
          <KpiCard
            label="Renewals (30d)" value={analytics?.renewals?.['30_days']?.count ?? '—'}
            sub={analytics?.renewals?.['30_days']?.premium ? `$${Number(analytics.renewals['30_days'].premium).toLocaleString('en-US')} at risk` : ''}
            Icon={ClockIcon} color="bg-purple-50 text-purple-600"
          />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Tasks column */}
          <div className="lg:col-span-2 space-y-4">
            {/* Overdue */}
            {overdueTasks.length > 0 && (
              <div>
                <h3 className="text-xs font-semibold text-red-600 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                  <ExclamationTriangleIcon className="w-3.5 h-3.5" />
                  Overdue ({overdueTasks.length})
                </h3>
                <div className="space-y-2">
                  {overdueTasks.map(t => (
                    <TaskCard key={t.task_id} task={t} onComplete={handleComplete} />
                  ))}
                </div>
              </div>
            )}

            {/* Due today */}
            {todayTasks.length > 0 && (
              <div>
                <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                  <ClockIcon className="w-3.5 h-3.5" />
                  Due Today ({todayTasks.length})
                </h3>
                <div className="space-y-2">
                  {todayTasks.map(t => (
                    <TaskCard key={t.task_id} task={t} onComplete={handleComplete} />
                  ))}
                </div>
              </div>
            )}

            {/* Upcoming */}
            {upcomingTasks.length > 0 && (
              <div>
                <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">
                  Upcoming
                </h3>
                <div className="space-y-2">
                  {upcomingTasks.slice(0, 5).map(t => (
                    <TaskCard key={t.task_id} task={t} onComplete={handleComplete} />
                  ))}
                </div>
              </div>
            )}

            {tasks.length === 0 && !tasksLoading && (
              <div className="text-center py-12 text-slate-400">
                <CheckCircleSolid className="w-12 h-12 mx-auto mb-3 text-emerald-300" />
                <p className="font-medium">All caught up!</p>
                <p className="text-sm">No open tasks.</p>
              </div>
            )}
          </div>

          {/* Pipeline summary */}
          <div className="bg-white rounded-2xl shadow-card p-5">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-semibold text-slate-800">Pipeline</h3>
              <button onClick={() => navigate('/pipeline')}
                className="text-xs text-brand-600 hover:underline">View →</button>
            </div>
            <div className="space-y-3">
              {[
                { stage: 'Lead',        color: 'bg-slate-400' },
                { stage: 'Qualified',   color: 'bg-blue-400'  },
                { stage: 'Proposal',    color: 'bg-amber-400' },
                { stage: 'Negotiation', color: 'bg-orange-400'},
                { stage: 'Closed',      color: 'bg-emerald-500'},
              ].map(({ stage, color }) => {
                const count = pipeline[stage] || 0
                const pct = totalClients ? Math.round(count / totalClients * 100) : 0
                return (
                  <div key={stage}>
                    <div className="flex items-center justify-between text-xs mb-1">
                      <span className="text-slate-600">{stage}</span>
                      <span className="font-medium text-slate-800">{count}</span>
                    </div>
                    <div className="h-1.5 bg-slate-100 rounded-full overflow-hidden">
                      <div className={`h-full ${color} rounded-full transition-all`} style={{ width: `${pct}%` }} />
                    </div>
                  </div>
                )
              })}
            </div>

            <div className="mt-5 pt-4 border-t border-slate-100 grid grid-cols-2 gap-2">
              <button onClick={() => navigate('/analytics')}
                className="py-2 text-xs font-medium text-brand-600 border border-brand-200 rounded-lg hover:bg-brand-50 transition-colors">
                Analytics
              </button>
              <button onClick={() => navigate('/renewals')}
                className="py-2 text-xs font-medium text-slate-600 border border-slate-200 rounded-lg hover:bg-slate-50 transition-colors">
                Renewals
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* New Task Modal */}
      {showNewTask && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-panel w-full max-w-md p-6 animate-slide-up">
            <h3 className="text-base font-semibold text-slate-800 mb-4">New Task</h3>
            <form onSubmit={handleCreateTask} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Title</label>
                <input
                  required value={newTask.title}
                  onChange={e => setNewTask(n => ({ ...n, title: e.target.value }))}
                  className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                  placeholder="Task description…"
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Priority</label>
                  <select
                    value={newTask.priority}
                    onChange={e => setNewTask(n => ({ ...n, priority: e.target.value }))}
                    className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                  >
                    <option value="high">High</option>
                    <option value="medium">Medium</option>
                    <option value="low">Low</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Due Date</label>
                  <input
                    type="date" value={newTask.due_date}
                    onChange={e => setNewTask(n => ({ ...n, due_date: e.target.value }))}
                    className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                  />
                </div>
              </div>
              <div className="flex gap-2 pt-2">
                <button type="button" onClick={() => setShowNewTask(false)}
                  className="flex-1 py-2 text-sm font-medium text-slate-600 border border-slate-200 rounded-lg hover:bg-slate-50">
                  Cancel
                </button>
                <button type="submit"
                  className="flex-1 py-2 text-sm font-semibold text-white bg-brand-600 hover:bg-brand-700 rounded-lg transition-colors">
                  Create Task
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
