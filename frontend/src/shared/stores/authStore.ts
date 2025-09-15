import { create } from "zustand"
import { devtools, persist } from "zustand/middleware"

interface AuthState {
  // State
  userRole: string | null
  userId: string | null
  email: string | null
  isAppOwner: boolean
  isLoaded: boolean
  isSignedIn: boolean
  sessionClaims: Record<string, any> | null

  // Actions
  setUserRole: (role: string | null) => void
  setUserId: (id: string | null) => void
  setEmail: (email: string | null) => void
  setIsAppOwner: (isOwner: boolean) => void
  setSessionClaims: (claims: Record<string, any> | null) => void
  setAuthData: (data: {
    userId: string | null
    email: string | null
    role: string | null
    isAppOwner: boolean
    sessionClaims: Record<string, any> | null
    isSignedIn: boolean
  }) => void
  setIsLoaded: (loaded: boolean) => void
  clearAuth: () => void

  // Computed getters
  hasRole: (requiredRoles: string | string[]) => boolean
  isAdmin: () => boolean
  isPlatformAdmin: () => boolean
}

export const useAuthStore = create<AuthState>()(
  devtools(
    persist(
      (set, get) => ({
        // Initial state
        userRole: null,
        userId: null,
        email: null,
        isAppOwner: false,
        isLoaded: false,
        isSignedIn: false,
        sessionClaims: null,

        // Actions
        setUserRole: (role) => set({ userRole: role }),
        setUserId: (id) => set({ userId: id }),
        setEmail: (email) => set({ email: email }),
        setIsAppOwner: (isOwner) => set({ isAppOwner: isOwner }),
        setSessionClaims: (claims) => set({ sessionClaims: claims }),
        setIsLoaded: (loaded) => set({ isLoaded: loaded }),

        setAuthData: (data) => set({
          userId: data.userId,
          email: data.email,
          userRole: data.role,
          isAppOwner: data.isAppOwner,
          sessionClaims: data.sessionClaims,
          isSignedIn: data.isSignedIn,
          isLoaded: true,
        }),

        clearAuth: () => set({
          userRole: null,
          userId: null,
          email: null,
          isAppOwner: false,
          isSignedIn: false,
          sessionClaims: null,
          isLoaded: true,
        }),

        // Computed getters
        hasRole: (requiredRoles) => {
          const state = get()
          if (!state.userRole) return false

          const roles = Array.isArray(requiredRoles) ? requiredRoles : [requiredRoles]

          // App owner has access to everything
          if (state.isAppOwner || state.userRole === "app_owner") return true

          // Platform admin has access to admin routes
          if (state.userRole === "platform_admin" && roles.some(r => ["admin", "platform_admin"].includes(r))) {
            return true
          }

          return roles.includes(state.userRole)
        },

        isAdmin: () => {
          const state = get()
          if (!state.userRole) return false
          return state.isAppOwner || ["app_owner", "platform_admin", "admin"].includes(state.userRole)
        },

        isPlatformAdmin: () => {
          const state = get()
          return state.userRole === "platform_admin"
        },
      }),
      {
        name: "auth-storage",
        partialize: (state) => ({
          // Only persist non-sensitive data
          userRole: state.userRole,
          userId: state.userId,
          email: state.email,
          isAppOwner: state.isAppOwner,
        }),
      }
    )
  )
)
