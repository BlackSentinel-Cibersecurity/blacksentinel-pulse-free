import { useState, useEffect, useCallback } from 'react'
import { motion } from 'framer-motion'
import {
  Radar, Plus, Play, X, Clock, CheckCircle, XCircle,
  Loader2, RefreshCw, Filter
} from 'lucide-react'
import { scansAPI } from '../services/api'

interface Scan {
  id: string
  name: string
  scan_type: string
  status: string
  progress: number
  targets: string[]
  created_at: string
  completed_at?: string
  findings_count: number
}

const SCAN_TYPES = [
  { value: 'full_discovery', label: 'Full Discovery' },
  { value: 'passive_recon', label: 'Passive Recon' },
  { value: 'active_scan', label: 'Active Scan' },
  { value: 'vulnerability_scan', label: 'Vulnerability Scan' },
  { value: 'port_scan', label: 'Port Scan' },
  { value: 'web_scan', label: 'Web Application' },
  { value: 'cloud_scan', label: 'Cloud Scan' },
  { value: 'dns_enumeration', label: 'DNS Enumeration' },
  { value: 'ssl_scan', label: 'SSL/TLS Scan' },
]

const STATUS_COLORS: Record<string, string> = {
  running: 'text-blue-400 bg-blue-500/10 border-blue-500/20',
  completed: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20',
  failed: 'text-red-400 bg-red-500/10 border-red-500/20',
  cancelled: 'text-sentinel-gray-400 bg-sentinel-gray-500/10 border-sentinel-gray-500/20',
  pending: 'text-yellow-400 bg-yellow-500/10 border-yellow-500/20',
}

