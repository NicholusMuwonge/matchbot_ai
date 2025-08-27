import type { BackendUser } from "../types/auth.types"

/**
 * Service for handling authentication API calls to the backend
 */
export class AuthApiService {
  private static instance: AuthApiService
  private baseUrl: string

  constructor() {
    this.baseUrl = import.meta.env.VITE_API_URL || "http://localhost:8000"
  }

  static getInstance(): AuthApiService {
    if (!AuthApiService.instance) {
      AuthApiService.instance = new AuthApiService()
    }
    return AuthApiService.instance
  }

  /**
   * Validate session token with backend
   */
  async validateSession(sessionToken: string): Promise<{
    valid: boolean
    user_id?: string
    clerk_user_id?: string
    error?: string
  }> {
    try {
      const response = await fetch(`${this.baseUrl}/auth/validate-session`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ session_token: sessionToken }),
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      return await response.json()
    } catch (error) {
      return {
        valid: false,
        error: error instanceof Error ? error.message : "Unknown error",
      }
    }
  }

  /**
   * Get current user from backend using session authentication
   */
  async getCurrentUser(sessionToken?: string): Promise<BackendUser | null> {
    try {
      const headers: Record<string, string> = {
        "Content-Type": "application/json",
      }

      if (sessionToken) {
        headers.Authorization = `Bearer ${sessionToken}`
      }

      const response = await fetch(`${this.baseUrl}/auth/me`, {
        method: "GET",
        headers,
      })

      if (!response.ok) {
        if (response.status === 401) {
          return null // Not authenticated
        }
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      return await response.json()
    } catch (error) {
      console.error("Failed to get current user:", error)
      return null
    }
  }
}
