import { useState, useEffect, useCallback } from 'react'
import { motion } from 'framer-motion'
import {
  FileText, Shield, AlertTriangle, Globe, Activity, BarChart3
} from 'lucide-react'
import { reportsAPI } from '../services/api'

interface RiskOverview {
  average_risk_score?: number
  open_alerts?: number
  risk_level?: string
}

interface AssetOverview {
  total?: number
  scans_performed?: number
}

interface VulnerabilityOverview {
  total?: number
  critical?: number
}

interface ComplianceOverview {
  status?: string
}

interface ExecutiveReport {
  period?: string
  executive_summary?: string
  risk_overview?: RiskOverview
  asset_overview?: AssetOverview
  vulnerability_overview?: VulnerabilityOverview
  recommendations?: string[]
  compliance_overview?: ComplianceOverview
}

export default function ReportsPage() {
  const [report, setReport] = useState<ExecutiveReport | null>(null)
  const [loading, setLoading] = useState(true)
  const [timeRange, setTimeRange] = useState(30)

  const fetchReport = useCallback(async () => {
    try {
      const response = await reportsAPI.getExecutive(timeRange)
      setReport(response.data)
    } catch (error) {
      console.error('Failed to fetch report:', error)
    } finally {
      setLoading(false)
    }
  }, [timeRange])

  useEffect(() => {
    fetchReport()
  }, [fetchReport])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <div className="spinner mx-auto mb-4" />
          <p className="text-sentinel-gray-400">Generating executive report...</p>
        </div>
      </div>
    )
  }

  const riskOverview = report?.risk_overview || {}
  const assetOverview = report?.asset_overview || {}
  const vulnOverview = report?.vulnerability_overview || {}
  const recommendations = report?.recommendations || []

  const riskScore = riskOverview.average_risk_score || 0
  const totalAssets = assetOverview.total || 0
  const totalVulns = vulnOverview.total || 0
  const openAlerts = riskOverview.open_alerts || 0

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Executive Report</h1>
          <p className="text-sentinel-gray-400 mt-1">
            {report?.period || 'Security posture overview for leadership'}
          </p>
        </div>
        <div className="flex items-center gap-3">
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
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { label: 'Risk Score', value: riskScore, suffix: '/100', icon: Activity, sub: riskOverview.risk_level || '' },
          { label: 'Assets Monitored', value: totalAssets, suffix: '', icon: Globe, sub: `${assetOverview.scans_performed || 0} scans` },
          { label: 'Vulnerabilities', value: totalVulns, suffix: '', icon: Shield, sub: `${vulnOverview.critical || 0} critical` },
          { label: 'Open Alerts', value: openAlerts, suffix: '', icon: AlertTriangle, sub: riskOverview.risk_level || '' },
        ].map((item, index) => (
          <motion.div
            key={item.label}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            className="stat-card"
          >
            <div className="flex items-center justify-between mb-2">
              <item.icon className="w-5 h-5 text-sentinel-orange-500" />
            </div>
            <p className="text-2xl font-bold text-white">
              {typeof item.value === 'number' ? item.value.toLocaleString() : item.value}{item.suffix}
            </p>
            <p className="text-xs text-sentinel-gray-400 mt-1">{item.label}</p>
            {item.sub && (
              <p className="text-xs text-sentinel-gray-500 mt-0.5">{item.sub}</p>
            )}
          </motion.div>
        ))}
      </div>

      {/* Executive Summary */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
        className="card p-6"
      >
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <FileText className="w-5 h-5 text-sentinel-orange-500" />
          Executive Summary
        </h3>
        <p className="text-sm text-sentinel-gray-300 whitespace-pre-line leading-relaxed">
          {report?.executive_summary || 'No summary available'}
        </p>
      </motion.div>

      {/* Recommendations */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5 }}
        className="card p-6"
      >
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <BarChart3 className="w-5 h-5 text-sentinel-orange-500" />
          Key Recommendations
        </h3>
        <div className="space-y-3">
          {recommendations.length === 0 ? (
            <p className="text-sm text-sentinel-gray-400">No recommendations at this time</p>
          ) : (
            recommendations.map((rec: string, index: number) => (
              <div key={index} className="flex items-start gap-3 p-3 rounded-lg bg-sentinel-gray-800/50 border border-sentinel-gray-700">
                <div className="w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold bg-sentinel-orange-500/20 text-sentinel-orange-500 shrink-0">
                  {index + 1}
                </div>
                <p className="text-sm text-sentinel-gray-300">{rec}</p>
              </div>
            ))
          )}
        </div>
      </motion.div>

      {/* Compliance */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.6 }}
        className="card p-6"
      >
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <Shield className="w-5 h-5 text-sentinel-orange-500" />
          Compliance Status
        </h3>
        <div className="flex items-center gap-3">
          <div className={`w-3 h-3 rounded-full ${
            report?.compliance_overview?.status === 'compliant' ? 'bg-emerald-400' :
            report?.compliance_overview?.status === 'needs_review' ? 'bg-yellow-400' :
            'bg-red-400'
          }`} />
          <span className="text-sm text-white capitalize">
            {report?.compliance_overview?.status?.replace('_', ' ') || 'Unknown'}
          </span>
        </div>
      </motion.div>
    </div>
  )
}
