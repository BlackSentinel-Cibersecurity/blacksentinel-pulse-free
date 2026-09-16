import { useState, useEffect, useCallback } from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  Shield, Search, AlertTriangle,
  CheckCircle, Clock, LucideIcon
} from 'lucide-react'
import { vulnsAPI } from '../services/api'

const SEVERITY_COLORS: Record<string, string> = {
  critical: 'badge-critical',
  high: 'badge-high',
  medium: 'badge-medium',
  low: 'badge-low',
  info: 'badge-info',
}

const STATUS_ICONS: Record<string, LucideIcon> = {
  open: AlertTriangle,
  confirmed: CheckCircle,
  remediated: CheckCircle,
  false_positive: CheckCircle,
}

interface Vulnerability {
  id: number
  title?: string
  external_id?: string
  severity: string
  status: string
  asset_id?: number
  asset_name?: string
  cvss_score?: number
}

interface VulnStats {
  critical?: number
  high?: number
  medium?: number
  low?: number
  info?: number
}

export default function VulnerabilitiesPage() {
  const [vulns, setVulns] = useState<Vulnerability[]>([])
  const [stats, setStats] = useState<VulnStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [severityFilter, setSeverityFilter] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)

  const fetchVulns = useCallback(async () => {
    try {
      const response = await vulnsAPI.list({
        search,
        severity: severityFilter || undefined,
        status: statusFilter || undefined,
        page,
        page_size: 20,
      })
      setVulns(response.data.items || [])
      setTotal(response.data.total || 0)
    } catch (error) {
      console.error('Failed to fetch vulnerabilities:', error)
    } finally {
      setLoading(false)
    }
  }, [search, severityFilter, statusFilter, page])

  const fetchStats = useCallback(async () => {
    try {
      const response = await vulnsAPI.getStats()
      setStats(response.data)
    } catch (error) {
      console.error('Failed to fetch vulnerability stats:', error)
    }
  }, [])

  useEffect(() => {
    fetchVulns()
    fetchStats()
  }, [fetchVulns, fetchStats])

  const handleStatusChange = async (id: number, status: string) => {
    try {
      await vulnsAPI.updateStatus(id, status)
      fetchVulns()
      fetchStats()
    } catch (error) {
      console.error('Failed to update status:', error)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Vulnerabilities</h1>
          <p className="text-sentinel-gray-400 mt-1">
            Track and manage security vulnerabilities
          </p>
        </div>
      </div>

      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
          {[
            { label: 'Critical', value: stats.critical || 0, color: 'red' },
            { label: 'High', value: stats.high || 0, color: 'sentinel-orange' },
            { label: 'Medium', value: stats.medium || 0, color: 'yellow' },
            { label: 'Low', value: stats.low || 0, color: 'emerald' },
            { label: 'Info', value: stats.info || 0, color: 'blue' },
          ].map((item, index) => (
            <motion.div
              key={item.label}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.05 }}
              className="stat-card"
            >
              <p className="text-sentinel-gray-400 text-sm">{item.label}</p>
              <p className="text-2xl font-bold text-white mt-1">{item.value}</p>
            </motion.div>
          ))}
        </div>
      )}

      {/* Filters */}
      <div className="card p-4">
        <div className="flex items-center gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-sentinel-gray-500" />
            <input
              type="text"
              placeholder="Search vulnerabilities..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="input pl-10"
            />
          </div>
          <select
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value)}
            className="input w-40"
          >
            <option value="">All Severity</option>
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
            <option value="info">Info</option>
          </select>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="input w-40"
          >
            <option value="">All Status</option>
            <option value="open">Open</option>
            <option value="confirmed">Confirmed</option>
            <option value="remediated">Remediated</option>
            <option value="false_positive">False Positive</option>
          </select>
        </div>
      </div>

      {/* Vuln List */}
      <div className="card overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="border-b border-sentinel-gray-800 bg-sentinel-gray-900/50">
              <th className="text-left py-3 px-4 text-xs font-medium text-sentinel-gray-400 uppercase">Vulnerability</th>
              <th className="text-left py-3 px-4 text-xs font-medium text-sentinel-gray-400 uppercase">Severity</th>
              <th className="text-left py-3 px-4 text-xs font-medium text-sentinel-gray-400 uppercase">Status</th>
              <th className="text-left py-3 px-4 text-xs font-medium text-sentinel-gray-400 uppercase">Asset</th>
              <th className="text-left py-3 px-4 text-xs font-medium text-sentinel-gray-400 uppercase">CVSS</th>
              <th className="text-left py-3 px-4 text-xs font-medium text-sentinel-gray-400 uppercase">Actions</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={6} className="py-12 text-center">
                  <div className="spinner mx-auto mb-4" />
                  <p className="text-sentinel-gray-400">Loading vulnerabilities...</p>
                </td>
              </tr>
            ) : vulns.length === 0 ? (
              <tr>
                <td colSpan={6} className="py-12 text-center">
                  <Shield className="w-12 h-12 text-sentinel-gray-600 mx-auto mb-4" />
                  <p className="text-sentinel-gray-400">No vulnerabilities found</p>
                </td>
              </tr>
            ) : (
              vulns.map((vuln, index) => {
                const StatusIcon = STATUS_ICONS[vuln.status] || Clock
                return (
                  <motion.tr
                    key={vuln.id}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.02 }}
                    className="table-row"
                  >
                    <td className="py-3 px-4">
                      <div>
                        <p className="text-sm font-medium text-white">{vuln.title || vuln.external_id}</p>
                        <p className="text-xs text-sentinel-gray-500 mt-0.5">{vuln.external_id || vuln.severity}</p>
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      <span className={`badge ${SEVERITY_COLORS[vuln.severity] || ''}`}>
                        {vuln.severity}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <span className={`inline-flex items-center gap-1.5 text-xs font-medium capitalize ${
                        vuln.status === 'remediated' ? 'text-emerald-400' :
                        vuln.status === 'open' ? 'text-sentinel-orange-500' :
                        'text-sentinel-gray-400'
                      }`}>
                        <StatusIcon className="w-3 h-3" />
                        {vuln.status?.replace('_', ' ')}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <Link
                        to={`/assets/${vuln.asset_id}`}
                        className="text-sm text-sentinel-gray-300 hover:text-sentinel-orange-500 transition-colors"
                      >
                        {vuln.asset_name || `Asset #${vuln.asset_id}`}
                      </Link>
                    </td>
                    <td className="py-3 px-4">
                      <span className={`text-sm font-mono font-medium ${
                        (vuln.cvss_score || 0) >= 9 ? 'text-red-400' :
                        (vuln.cvss_score || 0) >= 7 ? 'text-sentinel-orange-500' :
                        'text-sentinel-gray-300'
                      }`}>
                        {vuln.cvss_score?.toFixed(1) || '-'}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-1">
                        {vuln.status !== 'remediated' && (
                          <select
                            value={vuln.status}
                            onChange={(e) => handleStatusChange(vuln.id, e.target.value)}
                            className="text-xs bg-sentinel-gray-800 border border-sentinel-gray-700 rounded px-2 py-1 text-sentinel-gray-300"
                          >
                            <option value="open">Open</option>
                            <option value="confirmed">Confirmed</option>
                            <option value="remediated">Remediated</option>
                            <option value="false_positive">False Positive</option>
                          </select>
                        )}
                      </div>
                    </td>
                  </motion.tr>
                )
              })
            )}
          </tbody>
        </table>

        {total > 20 && (
          <div className="flex items-center justify-between px-4 py-3 border-t border-sentinel-gray-800">
            <p className="text-sm text-sentinel-gray-400">
              Showing {((page - 1) * 20) + 1} to {Math.min(page * 20, total)} of {total}
            </p>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setPage(Math.max(1, page - 1))}
                disabled={page === 1}
                className="btn-ghost text-sm disabled:opacity-50"
              >
                Previous
              </button>
              <button
                onClick={() => setPage(page + 1)}
                disabled={page * 20 >= total}
                className="btn-ghost text-sm disabled:opacity-50"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
