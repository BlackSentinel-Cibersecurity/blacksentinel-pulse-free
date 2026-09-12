import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import {
  Users, Plus, Shield, Trash2, Edit, Copy, CheckCircle,
  Loader2, X, User, Mail, KeyRound
} from 'lucide-react'
import { usersAPI } from '../services/api'

interface UserData {
  id: number
  email: string
  username: string
  black_id?: string
  first_name?: string
  last_name?: string
  full_name: string
  role: string
  is_active: boolean
  force_password_change: boolean
  totp_enabled: boolean
  temp_password_plain?: string
  current_password_plain?: string
  last_login?: string
  created_at: string
}

const ROLE_LABELS: Record<string, string> = {
  super_admin: 'Super Admin',
  ciso: 'CISO',
  security_director: 'Security Director',
  soc_manager: 'SOC Manager',
  soc_supervisor: 'SOC Supervisor',
  security_information_manager: 'Security Information Manager',
  security_compliance_manager: 'Security Compliance Manager',
  soc_analyst_1: 'SOC Analyst L1',
  soc_analyst_2: 'SOC Analyst L2',
  soc_analyst_3: 'SOC Analyst L3',
  soc_analyst_4: 'SOC Analyst L4',
  soc_analyst_5: 'SOC Analyst L5',
  security_analyst_1: 'Security Analyst L1',
  security_analyst_2: 'Security Analyst L2',
  security_analyst_3: 'Security Analyst L3',
  security_analyst_4: 'Security Analyst L4',
  security_analyst_5: 'Security Analyst L5',
  incident_responder: 'Incident Responder',
  threat_hunter: 'Threat Hunter',
  forensics_analyst: 'Forensics Analyst',
  vulnerability_analyst: 'Vulnerability Analyst',
  penetration_tester: 'Penetration Tester',
  security_engineer: 'Security Engineer',
  security_architect: 'Security Architect',
  cloud_security_engineer: 'Cloud Security Engineer',
  devsecops_engineer: 'DevSecOps Engineer',
  system_administrator: 'System Administrator',
  network_engineer: 'Network Engineer',
  it_administrator: 'IT Administrator',
  viewer: 'Viewer',
  auditor: 'Auditor',
}

const ROLE_COLORS: Record<string, string> = {
  super_admin: 'bg-red-500/10 text-red-400 border-red-500/20',
  ciso: 'bg-red-500/10 text-red-400 border-red-500/20',
  security_director: 'bg-red-500/10 text-red-400 border-red-500/20',
  soc_manager: 'bg-sentinel-orange-500/10 text-sentinel-orange-400 border-sentinel-orange-500/20',
  soc_supervisor: 'bg-sentinel-orange-500/10 text-sentinel-orange-400 border-sentinel-orange-500/20',
  security_information_manager: 'bg-sentinel-orange-500/10 text-sentinel-orange-400 border-sentinel-orange-500/20',
  security_compliance_manager: 'bg-sentinel-orange-500/10 text-sentinel-orange-400 border-sentinel-orange-500/20',
  soc_analyst_1: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
  soc_analyst_2: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
  soc_analyst_3: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
  soc_analyst_4: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
  soc_analyst_5: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
  security_analyst_1: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20',
  security_analyst_2: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20',
  security_analyst_3: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20',
  security_analyst_4: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20',
  security_analyst_5: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20',
  incident_responder: 'bg-purple-500/10 text-purple-400 border-purple-500/20',
  threat_hunter: 'bg-purple-500/10 text-purple-400 border-purple-500/20',
  forensics_analyst: 'bg-purple-500/10 text-purple-400 border-purple-500/20',
  vulnerability_analyst: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20',
  penetration_tester: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20',
  security_engineer: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
  security_architect: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
  cloud_security_engineer: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
  devsecops_engineer: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
  system_administrator: 'bg-sentinel-gray-500/10 text-sentinel-gray-400 border-sentinel-gray-500/20',
  network_engineer: 'bg-sentinel-gray-500/10 text-sentinel-gray-400 border-sentinel-gray-500/20',
  it_administrator: 'bg-sentinel-gray-500/10 text-sentinel-gray-400 border-sentinel-gray-500/20',
  viewer: 'bg-sentinel-gray-500/10 text-sentinel-gray-400 border-sentinel-gray-500/20',
  auditor: 'bg-sentinel-gray-500/10 text-sentinel-gray-400 border-sentinel-gray-500/20',
}

