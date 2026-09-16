import { useState, useEffect, useCallback } from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  Globe, Shield, AlertTriangle, Activity,
  ArrowUpRight, ArrowDownRight, Zap
} from 'lucide-react'
import {
  AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer
} from 'recharts'
import { dashboardAPI } from '../services/api'

const COLORS = {
  critical: '#FF3B3B',
  high: '#FF6B2C',
  medium: '#FFB020',
  low: '#34D399',
  info: '#60A5FA',
}

interface DashboardOverview {
  total_assets?: number
  assets_discovered_today?: number
  total_vulnerabilities?: number
  vulnerabilities_resolved_today?: number
  open_alerts?: number
  critical_assets?: number
  risk_score_avg?: number
}

interface RiskDistribution {
  critical?: number
  high?: number
  medium?: number
  low?: number
  info?: number
}

interface TimelinePoint {
  timestamp: string
  assets?: number
  vulnerabilities?: number
}

interface TopRiskyAsset {
  id: number
  name: string
  type?: string
  risk_score: number
  vulnerability_count?: number
}

interface DiscoveryTrendPoint {
  date: string
  new_assets?: number
}

interface RecentAlert {
  id: string
  title: string
  severity: string
  status: string
  created_at?: string
}

interface DashboardData {
  overview?: DashboardOverview
  risk_distribution?: RiskDistribution
  timeline?: TimelinePoint[]
  top_risky_assets?: TopRiskyAsset[]
  discovery_trends?: DiscoveryTrendPoint[]
  recent_alerts?: RecentAlert[]
}

