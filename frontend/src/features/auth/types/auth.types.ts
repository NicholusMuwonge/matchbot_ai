/**
 * Authentication type definitions for Clerk integration
 */

export interface ClerkUser {
  id: string
  email?: string
  full_name?: string
  first_name?: string
  last_name?: string
  profile_image_url?: string
  created_at?: string
  email_verified?: boolean
}

export interface AuthState {
  user: ClerkUser | null
  isSignedIn: boolean
  isLoaded: boolean
  loading?: boolean
  error?: string | null
}

export interface AuthActions {
  logout: () => Promise<void>
  signIn: (email: string, password: string) => Promise<void>
  signUp: (email: string, password: string, fullName?: string) => Promise<void>
}

export interface AuthRedirectOptions {
  fallbackRedirectUrl?: string
  signInFallbackRedirectUrl?: string
  signUpFallbackRedirectUrl?: string
}

export interface UserSyncStatus {
  isSynced: boolean
  lastSyncAt?: string
  syncError?: string
}

export interface BackendUser {
  id: string
  email: string
  full_name?: string
  is_active: boolean
  is_superuser: boolean
  clerk_user_id?: string
  auth_provider: string
  is_synced: boolean
  email_verified: boolean
  first_name?: string
  last_name?: string
  profile_image_url?: string
  created_at: string
  last_login?: string
}

export interface AuthApiError {
  status: number
  message: string
  details?: Record<string, any>
}
