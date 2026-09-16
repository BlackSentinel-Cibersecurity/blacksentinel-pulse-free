import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import {
  LayoutDashboard, Globe, Radar, Shield, AlertTriangle,
  Puzzle, FileText, Settings, LogOut, Search, Bell, Menu,
  User, Users
} from 'lucide-react'
import { useAuthStore } from '../../store/authStore'

const navigation = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard },
  { name: 'Assets', href: '/assets', icon: Globe },
  { name: 'Discovery', href: '/scans', icon: Radar },
  { name: 'Vulnerabilities', href: '/vulnerabilities', icon: Shield },
  { name: 'Alerts', href: '/alerts', icon: AlertTriangle },
  { name: 'Integrations', href: '/integrations', icon: Puzzle },
  { name: 'Reports', href: '/reports', icon: FileText },
  { name: 'Users', href: '/users', icon: Users },
  { name: 'Settings', href: '/settings', icon: Settings },
]

export default function Layout({ children }: { children: React.ReactNode }) {
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [searchOpen, setSearchOpen] = useState(false)
  const location = useLocation()
  const navigate = useNavigate()
  const { user, logout } = useAuthStore()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <div className="flex h-screen bg-sentinel-black">
      {/* Sidebar */}
      <motion.aside
        initial={false}
        animate={{ width: sidebarOpen ? 260 : 72 }}
        className="fixed left-0 top-0 h-full bg-sentinel-dark border-r border-sentinel-gray-800 z-40 flex flex-col"
      >
        {/* Logo */}
        <div className="flex items-center h-16 px-4 border-b border-sentinel-gray-800">
          <Link to="/" className="flex items-center gap-3">
            <div className="relative flex-shrink-0">
              <img
                src="/logo.png"
                alt="BlackSentinel"
                className="w-10 h-10 object-contain"
              />
            </div>
            {sidebarOpen && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="flex flex-col"
              >
                <span className="text-lg font-bold text-white tracking-tight">
                  BLACK<span className="text-sentinel-orange-500">SENTINEL</span>
                </span>
                <span className="text-[10px] font-medium text-sentinel-gray-400 tracking-[0.2em]">
                  PULSE
                </span>
              </motion.div>
            )}
          </Link>
        </div>

        {/* Navigation */}
        <nav className="flex-1 overflow-y-auto py-4 px-2">
          <div className="space-y-1">
            {navigation.map((item) => {
              const isActive = location.pathname === item.href ||
                (item.href !== '/' && location.pathname.startsWith(item.href))
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  className={`flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200 group ${
                    isActive
                      ? 'bg-sentinel-orange-500/10 text-sentinel-orange-500 border border-sentinel-orange-500/20'
                      : 'text-sentinel-gray-400 hover:bg-sentinel-gray-800 hover:text-white border border-transparent'
                  }`}
                >
                  <item.icon className={`w-5 h-5 flex-shrink-0 ${
                    isActive ? 'text-sentinel-orange-500' : 'text-sentinel-gray-500 group-hover:text-white'
                  }`} />
                  {sidebarOpen && (
                    <span className="text-sm font-medium">{item.name}</span>
                  )}
                  {isActive && sidebarOpen && (
                    <div className="ml-auto w-1.5 h-1.5 rounded-full bg-sentinel-orange-500" />
                  )}
                </Link>
              )
            })}
          </div>
        </nav>

        {/* Sidebar toggle */}
        <div className="p-2 border-t border-sentinel-gray-800">
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="w-full flex items-center justify-center p-2 rounded-lg text-sentinel-gray-500 hover:bg-sentinel-gray-800 hover:text-white transition-colors"
          >
            <Menu className="w-5 h-5" />
          </button>
        </div>
      </motion.aside>

      {/* Main content */}
      <div className="flex-1 flex flex-col" style={{ marginLeft: sidebarOpen ? 260 : 72 }}>
        {/* Header */}
        <header className="h-16 bg-sentinel-dark/80 backdrop-blur-xl border-b border-sentinel-gray-800 flex items-center justify-between px-6 sticky top-0 z-30">
          {/* Search */}
          <div className="flex items-center gap-4">
            <button
              onClick={() => setSearchOpen(true)}
              className="flex items-center gap-2 px-4 py-2 bg-sentinel-gray-800 border border-sentinel-gray-700 rounded-lg text-sentinel-gray-400 hover:border-sentinel-gray-600 transition-colors w-80"
            >
              <Search className="w-4 h-4" />
              <span className="text-sm">Search assets, vulnerabilities...</span>
              <kbd className="ml-auto text-xs bg-sentinel-gray-700 px-1.5 py-0.5 rounded">⌘K</kbd>
            </button>
          </div>

          {/* Right side */}
          <div className="flex items-center gap-4">
            {/* Live indicator */}
            <div className="flex items-center gap-2 px-3 py-1.5 bg-sentinel-gray-800 rounded-full border border-sentinel-gray-700">
              <div className="relative w-2 h-2">
                <div className="absolute inset-0 bg-emerald-500 rounded-full animate-ping" />
                <div className="relative w-2 h-2 bg-emerald-500 rounded-full" />
              </div>
              <span className="text-xs text-emerald-400 font-medium">LIVE</span>
            </div>

            {/* Notifications */}
            <button className="relative p-2 text-sentinel-gray-400 hover:text-white transition-colors">
              <Bell className="w-5 h-5" />
              <span className="absolute top-1 right-1 w-2 h-2 bg-sentinel-orange-500 rounded-full" />
            </button>

            {/* User menu */}
            <div className="flex items-center gap-3 pl-4 border-l border-sentinel-gray-700">
              <div className="w-8 h-8 rounded-full bg-sentinel-orange-500/20 border border-sentinel-orange-500/30 flex items-center justify-center">
                <User className="w-4 h-4 text-sentinel-orange-500" />
              </div>
              <div className="text-sm">
                <div className="text-white font-medium">{user?.full_name || user?.username}</div>
                <div className="text-sentinel-gray-500 text-xs">{user?.role}</div>
              </div>
              <button
                onClick={handleLogout}
                className="p-1.5 text-sentinel-gray-500 hover:text-sentinel-orange-500 transition-colors"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-y-auto bg-grid">
          <div className="p-6">
            {children}
          </div>
        </main>
      </div>

      {/* Search modal */}
      <AnimatePresence>
        {searchOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-start justify-center pt-[20vh]"
          >
            <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={() => setSearchOpen(false)} />
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: -10 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: -10 }}
              className="relative w-full max-w-2xl bg-sentinel-gray-900 border border-sentinel-gray-700 rounded-xl shadow-2xl overflow-hidden"
            >
              <div className="flex items-center gap-3 px-4 py-3 border-b border-sentinel-gray-800">
                <Search className="w-5 h-5 text-sentinel-gray-400" />
                <input
                  type="text"
                  placeholder="Search everything..."
                  className="flex-1 bg-transparent text-white placeholder-sentinel-gray-500 focus:outline-none"
                  autoFocus
                />
                <kbd className="text-xs bg-sentinel-gray-800 px-2 py-1 rounded text-sentinel-gray-500">ESC</kbd>
              </div>
              <div className="p-4 text-sentinel-gray-500 text-sm text-center">
                Start typing to search across assets, vulnerabilities, and alerts...
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
