/** Authentication state management using Zustand. */

import { create } from 'zustand'
import type { User } from '@/types/auth'
import { getCurrentUser } from '@/lib/auth-api'
import { hasValidToken } from '@/lib/token-storage'

interface AuthState {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  setUser: (user: User | null) => void
  setLoading: (loading: boolean) => void
  initialize: () => Promise<void>
  clear: () => void
}

// Load user from localStorage on initialization
const loadUserFromStorage = (): User | null => {
  if (typeof window === 'undefined') return null
  const stored = localStorage.getItem('auth_user')
  if (stored) {
    try {
      return JSON.parse(stored)
    } catch {
      return null
    }
  }
  return null
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: typeof window !== 'undefined' ? loadUserFromStorage() : null,
  isAuthenticated: typeof window !== 'undefined' ? !!loadUserFromStorage() : false,
  isLoading: true,

  setUser: (user) => {
    if (typeof window !== 'undefined') {
      if (user) {
        localStorage.setItem('auth_user', JSON.stringify(user))
      } else {
        localStorage.removeItem('auth_user')
      }
    }
    set({
      user,
      isAuthenticated: !!user,
    })
  },

  setLoading: (loading) => {
    set({ isLoading: loading })
  },

  initialize: async () => {
    // Check if we have a token
    if (!hasValidToken()) {
      set({ user: null, isAuthenticated: false, isLoading: false })
      if (typeof window !== 'undefined') {
        localStorage.removeItem('auth_user')
      }
      return
    }

    // Try to load from localStorage first
    const storedUser = loadUserFromStorage()
    if (storedUser) {
      set({ user: storedUser, isAuthenticated: true, isLoading: false })
    }

    try {
      // Verify with backend and get fresh user data
      const user = await getCurrentUser()
      set({ user, isAuthenticated: true, isLoading: false })
      if (typeof window !== 'undefined') {
        localStorage.setItem('auth_user', JSON.stringify(user))
      }
    } catch (error) {
      // Token might be invalid, clear state
      set({ user: null, isAuthenticated: false, isLoading: false })
      if (typeof window !== 'undefined') {
        localStorage.removeItem('auth_user')
      }
    }
  },

  clear: () => {
    set({ user: null, isAuthenticated: false, isLoading: false })
    if (typeof window !== 'undefined') {
      localStorage.removeItem('auth_user')
    }
  },
}))

/**
 * useAuth hook for accessing auth state and actions.
 */
export function useAuth() {
  const store = useAuthStore()
  return {
    user: store.user,
    isAuthenticated: store.isAuthenticated,
    isLoading: store.isLoading,
    setUser: store.setUser,
    setLoading: store.setLoading,
    initialize: store.initialize,
    clear: store.clear,
  }
}

