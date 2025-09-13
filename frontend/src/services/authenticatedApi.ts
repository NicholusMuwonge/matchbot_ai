/**
 * Authenticated API Service
 *
 * Gets fresh tokens for each request - no token storage anywhere
 * Best practice: tokens are retrieved just-in-time and never stored
 */

import { OpenAPI } from "@/client"
import type { UsersPublic } from "@/features/users/types/user.types"

export class AuthenticatedApiError extends Error {
  constructor(message: string, public status?: number, public body?: any) {
    super(message)
    this.name = "AuthenticatedApiError"
  }
}

interface ApiOptions {
  method: "GET" | "POST" | "PUT" | "DELETE" | "PATCH"
  url: string
  query?: Record<string, any>
  body?: any
}

export async function makeAuthenticatedRequest<T>(
  auth: any,
  options: ApiOptions
): Promise<T> {
  console.log("🔍 makeAuthenticatedRequest called with:", options)
  console.log("🔍 Auth state:", { isSignedIn: auth.isSignedIn, userId: auth.userId })

  if (!auth.isSignedIn || !auth.getToken) {
    console.log("❌ Not authenticated")
    throw new AuthenticatedApiError("Not authenticated", 401)
  }

  try {
    console.log("🔍 Getting token...")
    const token = await auth.getToken()
    console.log("🔍 Token result:", token ? `${token.substring(0, 20)}...` : "EMPTY")

    if (!token) {
      console.log("❌ Failed to get token")
      throw new AuthenticatedApiError("Failed to get authentication token", 401)
    }

    // Build URL with query params
    let url = `${OpenAPI.BASE}${options.url}`
    console.log("🔍 Base URL:", OpenAPI.BASE)
    console.log("🔍 Full URL before query:", url)

    if (options.query) {
      const queryString = new URLSearchParams(
        Object.entries(options.query)
          .filter(([_, value]) => value !== undefined && value !== null)
          .map(([key, value]) => [key, String(value)])
      ).toString()
      if (queryString) {
        url += `?${queryString}`
      }
    }

    console.log("🔍 Final URL:", url)
    console.log("🔍 Making fetch request...")

    // Create AbortController for timeout handling
    const controller = new AbortController()
    const timeoutId = setTimeout(() => {
      console.log("⏰ Request timeout - aborting")
      controller.abort()
    }, 15000) // 15 second timeout

    try {
      // Make request with fresh token
      const response = await fetch(url, {
        method: options.method,
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`,
        },
        body: options.body ? JSON.stringify(options.body) : undefined,
        credentials: OpenAPI.CREDENTIALS,
        signal: controller.signal,
      })

      clearTimeout(timeoutId)
      console.log("🔍 Fetch response:", response.status, response.statusText)

      if (!response.ok) {
        const errorBody = await response.text()
        console.log("❌ Response error:", errorBody)
        throw new AuthenticatedApiError(
          `HTTP ${response.status}: ${response.statusText}`,
          response.status,
          errorBody
        )
      }

      const result = await response.json()
      console.log("✅ Request successful:", result)
      return result
    } catch (error: any) {
      clearTimeout(timeoutId)
      if (error?.name === 'AbortError') {
        throw new AuthenticatedApiError("Request timeout after 15 seconds", 408)
      }
      throw error
    }
  } catch (error: any) {
    console.error("❌ Request failed:", error)
    if (error instanceof AuthenticatedApiError) {
      throw error
    }
    throw new AuthenticatedApiError(`Request failed: ${error?.message || 'Unknown error'}`)
  }
}

// Specific API methods
export const authenticatedApi = {
  users: {
    list: (auth: any, params: { skip?: number; limit?: number } = {}) =>
      makeAuthenticatedRequest<UsersPublic>(auth, {
        method: "GET",
        url: "/api/v1/users",
        query: params,
      }),
  },
}
