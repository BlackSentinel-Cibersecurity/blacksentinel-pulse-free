import { create } from 'zustand'

interface User {
  id: number
  email: string
  username: string
  black_id?: string
  full_name: string
  role: string
  organization_id: number
  force_password_change?: boolean
  totp_enabled?: boolean
}

interface AuthState {
  isAuthenticated: boolean
  user: User | null
  token: string | null
  refreshToken: string | null
  login: (token: string, refreshToken: string, user: User) => void
  logout: () => void
  updateUser: (user: Partial<User>) => void
}

const TOKEN_KEY = 'bsp_token'
const REFRESH_KEY = 'bsp_refresh'
const USER_KEY = 'bsp_user'

function loadFromSession(): { token: string | null; refreshToken: string | null; user: User | null } {
  try {
    const token = sessionStorage.getItem(TOKEN_KEY)
    const refreshToken = sessionStorage.getItem(REFRESH_KEY)
    const userStr = sessionStorage.getItem(USER_KEY)
    return {
      token: token || null,
      refreshToken: refreshToken || null,
      user: userStr ? JSON.parse(userStr) : null,
    }
  } catch {
    return { token: null, refreshToken: null, user: null }
  }
}

function saveToSession(token: string | null, refreshToken: string | null, user: User | null) {
  if (token) {
    sessionStorage.setItem(TOKEN_KEY, token)
  } else {
    sessionStorage.removeItem(TOKEN_KEY)
  }
  if (refreshToken) {
    sessionStorage.setItem(REFRESH_KEY, refreshToken)
  } else {
    sessionStorage.removeItem(REFRESH_KEY)
  }
  if (user) {
    sessionStorage.setItem(USER_KEY, JSON.stringify(user))
  } else {
    sessionStorage.removeItem(USER_KEY)
  }
}

const initial = loadFromSession()

export const useAuthStore = create<AuthState>()((set) => ({
  isAuthenticated: !!initial.token,
  user: initial.user,
  token: initial.token,
  refreshToken: initial.refreshToken,
  login: (token, refreshToken, user) => {
    saveToSession(token, refreshToken, user)
    set({ isAuthenticated: true, token, refreshToken, user })
  },
  logout: () => {
    saveToSession(null, null, null)
    set({ isAuthenticated: false, token: null, refreshToken: null, user: null })
  },
  updateUser: (userData) =>
    set((state) => {
      const updated = state.user ? { ...state.user, ...userData } : null
      if (updated) {
        sessionStorage.setItem(USER_KEY, JSON.stringify(updated))
      }
      return { user: updated }
    }),
}))
