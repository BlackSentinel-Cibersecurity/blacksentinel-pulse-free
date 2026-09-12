import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  ArrowLeft, Globe, Shield, Activity, AlertTriangle, ExternalLink,
  Copy, RefreshCw, Calendar, MapPin, Server, Lock, Wifi, Database
} from 'lucide-react'
import { assetsAPI } from '../services/api'

export default function AssetDetailPage() {
  const { id } = useParams()
  const [asset, setAsset] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('overview')

  useEffect(() => {
    fetchAsset()
  }, [id])

  const fetchAsset = async () => {
    try {
      const response = await assetsAPI.get(Number(id))
      setAsset(response.data)
    } catch (error) {
      console.error('Failed to fetch asset:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="spinner" />
      </div>
    )
  }

  if (!asset) {
    return (
      <div className="text-center py-12">
        <p className="text-sentinel-gray-400">Asset not found</p>
      </div>
    )
  }

  const tabs = [
    { id: 'overview', name: 'Overview' },
    { id: 'vulnerabilities', name: 'Vulnerabilities' },
    { id: 'relationships', name: 'Relationships' },
    { id: 'history', name: 'History' },
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link
          to="/assets"
          className="p-2 rounded-lg bg-sentinel-gray-800 text-sentinel-gray-400 hover:text-white transition-colors"
        >
          <ArrowLeft className="w-5 h-5" />
        </Link>
        <div className="flex-1">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-xl bg-sentinel-orange-500/10 border border-sentinel-orange-500/20 flex items-center justify-center">
              <Globe className="w-6 h-6 text-sentinel-orange-500" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white">{asset.name}</h1>
              <p className="text-sentinel-gray-400">
                {asset.asset_type?.replace('_', ' ')} • {asset.ip_address || asset.hostname || 'No IP'}
              </p>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <button className="btn-secondary flex items-center gap-2">
            <RefreshCw className="w-4 h-4" />
            Rescan
          </button>
          <button className="btn-primary flex items-center gap-2">
            <Shield className="w-4 h-4" />
            Quick Scan
          </button>
        </div>
      </div>

      {/* Risk Score Card */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="card p-6"
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-6">
            <div className="text-center">
              <div className="relative w-24 h-24">
                <svg className="w-24 h-24 transform -rotate-90">
                  <circle
                    cx="48"
                    cy="48"
                    r="40"
                    stroke="#2D2D2D"
                    strokeWidth="8"
                    fill="none"
                  />
                  <circle
                    cx="48"
                    cy="48"
                    r="40"
                    stroke={asset.risk_score >= 80 ? '#FF3B3B' : asset.risk_score >= 60 ? '#FF6B2C' : asset.risk_score >= 40 ? '#FFB020' : '#34D399'}
                    strokeWidth="8"
                    fill="none"
                    strokeDasharray={`${(asset.risk_score / 100) * 251.2} 251.2`}
                    strokeLinecap="round"
                  />
                </svg>
                <div className="absolute inset-0 flex items-center justify-center">
                  <span className="text-2xl font-bold text-white">{Math.round(asset.risk_score)}</span>
                </div>
              </div>
              <p className="text-xs text-sentinel-gray-400 mt-2">Risk Score</p>
            </div>
            <div className="grid grid-cols-3 gap-6">
              <div>
                <p className="text-sm text-sentinel-gray-400">Status</p>
                <p className="text-lg font-semibold text-white capitalize">{asset.status}</p>
              </div>
              <div>
                <p className="text-sm text-sentinel-gray-400">Criticality</p>
                <p className="text-lg font-semibold text-white capitalize">{asset.criticality}</p>
              </div>
              <div>
                <p className="text-sm text-sentinel-gray-400">Discovery</p>
                <p className="text-lg font-semibold text-white">{asset.discovery_method || 'N/A'}</p>
              </div>
            </div>
          </div>
        </div>
      </motion.div>

      {/* Tabs */}
      <div className="border-b border-sentinel-gray-800">
        <nav className="flex gap-1">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
                activeTab === tab.id
                  ? 'text-sentinel-orange-500 border-sentinel-orange-500'
                  : 'text-sentinel-gray-400 border-transparent hover:text-white hover:border-sentinel-gray-600'
              }`}
            >
              {tab.name}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-6">
          {activeTab === 'overview' && (
            <>
              {/* Asset Details */}
              <div className="card p-6">
                <h3 className="text-lg font-semibold text-white mb-4">Asset Details</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div className="p-3 bg-sentinel-gray-800/50 rounded-lg">
                    <p className="text-xs text-sentinel-gray-400">Name</p>
                    <p className="text-sm text-white mt-1">{asset.name}</p>
                  </div>
                  <div className="p-3 bg-sentinel-gray-800/50 rounded-lg">
                    <p className="text-xs text-sentinel-gray-400">Type</p>
                    <p className="text-sm text-white mt-1 capitalize">{asset.asset_type?.replace('_', ' ')}</p>
                  </div>
                  <div className="p-3 bg-sentinel-gray-800/50 rounded-lg">
                    <p className="text-xs text-sentinel-gray-400">IP Address</p>
                    <p className="text-sm text-white mt-1 font-mono">{asset.ip_address || 'N/A'}</p>
                  </div>
                  <div className="p-3 bg-sentinel-gray-800/50 rounded-lg">
                    <p className="text-xs text-sentinel-gray-400">Hostname</p>
                    <p className="text-sm text-white mt-1 font-mono">{asset.hostname || 'N/A'}</p>
                  </div>
                  <div className="p-3 bg-sentinel-gray-800/50 rounded-lg">
                    <p className="text-xs text-sentinel-gray-400">First Seen</p>
                    <p className="text-sm text-white mt-1">
                      {asset.created_at ? new Date(asset.created_at).toLocaleDateString() : 'N/A'}
                    </p>
                  </div>
                  <div className="p-3 bg-sentinel-gray-800/50 rounded-lg">
                    <p className="text-xs text-sentinel-gray-400">Last Seen</p>
                    <p className="text-sm text-white mt-1">
                      {asset.last_seen ? new Date(asset.last_seen).toLocaleDateString() : 'N/A'}
                    </p>
                  </div>
                </div>
              </div>

              {/* Tags */}
              <div className="card p-6">
                <h3 className="text-lg font-semibold text-white mb-4">Tags</h3>
                <div className="flex flex-wrap gap-2">
                  {(asset.tags || []).map((tag: string) => (
                    <span
                      key={tag}
                      className="px-3 py-1 bg-sentinel-gray-800 border border-sentinel-gray-700 rounded-full text-sm text-sentinel-gray-300"
                    >
                      {tag}
                    </span>
                  ))}
                  {(!asset.tags || asset.tags.length === 0) && (
                    <p className="text-sm text-sentinel-gray-500">No tags assigned</p>
                  )}
                </div>
              </div>
            </>
          )}

          {activeTab === 'vulnerabilities' && (
            <div className="card p-6">
              <h3 className="text-lg font-semibold text-white mb-4">Associated Vulnerabilities</h3>
              <p className="text-sentinel-gray-400">
                Vulnerability data will be displayed here after scanning.
              </p>
            </div>
          )}

          {activeTab === 'relationships' && (
            <div className="card p-6">
              <h3 className="text-lg font-semibold text-white mb-4">Asset Relationships</h3>
              <p className="text-sentinel-gray-400">
                Relationship graph will be displayed here showing connected assets.
              </p>
            </div>
          )}

          {activeTab === 'history' && (
            <div className="card p-6">
              <h3 className="text-lg font-semibold text-white mb-4">Change History</h3>
              <p className="text-sentinel-gray-400">
                Historical changes and audit trail will be displayed here.
              </p>
            </div>
          )}

        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Quick Actions */}
          <div className="card p-6">
            <h3 className="text-lg font-semibold text-white mb-4">Quick Actions</h3>
            <div className="space-y-2">
              <button className="w-full btn-secondary text-left flex items-center gap-3">
                <Shield className="w-4 h-4" />
                Run Vulnerability Scan
              </button>
              <button className="w-full btn-secondary text-left flex items-center gap-3">
                <Activity className="w-4 h-4" />
                Check Threat Intel
              </button>
              <button className="w-full btn-secondary text-left flex items-center gap-3">
                <AlertTriangle className="w-4 h-4" />
                View Attack Paths
              </button>
            </div>
          </div>

          {/* Metadata */}
          <div className="card p-6">
            <h3 className="text-lg font-semibold text-white mb-4">Metadata</h3>
            <div className="space-y-3">
              {Object.entries(asset.metadata || {}).map(([key, value]) => (
                <div key={key} className="flex items-center justify-between">
                  <span className="text-sm text-sentinel-gray-400 capitalize">
                    {key.replace(/_/g, ' ')}
                  </span>
                  <span className="text-sm text-white font-mono">
                    {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
