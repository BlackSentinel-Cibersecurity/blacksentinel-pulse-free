import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import {
  Bell, AlertTriangle, CheckCircle, XCircle, Clock,
  Filter, RefreshCw, Eye, Shield, ExternalLink
} from 'lucide-react'
import { alertsAPI } from '../services/api'

interface Alert {
  id: string
  title: string
  description: string
  severity: string
  status: string
  source: string
  asset_id?: number
  asset_name?: string
  created_at: string
  acknowledged_at?: string
  resolved_at?: string
}

const SEVERITY_STYLES: Record<string, string> = {
  critical: 'border-l-red-500 bg-red-500/5',
  high: 'border-l-sentinel-orange-500 bg-sentinel-orange-500/5',
  medium: 'border-l-yellow-500 bg-yellow-500/5',
  low: 'border-l-emerald-500 bg-emerald-500/5',
  info: 'border-l-blue-500 bg-blue-500/5',
}

const SEVERITY_BADGES: Record<string, string> = {
  critical: 'badge-critical',
  high: 'badge-high',
  medium: 'badge-medium',
  low: 'badge-low',
  info: 'badge-info',
}

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [stats, setStats] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [severityFilter, setSeverityFilter] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [expandedId, setExpandedId] = useState<string | null>(null)
  const [resolveNotes, setResolveNotes] = useState('')

  useEffect(() => {
    fetchAlerts()
    fetchStats()
  }, [severityFilter, statusFilter])

  const fetchAlerts = async () => {
    try {
      const response = await alertsAPI.list({
        severity: severityFilter || undefined,
        status: statusFilter || undefined,
      })
      setAlerts(response.data.items || response.data)
    } catch (error) {
      console.error('Failed to fetch alerts:', error)
    } finally {
      setLoading(false)
    }
  }

  const fetchStats = async () => {
    try {
      const response = await alertsAPI.getStats()
      setStats(response.data)
    } catch (error) {
      console.error('Failed to fetch alert stats:', error)
    }
  }

  const handleAcknowledge = async (id: string) => {
    try {
      await alertsAPI.acknowledge(id)
      fetchAlerts()
      fetchStats()
    } catch (error) {
      console.error('Failed to acknowledge alert:', error)
    }
  }

  const handleResolve = async (id: string) => {
    try {
      await alertsAPI.resolve(id, resolveNotes || undefined)
      setResolveNotes('')
      setExpandedId(null)
      fetchAlerts()
      fetchStats()
    } catch (error) {
      console.error('Failed to resolve alert:', error)
    }
  }

  const handleFalsePositive = async (id: string) => {
    try {
      await alertsAPI.markFalsePositive(id)
      fetchAlerts()
      fetchStats()
    } catch (error) {
      console.error('Failed to mark false positive:', error)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Security Alerts</h1>
          <p className="text-sentinel-gray-400 mt-1">
            Monitor and respond to security alerts
          </p>
        </div>
        <button onClick={() => { fetchAlerts(); fetchStats() }} className="btn-secondary flex items-center gap-2">
          <RefreshCw className="w-4 h-4" />
          Refresh
        </button>
      </div>

      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[
            { label: 'Open', value: stats.open || 0, icon: AlertTriangle, color: 'sentinel-orange' },
            { label: 'Acknowledged', value: stats.acknowledged || 0, icon: Eye, color: 'blue' },
            { label: 'Resolved', value: stats.resolved || 0, icon: CheckCircle, color: 'emerald' },
            { label: 'Critical', value: stats.critical || 0, icon: Shield, color: 'red' },
          ].map((item, index) => (
            <motion.div
              key={item.label}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.05 }}
              className="stat-card"
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sentinel-gray-400 text-sm">{item.label}</p>
                  <p className="text-2xl font-bold text-white mt-1">{item.value}</p>
                </div>
                <div className={`w-10 h-10 rounded-lg bg-${item.color}-500/10 border border-${item.color}-500/20 flex items-center justify-center`}>
                  <item.icon className={`w-5 h-5 text-${item.color}-400`} />
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      )}

      {/* Filters */}
      <div className="card p-4">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-sentinel-gray-400" />
            <span className="text-sm text-sentinel-gray-400">Severity:</span>
          </div>
          {['', 'critical', 'high', 'medium', 'low', 'info'].map((sev) => (
            <button
              key={sev}
              onClick={() => setSeverityFilter(sev)}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                severityFilter === sev
                  ? 'bg-sentinel-orange-500/20 text-sentinel-orange-500 border border-sentinel-orange-500/30'
                  : 'bg-sentinel-gray-800 text-sentinel-gray-400 hover:text-white border border-sentinel-gray-700'
              }`}
            >
              {sev || 'All'}
            </button>
          ))}
          <div className="w-px h-6 bg-sentinel-gray-700" />
          <span className="text-sm text-sentinel-gray-400">Status:</span>
          {['', 'open', 'acknowledged', 'resolved'].map((status) => (
            <button
              key={status}
              onClick={() => setStatusFilter(status)}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                statusFilter === status
                  ? 'bg-sentinel-orange-500/20 text-sentinel-orange-500 border border-sentinel-orange-500/30'
                  : 'bg-sentinel-gray-800 text-sentinel-gray-400 hover:text-white border border-sentinel-gray-700'
              }`}
            >
              {status || 'All'}
            </button>
          ))}
        </div>
      </div>

      {/* Alerts List */}
      <div className="space-y-3">
        {loading ? (
          <div className="card p-12 text-center">
            <div className="spinner mx-auto mb-4" />
            <p className="text-sentinel-gray-400">Loading alerts...</p>
          </div>
        ) : alerts.length === 0 ? (
          <div className="card p-12 text-center">
            <Bell className="w-12 h-12 text-sentinel-gray-600 mx-auto mb-4" />
            <p className="text-sentinel-gray-400">No alerts found</p>
          </div>
        ) : (
          alerts.map((alert, index) => (
            <motion.div
              key={alert.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.02 }}
              className={`card border-l-4 ${SEVERITY_STYLES[alert.severity] || ''} ${
                expandedId === alert.id ? 'ring-1 ring-sentinel-orange-500/30' : ''
              }`}
            >
              <div
                className="p-4 cursor-pointer"
                onClick={() => setExpandedId(expandedId === alert.id ? null : alert.id)}
              >
                <div className="flex items-start gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-3 mb-1">
                      <h3 className="text-sm font-semibold text-white">{alert.title}</h3>
                      <span className={`badge ${SEVERITY_BADGES[alert.severity] || ''}`}>
                        {alert.severity}
                      </span>
                      <span className={`text-xs font-medium capitalize ${
                        alert.status === 'resolved' ? 'text-emerald-400' :
                        alert.status === 'acknowledged' ? 'text-blue-400' :
                        'text-sentinel-orange-500'
                      }`}>
                        {alert.status}
                      </span>
                    </div>
                    <p className="text-xs text-sentinel-gray-400 line-clamp-1">{alert.description}</p>
                    <div className="flex items-center gap-4 mt-2">
                      <span className="text-xs text-sentinel-gray-500">Source: {alert.source}</span>
                      {alert.asset_name && (
                        <span className="text-xs text-sentinel-gray-500">Asset: {alert.asset_name}</span>
                      )}
                      <span className="text-xs text-sentinel-gray-500">
                        {alert.created_at ? new Date(alert.created_at).toLocaleString() : '-'}
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Expanded Actions */}
              {expandedId === alert.id && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  className="border-t border-sentinel-gray-800 px-4 py-3"
                >
                  <p className="text-xs text-sentinel-gray-400 mb-3">{alert.description}</p>
                  {alert.status !== 'resolved' && (
                    <div className="flex items-center gap-3">
                      {alert.status === 'open' && (
                        <button
                          onClick={(e) => { e.stopPropagation(); handleAcknowledge(alert.id) }}
                          className="btn-secondary text-xs flex items-center gap-1.5"
                        >
                          <Eye className="w-3 h-3" />
                          Acknowledge
                        </button>
                      )}
                      <button
                        onClick={(e) => { e.stopPropagation(); handleResolve(alert.id) }}
                        className="btn-primary text-xs flex items-center gap-1.5"
                      >
                        <CheckCircle className="w-3 h-3" />
                        Resolve
                      </button>
                      <button
                        onClick={(e) => { e.stopPropagation(); handleFalsePositive(alert.id) }}
                        className="btn-ghost text-xs flex items-center gap-1.5 text-sentinel-gray-400"
                      >
                        <XCircle className="w-3 h-3" />
                        False Positive
                      </button>
                    </div>
                  )}
                </motion.div>
              )}
            </motion.div>
          ))
        )}
      </div>
    </div>
  )
}
