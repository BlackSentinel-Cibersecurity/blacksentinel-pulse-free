import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from './store/authStore'
import ErrorBoundary from './components/common/ErrorBoundary'
import Layout from './components/layout/Layout'
import LoginPage from './pages/LoginPage'
import DashboardPage from './pages/DashboardPage'
import AssetsPage from './pages/AssetsPage'
import AssetDetailPage from './pages/AssetDetailPage'
import ScansPage from './pages/ScansPage'
import VulnerabilitiesPage from './pages/VulnerabilitiesPage'
import AlertsPage from './pages/AlertsPage'
import IntegrationsPage from './pages/IntegrationsPage'
import ReportsPage from './pages/ReportsPage'
import SettingsPage from './pages/SettingsPage'
import UsersPage from './pages/UsersPage'

function PrivateRoute({ children }: { children: React.ReactNode }) {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated)
  return isAuthenticated ? <>{children}</> : <Navigate to="/login" />
}

function App() {
  return (
    <>
      <div className="noise-overlay" />
      <ErrorBoundary>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route
            path="/*"
            element={
              <PrivateRoute>
                <Layout>
                  <ErrorBoundary>
                    <Routes>
                      <Route path="/" element={<DashboardPage />} />
                      <Route path="/assets" element={<AssetsPage />} />
                      <Route path="/assets/:id" element={<AssetDetailPage />} />
                      <Route path="/scans" element={<ScansPage />} />
                      <Route path="/vulnerabilities" element={<VulnerabilitiesPage />} />
                      <Route path="/alerts" element={<AlertsPage />} />
                      <Route path="/integrations" element={<IntegrationsPage />} />
                      <Route path="/reports" element={<ReportsPage />} />
                      <Route path="/settings" element={<SettingsPage />} />
                      <Route path="/users" element={<UsersPage />} />
                    </Routes>
                  </ErrorBoundary>
                </Layout>
              </PrivateRoute>
            }
          />
        </Routes>
      </ErrorBoundary>
    </>
  )
}

export default App
