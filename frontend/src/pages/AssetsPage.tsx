import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  Globe, Search, Filter, Download, RefreshCw, Plus,
  ChevronDown, ExternalLink, Shield, Activity
} from 'lucide-react'
import { assetsAPI } from '../services/api'

const ASSET_TYPE_ICONS: Record<string, any> = {
  domain: Globe,
  subdomain: Globe,
  ip_address: Activity,
  web_application: Globe,
  cloud_resource: Globe,
  database: Globe,
  repository: Globe,
}

export default function AssetsPage() {
  const [assets, setAssets] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [typeFilter, setTypeFilter] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [sortBy, setSortBy] = useState('risk_score')
  const [sortOrder, setSortOrder] = useState('desc')
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)

  useEffect(() => {
    fetchAssets()
  }, [search, typeFilter, statusFilter, sortBy, sortOrder, page])

  const fetchAssets = async () => {
    try {
      const response = await assetsAPI.list({
        search,
        asset_type: typeFilter || undefined,
        status: statusFilter || undefined,
        sort_by: sortBy,
        sort_order: sortOrder,
        page,
        page_size: 20,
      })
      setAssets(response.data.items || [])
      setTotal(response.data.total || 0)
    } catch (error) {
      console.error('Failed to fetch assets:', error)
    } finally {
      setLoading(false)
    }
  }

  const getRiskColor = (score: number) => {
    if (score >= 80) return 'text-red-400'
    if (score >= 60) return 'text-sentinel-orange-500'
    if (score >= 40) return 'text-yellow-400'
    return 'text-emerald-400'
  }

  const getRiskBg = (score: number) => {
    if (score >= 80) return 'bg-red-500'
    if (score >= 60) return 'bg-sentinel-orange-500'
    if (score >= 40) return 'bg-yellow-500'
    return 'bg-emerald-500'
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Attack Surface Assets</h1>
          <p className="text-sentinel-gray-400 mt-1">
            {total.toLocaleString()} assets discovered and monitored
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button className="btn-secondary flex items-center gap-2">
            <Download className="w-4 h-4" />
            Export
          </button>
          <button className="btn-primary flex items-center gap-2">
            <Plus className="w-4 h-4" />
            Add Asset
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="card p-4">
        <div className="flex items-center gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-sentinel-gray-500" />
            <input
              type="text"
              placeholder="Search assets by name, IP, or hostname..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="input pl-10"
            />
          </div>
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="input w-40"
          >
            <option value="">All Types</option>
            <option value="domain">Domain</option>
            <option value="subdomain">Subdomain</option>
            <option value="ip_address">IP Address</option>
            <option value="web_application">Web App</option>
            <option value="cloud_resource">Cloud</option>
            <option value="database">Database</option>
            <option value="repository">Repository</option>
          </select>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="input w-40"
          >
            <option value="">All Status</option>
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
            <option value="monitoring">Monitoring</option>
            <option value="compromised">Compromised</option>
          </select>
          <button
            onClick={() => setSortOrder(sortOrder === 'desc' ? 'asc' : 'desc')}
            className="btn-ghost flex items-center gap-2"
          >
            <Filter className="w-4 h-4" />
            Risk {sortOrder === 'desc' ? '↓' : '↑'}
          </button>
        </div>
      </div>

      {/* Asset List */}
      <div className="card overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="border-b border-sentinel-gray-800 bg-sentinel-gray-900/50">
              <th className="text-left py-3 px-4 text-xs font-medium text-sentinel-gray-400 uppercase">Asset</th>
              <th className="text-left py-3 px-4 text-xs font-medium text-sentinel-gray-400 uppercase">Type</th>
              <th className="text-left py-3 px-4 text-xs font-medium text-sentinel-gray-400 uppercase">Status</th>
              <th className="text-left py-3 px-4 text-xs font-medium text-sentinel-gray-400 uppercase">Risk Score</th>
              <th className="text-left py-3 px-4 text-xs font-medium text-sentinel-gray-400 uppercase">Last Seen</th>
              <th className="text-left py-3 px-4 text-xs font-medium text-sentinel-gray-400 uppercase">Actions</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={6} className="py-12 text-center">
                  <div className="spinner mx-auto mb-4" />
                  <p className="text-sentinel-gray-400">Loading assets...</p>
                </td>
              </tr>
            ) : assets.length === 0 ? (
              <tr>
                <td colSpan={6} className="py-12 text-center">
                  <Globe className="w-12 h-12 text-sentinel-gray-600 mx-auto mb-4" />
                  <p className="text-sentinel-gray-400">No assets found</p>
                </td>
              </tr>
            ) : (
              assets.map((asset, index) => (
                <motion.tr
                  key={asset.id}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.02 }}
                  className="table-row"
                >
                  <td className="py-3 px-4">
                    <Link
                      to={`/assets/${asset.id}`}
                      className="flex items-center gap-3 group"
                    >
                      <div className="w-10 h-10 rounded-lg bg-sentinel-gray-800 flex items-center justify-center border border-sentinel-gray-700 group-hover:border-sentinel-orange-500/30 transition-colors">
                        <Globe className="w-5 h-5 text-sentinel-gray-400 group-hover:text-sentinel-orange-500 transition-colors" />
                      </div>
                      <div>
                        <p className="text-sm font-medium text-white group-hover:text-sentinel-orange-500 transition-colors">
                          {asset.name}
                        </p>
                        <p className="text-xs text-sentinel-gray-500">
                          {asset.ip_address || asset.hostname || '-'}
                        </p>
                      </div>
                    </Link>
                  </td>
                  <td className="py-3 px-4">
                    <span className="text-sm text-sentinel-gray-300 capitalize">
                      {asset.asset_type?.replace('_', ' ')}
                    </span>
                  </td>
                  <td className="py-3 px-4">
                    <span className={`badge ${
                      asset.status === 'active' ? 'badge-low' :
                      asset.status === 'compromised' ? 'badge-critical' :
                      'badge-info'
                    }`}>
                      {asset.status}
                    </span>
                  </td>
                  <td className="py-3 px-4">
                    <div className="flex items-center gap-2">
                      <div className="w-20 h-1.5 bg-sentinel-gray-700 rounded-full overflow-hidden">
                        <div
                          className={`h-full rounded-full ${getRiskBg(asset.risk_score)}`}
                          style={{ width: `${asset.risk_score}%` }}
                        />
                      </div>
                      <span className={`text-sm font-mono font-medium ${getRiskColor(asset.risk_score)}`}>
                        {Math.round(asset.risk_score)}
                      </span>
                    </div>
                  </td>
                  <td className="py-3 px-4">
                    <span className="text-sm text-sentinel-gray-400">
                      {asset.last_seen ? new Date(asset.last_seen).toLocaleDateString() : '-'}
                    </span>
                  </td>
                  <td className="py-3 px-4">
                    <div className="flex items-center gap-2">
                      <Link
                        to={`/assets/${asset.id}`}
                        className="p-1.5 text-sentinel-gray-400 hover:text-sentinel-orange-500 transition-colors"
                      >
                        <ExternalLink className="w-4 h-4" />
                      </Link>
                    </div>
                  </td>
                </motion.tr>
              ))
            )}
          </tbody>
        </table>

        {/* Pagination */}
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
