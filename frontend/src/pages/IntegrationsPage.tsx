import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import {
  CheckCircle, XCircle, Loader2, RefreshCw,
  Settings, Zap, Link2, Cloud, Shield, Database
} from 'lucide-react'
import { AxiosError } from 'axios'
import { integrationsAPI } from '../services/api'

interface Integration {
  id: string
  name: string
  provider: string
  type: string
  status: string
  last_sync?: string
  description: string
}

interface ConfigField {
  name: string
  label: string
  type: 'text' | 'password' | 'select' | 'textarea'
  placeholder?: string
  required?: boolean
  options?: { value: string; label: string }[]
}

const INTEGRATION_CONFIGS: Record<string, ConfigField[]> = {
  aws: [
    { name: 'access_key_id', label: 'Access Key ID', type: 'text', placeholder: 'AKIA...', required: true },
    { name: 'secret_access_key', label: 'Secret Access Key', type: 'password', placeholder: 'Enter secret key', required: true },
    { name: 'region', label: 'Default Region', type: 'select', required: true, options: [
      { value: 'us-east-1', label: 'US East (N. Virginia)' },
      { value: 'us-west-2', label: 'US West (Oregon)' },
      { value: 'eu-west-1', label: 'EU (Ireland)' },
      { value: 'eu-central-1', label: 'EU (Frankfurt)' },
      { value: 'ap-southeast-1', label: 'Asia Pacific (Singapore)' },
      { value: 'ap-northeast-1', label: 'Asia Pacific (Tokyo)' },
    ]},
    { name: 'scan_services', label: 'Services to Scan', type: 'textarea', placeholder: 'ec2, s3, rds, iam, lambda...', required: false },
  ],
  gcp: [
    { name: 'project_id', label: 'Project ID', type: 'text', placeholder: 'my-gcp-project', required: true },
    { name: 'service_account_key', label: 'Service Account Key (JSON)', type: 'textarea', placeholder: 'Paste JSON key...', required: true },
    { name: 'region', label: 'Default Region', type: 'select', required: true, options: [
      { value: 'us-central1', label: 'US Central (Iowa)' },
      { value: 'us-east1', label: 'US East (South Carolina)' },
      { value: 'europe-west1', label: 'Europe West (Belgium)' },
      { value: 'asia-east1', label: 'Asia East (Taiwan)' },
    ]},
  ],
  azure: [
    { name: 'subscription_id', label: 'Subscription ID', type: 'text', placeholder: 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx', required: true },
    { name: 'tenant_id', label: 'Tenant ID', type: 'text', placeholder: 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx', required: true },
    { name: 'client_id', label: 'Application (Client) ID', type: 'text', placeholder: 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx', required: true },
    { name: 'client_secret', label: 'Client Secret', type: 'password', placeholder: 'Enter client secret', required: true },
  ],
  firewall_paloalto: [
    { name: 'management_ip', label: 'Management IP', type: 'text', placeholder: '192.168.1.1', required: true },
    { name: 'username', label: 'Admin Username', type: 'text', placeholder: 'admin', required: true },
    { name: 'password', label: 'Admin Password', type: 'password', placeholder: 'Enter password', required: true },
    { name: 'api_version', label: 'PAN-OS API Version', type: 'select', required: false, options: [
      { value: '10.2', label: 'PAN-OS 10.2' },
      { value: '11.0', label: 'PAN-OS 11.0' },
      { value: '11.1', label: 'PAN-OS 11.1' },
    ]},
  ],
  firewall_fortinet: [
    { name: 'management_ip', label: 'FortiGate IP', type: 'text', placeholder: '192.168.1.1', required: true },
    { name: 'api_key', label: 'API Key', type: 'password', placeholder: 'Enter API key', required: true },
    { name: 'vdom', label: 'VDOM', type: 'text', placeholder: 'root', required: false },
  ],
  firewall_cisco: [
    { name: 'management_ip', label: 'Firepower IP', type: 'text', placeholder: '192.168.1.1', required: true },
    { name: 'username', label: 'Username', type: 'text', placeholder: 'admin', required: true },
    { name: 'password', label: 'Password', type: 'password', placeholder: 'Enter password', required: true },
    { name: 'domain', label: 'Domain', type: 'text', placeholder: 'Global', required: false },
  ],
  firewall_checkpoint: [
    { name: 'management_server', label: 'Management Server', type: 'text', placeholder: '192.168.1.1', required: true },
    { name: 'api_key', label: 'API Key', type: 'password', placeholder: 'Enter API key', required: true },
    { name: 'domain', label: 'Domain', type: 'text', placeholder: 'MyDomain', required: false },
  ],
  siem_splunk: [
    { name: 'host', label: 'Splunk Host', type: 'text', placeholder: 'https://splunk.company.com', required: true },
    { name: 'port', label: 'Port', type: 'text', placeholder: '8089', required: true },
    { name: 'token', label: 'HEC Token', type: 'password', placeholder: 'Enter HEC token', required: true },
  ],
  siem_elastic: [
    { name: 'host', label: 'Elasticsearch Host', type: 'text', placeholder: 'https://elastic.company.com', required: true },
    { name: 'api_key', label: 'API Key', type: 'password', placeholder: 'Enter API key', required: true },
    { name: 'index', label: 'Index Pattern', type: 'text', placeholder: 'security-*', required: false },
  ],
}

const PROVIDER_CATEGORIES = [
  {
    name: 'Cloud Providers',
    items: [
      { id: 'aws', name: 'Amazon Web Services', icon: Cloud, color: 'text-orange-400 bg-orange-500/10 border-orange-500/20' },
      { id: 'gcp', name: 'Google Cloud Platform', icon: Cloud, color: 'text-blue-400 bg-blue-500/10 border-blue-500/20' },
      { id: 'azure', name: 'Microsoft Azure', icon: Cloud, color: 'text-sky-400 bg-sky-500/10 border-sky-500/20' },
    ],
  },
  {
    name: 'Firewalls',
    items: [
      { id: 'firewall_paloalto', name: 'Palo Alto Networks', icon: Shield, color: 'text-red-400 bg-red-500/10 border-red-500/20' },
      { id: 'firewall_fortinet', name: 'Fortinet FortiGate', icon: Shield, color: 'text-purple-400 bg-purple-500/10 border-purple-500/20' },
      { id: 'firewall_cisco', name: 'Cisco Firepower', icon: Shield, color: 'text-cyan-400 bg-cyan-500/10 border-cyan-500/20' },
      { id: 'firewall_checkpoint', name: 'Check Point', icon: Shield, color: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20' },
    ],
  },
  {
    name: 'SIEM & Analytics',
    items: [
      { id: 'siem_splunk', name: 'Splunk', icon: Database, color: 'text-green-400 bg-green-500/10 border-green-500/20' },
      { id: 'siem_elastic', name: 'Elastic SIEM', icon: Database, color: 'text-yellow-400 bg-yellow-500/10 border-yellow-500/20' },
    ],
  },
]

export default function IntegrationsPage() {
  const [integrations, setIntegrations] = useState<Integration[]>([])
  const [loading, setLoading] = useState(true)
  const [testing, setTesting] = useState<string | null>(null)
  const [syncing, setSyncing] = useState<string | null>(null)
  const [configuring, setConfiguring] = useState<string | null>(null)
  const [configData, setConfigData] = useState<Record<string, string>>({})
  const [configError, setConfigError] = useState('')

  useEffect(() => {
    fetchIntegrations()
  }, [])

  const fetchIntegrations = async () => {
    try {
      const response = await integrationsAPI.list()
      const data = response.data
      setIntegrations(data.available || data.items || (Array.isArray(data) ? data : []))
    } catch (error) {
      console.error('Failed to fetch integrations:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleTest = async (provider: string) => {
    setTesting(provider)
    try {
      await integrationsAPI.test(provider)
      fetchIntegrations()
    } catch (error) {
      console.error('Failed to test integration:', error)
    } finally {
      setTesting(null)
    }
  }

  const handleSync = async (provider: string) => {
    setSyncing(provider)
    try {
      await integrationsAPI.sync(provider)
      fetchIntegrations()
    } catch (error) {
      console.error('Failed to sync integration:', error)
    } finally {
      setSyncing(null)
    }
  }

  const handleConfigure = async (provider: string) => {
    setConfigError('')
    const fields = INTEGRATION_CONFIGS[provider] || []
    const requiredFields = fields.filter(f => f.required)
    const missing = requiredFields.filter(f => !configData[f.name])

    if (missing.length > 0) {
      setConfigError(`Required fields: ${missing.map(f => f.label).join(', ')}`)
      return
    }

    try {
      await integrationsAPI.configure({
        provider,
        name: provider,
        config: configData,
      })
      setConfiguring(null)
      setConfigData({})
      fetchIntegrations()
    } catch (error) {
      const axiosError = error as AxiosError<{ detail?: string }>
      setConfigError(axiosError.response?.data?.detail || 'Failed to configure integration')
    }
  }

  const getConnectionStatus = (provider: string) => {
    return integrations.find(i => i.provider === provider || i.id === provider)
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Integrations</h1>
          <p className="text-sentinel-gray-400 mt-1">
            Connect cloud providers, firewalls, and security tools
          </p>
        </div>
        <button onClick={fetchIntegrations} className="btn-secondary flex items-center gap-2">
          <RefreshCw className="w-4 h-4" />
          Refresh
        </button>
      </div>

      {loading ? (
        <div className="card p-12 text-center">
          <div className="spinner mx-auto mb-4" />
          <p className="text-sentinel-gray-400">Loading integrations...</p>
        </div>
      ) : (
        <div className="space-y-8">
          {PROVIDER_CATEGORIES.map((category) => (
            <div key={category.name}>
              <h2 className="text-lg font-semibold text-white mb-4">{category.name}</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {category.items.map((item) => {
                  const connection = getConnectionStatus(item.id)
                  const Icon = item.icon

                  return (
                    <motion.div
                      key={item.id}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="card p-6"
                    >
                      <div className="flex items-start justify-between mb-4">
                        <div className="flex items-center gap-3">
                          <div className={`w-12 h-12 rounded-xl flex items-center justify-center border ${item.color}`}>
                            <Icon className="w-6 h-6" />
                          </div>
                          <div>
                            <h3 className="text-sm font-semibold text-white">{item.name}</h3>
                            <p className="text-xs text-sentinel-gray-500">
                              {connection?.status === 'connected' ? 'Connected' : 'Not configured'}
                            </p>
                          </div>
                        </div>
                        <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium ${
                          connection?.status === 'connected'
                            ? 'text-emerald-400 bg-emerald-500/10 border border-emerald-500/20'
                            : 'text-sentinel-gray-400 bg-sentinel-gray-500/10 border border-sentinel-gray-500/20'
                        }`}>
                          {connection?.status === 'connected' ? (
                            <><CheckCircle className="w-3 h-3" /> Connected</>
                          ) : (
                            <><XCircle className="w-3 h-3" /> Disconnected</>
                          )}
                        </span>
                      </div>

                      {connection?.last_sync && (
                        <p className="text-xs text-sentinel-gray-500 mb-4">
                          Last sync: {new Date(connection.last_sync).toLocaleString()}
                        </p>
                      )}

                      <div className="flex items-center gap-2">
                        {connection?.status === 'connected' ? (
                          <>
                            <button
                              onClick={() => handleTest(item.id)}
                              disabled={testing === item.id}
                              className="btn-secondary text-xs flex items-center gap-1.5 flex-1"
                            >
                              {testing === item.id ? <Loader2 className="w-3 h-3 animate-spin" /> : <Zap className="w-3 h-3" />}
                              Test
                            </button>
                            <button
                              onClick={() => handleSync(item.id)}
                              disabled={syncing === item.id}
                              className="btn-primary text-xs flex items-center gap-1.5 flex-1"
                            >
                              {syncing === item.id ? <Loader2 className="w-3 h-3 animate-spin" /> : <RefreshCw className="w-3 h-3" />}
                              Sync
                            </button>
                          </>
                        ) : (
                          <button
                            onClick={() => { setConfiguring(item.id); setConfigData({}); setConfigError('') }}
                            className="btn-primary text-xs flex items-center gap-1.5 w-full"
                          >
                            <Settings className="w-3 h-3" />
                            Configure
                          </button>
                        )}
                      </div>
                    </motion.div>
                  )
                })}
              </div>
            </div>
          ))}
        </div>
      )}

      {configuring && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="card p-6 w-full max-w-lg max-h-[80vh] overflow-y-auto"
          >
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg font-semibold text-white">
                Configure {PROVIDER_CATEGORIES.flatMap(c => c.items).find(i => i.id === configuring)?.name}
              </h2>
              <button onClick={() => { setConfiguring(null); setConfigData({}); setConfigError('') }} className="text-sentinel-gray-400 hover:text-white">
                <XCircle className="w-5 h-5" />
              </button>
            </div>

            {configError && (
              <div className="mb-4 p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 text-sm">
                {configError}
              </div>
            )}

            <div className="space-y-4">
              {(INTEGRATION_CONFIGS[configuring] || []).map((field) => (
                <div key={field.name}>
                  <label className="block text-sm font-medium text-sentinel-gray-300 mb-1">
                    {field.label}
                    {field.required && <span className="text-red-400 ml-1">*</span>}
                  </label>
                  {field.type === 'select' ? (
                    <select
                      value={configData[field.name] || ''}
                      onChange={(e) => setConfigData({ ...configData, [field.name]: e.target.value })}
                      className="input w-full"
                    >
                      <option value="">Select...</option>
                      {field.options?.map((opt) => (
                        <option key={opt.value} value={opt.value}>{opt.label}</option>
                      ))}
                    </select>
                  ) : field.type === 'textarea' ? (
                    <textarea
                      value={configData[field.name] || ''}
                      onChange={(e) => setConfigData({ ...configData, [field.name]: e.target.value })}
                      placeholder={field.placeholder}
                      className="input w-full h-24 resize-none"
                    />
                  ) : (
                    <input
                      type={field.type}
                      value={configData[field.name] || ''}
                      onChange={(e) => setConfigData({ ...configData, [field.name]: e.target.value })}
                      placeholder={field.placeholder}
                      className="input w-full"
                    />
                  )}
                </div>
              ))}

              <div className="flex justify-end gap-3 pt-4">
                <button onClick={() => { setConfiguring(null); setConfigData({}); setConfigError('') }} className="btn-secondary">
                  Cancel
                </button>
                <button onClick={() => handleConfigure(configuring)} className="btn-primary flex items-center gap-2">
                  <Link2 className="w-4 h-4" />
                  Connect
                </button>
              </div>
            </div>
          </motion.div>
        </div>
      )}
    </div>
  )
}