export default function DashboardPage() {
  const [data, setData] = useState<DashboardData | null>(null)
  const [loading, setLoading] = useState(true)
  const [timeRange, setTimeRange] = useState(30)

  const fetchData = useCallback(async () => {
    try {
      const response = await dashboardAPI.getData(timeRange)
      setData(response.data)
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error)
    } finally {
      setLoading(false)
    }
  }, [timeRange])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <div className="spinner mx-auto mb-4" />
          <p className="text-sentinel-gray-400">Loading dashboard...</p>
        </div>
      </div>
    )
  }

  const overview = data?.overview || {}
  const riskDist = data?.risk_distribution || {}
  const timeline = data?.timeline || []
  const topRisky = data?.top_risky_assets || []
  const discoveryTrends = data?.discovery_trends || []

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Mission Control</h1>
          <p className="text-sentinel-gray-400 mt-1">
            Real-time attack surface intelligence
          </p>
        </div>
        <div className="flex items-center gap-2">
          {[7, 30, 90].map((days) => (
            <button
              key={days}
              onClick={() => setTimeRange(days)}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                timeRange === days
                  ? 'bg-sentinel-orange-500/20 text-sentinel-orange-500 border border-sentinel-orange-500/30'
                  : 'bg-sentinel-gray-800 text-sentinel-gray-400 hover:text-white border border-sentinel-gray-700'
              }`}
            >
              {days}D
            </button>
          ))}
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0 }}
          className="stat-card"
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sentinel-gray-400 text-sm">Total Assets</p>
              <p className="text-3xl font-bold text-white mt-1">
                {overview.total_assets?.toLocaleString() || 0}
              </p>
              <div className="flex items-center gap-1 mt-2">
                <ArrowUpRight className="w-3 h-3 text-emerald-400" />
                <span className="text-xs text-emerald-400">
                  +{overview.assets_discovered_today || 0} today
                </span>
              </div>
            </div>
            <div className="w-12 h-12 rounded-xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center">
              <Globe className="w-6 h-6 text-blue-400" />
            </div>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="stat-card"
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sentinel-gray-400 text-sm">Vulnerabilities</p>
              <p className="text-3xl font-bold text-white mt-1">
                {overview.total_vulnerabilities?.toLocaleString() || 0}
              </p>
              <div className="flex items-center gap-1 mt-2">
                <ArrowDownRight className="w-3 h-3 text-emerald-400" />
                <span className="text-xs text-emerald-400">
                  -{overview.vulnerabilities_resolved_today || 0} resolved
                </span>
              </div>
            </div>
            <div className="w-12 h-12 rounded-xl bg-sentinel-orange-500/10 border border-sentinel-orange-500/20 flex items-center justify-center">
              <Shield className="w-6 h-6 text-sentinel-orange-500" />
            </div>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="stat-card"
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sentinel-gray-400 text-sm">Open Alerts</p>
              <p className="text-3xl font-bold text-white mt-1">
                {overview.open_alerts || 0}
              </p>
              <div className="flex items-center gap-1 mt-2">
                <AlertTriangle className="w-3 h-3 text-sentinel-orange-500" />
                <span className="text-xs text-sentinel-orange-500">
                  {overview.critical_assets || 0} critical
                </span>
              </div>
            </div>
            <div className="w-12 h-12 rounded-xl bg-red-500/10 border border-red-500/20 flex items-center justify-center">
              <AlertTriangle className="w-6 h-6 text-red-400" />
            </div>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="stat-card"
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sentinel-gray-400 text-sm">Risk Score</p>
              <p className="text-3xl font-bold text-white mt-1">
                {overview.risk_score_avg || 0}
              </p>
              <div className="flex items-center gap-1 mt-2">
                <Activity className="w-3 h-3 text-sentinel-orange-500" />
                <span className="text-xs text-sentinel-gray-400">
                  /100 average
                </span>
              </div>
            </div>
            <div className="w-12 h-12 rounded-xl bg-sentinel-orange-500/10 border border-sentinel-orange-500/20 flex items-center justify-center">
              <Zap className="w-6 h-6 text-sentinel-orange-500" />
            </div>
          </div>
        </motion.div>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Timeline Chart */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="lg:col-span-2 card p-6"
        >
          <h3 className="text-lg font-semibold text-white mb-4">Activity Timeline</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={timeline}>
                <defs>
                  <linearGradient id="colorAssets" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#FF6B2C" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#FF6B2C" stopOpacity={0}/>
                  </linearGradient>
                  <linearGradient id="colorVulns" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#FF3B3B" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#FF3B3B" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#2D2D2D" />
                <XAxis
                  dataKey="timestamp"
                  stroke="#555555"
                  tick={{ fill: '#777777', fontSize: 12 }}
                  tickFormatter={(value) => new Date(value).toLocaleDateString('en', { month: 'short', day: 'numeric' })}
                />
                <YAxis stroke="#555555" tick={{ fill: '#777777', fontSize: 12 }} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1A1A1A',
                    border: '1px solid #3D3D3D',
                    borderRadius: '8px',
                    color: '#F5F5F5',
                  }}
                />
                <Area
                  type="monotone"
                  dataKey="assets"
                  stroke="#FF6B2C"
                  fillOpacity={1}
                  fill="url(#colorAssets)"
                  name="Assets"
                />
                <Area
                  type="monotone"
                  dataKey="vulnerabilities"
                  stroke="#FF3B3B"
                  fillOpacity={1}
                  fill="url(#colorVulns)"
                  name="Vulnerabilities"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </motion.div>

        {/* Risk Distribution */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="card p-6"
        >
          <h3 className="text-lg font-semibold text-white mb-4">Risk Distribution</h3>
          <div className="h-48">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={[
                    { name: 'Critical', value: riskDist.critical || 0 },
                    { name: 'High', value: riskDist.high || 0 },
                    { name: 'Medium', value: riskDist.medium || 0 },
                    { name: 'Low', value: riskDist.low || 0 },
                    { name: 'Info', value: riskDist.info || 0 },
                  ]}
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={80}
                  paddingAngle={2}
                  dataKey="value"
                >
                  {['#FF3B3B', '#FF6B2C', '#FFB020', '#34D399', '#60A5FA'].map((color, index) => (
                    <Cell key={`cell-${index}`} fill={color} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1A1A1A',
                    border: '1px solid #3D3D3D',
                    borderRadius: '8px',
                    color: '#F5F5F5',
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="grid grid-cols-2 gap-2 mt-4">
            {[
              { label: 'Critical', value: riskDist.critical, color: COLORS.critical },
              { label: 'High', value: riskDist.high, color: COLORS.high },
              { label: 'Medium', value: riskDist.medium, color: COLORS.medium },
              { label: 'Low', value: riskDist.low, color: COLORS.low },
            ].map((item) => (
              <div key={item.label} className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full" style={{ backgroundColor: item.color }} />
                <span className="text-xs text-sentinel-gray-400">{item.label}</span>
                <span className="text-xs font-medium text-white ml-auto">{item.value}</span>
              </div>
            ))}
          </div>
        </motion.div>
      </div>

      {/* Bottom Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Top Risky Assets */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
          className="card p-6"
        >
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-white">Highest Risk Assets</h3>
            <Link to="/assets" className="text-sm text-sentinel-orange-500 hover:text-sentinel-orange-400">
              View all
            </Link>
          </div>
          <div className="space-y-3">
            {topRisky.slice(0, 5).map((asset: TopRiskyAsset, index: number) => (
              <Link
                key={asset.id}
                to={`/assets/${asset.id}`}
                className="flex items-center gap-4 p-3 rounded-lg hover:bg-sentinel-gray-800/50 transition-colors group"
              >
                <div className="w-8 h-8 rounded-lg bg-sentinel-gray-800 flex items-center justify-center text-sm font-bold text-sentinel-gray-400">
                  {index + 1}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-white truncate group-hover:text-sentinel-orange-500 transition-colors">
                    {asset.name}
                  </p>
                  <p className="text-xs text-sentinel-gray-500">{asset.type}</p>
                </div>
                <div className="text-right">
                  <div className="flex items-center gap-1">
                    <div className="w-16 h-1.5 bg-sentinel-gray-700 rounded-full overflow-hidden">
                      <div
                        className="h-full rounded-full"
                        style={{
                          width: `${asset.risk_score}%`,
                          backgroundColor: asset.risk_score >= 80 ? COLORS.critical : asset.risk_score >= 60 ? COLORS.high : COLORS.medium,
                        }}
                      />
                    </div>
                    <span className="text-sm font-mono text-white">{Math.round(asset.risk_score)}</span>
                  </div>
                  <p className="text-xs text-sentinel-gray-500 mt-1">
                    {asset.vulnerability_count} vulns
                  </p>
                </div>
              </Link>
            ))}
          </div>
        </motion.div>

        {/* Discovery Trends */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.7 }}
          className="card p-6"
        >
          <h3 className="text-lg font-semibold text-white mb-4">Discovery Trends</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={discoveryTrends.slice(-14)}>
                <CartesianGrid strokeDasharray="3 3" stroke="#2D2D2D" />
                <XAxis
                  dataKey="date"
                  stroke="#555555"
                  tick={{ fill: '#777777', fontSize: 10 }}
                  tickFormatter={(value) => new Date(value).toLocaleDateString('en', { month: 'short', day: 'numeric' })}
                />
                <YAxis stroke="#555555" tick={{ fill: '#777777', fontSize: 12 }} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1A1A1A',
                    border: '1px solid #3D3D3D',
                    borderRadius: '8px',
                    color: '#F5F5F5',
                  }}
                />
                <Bar
                  dataKey="new_assets"
                  fill="#FF6B2C"
                  radius={[4, 4, 0, 0]}
                  name="New Assets"
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </motion.div>
      </div>

      {/* Recent Alerts */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.8 }}
        className="card p-6"
      >
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-white">Recent Alerts</h3>
          <Link to="/alerts" className="text-sm text-sentinel-orange-500 hover:text-sentinel-orange-400">
            View all
          </Link>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-sentinel-gray-800">
                <th className="text-left py-3 px-4 text-xs font-medium text-sentinel-gray-400 uppercase">Alert</th>
                <th className="text-left py-3 px-4 text-xs font-medium text-sentinel-gray-400 uppercase">Severity</th>
                <th className="text-left py-3 px-4 text-xs font-medium text-sentinel-gray-400 uppercase">Status</th>
                <th className="text-left py-3 px-4 text-xs font-medium text-sentinel-gray-400 uppercase">Time</th>
              </tr>
            </thead>
            <tbody>
              {(data?.recent_alerts || []).slice(0, 5).map((alert: RecentAlert) => (
                <tr key={alert.id} className="table-row">
                  <td className="py-3 px-4">
                    <span className="text-sm text-white">{alert.title}</span>
                  </td>
                  <td className="py-3 px-4">
                    <span className={`badge badge-${alert.severity}`}>
                      {alert.severity}
                    </span>
                  </td>
                  <td className="py-3 px-4">
                    <span className="text-sm text-sentinel-gray-400">{alert.status}</span>
                  </td>
                  <td className="py-3 px-4">
                    <span className="text-sm text-sentinel-gray-500">
                      {alert.created_at ? new Date(alert.created_at).toLocaleString() : '-'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </motion.div>
    </div>
  )
}