const ROLE_GROUPS = [
  { label: 'Leadership', roles: ['ciso', 'security_director', 'soc_manager', 'soc_supervisor', 'security_information_manager', 'security_compliance_manager'] },
  { label: 'SOC Analysts', roles: ['soc_analyst_1', 'soc_analyst_2', 'soc_analyst_3', 'soc_analyst_4', 'soc_analyst_5'] },
  { label: 'Security Analysts', roles: ['security_analyst_1', 'security_analyst_2', 'security_analyst_3', 'security_analyst_4', 'security_analyst_5'] },
  { label: 'Specialized', roles: ['incident_responder', 'threat_hunter', 'forensics_analyst', 'vulnerability_analyst', 'penetration_tester'] },
  { label: 'Engineering', roles: ['security_engineer', 'security_architect', 'cloud_security_engineer', 'devsecops_engineer'] },
  { label: 'Infrastructure', roles: ['system_administrator', 'network_engineer', 'it_administrator'] },
  { label: 'Access', roles: ['viewer', 'auditor'] },
]

export default function UsersPage() {
  const [users, setUsers] = useState<UserData[]>([])
  const [loading, setLoading] = useState(true)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [creating, setCreating] = useState(false)
  const [newUser, setNewUser] = useState({ email: '', first_name: '', last_name: '', role: 'soc_analyst_1' })
  const [createdUser, setCreatedUser] = useState<any>(null)
  const [copied, setCopied] = useState(false)

  useEffect(() => {
    fetchUsers()
  }, [])

  const fetchUsers = async () => {
    try {
      const response = await usersAPI.list()
      setUsers(response.data)
    } catch (error) {
      console.error('Failed to fetch users:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleCreate = async () => {
    setCreating(true)
    try {
      const response = await usersAPI.create(newUser)
      setCreatedUser(response.data)
      setNewUser({ email: '', first_name: '', last_name: '', role: 'analyst' })
      fetchUsers()
    } catch (error) {
      console.error('Failed to create user:', error)
    } finally {
      setCreating(false)
    }
  }

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this user?')) return
    try {
      await usersAPI.delete(id)
      fetchUsers()
    } catch (error) {
      console.error('Failed to delete user:', error)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="spinner mx-auto" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">User Management</h1>
          <p className="text-sentinel-gray-400 mt-1">Manage users and access control</p>
        </div>
        <button onClick={() => { setShowCreateModal(true); setCreatedUser(null) }} className="btn-primary flex items-center gap-2">
          <Plus className="w-4 h-4" /> Create User
        </button>
      </div>

      <div className="card">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-sentinel-gray-800">
                <th className="text-left py-3 px-4 text-xs font-medium text-sentinel-gray-400 uppercase">User</th>
                <th className="text-left py-3 px-4 text-xs font-medium text-sentinel-gray-400 uppercase">BlackID</th>
                <th className="text-left py-3 px-4 text-xs font-medium text-sentinel-gray-400 uppercase">Role</th>
                <th className="text-left py-3 px-4 text-xs font-medium text-sentinel-gray-400 uppercase">Password</th>
                <th className="text-left py-3 px-4 text-xs font-medium text-sentinel-gray-400 uppercase">2FA</th>
                <th className="text-left py-3 px-4 text-xs font-medium text-sentinel-gray-400 uppercase">Status</th>
                <th className="text-left py-3 px-4 text-xs font-medium text-sentinel-gray-400 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody>
              {users.map((user) => (
                <tr key={user.id} className="table-row">
                  <td className="py-3 px-4">
                    <div>
                      <p className="text-sm font-medium text-white">{user.full_name}</p>
                      <p className="text-xs text-sentinel-gray-500">{user.email}</p>
                    </div>
                  </td>
                  <td className="py-3 px-4">
                    <span className="font-mono text-sm text-sentinel-orange-400">{user.black_id || '-'}</span>
                  </td>
                  <td className="py-3 px-4">
                    <span className={`badge ${ROLE_COLORS[user.role] || ''}`}>
                      {ROLE_LABELS[user.role] || user.role}
                    </span>
                  </td>
                  <td className="py-3 px-4">
                    <div className="flex items-center gap-1">
                      {user.force_password_change ? (
                        <span className="font-mono text-xs text-yellow-400">{user.temp_password_plain || '***'}</span>
                      ) : (
                        <span className="font-mono text-xs text-sentinel-gray-400">{user.current_password_plain || '***'}</span>
                      )}
                      <button
                        onClick={() => copyToClipboard(user.force_password_change ? user.temp_password_plain || '' : user.current_password_plain || '')}
                        className="p-1 hover:bg-sentinel-gray-700 rounded"
                        title="Copy password"
                      >
                        <Copy className="w-3 h-3 text-sentinel-gray-500" />
                      </button>
                    </div>
                  </td>
                  <td className="py-3 px-4">
                    {user.totp_enabled ? (
                      <CheckCircle className="w-4 h-4 text-emerald-400" />
                    ) : (
                      <span className="text-xs text-sentinel-gray-500">Off</span>
                    )}
                  </td>
                  <td className="py-3 px-4">
                    <span className={`text-xs ${user.is_active ? 'text-emerald-400' : 'text-red-400'}`}>
                      {user.is_active ? 'Active' : 'Disabled'}
                    </span>
                  </td>
                  <td className="py-3 px-4">
                    <div className="flex items-center gap-2">
                      {user.role !== 'super_admin' && (
                        <button onClick={() => handleDelete(user.id)} className="p-1.5 hover:bg-red-500/10 rounded-lg">
                          <Trash2 className="w-4 h-4 text-red-400" />
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {showCreateModal && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="card p-6 w-full max-w-md mx-4"
          >
            {createdUser ? (
              <div className="space-y-4">
                <div className="flex items-center gap-2 text-emerald-400">
                  <CheckCircle className="w-5 h-5" />
                  <h3 className="text-lg font-semibold">User Created Successfully</h3>
                </div>
                <div className="bg-sentinel-gray-800/50 rounded-lg p-4 space-y-3 border border-sentinel-gray-700">
                  <div>
                    <p className="text-xs text-sentinel-gray-400">BlackID</p>
                    <div className="flex items-center gap-2">
                      <p className="font-mono text-sentinel-orange-400">{createdUser.black_id}</p>
                      <button onClick={() => copyToClipboard(createdUser.black_id)} className="p-1 hover:bg-sentinel-gray-700 rounded">
                        {copied ? <CheckCircle className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3 text-sentinel-gray-400" />}
                      </button>
                    </div>
                  </div>
                  <div>
                    <p className="text-xs text-sentinel-gray-400">Username</p>
                    <p className="font-mono text-white">{createdUser.username}</p>
                  </div>
                  <div>
                    <p className="text-xs text-sentinel-gray-400">Temporary Password</p>
                    <div className="flex items-center gap-2">
                      <p className="font-mono text-red-400">{createdUser.temp_password}</p>
                      <button onClick={() => copyToClipboard(createdUser.temp_password)} className="p-1 hover:bg-sentinel-gray-700 rounded">
                        <Copy className="w-3 h-3 text-sentinel-gray-400" />
                      </button>
                    </div>
                  </div>
                </div>
                <p className="text-xs text-sentinel-gray-400">
                  Share these credentials securely. The user must change their password on first login.
                </p>
                <button onClick={() => { setShowCreateModal(false); setCreatedUser(null) }} className="w-full btn-primary">
                  Done
                </button>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-semibold text-white">Create New User</h3>
                  <button onClick={() => setShowCreateModal(false)} className="p-1 hover:bg-sentinel-gray-700 rounded">
                    <X className="w-5 h-5 text-sentinel-gray-400" />
                  </button>
                </div>

                <div className="p-3 bg-sentinel-orange-500/10 border border-sentinel-orange-500/20 rounded-lg text-sentinel-orange-400 text-xs">
                  <p>Auto-generates: Username, BlackID (initials+4 numbers), and temporary password</p>
                </div>

                <div className="space-y-3">
                  <div>
                    <label className="block text-sm font-medium text-sentinel-gray-300 mb-1">First Name</label>
                    <input type="text" value={newUser.first_name} onChange={(e) => setNewUser({ ...newUser, first_name: e.target.value })} className="input w-full" placeholder="John" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-sentinel-gray-300 mb-1">Last Name</label>
                    <input type="text" value={newUser.last_name} onChange={(e) => setNewUser({ ...newUser, last_name: e.target.value })} className="input w-full" placeholder="Doe" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-sentinel-gray-300 mb-1">Email</label>
                    <input type="email" value={newUser.email} onChange={(e) => setNewUser({ ...newUser, email: e.target.value })} className="input w-full" placeholder="john.doe@company.com" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-sentinel-gray-300 mb-1">Role</label>
                    <select value={newUser.role} onChange={(e) => setNewUser({ ...newUser, role: e.target.value })} className="input w-full">
                      <optgroup label="Leadership">
                        <option value="super_admin">Super Admin</option>
                        <option value="ciso">CISO</option>
                        <option value="security_director">Security Director</option>
                        <option value="soc_manager">SOC Manager</option>
                        <option value="soc_supervisor">SOC Supervisor</option>
                        <option value="security_information_manager">Security Information Manager</option>
                        <option value="security_compliance_manager">Security Compliance Manager</option>
                      </optgroup>
                      <optgroup label="SOC Analysts">
                        <option value="soc_analyst_1">SOC Analyst L1</option>
                        <option value="soc_analyst_2">SOC Analyst L2</option>
                        <option value="soc_analyst_3">SOC Analyst L3</option>
                        <option value="soc_analyst_4">SOC Analyst L4</option>
                        <option value="soc_analyst_5">SOC Analyst L5</option>
                      </optgroup>
                      <optgroup label="Security Analysts">
                        <option value="security_analyst_1">Security Analyst L1</option>
                        <option value="security_analyst_2">Security Analyst L2</option>
                        <option value="security_analyst_3">Security Analyst L3</option>
                        <option value="security_analyst_4">Security Analyst L4</option>
                        <option value="security_analyst_5">Security Analyst L5</option>
                      </optgroup>
                      <optgroup label="Specialized">
                        <option value="incident_responder">Incident Responder</option>
                        <option value="threat_hunter">Threat Hunter</option>
                        <option value="forensics_analyst">Forensics Analyst</option>
                        <option value="vulnerability_analyst">Vulnerability Analyst</option>
                        <option value="penetration_tester">Penetration Tester</option>
                      </optgroup>
                      <optgroup label="Engineering">
                        <option value="security_engineer">Security Engineer</option>
                        <option value="security_architect">Security Architect</option>
                        <option value="cloud_security_engineer">Cloud Security Engineer</option>
                        <option value="devsecops_engineer">DevSecOps Engineer</option>
                      </optgroup>
                      <optgroup label="Infrastructure">
                        <option value="system_administrator">System Administrator</option>
                        <option value="network_engineer">Network Engineer</option>
                        <option value="it_administrator">IT Administrator</option>
                      </optgroup>
                      <optgroup label="Access">
                        <option value="viewer">Viewer</option>
                        <option value="auditor">Auditor</option>
                      </optgroup>
                    </select>
                  </div>
                </div>

                <button onClick={handleCreate} disabled={creating || !newUser.first_name || !newUser.last_name || !newUser.email} className="w-full btn-primary flex items-center justify-center gap-2">
                  {creating ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
                  Create User
                </button>
              </div>
            )}
          </motion.div>
        </div>
      )}
    </div>
  )
}
