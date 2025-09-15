import { OpenAPI } from '@/client'

/**
 * Setup Authentication Interceptors
 *
 * Adds Clerk session tokens to all API requests automatically.
 * Handles 401 errors by redirecting to sign in.
 */
export function setupAuthInterceptors() {
  // Add token to every request
  OpenAPI.interceptors.request.use(async (config) => {
    try {
      // Get fresh token from Clerk
      // @ts-ignore - window.Clerk is available after ClerkProvider loads
      if (window.Clerk?.session) {
        // @ts-ignore
        const token = await window.Clerk.session.getToken()
        if (token) {
          config.headers = {
            ...config.headers,
            Authorization: `Bearer ${token}`
          }
        }
      }
    } catch (error) {
      console.error('Failed to get Clerk token:', error)
      // Continue without token - let backend handle unauthorized
    }
    return config
  })

  // Handle auth errors
  OpenAPI.interceptors.response.use(async (response) => {
    // Check for 401 in response
    if (response.status === 401) {
      console.log('Unauthorized - redirecting to sign in')
      // Token expired or invalid - redirect to sign in
      // @ts-ignore
      if (window.Clerk?.redirectToSignIn) {
        // @ts-ignore
        window.Clerk.redirectToSignIn()
      }
    }
    return response
  })

  console.log('Auth interceptors configured')
}