export default function ScansPage() {
  const [scans, setScans] = useState<Scan[]>([])
  const [loading, setLoading] = useState(true)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [creating, setCreating] = useState(false)
  const [statusFilter, setStatusFilter] = useState('')
  const [newScan, setNewScan] = useState({
    name: '',
    scan_type: 'full',
    targets: '',
  })

  const fetchScans = useCallback(async () => {
    try {
      const response = await scansAPI.list({ status: statusFilter || undefined })
      setScans(response.data.items || response.data)
    } catch (error) {
      console.error('Failed to fetch scans:', error)
    } finally {
      setLoading(false)
    }
  }, [statusFilter])

  useEffect(() => {
    fetchScans()
    const interval = setInterval(fetchScans, 10000)
    return () => clearInterval(interval)
  }, [fetchScans])

  const handleCreateScan = async () => {
    if (!newScan.name || !newScan.targets) return
    setCreating(true)
    try {
      await scansAPI.create({
        name: newScan.name,
        scan_type: newScan.scan_type,
        targets: newScan.targets.split(',').map((t) => t.trim()),
      })
      setShowCreateModal(false)
      setNewScan({ name: '', scan_type: 'full', targets: '' })
      fetchScans()
    } catch (error) {
      console.error('Failed to create scan:', error)
    } finally {
      setCreating(false)
    }
  }

  const handleCancelScan = async (id: string) => {
    try {
      await scansAPI.cancel(id)
      fetchScans()
    } catch (error) {
      console.error('Failed to cancel scan:', error)
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'running':
        return <Loader2 className="w-4 h-4 animate-spin" />
      case 'completed':
        return <CheckCircle className="w-4 h-4" />
      case 'failed':
        return <XCircle className="w-4 h-4" />
      default:
        return <Clock className="w-4 h-4" />
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Security Scans</h1>
          <p className="text-sentinel-gray-400 mt-1">
            Run and monitor security scans across your attack surface
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button onClick={fetchScans} className="btn-secondary flex items-center gap-2">
            <RefreshCw className="w-4 h-4" />
            Refresh
          </button>
          <button onClick={() => setShowCreateModal(true)} className="btn-primary flex items-center gap-2">
            <Plus className="w-4 h-4" />
            New Scan
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="card p-4">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-sentinel-gray-400" />
            <span className="text-sm text-sentinel-gray-400">Status:</span>
          </div>
          {['', 'running', 'completed', 'failed', 'pending'].map((status) => (
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

      {/* Scans List */}
      <div className="space-y-3">
        {loading ? (
          <div className="card p-12 text-center">
            <div className="spinner mx-auto mb-4" />
            <p className="text-sentinel-gray-400">Loading scans...</p>
          </div>
        ) : scans.length === 0 ? (
          <div className="card p-12 text-center">
            <Radar className="w-12 h-12 text-sentinel-gray-600 mx-auto mb-4" />
            <p className="text-sentinel-gray-400">No scans found</p>
          </div>
        ) : (
          scans.map((scan, index) => (
            <motion.div
              key={scan.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.03 }}
              className="card p-4"
            >
              <div className="flex items-center gap-4">
                <div className="w-10 h-10 rounded-lg bg-sentinel-gray-800 flex items-center justify-center border border-sentinel-gray-700">
                  <Radar className="w-5 h-5 text-sentinel-orange-500" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-3">
                    <h3 className="text-sm font-semibold text-white">{scan.name}</h3>
                    <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium border ${STATUS_COLORS[scan.status] || ''}`}>
                      {getStatusIcon(scan.status)}
                      {scan.status}
                    </span>
                    <span className="text-xs text-sentinel-gray-500 capitalize">{scan.scan_type}</span>
                  </div>
                  <p className="text-xs text-sentinel-gray-500 mt-1">
                    {scan.targets?.join(', ')} • {scan.findings_count} findings
                  </p>
                </div>
                <div className="text-right">
                  {scan.status === 'running' && (
                    <div className="mb-2">
                      <div className="w-32 h-1.5 bg-sentinel-gray-700 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-sentinel-orange-500 rounded-full transition-all"
                          style={{ width: `${scan.progress}%` }}
                        />
                      </div>
                      <p className="text-xs text-sentinel-gray-400 mt-1">{scan.progress}%</p>
                    </div>
                  )}
                  <p className="text-xs text-sentinel-gray-500">
                    {scan.created_at ? new Date(scan.created_at).toLocaleString() : '-'}
                  </p>
                </div>
                <div className="flex items-center gap-1">
                  {scan.status === 'running' && (
                    <button
                      onClick={() => handleCancelScan(scan.id)}
                      className="p-1.5 text-sentinel-gray-400 hover:text-red-400 transition-colors"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  )}
                </div>
              </div>
            </motion.div>
          ))
        )}
      </div>

      {/* Create Scan Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="card p-6 w-full max-w-md"
          >
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg font-semibold text-white">New Security Scan</h2>
              <button onClick={() => setShowCreateModal(false)} className="text-sentinel-gray-400 hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-sentinel-gray-300 mb-1">Scan Name</label>
                <input
                  type="text"
                  value={newScan.name}
                  onChange={(e) => setNewScan({ ...newScan, name: e.target.value })}
                  placeholder="e.g., Q2 External Scan"
                  className="input w-full"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-sentinel-gray-300 mb-1">Scan Type</label>
                <select
                  value={newScan.scan_type}
                  onChange={(e) => setNewScan({ ...newScan, scan_type: e.target.value })}
                  className="input w-full"
                >
                  {SCAN_TYPES.map((type) => (
                    <option key={type.value} value={type.value}>{type.label}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-sentinel-gray-300 mb-1">Targets (comma-separated)</label>
                <input
                  type="text"
                  value={newScan.targets}
                  onChange={(e) => setNewScan({ ...newScan, targets: e.target.value })}
                  placeholder="e.g., example.com, 192.168.1.0/24"
                  className="input w-full"
                />
              </div>
              <div className="flex justify-end gap-3 pt-2">
                <button onClick={() => setShowCreateModal(false)} className="btn-secondary">
                  Cancel
                </button>
                <button
                  onClick={handleCreateScan}
                  disabled={creating || !newScan.name || !newScan.targets}
                  className="btn-primary flex items-center gap-2 disabled:opacity-50"
                >
                  {creating ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
                  Start Scan
                </button>
              </div>
            </div>
          </motion.div>
        </div>
      )}
    </div>
  )
}
