/**
 * Global State Management
 * 
 * Uses Zustand for simple, performant state management.
 * Keeps UI state, not PHI - PHI stays in backend only.
 */

import { create } from 'zustand'

interface User {
  id: string
  email: string
  fullName: string
  role: string
}

interface Claim {
  id: string
  status: string
  claimType: string
  totalCharges: number
  overallConfidence: number
  requiresReview: boolean
  createdAt: string
}

interface AppState {
  // Auth
  user: User | null
  isAuthenticated: boolean
  setUser: (user: User | null) => void
  
  // UI state
  sidebarOpen: boolean
  toggleSidebar: () => void
  
  // Theme
  theme: 'light' | 'dark'
  toggleTheme: () => void
  
  // Active view
  activeView: 'claims' | 'denials' | 'appeals' | 'audit' | 'analytics'
  setActiveView: (view: AppState['activeView']) => void
  
  // Claims list (IDs only, not full data)
  claimIds: string[]
  setClaimIds: (ids: string[]) => void
  
  // Loading states
  isLoading: boolean
  setLoading: (loading: boolean) => void
  
  // Notifications
  notifications: Array<{
    id: string
    type: 'success' | 'error' | 'warning' | 'info'
    message: string
  }>
  addNotification: (type: 'success' | 'error' | 'warning' | 'info', message: string) => void
  removeNotification: (id: string) => void
}

export const useAppStore = create<AppState>((set) => ({
  // Auth
  user: null,
  isAuthenticated: false,
  setUser: (user) => set({ user, isAuthenticated: !!user }),
  
  // UI
  sidebarOpen: true,
  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
  
  // Theme
  theme: 'dark',
  toggleTheme: () => set((state) => {
    const newTheme = state.theme === 'light' ? 'dark' : 'light'
    if (typeof document !== 'undefined') {
      document.documentElement.classList.toggle('dark', newTheme === 'dark')
    }
    return { theme: newTheme }
  }),
  
  // Views
  activeView: 'claims',
  setActiveView: (view) => set({ activeView: view }),
  
  // Claims
  claimIds: [],
  setClaimIds: (ids) => set({ claimIds: ids }),
  
  // Loading
  isLoading: false,
  setLoading: (loading) => set({ isLoading: loading }),
  
  // Notifications
  notifications: [],
  addNotification: (type, message) => set((state) => ({
    notifications: [
      ...state.notifications,
      { id: crypto.randomUUID(), type, message }
    ]
  })),
  removeNotification: (id) => set((state) => ({
    notifications: state.notifications.filter((n) => n.id !== id)
  })),
}))

