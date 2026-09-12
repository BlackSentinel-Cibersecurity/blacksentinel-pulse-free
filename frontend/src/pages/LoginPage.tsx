import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Eye, EyeOff, Shield, KeyRound } from 'lucide-react'
import { useAuthStore } from '../store/authStore'
import { authAPI } from '../services/api'

export default function LoginPage() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [totpCode, setTotpCode] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [needsTOTP, setNeedsTOTP] = useState(false)
  const [needsPasswordChange, setNeedsPasswordChange] = useState(false)
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [passwordError, setPasswordError] = useState('')
  const navigate = useNavigate()
  const login = useAuthStore((state) => state.login)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    try {
      const response = await authAPI.login(username, password, needsTOTP ? totpCode : undefined)
      const { access_token, refresh_token, user: userData } = response.data

      if (userData.force_password_change) {
        login(access_token, refresh_token, userData)
        setNeedsPasswordChange(true)
        setLoading(false)
        return
      }

      login(access_token, refresh_token, userData)
      navigate('/')
    } catch (err: any) {
      const detail = err.response?.data?.detail || 'Login failed.'
      if (detail.includes('TOTP')) {
        setNeedsTOTP(true)
        setError('')
      } else {
        useAuthStore.getState().logout()
        setError(detail)
      }
    } finally {
      setLoading(false)
    }
  }

  const handlePasswordChange = async (e: React.FormEvent) => {
    e.preventDefault()
    setPasswordError('')

    if (newPassword !== confirmPassword) {
      setPasswordError('Passwords do not match')
      return
    }

    try {
      await authAPI.forceChangePassword(newPassword)
      const user = useAuthStore.getState().user
      if (user) {
        useAuthStore.getState().updateUser({ force_password_change: false })
      }
      navigate('/')
    } catch (err: any) {
      setPasswordError(err.response?.data?.detail || 'Failed to change password')
    }
  }

  if (needsPasswordChange) {
    return (
      <div className="min-h-screen bg-sentinel-black flex items-center justify-center bg-grid relative overflow-hidden">
        <div className="absolute inset-0 bg-pulse-gradient" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-sentinel-orange-500/5 rounded-full blur-3xl" />

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="relative w-full max-w-md mx-4"
        >
          <div className="text-center mb-8">
            <KeyRound className="w-12 h-12 text-sentinel-orange-500 mx-auto mb-4" />
            <h1 className="text-2xl font-bold text-white">Change Your Password</h1>
            <p className="text-sentinel-gray-400 mt-2 text-sm">
              You must change your temporary password before continuing
            </p>
          </div>

          <div className="card p-8">
            <form onSubmit={handlePasswordChange} className="space-y-5">
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
                <label className="block text-sm font-medium text-sentinel-gray-300 mb-2">
                  New Password
                </label>
                <input
                  type="password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  className="input"
                  placeholder="Enter new password"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-sentinel-gray-300 mb-2">
                  Confirm Password
                </label>
                <input
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  className="input"
                  placeholder="Confirm new password"
                  required
                />
              </div>

              <button type="submit" className="w-full btn-primary py-3">
                Change Password & Continue
              </button>
            </form>
          </div>
        </motion.div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-sentinel-black flex items-center justify-center bg-grid relative overflow-hidden">
      <div className="absolute inset-0 bg-pulse-gradient" />
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-sentinel-orange-500/5 rounded-full blur-3xl" />

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="relative w-full max-w-md mx-4"
      >
        <div className="text-center mb-8">
          <motion.div
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ duration: 0.6, delay: 0.1, type: "spring", stiffness: 100 }}
            className="inline-block mb-6"
          >
            <img
              src="/logo.png"
              alt="BlackSentinel"
              className="w-32 h-32 mx-auto object-contain logo-glow"
            />
          </motion.div>
          <motion.h1
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="text-3xl font-bold text-white tracking-tight"
          >
            BLACK<span className="text-sentinel-orange-500">SENTINEL</span>
          </motion.h1>
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.4 }}
            className="text-sentinel-gray-400 mt-2 tracking-[0.3em] text-sm font-medium"
          >
            PULSE
          </motion.p>
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.5 }}
            className="text-sentinel-gray-500 mt-4 text-sm"
          >
            AI Autonomous Attack Surface Management
          </motion.p>
        </div>

        <div className="card p-8 glow-border">
          <form onSubmit={handleSubmit} className="space-y-5">
            {error && (
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 text-sm"
              >
                {error}
              </motion.div>
            )}

            <div>
              <label className="block text-sm font-medium text-sentinel-gray-300 mb-2">
                Username or BlackID
              </label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="input"
                placeholder="Enter username or BlackID"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-sentinel-gray-300 mb-2">
                Password
              </label>
              <div className="relative">
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="input pr-10"
                  placeholder="Enter your password"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-sentinel-gray-500 hover:text-white"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            {needsTOTP && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
              >
                <label className="block text-sm font-medium text-sentinel-gray-300 mb-2">
                  Authenticator Code
                </label>
                <input
                  type="text"
                  value={totpCode}
                  onChange={(e) => setTotpCode(e.target.value)}
                  className="input"
                  placeholder="6-digit code from Google Authenticator"
                  maxLength={6}
                  required
                />
              </motion.div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full btn-primary py-3 flex items-center justify-center gap-2"
            >
              {loading ? (
                <div className="spinner" />
              ) : (
                <>
                  <Shield className="w-4 h-4" />
                  Access Pulse
                </>
              )}
            </button>
          </form>
        </div>

        <p className="text-center text-sentinel-gray-600 text-xs mt-6">
          Protected by BlackSentinel Security
        </p>
      </motion.div>
    </div>
  )
}
