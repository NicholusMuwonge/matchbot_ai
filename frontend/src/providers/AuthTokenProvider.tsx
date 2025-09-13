/**
 * Auth Token Provider
 *
 * No longer stores tokens - just provides auth context to children
 * Tokens are retrieved fresh for each API request (best security practice)
 */

import React from "react"

interface AuthTokenProviderProps {
  children: React.ReactNode
}

export function AuthTokenProvider({ children }: AuthTokenProviderProps) {
  // No token storage - just pass through children
  // Individual services will get fresh tokens as needed
  return <>{children}</>
}
