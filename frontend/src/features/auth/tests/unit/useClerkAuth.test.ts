/**
 * Unit tests for useClerkAuth hook
 */

import { renderHook } from '@testing-library/react'
import { useAuth, useUser } from '@clerk/clerk-react'
import { useClerkAuth } from '../../hooks/useClerkAuth'
import { describe, it, expect, vi, beforeEach } from 'vitest'

// Mock Clerk hooks
vi.mock('@clerk/clerk-react', () => ({
  useAuth: vi.fn(),
  useUser: vi.fn(),
}))

describe('useClerkAuth', () => {
  const mockSignOut = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should return initial auth state when user is not signed in', () => {
    vi.mocked(useAuth).mockReturnValue({
      isSignedIn: false,
      isLoaded: true,
      signOut: mockSignOut,
    } as any)

    vi.mocked(useUser).mockReturnValue({
      user: null,
    } as any)

    const { result } = renderHook(() => useClerkAuth())

    expect(result.current).toEqual({
      user: null,
      isSignedIn: false,
      isLoaded: true,
      logout: expect.any(Function),
    })
  })

  it('should return user data when signed in', () => {
    const mockUser = {
      id: 'user_123',
      fullName: 'John Doe',
      firstName: 'John',
      lastName: 'Doe',
      primaryEmailAddress: {
        emailAddress: 'john@example.com',
        verification: { status: 'verified' },
      },
      imageUrl: 'https://example.com/avatar.jpg',
      createdAt: new Date('2023-01-01'),
    }

    vi.mocked(useAuth).mockReturnValue({
      isSignedIn: true,
      isLoaded: true,
      signOut: mockSignOut,
    } as any)

    vi.mocked(useUser).mockReturnValue({
      user: mockUser,
    } as any)

    const { result } = renderHook(() => useClerkAuth())

    expect(result.current.user).toEqual({
      id: 'user_123',
      email: 'john@example.com',
      full_name: 'John Doe',
      first_name: 'John',
      last_name: 'Doe',
      profile_image_url: 'https://example.com/avatar.jpg',
      created_at: '2023-01-01T00:00:00.000Z',
      email_verified: true,
    })
    expect(result.current.isSignedIn).toBe(true)
    expect(result.current.isLoaded).toBe(true)
  })

  it('should handle unverified email', () => {
    const mockUser = {
      id: 'user_123',
      primaryEmailAddress: {
        emailAddress: 'john@example.com',
        verification: { status: 'unverified' },
      },
    }

    vi.mocked(useAuth).mockReturnValue({
      isSignedIn: true,
      isLoaded: true,
      signOut: mockSignOut,
    } as any)

    vi.mocked(useUser).mockReturnValue({
      user: mockUser,
    } as any)

    const { result } = renderHook(() => useClerkAuth())

    expect(result.current.user?.email_verified).toBe(false)
  })

  it('should call signOut when logout is called', async () => {
    vi.mocked(useAuth).mockReturnValue({
      isSignedIn: true,
      isLoaded: true,
      signOut: mockSignOut,
    } as any)

    vi.mocked(useUser).mockReturnValue({
      user: null,
    } as any)

    const { result } = renderHook(() => useClerkAuth())

    await result.current.logout()

    expect(mockSignOut).toHaveBeenCalled()
  })

  it('should handle loading state', () => {
    vi.mocked(useAuth).mockReturnValue({
      isSignedIn: false,
      isLoaded: false,
      signOut: mockSignOut,
    } as any)

    vi.mocked(useUser).mockReturnValue({
      user: null,
    } as any)

    const { result } = renderHook(() => useClerkAuth())

    expect(result.current.isLoaded).toBe(false)
  })

  it('should handle missing optional user fields', () => {
    const mockUser = {
      id: 'user_123',
      primaryEmailAddress: {
        emailAddress: 'john@example.com',
        verification: { status: 'verified' },
      },
      // Missing optional fields
      fullName: null,
      firstName: null,
      lastName: null,
      imageUrl: null,
      createdAt: null,
    }

    vi.mocked(useAuth).mockReturnValue({
      isSignedIn: true,
      isLoaded: true,
      signOut: mockSignOut,
    } as any)

    vi.mocked(useUser).mockReturnValue({
      user: mockUser,
    } as any)

    const { result } = renderHook(() => useClerkAuth())

    expect(result.current.user).toEqual({
      id: 'user_123',
      email: 'john@example.com',
      full_name: undefined,
      first_name: undefined,
      last_name: undefined,
      profile_image_url: undefined,
      created_at: undefined,
      email_verified: true,
    })
  })
})
