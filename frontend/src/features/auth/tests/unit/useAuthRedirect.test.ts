/**
 * Unit tests for useAuthRedirect hook
 */

import { renderHook } from '@testing-library/react'
import { useAuth } from '@clerk/clerk-react'
import { useNavigate } from '@tanstack/react-router'
import { useAuthRedirect } from '../../hooks/useAuthRedirect'
import { describe, it, expect, vi, beforeEach } from 'vitest'

// Mock Clerk hooks
vi.mock('@clerk/clerk-react', () => ({
  useAuth: vi.fn(),
}))

// Mock TanStack Router
vi.mock('@tanstack/react-router', () => ({
  useNavigate: vi.fn(),
}))

describe('useAuthRedirect', () => {
  const mockNavigate = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(useNavigate).mockReturnValue(mockNavigate)
  })

  it('should not redirect when Clerk is not loaded', () => {
    vi.mocked(useAuth).mockReturnValue({
      isSignedIn: true,
      isLoaded: false,
    } as any)

    renderHook(() => useAuthRedirect())

    expect(mockNavigate).not.toHaveBeenCalled()
  })

  it('should redirect to default fallback URL when signed in and loaded', () => {
    vi.mocked(useAuth).mockReturnValue({
      isSignedIn: true,
      isLoaded: true,
    } as any)

    renderHook(() => useAuthRedirect())

    expect(mockNavigate).toHaveBeenCalledWith({ to: '/' })
  })

  it('should redirect to custom fallback URL when signed in', () => {
    vi.mocked(useAuth).mockReturnValue({
      isSignedIn: true,
      isLoaded: true,
    } as any)

    renderHook(() => useAuthRedirect({ fallbackRedirectUrl: '/dashboard' }))

    expect(mockNavigate).toHaveBeenCalledWith({ to: '/dashboard' })
  })

  it('should not redirect when not signed in', () => {
    vi.mocked(useAuth).mockReturnValue({
      isSignedIn: false,
      isLoaded: true,
    } as any)

    renderHook(() => useAuthRedirect())

    expect(mockNavigate).not.toHaveBeenCalled()
  })

  it('should return auth state', () => {
    vi.mocked(useAuth).mockReturnValue({
      isSignedIn: true,
      isLoaded: true,
    } as any)

    const { result } = renderHook(() => useAuthRedirect())

    expect(result.current.isSignedIn).toBe(true)
    expect(result.current.isLoaded).toBe(true)
  })

  it('should provide redirect functions with default URLs', () => {
    vi.mocked(useAuth).mockReturnValue({
      isSignedIn: false,
      isLoaded: true,
    } as any)

    const { result } = renderHook(() => useAuthRedirect())

    // Test redirectToSignIn
    result.current.redirectToSignIn()
    expect(mockNavigate).toHaveBeenCalledWith({ to: '/signin' })

    // Test redirectToSignUp
    result.current.redirectToSignUp()
    expect(mockNavigate).toHaveBeenCalledWith({ to: '/signup' })

    // Test redirectToDashboard
    result.current.redirectToDashboard()
    expect(mockNavigate).toHaveBeenCalledWith({ to: '/' })
  })

  it('should provide redirect functions with custom URLs', () => {
    vi.mocked(useAuth).mockReturnValue({
      isSignedIn: false,
      isLoaded: true,
    } as any)

    const { result } = renderHook(() => useAuthRedirect({
      signInFallbackRedirectUrl: '/custom-signin',
      signUpFallbackRedirectUrl: '/custom-signup',
      fallbackRedirectUrl: '/custom-dashboard',
    }))

    // Test redirectToSignIn with custom URL
    result.current.redirectToSignIn()
    expect(mockNavigate).toHaveBeenCalledWith({ to: '/custom-signin' })

    // Test redirectToSignUp with custom URL
    result.current.redirectToSignUp()
    expect(mockNavigate).toHaveBeenCalledWith({ to: '/custom-signup' })

    // Test redirectToDashboard with custom URL
    result.current.redirectToDashboard()
    expect(mockNavigate).toHaveBeenCalledWith({ to: '/custom-dashboard' })
  })

  it('should handle auth state changes', () => {
    const { rerender } = renderHook(
      (props) => useAuthRedirect(props),
      {
        initialProps: {},
      }
    )

    // Initially not signed in and not loaded
    vi.mocked(useAuth).mockReturnValue({
      isSignedIn: false,
      isLoaded: false,
    } as any)

    rerender({})
    expect(mockNavigate).not.toHaveBeenCalled()

    // Then loaded but not signed in
    vi.mocked(useAuth).mockReturnValue({
      isSignedIn: false,
      isLoaded: true,
    } as any)

    rerender({})
    expect(mockNavigate).not.toHaveBeenCalled()

    // Finally signed in
    vi.mocked(useAuth).mockReturnValue({
      isSignedIn: true,
      isLoaded: true,
    } as any)

    rerender({})
    expect(mockNavigate).toHaveBeenCalledWith({ to: '/' })
  })

  it('should handle undefined options', () => {
    vi.mocked(useAuth).mockReturnValue({
      isSignedIn: false,
      isLoaded: true,
    } as any)

    const { result } = renderHook(() => useAuthRedirect(undefined))

    // Should use default values
    result.current.redirectToSignIn()
    expect(mockNavigate).toHaveBeenCalledWith({ to: '/signin' })

    result.current.redirectToSignUp()
    expect(mockNavigate).toHaveBeenCalledWith({ to: '/signup' })

    result.current.redirectToDashboard()
    expect(mockNavigate).toHaveBeenCalledWith({ to: '/' })
  })

  it('should handle partial options', () => {
    vi.mocked(useAuth).mockReturnValue({
      isSignedIn: false,
      isLoaded: true,
    } as any)

    const { result } = renderHook(() => useAuthRedirect({
      signInFallbackRedirectUrl: '/custom-signin',
      // Omit other options to test defaults
    }))

    result.current.redirectToSignIn()
    expect(mockNavigate).toHaveBeenCalledWith({ to: '/custom-signin' })

    result.current.redirectToSignUp()
    expect(mockNavigate).toHaveBeenCalledWith({ to: '/signup' })

    result.current.redirectToDashboard()
    expect(mockNavigate).toHaveBeenCalledWith({ to: '/' })
  })
})
