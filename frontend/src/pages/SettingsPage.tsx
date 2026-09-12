import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import {
  User, Mail, Lock, Bell, Shield, Save, Loader2,
  CheckCircle, AlertTriangle, Smartphone, QrCode
} from 'lucide-react'
import { useAuthStore } from '../store/authStore'
import { authAPI } from '../services/api'

interface UserSettings {
  full_name: string
  email: string
  username: string
}

interface NotificationPrefs {
  email_alerts: boolean
  critical_alerts: boolean
  scan_complete: boolean
  weekly_report: boolean
}

export default function SettingsPage() {
  const { user } = useAuthStore()
  const [settings, setSettings] = useState<UserSettings>({
    full_name: user?.full_name || '',
    email: user?.email || '',
    username: user?.username || '',
  })
  const [notifications, setNotifications] = useState<NotificationPrefs>({
    email_alerts: true,
    critical_alerts: true,
    scan_complete: true,
    weekly_report: false,
  })
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const [activeTab, setActiveTab] = useState('profile')
  const [password, setPassword] = useState({ current: '', new: '', confirm: '' })
  const [changingPassword, setChangingPassword] = useState(false)
  const [passwordError, setPasswordError] = useState('')

  const [totpSetup, setTotpSetup] = useState<{ secret: string; qr_code: string; provisioning_uri: string } | null>(null)
  const [totpCode, setTotpCode] = useState('')
  const [settingUp2FA, setSettingUp2FA] = useState(false)
  const [enabling2FA, setEnabling2FA] = useState(false)
  const [disabling2FA, setDisabling2FA] = useState(false)

  const handleSaveProfile = async () => {
    setSaving(true)
    try {
      await new Promise((resolve) => setTimeout(resolve, 500))
      setSaved(true)
      setTimeout(() => setSaved(false), 2000)
    } catch (error) {
      console.error('Failed to save settings:', error)
    } finally {
      setSaving(false)
    }
  }

  const handleChangePassword = async () => {
    if (password.new !== password.confirm) {
      setPasswordError('Passwords do not match')
      return
    }
    setPasswordError('')
    setChangingPassword(true)
    try {
      await authAPI.changePassword(password.current, password.new)
      setPassword({ current: '', new: '', confirm: '' })
      setSaved(true)
      setTimeout(() => setSaved(false), 2000)
    } catch (error: any) {
      setPasswordError(error.response?.data?.detail || 'Failed to change password')
    } finally {
      setChangingPassword(false)
    }
  }

  const handleSetup2FA = async () => {
    setSettingUp2FA(true)
    try {
      const response = await authAPI.setupTOTP()
      setTotpSetup(response.data)
    } catch (error) {
      console.error('Failed to setup 2FA:', error)
    } finally {
      setSettingUp2FA(false)
    }
  }

  const handleVerify2FA = async () => {
    setEnabling2FA(true)
    try {
      await authAPI.verifyTOTP(totpCode)
      useAuthStore.getState().updateUser({ totp_enabled: true })
      setTotpSetup(null)
      setTotpCode('')
    } catch (error) {
      console.error('Failed to verify 2FA:', error)
    } finally {
      setEnabling2FA(false)
    }
  }

  const handleDisable2FA = async () => {
    setDisabling2FA(true)
    try {
      await authAPI.disableTOTP()
      useAuthStore.getState().updateUser({ totp_enabled: false })
    } catch (error) {
      console.error('Failed to disable 2FA:', error)
    } finally {
      setDisabling2FA(false)
    }
  }

  const tabs = [
    { id: 'profile', label: 'Profile', icon: User },
    { id: 'security', label: 'Security', icon: Lock },
    { id: 'notifications', label: 'Notifications', icon: Bell },
  ]

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Settings</h1>
        <p className="text-sentinel-gray-400 mt-1">
          Manage your account settings and preferences
        </p>
      </div>

      <div className="flex gap-6">
        <div className="w-48 flex-shrink-0">
          <div className="card p-2">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  activeTab === tab.id
                    ? 'bg-sentinel-orange-500/20 text-sentinel-orange-500'
                    : 'text-sentinel-gray-400 hover:text-white hover:bg-sentinel-gray-800'
                }`}
              >
                <tab.icon className="w-4 h-4" />
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        <div className="flex-1">
          {activeTab === 'profile' && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="card p-6"
            >
              <h3 className="text-lg font-semibold text-white mb-6">Profile Information</h3>
              <div className="space-y-4 max-w-lg">
                <div>
                  <label className="block text-sm font-medium text-sentinel-gray-300 mb-1">Full Name</label>
                  <div className="relative">
                    <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-sentinel-gray-500" />
                    <input type="text" value={settings.full_name} onChange={(e) => setSettings({ ...settings, full_name: e.target.value })} className="input pl-10 w-full" />
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-sentinel-gray-300 mb-1">Email</label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-sentinel-gray-500" />
                    <input type="email" value={settings.email} onChange={(e) => setSettings({ ...settings, email: e.target.value })} className="input pl-10 w-full" />
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-sentinel-gray-300 mb-1">Username</label>
                  <input type="text" value={settings.username} onChange={(e) => setSettings({ ...settings, username: e.target.value })} className="input w-full" />
                </div>
                <div className="pt-4">
                  <button onClick={handleSaveProfile} disabled={saving} className="btn-primary flex items-center gap-2">
                    {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : saved ? <CheckCircle className="w-4 h-4" /> : <Save className="w-4 h-4" />}
                    {saved ? 'Saved!' : 'Save Changes'}
                  </button>
                </div>
              </div>
            </motion.div>
          )}

          {activeTab === 'security' && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="card p-6"
            >
              <h3 className="text-lg font-semibold text-white mb-6">Change Password</h3>
              <div className="space-y-4 max-w-lg">
                {passwordError && (
                  <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 text-sm">
                    {passwordError}
                  </div>
                )}
                <div className="p-3 bg-sentinel-orange-500/10 border border-sentinel-orange-500/20 rounded-lg text-sentinel-orange-400 text-xs">
                  <p className="font-medium mb-1">Password Requirements:</p>
                  <ul className="list-disc list-inside space-y-0.5">
                    <li>Minimum 4 numbers (non-consecutive, non-sequential)</li>
                    <li>At least 1 special character (!@#$%^&amp;*...)</li>
                    <li>At least 1 uppercase letter</li>
                  </ul>
                </div>
                <div>
                  <label className="block text-sm font-medium text-sentinel-gray-300 mb-1">Current Password</label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-sentinel-gray-500" />
                    <input type="password" value={password.current} onChange={(e) => setPassword({ ...password, current: e.target.value })} className="input pl-10 w-full" />
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-sentinel-gray-300 mb-1">New Password</label>
                  <input type="password" value={password.new} onChange={(e) => setPassword({ ...password, new: e.target.value })} className="input w-full" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-sentinel-gray-300 mb-1">Confirm New Password</label>
                  <input type="password" value={password.confirm} onChange={(e) => setPassword({ ...password, confirm: e.target.value })} className="input w-full" />
                  {password.new && password.confirm && password.new !== password.confirm && (
                    <p className="text-xs text-red-400 mt-1">Passwords do not match</p>
                  )}
                </div>
                <div className="pt-4">
                  <button
                    onClick={handleChangePassword}
                    disabled={changingPassword || !password.current || !password.new || password.new !== password.confirm}
                    className="btn-primary flex items-center gap-2 disabled:opacity-50"
                  >
                    {changingPassword ? <Loader2 className="w-4 h-4 animate-spin" /> : <Lock className="w-4 h-4" />}
                    Update Password
                  </button>
                </div>
              </div>

              <div className="mt-8 pt-6 border-t border-sentinel-gray-800">
                <h4 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
                  <Smartphone className="w-4 h-4 text-sentinel-orange-500" />
                  Two-Factor Authentication (2FA)
                </h4>

                {totpSetup ? (
                  <div className="space-y-4">
                    <p className="text-sm text-sentinel-gray-300">
                      Scan this QR code with Google Authenticator or similar app:
                    </p>
                    <div className="bg-white p-4 rounded-lg inline-block">
                      <img src={totpSetup.qr_code} alt="2FA QR Code" className="w-48 h-48" />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-sentinel-gray-300 mb-1">Manual Entry Key</label>
                      <p className="font-mono text-sm text-sentinel-orange-400 bg-sentinel-gray-800/50 p-2 rounded">{totpSetup.secret}</p>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-sentinel-gray-300 mb-1">Enter 6-digit code from app</label>
                      <input type="text" value={totpCode} onChange={(e) => setTotpCode(e.target.value)} className="input w-full" placeholder="000000" maxLength={6} />
                    </div>
                    <div className="flex gap-3">
                      <button onClick={handleVerify2FA} disabled={enabling2FA || totpCode.length !== 6} className="btn-primary flex items-center gap-2">
                        {enabling2FA ? <Loader2 className="w-4 h-4 animate-spin" /> : <CheckCircle className="w-4 h-4" />}
                        Verify & Enable
                      </button>
                      <button onClick={() => { setTotpSetup(null); setTotpCode('') }} className="btn-secondary">
                        Cancel
                      </button>
                    </div>
                  </div>
                ) : user?.totp_enabled ? (
                  <div className="bg-sentinel-gray-800/50 rounded-lg p-4 border border-sentinel-gray-700">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <CheckCircle className="w-4 h-4 text-emerald-400" />
                        <span className="text-sm text-sentinel-gray-300">2FA is enabled</span>
                      </div>
                      <button onClick={handleDisable2FA} disabled={disabling2FA} className="text-xs text-red-400 hover:text-red-300">
                        {disabling2FA ? 'Disabling...' : 'Disable 2FA'}
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="bg-sentinel-gray-800/50 rounded-lg p-4 border border-sentinel-gray-700">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm text-sentinel-gray-300">Protect your account with 2FA</p>
                        <p className="text-xs text-sentinel-gray-500 mt-1">Works with Google Authenticator, Authy, etc.</p>
                      </div>
                      <button onClick={handleSetup2FA} disabled={settingUp2FA} className="btn-primary text-sm flex items-center gap-2">
                        {settingUp2FA ? <Loader2 className="w-4 h-4 animate-spin" /> : <Smartphone className="w-4 h-4" />}
                        Setup 2FA
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </motion.div>
          )}

          {activeTab === 'notifications' && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="card p-6"
            >
              <h3 className="text-lg font-semibold text-white mb-6">Notification Preferences</h3>
              <div className="space-y-4 max-w-lg">
                {[
                  { key: 'email_alerts', label: 'Email Alerts', desc: 'Receive alerts via email' },
                  { key: 'critical_alerts', label: 'Critical Alerts', desc: 'Immediate notification for critical findings' },
                  { key: 'scan_complete', label: 'Scan Complete', desc: 'Notify when scans finish' },
                  { key: 'weekly_report', label: 'Weekly Report', desc: 'Receive weekly security summary' },
                ].map((item) => (
                  <div key={item.key} className="flex items-center justify-between p-3 rounded-lg bg-sentinel-gray-800/50 border border-sentinel-gray-700">
                    <div>
                      <p className="text-sm font-medium text-white">{item.label}</p>
                      <p className="text-xs text-sentinel-gray-400">{item.desc}</p>
                    </div>
                    <button
                      onClick={() => setNotifications({ ...notifications, [item.key]: !notifications[item.key as keyof NotificationPrefs] })}
                      className={`w-11 h-6 rounded-full transition-colors relative ${
                        notifications[item.key as keyof NotificationPrefs] ? 'bg-sentinel-orange-500' : 'bg-sentinel-gray-600'
                      }`}
                    >
                      <div className={`w-5 h-5 rounded-full bg-white absolute top-0.5 transition-transform ${
                        notifications[item.key as keyof NotificationPrefs] ? 'translate-x-5' : 'translate-x-0.5'
                      }`} />
                    </button>
                  </div>
                ))}
                <div className="pt-4">
                  <button onClick={handleSaveProfile} disabled={saving} className="btn-primary flex items-center gap-2">
                    {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                    Save Preferences
                  </button>
                </div>
              </div>
            </motion.div>
          )}
        </div>
      </div>
    </div>
  )
}
